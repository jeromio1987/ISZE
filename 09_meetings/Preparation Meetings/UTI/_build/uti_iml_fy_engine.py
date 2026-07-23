"""UTI PMS cover — IML v7 intervals, 100% addressable, fiscal-year billing."""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import yaml

ISZE = Path(__file__).resolve().parents[4]
PRISM = ISZE / "03_analytics/Isuzu/prism"
sys.path.insert(0, str(PRISM))

from config import SALES_FACT_PARQUET, resolve_mapping_path, resolve_uio_path  # noqa: E402
from modules.bvp_analytics import resolve_uio_for_distributor  # noqa: E402
from modules.data_prep import (  # noqa: E402
    build_uio_lookup,
    load_distributor_mapping,
    load_uio_from_excel,
)
from modules.pms_engine import (  # noqa: E402
    CATEGORY_LABELS,
    filter_pms_by_scope,
    pms_scope_for_distributor,
)
from modules.pms_tagging import tag_pms_sales  # noqa: E402
from modules.sales_loader import _finish_sales_frame  # noqa: E402

IML_ITUK = PRISM / "data/iml_v7_ituk_cy2025.yaml"
DIM_CSV = ISZE / "01_data/00_derived/bvp_pn_dimension.csv"

FILTER_CATS = ["oil_filter", "fuel_filter", "air_filter", "urea_filter"]
BRAKE_CATS = ["brake_pad", "brake_shoe", "brake_rotor"]
CLUTCH_CATS = [
    "clutch_disc", "clutch_pressure_plate", "clutch_kit",
    "clutch_booster", "release_bearing", "pilot_bearing",
]
ALL_CATS = FILTER_CATS + BRAKE_CATS + CLUTCH_CATS

BRAKE_W = {"brake_pad": 0.5, "brake_shoe": 0.5, "brake_rotor": 0.25}
CLUTCH_W = {
    "clutch_disc": 0.2, "clutch_pressure_plate": 0.2, "clutch_kit": 0.15,
    "clutch_booster": 0.1, "release_bearing": 0.15, "pilot_bearing": 0.1,
}

# IML v7 freqs (same schedule for UTI presentation)
IML_FILTER_FREQ = 1.25
IML_WEAR_FREQ = 0.5
ADDRESSABLE = 1.0
MILEAGE_KM_YR = 50_000  # IML workbook convention (ITUK); km column for UTI deck
CLUTCH_UIO_RATIO = 10_549 / 22_389  # IML v7 clutch parc subset / full DVLA


def iml_interval_km(freq_yr: float) -> int | None:
    if freq_yr <= 0:
        return None
    return int(round(MILEAGE_KM_YR / freq_yr))


def load_sales() -> pd.DataFrame:
    mapping = load_distributor_mapping(str(resolve_mapping_path()))
    df = pd.read_parquet(SALES_FACT_PARQUET)
    df = _finish_sales_frame(df, mapping)
    dim = pd.read_csv(DIM_CSV)
    df = tag_pms_sales(df, dim, fill_catalog_pms=True)
    if "is_credit_note" in df.columns:
        df = df[~df["is_credit_note"]].copy()
    if "pms_capture_eligible" in df.columns:
        df = df[df["pms_capture_eligible"]].copy()
    return df[df["is_pms"]].copy()


def uti_uio(fy: int) -> int:
    uio_df = load_uio_from_excel(str(resolve_uio_path()))
    lookup, proxy = build_uio_lookup(uio_df)
    uio, _, _ = resolve_uio_for_distributor("UTI", fy, lookup, proxy)
    return int(uio or 0)


def expected_qty(cat: str, uio: int) -> float:
    uio = float(uio) * ADDRESSABLE
    if cat in FILTER_CATS:
        return uio * IML_FILTER_FREQ
    if cat in BRAKE_CATS:
        total = uio * IML_WEAR_FREQ
        wsum = sum(BRAKE_W.values())
        return total * (BRAKE_W[cat] / wsum)
    if cat in CLUTCH_CATS:
        uio_c = uio * CLUTCH_UIO_RATIO
        total = uio_c * IML_WEAR_FREQ
        wsum = sum(CLUTCH_W.values())
        return total * (CLUTCH_W[cat] / wsum)
    return 0.0


def compute_uti_fy(fy: int, sales: pd.DataFrame | None = None) -> dict:
    sales = sales if sales is not None else load_sales()
    scope = pms_scope_for_distributor("UTI")
    uio = uti_uio(fy)
    sub = filter_pms_by_scope(
        sales[(sales["distributor_code"] == "UTI") & (sales["fiscal_year"] == fy)],
        scope,
    )
    cats: dict = {}
    for cat in ALL_CATS:
        exp = expected_qty(cat, uio)
        df_c = sub[sub["pms_category"] == cat]
        for lt in ("total", "genuine", "bvp"):
            part = df_c if lt == "total" else df_c[df_c["pms_type"] == lt]
            act = float(part["billed_qty"].sum())
            rev = float(part["net_sales_value"].sum())
            cap = act / exp if exp > 0 else 0.0
            gap = max(exp - act, 0.0) * (rev / act if act > 0 else 0.0)
            cats.setdefault(cat, {})[lt] = {
                "capture": cap,
                "qty": act,
                "exp": exp,
                "rev": rev,
                "gap": gap,
            }
    return {"fy": fy, "uio": uio, "categories": cats}


def family_cover(cats: dict, keys: list[str]) -> tuple[float, float, float, float]:
    act = sum(cats[k]["total"]["qty"] for k in keys if k in cats)
    exp = sum(cats[k]["total"]["exp"] for k in keys if k in cats)
    raw = act / exp if exp else 0.0
    pct = raw * 100
    return min(pct, 100.0), pct, act, exp


def clutch_kit_job_capture(cats: dict) -> tuple[float, float, float]:
    """Kit is a full substitute for a clutch job (bundles disc+plate+bearing in one PN),
    so score kit sales against total clutch-job demand — not the CLUTCH_W slice
    (0.15/0.9 ~ 16.7%) that assumes components are bought as separate line items.
    That slice-based view is what produced the misleading 108.9% single-category read."""
    _, _, _, exp_total = family_cover(cats, CLUTCH_CATS)
    kit_qty = cats.get("clutch_kit", {}).get("total", {}).get("qty", 0.0)
    pct = (kit_qty / exp_total * 100) if exp_total else 0.0
    return kit_qty, exp_total, pct


def load_ituk_iml() -> dict:
    return yaml.safe_load(IML_ITUK.read_text(encoding="utf-8"))


def schedule_table_rows() -> list[dict]:
    rows = []
    for cat in FILTER_CATS:
        rows.append({
            "label": CATEGORY_LABELS.get(cat, cat),
            "freq": IML_FILTER_FREQ,
            "km": iml_interval_km(IML_FILTER_FREQ),
        })
    rows.append({"label": "Brake (rolled)", "freq": IML_WEAR_FREQ, "km": iml_interval_km(IML_WEAR_FREQ)})
    rows.append({"label": "Clutch (rolled)", "freq": IML_WEAR_FREQ, "km": iml_interval_km(IML_WEAR_FREQ)})
    return rows


def cap_pct(rate: float) -> tuple[float, float]:
    pct = round(rate * 100, 1)
    return min(pct, 100.0), pct


if __name__ == "__main__":
    sales = load_sales()
    for fy in (2023, 2024, 2025):
        r = compute_uti_fy(fy, sales)
        fc = family_cover(r["categories"], FILTER_CATS)
        bc = family_cover(r["categories"], BRAKE_CATS)
        cc = family_cover(r["categories"], CLUTCH_CATS)
        kit_qty, kit_exp, kit_pct = clutch_kit_job_capture(r["categories"])
        print(
            f"FY{fy} UIO={r['uio']:,} | Filters {fc[1]:.1f}% | Brakes {bc[1]:.1f}% | Clutch {cc[1]:.1f}% "
            f"| Clutch kit vs full job {kit_qty:.0f}/{kit_exp:.0f} = {kit_pct:.1f}%"
        )

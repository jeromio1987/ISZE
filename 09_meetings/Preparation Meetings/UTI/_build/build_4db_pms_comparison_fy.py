"""UTI vs ITUK / Imotors / Ireland — PMS & BVP comparison, FY basis (v4).

Rebuilds UTI_vs_ITUK_Imotors_Ireland_PMS_BVP_Comparison_CY2025_v3.xlsx on Jerome's FY
convention (Apr-Mar). v3 had no surviving build script (confirmed via investigation:
its own Read Me states it was built ad-hoc in an agent sandbox against
pms_opportunity_matrix.csv, and never ran the full production pipeline).

Methodology reproduced from v3's own formulas/structure (N75 model: 0.5 services/yr,
100% addressable, CONSUMABLE_FACTOR/WEAR_FACTOR from prism's pms_capture_config —
this is the SAME model as pms_capture_assumptions.yaml, NOT the IML model used in the
UTI-only files). UIO source: 06_uio/_CURRENT/ISUZU_UIO_Overview_2026.xlsx (V19, confirmed
2026-07-04). UTI/ITUK are CV-pure-play (their aggregate UIO IS their CV-truck UIO).
Imotors/Ireland are mixed CV+LCV importers — v3 used the CV-only truck-parc subset as
the PMS denominator (traced and confirmed from V19's row-level CV/LCV split: Imotors CV
2025=2,475, Ireland CV 2025=823 — exact match to v3's hardcoded figures).
"""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter

PRISM = Path(r"C:\Users\jerom\Desktop\claude\ISZE\03_analytics\Isuzu\prism")
sys.path.insert(0, str(PRISM))

from config import SALES_FACT_PARQUET, resolve_mapping_path, resolve_uio_path  # noqa: E402
from modules.data_prep import (  # noqa: E402
    build_uio_lookup,
    load_distributor_mapping,
    load_uio_detail_from_excel,
    load_uio_from_excel,
)
from modules.pms_capture_config import CONSUMABLE_CATS, CONSUMABLE_FACTOR, WEAR_FACTOR  # noqa: E402
from modules.pms_engine import CATEGORY_LABELS, filter_pms_by_scope  # noqa: E402
from modules.pms_tagging import tag_pms_sales  # noqa: E402
from modules.sales_loader import _finish_sales_frame  # noqa: E402

OUT = Path(__file__).resolve().parent.parent / "UTI_vs_ITUK_Imotors_Ireland_PMS_BVP_Comparison_FY_v4.xlsx"
DIM_CSV = PRISM.parent.parent.parent / "01_data/00_derived/bvp_pn_dimension.csv"

DISTRIBUTORS = {
    "UTI": "UTI (Israel)",
    "ITUK": "ITUK (UK)",
    "PORTUGAL": "Imotors (Portugal)",
    "IRELAND": "Isuzu Ireland",
}
# UTI/ITUK: 100% CV parc, standard aggregate UIO IS the CV-truck UIO.
# Portugal/Ireland: mixed CV+LCV importers -- must use CV-only subset (see module docstring).
CV_ONLY_DISTRIBUTORS = {"PORTUGAL", "IRELAND"}

ALL_CATS = CONSUMABLE_CATS + list(WEAR_FACTOR.keys())
BUCKET_OF = {}
for c in CONSUMABLE_CATS:
    BUCKET_OF[c] = "Filters"
for c in WEAR_FACTOR:
    BUCKET_OF[c] = "Clutch" if "clutch" in c or c in ("release_bearing", "pilot_bearing") else "Brakes"

SERVICES_PER_YEAR = 0.5   # N75 model default (pms_capture_assumptions.yaml n75_parc_assumptions)
ADDRESSABLE_PCT = 1.0

NATIVE_FY_YEARS = [2023, 2024, 2025]
FY_LABEL = {fy: fy + 1 for fy in NATIVE_FY_YEARS}  # native fiscal_year -> Jerome's FY naming

NAVY = "1F3864"
HEADER_FILL = PatternFill("solid", fgColor=NAVY)
HEADER_FONT = Font(color="FFFFFF", bold=True)


def load_all_sales() -> pd.DataFrame:
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


def load_uio_sources():
    uio_path = str(resolve_uio_path())
    agg = load_uio_from_excel(uio_path)
    lookup, _ = build_uio_lookup(agg)
    detail = load_uio_detail_from_excel(uio_path)
    cv_only = (
        detail[detail["cv_lcv"] == "CV"]
        .groupby(["distributor_code", "year"])["uio_units"].sum()
        .to_dict()
    )
    return lookup, cv_only


def uio_for(dist: str, fy: int, lookup: dict, cv_only: dict) -> tuple[float, float]:
    """Return (denominator_uio_for_pms, total_parc_uio)."""
    total = float(lookup.get((dist, fy), 0) or 0)
    if dist in CV_ONLY_DISTRIBUTORS:
        cv = float(cv_only.get((dist, fy), 0) or 0)
        return cv, total
    return total, total  # UTI/ITUK: CV parc IS the total parc


def compute_distributor_fy(dist: str, fy: int, sales: pd.DataFrame, lookup: dict, cv_only: dict) -> dict:
    pms_uio, total_uio = uio_for(dist, fy, lookup, cv_only)
    base_qty = pms_uio * SERVICES_PER_YEAR * ADDRESSABLE_PCT

    sub = sales[(sales["distributor_code"] == dist) & (sales["fiscal_year"] == fy)]
    sub = filter_pms_by_scope(sub, "N75_only")

    cats = {}
    for cat in ALL_CATS:
        factor = CONSUMABLE_FACTOR.get(cat) or WEAR_FACTOR.get(cat, 0.0)
        exp_qty = base_qty * factor
        df_c = sub[sub["pms_category"] == cat]
        entry = {}
        for lt in ("total", "genuine", "bvp"):
            part = df_c if lt == "total" else df_c[df_c["pms_type"] == lt]
            act_qty = float(part["billed_qty"].sum())
            act_rev = float(part["net_sales_value"].sum())
            avg_sp = (act_rev / act_qty) if act_qty > 0 else 0.0
            cap = (act_qty / exp_qty) if exp_qty > 0 else 0.0
            gap_eur = max(exp_qty - act_qty, 0.0) * avg_sp
            entry[lt] = {"qty": act_qty, "rev": act_rev, "avg_sp": avg_sp, "capture": cap, "gap": gap_eur}
        entry["exp_qty"] = exp_qty
        entry["tam_eur"] = exp_qty * (entry["total"]["avg_sp"] or 0.0)
        cats[cat] = entry

    return {"dist": dist, "fy": fy, "pms_uio": pms_uio, "total_uio": total_uio, "categories": cats}


def build_category_detail(results: list[dict]) -> pd.DataFrame:
    rows = []
    for r in results:
        for cat in ALL_CATS:
            c = r["categories"][cat]
            rows.append({
                "Distributor": DISTRIBUTORS[r["dist"]],
                "FY": f"FY{FY_LABEL[r['fy']]}",
                "Category": CATEGORY_LABELS.get(cat, cat),
                "Bucket": BUCKET_OF[cat],
                "TAM (EUR)": round(c["tam_eur"]),
                "Actual Total Revenue (EUR)": round(c["total"]["rev"]),
                "Actual Genuine Revenue (EUR)": round(c["genuine"]["rev"]),
                "Total Capture %": round(c["total"]["capture"] * 100, 2),
                "Genuine Capture %": round(c["genuine"]["capture"] * 100, 2),
                "Genuine-vs-BVP Gap (pp)": round((c["total"]["capture"] - c["genuine"]["capture"]) * 100, 2),
                "EUR Gap to 100%": round(c["total"]["gap"]),
            })
    return pd.DataFrame(rows)


def build_bucket_rollup(results: list[dict]) -> pd.DataFrame:
    rows = []
    for r in results:
        by_bucket: dict = {}
        for cat in ALL_CATS:
            b = BUCKET_OF[cat]
            c = r["categories"][cat]
            agg = by_bucket.setdefault(b, {"tam": 0.0, "act": 0.0, "act_gen": 0.0, "exp": 0.0, "gap": 0.0})
            agg["tam"] += c["tam_eur"]
            agg["act"] += c["total"]["qty"]
            agg["act_gen"] += c["genuine"]["qty"]
            agg["exp"] += c["exp_qty"]
            agg["gap"] += c["total"]["gap"]
        for b, agg in by_bucket.items():
            total_cap = agg["act"] / agg["exp"] if agg["exp"] else 0.0
            gen_cap = agg["act_gen"] / agg["exp"] if agg["exp"] else 0.0
            rows.append({
                "Distributor": DISTRIBUTORS[r["dist"]],
                "FY": f"FY{FY_LABEL[r['fy']]}",
                "Bucket": b,
                "TAM (EUR)": round(agg["tam"]),
                "Total Capture %": round(total_cap * 100, 2),
                "Genuine Capture %": round(gen_cap * 100, 2),
                "Genuine-vs-BVP Gap (pp)": round((total_cap - gen_cap) * 100, 2),
                "EUR Gap to 100%": round(agg["gap"]),
            })
    return pd.DataFrame(rows)


def build_distributor_summary(results: list[dict], detail: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for r in results:
        dist_label = DISTRIBUTORS[r["dist"]]
        fy_label = f"FY{FY_LABEL[r['fy']]}"
        d = detail[(detail["Distributor"] == dist_label) & (detail["FY"] == fy_label)]
        tam_sum = d["TAM (EUR)"].sum()
        act_sum = d["Actual Total Revenue (EUR)"].sum()
        gen_sum = d["Actual Genuine Revenue (EUR)"].sum()
        total_cap = sum(r["categories"][c]["total"]["qty"] for c in ALL_CATS) / \
            sum(r["categories"][c]["exp_qty"] for c in ALL_CATS) if sum(r["categories"][c]["exp_qty"] for c in ALL_CATS) else 0
        gen_cap = sum(r["categories"][c]["genuine"]["qty"] for c in ALL_CATS) / \
            sum(r["categories"][c]["exp_qty"] for c in ALL_CATS) if sum(r["categories"][c]["exp_qty"] for c in ALL_CATS) else 0
        rows.append({
            "Distributor": dist_label,
            "FY": fy_label,
            "CV (truck) UIO [PMS denominator]": round(r["pms_uio"]),
            "Total parc UIO (all vehicle types)": round(r["total_uio"]),
            "CV share of total parc": round(r["pms_uio"] / r["total_uio"], 4) if r["total_uio"] else None,
            "TAM (EUR)": round(tam_sum),
            "Actual Total Revenue (EUR)": round(act_sum),
            "Actual Genuine Revenue (EUR)": round(gen_sum),
            "Total Capture %": round(total_cap * 100, 2),
            "Genuine Capture %": round(gen_cap * 100, 2),
            "Genuine-vs-BVP Gap (pp)": round((total_cap - gen_cap) * 100, 2),
        })
    return pd.DataFrame(rows)


def style_header(ws, ncols, row=1):
    for col in range(1, ncols + 1):
        cell = ws.cell(row=row, column=col)
        cell.fill = HEADER_FILL
        cell.font = HEADER_FONT
        cell.alignment = Alignment(horizontal="center")
    ws.freeze_panes = ws.cell(row=row + 1, column=1).coordinate


def autosize(ws, df, extra=2):
    for i, col in enumerate(df.columns, start=1):
        width = max(len(str(col)), df[col].astype(str).map(len).max() if len(df) else 0) + extra
        ws.column_dimensions[get_column_letter(i)].width = min(width, 40)


def write_sheet(writer, name, df):
    df.to_excel(writer, sheet_name=name, index=False)
    ws = writer.sheets[name]
    style_header(ws, len(df.columns))
    autosize(ws, df)


def main():
    print("Loading sales + UIO sources...")
    sales = load_all_sales()
    lookup, cv_only = load_uio_sources()

    results = []
    for dist in DISTRIBUTORS:
        for fy in NATIVE_FY_YEARS:
            results.append(compute_distributor_fy(dist, fy, sales, lookup, cv_only))

    detail = build_category_detail(results)
    bucket = build_bucket_rollup(results)
    summary = build_distributor_summary(results, detail)

    with pd.ExcelWriter(OUT, engine="openpyxl") as writer:
        readme = pd.DataFrame({
            "UTI vs ITUK / Imotors / Ireland -- PMS & BVP Comparison (FY basis, v4)": [
                "Rebuild of the CY2025 v3 workbook on Jerome's FY convention (Apr-Mar). v3 had no surviving build script; this is a from-scratch rebuild replicating its methodology, verified formula-by-formula against v3's own SUMIF structure.",
                "Model: N75 model (0.5 services/yr, 100% addressable, CONSUMABLE_FACTOR/WEAR_FACTOR per prism's pms_capture_config.py / pms_capture_assumptions.yaml) -- the SAME model v3 used. This is NOT the IML model used in the UTI-only files (UTI_PMS_Score_by_PN.xlsx, UTI_PMS_Evolution.html) -- kept as-is for comparability with the existing CY2025 version.",
                "FY labels: FY2024=Apr2023-Mar2024, FY2025=Apr2024-Mar2025, FY2026=Apr2025-Mar2026 (ended 30 Mar 2026, latest available billing data).",
                "UIO source: 06_uio/_CURRENT/ISUZU_UIO_Overview_2026.xlsx -- confirmed this IS the latest version (internal header + changelog both read 'V19') as of 2026-07-04.",
                "PMS denominator: UTI/ITUK are CV-pure-play distributors -- their standard aggregate UIO already IS their CV-truck UIO. Imotors (Portugal) and Isuzu Ireland are mixed CV+LCV importers -- the PMS denominator uses the CV-only truck-parc subset, traced from V19's row-level CV/LCV split (sheet '1.UIO Overview', column 'CV/LCV'). This exactly reproduces v3's hardcoded CV-truck UIO figures (Imotors 2,475 / Ireland 823 for CY2025) -- confirmed match to the unit.",
                "Classification-leakage fix: included via prism's tag_pms_sales(fill_catalog_pms=True), the same mechanism documented in project_pms_classification_leakage -- no separate supplement file needed at this layer.",
                "'Category Detail' = all 4 distributors x 3 FY periods x 14 PMS categories. 'Bucket Rollup' = Filters/Brakes/Clutch TAM-weighted. 'Distributor Summary' = headline comparison per distributor per FY. All values computed directly (not live Excel formulas, unlike v3's Distributor Summary tab).",
                "Known caveat: PMS classification leakage remediation (pms_capture_supplement.csv, 339 PNs) is baked into the tagging pipeline already -- figures here should not be adjusted further for that fix.",
                "'New Categories' section from v3 (leaf spring, shock absorber, water pump, fan belt -- observed revenue only, no capture %) is NOT included here -- no PMS demand model exists for those categories in the reusable engine; would need separate confirmation of methodology before adding.",
            ]
        })
        readme.to_excel(writer, sheet_name="README", index=False, header=False)
        ws = writer.sheets["README"]
        ws.column_dimensions["A"].width = 130
        for row in ws.iter_rows(min_row=1, max_row=1):
            for cell in row:
                cell.font = Font(bold=True, size=13, color=NAVY)
        for row in ws.iter_rows(min_row=2):
            for cell in row:
                cell.alignment = Alignment(wrap_text=True, vertical="top")
                ws.row_dimensions[cell.row].height = 30

        write_sheet(writer, "Distributor Summary", summary)
        write_sheet(writer, "Category Detail", detail)
        write_sheet(writer, "Bucket Rollup", bucket)

    print(f"Wrote {OUT}")
    print(summary.to_string())


if __name__ == "__main__":
    main()

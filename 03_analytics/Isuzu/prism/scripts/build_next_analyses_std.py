#!/usr/bin/env python3
"""
Next useful sales-to-dealer analyses (park stock/loading) — deep layers.

Layers (see 00_docs/sales-to-dealer-analytics-framework_deeplayers.md):
  0 Push vs Pull (billing vs sales-to-dealer value proxy)
  1 Consumables gate via AIM taxonomy (core default for ranking)
  2 AIM buckets inside the gate
  3 GPS gated €/UIO overall / core / consumables
  4 PMS expected-vs-actual (PRISM defs)

Dashboard: one HTML with Metric focus + View toggles (not more packs).
Reuses AIM/GPS loader patterns; does not rebuild sales_fact.
"""
from __future__ import annotations

import html
import json
import math
import re
import sys
from datetime import date
from pathlib import Path

import pandas as pd

PRISM = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PRISM))

from config import (  # noqa: E402
    DASHBOARDS_DIR,
    DASHBOARDS_JSON_DIR,
    DERIVED_DIR,
    GPS_SPU_BY_DB_CSV,
    SALES_FACT_PARQUET,
    resolve_mapping_path,
)
from modules.data_prep import apply_distributor_codes, load_distributor_mapping  # noqa: E402
from modules.dealer_sales_loader import (  # noqa: E402
    load_sellout_long_pn,
    normalize_pn,
)
from modules.dealer_sellout_analytics import attach_pn_master, load_dimension_and_xref  # noqa: E402

YEAR = 2025
YEAR_YTD = 2026
DIST_ORDER = ("ITUK", "UTI", "IRELAND", "IUK", "GREECE", "PORTUGAL")
YTD_STD_DISTS = ("PORTUGAL", "IRELAND", "IUK", "UTI")
NO_2026_STD = ("ITUK", "GREECE")
# UIO channel per DB. Never label IUK as CV / trucks.
DIST_CHANNEL = {
    "ITUK": "CV",
    "UTI": "CV",
    "IUK": "LCV",
    "IRELAND": "CV+LCV",
    "PORTUGAL": "CV+LCV",
    "GREECE": "CV+LCV",
}

CONSUMABLES_L1 = "Hardware & consumables"
CONSUMABLES_TERM_RE = re.compile(r"gasket|seal|bolt|fastener", re.I)
GATE_KEYS = ("overall", "core", "consumables")
DEFAULT_FOCUS = "core"
DEFAULT_VIEW = "gps"
DEFAULT_GAP_METRIC = "eur"  # never land on qty
# Headline PMS layers (filters / brakes / clutch) — not blower-first by expected qty.
PMS_HEADLINE = (
    "oil_filter",
    "fuel_filter",
    "air_filter",
    "brake_pad",
    "brake_shoe",
    "brake_rotor",
    "clutch_kit",
    "clutch_disc",
    "clutch_pressure_plate",
)

PMS_CAPTURE_CSV = DERIVED_DIR / "pms_capture_by_db_year.csv"
AIM_CLASS_CSV = DERIVED_DIR / "aim_pn_classification.csv"

AIM_JSON = DASHBOARDS_JSON_DIR / "dealer_sellout_aim_gps.json"
ENTITY_MIX = DERIVED_DIR / f"dealer_sellout_aim_mix_{YEAR}.csv"
CHART_JS = DASHBOARDS_DIR / "_ui" / "chart.umd.min.js"

OUT_GAP = DERIVED_DIR / "next_analyses_billing_vs_std_gap_2025.csv"
OUT_RANK = DERIVED_DIR / "next_analyses_bvp_country_rank_2025.csv"
OUT_CONC = DERIVED_DIR / "next_analyses_pn_concentration_2025.csv"
OUT_SPU = DERIVED_DIR / "next_analyses_eur_per_vehicle_2025.csv"
OUT_RR = DERIVED_DIR / "next_analyses_2026_runrate.csv"
OUT_PMS = DERIVED_DIR / "next_analyses_pms_contested_capture_2025.csv"
OUT_PMS_EVA = DERIVED_DIR / "next_analyses_pms_expected_vs_actual_2025.csv"
OUT_GPS_GATED = DERIVED_DIR / "next_analyses_gps_gated_2025.csv"
OUT_ITUK = DERIVED_DIR / "next_analyses_ituk_dealer_grain_2025.csv"
OUT_JSON = DASHBOARDS_JSON_DIR / "next_analyses_sales_to_dealer.json"
OUT_HTML = DASHBOARDS_DIR / "sales" / "Next_Analyses_Sales_to_Dealer_SixDB.html"
OUT_CMD = DASHBOARDS_DIR / "sales" / "OPEN_Next_Analyses_Sales_to_Dealer_SixDB.cmd"
OUT_FINDINGS = DERIVED_DIR / "next_analyses_findings.md"

PMS_LABELS = {
    "oil_filter": "Oil filter",
    "fuel_filter": "Fuel filter",
    "air_filter": "Air filter",
    "urea_filter": "Urea filter",
    "brake_pad": "Brake pad",
    "brake_shoe": "Brake shoe",
    "clutch_disc": "Clutch disc",
    "clutch_pressure_plate": "Clutch pressure plate",
    "clutch_kit": "Clutch kit",
    "blower_filter": "Blower / cabin filter",
    "wiper_blade": "Wiper blade",
    "fan_belt": "Fan / A/C belt",
    "shock_absorber": "Shock absorber",
    "hub_bearing": "Hub bearing",
    "bushing": "Bushing",
    "king_pin": "King pin",
    "release_bearing": "Release bearing",
    "pilot_bearing": "Pilot bearing",
    "clutch_booster": "Clutch booster",
    "brake_rotor": "Brake rotor",
}


def dist_label(code: str) -> str:
    ch = DIST_CHANNEL.get(code)
    return f"{code} ({ch})" if ch else code


def _clean(obj: object) -> object:
    if isinstance(obj, dict):
        return {k: _clean(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_clean(x) for x in obj]
    if isinstance(obj, float) and (math.isnan(obj) or math.isinf(obj)):
        return None
    return obj


def _e(t: object) -> str:
    return html.escape(str(t) if t is not None else "")


def _fmt(n: object, digits: int = 0) -> str:
    if n is None or (isinstance(n, float) and math.isnan(n)):
        return "—"
    if digits == 0:
        return f"{float(n):,.0f}"
    return f"{float(n):,.{digits}f}"


def _pct(n: object, digits: int = 1) -> str:
    if n is None or (isinstance(n, float) and math.isnan(n)):
        return "—"
    return f"{float(n) * 100:.{digits}f}%"


def _eur(n: object) -> str:
    if n is None or (isinstance(n, float) and math.isnan(n)):
        return "—"
    return f"€{_fmt(n)}"


def load_aim() -> dict:
    return json.loads(AIM_JSON.read_text(encoding="utf-8"))


def load_uio(dists: tuple[str, ...]) -> dict[str, float]:
    out: dict[str, float] = {}
    if GPS_SPU_BY_DB_CSV.exists():
        gps = pd.read_csv(GPS_SPU_BY_DB_CSV)
        sub = gps[(gps["year"] == YEAR) & (gps["distributor_code"].isin(dists))]
        for _, r in sub.iterrows():
            u = float(r["uio_units"]) if pd.notna(r["uio_units"]) else 0.0
            if u > 0:
                out[str(r["distributor_code"])] = u
    return out


def load_asp(year: int, dists: tuple[str, ...]) -> pd.DataFrame:
    sales = pd.read_parquet(SALES_FACT_PARQUET)
    mapping = load_distributor_mapping(resolve_mapping_path())
    sales = apply_distributor_codes(sales, mapping)
    s = sales[(sales["year"] == year) & (sales["distributor_code"].isin(dists))].copy()
    if "line_kind" in s.columns:
        s = s[s["line_kind"] == "part"]
    s["part_number"] = s["part_number"].map(normalize_pn)
    s = s.dropna(subset=["part_number"])
    s = s[s["billed_qty"] > 0]
    s["asp_eur"] = s["net_sales_value"] / s["billed_qty"]
    s = s[s["asp_eur"] > 0]
    return (
        s.groupby(["distributor_code", "part_number"], as_index=False)["asp_eur"]
        .median()
    )


def load_billing_year(year: int, dists: tuple[str, ...]) -> pd.DataFrame:
    sales = pd.read_parquet(SALES_FACT_PARQUET)
    mapping = load_distributor_mapping(resolve_mapping_path())
    sales = apply_distributor_codes(sales, mapping)
    s = sales[(sales["year"] == year) & (sales["distributor_code"].isin(dists))].copy()
    if "line_kind" in s.columns:
        s = s[s["line_kind"] == "part"]
    s["part_number"] = s["part_number"].map(normalize_pn)
    s = s.dropna(subset=["part_number"])
    s["billing_date"] = pd.to_datetime(s["billing_date"], errors="coerce")
    return s


def classify_pn(pn_df: pd.DataFrame, genuine_pns: set[str], bvp_pns: set[str]) -> pd.DataFrame:
    pn = pn_df["part_number"].astype(str)
    bucket = pd.Series("genuine_only", index=pn_df.index)
    bucket.loc[pn.isin(genuine_pns)] = "genuine_contested"
    bucket.loc[pn.isin(bvp_pns)] = "bvp"
    out = pn_df.copy()
    out["aim_bucket"] = bucket
    return out


def apply_consumables_gate(df: pd.DataFrame) -> pd.DataFrame:
    """Layer 1: consumables_flag / core_flag from AIM L1/L2/L3."""
    out = df.copy()
    l1 = out["aim_l1"].astype(str) if "aim_l1" in out.columns else pd.Series("", index=out.index)
    l2 = out["aim_l2"].astype(str) if "aim_l2" in out.columns else pd.Series("", index=out.index)
    l3 = out["aim_l3"].astype(str) if "aim_l3" in out.columns else pd.Series("", index=out.index)
    hw = l1.eq(CONSUMABLES_L1)
    term = l2.str.contains(CONSUMABLES_TERM_RE, na=False) | l3.str.contains(
        CONSUMABLES_TERM_RE, na=False
    )
    out["consumables_flag"] = hw | term
    out["core_flag"] = ~out["consumables_flag"]
    return out


def attach_aim_class_only(df: pd.DataFrame) -> pd.DataFrame:
    """Light AIM join for billing lines (no full taxonomy enrich)."""
    out = df.copy()
    if not AIM_CLASS_CSV.exists():
        out["aim_l1"] = None
        out["aim_l2"] = None
        out["aim_l3"] = None
        return apply_consumables_gate(out)
    aim = pd.read_csv(
        AIM_CLASS_CSV,
        usecols=["part_number", "aim_l1", "aim_l2", "aim_l3"],
        low_memory=False,
    )
    aim["part_number"] = aim["part_number"].map(normalize_pn)
    aim = aim.dropna(subset=["part_number"]).drop_duplicates("part_number")
    out = out.merge(aim, on="part_number", how="left")
    return apply_consumables_gate(out)


def gate_mask(df: pd.DataFrame, gate: str) -> pd.Series:
    if gate == "overall":
        return pd.Series(True, index=df.index)
    if gate == "core":
        return df["core_flag"].fillna(False)
    if gate == "consumables":
        return df["consumables_flag"].fillna(False)
    raise ValueError(gate)


def hhi_share(qty: pd.Series) -> dict:
    q = qty[qty > 0].astype(float)
    tot = float(q.sum())
    if tot <= 0:
        return {"n_pn": 0, "top10_share": None, "top50_share": None, "hhi": None}
    shares = (q / tot).sort_values(ascending=False)
    return {
        "n_pn": int(shares.shape[0]),
        "top10_share": float(shares.head(10).sum()),
        "top50_share": float(shares.head(50).sum()),
        "hhi": float((shares ** 2).sum()),
    }


def ytd_months_covered(dist: str) -> tuple[int, str]:
    path = DERIVED_DIR / f"dealer_sellout_long_{dist}_CY{YEAR_YTD}YTD.csv"
    if not path.exists():
        path = DERIVED_DIR / f"dealer_sellout_long_{dist}_CY{YEAR_YTD}.csv"
    if not path.exists():
        return 0, "—"
    df = pd.read_csv(path, usecols=lambda c: c in {"period", "period_grain"}, low_memory=False)
    if "period_grain" in df.columns:
        mon = df[df["period_grain"].astype(str).str.lower() == "month"]
    else:
        mon = df
    periods = sorted(
        {
            str(p)
            for p in mon["period"].dropna().unique()
            if re.match(r"^\d{4}-\d{2}$", str(p))
        }
    )
    if not periods:
        return 0, "—"
    return len(periods), periods[-1]


def _aim_metrics(valued: pd.DataFrame) -> dict:
    if valued.empty:
        return {
            "proxy_eur": 0.0,
            "qty": 0.0,
            "bvp_eur": 0.0,
            "genuine_contested_eur": 0.0,
            "bvp_pct": None,
            "genuine_contested_pct": None,
            "contested_bvp_capture": None,
        }
    tot = float(valued["valued_eur"].sum())
    bvp = float(valued.loc[valued["aim_bucket"] == "bvp", "valued_eur"].sum())
    gen_c = float(
        valued.loc[valued["aim_bucket"] == "genuine_contested", "valued_eur"].sum()
    )
    contested = bvp + gen_c
    return {
        "proxy_eur": tot,
        "qty": float(valued["qty_year"].sum()) if "qty_year" in valued.columns else 0.0,
        "bvp_eur": bvp,
        "genuine_contested_eur": gen_c,
        "bvp_pct": (bvp / tot) if tot else None,
        "genuine_contested_pct": (gen_c / tot) if tot else None,
        "contested_bvp_capture": (bvp / contested) if contested else None,
    }


def prepare_std_valued(
    dist: str,
    asp: pd.DataFrame,
    dim: pd.DataFrame,
    desc: pd.DataFrame,
    xref: pd.DataFrame,
    xref_g: set[str],
    xref_b: set[str],
) -> pd.DataFrame:
    sell = load_sellout_long_pn(dist, YEAR, DERIVED_DIR)
    if sell.empty:
        return pd.DataFrame()
    sell = attach_pn_master(sell, dim, desc, xref)
    sell = classify_pn(sell, xref_g, xref_b)
    sell = apply_consumables_gate(sell)
    a = asp[asp["distributor_code"] == dist][["part_number", "asp_eur"]]
    sell = sell.merge(a, on="part_number", how="left")
    sell["valued_eur"] = sell["qty_year"] * sell["asp_eur"].fillna(0)
    return sell


def prepare_bill_valued(bill_dist: pd.DataFrame, xref_g: set[str], xref_b: set[str]) -> pd.DataFrame:
    if bill_dist.empty:
        return pd.DataFrame()
    g = (
        bill_dist.groupby("part_number", as_index=False)
        .agg(billed_qty=("billed_qty", "sum"), net_sales_value=("net_sales_value", "sum"))
    )
    g = attach_aim_class_only(g)
    g = classify_pn(g, xref_g, xref_b)
    g["qty_year"] = g["billed_qty"]
    g["valued_eur"] = g["net_sales_value"]
    return g


def build_gated_bundle(
    dists: tuple[str, ...],
    asp: pd.DataFrame,
    dim: pd.DataFrame,
    desc: pd.DataFrame,
    xref: pd.DataFrame,
    xref_g: set[str],
    xref_b: set[str],
    uio: dict[str, float],
    bill_year: pd.DataFrame,
) -> dict[str, dict]:
    """Per-gate gap / rank / GPS for overall, core, consumables."""
    std_by: dict[str, pd.DataFrame] = {}
    bill_by: dict[str, pd.DataFrame] = {}
    for dist in dists:
        print(f"  gated prepare {dist}…")
        std_by[dist] = prepare_std_valued(dist, asp, dim, desc, xref, xref_g, xref_b)
        bill_by[dist] = prepare_bill_valued(
            bill_year[bill_year["distributor_code"] == dist], xref_g, xref_b
        )

    out: dict[str, dict] = {}
    gps_flat: list[dict] = []
    for gate in GATE_KEYS:
        gaps: list[dict] = []
        ranks: list[dict] = []
        gps_rows: list[dict] = []
        for dist in dists:
            std = std_by[dist]
            bill = bill_by[dist]
            std_g = std[gate_mask(std, gate)] if not std.empty else std
            bill_g = bill[gate_mask(bill, gate)] if not bill.empty else bill
            sm = _aim_metrics(std_g) if not std_g.empty else _aim_metrics(pd.DataFrame())
            # billing AIM metrics on EUR (invoice)
            if bill_g.empty:
                bm = _aim_metrics(pd.DataFrame())
                bill_qty = 0.0
                bill_eur = 0.0
            else:
                bm = _aim_metrics(
                    bill_g.assign(
                        qty_year=bill_g["qty_year"],
                        valued_eur=bill_g["valued_eur"],
                        aim_bucket=bill_g["aim_bucket"],
                    )
                )
                bill_qty = float(bill_g["qty_year"].sum())
                bill_eur = float(bill_g["valued_eur"].sum())

            std_qty = float(std_g["qty_year"].sum()) if not std_g.empty else 0.0
            std_eur = sm["proxy_eur"]
            qty_gap = std_qty - bill_qty
            eur_gap = std_eur - bill_eur
            u = uio.get(dist)
            std_spu = (std_eur / u) if u and std_eur is not None else None
            bill_spu = (bill_eur / u) if u and bill_eur is not None else None

            # Consumables share of overall StD proxy (transparency)
            cons_share = None
            if gate == "core" and not std.empty:
                tot_all = float(std["valued_eur"].sum()) or 0.0
                cons_eur = float(std.loc[std["consumables_flag"], "valued_eur"].sum())
                cons_share = (cons_eur / tot_all) if tot_all else None
            elif gate == "overall" and not std.empty:
                tot_all = float(std["valued_eur"].sum()) or 0.0
                cons_eur = float(std.loc[std["consumables_flag"], "valued_eur"].sum())
                cons_share = (cons_eur / tot_all) if tot_all else None

            gaps.append(
                {
                    "distributor_code": dist,
                    "gate": gate,
                    "uio_channel": DIST_CHANNEL.get(dist),
                    "std_qty": std_qty,
                    "billing_qty": bill_qty,
                    "qty_gap": qty_gap,
                    "qty_gap_pct_of_billing": (qty_gap / bill_qty) if bill_qty else None,
                    "std_proxy_eur": std_eur,
                    "billing_invoice_eur": bill_eur,
                    "eur_gap_proxy_minus_invoice": eur_gap,
                    "eur_gap_pct_of_billing": (eur_gap / bill_eur) if bill_eur else None,
                    "std_bvp_pct": sm["bvp_pct"],
                    "billing_bvp_pct": bm["bvp_pct"],
                    "bvp_pct_pp": (
                        (sm["bvp_pct"] or 0) - (bm["bvp_pct"] or 0)
                        if sm["bvp_pct"] is not None or bm["bvp_pct"] is not None
                        else None
                    ),
                    "std_capture": sm["contested_bvp_capture"],
                    "billing_capture": bm["contested_bvp_capture"],
                    "consumables_share_of_std_proxy": cons_share,
                }
            )
            ranks.append(
                {
                    "distributor_code": dist,
                    "gate": gate,
                    "uio_channel": DIST_CHANNEL.get(dist),
                    "bvp_pct": sm["bvp_pct"],
                    "contested_bvp_capture": sm["contested_bvp_capture"],
                    "genuine_contested_pct": sm["genuine_contested_pct"],
                    "proxy_eur": sm["proxy_eur"],
                    "bvp_eur": sm["bvp_eur"],
                    "qty": sm["qty"],
                    "uio_units": u,
                    "proxy_eur_per_vehicle": std_spu,
                    "consumables_share_of_std_proxy": cons_share,
                }
            )
            gps_row = {
                "distributor_code": dist,
                "gate": gate,
                "uio_channel": DIST_CHANNEL.get(dist),
                "uio_units": u,
                "std_proxy_eur": std_eur,
                "billing_invoice_eur": bill_eur,
                "std_proxy_eur_per_vehicle": std_spu,
                "billing_gps_eur_per_vehicle": bill_spu,
                "consumables_share_of_std_proxy": cons_share,
            }
            gps_rows.append(gps_row)
            gps_flat.append(gps_row)

        ranks.sort(key=lambda x: -(x.get("contested_bvp_capture") or 0))
        for i, r in enumerate(ranks, 1):
            r["rank_by_capture"] = i
        by_mix = sorted(ranks, key=lambda x: -(x.get("bvp_pct") or 0))
        mix_rank = {r["distributor_code"]: i for i, r in enumerate(by_mix, 1)}
        for r in ranks:
            r["rank_by_bvp_pct"] = mix_rank[r["distributor_code"]]

        # AIM L1 proxy € (gated) — deeper layer on the same page as GPS/PMS.
        l1_map: dict[str, dict[str, float]] = {}
        for dist in dists:
            std = std_by[dist]
            std_g = std[gate_mask(std, gate)] if not std.empty else std
            if std_g.empty or "aim_l1" not in std_g.columns:
                continue
            g = std_g.groupby("aim_l1", dropna=False)["valued_eur"].sum()
            for l1, val in g.items():
                key = str(l1) if pd.notna(l1) and str(l1).strip() and str(l1) != "nan" else "(unclassified)"
                l1_map.setdefault(key, {})[dist] = float(val)
        aim_l1_rows = []
        for l1, by_d in l1_map.items():
            row = {"aim_l1": l1, "total_proxy_eur": sum(by_d.values())}
            for dist in dists:
                row[f"{dist}_proxy_eur"] = by_d.get(dist)
            aim_l1_rows.append(row)
        aim_l1_rows.sort(key=lambda x: -(x["total_proxy_eur"] or 0))

        out[gate] = {
            "gap": gaps,
            "rank": ranks,
            "gps": gps_rows,
            "aim_l1": aim_l1_rows[:12],
        }
    out["_gps_flat"] = gps_flat
    return out


def build_gap_legacy(aim: dict) -> list[dict]:
    by = {}
    for r in aim["aim_mix_comparison"]:
        by[(r["distributor_code"], r["layer"])] = r
    rows = []
    for dist in aim["distributors"]:
        so = by.get((dist, "sellout_db_dlr"))
        bill = by.get((dist, "billing_isze_db"))
        if not so or not bill:
            continue
        qty_gap = float(so["qty_year"]) - float(bill["qty_year"])
        eur_gap = float(so["total_eur"]) - float(bill["total_eur"])
        rows.append(
            {
                "distributor_code": dist,
                "std_qty": so["qty_year"],
                "billing_qty": bill["qty_year"],
                "qty_gap": qty_gap,
                "qty_gap_pct_of_billing": qty_gap / bill["qty_year"] if bill["qty_year"] else None,
                "std_proxy_eur": so["total_eur"],
                "billing_invoice_eur": bill["total_eur"],
                "eur_gap_proxy_minus_invoice": eur_gap,
                "eur_gap_pct_of_billing": eur_gap / bill["total_eur"] if bill["total_eur"] else None,
                "std_bvp_pct": so.get("bvp_pct"),
                "billing_bvp_pct": bill.get("bvp_pct"),
                "bvp_pct_pp": (so.get("bvp_pct") or 0) - (bill.get("bvp_pct") or 0),
                "std_capture": so.get("contested_bvp_capture"),
                "billing_capture": bill.get("contested_bvp_capture"),
                "note": (
                    "StD proxy € uses qty×ISZE ASP; billing € is invoice. "
                    "Qty gap ≠ stock (parked)."
                    + (
                        " UTI StD qty is Dec qty Year TYD (full CY2025)."
                        if dist == "UTI"
                        else ""
                    )
                ),
            }
        )
    return rows


def build_pms_contested(aim: dict) -> list[dict]:
    dists = tuple(aim["distributors"])
    out = []
    for r in aim.get("pms_compare", []):
        cat = r.get("pms_category")
        if not cat or cat == "(unclassified)":
            continue
        row = {
            "pms_category": cat,
            "category_label": PMS_LABELS.get(cat, r.get("category_label") or cat),
        }
        for dist in dists:
            bvp_q = r.get(f"{dist}_sellout_db_dlr_bvp_qty") or 0
            gen_c = r.get(f"{dist}_sellout_db_dlr_genuine_contested_qty") or 0
            gen_o = r.get(f"{dist}_sellout_db_dlr_genuine_only_qty") or 0
            tot = bvp_q + gen_c + gen_o
            contested = bvp_q + gen_c
            row[f"{dist}_bvp_qty"] = bvp_q
            row[f"{dist}_contested_qty"] = contested
            row[f"{dist}_total_qty"] = tot
            row[f"{dist}_bvp_share"] = bvp_q / tot if tot else None
            row[f"{dist}_capture"] = bvp_q / contested if contested else None
        out.append(row)
    out.sort(key=lambda x: -sum(x.get(f"{d}_contested_qty") or 0 for d in dists))
    return out


def build_pms_expected_vs_actual(
    dists: tuple[str, ...],
    dim: pd.DataFrame,
    desc: pd.DataFrame,
    xref: pd.DataFrame,
    asp: pd.DataFrame,
) -> list[dict]:
    """Layer 4: PRISM expected vs billing vs sales-to-dealer — € primary, qty beside.

    Expected demand in PRISM is unit-based. Expected € = expected_qty × billing avg SP
    when avg_sp_eur is available. StD actual € = dealer qty × median ISZE ASP.
    """
    if not PMS_CAPTURE_CSV.exists():
        return []
    cap = pd.read_csv(PMS_CAPTURE_CSV)
    bill = cap[
        (cap["year"] == YEAR)
        & (cap["line_type"] == "total")
        & (cap["distributor_code"].isin(dists))
    ].copy()

    std_qty: dict[tuple[str, str], float] = {}
    std_eur: dict[tuple[str, str], float] = {}
    for dist in dists:
        sell = load_sellout_long_pn(dist, YEAR, DERIVED_DIR)
        if sell.empty:
            continue
        sell = attach_pn_master(sell, dim, desc, xref)
        sell = sell[sell["pms_category"].notna() & (sell["pms_category"].astype(str) != "")]
        sell = sell[sell["pms_category"].astype(str) != "(unclassified)"]
        if sell.empty:
            continue
        a = asp[asp["distributor_code"] == dist][["part_number", "asp_eur"]]
        sell = sell.merge(a, on="part_number", how="left")
        sell["valued_eur"] = sell["qty_year"] * sell["asp_eur"].fillna(0)
        g = sell.groupby("pms_category", as_index=False).agg(
            qty_year=("qty_year", "sum"),
            valued_eur=("valued_eur", "sum"),
        )
        for _, r in g.iterrows():
            cat = str(r["pms_category"])
            std_qty[(dist, cat)] = float(r["qty_year"])
            std_eur[(dist, cat)] = float(r["valued_eur"])

    cats = sorted(set(bill["pms_category"].dropna().astype(str)) | {c for _, c in std_qty})
    rows = []
    for cat in cats:
        row: dict = {
            "pms_category": cat,
            "category_label": PMS_LABELS.get(cat, cat.replace("_", " ").title()),
            "headline": cat in PMS_HEADLINE,
            "expected_is_qty": True,
        }
        for dist in dists:
            bsub = bill[(bill["distributor_code"] == dist) & (bill["pms_category"] == cat)]
            exp_qty = float(bsub["expected_qty"].iloc[0]) if not bsub.empty else None
            bill_qty = float(bsub["actual_qty"].iloc[0]) if not bsub.empty else None
            bill_eur = None
            avg_sp = None
            if not bsub.empty:
                if "actual_rev_eur" in bsub.columns and pd.notna(bsub["actual_rev_eur"].iloc[0]):
                    bill_eur = float(bsub["actual_rev_eur"].iloc[0])
                if "avg_sp_eur" in bsub.columns and pd.notna(bsub["avg_sp_eur"].iloc[0]):
                    avg_sp = float(bsub["avg_sp_eur"].iloc[0])
            exp_eur = (exp_qty * avg_sp) if exp_qty is not None and avg_sp else None
            std_q = std_qty.get((dist, cat))
            std_e = std_eur.get((dist, cat))
            row[f"{dist}_expected"] = exp_qty
            row[f"{dist}_expected_qty"] = exp_qty
            row[f"{dist}_expected_eur"] = exp_eur
            row[f"{dist}_billing_actual"] = bill_qty
            row[f"{dist}_billing_actual_qty"] = bill_qty
            row[f"{dist}_billing_actual_eur"] = bill_eur
            row[f"{dist}_std_actual"] = std_q
            row[f"{dist}_std_actual_qty"] = std_q
            row[f"{dist}_std_actual_eur"] = std_e
            row[f"{dist}_avg_sp_eur"] = avg_sp
            row[f"{dist}_billing_capture"] = (
                (bill_qty / exp_qty) if exp_qty and bill_qty is not None else None
            )
            row[f"{dist}_billing_capture_eur"] = (
                (bill_eur / exp_eur) if exp_eur and bill_eur is not None else None
            )
            row[f"{dist}_std_capture"] = (
                (std_q / exp_qty) if exp_qty and std_q is not None else None
            )
            row[f"{dist}_std_capture_eur"] = (
                (std_e / exp_eur) if exp_eur and std_e is not None else None
            )
            row[f"{dist}_uio"] = (
                float(bsub["uio_units"].iloc[0]) if not bsub.empty else None
            )
        rows.append(row)

    def _sort_key(x: dict) -> tuple:
        hl = 0 if x.get("headline") else 1
        tot = sum((x.get(f"{d}_billing_actual_eur") or 0) for d in dists)
        return (hl, -tot)

    rows.sort(key=_sort_key)
    return rows


def build_concentration(
    dists: tuple[str, ...],
    asp: pd.DataFrame,
    dim: pd.DataFrame,
    desc: pd.DataFrame,
    xref: pd.DataFrame,
) -> list[dict]:
    rows = []
    for dist in dists:
        sell = load_sellout_long_pn(dist, YEAR, DERIVED_DIR)
        if sell.empty:
            continue
        bill = load_billing_year(YEAR, (dist,))
        if bill.empty:
            bill_pn = pd.DataFrame(columns=["part_number", "qty_year"])
        else:
            bill_pn = (
                bill.groupby("part_number", as_index=False)["billed_qty"]
                .sum()
                .rename(columns={"billed_qty": "qty_year"})
            )
        so_m = hhi_share(sell.set_index("part_number")["qty_year"])
        bi_m = (
            hhi_share(bill_pn.set_index("part_number")["qty_year"])
            if not bill_pn.empty
            else {"n_pn": 0, "top10_share": None, "top50_share": None, "hhi": None}
        )
        so_top = set(sell.nlargest(25, "qty_year")["part_number"])
        bi_top = set(bill_pn.nlargest(25, "qty_year")["part_number"]) if not bill_pn.empty else set()
        overlap = len(so_top & bi_top) / 25 if so_top and bi_top else None
        sell2 = attach_pn_master(sell, dim, desc, xref)
        xref_g = set(xref["genuine_pn"].dropna().str.strip())
        xref_b = set(xref["bvp_pn"].dropna().str.strip())
        sell2 = classify_pn(sell2, xref_g, xref_b)
        sell2 = apply_consumables_gate(sell2)
        top25 = sell2.nlargest(25, "qty_year")
        top25_bvp_qty = float(top25.loc[top25["aim_bucket"] == "bvp", "qty_year"].sum())
        top25_qty = float(top25["qty_year"].sum())
        top25_cons = float(top25.loc[top25["consumables_flag"], "qty_year"].sum())
        rows.append(
            {
                "distributor_code": dist,
                "std_n_pn": so_m["n_pn"],
                "billing_n_pn": bi_m["n_pn"],
                "std_top10_qty_share": so_m["top10_share"],
                "billing_top10_qty_share": bi_m["top10_share"],
                "std_top50_qty_share": so_m["top50_share"],
                "billing_top50_qty_share": bi_m["top50_share"],
                "std_hhi": so_m["hhi"],
                "billing_hhi": bi_m["hhi"],
                "top25_pn_overlap_share": overlap,
                "std_top25_bvp_qty_share": top25_bvp_qty / top25_qty if top25_qty else None,
                "std_top25_consumables_qty_share": top25_cons / top25_qty if top25_qty else None,
            }
        )
    return rows


def build_runrate_2026(
    asp25: pd.DataFrame,
    xref_g: set[str],
    xref_b: set[str],
    dim: pd.DataFrame,
    desc: pd.DataFrame,
    xref: pd.DataFrame,
    uio: dict[str, float],
) -> list[dict]:
    bill26 = load_billing_year(YEAR_YTD, DIST_ORDER)
    asp26 = load_asp(YEAR_YTD, DIST_ORDER)
    rows = []
    for dist in DIST_ORDER:
        months, through = ytd_months_covered(dist) if dist in YTD_STD_DISTS else (0, "—")
        has_std = dist in YTD_STD_DISTS and months > 0
        std_qty = None
        std_proxy = None
        std_bvp_pct = None
        std_capture = None
        std_rr_qty = None
        std_rr_proxy = None
        if has_std:
            sell = load_sellout_long_pn(dist, YEAR_YTD, DERIVED_DIR)
            if not sell.empty:
                a = asp26[asp26["distributor_code"] == dist][["part_number", "asp_eur"]]
                a25 = asp25[asp25["distributor_code"] == dist][["part_number", "asp_eur"]]
                a = a.rename(columns={"asp_eur": "asp26"}).merge(
                    a25.rename(columns={"asp_eur": "asp25"}), on="part_number", how="outer"
                )
                a["asp_eur"] = a["asp26"].fillna(a["asp25"])
                sell = attach_pn_master(sell, dim, desc, xref)
                sell = classify_pn(sell, xref_g, xref_b)
                sell = sell.merge(a[["part_number", "asp_eur"]], on="part_number", how="left")
                sell["valued_eur"] = sell["qty_year"] * sell["asp_eur"].fillna(0)
                std_qty = float(sell["qty_year"].sum())
                std_proxy = float(sell["valued_eur"].sum())
                bvp_e = float(sell.loc[sell["aim_bucket"] == "bvp", "valued_eur"].sum())
                gen_c = float(
                    sell.loc[sell["aim_bucket"] == "genuine_contested", "valued_eur"].sum()
                )
                tot = float(sell["valued_eur"].sum())
                std_bvp_pct = bvp_e / tot if tot else None
                contested = bvp_e + gen_c
                std_capture = bvp_e / contested if contested else None
                std_rr_qty = std_qty / months * 12
                std_rr_proxy = std_proxy / months * 12

        bsub = bill26[bill26["distributor_code"] == dist]
        bill_qty = float(bsub["billed_qty"].sum()) if not bsub.empty else 0.0
        bill_eur = float(bsub["net_sales_value"].sum()) if not bsub.empty else 0.0
        bill_months = 8
        if not bsub.empty and bsub["billing_date"].notna().any():
            mx = bsub["billing_date"].max()
            bill_months = int(mx.month) if pd.notna(mx) else 8
        bill_rr_qty = bill_qty / bill_months * 12 if bill_months else None
        bill_rr_eur = bill_eur / bill_months * 12 if bill_months else None

        if dist in NO_2026_STD:
            note = f"No 2026 sales-to-dealer file on disk — billing-only run-rate (through {bill_months:02d})."
        elif has_std:
            note = f"StD YTD through {through} ({months} months); billing through month {bill_months}."
        else:
            note = "No StD YTD."

        rows.append(
            {
                "distributor_code": dist,
                "has_2026_std": has_std,
                "std_months": months if has_std else None,
                "std_through": through if has_std else None,
                "std_ytd_qty": std_qty,
                "std_ytd_proxy_eur": std_proxy,
                "std_runrate_qty": std_rr_qty,
                "std_runrate_proxy_eur": std_rr_proxy,
                "std_bvp_pct_ytd": std_bvp_pct,
                "std_capture_ytd": std_capture,
                "std_proxy_eur_per_vehicle_rr": (
                    (std_rr_proxy / uio[dist]) if std_rr_proxy and uio.get(dist) else None
                ),
                "billing_months": bill_months,
                "billing_ytd_qty": bill_qty,
                "billing_ytd_eur": bill_eur,
                "billing_runrate_qty": bill_rr_qty,
                "billing_runrate_eur": bill_rr_eur,
                "billing_gps_rr": (
                    (bill_rr_eur / uio[dist]) if bill_rr_eur and uio.get(dist) else None
                ),
                "uio_units": uio.get(dist),
                "note": note,
            }
        )
    return rows


def build_ituk_dealers() -> list[dict]:
    if not ENTITY_MIX.exists():
        return []
    df = pd.read_csv(ENTITY_MIX)
    ituk = df[df["distributor_code"] == "ITUK"].copy()
    ituk = ituk[~ituk["entity"].astype(str).str.contains("network aggregate", case=False, na=False)]
    ituk = ituk.sort_values("total_eur", ascending=False)
    tot = float(ituk["total_eur"].sum()) or 1.0
    ituk["share_of_network_proxy"] = ituk["total_eur"] / tot
    ituk["rank_by_proxy"] = range(1, len(ituk) + 1)
    cols = [
        "entity",
        "distributor_code",
        "qty_year",
        "total_eur",
        "bvp_eur",
        "bvp_pct",
        "genuine_contested_pct",
        "contested_bvp_capture",
        "share_of_network_proxy",
        "rank_by_proxy",
        "qty_unvalued_share",
    ]
    for c in cols:
        if c not in ituk.columns:
            ituk[c] = None
    return ituk[cols].to_dict(orient="records")


def pointed_bullets(payload: dict) -> list[str]:
    gates = payload["gates"]
    core = gates["core"]
    overall = gates["overall"]
    gap = {r["distributor_code"]: r for r in core["gap"]}
    rank = core["rank"]
    gps = {r["distributor_code"]: r for r in core["gps"]}
    conc = {r["distributor_code"]: r for r in payload["pn_concentration"]}
    rr = {r["distributor_code"]: r for r in payload["runrate_2026"]}
    ituk = payload["ituk_dealers"]
    pms_eva = payload.get("pms_expected_vs_actual") or []
    bullets = []

    # Core vs overall ranking shift
    o_order = [r["distributor_code"] for r in overall["rank"]]
    c_order = [r["distributor_code"] for r in core["rank"]]
    if o_order != c_order:
        bullets.append(
            f"Core gate (ex-gaskets/bolts/Hardware & consumables) reorders BVP capture: "
            f"Overall { ' > '.join(o_order) } → Core { ' > '.join(c_order) }."
        )
    else:
        bullets.append(
            "Core gate (ex-consumables) keeps the same BVP capture order as Overall — "
            "consumables were not the ranking driver."
        )

    for code in DIST_ORDER:
        g = gap.get(code)
        if g and g.get("consumables_share_of_std_proxy") is not None:
            bullets.append(
                f"Consumables share of StD proxy € — {code}: {_pct(g['consumables_share_of_std_proxy'])} "
                f"(excluded from Core ranking)."
            )
            break

    uti_g = gap.get("UTI")
    if uti_g:
        bullets.append(
            f"UTI billing/StD disconnect (Core gate, €): StD proxy {_eur(uti_g['std_proxy_eur'])} vs billing "
            f"{_eur(uti_g['billing_invoice_eur'])} ({_pct(uti_g['eur_gap_pct_of_billing'])})."
        )

    top, bottom = rank[0], rank[-1]
    bullets.append(
        f"Core BVP capture: {top['distributor_code']} {_pct(top['contested_bvp_capture'])} "
        f"(mix {_pct(top['bvp_pct'])}); floor {bottom['distributor_code']} {_pct(bottom['contested_bvp_capture'])}."
    )

    iuk = gps.get("IUK")
    if iuk:
        bullets.append(
            f"IUK GPS (Core): StD proxy {_eur(iuk['std_proxy_eur_per_vehicle'])}/vehicle vs billing "
            f"{_eur(iuk['billing_gps_eur_per_vehicle'])}/vehicle — park = LCV only "
            f"(UIO {_fmt(iuk.get('uio_units'))}), not CV/trucks."
        )

    oil = next((x for x in pms_eva if x["pms_category"] == "oil_filter"), None)
    if oil:
        bits = []
        for d in payload["distributors"]:
            bc = oil.get(f"{d}_billing_capture")
            if bc is not None:
                bits.append(f"{d} bill {_pct(bc)}")
        if bits:
            bullets.append("PMS oil filter total capture (billing ÷ PRISM expected): " + " · ".join(bits[:4]) + ".")

    for code in ("PORTUGAL", "IRELAND", "IUK", "UTI"):
        r = rr.get(code)
        if r and r.get("has_2026_std"):
            bullets.append(
                f"{code} 2026 StD run-rate ~ {_eur(r['std_runrate_proxy_eur'])} through {r['std_through']}."
            )
            break

    if ituk:
        big = [x for x in ituk if (x.get("total_eur") or 0) >= 20000]
        if big:
            best = max(big, key=lambda x: x.get("contested_bvp_capture") or 0)
            worst = min(big, key=lambda x: x.get("contested_bvp_capture") or 0)
            bullets.append(
                f"ITUK dealer spread: {best['entity']} {_pct(best['contested_bvp_capture'])} vs "
                f"{worst['entity']} {_pct(worst['contested_bvp_capture'])} (≥€20k)."
            )

    iuk_c = conc.get("IUK")
    if iuk_c and iuk_c.get("std_top25_consumables_qty_share") is not None:
        bullets.append(
            f"IUK top-25 StD qty consumables share {_pct(iuk_c['std_top25_consumables_qty_share'])} "
            f"(why Core gate exists — ranking uses € on Core, not gasket/bolt qty)."
        )
    bullets.append(
        "Stock/loading: parked. Default landing = Core · GPS €/UIO · gap in € · PMS filters/brakes/clutch on the same page."
    )
    return bullets


def findings_text(payload: dict) -> str:
    gates = payload["gates"]
    core = gates["core"]
    lines = [
        "# Next analyses — sales-to-dealer deep layers (six DBs)",
        "",
        "Framework: `00_docs/sales-to-dealer-analytics-framework_deeplayers.md`",
        f"Default focus: **{DEFAULT_FOCUS}** · default view: **{DEFAULT_VIEW}** · gap metric: **{DEFAULT_GAP_METRIC}**",
        "",
        "## Consumables gate",
        "- AIM: `aim_l1 == Hardware & consumables` OR L2/L3 gasket|seal|bolt|fastener",
        "- Core ranking excludes consumables; share shown for transparency",
        "",
        "## Core BVP capture ranking",
    ]
    for r in core["rank"]:
        lines.append(
            f"- **#{r['rank_by_capture']} {r['distributor_code']} ({r.get('uio_channel')})**: "
            f"capture {_pct(r['contested_bvp_capture'])}, mix {_pct(r['bvp_pct'])}, "
            f"consumables share {_pct(r.get('consumables_share_of_std_proxy'))}."
        )
    lines.append("")
    lines.append("## GPS gated (Core) €/UIO")
    lines.append(
        "- Channels: "
        + " · ".join(f"{d}={DIST_CHANNEL[d]}" for d in DIST_ORDER)
        + ". **IUK = LCV only**."
    )
    for r in core["gps"]:
        lines.append(
            f"- **{r['distributor_code']} ({r.get('uio_channel')})**: StD {_eur(r['std_proxy_eur_per_vehicle'])}/vehicle "
            f"vs billing {_eur(r['billing_gps_eur_per_vehicle'])}/vehicle (UIO {_fmt(r['uio_units'])})."
        )
    lines.append("")
    lines.append("## PMS expected vs actual (headline filters / brakes / clutch, €)")
    for cat in PMS_HEADLINE:
        row = next(
            (x for x in payload.get("pms_expected_vs_actual") or [] if x["pms_category"] == cat),
            None,
        )
        if not row:
            continue
        bits = []
        for d in payload["distributors"]:
            bits.append(
                f"{d} exp {_eur(row.get(f'{d}_expected_eur'))} / bill {_eur(row.get(f'{d}_billing_actual_eur'))} "
                f"/ StD {_eur(row.get(f'{d}_std_actual_eur'))}"
            )
        lines.append(f"- **{row['category_label']}**: " + " · ".join(bits))
    lines.append("")
    lines.append("## Pointed findings")
    for b in payload.get("findings_bullets") or []:
        lines.append(f"- {b}")
    lines.append("")
    lines.append("## Parked")
    lines.append("- Stock / loading — not analysed.")
    lines.append("")
    return "\n".join(lines)


def _tbl(headers, rows) -> str:
    h = (
        "<table class='tbl'><thead><tr>"
        + "".join(f"<th>{_e(x)}</th>" for x in headers)
        + "</tr></thead><tbody>"
    )
    body = "".join("<tr>" + "".join(f"<td>{c}</td>" for c in row) + "</tr>" for row in rows)
    return h + body + "</tbody></table>"


def build_html(payload: dict) -> str:
    chart_src = CHART_JS.read_text(encoding="utf-8") if CHART_JS.exists() else ""
    chart_src = re.sub(r"//# sourceMappingURL=.*$", "", chart_src, flags=re.M).strip()

    gates = payload["gates"]
    core = gates["core"]
    conc = payload["pn_concentration"]
    rr = payload["runrate_2026"]
    pms_c = payload["pms_contested"][:12]
    pms_e = payload.get("pms_expected_vs_actual") or []
    pms_hl = [r for r in pms_e if r.get("headline")] or pms_e[:9]
    pms_e_top = pms_hl + [r for r in pms_e if not r.get("headline")][:6]
    ituk = payload["ituk_dealers"]
    dists = payload["distributors"]
    findings_html = "".join(f"<li>{_e(b)}</li>" for b in payload.get("findings_bullets", []))

    std_eur_tot = sum((r.get("std_proxy_eur") or 0) for r in core["gap"])
    bill_eur_tot = sum((r.get("billing_invoice_eur") or 0) for r in core["gap"])
    eur_gap_tot = std_eur_tot - bill_eur_tot
    gps_iuk = next((r for r in core["gps"] if r["distributor_code"] == "IUK"), None)
    gps_ituk = next((r for r in core["gps"] if r["distributor_code"] == "ITUK"), None)
    rank = core["rank"]
    top = rank[0] if rank else {}
    floor = rank[-1] if rank else {}
    uti_gap = next((r for r in core["gap"] if r["distributor_code"] == "UTI"), None)

    # Static SSR tables for Core default (file:// first paint) — € first, qty last
    gap_tbl = _tbl(
        ["DB", "Channel", "StD proxy €", "Billing invoice €", "€ gap", "€ gap %", "Cons. share", "StD qty", "Bill qty"],
        [
            [
                _e(r["distributor_code"]),
                _e(r.get("uio_channel") or DIST_CHANNEL.get(r["distributor_code"], "—")),
                _eur(r["std_proxy_eur"]),
                _eur(r["billing_invoice_eur"]),
                _eur(r["eur_gap_proxy_minus_invoice"]),
                _pct(r["eur_gap_pct_of_billing"]),
                _pct(r.get("consumables_share_of_std_proxy")),
                _fmt(r["std_qty"]),
                _fmt(r["billing_qty"]),
            ]
            for r in core["gap"]
        ],
    )
    rank_tbl = _tbl(
        ["Rank", "DB", "Channel", "BVP capture", "BVP mix", "Proxy €", "€/vehicle", "Cons. share"],
        [
            [
                str(r["rank_by_capture"]),
                _e(r["distributor_code"]),
                _e(r.get("uio_channel") or "—"),
                _pct(r["contested_bvp_capture"]),
                _pct(r["bvp_pct"]),
                _eur(r["proxy_eur"]),
                _eur(r["proxy_eur_per_vehicle"]),
                _pct(r.get("consumables_share_of_std_proxy")),
            ]
            for r in core["rank"]
        ],
    )
    gps_tbl = _tbl(
        ["DB", "Channel", "UIO", "StD proxy €/vehicle", "Billing GPS €/vehicle", "Cons. share of StD"],
        [
            [
                _e(r["distributor_code"]),
                _e(r.get("uio_channel") or "—"),
                _fmt(r["uio_units"]),
                _eur(r["std_proxy_eur_per_vehicle"]),
                _eur(r["billing_gps_eur_per_vehicle"]),
                _pct(r.get("consumables_share_of_std_proxy")),
            ]
            for r in core["gps"]
        ],
    )
    conc_tbl = _tbl(
        ["DB", "StD PNs", "Bill PNs", "StD top10", "Bill top10", "Top25 overlap", "Top25 BVP", "Top25 cons."],
        [
            [
                _e(r["distributor_code"]),
                _fmt(r["std_n_pn"]),
                _fmt(r["billing_n_pn"]),
                _pct(r["std_top10_qty_share"]),
                _pct(r["billing_top10_qty_share"]),
                _pct(r["top25_pn_overlap_share"]),
                _pct(r["std_top25_bvp_qty_share"]),
                _pct(r.get("std_top25_consumables_qty_share")),
            ]
            for r in conc
        ],
    )
    rr_tbl = _tbl(
        ["DB", "StD?", "Through", "StD qty RR", "StD proxy RR", "StD €/veh RR", "Bill € RR", "Note"],
        [
            [
                _e(r["distributor_code"]),
                "Yes" if r["has_2026_std"] else "No",
                _e(r["std_through"] or "—"),
                _fmt(r["std_runrate_qty"]),
                _eur(r["std_runrate_proxy_eur"]),
                _eur(r["std_proxy_eur_per_vehicle_rr"]),
                _eur(r["billing_runrate_eur"]),
                _e(r["note"]),
            ]
            for r in rr
        ],
    )
    pms_eva_headers = ["PMS"] + [
        f"{d} exp € / bill € / StD € / bill cap" for d in dists
    ]
    pms_eva_rows = []
    for r in pms_hl:
        row = [_e(r["category_label"])]
        for d in dists:
            row.append(
                f"{_eur(r.get(f'{d}_expected_eur'))} / {_eur(r.get(f'{d}_billing_actual_eur'))} / "
                f"{_eur(r.get(f'{d}_std_actual_eur'))} / {_pct(r.get(f'{d}_billing_capture_eur') or r.get(f'{d}_billing_capture'))}"
            )
        pms_eva_rows.append(row)
    pms_eva_tbl = _tbl(pms_eva_headers, pms_eva_rows)

    aim_l1 = (core.get("aim_l1") or [])[:8]
    aim_headers = ["AIM L1"] + [str(d) for d in dists] + ["Total proxy €"]
    aim_rows = []
    for r in aim_l1:
        row = [_e(r["aim_l1"])]
        for d in dists:
            row.append(_eur(r.get(f"{d}_proxy_eur")))
        row.append(_eur(r.get("total_proxy_eur")))
        aim_rows.append(row)
    aim_tbl = _tbl(aim_headers, aim_rows)

    pms_headers = ["PMS"] + [f"{d} BVP share" for d in dists]
    pms_rows = []
    for r in pms_c:
        row = [_e(r["category_label"])]
        for d in dists:
            row.append(_pct(r.get(f"{d}_bvp_share")))
        pms_rows.append(row)
    pms_mix_tbl = _tbl(pms_headers, pms_rows)

    top15 = ituk[:15]
    big = [x for x in ituk if (x.get("total_eur") or 0) >= 20000]
    weak = sorted(big, key=lambda x: (x.get("contested_bvp_capture") or 0))[:8]
    strong = sorted(big, key=lambda x: -(x.get("contested_bvp_capture") or 0))[:8]
    ituk_top = _tbl(
        ["#", "Dealer", "Qty", "Proxy €", "Share", "BVP %", "Capture"],
        [
            [
                str(r["rank_by_proxy"]),
                _e(r["entity"]),
                _fmt(r["qty_year"]),
                _eur(r["total_eur"]),
                _pct(r["share_of_network_proxy"]),
                _pct(r["bvp_pct"]),
                _pct(r["contested_bvp_capture"]),
            ]
            for r in top15
        ],
    )
    ituk_cap = _tbl(
        ["Dealer", "Proxy €", "BVP %", "Capture", "Flag"],
        [
            [_e(r["entity"]), _eur(r["total_eur"]), _pct(r["bvp_pct"]), _pct(r["contested_bvp_capture"]), "Strong"]
            for r in strong
        ]
        + [
            [_e(r["entity"]), _eur(r["total_eur"]), _pct(r["bvp_pct"]), _pct(r["contested_bvp_capture"]), "Weak"]
            for r in weak
        ],
    )

    chart_payload = json.dumps(
        _clean(
            {
                "gates": {k: gates[k] for k in GATE_KEYS},
                "conc": conc,
                "rr": rr,
                "pms_contested": pms_c,
                "pms_expected_vs_actual": pms_hl,
                "dists": list(dists),
                "channels": {d: DIST_CHANNEL.get(d, "") for d in dists},
                "default_focus": DEFAULT_FOCUS,
                "default_view": DEFAULT_VIEW,
                "default_gap_metric": DEFAULT_GAP_METRIC,
            }
        ),
        allow_nan=False,
    )

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1"/>
<title>Next analyses · Sales-to-dealer · Six DBs · Deep layers</title>
<style>
:root {{
  --navy:#1a2b4a; --terra:#c0552d; --bg:#f7f4ee; --card:#fff;
  --text:#222; --muted:#6b6256; --line:#d9d3c8;
}}
* {{ box-sizing:border-box; }}
body {{ margin:0; font-family:"Segoe UI",Helvetica,Arial,sans-serif; background:var(--bg); color:var(--text); }}
header {{ background:linear-gradient(155deg,#15233c 0%,#203759 60%,#2b4a78 100%); color:#eef1f6; padding:1.6rem 2rem; }}
header .eyebrow {{ font-size:0.72rem; letter-spacing:0.1em; text-transform:uppercase; opacity:0.85; }}
header h1 {{ font-family:Georgia,"Times New Roman",serif; margin:0.35rem 0 0.4rem; font-size:1.55rem; color:#fff; }}
header .rule {{ width:54px; height:3px; background:var(--terra); margin:0.5rem 0 0.7rem; }}
.badge {{ display:inline-block; padding:0.2rem 0.55rem; background:rgba(0,0,0,0.28); border-radius:4px; font-size:0.72rem; margin-right:0.35rem; }}
.wrap {{ max-width:1280px; margin:0 auto; padding:1rem 1.25rem 2.5rem; }}
.controls {{
  display:flex; flex-wrap:wrap; gap:0.85rem; align-items:flex-end;
  background:var(--card); border:1px solid var(--line); border-radius:8px;
  padding:0.85rem 1rem; margin-bottom:1rem; position:sticky; top:0; z-index:20;
}}
.controls label {{ display:flex; flex-direction:column; gap:0.25rem; font-size:0.72rem; color:var(--muted); text-transform:uppercase; letter-spacing:0.04em; }}
.controls select {{
  min-width:180px; padding:0.4rem 0.55rem; border:1px solid var(--line);
  border-radius:4px; background:#fff; color:var(--navy); font-size:0.9rem;
}}
.controls .hint {{ flex:1 1 220px; font-size:0.82rem; color:var(--muted); }}
section {{ background:var(--card); border:1px solid var(--line); border-radius:8px; padding:1rem 1.15rem; margin-bottom:1rem; overflow-x:auto; }}
section h2 {{ font-family:Georgia,serif; margin:0 0 0.55rem; font-size:1.12rem; color:var(--navy); border-bottom:2px solid var(--navy); padding-bottom:0.3rem; }}
section h2 .no {{ color:var(--terra); }}
section h3 {{ font-size:0.88rem; color:var(--muted); margin:0.7rem 0 0.4rem; }}
.callout {{ border-left:3px solid var(--terra); background:#fff; padding:0.7rem 0.9rem; margin-bottom:1rem; font-size:0.9rem; }}
.callout.amber {{ border-left-color:#c0552d; background:#fff3d6; color:#222; }}
.parked {{ border-left-color:#888780; color:var(--muted); }}
.findings {{ margin:0; padding-left:1.1rem; }}
.findings li {{ margin:0.25rem 0; font-size:0.9rem; }}
.grid2 {{ display:grid; grid-template-columns:1fr 1fr; gap:1rem; }}
@media(max-width:900px){{ .grid2{{ grid-template-columns:1fr; }} }}
.chart-box {{ position:relative; width:100%; height:320px; }}
.chart-box.tall {{ height:400px; }}
.tbl {{ width:100%; border-collapse:collapse; font-size:0.78rem; }}
.tbl th {{ background:var(--navy); color:#fff; padding:0.4rem 0.45rem; text-align:left; white-space:nowrap; font-size:0.7rem; text-transform:uppercase; }}
.tbl td {{ padding:0.35rem 0.45rem; border-bottom:0.5px solid var(--line); }}
.tbl tbody tr:nth-child(even) {{ background:#f7f4ee; }}
.muted {{ color:var(--muted); font-size:0.82rem; }}
.kpi-row {{ display:flex; flex-wrap:wrap; gap:0.55rem; margin-bottom:0.8rem; }}
.kpi {{ flex:1 1 150px; background:var(--bg); border-left:4px solid var(--terra); padding:0.55rem 0.75rem; border-radius:4px; position:relative; cursor:help; }}
.kpi .val {{ font-size:1.05rem; font-weight:700; color:var(--navy); }}
.kpi .lbl {{ font-size:0.7rem; color:var(--muted); }}
.kpi .tip {{
  display:none; position:absolute; left:0; top:100%; z-index:30; min-width:220px;
  background:#15233c; color:#f7f4ee; font-size:0.75rem; padding:0.55rem 0.7rem;
  border-radius:4px; border-top:3px solid var(--terra); margin-top:4px;
}}
.kpi:hover .tip {{ display:block; }}
.qty-toggle {{ display:flex; flex-direction:row; align-items:center; gap:0.4rem; font-size:0.82rem; color:var(--muted); text-transform:none; letter-spacing:0; }}
.qty-toggle input {{ margin:0; }}
.panel-hidden {{ display:none !important; }}
footer {{ text-align:center; color:var(--muted); font-size:0.72rem; padding:1rem; }}
</style>
</head>
<body>
<header>
  <div class="eyebrow">ISZE · Sales-to-dealer · Deep layers (GPS + PMS + AIM)</div>
  <h1>Six-DB pack — Core in euros · GPS + PMS layers</h1>
  <div class="rule"></div>
  <span class="badge">Meeting pack · DATA AS-OF CY{YEAR}</span>
  <span class="badge">Focus default: Core (ex gaskets/bolts)</span>
  <span class="badge">IUK = LCV · ITUK = CV</span>
</header>
<div class="wrap">
  <div class="callout">
    Language: <strong>sales-to-dealer</strong> (DB→DLR). Headline numbers are <strong>euros</strong>:
    sales-to-dealer proxy € (qty × median ISZE ASP) vs billing invoice €.
    Qty is a diagnostic toggle — gaskets/bolts inflate units. Default gate is <strong>Core</strong>
    (Hardware &amp; consumables + gasket/seal/bolt/fastener excluded from ranking).
    Consumables is a diagnostic focus, not the landing view.
    PMS headline = <strong>total capture</strong>. Not a Monday home.
  </div>
  <div class="callout amber">
    GREECE and ITUK have no 2026 sales-to-dealer file in this pack — CY2025 still paints.
    Duncan dealer × PN × month is not required for this grain.
  </div>

  <div class="kpi-row" id="heroKpis">
    <div class="kpi"><div class="val">{_pct(top.get('contested_bvp_capture'))}</div><div class="lbl">{_e(top.get('distributor_code') or 'Top')} BVP capture (Core)</div>
      <div class="tip">Core BVP capture = BVP StD proxy € ÷ (BVP + contested genuine) basket. CY{YEAR}. Total capture, not genuine-only.</div></div>
    <div class="kpi"><div class="val">{_pct(floor.get('contested_bvp_capture'))}</div><div class="lbl">{_e(floor.get('distributor_code') or 'Floor')} BVP capture (Core)</div>
      <div class="tip">Floor of the six-DB Core ranking. IUK park is LCV, never trucks.</div></div>
    <div class="kpi"><div class="val">{_pct(uti_gap.get('eur_gap_pct_of_billing')) if uti_gap else '—'}</div><div class="lbl">UTI StD vs billing €</div>
      <div class="tip">Core gate: sales-to-dealer proxy € vs ISZE invoice €. Negative = dealers moved less € than billed.</div></div>
  </div>

  <div class="controls">
    <label>Metric focus
      <select id="metricFocus" aria-label="Metric focus">
        <option value="overall">Overall (context)</option>
        <option value="core" selected>Core (default ranking)</option>
        <option value="consumables">Consumables only (diagnostic)</option>
        <option value="pms">PMS service items</option>
      </select>
    </label>
    <label>View
      <select id="viewMode" aria-label="View mode">
        <option value="gap">Gap — billing vs sales-to-dealer €</option>
        <option value="gps" selected>GPS — € per UIO</option>
        <option value="pms">PMS — filters / brakes / clutch</option>
      </select>
    </label>
    <label class="qty-toggle">
      <input type="checkbox" id="showQtyGap"/> Qty diagnostic (never the landing axis)
    </label>
    <div class="hint" id="controlHint">Landing: Core · GPS €/UIO · gap in €. PMS filters/brakes/clutch stay on this page. IUK = LCV park.</div>
  </div>

  <section>
    <h2><span class="no">0</span> Pointed findings</h2>
    <ul class="findings">{findings_html}</ul>
  </section>

  <div class="grid2" id="panelGapRank">
    <section id="secGap">
      <h2><span class="no">1</span> Billing vs sales-to-dealer gap <span class="muted" id="gapGateLabel">(Core · €)</span></h2>
      <div class="chart-box"><canvas id="cGap" aria-label="Euro gap by DB"></canvas></div>
      <div id="gapTblWrap">{gap_tbl}</div>
      <p class="muted" id="gapFoot">Headline = proxy € minus invoice €. Qty inflates on gaskets/bolts — use the Qty diagnostic checkbox only. Gap ≠ inventory.</p>
    </section>
    <section id="secRank">
      <h2><span class="no">2</span> BVP capture ranking <span class="muted" id="rankGateLabel">(Core)</span></h2>
      <div class="chart-box"><canvas id="cCap" aria-label="Contested BVP capture by DB"></canvas></div>
      <div id="rankTblWrap">{rank_tbl}</div>
    </section>
  </div>

  <section id="secGps">
    <h2><span class="no">3</span> GPS-style € per UIO <span class="muted" id="gpsGateLabel">(Core)</span></h2>
    <div class="chart-box"><canvas id="cSpu" aria-label="Euro per vehicle StD vs billing GPS"></canvas></div>
    <div id="gpsTblWrap">{gps_tbl}</div>
    <p class="muted">Dealer GPS-style proxy = gated StD proxy € ÷ UIO. Billing GPS = gated invoice € ÷ UIO.
    Channels: ITUK=CV · UTI=CV · <strong>IUK=LCV</strong> · IRELAND=CV+LCV · PORTUGAL=CV+LCV · GREECE=CV+LCV. Never label IUK as trucks.</p>
  </section>

  <section id="secPms">
    <h2><span class="no">4</span> PMS layers — filters, brakes, clutch (€)</h2>
    <p class="muted">PRISM expected is unit-based (UIO × svc/yr × factor). Chart uses expected € = expected qty × billing avg selling price, beside billing actual € and sales-to-dealer proxy €. Headline cats: oil / fuel / air filters, brake pad/shoe/rotor, clutch kit/disc/plate. Primary capture = total, not genuine-only.</p>
    <div class="chart-box tall"><canvas id="cPmsEva" aria-label="PMS expected vs actual euros"></canvas></div>
    {pms_eva_tbl}
    <h3>Contested basket BVP share (sales-to-dealer mix inside PMS categories)</h3>
    <div class="chart-box tall"><canvas id="cPmsMix" aria-label="PMS BVP share by DB"></canvas></div>
    {pms_mix_tbl}
  </section>

  <section id="secAim">
    <h2><span class="no">4b</span> AIM L1 — sales-to-dealer proxy € (Core)</h2>
    <p class="muted">Deeper AIM layer on the same page. Hardware &amp; consumables are excluded under Core. Switch focus to Consumables to see that basket in € (still not qty-first).</p>
    <div class="chart-box tall"><canvas id="cAim" aria-label="AIM L1 proxy euros"></canvas></div>
    <div id="aimTblWrap">{aim_tbl}</div>
  </section>

  <div class="grid2">
    <section>
      <h2><span class="no">5</span> PN concentration</h2>
      <div class="chart-box"><canvas id="cConc" aria-label="Top10 qty share"></canvas></div>
      {conc_tbl}
    </section>
    <section>
      <h2><span class="no">6</span> 2026 run-rate</h2>
      <div class="kpi-row">
        <div class="kpi"><div class="val">PT · IE · IUK · UTI</div><div class="lbl">Have 2026 sales-to-dealer YTD</div></div>
        <div class="kpi"><div class="val">ITUK · Greece</div><div class="lbl">No 2026 StD — billing only</div></div>
      </div>
      <div class="chart-box tall"><canvas id="cRr" aria-label="2026 run-rate"></canvas></div>
      {rr_tbl}
    </section>
  </div>

  <section>
    <h2><span class="no">7</span> ITUK dealer grain</h2>
    <div class="grid2">
      <div><h3>Largest dealers by proxy €</h3>{ituk_top}</div>
      <div><h3>Capture leaders &amp; laggards (≥ €20k)</h3>{ituk_cap}</div>
    </div>
  </section>
  <div class="callout parked"><strong>8 · Stock / loading — PARKED.</strong></div>
</div>
<footer>
  Sources: sales_fact · dealer_sellout_long_* · aim_pn_classification · pms_capture_by_db_year · gps_spu · rebuild: build_next_analyses_std.py
</footer>
<script>{chart_src}</script>
<script type="application/json" id="chart-data">{chart_payload}</script>
<script>
(function(){{
  if (typeof Chart === 'undefined') return;
  const D = JSON.parse(document.getElementById('chart-data').textContent);
  const ink = '#52514e', grid = '#e1e0d9';
  const order = D.dists;
  const ch = D.channels || {{}};
  const axisLabel = (d) => ch[d] ? (d + ' (' + ch[d] + ')') : d;
  const eur = (v) => v==null ? '—' : ('€' + Math.round(v).toLocaleString('en-GB'));
  const pct = (v) => v==null ? '—' : ((v*100).toFixed(1) + '%');
  const fmt = (v) => v==null ? '—' : Math.round(v).toLocaleString('en-GB');

  let focus = D.default_focus || 'core';
  let view = D.default_view || 'gps';
  let qtyGap = false;
  const charts = {{}};

  function gateData() {{
    if (focus === 'pms') return D.gates.core;
    return D.gates[focus] || D.gates.core;
  }}

  function renderGapTbl(rows) {{
    let h = "<table class='tbl'><thead><tr><th>DB</th><th>Channel</th><th>StD proxy €</th><th>Billing invoice €</th><th>€ gap</th><th>€ gap %</th><th>Cons. share</th><th>StD qty</th><th>Bill qty</th></tr></thead><tbody>";
    for (const r of rows) {{
      h += "<tr><td>"+r.distributor_code+"</td><td>"+(r.uio_channel||ch[r.distributor_code]||'')+"</td><td>"+eur(r.std_proxy_eur)+"</td><td>"+eur(r.billing_invoice_eur)+"</td><td>"+eur(r.eur_gap_proxy_minus_invoice)+"</td><td>"+pct(r.eur_gap_pct_of_billing)+"</td><td>"+pct(r.consumables_share_of_std_proxy)+"</td><td>"+fmt(r.std_qty)+"</td><td>"+fmt(r.billing_qty)+"</td></tr>";
    }}
    return h + "</tbody></table>";
  }}
  function renderRankTbl(rows) {{
    let h = "<table class='tbl'><thead><tr><th>Rank</th><th>DB</th><th>Channel</th><th>BVP capture</th><th>BVP mix</th><th>Proxy €</th><th>€/vehicle</th><th>Cons. share</th></tr></thead><tbody>";
    for (const r of rows) {{
      h += "<tr><td>"+r.rank_by_capture+"</td><td>"+r.distributor_code+"</td><td>"+(r.uio_channel||'')+"</td><td>"+pct(r.contested_bvp_capture)+"</td><td>"+pct(r.bvp_pct)+"</td><td>"+eur(r.proxy_eur)+"</td><td>"+eur(r.proxy_eur_per_vehicle)+"</td><td>"+pct(r.consumables_share_of_std_proxy)+"</td></tr>";
    }}
    return h + "</tbody></table>";
  }}
  function renderGpsTbl(rows) {{
    let h = "<table class='tbl'><thead><tr><th>DB</th><th>Channel</th><th>UIO</th><th>StD proxy €/vehicle</th><th>Billing GPS €/vehicle</th><th>Cons. share</th></tr></thead><tbody>";
    for (const r of rows) {{
      h += "<tr><td>"+r.distributor_code+"</td><td>"+(r.uio_channel||'')+"</td><td>"+fmt(r.uio_units)+"</td><td>"+eur(r.std_proxy_eur_per_vehicle)+"</td><td>"+eur(r.billing_gps_eur_per_vehicle)+"</td><td>"+pct(r.consumables_share_of_std_proxy)+"</td></tr>";
    }}
    return h + "</tbody></table>";
  }}
  function renderAimTbl(rows) {{
    let h = "<table class='tbl'><thead><tr><th>AIM L1</th>"+order.map(d=>"<th>"+d+"</th>").join("")+"<th>Total proxy €</th></tr></thead><tbody>";
    for (const r of (rows||[]).slice(0,8)) {{
      h += "<tr><td>"+(r.aim_l1||'')+"</td>";
      for (const d of order) h += "<td>"+eur(r[d+'_proxy_eur'])+"</td>";
      h += "<td>"+eur(r.total_proxy_eur)+"</td></tr>";
    }}
    return h + "</tbody></table>";
  }}

  function destroy(id) {{ if (charts[id]) {{ charts[id].destroy(); delete charts[id]; }} }}

  function paintCharts() {{
    const G = gateData();
    const labelsCh = order.map(axisLabel);
    const by = (arr) => Object.fromEntries(arr.map(r => [r.distributor_code, r]));
    const gap = by(G.gap), rank = G.rank, gps = by(G.gps);
    const C = by(D.conc), RR = by(D.rr);
    const gateWord = focus === 'pms' ? 'Core' : (focus.charAt(0).toUpperCase()+focus.slice(1));
    const gapAxis = qtyGap ? 'qty' : 'eur';
    document.getElementById('gapGateLabel').textContent = '(' + gateWord + ' · ' + (qtyGap ? 'qty diagnostic' : '€') + ')';
    document.getElementById('rankGateLabel').textContent = '(' + gateWord + ')';
    document.getElementById('gpsGateLabel').textContent = '(' + gateWord + ')';
    document.getElementById('gapTblWrap').innerHTML = renderGapTbl(G.gap);
    document.getElementById('rankTblWrap').innerHTML = renderRankTbl(G.rank);
    document.getElementById('gpsTblWrap').innerHTML = renderGpsTbl(G.gps);
    const aimWrap = document.getElementById('aimTblWrap');
    if (aimWrap) aimWrap.innerHTML = renderAimTbl(G.aim_l1 || []);

    const gapVals = order.map(d => qtyGap ? ((gap[d]||{{}}).qty_gap||0) : ((gap[d]||{{}}).eur_gap_proxy_minus_invoice||0));
    destroy('cGap');
    charts.cGap = new Chart(document.getElementById('cGap'), {{
      type:'bar',
      data:{{ labels:labelsCh, datasets:[{{
        label: qtyGap ? 'Qty gap (StD − billing) diagnostic' : '€ gap (StD proxy − billing invoice)',
        data:gapVals,
        backgroundColor:gapVals.map(v => v >= 0 ? '#2a78d6' : '#e24b4a'),
        borderRadius:4, barThickness:22
      }}]}},
      options:{{ responsive:true, maintainAspectRatio:false,
        plugins:{{ legend:{{ display:false }} }},
        scales:{{
          x:{{ ticks:{{ color:ink, maxRotation:45 }}, grid:{{ display:false }} }},
          y:{{ ticks:{{ color:ink, callback: v => qtyGap ? v : ('€'+Math.round(v).toLocaleString('en-GB')) }},
              grid:{{ color:grid }}, title:{{ display:true, text: qtyGap ? 'Qty units (diagnostic)' : 'Euros', color:ink }} }}
        }}
      }}
    }});

    destroy('cCap');
    const rankSorted = [...rank].sort((a,b)=>(b.contested_bvp_capture||0)-(a.contested_bvp_capture||0));
    charts.cCap = new Chart(document.getElementById('cCap'), {{
      type:'bar',
      data:{{ labels:rankSorted.map(r=>axisLabel(r.distributor_code)), datasets:[
        {{ label:'Contested BVP capture %', data:rankSorted.map(r=>(r.contested_bvp_capture||0)*100), backgroundColor:'#c0552d', borderRadius:4, barThickness:18 }},
        {{ label:'BVP mix %', data:rankSorted.map(r=>(r.bvp_pct||0)*100), backgroundColor:'#85b7eb', borderRadius:4, barThickness:18 }}
      ]}},
      options:{{ indexAxis:'y', responsive:true, maintainAspectRatio:false,
        plugins:{{ legend:{{ position:'bottom', labels:{{ color:ink }} }} }},
        scales:{{
          x:{{ max:100, ticks:{{ color:ink }}, grid:{{ color:grid }} }},
          y:{{ ticks:{{ color:ink }}, grid:{{ display:false }} }}
        }}
      }}
    }});

    destroy('cSpu');
    charts.cSpu = new Chart(document.getElementById('cSpu'), {{
      type:'bar',
      data:{{ labels:labelsCh, datasets:[
        {{ label:'StD proxy €/vehicle', data:order.map(d=>(gps[d]||{{}}).std_proxy_eur_per_vehicle||0), backgroundColor:'#c0552d', borderRadius:4, barThickness:18 }},
        {{ label:'Billing GPS €/vehicle', data:order.map(d=>(gps[d]||{{}}).billing_gps_eur_per_vehicle||0), backgroundColor:'#2a78d6', borderRadius:4, barThickness:18 }}
      ]}},
      options:{{ responsive:true, maintainAspectRatio:false,
        plugins:{{ legend:{{ position:'bottom', labels:{{ color:ink }} }} }},
        scales:{{
          x:{{ ticks:{{ color:ink, maxRotation:45 }}, grid:{{ display:false }} }},
          y:{{ ticks:{{ color:ink }}, grid:{{ color:grid }}, title:{{ display:true, text:'€ per vehicle (UIO)', color:ink }} }}
        }}
      }}
    }});

    destroy('cConc');
    charts.cConc = new Chart(document.getElementById('cConc'), {{
      type:'bar',
      data:{{ labels:labelsCh, datasets:[
        {{ label:'StD top-10 qty share %', data:order.map(d=>((C[d]||{{}}).std_top10_qty_share||0)*100), backgroundColor:'#2a78d6', borderRadius:4, barThickness:18 }},
        {{ label:'Billing top-10 qty share %', data:order.map(d=>((C[d]||{{}}).billing_top10_qty_share||0)*100), backgroundColor:'#888780', borderRadius:4, barThickness:18 }}
      ]}},
      options:{{ responsive:true, maintainAspectRatio:false,
        plugins:{{ legend:{{ position:'bottom', labels:{{ color:ink }} }} }},
        scales:{{
          x:{{ ticks:{{ color:ink, maxRotation:45 }}, grid:{{ display:false }} }},
          y:{{ max:60, ticks:{{ color:ink }}, grid:{{ color:grid }} }}
        }}
      }}
    }});

    destroy('cRr');
    charts.cRr = new Chart(document.getElementById('cRr'), {{
      type:'bar',
      data:{{ labels:labelsCh, datasets:[
        {{ label:'StD proxy € RR', data:order.map(d => (RR[d]&&RR[d].has_2026_std) ? (RR[d].std_runrate_proxy_eur||0) : null), backgroundColor:'#c0552d', borderRadius:4, barThickness:18 }},
        {{ label:'Billing € RR', data:order.map(d => (RR[d]||{{}}).billing_runrate_eur||0), backgroundColor:'#2a78d6', borderRadius:4, barThickness:18 }}
      ]}},
      options:{{ responsive:true, maintainAspectRatio:false,
        plugins:{{ legend:{{ position:'bottom', labels:{{ color:ink }} }} }},
        scales:{{
          x:{{ ticks:{{ color:ink, maxRotation:45 }}, grid:{{ display:false }} }},
          y:{{ ticks:{{ color:ink, callback:v=>'€'+(v/1e6).toFixed(1)+'m' }}, grid:{{ color:grid }} }}
        }}
      }}
    }});

    const pms = D.pms_expected_vs_actual || [];
    const sumField = (r, field) => order.reduce((s,d) => s + (r[d+'_'+field] || 0), 0);
    destroy('cPmsEva');
    charts.cPmsEva = new Chart(document.getElementById('cPmsEva'), {{
      type:'bar',
      data:{{ labels:pms.map(r => r.category_label || r.pms_category), datasets:[
        {{ label:'Expected € (qty × avg SP)', data:pms.map(r => sumField(r,'expected_eur')), backgroundColor:'#888780', borderRadius:3, barThickness:12 }},
        {{ label:'Billing actual €', data:pms.map(r => sumField(r,'billing_actual_eur')), backgroundColor:'#2a78d6', borderRadius:3, barThickness:12 }},
        {{ label:'Sales-to-dealer actual €', data:pms.map(r => sumField(r,'std_actual_eur')), backgroundColor:'#c0552d', borderRadius:3, barThickness:12 }}
      ] }},
      options:{{ indexAxis:'y', responsive:true, maintainAspectRatio:false,
        plugins:{{ legend:{{ position:'bottom', labels:{{ color:ink, boxWidth:12 }} }} }},
        scales:{{
          x:{{ ticks:{{ color:ink, callback:v=>'€'+Math.round(v).toLocaleString('en-GB') }}, grid:{{ color:grid }}, title:{{ display:true, text:'Euros (six-DB sum)', color:ink }} }},
          y:{{ ticks:{{ color:ink }}, grid:{{ display:false }} }}
        }}
      }}
    }});

    const mix = D.pms_contested || [];
    destroy('cPmsMix');
    charts.cPmsMix = new Chart(document.getElementById('cPmsMix'), {{
      type:'bar',
      data:{{ labels:mix.map(r => r.category_label || r.pms_category), datasets: order.map((d,i)=>({{
        label:axisLabel(d)+' BVP share %',
        data:mix.map(r => r[d+'_bvp_share']==null ? null : r[d+'_bvp_share']*100),
        backgroundColor:['#c0552d','#2a78d6','#1d9e75','#eda100','#888780','#85b7eb'][i%6],
        borderRadius:3, barThickness:8
      }})) }},
      options:{{ indexAxis:'y', responsive:true, maintainAspectRatio:false,
        plugins:{{ legend:{{ position:'bottom', labels:{{ color:ink, boxWidth:12 }} }} }},
        scales:{{
          x:{{ max:100, ticks:{{ color:ink }}, grid:{{ color:grid }} }},
          y:{{ ticks:{{ color:ink }}, grid:{{ display:false }} }}
        }}
      }}
    }});

    const aimRows = (G.aim_l1 || []).slice(0,8);
    destroy('cAim');
    if (document.getElementById('cAim')) {{
      charts.cAim = new Chart(document.getElementById('cAim'), {{
        type:'bar',
        data:{{ labels:aimRows.map(r => r.aim_l1), datasets:[{{
          label:'Sales-to-dealer proxy €', data:aimRows.map(r => r.total_proxy_eur||0),
          backgroundColor:'#1a2b4a', borderRadius:4, barThickness:14
        }}] }},
        options:{{ indexAxis:'y', responsive:true, maintainAspectRatio:false,
          plugins:{{ legend:{{ display:false }} }},
          scales:{{
            x:{{ ticks:{{ color:ink, callback:v=>'€'+Math.round(v).toLocaleString('en-GB') }}, grid:{{ color:grid }}, title:{{ display:true, text:'Euros', color:ink }} }},
            y:{{ ticks:{{ color:ink }}, grid:{{ display:false }} }}
          }}
        }}
      }});
    }}
  }}

  function applyPanels() {{
    const pmsFocus = (focus === 'pms') || (view === 'pms');
    document.getElementById('panelGapRank').classList.remove('panel-hidden');
    document.getElementById('secGap').classList.toggle('panel-hidden', false);
    document.getElementById('secRank').classList.toggle('panel-hidden', false);
    document.getElementById('secGps').classList.toggle('panel-hidden', view === 'gap' && !pmsFocus);
    document.getElementById('secPms').classList.remove('panel-hidden');
    const aim = document.getElementById('secAim');
    if (aim) aim.classList.remove('panel-hidden');
    const hints = {{
      overall: 'Overall = all PNs in €. Core remains the ranking default.',
      core: 'Core excludes AIM consumables (Hardware & consumables + gasket/seal/bolt/fastener). Charts in €.',
      consumables: 'Consumables diagnostic in € (not qty). Gaskets/bolts belong here, not on the Core landing.',
      pms: 'PMS filters / brakes / clutch: expected € vs billing € vs sales-to-dealer €. Qty expected is the PRISM unit denom.'
    }};
    document.getElementById('controlHint').textContent = hints[focus] || '';
  }}

  document.getElementById('metricFocus').addEventListener('change', function(){{
    focus = this.value;
    if (focus === 'pms') {{ view = 'pms'; document.getElementById('viewMode').value = 'pms'; }}
    applyPanels(); paintCharts();
  }});
  document.getElementById('viewMode').addEventListener('change', function(){{
    view = this.value;
    applyPanels(); paintCharts();
  }});
  document.getElementById('showQtyGap').addEventListener('change', function(){{
    qtyGap = !!this.checked;
    paintCharts();
  }});

  applyPanels();
  paintCharts();
}})();
</script>
</body>
</html>
"""



def write_open_cmd() -> None:
    OUT_CMD.write_text(
        "@echo off\r\n"
        "start \"\" \"%~dp0Next_Analyses_Sales_to_Dealer_SixDB.html\"\r\n",
        encoding="utf-8",
    )


def main() -> None:
    if not AIM_JSON.exists():
        raise SystemExit(f"Missing AIM/GPS JSON: {AIM_JSON} — run build_dealer_sellout_aim_gps.py first")

    aim = load_aim()
    dists = tuple(aim.get("distributors") or DIST_ORDER)
    uio = load_uio(dists)
    for k, v in (aim.get("uio_units") or {}).items():
        if v:
            uio[k] = float(v)

    print("loading dimensions / ASP / billing…")
    dim, xref, desc = load_dimension_and_xref()
    xref_g = set(xref["genuine_pn"].dropna().str.strip())
    xref_b = set(xref["bvp_pn"].dropna().str.strip())
    asp25 = load_asp(YEAR, dists)
    bill25 = load_billing_year(YEAR, dists)

    print("gated layers (overall / core / consumables)…")
    gated = build_gated_bundle(
        dists, asp25, dim, desc, xref, xref_g, xref_b, uio, bill25
    )
    gps_flat = gated.pop("_gps_flat")

    print("legacy overall gap (AIM JSON) + contested PMS mix…")
    gap_legacy = build_gap_legacy(aim)
    pms_contested = build_pms_contested(aim)

    print("PMS expected vs actual…")
    pms_eva = build_pms_expected_vs_actual(dists, dim, desc, xref, asp25)

    print("PN concentration…")
    conc = build_concentration(dists, asp25, dim, desc, xref)

    print("2026 run-rate…")
    rr = build_runrate_2026(asp25, xref_g, xref_b, dim, desc, xref, uio)

    print("ITUK dealers…")
    ituk = build_ituk_dealers()

    # Default CSVs use Core ranking / GPS
    core = gated["core"]
    payload = {
        "generated": str(date.today()),
        "framework": "sales-to-dealer-analytics-framework_deeplayers",
        "default_focus": DEFAULT_FOCUS,
        "default_view": DEFAULT_VIEW,
        "distributors": list(dists),
        "parked": ["stock_loading"],
        "gates": {k: gated[k] for k in GATE_KEYS},
        "billing_vs_std_gap": core["gap"],
        "billing_vs_std_gap_overall_aim": gap_legacy,
        "bvp_country_rank": core["rank"],
        "pn_concentration": conc,
        "eur_per_vehicle": core["gps"],
        "runrate_2026": rr,
        "pms_contested": pms_contested,
        "pms_expected_vs_actual": pms_eva,
        "ituk_dealers": ituk,
        "consumables_gate": {
            "aim_l1": CONSUMABLES_L1,
            "aim_l2_l3_terms": ["gasket", "seal", "bolt", "fastener"],
            "default_ranking": "core",
        },
        "scope_note": (
            "Deep layers: AIM consumables gate · GPS gated €/UIO · PMS expected-vs-actual. "
            "Default ranking = Core (ex-consumables). Gap headline = proxy € vs invoice €. "
            "Channels: ITUK=CV, UTI=CV, IUK=LCV, IRELAND=CV+LCV, PORTUGAL=CV+LCV, GREECE=CV+LCV. "
            "IUK never labelled trucks. Warranty untouched. Stock/loading parked."
        ),
        "uio_channel": dict(DIST_CHANNEL),
    }
    payload["findings_bullets"] = pointed_bullets(payload)

    pd.DataFrame(core["gap"]).to_csv(OUT_GAP, index=False)
    pd.DataFrame(core["rank"]).to_csv(OUT_RANK, index=False)
    pd.DataFrame(conc).to_csv(OUT_CONC, index=False)
    pd.DataFrame(core["gps"]).to_csv(OUT_SPU, index=False)
    pd.DataFrame(rr).to_csv(OUT_RR, index=False)
    pd.DataFrame(pms_contested).to_csv(OUT_PMS, index=False)
    pd.DataFrame(pms_eva).to_csv(OUT_PMS_EVA, index=False)
    pd.DataFrame(gps_flat).to_csv(OUT_GPS_GATED, index=False)
    pd.DataFrame(ituk).to_csv(OUT_ITUK, index=False)

    findings = findings_text(payload)
    OUT_FINDINGS.write_text(findings, encoding="utf-8")

    OUT_JSON.write_text(json.dumps(_clean(payload), indent=2, default=str), encoding="utf-8")
    OUT_HTML.parent.mkdir(parents=True, exist_ok=True)
    OUT_HTML.write_text(build_html(payload), encoding="utf-8")
    write_open_cmd()

    html_txt = OUT_HTML.read_text(encoding="utf-8")
    cdn_hits = len(re.findall(r'src=["\']https?://', html_txt))
    print(f"ok: {OUT_HTML} (cdn src hits={cdn_hits})")
    print(f"ok: {OUT_CMD}")
    print(f"ok: {OUT_JSON}")
    for p in (
        OUT_GAP,
        OUT_RANK,
        OUT_CONC,
        OUT_SPU,
        OUT_RR,
        OUT_PMS,
        OUT_PMS_EVA,
        OUT_GPS_GATED,
        OUT_ITUK,
        OUT_FINDINGS,
    ):
        print(f"ok: {p}")
    print("\n--- findings ---")
    for b in payload["findings_bullets"]:
        print("-", b.encode("ascii", "replace").decode("ascii"))


if __name__ == "__main__":
    main()

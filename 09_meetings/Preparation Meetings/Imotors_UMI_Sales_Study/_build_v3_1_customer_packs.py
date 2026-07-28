# -*- coding: utf-8 -*-
"""
V3.1 customer-facing deep packs — one HTML/Excel/PDF per customer (I Motors, UMI).

V3.1 (Jerome critique): restore V2 source-mix; GPS now-vs-past only (no peer countries);
PMS never silent-cap — diagnose >100% / exclude with reason; family share % only;
no PR00 wording; one network-avg sales compare; PBI vs ISZE billing reconcile.
See CUSTOMER_PACK_RULES.md.
"""
from __future__ import annotations

import json
import math
import re
from datetime import date
from pathlib import Path
from string import Template

import pandas as pd
import pyarrow.dataset as ds
from openpyxl import Workbook
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter

OUT = Path(__file__).resolve().parent
V3 = OUT / "V3"
ROOT = OUT.parents[2]
STUDY = json.loads((OUT / "study_data.json").read_text(encoding="utf-8"))
CHART_JS = (OUT / "assets" / "chart.umd.min.js").read_text(encoding="utf-8")
CHART_JS = re.sub(r"//# sourceMappingURL=.*", "", CHART_JS)

PARQUET = ROOT / "01_data" / "00_derived" / "sales_fact.parquet"
SAP_MAP = ROOT / "03_analytics" / "Isuzu" / "prism" / "data" / "sap_sold_to_mapping.csv"
MASTER = ROOT / "03_analytics" / "Isuzu" / "prism" / "data" / "distributor_master_mapping.csv"
CATALOG = ROOT / "01_data" / "00_derived" / "parts_catalog_dimension.csv"
GPS_CSV = ROOT / "01_data" / "00_derived" / "gps_spu_by_distributor.csv"
PMS_CAP = (
    ROOT
    / "03_analytics"
    / "Isuzu"
    / "prism"
    / "evidence-app"
    / "data"
    / "derived"
    / "pms_capture_by_db_year.csv"
)
IDS_ISR = ROOT / "01_data" / "90_INBOX" / "IDS_2026" / "rankings" / "Israel_dealer_ranking.xlsx"
IDS_PT = ROOT / "01_data" / "90_INBOX" / "IDS_2026" / "rankings" / "Portugal_dealer_ranking.xlsx"

NON_PART = {
    "TRANSPORT",
    "REBATE",
    "LATE PAYMENT INTEREST",
    "DISRACK01",
    "5874123810",
    "5874123811",
    "5874123812",
}

PMS_ASSUMPTION = (
    "Service-interval assumption (IML service schedule modelling): "
    "filters ≈ 1.25× per year; wear items ≈ 0.5× per year. "
    "Capture % = actual quantity ÷ expected demand under this schedule. "
    "Primary lens = total capture (genuine share is secondary)."
)

CUSTOMERS = {
    "IMOTORS": {
        "file_stem": "ISZE_Imotors_Deep_Study_V3.1",
        "title": "I Motors — Parts Sales Deep Study",
        "subtitle": "Portugal · customer briefing V3.1",
        "code": "PORTUGAL",
        "label": "I Motors",
        "country": "Portugal",
        "include_source": True,
        "include_lcv_saty_bench": False,
        "forbid_uti": False,
    },
    "UMI": {
        "file_stem": "ISZE_UMI_Deep_Study_V3.1",
        "title": "UMI — Parts Sales Deep Study",
        "subtitle": "Israel LCV · customer briefing V3.1",
        "code": "UMI",
        "label": "UMI",
        "country": "Israel",
        "include_source": True,  # V3.1: restore V2 JP/TH/LOCAL source chart
        "include_lcv_saty_bench": False,  # only ONE network compare (sales YoY)
        "forbid_uti": True,
    },
}


def money(x: float) -> float:
    return round(float(x or 0), 2)


def eur(x) -> str:
    v = float(x or 0)
    if abs(v) >= 1_000_000:
        return f"€{v / 1_000_000:.2f}M"
    if abs(v) >= 10_000:
        return f"€{v / 1000:.0f}K"
    return f"€{v:,.0f}"


def pct(x, digits=1) -> str:
    if x is None or (isinstance(x, float) and math.isnan(x)):
        return "n/a"
    return f"{100 * float(x):.{digits}f}%" if abs(float(x)) <= 1.5 else f"{float(x):.{digits}f}%"


def is_rebate_row(pn: str, desc: str) -> bool:
    u = (pn or "").upper().strip()
    d = (desc or "").upper()
    if u in NON_PART:
        return True
    if "REBATE" in u or "REBATE" in d:
        return True
    return False


def classify_family(pr00_family, pr00_group, desc: str) -> tuple[str, str]:
    """Return (family_bucket, group_label) for charts — never dump lubricants into fat Others."""
    fam = "" if pr00_family is None or (isinstance(pr00_family, float) and math.isnan(pr00_family)) else str(pr00_family).strip()
    grp = "" if pr00_group is None or (isinstance(pr00_group, float) and math.isnan(pr00_group)) else str(pr00_group).strip()
    if fam.lower() in ("nan", "none"):
        fam = ""
    if grp.lower() in ("nan", "none"):
        grp = ""
    d = (desc or "").upper()
    if not fam:
        if any(k in d for k in ("RIMULA", "RIM R", "RIMR", "TELLUS", "ENGINE OIL", "15W40", "10W40", "5W30")):
            return "Lubricants", "Engine / hydraulic oils"
        if any(k in d for k in ("FILTER",)):
            return "Filters (unmapped)", "Filter"
        return "Catalogue gap", "Unmapped PN"
    if fam.lower().startswith("other"):
        # Keep named PR00 group instead of collapsing to Others
        return (grp or "Review / misc"), (grp or fam)
    return fam, (grp or fam)


def load_sales() -> pd.DataFrame:
    sap = pd.read_csv(SAP_MAP).rename(columns={"sap_sold_to_pt": "sold_to_sap"})
    sap["sold_to_sap"] = pd.to_numeric(sap["sold_to_sap"], errors="coerce")
    cols = [
        "billing_date",
        "sold_to_sap",
        "part_number",
        "description",
        "billed_qty",
        "net_sales_value",
        "saty",
        "fig_key",
    ]
    df = ds.dataset(PARQUET).to_table(columns=cols).to_pandas()
    df["billing_date"] = pd.to_datetime(df["billing_date"])
    df["sold_to_sap"] = pd.to_numeric(df["sold_to_sap"], errors="coerce")
    df = df.merge(sap[["sold_to_sap", "distributor_code"]], on="sold_to_sap", how="left")
    df["part_number"] = df["part_number"].astype(str).str.strip()
    df["description"] = df["description"].fillna("").astype(str)
    df["saty"] = df["saty"].fillna("(blank)").astype(str)
    df["fig_key"] = df["fig_key"].fillna("(none)").astype(str)
    pn_u = df["part_number"].str.upper()
    desc_u = df["description"].str.upper()
    mask = pn_u.isin(NON_PART) | pn_u.str.contains("REBATE", na=False) | desc_u.str.contains("REBATE", na=False)
    df = df[~mask].copy()
    df["fiscal_year"] = df["billing_date"].dt.year.where(
        df["billing_date"].dt.month >= 4, df["billing_date"].dt.year - 1
    ).astype(int)
    df["ym"] = df["billing_date"].dt.to_period("M").astype(str)
    return df


def load_catalog() -> pd.DataFrame:
    cat = pd.read_csv(
        CATALOG,
        usecols=["part_number", "pr00_family", "pr00_group", "pms_category", "fig_key_label"],
        dtype=str,
        low_memory=False,
    )
    cat["part_number"] = cat["part_number"].astype(str).str.strip()
    return cat.drop_duplicates("part_number")


def ids_country_avg(path: Path) -> dict:
    import openpyxl

    wb = openpyxl.load_workbook(path, data_only=True, read_only=True)
    ws = wb[wb.sheetnames[0]]
    rows = list(ws.iter_rows(values_only=True))
    header = [str(c).strip() if c is not None else "" for c in rows[0]]
    # find points col
    idx_pts = next(i for i, h in enumerate(header) if "points" in h.lower())
    vals = []
    for r in rows[1:]:
        if not r or r[0] is None:
            continue
        name = str(r[0])
        if "total" in name.lower() or "average" in name.lower() or "country" in name.lower():
            # sometimes footer
            try:
                vals.append(float(r[idx_pts]))
            except Exception:
                pass
            continue
        try:
            # rank rows start with int
            if isinstance(r[0], (int, float)) or str(r[0]).isdigit():
                vals.append(float(r[idx_pts]))
            elif r[1] is not None and isinstance(r[idx_pts], (int, float)):
                vals.append(float(r[idx_pts]))
        except Exception:
            continue
    # Prefer explicit dealer rows: Rank is col0 numeric
    dealers = []
    for r in rows[1:]:
        if r and isinstance(r[0], (int, float)) and r[idx_pts] is not None:
            try:
                dealers.append(float(r[idx_pts]))
            except Exception:
                pass
    if not dealers:
        dealers = vals
    return {
        "n_dealers": len(dealers),
        "avg_pct": round(sum(dealers) / len(dealers), 2) if dealers else None,
        "max_pct": round(max(dealers), 2) if dealers else None,
        "min_pct": round(min(dealers), 2) if dealers else None,
    }


def gps_row(code: str, year: int = 2025) -> dict:
    g = pd.read_csv(GPS_CSV)
    r = g[(g["distributor_code"] == code) & (g["year"] == year)]
    if r.empty:
        return {}
    row = r.iloc[0]
    cap = row.get("gps_capture_vs_max")
    return {
        "year": year,
        "gps_pct": None if pd.isna(cap) else round(100 * float(cap), 1),
        "traffic_light": row.get("traffic_light_v9") or row.get("traffic_light"),
        "uio": int(float(row["uio_units"])) if not pd.isna(row["uio_units"]) else None,
        "spu_eur": round(float(row["spend_per_unit_eur"]), 1),
        "sales_eur": money(row["total_sales_eur"]),
        "max_spend_eur": None
        if pd.isna(row.get("max_spend_eur"))
        else money(row["max_spend_eur"]),
    }


def gps_time_series(code: str) -> list[dict]:
    """Now vs past capture % only — never peer countries.
    CY2024 uses sales / CY2025 max_spend as trend proxy when max_spend missing.
    CY2026 YTD shown as annualised run-rate (YTD×4 / max_spend_2026).
    """
    g = pd.read_csv(GPS_CSV)
    sub = g[g["distributor_code"] == code].set_index("year")
    out = []
    max_2025 = None
    if 2025 in sub.index and pd.notna(sub.loc[2025].get("max_spend_eur")):
        max_2025 = float(sub.loc[2025]["max_spend_eur"])
    # CY2024 proxy
    if 2024 in sub.index and max_2025:
        sales = float(sub.loc[2024]["total_sales_eur"])
        out.append(
            {
                "label": "CY2024",
                "gps_pct": round(100 * sales / max_2025, 1),
                "note": "trend proxy: CY2024 sales ÷ CY2025 max-spend target",
            }
        )
    if 2025 in sub.index and pd.notna(sub.loc[2025].get("gps_capture_vs_max")):
        out.append(
            {
                "label": "CY2025",
                "gps_pct": round(100 * float(sub.loc[2025]["gps_capture_vs_max"]), 1),
                "note": "verified capture vs max",
            }
        )
    if 2026 in sub.index and pd.notna(sub.loc[2026].get("max_spend_eur")):
        sales = float(sub.loc[2026]["total_sales_eur"])
        mx = float(sub.loc[2026]["max_spend_eur"])
        # YTD through ~Mar → annualise ×4
        run = 100 * (sales * 4) / mx if mx else None
        out.append(
            {
                "label": "CY2026 run-rate",
                "gps_pct": round(run, 1) if run is not None else None,
                "note": "YTD sales×4 ÷ CY2026 max-spend (pace, not final year)",
            }
        )
    return out


def network_fy_yoy(df: pd.DataFrame, segment: str = "lcv") -> float | None:
    """Single allowed benchmark: LCV (excl. UTI) or all-DB average FY YoY %."""
    master = pd.read_csv(MASTER)
    if segment == "lcv":
        codes = set(master.loc[master["segment_lcv"].astype(str).str.upper() == "YES", "distributor_code"])
        codes.discard("UTI")
    else:
        codes = set(master["distributor_code"].astype(str))
        codes.discard("UTI")
    sub = df[df["distributor_code"].isin(codes) & df["fiscal_year"].isin([2024, 2025])]
    if sub.empty:
        return None
    t24 = float(sub.loc[sub["fiscal_year"] == 2024, "net_sales_value"].sum())
    t25 = float(sub.loc[sub["fiscal_year"] == 2025, "net_sales_value"].sum())
    if t24 <= 0:
        return None
    return round(100 * (t25 - t24) / t24, 1)


def lcv_saty_bench(df: pd.DataFrame, fy: int = 2025) -> list[dict]:
    master = pd.read_csv(MASTER)
    lcv = set(master.loc[master["segment_lcv"].astype(str).str.upper() == "YES", "distributor_code"])
    lcv.discard("UTI")  # never blend UTI into UMI pack benchmark
    sub = df[(df["distributor_code"].isin(lcv)) & (df["fiscal_year"] == fy)]
    if sub.empty:
        return []
    tot = sub["net_sales_value"].sum() or 1
    rows = (
        sub.groupby("saty", as_index=False)["net_sales_value"]
        .sum()
        .sort_values("net_sales_value", ascending=False)
    )
    return [
        {"saty": r.saty, "share_pct": round(100 * float(r.net_sales_value) / float(tot), 1)}
        for r in rows.itertuples()
    ]


def pms_total_cats(code: str, year: int = 2025) -> dict:
    """Load total-line PMS categories with diagnosis — never silent-cap at 100%.

    Returns chart rows + footnotes / exclusions with reasons.
    """
    cap = pd.read_csv(PMS_CAP)
    scopes = cap.loc[(cap["distributor_code"] == code) & (cap["year"] == year), "scope"].dropna().unique().tolist()
    # Prefer DB-native scope: UMI = LCV_only; Portugal / CV = N75_only
    if code == "UMI":
        scope = "LCV_only" if "LCV_only" in scopes else (scopes[0] if scopes else "LCV_only")
    else:
        scope = "N75_only" if "N75_only" in scopes else (scopes[0] if scopes else "N75_only")

    sub = cap[
        (cap["distributor_code"] == code)
        & (cap["year"] == year)
        & (cap["line_type"] == "total")
        & (cap["scope"] == scope)
    ]
    # genuine split for brake_pad diagnosis
    gen = cap[
        (cap["distributor_code"] == code)
        & (cap["year"] == year)
        & (cap["line_type"] == "genuine")
        & (cap["scope"] == scope)
    ].set_index("pms_category")

    chart = []
    excluded = []
    footnotes = []
    for _, r in sub.iterrows():
        cat = r["pms_category"]
        label = r["category_label"] if pd.notna(r.get("category_label")) else cat
        rate = float(r["capture_rate"])
        pct = round(100 * rate, 1)
        exp = float(r["expected_qty"]) if pd.notna(r["expected_qty"]) else None
        act = float(r["actual_qty"]) if pd.notna(r["actual_qty"]) else None
        uio = float(r["uio_units"]) if pd.notna(r["uio_units"]) else None

        # Blower: known under-predicted interval (factor 0.25) — network often >>100%
        if cat == "blower_filter" and rate > 1.0:
            excluded.append(
                {
                    "category": label,
                    "raw_capture_pct": pct,
                    "reason": (
                        f"Excluded from chart: capture {pct}% (actual {act:.0f} vs expected {exp:.0f} on UIO {uio:.0f}). "
                        "Cabin/blower was modelled at 0.25 (wrong); network now uses 1.0 like other filters — "
                        "this is a model artefact, not evidence of 2× overselling."
                    ),
                }
            )
            continue

        row = {"category": label, "pms_category": cat, "capture_pct": pct, "expected_qty": exp, "actual_qty": act}
        chart.append(row)

        if cat == "brake_pad" and rate >= 0.80:
            g_pct = None
            if cat in gen.index:
                g_pct = round(100 * float(gen.loc[cat]["capture_rate"]), 1)
            footnotes.append(
                {
                    "category": label,
                    "text": (
                        f"Brake pad total capture {pct}% is near the model ceiling "
                        f"(actual {act:.0f} / expected {exp:.0f}, UIO {uio:.0f}, scope {scope}). "
                        f"Genuine-only is {g_pct}% — the headline is mix-led (genuine + BVP), not pure genuine saturation. "
                        "Wear factor 0.5×/yr is an assumption pending local confirmation; "
                        "pad-vs-set unit definition can also inflate %. Treat as 'verify', not a trophy."
                    ),
                }
            )
        elif rate > 1.0:
            footnotes.append(
                {
                    "category": label,
                    "text": (
                        f"{label} shows {pct}% (actual {act:.0f} / expected {exp:.0f}). "
                        "Above 100% usually means expected demand is too low (interval/UIO/scope) "
                        "or qty double-count — investigate before reading as overselling."
                    ),
                }
            )

    chart.sort(key=lambda x: x["capture_pct"])
    return {"scope": scope, "chart": chart, "excluded": excluded, "footnotes": footnotes}


def build_customer_pack(key: str, df: pd.DataFrame, cat: pd.DataFrame) -> dict:
    meta = CUSTOMERS[key]
    study = next(d for d in STUDY["distributors"] if d["key"] == key)
    code = meta["code"]
    g = df[df["distributor_code"] == code].copy()
    g = g.merge(cat, left_on="part_number", right_on="part_number", how="left", suffixes=("", "_cat"))

    fam_labels = []
    grp_labels = []
    for r in g.itertuples():
        f, gr = classify_family(getattr(r, "pr00_family", None), getattr(r, "pr00_group", None), r.description)
        fam_labels.append(f)
        grp_labels.append(gr)
    g["family_bucket"] = fam_labels
    g["group_label"] = grp_labels

    fy24 = g[g["fiscal_year"] == 2024]
    fy25 = g[g["fiscal_year"] == 2025]
    tot24 = float(fy24["net_sales_value"].sum())
    tot25 = float(fy25["net_sales_value"].sum())
    yoy = round(100 * (tot25 - tot24) / tot24, 1) if tot24 else None

    # monthly 24m (FY24+FY25)
    monthly = (
        g[g["fiscal_year"].isin([2024, 2025])]
        .groupby("ym", as_index=False)["net_sales_value"]
        .sum()
        .sort_values("ym")
    )
    monthly_rows = [{"ym": r.ym, "sales_eur": money(r.net_sales_value)} for r in monthly.itertuples()]

    # SaTy
    def saty_fy(sub, fy):
        s = sub[sub["fiscal_year"] == fy]
        t = float(s["net_sales_value"].sum()) or 1
        rows = s.groupby("saty", as_index=False)["net_sales_value"].sum().sort_values("net_sales_value", ascending=False)
        return [
            {"saty": r.saty, "sales_eur": money(r.net_sales_value), "share_pct": round(100 * float(r.net_sales_value) / t, 1)}
            for r in rows.itertuples()
        ]

    # PR00 group chart — top groups by FY25, with FY24 align
    def group_compare():
        a = fy24.groupby("group_label")["net_sales_value"].sum()
        b = fy25.groupby("group_label")["net_sales_value"].sum()
        # drop tiny catalogue-gap noise unless material
        keys = sorted(set(a.index) | set(b.index), key=lambda k: -float(b.get(k, 0)))
        rows = []
        for k in keys:
            e24 = float(a.get(k, 0))
            e25 = float(b.get(k, 0))
            if e25 < 0.01 * tot25 and e24 < 0.01 * tot24:
                continue
            rows.append(
                {
                    "group": k,
                    "fy24_eur": money(e24),
                    "fy25_eur": money(e25),
                    "fy24_share": round(100 * e24 / tot24, 1) if tot24 else 0,
                    "fy25_share": round(100 * e25 / tot25, 1) if tot25 else 0,
                    "yoy_pct": round(100 * (e25 - e24) / e24, 1) if e24 else None,
                }
            )
        return rows[:12]

    # family buckets FY25
    fam25 = (
        fy25.groupby("family_bucket")["net_sales_value"]
        .sum()
        .sort_values(ascending=False)
    )
    family_rows = [
        {"family": k, "sales_eur": money(v), "share_pct": round(100 * float(v) / tot25, 1)}
        for k, v in fam25.items()
        if float(v) / tot25 >= 0.005 or k != "Catalogue gap"
    ]

    # PN rankings FY24 / FY25
    def top_pn(sub, tot, n=20):
        rows = (
            sub.groupby(["part_number", "description"], as_index=False)["net_sales_value"]
            .sum()
            .sort_values("net_sales_value", ascending=False)
            .head(n)
        )
        out = []
        for i, r in enumerate(rows.itertuples(), 1):
            out.append(
                {
                    "rank": i,
                    "part_number": r.part_number,
                    "description": (r.description or "")[:60].strip(),
                    "sales_eur": money(r.net_sales_value),
                    "share_pct": round(100 * float(r.net_sales_value) / tot, 2) if tot else 0,
                }
            )
        return out

    # movers
    a = fy24.groupby(["part_number", "description"])["net_sales_value"].sum()
    b = fy25.groupby(["part_number", "description"])["net_sales_value"].sum()
    keys = set(a.index) | set(b.index)
    movers = []
    for k in keys:
        e24 = float(a.get(k, 0))
        e25 = float(b.get(k, 0))
        movers.append(
            {
                "part_number": k[0],
                "description": (k[1] or "")[:60].strip(),
                "fy24_eur": money(e24),
                "fy25_eur": money(e25),
                "delta_eur": money(e25 - e24),
            }
        )
    gainers = sorted(movers, key=lambda x: -x["delta_eur"])[:15]
    losers = sorted(movers, key=lambda x: x["delta_eur"])[:15]
    silent = [
        m
        for m in sorted(movers, key=lambda x: -x["fy24_eur"])
        if m["fy24_eur"] >= 2000 and m["fy25_eur"] <= 0.05 * m["fy24_eur"]
    ][:12]

    # concentration
    def concentration(sub, tot):
        s = (
            sub.groupby("part_number")["net_sales_value"]
            .sum()
            .sort_values(ascending=False)
        )
        if tot <= 0 or s.empty:
            return {}
        cum = s.cumsum()
        pn80 = int((cum < 0.8 * tot).sum() + 1)
        return {
            "top10_share_pct": round(100 * float(s.head(10).sum()) / tot, 1),
            "top25_share_pct": round(100 * float(s.head(25).sum()) / tot, 1),
            "pn_for_80pct": pn80,
            "distinct_pn": int(s.shape[0]),
        }

    # attach PMS category to top losers via catalog
    pms_map = cat.set_index("part_number")["pms_category"].to_dict() if "pms_category" in cat.columns else {}

    def enrich(rows):
        out = []
        for r in rows:
            rr = dict(r)
            rr["pms_category"] = pms_map.get(r["part_number"]) or ""
            out.append(rr)
        return out

    gps = gps_row(code, 2025)
    gps_series = gps_time_series(code)
    pms_sum = study["pms_summary"][0]
    pms_pack = pms_total_cats(code, 2025)

    # IDS
    if key == "IMOTORS":
        ids = ids_country_avg(IDS_PT)
        ids["label"] = "Portugal dealer network (IDS 2026)"
    else:
        ids = ids_country_avg(IDS_ISR)
        ids["label"] = "Israel dealer network — UMI participants (IDS 2026)"

    # Single allowed compare: this customer FY YoY vs LCV network average
    net_yoy = network_fy_yoy(df, "lcv")
    network_compare = {
        "customer_yoy_pct": yoy,
        "network_yoy_pct": net_yoy,
        "label": "FY2025 vs FY2024 sales change — this customer vs LCV network average",
    }

    # Source from PBI drills (V2 JP/TH/LOCAL chart)
    source = []
    if meta["include_source"]:
        try:
            source = list(STUDY["pbi_h1_2026"]["drills"][key]["source"])
        except Exception:
            source = []

    # PBI vs ISZE billing reconcile
    pbi_cust = STUDY.get("pbi_h1_2026", {}).get("customers", {}).get(key, {})
    pbi_drill = STUDY.get("pbi_h1_2026", {}).get("drills", {}).get(key, {})
    cy = study.get("cy_totals") or {}
    cy25_isze = (cy.get("2025") or {}).get("sales_eur")
    cy26_q1 = (cy.get("2026") or {}).get("sales_eur")  # typically Jan–Mar in local billing
    gps_cy25 = gps.get("sales_eur")
    pbi_h1 = pbi_drill.get("sales_eur") or pbi_cust.get("sales_eur")
    reconcile = []
    if cy25_isze and gps_cy25:
        dlt = money(cy25_isze - gps_cy25)
        pct_d = round(100 * (cy25_isze - gps_cy25) / cy25_isze, 2) if cy25_isze else None
        reconcile.append(
            {
                "period": "CY2025",
                "pbi_or_gps_label": "ISZE GPS wallet (CY)",
                "reference_eur": gps_cy25,
                "isze_billing_eur": cy25_isze,
                "delta_eur": dlt,
                "delta_pct": pct_d,
                "note": "Billing vs GPS CY sales — small gaps = rebate/non-part exclusion or warranty timing.",
            }
        )
    if pbi_h1 and cy26_q1:
        share = round(100 * cy26_q1 / pbi_h1, 1)
        reconcile.append(
            {
                "period": "H1 CY2026 vs Q1 billing",
                "pbi_or_gps_label": "Power BI H1 (Jan–Jun)",
                "reference_eur": money(pbi_h1),
                "isze_billing_eur": money(cy26_q1),
                "delta_eur": None,
                "delta_pct": None,
                "note": (
                    f"ISZE billing only through {STUDY.get('local_billing_max')} (Q1 ≈ {share}% of PBI H1). "
                    "Not a full-period mismatch — partial overlap."
                ),
            }
        )
    reconcile.append(
        {
            "period": "FY2025",
            "pbi_or_gps_label": "ISZE billing FY (ex-rebate)",
            "reference_eur": None,
            "isze_billing_eur": money(tot25),
            "delta_eur": None,
            "delta_pct": None,
            "note": f"Fiscal Apr–Mar used for PN/SaTy. Seed study FY may differ slightly if rebate lines included (~{money(study['fy_totals'].get('2025',{}).get('sales_eur',0))} in seed).",
        }
    )

    cross = build_crosscheck(key, yoy, gps, pms_sum, ids, tot25)
    asks = build_asks(key)

    pack = {
        "key": key,
        "meta": meta,
        "generated": date.today().isoformat(),
        "fiscal_definition": STUDY.get("fiscal_definition"),
        "billing_max": STUDY.get("local_billing_max"),
        "fy24_eur": money(tot24),
        "fy25_eur": money(tot25),
        "fy_yoy_pct": yoy,
        "monthly": monthly_rows,
        "saty_fy24": saty_fy(g, 2024),
        "saty_fy25": saty_fy(g, 2025),
        "lcv_saty_bench": [],
        "network_compare": network_compare,
        "groups": group_compare(),
        "families": family_rows,
        "top_pn_fy24": top_pn(fy24, tot24),
        "top_pn_fy25": top_pn(fy25, tot25),
        "concentration_fy24": concentration(fy24, tot24),
        "concentration_fy25": concentration(fy25, tot25),
        "gainers": enrich(gainers),
        "losers": enrich(losers),
        "silent": enrich(silent),
        "gps": gps,
        "gps_series": gps_series,
        "gps_peers": [],  # V3.1 rule: never peer-country GPS
        "pms_total_wtd_pct": round(100 * float(pms_sum["capture_rate_total_wtd"]), 1),
        "pms_genuine_wtd_pct": round(100 * float(pms_sum["capture_rate_genuine_wtd"]), 1),
        "pms_cats": pms_pack["chart"],
        "pms_scope": pms_pack["scope"],
        "pms_excluded": pms_pack["excluded"],
        "pms_footnotes": pms_pack["footnotes"],
        "pms_assumption": PMS_ASSUMPTION,
        "ids": ids,
        "source_h1": source,
        "h1_sales": pbi_cust,
        "h1_drill_sales": pbi_drill.get("sales_eur"),
        "fill_imotors": 87.5 if key == "IMOTORS" else None,
        "reconcile": reconcile,
        "crosscheck": cross,
        "asks": asks,
        "rebate_note": "REBATE / freight / finance / tool placeholder lines excluded from PN rankings and movers.",
    }
    return pack


def build_crosscheck(key, yoy, gps, pms_sum, ids, tot25) -> list[dict]:
    gps_pct = gps.get("gps_pct")
    pms_pct = round(100 * float(pms_sum["capture_rate_total_wtd"]), 1)
    ids_avg = ids.get("avg_pct")
    findings = []
    if key == "IMOTORS":
        findings.append(
            {
                "tone": "align",
                "text": f"Sales trajectory is positive (FY2025 {yoy:+.1f}% vs FY2024). That aligns with a strong IDS Portugal network result (avg {ids_avg}% points).",
            }
        )
        findings.append(
            {
                "tone": "tension",
                "text": f"IDS looks strong, but GPS capture vs max is only {gps_pct}% — dealer process scores are ahead of wallet capture.",
            }
        )
        findings.append(
            {
                "tone": "tension",
                "text": f"PMS total capture {pms_pct}% under the IML service-schedule assumption — room on scheduled maintenance parts despite growing sales.",
            }
        )
        findings.append(
            {
                "tone": "note",
                "text": "KPI reporting for I Motors is relatively complete vs peers (distributor KPI pack FY2025-26). Use that completeness to track fill and MOS with the same rigor as sales.",
            }
        )
    else:
        findings.append(
            {
                "tone": "tension",
                "text": f"GPS capture vs max is {gps_pct}% (headline looks healthy) while fiscal sales declined ({yoy:+.1f}% FY2025 vs FY2024). Capture % and volume are telling different stories.",
            }
        )
        findings.append(
            {
                "tone": "tension",
                "text": f"PMS total capture {pms_pct}% under the IML service-schedule assumption — scheduled-parts opportunity remains large even where GPS % is green.",
            }
        )
        findings.append(
            {
                "tone": "note",
                "text": f"IDS Israel (UMI dealer network only) averages {ids_avg}% points — mid-pack vs the wider IDS field. Standards are not yet at the level of top Portugal dealers.",
            }
        )
        findings.append(
            {
                "tone": "tension",
                "text": "Distributor KPI completeness for UMI is thin in the FY2025-26 KPI master (few months on several lines). Fill/MOS, when reported, can look strong — do not read that as full commercial recovery.",
            }
        )
        findings.append(
            {
                "tone": "note",
                "text": "Part-number concentration is high (lubricants heavy). A green GPS % with narrow PN mix is fragile if oil channel softens.",
            }
        )
    return findings


def build_asks(key: str) -> list[str]:
    if key == "IMOTORS":
        return [
            "Competitive-parts share fell in H1 while emission/engine lines rose — is that an intentional mix shift, or are we losing genuine aftermarket on competitive lines?",
            "Which three PMS categories (by capture %) should we put on a joint action list for the next two quarters?",
            "Fill rate ~87.5% on the SPI view — what blocks the last ~12 points (stock, order cut-off, supersession)?",
            "Can we confirm N-series service-interval practice locally so capture modelling matches workshop reality?",
            "Which dealers in the IDS Portugal pack need a parts coaching visit first (below country average)?",
        ]
    return [
        "Fiscal sales are down while GPS capture % still looks relatively strong — where did volume leave the basket, and which channels can recover it?",
        "Lubricants dominate top part numbers — what is the 12-month outlook for that channel, and how do we grow the genuine scheduled-maintenance basket alongside it?",
        "PMS total capture is low under the IML service-schedule assumption — which categories (clutch, brakes, filters) should we pilot with dealers first?",
        "IDS Israel covers the UMI network only — do not combine other Israel distributors with IDS Israel / PMS / GPS for this pack. Which UMI dealers should we prioritise for parts process coaching?",
        "KPI reporting completeness is weak on several lines — can we commit to monthly fill / MOS / sales-to-dealer so we can manage with the same numbers?",
        "Which declining or silent part numbers should return to active promotion or stock in FY2026?",
    ]


def try_load_imotors_source():
    """Pull H1 source mix from V2 HTML builder cache if present in study extensions."""
    # Optional sidecar
    side = OUT / "pbi_imotors_h1_source.json"
    if side.exists():
        return json.loads(side.read_text(encoding="utf-8"))
    # Reconstruct from known session values if we stored in FULL study — scan study for source arrays
    # V1 full HTML had hardcoded drills — leave empty and note in pack if missing
    return [
        {"name": "GENUINE", "eur": None, "note": "See Power BI SALES · H1 CY2026 source drill for I Motors"},
    ]


# ---------- HTML / Excel ----------

CSS = """
*{box-sizing:border-box}
html,body{margin:0;padding:0;-webkit-print-color-adjust:exact;print-color-adjust:exact}
body{font-family:"Segoe UI",Helvetica,Arial,sans-serif;color:#222;background:#f7f4ee;font-size:15px;line-height:1.5}
h1,h2,h3{font-family:Georgia,"Times New Roman",serif;color:#1a2b4a;margin:0}
.page{max-width:980px;margin:0 auto;padding:2rem 1.4rem 1.2rem;min-height:70vh;border-bottom:1px solid #d9d3c8}
@media print{.page{break-after:page;min-height:0;border:0}.no-print{display:none!important}body{background:#fff}}
.cover{background:linear-gradient(155deg,#15233c 0%,#203759 55%,#2b4a78 100%);color:#eef1f6;padding:3.2rem 1.6rem 2.8rem}
.cover .inner{max-width:980px;margin:0 auto}
.cover h1{color:#fff;font-size:2.35rem;line-height:1.12}
.cover .rule{width:4.2rem;height:3px;background:#c0552d;margin:1rem 0 .9rem}
.chip{display:inline-block;background:rgba(255,255,255,.12);border:1px solid rgba(255,255,255,.22);padding:.2rem .65rem;border-radius:4px;font-size:.78rem;margin:.15rem .25rem .15rem 0}
.nav{position:sticky;top:0;z-index:20;background:#f7f4ee;border-bottom:1px solid #d9d3c8;padding:.4rem 1rem;display:flex;flex-wrap:wrap;gap:.3rem}
.nav a{font-size:.72rem;color:#1a2b4a;text-decoration:none;padding:.22rem .4rem;border:1px solid #d9d3c8;background:#fff}
h2.sec{font-size:1.4rem;margin:0 0 .65rem;padding-bottom:.3rem;border-bottom:2px solid #1a2b4a}
h2.sec .no{color:#c0552d}
h3{font-size:1.02rem;margin:1rem 0 .35rem}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:.65rem;margin:.85rem 0}
.stat{background:#fff;border:1px solid #d9d3c8;padding:.75rem .9rem}
.stat .lbl{font-size:.68rem;text-transform:uppercase;letter-spacing:.04em;color:#6b6256}
.stat .val{font-size:1.25rem;font-weight:700;color:#1a2b4a;margin-top:.08rem}
.stat .sub{font-size:.8rem;color:#6b6256}
.good{color:#2e7d54!important}.bad{color:#b23b3b!important}.amber{color:#a67c00!important}
.callout{border-left:3px solid #c0552d;background:#fff;padding:.75rem .95rem;margin:.85rem 0}
.callout.warn{border-left-color:#eda100}.callout.ok{border-left-color:#1d9e75}
.assume{border:1px solid #d9d3c8;background:#fff8f2;padding:.65rem .85rem;margin:.5rem 0 .8rem;font-size:.88rem;color:#3a342c}
.chart{position:relative;width:100%;height:300px;background:#fff;border:1px solid #d9d3c8;padding:.45rem;margin:.7rem 0}
.chart.tall{height:400px}
.two{display:grid;grid-template-columns:1fr 1fr;gap:1rem}
@media(max-width:820px){.two{grid-template-columns:1fr}}
table{width:100%;border-collapse:collapse;font-size:.84rem;background:#fff;margin:.6rem 0}
th{background:#1a2b4a;color:#fff;text-align:left;padding:.45rem .55rem;font-size:.7rem;text-transform:uppercase}
td{padding:.4rem .55rem;border-bottom:1px solid #d9d3c8}
tbody tr:nth-child(even){background:#faf8f4}
td.num,.num{text-align:right;font-variant-numeric:tabular-nums}
code{font-family:Consolas,monospace;font-size:.84em}
.muted{color:#6b6256;font-size:.88rem}
.ask{background:#fff;border:1px solid #d9d3c8;padding:.65rem .9rem;margin:.35rem 0}
.ask .n{color:#c0552d;font-weight:700;margin-right:.35rem}
.footer{max-width:980px;margin:0 auto;padding:1rem 1.4rem 2.2rem;font-size:.72rem;color:#6b6256}
.tag{display:inline-block;font-size:.7rem;padding:.12rem .4rem;border-radius:3px;margin-right:.3rem}
.tag.ok{background:#e6f5ef;color:#1d6b4f}.tag.warn{background:#fff3d6;color:#8a6500}.tag.bad{background:#fde8e8;color:#9b2c2c}
"""


def render_html(pack: dict) -> str:
    meta = pack["meta"]
    yoy_cls = "good" if (pack["fy_yoy_pct"] or 0) >= 0 else "bad"
    nav = []
    pages = [
        ("p1", "01 Scope"),
        ("p2", "02 Sales"),
        ("p3", "03 SaTy"),
    ]
    n = 4
    if meta["include_source"]:
        pages.append((f"p{n}", f"{n:02d} Source"))
        n += 1
    pages += [
        (f"p{n}", f"{n:02d} GPS"),
        (f"p{n+1}", f"{n+1:02d} PMS"),
        (f"p{n+2}", f"{n+2:02d} Family"),
        (f"p{n+3}", f"{n+3:02d} PN"),
        (f"p{n+4}", f"{n+4:02d} Movers"),
        (f"p{n+5}", f"{n+5:02d} Cross-check"),
        (f"p{n+6}", f"{n+6:02d} Asks"),
    ]
    # rebuild with stable ids used below
    # Fixed page ids for template simplicity:
    page_ids = ["p1", "p2", "p3", "p4", "p5", "p6", "p7", "p8", "p9", "p10"]
    labels = ["Scope", "Sales", "SaTy", "GPS", "PMS", "Family", "PN", "Movers", "Cross-check", "Asks"]
    if meta["include_source"]:
        page_ids = ["p1", "p2", "p3", "p3b", "p4", "p5", "p6", "p7", "p8", "p9", "p10"]
        labels = ["Scope", "Sales", "SaTy", "Source", "GPS", "PMS", "Family", "PN", "Movers", "Cross-check", "Asks"]
    nav_html = "".join(f'<a href="#{i}">{j+1:02d} {lab}</a>' for j, (i, lab) in enumerate(zip(page_ids, labels)))

    saty_bench = ""
    if pack["lcv_saty_bench"]:
        rows = "".join(
            f"<tr><td>{r['saty']}</td><td class='num'>{r['share_pct']:.1f}%</td></tr>"
            for r in pack["lcv_saty_bench"][:6]
        )
        saty_bench = f"""
        <div>
          <h3>LCV network share benchmark (FY2025)</h3>
          <p class="muted">Average SaTy mix across the LCV distributor network (reference only — this pack stays UMI-only).</p>
          <table><thead><tr><th>SaTy</th><th>Share</th></tr></thead><tbody>{rows}</tbody></table>
        </div>"""

    # One allowed network compare (sales YoY) — not GPS peers
    nc = pack.get("network_compare") or {}
    network_block = f"""
<h3>Only network benchmark (sales)</h3>
<p class="muted">{nc.get('label') or 'FY YoY vs LCV network average'}</p>
<div class="chart"><canvas id="cNet"></canvas></div>
"""

    source_page = ""
    if meta["include_source"]:
        h1 = pack.get("h1_sales") or {}
        drill = pack.get("h1_drill_sales")
        src_note = (
            f"H1 CY2026 sales {eur(drill or h1.get('sales_eur'))} "
            f"({h1.get('yoy_pct')}% YoY) — Power BI source shares (JP / TH / LOCAL)."
        )
        source_page = f"""
<section class="page" id="p3b">
<h2 class="sec"><span class="no">04</span> Source mix (H1 CY2026)</h2>
<div class="callout">{src_note}</div>
<p class="muted">Share of H1 sales by sourcing origin — restored V2 view (not H1 total bars).</p>
<div class="chart tall"><canvas id="cSrc"></canvas></div>
</section>"""

    # PN tables
    def pn_rows(rows):
        return "".join(
            f"<tr><td>{r['rank']}</td><td><code>{r['part_number']}</code></td><td>{r['description']}</td>"
            f"<td class='num'>{eur(r['sales_eur'])}</td><td class='num'>{r['share_pct']:.1f}%</td></tr>"
            for r in rows[:12]
        )

    def mover_rows(rows, bad=False):
        cls = "bad" if bad else "good"
        return "".join(
            f"<tr><td><code>{r['part_number']}</code></td><td>{r['description']}</td>"
            f"<td class='num'>{eur(r['fy24_eur'])}</td><td class='num'>{eur(r['fy25_eur'])}</td>"
            f"<td class='num {cls}'>{eur(r['delta_eur'])}</td><td>{r.get('pms_category') or '—'}</td></tr>"
            for r in rows[:10]
        )

    cross_html = ""
    for f in pack["crosscheck"]:
        tag = {"align": "ok", "tension": "warn", "note": "ok"}.get(f["tone"], "ok")
        cross_html += f"<div class='ask'><span class='tag {tag}'>{f['tone']}</span>{f['text']}</div>"

    # Reconcile + PMS footnotes
    rec_rows = "".join(
        f"<tr><td>{r['period']}</td><td>{r['pbi_or_gps_label']}</td>"
        f"<td class='num'>{eur(r['reference_eur']) if r.get('reference_eur') is not None else '—'}</td>"
        f"<td class='num'>{eur(r['isze_billing_eur']) if r.get('isze_billing_eur') is not None else '—'}</td>"
        f"<td class='num'>{eur(r['delta_eur']) if r.get('delta_eur') is not None else '—'}</td>"
        f"<td>{r.get('note') or ''}</td></tr>"
        for r in pack.get("reconcile") or []
    )
    rec_html = f"""
<h3>Power BI vs ISZE billing</h3>
<table><thead><tr><th>Period</th><th>External / GPS</th><th>Ref €</th><th>ISZE €</th><th>Δ</th><th>Note</th></tr></thead>
<tbody>{rec_rows}</tbody></table>
"""
    pms_extra = ""
    for ex in pack.get("pms_excluded") or []:
        pms_extra += f"<div class='callout warn'><strong>Excluded — {ex['category']} ({ex['raw_capture_pct']}%)</strong><br/>{ex['reason']}</div>"
    for fn in pack.get("pms_footnotes") or []:
        pms_extra += f"<div class='callout'><strong>{fn['category']}</strong><br/>{fn['text']}</div>"

    asks_html = "".join(f"<div class='ask'><span class='n'>{i}.</span>{q}</div>" for i, q in enumerate(pack["asks"], 1))

    c24 = pack["concentration_fy24"]
    c25 = pack["concentration_fy25"]
    gps = pack["gps"]

    data = {
        "monthly": pack["monthly"],
        "saty24": pack["saty_fy24"],
        "saty25": pack["saty_fy25"],
        "groups": pack["groups"][:10],
        "pms": pack["pms_cats"],
        "gps_series": pack.get("gps_series") or [],
        "net_compare": [
            {"label": meta["label"], "yoy": pack["fy_yoy_pct"]},
            {"label": "LCV network avg", "yoy": (pack.get("network_compare") or {}).get("network_yoy_pct")},
        ],
        "fy": [pack["fy24_eur"], pack["fy25_eur"]],
        "include_source": meta["include_source"],
        "source": pack.get("source_h1") or [],
        "h1": pack.get("h1_sales") or {},
    }

    src_script = ""
    if meta["include_source"]:
        src_script = """
if (D.include_source && D.source && D.source.length) {
  const src = D.source.filter(r => r.name !== 'OTHER' || (r.pct||0) > 0);
  new Chart(document.getElementById('cSrc'), {type:'bar', data:{
    labels: src.map(r=>r.name),
    datasets:[
      {label:'Share of H1 %', data:src.map(r=>r.pct), backgroundColor:'#2a78d6', barThickness:28},
      {label:'YoY %', data:src.map(r=>r.yoy), backgroundColor:'#c0552d', barThickness:28}
    ]},
    options:{responsive:true,maintainAspectRatio:false,plugins:{legend:{position:'bottom'}},
      scales:{y:{ticks:{callback:v=>v+'%'},grid:{color:grid}},x:{grid:{display:false}}}}});
}
"""

    html = Template("""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1"/>
<title>$title</title>
<style>$css</style>
</head>
<body>
<!--CHARTJS-->
<div class="cover"><div class="inner">
<span class="chip">ISZE Parts · Customer briefing V3.1</span>
<span class="chip">$subtitle</span>
<h1>$title</h1>
<div class="rule"></div>
<p style="max-width:38rem;opacity:.93">Fiscal sales, mix, GPS capture %, PMS capture %, and part-number depth — prepared for a meeting with <strong>$label</strong> only.</p>
<p style="color:#c9d2e0;font-size:.9rem">FY = Apr–Mar · Billing through $billing_max · Generated $generated</p>
</div></div>
<nav class="nav no-print">$nav</nav>

<section class="page" id="p1">
<h2 class="sec"><span class="no">01</span> Scope &amp; periods</h2>
<div class="callout"><strong>Customer:</strong> $label ($country).<br/>
<strong>This pack is single-customer</strong> — at most one light network-average benchmark; no peer-country GPS compare.
$scope_ids_note</div>
<table>
<thead><tr><th>Layer</th><th>Period</th><th>What you see</th></tr></thead>
<tbody>
<tr><td>Fiscal sales, SaTy, PN</td><td>FY2024 vs FY2025 (Apr–Mar)</td><td>ISZE billing (rebate lines excluded)</td></tr>
<tr><td>Sales tendency</td><td>24 fiscal months</td><td>Monthly billed sales</td></tr>
<tr><td>GPS capture</td><td>CY now vs past</td><td>Capture vs max % (time series only)</td></tr>
<tr><td>PMS capture</td><td>CY2025</td><td>Total capture % by category (no silent 100% ceiling)</td></tr>
$h1_row
</tbody></table>
<p class="muted">$rebate_note</p>
</section>

<section class="page" id="p2">
<h2 class="sec"><span class="no">02</span> Sales trajectory</h2>
<div class="grid">
<div class="stat"><div class="lbl">FY2024</div><div class="val">$fy24</div></div>
<div class="stat"><div class="lbl">FY2025</div><div class="val">$fy25</div><div class="sub $yoy_cls">$yoy vs prior FY</div></div>
<div class="stat"><div class="lbl">H1 CY2026 (PBI)</div><div class="val">$h1s</div><div class="sub">Calendar Jan–Jun 2026</div></div>
</div>
<div class="chart"><canvas id="cFy"></canvas></div>
$network_block
<h3>Monthly tendency (FY2024–FY2025)</h3>
<div class="chart tall"><canvas id="cM"></canvas></div>
$rec_html
</section>

<section class="page" id="p3">
<h2 class="sec"><span class="no">03</span> SaTy evolution</h2>
<div class="two">
<div><h3>FY2024</h3><div class="chart"><canvas id="cS24"></canvas></div></div>
<div><h3>FY2025</h3><div class="chart"><canvas id="cS25"></canvas></div></div>
</div>
</section>

$source_page

<section class="page" id="p4">
<h2 class="sec"><span class="no">$gps_no</span> GPS capture — now vs past</h2>
<div class="grid">
<div class="stat"><div class="lbl">GPS capture vs max (CY2025)</div><div class="val">$gps_pct</div><div class="sub">Traffic light: $gps_tl</div></div>
<div class="stat"><div class="lbl">UIO (context)</div><div class="val">$uio</div><div class="sub muted">Absolute €/SPU in footnote only</div></div>
</div>
<p class="muted">Headline = <strong>percentage capture over time</strong> — no other-country peer bars. Footnote: SPU ≈ €$spu · CY2025 sales ≈ $gps_sales.</p>
<div class="chart"><canvas id="cGps"></canvas></div>
<p class="muted">CY2024 uses sales ÷ CY2025 max-spend as a trend proxy when max-spend was not stored. CY2026 run-rate = YTD×4 ÷ year max-spend.</p>
</section>

<section class="page" id="p5">
<h2 class="sec"><span class="no">$pms_no</span> PMS capture %</h2>
<div class="assume">$pms_assumption</div>
<div class="grid">
<div class="stat"><div class="lbl">Total capture (weighted)</div><div class="val">$pms_tot</div></div>
<div class="stat"><div class="lbl">Genuine capture (secondary)</div><div class="val">$pms_gen</div><div class="sub">Mix / quality lens</div></div>
<div class="stat"><div class="lbl">Scope</div><div class="val" style="font-size:1rem">$pms_scope</div></div>
</div>
<div class="assume">$pms_assumption</div>
<h3>Category hit rate — total capture % (uncapped display)</h3>
<div class="chart tall"><canvas id="cPms"></canvas></div>
$pms_extra
<p class="muted">No euro gap bars. Values above 100% are diagnosed or excluded with reason — never silently capped.</p>
</section>

<section class="page" id="p6">
<h2 class="sec"><span class="no">$fam_no</span> Product family / group</h2>
<p class="muted">ISZE parts classification (family / group) — share % now vs past, not euros. Lubricants without catalogue match are labelled explicitly.</p>
<div class="chart tall"><canvas id="cFam"></canvas></div>
<table>
<thead><tr><th>Group</th><th>FY2024 share</th><th>FY2025 share</th><th>YoY €</th></tr></thead>
<tbody>$group_rows</tbody>
</table>
</section>

<section class="page" id="p7">
<h2 class="sec"><span class="no">$pn_no</span> Part numbers — full year vs full year</h2>
<div class="callout">Period: <strong>FY2024 (Apr 2024–Mar 2025)</strong> vs <strong>FY2025 (Apr 2025–Mar 2026)</strong>. Rebate / non-part lines excluded.</div>
<div class="grid">
<div class="stat"><div class="lbl">Top-10 share FY24</div><div class="val">$c24_10</div></div>
<div class="stat"><div class="lbl">Top-10 share FY25</div><div class="val">$c25_10</div></div>
<div class="stat"><div class="lbl">PNs for 80% FY25</div><div class="val">$c25_80</div><div class="sub">$c25_n distinct PNs</div></div>
</div>
<div class="two">
<div><h3>Top PN FY2024</h3><table><thead><tr><th>#</th><th>PN</th><th>Desc</th><th>€</th><th>%</th></tr></thead><tbody>$pn24</tbody></table></div>
<div><h3>Top PN FY2025</h3><table><thead><tr><th>#</th><th>PN</th><th>Desc</th><th>€</th><th>%</th></tr></thead><tbody>$pn25</tbody></table></div>
</div>
</section>

<section class="page" id="p8">
<h2 class="sec"><span class="no">$mov_no</span> PN movers &amp; silent lines</h2>
<p class="muted">Largest € gains / losses FY2024 → FY2025 (rebate excluded). PMS category shown when mapped.</p>
<h3>Top gainers</h3>
<table><thead><tr><th>PN</th><th>Desc</th><th>FY24</th><th>FY25</th><th>Δ</th><th>PMS</th></tr></thead><tbody>$gain</tbody></table>
<h3>Top losers</h3>
<table><thead><tr><th>PN</th><th>Desc</th><th>FY24</th><th>FY25</th><th>Δ</th><th>PMS</th></tr></thead><tbody>$lose</tbody></table>
<h3>Silent / collapsing (had FY24 sales, near-zero FY25)</h3>
<table><thead><tr><th>PN</th><th>Desc</th><th>FY24</th><th>FY25</th><th>Δ</th><th>PMS</th></tr></thead><tbody>$silent</tbody></table>
</section>

<section class="page" id="p9">
<h2 class="sec"><span class="no">$x_no</span> IDS / KPI cross-check</h2>
<p class="muted">Where dealer standards / KPI reporting and wallet metrics agree — or pull apart.</p>
$cross
<div class="callout"><strong>IDS snapshot:</strong> $ids_label — average <strong>$ids_avg%</strong> points (n=$ids_n; max $ids_max% · min $ids_min%).</div>
</section>

<section class="page" id="p10">
<h2 class="sec"><span class="no">$ask_no</span> Meeting asks</h2>
<p class="muted">Clear questions for the joint discussion — customer-safe wording.</p>
$asks
</section>

<div class="footer">Sources: ISZE billing · PRISM GPS/PMS · IDS 2026 dealer ranking · Power BI SALES (H1). External pack — no internal methodology nicknames. $label only.</div>

<!--CHART_BOOT-->
</body></html>
""")

    # numbering depends on source page
    if meta["include_source"]:
        nums = dict(gps_no="05", pms_no="06", fam_no="07", pn_no="08", mov_no="09", x_no="10", ask_no="11")
        h1_row = f"<tr><td>H1 sales / source</td><td>Jan–Jun 2026</td><td>Power BI ({meta['label']})</td></tr>"
    else:
        nums = dict(gps_no="04", pms_no="05", fam_no="06", pn_no="07", mov_no="08", x_no="09", ask_no="10")
        h1_row = "<tr><td>H1 sales context</td><td>Jan–Jun 2026</td><td>Power BI total</td></tr>"

    group_rows = "".join(
        f"<tr><td>{r['group']}</td><td class='num'>{r['fy24_share']:.1f}%</td>"
        f"<td class='num'>{r['fy25_share']:.1f}%</td>"
        f"<td class='num'>{('+' if (r['yoy_pct'] or 0)>=0 else '') + (str(r['yoy_pct'])+'%' if r['yoy_pct'] is not None else 'n/a')}</td></tr>"
        for r in pack["groups"][:10]
    )

    h1 = pack.get("h1_sales") or {}
    if meta.get("forbid_uti"):
        scope_ids_note = (
            "<br/><strong>IDS Israel:</strong> covers the UMI dealer network only. "
            "Do not combine other Israel distributors with IDS Israel scores, PMS, or GPS in this pack."
        )
    else:
        scope_ids_note = ""

    out = html.safe_substitute(
        title=meta["title"],
        subtitle=meta["subtitle"],
        label=meta["label"],
        country=meta["country"],
        scope_ids_note=scope_ids_note,
        css=CSS,
        nav=nav_html,
        billing_max=pack["billing_max"],
        generated=pack["generated"],
        rebate_note=pack["rebate_note"],
        fy24=eur(pack["fy24_eur"]),
        fy25=eur(pack["fy25_eur"]),
        yoy=f"{pack['fy_yoy_pct']:+.1f}%" if pack["fy_yoy_pct"] is not None else "n/a",
        yoy_cls=yoy_cls,
        h1s=eur(h1.get("sales_eur") or pack.get("h1_drill_sales")) if (h1.get("sales_eur") or pack.get("h1_drill_sales")) else "—",
        network_block=network_block,
        rec_html=rec_html,
        source_page=source_page,
        gps_pct=f"{gps.get('gps_pct')}%" if gps.get("gps_pct") is not None else "n/a",
        gps_tl=gps.get("traffic_light") or "—",
        uio=f"{gps.get('uio'):,}" if gps.get("uio") else "—",
        spu=gps.get("spu_eur") or "—",
        gps_sales=eur(gps.get("sales_eur")),
        pms_assumption=pack["pms_assumption"],
        pms_tot=f"{pack['pms_total_wtd_pct']}%",
        pms_gen=f"{pack['pms_genuine_wtd_pct']}%",
        pms_scope=pack.get("pms_scope") or "—",
        pms_extra=pms_extra,
        group_rows=group_rows,
        c24_10=f"{c24.get('top10_share_pct', '—')}%",
        c25_10=f"{c25.get('top10_share_pct', '—')}%",
        c25_80=str(c25.get("pn_for_80pct", "—")),
        c25_n=str(c25.get("distinct_pn", "—")),
        pn24=pn_rows(pack["top_pn_fy24"]),
        pn25=pn_rows(pack["top_pn_fy25"]),
        gain=mover_rows(pack["gainers"], False),
        lose=mover_rows(pack["losers"], True),
        silent=mover_rows(pack["silent"], True),
        cross=cross_html + rec_html,
        asks=asks_html,
        ids_label=pack["ids"]["label"],
        ids_avg=pack["ids"]["avg_pct"],
        ids_n=pack["ids"]["n_dealers"],
        ids_max=pack["ids"]["max_pct"],
        ids_min=pack["ids"]["min_pct"],
        h1_row=h1_row,
        **nums,
    )
    boot = (
        f"<script>{CHART_JS}</script>\n<script>\n"
        f"const D = {json.dumps(data)};\n"
        """
const ink='#52514e', grid='#e1e0d9', navy='#1a2b4a', blue='#2a78d6', terra='#c0552d', green='#1d9e75', red='#e24b4a';
new Chart(document.getElementById('cFy'),{type:'bar',data:{labels:['FY2024','FY2025'],datasets:[{data:D.fy,backgroundColor:[blue,terra],barThickness:42}]},
  options:{responsive:true,maintainAspectRatio:false,plugins:{legend:{display:false}},scales:{y:{ticks:{callback:v=>'€'+(v/1e6).toFixed(2)+'M'},grid:{color:grid}},x:{grid:{display:false}}}}});
new Chart(document.getElementById('cNet'),{type:'bar',data:{labels:D.net_compare.map(r=>r.label),datasets:[{data:D.net_compare.map(r=>r.yoy),backgroundColor:[terra,blue],barThickness:36}]},
  options:{responsive:true,maintainAspectRatio:false,plugins:{legend:{display:false}},scales:{y:{ticks:{callback:v=>v+'%'},grid:{color:grid}},x:{grid:{display:false}}}}});
new Chart(document.getElementById('cM'),{type:'line',data:{labels:D.monthly.map(r=>r.ym),datasets:[{data:D.monthly.map(r=>r.sales_eur),borderColor:navy,backgroundColor:'rgba(26,43,74,.12)',fill:true,tension:.25,pointRadius:2}]},
  options:{responsive:true,maintainAspectRatio:false,plugins:{legend:{display:false}},scales:{y:{ticks:{callback:v=>'€'+(v/1000).toFixed(0)+'K'},grid:{color:grid}},x:{ticks:{maxRotation:60,autoSkip:true,maxTicksLimit:12},grid:{display:false}}}}});
function satyChart(id, rows){
  new Chart(document.getElementById(id),{type:'bar',data:{labels:rows.map(r=>r.saty),datasets:[{data:rows.map(r=>r.share_pct),backgroundColor:blue,barThickness:22}]},
    options:{indexAxis:'y',responsive:true,maintainAspectRatio:false,plugins:{legend:{display:false}},scales:{x:{max:100,ticks:{callback:v=>v+'%'},grid:{color:grid}},y:{grid:{display:false}}}}});
}
satyChart('cS24', D.saty24); satyChart('cS25', D.saty25);
"""
        + src_script
        + """
new Chart(document.getElementById('cGps'),{type:'bar',data:{labels:D.gps_series.map(r=>r.label),datasets:[{data:D.gps_series.map(r=>r.gps_pct),backgroundColor:terra,barThickness:36}]},
  options:{responsive:true,maintainAspectRatio:false,plugins:{legend:{display:false}},scales:{y:{ticks:{callback:v=>v+'%'},grid:{color:grid}},x:{grid:{display:false}}}}});
new Chart(document.getElementById('cPms'),{type:'bar',data:{labels:D.pms.map(r=>r.category),datasets:[{data:D.pms.map(r=>r.capture_pct),backgroundColor:D.pms.map(r=>r.capture_pct>100?'#eda100':r.capture_pct>=80?green:r.capture_pct>=40?blue:red),barThickness:16}]},
  options:{indexAxis:'y',responsive:true,maintainAspectRatio:false,plugins:{legend:{display:false}},scales:{x:{ticks:{callback:v=>v+'%'},grid:{color:grid}},y:{grid:{display:false},ticks:{font:{size:10}}}}}});
new Chart(document.getElementById('cFam'),{type:'bar',data:{labels:D.groups.map(r=>r.group),datasets:[
  {label:'FY2024 share %', data:D.groups.map(r=>r.fy24_share), backgroundColor:'#85b7eb', barThickness:14},
  {label:'FY2025 share %', data:D.groups.map(r=>r.fy25_share), backgroundColor:terra, barThickness:14}]},
  options:{indexAxis:'y',responsive:true,maintainAspectRatio:false,plugins:{legend:{position:'bottom'}},scales:{x:{ticks:{callback:v=>v+'%'},grid:{color:grid}},y:{grid:{display:false},ticks:{font:{size:10}}}}}});
</script>
"""
    )
    out = out.replace("<!--CHARTJS-->", "").replace("<!--CHART_BOOT-->", boot)
    if meta["forbid_uti"]:
        m = re.search(r".{0,50}\bUTI\b.{0,50}", out)
        if m:
            raise RuntimeError("UMI V3 pack accidentally contains UTI — near: " + m.group(0))
    return out


def write_excel(pack: dict, path: Path):
    wb = Workbook()
    navy_f = PatternFill("solid", fgColor="1A2B4A")
    head = Font(name="Calibri", bold=True, color="FFFFFF", size=11)
    title = Font(name="Calibri", bold=True, color="1A2B4A", size=14)
    body = Font(name="Calibri", size=10)
    wrap = Alignment(wrap_text=True, vertical="top")
    thin = Border(
        left=Side(style="thin", color="D9D3C8"),
        right=Side(style="thin", color="D9D3C8"),
        top=Side(style="thin", color="D9D3C8"),
        bottom=Side(style="thin", color="D9D3C8"),
    )
    zebra = PatternFill("solid", fgColor="F7F4EE")

    def hdr(ws, row, ncols):
        for c in range(1, ncols + 1):
            cell = ws.cell(row, c)
            cell.fill = navy_f
            cell.font = head
            cell.border = thin

    def table(ws, r0, headers, rows, money_cols=()):
        for j, h in enumerate(headers, 1):
            ws.cell(r0, j, h)
        hdr(ws, r0, len(headers))
        for i, row in enumerate(rows):
            for j, val in enumerate(row, 1):
                cell = ws.cell(r0 + 1 + i, j, val)
                cell.font = body
                cell.border = thin
                cell.alignment = wrap
                if i % 2:
                    cell.fill = zebra
                if j in money_cols and isinstance(val, (int, float)):
                    cell.number_format = "#,##0"

    def widths(ws, ws_):
        for i, w in enumerate(ws_, 1):
            ws.column_dimensions[get_column_letter(i)].width = max(w, 28 if i == 2 else w)

    meta = pack["meta"]
    ws = wb.active
    ws.title = "00_README"
    ws["A1"] = f"{meta['title']} — V3"
    ws["A1"].font = title
    for i, t in enumerate(
        [
            "Single-customer pack. No dual-DB compare.",
            PMS_ASSUMPTION,
            pack["rebate_note"],
            "Primary = total PMS capture %. GPS = capture vs max %.",
            "External language: IML service schedule — no internal nicknames.",
        ],
        3,
    ):
        ws.cell(i, 1, t).alignment = wrap
    ws.column_dimensions["A"].width = 100

    ws = wb.create_sheet("01_Sales")
    table(
        ws,
        1,
        ["Metric", "Value"],
        [
            ["FY2024 €", pack["fy24_eur"]],
            ["FY2025 €", pack["fy25_eur"]],
            ["FY YoY %", pack["fy_yoy_pct"]],
            ["GPS capture % CY2025", pack["gps"].get("gps_pct")],
            ["PMS total %", pack["pms_total_wtd_pct"]],
            ["PMS genuine % (secondary)", pack["pms_genuine_wtd_pct"]],
            ["IDS avg %", pack["ids"]["avg_pct"]],
        ],
        money_cols={2},
    )
    widths(ws, [36, 18])

    ws = wb.create_sheet("02_Monthly")
    table(ws, 1, ["YM", "Sales €"], [[r["ym"], r["sales_eur"]] for r in pack["monthly"]], {2})
    widths(ws, [14, 14])

    ws = wb.create_sheet("03_SaTy")
    rows = []
    for fy, block in ((2024, pack["saty_fy24"]), (2025, pack["saty_fy25"])):
        for r in block:
            rows.append([fy, r["saty"], r["sales_eur"], r["share_pct"]])
    table(ws, 1, ["FY", "SaTy", "€", "Share %"], rows, {3})
    widths(ws, [8, 12, 14, 12])

    ws = wb.create_sheet("04_GPS_PMS")
    rows = [["GPS " + r["label"], r["gps_pct"], r.get("note")] for r in pack.get("gps_series") or []]
    rows.append(["—", "", ""])
    rows += [[r["category"], r["capture_pct"], ""] for r in pack["pms_cats"]]
    for ex in pack.get("pms_excluded") or []:
        rows.append([f"EXCLUDED {ex['category']}", ex["raw_capture_pct"], ex["reason"][:80]])
    table(ws, 1, ["Series / Category", "Capture %", "Note"], rows)
    widths(ws, [36, 14, 60])

    ws = wb.create_sheet("04b_Reconcile")
    table(
        ws,
        1,
        ["Period", "Ref label", "Ref €", "ISZE €", "Delta", "Note"],
        [
            [
                r["period"],
                r["pbi_or_gps_label"],
                r.get("reference_eur"),
                r.get("isze_billing_eur"),
                r.get("delta_eur"),
                r.get("note"),
            ]
            for r in pack.get("reconcile") or []
        ],
        {3, 4, 5},
    )
    widths(ws, [22, 28, 14, 14, 12, 60])

    ws = wb.create_sheet("05_Family")
    table(
        ws,
        1,
        ["Group", "FY24 share", "FY25 share", "YoY %"],
        [[r["group"], r["fy24_share"], r["fy25_share"], r["yoy_pct"]] for r in pack["groups"]],
    )
    widths(ws, [28, 12, 12, 12])

    ws = wb.create_sheet("06_PN_FY")
    r = 1
    for label, block in (("FY2024", pack["top_pn_fy24"]), ("FY2025", pack["top_pn_fy25"])):
        ws.cell(r, 1, label).font = title
        table(
            ws,
            r + 1,
            ["Rank", "PN", "Desc", "€", "%"],
            [[x["rank"], x["part_number"], x["description"], x["sales_eur"], x["share_pct"]] for x in block],
            {4},
        )
        r += 3 + len(block)
    widths(ws, [10, 16, 40, 12, 10])

    ws = wb.create_sheet("07_Movers")
    r = 1
    for label, block in (("Gainers", pack["gainers"]), ("Losers", pack["losers"]), ("Silent", pack["silent"])):
        ws.cell(r, 1, label).font = title
        table(
            ws,
            r + 1,
            ["PN", "Desc", "FY24", "FY25", "Delta", "PMS"],
            [
                [x["part_number"], x["description"], x["fy24_eur"], x["fy25_eur"], x["delta_eur"], x.get("pms_category")]
                for x in block
            ],
            {3, 4, 5},
        )
        r += 3 + len(block)
    widths(ws, [14, 36, 12, 12, 12, 16])

    ws = wb.create_sheet("08_Asks")
    table(ws, 1, ["#", "Ask"], [[i, q] for i, q in enumerate(pack["asks"], 1)])
    widths(ws, [6, 90])

    for name in wb.sheetnames:
        wb[name].freeze_panes = "A2"
    wb.save(path)


def main():
    V3.mkdir(parents=True, exist_ok=True)
    print("Loading sales…")
    df = load_sales()
    cat = load_catalog()
    # optional Imotors source sidecar
    STUDY["_imotors_h1_source"] = try_load_imotors_source()

    manifests = []
    for key in ("IMOTORS", "UMI"):
        print("Building pack", key)
        pack = build_customer_pack(key, df, cat)
        stem = CUSTOMERS[key]["file_stem"]
        html_path = V3 / f"{stem}.html"
        xlsx_path = V3 / f"{stem}.xlsx"
        json_path = V3 / f"{stem}_data.json"
        # strip huge monthly detail already in pack — save
        json_path.write_text(json.dumps(pack, indent=2), encoding="utf-8")
        html_path.write_text(render_html(pack), encoding="utf-8")
        write_excel(pack, xlsx_path)
        # also copy clear names to parent folder as requested
        for src, dst in [
            (html_path, OUT / f"{stem}.html"),
            (xlsx_path, OUT / f"{stem}.xlsx"),
        ]:
            dst.write_bytes(src.read_bytes())
        manifests.append({"key": key, "html": str(OUT / f"{stem}.html"), "xlsx": str(OUT / f"{stem}.xlsx")})
        print(" wrote", stem)

    (V3 / "manifest.json").write_text(json.dumps(manifests, indent=2), encoding="utf-8")
    print("done", manifests)


if __name__ == "__main__":
    main()

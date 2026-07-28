# -*- coding: utf-8 -*-
"""
V4 customer-facing deep packs — one HTML/Excel/JSON pack per distributor, ALL 22 DBs.

V4 (network-wide rollout of the V3.1 single-customer template):
- Generalises V3.1 (I Motors / UMI only) to every distributor in
  DB_Sales_Order_Study/study_state.json (22 codes).
- Adds Germany-level part-number depth: vanished / new / continuing-dropper PNs
  on quantity, plus a channel-shift test (customer decline vs rest-of-network)
  for the biggest quantity crashes.
- Computes FY totals, GPS and PMS straight from derived files — study_data.json
  is only used (optionally) for Power BI H1 source-mix context on PORTUGAL/UMI.
- Keeps all V3.1 hard rules: one pack per customer, GPS now-vs-past % only,
  PMS never silent-capped, family = share % only, PN = FY vs FY ex-rebate,
  UMI pack never contains the string UTI.
See CUSTOMER_PACK_RULES.md.
"""
from __future__ import annotations

import json
import math
import re
from pathlib import Path
from string import Template

import pandas as pd
import pyarrow.dataset as ds
from openpyxl import Workbook
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter

# ---------- paths ----------

OUT = Path(__file__).resolve().parent
V4 = OUT / "V4"
ROOT = OUT.parents[2]
NETWORK_HUB = OUT.parent / "DB_Sales_Order_Study" / "deep_v4"

STUDY_DATA_PATH = OUT / "study_data.json"
STUDY_DATA: dict = json.loads(STUDY_DATA_PATH.read_text(encoding="utf-8")) if STUDY_DATA_PATH.exists() else {}

CHART_JS = (OUT / "assets" / "chart.umd.min.js").read_text(encoding="utf-8")
CHART_JS = re.sub(r"//# sourceMappingURL=.*", "", CHART_JS)

PARQUET = ROOT / "01_data" / "00_derived" / "sales_fact.parquet"
SAP_MAP = ROOT / "03_analytics" / "Isuzu" / "prism" / "data" / "sap_sold_to_mapping.csv"
MASTER = ROOT / "03_analytics" / "Isuzu" / "prism" / "data" / "distributor_master_mapping.csv"
CATALOG = ROOT / "01_data" / "00_derived" / "parts_catalog_dimension.csv"
GPS_CSV = ROOT / "01_data" / "00_derived" / "gps_spu_by_distributor.csv"
PMS_CAP = ROOT / "01_data" / "00_derived" / "pms_capture_by_db_year.csv"

# Optional — only attempted for PORTUGAL / UMI; missing files are skipped, not fatal.
IDS_CANDIDATES: dict[str, list[Path]] = {
    "PORTUGAL": [
        ROOT / "01_data" / "90_INBOX" / "IDS_2026" / "rankings" / "Portugal_dealer_ranking.xlsx",
        ROOT / "01_data" / "90_INBOX" / "IDS_2026" / "Portugal_dealer_ranking.xlsx",
    ],
    "UMI": [
        ROOT / "01_data" / "90_INBOX" / "IDS_2026" / "rankings" / "Israel_dealer_ranking.xlsx",
        ROOT / "01_data" / "90_INBOX" / "IDS_2026" / "Israel_dealer_ranking.xlsx",
    ],
}

BILLING_MAX = "2026-03-31"
FISCAL_DEFINITION = "ISZE FY = Apr–Mar. FY2024 = Apr2024–Mar2025; FY2025 = Apr2025–Mar2026 (both complete)."

NON_PART = {
    "TRANSPORT",
    "REBATE",
    "LATE PAYMENT INTEREST",
    "DISRACK01",
    "5874123810",
    "5874123811",
    "5874123812",
}
CREDIT_SATY = {"CR", "RE"}
PMS_BASKET_CATS = {
    "oil_filter",
    "fuel_filter",
    "blower_filter",
    "air_filter",
    "brake_pad",
    "brake_pad_front",
    "brake_pad_rear",
    "urea_filter",
}

PMS_ASSUMPTION = (
    "Service-interval assumption (IML service schedule modelling): "
    "filters ≈ 1.25× per year; wear items ≈ 0.5× per year. "
    "Capture % = actual quantity ÷ expected demand under this schedule. "
    "Primary lens = total capture (genuine share is secondary)."
)

VERDICT_TEXT = {
    "local_leak": "Customer-local decline — part still sold elsewhere in the network",
    "network_fade": "Network-wide decline",
    "channel_shift": "Volume appears to have shifted to other distributors",
    "mixed": "Mixed signal — no clear network pattern",
}

NAVY = "#0b1f33"
NAVY_MID = "#173a5c"
NAVY_LIGHT = "#234f7d"
TERRA = "#c45c26"

# ---------- customer registry ----------

CUSTOMER_CODES = [
    "IUK", "ITUK", "UTI", "UMI", "GERMANY", "BELGIUM", "PORTUGAL", "NORWAY",
    "SWEDEN", "IRELAND", "UKRAINE", "GREECE", "CYPRUS", "HUNGARY", "FINLAND",
    "ARMENIA", "MALTA", "ROMANIA", "KAZAKHSTAN", "DENMARK", "ICELAND", "PALESTINE",
]

LABEL_OVERRIDE = {
    "PORTUGAL": "I Motors",
    "IUK": "IUK",
    "ITUK": "ITUK",
    "UTI": "UTI",
    "UMI": "UMI",
}
FILE_STEM_OVERRIDE = {
    "PORTUGAL": "Imotors",
    "UMI": "UMI",
}
CODE_TO_STUDY_KEY = {"PORTUGAL": "IMOTORS", "UMI": "UMI"}


def build_customers_registry(master: pd.DataFrame) -> dict[str, dict]:
    idx = master.set_index("distributor_code")
    reg = {}
    for code in CUSTOMER_CODES:
        row = idx.loc[code] if code in idx.index else None
        country = str(row["country"]) if row is not None and pd.notna(row.get("country")) else code.title()
        segment_lcv = bool(row is not None and str(row.get("segment_lcv", "")).strip().upper() == "YES")
        label = LABEL_OVERRIDE.get(code, country)
        stem_name = FILE_STEM_OVERRIDE.get(code, code)
        forbid_uti = code == "UMI"
        reg[code] = {
            "code": code,
            "label": label,
            "country": country,
            "segment_lcv": segment_lcv,
            "file_stem": f"ISZE_{stem_name}_Deep_Study_V4",
            "title": f"{label} — Parts Sales Deep Study",
            "subtitle": f"{country} · customer briefing V4",
            "include_source": code in CODE_TO_STUDY_KEY,
            "include_ids": code in IDS_CANDIDATES,
            "forbid_uti": forbid_uti,
        }
    return reg


# ---------- small helpers ----------

def money(x: float) -> float:
    return round(float(x or 0), 2)


def eur(x) -> str:
    if x is None:
        return "n/a"
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
        if "FILTER" in d:
            return "Filters (unmapped)", "Filter"
        return "Catalogue gap", "Unmapped PN"
    if fam.lower().startswith("other"):
        return (grp or "Review / misc"), (grp or fam)
    return fam, (grp or fam)


def scrub_uti(text: str) -> str:
    """Defensive scrub — the UMI pack must never contain the string UTI."""
    return re.sub(r"\bUTI\b", "the wider network", text)


def scrub_uti_deep(obj):
    if isinstance(obj, str):
        return scrub_uti(obj)
    if isinstance(obj, list):
        return [scrub_uti_deep(v) for v in obj]
    if isinstance(obj, dict):
        return {scrub_uti_deep(k): scrub_uti_deep(v) for k, v in obj.items()}
    return obj


# ---------- data loaders ----------

def load_sales() -> pd.DataFrame:
    sap = pd.read_csv(SAP_MAP).rename(columns={"sap_sold_to_pt": "sold_to_sap"})
    sap["sold_to_sap"] = pd.to_numeric(sap["sold_to_sap"], errors="coerce")
    cols = ["billing_date", "sold_to_sap", "part_number", "description", "billed_qty", "net_sales_value", "saty"]
    df = ds.dataset(PARQUET).to_table(columns=cols).to_pandas()
    df["billing_date"] = pd.to_datetime(df["billing_date"])
    df["sold_to_sap"] = pd.to_numeric(df["sold_to_sap"], errors="coerce")
    df = df.merge(sap[["sold_to_sap", "distributor_code"]], on="sold_to_sap", how="left")
    df["part_number"] = df["part_number"].astype(str).str.strip()
    df["description"] = df["description"].fillna("").astype(str)
    df["saty"] = df["saty"].fillna("(blank)").astype(str)
    df["billed_qty"] = pd.to_numeric(df["billed_qty"], errors="coerce").fillna(0.0)
    df["net_sales_value"] = pd.to_numeric(df["net_sales_value"], errors="coerce").fillna(0.0)
    pn_u = df["part_number"].str.upper()
    desc_u = df["description"].str.upper()
    mask = pn_u.isin(NON_PART) | pn_u.str.contains("REBATE", na=False) | desc_u.str.contains("REBATE", na=False)
    df = df[~mask].copy()
    df["fiscal_year"] = df["billing_date"].dt.year.where(
        df["billing_date"].dt.month >= 4, df["billing_date"].dt.year - 1
    ).astype(int)
    df["ym"] = df["billing_date"].dt.to_period("M").astype(str)
    df["is_credit"] = df["saty"].isin(CREDIT_SATY) | (df["net_sales_value"] < 0)
    return df


def load_catalog() -> pd.DataFrame:
    cat = pd.read_csv(
        CATALOG,
        usecols=["part_number", "pr00_family", "pr00_group", "pms_category"],
        dtype=str,
        low_memory=False,
    )
    cat["part_number"] = cat["part_number"].astype(str).str.strip()
    return cat.drop_duplicates("part_number")


def load_master() -> pd.DataFrame:
    return pd.read_csv(MASTER)


def load_gps_df() -> pd.DataFrame:
    return pd.read_csv(GPS_CSV)


def load_pms_df() -> pd.DataFrame:
    return pd.read_csv(PMS_CAP)


def ids_country_avg(path: Path) -> dict:
    import openpyxl

    wb = openpyxl.load_workbook(path, data_only=True, read_only=True)
    ws = wb[wb.sheetnames[0]]
    rows = list(ws.iter_rows(values_only=True))
    header = [str(c).strip() if c is not None else "" for c in rows[0]]
    idx_pts = next(i for i, h in enumerate(header) if "points" in h.lower())
    dealers = []
    for r in rows[1:]:
        if r and isinstance(r[0], (int, float)) and r[idx_pts] is not None:
            try:
                dealers.append(float(r[idx_pts]))
            except Exception:
                pass
    if not dealers:
        return {}
    return {
        "n_dealers": len(dealers),
        "avg_pct": round(sum(dealers) / len(dealers), 2),
        "max_pct": round(max(dealers), 2),
        "min_pct": round(min(dealers), 2),
    }


def load_ids(code: str) -> dict | None:
    for path in IDS_CANDIDATES.get(code, []):
        if path.exists():
            try:
                ids = ids_country_avg(path)
            except Exception as exc:
                print(f"  IDS load failed for {code} ({path.name}): {exc}")
                return None
            if ids:
                label = (
                    "Portugal dealer network (IDS 2026)"
                    if code == "PORTUGAL"
                    else "Israel dealer network — UMI participants (IDS 2026)"
                )
                ids["label"] = label
                return ids
    return None


# ---------- GPS ----------

def gps_row(gps_df: pd.DataFrame, code: str, year: int = 2025) -> dict:
    r = gps_df[(gps_df["distributor_code"] == code) & (gps_df["year"] == year)]
    if r.empty:
        return {}
    row = r.iloc[0]
    cap = row.get("gps_capture_vs_max")
    uio = row.get("uio_units")
    spu = row.get("spend_per_unit_eur")
    max_spend = row.get("max_spend_eur")
    return {
        "year": year,
        "gps_pct": None if pd.isna(cap) else round(100 * float(cap), 1),
        "traffic_light": row.get("traffic_light_v9") or row.get("traffic_light"),
        "uio": None if pd.isna(uio) else int(float(uio)),
        "spu_eur": None if pd.isna(spu) else round(float(spu), 1),
        "sales_eur": money(row.get("total_sales_eur")),
        "max_spend_eur": None if pd.isna(max_spend) else money(max_spend),
    }


def gps_time_series(gps_df: pd.DataFrame, code: str) -> list[dict]:
    """Now vs past capture % only — never peer countries."""
    sub = gps_df[gps_df["distributor_code"] == code].set_index("year")
    out = []
    max_2025 = None
    if 2025 in sub.index and pd.notna(sub.loc[2025].get("max_spend_eur")):
        max_2025 = float(sub.loc[2025]["max_spend_eur"])
    if 2024 in sub.index and max_2025:
        sales = float(sub.loc[2024]["total_sales_eur"])
        out.append({
            "label": "CY2024",
            "gps_pct": round(100 * sales / max_2025, 1),
            "note": "trend proxy: CY2024 sales ÷ CY2025 max-spend target",
        })
    if 2025 in sub.index and pd.notna(sub.loc[2025].get("gps_capture_vs_max")):
        out.append({
            "label": "CY2025",
            "gps_pct": round(100 * float(sub.loc[2025]["gps_capture_vs_max"]), 1),
            "note": "verified capture vs max",
        })
    if 2026 in sub.index and pd.notna(sub.loc[2026].get("max_spend_eur")):
        sales = float(sub.loc[2026]["total_sales_eur"])
        mx = float(sub.loc[2026]["max_spend_eur"])
        run = 100 * (sales * 4) / mx if mx else None
        out.append({
            "label": "CY2026 run-rate",
            "gps_pct": round(run, 1) if run is not None else None,
            "note": "YTD sales×4 ÷ CY2026 max-spend (pace, not final year)",
        })
    return out


def network_fy_yoy(df: pd.DataFrame, master: pd.DataFrame, code: str, is_lcv: bool) -> float | None:
    """Single allowed benchmark: LCV (excl. UTI, excl. self) or all-DB average FY YoY %."""
    if is_lcv:
        codes = set(master.loc[master["segment_lcv"].astype(str).str.upper() == "YES", "distributor_code"])
        codes.discard("UTI")
    else:
        codes = set(master["distributor_code"].astype(str))
    codes.discard(code)
    sub = df[df["distributor_code"].isin(codes) & df["fiscal_year"].isin([2024, 2025])]
    if sub.empty:
        return None
    t24 = float(sub.loc[sub["fiscal_year"] == 2024, "net_sales_value"].sum())
    t25 = float(sub.loc[sub["fiscal_year"] == 2025, "net_sales_value"].sum())
    if t24 <= 0:
        return None
    return round(100 * (t25 - t24) / t24, 1)


# ---------- PMS ----------

def pms_weighted(pms_df: pd.DataFrame, code: str, year: int) -> dict | None:
    """Weighted total/genuine capture = sum(actual) / sum(expected) across the
    total (or genuine) line_type categories, canonical model_bucket scope."""
    sub = pms_df[(pms_df["distributor_code"] == code) & (pms_df["year"] == year) & (pms_df["scope"] == "model_bucket")]
    if sub.empty:
        return None

    def wtd(frame: pd.DataFrame) -> float | None:
        exp = float(frame["expected_qty"].sum())
        act = float(frame["actual_qty"].sum())
        return round(100 * act / exp, 1) if exp else None

    total_pct = wtd(sub[sub["line_type"] == "total"])
    genuine_pct = wtd(sub[sub["line_type"] == "genuine"])
    if total_pct is None and genuine_pct is None:
        return None
    return {"total_pct": total_pct, "genuine_pct": genuine_pct}


def pms_capture_series(pms_df: pd.DataFrame, code: str) -> list[dict]:
    out = []
    for y in (2024, 2025):
        w = pms_weighted(pms_df, code, y)
        if w and w["total_pct"] is not None:
            out.append({"label": f"CY{y}", "capture_pct": w["total_pct"]})
    return out


def pms_total_cats(pms_df: pd.DataFrame, code: str, year: int) -> dict:
    """Total-line PMS categories with diagnosis — never silent-cap at 100%."""
    sub_all = pms_df[(pms_df["distributor_code"] == code) & (pms_df["year"] == year) & (pms_df["scope"] == "model_bucket")]
    if sub_all.empty:
        return {
            "available": False,
            "chart": [],
            "excluded": [],
            "footnotes": [],
            "note": f"PMS capture is not modelled for this distributor (no model_bucket UIO coverage for CY{year}).",
        }

    sub = sub_all[sub_all["line_type"] == "total"]
    gen = sub_all[sub_all["line_type"] == "genuine"].set_index("pms_category")

    chart, excluded, footnotes = [], [], []
    for _, r in sub.iterrows():
        cat = r["pms_category"]
        label = r["category_label"] if pd.notna(r.get("category_label")) else cat
        rate = float(r["capture_rate"])
        cap_pct = round(100 * rate, 1)
        exp = float(r["expected_qty"]) if pd.notna(r["expected_qty"]) else None
        act = float(r["actual_qty"]) if pd.notna(r["actual_qty"]) else None
        uio = float(r["uio_units"]) if pd.notna(r["uio_units"]) else None

        if cat == "blower_filter" and rate > 1.0:
            excluded.append({
                "category": label,
                "raw_capture_pct": cap_pct,
                "reason": (
                    f"Excluded from chart: capture {cap_pct}% (actual {act:.0f} vs expected {exp:.0f} on UIO "
                    f"{uio:.0f}). Cabin/blower interval was modelled at 0.25×/yr (too low); network now uses "
                    "1.0× like other filters — this is a model artefact, not evidence of overselling."
                ),
            })
            continue

        chart.append({"category": label, "pms_category": cat, "capture_pct": cap_pct, "expected_qty": exp, "actual_qty": act})

        if cat == "brake_pad" and rate >= 0.80:
            g_pct = round(100 * float(gen.loc[cat]["capture_rate"]), 1) if cat in gen.index else None
            footnotes.append({
                "category": label,
                "text": (
                    f"Brake pad total capture {cap_pct}% is near the model ceiling (actual {act:.0f} / "
                    f"expected {exp:.0f}, UIO {uio:.0f}). Genuine-only is {g_pct}% — the headline is mix-led "
                    "(genuine + BVP), not pure genuine saturation. Treat as 'verify', not a trophy."
                ),
            })
        elif rate > 1.0:
            footnotes.append({
                "category": label,
                "text": (
                    f"{label} shows {cap_pct}% (actual {act:.0f} / expected {exp:.0f}). Above 100% usually means "
                    "expected demand is too low (interval/UIO/scope) or a qty double-count — investigate before "
                    "reading this as overselling."
                ),
            })

    chart.sort(key=lambda x: x["capture_pct"])
    return {"available": True, "chart": chart, "excluded": excluded, "footnotes": footnotes, "note": None}


# ---------- network part-number quantity table (for channel-shift test) ----------

def build_network_qty_table(df: pd.DataFrame) -> pd.DataFrame:
    """Total network qty per (part_number, fiscal_year), non-credit rows only,
    for the two complete fiscal years — used as the 'rest of network' baseline."""
    sub = df[df["fiscal_year"].isin([2024, 2025]) & (~df["is_credit"])]
    net_by_pn_fy = sub.groupby(["part_number", "fiscal_year"])["billed_qty"].sum().unstack("fiscal_year")
    for y in (2024, 2025):
        if y not in net_by_pn_fy.columns:
            net_by_pn_fy[y] = 0.0
    return net_by_pn_fy.fillna(0.0)


def pn_depth_analysis(code: str, gq: pd.DataFrame, net_by_pn_fy: pd.DataFrame) -> dict:
    """gq = this customer's non-credit rows for fiscal_year in (2024, 2025)."""
    if gq.empty:
        return {"vanished": [], "new_pn": [], "droppers": [], "channel": [], "narrative": [], "thresholds_note": ""}

    piv_q = gq.groupby(["part_number", "fiscal_year"])["billed_qty"].sum().unstack("fiscal_year")
    piv_e = gq.groupby(["part_number", "fiscal_year"])["net_sales_value"].sum().unstack("fiscal_year")
    for y in (2024, 2025):
        if y not in piv_q.columns:
            piv_q[y] = 0.0
        if y not in piv_e.columns:
            piv_e[y] = 0.0
    piv_q = piv_q.fillna(0.0)
    piv_e = piv_e.fillna(0.0)
    desc_map = gq.groupby("part_number")["description"].agg(lambda s: s.iloc[0] if len(s) else "")

    full = pd.DataFrame({
        "q24": piv_q[2024], "q25": piv_q[2025],
        "e24": piv_e[2024], "e25": piv_e[2025],
    })
    full["description"] = full.index.map(desc_map).fillna("")
    full["delta_qty"] = full["q25"] - full["q24"]

    def row_dict(pn, r) -> dict:
        return {
            "part_number": pn,
            "description": (r["description"] or "")[:60].strip(),
            "fy24_qty": round(float(r["q24"]), 1),
            "fy25_qty": round(float(r["q25"]), 1),
            "fy24_eur": money(r["e24"]),
            "fy25_eur": money(r["e25"]),
            "delta_qty": round(float(r["delta_qty"]), 1),
        }

    vanished_mask = (full["q24"] > 0) & (full["q25"] == 0) & ((full["q24"] >= 10) | (full["e24"] >= 500))
    vanished = [row_dict(pn, r) for pn, r in full[vanished_mask].sort_values("q24", ascending=False).iterrows()][:12]

    new_mask = (full["q24"] == 0) & (full["q25"] > 0) & ((full["q25"] >= 10) | (full["e25"] >= 500))
    new_pn = [row_dict(pn, r) for pn, r in full[new_mask].sort_values("q25", ascending=False).iterrows()][:12]

    dropper_mask = (
        (full["q24"] > 0) & (full["q25"] > 0) & (full["q24"] >= 20) & (full["delta_qty"] <= -0.3 * full["q24"])
    )
    droppers_df = full[dropper_mask].copy()
    droppers_df["drop_pct"] = round(100 * droppers_df["delta_qty"] / droppers_df["q24"], 1)
    droppers = []
    for pn, r in droppers_df.sort_values("delta_qty").iterrows():
        rd = row_dict(pn, r)
        rd["drop_pct"] = float(r["drop_pct"])
        droppers.append(rd)
    droppers = droppers[:12]

    # crash candidates for the channel-shift test: biggest negative qty deltas
    crash_pool = full[(full["q24"] >= 10) & (full["delta_qty"] < 0)].sort_values("delta_qty").head(12)
    channel = []
    for pn, r in crash_pool.iterrows():
        cust_delta = float(r["delta_qty"])
        mag = abs(cust_delta)
        total_q24 = float(net_by_pn_fy.loc[pn, 2024]) if pn in net_by_pn_fy.index else float(r["q24"])
        total_q25 = float(net_by_pn_fy.loc[pn, 2025]) if pn in net_by_pn_fy.index else float(r["q25"])
        rest_q24 = max(total_q24 - float(r["q24"]), 0.0)
        rest_q25 = max(total_q25 - float(r["q25"]), 0.0)
        rest_delta = rest_q25 - rest_q24

        if mag <= 0:
            verdict = "mixed"
        elif rest_delta > 0 and rest_delta >= 0.3 * mag:
            verdict = "channel_shift"
        elif rest_delta <= -0.3 * mag:
            verdict = "network_fade"
        elif rest_q25 > 0:
            verdict = "local_leak"
        else:
            verdict = "mixed"

        channel.append({
            "part_number": pn,
            "description": (r["description"] or "")[:60].strip(),
            "customer_delta_qty": round(cust_delta, 1),
            "rest_delta_qty": round(rest_delta, 1),
            "rest_q25_qty": round(rest_q25, 1),
            "verdict": verdict,
            "verdict_text": VERDICT_TEXT[verdict],
        })

    counts = {"local_leak": 0, "network_fade": 0, "channel_shift": 0, "mixed": 0}
    for r in channel:
        counts[r["verdict"]] += 1
    narrative = []
    if counts["local_leak"]:
        narrative.append(
            f"{counts['local_leak']} of the biggest quantity drops look customer-local — the part is still moving "
            "elsewhere in the network, so check local stock, price, or competitive pressure first."
        )
    if counts["network_fade"]:
        narrative.append(
            f"{counts['network_fade']} decline(s) are network-wide, not specific to this customer — likely a "
            "parc-age / model-mix effect rather than something to fix locally."
        )
    if counts["channel_shift"]:
        narrative.append(
            f"{counts['channel_shift']} decline(s) coincide with a similar-sized gain elsewhere in the network — "
            "worth checking for cross-border buying or a change in SAP sold-to routing."
        )
    if not narrative:
        narrative.append("No large quantity-crash part numbers met the screening threshold for this distributor.")

    thresholds_note = (
        "Vanished / new PN threshold: min FY24 (or FY25) qty ≥10 or €≥500. Continuing droppers: both years >0, "
        "quantity down ≥30% with FY24 qty ≥20. Credit / return lines (SaTy CR/RE or negative net value) are "
        "excluded from all quantity-based analysis on this page."
    )

    return {
        "vanished": vanished,
        "new_pn": new_pn,
        "droppers": droppers,
        "channel": channel,
        "narrative": narrative,
        "thresholds_note": thresholds_note,
    }


def pms_basket_qty(gq_cat: pd.DataFrame) -> list[dict]:
    sub = gq_cat[gq_cat["pms_category"].isin(PMS_BASKET_CATS)]
    if sub.empty:
        return []
    piv = sub.groupby(["pms_category", "fiscal_year"])["billed_qty"].sum().unstack("fiscal_year")
    for y in (2024, 2025):
        if y not in piv.columns:
            piv[y] = 0.0
    piv = piv.fillna(0.0)
    rows = []
    for cat, r in piv.iterrows():
        q24 = float(r[2024])
        q25 = float(r[2025])
        if q24 <= 0 and q25 <= 0:
            continue
        yoy = round(100 * (q25 - q24) / q24, 1) if q24 else None
        rows.append({"pms_category": cat, "fy24_qty": round(q24, 1), "fy25_qty": round(q25, 1), "yoy_pct": yoy})
    return sorted(rows, key=lambda r: -r["fy25_qty"])


# ---------- cross-check / asks (generic, data-driven) ----------

def build_crosscheck(meta: dict, yoy, gps: dict, pms_wtd: dict | None, ids: dict | None, net_yoy) -> list[dict]:
    findings = []
    gps_pct = gps.get("gps_pct")
    pms_pct = pms_wtd.get("total_pct") if pms_wtd else None

    if yoy is not None:
        tone = "align" if yoy >= 0 else "tension"
        vs_net = ""
        if net_yoy is not None:
            vs_net = f" (network average {net_yoy:+.1f}%)"
            if (yoy >= 0) != (net_yoy >= 0) or abs(yoy - net_yoy) >= 10:
                tone = "tension"
        findings.append({"tone": tone, "text": f"FY2025 sales are {yoy:+.1f}% vs FY2024{vs_net}."})

    if gps_pct is not None:
        if yoy is not None and gps_pct >= 70 and yoy < 0:
            findings.append({
                "tone": "tension",
                "text": (
                    f"GPS capture vs max looks healthy ({gps_pct}%) while fiscal sales declined "
                    f"({yoy:+.1f}%) — capture % and volume are telling different stories."
                ),
            })
        elif gps_pct < 40:
            findings.append({
                "tone": "tension",
                "text": f"GPS capture vs max is only {gps_pct}% — meaningful wallet headroom versus the modelled ceiling.",
            })
        else:
            findings.append({"tone": "note", "text": f"GPS capture vs max is {gps_pct}%."})

    if pms_pct is not None:
        tone = "tension" if pms_pct < 50 else "note"
        room = "significant" if pms_pct < 50 else "some"
        findings.append({
            "tone": tone,
            "text": f"PMS total capture is {pms_pct}% under the IML service-schedule assumption — {room} room on scheduled-maintenance parts.",
        })
    else:
        findings.append({
            "tone": "note",
            "text": "PMS capture is not modelled for this distributor (insufficient UIO / parc coverage in the model-bucket scope).",
        })

    if ids:
        findings.append({
            "tone": "note",
            "text": f"{ids['label']} averages {ids.get('avg_pct')}% points (n={ids.get('n_dealers')}).",
        })

    return findings


def build_asks(meta: dict, depth: dict, pms_wtd: dict | None, gps: dict) -> list[str]:
    label = meta["label"]
    asks = [
        f"Which two or three part-number families should {label} and ISZE prioritise for joint action over the next two quarters?",
    ]
    if depth["vanished"]:
        top = depth["vanished"][0]
        asks.append(
            f"Part number {top['part_number']} ({top['description'] or 'no description'}) went from FY2024 "
            "sales to zero in FY2025 — is this a stock, supersession, or competitive-loss issue?"
        )
    n_shift = sum(1 for r in depth["channel"] if r["verdict"] == "channel_shift")
    if n_shift:
        asks.append(
            f"{n_shift} declining part number(s) show volume that may have shifted to other distributors — "
            "is there cross-border buying or a SAP sold-to routing change we should check?"
        )
    if pms_wtd and pms_wtd.get("total_pct") is not None and pms_wtd["total_pct"] < 60:
        asks.append("PMS total capture has clear headroom under the IML service-schedule assumption — which categories should we pilot with dealers first?")
    if gps.get("gps_pct") is not None and gps["gps_pct"] < 50:
        asks.append("GPS capture vs max still has real headroom — what would it take to close the gap over the next 12 months?")
    if meta.get("forbid_uti"):
        asks.append("IDS Israel covers the UMI dealer network only — which UMI dealers should we prioritise for parts process coaching?")
    asks.append("Which declining or silent part numbers should return to active promotion or stock in FY2026?")
    return asks


# ---------- pack builder ----------

def cy_sales(g: pd.DataFrame) -> dict[int, float]:
    cy = g["billing_date"].dt.year
    t = g.groupby(cy)["net_sales_value"].sum()
    return {int(y): money(v) for y, v in t.items()}


def load_h1_context(code: str) -> tuple[list, dict]:
    key = CODE_TO_STUDY_KEY.get(code)
    if not key:
        return [], {}
    pbi = STUDY_DATA.get("pbi_h1_2026", {})
    cust = dict(pbi.get("customers", {}).get(key, {}))
    drill = pbi.get("drills", {}).get(key, {})
    source = []
    try:
        source = list(drill.get("source", []))
    except Exception:
        source = []
    if drill.get("sales_eur") and not cust.get("sales_eur"):
        cust["sales_eur"] = drill.get("sales_eur")
    return source, cust


def build_customer_pack(
    code: str,
    meta: dict,
    df: pd.DataFrame,
    cat: pd.DataFrame,
    master: pd.DataFrame,
    gps_df: pd.DataFrame,
    pms_df: pd.DataFrame,
    net_by_pn_fy: pd.DataFrame,
) -> dict:
    g = df[df["distributor_code"] == code].copy()
    g = g.merge(cat, on="part_number", how="left")

    fam_labels, grp_labels = [], []
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

    monthly = (
        g[g["fiscal_year"].isin([2024, 2025])]
        .groupby("ym", as_index=False)["net_sales_value"]
        .sum()
        .sort_values("ym")
    )
    monthly_rows = [{"ym": r.ym, "sales_eur": money(r.net_sales_value)} for r in monthly.itertuples()]

    def saty_fy(sub, fy):
        s = sub[sub["fiscal_year"] == fy]
        t = float(s["net_sales_value"].sum()) or 1
        rows = s.groupby("saty", as_index=False)["net_sales_value"].sum().sort_values("net_sales_value", ascending=False)
        return [
            {"saty": r.saty, "sales_eur": money(r.net_sales_value), "share_pct": round(100 * float(r.net_sales_value) / t, 1)}
            for r in rows.itertuples()
        ]

    def group_compare():
        a = fy24.groupby("group_label")["net_sales_value"].sum()
        b = fy25.groupby("group_label")["net_sales_value"].sum()
        keys = sorted(set(a.index) | set(b.index), key=lambda k: -float(b.get(k, 0)))
        rows = []
        for k in keys:
            e24 = float(a.get(k, 0))
            e25 = float(b.get(k, 0))
            if (not tot25 or e25 < 0.01 * tot25) and (not tot24 or e24 < 0.01 * tot24):
                continue
            rows.append({
                "group": k,
                "fy24_eur": money(e24),
                "fy25_eur": money(e25),
                "fy24_share": round(100 * e24 / tot24, 1) if tot24 else 0,
                "fy25_share": round(100 * e25 / tot25, 1) if tot25 else 0,
                "yoy_pct": round(100 * (e25 - e24) / e24, 1) if e24 else None,
            })
        return rows[:12]

    def family_share_compare():
        a = fy24.groupby("family_bucket")["net_sales_value"].sum()
        b = fy25.groupby("family_bucket")["net_sales_value"].sum()
        keys = sorted(set(a.index) | set(b.index), key=lambda k: -float(b.get(k, 0)))
        rows = []
        for k in keys:
            s24 = round(100 * float(a.get(k, 0)) / tot24, 1) if tot24 else 0.0
            s25 = round(100 * float(b.get(k, 0)) / tot25, 1) if tot25 else 0.0
            if s24 < 0.5 and s25 < 0.5:
                continue
            rows.append({"family": k, "fy24_share_pct": s24, "fy25_share_pct": s25})
        return rows[:12]

    def top_pn(sub, tot, n=20):
        rows = (
            sub.groupby(["part_number", "description"], as_index=False)["net_sales_value"]
            .sum()
            .sort_values("net_sales_value", ascending=False)
            .head(n)
        )
        out = []
        for i, r in enumerate(rows.itertuples(), 1):
            out.append({
                "rank": i,
                "part_number": r.part_number,
                "description": (r.description or "")[:60].strip(),
                "sales_eur": money(r.net_sales_value),
                "share_pct": round(100 * float(r.net_sales_value) / tot, 2) if tot else 0,
            })
        return out

    a = fy24.groupby(["part_number", "description"])["net_sales_value"].sum()
    b = fy25.groupby(["part_number", "description"])["net_sales_value"].sum()
    keys = set(a.index) | set(b.index)
    movers = []
    for k in keys:
        e24 = float(a.get(k, 0))
        e25 = float(b.get(k, 0))
        movers.append({
            "part_number": k[0],
            "description": (k[1] or "")[:60].strip(),
            "fy24_eur": money(e24),
            "fy25_eur": money(e25),
            "delta_eur": money(e25 - e24),
        })
    gainers = sorted(movers, key=lambda x: -x["delta_eur"])[:15]
    losers = sorted(movers, key=lambda x: x["delta_eur"])[:15]
    silent = [
        m for m in sorted(movers, key=lambda x: -x["fy24_eur"])
        if m["fy24_eur"] >= 2000 and m["fy25_eur"] <= 0.05 * m["fy24_eur"]
    ][:12]

    def concentration(sub, tot):
        s = sub.groupby("part_number")["net_sales_value"].sum().sort_values(ascending=False)
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

    pms_map = cat.set_index("part_number")["pms_category"].to_dict() if "pms_category" in cat.columns else {}

    def enrich(rows):
        out = []
        for r in rows:
            rr = dict(r)
            raw = pms_map.get(r["part_number"])
            if raw is None or (isinstance(raw, float) and math.isnan(raw)) or str(raw).lower() in ("nan", "none", ""):
                rr["pms_category"] = ""
            else:
                rr["pms_category"] = str(raw)
            out.append(rr)
        return out

    # PN depth (qty-based, non-credit rows only)
    gq = g[(~g["is_credit"]) & (g["fiscal_year"].isin([2024, 2025]))]
    depth = pn_depth_analysis(code, gq, net_by_pn_fy)
    pms_basket = pms_basket_qty(gq)

    gps = gps_row(gps_df, code, 2025)
    gps_series = gps_time_series(gps_df, code)
    pms_wtd = pms_weighted(pms_df, code, 2025)
    pms_series_cy = pms_capture_series(pms_df, code)
    pms_pack = pms_total_cats(pms_df, code, 2025)

    ids = load_ids(code) if meta["include_ids"] else None

    net_yoy = network_fy_yoy(df, master, code, meta["segment_lcv"])
    network_compare = {
        "customer_yoy_pct": yoy,
        "network_yoy_pct": net_yoy,
        "label": (
            f"FY2025 vs FY2024 sales change — {meta['label']} vs "
            + ("LCV network average" if meta["segment_lcv"] else "all-distributor network average")
        ),
    }

    source, h1 = load_h1_context(code) if meta["include_source"] else ([], {})

    cy_map = cy_sales(g)
    reconcile = []
    gps_cy25 = gps.get("sales_eur")
    cy25_billing = cy_map.get(2025)
    if gps_cy25 and cy25_billing is not None:
        dlt = money(cy25_billing - gps_cy25)
        pct_d = round(100 * (cy25_billing - gps_cy25) / gps_cy25, 2) if gps_cy25 else None
        reconcile.append({
            "period": "CY2025",
            "pbi_or_gps_label": "ISZE GPS wallet (CY)",
            "reference_eur": gps_cy25,
            "isze_billing_eur": cy25_billing,
            "delta_eur": dlt,
            "delta_pct": pct_d,
            "note": "Billing vs GPS CY sales — small gaps usually reflect rebate/non-part exclusion or warranty timing.",
        })
    if h1.get("sales_eur") and cy_map.get(2026) is not None:
        share = round(100 * cy_map[2026] / h1["sales_eur"], 1) if h1["sales_eur"] else None
        reconcile.append({
            "period": "H1 CY2026 vs Q1 billing",
            "pbi_or_gps_label": "Power BI H1 (Jan–Jun)",
            "reference_eur": money(h1["sales_eur"]),
            "isze_billing_eur": cy_map.get(2026),
            "delta_eur": None,
            "delta_pct": None,
            "note": f"ISZE billing only through {BILLING_MAX} (partial-period overlap ≈{share}% of PBI H1).",
        })
    reconcile.append({
        "period": "FY2025",
        "pbi_or_gps_label": "ISZE billing FY (ex-rebate)",
        "reference_eur": None,
        "isze_billing_eur": money(tot25),
        "delta_eur": None,
        "delta_pct": None,
        "note": "Fiscal Apr–Mar used for PN / SaTy / family analysis on this pack.",
    })

    cross = build_crosscheck(meta, yoy, gps, pms_wtd, ids, net_yoy)
    asks = build_asks(meta, depth, pms_wtd, gps)

    pack = {
        "code": code,
        "meta": meta,
        "generated": pd.Timestamp.today().date().isoformat(),
        "fiscal_definition": FISCAL_DEFINITION,
        "billing_max": BILLING_MAX,
        "fy24_eur": money(tot24),
        "fy25_eur": money(tot25),
        "fy_yoy_pct": yoy,
        "monthly": monthly_rows,
        "saty_fy24": saty_fy(g, 2024),
        "saty_fy25": saty_fy(g, 2025),
        "network_compare": network_compare,
        "groups": group_compare(),
        "families": family_share_compare(),
        "top_pn_fy24": top_pn(fy24, tot24),
        "top_pn_fy25": top_pn(fy25, tot25),
        "concentration_fy24": concentration(fy24, tot24),
        "concentration_fy25": concentration(fy25, tot25),
        "gainers": enrich(gainers),
        "losers": enrich(losers),
        "silent": enrich(silent),
        "depth": depth,
        "pms_basket": pms_basket,
        "gps": gps,
        "gps_series": gps_series,
        "pms_total_wtd_pct": pms_wtd.get("total_pct") if pms_wtd else None,
        "pms_genuine_wtd_pct": pms_wtd.get("genuine_pct") if pms_wtd else None,
        "pms_series_cy": pms_series_cy,
        "pms_cats": pms_pack["chart"],
        "pms_available": pms_pack["available"],
        "pms_note": pms_pack["note"],
        "pms_scope": "model_bucket",
        "pms_excluded": pms_pack["excluded"],
        "pms_footnotes": pms_pack["footnotes"],
        "pms_assumption": PMS_ASSUMPTION,
        "ids": ids,
        "source_h1": source,
        "h1_sales": h1,
        "reconcile": reconcile,
        "crosscheck": cross,
        "asks": asks,
        "rebate_note": "REBATE / freight / finance / tool placeholder lines excluded from PN rankings, movers, and part-number depth.",
    }
    if meta["forbid_uti"]:
        pack = scrub_uti_deep(pack)
    return pack


# ---------- HTML ----------

CSS = f"""
*{{box-sizing:border-box}}
html,body{{margin:0;padding:0;-webkit-print-color-adjust:exact;print-color-adjust:exact}}
body{{font-family:"Segoe UI",Helvetica,Arial,sans-serif;color:#222;background:#f7f4ee;font-size:15px;line-height:1.5}}
h1,h2,h3{{font-family:Georgia,"Times New Roman",serif;color:{NAVY};margin:0}}
.page{{max-width:980px;margin:0 auto;padding:2rem 1.4rem 1.2rem;min-height:70vh;border-bottom:1px solid #d9d3c8}}
@media print{{.page{{break-after:page;min-height:0;border:0}}.no-print{{display:none!important}}body{{background:#fff}}}}
.cover{{background:linear-gradient(155deg,{NAVY} 0%,{NAVY_MID} 55%,{NAVY_LIGHT} 100%);color:#eef1f6;padding:3.2rem 1.6rem 2.8rem}}
.cover .inner{{max-width:980px;margin:0 auto}}
.cover h1{{color:#fff;font-size:2.35rem;line-height:1.12}}
.cover .rule{{width:4.2rem;height:3px;background:{TERRA};margin:1rem 0 .9rem}}
.chip{{display:inline-block;background:rgba(255,255,255,.12);border:1px solid rgba(255,255,255,.22);padding:.2rem .65rem;border-radius:4px;font-size:.78rem;margin:.15rem .25rem .15rem 0}}
.nav{{position:sticky;top:0;z-index:20;background:#f7f4ee;border-bottom:1px solid #d9d3c8;padding:.4rem 1rem;display:flex;flex-wrap:wrap;gap:.3rem}}
.nav a{{font-size:.72rem;color:{NAVY};text-decoration:none;padding:.22rem .4rem;border:1px solid #d9d3c8;background:#fff}}
h2.sec{{font-size:1.4rem;margin:0 0 .65rem;padding-bottom:.3rem;border-bottom:2px solid {NAVY}}}
h2.sec .no{{color:{TERRA}}}
h3{{font-size:1.02rem;margin:1rem 0 .35rem}}
.grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:.65rem;margin:.85rem 0}}
.stat{{background:#fff;border:1px solid #d9d3c8;padding:.75rem .9rem}}
.stat .lbl{{font-size:.68rem;text-transform:uppercase;letter-spacing:.04em;color:#6b6256}}
.stat .val{{font-size:1.25rem;font-weight:700;color:{NAVY};margin-top:.08rem}}
.stat .sub{{font-size:.8rem;color:#6b6256}}
.good{{color:#2e7d54!important}}.bad{{color:#b23b3b!important}}.amber{{color:#a67c00!important}}
.callout{{border-left:3px solid {TERRA};background:#fff;padding:.75rem .95rem;margin:.85rem 0}}
.callout.warn{{border-left-color:#eda100}}.callout.ok{{border-left-color:#1d9e75}}
.assume{{border:1px solid #d9d3c8;background:#fff8f2;padding:.65rem .85rem;margin:.5rem 0 .8rem;font-size:.88rem;color:#3a342c}}
.chart{{position:relative;width:100%;height:300px;background:#fff;border:1px solid #d9d3c8;padding:.45rem;margin:.7rem 0}}
.chart.tall{{height:400px}}
.two{{display:grid;grid-template-columns:1fr 1fr;gap:1rem}}
@media(max-width:820px){{.two{{grid-template-columns:1fr}}}}
table{{width:100%;border-collapse:collapse;font-size:.84rem;background:#fff;margin:.6rem 0}}
th{{background:{NAVY};color:#fff;text-align:left;padding:.45rem .55rem;font-size:.7rem;text-transform:uppercase}}
td{{padding:.4rem .55rem;border-bottom:1px solid #d9d3c8}}
tbody tr:nth-child(even){{background:#faf8f4}}
td.num,.num{{text-align:right;font-variant-numeric:tabular-nums}}
code{{font-family:Consolas,monospace;font-size:.84em}}
.muted{{color:#6b6256;font-size:.88rem}}
.ask{{background:#fff;border:1px solid #d9d3c8;padding:.65rem .9rem;margin:.35rem 0}}
.ask .n{{color:{TERRA};font-weight:700;margin-right:.35rem}}
.footer{{max-width:980px;margin:0 auto;padding:1rem 1.4rem 2.2rem;font-size:.72rem;color:#6b6256}}
.tag{{display:inline-block;font-size:.7rem;padding:.12rem .4rem;border-radius:3px;margin-right:.3rem}}
.tag.ok{{background:#e6f5ef;color:#1d6b4f}}.tag.warn{{background:#fff3d6;color:#8a6500}}.tag.bad{{background:#fde8e8;color:#9b2c2c}}
.bullet{{background:#fff;border:1px solid #d9d3c8;border-left:3px solid {NAVY};padding:.6rem .85rem;margin:.35rem 0}}
"""


def _pn_rows(rows):
    return "".join(
        f"<tr><td>{r['rank']}</td><td><code>{r['part_number']}</code></td><td>{r['description']}</td>"
        f"<td class='num'>{eur(r['sales_eur'])}</td><td class='num'>{r['share_pct']:.1f}%</td></tr>"
        for r in rows[:12]
    )


def _mover_rows(rows, bad=False):
    cls = "bad" if bad else "good"
    return "".join(
        f"<tr><td><code>{r['part_number']}</code></td><td>{r['description']}</td>"
        f"<td class='num'>{eur(r['fy24_eur'])}</td><td class='num'>{eur(r['fy25_eur'])}</td>"
        f"<td class='num {cls}'>{eur(r['delta_eur'])}</td><td>{r.get('pms_category') or '—'}</td></tr>"
        for r in rows[:10]
    )


def _vanished_rows(rows):
    return "".join(
        f"<tr><td><code>{r['part_number']}</code></td><td>{r['description'] or '—'}</td>"
        f"<td class='num'>{r['fy24_qty']:.0f}</td><td class='num'>{eur(r['fy24_eur'])}</td></tr>"
        for r in rows
    )


def _new_rows(rows):
    return "".join(
        f"<tr><td><code>{r['part_number']}</code></td><td>{r['description'] or '—'}</td>"
        f"<td class='num'>{r['fy25_qty']:.0f}</td><td class='num'>{eur(r['fy25_eur'])}</td></tr>"
        for r in rows
    )


def _dropper_rows(rows):
    return "".join(
        f"<tr><td><code>{r['part_number']}</code></td><td>{r['description'] or '—'}</td>"
        f"<td class='num'>{r['fy24_qty']:.0f}</td><td class='num'>{r['fy25_qty']:.0f}</td>"
        f"<td class='num bad'>{r['drop_pct']:.0f}%</td></tr>"
        for r in rows
    )


def _channel_rows(rows):
    tag_cls = {"local_leak": "warn", "network_fade": "ok", "channel_shift": "bad", "mixed": "ok"}
    return "".join(
        f"<tr><td><code>{r['part_number']}</code></td><td>{r['description'] or '—'}</td>"
        f"<td class='num bad'>{r['customer_delta_qty']:.0f}</td><td class='num'>{r['rest_delta_qty']:+.0f}</td>"
        f"<td class='num'>{r['rest_q25_qty']:.0f}</td>"
        f"<td><span class='tag {tag_cls.get(r['verdict'], 'ok')}'>{r['verdict_text']}</span></td></tr>"
        for r in rows
    )


def render_html(pack: dict) -> str:
    meta = pack["meta"]
    yoy_cls = "good" if (pack["fy_yoy_pct"] or 0) >= 0 else "bad"

    sections = [("p1", "Scope")]
    sections.append(("p2", "Sales"))
    sections.append(("p3", "SaTy"))
    if meta["include_source"]:
        sections.append(("p3b", "Source"))
    sections.append(("p4", "GPS"))
    sections.append(("p5", "PMS"))
    sections.append(("p6", "Family"))
    sections.append(("p7", "Part numbers"))
    sections.append(("p8", "PN depth"))
    sections.append(("p9", "Movers"))
    sections.append(("p10", "Cross-check"))
    sections.append(("p11", "Asks"))
    numbered = [(sid, i + 1, label) for i, (sid, label) in enumerate(sections)]
    num = {sid: f"{n:02d}" for sid, n, _ in numbered}
    nav_html = "".join(f'<a href="#{sid}">{n:02d} {label}</a>' for sid, n, label in numbered)

    nc = pack.get("network_compare") or {}
    network_block = f"""
<h3>Only network benchmark (sales)</h3>
<p class="muted">{nc.get('label') or 'FY YoY vs network average'}</p>
<div class="chart"><canvas id="cNet"></canvas></div>
"""

    source_page = ""
    if meta["include_source"]:
        h1 = pack.get("h1_sales") or {}
        drill_sales = h1.get("sales_eur")
        src_note = f"H1 CY2026 sales {eur(drill_sales)} ({h1.get('yoy_pct')}% YoY) — Power BI source shares."
        source_page = f"""
<section class="page" id="p3b">
<h2 class="sec"><span class="no">{num['p3b']}</span> Source mix (H1 CY2026)</h2>
<div class="callout">{src_note}</div>
<p class="muted">Share of H1 sales by sourcing origin.</p>
<div class="chart tall"><canvas id="cSrc"></canvas></div>
</section>"""

    cross_html = ""
    for f in pack["crosscheck"]:
        tag = {"align": "ok", "tension": "warn", "note": "ok"}.get(f["tone"], "ok")
        cross_html += f"<div class='ask'><span class='tag {tag}'>{f['tone']}</span>{f['text']}</div>"

    rec_rows = "".join(
        f"<tr><td>{r['period']}</td><td>{r['pbi_or_gps_label']}</td>"
        f"<td class='num'>{eur(r['reference_eur']) if r.get('reference_eur') is not None else '—'}</td>"
        f"<td class='num'>{eur(r['isze_billing_eur']) if r.get('isze_billing_eur') is not None else '—'}</td>"
        f"<td class='num'>{eur(r['delta_eur']) if r.get('delta_eur') is not None else '—'}</td>"
        f"<td>{r.get('note') or ''}</td></tr>"
        for r in pack.get("reconcile") or []
    )
    rec_html = f"""
<h3>Power BI / GPS vs ISZE billing</h3>
<table><thead><tr><th>Period</th><th>External / GPS</th><th>Ref €</th><th>ISZE €</th><th>Δ</th><th>Note</th></tr></thead>
<tbody>{rec_rows}</tbody></table>
"""

    pms_extra = ""
    for ex in pack.get("pms_excluded") or []:
        pms_extra += f"<div class='callout warn'><strong>Excluded — {ex['category']} ({ex['raw_capture_pct']}%)</strong><br/>{ex['reason']}</div>"
    for fn in pack.get("pms_footnotes") or []:
        pms_extra += f"<div class='callout'><strong>{fn['category']}</strong><br/>{fn['text']}</div>"

    if pack["pms_available"]:
        pms_stats = f"""
<div class="grid">
<div class="stat"><div class="lbl">Total capture (weighted, CY2025)</div><div class="val">{pct(pack['pms_total_wtd_pct']/100) if pack['pms_total_wtd_pct'] is not None else 'n/a'}</div></div>
<div class="stat"><div class="lbl">Genuine capture (secondary)</div><div class="val">{pct(pack['pms_genuine_wtd_pct']/100) if pack['pms_genuine_wtd_pct'] is not None else 'n/a'}</div><div class="sub">Mix / quality lens</div></div>
<div class="stat"><div class="lbl">Scope</div><div class="val" style="font-size:1rem">{pack['pms_scope']}</div></div>
</div>
<h3>Category hit rate — total capture % (uncapped display, CY2025)</h3>
<div class="chart tall"><canvas id="cPms"></canvas></div>
{pms_extra}
<h3>Weighted total capture — CY2024 vs CY2025</h3>
<div class="chart"><canvas id="cPmsSeries"></canvas></div>
<p class="muted">No euro gap bars. Values above 100% are diagnosed or excluded with reason — never silently capped.</p>
"""
    else:
        pms_stats = f"<div class='callout warn'>{pack.get('pms_note') or 'PMS capture is not modelled for this distributor.'}</div>"

    asks_html = "".join(f"<div class='ask'><span class='n'>{i}.</span>{q}</div>" for i, q in enumerate(pack["asks"], 1))

    c24 = pack["concentration_fy24"]
    c25 = pack["concentration_fy25"]
    gps = pack["gps"]

    depth = pack["depth"]
    vanished_block = (
        f"<table><thead><tr><th>PN</th><th>Desc</th><th>FY24 qty</th><th>FY24 €</th></tr></thead>"
        f"<tbody>{_vanished_rows(depth['vanished']) or '<tr><td colspan=4 class=\"muted\">None above threshold.</td></tr>'}</tbody></table>"
    )
    new_block = (
        f"<table><thead><tr><th>PN</th><th>Desc</th><th>FY25 qty</th><th>FY25 €</th></tr></thead>"
        f"<tbody>{_new_rows(depth['new_pn']) or '<tr><td colspan=4 class=\"muted\">None above threshold.</td></tr>'}</tbody></table>"
    )
    dropper_block = (
        f"<table><thead><tr><th>PN</th><th>Desc</th><th>FY24 qty</th><th>FY25 qty</th><th>Δ%</th></tr></thead>"
        f"<tbody>{_dropper_rows(depth['droppers']) or '<tr><td colspan=5 class=\"muted\">None above threshold.</td></tr>'}</tbody></table>"
    )
    channel_block = (
        f"<table><thead><tr><th>PN</th><th>Desc</th><th>Customer Δqty</th><th>Rest-of-network Δqty</th>"
        f"<th>Rest FY25 qty</th><th>Verdict</th></tr></thead>"
        f"<tbody>{_channel_rows(depth['channel']) or '<tr><td colspan=6 class=\"muted\">No qualifying crash part numbers.</td></tr>'}</tbody></table>"
    )
    narrative_html = "".join(f"<div class='bullet'>{n}</div>" for n in depth["narrative"])
    basket = pack.get("pms_basket") or []
    basket_block = ""
    if basket:
        rows = "".join(
            f"<tr><td>{r['pms_category']}</td><td class='num'>{r['fy24_qty']:.0f}</td>"
            f"<td class='num'>{r['fy25_qty']:.0f}</td>"
            f"<td class='num'>{('%+.1f%%' % r['yoy_pct']) if r['yoy_pct'] is not None else 'n/a'}</td></tr>"
            for r in basket
        )
        basket_block = f"""
<h3>PMS-filter basket — quantity YoY</h3>
<table><thead><tr><th>Category</th><th>FY24 qty</th><th>FY25 qty</th><th>YoY %</th></tr></thead>
<tbody>{rows}</tbody></table>
"""

    data = {
        "monthly": pack["monthly"],
        "saty24": pack["saty_fy24"],
        "saty25": pack["saty_fy25"],
        "groups": pack["groups"][:10],
        "families": pack["families"],
        "pms": pack["pms_cats"],
        "pms_series": pack.get("pms_series_cy") or [],
        "gps_series": pack.get("gps_series") or [],
        "net_compare": [
            {"label": meta["label"], "yoy": pack["fy_yoy_pct"]},
            {"label": "Network average", "yoy": (pack.get("network_compare") or {}).get("network_yoy_pct")},
        ],
        "fy": [pack["fy24_eur"], pack["fy25_eur"]],
        "include_source": meta["include_source"],
        "source": pack.get("source_h1") or [],
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
      {label:'YoY %', data:src.map(r=>r.yoy), backgroundColor:terra, barThickness:28}
    ]},
    options:{responsive:true,maintainAspectRatio:false,plugins:{legend:{position:'bottom'}},
      scales:{y:{ticks:{callback:v=>v+'%'},grid:{color:grid}},x:{grid:{display:false}}}}});
}
"""

    pms_html = ""
    if pack["pms_available"]:
        pms_html = """
new Chart(document.getElementById('cPms'),{type:'bar',data:{labels:D.pms.map(r=>r.category),datasets:[{data:D.pms.map(r=>r.capture_pct),backgroundColor:D.pms.map(r=>r.capture_pct>100?'#eda100':r.capture_pct>=80?green:r.capture_pct>=40?blue:red),barThickness:16}]},
  options:{indexAxis:'y',responsive:true,maintainAspectRatio:false,plugins:{legend:{display:false}},scales:{x:{ticks:{callback:v=>v+'%'},grid:{color:grid}},y:{grid:{display:false},ticks:{font:{size:10}}}}}});
new Chart(document.getElementById('cPmsSeries'),{type:'bar',data:{labels:D.pms_series.map(r=>r.label),datasets:[{data:D.pms_series.map(r=>r.capture_pct),backgroundColor:navy,barThickness:36}]},
  options:{responsive:true,maintainAspectRatio:false,plugins:{legend:{display:false}},scales:{y:{ticks:{callback:v=>v+'%'},grid:{color:grid}},x:{grid:{display:false}}}}});
"""

    html_tpl = Template("""<!DOCTYPE html>
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
<span class="chip">ISZE Parts · Customer briefing V4</span>
<span class="chip">$subtitle</span>
<h1>$title</h1>
<div class="rule"></div>
<p style="max-width:38rem;opacity:.93">Fiscal sales, mix, GPS capture %, PMS capture %, and part-number depth — prepared for a meeting with <strong>$label</strong> only.</p>
<p style="color:#c9d2e0;font-size:.9rem">FY = Apr–Mar · Billing through $billing_max · Generated $generated</p>
</div></div>
<nav class="nav no-print">$nav</nav>

<section class="page" id="p1">
<h2 class="sec"><span class="no">$n_p1</span> Scope &amp; periods</h2>
<div class="callout"><strong>Customer:</strong> $label ($country).<br/>
<strong>This pack is single-customer</strong> — at most one light network-average benchmark; no peer-country GPS compare.
$scope_ids_note</div>
<table>
<thead><tr><th>Layer</th><th>Period</th><th>What you see</th></tr></thead>
<tbody>
<tr><td>Fiscal sales, SaTy, PN</td><td>FY2024 vs FY2025 (Apr–Mar)</td><td>ISZE billing (rebate lines excluded)</td></tr>
<tr><td>Sales tendency</td><td>24 fiscal months</td><td>Monthly billed sales</td></tr>
<tr><td>GPS capture</td><td>CY now vs past</td><td>Capture vs max % (time series only)</td></tr>
<tr><td>PMS capture</td><td>CY2025 (CY2024 trend)</td><td>Total capture % by category (no silent 100% ceiling)</td></tr>
</tbody></table>
<p class="muted">$rebate_note</p>
</section>

<section class="page" id="p2">
<h2 class="sec"><span class="no">$n_p2</span> Sales trajectory</h2>
<div class="grid">
<div class="stat"><div class="lbl">FY2024</div><div class="val">$fy24</div></div>
<div class="stat"><div class="lbl">FY2025</div><div class="val">$fy25</div><div class="sub $yoy_cls">$yoy vs prior FY</div></div>
</div>
<div class="chart"><canvas id="cFy"></canvas></div>
$network_block
<h3>Monthly tendency (FY2024–FY2025)</h3>
<div class="chart tall"><canvas id="cM"></canvas></div>
$rec_html
</section>

<section class="page" id="p3">
<h2 class="sec"><span class="no">$n_p3</span> SaTy evolution</h2>
<div class="two">
<div><h3>FY2024</h3><div class="chart"><canvas id="cS24"></canvas></div></div>
<div><h3>FY2025</h3><div class="chart"><canvas id="cS25"></canvas></div></div>
</div>
</section>

$source_page

<section class="page" id="p4">
<h2 class="sec"><span class="no">$n_p4</span> GPS capture — now vs past</h2>
<div class="grid">
<div class="stat"><div class="lbl">GPS capture vs max (CY2025)</div><div class="val">$gps_pct</div><div class="sub">Traffic light: $gps_tl</div></div>
<div class="stat"><div class="lbl">UIO (context)</div><div class="val">$uio</div><div class="sub muted">Absolute €/SPU in footnote only</div></div>
</div>
<p class="muted">Headline = <strong>percentage capture over time</strong> — no other-country peer bars. Footnote: SPU ≈ €$spu · CY2025 sales ≈ $gps_sales.</p>
<div class="chart"><canvas id="cGps"></canvas></div>
<p class="muted">CY2024 uses sales ÷ CY2025 max-spend as a trend proxy when max-spend was not stored. CY2026 run-rate = YTD×4 ÷ year max-spend.</p>
</section>

<section class="page" id="p5">
<h2 class="sec"><span class="no">$n_p5</span> PMS capture %</h2>
<div class="assume">$pms_assumption</div>
$pms_stats
</section>

<section class="page" id="p6">
<h2 class="sec"><span class="no">$n_p6</span> Product family / group</h2>
<p class="muted">ISZE parts classification (family / group) — share % now vs past, not euros. Lubricants without catalogue match are labelled explicitly.</p>
<div class="chart tall"><canvas id="cFam"></canvas></div>
<h3>Group detail (finer classification, supplementary)</h3>
<table>
<thead><tr><th>Group</th><th>FY2024 share</th><th>FY2025 share</th><th>YoY €</th></tr></thead>
<tbody>$group_rows</tbody>
</table>
</section>

<section class="page" id="p7">
<h2 class="sec"><span class="no">$n_p7</span> Part numbers — full year vs full year</h2>
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
<h2 class="sec"><span class="no">$n_p8</span> Part-number depth — quantity, FY2024 vs FY2025</h2>
<p class="muted">$depth_thresholds</p>
$narrative
<h3>Vanished part numbers (had FY2024 qty, zero in FY2025)</h3>
$vanished_block
<h3>New part numbers (zero in FY2024, active in FY2025)</h3>
$new_block
<h3>Continuing droppers (both years active, qty down ≥30%)</h3>
$dropper_block
<h3>Channel-shift test — top crash part numbers vs rest of network</h3>
<p class="muted">Customer Δqty is this customer's FY2024→FY2025 change. Rest-of-network Δqty is the same part number across every other distributor over the same period.</p>
$channel_block
$basket_block
</section>

<section class="page" id="p9">
<h2 class="sec"><span class="no">$n_p9</span> PN movers &amp; silent lines</h2>
<p class="muted">Largest € gains / losses FY2024 → FY2025 (rebate excluded). PMS category shown when mapped.</p>
<h3>Top gainers</h3>
<table><thead><tr><th>PN</th><th>Desc</th><th>FY24</th><th>FY25</th><th>Δ</th><th>PMS</th></tr></thead><tbody>$gain</tbody></table>
<h3>Top losers</h3>
<table><thead><tr><th>PN</th><th>Desc</th><th>FY24</th><th>FY25</th><th>Δ</th><th>PMS</th></tr></thead><tbody>$lose</tbody></table>
<h3>Silent / collapsing (had FY24 sales, near-zero FY25)</h3>
<table><thead><tr><th>PN</th><th>Desc</th><th>FY24</th><th>FY25</th><th>Δ</th><th>PMS</th></tr></thead><tbody>$silent</tbody></table>
</section>

<section class="page" id="p10">
<h2 class="sec"><span class="no">$n_p10</span> Cross-check</h2>
<p class="muted">Where sales, GPS, PMS and (where available) dealer standards agree — or pull apart.</p>
$cross
$ids_block
</section>

<section class="page" id="p11">
<h2 class="sec"><span class="no">$n_p11</span> Meeting asks</h2>
<p class="muted">Clear questions for the joint discussion — customer-safe wording.</p>
$asks
</section>

<div class="footer">Sources: ISZE billing · PRISM GPS/PMS derived files · Power BI SALES (H1, where applicable). External pack — no internal methodology nicknames. $label only.</div>

<!--CHART_BOOT-->
</body></html>
""")

    group_rows = "".join(
        f"<tr><td>{r['group']}</td><td class='num'>{r['fy24_share']:.1f}%</td>"
        f"<td class='num'>{r['fy25_share']:.1f}%</td>"
        f"<td class='num'>{('+' if (r['yoy_pct'] or 0) >= 0 else '') + (str(r['yoy_pct']) + '%' if r['yoy_pct'] is not None else 'n/a')}</td></tr>"
        for r in pack["groups"][:10]
    )

    if meta.get("forbid_uti"):
        scope_ids_note = (
            "<br/><strong>IDS Israel:</strong> covers the UMI dealer network only. "
            "Do not combine other Israel distributors with IDS Israel scores, PMS, or GPS in this pack."
        )
    else:
        scope_ids_note = ""

    ids = pack.get("ids")
    ids_block = ""
    if ids:
        ids_block = (
            f"<div class='callout'><strong>IDS snapshot:</strong> {ids['label']} — average "
            f"<strong>{ids.get('avg_pct')}%</strong> points (n={ids.get('n_dealers')}; "
            f"max {ids.get('max_pct')}% · min {ids.get('min_pct')}%).</div>"
        )

    out = html_tpl.safe_substitute(
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
        network_block=network_block,
        rec_html=rec_html,
        source_page=source_page,
        gps_pct=f"{gps.get('gps_pct')}%" if gps.get("gps_pct") is not None else "n/a",
        gps_tl=gps.get("traffic_light") or "—",
        uio=f"{gps.get('uio'):,}" if gps.get("uio") else "—",
        spu=gps.get("spu_eur") if gps.get("spu_eur") is not None else "—",
        gps_sales=eur(gps.get("sales_eur")),
        pms_assumption=pack["pms_assumption"],
        pms_stats=pms_stats,
        group_rows=group_rows,
        c24_10=f"{c24.get('top10_share_pct', '—')}%",
        c25_10=f"{c25.get('top10_share_pct', '—')}%",
        c25_80=str(c25.get("pn_for_80pct", "—")),
        c25_n=str(c25.get("distinct_pn", "—")),
        pn24=_pn_rows(pack["top_pn_fy24"]),
        pn25=_pn_rows(pack["top_pn_fy25"]),
        depth_thresholds=depth["thresholds_note"],
        narrative=narrative_html,
        vanished_block=vanished_block,
        new_block=new_block,
        dropper_block=dropper_block,
        channel_block=channel_block,
        basket_block=basket_block,
        gain=_mover_rows(pack["gainers"], False),
        lose=_mover_rows(pack["losers"], True),
        silent=_mover_rows(pack["silent"], True),
        cross=cross_html,
        ids_block=ids_block,
        asks=asks_html,
        n_p1=num["p1"], n_p2=num["p2"], n_p3=num["p3"], n_p4=num["p4"], n_p5=num["p5"],
        n_p6=num["p6"], n_p7=num["p7"], n_p8=num["p8"], n_p9=num["p9"], n_p10=num["p10"], n_p11=num["p11"],
    )

    boot = (
        f"<script>{CHART_JS}</script>\n<script>\n"
        f"const D = {json.dumps(data)};\n"
        f"""
const ink='#52514e', grid='#e1e0d9', navy='{NAVY}', blue='#2a78d6', terra='{TERRA}', green='#1d9e75', red='#e24b4a';
new Chart(document.getElementById('cFy'),{{type:'bar',data:{{labels:['FY2024','FY2025'],datasets:[{{data:D.fy,backgroundColor:[blue,terra],barThickness:42}}]}},
  options:{{responsive:true,maintainAspectRatio:false,plugins:{{legend:{{display:false}}}},scales:{{y:{{ticks:{{callback:v=>'€'+(v/1e6).toFixed(2)+'M'}},grid:{{color:grid}}}},x:{{grid:{{display:false}}}}}}}}}});
new Chart(document.getElementById('cNet'),{{type:'bar',data:{{labels:D.net_compare.map(r=>r.label),datasets:[{{data:D.net_compare.map(r=>r.yoy),backgroundColor:[terra,blue],barThickness:36}}]}},
  options:{{responsive:true,maintainAspectRatio:false,plugins:{{legend:{{display:false}}}},scales:{{y:{{ticks:{{callback:v=>v+'%'}},grid:{{color:grid}}}},x:{{grid:{{display:false}}}}}}}}}});
new Chart(document.getElementById('cM'),{{type:'line',data:{{labels:D.monthly.map(r=>r.ym),datasets:[{{data:D.monthly.map(r=>r.sales_eur),borderColor:navy,backgroundColor:'rgba(11,31,51,.12)',fill:true,tension:.25,pointRadius:2}}]}},
  options:{{responsive:true,maintainAspectRatio:false,plugins:{{legend:{{display:false}}}},scales:{{y:{{ticks:{{callback:v=>'€'+(v/1000).toFixed(0)+'K'}},grid:{{color:grid}}}},x:{{ticks:{{maxRotation:60,autoSkip:true,maxTicksLimit:12}},grid:{{display:false}}}}}}}}}});
function satyChart(id, rows){{
  new Chart(document.getElementById(id),{{type:'bar',data:{{labels:rows.map(r=>r.saty),datasets:[{{data:rows.map(r=>r.share_pct),backgroundColor:blue,barThickness:22}}]}},
    options:{{indexAxis:'y',responsive:true,maintainAspectRatio:false,plugins:{{legend:{{display:false}}}},scales:{{x:{{max:100,ticks:{{callback:v=>v+'%'}},grid:{{color:grid}}}},y:{{grid:{{display:false}}}}}}}}}});
}}
satyChart('cS24', D.saty24); satyChart('cS25', D.saty25);
"""
        + src_script
        + pms_html
        + """
new Chart(document.getElementById('cGps'),{type:'bar',data:{labels:D.gps_series.map(r=>r.label),datasets:[{data:D.gps_series.map(r=>r.gps_pct),backgroundColor:terra,barThickness:36}]},
  options:{responsive:true,maintainAspectRatio:false,plugins:{legend:{display:false}},scales:{y:{ticks:{callback:v=>v+'%'},grid:{color:grid}},x:{grid:{display:false}}}}});
new Chart(document.getElementById('cFam'),{type:'bar',data:{labels:D.families.map(r=>r.family),datasets:[
  {label:'FY2024 share %', data:D.families.map(r=>r.fy24_share_pct), backgroundColor:'#85b7eb', barThickness:14},
  {label:'FY2025 share %', data:D.families.map(r=>r.fy25_share_pct), backgroundColor:terra, barThickness:14}]},
  options:{indexAxis:'y',responsive:true,maintainAspectRatio:false,plugins:{legend:{position:'bottom'}},scales:{x:{ticks:{callback:v=>v+'%'},grid:{color:grid}},y:{grid:{display:false},ticks:{font:{size:10}}}}}});
</script>
"""
    )
    out = out.replace("<!--CHARTJS-->", "").replace("<!--CHART_BOOT-->", boot)

    if meta.get("forbid_uti"):
        out = scrub_uti(out)
        m = re.search(r".{0,50}\bUTI\b.{0,50}", out)
        if m:
            raise RuntimeError("UMI V4 pack still contains UTI after scrub — near: " + m.group(0))
    return out


# ---------- Excel ----------

def write_excel(pack: dict, path: Path, forbid_uti: bool = False):
    wb = Workbook()
    navy_f = PatternFill("solid", fgColor=NAVY.lstrip("#").upper())
    head = Font(name="Calibri", bold=True, color="FFFFFF", size=11)
    title = Font(name="Calibri", bold=True, color=NAVY.lstrip("#").upper(), size=14)
    body = Font(name="Calibri", size=10)
    wrap = Alignment(wrap_text=True, vertical="top")
    thin = Border(
        left=Side(style="thin", color="D9D3C8"),
        right=Side(style="thin", color="D9D3C8"),
        top=Side(style="thin", color="D9D3C8"),
        bottom=Side(style="thin", color="D9D3C8"),
    )
    zebra = PatternFill("solid", fgColor="F7F4EE")

    def _v(val):
        if forbid_uti and isinstance(val, str):
            return scrub_uti(val)
        return val

    def hdr(ws, row, ncols):
        for c in range(1, ncols + 1):
            cell = ws.cell(row, c)
            cell.fill = navy_f
            cell.font = head
            cell.border = thin

    def table(ws, r0, headers, rows, money_cols=()):
        for j, h in enumerate(headers, 1):
            ws.cell(r0, j, _v(h))
        hdr(ws, r0, len(headers))
        for i, row in enumerate(rows):
            for j, val in enumerate(row, 1):
                cell = ws.cell(r0 + 1 + i, j, _v(val))
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
    ws.title = "01_Summary"
    ws["A1"] = _v(f"{meta['title']} — V4")
    ws["A1"].font = title
    notes = [
        "Single-customer pack. No dual-DB compare.",
        PMS_ASSUMPTION,
        pack["rebate_note"],
        "Primary = total PMS capture %. GPS = capture vs max %. Family = share % only.",
        "External language: IML service schedule — no internal nicknames.",
    ]
    for i, t in enumerate(notes, 3):
        ws.cell(i, 1, _v(t)).alignment = wrap
    r0 = len(notes) + 5
    table(
        ws, r0,
        ["Metric", "Value"],
        [
            ["FY2024 €", pack["fy24_eur"]],
            ["FY2025 €", pack["fy25_eur"]],
            ["FY YoY %", pack["fy_yoy_pct"]],
            ["GPS capture % CY2025", pack["gps"].get("gps_pct")],
            ["PMS total % (weighted, CY2025)", pack["pms_total_wtd_pct"]],
            ["PMS genuine % (secondary)", pack["pms_genuine_wtd_pct"]],
            ["IDS avg %", pack["ids"]["avg_pct"] if pack.get("ids") else None],
        ],
        money_cols={2},
    )
    r1 = r0 + 10
    ws.cell(r1, 1, "GPS / PMS series").font = title
    rows = [["GPS " + r["label"], r["gps_pct"], r.get("note")] for r in pack.get("gps_series") or []]
    rows.append(["—", "", ""])
    rows += [["PMS " + r["label"], r["capture_pct"], "weighted total capture"] for r in pack.get("pms_series_cy") or []]
    rows.append(["—", "", ""])
    rows += [[r["category"], r["capture_pct"], ""] for r in pack["pms_cats"]]
    for ex in pack.get("pms_excluded") or []:
        rows.append([f"EXCLUDED {ex['category']}", ex["raw_capture_pct"], ex["reason"][:100]])
    table(ws, r1 + 1, ["Series / Category", "Capture %", "Note"], rows)
    r2 = r1 + 3 + len(rows)
    ws.cell(r2, 1, "Reconcile — Power BI / GPS vs ISZE billing").font = title
    table(
        ws, r2 + 1,
        ["Period", "Ref label", "Ref €", "ISZE €", "Delta", "Note"],
        [
            [r["period"], r["pbi_or_gps_label"], r.get("reference_eur"), r.get("isze_billing_eur"), r.get("delta_eur"), r.get("note")]
            for r in pack.get("reconcile") or []
        ],
        {3, 4, 5},
    )
    widths(ws, [30, 28, 14, 14, 12, 60])

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

    ws = wb.create_sheet("04_Family")
    table(
        ws, 1,
        ["Family (ISZE parts classification)", "FY2024 share %", "FY2025 share %"],
        [[r["family"], r["fy24_share_pct"], r["fy25_share_pct"]] for r in pack["families"]],
    )
    widths(ws, [30, 16, 16])

    ws = wb.create_sheet("05_Groups")
    table(
        ws, 1,
        ["Group", "FY24 €", "FY25 €", "FY24 share", "FY25 share", "YoY %"],
        [[r["group"], r["fy24_eur"], r["fy25_eur"], r["fy24_share"], r["fy25_share"], r["yoy_pct"]] for r in pack["groups"]],
        {2, 3},
    )
    widths(ws, [28, 14, 14, 12, 12, 12])

    ws = wb.create_sheet("06_PN_FY")
    r = 1
    for label, block in (("FY2024", pack["top_pn_fy24"]), ("FY2025", pack["top_pn_fy25"])):
        ws.cell(r, 1, _v(label)).font = title
        table(
            ws, r + 1,
            ["Rank", "PN", "Desc", "€", "%"],
            [[x["rank"], x["part_number"], x["description"], x["sales_eur"], x["share_pct"]] for x in block],
            {4},
        )
        r += 3 + len(block)
    widths(ws, [10, 16, 40, 12, 10])

    ws = wb.create_sheet("07_Movers")
    r = 1
    for label, block in (("Gainers", pack["gainers"]), ("Losers", pack["losers"]), ("Silent", pack["silent"])):
        ws.cell(r, 1, _v(label)).font = title
        table(
            ws, r + 1,
            ["PN", "Desc", "FY24", "FY25", "Delta", "PMS"],
            [[x["part_number"], x["description"], x["fy24_eur"], x["fy25_eur"], x["delta_eur"], x.get("pms_category")] for x in block],
            {3, 4, 5},
        )
        r += 3 + len(block)
    widths(ws, [14, 36, 12, 12, 12, 16])

    ws = wb.create_sheet("08_PN_Depth")
    depth = pack["depth"]
    r = 1
    ws.cell(r, 1, _v("Vanished (FY24 qty>0, FY25 qty==0)")).font = title
    table(
        ws, r + 1,
        ["PN", "Desc", "FY24 qty", "FY24 €"],
        [[x["part_number"], x["description"], x["fy24_qty"], x["fy24_eur"]] for x in depth["vanished"]],
        {4},
    )
    r += 3 + len(depth["vanished"])
    ws.cell(r, 1, _v("New (FY24 qty==0, FY25 qty>0)")).font = title
    table(
        ws, r + 1,
        ["PN", "Desc", "FY25 qty", "FY25 €"],
        [[x["part_number"], x["description"], x["fy25_qty"], x["fy25_eur"]] for x in depth["new_pn"]],
        {4},
    )
    r += 3 + len(depth["new_pn"])
    ws.cell(r, 1, _v("Continuing droppers (qty down >= 30%)")).font = title
    table(
        ws, r + 1,
        ["PN", "Desc", "FY24 qty", "FY25 qty", "Drop %"],
        [[x["part_number"], x["description"], x["fy24_qty"], x["fy25_qty"], x["drop_pct"]] for x in depth["droppers"]],
    )
    r += 3 + len(depth["droppers"])
    ws.cell(r, 1, _v("Channel-shift verdicts (top crash PNs)")).font = title
    table(
        ws, r + 1,
        ["PN", "Desc", "Customer Δqty", "Rest-of-network Δqty", "Rest FY25 qty", "Verdict"],
        [
            [x["part_number"], x["description"], x["customer_delta_qty"], x["rest_delta_qty"], x["rest_q25_qty"], x["verdict_text"]]
            for x in depth["channel"]
        ],
    )
    widths(ws, [14, 36, 14, 18, 14, 44])

    ws = wb.create_sheet("09_Asks")
    table(ws, 1, ["#", "Ask"], [[i, q] for i, q in enumerate(pack["asks"], 1)])
    widths(ws, [6, 100])

    for name in wb.sheetnames:
        wb[name].freeze_panes = "A2"
    wb.save(path)


# ---------- main ----------

def main():
    V4.mkdir(parents=True, exist_ok=True)
    NETWORK_HUB.mkdir(parents=True, exist_ok=True)

    print("Loading sales…")
    df = load_sales()
    cat = load_catalog()
    master = load_master()
    gps_df = load_gps_df()
    pms_df = load_pms_df()

    print("Precomputing network-wide PN quantity table (FY2024/FY2025)…")
    net_by_pn_fy = build_network_qty_table(df)

    registry = build_customers_registry(master)

    manifest = []
    for code in CUSTOMER_CODES:
        meta = registry[code]
        print(f"Building pack {code} ({meta['label']})…")
        pack = build_customer_pack(code, meta, df, cat, master, gps_df, pms_df, net_by_pn_fy)

        stem = meta["file_stem"]
        html_path = V4 / f"{stem}.html"
        xlsx_path = V4 / f"{stem}.xlsx"
        json_path = V4 / f"{stem}_data.json"

        html = render_html(pack)
        write_excel(pack, xlsx_path, forbid_uti=meta["forbid_uti"])
        html_path.write_text(html, encoding="utf-8")

        def _json_default(o):
            if isinstance(o, float) and (math.isnan(o) or math.isinf(o)):
                return None
            if hasattr(o, "item"):
                try:
                    v = o.item()
                    if isinstance(v, float) and (math.isnan(v) or math.isinf(v)):
                        return None
                    return v
                except Exception:
                    return str(o)
            return str(o)

        json_txt = json.dumps(pack, indent=2, default=_json_default, allow_nan=False)
        if meta["forbid_uti"]:
            json_txt = scrub_uti(json_txt)
        json_path.write_text(json_txt, encoding="utf-8")

        if code in ("PORTUGAL", "UMI"):
            for src, dst in [(html_path, OUT / f"{stem}.html"), (xlsx_path, OUT / f"{stem}.xlsx")]:
                dst.write_bytes(src.read_bytes())

        for src, dst in [
            (html_path, NETWORK_HUB / f"{stem}.html"),
            (xlsx_path, NETWORK_HUB / f"{stem}.xlsx"),
            (json_path, NETWORK_HUB / f"{stem}_data.json"),
        ]:
            dst.write_bytes(src.read_bytes())

        manifest.append({
            "code": code,
            "label": meta["label"],
            "file_stem": stem,
            "html": str(html_path),
            "xlsx": str(xlsx_path),
            "json": str(json_path),
            "fy24_eur": pack["fy24_eur"],
            "fy25_eur": pack["fy25_eur"],
            "fy_yoy_pct": pack["fy_yoy_pct"],
            "gps_pct": pack["gps"].get("gps_pct"),
            "pms_total_pct": pack["pms_total_wtd_pct"],
        })
        print(
            f"  wrote {stem} (FY25 EUR {pack['fy25_eur']:,.0f}, "
            f"YoY {pack['fy_yoy_pct']}, GPS {pack['gps'].get('gps_pct')}%, "
            f"PMS {pack['pms_total_wtd_pct']}%)"
        )

    (V4 / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(f"Done. Wrote {len(manifest)} packs to {V4}")
    print(f"Copied all packs to network hub: {NETWORK_HUB}")


if __name__ == "__main__":
    main()

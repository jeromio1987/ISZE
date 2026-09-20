"""UTI CY2025 sell-through + H2 2025 replenishment (internal).

ISZE→UTI billed qty (sold_to_sap 1799 only) vs UTI→dealer PartSales.
Does not rebuild existing dealer-sellout HTML. Does not send mail.
"""
from __future__ import annotations

import json
import math
import re
import sys
from pathlib import Path

import pandas as pd

ISZE = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ISZE / "03_analytics" / "Isuzu" / "prism"))

from modules.dealer_sales_loader import load_uti_part_sales, normalize_pn  # noqa: E402

UTI_SAP = 1799
UMI_SAP = 1797
MATCH_LO = 0.70
MATCH_HI = 1.30
H2_MONTHS = (8, 9, 10, 11, 12)
MONTH_LABELS = {
    1: "Jan",
    2: "Feb",
    3: "Mar",
    4: "Apr",
    5: "May",
    6: "Jun",
    7: "Jul",
    8: "Aug",
    9: "Sep",
    10: "Oct",
    11: "Nov",
    12: "Dec",
}

UTI_DIR = ISZE / "01_data" / "12_raw" / "dealer_sales" / "UTI"
SALES_CSV = ISZE / "01_data" / "00_derived" / "sales_fact.csv"
SALES_PARQUET = ISZE / "01_data" / "00_derived" / "sales_fact.parquet"
NEWEST_CSV = ISZE / "01_data" / "00_derived" / "price_file_2026_pn_newest.csv"
CHART_JS = ISZE / "02_dashboards" / "_ui" / "chart.umd.min.js"
OUT_JSON = Path(__file__).with_name("uti_replenishment_h2_2025.json")
OUT_HTML = ISZE / "02_dashboards" / "sales" / "ISZE_UTI_Replenishment_H2_2025.html"

UTI_FILES = {
    (2025, 1): UTI_DIR / "UTIPartSales_2025-01.xlsx",
    (2025, 8): UTI_DIR / "UTIPartSales_2025-08.xlsx",
    (2025, 9): UTI_DIR / "UTIPartSales_2025-09.xlsx",
    (2025, 10): UTI_DIR / "UTIPartSales_2025-10.xlsx",
    (2025, 11): UTI_DIR / "UTIPartSales_2025-11.xlsx",
    (2025, 12): UTI_DIR / "UTIPartSales_2025-12_YTD.xlsx",
    (2026, 1): UTI_DIR / "UTIPartSales_2026-01.xlsx",
    (2026, 2): UTI_DIR / "UTIPartSales_2026-02.xlsx",
    (2026, 3): UTI_DIR / "UTIPartSales_2026-03.xlsx",
    (2026, 4): UTI_DIR / "UTIPartSales_2026-04.xlsx",
    (2026, 5): UTI_DIR / "UTIPartSales_2026-05.xlsx",
    (2026, 6): UTI_DIR / "UTIPartSales_2026-06.xlsx",
}


def _pearson(a: list[float], b: list[float]) -> float | None:
    if len(a) < 3 or len(a) != len(b):
        return None
    n = len(a)
    ma = sum(a) / n
    mb = sum(b) / n
    va = sum((x - ma) ** 2 for x in a)
    vb = sum((y - mb) ** 2 for y in b)
    if va <= 0 or vb <= 0:
        return None
    cov = sum((a[i] - ma) * (b[i] - mb) for i in range(n))
    return cov / math.sqrt(va * vb)


def _cv(vals: list[float]) -> float | None:
    if not vals:
        return None
    m = sum(vals) / len(vals)
    if m == 0:
        return None
    var = sum((x - m) ** 2 for x in vals) / len(vals)
    return math.sqrt(var) / abs(m)


def _classify(si: float, so: float, in_partsales: bool) -> str:
    if si > 0 and not in_partsales:
        return "coverage_hole"
    if si <= 0 and so > 0:
        return "destock"
    if si > 0 and so <= 0:
        return "stock_build"
    if si > 0 and so > 0:
        r = so / si
        if MATCH_LO <= r <= MATCH_HI:
            return "matched"
        if r < MATCH_LO:
            return "stock_build"
        return "destock"
    return "idle"


def _load_newest_map() -> dict[str, str]:
    if not NEWEST_CSV.exists():
        return {}
    raw = pd.read_csv(NEWEST_CSV, usecols=["P/N", "Newest P/N"], dtype=str)
    out: dict[str, str] = {}
    for old, new in zip(raw["P/N"], raw["Newest P/N"]):
        a = normalize_pn(old)
        b = normalize_pn(new)
        if a and b:
            out[a] = b
    return out


def _roll(pn: str, newest: dict[str, str]) -> str:
    return newest.get(pn, pn)


def _agg_qty(df: pd.DataFrame, pn_col: str, qty_col: str) -> pd.DataFrame:
    g = df.groupby(pn_col, as_index=False)[qty_col].sum()
    return g.rename(columns={pn_col: "part_number", qty_col: "qty"})


def load_billing() -> pd.DataFrame:
    cols = [
        "billing_date",
        "sold_to_sap",
        "sold_to",
        "part_number",
        "description",
        "billed_qty",
        "net_sales_value",
        "year",
    ]
    src = SALES_CSV if SALES_CSV.exists() else SALES_PARQUET
    if src.suffix == ".parquet":
        df = pd.read_parquet(src, columns=cols)
    else:
        df = pd.read_csv(src, usecols=cols)
    df["sold_to_sap"] = pd.to_numeric(df["sold_to_sap"], errors="coerce")
    # Hard split: UTI 1799 only. sold_to can be 1797 for both — ignore it.
    n_umi = int((df["sold_to_sap"] == UMI_SAP).sum())
    df = df.loc[df["sold_to_sap"] == UTI_SAP].copy()
    df["part_number"] = df["part_number"].map(normalize_pn)
    df = df.dropna(subset=["part_number"])
    df["billed_qty"] = pd.to_numeric(df["billed_qty"], errors="coerce").fillna(0)
    df["net_sales_value"] = pd.to_numeric(df["net_sales_value"], errors="coerce").fillna(0)
    df["billing_date"] = pd.to_datetime(df["billing_date"], errors="coerce")
    df["year"] = pd.to_numeric(df["year"], errors="coerce")
    df["month"] = df["billing_date"].dt.month
    df["_umi_rows_in_fact"] = n_umi  # stash via attrs
    df.attrs["umi_rows_in_fact"] = n_umi
    return df


def load_snapshots() -> dict[tuple[int, int], tuple[pd.DataFrame, dict]]:
    out: dict[tuple[int, int], tuple[pd.DataFrame, dict]] = {}
    for key, path in UTI_FILES.items():
        if not path.exists():
            continue
        df, meta = load_uti_part_sales(path)
        if df.empty:
            continue
        g = df.groupby("part_number", as_index=False)[["qty_month", "qty_ytd"]].sum()
        # Trust sheet meta (row 3). Mail dated 1 Sep = August report.
        ym = (int(meta.get("report_year") or key[0]), int(meta.get("report_month") or key[1]))
        meta = dict(meta)
        meta["path_key"] = f"{key[0]}-{key[1]:02d}"
        meta["bytes"] = path.stat().st_size
        out[ym] = (g, meta)
    return out


def top_rows(
    joined: pd.DataFrame,
    kind: str,
    n: int = 12,
    sort_col: str = "gap_qty",
) -> list[dict]:
    sub = joined.loc[joined["klass"] == kind].copy()
    if sub.empty:
        return []
    sub["gap_qty"] = sub["si_qty"] - sub["so_qty"]
    sub["abs_gap"] = sub["gap_qty"].abs()
    if sort_col == "si_qty":
        sub = sub.sort_values("si_qty", ascending=False)
    elif sort_col == "so_qty":
        sub = sub.sort_values("so_qty", ascending=False)
    else:
        sub = sub.sort_values("abs_gap", ascending=False)
    rows = []
    for _, r in sub.head(n).iterrows():
        si = float(r["si_qty"])
        so = float(r["so_qty"])
        rows.append(
            {
                "pn": r["pn_show"],
                "desc": (str(r["description"])[:48] if pd.notna(r.get("description")) else ""),
                "si": round(si, 1),
                "so": round(so, 1),
                "gap": round(si - so, 1),
                "ratio": round(so / si, 2) if si else None,
            }
        )
    return rows


def klass_summary(joined: pd.DataFrame) -> dict:
    out = {}
    for k in ("matched", "stock_build", "destock", "coverage_hole", "idle"):
        sub = joined.loc[joined["klass"] == k]
        out[k] = {
            "pn": int(len(sub)),
            "si_qty": float(sub["si_qty"].sum()) if len(sub) else 0.0,
            "so_qty": float(sub["so_qty"].sum()) if len(sub) else 0.0,
            "si_eur": float(sub["si_eur"].sum()) if len(sub) and "si_eur" in sub.columns else 0.0,
        }
    return out


def build() -> dict:
    bill = load_billing()
    newest = _load_newest_map()
    snaps = load_snapshots()

    bill25 = bill.loc[bill["year"] == 2025].copy()
    bill26 = bill.loc[bill["year"] == 2026].copy()

    desc_map = (
        bill25.dropna(subset=["description"])
        .drop_duplicates("part_number")
        .set_index("part_number")["description"]
        .to_dict()
    )

    si_cy = bill25.groupby("part_number", as_index=False).agg(
        si_qty=("billed_qty", "sum"),
        si_eur=("net_sales_value", "sum"),
    )
    si_cy["pn_new"] = si_cy["part_number"].map(lambda p: _roll(p, newest))
    si_cy_raw_qty = float(si_cy["si_qty"].sum())
    si_cy_raw_eur = float(si_cy["si_eur"].sum())
    si_cy_raw_pn = int(si_cy["part_number"].nunique())

    si_rolled = si_cy.groupby("pn_new", as_index=False).agg(
        si_qty=("si_qty", "sum"),
        si_eur=("si_eur", "sum"),
    )

    dec = snaps.get((2025, 12))
    if dec is None:
        raise SystemExit("Missing Dec 2025 UTI PartSales snapshot")
    so_dec, meta_dec = dec
    so_cy = so_dec.rename(columns={"qty_ytd": "so_qty"})[["part_number", "so_qty"]].copy()
    so_cy["pn_new"] = so_cy["part_number"].map(lambda p: _roll(p, newest))
    so_cy_raw_qty = float(so_cy["so_qty"].sum())
    so_cy_raw_pn = int(so_cy["part_number"].nunique())
    so_rolled = so_cy.groupby("pn_new", as_index=False).agg(so_qty=("so_qty", "sum"))

    # Seen in any 2025 PartSales file (Jan + Aug–Dec)
    seen_2025: set[str] = set()
    seen_2025_rolled: set[str] = set()
    snap_meta = []
    for (y, m), (df, meta) in sorted(snaps.items()):
        snap_meta.append(
            {
                "year": y,
                "month": m,
                "label": f"{MONTH_LABELS[m]} {y}",
                "file": meta.get("source_file"),
                "report_month": meta.get("report_month"),
                "report_year": meta.get("report_year"),
                "unique_pn": meta.get("unique_pn"),
                "qty_month": float(df["qty_month"].sum()),
                "qty_ytd": float(df["qty_ytd"].sum()),
            }
        )
        if y == 2025:
            seen_2025.update(df["part_number"].tolist())
            seen_2025_rolled.update(_roll(p, newest) for p in df["part_number"])

    annual = si_rolled.merge(so_rolled, on="pn_new", how="outer")
    annual["si_qty"] = annual["si_qty"].fillna(0)
    annual["so_qty"] = annual["so_qty"].fillna(0)
    annual["si_eur"] = annual["si_eur"].fillna(0)
    annual["in_so"] = annual["pn_new"].isin(seen_2025_rolled)
    annual["klass"] = [
        _classify(float(r.si_qty), float(r.so_qty), bool(r.in_so)) for r in annual.itertuples()
    ]
    annual["description"] = annual["pn_new"].map(desc_map)
    annual["pn_show"] = annual["pn_new"]

    # Unrolled (raw PN) for "did supersession change the story"
    annual_raw = si_cy[["part_number", "si_qty", "si_eur"]].merge(
        so_cy[["part_number", "so_qty"]], on="part_number", how="outer"
    )
    annual_raw["si_qty"] = annual_raw["si_qty"].fillna(0)
    annual_raw["so_qty"] = annual_raw["so_qty"].fillna(0)
    annual_raw["si_eur"] = annual_raw["si_eur"].fillna(0)
    annual_raw["in_so"] = annual_raw["part_number"].isin(seen_2025)
    annual_raw["klass"] = [
        _classify(float(r.si_qty), float(r.so_qty), bool(r.in_so))
        for r in annual_raw.itertuples()
    ]

    k_roll = klass_summary(annual)
    k_raw = klass_summary(annual_raw.rename(columns={"part_number": "pn_show"}).assign(pn_show=annual_raw["part_number"]))

    hole = annual.loc[annual["klass"] == "coverage_hole"]
    hole_pn = int(len(hole))
    hole_qty = float(hole["si_qty"].sum())
    hole_eur = float(hole["si_eur"].sum())

    si_tot = float(annual["si_qty"].sum())
    so_tot = float(annual["so_qty"].sum())
    st_pct = (so_tot / si_tot * 100) if si_tot else None
    net_stock = si_tot - so_tot

    # --- monthly SI ---
    def monthly_si(frame: pd.DataFrame, year: int, months: tuple[int, ...]) -> dict[int, float]:
        sub = frame.loc[frame["year"] == year]
        g = sub.groupby("month")["billed_qty"].sum()
        return {m: float(g.get(m, 0.0)) for m in months}

    si_h2 = monthly_si(bill25, 2025, H2_MONTHS)
    si_jan = monthly_si(bill25, 2025, (1,))
    si_h1 = monthly_si(bill25, 2025, (1, 2, 3, 4, 5, 6, 7))
    si_26 = monthly_si(bill26, 2026, (1, 2, 3, 4, 5, 6))

    so_month: dict[tuple[int, int], float] = {}
    so_month_pn: dict[tuple[int, int], pd.DataFrame] = {}
    for (y, m), (df, _meta) in snaps.items():
        so_month[(y, m)] = float(df["qty_month"].sum())
        so_month_pn[(y, m)] = df[["part_number", "qty_month"]].copy()

    h2_series = []
    for m in H2_MONTHS:
        h2_series.append(
            {
                "month": m,
                "label": MONTH_LABELS[m],
                "si": round(si_h2[m], 1),
                "so": round(so_month.get((2025, m), 0.0), 1),
            }
        )
    si_h2_tot = sum(si_h2[m] for m in H2_MONTHS)
    so_h2_tot = sum(so_month.get((2025, m), 0.0) for m in H2_MONTHS)

    si_vals = [si_h2[m] for m in H2_MONTHS]
    so_vals = [so_month.get((2025, m), 0.0) for m in H2_MONTHS]
    ratios = [(so_vals[i] / si_vals[i]) if si_vals[i] else None for i in range(5)]
    corr0 = _pearson(si_vals, so_vals)
    corr_lag1 = _pearson(si_vals[:-1], so_vals[1:])  # SI leads SO (replenish with lag)
    corr_lead = _pearson(so_vals[:-1], si_vals[1:])  # SO leads SI
    cv_si = _cv(si_vals)
    cv_so = _cv(so_vals)

    jan_ctx = {
        "si": round(si_jan.get(1, 0.0), 1),
        "so": round(so_month.get((2025, 1), 0.0), 1),
    }

    # Implied Feb–Jul sell-out from Dec YTD − Jan month − H2 months (network total)
    implied_feb_jul_so = so_cy_raw_qty - jan_ctx["so"] - so_h2_tot
    si_feb_jul = sum(si_h1[m] for m in (2, 3, 4, 5, 6, 7))
    si_h1_tot = sum(si_h1[m] for m in (1, 2, 3, 4, 5, 6, 7))

    bill_max = bill["billing_date"].max()
    bill_max_s = bill_max.strftime("%Y-%m-%d") if pd.notna(bill_max) else None
    # Fact currently ends 2026-03 — do not treat Apr–Jun SI=0 as destock.
    y26_overlap_months = [m for m in range(1, 7) if si_26.get(m, 0.0) > 0 or m <= 3]
    if pd.notna(bill_max) and int(bill_max.year) == 2026:
        last_bill_m = int(bill_max.month)
        y26_overlap_months = list(range(1, last_bill_m + 1))
    y26 = []
    for m in range(1, 7):
        si_m = si_26.get(m, 0.0)
        comparable = m in y26_overlap_months
        y26.append(
            {
                "month": m,
                "label": f"{MONTH_LABELS[m]} 26",
                "si": round(si_m, 1) if comparable else None,
                "so": round(so_month.get((2026, m), 0.0), 1),
                "billing_in_fact": comparable,
            }
        )
    si_26_tot = sum(si_26.get(m, 0.0) for m in y26_overlap_months)
    so_26_overlap = sum(so_month.get((2026, m), 0.0) for m in y26_overlap_months)
    so_26_tot = sum(so_month.get((2026, m), 0.0) for m in range(1, 7))

    # H2 PN join (rolled)
    si_h2_pn = bill25.loc[bill25["month"].isin(H2_MONTHS)].copy()
    si_h2_pn["pn_new"] = si_h2_pn["part_number"].map(lambda p: _roll(p, newest))
    si_h2_g = si_h2_pn.groupby("pn_new", as_index=False).agg(
        si_qty=("billed_qty", "sum"),
        si_eur=("net_sales_value", "sum"),
    )
    so_h2_frames = []
    for m in H2_MONTHS:
        d = so_month_pn.get((2025, m))
        if d is None:
            continue
        t = d.copy()
        t["pn_new"] = t["part_number"].map(lambda p: _roll(p, newest))
        so_h2_frames.append(t.groupby("pn_new", as_index=False)["qty_month"].sum())
    so_h2_g = (
        pd.concat(so_h2_frames, ignore_index=True).groupby("pn_new", as_index=False)["qty_month"].sum()
        if so_h2_frames
        else pd.DataFrame(columns=["pn_new", "qty_month"])
    )
    so_h2_g = so_h2_g.rename(columns={"qty_month": "so_qty"})
    h2j = si_h2_g.merge(so_h2_g, on="pn_new", how="outer")
    h2j["si_qty"] = h2j["si_qty"].fillna(0)
    h2j["so_qty"] = h2j["so_qty"].fillna(0)
    h2j["si_eur"] = h2j["si_eur"].fillna(0)
    h2_seen = set(h2j.loc[h2j["so_qty"] != 0, "pn_new"]).union(
        set(so_h2_g["pn_new"].tolist()) if len(so_h2_g) else set()
    )
    # in PartSales H2 = appeared in any Aug–Dec file
    h2_file_pns: set[str] = set()
    for m in H2_MONTHS:
        d = so_month_pn.get((2025, m))
        if d is not None:
            h2_file_pns.update(_roll(p, newest) for p in d["part_number"])
    h2j["in_so"] = h2j["pn_new"].isin(h2_file_pns)
    h2j["klass"] = [
        _classify(float(r.si_qty), float(r.so_qty), bool(r.in_so)) for r in h2j.itertuples()
    ]
    h2j["description"] = h2j["pn_new"].map(desc_map)
    h2j["pn_show"] = h2j["pn_new"]
    k_h2 = klass_summary(h2j)

    # Same-month vs lag tracking at network level: |SO-SI|/SI
    abs_gap_h2 = abs(so_h2_tot - si_h2_tot)
    h2_st = (so_h2_tot / si_h2_tot * 100) if si_h2_tot else None

    # Verdict heuristics (internal)
    lumpy_si = bool(cv_si is not None and cv_so is not None and cv_si > 1.4 * cv_so and cv_si > 0.35)
    lag_replenish = bool(
        corr_lag1 is not None and corr0 is not None and corr_lag1 > corr0 + 0.08 and corr_lag1 > 0.4
    )
    same_track = bool(corr0 is not None and corr0 > 0.55)
    h2_stocking = bool(si_h2_tot > so_h2_tot * 1.15)
    h2_destocking = bool(so_h2_tot > si_h2_tot * 1.15)
    cy_stocking = bool(si_tot > so_tot * 1.15)

    if h2_destocking and not h2_stocking:
        verdict_h2 = "destock"
        verdict_line = "H2 2025 is destock, not replenishment — dealers took more than ISZE billed."
    elif lag_replenish:
        verdict_h2 = "replenish_lag"
        verdict_line = "H2 2025 looks like replenishment with lag — sell-out tracks the prior month’s sell-in."
    elif h2_stocking and lumpy_si:
        verdict_h2 = "stock_ahead_lumpy"
        verdict_line = "Not replenishment as a system: dealer offtake is smooth (~7–10k/month); ISZE billing is lumpy. August billed 19.6k against 10.5k dealer. Nov–Dec then sit near 1.0 — that is the tail after a stock-up, not a monthly loop."
    elif h2_stocking and not same_track:
        verdict_h2 = "stock_ahead"
        verdict_line = "H2 2025 is stocking ahead — billed qty runs ahead of dealer sell-out, no tight month-to-month track."
    elif same_track and abs(h2_st - 100) < 15 if h2_st else False:
        verdict_h2 = "replenish"
        verdict_line = "H2 2025 is replenishment — sell-out tracks sell-in in the same window."
    elif cy_stocking:
        verdict_h2 = "stock_ahead"
        verdict_line = "Not clean replenishment — CY2025 net stock-build, and H2 does not close the gap."
    else:
        verdict_h2 = "mixed"
        verdict_line = "Mixed: some PNs replenish, the network total does not behave like a tight SO≈SI loop."

    payload = {
        "generated": "2026-08-13",
        "scope": {
            "db": "UTI",
            "sold_to_sap": UTI_SAP,
            "never_blend": UMI_SAP,
            "supersession_rolled": bool(newest),
            "newest_map_rows": len(newest),
            "match_band": [MATCH_LO, MATCH_HI],
            "h1_hole": "CY2025 Feb–Jul PartSales not in mailbox; annual uses Dec YTD; H2 uses qty_month Aug–Dec.",
        },
        "snapshots": snap_meta,
        "annual": {
            "si_qty": round(si_tot, 1),
            "so_qty": round(so_tot, 1),
            "si_eur": round(si_cy_raw_eur, 0),
            "sellthrough_pct": round(st_pct, 1) if st_pct is not None else None,
            "net_stock_qty": round(net_stock, 1),
            "si_pn": int((annual["si_qty"] > 0).sum()),
            "so_pn": int((annual["so_qty"] > 0).sum()),
            "raw": {
                "si_qty": round(si_cy_raw_qty, 1),
                "so_qty": round(so_cy_raw_qty, 1),
                "si_pn": si_cy_raw_pn,
                "so_pn": so_cy_raw_pn,
            },
            "klass": k_roll,
            "klass_raw": k_raw,
            "hole_pn": hole_pn,
            "hole_qty": round(hole_qty, 1),
            "hole_eur": round(hole_eur, 0),
            "hole_share_si_pct": round(hole_qty / si_tot * 100, 1) if si_tot else None,
            "top_hole": top_rows(annual, "coverage_hole", 12, "si_qty"),
            "top_stock_build": top_rows(annual, "stock_build", 10),
            "top_destock": top_rows(annual, "destock", 10),
            "top_matched": top_rows(annual, "matched", 8, "si_qty"),
        },
        "h2": {
            "months": h2_series,
            "si_qty": round(si_h2_tot, 1),
            "so_qty": round(so_h2_tot, 1),
            "sellthrough_pct": round(h2_st, 1) if h2_st is not None else None,
            "net_stock_qty": round(si_h2_tot - so_h2_tot, 1),
            "ratios": [round(r, 2) if r is not None else None for r in ratios],
            "corr_same_month": round(corr0, 2) if corr0 is not None else None,
            "corr_si_leads_so": round(corr_lag1, 2) if corr_lag1 is not None else None,
            "corr_so_leads_si": round(corr_lead, 2) if corr_lead is not None else None,
            "cv_si": round(cv_si, 2) if cv_si is not None else None,
            "cv_so": round(cv_so, 2) if cv_so is not None else None,
            "n_months": 5,
            "klass": k_h2,
            "top_stock_build": top_rows(h2j, "stock_build", 8),
            "top_destock": top_rows(h2j, "destock", 8),
            "top_hole": top_rows(h2j, "coverage_hole", 8, "si_qty"),
        },
        "jan_2025": jan_ctx,
        "h1_context": {
            "si_qty": round(si_h1_tot, 1),
            "si_feb_jul": round(si_feb_jul, 1),
            "implied_feb_jul_so": round(implied_feb_jul_so, 1),
            "note": "Feb–Jul sell-out files missing. Implied Feb–Jul dealer qty = Dec YTD − Jan month − Aug–Dec months.",
        },
        "y2026_h1": {
            "months": y26,
            "si_qty": round(si_26_tot, 1),
            "so_qty_overlap": round(so_26_overlap, 1),
            "so_qty_jan_jun": round(so_26_tot, 1),
            "sellthrough_pct": round(so_26_overlap / si_26_tot * 100, 1) if si_26_tot else None,
            "billing_max": bill_max_s,
            "overlap_months": y26_overlap_months,
            "note": "Billing extract ends 2026-03-31. Apr–Jun dealer qty is real; billed qty is not in fact yet — do not read as destock.",
        },
        "verdict": {
            "code": verdict_h2,
            "line": verdict_line,
            "cy_stocking": cy_stocking,
            "h2_stocking": h2_stocking,
            "h2_destocking": h2_destocking,
            "lumpy_si": lumpy_si,
            "lag_replenish": lag_replenish,
            "same_track": same_track,
        },
        "billing_source": str(SALES_CSV.name if SALES_CSV.exists() else SALES_PARQUET.name),
        "umi_rows_in_fact": int(bill.attrs.get("umi_rows_in_fact", 0)),
        "uti_bill_lines_2025": int(len(bill25)),
    }
    return payload


def _fmt_int(n) -> str:
    if n is None:
        return "—"
    return f"{round(n):,}"


def _fmt_pct(n) -> str:
    if n is None:
        return "—"
    return f"{n:.0f}%"


def write_html(d: dict) -> None:
    chart = CHART_JS.read_text(encoding="utf-8")
    chart = re.sub(r"//# sourceMappingURL=.*", "", chart).strip()
    data_json = json.dumps(d, ensure_ascii=False)
    a = d["annual"]
    h = d["h2"]
    v = d["verdict"]
    hole_share = a.get("hole_share_si_pct")
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1"/>
<title>UTI replenishment · H2 2025</title>
<style>
*{{box-sizing:border-box}}
html,body{{margin:0;padding:0;-webkit-print-color-adjust:exact;print-color-adjust:exact}}
body{{font-family:"Segoe UI",Helvetica,Arial,sans-serif;color:#222;font-size:15px;line-height:1.45;background:#f7f4ee}}
h1,h2,h3{{font-family:Georgia,"Times New Roman",serif;color:#1a2b4a;margin:0}}
.cover{{background:#15233c;color:#eef1f6;padding:42px 36px 36px}}
.cover h1{{color:#fff;font-size:34px;line-height:1.12;max-width:920px}}
.cover .rule{{width:72px;height:4px;background:#c0552d;margin:18px 0 16px}}
.cover .verdict{{font-size:18px;max-width:860px;color:#e8ecf3}}
.badge{{display:inline-block;font-size:11px;letter-spacing:.08em;text-transform:uppercase;opacity:.75;margin-bottom:10px}}
.wrap{{max-width:1080px;margin:0 auto;padding:22px 22px 48px}}
.kpis{{display:grid;grid-template-columns:repeat(4,1fr);gap:10px;margin:-28px 22px 18px;max-width:1080px}}
@media(max-width:900px){{.kpis{{grid-template-columns:repeat(2,1fr);margin-left:12px;margin-right:12px}}}}
.kpi{{background:#fff;border:1px solid #d9d3c8;padding:12px 14px}}
.kpi .val{{font-size:22px;font-weight:600;color:#1a2b4a}}
.kpi .lbl{{font-size:11px;color:#6b6256;text-transform:uppercase;letter-spacing:.04em;margin-top:4px}}
.kpi.warn .val{{color:#c0552d}}
.kpi.good .val{{color:#2e7d54}}
.kpi.bad .val{{color:#b23b3b}}
h2.sec{{font-size:20px;margin:28px 0 8px;padding-bottom:6px;border-bottom:2px solid #1a2b4a}}
h2.sec .no{{color:#c0552d}}
p.lead{{color:#3a342c;max-width:820px}}
.callout{{border-left:3px solid #c0552d;background:#fff;padding:12px 16px;margin:12px 0}}
.grid2{{display:grid;grid-template-columns:1fr 1fr;gap:16px}}
@media(max-width:800px){{.grid2{{grid-template-columns:1fr}}}}
.card{{background:#fff;border:1px solid #d9d3c8;padding:14px 16px}}
.chart-wrap{{position:relative;width:100%;height:280px}}
.chart-wrap.tall{{height:320px}}
.muted{{color:#6b6256;font-size:13px}}
table{{width:100%;border-collapse:collapse;margin:8px 0 4px;font-size:13px}}
th{{background:#1a2b4a;color:#fff;text-align:left;padding:7px 8px;font-size:11px;text-transform:uppercase}}
td{{padding:6px 8px;border-bottom:.5px solid #d9d3c8}}
tbody tr:nth-child(even){{background:#f7f4ee}}
td.num,th.num{{text-align:right}}
.tag{{display:inline-block;padding:1px 7px;font-size:11px;background:#eeeae3;color:#1a2b4a}}
.tag.build{{background:#f3e0d6;color:#8a3a1c}}
.tag.hole{{background:#f6d6d6;color:#8a2a2a}}
.tag.ok{{background:#dceee4;color:#1e6b45}}
.tag.de{{background:#e8e4dc;color:#5a5248}}
.foot{{margin-top:36px;font-size:12px;color:#6b6256;border-top:1px solid #d9d3c8;padding-top:10px}}
.note{{font-size:13px;color:#6b6256;margin:0 0 10px}}
</style>
</head>
<body>
<div class="cover">
  <div class="badge">internal · UTI 1799 · not UMI · 13 Aug 2026</div>
  <h1>UTI is not replenishing month-for-month — dealer offtake is smooth, buy-in is lumpy</h1>
  <div class="rule"></div>
  <p class="verdict" id="verdictLine">{v["line"]}</p>
</div>
<div class="kpis">
  <div class="kpi warn"><div class="val" id="kSt">{_fmt_pct(a["sellthrough_pct"])}</div><div class="lbl">CY2025 sell-through (dealer ÷ billed qty)</div></div>
  <div class="kpi"><div class="val" id="kSi">{_fmt_int(a["si_qty"])}</div><div class="lbl">ISZE → UTI billed qty 2025</div></div>
  <div class="kpi"><div class="val" id="kSo">{_fmt_int(a["so_qty"])}</div><div class="lbl">UTI → dealers YTD qty 2025</div></div>
  <div class="kpi bad"><div class="val" id="kHole">{_fmt_int(a["hole_pn"])} PNs</div><div class="lbl">Coverage hole · billed, never in PartSales ({_fmt_pct(hole_share)} of billed qty)</div></div>
</div>
<div class="wrap">
  <p class="lead">Same PNs, two sides of the warehouse. Sell-in is ISZE billed qty to UTI (sold-to SAP 1799). Sell-out is UTI network PartSales to dealers — no dealer names in the files. Matched = dealer qty within 30% of billed. Stock-build = billed well above dealer. Destock = dealers took more than we billed. Hole = we billed a PN that never appears in any 2025 PartSales file.</p>
  <p class="note">PNs rolled to ITC newest code so a supersession does not look like destock. Feb–Jul 2025 monthly sell-out is still missing; the annual number uses the December YTD column, not a reconstructed H1.</p>

  <h2 class="sec"><span class="no">01</span> · CY2025 — billed vs dealer</h2>
  <div class="grid2">
    <div class="card">
      <p class="muted" style="margin:0 0 8px">Qty by class (rolled to newest P/N)</p>
      <div class="chart-wrap"><canvas id="cKlass" role="img" aria-label="CY2025 qty by class: matched, stock-build, destock, coverage hole">Classes</canvas></div>
    </div>
    <div class="card">
      <p class="muted" style="margin:0 0 8px">PN count by class</p>
      <div class="chart-wrap"><canvas id="cKlassPn" role="img" aria-label="CY2025 part-number count by class">PN counts</canvas></div>
    </div>
  </div>
  <div class="callout" id="annualTake"></div>

  <h2 class="sec"><span class="no">02</span> · H2 2025 months — is sell-out tracking sell-in?</h2>
  <p class="note">August–December only. December sell-out is the month column, not YTD. January 2025 is plotted as a ghost point, not part of the H2 fit.</p>
  <div class="card">
    <div class="chart-wrap tall"><canvas id="cH2" role="img" aria-label="H2 2025 monthly billed qty versus dealer qty">H2 monthly</canvas></div>
  </div>
  <div class="grid2" style="margin-top:12px">
    <div class="card">
      <p class="muted" style="margin:0 0 8px">Dealer qty ÷ billed qty by month (1.0 = replenish)</p>
      <div class="chart-wrap"><canvas id="cRatio" role="img" aria-label="Monthly sell-out over sell-in ratio">Ratios</canvas></div>
    </div>
    <div class="card" id="h2Stats"></div>
  </div>

  <h2 class="sec"><span class="no">03</span> · Coverage hole</h2>
  <p class="note">Billed to UTI in 2025, absent from every 2025 PartSales file we have (Jan + Aug–Dec). Fasteners and clips often sit here — UTI may not put them on the dealer extract.</p>
  <div id="holeTable"></div>

  <h2 class="sec"><span class="no">04</span> · Biggest stock-build vs destock (annual)</h2>
  <div class="grid2">
    <div><p class="muted">Stock-build — billed minus dealer (top by gap)</p><div id="buildTable"></div></div>
    <div><p class="muted">Destock — dealer minus billed (top by gap)</p><div id="destockTable"></div></div>
  </div>

  <h2 class="sec"><span class="no">05</span> · 2026 extra (not the H2 test)</h2>
  <p class="note">Billing extract currently stops 31 Mar 2026. Compare Jan–Mar only. April–June dealer offtake is in PartSales; billed qty is not in the fact yet — that is a cutoff, not destock.</p>
  <div class="card">
    <div class="chart-wrap"><canvas id="c26" role="img" aria-label="2026 January to March billed qty versus dealer qty; April to June dealer qty only">2026 H1</canvas></div>
  </div>
  <p class="muted" id="y26note"></p>

  <p class="foot">Sources: ISZE billing to UTI (sold-to SAP 1799) and UTI network PartSales (qty month + YTD). PNs rolled to ITC newest code. No dealer names in the extract. H1 2025 monthly sell-out (Feb–Jul) not in the mailbox. Internal internal — not a client pack.</p>
</div>
<script>{chart}
</script>
<script>
const D = {data_json};
function fmt(n){{
  if(n==null||n==='') return '—';
  return Math.round(n).toLocaleString('en-GB');
}}
function pct(n){{
  if(n==null) return '—';
  return Math.round(n)+'%';
}}
const ink='#52514e', grid='#e1e0d9';
const COL = {{
  matched:'#1d9e75',
  stock_build:'#c0552d',
  destock:'#2a78d6',
  coverage_hole:'#e24b4a',
  si:'#1a2b4a',
  so:'#c0552d'
}};
const k = D.annual.klass;
const order = ['matched','stock_build','destock','coverage_hole'];
const labels = ['Matched','Stock-build','Destock','Coverage hole'];
new Chart(document.getElementById('cKlass'),{{
  type:'bar',
  data:{{labels:labels,datasets:[
    {{label:'Billed qty',data:order.map(x=>k[x].si_qty),backgroundColor:'#1a2b4a',borderRadius:3,barThickness:22}},
    {{label:'Dealer qty',data:order.map(x=>k[x].so_qty),backgroundColor:'#c0552d',borderRadius:3,barThickness:22}}
  ]}},
  options:{{responsive:true,maintainAspectRatio:false,
    plugins:{{legend:{{position:'bottom',labels:{{color:ink}}}}}},
    scales:{{x:{{grid:{{display:false}},ticks:{{color:ink}}}},
             y:{{grid:{{color:grid}},ticks:{{color:ink}},beginAtZero:true}}}}}}
}});
new Chart(document.getElementById('cKlassPn'),{{
  type:'bar',
  data:{{labels:labels,datasets:[
    {{label:'PNs',data:order.map(x=>k[x].pn),backgroundColor:['#1d9e75','#c0552d','#2a78d6','#e24b4a'],borderRadius:3,barThickness:26}}
  ]}},
  options:{{indexAxis:'y',responsive:true,maintainAspectRatio:false,
    plugins:{{legend:{{display:false}}}},
    scales:{{x:{{grid:{{color:grid}},ticks:{{color:ink}},beginAtZero:true}},
             y:{{grid:{{display:false}},ticks:{{color:ink}}}}}}}}
}});

const h2labs = D.h2.months.map(m=>m.label);
const jan = D.jan_2025;
new Chart(document.getElementById('cH2'),{{
  type:'bar',
  data:{{labels:h2labs,datasets:[
    {{label:'ISZE → UTI (sell-in)',data:D.h2.months.map(m=>m.si),backgroundColor:'#1a2b4a',borderRadius:3,barThickness:24}},
    {{label:'UTI → dealers (sell-out)',data:D.h2.months.map(m=>m.so),backgroundColor:'#c0552d',borderRadius:3,barThickness:24}}
  ]}},
  options:{{responsive:true,maintainAspectRatio:false,
    plugins:{{legend:{{position:'bottom',labels:{{color:ink}}}},
      title:{{display:true,text:'Aug–Dec 2025 qty  ·  Jan billed '+fmt(jan.si)+' / dealer '+fmt(jan.so)+' (context only)',color:ink,font:{{size:12,weight:'400'}}}}}},
    scales:{{x:{{grid:{{display:false}},ticks:{{color:ink}}}},
             y:{{grid:{{color:grid}},ticks:{{color:ink}},beginAtZero:true}}}}}}
}});

const ratios = D.h2.ratios.map(r=>r==null?null:Math.round(r*100));
new Chart(document.getElementById('cRatio'),{{
  type:'line',
  data:{{labels:h2labs,datasets:[
    {{label:'Even (100%)',data:[100,100,100,100,100],borderColor:'#888780',borderDash:[5,4],pointRadius:0,fill:false,borderWidth:1.5}},
    {{label:'Dealer / billed %',data:ratios,borderColor:'#c0552d',backgroundColor:'rgba(192,85,45,.12)',fill:true,tension:0,pointRadius:5,pointBackgroundColor:'#c0552d'}}
  ]}},
  options:{{responsive:true,maintainAspectRatio:false,
    plugins:{{legend:{{position:'bottom',labels:{{color:ink}}}}}},
    scales:{{x:{{grid:{{display:false}},ticks:{{color:ink}}}},
             y:{{min:0,max:160,grid:{{color:grid}},ticks:{{color:ink,callback:v=>v+'%'}}}},}},
    }}
}});

const h2s = D.h2;
document.getElementById('h2Stats').innerHTML =
  '<p class="muted" style="margin:0 0 10px">H2 network totals (5 months — treat correlations as directional)</p>'+
  '<table><tbody>'+
  '<tr><td>H2 billed qty</td><td class="num">'+fmt(h2s.si_qty)+'</td></tr>'+
  '<tr><td>H2 dealer qty</td><td class="num">'+fmt(h2s.so_qty)+'</td></tr>'+
  '<tr><td>H2 sell-through</td><td class="num">'+pct(h2s.sellthrough_pct)+'</td></tr>'+
  '<tr><td>Same-month correlation</td><td class="num">'+(h2s.corr_same_month==null?'—':h2s.corr_same_month)+'</td></tr>'+
  '<tr><td>Lag-1 (sell-in leads sell-out)</td><td class="num">'+(h2s.corr_si_leads_so==null?'—':h2s.corr_si_leads_so)+'</td></tr>'+
  '<tr><td>Sell-in lumpiness (CV)</td><td class="num">'+(h2s.cv_si==null?'—':h2s.cv_si)+'</td></tr>'+
  '<tr><td>Sell-out lumpiness (CV)</td><td class="num">'+(h2s.cv_so==null?'—':h2s.cv_so)+'</td></tr>'+
  '</tbody></table>'+
  '<p class="muted">A replenisher would sit near 100% with sell-out following sell-in. n=5 months is thin — the shape of the bars matters more than r.</p>';

const a = D.annual;
const kh = a.klass;
document.getElementById('annualTake').innerHTML =
  '<strong>CY2025:</strong> billed '+fmt(a.si_qty)+' units, dealers took '+fmt(a.so_qty)+
  ' ('+pct(a.sellthrough_pct)+'). Net warehouse add ≈ '+fmt(a.net_stock_qty)+
  ' units. Coverage hole: '+fmt(a.hole_pn)+' PNs / '+fmt(a.hole_qty)+' units ('+pct(a.hole_share_si_pct)+
  ' of billed qty). Matched PNs '+fmt(kh.matched.pn)+', stock-build '+fmt(kh.stock_build.pn)+
  ', destock '+fmt(kh.destock.pn)+'. Implied Feb–Jul dealer qty (YTD − Jan − H2 months): '+
  fmt(D.h1_context.implied_feb_jul_so)+' vs billed Feb–Jul '+fmt(D.h1_context.si_feb_jul)+'.';

function tbl(rows, kind){{
  if(!rows||!rows.length) return '<p class="muted">None</p>';
  const tag = kind==='coverage_hole'?'hole':kind==='stock_build'?'build':kind==='destock'?'de':'ok';
  let h = '<table><thead><tr><th>P/N</th><th>Description</th><th class="num">Billed</th><th class="num">Dealer</th><th class="num">Gap</th></tr></thead><tbody>';
  rows.forEach(r=>{{
    h += '<tr><td><span class="tag '+tag+'">'+r.pn+'</span></td><td>'+(r.desc||'')+
      '</td><td class="num">'+fmt(r.si)+'</td><td class="num">'+fmt(r.so)+'</td><td class="num">'+fmt(r.gap)+'</td></tr>';
  }});
  return h+'</tbody></table>';
}}
document.getElementById('holeTable').innerHTML = tbl(a.top_hole,'coverage_hole');
document.getElementById('buildTable').innerHTML = tbl(a.top_stock_build,'stock_build');
document.getElementById('destockTable').innerHTML = tbl(a.top_destock,'destock');

const y26 = D.y2026_h1;
new Chart(document.getElementById('c26'),{{
  type:'bar',
  data:{{labels:y26.months.map(m=>m.label),datasets:[
    {{label:'ISZE → UTI (in billing extract)',data:y26.months.map(m=>m.si),backgroundColor:'#1a2b4a',borderRadius:3,barThickness:22}},
    {{label:'UTI → dealers',data:y26.months.map(m=>m.so),backgroundColor:'#c0552d',borderRadius:3,barThickness:22}}
  ]}},
  options:{{responsive:true,maintainAspectRatio:false,
    plugins:{{legend:{{position:'bottom',labels:{{color:ink}}}}}},
    scales:{{x:{{grid:{{display:false}},ticks:{{color:ink}}}},
             y:{{grid:{{color:grid}},ticks:{{color:ink}},beginAtZero:true}}}}}}
}});
document.getElementById('y26note').textContent =
  '2026 Jan–Mar (billing through '+ (y26.billing_max||'Mar') +'): billed '+fmt(y26.si_qty)+
  ' vs dealer '+fmt(y26.so_qty_overlap)+' ('+pct(y26.sellthrough_pct)+
  ' sell-through). Apr–Jun dealer qty '+fmt((y26.so_qty_jan_jun||0) - (y26.so_qty_overlap||0))+
  ' with no billed qty in the extract yet. Extra context only.';
</script>
</body>
</html>
"""
    OUT_HTML.write_text(html, encoding="utf-8")


def main() -> None:
    d = build()
    OUT_JSON.write_text(json.dumps(d, indent=2), encoding="utf-8")
    write_html(d)
    https_hits = len(re.findall(r"""(?:src|href)\s*=\s*['"]https://""", OUT_HTML.read_text(encoding="utf-8")))
    print(json.dumps({
        "json": str(OUT_JSON),
        "html": str(OUT_HTML),
        "html_bytes": OUT_HTML.stat().st_size,
        "https_src_href": https_hits,
        "verdict": d["verdict"],
        "annual_st": d["annual"]["sellthrough_pct"],
        "annual_si": d["annual"]["si_qty"],
        "annual_so": d["annual"]["so_qty"],
        "hole_pn": d["annual"]["hole_pn"],
        "hole_qty": d["annual"]["hole_qty"],
        "h2_si": d["h2"]["si_qty"],
        "h2_so": d["h2"]["so_qty"],
        "h2_st": d["h2"]["sellthrough_pct"],
        "h2_corr": d["h2"]["corr_same_month"],
        "h2_lag": d["h2"]["corr_si_leads_so"],
        "h2_cv_si": d["h2"]["cv_si"],
        "h2_cv_so": d["h2"]["cv_so"],
        "h2_months": d["h2"]["months"],
        "jan": d["jan_2025"],
        "h1": d["h1_context"],
        "y26_st": d["y2026_h1"]["sellthrough_pct"],
        "y26_si": d["y2026_h1"]["si_qty"],
        "y26_so_overlap": d["y2026_h1"]["so_qty_overlap"],
        "y26_bill_max": d["y2026_h1"]["billing_max"],
        "klass": {k: {"pn": v["pn"], "si": round(v["si_qty"]), "so": round(v["so_qty"])} for k, v in d["annual"]["klass"].items()},
        "supersession": d["scope"]["supersession_rolled"],
        "newest_map_rows": d["scope"]["newest_map_rows"],
    }, indent=2))


if __name__ == "__main__":
    main()

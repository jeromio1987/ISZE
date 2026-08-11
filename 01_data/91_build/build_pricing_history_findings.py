"""Year-matched PR00 realization + ZPR1/MOS/NO_LIST/VPACC findings MVP.

Outputs under 01_data/00_derived/ + Mode A HTML under 02_dashboards/pricing/.
List-to-pocket figures are provisional (QA pending) — integrity score included.
"""
from __future__ import annotations

import json
import math
import re
from datetime import datetime, timezone
from pathlib import Path

import openpyxl
import pandas as pd

ISZE = Path(__file__).resolve().parents[2]
DER = ISZE / "01_data" / "00_derived"
DASH = ISZE / "02_dashboards" / "pricing"
KPI_XLSX = ISZE / "01_data" / "11_planning" / "KPI Master File june 2026.xlsx"
MAP_CSV = ISZE / "03_analytics" / "Isuzu" / "prism" / "data" / "sap_sold_to_mapping.csv"

PAYERS = {
    1799: "UTI",
    1797: "UMI",
    2372: "2372",
}

UTC_NOW = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def norm_pn(v) -> str:
    if v is None or (isinstance(v, float) and pd.isna(v)):
        return ""
    if isinstance(v, (int,)):
        return str(int(v))
    s = str(v).strip()
    if s.endswith(".0") and s[:-2].isdigit():
        s = s[:-2]
    digits = re.sub(r"\D", "", s)
    return digits.lstrip("0") or ("0" if digits else "")


def load_pr00(year: int) -> tuple[pd.DataFrame, dict]:
    meta = {"year": year, "blank_prices": 0, "rows": 0, "source": ""}
    if year >= 2026:
        path = DER / "pricing_pr00_ie40.parquet"
        df = pd.read_parquet(path)
        meta["source"] = path.name
        # prefer newest active row per PN with sp_eur > 0
        df = df.rename(columns={"part_number": "Material", "sp_eur": "Price_EUR"})
        df["pn"] = df["Material"].map(norm_pn)
        df["Price_EUR"] = pd.to_numeric(df["Price_EUR"], errors="coerce")
        # Prefer active non-superseded rows for blank count / matching
        if "is_superseded_row" in df.columns:
            active = df[~df["is_superseded_row"].fillna(False)].copy()
        else:
            active = df
        meta["blank_prices"] = int(active["Price_EUR"].isna().sum() + ((active["Price_EUR"] <= 0).sum()))
        meta["rows"] = int(len(df))
        usable = active[active["Price_EUR"].notna() & (active["Price_EUR"] > 0) & (active["pn"] != "")].copy()
        usable = usable.sort_values("Price_EUR", ascending=False).drop_duplicates("pn", keep="first")
        return usable[["pn", "Price_EUR"]], meta

    path = DER / f"pricing_pr00_ie40_{year}.parquet"
    df = pd.read_parquet(path)
    meta["source"] = path.name
    df["pn"] = df["Material"].map(norm_pn)
    df["Price_EUR"] = pd.to_numeric(df["Price_EUR"], errors="coerce")
    meta["blank_prices"] = int(df["Price_EUR"].isna().sum())
    meta["rows"] = int(len(df))
    usable = df[df["Price_EUR"].notna() & (df["Price_EUR"] > 0) & (df["pn"] != "")].copy()
    usable = usable.drop_duplicates("pn", keep="first")
    return usable[["pn", "Price_EUR"]], meta


def load_zpr1(year: int) -> pd.DataFrame:
    if year >= 2026:
        path = DER / "pricing_zpr1.parquet"
        df = pd.read_parquet(path)
        # Engine extract: customer_code / part_number / sp_eur_zpr1
        cust_raw = df["customer_code"] if "customer_code" in df.columns else df["Customer"]
        mat_raw = df["part_number"] if "part_number" in df.columns else df["Material"]
        price_raw = df["sp_eur_zpr1"] if "sp_eur_zpr1" in df.columns else df["Price"]
        out = pd.DataFrame(
            {
                "Customer": pd.to_numeric(cust_raw.astype(str).str.replace(r"\D", "", regex=True), errors="coerce"),
                "pn": mat_raw.map(norm_pn),
                "Price": pd.to_numeric(price_raw, errors="coerce"),
                "list_year": year,
            }
        )
    else:
        path = DER / f"pricing_zpr1_{year}.parquet"
        df = pd.read_parquet(path)
        out = pd.DataFrame(
            {
                "Customer": pd.to_numeric(df["Customer"], errors="coerce"),
                "pn": df["Material"].map(norm_pn),
                "Price": pd.to_numeric(df["Price"], errors="coerce"),
                "list_year": year,
            }
        )
    out = out[out["pn"] != ""].dropna(subset=["Customer", "Price"])
    out = out[out["Price"] > 0]
    out["Customer"] = out["Customer"].astype(int)
    return out.drop_duplicates(["Customer", "pn"], keep="first")


def load_sales() -> pd.DataFrame:
    sf = pd.read_parquet(DER / "sales_fact.parquet")
    sf["pn"] = sf["part_number"].map(norm_pn)
    sf["sold_to_sap"] = pd.to_numeric(sf["sold_to_sap"], errors="coerce")
    sf["net_sales_value"] = pd.to_numeric(sf["net_sales_value"], errors="coerce").fillna(0.0)
    sf["billed_qty"] = pd.to_numeric(sf["billed_qty"], errors="coerce").fillna(0.0)
    # map DB label
    mp = pd.read_csv(MAP_CSV)
    mp["sap_sold_to_pt"] = pd.to_numeric(mp["sap_sold_to_pt"], errors="coerce")
    sf = sf.merge(
        mp[["sap_sold_to_pt", "distributor_code"]],
        left_on="sold_to_sap",
        right_on="sap_sold_to_pt",
        how="left",
    )
    sf["db"] = sf["distributor_code"].fillna(sf["sold_to_sap"].map(lambda x: str(int(x)) if pd.notna(x) else "UNKNOWN"))
    return sf


def realization_for_year(sf: pd.DataFrame, year: int) -> tuple[pd.DataFrame, pd.DataFrame, dict]:
    pr, pr_meta = load_pr00(year)
    y = sf[sf["year"] == year].copy()
    if year >= 2026:
        # YTD already in sales_fact through Mar 2026
        pass
    total_eur = float(y["net_sales_value"].sum())
    total_lines = int(len(y))
    m = y.merge(pr, on="pn", how="left", indicator=True)
    matched = m["_merge"] == "both"
    m["list_value"] = m["billed_qty"] * m["Price_EUR"]
    # realization only where qty>0, list>0, and list_value meaningful
    ok = matched & (m["billed_qty"] > 0) & (m["Price_EUR"] > 0) & (m["list_value"] > 0)
    matched_eur = float(m.loc[ok, "net_sales_value"].sum())
    list_eur = float(m.loc[ok, "list_value"].sum())
    realization = (matched_eur / list_eur) if list_eur > 0 else float("nan")
    coverage = (matched_eur / total_eur) if total_eur else 0.0
    no_list_eur = float(m.loc[~matched, "net_sales_value"].sum())

    net = pd.DataFrame(
        [
            {
                "year": year,
                "period": "CY" if year < 2026 else "CY_YTD",
                "billing_end": str(pd.to_datetime(y["billing_date"]).max().date()) if len(y) else None,
                "parts_eur": round(total_eur, 2),
                "lines": total_lines,
                "matched_eur": round(matched_eur, 2),
                "no_list_eur": round(no_list_eur, 2),
                "coverage_pct": round(100.0 * coverage, 2),
                "list_value_eur": round(list_eur, 2),
                "realization_pct": round(100.0 * realization, 2) if realization == realization else None,
                "pr00_blank_prices": pr_meta["blank_prices"],
                "pr00_source": pr_meta["source"],
                "status": "provisional_qa_pending",
            }
        ]
    )

    by_db = (
        m.assign(matched=ok.astype(int))
        .groupby("db", dropna=False)
        .agg(
            parts_eur=("net_sales_value", "sum"),
            matched_eur=("net_sales_value", lambda s: s[ok.loc[s.index]].sum() if len(s) else 0.0),
            list_value_eur=("list_value", lambda s: s[ok.loc[s.index]].sum() if len(s) else 0.0),
            lines=("net_sales_value", "size"),
        )
        .reset_index()
    )
    # recompute properly
    rows = []
    for db, g in m.groupby("db", dropna=False):
        g_ok = g[ok.loc[g.index]]
        pe = float(g["net_sales_value"].sum())
        me = float(g_ok["net_sales_value"].sum())
        lv = float(g_ok["list_value"].sum())
        rows.append(
            {
                "year": year,
                "db": db,
                "parts_eur": round(pe, 2),
                "matched_eur": round(me, 2),
                "no_list_eur": round(pe - me, 2),
                "coverage_pct": round(100.0 * me / pe, 2) if pe else None,
                "list_value_eur": round(lv, 2),
                "realization_pct": round(100.0 * me / lv, 2) if lv > 0 else None,
            }
        )
    by_db = pd.DataFrame(rows).sort_values(["year", "parts_eur"], ascending=[True, False])

    detail = {
        "year": year,
        "pr00_meta": pr_meta,
        "pn_match_rate": round(100.0 * m.loc[matched, "pn"].nunique() / max(1, y["pn"].nunique()), 2),
        "unique_pns_billed": int(y["pn"].nunique()),
        "unique_pns_matched": int(m.loc[matched, "pn"].nunique()),
    }
    return net, by_db, detail


def zpr1_vs_pr00_yoy() -> tuple[pd.DataFrame, dict]:
    """Median ZPR1 vs year PR00 for key payers; YoY ZPR1 price change on common PNs."""
    rows = []
    issues = []
    for year in (2023, 2024, 2025, 2026):
        try:
            z = load_zpr1(year)
            pr, _ = load_pr00(year)
        except Exception as e:  # noqa: BLE001
            issues.append(f"{year}: {e}")
            continue
        pr_map = pr.set_index("pn")["Price_EUR"]
        for cust, label in PAYERS.items():
            zc = z[z["Customer"] == cust].copy()
            if zc.empty:
                issues.append(f"{year} customer {cust} ({label}): no ZPR1 rows")
                continue
            zc["pr00"] = zc["pn"].map(pr_map)
            both = zc[zc["pr00"].notna() & (zc["pr00"] > 0)]
            if both.empty:
                continue
            ratio = both["Price"] / both["pr00"]
            rows.append(
                {
                    "year": year,
                    "customer": cust,
                    "payer": label,
                    "n_zpr1_pns": int(zc["pn"].nunique()),
                    "n_vs_pr00": int(both["pn"].nunique()),
                    "median_zpr1_vs_pr00_pct": round(100.0 * (float(ratio.median()) - 1.0), 2),
                    "p25_zpr1_vs_pr00_pct": round(100.0 * (float(ratio.quantile(0.25)) - 1.0), 2),
                    "p75_zpr1_vs_pr00_pct": round(100.0 * (float(ratio.quantile(0.75)) - 1.0), 2),
                    "note": "UTI≠UMI; never blend",
                }
            )

    lev = pd.DataFrame(rows)
    # YoY ZPR1 on overlapping PNs per payer 2024→2025→2026 and 2023→2024
    yoy_rows = []
    for cust, label in PAYERS.items():
        for y0, y1 in ((2023, 2024), (2024, 2025), (2025, 2026)):
            try:
                a = load_zpr1(y0)
                b = load_zpr1(y1)
            except Exception as e:  # noqa: BLE001
                issues.append(f"yoy {y0}-{y1}: {e}")
                continue
            a = a[a["Customer"] == cust][["pn", "Price"]].rename(columns={"Price": "p0"})
            b = b[b["Customer"] == cust][["pn", "Price"]].rename(columns={"Price": "p1"})
            j = a.merge(b, on="pn")
            if j.empty:
                continue
            chg = j["p1"] / j["p0"] - 1.0
            yoy_rows.append(
                {
                    "from_year": y0,
                    "to_year": y1,
                    "customer": cust,
                    "payer": label,
                    "n_common_pns": int(len(j)),
                    "median_zpr1_yoy_pct": round(100.0 * float(chg.median()), 2),
                    "p25_zpr1_yoy_pct": round(100.0 * float(chg.quantile(0.25)), 2),
                    "p75_zpr1_yoy_pct": round(100.0 * float(chg.quantile(0.75)), 2),
                }
            )
    yoy = pd.DataFrame(yoy_rows)
    meta = {"issues": issues, "payers": PAYERS, "built_at_utc": UTC_NOW}
    return lev, yoy, meta


def extract_mos() -> tuple[pd.DataFrame, pd.DataFrame, dict]:
    """KPI Days of Parts in Stock — NOT market elasticity."""
    wb = openpyxl.load_workbook(KPI_XLSX, read_only=True, data_only=True)
    ws = wb["Parts Handling"]
    rows = list(ws.iter_rows(values_only=True, max_row=26))
    wb.close()
    header = list(rows[2])
    months = [str(h) for h in header[1:] if h is not None]

    def parse_cell(v):
        if v is None:
            return None
        if isinstance(v, (int, float)) and not isinstance(v, bool):
            if isinstance(v, float) and (math.isnan(v) or math.isinf(v)):
                return None
            return float(v)
        s = str(v).strip().replace(",", ".")
        if not s or s.upper() in {"N/A", "N/D", "IBX", "ISZE", "NONE"}:
            return None
        try:
            return float(s)
        except ValueError:
            return None

    long_rows = []
    for r in rows[3:]:
        if not r or r[0] is None:
            continue
        name = str(r[0]).strip()
        if name in {"First Fill Rate", "Distributor"}:
            break
        for i, mon in enumerate(months):
            val = parse_cell(r[i + 1] if i + 1 < len(r) else None)
            # map month token to year-month
            ym = _month_token_to_ym(mon)
            if ym is None:
                continue
            long_rows.append(
                {
                    "distributor": name,
                    "month_label": mon,
                    "year_month": ym,
                    "cy": int(ym[:4]),
                    "mos_days": val,
                }
            )
    long = pd.DataFrame(long_rows)
    # focus CY2025 + CY2026 YTD
    focus = long[long["cy"].isin([2025, 2026])].copy()
    summary = []
    for db, g in focus.groupby("distributor"):
        g25 = g[(g["cy"] == 2025) & g["mos_days"].notna()]
        g26 = g[(g["cy"] == 2026) & g["mos_days"].notna()]
        summary.append(
            {
                "distributor": db,
                "n_months_2025": int(len(g25)),
                "avg_mos_days_2025": round(float(g25["mos_days"].mean()), 2) if len(g25) else None,
                "n_months_2026_ytd": int(len(g26)),
                "avg_mos_days_2026_ytd": round(float(g26["mos_days"].mean()), 2) if len(g26) else None,
                "delta_days_2026_vs_2025": (
                    round(float(g26["mos_days"].mean()) - float(g25["mos_days"].mean()), 2)
                    if len(g25) and len(g26)
                    else None
                ),
                "label": "KPI Days of Parts in Stock — NOT market elasticity; ISZE→DB volume elasticity non-quotable",
            }
        )
    summ = pd.DataFrame(summary).sort_values("avg_mos_days_2025", ascending=False, na_position="last")
    meta = {
        "source": str(KPI_XLSX.relative_to(ISZE)).replace("\\", "/"),
        "metric": "Days of Parts in Stock (MOS days)",
        "caveat": "Warehouse / ordering response proxy only — not end-market price elasticity",
        "built_at_utc": UTC_NOW,
        "dbs_with_any_2025": int((summ["n_months_2025"] > 0).sum()),
        "dbs_with_any_2026": int((summ["n_months_2026_ytd"] > 0).sum()),
    }
    return focus, summ, meta


def _month_token_to_ym(tok: str) -> str | None:
    t = tok.strip().lower().replace(".", "")
    # German/English abbreviations
    map_m = {
        "jan": 1,
        "feb": 2,
        "mar": 3,
        "mrz": 3,
        "apr": 4,
        "may": 5,
        "mai": 5,
        "jun": 6,
        "jul": 7,
        "aug": 8,
        "sep": 9,
        "oct": 10,
        "okt": 10,
        "nov": 11,
        "dec": 12,
        "dez": 12,
    }
    # tokens like "Apr 24", "Jan 26"
    parts = t.split()
    if len(parts) != 2:
        return None
    mon = map_m.get(parts[0][:3])
    if mon is None:
        return None
    try:
        yy = int(parts[1])
    except ValueError:
        return None
    year = 2000 + yy if yy < 100 else yy
    return f"{year:04d}-{mon:02d}"


def nolist_summary() -> tuple[pd.DataFrame, dict]:
    gap = pd.read_csv(DER / "no_pr00_gap_cy2025_ranked.csv")
    meta_path = DER / "no_pr00_gap_cy2025_ranked.meta.json"
    meta = json.loads(meta_path.read_text(encoding="utf-8")) if meta_path.exists() else {}
    top = gap.head(25).copy()
    by_reason = (
        gap.groupby("gap_reason", dropna=False)
        .agg(pn_count=("part_number", "count"), gap_eur=("cy2025_eur", "sum"))
        .reset_index()
        .sort_values("gap_eur", ascending=False)
    )
    summary = {
        "built_at_utc": UTC_NOW,
        "source_csv": "01_data/00_derived/no_pr00_gap_cy2025_ranked.csv",
        "pn_count": int(meta.get("pn_count", gap["part_number"].nunique())),
        "gap_eur": float(meta.get("gap_eur", gap["cy2025_eur"].sum())),
        "gap_share_of_parts": float(meta.get("gap_share_of_parts", 0)),
        "by_reason": by_reason.to_dict(orient="records"),
        "top_pn": str(meta.get("largest_pn", gap.iloc[0]["part_number"] if len(gap) else "")),
    }
    return top, summary


def vpacc_snapshot() -> tuple[pd.DataFrame, dict]:
    p = DER / "vpacc_fy2027_action_plan_july.parquet"
    df = pd.read_parquet(p)
    status = (
        df.groupby(["stream", "progress_status"], dropna=False)
        .size()
        .reset_index(name="n")
        .sort_values(["stream", "n"], ascending=[True, False])
    )
    # open = not completed
    completed = {"completed_and_eval"}
    open_mask = ~df["progress_status"].isin(completed) | df["progress_status"].isna()
    # treat None/NaN as open
    open_n = int(df["progress_status"].isna().sum() + (~df["progress_status"].isin(completed) & df["progress_status"].notna()).sum())
    # simpler:
    done_n = int(df["progress_status"].isin(list(completed)).sum())
    open_n = int(len(df) - done_n)
    snap = {
        "built_at_utc": UTC_NOW,
        "source": "01_data/00_derived/vpacc_fy2027_action_plan_july.parquet",
        "total_actions": int(len(df)),
        "open_or_in_progress": open_n,
        "completed_and_eval": done_n,
        "by_status": df["progress_status"].fillna("blank").value_counts().to_dict(),
        "by_stream": df.groupby("stream").size().to_dict(),
        "note": "Status snapshot only — thin join to pricing metrics; PIC-keyed not dealer-keyed",
    }
    return status, snap


def integrity_score(ctx: dict) -> dict:
    """0–100 with explicit deductions. Expect errors."""
    score = 100
    deductions = []

    # PN match quality (avg across years)
    pn_rates = [d.get("pn_match_rate", 0) for d in ctx["realization_details"]]
    avg_pn = sum(pn_rates) / max(1, len(pn_rates))
    if avg_pn < 95:
        d = min(15, int(round((95 - avg_pn) * 0.8)))
        score -= d
        deductions.append({"item": "PN match quality", "deduction": d, "detail": f"Avg unique-PN match {avg_pn:.1f}% vs billed"})

    # Coverage %
    covs = [r["coverage_pct"] for r in ctx["network"] if r.get("coverage_pct") is not None]
    avg_cov = sum(covs) / max(1, len(covs))
    if avg_cov < 90:
        d = min(18, int(round((90 - avg_cov) * 1.2)))
        score -= d
        deductions.append({"item": "List coverage %", "deduction": d, "detail": f"Avg matched revenue coverage {avg_cov:.1f}% (NO_LIST gap)"})

    # Blank PR00 prices (history #VALUE! + unusable current list)
    blanks_hist = sum(
        d.get("pr00_meta", {}).get("blank_prices", 0)
        for d in ctx["realization_details"]
        if d.get("year", 0) < 2026
    )
    blanks_2026 = next(
        (d.get("pr00_meta", {}).get("blank_prices", 0) for d in ctx["realization_details"] if d.get("year") == 2026),
        0,
    )
    if blanks_hist:
        d = min(6, 2 + blanks_hist // 2)
        score -= d
        deductions.append(
            {
                "item": "Blank PR00 prices (#VALUE!/null)",
                "deduction": d,
                "detail": f"{blanks_hist} blank/unusable Price_EUR in 2023–2025 history extracts",
            }
        )
    if blanks_2026 > 100:
        d = 4
        score -= d
        deductions.append(
            {
                "item": "2026 PR00 unusable prices",
                "deduction": d,
                "detail": f"{blanks_2026} blank/non-positive SP on active current PR00 rows",
            }
        )

    # Year alignment assumptions
    d = 10
    score -= d
    deductions.append(
        {
            "item": "Year alignment assumptions",
            "deduction": d,
            "detail": "PR00 history stamps are year-end conventional (2024/2025 sheet labels; 2023 mixed workbook). Intra-year list changes not dated.",
        }
    )

    # 2026 uses current list not year-end snapshot
    d = 6
    score -= d
    deductions.append(
        {
            "item": "2026 list vintage",
            "deduction": d,
            "detail": "2026 YTD joins current IE40 PR00 extract (2026-08-10), not a 2026-01 list snapshot",
        }
    )

    # MOS sample
    mos_dbs = ctx["mos_meta"].get("dbs_with_any_2025", 0)
    if mos_dbs < 15:
        d = min(12, 15 - mos_dbs)
        score -= d
        deductions.append({"item": "MOS sample size", "deduction": d, "detail": f"Only {mos_dbs} DBs with numeric MOS in 2025; sparse N/D/N/A"})

    # ZPR1 customer coverage
    z_issues = len(ctx.get("zpr1_meta", {}).get("issues", []))
    if z_issues:
        d = min(8, z_issues)
        score -= d
        deductions.append({"item": "ZPR1 customer coverage", "deduction": d, "detail": f"{z_issues} load/coverage issues logged"})

    # FY vs CY
    d = 5
    score -= d
    deductions.append({"item": "FY vs CY caveat", "deduction": d, "detail": "Realization is calendar-year; VPACC/KPI MOS mix FY labels — do not blend without care"})

    # Quotability gate
    d = 8
    score -= d
    deductions.append(
        {
            "item": "First-pass join (QA pending)",
            "deduction": d,
            "detail": "Year-matched joins not independently validated — provisional / internal QA only",
        }
    )

    score = max(0, min(100, score))
    band = "weak" if score < 55 else ("provisional" if score < 75 else "usable_internal")
    return {
        "score": score,
        "band": band,
        "quotable_externally": False,
        "label": "Internal QA / provisional — do not quote list-to-pocket externally",
        "deductions": deductions,
        "built_at_utc": UTC_NOW,
    }


def write_html(payload: dict, path: Path) -> None:
    n = payload["network"]
    integ = payload["integrity"]
    gap = payload["nolist"]
    mos = payload["mos_summary"]
    zlev = payload["zpr1_level"]
    zyoy = payload["zpr1_yoy"]
    vp = payload["vpacc"]

    def eur(x):
        if x is None:
            return "—"
        return f"€{x:,.1f}M" if abs(x) >= 1_000_000 else f"€{x:,.0f}"

    def pct(x):
        return "—" if x is None else f"{x:.1f}%"

    net_rows = "".join(
        f"<tr><td>{r['year']}</td><td>{r['period']}</td><td class='n'>{eur(r['parts_eur'])}</td>"
        f"<td class='n'>{pct(r['coverage_pct'])}</td><td class='n'>{pct(r['realization_pct'])}</td>"
        f"<td class='n'>{eur(r['no_list_eur'])}</td><td class='sm'>{r['billing_end'] or ''}</td></tr>"
        for r in n
    )

    z_rows = "".join(
        f"<tr><td>{r['year']}</td><td>{r['payer']} ({r['customer']})</td>"
        f"<td class='n'>{r['n_vs_pr00']:,}</td><td class='n'>{r['median_zpr1_vs_pr00_pct']:+.1f}%</td>"
        f"<td class='n'>{r['p25_zpr1_vs_pr00_pct']:+.1f}% … {r['p75_zpr1_vs_pr00_pct']:+.1f}%</td></tr>"
        for r in zlev
    )
    zy_rows = "".join(
        f"<tr><td>{r['from_year']}→{r['to_year']}</td><td>{r['payer']} ({r['customer']})</td>"
        f"<td class='n'>{r['n_common_pns']:,}</td><td class='n'>{r['median_zpr1_yoy_pct']:+.1f}%</td></tr>"
        for r in zyoy
    )

    def _fmt_num(v, signed=False):
        if v is None:
            return ""
        return f"{v:+.0f}" if signed else f"{v:.0f}"

    mos_rows = "".join(
        "<tr><td>{dist}</td><td class='n'>{n25}</td>"
        "<td class='n'>{a25}</td><td class='n'>{n26}</td>"
        "<td class='n'>{a26}</td><td class='n'>{dlt}</td></tr>".format(
            dist=r["distributor"],
            n25=r["n_months_2025"],
            a25=_fmt_num(r["avg_mos_days_2025"]),
            n26=r["n_months_2026_ytd"],
            a26=_fmt_num(r["avg_mos_days_2026_ytd"]),
            dlt=_fmt_num(r["delta_days_2026_vs_2025"], signed=True),
        )
        for r in mos[:18]
    )

    gap_rows = "".join(
        f"<tr><td class='mono'>{r['part_number']}</td><td>{r.get('description','')}</td>"
        f"<td class='n'>{eur(float(r['cy2025_eur']))}</td><td class='sm'>{r.get('gap_reason','')}</td></tr>"
        for r in payload["nolist_top"][:12]
    )

    ded_rows = "".join(
        f"<tr><td>−{d['deduction']}</td><td>{d['item']}</td><td class='sm'>{d['detail']}</td></tr>"
        for d in integ["deductions"]
    )

    cy25 = next((r for r in n if r["year"] == 2025), {})
    conclusion = (
        f"Year-matched PR00 realization is provisional (integrity {integ['score']}/100). "
        f"CY2025 matched coverage {pct(cy25.get('coverage_pct'))}; "
        f"realization on matched lines {pct(cy25.get('realization_pct'))}. "
        f"NO_LIST gap ≈ {eur(gap.get('gap_eur', 0))} ({100*gap.get('gap_share_of_parts',0):.1f}% of CY2025 parts). "
        "Do not quote list-to-pocket externally until QA closes."
    )

    html = f"""<!DOCTYPE html>
<html lang="en"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>ISZE · Pricing History Findings</title>
<style>
*{{box-sizing:border-box}}
body{{margin:0;background:#fff;color:#1A1A1A;font:15px/1.55 "Segoe UI",Arial,sans-serif}}
.wrap{{max-width:1120px;margin:0 auto;padding:0 28px 80px}}
header{{border-bottom:3px solid #CC0E1E;padding:36px 0 18px;margin-bottom:28px}}
.brand{{font:800 13px/1 Arial Black,Arial;letter-spacing:.22em;color:#CC0E1E;margin-bottom:14px}}
h1{{font-size:30px;margin:0 0 8px;letter-spacing:-.3px}}
.sub{{color:#5A5A5A;max-width:820px}}
.stamp{{color:#5A5A5A;font-size:12.5px;margin-top:12px}}
.callout{{border-left:4px solid #B45309;background:#FEF8F0;padding:14px 16px;margin:0 0 22px}}
.callout b{{color:#B45309}}
.kpis{{display:grid;grid-template-columns:repeat(auto-fit,minmax(170px,1fr));gap:12px;margin:0 0 28px}}
.kpi{{border:1px solid #E4E4E7;border-top:3px solid #CC0E1E;padding:14px}}
.kpi .v{{font-size:28px;font-weight:800;letter-spacing:-1px}}
.kpi .l{{font-size:11px;color:#5A5A5A;text-transform:uppercase;letter-spacing:.06em;margin-top:6px;font-weight:600}}
.kpi.amber{{border-top-color:#B45309}}.kpi.amber .v{{color:#B45309}}
h2{{font-size:20px;margin:36px 0 8px}}
.lead{{color:#5A5A5A;font-size:14px;margin:0 0 14px;max-width:860px}}
table{{width:100%;border-collapse:collapse;font-size:13px;margin-bottom:8px}}
th{{background:#CC0E1E;color:#fff;text-align:left;padding:8px 10px;font-size:11px;text-transform:uppercase;letter-spacing:.04em}}
td{{padding:7px 10px;border-bottom:1px solid #F0F0F0}}
tbody tr:nth-child(even){{background:#FAFAFA}}
td.n,th.n{{text-align:right;font-variant-numeric:tabular-nums}}
td.sm{{font-size:12px;color:#5A5A5A}} td.mono{{font-family:Consolas,monospace;font-size:12px}}
.foot{{margin-top:48px;padding-top:16px;border-top:1px solid #E4E4E7;font-size:11.5px;color:#5A5A5A}}
.badge{{display:inline-block;padding:4px 10px;background:#FEF8F0;color:#B45309;font-weight:700;font-size:12px;border:1px solid #F0D7B0}}
</style></head><body>
<div class="wrap">
<header>
  <div class="brand">ISUZU · ISZE</div>
  <h1>Pricing history findings</h1>
  <div class="sub">Year-matched PR00 realization (2023–2025 + 2026 YTD), ZPR1 vs PR00 for key payers,
  KPI MOS stock days, NO_LIST gap, and VPACC action status. Internal QA pack.</div>
  <div class="stamp">Built {UTC_NOW} · Integrity score <b>{integ['score']}/100</b> ({integ['band']}) ·
  <span class="badge">Provisional — not externally quotable</span></div>
</header>

<div class="callout"><b>Conclusion.</b> {conclusion}</div>

<div class="kpis">
  <div class="kpi amber"><div class="v">{integ['score']}</div><div class="l">Integrity / 100</div></div>
  <div class="kpi"><div class="v">{pct(cy25.get('realization_pct'))}</div><div class="l">CY2025 realization (matched)</div></div>
  <div class="kpi amber"><div class="v">{pct(cy25.get('coverage_pct'))}</div><div class="l">CY2025 list coverage</div></div>
  <div class="kpi amber"><div class="v">{gap.get('pn_count', '—')}</div><div class="l">NO_LIST PNs CY2025</div></div>
  <div class="kpi"><div class="v">{vp.get('open_or_in_progress','—')}</div><div class="l">VPACC open actions</div></div>
</div>

<h2>1. Year-matched PR00 realization</h2>
<p class="lead">Billing net ÷ (qty × year PR00 list) on matched lines only. Coverage footnote = matched € / all parts €.
2026 uses current IE40 PR00 extract. Status: provisional QA pending.</p>
<table><thead><tr><th>Year</th><th>Period</th><th class="n">Parts €</th><th class="n">Coverage</th>
<th class="n">Realization</th><th class="n">NO_LIST €</th><th>Billing end</th></tr></thead>
<tbody>{net_rows}</tbody></table>

<h2>2. ZPR1 vs PR00 (UTI / UMI — never blend)</h2>
<p class="lead">Customer-condition list vs network PR00 for the same year. Optional payer 2372 included when present.
Median gap vs PR00 and YoY ZPR1 change on common part numbers.</p>
<table><thead><tr><th>Year</th><th>Payer</th><th class="n">PNs vs PR00</th><th class="n">Median vs PR00</th><th class="n">P25–P75</th></tr></thead>
<tbody>{z_rows}</tbody></table>
<table><thead><tr><th>YoY</th><th>Payer</th><th class="n">Common PNs</th><th class="n">Median ZPR1 YoY</th></tr></thead>
<tbody>{zy_rows}</tbody></table>

<h2>3. MOS response 2025–26 (KPI stock days)</h2>
<p class="lead"><b>Not market elasticity.</b> KPI “Days of Parts in Stock” is a warehouse / ordering response signal.
ISZE→DB volume elasticity remains non-quotable. Source: KPI Master File June 2026 · Parts Handling.</p>
<table><thead><tr><th>Distributor</th><th class="n">n 2025</th><th class="n">Avg MOS 2025</th>
<th class="n">n 2026 YTD</th><th class="n">Avg MOS 2026</th><th class="n">Δ days</th></tr></thead>
<tbody>{mos_rows}</tbody></table>

<h2>4. NO_LIST gap (CY2025)</h2>
<p class="lead">{gap.get('pn_count')} part numbers · {eur(gap.get('gap_eur',0))} ·
{100*gap.get('gap_share_of_parts',0):.1f}% of CY2025 parts revenue without usable PR00 price.</p>
<table><thead><tr><th>Part</th><th>Description</th><th class="n">CY2025 €</th><th>Reason</th></tr></thead>
<tbody>{gap_rows}</tbody></table>

<h2>5. VPACC action status (FY2027 July update)</h2>
<p class="lead">Light link — status snapshot only ({vp.get('total_actions')} actions).
Open/in progress: <b>{vp.get('open_or_in_progress')}</b> · Completed &amp; eval: <b>{vp.get('completed_and_eval')}</b>.
Join to pricing metrics is thin (PIC / stream keys, not dealer).</p>

<h2>Integrity score breakdown</h2>
<p class="lead">Start 100; explicit deductions below. Band: <b>{integ['band']}</b>. External quote: <b>no</b>.</p>
<table><thead><tr><th>Pts</th><th>Item</th><th>Detail</th></tr></thead>
<tbody>{ded_rows}</tbody></table>

<div class="foot">
Sources: sales_fact.parquet · pricing_pr00_ie40_YYYY.parquet · pricing_zpr1_YYYY.parquet ·
no_pr00_gap_cy2025_ranked.csv · KPI Master File june 2026.xlsx · vpacc_fy2027_action_plan_july.parquet.<br>
Mode A pack · UTI and UMI kept separate · Built {UTC_NOW}
</div>
</div>
</body></html>
"""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(html, encoding="utf-8")


def main() -> int:
    print("Loading sales_fact…")
    sf = load_sales()

    net_frames = []
    db_frames = []
    details = []
    for year in (2023, 2024, 2025, 2026):
        print(f"  realization {year}…")
        net, by_db, detail = realization_for_year(sf, year)
        net_frames.append(net)
        db_frames.append(by_db)
        details.append(detail)

    network = pd.concat(net_frames, ignore_index=True)
    by_db = pd.concat(db_frames, ignore_index=True)

    print("ZPR1 vs PR00…")
    zlev, zyoy, zmeta = zpr1_vs_pr00_yoy()

    print("MOS KPI…")
    mos_long, mos_sum, mos_meta = extract_mos()

    print("NO_LIST…")
    gap_top, gap_sum = nolist_summary()

    print("VPACC…")
    vp_status, vp_snap = vpacc_snapshot()

    ctx = {
        "network": network.to_dict(orient="records"),
        "realization_details": details,
        "mos_meta": mos_meta,
        "zpr1_meta": zmeta,
    }
    integ = integrity_score(ctx)

    # write derived
    outs = {
        "pr00_realization_network_cy.csv": network,
        "pr00_realization_by_db_cy.csv": by_db,
        "zpr1_vs_pr00_by_payer_year.csv": zlev,
        "zpr1_yoy_by_payer.csv": zyoy,
        "kpi_mos_days_2025_2026_long.csv": mos_long,
        "kpi_mos_response_summary_2025_2026.csv": mos_sum,
        "no_pr00_gap_top25_summary.csv": gap_top,
        "vpacc_fy2027_status_by_stream.csv": vp_status,
    }
    for name, df in outs.items():
        p = DER / name
        df.to_csv(p, index=False)
        print(f"  wrote {p.name} ({len(df)} rows)")

    payload = {
        "built_at_utc": UTC_NOW,
        "status": "provisional_qa_pending",
        "quotable_externally": False,
        "network": network.to_dict(orient="records"),
        "realization_details": details,
        "zpr1_level": zlev.to_dict(orient="records"),
        "zpr1_yoy": zyoy.to_dict(orient="records"),
        "zpr1_meta": zmeta,
        "mos_summary": mos_sum.to_dict(orient="records"),
        "mos_meta": mos_meta,
        "nolist": gap_sum,
        "nolist_top": gap_top.to_dict(orient="records"),
        "vpacc": vp_snap,
        "integrity": integ,
        "outputs": {k: f"01_data/00_derived/{k}" for k in outs},
        "html": "02_dashboards/pricing/ISZE_Pricing_History_Findings_Dashboard.html",
    }
    meta_path = DER / "pricing_history_findings.meta.json"
    meta_path.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")
    print(f"  wrote {meta_path.name}")

    # compact JSON beside HTML for offline
    DASH.mkdir(parents=True, exist_ok=True)
    dash_json = DASH / "pricing_history_findings.json"
    dash_json.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")

    html_path = DASH / "ISZE_Pricing_History_Findings_Dashboard.html"
    write_html(payload, html_path)
    print(f"HTML -> {html_path}")
    print(f"INTEGRITY SCORE: {integ['score']}/100 ({integ['band']})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

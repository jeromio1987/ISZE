# -*- coding: utf-8 -*-
"""Year-end behaviour across the nine distributors - the evidence for argument 1 of
ISZE_Kickback_Japan_Final_2026-10-09.pptx.

Question: do distributors jump in at the end of the fiscal year to cross the target and
leave stock behind?

Every figure is read from these files; nothing is typed in:
  01_data/00_derived/sales_fact.parquet                  billing (net_sales_value), sold-to codes
  01_data/11_planning/budget_per_DB_reviewed_24042026.xlsx  'Incentive FY27', BP FY26 per customer
  01_data/00_derived/dealer_sellout_long_*.csv           dealer volume (month grain only)

Sold-to codes are the ones the earlier kickback builder used (build_kickback_jump_case.py).
Writes _analysis_yearend_20261009.json beside this script.
"""
import json
import sys
from pathlib import Path

import numpy as np
import openpyxl
import pandas as pd

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
ROOT = Path(r"C:\Users\jerom\Desktop\claude\ISZE")
DER = ROOT / "01_data" / "00_derived"
PLANF = ROOT / "01_data" / "11_planning" / "budget_per_DB_reviewed_24042026.xlsx"
OUT = Path(__file__).resolve().parent / "_analysis_yearend_20261009.json"

CODES = {"IUK": [2574], "UMI": [1797], "UTI": [1799], "Benelux": [90],
         "Germany": [93, 2516, 601], "Portugal": [519, 92], "Ireland": [76],
         "Norway": [86], "Sweden": [2181], "ITUK": [2575]}
DIST = ["IUK", "UMI", "UTI", "Germany", "Benelux", "Portugal", "Sweden", "Norway", "Ireland"]

# ---- plan FY2026 per customer, from the workbook
wb = openpyxl.load_workbook(PLANF, data_only=True)
ws = wb["Incentive FY27"]
PLAN = {}
for r in ws.iter_rows(min_row=3, values_only=True):
    if r[0] is None or str(r[0]).startswith("Total"):
        continue
    PLAN[{"IBX": "Benelux", "ISD": "Germany"}.get(str(r[0]).strip(), str(r[0]).strip())] = float(r[1])
wb.close()

sf = pd.read_parquet(DER / "sales_fact.parquet",
                     columns=["billing_date", "sold_to_sap", "net_sales_value",
                              "part_number", "billed_qty"])
sf["d"] = pd.to_datetime(sf["billing_date"], errors="coerce")
sf = sf.dropna(subset=["d"]).copy()
sf["code"] = pd.to_numeric(sf["sold_to_sap"], errors="coerce")
sf["eur"] = pd.to_numeric(sf["net_sales_value"], errors="coerce").fillna(0.0)
sf["fy"] = sf["d"].dt.year + (sf["d"].dt.month >= 4).astype(int)
sf["m"] = sf["d"].dt.month
sf["ym"] = sf["d"].dt.to_period("M").astype(str)


def sub(name):
    return sf[sf["code"].isin(CODES[name])]


def between(x, a, b):
    return x[(x["d"] >= a) & (x["d"] <= b)]["eur"].sum()


res = {"sources": {"billing": str(DER / "sales_fact.parquet"),
                   "plan": str(PLANF) + " 'Incentive FY27'",
                   "billing_range": [str(sf["d"].min().date()), str(sf["d"].max().date())]}}

# ---- 1. Feb+Mar share of the fiscal year, three fiscal years
x9 = sf[sf["code"].isin(sum((CODES[n] for n in DIST), []))]
share = {}
for fy in (2024, 2025, 2026):
    y = x9[x9["fy"] == fy]
    share[f"FY{fy}"] = round(100 * y[y["m"].isin([2, 3])]["eur"].sum() / y["eur"].sum(), 1)
res["febmar_share_9dist"] = share
res["febmar_share_even"] = round(100 * 2 / 12, 1)
per = {}
for n in DIST + ["ITUK"]:
    x = sub(n)
    per[n] = {}
    for fy in (2024, 2025, 2026):
        y = x[x["fy"] == fy]
        per[n][f"FY{fy}"] = round(100 * y[y["m"].isin([2, 3])]["eur"].sum() / y["eur"].sum(), 1)
res["febmar_share_per_db"] = per
xall = sf[sf["code"].isin(sum(CODES.values(), []))]
res["febmar_share_10_incl_ituk"] = {
    f"FY{fy}": round(100 * xall[(xall.fy == fy) & xall.m.isin([2, 3])]["eur"].sum()
                     / xall[xall.fy == fy]["eur"].sum(), 1) for fy in (2024, 2025, 2026)}

# ---- 2. pace at end of January FY2026, need vs bought, final vs plan
pace = {}
for n in DIST + ["ITUK"]:
    x = sub(n)
    aj = between(x, "2025-04-01", "2026-01-31")
    fm = between(x, "2026-02-01", "2026-03-31")
    p = PLAN[n]
    pace[n] = {"plan_fy26": round(p, 2), "apr_jan": round(aj, 2),
               "pace_pct_of_10m_plan": round(100 * aj / (p * 10 / 12), 1),
               "needed_feb_mar": round(p - aj, 2), "bought_feb_mar": round(fm, 2),
               "fy26_billed": round(aj + fm, 2), "vs_plan_eur": round(aj + fm - p, 2),
               "vs_plan_pct": round(100 * (aj + fm) / p - 100, 1)}
res["pace"] = pace
res["ahead_at_january"] = [n for n in DIST if pace[n]["pace_pct_of_10m_plan"] >= 100]
res["short_at_year_end"] = [n for n in DIST if pace[n]["vs_plan_eur"] < 0]

# ---- 3. March split at the 13 March price change, per working day
bd = lambda a, b: int(np.busday_count(a, b))
msplit = {}
for n in DIST + ["ITUK"]:
    x = sub(n)
    a = between(x, "2026-03-01", "2026-03-12") / bd("2026-03-01", "2026-03-13")
    b = between(x, "2026-03-13", "2026-03-31") / bd("2026-03-13", "2026-04-01")
    msplit[n] = {"per_wd_before": round(a), "per_wd_after": round(b),
                 "after_higher": bool(b > a)}
res["march_split_per_working_day"] = msplit

# ---- 4. the months after: Apr+May 2026 against the FY2026 monthly average
after = {}
for n in DIST + ["ITUK"]:
    x = sub(n)
    fy = between(x, "2025-04-01", "2026-03-31")
    am = between(x, "2026-04-01", "2026-05-31")
    after[n] = round(100 * am / (2 * fy / 12))
res["apr_may_2026_pct_of_fy26_month_avg"] = after

# ---- 5. Benelux months around the records gap
bx = sub("Benelux").groupby("ym")["eur"].sum()
res["benelux_monthly_2025"] = {k: round(float(bx.get(k, 0.0))) for k in
                               ["2025-03", "2025-04", "2025-05", "2025-06", "2025-07"]}

# ---- 6. Feb+Mar against each distributor's own 10-month run: billing and sales to dealer
pos = sf[pd.to_numeric(sf["billed_qty"], errors="coerce") > 0].copy()
pos["pn"] = pos["part_number"].astype(str).str.strip()
pos["unit"] = pos["eur"] / pd.to_numeric(pos["billed_qty"])
PRICE = pos.groupby("pn")["unit"].median()
FY26 = [f"2025-{m:02d}" for m in range(4, 13)] + ["2026-01", "2026-02", "2026-03"]
files = {"IUK": ["IUK_CY2025", "IUK_CY2026YTD"], "Ireland": ["IRELAND_CY2025", "IRELAND_CY2026YTD"],
         "Portugal": ["PORTUGAL_CY2025", "PORTUGAL_CY2026YTD"], "ITUK": ["ITUK_CY2025", "ITUK_CY2026YTD"]}
std = {}
for n, fs in files.items():
    parts = []
    for f in fs:
        fp = DER / f"dealer_sellout_long_{f}.csv"
        if not fp.exists():
            continue
        d = pd.read_csv(fp, usecols=lambda c: c in {"period", "period_grain", "part_number", "qty"},
                        low_memory=False)
        d = d[d["period_grain"] == "month"].copy()
        d["eur"] = pd.to_numeric(d["qty"], errors="coerce") * d["part_number"].astype(str).str.strip().map(PRICE)
        parts.append(d[["period", "eur"]])
    e = pd.concat(parts).groupby(pd.concat(parts)["period"].astype(str))["eur"].sum().reindex(FY26)
    b = sub(n).groupby("ym")["eur"].sum().reindex(FY26)
    cov = int(e.notna().sum())
    if cov < 12:
        std[n] = {"months_covered": cov, "usable": False}
        continue
    std[n] = {"months_covered": cov, "usable": True,
              "billing_febmar_vs_run_pct": round(100 * (b.iloc[10:].sum() / (2 * b.iloc[:10].mean()) - 1), 1),
              "std_febmar_vs_run_pct": round(100 * (e.iloc[10:].sum() / (2 * e.iloc[:10].mean()) - 1), 1)}
res["febmar_vs_own_run_billing_and_std"] = std
res["std_valuation"] = "dealer volume x median ISZE net billed price per part number"

OUT.write_text(json.dumps(res, indent=1), encoding="utf-8")
print(json.dumps(res, indent=1))

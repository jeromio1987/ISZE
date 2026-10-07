"""IML delay proof - analysis pass. Prints everything the page needs, and writes interim CSVs.

Three legs:
  A. IML warehouse delays - how long each line has waited, by status, family, part, and country detail
  B. UTI recurrence - the same parts on the back-order list week after week (39 weeks)
  C. Fill rate and back-order lines against the FY26-27 targets
Plus: the part-level overlap that lets a waiting distributor be named for a delayed part.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

import openpyxl
import pandas as pd

ROOT = Path(r"C:\Users\jerom\Desktop\claude\ISZE")
DELAY = ROOT / "01_data" / "ISZE_Order Status as of 2 October 2026_request to check.xlsx"
BO = ROOT / "01_data" / "90_INBOX" / "_iml_delay_wk41_20261007" / "bo_overview" / "20261006_BO info VP 06-10-2026.xlsx"
AIM = ROOT / "01_data" / "00_derived" / "aim_master_v2.csv"
KPI = ROOT / "01_data" / "11_planning" / "KPI Master File august 2026.xlsx"
TARGETS = ROOT / "01_data" / "11_planning" / "ISZE_DB_KPI_Targets_FY2627_v1.xlsx"
UTI = ROOT / "02_dashboards" / "pricing" / "_build" / "price_5pct_proposal_2026-09-29" / "uti_panels_2026-10-02" / "t13_uti_bo_body_lines_wk2_wk40.csv"
OUT = ROOT / "01_data" / "90_INBOX" / "_iml_delay_wk41_20261007"

EXCLUDE = ("MIDI", "RUS", "KAZ", "CBC-TRANS", "GRAND AVTO", "KOMTRANS", "KIMA")
ASOF_IML = pd.Timestamp("2026-10-02")


def norm_pn(v) -> str:
    return re.sub(r"[^0-9A-Za-z]", "", str(v if v is not None else ""))


def kpn(v) -> str:
    return norm_pn(v).lstrip("0")


# ---------------- AIM ----------------
aim = pd.read_csv(AIM, dtype=str, low_memory=False)
aim["pn"] = aim["part_number"].fillna("").map(norm_pn)
fam = {}
for p, f in zip(aim["pn"], aim["aim_l1"].fillna("").str.strip()):
    if not p:
        continue
    k = p.lstrip("0")
    if f and (k not in fam or not fam[k]):
        fam[k] = f
infile = set(aim["pn"].map(kpn))


def aim_of(pn):
    k = kpn(pn)
    if k in infile:
        f = fam.get(k, "")
        return (f, "family") if f else ("", "nofam")
    return "", "absent"


# ---------------- A. IML warehouse ----------------
dly = pd.read_excel(DELAY, sheet_name="isze", dtype=str)
dly.columns = [str(c).strip() for c in dly.columns]
dly["pn"] = dly["PN"].map(norm_pn)
dly["part"] = dly["Part Name"].fillna("").str.strip()
dly["status"] = dly["Status"].fillna("").str.strip()
dly["qty"] = pd.to_numeric(dly["Q'ty"], errors="coerce").fillna(0)
dly["mode"] = dly["Mode"].fillna("").str.strip().map({"S": "Sea", "A": "Air"}).fillna("other")
dly["order_no"] = dly["Order No"].fillna("").str.strip()
dly["procced"] = pd.to_datetime(dly["Procced"], format="%y%m%d", errors="coerce")
dly["days_waiting"] = (ASOF_IML - dly["procced"]).dt.days
st = [aim_of(p) for p in dly["pn"]]
dly["aim"] = [s[0] if s[1] == "family" else ("in AIM, no family yet" if s[1] == "nofam" else "not in the AIM file") for s in st]
dly["aim_state"] = [s[1] for s in st]

print("=" * 78)
print("A. IML WAREHOUSE (as of 2026-10-02)")
print("=" * 78)
print("lines:", len(dly), "| pieces:", f"{dly['qty'].sum():,.0f}", "| orders:", dly["order_no"].nunique())
print("\n-- by status --")
print(dly.groupby("status").agg(lines=("qty", "size"), pcs=("qty", "sum"),
      median=("days_waiting", "median"), p90=("days_waiting", lambda s: s.quantile(.9)),
      oldest=("days_waiting", "max"), over30=("days_waiting", lambda s: int((s > 30).sum()))).to_string(float_format=lambda x: f"{x:,.0f}"))

print("\n-- three-way view: order date vs arrival estimate --")
print("procced range:", dly["procced"].min(), "->", dly["procced"].max())
print("lines with NO procced date:", int(dly["procced"].isna().sum()))

print("\n-- the delayed queue (over 30 days) by status --")
old = dly[dly["days_waiting"] > 30]
print(old.groupby("status").agg(lines=("qty", "size"), pcs=("qty", "sum"),
      oldest=("days_waiting", "max")).to_string(float_format=lambda x: f"{x:,.0f}"))
print("total over 30d:", len(old), "lines,", f"{old['qty'].sum():,.0f}", "pcs")

print("\n-- by parts family (all lines / over 30 days) --")
fa = old.groupby("aim").agg(delayed_lines=("qty", "size"), delayed_pcs=("qty", "sum"),
                            oldest=("days_waiting", "max"))
allf = dly.groupby("aim").agg(lines=("qty", "size"), pcs=("qty", "sum"))
fa = fa.join(allf).sort_values("delayed_pcs", ascending=False)
print(fa.to_string(float_format=lambda x: f"{x:,.0f}"))

print("\n-- top 20 delayed parts --")
tp = (old.groupby(["pn", "part", "aim"], as_index=False)
        .agg(lines=("qty", "size"), pcs=("qty", "sum"), oldest=("days_waiting", "max"),
             orders=("order_no", "nunique"),
             statuses=("status", lambda s: "/".join(sorted(set(s)))))
        .sort_values("pcs", ascending=False).head(20))
print(tp.to_string(index=False, float_format=lambda x: f"{x:,.0f}"))

print("\n-- worst 15 individual lines --")
w = dly[dly["days_waiting"] > 30].sort_values("days_waiting", ascending=False)
print(w[["order_no", "pn", "part", "status", "qty", "days_waiting", "mode", "procced"]].head(15).to_string(index=False))

print("\n-- orders with several delayed lines --")
oy = (old.groupby("order_no", as_index=False)
        .agg(lines=("qty", "size"), pcs=("qty", "sum"), oldest=("days_waiting", "max"))
        .sort_values("lines", ascending=False).head(12))
print(oy.to_string(index=False, float_format=lambda x: f"{x:,.0f}"))

# ---------------- B. UTI recurrence ----------------
print("\n" + "=" * 78)
print("B. UTI RECURRENCE (WK2-WK40 2026, 39 weekly lists)")
print("=" * 78)
u = pd.read_csv(UTI)
print("lines in tidy file:", len(u), "| weeks:", u["week"].nunique(),
      "| parts:", u["pn"].nunique(), "| window:", u["snapshot_date"].min(), "->", u["snapshot_date"].max())

wk = (u.groupby("week", as_index=False)
       .agg(snapshot=("snapshot_date", "first"), lines=("pn", "size"), parts=("pn", "nunique"),
            units=("open_qty", "sum"), median_days=("days_open", "median"),
            max_days=("days_open", "max"),
            over60=("days_open", lambda s: int((s > 60).sum())),
            urgent=("order_type", lambda s: int(s.isin(["VOR", "RUSH"]).sum()))))
print("\n-- weekly --")
print(wk.to_string(index=False, float_format=lambda x: f"{x:,.0f}"))

rec = (u.groupby(["pn", "description", "seg"], as_index=False)
        .agg(weeks_on=("week", "nunique"), first_wk=("week", "min"), last_wk=("week", "max"),
             orders=("sales_doc", "nunique"), max_days=("days_open", "max"),
             max_units=("open_qty", "max"))
        .sort_values("weeks_on", ascending=False))
print("\n-- parts recurring the most weeks (of 39) --")
print(rec.head(20).to_string(index=False, float_format=lambda x: f"{x:,.0f}"))
print("\nrecurrence counts: parts on the list 20+ weeks:", int((rec["weeks_on"] >= 20).sum()),
      "| 10+ weeks:", int((rec["weeks_on"] >= 10).sum()), "| 4+ weeks:", int((rec["weeks_on"] >= 4).sum()))
# how many are STILL on the last list
last_wk_no = int(u["week"].max())
last_pns = set(u[u["week"] == last_wk_no]["pn"])
long_tail = rec[(rec["weeks_on"] >= 20) & (rec["pn"].isin(last_pns))]
print(f"parts on 20+ weeks that are STILL open in WK{last_wk_no}:", len(long_tail))
print(f"median days open on the last list: {u[u['week']==last_wk_no]['days_open'].median():.0f}")

print("\n-- age trend, first list vs last list --")
for wnum in [2, 20, last_wk_no]:
    sub = u[u["week"] == wnum]
    if len(sub):
        print(f"  WK{wnum} ({sub['snapshot_date'].iloc[0]}): lines {len(sub)}, median days {sub['days_open'].median():.0f}, over 60d {int((sub['days_open']>60).sum())}")

# ---------------- C. Fill rate / back orders ----------------
print("\n" + "=" * 78)
print("C. FILL RATE + BACK ORDER LINES vs TARGETS")
print("=" * 78)


def block(ws, start_row, label):
    """Read a KPI block: header at start_row+2, distributors from start_row+3 to the next blank."""
    rows = list(ws.iter_rows(min_row=start_row, max_row=start_row + 40, values_only=True))
    # find header row: first row containing 'Distributor'
    hdr_idx = None
    for i, r in enumerate(rows):
        if r and str(r[0]).strip().lower() == "distributor":
            hdr_idx = i
            break
    if hdr_idx is None:
        print(f"  {label}: no header found")
        return None
    hdr = [str(c).strip() if c is not None else "" for c in rows[hdr_idx]]
    out = []
    for r in rows[hdr_idx + 1:]:
        if r is None or r[0] is None or not str(r[0]).strip():
            break
        dist = str(r[0]).strip()
        rec = {"distributor": dist}
        for ci in range(1, min(len(hdr), len(r))):
            month = hdr[ci]
            val = r[ci]
            if month and val is not None:
                rec[month] = val
        out.append(rec)
    print(f"  {label}: {len(out)} distributors, months {hdr[1:6]} ... {hdr[-3:]}")
    return out


wbf = openpyxl.load_workbook(KPI, read_only=True, data_only=True)
ws = wbf["Parts Handling"]
stock = block(ws, 1, "Days of Parts in Stock")
fill = block(ws, 28, "First Fill Rate")
bo = block(ws, 55, "Back Order Lines")

def latest(recs):
    """last reported value per distributor, with its month"""
    rows = []
    for rec in recs:
        months = [(k, v) for k, v in rec.items() if k != "distributor"]
        vals = [(k, v) for k, v in months if isinstance(v, (int, float))]
        if not vals:
            rows.append({"distributor": rec["distributor"], "value": None, "month": "N/D"})
            continue
        k, v = vals[-1]
        rows.append({"distributor": rec["distributor"], "value": float(v), "month": k})
    return rows

for label, recs, unit in [("days of stock", stock, "days"), ("first fill %", fill, "%"), ("back order lines", bo, "lines")]:
    print(f"\n-- {label}: latest reported --")
    for r in latest(recs):
        print(f"   {r['distributor']:22s} {r['month']:8s} {r['value']}")

# targets
print("\n-- targets file --")
try:
    twb = openpyxl.load_workbook(TARGETS, read_only=True, data_only=True)
    print("sheets:", twb.sheetnames)
    for s in twb.sheetnames:
        w = twb[s]
        rows = list(w.iter_rows(min_row=1, max_row=40, values_only=True))
        print(f"=== {s} ===")
        for i, r in enumerate(rows[:22]):
            vals = [str(c)[:26] for c in r if c is not None]
            if vals:
                print(" ", i + 1, vals[:10])
except Exception as exc:
    print("targets read failed:", exc)

dly.to_csv(OUT / "iml_delays_enriched.csv", index=False)
wk.to_csv(OUT / "uti_weekly_summary_recomputed.csv", index=False)
rec.to_csv(OUT / "uti_recurrence_recomputed.csv", index=False)
print("\nwrote csvs to", OUT)

"""Verify the recalculated pricing-grid workbook against an independent Python replica.

Independent: the replica below re-derives everything from the CSVs, the live workbook's cached Proposal values and
evidence_lib.load_base(); it shares no code with the builder. It reads the switch positions out of the recalculated
workbook, rebuilds the holds and the solved base for those positions, and compares every part x market increase
(both Isuzu UK switch positions), the reason code on every line, the solver, the reconciliation block, the
per-market table, the twelve grid cells, the margin and volume sheet, the stance sheets, the test design and the
label fixes. It also checks that the original sheets are unchanged apart from the three agreed label fixes.

Run:  python verify_pricing_grid_20261011.py [path to the recalculated workbook]
"""
import json
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from openpyxl import load_workbook

HERE = Path(__file__).resolve().parent
ISZE = Path(r"C:\Users\jerom\Desktop\claude\ISZE")
sys.path.insert(0, str(HERE))
from evidence_lib import load_base  # noqa: E402

STAGE = HERE / "stage_grid_2026-10-11"
XLSX = Path(sys.argv[1]) if len(sys.argv) > 1 else STAGE / "Price_Increase_5pct_Proposal_GRID_DRAFT_2026-10-11.xlsx"
LIVE = ISZE / "01_data" / "01_Pricing" / "Price_Increase_5pct_Proposal_2026-09-29.xlsx"
RR = HERE / "room_to_raise_2026-10-02"
DERIVED = ISZE / "01_data" / "00_derived"
ADDR = json.loads((STAGE / "grid_addresses_2026-10-11.json").read_text(encoding="utf-8"))
PUB = json.loads((RR / "room_to_raise_variant_B_iuk_exempt_2026-10-02.json").read_text(encoding="utf-8"))
AIM_RELEASE = DERIVED / "_releases" / "aim_pn_classification_release_2026-10-07.csv"
ROLE_CSV = ISZE / "01_data" / "01_Pricing" / "aim_category_target_gm_20261007.csv"
R_SERVICE = "Service parts held at today's price"
ROLES = ["wear_pms", "captive", "commercial", "body_legal"]
ROLE_CODE = {"wear_pms": "WEAR_PMS", "captive": "CAPTIVE", "commercial": "COMMERCIAL", "body_legal": "BODY_LEGAL"}
SHEETS = ["Read me", "Summary", "Market layer", "Stance PR00", "Stance ZPR1", "Stance CIS", "Pricing grid", "Proposal",
          "Review lists", "Dealer response", "Not in proposal", "Checks", "Layer by part and market", "Layer by part",
          "Layer solver", "Margin and volume", "Test design", "Repair rules"]
fails = []
lines = []


def say(s):
    print(s)
    lines.append(s)


def check(label, ok, detail=""):
    say(f"{'OK  ' if ok else 'FAIL'} {label}" + (f": {detail}" if detail else ""))
    if not ok:
        fails.append(label)


# ============================================================ read the switch positions first
wbv = load_workbook(XLSX, data_only=True, read_only=True)
say(f"Workbook: {XLSX} ({XLSX.stat().st_size / 1e6:.1f} MB)")
SM = ADDR["summary"]
sm = wbv["Summary"]
SWv = {k: sm.cell(SM[k], 2).value for k in ("s1", "s2", "disc", "b1", "b2", "b3", "elig", "scen")}
EXEMPT_SW = sm["D5"].value
say(f"Switches now: filters held={SWv['s1']}, intake/exhaust held={SWv['s2']}, discs held={SWv['disc']}, "
    f"Israel-trucks body={SWv['b1']}, Isuzu-UK body={SWv['b2']}, other-markets body={SWv['b3']}, "
    f"extra only on no-alternative parts={SWv['elig']}, scenario={SWv['scen']}, Isuzu UK exemption D5={EXEMPT_SW}")
S1, S2 = int(SWv["s1"]), int(SWv["s2"])
PAPER = (S1 == 1 and S2 == 1 and SWv["scen"] == "A" and int(SWv["b1"]) == 1 and int(SWv["b2"]) == 1
         and float(SWv["b3"]) == 1 and int(SWv["elig"]) == 1)
say(f"Position: {'PAPER (every switch at its 2 October position)' if PAPER else 'DELIVERED DEFAULT (filters follow the factory increase)'}")

# ============================================================ independent replica
live = pd.read_excel(LIVE, sheet_name="Proposal", dtype={"Part number": str})
live = live.rename(columns={"Part number": "pn", "Billed EUR (Jul 25-Jun 26)": "billed", "Factory move": "c",
                            "Proposed move": "base", "Class margin": "m0"})
ins = load_base()
L = ins[ins.movable].copy()
dd = pd.read_csv(DERIVED / "distributor_dimension.csv", dtype=str)
L["db"] = L.customer_code.astype(str).map(dict(zip(dd.sold_to_sap, dd.distributor_code)))
pm = L.groupby(["pn", "db"], as_index=False).net_sales_value.sum().rename(columns={"net_sales_value": "billed"})
csv_pm = pd.read_csv(RR / "room_to_raise_by_part_market_2026-10-02.csv", dtype={"pn": str}, usecols=["pn", "db", "hold_reason"])
pm = pm.merge(csv_pm, on=["pn", "db"], how="left", validate="1:1")
bp = pd.read_csv(RR / "room_to_raise_by_part_2026-10-02.csv", dtype={"pn": str}, low_memory=False,
                 usecols=["pn", "segment", "captive_strict", "lubricant", "padkit"]).set_index("pn")
P = live[["pn", "c", "base", "m0"]].set_index("pn").join(bp)

zpad = lambda s: s.astype(str).str.replace(r"\.0$", "", regex=True).str.zfill(10)
aim = pd.read_csv(AIM_RELEASE, dtype=str, usecols=["part_number", "aim_l1_fixed", "aim_l2_fixed", "aim_l3_fixed"])
aim["pn"] = zpad(aim.part_number)
aim = aim.drop_duplicates("pn").set_index("pn")
l1 = P.index.map(aim.aim_l1_fixed).fillna("")
l2 = pd.Series(P.index.map(aim.aim_l2_fixed), index=P.index).fillna("").str.lower()
l3 = pd.Series(P.index.map(aim.aim_l3_fixed), index=P.index).fillna("").str.lower()
DISC_PAT = r"discs? ?& ?drums?|brake disc|brake drum|brake rotor"
P["hk"] = np.select([l2.str.contains(DISC_PAT, regex=True) | l3.str.contains(DISC_PAT, regex=True),
                     l2.str.contains("filter") | l3.str.contains("filter"),
                     pd.Series(l1, index=P.index).eq("Intake Exhaust Emission")], [3, 1, 2], default=0)
rl = pd.read_csv(ROLE_CSV, usecols=["aim_level_1", "pricing_role"])
role_of = dict(zip(rl.aim_level_1, rl.pricing_role))
P["role"] = pd.Series(l1, index=P.index).map(role_of).fillna("unclassified")
P["ridx"] = P.role.map(lambda r: ROLES.index(r) + 1 if r in ROLES else ROLES.index("commercial") + 1)

pm["reason_src"] = pm.hold_reason.fillna("").map(
    {"service hold (market exercise)": R_SERVICE,
     "UMI body/collision hold": "Body and collision parts held at today's price (Israel D-Max distributor)",
     "UMI lighting hold": "Lighting held at today's price (Israel D-Max distributor)",
     "UTI lighting hold": "Lighting held at today's price (Israel trucks distributor)"}).fillna("")
pm["hk"] = pm.pn.map(P.hk)
released = pm.reason_src.eq(R_SERVICE) & ((pm.hk.eq(1) & (S1 == 0)) | (pm.hk.eq(2) & (S2 == 0)))
pm["hold"] = pm.reason_src.ne("") & ~released
pm["cis"] = pm.db.isin(["ARMENIA", "KAZAKHSTAN"])
pm["base"] = pm.pn.map(P.base)
TOT = pm.billed.sum()
TGT = 0.05 * TOT
elig = (P.segment.isin(["repair", "body"]) & (P.captive_strict == 1)).astype(float)
padH, lub = P.padkit == 1, P.lubricant == 1
cap = (P.c.clip(lower=0) + 0.05).where(~padH & ~lub, 0.0)
v = elig.where(~padH & ~lub, 0.0)
base = P.base
HELD8 = ["BELGIUM", "CYPRUS", "GERMANY", "HUNGARY", "IUK", "MALTA", "NORWAY", "UMI"]
stance_code = {m: ("KEEP" if m in HELD8 else "FOLLOW") for m in pm.db.unique()}


def replica(exempt):
    free = ~pm.hold & ~pm.cis
    fixed = free & pm.db.isin(exempt)
    flex = free & ~pm.db.isin(exempt)
    Wflex = pm[flex].groupby("pn").billed.sum().reindex(P.index).fillna(0)
    Wfix = pm[fixed].groupby("pn").billed.sum().reindex(P.index).fillna(0)
    cis_step = float((pm.billed * pm.base)[pm.cis].sum())
    mv_fix = np.minimum(cap, base)
    need = TGT - cis_step - float((Wfix * mv_fix).sum())
    f = lambda t: float((Wflex * np.minimum(cap, base + t * v)).sum())
    lo, hi = -1.0, 50.0
    for _ in range(200):
        mid = (lo + hi) / 2
        lo, hi = (mid, hi) if f(mid) < need else (lo, mid)
    t = hi
    mv = np.minimum(cap, base + t * v)
    line_mv = np.where(flex, pm.pn.map(mv), np.where(fixed, pm.pn.map(mv_fix), np.where(pm.cis, pm.base, 0.0)))
    line_base = np.where(free, pm.base, 0.0)
    extra = (pm.billed * (line_mv - line_base)).clip(lower=0).where(free, 0.0)
    cut = (pm.billed * (line_base - line_mv)).clip(lower=0).where(free, 0.0)
    seg = pm.pn.map(P.segment)
    iuk = pm.db.eq("IUK") & seg.isin(["repair", "body"])
    out = dict(t=t, total=float((pm.billed * line_mv).sum()), extra=float(extra.sum()), cut=float(cut.sum()),
               iuk=float(extra[iuk].sum()), repair=float(extra[seg == "repair"].sum()), body=float(extra[seg == "body"].sum()),
               service=float(extra[seg == "service"].sum()), nparts=int(((v > 0) & (Wflex > 0)).sum()),
               given=float((pm.billed * pm.base)[pm.hold].sum()), own=float((pm.billed * pm.base).sum()))
    by = pd.DataFrame({"db": pm.db, "b": pm.billed, "s": pm.billed * line_mv, "x": extra, "p": pm.billed * pm.base,
                       "g": (pm.billed * pm.base).where(pm.hold, 0.0)}).groupby("db")
    tab = pd.DataFrame({"billed": by.b.sum(), "own": by.p.sum() / by.b.sum(), "avg": by.s.sum() / by.b.sum(), "extra": by.x.sum(),
                        "given": by.g.sum(), "step": by.s.sum()})
    return out, tab, line_mv, mv


off, tab_off, mv_off_line, mv_off_part = replica([])
on, tab_on, mv_on_line, mv_on_part = replica(["IUK"])
say(f"Replica OFF: t={off['t']:.6f} total={off['total']:,.2f} extra={off['extra']:,.2f} given={off['given']:,.2f} cut={off['cut']:,.2f} IUK={off['iuk']:,.2f}")
say(f"Replica ON : t={on['t']:.6f} total={on['total']:,.2f} extra={on['extra']:,.2f} IUK={on['iuk']:,.2f}")
pb, pe = PUB["B_as_published"], PUB["B_iuk_exempt"]
if PAPER:
    check("replica reproduces published OFF (t, extra, IUK, repair, body)",
          abs(off["t"] - pb["solver_t_pts"]) < 1e-6 and abs(off["extra"] - pb["uplift_above_proposal_eur"]) <= 1
          and abs(off["iuk"] - pb["uplift_on_iuk_repair_body_eur"]) <= 1 and abs(off["repair"] - pb["uplift_repair_eur"]) <= 1
          and abs(off["body"] - pb["uplift_body_eur"]) <= 1)
    check("replica reproduces published ON (t, extra, IUK, repair, body)",
          abs(on["t"] - pe["solver_t_pts"]) < 1e-6 and abs(on["extra"] - pe["uplift_above_proposal_eur"]) <= 1
          and abs(on["iuk"] - pe["uplift_on_iuk_repair_body_eur"]) <= 1 and abs(on["repair"] - pe["uplift_repair_eur"]) <= 1
          and abs(on["body"] - pe["uplift_body_eur"]) <= 1)
pub_csv = pd.read_csv(RR / "room_to_raise_variant_B_iuk_exempt_2026-10-02.csv").set_index("market")

# ============================================================ read the recalculated workbook
check("sheet order and names", wbv.sheetnames == SHEETS, str(wbv.sheetnames))
ml = wbv["Market layer"]
cells = {(r[0].row, c.column): c.value for r in ml.iter_rows(min_row=1, max_row=ml.max_row, max_col=16) for c in r if c.value is not None}
g = lambda row, col: cells.get((row, col))
rec = ADDR["market_layer"]["rec"]
COL = {"B": 2, "C": 3, "D": 4, "E": 5, "F": 6, "G": 7}
rv = lambda key, col: g(rec[key], COL[col])

for col, rp, nm in (("B", off, "OFF"), ("C", on, "ON")):
    check(f"[{nm}] total after treatment = target", abs(rv("total", col) - TGT) < 0.5, f"excel={rv('total', col):,.4f} target={TGT:,.4f}")
    check(f"[{nm}] weighted increase = 5.000%", abs(rv("pct", col) - 0.05) < 1e-9, f"{rv('pct', col):.9f}")
    check(f"[{nm}] extra vs replica", abs(rv("extra", col) - rp["extra"]) < 0.05, f"excel={rv('extra', col):,.2f} replica={rp['extra']:,.2f}")
    check(f"[{nm}] given up vs replica", abs(rv("given", col) - rp["given"]) < 0.05, f"excel={rv('given', col):,.2f} replica={rp['given']:,.2f}")
    check(f"[{nm}] cut vs replica", abs(rv("cut", col) - rp["cut"]) < 0.05, f"excel={rv('cut', col):,.2f} replica={rp['cut']:,.2f}")
    check(f"[{nm}] solver base vs replica", abs(rv("t", col) - rp["t"]) < 1e-9, f"excel={rv('t', col):.9f} replica={rp['t']:.9f}")
    check(f"[{nm}] IUK repair+body extra vs replica", abs(rv("iuk", col) - rp["iuk"]) < 0.05, f"excel={rv('iuk', col):,.2f}")
    check(f"[{nm}] repair extra vs replica", abs(rv("rep", col) - rp["repair"]) < 0.05, f"excel={rv('rep', col):,.2f}")
    check(f"[{nm}] body extra vs replica", abs(rv("body", col) - rp["body"]) < 0.05, f"excel={rv('body', col):,.2f}")
    check(f"[{nm}] service extra = 0 while the extra is limited to no-alternative parts", abs(rv("svc", col)) < 0.005)
    check(f"[{nm}] identity own-given-cut+extra=total", abs(g(rec['ident'], COL[col])) < 0.01, f"{g(rec['ident'], COL[col]):.6f}")

say("")
say(f"REPRODUCTION FIGURES at this position: given up EUR {rv('given', 'B'):,.2f}; ceiling cut EUR {rv('cut', 'B'):,.2f}; "
    f"recovered EUR {rv('extra', 'B'):,.2f}; total EUR {rv('total', 'B'):,.2f}; "
    f"base points OFF {rv('t', 'B'):.4%} / ON {rv('t', 'C'):.4%}")
say("")
if PAPER:
    check("[OFF] published: IUK extra = EUR 91,065, extra EUR 396,568 (rounded)",
          round(rv("iuk", "B")) == 91065 and round(rv("extra", "B")) == 396568, f"{rv('iuk', 'B'):,.2f} / {rv('extra', 'B'):,.2f}")
    check("[ON] published: IUK extra = 0, extra EUR 396,568 (rounded)", round(rv("iuk", "C")) == 0 and round(rv("extra", "C")) == 396568,
          f"{rv('iuk', 'C'):,.2f} / {rv('extra', 'C'):,.2f}")
    check("[OFF] given up rounds to EUR 388,914", round(rv("given", "B")) == 388914, f"{rv('given', 'B'):,.2f}")
    check("[OFF] ceiling cut rounds to EUR 7,654", round(rv("cut", "B")) == 7654, f"{rv('cut', 'B'):,.2f}")
    check("[OFF] total rounds to EUR 1,629,793", round(rv("total", "B")) == 1629793, f"{rv('total', 'B'):,.2f}")
    check("[ON] total rounds to EUR 1,629,793", round(rv("total", "C")) == 1629793, f"{rv('total', 'C'):,.2f}")
    check("[OFF] base points round to 3.727 / [ON] 4.837",
          round(rv("t", "B") * 100, 3) == 3.727 and round(rv("t", "C") * 100, 3) == 4.837,
          f"{rv('t', 'B') * 100:.4f} / {rv('t', 'C') * 100:.4f}")
    mism = [k for k in ("given", "cut", "extra", "total", "pct", "t", "rep", "body", "svc", "iuk", "nparts") if g(rec[k], 7) != "OK"]
    check("column G 'Matches published' reads OK on every published row", not mism, f"not OK: {mism}")
else:
    nas = [k for k in ("given", "cut", "extra", "total") if g(rec[k], 7) != "n/a: settings changed"]
    check("column G says the settings were changed (not comparing to the published figures)", not nas, str(nas))
check("[now] column equals switch OFF (delivered state)", all(abs(rv(k, "D") - rv(k, "B")) < 1e-9 for k in ("total", "extra", "given", "cut", "iuk")))

# ---- what each hold is worth
hv = ADDR["market_layer"]["hv_rows"]
say("What each hold is worth (EUR given up if held / given up now):")
for lab, r_ in hv.items():
    say(f"   {lab}: if held {g(r_, 6):,.0f} | now {g(r_, 7):,.0f} | lines {g(r_, 4):,.0f} | billed {g(r_, 5):,.0f}")
GB = ADDR["given_by_hold_paper"]
check("filters hold worth EUR 26,030 (the figure checked on disk before the build)", round(g(hv["Filters (oil, air, fuel, blower, strainers)"], 6)) == 26030,
      f"{g(hv['Filters (oil, air, fuel, blower, strainers)'], 6):,.2f}")
check("intake, exhaust and emission hold worth EUR 92,749", round(g(hv["Intake, exhaust and emission parts"], 6)) == 92749,
      f"{g(hv['Intake, exhaust and emission parts'], 6):,.2f}")
check("brake discs and drums hold worth EUR 52,339", round(g(hv["Brake discs and drums"], 6)) == 52339,
      f"{g(hv['Brake discs and drums'], 6):,.2f}")
check("the five holds add up to the hold euro of the paper (EUR 388,914)",
      abs(sum(g(r_, 6) for r_ in hv.values()) - 388914) < 1, f"{sum(g(r_, 6) for r_ in hv.values()):,.2f}")
check("filters are released when the switch says follow", (S1 == 1) or abs(g(hv["Filters (oil, air, fuel, blower, strainers)"], 7)) < 0.005)

# ---- per-market table
mt_first, mt_last = ADDR["market_layer"]["mt_first"], ADDR["market_layer"]["mt_last"]
mk_rows = {g(r, 2): r for r in range(mt_first, mt_last + 1)}
check("22 markets in the per-market table", len(mk_rows) == 22, str(len(mk_rows)))
worst = {"avgOFF": 0, "upOFF": 0, "avgON": 0, "upON": 0, "own": 0, "given": 0, "avg_now": 0}
for m, r in mk_rows.items():
    worst["avgOFF"] = max(worst["avgOFF"], abs(g(r, 12) - pub_csv.loc[m, "B_avg_move"]))
    worst["upOFF"] = max(worst["upOFF"], abs(g(r, 13) - pub_csv.loc[m, "B_uplift_eur"]))
    worst["avgON"] = max(worst["avgON"], abs(g(r, 14) - pub_csv.loc[m, "B_iuk_exempt_avg_move"]))
    worst["upON"] = max(worst["upON"], abs(g(r, 15) - pub_csv.loc[m, "B_iuk_exempt_uplift_eur"]))
    worst["own"] = max(worst["own"], abs(g(r, 4) - tab_off.loc[m, "own"]))
    worst["given"] = max(worst["given"], abs(g(r, 5) - tab_off.loc[m, "given"]))
    worst["avg_now"] = max(worst["avg_now"], abs(g(r, 10) - tab_off.loc[m, "avg"]))
say("per-market worst gaps vs published csv / replica: " + json.dumps({k: float(f"{v:.3g}") for k, v in worst.items()}))
if PAPER:
    check("per-market increase, switch OFF vs published csv (<= 0.00001)", worst["avgOFF"] <= 1e-5)
    check("per-market recovered EUR, switch OFF vs published csv (<= EUR 0.05)", worst["upOFF"] <= 0.05)
    check("per-market increase, switch ON vs published csv (<= 0.00001)", worst["avgON"] <= 1e-5)
    check("per-market recovered EUR, switch ON vs published csv (<= EUR 0.05)", worst["upON"] <= 0.05)
check("per-market own increase and given up vs replica", worst["own"] < 1e-9 and worst["given"] < 0.01)
check("per-market increase now vs replica", worst["avg_now"] < 1e-9)
for m in ("ARMENIA", "KAZAKHSTAN"):
    r = mk_rows[m]
    check(f"{m}: no hold, no extra, increase = own increase (both positions)",
          g(r, 5) in (0, None) and abs(g(r, 9) or 0) < 1e-9 and abs(g(r, 12) - g(r, 4)) < 1e-9 and abs(g(r, 14) - g(r, 4)) < 1e-9
          and abs(g(r, 13) or 0) < 1e-9 and abs(g(r, 15) or 0) < 1e-9)
check("every market shows its stance on the per-market table",
      all(isinstance(g(r, 16), str) and g(r, 16) for r in mk_rows.values()))
ak_t, ak_n = ADDR["market_layer"]["ak_total_row"], ADDR["market_layer"]["ak_nocis_row"]
say(f"Armenia + Kazakhstan: billed EUR {g(ak_t, 2):,.0f}, increase {g(ak_t, 3):.4%}, EUR {g(ak_t, 4):,.0f}; "
    f"total if it does not reach them EUR {g(ak_n, 2):,.0f} = {g(ak_n, 3):.4%}")

# ---- checks on the layer sheet, Checks sheet, Summary
ck_first, ck_last = ADDR["market_layer"]["ck_first"], ADDR["market_layer"]["ck_last"]
check("market layer check count matches the Checks sheet", ck_last - ck_first + 1 == ADDR["market_layer"]["n_checks"])
for r in range(ck_first, ck_last + 2):
    res = g(r, 4)
    check(f"layer check: {str(g(r, 1))[:90]}", res == "OK", f"value={g(r, 2)} expected={g(r, 3)}")
check("Summary D9 reads OK", sm["D9"].value == "OK", str(sm["D9"].value))
say(f"Summary D6 total EUR {sm['D6'].value:,.2f}; D7 {sm['D7'].value:.5%}; D8 extra EUR {sm['D8'].value:,.2f}")
say("Summary read-out block (rows %d-%d):" % (SM["readout_first"], SM["readout_last"]))
for r in range(SM["readout_first"], SM["readout_last"] + 1):
    say(f"   {sm.cell(r, 1).value} = {sm.cell(r, 2).value}")
check("Summary read-out says every line has one reason code", sm.cell(SM["readout_last"], 2).value == "OK",
      str(sm.cell(SM["readout_last"], 2).value))
ck = wbv["Checks"]
for r in range(4, 14):
    check(f"Checks row {r}: {str(ck[f'A{r}'].value)[:70]}", ck[f"D{r}"].value == "OK", str(ck[f"D{r}"].value))

# ============================================================ every part x market row and every part
pmx = pd.read_excel(XLSX, sheet_name="Layer by part and market", header=3, dtype={"Part number": str})
pmx.columns = ADDR["pm"]["names"]
check("part x market rows = 45,581", len(pmx) == 45581, str(len(pmx)))
check("part x market billed total = EUR 32,595,852.63", abs(pmx.billed.sum() - 32595852.63) < 0.005, f"{pmx.billed.sum():,.2f}")
mrg = pmx.merge(pm.assign(ro=mv_off_line, rn=mv_on_line)[["pn", "db", "ro", "rn", "base", "billed"]].rename(columns={"db": "mkt", "billed": "billed_r"}),
                on=["pn", "mkt"], how="left", validate="1:1")
check("every part x market row matched to the replica", mrg.ro.notna().all())
check("per-row billed equals replica billed", (mrg.billed - mrg.billed_r).abs().max() < 0.0051, f"{(mrg.billed - mrg.billed_r).abs().max():.4g}")
check("per-row own increase equals Proposal column P (live)", (mrg.own - mrg.base).abs().max() < 1e-12, f"{(mrg.own - mrg.base).abs().max():.3g}")
d_off, d_on = (mrg.inc_off - mrg.ro).abs().max(), (mrg.inc_on - mrg.rn).abs().max()
check("per-row increase, switch OFF, all 45,581 rows vs replica (max gap)", d_off < 1e-9, f"{d_off:.3g}")
check("per-row increase, switch ON, all 45,581 rows vs replica (max gap)", d_on < 1e-9, f"{d_on:.3g}")
check("per-row 'increase now' equals the OFF column (delivered state)", (mrg.inc - mrg.inc_off).abs().max() < 1e-12)
check("no error values on the part x market sheet", not pmx.apply(lambda s: s.astype(str).str.startswith("#")).any().any())
cond_counts = pmx.cond.value_counts()
say("conditions now (rows): " + "; ".join(f"{k}: {v:,}" for k, v in cond_counts.items()))
say("line types now: " + "; ".join(f"{k}: {v:,}" for k, v in pmx.state.value_counts().items()))
check("every hold row pays 0%", (pmx.inc[pmx.state == "hold"] == 0).all())
check("hold rows match the replica", int((pmx.state == "hold").sum()) == int(pm.hold.sum()),
      f"excel {int((pmx.state == 'hold').sum())} replica {int(pm.hold.sum())}")
cis_plain = pmx[(pmx.state == "own only") & ~pmx.rcode.isin(["HOLD_PAD", "LUBRICANT_NONE"])]
check("every Armenia/Kazakhstan row is own increase only (apart from pad kits and lubricants, which are held everywhere)",
      (cis_plain.cond == "Own increase only: no hold, no extra (option A)").all(),
      str(sorted(set(cis_plain.cond))[:3]))
check("recovery-extra rows exist and only on repair/body while the extra is limited to no-alternative parts",
      int((pmx.cond == "Own increase + recovery extra").sum()) > 0
      and set(pmx.cat[pmx.cond == "Own increase + recovery extra"]) <= {"repair", "body"})
check("condition text present on every row", pmx.cond.notna().all() and (pmx.cond.astype(str).str.len() > 0).all())

# ---- reason codes (package E), replicated line by line
line_mv_now = mv_off_line if EXEMPT_SW == 0 else mv_on_line
own_line = pm.base.to_numpy()
rep_code = np.where(pm.pn.map(lub).to_numpy(), "LUBRICANT_NONE",
           np.where(pm.pn.map(padH).to_numpy(), "HOLD_PAD",
           np.where(pm.hold.to_numpy(),
                    np.where(pm.hk.to_numpy() == 3, "HOLD_DISC",
                             np.where(pm.reason_src.eq(R_SERVICE).to_numpy(), "HOLD_SERVICE", "HOLD_ISRAEL_BODY_LIGHTING")),
           np.where(pm.cis.to_numpy(), "OWN_ONLY_AM_KZ",
           np.where(line_mv_now > own_line + 1e-12,
                    np.array(["EXTRA_" + stance_code[d] + "_" + ROLE_CODE[ROLES[int(i) - 1]]
                              for d, i in zip(pm.db, pm.pn.map(P.ridx))]),
           np.where(line_mv_now < own_line - 1e-12, "CEILING_CUT", "OWN"))))))
rep = pd.DataFrame({"pn": pm.pn, "mkt": pm.db, "rc": rep_code})
mrc = pmx[["pn", "mkt", "rcode"]].merge(rep, on=["pn", "mkt"], how="left", validate="1:1")
bad = mrc[mrc.rcode != mrc.rc]
check("every line's reason code matches the replica", len(bad) == 0, f"{len(bad)} rows differ, first: {bad.head(3).to_dict('records')}")
check("every line has a reason code", pmx.rcode.notna().all() and (pmx.rcode.astype(str).str.len() > 0).all())
codes_seen = set(pmx.rcode.unique())
say("reason codes in use: " + "; ".join(f"{k}: {v:,}" for k, v in pmx.rcode.value_counts().items()))
ALLOWED = set(ADDR["grid"]["codes"])
check("no reason code outside the agreed list", codes_seen <= ALLOWED, str(sorted(codes_seen - ALLOWED)))
check("no warranty reason code anywhere", not any("WARRANT" in c.upper() for c in codes_seen))
need_now = {"HOLD_PAD", "HOLD_SERVICE", "HOLD_ISRAEL_BODY_LIGHTING", "HOLD_DISC", "OWN", "CEILING_CUT",
            "OWN_ONLY_AM_KZ", "LUBRICANT_NONE"}
check("every non-grid reason code appears on at least one line", need_now <= codes_seen, str(sorted(need_now - codes_seen)))
check("at least one EXTRA_ code appears", any(c.startswith("EXTRA_") for c in codes_seen))

# ---- one list price per part
lpx = pd.read_excel(XLSX, sheet_name="Layer by part", header=3, dtype={"Part number": str})
lpx.columns = ADDR["lp"]["names"]
check("part rows = 15,273 and pointers all 0", len(lpx) == 15273 and int(lpx.ptr.sum()) == 0)
mp = lpx.set_index("pn")
if PAPER:
    check("part list increase OFF vs replica (max gap)", (mp.inc_off - mv_off_part.reindex(mp.index)).abs().max() < 1e-9)
    check("part list increase ON vs replica (max gap)", (mp.inc_on - mv_on_part.reindex(mp.index)).abs().max() < 1e-9)
chk_list = lpx[lpx.list_now.notna() & (lpx.list_now != "")]
exp_new = (pd.to_numeric(chk_list.list_now) * (1 + chk_list.inc_now)).round(2)
check("new list EUR = current list x (1 + list increase now), rounded to cents", (pd.to_numeric(chk_list.list_new) - exp_new).abs().max() < 0.0051)
say(f"pad kits held: {int(lpx.padheld.sum())}; lubricants: {int(lpx.lub.sum())}; parts that can carry the extra: {int(lpx.elig.sum())}")
check("29 pad kits held at 0% list increase", int(lpx.padheld.sum()) == 29 and (lpx.inc_off[lpx.padheld == 1] == 0).all())
check("role number on every part row is 1 to 4", set(lpx.ridx.unique()) <= {1, 2, 3, 4})
check("hold group on every part row is 0 to 3", set(lpx.hk.unique()) <= {0, 1, 2, 3})
check("part roles agree with the role file", (lpx.set_index("pn").ridx - P.ridx.reindex(mp.index)).abs().max() == 0)

# ---- solver
sv = wbv["Layer solver"]
svc = {(r[0].row, c.column): c.value for r in sv.iter_rows(min_row=1, max_row=20, max_col=9) for c in r if c.value is not None}
check("solver differences are 0.00 and the ceiling reaches the target",
      abs(svc[(15, 2)]) < 0.01 and abs(svc[(15, 3)]) < 0.01 and svc[(16, 2)] == "yes" and svc[(16, 3)] == "yes",
      f"gaps {svc[(15, 2)]:.6f} / {svc[(15, 3)]:.6f}")
say(f"solver base OFF {svc[(12, 2)]:.8f}  ON {svc[(12, 3)]:.8f}")

# ---- the pricing grid (package D)
gr = wbv["Pricing grid"]
G = ADDR["grid"]
gcell = {(r[0].row, c.column): c.value for r in gr.iter_rows(min_row=1, max_row=gr.max_row, max_col=10) for c in r if c.value is not None}
mult_now = [[gcell.get((G["mult_now"][0] + i, 2 + j)) for j in range(4)] for i in range(3)]
say("multipliers in use: " + json.dumps(mult_now))
if PAPER:
    check("scenario A multipliers in use are all 1", all(abs(x - 1) < 1e-12 for row in mult_now for x in row))
st0, st1 = G["stance_first"], G["stance_last"]
stances = {gcell.get((r, 2)): (gcell.get((r, 6)), gcell.get((r, 7)), gcell.get((r, 8))) for r in range(st0, st1 + 1)}
check("22 markets on the stance table with a stance, a number and a code", len(stances) == 22
      and all(s and isinstance(n, (int, float)) and c in ("KEEP", "FOLLOW", "RAISE") for s, n, c in stances.values()),
      json.dumps({k: v[0] for k, v in list(stances.items())[:4]}))
check("scenario A stances: the 8 service-hold markets keep, everyone else follows",
      all(v[2] == ("KEEP" if k in HELD8 else "FOLLOW") for k, v in stances.items()),
      str([k for k, v in stances.items() if v[2] != ("KEEP" if k in HELD8 else "FOLLOW")]))
cell_first, cell_last = G["cell_first"], G["cell_last"]
cell_sum = gcell.get((G["cell_total"], 6))
check("the twelve grid cells add up to the recovery extra", abs(cell_sum - rv("extra", "D")) < 0.5,
      f"cells {cell_sum:,.2f} vs reconciliation {rv('extra', 'D'):,.2f}")
say("grid cells with euro in them:")
for r in range(cell_first, cell_last + 1):
    if (gcell.get((r, 6)) or 0) != 0:
        say(f"   {gcell.get((r, 1))} / {gcell.get((r, 2))}: {gcell.get((r, 3)):.4%}, {gcell.get((r, 4)):,.0f} lines, "
            f"billed {gcell.get((r, 5)):,.0f}, recovered {gcell.get((r, 6)):,.0f}")
code_rows = {gcell.get((r, 1)): (gcell.get((r, 3)), gcell.get((r, 4))) for r in range(G["code_first"], G["code_first"] + G["code_n"])}
check("the reason-code table lists all 20 codes", len(code_rows) == 20 and set(code_rows) == ALLOWED)
check("the reason-code table counts every line once",
      abs(sum(v[0] or 0 for v in code_rows.values()) - 45581) < 0.5, str(sum(v[0] or 0 for v in code_rows.values())))
check("the grid's own one-code-per-line check reads OK", gcell.get((int(G["code_check"][1:]), 3)) == "OK",
      str(gcell.get((int(G["code_check"][1:]), 3))))

# ---- stance sheets (package C)
for basis, sheet in (("PR00", "Stance PR00"), ("ZPR1", "Stance ZPR1"), ("CIS", "Stance CIS")):
    wsx = wbv[sheet]
    rows = {m: d["row"] for m, d in ADDR["stance"].items() if d["basis"] == basis}
    vals = {(r[0].row, c.column): c.value for r in wsx.iter_rows(min_row=1, max_row=wsx.max_row, max_col=24) for c in r if c.value is not None}
    check(f"{sheet}: one row per market on this price basis", len(rows) == {"PR00": 17, "ZPR1": 3, "CIS": 2}[basis], str(len(rows)))
    check(f"{sheet}: every row names its market and has a scenario A and a scenario B stance",
          all(vals.get((r, 2)) == m and isinstance(vals.get((r, 21)), str) and isinstance(vals.get((r, 22)), str)
              for m, r in rows.items()))
    check(f"{sheet}: the registrations outlook column is left empty", all(vals.get((r, 16)) is None for r in rows.values()))
    check(f"{sheet}: the stance override column is left empty", all(vals.get((r, 24)) is None for r in rows.values()))
sp = {(r[0].row, c.column): c.value for r in wbv["Stance PR00"].iter_rows(min_row=1, max_row=40, max_col=24) for c in r if c.value is not None}
srow = {m: d["row"] for m, d in ADDR["stance"].items()}
say("fleet, like-for-like, service share and stance, a few markets:")
for m in ("ITUK", "IUK", "IRELAND", "GERMANY", "SWEDEN", "NORWAY", "PORTUGAL"):
    r = srow[m]
    say(f"   {m}: fleet 2025 paper {sp.get((r, 6))}, carpark {sp.get((r, 7))} -> 2026 {sp.get((r, 8))}; "
        f"like-for-like {sp.get((r, 9)):+.1%}, as printed in the paper {sp.get((r, 10)):+.1%}; "
        f"service share {sp.get((r, 12)):.1%}; direction {sp.get((r, 20))}; A={sp.get((r, 21))} B={sp.get((r, 22))}")
check("Ireland's like-for-like change is +20.0% (the paper printed -15.1% on two different bases)",
      abs(sp.get((srow["IRELAND"], 9)) - 0.20037) < 1e-4, f"{sp.get((srow['IRELAND'], 9)):.5f}")
check("Germany's like-for-like change is -2.1% (the paper printed +4.9%)",
      abs(sp.get((srow["GERMANY"], 9)) + 0.021045) < 1e-4, f"{sp.get((srow['GERMANY'], 9)):.5f}")
check("Sweden's fleet at the registrations pace is about +6%",
      abs(sp.get((srow["SWEDEN"], 19)) - 0.0606) < 0.002, f"{sp.get((srow['SWEDEN'], 19)):.4f}")
check("Norway's fleet at the registrations pace is about -8%",
      abs(sp.get((srow["NORWAY"], 19)) + 0.0814) < 0.002, f"{sp.get((srow['NORWAY'], 19)):.4f}")
check("only Sweden and Norway carry a registrations pace",
      sorted(m for m, r in srow.items() if sp.get((r, 17)) is not None) == ["NORWAY", "SWEDEN"]
      if all(ADDR["stance"][m]["basis"] == "PR00" for m in ("SWEDEN", "NORWAY")) else True,
      str(sorted(m for m, r in srow.items() if ADDR["stance"][m]["basis"] == "PR00" and sp.get((r, 17)) is not None)))
check("the dealer reaction column is filled only where it was measured",
      sorted(m for m, r in srow.items() if ADDR["stance"][m]["basis"] == "PR00" and sp.get((r, 15)) is not None)
      == ["IRELAND", "ITUK", "IUK", "PORTUGAL"],
      str(sorted(m for m, r in srow.items() if ADDR["stance"][m]["basis"] == "PR00" and sp.get((r, 15)) is not None)))

# ---- margin and volume (package F)
mv = wbv["Margin and volume"]
MVA = ADDR["margin_volume"]
mvv = {(r[0].row, c.column): c.value for r in mv.iter_rows(min_row=1, max_row=mv.max_row, max_col=14) for c in r if c.value is not None}
check("margin and volume sheet has one row per market and role", MVA["last"] - MVA["first"] + 1 == 22 * 4)
check("margin and volume billed total equals the billed base",
      abs(mvv.get((MVA["total"], 4)) - 32595852.63) < 0.5, f"{mvv.get((MVA['total'], 4)):,.2f}")
check("margin and volume increase total equals the total after treatment",
      abs(mvv.get((MVA["total"], 6)) - rv("total", "D")) < 1.0,
      f"{mvv.get((MVA['total'], 6)):,.2f} vs {rv('total', 'D'):,.2f}")
check("margin and volume recovered total equals the recovery extra",
      abs(mvv.get((MVA["total"], 7)) - rv("extra", "D")) < 1.0, f"{mvv.get((MVA['total'], 7)):,.2f}")
say(f"class margin change, billed-weighted: {mvv.get((MVA['total'], 8)):+.4%}; "
    f"billed EUR on parts losing more than 1 margin point: {mvv.get((MVA['total'], 9)):,.0f}")
say(f"volume scenarios, whole book: no reaction EUR {mvv.get((MVA['total'], 10)):,.0f}; "
    f"central EUR {mvv.get((MVA['total'], 11)):,.0f}; stress EUR {mvv.get((MVA['total'], 12)):,.0f}")
measured = [m for m in ("ITUK", "IUK", "IRELAND", "PORTUGAL")]
mv_meas = {}
for i, m in enumerate(ADDR["market_layer"]["markets"]):
    r0 = MVA["first"] + i * 4
    mv_meas[m] = mvv.get((r0, 13))
check("the measured-reaction column holds a number only for the four measured markets",
      all(isinstance(mv_meas[m], (int, float)) for m in measured)
      and all(mv_meas[m] == "not measured here" for m in mv_meas if m not in measured),
      str({k: v for k, v in mv_meas.items() if k in measured}))

# ---- test design (package G)
td = ADDR["test"]
tdx = pd.read_excel(XLSX, sheet_name="Test design", header=td["list_first"] - 2, usecols="A:F",
                    nrows=td["rows"], dtype={"Part number": str})
tdx.columns = ["pn", "mkt", "role", "band", "billed", "arm"]
check("test design rows written", len(tdx) == td["rows"] and td["rows"] > 0, str(td["rows"]))
check("the test splits inside markets, never across them", set(tdx.mkt) == set(td["markets"]), str(sorted(set(tdx.mkt))))
check("Isuzu UK is not in the test", "IUK" not in set(tdx.mkt))
check("three arms", tdx.arm.nunique() == 3, str(sorted(set(tdx.arm))))
for m in td["markets"]:
    s = tdx[tdx.mkt == m]
    by = s.groupby("arm").billed.sum()
    spread = (by.max() - by.min()) / by.mean()
    say(f"   {m}: {len(s):,} part numbers, billed per arm {', '.join(f'{v:,.0f}' for v in by)} (spread {spread:.1%})")
    check(f"{m}: billed euro is balanced across the three arms (spread under 5%)", spread < 0.05, f"{spread:.3%}")
for m in td["markets"]:
    i_ = td["readout"][m]
    if i_.get("mde"):
        say(f"   {m}: smallest dealer reaction the test could see {i_['mde']['mde_dealer_reaction']:.2f} "
            f"(simulated on {i_['mde']['parts_with_months']} parts with real months {i_['mde']['pre'][0]}-{i_['mde']['post'][1]})")
    else:
        say(f"   {m}: no power figure - {i_['note']}")
check("every test market has either a simulated figure or a stated reason",
      all(td["readout"][m].get("mde") or td["readout"][m].get("note") for m in td["markets"]))

# ---- repair rules (package H)
rr_ws = wbv["Repair rules"]
rr_txt = " ".join(str(c.value) for row in rr_ws.iter_rows() for c in row if isinstance(c.value, str))
for needle in ("Israel", "60% of its value", "130%", "United Kingdom", "2024/2823", "9 December 2027", "9 December 2032",
               "Public secondary source, verify before quoting", "Nordic", "Portugal", "Ireland", "Belgium"):
    check(f"repair rules sheet says: {needle}", needle in rr_txt)
check("repair rules sheet carries no euro figure", "EUR" not in rr_txt)

# ============================================================ original sheets unchanged apart from the agreed label fixes
wbl = load_workbook(LIVE, data_only=True, read_only=True)
SKIP = {"Summary": {(r, c) for r in range(4, 11) for c in range(4, 9)} | {(r, c) for r in range(SM["sw0"], SM["readout_last"] + 1) for c in (1, 2)}
                   | {(9, 1), (36, 1)},
        "Checks": {(13, 1), (13, 2), (13, 3), (13, 4)},
        "Review lists": {(38, 1)}}
for name in ["Summary", "Proposal", "Review lists", "Dealer response", "Not in proposal", "Checks", "Read me"]:
    a, b = wbl[name], wbv[name]
    va = {(r[0].row, c.column): c.value for r in a.iter_rows() for c in r if c.value is not None}
    vb = {(r[0].row, c.column): c.value for r in b.iter_rows() for c in r if c.value is not None}
    skip = SKIP.get(name, set())
    diffs = 0
    first = None
    for k, x in va.items():
        if k in skip:
            continue
        y = vb.get(k)
        same = (x == y) or (isinstance(x, (int, float)) and isinstance(y, (int, float)) and abs(x - y) <= 1e-9 * max(1, abs(x)))
        if not same:
            diffs += 1
            first = first or (k, x, y)
    extra_cells = [k for k in vb if k not in va and k not in skip]
    if name == "Read me":
        check(f"{name}: original lines unchanged apart from the label fix (new lines appended: {len(extra_cells)})",
              diffs == 1 and first[0] == (11, 1) and all(k[0] > max(r for r, _ in va) for k in extra_cells), str(first)[:160])
    else:
        check(f"{name}: every original cell unchanged apart from the agreed label fixes ({len(va):,} cells)",
              diffs == 0 and not extra_cells, f"diffs={diffs} first={str(first)[:160]} new={extra_cells[:3]}")

# ---- label fixes (package H)
sm_full = wbv["Summary"]
rv_ws = wbv["Review lists"]
rd_ws = wbv["Read me"]
check("Summary A9 says 'decided 30 September 2026', with no personal name",
      "decided 30 September 2026" in str(sm_full["A9"].value) and "Jerome" not in str(sm_full["A9"].value), str(sm_full["A9"].value))
check("Summary A36 labels the by-market table 'before the market decisions' and points to the layer",
      "before the market decisions" in str(sm_full["A36"].value) and "Market layer" in str(sm_full["A36"].value))
check("Review lists A38 says 'decided 30 September 2026'", "decided 30 September 2026" in str(rv_ws["A38"].value)
      and "Jerome" not in str(rv_ws["A38"].value))
check("Read me A11 says 'decided 30 September 2026'", "decided 30 September 2026" in str(rd_ws["A11"].value)
      and "your call" not in str(rd_ws["A11"].value))
ml_txt = " ".join(str(v) for v in cells.values() if isinstance(v, str))
check("the Market layer explains which of 1.785 and 2.19 is right",
      "2.19" in ml_txt and "1.785" in ml_txt and "superseded" in ml_txt)
check("no personal name on the Market layer", "Jerome" not in ml_txt)
check("the Armenia and Kazakhstan block says 'decided 2 October 2026'",
      "Armenia and Kazakhstan: own increase only (decided 2 October 2026)" in ml_txt)

errs, hits, names = 0, [], []
banned = re.compile(r"\b(wallet|street|sell-?out|sellout|book b|mode a|mode b|class factor|IML v7|Model B|PRISM|warrant\w*)\b", re.I)
PERSON = re.compile(r"\b(Jerome|your call)\b", re.I)
ERR = ("#VALUE!", "#NAME?", "#DIV/0!", "#REF!", "#N/A", "#NUM!", "#NULL!")
for ws in wbv.worksheets:
    n_err = 0
    for row in ws.iter_rows():
        for c in row:
            vv = c.value
            if isinstance(vv, str):
                if vv in ERR:
                    n_err += 1
                if banned.search(vv):
                    hits.append((ws.title, c.coordinate, vv[:60]))
                if PERSON.search(vv):
                    names.append((ws.title, c.coordinate, vv[:60]))
    errs += n_err
    if n_err:
        say(f"  error cells on {ws.title}: {n_err}")
check("no formula error cells anywhere in the workbook", errs == 0, str(errs))
check("no banned label and no warranty wording in any sheet", not hits, str(hits[:3]))
check("no personal name on any sheet", not names, str(names[:3]))
check("file size under 30 MB", XLSX.stat().st_size < 30e6, f"{XLSX.stat().st_size / 1e6:.1f} MB")
wbv.close()
wbl.close()

# literal presence of the deliverable items
for lab, needle in [("switch explained", "exempt from the recovery extra"), ("reconciliation block", "Reconciliation"),
                    ("per-market totals", "Per market: average increase, euro given up, euro recovered"),
                    ("distributor conditions per market and category", "Distributor conditions per market and parts category"),
                    ("Armenia / Kazakhstan note", "Armenia and Kazakhstan: own increase only"), ("open price-basis wording", "price basis"),
                    ("sources block", "Where each block of values comes from"),
                    ("what each hold is worth", "What each hold is worth"),
                    ("label fixes", "Labels corrected in this draft")]:
    check(f"present on 'Market layer': {lab}", needle in ml_txt)

say("")
say("RESULT: " + ("ALL OK" if not fails else f"FAILED {fails}"))
(STAGE / ("verify_log_" + ("paper" if PAPER else "default") + ".txt")).write_text("\n".join(lines), encoding="utf-8")
sys.exit(1 if fails else 0)

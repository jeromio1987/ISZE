"""Verify the recalculated market-layer workbook against an independent Python replica of the published scenario.

Independent: the replica below re-derives everything from the CSVs, the live workbook's cached Proposal values and
evidence_lib.load_base(); it shares no code with the builder. Compares every part x market increase (both switch
positions), the solver points, the reconciliation block, the per-market table and the published figures
(room_to_raise_variant_B_iuk_exempt_2026-10-02.json / .csv), checks that the original sheets are unchanged against
the live workbook, and that every check cell reads OK.

Run:  python verify_market_layer_20261004.py [path to the recalculated workbook]
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
ADDR = json.loads((STAGE / "grid_addresses_2026-10-11.json").read_text(encoding="utf-8"))
PUB = json.loads((RR / "room_to_raise_variant_B_iuk_exempt_2026-10-02.json").read_text(encoding="utf-8"))
fails = []
lines = []


def say(s):
    print(s)
    lines.append(s)


def check(label, ok, detail=""):
    say(f"{'OK  ' if ok else 'FAIL'} {label}" + (f": {detail}" if detail else ""))
    if not ok:
        fails.append(label)


# ============================================================ independent replica
live = pd.read_excel(LIVE, sheet_name="Proposal", dtype={"Part number": str})
live = live.rename(columns={"Part number": "pn", "Billed EUR (Jul 25-Jun 26)": "billed", "Factory move": "c", "Proposed move": "base"})
ins = load_base()
L = ins[ins.movable].copy()
dd = pd.read_csv(ISZE / "01_data" / "00_derived" / "distributor_dimension.csv", dtype=str)
L["db"] = L.customer_code.astype(str).map(dict(zip(dd.sold_to_sap, dd.distributor_code)))
pm = L.groupby(["pn", "db"], as_index=False).net_sales_value.sum().rename(columns={"net_sales_value": "billed"})
csv_pm = pd.read_csv(RR / "room_to_raise_by_part_market_2026-10-02.csv", dtype={"pn": str}, usecols=["pn", "db", "hold_reason"])
pm = pm.merge(csv_pm, on=["pn", "db"], how="left", validate="1:1")
bp = pd.read_csv(RR / "room_to_raise_by_part_2026-10-02.csv", dtype={"pn": str}, low_memory=False,
                 usecols=["pn", "segment", "captive_strict", "lubricant", "padkit"]).set_index("pn")
P = live[["pn", "c", "base"]].set_index("pn").join(bp)
pm["hold"] = pm.hold_reason.fillna("") != ""
pm["cis"] = pm.db.isin(["ARMENIA", "KAZAKHSTAN"])
pm["base"] = pm.pn.map(P.base)
TOT = pm.billed.sum()
TGT = 0.05 * TOT
elig = (P.segment.isin(["repair", "body"]) & (P.captive_strict == 1)).astype(float)
padH, lub = P.padkit == 1, P.lubricant == 1
cap = (P.c.clip(lower=0) + 0.05).where(~padH & ~lub, 0.0)
v = elig.where(~padH & ~lub, 0.0)
base = P.base


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


say(f"Workbook: {XLSX}")
off, tab_off, mv_off_line, mv_off_part = replica([])
on, tab_on, mv_on_line, mv_on_part = replica(["IUK"])
say(f"Replica OFF: t={off['t']:.6f} total={off['total']:,.2f} extra={off['extra']:,.2f} given={off['given']:,.2f} cut={off['cut']:,.2f} IUK={off['iuk']:,.2f}")
say(f"Replica ON : t={on['t']:.6f} total={on['total']:,.2f} extra={on['extra']:,.2f} IUK={on['iuk']:,.2f}")
pb, pe = PUB["B_as_published"], PUB["B_iuk_exempt"]
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
wbv = load_workbook(XLSX, data_only=True, read_only=True)
say("Sheets: " + ", ".join(wbv.sheetnames))
check("sheet order and names", wbv.sheetnames == ["Read me", "Summary", "Market layer", "Proposal", "Review lists", "Dealer response",
                                                   "Not in proposal", "Checks", "Layer by part and market", "Layer by part", "Layer solver"])
ml = wbv["Market layer"]
cells = {(r[0].row, c.column): c.value for r in ml.iter_rows(min_row=1, max_row=ml.max_row, max_col=16) for c in r if c.value is not None}
g = lambda row, col: cells.get((row, col))
rec = ADDR["market_layer"]["rec"]
COL = {"B": 2, "C": 3, "D": 4, "E": 5, "F": 6, "G": 7}

# settings
say(f"Summary switch D5 = {wbv['Summary']['D5'].value}")
check("Summary switch D5 delivered at 0 (OFF)", wbv["Summary"]["D5"].value == 0)

# reconciliation block
def rv(key, col):
    return g(rec[key], COL[col])


for col, rp, nm in (("B", off, "OFF"), ("C", on, "ON")):
    check(f"[{nm}] total after treatment = target", abs(rv("total", col) - TGT) < 0.5, f"excel={rv('total', col):,.4f} target={TGT:,.4f}")
    check(f"[{nm}] weighted increase = 5.000%", abs(rv("pct", col) - 0.05) < 1e-9, f"{rv('pct', col):.9f}")
    check(f"[{nm}] extra vs replica", abs(rv("extra", col) - rp["extra"]) < 0.05, f"excel={rv('extra', col):,.2f} replica={rp['extra']:,.2f}")
    check(f"[{nm}] given up vs replica", abs(rv("given", col) - rp["given"]) < 0.05, f"excel={rv('given', col):,.2f} replica={rp['given']:,.2f}")
    check(f"[{nm}] cut vs replica", abs(rv("cut", col) - rp["cut"]) < 0.05, f"excel={rv('cut', col):,.2f} replica={rp['cut']:,.2f}")
    check(f"[{nm}] solver t vs replica", abs(rv("t", col) - rp["t"]) < 1e-9, f"excel={rv('t', col):.9f} replica={rp['t']:.9f}")
    check(f"[{nm}] IUK repair+body extra vs replica", abs(rv("iuk", col) - rp["iuk"]) < 0.05, f"excel={rv('iuk', col):,.2f}")
    check(f"[{nm}] repair extra vs replica", abs(rv("rep", col) - rp["repair"]) < 0.05, f"excel={rv('rep', col):,.2f}")
    check(f"[{nm}] body extra vs replica", abs(rv("body", col) - rp["body"]) < 0.05, f"excel={rv('body', col):,.2f}")
    check(f"[{nm}] service extra = 0", abs(rv("svc", col)) < 0.005)
    check(f"[{nm}] parts carrying the extra", rv("nparts", col) == rp["nparts"], f"excel={rv('nparts', col)} replica={rp['nparts']}")
    check(f"[{nm}] identity own-given-cut+extra=total", abs(g(rec['ident'], COL[col])) < 0.01, f"{g(rec['ident'], COL[col]):.6f}")
check("[OFF] published: IUK extra = EUR 91,065, extra EUR 396,568 (rounded)",
      round(rv("iuk", "B")) == 91065 and round(rv("extra", "B")) == 396568, f"{rv('iuk', 'B'):,.2f} / {rv('extra', 'B'):,.2f}")
check("[ON] published: IUK extra = 0, extra EUR 396,568 (rounded)", round(rv("iuk", "C")) == 0 and round(rv("extra", "C")) == 396568,
      f"{rv('iuk', 'C'):,.2f} / {rv('extra', 'C'):,.2f}")
check("[OFF] given up rounds to EUR 388,914", round(rv("given", "B")) == 388914, f"{rv('given', 'B'):,.2f}")
check("[OFF] total rounds to EUR 1,629,793", round(rv("total", "B")) == 1629793, f"{rv('total', 'B'):,.2f}")
check("[ON] total rounds to EUR 1,629,793", round(rv("total", "C")) == 1629793, f"{rv('total', 'C'):,.2f}")
check("[now] column equals switch OFF (delivered state)", all(abs(rv(k, "D") - rv(k, "B")) < 1e-9 for k in ("total", "extra", "given", "cut", "iuk")))
mism = [k for k in ("given", "cut", "extra", "total", "pct", "t", "rep", "body", "svc", "iuk", "nparts") if g(rec[k], 7) not in ("OK",)]
check("column G 'Matches published' reads OK on every published row", not mism, f"not OK: {mism}")

# per-market table
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
iuk = mk_rows["IUK"]
check("IUK: recovered 91,065 (OFF) -> 0 (ON), average increase OFF/ON", round(g(iuk, 13)) == 91065 and abs(g(iuk, 15)) < 0.005,
      f"OFF {g(iuk, 12):.5f} / ON {g(iuk, 14):.5f}")
ak_t, ak_n = ADDR["market_layer"]["ak_total_row"], ADDR["market_layer"]["ak_nocis_row"]
say(f"Armenia + Kazakhstan: billed EUR {g(ak_t, 2):,.0f}, increase {g(ak_t, 3):.4%}, EUR {g(ak_t, 4):,.0f}; "
    f"total if it does not reach them EUR {g(ak_n, 2):,.0f} = {g(ak_n, 3):.4%}")

# checks on the layer sheet, Checks sheet, Summary
ck_first, ck_last = ADDR["market_layer"]["ck_first"], ADDR["market_layer"]["ck_last"]
for r in range(ck_first, ck_last + 2):
    res = g(r, 4)
    check(f"layer check: {str(g(r, 1))[:90]}", res == "OK", f"value={g(r, 2)} expected={g(r, 3)}")
sm = wbv["Summary"]
check("Summary D9 reads OK", sm["D9"].value == "OK", str(sm["D9"].value))
say(f"Summary D6 total EUR {sm['D6'].value:,.2f}; D7 {sm['D7'].value:.5%}; D8 extra EUR {sm['D8'].value:,.2f}")
ck = wbv["Checks"]
for r in range(4, 14):
    check(f"Checks row {r}: {str(ck[f'A{r}'].value)[:70]}", ck[f"D{r}"].value == "OK", str(ck[f"D{r}"].value))

# ============================================================ every part x market row and every part
pmx = pd.read_excel(XLSX, sheet_name="Layer by part and market", header=3, dtype={"Part number": str})
pmx.columns = ["pn", "mkt", "cat", "billed", "cond", "own", "inc", "pts", "eur", "eur_vs", "state", "lprow", "free_b",
               "free_ex", "inc_off", "inc_on", "reason"]
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
check("hold rows = 7,833", int((pmx.state == "hold").sum()) == 7833, str(int((pmx.state == "hold").sum())))
check("every hold row pays 0%", (pmx.inc[pmx.state == "hold"] == 0).all())
check("every Armenia/Kazakhstan row is own increase only", (pmx.cond[pmx.state == "own only"] == "Own increase only: no hold, no extra (option A)").all())
check("no recovery extra on service parts", not ((pmx.cat == "service") & (pmx.cond == "Own increase + recovery extra")).any())
check("recovery-extra rows exist and only on repair/body", int((pmx.cond == "Own increase + recovery extra").sum()) > 0
      and set(pmx.cat[pmx.cond == "Own increase + recovery extra"]) <= {"repair", "body"})
check("condition text present on every row", pmx.cond.notna().all() and (pmx.cond.astype(str).str.len() > 0).all())
# one list price per part: new list EUR read once
lpx = pd.read_excel(XLSX, sheet_name="Layer by part", header=3, dtype={"Part number": str})
lpx.columns = ["pn", "desc", "cat", "noalt", "lub", "list_now", "inc_now", "list_new", "own_fact", "own_inc", "padheld", "ceil", "floor",
               "elig", "room", "free_b", "free_ex", "w_off", "w_on", "inc_off", "inc_on", "first", "nrows", "ptr", "prow"]
check("part rows = 15,273 and pointers all 0", len(lpx) == 15273 and int(lpx.ptr.sum()) == 0)
mp = lpx.set_index("pn")
check("part list increase OFF vs replica (max gap)", (mp.inc_off - mv_off_part.reindex(mp.index)).abs().max() < 1e-9)
check("part list increase ON vs replica (max gap)", (mp.inc_on - mv_on_part.reindex(mp.index)).abs().max() < 1e-9)
chk_list = lpx[lpx.list_now.notna() & (lpx.list_now != "")]
exp_new = (pd.to_numeric(chk_list.list_now) * (1 + chk_list.inc_now)).round(2)
check("new list EUR = current list x (1 + list increase now), rounded to cents", (pd.to_numeric(chk_list.list_new) - exp_new).abs().max() < 0.0051)
say(f"pad kits held: {int(lpx.padheld.sum())}; lubricants: {int(lpx.lub.sum())}; parts carrying the extra (eligible): {int(lpx.elig.sum())}")
check("29 pad kits held at 0% list increase", int(lpx.padheld.sum()) == 29 and (lpx.inc_off[lpx.padheld == 1] == 0).all())

# solver sheet
sv = wbv["Layer solver"]
svc = {(r[0].row, c.column): c.value for r in sv.iter_rows(min_row=1, max_row=20, max_col=9) for c in r if c.value is not None}
check("solver differences are 0.00 and ceiling reaches the target",
      abs(svc[(15, 2)]) < 0.01 and abs(svc[(15, 3)]) < 0.01 and svc[(16, 2)] == "yes" and svc[(16, 3)] == "yes",
      f"gaps {svc[(15, 2)]:.6f} / {svc[(15, 3)]:.6f}")
say(f"solver t OFF {svc[(12, 2)]:.8f}  ON {svc[(12, 3)]:.8f}")

# ============================================================ original sheets unchanged, errors, banned labels
wbl = load_workbook(LIVE, data_only=True, read_only=True)
SKIP = {"Summary": {(r, c) for r in range(4, 10) for c in range(4, 9)}, "Checks": {(13, 1), (13, 2), (13, 3), (13, 4)}}
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
        check(f"{name}: original lines unchanged (new lines appended: {len(extra_cells)})", diffs == 0 and all(k[0] > max(r for r, _ in va) for k in extra_cells), str(first))
    else:
        check(f"{name}: every original cell unchanged ({len(va):,} cells)", diffs == 0 and not extra_cells, f"diffs={diffs} first={first} new={extra_cells[:3]}")
errs, hits = 0, []
banned = re.compile(r"\b(wallet|street|sell-?out|sellout|book b|mode a|mode b|class factor|IML v7|Model B|PRISM)\b", re.I)
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
    errs += n_err
    if n_err:
        say(f"  error cells on {ws.title}: {n_err}")
check("no formula error cells anywhere in the workbook", errs == 0, str(errs))
check("no banned labels in any sheet", not hits, str(hits[:3]))
wbv.close()
wbl.close()

# literal presence of the deliverable items
txt = " ".join(str(v) for v in cells.values() if isinstance(v, str))
for lab, needle in [("switch explained", "exempt from the recovery extra"), ("reconciliation block", "Reconciliation"),
                    ("per-market totals", "Per market: average increase, euro given up, euro recovered"),
                    ("distributor conditions per market and category", "Distributor conditions per market and parts category"),
                    ("Armenia / Kazakhstan note", "Armenia and Kazakhstan: own increase only"), ("open price-basis wording", "price basis"),
                    ("sources block", "Where each block of values comes from")]:
    check(f"present on 'Market layer': {lab}", needle in txt)

say("")
say("RESULT: " + ("ALL OK" if not fails else f"FAILED {fails}"))
(STAGE / "verify_log_2026-10-04.txt").write_text("\n".join(lines), encoding="utf-8")
sys.exit(1 if fails else 0)

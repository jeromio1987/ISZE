"""Price revision at +5.3% weighted (Masumi, 12 Oct 2026). One price per part per price list.

Recipe = Jerome's start state of 15 Oct 2026 (simulator v4-v6): every part follows its own base price (BP)
increase, scaled so the book lands on the target; brake pad kits at today's price; steering units +5%;
parts whose reference dealer price is more than 60% above the UK shop KS International held at today's price.
Here a hold is applied to the whole part on that price list (one list price), then the book is re-solved.
Variants for the questions sheet are solved at line level (market conditions), same as the simulator.
"""
import json
from pathlib import Path
import numpy as np
import pandas as pd

H = Path(__file__).parent
ISZE = H.parents[3]
D = json.loads((H.parent / "price_tool_html_v6_2026-10-15" / "payload6.json").read_text(encoding="utf-8"))
TARGET, CEIL = 0.053, 0.05
cols = ["pn", "desc", "l1", "l2", "l3", "c", "bp0", "bp1", "p0", "p1", "p2", "nw", "pbi", "pcat", "cell", "src"]
P = pd.DataFrame(D["parts"], columns=cols)
L = pd.DataFrame(D["lines"], columns=["pi", "db", "k", "b", "q", "c0", "bits", "cat1"])
# made in: the payload only labels PMS parts, so take the source field of the price list (J = Japan IML, T = Thailand IMIT)
_pl = pd.read_parquet(ISZE / "01_data/00_derived/pricing_list_pn.parquet", columns=["part_number", "source", "is_superseded_row"])
_pl = _pl[_pl.source.isin(["J", "T"])].sort_values("is_superseded_row").drop_duplicates("part_number")
P["src"] = P.pn.map(_pl.set_index("part_number").source).fillna(P.src.replace("", np.nan)).fillna("")
P["step_raw"] =np.where(P.bp0 > 0, P.bp1 / P.bp0.where(P.bp0 > 0, 1) - 1, 0.0)
P["cp"] = P.step_raw.clip(lower=0)
L1 = D["l1"]; L2 = {i: t[1] for i, t in enumerate(D["l2"])}; L3 = {i: t[1] for i, t in enumerate(D["l3"])}
STEER = [i for i, t in enumerate(D["l3"]) if t[1] == "Steering Unit"][0]
PAD_L3 = set(D["pad_l3"]); PAD_P = set(D["pad_parts"])
P["fixed"] = np.nan; P["why"] = ""
pad = P.pn.isin(PAD_P) | P.l3.isin(PAD_L3)
P.loc[P.l3 == STEER, ["fixed", "why"]] = [0.05, "steer"]
P.loc[pad, ["fixed", "why"]] = [0.0, "pad"]
L = L.join(P[["cp", "fixed", "step_raw"]], on="pi")
FX0, FX1 = D["fx_prior"], D["fx"]
bp_w = D["bp_qty"]


def solve(held_line, target=TARGET):
    """held_line: bool array -> line moves landing on target. Same maths as the simulator (scale on own step, cap own step + 5 pts)."""
    base = L.b.sum()
    fixed = L.fixed.notna() & ~held_line
    auto = ~L.fixed.notna() & ~held_line
    F = (L.b[fixed] * L.fixed[fixed]).sum()
    need = target * base - F
    b, cp = L.b[auto].to_numpy(), L.cp[auto].to_numpy()
    lo, hi = 0.0, 5.0
    for _ in range(200):
        s = (lo + hi) / 2
        if (b * np.clip(s * cp, 0, cp + CEIL)).sum() < need: lo = s
        else: hi = s
    m = np.zeros(len(L))
    m[fixed.to_numpy()] = L.fixed[fixed]
    m[auto.to_numpy()] = np.clip(s * cp, 0, cp + CEIL)
    return m, s


# --- proposal: shop-far hold on the whole part x list
L["far"] = (L.bits & 32) > 0
far_pk = L.groupby(["pi", "k"]).far.transform("max")
# brake discs at today's price in the eight markets where service parts are held (Jerome, mail of 11 Oct, confirmed 19 Oct)
L["L3n"] = L.pi.map(P.l3).map(L3)
DISC_L3 = ["Brake Rotor", "Brake Disc"]
L["disc"] = ((L.bits & 1) > 0) & L.L3n.isin(DISC_L3)
L["dh"] = L.disc & ~far_pk
base_hold = (far_pk | L.disc).to_numpy()
m, scale = solve(base_hold)
L["m"] = m
base = L.b.sum(); extra = (L.b * L.m).sum()
assert abs(extra / base - TARGET) < 1e-9

# --- per part x list
pk = L.assign(x=L.b * L.m, hb=L.b.where(L.dh, 0.0)).groupby(["pi", "k"]).agg(b=("b", "sum"), x=("x", "sum"), q=("q", "sum"), far=("far", "max"), hb=("hb", "sum")).reset_index()
pk["m"] = np.where(pk.b != 0, pk.x / pk.b.where(pk.b != 0, 1), 0)
# moves are uniform within part x list by construction; recompute from the rule to avoid credit-note noise
def rule_move(r):
    p = P.loc[r.pi]
    if r.far: return 0.0
    if not np.isnan(p.fixed): return p.fixed
    return float(np.clip(scale * p.cp, 0, p.cp + CEIL))
pk["m"] = pk.apply(rule_move, axis=1)
# on the Israel and CIS own lists a held disc is the whole list (one distributor): move 0, nothing left to hold separately
own = (pk.k != 0) & (pk.hb != 0)
pk.loc[own, "m"] = 0.0; pk.loc[own, "hb"] = 0.0
disc_parts = set(L.pi[L.dh])

def reason(i, far_any):
    p = P.loc[i]
    if p.why == "pad": return "Brake pad kit: kept at today's price (decided 30 Sep 2026)"
    if i in disc_parts:
        return "Brake disc: today's price in the eight markets where service parts are held (customer condition on PR00, own list for UMI); other markets follow the base price"
    if p.why == "steer": return "Steering unit: +5% set by hand (base price did not move on the large ones)"
    if far_any:
        ks_ = sorted(far_k.get(i, []))
        names = " and ".join(["PR00", "UTI", "UMI", "Armenia/Kazakhstan"][k] for k in ks_)
        return "Held at today's price where our price to the end customer is already far above the UK shop (on %s; other lists follow the base price)" % names
    if p.bp0 <= 0: return "No base price on file: held at today's price"
    if p.step_raw < 0: return "Base price went down: kept at today's price"
    if p.cp == 0: return "No base price increase: kept at today's price"
    return "Follows its own base price increase (x %.3f)" % scale

wide = pk.pivot(index="pi", columns="k", values=["b", "m", "x", "hb"])
far_any = pk.groupby("pi").far.max()
far_k = pk[pk.far].groupby("pi").k.apply(list).to_dict()
SRC = {"J": "Japan (IML)", "T": "Thailand (IMIT)", "": "Not labelled"}
rows = []
for i in wide.index:
    p = P.loc[i]
    r = {"pn": p.pn, "newest": p.pbi if (isinstance(p.pbi, str) and p.pbi and p.pbi != p.pn) else "",
         "desc": p.desc, "l1": L1[p.l1], "l2": L2[p.l2], "l3": L3[p.l3], "src": SRC.get(p.src, "Not labelled"),
         "bp0": p.bp0, "bp1": p.bp1, "bp_step": p.step_raw, "reason": reason(i, bool(far_any.get(i, False)))}
    for k, nm in enumerate(["pr00", "uti", "umi", "oth"]):
        bb = wide["b"].get(k, pd.Series(dtype=float)).get(i, np.nan)
        r[nm + "_b"] = 0.0 if pd.isna(bb) else float(bb)
        mm = wide["m"].get(k, pd.Series(dtype=float)).get(i, np.nan)
        r[nm + "_m"] = None if pd.isna(mm) else float(mm)
    hb0 = wide["hb"].get(0, pd.Series(dtype=float)).get(i, np.nan)
    r["pr00_hb"] = 0.0 if pd.isna(hb0) else float(hb0)
    r["pr00_p"], r["uti_p"], r["umi_p"] = p.p0, p.p1, p.p2
    rows.append(r)
parts = pd.DataFrame(rows)
# a part not bought on a list still gets the move of the rule so the list stays complete
for nm in ["pr00", "uti", "umi", "oth"]:
    miss = parts[nm + "_m"].isna()
    parts.loc[miss, nm + "_m"] = [rule_move(pd.Series({"pi": P.index[P.pn == pn][0], "far": False})) for pn in parts.pn[miss]]
# UMI is one of the eight markets and has its own list: every brake disc keeps today's price there, bought in the window or not
parts.loc[parts.l3.isin(DISC_L3), "umi_m"] = 0.0
parts["b_tot"] = parts[["pr00_b", "uti_b", "umi_b", "oth_b"]].sum(axis=1)
parts["x_tot"] = (parts.pr00_b - parts.pr00_hb) * parts.pr00_m + sum(parts[n + "_b"] * parts[n + "_m"] for n in ["uti", "umi", "oth"])
assert abs(parts.x_tot.sum() - extra) < 1.0, (parts.x_tot.sum(), extra)
parts = parts.sort_values("b_tot", ascending=False)

# --- KS International shop price for the held parts (explanation only)
ks = pd.read_csv(ISZE / "01_data/00_derived/iam_ks_price_gap.csv", dtype={"pn": str})
ks = ks[ks.status == "ok"].groupby("pn").ks_am_min_eur.min()
parts["ks_eur"] = parts.pn.map(ks)

# --- aggregates
L["x"] = L.b * L.m
L["bpx"] = L.b * L.step_raw
L = L.join(P[["src", "l1", "pcat"]], on="pi")
DBN = {"ITUK": "Isuzu Truck UK", "IUK": "Isuzu UK (D-Max)", "UTI": "UTI Israel (trucks)", "UMI": "UMI Israel (D-Max)"}
dbname = lambda c: DBN.get(c, c.title())
by_db = L.groupby("db").agg(b=("b", "sum"), x=("x", "sum"), bpx=("bpx", "sum")).reset_index()
by_db["name"] = [dbname(D["dbs"][d]) for d in by_db.db]
LISTN = ["PR00 (EU and UK distributors)", "UTI Israel own list (1799)", "UMI Israel own list (1797)", "Armenia and Kazakhstan own lists"]
by_list = L.groupby("k").agg(b=("b", "sum"), x=("x", "sum"), c=("c0", "sum"), bpx=("bpx", "sum")).reset_index(); by_list["name"] = [LISTN[k] for k in by_list.k]
by_src = L.groupby("src").agg(b=("b", "sum"), x=("x", "sum"), bpx=("bpx", "sum")).reset_index(); by_src["name"] = by_src.src.map(SRC)
by_l1 = L.groupby("l1").agg(b=("b", "sum"), x=("x", "sum"), bpx=("bpx", "sum")).reset_index(); by_l1["name"] = [L1[i] for i in by_l1.l1]

# --- the gap Masumi asked about
bp_w = D["bp_qty"]                                   # yen base price change weighted on quantity = 5.96%
cost0 = L.c0.sum()                                   # purchase cost, euro, today's base price at 172.6 yen
cost1_samefx = (L.c0 * (1 + L.step_raw)).sum()
cost1 = cost1_samefx * FX0 / FX1
gap = {"bp_w": bp_w, "base": base, "extra": extra, "at_bp": bp_w * base, "gap_sales": (bp_w - TARGET) * base,
       "gap_cost": (bp_w - TARGET) * cost0, "cost0": cost0, "cost_up_samefx": cost1_samefx - cost0, "cost_up": cost1 - cost0,
       "fx0": FX0, "fx1": FX1, "gm0": base - cost0, "gm1": base + extra - cost1, "gm1_samefx": base + extra - cost1_samefx}

# --- dealer reaction (same formula as simulator v6)
react = []
for rr in D["react"]:
    e = rr["e"]; react.append({"label": rr["label"], "e": e, "x": float((L.b * ((1 + L.m) * (1 + e * L.m) - 1)).sum()), "src": rr["src"]})

# --- fiscal-year value by start date (same as simulator v6)
cal = D["months"]["cal"]; share = D["months"]["share"]
perdb = L.groupby("db").x.sum().to_dict()
def fy(y, mo):
    res = {}
    for i in range(24):
        yy = y + (mo - 1 + i) // 12; mn = (mo - 1 + i) % 12 + 1
        idx = cal.index(mn); v = sum(x * share[str(k)][idx] for k, x in perdb.items() if str(k) in share)
        f = "FY%d" % (yy + 1 if mn >= 4 else yy); res[f] = res.get(f, 0) + v
    return res
fyv = {"2027-01-01": fy(2027, 1), "2027-04-01": fy(2027, 4)}

# --- variants for the questions (line-level market conditions, like the simulator)
def variant(held=None, fixed_change=None):
    global L
    keep = L.fixed.copy()
    if fixed_change is not None:
        L["fixed"] = fixed_change
    h = base_hold.copy() if held is None else (base_hold | held)
    mv, s = solve(h)
    L["fixed"] = keep
    auto = L.fixed.isna() & ~pd.Series(h, index=L.index) & (L.cp > 0)
    typ = float(np.median(mv[auto.to_numpy()])) if auto.any() else 0.0
    return {"scale": s, "held_eur": float(L.b[h].sum()), "typical": typ}

base_v = variant()
V = {"proposal": base_v}
V["service8"] = variant(held=((L.bits & 1) > 0).to_numpy())
V["discs8"] = variant(held=(((L.bits & 1) > 0) & (L.pcat.isin([3]))).to_numpy())  # PMS brake_rotor = index 3 (cats list)
V["israel"] = variant(held=((L.bits & (2 | 4 | 8)) > 0).to_numpy())
V["lost45"] = variant(held=((L.bits & 16) > 0).to_numpy())
_mv, _s = solve(L.disc.to_numpy()); _a = (L.fixed.isna() & ~L.disc & (L.cp > 0)).to_numpy()
V["no_far"] = {"scale": _s, "held_eur": 0.0, "typical": float(np.median(_mv[_a]))}
fc = L.fixed.copy(); fc[(P.l3 == STEER).reindex(L.pi).to_numpy()] = np.nan
V["steer_follow"] = variant(fixed_change=fc)
fc2 = L.fixed.copy(); fc2[pad.reindex(L.pi).to_numpy()] = np.nan
V["pads_follow"] = variant(fixed_change=fc2)
assert D["pms"]["cats"][3] == "brake_rotor"
ie = L.join(P[["l2"]], on="pi", rsuffix="_")
ie_mask = ie.l2.map(L2).str.contains("Intake|Exhaust|Emission|Turbo|EGR|DPF|Catal", case=False, na=False)
V["intake_exhaust"] = variant(held=ie_mask.to_numpy())
V["drums8"] = variant(held=(((L.bits & 1) > 0) & L.L3n.eq("Brake Drum")).to_numpy())
V["discs_all_pr00"] = variant(held=(L.L3n.isin(DISC_L3) & (L.k == 0)).to_numpy())
V["no_disc"] = (lambda mv_s: {"scale": mv_s[1]})(solve(far_pk.to_numpy()))
_mv, _s = solve(base_hold, target=bp_w); _a = (L.fixed.isna() & ~base_hold & (L.cp > 0)).to_numpy()
V["full_bp"] = {"scale": _s, "typical": float(np.median(_mv[_a]))}

facts = {
    "scale": scale, "base": base, "extra": extra, "n_parts": len(parts),
    "n_held": int(((parts.pr00_m == 0) & (parts.b_tot != 0)).sum()),
    "b_held": float(parts.b_tot[(parts.x_tot == 0)].sum()),
    "steer_b": float(parts.b_tot[parts.reason.str.startswith("Steering")].sum()),
    "steer_n": int(parts.reason.str.startswith("Steering").sum()),
    "pad_b": float(parts.b_tot[parts.reason.str.startswith("Brake pad")].sum()),
    "pad_n": int(parts.reason.str.startswith("Brake pad").sum()),
    "far_b": float(parts.b_tot[parts.reason.str.startswith("Held at today's price where our")].sum()),
    "far_n": int(parts.reason.str.startswith("Held at today's price where our").sum()),
    "big_n": int(((parts.pr00_m > 0.15) & (parts.b_tot > 0)).sum()),
    "big_b": float(parts.b_tot[(parts.pr00_m > 0.15)].sum()),
    "big_x": float(parts.x_tot[(parts.pr00_m > 0.15)].sum()),
    "noprice_pr00": int(((parts.pr00_b > 0) & parts.pr00_p.isna()).sum()),
    "noprice_pr00_b": float(parts.pr00_b[(parts.pr00_b > 0) & parts.pr00_p.isna()].sum()),
    "noprice_uti": int(((parts.uti_b > 0) & parts.uti_p.isna()).sum()),
    "noprice_umi": int(((parts.umi_b > 0) & parts.umi_p.isna()).sum()),
    "newest_diff": int((parts.newest != "").sum()),
    "median_move": float(parts.pr00_m[(parts.b_tot > 0) & (parts.x_tot > 0)].median()),
    "max_move": float(parts.pr00_m.max()),
    "ie_b": float(L.b[ie_mask].sum()),
    "disc_held_b": float(L.b[L.dh].sum()), "disc_n": len(disc_parts),
    "disc_by_db": {dbname(D["dbs"][d]): float(v) for d, v in L[L.dh].groupby("db").b.sum().items()},
    "drums8_b": float(L.b[((L.bits & 1) > 0) & L.L3n.eq("Brake Drum")].sum()),
    "discs_pr00_all_b": float(L.b[L.L3n.isin(DISC_L3) & (L.k == 0)].sum()),
    "service8_b": float(L.b[(L.bits & 1) > 0].sum()),
    "discs8_b": float(L.b[((L.bits & 1) > 0) & (L.pcat == 3)].sum()),
    "service8_dbs": sorted({dbname(D["dbs"][d]) for d in L.db[(L.bits & 1) > 0]}),
}
out = {"facts": facts, "gap": gap, "react": react, "fy": fyv, "V": V,
       "by_db": by_db.to_dict("records"), "by_list": by_list.to_dict("records"), "by_src": by_src.to_dict("records"),
       "by_l1": by_l1.to_dict("records")}
(H / "result.json").write_text(json.dumps(out, indent=1, default=float), encoding="utf-8")
parts.to_pickle(H / "parts.pkl")
print(json.dumps({"facts": facts, "gap": gap, "react": react, "fy": fyv, "V": V}, indent=1, default=float))

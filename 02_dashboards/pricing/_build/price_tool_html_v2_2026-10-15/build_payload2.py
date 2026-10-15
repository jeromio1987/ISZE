"""Payload for the v2 price revision simulator (lines = part x distributor x price list).
Base: same in-scope revision base as the AIM-level Excel tool (47,617 lines, EUR 32,595,852.63, Jul 2025 - Jun 2026).
Adds: price now per list, distributor and hold flags per line, quantity-weighted BP step, PBI newest sample.
Writes payload2.json next to this file."""
import json, sys, time
from pathlib import Path
import numpy as np, pandas as pd, yaml

ISZE = Path(r"C:\Users\jerom\Desktop\claude\ISZE")
PROP = ISZE / "02_dashboards/pricing/_build/price_5pct_proposal_2026-09-29"
sys.path.insert(0, str(PROP))
from evidence_lib import load_base, attach_evidence  # noqa: E402

DER = ISZE / "01_data/00_derived"
RR = PROP / "room_to_raise_2026-10-02"
CFG = yaml.safe_load((ISZE / "03_analytics/isze_pricing/config.yaml").read_text(encoding="utf-8"))
FX = float(CFG["formula"]["fx_rate"])
FXP = float([v for k, v in CFG["formula"]["fx_prior_vintages"].items() if str(k) == "2026-04-01"][0])
DISC = {k: float(v) for k, v in CFG["formula"]["source_discount"].items()}
OWN = {"1799": "UTI", "1797": "UMI", "2372": "OTH", "2733": "OTH", "2734": "OTH"}
LISTS = ["PR00", "UTI", "UMI", "OTH"]
t0 = time.time()

L = load_base()
L = L[L.movable].copy()
assert len(L) == 47617 and abs(L.net_sales_value.sum() - 32595852.63) < 0.01
cust = L.customer_code.astype(str).str.strip().str.lstrip("0")
L["lst"] = cust.map(OWN).fillna("PR00")
dd = pd.read_csv(DER / "distributor_dimension.csv", dtype=str)
L["db"] = L.customer_code.astype(str).map(dict(zip(dd.sold_to_sap, dd.distributor_code)))
assert L.db.notna().all()
L["c"] = L.bp_new_jpy / L.bp_prior_revised - 1

# quantity-weighted BP step as published (5.9616%): check on the movable lines
q = L.billed_qty.astype(float)
bpq = (q * L.bp_new_jpy).sum() / (q * L.bp_prior_revised).sum() - 1
print("BP step weighted by quantity, movable lines: %.5f%%" % (bpq * 100))

# per-line evidence: capture zone per distributor x service category (Lost = sells under 45% of need)
E = attach_evidence(L.copy())
zone = E.groupby(["pn", "db"]).zone.agg(lambda s: "Lost" if (s == "Lost").any() else "")
print("zone Lost part x db:", int((zone == "Lost").sum()))

# decided market holds per part x distributor (2 Oct paper): reason strings from the room-to-raise file
pm = pd.read_csv(RR / "room_to_raise_by_part_market_2026-10-02.csv", dtype={"pn": str},
                 usecols=["pn", "db", "hold_reason"])
print(pm.hold_reason.value_counts(dropna=False).to_dict())
BITS = {"service hold (market exercise)": 1, "UMI body/collision hold": 2, "UMI lighting hold": 4, "UTI lighting hold": 8}
pm["bits"] = pm.hold_reason.map(BITS).fillna(0).astype(int)
assert pm.hold_reason.dropna().isin(BITS).all()
bymk = pm.groupby(["pn", "db"]).bits.max()

rel = pd.read_csv(DER / "_releases/aim_pn_classification_release_2026-10-15.csv", dtype=str,
                  usecols=["part_number", "aim_l1_fixed", "aim_l2_fixed", "aim_l3_fixed"])
rel["part_number"] = rel.part_number.str.strip()
rel = rel.drop_duplicates("part_number").set_index("part_number")
rv = pd.read_csv(DER / "_releases/revert_list_wrong_moves_2026-10-15.csv", dtype=str)
rv["part_number"] = rv.part_number.str.strip()
rv = rv.drop_duplicates("part_number").set_index("part_number")
print("revert list parts:", len(rv))
enq = pd.read_parquet(DER / "pricing_pn_enquiry.parquet", columns=["part_number", "source", "sp_eur_pr00_ie40", "newest_pn"])
enq["pn"] = enq.part_number.astype(str).str.strip()
enq = enq.drop_duplicates("pn").set_index("pn")
kw = pd.read_parquet(DER / "pricing_zpr1_key_wide.parquet", columns=["part_number", "zpr1_sp_UTI", "zpr1_sp_UMI"])
kw["part_number"] = kw.part_number.astype(str).str.strip()
kw = kw.drop_duplicates("part_number").set_index("part_number")
pbi = pd.read_csv(ISZE / "01_data/90_INBOX/pbi_iszj_newest_export_pns_2026-10-15.csv", dtype=str)
pbi_new = {str(a).strip(): str(b).strip() for a, b in zip(pbi.Material, pbi.NEWEST)}

g = L.groupby("pn")
P = pd.DataFrame({"c": g.c.first(), "bp0": g.bp_prior_revised.first(), "bp1": g.bp_new_jpy.first()})
P["billed"] = g.net_sales_value.sum()
P["desc"] = (L.sort_values("net_sales_value", ascending=False).drop_duplicates("pn").set_index("pn")
             .billed_description.reindex(P.index).fillna("").astype(str).str.slice(0, 44))
for lv in ("l1", "l2", "l3"):
    P[lv] = rel["aim_%s_fixed" % lv].reindex(P.index).fillna("Not classified").astype(str)
    P.loc[P.index.isin(rv.index), lv] = rv["revert_to_aim_" + lv].reindex(P.index[P.index.isin(rv.index)]).to_numpy()
src = enq.source.reindex(P.index)
src[~src.isin(["J", "T"])] = ""
P["fob"] = np.where(src == "J", P.bp0 / FX * DISC["J"], np.where(src == "T", P.bp0 / FX * DISC["T"], np.nan))
P["pPR00"] = pd.to_numeric(enq.sp_eur_pr00_ie40.reindex(P.index), errors="coerce")
P["pUTI"] = pd.to_numeric(kw.zpr1_sp_UTI.reindex(P.index), errors="coerce")
P["pUMI"] = pd.to_numeric(kw.zpr1_sp_UMI.reindex(P.index), errors="coerce")
for k in ("pPR00", "pUTI", "pUMI"):
    P.loc[~(P[k] > 0), k] = np.nan
nn = enq.newest_pn.reindex(P.index)
P["new_ie40"] = nn.map(lambda v: "" if pd.isna(v) else str(v).replace(".0", "").strip().zfill(10))
P = P.sort_values("billed", ascending=False)
assert len(P) == 15273
pidx = {pn: i for i, pn in enumerate(P.index)}

l1 = sorted(P.l1.unique())
l2 = sorted({(a, b) for a, b in zip(P.l1, P.l2)})
l3 = sorted({(a, b, c) for a, b, c in zip(P.l1, P.l2, P.l3)})
i1 = {v: i for i, v in enumerate(l1)}
i2 = {v: i for i, v in enumerate(l2)}
i3 = {v: i for i, v in enumerate(l3)}


def n2(x):
    return None if pd.isna(x) else round(float(x), 2)


prow = []
for pn, r in P.iterrows():
    nw = r.new_ie40 if r.new_ie40 not in ("", "0000000000", pn) else ""
    prow.append([pn, r.desc, i1[r.l1], i2[(r.l1, r.l2)], i3[(r.l1, r.l2, r.l3)], round(float(r.c), 5),
                 round(float(r.bp0)), round(float(r.bp1)), n2(r.pPR00), n2(r.pUTI), n2(r.pUMI), nw,
                 pbi_new.get(pn, "")])

# lines: part x distributor x list
LN = L.groupby(["pn", "db", "lst"], as_index=False).agg(b=("net_sales_value", "sum"), q=("billed_qty", "sum"))
LN["fob"] = LN.pn.map(P.fob)
LN["cost0"] = np.where(LN.fob.notna(), LN.q * LN.fob, 0.0)
mk = pd.MultiIndex.from_frame(LN[["pn", "db"]])
LN["bits"] = bymk.reindex(mk).fillna(0).astype(int).to_numpy()
LN["lost"] = (zone.reindex(mk).fillna("") == "Lost").to_numpy().astype(int)
dbs = sorted(LN.db.unique(), key=lambda d: -LN.b[LN.db == d].sum())
dix = {d: i for i, d in enumerate(dbs)}
lix = {k: i for i, k in enumerate(LISTS)}
lines = [[pidx[r.pn], dix[r.db], lix[r.lst], round(r.b, 2), round(r.q), round(r.cost0), int(r.bits) | (16 if r.lost else 0)]
         for r in LN.itertuples()]
print("lines", len(lines), "dbs", len(dbs), "billed", round(sum(x[3] for x in lines), 2))

out = {"l1": l1, "l2": [[i1[a], b] for a, b in l2], "l3": [[i2[(a, b)], c] for a, b, c in l3],
       "dbs": dbs, "parts": prow, "lines": lines, "fx": FX, "fx_prior": FXP, "disc": DISC,
       "pad_parts": json.loads((PROP / "price_5pct_proposal_summary_2026-09-29.json").read_text())["pad_kits_pns"][:0]
       or ["8978279610", "5876150640", "8978279590", "5876150650", "8978279601"],
       "pad_l3": [i3[t] for t in l3 if t[2] == "Brake Pad Kit"],
       "bp_qty": bpq, "pbi_n": len(pbi_new),
       "ly": {"turn0": 32653680.99999973, "turn1": 34395480.82000011, "bp": 0.030504465833538275,
              "fob": 0.002951740710517514, "turn": 0.05334160703047219}}
Path(__file__).with_name("payload2.json").write_text(json.dumps(out, separators=(",", ":")), encoding="utf-8")
print("done in %.0fs" % (time.time() - t0))

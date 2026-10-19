"""Payload for the clickable price revision page. Same base as the AIM-level Excel tool
(47,617 lines, EUR 32,595,852.63, Jul 2025 - Jun 2026). Writes payload.json next to this file."""
import json, sys
from pathlib import Path
import numpy as np, pandas as pd, yaml
ISZE = Path(r"C:\Users\jerom\Desktop\claude\ISZE")
sys.path.insert(0, str(ISZE / "02_dashboards/pricing/_build/price_5pct_proposal_2026-09-29"))
from evidence_lib import load_base
DER = ISZE / "01_data/00_derived"
CFG = yaml.safe_load((ISZE / "03_analytics/isze_pricing/config.yaml").read_text(encoding="utf-8"))
FX = float(CFG["formula"]["fx_rate"]); FXP = float([v for k, v in CFG["formula"]["fx_prior_vintages"].items() if str(k) == "2026-04-01"][0])
DISC = {k: float(v) for k, v in CFG["formula"]["source_discount"].items()}
OWN = {"1799": "UTI", "1797": "UMI", "2372": "OTH", "2733": "OTH", "2734": "OTH"}
LISTS = ["PR00", "UTI", "UMI", "OTH"]
L = load_base(); L = L[L.movable].copy()
assert len(L) == 47617 and abs(L.net_sales_value.sum() - 32595852.63) < 0.01
L["lst"] = L.customer_code.astype(str).str.strip().str.lstrip("0").map(OWN).fillna("PR00")
L["c"] = L.bp_new_jpy / L.bp_prior_revised - 1
rel = pd.read_csv(DER / "_releases/aim_pn_classification_release_2026-10-11.csv", dtype=str,
                  usecols=["part_number", "aim_l1_fixed", "aim_l2_fixed", "aim_l3_fixed"])
rel["part_number"] = rel.part_number.str.strip(); rel = rel.drop_duplicates("part_number").set_index("part_number")
enq = pd.read_parquet(DER / "pricing_pn_enquiry.parquet", columns=["part_number", "source"])
enq["pn"] = enq.part_number.astype(str).str.strip(); enq = enq.drop_duplicates("pn").set_index("pn")
g = L.groupby("pn")
P = pd.DataFrame({"c": g.c.first(), "bp0": g.bp_prior_revised.first(), "bp1": g.bp_new_jpy.first()})
for k in LISTS:
    d = L[L.lst == k].groupby("pn")
    P["b_" + k] = d.net_sales_value.sum().reindex(P.index).fillna(0.0)
    P["q_" + k] = d.billed_qty.sum().reindex(P.index).fillna(0.0)
P["billed"] = P[["b_" + k for k in LISTS]].sum(axis=1)
P["desc"] = (L.sort_values("net_sales_value", ascending=False).drop_duplicates("pn").set_index("pn")
             .billed_description.reindex(P.index).fillna("").astype(str).str.slice(0, 44))
for lv in ("l1", "l2", "l3"):
    P[lv] = rel["aim_%s_fixed" % lv].reindex(P.index).fillna("Not classified").astype(str)
src = enq.source.reindex(P.index); src[~src.isin(["J", "T"])] = ""
P["fob"] = np.where(src == "J", P.bp0 / FX * DISC["J"], np.where(src == "T", P.bp0 / FX * DISC["T"], np.nan))
P = P.sort_values("billed", ascending=False); assert len(P) == 15273
l1 = sorted(P.l1.unique()); l2 = sorted({(a, b) for a, b in zip(P.l1, P.l2)})
l3 = sorted({(a, b, c) for a, b, c in zip(P.l1, P.l2, P.l3)})
i1 = {v: i for i, v in enumerate(l1)}; i2 = {v: i for i, v in enumerate(l2)}; i3 = {v: i for i, v in enumerate(l3)}
rows = []
for pn, r in P.iterrows():
    cost = [0 if np.isnan(r.fob) else round(r["q_" + k] * r.fob) for k in LISTS]
    rows.append([pn, r.desc, i1[r.l1], i2[(r.l1, r.l2)], i3[(r.l1, r.l2, r.l3)],
                 *[round(r["b_" + k]) for k in LISTS], round(float(r.c), 5), *cost,
                 round(float(r.bp0)), round(float(r.bp1))])
out = {"l1": l1, "l2": [[i1[a], b] for a, b in l2], "l3": [[i2[(a, b)], c] for a, b, c in l3],
       "rows": rows, "fx": FX, "fx_prior": FXP, "disc": DISC,
       "cols": ["pn", "desc", "l1", "l2", "l3", "bPR00", "bUTI", "bUMI", "bOTH", "c", "kPR00", "kUTI", "kUMI", "kOTH", "bp0", "bp1"],
       "pad_parts": ["8978279610", "5876150640", "8978279590", "5876150650", "8978279601"],
       "pad_l3": [i3[t] for t in l3 if t[2] == "Brake Pad Kit"],
       "ly": {"turn0": 32653680.99999973, "turn1": 34395480.82000011, "bp": 0.030504465833538275, "fob": 0.002951740710517514,
              "turn": 0.05334160703047219}}
Path(__file__).with_name("payload.json").write_text(json.dumps(out, separators=(",", ":")), encoding="utf-8")
print(len(rows), len(l1), len(l2), len(l3), out["pad_l3"])

"""Which part x market lines have our reference dealer price more than 60% above the KS International price (the A8 rule of the workbook)."""
import json, sys
from pathlib import Path
import numpy as np, pandas as pd
ISZE = Path(r"C:\Users\jerom\Desktop\claude\ISZE")
PROP = ISZE / "02_dashboards/pricing/_build/price_5pct_proposal_2026-09-29"
sys.path.insert(0, str(PROP))
from evidence_lib import load_base, attach_evidence
H = Path(__file__).parent
D = json.loads((H / "payload2.json").read_text(encoding="utf-8"))
L = load_base(); L = L[L.movable].copy()
dd = pd.read_csv(ISZE / "01_data/00_derived/distributor_dimension.csv", dtype=str)
L["db"] = L.customer_code.astype(str).map(dict(zip(dd.sold_to_sap, dd.distributor_code)))
E = attach_evidence(L.copy())
ks = E.evidence_tier.isin(["T1", "T2"])
idx = np.where(ks, E.ref_dealer_price_eur / E.independent_price_eur, np.nan)
lost = (E.zone_basis == "Measured") & (E.zone == "Lost")
E["far"] = ks & (idx > 1.60) & ~lost
far = E[E.far].groupby(["pn", "db"]).size().index
fs = set(far)
pidx = {p[0]: i for i, p in enumerate(D["parts"])}
dix = {d: i for i, d in enumerate(D["dbs"])}
fl = sorted({(pidx[pn], dix[db]) for pn, db in fs})
(H / "far_flags.json").write_text(json.dumps(fl), encoding="utf-8")
print("part x market pairs far above KS:", len(fl), "parts:", len({a for a, b in fl}))

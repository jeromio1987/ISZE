"""v5 payload: payload4 plus the PMS dimension.
PMS parts = the 484 part numbers of the revision base that sit in a PMS category of vehicle_family_bands.csv (Jerome, 15 Oct 2026).
Per part: category, made-in source (Japan IML / Thailand IMIT), weight band (vehicle_band_applicability.csv).
Per line: category index and bit 64 = the distributor buys under 45% of what its trucks need in that category (pms_capture_by_db_year.csv, 2025, total lines)."""
import json
from pathlib import Path
import numpy as np, pandas as pd
ISZE = Path(r"C:\Users\jerom\Desktop\claude\ISZE"); H = Path(__file__).parent; DER = ISZE / "01_data/00_derived"
D = json.loads((H / "payload4.json").read_text(encoding="utf-8"))
pn = [p[0] for p in D["parts"]]; pidx = {p: i for i, p in enumerate(pn)}
fb = pd.read_csv(DER / "vehicle_family_bands.csv", dtype=str).drop_duplicates("pn"); fb = fb[fb.pn.isin(pidx)]
cap = pd.read_csv(DER / "pms_capture_by_db_year.csv")
c25 = cap[(cap.year == 2025) & (cap.line_type == "total")]
labels = dict(zip(c25.pms_category, c25.category_label))
cats = sorted(fb.pms_category.unique())
cix = {c: i for i, c in enumerate(cats)}
va = pd.read_csv(DER / "vehicle_band_applicability.csv", dtype=str).drop_duplicates("pn").set_index("pn")
enq = pd.read_parquet(DER / "pricing_pn_enquiry.parquet", columns=["part_number", "source"]); enq["pn"] = enq.part_number.astype(str).str.strip(); enq = enq.drop_duplicates("pn").set_index("pn")
BAND = {"LCV_D-Max": "D-Max (light vehicle)", "7.5t_N50_N62_N75": "7.5 t trucks (N50, N62, N75)", "F_series_MD_heavy": "F-series medium and heavy",
        "3.5t_N35": "3.5 t trucks (N35)", "5.5t_N50_N55": "5.5 t trucks (N50, N55)"}


def band(p):
    if p not in va.index: return "No weight band on file"
    st = va.at[p, "band_status"]
    if st == "single_band": return BAND.get(va.at[p, "vehicle_bands"], str(va.at[p, "vehicle_bands"]))
    if st == "shared_across_bands": return "Fits several weight bands"
    return "No weight band on file"


cells, cell_ix = [], {}
for i, p in enumerate(D["parts"]):
    c = fb.set_index("pn").pms_category.get(p[0]) if p[0] in set(fb.pn) else None
    if c is None:
        p += [-1, -1, ""]; continue
    s = enq.source.get(p[0]); s = s if s in ("J", "T") else ""
    key = (cix[c], s, band(p[0]))
    if key not in cell_ix: cell_ix[key] = len(cells); cells.append(list(key))
    p += [cix[c], cell_ix[key], s]
dix = {d: i for i, d in enumerate(D["dbs"])}
capm = {}
for r in c25.itertuples():
    if r.pms_category in cix and r.distributor_code in dix and np.isfinite(r.capture_rate):
        capm.setdefault(str(cix[r.pms_category]), {})[str(dix[r.distributor_code])] = round(float(r.capture_rate), 4)
n_lost = 0
for l in D["lines"]:
    ci = D["parts"][l[0]][13]
    if ci < 0:
        l.append(0); continue
    l.append(ci + 1)
    r = capm.get(str(ci), {}).get(str(l[1]))
    if r is not None and r < 0.45:
        l[6] |= 64; n_lost += 1
D["pms"] = {"cats": cats, "labels": [labels.get(c, c) for c in cats], "cells": cells, "cap": capm,
            "src": {"J": "Japan (IML)", "T": "Thailand (IMIT)", "": "Source not on file"}}
(H / "payload5.json").write_text(json.dumps(D, separators=(",", ":")), encoding="utf-8")
pm = [p for p in D["parts"] if p[13] >= 0]
print("PMS parts", len(pm), "categories", len(cats), "cells", len(cells), "lost lines", n_lost, "capture cells", sum(len(v) for v in capm.values()))
from collections import Counter
print(Counter(c[2] for c in cells).most_common(8))

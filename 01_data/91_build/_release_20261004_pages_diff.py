"""Page-level effect of release 2026-10-04 (candidate) vs the approved 2026-10-02-chassis-frame.

Input: the two figure-key exports the AIM pages read (spine = AIM master, release AIM labels laid
over it) and the VERIFY files of the live pages and of the staged test copies. Read-only; writes only
_release_20261004_pages_diff.json beside itself.

Euro: sales_fact.parquet net_sales_value 2025-09-01..2026-08-31, 10-digit padded key.
"""
from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path

import pandas as pd

DER = Path(r"C:\Users\jerom\Desktop\claude\ISZE\01_data\00_derived")
TOOL = Path(r"C:\Users\jerom\Desktop\claude\ISZE\04_tools\aim_db_dlr_deep_dive")
X_NEW = DER / "AIM_Master_PN_Categories_Figkey_release_2026-10-04.csv"
X_OLD = DER / "AIM_Master_PN_Categories_Figkey_release_2026-10-02-chassis-frame.csv"
REL = DER / "_releases" / "aim_pn_classification_release_2026-10-04.csv"
OUT = Path(__file__).with_suffix(".json")
PH = {"", "nan", "none", "unknown", "unknown review", "null"}


def rd(p):
    return pd.read_csv(p, dtype=str, keep_default_na=False, low_memory=False)


def pad(k):
    k = str(k).strip()
    return k.zfill(10) if k.isdigit() else k


sf = pd.read_parquet(DER / "sales_fact.parquet", columns=["billing_date", "part_number", "net_sales_value"])
sf = sf[(sf.billing_date >= "2025-09-01") & (sf.billing_date <= "2026-08-31")]
sf["pn"] = sf.part_number.astype(str).map(pad)
L12 = sf.groupby("pn").net_sales_value.sum()
TOTAL = float(sf.net_sales_value.sum())

xn, xo = rd(X_NEW).set_index("part_number"), rd(X_OLD).set_index("part_number")
out: dict = {"export_new": X_NEW.name, "export_old": X_OLD.name, "l12m_total_sales_fact_eur": round(TOTAL, 2)}
out["rows"] = {"old": len(xo), "new": len(xn), "same_part_set": set(xn.index) == set(xo.index)}
xo = xo.loc[xn.index]
lv = ["aim_level_1", "aim_level_2", "aim_level_3"]
mv = (xn[lv] != xo[lv]).any(axis=1)
na_old = xo.aim_level_1.str.strip().str.lower().isin(PH)
na_new = xn.aim_level_1.str.strip().str.lower().isin(PH)
eur_x = pd.Series([float(L12.get(pad(p), 0.0)) for p in xn.index], index=xn.index)
out["pns_level_move"] = int(mv.sum())
out["eur_level_move"] = round(float(eur_x[mv].sum()), 2)
out["other_columns_changed"] = {c: int((xn[c] != xo[c]).sum()) for c in xn.columns
                                if c not in lv and (xn[c] != xo[c]).any()}
out["not_classified_parts"] = {"old": int(na_old.sum()), "new": int(na_new.sum())}
out["not_classified_eur"] = {"old": round(float(eur_x[na_old].sum()), 2),
                             "new": round(float(eur_x[na_new].sum()), 2)}
out["not_classified_eur_pct_of_total"] = {"old": round(100 * float(eur_x[na_old].sum()) / TOTAL, 3),
                                          "new": round(100 * float(eur_x[na_new].sum()) / TOTAL, 3)}
pm = defaultdict(lambda: {"parts": 0, "eur": 0.0})
for pn in xn.index[mv]:
    k = f"{' > '.join(xo.loc[pn, lv])}  ->  {' > '.join(xn.loc[pn, lv])}"
    pm[k]["parts"] += 1
    pm[k]["eur"] += float(eur_x[pn])
out["moves"] = sorted([{"move": k, "parts": v["parts"], "eur": round(v["eur"], 2)} for k, v in pm.items()],
                      key=lambda r: (-r["eur"], -r["parts"]))
rel = rd(REL)
relpn = set(rel.part_number)
spine = set(xn.index)
out["release_rows_not_on_the_page_spine"] = len(relpn - spine - set(map(pad, spine)))
added_pns = set(rel.loc[rel.aim_source == "missing_billed_20261004", "part_number"])
out["added_rows"] = len(added_pns)
out["added_rows_on_spine"] = sorted(p for p in added_pns if p in spine)

# ---- VERIFY files: live (approved release) vs staged (candidate)
vals = {}
for run in ("PORTUGAL", "ALL"):
    for kind, stem in (("deep_dive", "VERIFY_"), ("comparison", "VERIFY_COMPARISON_")):
        live = json.loads((TOOL / f"{stem}{run}.json").read_text(encoding="utf-8"))
        stg_p = TOOL / f"{stem}{run}_staged.json"
        stg = json.loads(stg_p.read_text(encoding="utf-8")) if stg_p.exists() else None
        for name, doc in (("live", live), ("staged", stg)):
            if doc is None:
                continue
            for c in doc.get("checks", []):
                if "not classified in AIM" in c.get("name", ""):
                    vals.setdefault(f"{kind} {run}: {c['name']}", {})[name] = c.get("actual")
            vals.setdefault(f"{kind} {run}: checks", {})[name] = f"{doc.get('passed')} pass, {doc.get('failed')} fail"
out["page_verify_not_classified"] = vals
OUT.write_text(json.dumps(out, indent=2, default=str), encoding="utf-8")
print(json.dumps({k: v for k, v in out.items() if k != "moves"}, indent=1)[:5000])
print("MOVES")
for r in out["moves"]:
    print(f"  {r['parts']:4d}  {r['eur']:>11,.2f}  {r['move']}")

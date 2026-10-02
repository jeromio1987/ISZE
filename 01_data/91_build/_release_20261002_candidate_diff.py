"""Diff release 2026-10-02-candidate against the approved release 2026-10-02, at file level
(both axes) and at page-input level (figure-key export). Read-only; writes only
_release_20261002_candidate_diff.json beside itself.

Euro: L12M parts billed = sales_fact.parquet net_sales_value 2025-09-01..2026-08-31, all
sold-to, 10-digit padded key (the 21 Sep review's window). The export's own l12m_billed_eur
column is reported beside it for the page-level diff only."""
from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path

import pandas as pd

DER = Path(r"C:\Users\jerom\Desktop\claude\ISZE\01_data\00_derived")
REL = DER / "_releases"
NEW = REL / "aim_pn_classification_release_2026-10-02-candidate.csv"
OLD = REL / "aim_pn_classification_release_2026-10-02.csv"
LOG = REL / "aim_pn_classification_release_2026-10-02-candidate.changes.csv"
X_NEW = DER / "AIM_Master_PN_Categories_Figkey_release_2026-10-02-candidate.csv"
X_OLD = DER / "AIM_Master_PN_Categories_Figkey_release_2026-10-02.csv"
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
TOTAL_L12 = float(sf.net_sales_value.sum())


def eur(pns):
    return round(float(sum(L12.get(pad(p), 0.0) for p in pns)), 2)


new, old = rd(NEW), rd(OLD)
log = rd(LOG)
grp = log.groupby("part_number").change_group.first()
out: dict = {"files": {"new": NEW.name, "old": OLD.name}, "l12m_window": "2025-09-01..2026-08-31",
             "l12m_total_sales_fact_eur": round(TOTAL_L12, 2)}
kn, ko = set(new.part_number), set(old.part_number)
out["rows"] = {"old": len(old), "new": len(new), "added": sorted(kn - ko), "removed": sorted(ko - kn)}
n, o = new.set_index("part_number"), old.set_index("part_number").reindex(new.part_number)
common = sorted(kn & ko)
nc, oc = n.loc[common], o.loc[common]
out["columns_changed"] = {c: int((nc[c] != oc[c]).sum()) for c in nc.columns if (nc[c] != oc[c]).any()}
changed_pns = sorted(set(nc.index[(nc != oc).any(axis=1)]) | (kn - ko))
out["parts_changed"] = len(changed_pns)
out["parts_changed_eur"] = eur(changed_pns)
out["parts_changed_by_group"] = {g: {"parts": int((grp.reindex(changed_pns) == g).sum()),
                                     "eur": eur([p for p in changed_pns if grp.get(p) == g])}
                                 for g in sorted(grp.unique())}
assert set(changed_pns) == set(grp.index), "a changed part is not in the change log, or vice versa"


def moves(cols, label):
    d = defaultdict(lambda: {"parts": 0, "eur": 0.0, "groups": set(), "examples": []})
    for pn in changed_pns:
        a = " > ".join(oc.loc[pn, cols]) if pn in oc.index else "(not in release)"
        b = " > ".join(n.loc[pn, cols])
        if a == b:
            continue
        k = f"{a}  ->  {b}"
        d[k]["parts"] += 1
        d[k]["eur"] += eur([pn])
        d[k]["groups"].add(grp.get(pn, ""))
        if len(d[k]["examples"]) < 3:
            d[k]["examples"].append(pn)
    rows = [{"move": k, "parts": v["parts"], "eur": round(v["eur"], 2), "groups": sorted(v["groups"]),
             "examples": v["examples"]} for k, v in d.items()]
    return sorted(rows, key=lambda r: (-r["eur"], -r["parts"]))


out["catalogue_moves"] = moves(["catalog_l1", "catalog_l2", "catalog_l3"], "catalogue")
out["aim_moves"] = moves(["aim_l1_fixed", "aim_l2_fixed", "aim_l3_fixed"], "aim")
out["catalogue_moves_total"] = {"parts": sum(r["parts"] for r in out["catalogue_moves"]),
                                "eur": round(sum(r["eur"] for r in out["catalogue_moves"]), 2)}
out["aim_moves_total"] = {"parts": sum(r["parts"] for r in out["aim_moves"]),
                          "eur": round(sum(r["eur"] for r in out["aim_moves"]), 2)}

# ---- page input: the figure-key export (spine = master; release AIM where non-blank)
xn, xo = rd(X_NEW).set_index("part_number"), rd(X_OLD).set_index("part_number")
assert set(xn.index) == set(xo.index)
xo = xo.loc[xn.index]
lv = ["aim_level_1", "aim_level_2", "aim_level_3"]
mv = (xn[lv] != xo[lv]).any(axis=1)
na_old = xo.aim_level_1.str.strip().str.lower().isin(PH)
na_new = xn.aim_level_1.str.strip().str.lower().isin(PH)
xpn = list(xn.index.map(pad))
eur_x = pd.Series([L12.get(p, 0.0) for p in xpn], index=xn.index)
out["page_export"] = {
    "rows": len(xn),
    "pns_level_move": int(mv.sum()), "eur_level_move": round(float(eur_x[mv].sum()), 2),
    "other_columns_changed": {c: int((xn[c] != xo[c]).sum()) for c in xn.columns
                              if c not in lv and (xn[c] != xo[c]).any()},
    "not_classified_in_aim_parts": {"old": int(na_old.sum()), "new": int(na_new.sum())},
    "not_classified_in_aim_l12m_eur": {"old": round(float(eur_x[na_old].sum()), 2),
                                       "new": round(float(eur_x[na_new].sum()), 2)},
    "candidate_rows_not_in_export": sorted(kn - set(xn.index.map(pad)) - set(xn.index)),
}
pm = defaultdict(lambda: {"parts": 0, "eur": 0.0})
for pn in xn.index[mv]:
    k = f"{' > '.join(xo.loc[pn, lv])}  ->  {' > '.join(xn.loc[pn, lv])}"
    pm[k]["parts"] += 1
    pm[k]["eur"] += float(eur_x[pn])
out["page_export"]["moves"] = sorted([{"move": k, "parts": v["parts"], "eur": round(v["eur"], 2)}
                                      for k, v in pm.items()], key=lambda r: (-r["eur"], -r["parts"]))
OUT.write_text(json.dumps(out, indent=2, default=list), encoding="utf-8")
print(json.dumps({k: v for k, v in out.items() if k not in ("catalogue_moves", "aim_moves")}, indent=1, default=list)[:6000])
print("CATALOGUE MOVES")
for r in out["catalogue_moves"]:
    print(f"  {r['parts']:4d}  {r['eur']:>11,.2f}  {r['move']}  {r['groups']} {r['examples']}")
print("AIM MOVES")
for r in out["aim_moves"]:
    print(f"  {r['parts']:4d}  {r['eur']:>11,.2f}  {r['move']}  {r['groups']} {r['examples']}")

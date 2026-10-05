"""Diff classification release 2026-10-02 against the approved 2026-09-20 release and the live
overlay, at file level and at page-input (figure-key export) level. Read-only; writes only
_release_20261002_diff.json beside itself. Euro = the export's own l12m_billed_eur column, the
method the 1 Oct wiring agent used (window Jan 2025 - Jun 2026 despite the column name)."""
from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path

import pandas as pd

DER = Path(r"C:\Users\jerom\Desktop\claude\ISZE\01_data\00_derived")
REL = DER / "_releases"
NEW = REL / "aim_pn_classification_release_2026-10-02.csv"
APPR = REL / "aim_pn_classification_release_2026-09-20.csv"
OV = DER / "aim_pn_classification_20260920.csv"
X_NEW = DER / "AIM_Master_PN_Categories_Figkey_release_2026-10-02.csv"
X_APPR = DER / "AIM_Master_PN_Categories_Figkey_release_2026-09-20.csv"
X_LIVE = DER / "AIM_Master_PN_Categories_Figkey_20260924.csv"
LOG = REL / "aim_pn_classification_release_2026-10-02.changes.csv"
RESID = {"", "unknown", "unknown review"}


def rd(p):
    return pd.read_csv(p, dtype=str, keep_default_na=False, low_memory=False)


def file_diff(a: pd.DataFrame, b: pd.DataFrame) -> dict:
    ka, kb = set(a.part_number), set(b.part_number)
    ai, bi = a.set_index("part_number"), b.set_index("part_number")
    common = sorted(ka & kb)
    ai, bi = ai.loc[common], bi.loc[common]
    cols = {c: sorted(ai.index[ai[c] != bi[c]].tolist()) for c in ai.columns}
    return {"rows_a": len(a), "rows_b": len(b), "only_in_a": sorted(ka - kb),
            "only_in_b": sorted(kb - ka),
            "rows_changed_by_column": {c: len(v) for c, v in cols.items() if v},
            "pns_changed_by_column": {c: v for c, v in cols.items() if v and len(v) <= 40}}


def export_diff(new: pd.DataFrame, old: pd.DataFrame, reason_of) -> dict:
    n, o = new.set_index("part_number"), old.set_index("part_number")
    assert set(n.index) == set(o.index)
    o = o.loc[n.index]
    eur = pd.to_numeric(n["l12m_billed_eur"], errors="coerce").fillna(0.0)
    lv = ["aim_level_1", "aim_level_2", "aim_level_3"]
    moved = (n[lv] != o[lv]).any(axis=1)
    lk = n["line_kind"] != o["line_kind"]
    out = {"rows": len(n), "same_pn_set": True,
           "pns_level_move": int(moved.sum()),
           "eur_level_move": round(float(eur[moved].sum()), 2),
           "pns_line_kind_change": int(lk.sum()),
           "eur_line_kind_change": round(float(eur[lk].sum()), 2),
           "other_columns_changed": {c: int((n[c] != o[c]).sum()) for c in n.columns
                                     if c not in lv + ["line_kind"] and (n[c] != o[c]).any()}}
    groups = defaultdict(lambda: {"pns": 0, "eur": 0.0, "examples": []})
    direction = defaultdict(lambda: {"pns": 0, "eur": 0.0})
    for pn in n.index[moved | lk]:
        a = " > ".join(o.loc[pn, lv]); b = " > ".join(n.loc[pn, lv])
        r = reason_of(pn, o.loc[pn], n.loc[pn])
        g = groups[r]; g["pns"] += 1; g["eur"] += float(eur[pn])
        if len(g["examples"]) < 12:
            g["examples"].append({"pn": pn, "from": a, "to": b,
                                  "line_kind": f"{o.loc[pn,'line_kind']} -> {n.loc[pn,'line_kind']}",
                                  "eur": round(float(eur[pn]), 2)})
        if moved[pn]:
            fr = o.loc[pn, "aim_level_1"].strip().lower() in RESID
            to = n.loc[pn, "aim_level_1"].strip().lower() in RESID
            k = ("residual->named" if fr and not to else "named->residual" if to and not fr
                 else "named->named" if not fr else "residual->residual")
            direction[k]["pns"] += 1; direction[k]["eur"] += float(eur[pn])
    out["by_reason"] = {k: {**v, "eur": round(v["eur"], 2)} for k, v in groups.items()}
    out["by_direction"] = {k: {**v, "eur": round(v["eur"], 2)} for k, v in direction.items()}
    return out


def main():
    new, appr, ov = rd(NEW), rd(APPR), rd(OV)
    log = rd(LOG)
    logged = defaultdict(set)
    for _, r in log.iterrows():
        logged[r["part_number"]].add(r["reason"].split(":")[0])
    ov_i = ov.set_index("part_number"); ap_i = appr.set_index("part_number")
    aim = ["aim_l1_fixed", "aim_l2_fixed", "aim_l3_fixed"]
    post0920 = set(ov_i.index[(ov_i[aim] != ap_i.loc[ov_i.index, aim]).any(axis=1)])

    def reason_vs_live(pn, o, n):
        k = pn if pn in logged else pn
        rs = logged.get(pn) or logged.get(pn.zfill(10)) or set()
        if pn in ("8980554611", "8980554621"):
            return "Jerome decision 2: side sill -> Panels > Panel"
        if pn.lstrip("0").startswith("5500") and len(pn.lstrip("0")) == 9:
            return "lubricant: master's Fluids Chemicals fix and/or lubricant line_kind on the billed 9-digit key"
        return "UNEXPLAINED: " + "; ".join(sorted(rs))

    def reason_vs_appr(pn, o, n):
        r = reason_vs_live(pn, o, n)
        if not r.startswith("UNEXPLAINED"):
            return r
        if pn in post0920:
            src = ov_i.loc[pn, "aim_source"]
            return f"post-20-Sep AIM work in the live overlay ({src.split('|')[-1]})"
        return "UNEXPLAINED"

    res = {
        "file_new_vs_approved_0920": file_diff(new, appr),
        "file_new_vs_live_overlay": file_diff(new, ov),
        "export_new_vs_live_page_input_20260924": export_diff(rd(X_NEW), rd(X_LIVE), reason_vs_live),
        "export_new_vs_approved_0920_export": export_diff(rd(X_NEW), rd(X_APPR), reason_vs_appr),
    }
    out = Path(__file__).with_name("_release_20261002_diff.json")
    out.write_text(json.dumps(res, indent=1), encoding="utf-8")
    for k, v in res.items():
        print("==", k)
        print(json.dumps({x: y for x, y in v.items() if x not in ("pns_changed_by_column",)},
                         indent=1)[:6000])
    print("->", out)


if __name__ == "__main__":
    main()

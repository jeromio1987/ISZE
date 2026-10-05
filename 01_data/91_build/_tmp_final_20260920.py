# -*- coding: utf-8 -*-
"""
FINAL consolidated measurement for the price-class concentration question.

Reads (read-only): spine, jp code cache, the CD distribution JSON, the CD ZKK JSON.
Writes: 01_data/90_INBOX/_tmp_final_20260920.json   (for review before the JSON repair)
"""
from __future__ import annotations

import collections
import csv
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SPINE = ROOT / "01_data" / "00_derived" / "aim_master_v2.csv"
CACHE = ROOT / "01_data" / "00_derived" / "jp_codes_cache_20260920.csv"
CD_DIST = ROOT / "01_data" / "90_INBOX" / "_tmp_price_cd_class_dist_20260920.json"
CD_ZKK = ROOT / "01_data" / "90_INBOX" / "_tmp_zkk_class_from_cd_20260920.json"
OUT = ROOT / "01_data" / "90_INBOX" / "_tmp_final_20260920.json"


def s(v) -> str:
    if v is None:
        return ""
    t = str(v).strip()
    return t[:-2] if t.endswith(".0") else t


def noun(desc: str) -> str:
    d = (desc or "").upper().strip()
    return re.split(r"[;,(]", d)[0].strip()


def main() -> int:
    # --- spine ---
    spine = {}
    total_eur = 0.0
    with SPINE.open(encoding="utf-8", newline="") as fh:
        for r in csv.DictReader(fh):
            pn = s(r.get("part_number"))
            spine[pn] = {
                "eur": float(r.get("l12m_billed_eur") or 0),
                "iml": s(r.get("price_class_iml")),
                "zkk": s(r.get("jp_zkk")),
                "jc": s(r.get("jp_class_new")),
                "l1": s(r.get("aim_l1_fixed")) or s(r.get("aim_l1")),
            }
            total_eur += spine[pn]["eur"]
    base = [p for p, v in spine.items() if v["zkk"]]
    base_eur = sum(spine[p]["eur"] for p in base)

    # --- cache: pn -> (zkk, jp_description) ---
    pn_zkk, pn_desc = {}, {}
    with CACHE.open(encoding="utf-8", newline="") as fh:
        for r in csv.DictReader(fh):
            pn_zkk[r["pn"]] = r["zkk"]
            pn_desc[r["pn"]] = r.get("jp_description", "")

    # --- Part A basis 2 and 3 ---
    def dist(keyfn, filt=None):
        pns = collections.Counter()
        eur = collections.defaultdict(float)
        for pn in base:
            v = spine[pn]
            if filt and not filt(v):
                continue
            k = keyfn(v) or "(blank)"
            pns[k] += 1
            eur[k] += v["eur"]
        return pns, eur

    # A.2 price_class_iml over the WHOLE spine (all rows), and over the base
    all_pns = collections.Counter()
    all_eur = collections.defaultdict(float)
    for pn, v in spine.items():
        k = v["iml"] or "(blank)"
        all_pns[k] += 1
        all_eur[k] += v["eur"]

    def table(pns, eur, denom_eur=None, denom_pns=None):
        te = denom_eur if denom_eur is not None else sum(eur.values())
        tp = denom_pns if denom_pns is not None else sum(pns.values())
        return [{"code": k, "pns": pns[k], "eur": round(eur[k], 2),
                 "pct_eur_of_priced": round(100 * eur[k] / te, 3),
                 "pct_pns_of_priced": round(100 * pns[k] / tp, 3)}
                for k in sorted(eur, key=lambda x: -eur[x])]

    priced_eur = sum(v for k, v in all_eur.items() if k != "(blank)")
    priced_pns = sum(v for k, v in all_pns.items() if k != "(blank)")
    a2 = {
        "basis": "01_data/00_derived/aim_master_v2.csv column price_class_iml, weighted by l12m_billed_eur",
        "distribution_whole_spine": table(all_pns, all_eur),
        "distribution_whole_spine_pct_of_priced_only": table(
            all_pns, all_eur, denom_eur=priced_eur, denom_pns=priced_pns),
        "priced_eur": round(priced_eur, 2),
        "priced_pns": priced_pns,
        "blank_eur": round(all_eur.get("(blank)", 0.0), 2),
        "blank_pns": all_pns.get("(blank)", 0),
        "codes_ge_0p5pct_priced": sum(
            1 for k in all_eur if k != "(blank)" and all_eur[k] / priced_eur >= 0.005),
        "codes_ge_1pct_priced": sum(
            1 for k in all_eur if k != "(blank)" and all_eur[k] / priced_eur >= 0.01),
    }

    bp, be = dist(lambda v: v["jc"], filt=lambda v: bool(v["zkk"]))
    a3 = {
        "basis": ("01_data/00_derived/aim_master_v2.csv filtered to rows with a non-blank jp_zkk, "
                  "column jp_class_new, weighted by l12m_billed_eur"),
        "distribution": table(bp, be),
        "codes_ge_0p5pct": sum(1 for k in be if be[k] / sum(be.values()) >= 0.005),
        "codes_ge_1pct": sum(1 for k in be if be[k] / sum(be.values()) >= 0.01),
        "rows": sum(bp.values()),
        "eur": round(sum(be.values()), 2),
    }

    # --- ZKK leading nouns, and inside class C ---
    zkk_eur, zkk_pns = collections.Counter(), collections.Counter()
    zkk_cls = collections.defaultdict(collections.Counter)
    zkk_cls_eur = collections.defaultdict(collections.Counter)
    zkk_noun_all = collections.defaultdict(collections.Counter)
    zkk_noun_c = collections.defaultdict(collections.Counter)
    zkk_iml_in_c = collections.defaultdict(set)
    for pn in base:
        v = spine[pn]
        z = v["zkk"]
        zkk_eur[z] += v["eur"]
        zkk_pns[z] += 1
        cls = v["iml"] or "(blank)"
        zkk_cls[z][cls] += 1
        zkk_cls_eur[z][cls] += v["eur"]
        if z == pn_zkk.get(pn, ""):
            n = noun(pn_desc.get(pn, ""))
            if n:
                zkk_noun_all[z][n] += 1
                if cls == "C":
                    zkk_noun_c[z][n] += 1
        if cls == "C":
            zkk_iml_in_c[z].add(pn)

    # spine: ZKK codes appearing under exactly one ISZE class (non-blank)
    single_iml = []
    for z in zkk_eur:
        classes = {c for c in zkk_cls_eur[z] if c != "(blank)"}
        if len(classes) == 1:
            single_iml.append(z)

    c_codes = sorted(zkk_iml_in_c, key=lambda z: -zkk_cls_eur[z]["C"])
    zkk_in_c = []
    for z in c_codes:
        n = zkk_noun_all[z].most_common(1)
        nc = zkk_noun_c[z].most_common(1)
        zkk_in_c.append({
            "zkk": z,
            "eur_total": round(zkk_eur[z], 2),
            "eur_in_C": round(zkk_cls_eur[z]["C"], 2),
            "share_of_zkk_in_C_pct": (round(100 * zkk_cls_eur[z]["C"] / zkk_eur[z], 1)
                                      if zkk_eur[z] else 0.0),
            "classes_spanned": len([c for c in zkk_cls_eur[z] if c != "(blank)"]),
            "class_split_eur": {k: round(v, 2) for k, v in zkk_cls_eur[z].most_common()},
            "lead_noun_all": n[0][0] if n else "",
            "lead_noun_all_pct": round(100 * n[0][1] / zkk_pns[z], 1) if n else 0.0,
            "lead_noun_in_C": nc[0][0] if nc else "",
        })

    # --- CD results ---
    cd = json.loads(CD_DIST.read_text(encoding="utf-8"))
    cdz = json.loads(CD_ZKK.read_text(encoding="utf-8"))
    ncd = cd["rows_with_pn"]
    newc = cd["new_part_class"]
    # naive last-letter collapse on the CD codes, and the measured collapse
    naive = collections.Counter()
    for c, v in newc.items():
        naive["(blank)" if c == "(blank)" else c[-1]] += v
    measured = collections.Counter()
    mapping = json.loads(
        (ROOT / "01_data" / "90_INBOX" / "_tmp_consolidated_20260920.json")
        .read_text(encoding="utf-8"))["measured_jp_to_iml_mapping"]
    unmapped = collections.Counter()
    for c, v in newc.items():
        m = mapping.get(c)
        if m:
            measured[m["dominant_class"]] += v
        else:
            unmapped[c] += v

    def as_table(cnt, denom):
        return [{"code": k, "rows": v, "pct": round(100 * v / denom, 3)}
                for k, v in cnt.most_common()]

    a1 = {
        "source": cd["source_file"],
        "sheet": cd["sheet"],
        "rows": ncd,
        "new_part_class_raw": as_table(collections.Counter(newc), ncd),
        "new_part_class_naive_last_letter": as_table(naive, ncd),
        "new_part_class_measured_collapse": as_table(measured, ncd),
        "unmapped_codes": dict(unmapped),
        "collapse_rule": "measured from the spine join: the Japan two-letter code's dominant ISZE "
                         "price_class_iml by EUR",
        "mapping_evidence": mapping,
        "c_share_all_rows_pct": round(100 * measured.get("C", 0) / ncd, 3),
        "c_share_of_classed_rows_pct": round(
            100 * measured.get("C", 0) / (ncd - (newc.get("(blank)") or 0)), 3),
        "codes_ge_1pct_measured": sum(
            1 for k, v in measured.items() if k != "(blank)" and v / ncd >= 0.01),
        "codes_ge_1pct_naive": sum(
            1 for k, v in naive.items() if k != "(blank)" and v / ncd >= 0.01),
    }

    zkk_cd = {
        "rows": cdz["rows_with_pn"],
        "zkk_total": cdz["zkk_codes_total"],
        "zkk_with_exactly_one_class": cdz["zkk_codes_with_exactly_one_class"],
        "zkk_with_exactly_one_class_list": cdz["zkk_codes_with_exactly_one_class_list"],
        "zkk_per_collapsed_class": {k: len(v) for k, v in
                                    cdz["zkk_codes_per_collapsed_class"].items()},
        "top_zkk": [
            {"zkk": x["zkk"], "rows": x["rows"],
             "distinct_classes": x["distinct_new_part_class"],
             "dominant_class": x["dominant_class"],
             "dominant_share_pct": x["dominant_share_pct"]}
            for x in cdz["zkk_report"][:12]
        ],
    }
    zkk_spine = {
        "zkk_total": len(zkk_eur),
        "zkk_with_exactly_one_iml_class": len(single_iml),
        "zkk_with_exactly_one_iml_class_list": sorted(single_iml),
        "zkk_codes_appearing_in_class_C": len(zkk_iml_in_c),
        "zkk_codes_appearing_per_class": {
            c: sum(1 for z in zkk_eur if any(x == c for x in zkk_cls_eur[z]))
            for c in ("C", "V", "D", "F", "M", "P", "J", "T")
        },
        "zkk_ranked_in_class_C": zkk_in_c,
    }

    out = {
        "book_l12m_eur": round(total_eur, 2),
        "common_base": {"pns": len(base), "eur": round(base_eur, 2)},
        "A1_japan_cd_rows": a1,
        "A2_spine_iml_eur": a2,
        "A3_spine_jpclass_new_eur": a3,
        "zkk_from_cd": zkk_cd,
        "zkk_from_spine": zkk_spine,
        "zkk_leading_noun_all_top": {
            z: zkk_noun_all[z].most_common(3)
            for z in sorted(zkk_eur, key=lambda x: -zkk_eur[x])[:12]
        },
    }
    OUT.write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8")

    print(f"book EUR {total_eur:,.2f}")
    print("\n=== A.1 CD rows, measured collapse ===")
    for x in a1["new_part_class_measured_collapse"]:
        print(f"   {x['code']:<8} {x['rows']:>8} {x['pct']:>7.3f}%")
    print(f"   unmapped: {a1['unmapped_codes']}")
    print(f"   C of all rows {a1['c_share_all_rows_pct']}%   "
          f"of classed rows {a1['c_share_of_classed_rows_pct']}%")
    print(f"   codes >=1% (measured collapse) {a1['codes_ge_1pct_measured']}   "
          f"(naive last letter) {a1['codes_ge_1pct_naive']}")
    print("\n=== A.2 spine price_class_iml, EUR, whole book ===")
    for x in a2["distribution_whole_spine"]:
        print(f"   {x['code']:<8} {x['pns']:>7}  EUR {x['eur']:>15,.2f} "
              f"{x['pct_eur_of_priced']:>7.3f}%  (pns {x['pct_pns_of_priced']:>6.2f}%)")
    print(f"   priced EUR {a2['priced_eur']:,.2f}  blank EUR {a2['blank_eur']:,.2f} "
          f"({100*a2['blank_eur']/total_eur:.2f}% of book)")
    print(f"   codes >=1% of priced: {a2['codes_ge_1pct_priced']}")
    print("\n=== A.3 spine jp_class_new, EUR, ZKK rows ===")
    for x in a3["distribution"]:
        print(f"   {x['code']:<8} {x['pns']:>7}  EUR {x['eur']:>15,.2f} {x['pct_eur_of_priced']:>7.3f}%")
    print(f"   codes >=1%: {a3['codes_ge_1pct']}   >=0.5%: {a3['codes_ge_0p5pct']}")
    print("\n=== ZKK vs class ===")
    print(f"   CD : ZKK total {zkk_cd['zkk_total']}, exactly one class {zkk_cd['zkk_with_exactly_one_class']}")
    print(f"   CD : ZKK per collapsed class {zkk_cd['zkk_per_collapsed_class']}")
    print(f"   spine: ZKK total {zkk_spine['zkk_total']}, exactly one class "
          f"{zkk_spine['zkk_with_exactly_one_iml_class']}")
    print(f"   spine: ZKK codes appearing in class C {zkk_spine['zkk_codes_appearing_in_class_C']}")
    print(f"   spine: ZKK per class {zkk_spine['zkk_codes_appearing_per_class']}")
    print("\n   largest ZKK codes inside class C:")
    for x in zkk_spine["zkk_ranked_in_class_C"][:10]:
        print(f"      {x['zkk']:<6} EUR {x['eur_total']:>14,.2f}  inC {x['eur_in_C']:>14,.2f} "
              f"({x['share_of_zkk_in_C_pct']:>5.1f}%) classes {x['classes_spanned']:>2} "
              f"noun '{x['lead_noun_all']}' ({x['lead_noun_all_pct']}%)")
    print("\n   top ZKK leading nouns (Japan parts name):")
    for z, n in out["zkk_leading_noun_all_top"].items():
        print(f"      {z:<6} EUR {zkk_eur[z]:>14,.2f}  {n}")
    print(f"\n-> {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

# -*- coding: utf-8 -*-
"""
ZKK vs AIM — measured on the review pack's own L12 billing population.

Read-only. Nothing is rebuilt, nothing is overwritten. This runs the head-to-head that
the pack (01_PROMPT_FOR_NEXT_MODEL.md) declares cannot be run, because it reports that no
ZKK or AIM mapping exists in the package. Both mappings exist on the ISZE spine
(01_data/00_derived/aim_master_v2.csv) and 99.76% of the pack's part numbers join to it.

Outputs (new files only):
  01_data/90_INBOX/_zkk_vs_aim_pack_population_20260920.json
  01_data/90_INBOX/_zkk_vs_aim_pack_population_20260920.csv

Run: python 01_data/91_build/zkk_vs_aim_pack_population_20260920.py
"""
from __future__ import annotations

import collections
import csv
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SPINE = ROOT / "01_data" / "00_derived" / "aim_master_v2.csv"
PACK = (ROOT / "ISZE_ZKK_AIM_Independent_Review_Pack"
        / "ISZE_ZKK_AIM_Independent_Review_Pack" / "comparison_data"
        / "billing_L12_vs_previous_by_distributor_part.csv")
OUT_JSON = ROOT / "01_data" / "90_INBOX" / "_zkk_vs_aim_pack_population_20260920.json"
OUT_CSV = ROOT / "01_data" / "90_INBOX" / "_zkk_vs_aim_pack_population_20260920.csv"


def s(v) -> str:
    if v is None:
        return ""
    t = str(v).strip()
    return t[:-2] if t.endswith(".0") else t


def leading_noun(desc: str) -> str:
    d = (desc or "").upper().strip()
    d = re.split(r"[;,(]", d)[0].strip()
    return d


def main() -> int:
    # ---------- 1. the classification spine ----------
    spine: dict[str, dict] = {}
    with SPINE.open(encoding="utf-8", newline="") as fh:
        for r in csv.DictReader(fh):
            pn = s(r.get("part_number"))
            if not pn:
                continue
            spine[pn] = {
                "zkk": s(r.get("jp_zkk")),
                "aim1": s(r.get("aim_l1_fixed")) or s(r.get("aim_l1")),
                "aim2": s(r.get("aim_l2_fixed")) or s(r.get("aim_l2")),
                "aim3": s(r.get("aim_l3")),
                "cls": s(r.get("price_class_iml")),
                "desc": s(r.get("description")),
            }
    print(f"spine: {len(spine):,} part numbers")

    # ---------- 2. the pack's own L12 population ----------
    # One row per distributor x part, two periods. Join on part number (the pack is
    # distributor-agnostic for classification: a part carries one classification).
    cur: dict[str, float] = collections.defaultdict(float)
    prev: dict[str, float] = collections.defaultdict(float)
    cur_qty: dict[str, float] = collections.defaultdict(float)
    dist_of: dict[str, set] = collections.defaultdict(set)
    pack_pns: set[str] = set()
    with PACK.open(encoding="utf-8", newline="") as fh:
        for r in csv.DictReader(fh):
            pn = s(r["part_number"])
            pack_pns.add(pn)
            cur[pn] += float(r["current_l12_parts_billed_eur"] or 0)
            prev[pn] += float(r["previous_l12_parts_billed_eur"] or 0)
            cur_qty[pn] += float(r["current_l12_billed_qty"] or 0)
            dist_of[pn].add(r["distributor_code"])

    tot_cur = sum(cur.values())
    tot_prev = sum(prev.values())
    print(f"pack: {len(pack_pns):,} part numbers, dist-part rows loaded")
    print(f"pack L12      EUR {tot_cur:,.2f}")
    print(f"pack prev L12 EUR {tot_prev:,.2f}")

    joined = {p for p in pack_pns if p in spine}
    unmatched = pack_pns - joined
    un_eur = sum(cur[p] for p in unmatched)
    print(f"joined to spine: {len(joined):,} = {100*len(joined)/len(pack_pns):.2f}% of parts, "
          f"EUR {un_eur:,.2f} = {100*un_eur/tot_cur:.2f}% of L12 euro unjoined")

    # ---------- 3. system definitions, on the SAME rows ----------
    def zkk(pn):
        return spine[pn]["zkk"]

    def aim1(pn):
        return spine[pn]["aim1"]

    def aim2(pn):
        return spine[pn]["aim2"]

    def aim_triple(pn):
        v = spine[pn]
        return f'{v["aim1"]} > {v["aim2"]} > {v["aim3"]}' if v["aim1"] else ""

    SYSTEMS = {
        "ZKK (Japan catalogue)": zkk,
        "AIM L1": aim1,
        "AIM L2": aim2,
        "AIM L1>L2>L3": aim_triple,
    }

    def measure(label, fn):
        eur_by_code: dict[str, float] = collections.defaultdict(float)
        pns_by_code: dict[str, int] = collections.defaultdict(int)
        labelled_eur = 0.0
        labelled_pns = 0
        for pn in pack_pns:
            code = fn(pn) if pn in spine else ""
            code = (code or "").strip()
            if not code:
                continue
            e = cur[pn]
            labelled_eur += e
            labelled_pns += 1
            eur_by_code[code] += e
            pns_by_code[code] += 1
        if labelled_eur <= 0:
            return None
        ranked = sorted(eur_by_code.items(), key=lambda kv: -kv[1])
        shares = [v / labelled_eur for _, v in ranked]
        return {
            "system": label,
            "codes_used": len(eur_by_code),
            "labelled_pns": labelled_pns,
            "pn_coverage_pct": round(100 * labelled_pns / len(pack_pns), 2),
            "labelled_eur": round(labelled_eur, 2),
            "eur_coverage_pct": round(100 * labelled_eur / tot_cur, 2),
            "unlabelled_eur": round(tot_cur - labelled_eur, 2),
            "codes_ge_0p5pct": sum(1 for x in shares if x >= 0.005),
            "codes_ge_1pct": sum(1 for x in shares if x >= 0.01),
            "max_code": ranked[0][0],
            "max_code_share_pct": round(100 * shares[0], 2),
            "top5_share_pct": round(100 * sum(shares[:5]), 2),
            "top10_share_pct": round(100 * sum(shares[:10]), 2),
            "top_codes": [
                {"code": k, "pns": pns_by_code[k], "eur": round(v, 2),
                 "pct_of_labelled": round(100 * v / labelled_eur, 2),
                 "pct_of_book": round(100 * v / tot_cur, 2)}
                for k, v in ranked[:15]
            ],
        }

    results = {}
    for label, fn in SYSTEMS.items():
        r = measure(label, fn)
        if r:
            results[label] = r

    # ---------- 4. the fair test the pack's own basket column cannot do ----------
    # Define a service basket WITHOUT using either system, then ask each system to isolate it.
    # The pack warns that the previous workbook's basket column defined the basket from AIM,
    # which makes AIM score 100% by construction. This basket is defined from the part
    # description text and catalogue figure key only, so neither system is privileged.
    BASKET_RULES = {
        "Filters": r"\b(FILTER|ELEMENT)\b",
        "Brake friction": r"\b(BRAKE|PAD|LINING|SHOE)\b",
        "Clutch": r"\b(CLUTCH|DISC ASSY|PRESSURE PLATE)\b",
    }
    basket_eur: dict[str, float] = collections.defaultdict(float)
    basket_pns: dict[str, int] = collections.defaultdict(int)
    for pn in pack_pns:
        if pn not in spine:
            continue
        txt = f"{spine[pn]['desc']}".upper()
        if not txt:
            continue
        for name, pat in BASKET_RULES.items():
            if re.search(pat, txt):
                basket_eur[name] += cur[pn]
                basket_pns[name] += 1
    # descriptions are blank on the spine for most rows, so also try the pack's own label file
    LABELS = (ROOT / "ISZE_ZKK_AIM_Independent_Review_Pack"
              / "ISZE_ZKK_AIM_Independent_Review_Pack" / "comparison_data"
              / "part_reference_labels_NOT_ZKK_OR_AIM.csv")
    lab: dict[str, str] = {}
    if LABELS.exists():
        with LABELS.open(encoding="utf-8", newline="") as fh:
            rd = csv.DictReader(fh)
            dcol = next((c for c in rd.fieldnames if "desc" in c.lower()), None)
            for r in rd:
                pn = s(r.get("part_number") or r.get("part_no") or "")
                if pn and dcol:
                    lab[pn] = r[dcol]
    print(f"pack part labels loaded: {len(lab):,}")

    basket2_eur: dict[str, float] = collections.defaultdict(float)
    basket2_pns: dict[str, int] = collections.defaultdict(int)
    for pn, d in lab.items():
        txt = (d or "").upper()
        if not txt or pn not in pack_pns:
            continue
        for name, pat in BASKET_RULES.items():
            if re.search(pat, txt):
                basket2_eur[name] += cur[pn]
                basket2_pns[name] += 1

    # isolation quality: share of the labelled euro that lands in the single best code
    def isolation(fn, basket: set[str]) -> dict:
        by_code: dict[str, float] = collections.defaultdict(float)
        tot = 0.0
        for pn in basket:
            if pn not in spine:
                continue
            code = (fn(pn) or "").strip()
            if not code:
                continue
            by_code[code] += cur[pn]
            tot += cur[pn]
        if not by_code or tot <= 0:
            return {"basket_eur": round(tot, 2), "covered_eur": 0.0,
                    "top_code": "", "top_code_share_pct": 0.0, "codes_holding_80pct": None}
        ranked = sorted(by_code.items(), key=lambda kv: -kv[1])
        cum = 0.0
        n80 = 0
        for _, v in ranked:
            cum += v
            n80 += 1
            if cum / tot >= 0.80:
                break
        return {
            "basket_eur": round(tot, 2),
            "covered_eur": round(sum(by_code.values()), 2),
            "top_code": ranked[0][0],
            "top_code_share_pct": round(100 * ranked[0][1] / tot, 2),
            "codes_holding_80pct": n80,
            "codes_used": len(by_code),
        }

    # basket membership by pack label (all pack PNs that carry a label)
    baskets = {}
    for name in BASKET_RULES:
        members = {pn for pn, d in lab.items()
                   if pn in pack_pns and re.search(BASKET_RULES[name], (d or "").upper())}
        if not members:
            continue
        eur = sum(cur[p] for p in members)
        baskets[name] = {
            "pns": len(members),
            "eur": round(eur, 2),
            "pct_of_book": round(100 * eur / tot_cur, 2),
            "systems": {lbl: isolation(fn, members) for lbl, fn in SYSTEMS.items()},
        }

    # ---------- 5. EUR-weighted crosswalk ZKK x AIM L1 ----------
    xwalk: dict[str, dict[str, float]] = collections.defaultdict(lambda: collections.defaultdict(float))
    for pn in pack_pns:
        if pn not in spine:
            continue
        z = spine[pn]["zkk"]
        a = spine[pn]["aim1"]
        if z and a:
            xwalk[z][a] += cur[pn]
    xwalk_out = {}
    for z, fams in sorted(xwalk.items(), key=lambda kv: -sum(kv[1].values()))[:20]:
        tot = sum(fams.values())
        top = sorted(fams.items(), key=lambda kv: -kv[1])[:6]
        xwalk_out[z] = {
            "eur": round(tot, 2),
            "aim_families": len(fams),
            "top_families": [{"aim": k, "eur": round(v, 2),
                              "pct_of_code": round(100 * v / tot, 2)} for k, v in top],
        }

    # ---------- 6. write ----------
    payload = {
        "purpose": "ZKK vs AIM measured on the review pack's own L12 population",
        "population": {
            "source": str(PACK.relative_to(ROOT)),
            "distributor_part_rows": None,
            "distinct_part_numbers": len(pack_pns),
            "l12_eur": round(tot_cur, 2),
            "previous_l12_eur": round(tot_prev, 2),
            "l12_joined_to_spine_pct_parts": round(100 * len(joined) / len(pack_pns), 2),
            "l12_unjoined_eur": round(un_eur, 2),
            "l12_unjoined_pct_eur": round(100 * un_eur / tot_cur, 2),
        },
        "systems": results,
        "basket_isolation_description_joined": baskets,
        "crosswalk_zkk_to_aim_l1": xwalk_out,
    }
    OUT_JSON.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")

    with OUT_CSV.open("w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["system", "code", "pns", "eur", "pct_of_labelled", "pct_of_book"])
        for label, r in results.items():
            for c in r["top_codes"]:
                w.writerow([label, c["code"], c["pns"], c["eur"],
                            c["pct_of_labelled"], c["pct_of_book"]])

    # ---------- print ----------
    print()
    print(f"{'system':<26} {'codes':>6} {'>=1%':>5} {'max%':>7} {'top10%':>7} "
          f"{'EURcov':>7} {'unlab EUR':>12}")
    print("-" * 80)
    for label, r in sorted(results.items(), key=lambda kv: -kv[1]["eur_coverage_pct"]):
        print(f"{label:<26} {r['codes_used']:>6} {r['codes_ge_1pct']:>5} "
              f"{r['max_code_share_pct']:>7.2f} {r['top10_share_pct']:>7.2f} "
              f"{r['eur_coverage_pct']:>6.2f}% {r['unlabelled_eur']:>12,.0f}")
    print()
    for name, b in baskets.items():
        print(f"basket {name}: {b['pns']:,} PNs, EUR {b['eur']:,.0f} ({b['pct_of_book']:.2f}% of book)")
        for lbl, iso in b["systems"].items():
            print(f"    {lbl:<26} top code {iso['top_code']:<9} "
                  f"{iso['top_code_share_pct']:>6.2f}% of basket  "
                  f"{iso['codes_holding_80pct']} codes to reach 80%")
    print()
    print(f"-> {OUT_JSON.name}")
    print(f"-> {OUT_CSV.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

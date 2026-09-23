# -*- coding: utf-8 -*-
"""
ZKK vs AIM — framework-based classification review.

Measures every criterion in the review pack's own comparison framework
(02_COMPARISON_FRAMEWORK.md), on identical rows for every system.

Read-only against the spine and the pack. Writes two new files only:
  01_data/90_INBOX/_classification_framework_review_20260920.json
  01_data/90_INBOX/_classification_framework_review_20260920.csv

Bases
  full_book    the whole ISZE billed book on the spine      (165,213 PNs)
  common_base  PNs that carry a ZKK code, both systems can label (fair head-to-head)
  pack_L12     the review pack's own L12 population         (20,639 PNs)

Systems
  Japan   ZKK, ZUK, HKK, figure-key prefix, price class
  ISZE    AIM L1, AIM L2, AIM L1>L2>L3

Run: python 01_data/91_build/classification_framework_review_20260920.py
"""
from __future__ import annotations

import collections
import csv
import json
import math
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SPINE = ROOT / "01_data" / "00_derived" / "aim_master_v2.csv"
CACHE = ROOT / "01_data" / "00_derived" / "jp_codes_cache_20260920.csv"
AIM_V2 = ROOT / "01_data" / "00_derived" / "aim_pn_classification_v2.csv"
AIM_NOW = ROOT / "01_data" / "00_derived" / "aim_pn_classification_20260920.csv"
PACKDIR = (ROOT / "ISZE_ZKK_AIM_Independent_Review_Pack"
           / "ISZE_ZKK_AIM_Independent_Review_Pack")
PACKPAIR = PACKDIR / "comparison_data" / "billing_L12_vs_previous_by_distributor_part.csv"
PACKLAB = PACKDIR / "comparison_data" / "part_reference_labels_NOT_ZKK_OR_AIM.csv"
OUT_JSON = ROOT / "01_data" / "90_INBOX" / "_classification_framework_review_20260920.json"
OUT_CSV = ROOT / "01_data" / "90_INBOX" / "_classification_framework_review_20260920.csv"

JUDGEABLE_PNS = 200      # a code is judgeable at this many part numbers (matches the ZKK dictionary)
COHERENT_SHARE = 0.40    # dominant part type at or above this = coherent


def s(v) -> str:
    if v is None:
        return ""
    t = str(v).strip()
    return t[:-2] if t.endswith(".0") else t


def leading_noun(desc: str) -> str:
    d = (desc or "").upper().strip()
    d = re.split(r"[;,(]", d)[0].strip()
    return d


def numeric_pn(pn: str) -> bool:
    return bool(re.fullmatch(r"[0-9]+", (pn or "").strip()))


# ----------------------------------------------------------------------------- load
def load_spine():
    rows = {}
    with SPINE.open(encoding="utf-8", newline="") as fh:
        for r in csv.DictReader(fh):
            pn = s(r.get("part_number"))
            if not pn:
                continue
            fig = s(r.get("jp_fig_key")) or s(r.get("fig_key"))
            rows[pn] = {
                "eur": float(r.get("l12m_billed_eur") or 0),
                "zkk": s(r.get("jp_zkk")),
                "zuk": s(r.get("jp_zuk")),
                "hkk": s(r.get("jp_hkk")),
                "fig3": fig[:3] if len(fig) >= 3 else "",
                "cls": s(r.get("price_class_iml")),
                "aim1": s(r.get("aim_l1_fixed")) or s(r.get("aim_l1")),
                "aim2": s(r.get("aim_l2_fixed")) or s(r.get("aim_l2")),
                "aim3": s(r.get("aim_l3")),
                "aimsrc": s(r.get("aim_source")),
            }
    return rows


def load_cache():
    out = {}
    with CACHE.open(encoding="utf-8", newline="") as fh:
        for r in csv.DictReader(fh):
            pn = s(r.get("pn"))
            if pn:
                out[pn] = r.get("jp_description") or ""
    return out


def load_pack():
    cur, prev, qty = (collections.defaultdict(float) for _ in range(3))
    dists = collections.defaultdict(set)
    with PACKPAIR.open(encoding="utf-8", newline="") as fh:
        for r in csv.DictReader(fh):
            pn = s(r["part_number"])
            cur[pn] += float(r["current_l12_parts_billed_eur"] or 0)
            prev[pn] += float(r["previous_l12_parts_billed_eur"] or 0)
            qty[pn] += float(r["current_l12_billed_qty"] or 0)
            dists[pn].add(r["distributor_code"])
    return cur, prev, qty, dists


def load_labels():
    out = {}
    with PACKLAB.open(encoding="utf-8", newline="") as fh:
        for r in csv.DictReader(fh):
            out[s(r["part_number"])] = r.get("representative_billed_description") or ""
    return out


# ----------------------------------------------------------------------------- main
def main() -> int:
    spine = load_spine()
    cache = load_cache()
    cur, prev, qty, dists = load_pack()
    label = load_labels()
    print(f"spine {len(spine):,} PNs | jp cache {len(cache):,} | pack {len(cur):,} PNs "
          f"| labels {len(label):,}")

    total_book = sum(v["eur"] for v in spine.values())
    print(f"full billed book EUR {total_book:,.2f}")

    def desc(pn: str) -> str:
        return cache.get(pn) or label.get(pn) or ""

    def cell(p, key):
        """Spine value, or '' for the handful of pack parts the spine does not carry."""
        v = spine.get(p)
        return v[key] if v else ""

    SYSTEMS = {
        "ZKK (Japan, 3 char)":        lambda p: cell(p, "zkk"),
        "ZUK (Japan, 5 char)":        lambda p: cell(p, "zuk"),
        "HKK (Japan, 4 char)":        lambda p: cell(p, "hkk"),
        "Figure key prefix (Japan)":  lambda p: cell(p, "fig3"),
        "Price class (Japan/ours)":   lambda p: cell(p, "cls"),
        "AIM L1":                     lambda p: cell(p, "aim1"),
        "AIM L2":                     lambda p: cell(p, "aim2"),
        "AIM L1>L2>L3":               lambda p: (
            f'{cell(p, "aim1")} > {cell(p, "aim2")} > {cell(p, "aim3")}'
            if cell(p, "aim1") else ""),
    }

    common_base = {p for p in spine if spine[p]["zkk"]}
    pack_pns = set(cur)

    # ---------------- 1. coverage, separating the three kinds of missing -------------
    def coverage(fn, pops):
        out = {}
        for name, pns in pops.items():
            lab, lab_eur, unlab_eur = 0, 0.0, 0.0
            for p in pns:
                e = spine[p]["eur"] if name != "pack_L12" else cur[p]
                if (fn(p) or "").strip():
                    lab += 1
                    lab_eur += e
                else:
                    unlab_eur += e
            tot = sum((spine[p]["eur"] if name != "pack_L12" else cur[p]) for p in pns)
            out[name] = {
                "pns": len(pns), "labelled_pns": lab,
                "pn_coverage_pct": round(100 * lab / len(pns), 2) if pns else 0,
                "book_eur": round(tot, 2), "labelled_eur": round(lab_eur, 2),
                "eur_coverage_pct": round(100 * lab_eur / tot, 2) if tot else 0,
                "unlabelled_eur": round(unlab_eur, 2),
            }
        return out

    pops = {"full_book": set(spine), "common_base": common_base, "pack_L12": pack_pns}
    cov = {k: coverage(f, pops) for k, f in SYSTEMS.items()}

    # the three kinds of missing, separated (framework: unknown vs not applicable vs unresolved)
    gap_detail = {}
    for k, f in SYSTEMS.items():
        miss = [p for p in spine if not (f(p) or "").strip()]
        admin = [p for p in miss if not numeric_pn(p)]
        part = [p for p in miss if numeric_pn(p)]
        not_in_source = [p for p in part if p not in cache]
        unresolved = [p for p in part if p in cache]
        gap_detail[k] = {
            "missing_pns": len(miss),
            "missing_eur": round(sum(spine[p]["eur"] for p in miss), 2),
            "administrative_lines_pns": len(admin),
            "administrative_lines_eur": round(sum(spine[p]["eur"] for p in admin), 2),
            "parts_not_in_jp_source_pns": len(not_in_source),
            "parts_not_in_jp_source_eur": round(sum(spine[p]["eur"] for p in not_in_source), 2),
            "genuinely_unresolved_pns": len(unresolved),
            "genuinely_unresolved_eur": round(sum(spine[p]["eur"] for p in unresolved), 2),
        }

    # ---------------- 2. granularity / concentration (criterion: hierarchy) ----------
    def granularity(fn, pns):
        eur_by = collections.defaultdict(float)
        pn_by = collections.defaultdict(int)
        tot = 0.0
        for p in pns:
            code = (fn(p) or "").strip()
            if not code:
                continue
            e = spine[p]["eur"]
            eur_by[code] += e
            pn_by[code] += 1
            tot += e
        if tot <= 0:
            return None
        ranked = sorted(eur_by.items(), key=lambda kv: -kv[1])
        sh = [v / tot for _, v in ranked]
        hhi = sum(x * x for x in sh)
        return {
            "codes_used": len(eur_by),
            "codes_ge_0p5pct": sum(1 for x in sh if x >= 0.005),
            "codes_ge_1pct": sum(1 for x in sh if x >= 0.01),
            "codes_ge_2pct": sum(1 for x in sh if x >= 0.02),
            "max_code": ranked[0][0],
            "max_code_share_pct": round(100 * sh[0], 2),
            "top3_share_pct": round(100 * sum(sh[:3]), 2),
            "top5_share_pct": round(100 * sum(sh[:5]), 2),
            "top10_share_pct": round(100 * sum(sh[:10]), 2),
            "hhi": round(hhi, 4),
            "effective_codes": round(1 / hhi, 1) if hhi else 0,
            "codes_to_reach_80pct": next(
                (i + 1 for i in range(len(sh)) if sum(sh[:i + 1]) >= 0.80), len(sh)),
            "labelled_eur": round(tot, 2),
        }

    gran = {k: granularity(f, common_base) for k, f in SYSTEMS.items()}

    # ---------------- 3. coherence / purity on the Japanese description ------------
    # (the pack's retired purity column measured blank descriptions; jp_description is complete)
    def coherence(fn, pns):
        by_code = collections.defaultdict(list)
        tot = 0.0
        for p in pns:
            code = (fn(p) or "").strip()
            if not code:
                continue
            by_code[code].append(p)
            tot += spine[p]["eur"]
        judgeable = 0
        coherent = 0
        frag_eur = 0.0
        pure_rows = 0
        all_rows = 0
        for code, ps in by_code.items():
            nouns = collections.Counter(leading_noun(desc(p)) for p in ps)
            if not nouns:
                continue
            top_n, top_c = nouns.most_common(1)[0]
            all_rows += len(ps)
            pure_rows += top_c
            if len(ps) >= JUDGEABLE_PNS:
                judgeable += 1
                if top_c / len(ps) >= COHERENT_SHARE:
                    coherent += 1
                else:
                    frag_eur += sum(spine[p]["eur"] for p in ps)
        return {
            "codes_used": len(by_code),
            "judgeable_codes_ge200pns": judgeable,
            "coherent_codes": coherent,
            "fragmented_codes": judgeable - coherent,
            "fragmented_eur": round(frag_eur, 2),
            "fragmented_pct_of_base": round(100 * frag_eur / tot, 2) if tot else 0,
            "row_weighted_purity_pct": round(100 * pure_rows / all_rows, 2) if all_rows else 0,
        }

    coh = {k: coherence(f, common_base) for k, f in SYSTEMS.items()}

    # ---------------- 4. does the system explain the movement? ----------------------
    # L12 vs prior L12 on the pack population (the only base carrying both periods)
    mv = {p: cur[p] - prev[p] for p in pack_pns}
    net_move = sum(mv.values())
    gross_move = sum(abs(v) for v in mv.values() if v)

    def movement(fn):
        by_code = collections.defaultdict(lambda: {"net": 0.0, "gain": 0.0, "loss": 0.0, "n": 0})
        for p in pack_pns:
            code = (fn(p) or "").strip()
            if not code:
                continue
            d = by_code[code]
            v = mv[p]
            d["net"] += v
            if v > 0:
                d["gain"] += v
            elif v < 0:
                d["loss"] += v
            d["n"] += 1
        ranked = sorted(by_code.items(), key=lambda kv: -abs(kv[1]["net"]))
        abs_tot = sum(abs(d["net"]) for _, d in ranked) or 1.0
        cum, n80 = 0.0, 0
        for _, d in ranked:
            cum += abs(d["net"])
            n80 += 1
            if cum / abs_tot >= 0.80:
                break
        hidden = sum(min(d["gain"], abs(d["loss"])) for _, d in ranked)
        hidden_codes = sum(1 for _, d in ranked
                           if d["gain"] > 50_000 and d["loss"] < -50_000)
        return {
            "codes_used": len(by_code),
            "net_movement_eur": round(net_move, 2),
            "codes_to_explain_80pct_of_absolute_movement": n80,
            "offsetting_eur_hidden_inside_codes": round(hidden, 2),
            "offsetting_pct_of_gross_movement": round(100 * hidden / gross_move, 2) if gross_move else 0,
            "codes_with_both_gt50k_gain_and_loss": hidden_codes,
            "top_movers": [
                {"code": c, "net": round(d["net"], 2), "gain": round(d["gain"], 2),
                 "loss": round(d["loss"], 2), "pns": d["n"]}
                for c, d in ranked[:10]
            ],
        }

    mov = {k: movement(f) for k, f in SYSTEMS.items()}

    # ---------------- 5. service-basket isolation, defined without either system ----
    BASKETS = {
        "Filters": r"\b(FILTER|ELEMENT)\b",
        "Brake friction": r"\b(BRAKE|PAD|LINING|SHOE)\b",
        "Clutch": r"\b(CLUTCH|DISC ASSY|PRESSURE PLATE)\b",
    }
    basket_members = {}
    for name, pat in BASKETS.items():
        basket_members[name] = {p for p in pack_pns if re.search(pat, (desc(p) or "").upper())}
    all_service = set().union(*basket_members.values())
    basket_members["All three combined"] = all_service

    def isolate(fn, members):
        by_code = collections.defaultdict(float)
        tot = 0.0
        for p in members:
            code = (fn(p) or "").strip()
            if not code:
                continue
            by_code[code] += cur[p]
            tot += cur[p]
        if not by_code or tot <= 0:
            return None
        ranked = sorted(by_code.items(), key=lambda kv: -kv[1])
        cum, n80 = 0.0, 0
        for _, v in ranked:
            cum += v
            n80 += 1
            if cum / tot >= 0.80:
                break
        return {
            "top_code": ranked[0][0],
            "top_code_share_pct": round(100 * ranked[0][1] / tot, 2),
            "codes_to_reach_80pct": n80,
            "codes_used": len(by_code),
            "covered_eur": round(tot, 2),
        }

    baskets = {}
    for name, members in basket_members.items():
        eur = sum(cur[p] for p in members)
        baskets[name] = {
            "pns": len(members), "eur": round(eur, 2),
            "pct_of_book": round(100 * eur / sum(cur.values()), 2),
            "systems": {k: isolate(f, members) for k, f in SYSTEMS.items()},
        }

    # ---------------- 6. pricing relevance: does the code predict the margin band? --
    def class_purity(fn, pns):
        by_code = collections.defaultdict(collections.Counter)
        for p in pns:
            code = (fn(p) or "").strip()
            c = spine[p]["cls"]
            if not code or not c:
                continue
            by_code[code][c] += spine[p]["eur"]
        if not by_code:
            return None
        tot = sum(sum(c.values()) for c in by_code.values())
        dom = sum(max(c.values()) for c in by_code.values())
        return {
            "codes": len(by_code),
            "weighted_dominant_class_share_pct": round(100 * dom / tot, 2) if tot else 0,
        }

    cls_pur = {k: class_purity(f, common_base) for k, f in SYSTEMS.items()}

    # ---------------- 7. distributor applicability ---------------------------------
    def per_distributor(fn):
        by_d = collections.defaultdict(lambda: [0.0, 0.0])
        for p in pack_pns:
            for d in dists[p]:
                e = cur[p] / len(dists[p]) if dists[p] else 0
                by_d[d][0] += e
                if (fn(p) or "").strip():
                    by_d[d][1] += e
        pcts = sorted(100 * v[1] / v[0] for v in by_d.values() if v[0] > 0)
        if not pcts:
            return None
        return {
            "distributors": len(pcts),
            "min_coverage_pct": round(pcts[0], 2),
            "median_coverage_pct": round(pcts[len(pcts) // 2], 2),
            "max_coverage_pct": round(pcts[-1], 2),
        }

    dist_app = {k: per_distributor(f) for k, f in SYSTEMS.items()}

    # ---------------- 8. stability: AIM churn between two of its own generations ---
    stability = {}
    if AIM_V2.exists() and AIM_NOW.exists():
        old = {}
        with AIM_V2.open(encoding="utf-8", newline="") as fh:
            for r in csv.DictReader(fh):
                old[s(r["part_number"])] = s(r.get("catalog_l1"))
        new = {}
        with AIM_NOW.open(encoding="utf-8", newline="") as fh:
            for r in csv.DictReader(fh):
                new[s(r["part_number"])] = s(r.get("catalog_l1"))
        common = [p for p in old if p in new and old[p] and new[p]]
        changed = [p for p in common if old[p] != new[p]]
        eur_changed = sum(spine[p]["eur"] for p in changed if p in spine)
        eur_common = sum(spine[p]["eur"] for p in common if p in spine)
        stability["AIM churn, 18 to 20 September files"] = {
            "compared_pns": len(common),
            "changed_pns": len(changed),
            "changed_pct_of_pns": round(100 * len(changed) / len(common), 2) if common else 0,
            "changed_eur": round(eur_changed, 2),
            "changed_pct_of_eur": round(100 * eur_changed / eur_common, 2) if eur_common else 0,
        }
    # AIM provenance spread
    src_eur = collections.defaultdict(float)
    src_pns = collections.Counter()
    for p, v in spine.items():
        src_pns[v["aimsrc"] or "(blank)"] += 1
        src_eur[v["aimsrc"] or "(blank)"] += v["eur"]
    stability["AIM provenance spread (aim_source)"] = {
        "distinct_values": len(src_pns),
        "top": [{"aim_source": k, "pns": src_pns[k], "eur": round(src_eur[k], 2)}
                for k, _ in sorted(src_eur.items(), key=lambda kv: -kv[1])[:8]],
    }
    stability["ZKK across price-CDs"] = {
        "status": "UNTESTABLE in this workspace",
        "reason": ("only one Japanese file generation carries ZKK (PRICE CD 250912). "
                   "The current master price file PRICE CD 260910 carries no ZKK/ZUK/HKK/EPLE column, "
                   "so code stability between generations cannot be measured."),
    }

    # ---------------- 9. crosswalk --------------------------------------------------
    xwalk = {}
    for z in ("275", "200", "283", "114"):
        fam = collections.defaultdict(float)
        tot = 0.0
        for p in pack_pns:
            if not spine.get(p) or spine[p]["zkk"] != z:
                continue
            a = spine[p]["aim1"]
            if not a:
                continue
            fam[a] += cur[p]
            tot += cur[p]
        if not fam:
            continue
        xwalk[z] = {
            "eur": round(tot, 2),
            "aim_families": len(fam),
            "top": [{"aim": k, "eur": round(v, 2), "pct_of_code": round(100 * v / tot, 2)}
                    for k, v in sorted(fam.items(), key=lambda kv: -kv[1])[:6]],
        }

    # ---------------- write ---------------------------------------------------------
    payload = {
        "purpose": "ZKK vs AIM classification review against the review pack's comparison framework",
        "base_definition": {
            "full_book": {"pns": len(spine), "eur": round(total_book, 2)},
            "common_base": {"pns": len(common_base),
                            "eur": round(sum(spine[p]["eur"] for p in common_base), 2)},
            "pack_L12": {"pns": len(pack_pns), "eur": round(sum(cur.values()), 2)},
            "note": ("granularity, coherence, pricing and service tests run on the common base "
                     "(same rows for every system). Movement tests run on pack_L12, the only base "
                     "carrying both periods."),
        },
        "coverage": cov,
        "gap_detail": gap_detail,
        "granularity": gran,
        "coherence": coh,
        "movement": mov,
        "service_baskets": baskets,
        "price_class_purity": cls_pur,
        "distributor_applicability": dist_app,
        "stability": stability,
        "crosswalk_zkk_to_aim_l1": xwalk,
    }
    OUT_JSON.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")

    with OUT_CSV.open("w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["criterion", "system", "metric", "value"])
        for k, v in gran.items():
            for m in ("codes_used", "codes_ge_1pct", "max_code_share_pct", "top10_share_pct",
                      "hhi", "effective_codes", "codes_to_reach_80pct"):
                w.writerow(["granularity", k, m, v[m] if v else ""])
        for k, v in coh.items():
            for m in ("judgeable_codes_ge200pns", "coherent_codes", "fragmented_codes",
                      "fragmented_pct_of_base", "row_weighted_purity_pct"):
                w.writerow(["coherence", k, m, v[m]])
        for k, v in mov.items():
            for m in ("codes_to_explain_80pct_of_absolute_movement",
                      "offsetting_pct_of_gross_movement",
                      "codes_with_both_gt50k_gain_and_loss"):
                w.writerow(["movement", k, m, v[m]])
        for k, v in cov.items():
            w.writerow(["coverage_common_base", k, "eur_coverage_pct",
                        (v["common_base"]["eur_coverage_pct"] if v else "")])
            w.writerow(["coverage_full_book", k, "eur_coverage_pct",
                        (v["full_book"]["eur_coverage_pct"] if v else "")])

    # ---------------- print ---------------------------------------------------------
    print()
    print("=== GRANULARITY (common base, identical rows) ===")
    print(f"{'system':<28}{'codes':>6}{'>=1%':>6}{'max%':>8}{'top10%':>8}{'HHI':>8}{'eff':>7}{'to80':>6}")
    for k, v in sorted(gran.items(), key=lambda kv: (kv[1] is None, -(kv[1]["effective_codes"] if kv[1] else 0))):
        if not v:
            continue
        print(f"{k:<28}{v['codes_used']:>6}{v['codes_ge_1pct']:>6}{v['max_code_share_pct']:>8.2f}"
              f"{v['top10_share_pct']:>8.2f}{v['hhi']:>8.4f}{v['effective_codes']:>7.1f}"
              f"{v['codes_to_reach_80pct']:>6}")

    print()
    print("=== COHERENCE (dominant part type on the Japanese description) ===")
    print(f"{'system':<28}{'judgeable':>10}{'coherent':>10}{'fragmented':>11}{'frag%':>8}{'purity%':>9}")
    for k, v in sorted(coh.items(), key=lambda kv: -kv[1]["row_weighted_purity_pct"]):
        print(f"{k:<28}{v['judgeable_codes_ge200pns']:>10}{v['coherent_codes']:>10}"
              f"{v['fragmented_codes']:>11}{v['fragmented_pct_of_base']:>8.2f}"
              f"{v['row_weighted_purity_pct']:>9.2f}")

    print()
    print("=== MOVEMENT (pack L12 vs previous L12) ===")
    print(f"{'system':<28}{'codes':>6}{'to explain 80%':>15}{'offsetting hidden%':>20}{'codes >50k both':>17}")
    for k, v in sorted(mov.items(), key=lambda kv: kv[1]["codes_to_explain_80pct_of_absolute_movement"]):
        print(f"{k:<28}{v['codes_used']:>6}"
              f"{v['codes_to_explain_80pct_of_absolute_movement']:>15}"
              f"{v['offsetting_pct_of_gross_movement']:>20.2f}"
              f"{v['codes_with_both_gt50k_gain_and_loss']:>17}")

    print()
    print("=== SERVICE BASKET ISOLATION (basket defined from description text) ===")
    for name, b in baskets.items():
        print(f"  {name}: {b['pns']} PNs, EUR {b['eur']:,.0f} ({b['pct_of_book']:.2f}% of book)")
        for k, v in b["systems"].items():
            if v:
                print(f"     {k:<28} top {v['top_code'][:34]:<34} {v['top_code_share_pct']:>6.2f}%"
                      f"  {v['codes_to_reach_80pct']} codes to 80%")

    print()
    print("=== PRICE-CLASS PURITY ===")
    for k, v in sorted(cls_pur.items(), key=lambda kv: -(kv[1]["weighted_dominant_class_share_pct"] if kv[1] else 0)):
        if v:
            print(f"  {k:<28} {v['weighted_dominant_class_share_pct']:>6.2f}% across {v['codes']} codes")

    print()
    print("=== STABILITY ===")
    for k, v in stability.items():
        print(f"  {k}: {json.dumps(v)[:220]}")

    print()
    print(f"-> {OUT_JSON.name}")
    print(f"-> {OUT_CSV.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

# -*- coding: utf-8 -*-
"""
ZKK dictionary -- close-out pass.

  * the full 142-row table (billed book basis, plus the codes that never billed)
  * euro-weighted purity for ZKK and HKK, and purity over the codes that carry the money
  * HKK concentration check (is HKK's edge real, or one tiny-code tail?)
  * consistency check: spine.jp_zkk vs cache.zkk, and what jp_* columns the spine carries

Read-only. Nothing written to disk.

Run: python 01_data/91_build/zkk_dictionary_closeout_20260920.py
"""
from __future__ import annotations

import collections
import csv
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CACHE = ROOT / "01_data" / "00_derived" / "jp_codes_cache_20260920.csv"
SPINE = ROOT / "01_data" / "00_derived" / "aim_master_v2.csv"
BLANKISH = {"", "-", "--", "N/A", "NA", "NONE", "UNKNOWN", "(BLANK)"}


def s(v) -> str:
    if v is None:
        return ""
    t = str(v).strip()
    if t.endswith(".0") and t[:-2].replace("-", "").isdigit():
        t = t[:-2]
    return t


def collapse(t: str) -> str:
    return re.sub(r"\s+", " ", t).strip()


def noun(desc: str) -> str:
    d = collapse((desc or "").upper())
    head = collapse(re.split(r"[;,]", d)[0]).strip(" .-*/")
    return head if head and head not in BLANKISH else "(blank)"


def main() -> int:
    P = print
    cache: dict[str, dict] = {}
    with CACHE.open(encoding="utf-8", newline="") as fh:
        for r in csv.DictReader(fh):
            pn = s(r.get("pn"))
            if pn:
                cache[pn] = r

    spine_cols = None
    spine = {}
    total_eur = 0.0
    with SPINE.open(encoding="utf-8", newline="") as fh:
        rd = csv.DictReader(fh)
        spine_cols = list(rd.fieldnames or [])
        for r in rd:
            pn = s(r.get("part_number"))
            if not pn:
                continue
            e = float(r.get("l12m_billed_eur") or 0)
            spine[pn] = {
                "eur": e,
                "aim_l1": s(r.get("aim_l1_fixed")) or s(r.get("aim_l1")) or "(blank)",
                "aim_l2": s(r.get("aim_l2_fixed")) or s(r.get("aim_l2")) or "(blank)",
                "jp_zkk": s(r.get("jp_zkk")),
                "jp_zuk": s(r.get("jp_zuk")),
                "jp_hkk": s(r.get("jp_hkk")),
                "jp_code_source": s(r.get("jp_code_source")),
            }
            total_eur += e

    P("=" * 100)
    P("F. SPINE COLUMNS AND CONSISTENCY")
    P("=" * 100)
    P(f"  spine columns ({len(spine_cols)}): {spine_cols}")
    P(f"  jp_* columns present: {[c for c in spine_cols if c.startswith('jp_')]}")
    P(f"  -> a jp_description column exists? {'jp_description' in spine_cols}")

    # coverage of spine jp_zkk
    filled = sum(1 for v in spine.values() if v["jp_zkk"])
    P(f"  spine rows with jp_zkk filled: {filled:,} of {len(spine):,} "
      f"({100*filled/len(spine):.2f}%)")
    src = collections.Counter(v["jp_code_source"] or "(blank)" for v in spine.values())
    P(f"  jp_code_source values: {src.most_common()}")

    # compare spine.jp_zkk against cache.zkk for the same PN
    both = same = diff = 0
    examples = []
    for pn, v in spine.items():
        c = cache.get(pn)
        if not c:
            continue
        both += 1
        cz = s(c.get("zkk"))
        if cz == v["jp_zkk"]:
            same += 1
        else:
            diff += 1
            if len(examples) < 5:
                examples.append((pn, v["jp_zkk"], cz))
    P(f"  PNs in both spine and cache: {both:,}; jp_zkk equal: {same:,}; different: {diff:,}")
    if examples:
        P(f"  example disagreements (pn, spine, cache): {examples}")

    # ---- rebuild the base ----
    base = {}
    for pn, v in spine.items():
        c = cache.get(pn)
        if not c:
            continue
        zk = s(c.get("zkk"))
        if not zk:
            continue
        base[pn] = {
            "eur": v["eur"],
            "desc": s(c.get("jp_description")),
            "zkk": zk,
            "hkk": s(c.get("hkk")),
            "aim_l1": v["aim_l1"],
            "aim_l2": v["aim_l2"],
        }
    base_eur = sum(v["eur"] for v in base.values())
    P(f"  common base re-built: {len(base):,} PNs, EUR {base_eur:,.2f}, "
      f"{100*base_eur/total_eur:.2f}% of the book")
    P(f"  base rows with a blank Japanese description: "
      f"{sum(1 for v in base.values() if noun(v['desc']) == '(blank)'):,}")

    # ---- AIM L1 sizes ----
    fam_pns = collections.Counter()
    fam_eur = collections.Counter()
    for pn, v in base.items():
        fam_pns[v["aim_l1"]] += 1
        fam_eur[v["aim_l1"]] += v["eur"]
    P("")
    P("  AIM L1 family sizes on the base (PNs / EUR):")
    for fam, e in fam_eur.most_common():
        P(f"    {fam:<28} {fam_pns[fam]:>7,} PNs   EUR {e:>13,.0f}")

    # ---- per-code aggregates on the base ----
    per = collections.defaultdict(lambda: {"pns": 0, "eur": 0.0, "nouns": collections.Counter()})
    for pn, v in base.items():
        c = per[v["zkk"]]
        c["pns"] += 1
        c["eur"] += v["eur"]
        c["nouns"][noun(v["desc"])] += 1

    # file-side aggregates for the codes that never billed
    file_only = collections.defaultdict(lambda: {"rows": 0, "nouns": collections.Counter()})
    for pn, r in cache.items():
        zk = s(r.get("zkk"))
        if zk:
            file_only[zk]["rows"] += 1
            file_only[zk]["nouns"][noun(s(r.get("jp_description")))] += 1

    all_codes = sorted(set(file_only) | set(per))
    P("")
    P(f"  ZKK codes on the price file: {len(file_only)}")
    P(f"  ZKK codes with billed euro : {len(per)}")
    P(f"  ZKK codes with no billed euro: {len(set(file_only) - set(per))} -> "
      f"{sorted(set(file_only) - set(per))}")

    P("")
    P("=" * 100)
    P("G. FULL 142-ROW TABLE  (billed book basis; rows marked * are file-only, no billed euro)")
    P("=" * 100)
    for c in all_codes:
        v = per.get(c)
        if v:
            t3 = v["nouns"].most_common(3)
            while len(t3) < 3:
                t3.append(("(none)", 0))
            P("| `%s` | %d | %.0f | %.2f%% | %s %.1f%% | %s %.1f%% | %s %.1f%% |" % (
                c, v["pns"], v["eur"], 100 * v["eur"] / base_eur,
                t3[0][0], 100 * t3[0][1] / v["pns"],
                t3[1][0], 100 * t3[1][1] / v["pns"],
                t3[2][0], 100 * t3[2][1] / v["pns"]))
        else:
            f = file_only[c]
            t3 = f["nouns"].most_common(3)
            while len(t3) < 3:
                t3.append(("(none)", 0))
            P("| `%s` * | 0 | 0 | 0.00%% | %s %.1f%% | %s %.1f%% | %s %.1f%% |" % (
                c, t3[0][0], 100 * t3[0][1] / f["rows"],
                t3[1][0], 100 * t3[1][1] / f["rows"],
                t3[2][0], 100 * t3[2][1] / f["rows"]))

    # ---- euro-weighted and money-concentrated purity ----
    P("")
    P("=" * 100)
    P("H. PURITY THAT DOES NOT FLATTER SMALL OR COARSE SYSTEMS")
    P("=" * 100)

    def purities(kf, nounf=noun):
        mp = collections.defaultdict(collections.Counter)
        mpe = collections.defaultdict(collections.Counter)
        for pn, v in base.items():
            mp[kf(v)][nounf(v["desc"])] += 1
            mpe[kf(v)][nounf(v["desc"])] += v["eur"]
        rows_tot = sum(sum(c.values()) for c in mp.values())
        rows_dom = sum(c.most_common(1)[0][1] for c in mp.values())
        eur_tot = sum(sum(c.values()) for c in mpe.values())
        eur_dom = sum(c.most_common(1)[0][1] for c in mpe.values())
        # purity over the money codes: the smallest set of codes >= 90% of EUR
        ranked = sorted(((sum(c.values()), k) for k, c in mpe.items()), key=lambda x: -x[0])
        acc = 0.0
        keep = 0
        for amt, c in ranked:
            acc += amt
            keep += 1
            if acc >= 0.90 * eur_tot:
                break
        keepset = {c for _, c in ranked[:keep]}
        sub = collections.defaultdict(collections.Counter)
        for pn, v in base.items():
            if kf(v) in keepset:
                sub[kf(v)][nounf(v["desc"])] += 1
        sub_tot = sum(sum(c.values()) for c in sub.values())
        sub_dom = sum(c.most_common(1)[0][1] for c in sub.values())
        return (len(mp), 100 * rows_dom / rows_tot, 100 * eur_dom / eur_tot,
                keep, 100 * sub_dom / sub_tot, len(sub))

    def wf(kf, nounf):
        """weighted purity: dominant noun per code, weighted by that code's EUR"""
        mp = collections.defaultdict(lambda: collections.Counter())
        eur = collections.defaultdict(float)
        for pn, v in base.items():
            mp[kf(v)][nounf(v["desc"])] += 1
            eur[kf(v)] += v["eur"]
        tot = sum(eur.values())
        acc = 0.0
        for c, cc in mp.items():
            share = cc.most_common(1)[0][1] / sum(cc.values())
            acc += share * eur[c]
        return 100 * acc / tot

    P(f"  {'system':<16} {'codes':>6} {'row purity':>11} {'EUR purity':>11} "
      f"{'codes=90%EUR':>13} {'purity on those':>16}")
    for label, kf in (("ZKK (3 char)", lambda v: v["zkk"]),
                      ("HKK (4 char)", lambda v: v["hkk"])):
        n, rp, ep, keep, kp, ns = purities(kf)
        P(f"  {label:<16} {n:>6} {rp:>10.2f}% {ep:>10.2f}% {keep:>13} {kp:>15.2f}%")
        P(f"  {'  ^ weighted':<16} dominant-noun share weighted by code EUR: {wf(kf, noun):.2f}%")

    P("")
    P("  HKK concentration on the base:")
    hkk_agg = collections.Counter()
    hkk_eur = collections.Counter()
    for pn, v in base.items():
        hkk_agg[v["hkk"]] += 1
        hkk_eur[v["hkk"]] += v["eur"]
    n_rows = sum(hkk_agg.values())
    for c, n in hkk_agg.most_common(4):
        P(f"    HKK `{c}`: {n:,} PNs = {100*n/n_rows:.1f}% of base rows, "
          f"EUR {hkk_eur[c]:,.0f} = {100*hkk_eur[c]/base_eur:.1f}% of base EUR")
    P(f"    HKK codes with >=100 PNs: {sum(1 for c, n in hkk_agg.items() if n>=100)} of {len(hkk_agg)}")
    P(f"    HKK codes with <20 PNs : {sum(1 for c, n in hkk_agg.items() if n<20)} of {len(hkk_agg)}")
    zkk_agg = collections.Counter(v["zkk"] for v in base.values())
    P(f"    ZKK codes with >=100 PNs: {sum(1 for c, n in zkk_agg.items() if n>=100)} of {len(zkk_agg)}")
    P("")
    P("  purity excluding the single dominant code of each system (the 'one big bucket' test):")
    for label, kf, drop in (("ZKK without `275`", lambda v: v["zkk"], "275"),
                            ("HKK without `1110`", lambda v: v["hkk"], "1110")):
        mp = collections.defaultdict(lambda: collections.Counter())
        for pn, v in base.items():
            c = kf(v)
            if c == drop:
                continue
            mp[c][noun(v["desc"])] += 1
        tot = sum(sum(c.values()) for c in mp.values())
        dom = sum(c.most_common(1)[0][1] for c in mp.values())
        P(f"    {label:<20} codes={len(mp):<4} rows={tot:,} purity={100*dom/tot:.2f}%")
    return 0


if __name__ == "__main__":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    raise SystemExit(main())

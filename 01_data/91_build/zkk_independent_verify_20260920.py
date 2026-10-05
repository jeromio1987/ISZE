# -*- coding: utf-8 -*-
"""
Independent re-measurement of the headline figures in
  01_data/90_INBOX/ZKK_CODE_DICTIONARY_2026-09-20.md

Written from scratch (not a copy of the earlier zkk_dictionary_* scripts).
Read-only: nothing is written to disk, no source file is modified.

Sources
  spine  : 01_data/00_derived/aim_master_v2.csv          (part_number, l12m_billed_eur, jp_zkk, aim_l1, aim_l1_fixed, aim_l2, aim_l2_fixed, price_class_iml)
  cache  : 01_data/00_derived/jp_codes_cache_20260920.csv (pn, jp_description, zkk, hkk, zuk, class_new)

What is measured
  A1  share of l12m_billed_eur carried by jp_zkk == '275'; distinct leading nouns inside 275;
      join method and a row-by-row soundness check of spine.jp_zkk against cache.zkk
  A2  coherent / near / mixed / fragmented counts at the stated threshold, the leading-noun
      definition, how blank descriptions are treated, and what the <200 PN floor hides
  A3  whether ZKK 275 holds >=1% of the euro of at least 25 distinct AIM families, measured on
      aim_l1_fixed, on aim_l1, and on the fallback used by the dictionary

Run: python 01_data/91_build/zkk_independent_verify_20260920.py
"""
from __future__ import annotations

import collections
import csv
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SPINE = ROOT / "01_data" / "00_derived" / "aim_master_v2.csv"
CACHE = ROOT / "01_data" / "00_derived" / "jp_codes_cache_20260920.csv"

BLANKISH = {"", "-", "--", "N/A", "NA", "NONE", "UNKNOWN", "(BLANK)"}


def s(v) -> str:
    if v is None:
        return ""
    t = str(v).strip()
    if t.endswith(".0") and t[:-2].replace("-", "").isdigit():
        t = t[:-2]
    return t


def collapse(t: str) -> str:
    return re.sub(r"\s+", " ", t or "").strip()


def leading_noun(desc: str) -> str:
    """Dictionary definition: the head of the Japanese description up to the first ';' or ','."""
    d = collapse((desc or "").upper())
    head = collapse(re.split(r"[;,]", d)[0]).strip(" .-*/")
    if head in BLANKISH:
        return "(blank)"
    return head


def first_word(desc: str) -> str:
    """Alternative, narrower definition: the first whitespace-delimited token."""
    ln = leading_noun(desc)
    w = ln.split(" ")[0]
    return w if w and w not in BLANKISH else "(blank)"


def pct(a: float, b: float) -> float:
    return 100.0 * a / b if b else 0.0


def main() -> int:
    P = print
    out = []

    # ------------------------------------------------------------------ cache
    cache_rows = 0
    cache_pns = collections.Counter()          # pn -> how many cache rows
    cache_zkk = collections.Counter()          # zkk -> rows (all cache rows)
    cache_hkk = collections.Counter()
    cache_desc_blank = 0
    cache_multi_zkk = 0
    cache_by_pn: dict[str, list[dict]] = collections.defaultdict(list)
    with CACHE.open(encoding="utf-8", newline="") as fh:
        for r in csv.DictReader(fh):
            pn = s(r.get("pn"))
            if not pn:
                continue
            cache_rows += 1
            cache_pns[pn] += 1
            zk = s(r.get("zkk"))
            hk = s(r.get("hkk"))
            cache_zkk[zk] += 1
            cache_hkk[hk] += 1
            d = s(r.get("jp_description"))
            if leading_noun(d) == "(blank)":
                cache_desc_blank += 1
            cache_by_pn[pn].append({"zkk": zk, "hkk": hk, "desc": d})
    for pn, rr in cache_by_pn.items():
        if len({x["zkk"] for x in rr}) > 1:
            cache_multi_zkk += 1

    out += [
        "=" * 100,
        "CACHE  " + str(CACHE),
        "=" * 100,
        f"  cache rows                          : {cache_rows:,}",
        f"  cache distinct part numbers         : {len(cache_pns):,}",
        f"  cache PNs carrying more than one ZKK: {cache_multi_zkk:,}",
        f"  cache ZKK blank rows                : {cache_zkk.get('', 0):,}",
        f"  cache distinct ZKK values (non-blank): {len([k for k in cache_zkk if k]):,}",
        f"  cache distinct HKK values (non-blank): {len([k for k in cache_hkk if k]):,}",
        f"  cache rows with blank leading noun   : {cache_desc_blank:,} "
        f"({pct(cache_desc_blank, cache_rows):.2f}% of cache rows)",
    ]

    # ------------------------------------------------------------------ spine
    spine_all_rows = 0
    spine_total_eur_all_rows = 0.0
    spine_pns: dict[str, dict] = {}
    spine_dupe_pns = 0
    with SPINE.open(encoding="utf-8", newline="") as fh:
        rd = csv.DictReader(fh)
        spine_cols = list(rd.fieldnames or [])
        for r in rd:
            pn = s(r.get("part_number"))
            if not pn:
                continue
            e = float(r.get("l12m_billed_eur") or 0)
            spine_all_rows += 1
            spine_total_eur_all_rows += e
            if pn in spine_pns:
                spine_dupe_pns += 1
            spine_pns[pn] = {
                "eur": e,
                "jp_zkk": s(r.get("jp_zkk")),
                "aim_l1": s(r.get("aim_l1")),
                "aim_l1_fixed": s(r.get("aim_l1_fixed")),
                "aim_l2": s(r.get("aim_l2")),
                "aim_l2_fixed": s(r.get("aim_l2_fixed")),
            }
    spine_total_eur_dedup = sum(v["eur"] for v in spine_pns.values())
    spine_zkk_filled = sum(1 for v in spine_pns.values() if v["jp_zkk"])

    out += [
        "",
        "=" * 100,
        "SPINE  " + str(SPINE),
        "=" * 100,
        f"  spine columns                       : {len(spine_cols)}",
        f"  spine data rows                     : {spine_all_rows:,}",
        f"  spine distinct part numbers         : {len(spine_pns):,} "
        f"(repeat part_number rows: {spine_dupe_pns:,})",
        f"  spine total l12m_billed_eur (all rows)     : EUR {spine_total_eur_all_rows:,.2f}",
        f"  spine total l12m_billed_eur (deduped)      : EUR {spine_total_eur_dedup:,.2f}",
        f"  spine rows with jp_zkk filled       : {spine_zkk_filled:,} of {len(spine_pns):,}",
    ]

    # ------------------------------------------------------------------ join
    shared = 0
    same = 0
    diff = 0
    examples = []
    spine_only_zkk = 0
    for pn, v in spine_pns.items():
        if pn not in cache_by_pn:
            continue
        shared += 1
        cz = cols = {x["zkk"] for x in cache_by_pn[pn]}
        if len(cols) == 1:
            cz = next(iter(cols))
        else:
            cz = collections.Counter(x["zkk"] for x in cache_by_pn[pn]).most_common(1)[0][0]
        if cz == v["jp_zkk"]:
            same += 1
        else:
            diff += 1
            if len(examples) < 5:
                examples.append((pn, v["jp_zkk"], sorted(cols)))
    out += [
        "",
        "JOIN SOUNDNESS  (spine.jp_zkk  vs  cache.zkk, same part_number)",
        f"  part numbers in both files          : {shared:,}",
        f"  jp_zkk identical                    : {same:,}",
        f"  jp_zkk different                    : {diff:,}",
        f"  examples (pn, spine, cache)         : {examples}",
    ]

    # ------------------------------------------------------------------ base
    # The dictionary's base: a spine part number that the cache can label with a non-blank ZKK.
    base: dict[str, dict] = {}
    for pn, v in spine_pns.items():
        rr = cache_by_pn.get(pn)
        if not rr:
            continue
        zk = collections.Counter(x["zkk"] for x in rr).most_common(1)[0][0]
        if not zk:
            continue
        base[pn] = {
            "eur": v["eur"],
            "desc": rr[0]["desc"],
            "zkk": zk,
            "hkk": collections.Counter(x["hkk"] for x in rr).most_common(1)[0][0],
            "aim_l1": v["aim_l1"],
            "aim_l1_fixed": v["aim_l1_fixed"],
            "aim_l2": v["aim_l2"],
            "aim_l2_fixed": v["aim_l2_fixed"],
        }
    base_eur = sum(v["eur"] for v in base.values())
    out += [
        "",
        "=" * 100,
        "BASE  (spine part numbers the cache can label with a ZKK code)",
        "=" * 100,
        f"  base part numbers                   : {len(base):,}",
        f"  base EUR                            : EUR {base_eur:,.2f}",
        f"  base as share of spine book (all rows): {pct(base_eur, spine_total_eur_all_rows):.2f}%",
        f"  base rows with blank leading noun   : "
        f"{sum(1 for v in base.values() if leading_noun(v['desc']) == '(blank)'):,}",
    ]

    # ------------------------------------------------------------------ A1: ZKK 275
    z275 = [v for v in base.values() if v["zkk"] == "275"]
    z275_eur = sum(v["eur"] for v in z275)
    z275_nouns = collections.Counter(leading_noun(v["desc"]) for v in z275)
    z275_nouns_fw = collections.Counter(first_word(v["desc"]) for v in z275)
    out += [
        "",
        "=" * 100,
        "A1  ZKK 275",
        "=" * 100,
        f"  part numbers in 275                 : {len(z275):,}",
        f"  EUR in 275                          : EUR {z275_eur:,.2f}",
        f"  share of the base                   : {pct(z275_eur, base_eur):.2f}%",
        f"  share of the spine book (all rows)  : {pct(z275_eur, spine_total_eur_all_rows):.2f}%",
        f"  distinct leading nouns inside 275   : {len(z275_nouns):,}",
        f"  distinct first words inside 275     : {len(z275_nouns_fw):,}",
        "  top 8 leading nouns                 : "
        + ", ".join(f"{n} {c:,} ({pct(c, len(z275)):.1f}%)" for n, c in z275_nouns.most_common(8)),
    ]

    # ------------------------------------------------------------------ A2: threshold
    per = collections.defaultdict(lambda: {"pns": 0, "eur": 0.0, "nouns": collections.Counter()})
    for v in base.values():
        c = per[v["zkk"]]
        c["pns"] += 1
        c["eur"] += v["eur"]
        c["nouns"][leading_noun(v["desc"])] += 1

    rows = []
    for code, v in per.items():
        top_noun, top_cnt = v["nouns"].most_common(1)[0]
        rows.append({
            "code": code, "pns": v["pns"], "eur": v["eur"],
            "noun": top_noun, "share": pct(top_cnt, v["pns"]),
            "distinct_nouns": len(v["nouns"]),
        })

    big = [r for r in rows if r["pns"] >= 200]
    small = [r for r in rows if r["pns"] < 200]
    coherent = [r for r in big if r["share"] >= 80.0]
    near = [r for r in big if 60.0 <= r["share"] < 80.0]
    mixed = [r for r in big if 40.0 <= r["share"] < 60.0]
    frag = [r for r in big if r["share"] < 40.0]
    eur_of = lambda rs: sum(r["eur"] for r in rs)

    out += [
        "",
        "=" * 100,
        "A2  COHERENCE AT THE STATED THRESHOLD",
        "    coherent = >=200 part numbers AND leading noun >=80% of those part numbers",
        "=" * 100,
        f"  ZKK codes seen on the base          : {len(rows):,}",
        f"  codes with >=200 part numbers       : {len(big):,}",
        f"  COHERENT  (>=200, noun >=80%)       : {len(coherent):,}   EUR {eur_of(coherent):,.0f} "
        f"({pct(eur_of(coherent), base_eur):.2f}% of base)",
        f"  NEAR      (>=200, noun 60-80%)      : {len(near):,}   EUR {eur_of(near):,.0f} "
        f"({pct(eur_of(near), base_eur):.2f}%)",
        f"  MIXED     (>=200, noun 40-60%)      : {len(mixed):,}   EUR {eur_of(mixed):,.0f} "
        f"({pct(eur_of(mixed), base_eur):.2f}%)",
        f"  FRAGMENTED(>=200, noun <40%)        : {len(frag):,}   EUR {eur_of(frag):,.0f} "
        f"({pct(eur_of(frag), base_eur):.2f}%)",
        f"  BELOW THE 200-PN FLOOR (not judged) : {len(small):,}   EUR {eur_of(small):,.0f} "
        f"({pct(eur_of(small), base_eur):.2f}%)",
        f"  coherent codes named                : "
        + " ".join(f"{r['code']}({r['pns']}pn,{r['share']:.1f}%,{r['noun']})" for r in sorted(coherent, key=lambda x: -x["pns"])),
        f"  near codes named                    : "
        + " ".join(f"{r['code']}({r['pns']}pn,{r['share']:.1f}%,{r['noun']})" for r in sorted(near, key=lambda x: -x["pns"])),
        f"  mixed codes named                   : "
        + " ".join(f"{r['code']}({r['pns']}pn,{r['share']:.1f}%,{r['noun']})" for r in sorted(mixed, key=lambda x: -x["pns"])),
        "  fragmented, 10 largest by EUR       : "
        + " ".join(f"{r['code']}({r['eur']:,.0f})" for r in sorted(frag, key=lambda x: -x["eur"])[:10]),
        "",
        "  widened sweep over all billed ZKK codes:",
        f"    codes with noun >=80%             : {sum(1 for r in rows if r['share'] >= 80.0):,}",
        f"    codes with noun 40-80%            : {sum(1 for r in rows if 40.0 <= r['share'] < 80.0):,}",
        f"    codes with noun <40%              : {sum(1 for r in rows if r['share'] < 40.0):,}"
        f"   EUR {eur_of([r for r in rows if r['share'] < 40.0]):,.0f} "
        f"({pct(eur_of([r for r in rows if r['share'] < 40.0]), base_eur):.2f}% of base)",
        "",
        "  sensitivity of the threshold result:",
    ]
    for floor in (100, 150, 200, 300, 500):
        b = [r for r in rows if r["pns"] >= floor]
        co = [r for r in b if r["share"] >= 80.0]
        fr = [r for r in b if r["share"] < 40.0]
        out.append(f"    floor {floor:>4}: judged {len(b):>3} codes, coherent {len(co):>2}, "
                   f"fragmented {len(fr):>2} holding {pct(eur_of(fr), base_eur):.2f}% of base EUR")
    # blank handling: include blanks as their own noun bucket, and exclude them
    b_int = []
    b_excl = []
    for code, v in per.items():
        tot = sum(v["nouns"].values())
        blanks = v["nouns"].get("(blank)", 0)
        top = max((c for n, c in v["nouns"].items() if n != "(blank)"), default=0)
        if tot >= 200:
            b_int.append((code, 100.0 * v["nouns"].most_common(1)[0][1] / tot))
            if tot - blanks > 0:
                b_excl.append((code, 100.0 * top / (tot - blanks)))
    out += [
        f"    blanks counted as their own bucket : coherent {sum(1 for _, p in b_int if p >= 80.0):,} of {len(b_int):,}",
        f"    blanks excluded from the denominator: coherent {sum(1 for _, p in b_excl if p >= 80.0):,} of {len(b_excl):,}",
        f"    (blank descriptions on the base      : "
        f"{sum(1 for v in base.values() if leading_noun(v['desc']) == '(blank)'):,})",
    ]

    # ------------------------------------------------------------------ A3: AIM families
    def aim_families(key: str, fallback: bool = False) -> tuple[int, list]:
        fam_tot = collections.Counter()
        fam_275 = collections.Counter()
        for v in base.values():
            f = v[key]
            if fallback and not f:
                f = v["aim_l1"]
            f = f or "(blank)"
            fam_tot[f] += v["eur"]
            if v["zkk"] == "275":
                fam_275[f] += v["eur"]
        hits = []
        for f, tot in fam_tot.items():
            if tot > 0 and pct(fam_275[f], tot) >= 1.0:
                hits.append((f, fam_275[f], tot, pct(fam_275[f], tot)))
        hits.sort(key=lambda x: -x[3])
        return len(hits), hits

    out += [
        "",
        "=" * 100,
        "A3  ZKK 275 AGAINST THE AIM FAMILIES  (>=1% of a family's euro)",
        "=" * 100,
    ]
    for label, key, fb in (
        ("aim_l1_fixed only", "aim_l1_fixed", False),
        ("aim_l1 only", "aim_l1", False),
        ("aim_l1_fixed, falling back to aim_l1", "aim_l1_fixed", True),
    ):
        n, hits = aim_families(key, fb)
        out.append(f"  {label:<38}: {n:,} families at >=1%; "
                   f"top: " + ", ".join(f"{f} {p:.1f}%" for f, _, _, p in hits[:5]))
    # the fallback view in full, with the absolute size of each family, because a
    # family of EUR 40 can pass a 1% test without meaning anything
    n_fb, hits_fb = aim_families("aim_l1_fixed", True)
    out += ["", "  the 25 families in full (fallback definition), sorted by 275's EUR in them:", 
            "    family                          EUR in 275      family EUR   275 share"]
    for f, e275, etot, p in sorted(hits_fb, key=lambda x: -x[1]):
        out.append(f"    {f[:30]:<30} {e275:>12,.0f} {etot:>15,.0f} {p:>10.1f}%")
    # how many base rows carry each column at all
    # which family moves between the two columns, so I can report the difference precisely
    def fam_set(key: str) -> set:
        fam_tot = collections.Counter()
        fam_275 = collections.Counter()
        for v in base.values():
            f = v[key] or "(blank)"
            fam_tot[f] += v["eur"]
            if v["zkk"] == "275":
                fam_275[f] += v["eur"]
        return {f for f, tot in fam_tot.items() if tot > 0 and pct(fam_275[f], tot) >= 1.0}

    fixed_only = fam_set("aim_l1_fixed") - fam_set("aim_l1")
    l1_only = fam_set("aim_l1") - fam_set("aim_l1_fixed")
    out += [
        f"  families at >=1% on aim_l1_fixed but not on aim_l1: {sorted(fixed_only)}",
        f"  families at >=1% on aim_l1 but not on aim_l1_fixed: {sorted(l1_only)}",
    ]

    out += [
        f"  base rows with a non-blank aim_l1_fixed: "
        f"{sum(1 for v in base.values() if v['aim_l1_fixed']):,} of {len(base):,}",
        f"  base rows with a non-blank aim_l1      : "
        f"{sum(1 for v in base.values() if v['aim_l1']):,} of {len(base):,}",
    ]

    # ------------------------------------------------------------------ extra: HKK and the ZKK/HKK code relation
    zkk_vals = {k for k in cache_zkk if k}
    hkk_vals = {k for k in cache_hkk if k}
    hkk_pfx = {k[:3] for k in hkk_vals}
    out += [
        "",
        "=" * 100,
        "EXTRA  ZKK vs HKK (reported supporting figures)",
        "=" * 100,
        f"  distinct ZKK values                 : {len(zkk_vals):,}",
        f"  distinct HKK values                 : {len(hkk_vals):,}",
        f"  HKK distinct 3-char prefixes        : {len(hkk_pfx):,}",
        f"  ZKK values equal to a full HKK value: {len(zkk_vals & hkk_vals):,}",
        f"  ZKK values equal to a 3-char HKK prefix: {len(zkk_vals & hkk_pfx):,} -> {sorted(zkk_vals & hkk_pfx)}",
        f"  ZKK value lengths                   : {sorted({len(k) for k in zkk_vals})}",
        f"  HKK value lengths                   : {sorted({len(k) for k in hkk_vals})}",
    ]

    def wide_noun(desc: str) -> str:
        """Benchmark-style wider split: also break on '(' and '[' and '/'."""
        d = collapse((desc or "").upper())
        head = collapse(re.split(r"[;,]", d)[0])
        head = collapse(re.split(r"[(\[/]", head)[0]).strip(" .-*/")
        return head if head and head not in BLANKISH else "(blank)"

    def row_purity(key_fn, nounf=leading_noun) -> tuple[int, float, int, int]:
        mp = collections.defaultdict(collections.Counter)
        for v in base.values():
            mp[key_fn(v)][nounf(v["desc"])] += 1
        tot = sum(sum(c.values()) for c in mp.values())
        dom = sum(c.most_common(1)[0][1] for c in mp.values())
        single = sum(1 for c in mp.values() if len(c) == 1)
        return len(mp), pct(dom, tot), dom, tot

    nz, pz, dz, tz = row_purity(lambda v: v["zkk"])
    nh, ph, dh, th = row_purity(lambda v: v["hkk"])
    nzw, pzw, dzw, tzw = row_purity(lambda v: v["zkk"], wide_noun)
    nhw, phw, dhw, thw = row_purity(lambda v: v["hkk"], wide_noun)

    # the same measurements on the whole 142-code cache file, for comparison
    fc_zkk = collections.defaultdict(collections.Counter)
    fc_hkk = collections.defaultdict(collections.Counter)
    for pn, rr in cache_by_pn.items():
        fc_zkk[rr[0]["zkk"]][leading_noun(rr[0]["desc"])] += 1
        fc_hkk[rr[0]["hkk"]][leading_noun(rr[0]["desc"])] += 1
    ftz = sum(sum(c.values()) for c in fc_zkk.values())
    fdz = sum(c.most_common(1)[0][1] for c in fc_zkk.values())
    fth = sum(sum(c.values()) for c in fc_hkk.values())
    fdh = sum(c.most_common(1)[0][1] for c in fc_hkk.values())
    # the same on the 2-row file-only codes, to test whether they inflate the number
    fc_zkk_98 = {k: c for k, c in fc_zkk.items() if sum(c.values()) > 2}
    ftz98 = sum(sum(c.values()) for c in fc_zkk_98.values())
    fdz98 = sum(c.most_common(1)[0][1] for c in fc_zkk_98.values())
    out += [
        f"  row purity ZKK, full cache file      : {pct(fdz, ftz):.4f}% "
        f"({fdz:,} / {ftz:,}) over {len(fc_zkk):,} codes",
        f"  row purity HKK, full cache file      : {pct(fdh, fth):.4f}% "
        f"({fdh:,} / {fth:,}) over {len(fc_hkk):,} codes",
        f"  ZKK file purity excluding the 2-row file-only codes: {pct(fdz98, ftz98):.4f}% "
        f"({fdz98:,} / {ftz98:,}) over {len(fc_zkk_98):,} codes",
    ]
    out += [
        f"  row purity ZKK, split on ';' and ',' : {pz:.4f}%  ({dz:,} / {tz:,}) over {nz:,} codes",
        f"  row purity HKK, split on ';' and ',' : {ph:.4f}%  ({dh:,} / {th:,}) over {nh:,} codes",
        f"  row purity ZKK, wider split          : {pzw:.4f}%  ({dzw:,} / {tzw:,})",
        f"  row purity HKK, wider split          : {phw:.4f}%  ({dhw:,} / {thw:,})",
    ]
    hkk_1110_rows = cache_hkk.get("1110", 0)
    hkk_agg_pns = collections.Counter()
    hkk_agg_eur = collections.Counter()
    hkk_1110_nouns = collections.Counter()
    for v in base.values():
        hkk_agg_pns[v["hkk"]] += 1
        hkk_agg_eur[v["hkk"]] += v["eur"]
        if v["hkk"] == "1110":
            hkk_1110_nouns[leading_noun(v["desc"])] += 1
    n_rows_base = sum(hkk_agg_pns.values())
    top1110 = hkk_1110_nouns.most_common(1)[0]
    out += [
        f"  HKK 1110 on the cache file          : {hkk_1110_rows:,} rows "
        f"({pct(hkk_1110_rows, cache_rows):.1f}% of the file)",
        f"  HKK 1110 on the base               : {hkk_agg_pns['1110']:,} part numbers "
        f"({pct(hkk_agg_pns['1110'], n_rows_base):.1f}% of base rows), "
        f"EUR {hkk_agg_eur['1110']:,.0f} ({pct(hkk_agg_eur['1110'], base_eur):.1f}% of base EUR)",
        f"  HKK 1110 top leading noun           : {top1110[0]} "
        f"{top1110[1]:,} = {pct(top1110[1], hkk_agg_pns['1110']):.1f}% of its part numbers",
    ]

    # ------------------------------------------------------------------ extra: HKK named slot characters
    # Section 5 of the dictionary quotes a per-slot-character claim (28 of 39 HKK codes at >=20 PNs
    # carry the part type the 2022 workbook names). Re-measured here so the thesis edit rests on a
    # number I produced myself.
    wb = None
    names: dict[str, str] = {}
    try:
        import openpyxl  # noqa: PLC0415
        import unicodedata
        wb = openpyxl.load_workbook(ROOT / "01_data" / "HKK Code 20221028.xlsx",
                                    read_only=True, data_only=True)
        for sh in wb.sheetnames:
            ws = wb[sh]
            for row in ws.iter_rows(values_only=True):
                cells = [unicodedata.normalize("NFKC", str(c or "")).strip() for c in row]
                # the sheet lays several prefix blocks side by side: prefix, slot character, name.
                # scan every column, not just the first block.
                for i, c in enumerate(cells):
                    if not re.fullmatch(r"\d{3}", c):
                        continue
                    if i + 2 >= len(cells):
                        continue
                    if len(cells[i + 1]) == 1:
                        names[c + cells[i + 1]] = cells[i + 2]
        wb.close()
    except Exception as exc:  # pragma: no cover
        out.append(f"  2022 workbook read failed: {exc}")

    hkk_pn = collections.Counter()
    hkk_noun_rows = collections.defaultdict(collections.Counter)
    hkk_noun_eur = collections.defaultdict(collections.Counter)
    for v in base.values():
        hkk_pn[v["hkk"]] += 1
    for v in base.values():
        hkk_noun_rows[v["hkk"]][leading_noun(v["desc"])] += 1
        hkk_noun_eur[v["hkk"]][leading_noun(v["desc"])] += v["eur"]
    ranked = [c for c, n in hkk_pn.items() if n >= 20 and c in names]

    def matched(counter_map, c) -> bool:
        if not counter_map.get(c):
            return False
        top = counter_map[c].most_common(1)[0][0]
        # the workbook name may carry several words separated by ';' or ',' — any of them counts
        parts = [w for w in re.split(r"[;,]", names[c]) if w.strip()]
        return any(p.strip().lower() in top.lower() for p in parts)

    carry_rows = [c for c in ranked if matched(hkk_noun_rows, c)]
    carry_eur = [c for c in ranked if matched(hkk_noun_eur, c)]
    # strict version: the code's single most common noun starts with the workbook's first word
    carry_strict = []
    for c in ranked:
        first = re.split(r"[;,]", names[c])[0].strip().lower()
        top_r = hkk_noun_rows[c].most_common(1)[0][0].lower()
        if first and top_r.split(" ")[0] == first.split(" ")[0]:
            carry_strict.append(c)
    # loosest rule: the workbook name appears anywhere among the code's nouns, at any frequency
    carry_any = []
    for c in ranked:
        parts = [w.strip().lower() for w in re.split(r"[;,]", names[c]) if w.strip()]
        nouns = [n.lower() for n in hkk_noun_rows[c]]
        if any(p in n for p in parts for n in nouns):
            carry_any.append(c)
    out += [
        "",
        "EXTRA  HKK named slot characters (2022 workbook names tested against measurement)",
        f"  2022 workbook: names extracted for {len(names):,} four-character codes",
        f"  HKK codes at >=20 part numbers covering a named code: {len(ranked):,}",
        f"  name appears in the code's top noun, row-weighted   : {len(carry_rows):,} "
        f"of {len(ranked):,} ({pct(len(carry_rows), len(ranked)):.0f}%)",
        f"  name appears in the code's top noun, euro-weighted  : {len(carry_eur):,} "
        f"of {len(ranked):,} ({pct(len(carry_eur), len(ranked)):.0f}%)",
        f"  strict: first word of the name equals the code's top noun's first word, row-weighted: "
        f"{len(carry_strict):,} of {len(ranked):,} ({pct(len(carry_strict), len(ranked)):.0f}%)",
        f"  loosest: name appears somewhere among the code's nouns, any frequency: "
        f"{len(carry_any):,} of {len(ranked):,} ({pct(len(carry_any), len(ranked)):.0f}%)",
        "  the codes this document quotes by name, as I measure them (row-weighted):"]
    for c in ("111D", "111X", "113A", "113F", "113B", "313A", "111K", "111J"):
        if c not in names:
            out.append(f"    {c}: no name in my extraction")
            continue
        eur = hkk_noun_eur.get(c)
        if not eur:
            out.append(f"    {c}: named {names[c]}; not present on the billed base at all")
            continue
        top = eur.most_common(2)
        tot_e = sum(eur.values())
        out.append(f"    {c}: named {names[c]}; most-common noun {top[0][0]} "
                   f"{pct(top[0][1], tot_e):.1f}% of its euro"
                   + (f", then {top[1][0]} {pct(top[1][1], tot_e):.1f}%" if len(top) > 1 else ""))
    # ------------------------------------------------------------------ extra: purity with 1110 and 275 removed
    def purity_excluding(drop_key: str, drop_val: str) -> tuple[int, float, float]:
        mp = collections.defaultdict(collections.Counter)
        kept_eur = 0.0
        for v in base.values():
            if v[drop_key] == drop_val:
                continue
            mp[v[drop_key]][leading_noun(v["desc"])] += 1
            kept_eur += v["eur"]
        tot = sum(sum(c.values()) for c in mp.values())
        dom = sum(c.most_common(1)[0][1] for c in mp.values())
        return len(mp), pct(dom, tot), pct(kept_eur, base_eur)

    n1, p1, e1 = purity_excluding("zkk", "275")
    n2, p2, e2 = purity_excluding("hkk", "1110")
    out += [
        f"  ZKK without 275                     : {n1:,} codes, purity {p1:.2f}%, "
        f"covering {e1:.1f}% of base EUR",
        f"  HKK without 1110                    : {n2:,} codes, purity {p2:.2f}%, "
        f"covering {e2:.1f}% of base EUR",
    ]

    print("\n".join(out))
    return 0


if __name__ == "__main__":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    raise SystemExit(main())

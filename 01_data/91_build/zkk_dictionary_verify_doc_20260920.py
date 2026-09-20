# -*- coding: utf-8 -*-
"""
ZKK dictionary -- verify every aggregate quoted in ZKK_CODE_DICTIONARY_2026-09-20.md.

Read-only. Prints each number the document claims so it can be checked against the text.

Run: python 01_data/91_build/zkk_dictionary_verify_doc_20260920.py
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
BLANKISH = {"", "-", "--"}


def s(v) -> str:
    if v is None:
        return ""
    t = str(v).strip()
    if t.endswith(".0") and t[:-2].replace("-", "").isdigit():
        t = t[:-2]
    return t


def noun(d):
    d = re.sub(r"\s+", " ", (d or "").upper()).strip()
    h = re.sub(r"\s+", " ", re.split(r"[;,]", d)[0]).strip(" .-*/")
    return h if h and h not in BLANKISH else "(blank)"


def main() -> int:
    P = print
    cache = {}
    with CACHE.open(encoding="utf-8", newline="") as fh:
        for r in csv.DictReader(fh):
            pn = s(r.get("pn"))
            if pn:
                cache[pn] = r
    base = {}
    with SPINE.open(encoding="utf-8", newline="") as fh:
        for r in csv.DictReader(fh):
            pn = s(r.get("part_number"))
            if not pn:
                continue
            c = cache.get(pn)
            if not c:
                continue
            z = s(c.get("zkk"))
            if not z:
                continue
            base[pn] = {"eur": float(r.get("l12m_billed_eur") or 0),
                        "zkk": z, "noun": noun(s(c.get("jp_description")))}
    base_eur = sum(v["eur"] for v in base.values())
    per = collections.defaultdict(lambda: {"pns": 0, "eur": 0.0, "nouns": collections.Counter()})
    for v in base.values():
        c = per[v["zkk"]]
        c["pns"] += 1
        c["eur"] += v["eur"]
        c["nouns"][v["noun"]] += 1

    P("=" * 90)
    P("DOC VERIFICATION")
    P("=" * 90)
    P(f"base: {len(base):,} PNs, EUR {base_eur:,.2f}")

    # coherence buckets, PNs >= 200
    big = {c: v for c, v in per.items() if v["pns"] >= 200}
    P(f"\ncodes with >=200 PNs: {len(big)}")
    buckets = [("Coherent  >=80%", 0.80, 1.01), ("Near      60-80%", 0.60, 0.80),
               ("Mixed     40-60%", 0.40, 0.60), ("Fragmented <40%", -1.0, 0.40)]
    tot_check = 0.0
    for label, lo, hi in buckets:
        ok = [c for c, v in big.items()
              if lo <= v["nouns"].most_common(1)[0][1] / v["pns"] < hi]
        e = sum(big[c]["eur"] for c in ok)
        tot_check += e
        P(f"  {label:<20} {len(ok):>3} codes   EUR {e:>14,.0f}  ({100*e/base_eur:6.2f}%)"
          + (f"  -> {sorted(ok)}" if len(ok) <= 4 else ""))
    small = {c: v for c, v in per.items() if v["pns"] < 200}
    e_small = sum(v["eur"] for v in small.values())
    P(f"  {'codes <200 PNs':<20} {len(small):>3} codes   EUR {e_small:>14,.0f}  "
      f"({100*e_small/base_eur:6.2f}%)")
    P(f"  buckets + small = EUR {tot_check+e_small:,.0f} (must equal {base_eur:,.0f})")

    # all 132 codes
    P("")
    for thr in (0.80, 0.40):
        ok = [c for c, v in per.items() if v["nouns"].most_common(1)[0][1] / v["pns"] >= thr]
        e = sum(per[c]["eur"] for c in ok)
        P(f"  all 132 codes, dominant noun >={thr:.0%}: {len(ok)} codes, EUR {e:,.0f} "
          f"({100*e/base_eur:.2f}%)")
    below = [c for c, v in per.items() if v["nouns"].most_common(1)[0][1] / v["pns"] < 0.40]
    e_below = sum(per[c]["eur"] for c in below)
    P(f"  all 132 codes, dominant noun <40%: {len(below)} codes, EUR {e_below:,.0f} "
      f"({100*e_below/base_eur:.2f}%)")

    # the six largest codes
    P("")
    top6 = sorted(per.items(), key=lambda kv: -kv[1]["eur"])[:6]
    e6 = sum(v["eur"] for _, v in top6)
    P(f"  six largest codes: {[c for c,_ in top6]}")
    P(f"    combined EUR {e6:,.0f} = {100*e6/base_eur:.2f}% of base")
    for c, v in top6:
        t = v["nouns"].most_common(1)[0]
        P(f"    `{c}` EUR {v['eur']:,.0f} ({100*v['eur']/base_eur:.2f}%) "
          f"dom {t[0]} {100*t[1]/v['pns']:.1f}% distinct nouns {len(v['nouns']):,}")

    # biggest code's noun depth
    P("")
    P(f"  `275` distinct leading nouns: {len(per['275']['nouns']):,}")
    P(f"  `114` distinct leading nouns: {len(per['114']['nouns']):,}")
    P(f"  `200` distinct leading nouns: {len(per['200']['nouns']):,}")

    # 16 codes >=0.5%
    big16 = [c for c, v in per.items() if v["eur"] >= 0.005 * base_eur]
    P("")
    P(f"  codes >=0.5% of base EUR: {len(big16)} -> {sorted(big16)}")

    # HKK facts
    P("")
    hk = collections.Counter()
    hke = collections.Counter()
    for pn, r in cache.items():
        if pn in base:
            hk[s(r.get("hkk"))] += 1
            hke[s(r.get("hkk"))] += base[pn]["eur"]
    nh = sum(hk.values())
    P(f"  HKK 1110: {hk['1110']:,} PNs = {100*hk['1110']/nh:.1f}% of base rows, "
      f"EUR {hke['1110']:,.0f} = {100*hke['1110']/base_eur:.1f}% of base EUR")
    P(f"  HKK codes used on base: {len(hk)}")

    # ZUK facts
    P("")
    zu = collections.Counter()
    for pn, r in cache.items():
        if pn in base:
            zu[s(r.get("zuk"))] += base[pn]["eur"]
    P(f"  ZUK top value: {zu.most_common(1)[0][0]} EUR {zu.most_common(1)[0][1]:,.0f} "
      f"= {100*zu.most_common(1)[0][1]/base_eur:.2f}%")
    P(f"  ZUK top-10 share: {100*sum(x for _,x in zu.most_common(10))/base_eur:.2f}%")

    # spine blank share
    spine_rows = 0
    spine_blank = 0
    spine_blank_eur = 0.0
    spine_eur = 0.0
    with SPINE.open(encoding="utf-8", newline="") as fh:
        for r in csv.DictReader(fh):
            e = float(r.get("l12m_billed_eur") or 0)
            spine_rows += 1
            spine_eur += e
            if not s(r.get("jp_zkk")):
                spine_blank += 1
                spine_blank_eur += e
    P("")
    P(f"  spine rows {spine_rows:,}, jp_zkk blank {spine_blank:,} "
      f"({100*spine_blank/spine_rows:.2f}%)")
    P(f"  blank EUR {spine_blank_eur:,.2f} = {100*spine_blank_eur/spine_eur:.2f}% of book")
    P(f"  labelled EUR {spine_eur-spine_blank_eur:,.2f} = "
      f"{100*(spine_eur-spine_blank_eur)/spine_eur:.2f}%")
    return 0


if __name__ == "__main__":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    raise SystemExit(main())

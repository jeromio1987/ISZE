# -*- coding: utf-8 -*-
"""
ZKK dictionary -- numeric block structure.

Does the number itself encode anything, or is it just a serial? Groups the 142 ZKK
codes into their hundred-blocks and reports what each block holds.

Read-only. Nothing written to disk.

Run: python 01_data/91_build/zkk_dictionary_blocks_20260920.py
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
                        "noun": noun(s(c.get("jp_description"))),
                        "zkk": z,
                        "aim_l1": s(r.get("aim_l1_fixed")) or s(r.get("aim_l1")) or "(blank)"}
    base_eur = sum(v["eur"] for v in base.values())

    blocks = collections.defaultdict(lambda: {"codes": set(), "pns": 0, "eur": 0.0,
                                              "nouns": collections.Counter(),
                                              "aim": collections.Counter()})
    for pn, v in base.items():
        b = v["zkk"][0] + "00s"
        bl = blocks[b]
        bl["codes"].add(v["zkk"])
        bl["pns"] += 1
        bl["eur"] += v["eur"]
        bl["nouns"][v["noun"]] += 1
        bl["aim"][v["aim_l1"]] += v["eur"]

    P("=" * 100)
    P("M. ZKK NUMERIC BLOCKS -- what each hundred-block holds on the billed book")
    P("=" * 100)
    for b, bl in sorted(blocks.items(), key=lambda kv: -kv[1]["eur"]):
        top = bl["nouns"].most_common(3)
        fam = bl["aim"].most_common(1)[0] if bl["aim"] else ("(none)", 0.0)
        famtxt = (f"{fam[0]} {100*fam[1]/bl['eur']:.0f}%" if bl["eur"] > 0
                  else f"{fam[0]} (no billed euro)")
        P(f"  block {b:<6} {len(bl['codes']):>3} codes  {bl['pns']:>7,} PNs  "
          f"EUR {bl['eur']:>13,.0f} ({100*bl['eur']/base_eur:5.2f}%)")
        P(f"      top nouns: " + ", ".join(f"{n} {100*c/bl['pns']:.1f}%" for n, c in top)
          + f"   | dominant AIM L1: {famtxt}")

    P("")
    P("  does the last digit or the middle digit carry a signal?")
    for pos, label in ((0, "first"), (1, "second"), (2, "third")):
        mp = collections.defaultdict(collections.Counter)
        for pn, v in base.items():
            mp[v["zkk"][pos]][v["noun"]] += 1
        P(f"  {label} digit:")
        for d in sorted(mp):
            c = mp[d]
            tot = sum(c.values())
            t = c.most_common(1)[0]
            P(f"     `{d}` rows {tot:>7,}  dom noun {t[0]:<16}{100*t[1]/tot:5.1f}%  "
              f"distinct nouns {len(c):,}")
    return 0


if __name__ == "__main__":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    raise SystemExit(main())

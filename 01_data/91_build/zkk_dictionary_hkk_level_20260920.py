# -*- coding: utf-8 -*-
"""
ZKK dictionary -- final check on the HKK level question.

The raw 'exclude the biggest code' test can flatter HKK because 28 of its 72 codes
hold under 20 part numbers, and a 1-2 PN code scores 100% trivially. This pass
re-runs the comparison on codes that actually carry volume.

Read-only. Nothing written to disk.

Run: python 01_data/91_build/zkk_dictionary_hkk_level_20260920.py
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


def noun(desc: str) -> str:
    d = re.sub(r"\s+", " ", (desc or "").upper()).strip()
    head = re.sub(r"\s+", " ", re.split(r"[;,]", d)[0]).strip(" .-*/")
    return head if head and head not in BLANKISH else "(blank)"


def main() -> int:
    P = print
    cache = {}
    with CACHE.open(encoding="utf-8", newline="") as fh:
        for r in csv.DictReader(fh):
            pn = s(r.get("pn"))
            if pn:
                cache[pn] = r
    spine = {}
    total = 0.0
    with SPINE.open(encoding="utf-8", newline="") as fh:
        for r in csv.DictReader(fh):
            pn = s(r.get("part_number"))
            if not pn:
                continue
            e = float(r.get("l12m_billed_eur") or 0)
            spine[pn] = e
            total += e
    base = {}
    for pn, e in spine.items():
        c = cache.get(pn)
        if not c:
            continue
        z = s(c.get("zkk"))
        if not z:
            continue
        base[pn] = {"eur": e, "desc": s(c.get("jp_description")), "zkk": z,
                    "hkk": s(c.get("hkk"))}
    base_eur = sum(v["eur"] for v in base.values())

    def stats(kf, min_pn, drop=None, label=""):
        mp = collections.defaultdict(collections.Counter)
        mpe = collections.defaultdict(float)
        for pn, v in base.items():
            c = kf(v)
            if c == drop:
                continue
            mp[c][noun(v["desc"])] += 1
            mpe[c] += v["eur"]
        use = {c: cc for c, cc in mp.items() if sum(cc.values()) >= min_pn}
        tot = sum(sum(c.values()) for c in use.values())
        dom = sum(c.most_common(1)[0][1] for c in use.values())
        eur_use = sum(mpe[c] for c in use)
        P(f"  {label:<44} codes={len(use):<4} rows={tot:>7,} EUR={eur_use:>13,.0f} "
          f"({100*eur_use/base_eur:5.1f}% of base) purity={100*dom/tot if tot else 0:6.2f}%")

    P("=" * 100)
    P("I. HKK vs ZKK -- on codes that actually carry volume")
    P("=" * 100)
    P("  all codes:")
    stats(lambda v: v["zkk"], 1, None, "ZKK, all codes")
    stats(lambda v: v["hkk"], 1, None, "HKK, all codes")
    P("")
    P("  codes holding >=100 part numbers:")
    stats(lambda v: v["zkk"], 100, None, "ZKK, codes >=100 PNs")
    stats(lambda v: v["hkk"], 100, None, "HKK, codes >=100 PNs")
    P("")
    P("  codes holding >=100 PNs, with the single big mixed bucket removed:")
    stats(lambda v: v["zkk"], 100, "275", "ZKK >=100 PNs, without `275`")
    stats(lambda v: v["hkk"], 100, "1110", "HKK >=100 PNs, without `1110`")
    P("")
    P("  codes holding >=50 PNs, with the big bucket removed:")
    stats(lambda v: v["zkk"], 50, "275", "ZKK >=50 PNs, without `275`")
    stats(lambda v: v["hkk"], 50, "1110", "HKK >=50 PNs, without `1110`")

    P("")
    P("=" * 100)
    P("J. WHERE THE MONEY SITS IN EACH COLUMN")
    P("=" * 100)
    for label, kf, big in (("ZKK", lambda v: v["zkk"], "275"),
                           ("HKK", lambda v: v["hkk"], "1110")):
        mp = collections.Counter()
        mpe = collections.Counter()
        for v in base.values():
            mp[kf(v)] += 1
            mpe[kf(v)] += v["eur"]
        n = sum(mp.values())
        P(f"  {label}: {len(mp)} codes; biggest `{big}` = {mp[big]:,} PNs "
          f"({100*mp[big]/n:.1f}% of rows), EUR {mpe[big]:,.0f} "
          f"({100*mpe[big]/base_eur:.1f}% of base EUR)")
        top5 = mpe.most_common(5)
        P(f"    top 5 codes hold {100*sum(x for _, x in top5)/base_eur:.1f}% of base EUR: "
          + ", ".join(f"`{c}` {100*x/base_eur:.1f}%" for c, x in top5))

    P("")
    P("  cross-tab: how the two big buckets overlap")
    z275 = {pn for pn, v in base.items() if v["zkk"] == "275"}
    h1110 = {pn for pn, v in base.items() if v["hkk"] == "1110"}
    P(f"    ZKK `275` PNs {len(z275):,}; HKK `1110` PNs {len(h1110):,}; "
      f"in both {len(z275 & h1110):,} ({100*len(z275 & h1110)/len(z275):.1f}% of 275)")
    eur_both = sum(base[p]["eur"] for p in (z275 & h1110))
    P(f"    EUR in both: {eur_both:,.0f} ({100*eur_both/base_eur:.1f}% of base EUR)")

    P("")
    P("  how many ZKK codes does one HKK code span, and the reverse (billed book)")
    z_to_h = collections.defaultdict(set)
    h_to_z = collections.defaultdict(set)
    for v in base.values():
        z_to_h[v["zkk"]].add(v["hkk"])
        h_to_z[v["hkk"]].add(v["zkk"])
    P(f"    ZKK codes (>=100 PNs) span, median / max HKK codes: "
      f"{sorted(len(z_to_h[c]) for c in z_to_h if sum(1 for v in base.values() if v['zkk']==c)>=100)[len([c for c in z_to_h if sum(1 for v in base.values() if v['zkk']==c)>=100])//2]}"
      f" / {max(len(z_to_h[c]) for c in z_to_h)}")
    P(f"    HKK codes (>=100 PNs) span, median / max ZKK codes: "
      f"{sorted(len(h_to_z[c]) for c in h_to_z if sum(1 for v in base.values() if v['hkk']==c)>=100)[len([c for c in h_to_z if sum(1 for v in base.values() if v['hkk']==c)>=100])//2]}"
      f" / {max(len(h_to_z[c]) for c in h_to_z)}")

    P("")
    P("=" * 100)
    P("K. NAMED HKK CODES ON THE BILLED BOOK (the 2022 workbook names the prefix, not the slot char)")
    P("=" * 100)
    agg = collections.defaultdict(lambda: {"pns": 0, "eur": 0.0, "nouns": collections.Counter(),
                                           "zkk": collections.Counter()})
    for pn, v in base.items():
        a = agg[v["hkk"]]
        a["pns"] += 1
        a["eur"] += v["eur"]
        a["nouns"][noun(v["desc"])] += 1
        a["zkk"][v["zkk"]] += 1
    for c, v in sorted(agg.items(), key=lambda kv: (kv[0][:3], kv[0])):
        if v["pns"] < 20:
            continue
        t = v["nouns"].most_common(1)[0]
        z = v["zkk"].most_common(1)[0]
        P(f"  `{c}`  {v['pns']:>6,} PNs  EUR {v['eur']:>12,.0f}  "
          f"dom noun {t[0]:<16}{100*t[1]/v['pns']:5.1f}%  dom ZKK `{z[0]}` ({len(v['zkk'])} ZKK codes)")
    return 0


if __name__ == "__main__":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    raise SystemExit(main())

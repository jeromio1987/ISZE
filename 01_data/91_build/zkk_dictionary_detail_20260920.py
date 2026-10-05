# -*- coding: utf-8 -*-
"""
ZKK dictionary -- detail pass.

Answers, with numbers:
  * coherence counts at several thresholds, and the euro that sits in the fragmented codes
  * ZKK inside each AIM L1 family (does ZKK split the family, or repeat it?)
  * ZKK inside AIM L1>L2 for the largest families
  * normalised purity so coarser systems are not flattered
  * ZUK: does it separate anything that ZKK / HKK do not?

Read-only. Nothing written to disk.

Run: python 01_data/91_build/zkk_dictionary_detail_20260920.py
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
    rows_by_pn: dict[str, list[dict]] = collections.defaultdict(list)
    with CACHE.open(encoding="utf-8", newline="") as fh:
        for r in csv.DictReader(fh):
            pn = s(r.get("pn"))
            if pn:
                rows_by_pn[pn].append(r)

    spine = {}
    total_eur = 0.0
    with SPINE.open(encoding="utf-8", newline="") as fh:
        for r in csv.DictReader(fh):
            pn = s(r.get("part_number"))
            if not pn:
                continue
            e = float(r.get("l12m_billed_eur") or 0)
            spine[pn] = {
                "eur": e,
                "aim_l1": s(r.get("aim_l1_fixed")) or s(r.get("aim_l1")) or "(blank)",
                "aim_l2": s(r.get("aim_l2_fixed")) or s(r.get("aim_l2")) or "(blank)",
            }
            total_eur += e

    base = {}
    for pn, rr in rows_by_pn.items():
        if pn not in spine:
            continue
        zk = collections.Counter(s(x.get("zkk")) for x in rr).most_common(1)[0][0]
        if not zk:
            continue
        base[pn] = {
            "eur": spine[pn]["eur"],
            "desc": s(rr[0].get("jp_description")),
            "zkk": zk,
            "hkk": collections.Counter(s(x.get("hkk")) for x in rr).most_common(1)[0][0],
            "zuk": collections.Counter(s(x.get("zuk")) for x in rr).most_common(1)[0][0],
            "aim_l1": spine[pn]["aim_l1"],
            "aim_l2": spine[pn]["aim_l2"],
        }
    base_eur = sum(v["eur"] for v in base.values())
    P = print

    # ---- per ZKK aggregate ----
    per = collections.defaultdict(lambda: {"pns": 0, "eur": 0.0, "nouns": collections.Counter()})
    for pn, v in base.items():
        c = per[v["zkk"]]
        c["pns"] += 1
        c["eur"] += v["eur"]
        c["nouns"][noun(v["desc"])] += 1

    P("=" * 100)
    P("A. COHERENCE THRESHOLDS (dominant Japanese leading noun inside the ZKK code)")
    P("=" * 100)
    for minpn in (200, 50, 1):
        codes = {c: v for c, v in per.items() if v["pns"] >= minpn}
        for thr in (90, 80, 70, 60, 50, 40):
            ok = [c for c, v in codes.items() if 100 * v["nouns"].most_common(1)[0][1] / v["pns"] >= thr]
            eur_ok = sum(codes[c]["eur"] for c in ok)
            P(f"  PNs>={minpn:<4} dominant noun >={thr}%  ->  {len(ok):>3} of {len(codes):<4} codes, "
              f"EUR {eur_ok:>14,.0f} ({100*eur_ok/base_eur:5.2f}% of base)")
        frag = [c for c, v in codes.items() if 100 * v["nouns"].most_common(1)[0][1] / v["pns"] < 40]
        eur_frag = sum(codes[c]["eur"] for c in frag)
        P(f"  PNs>={minpn:<4} dominant noun <40%   ->  {len(frag):>3} of {len(codes):<4} codes, "
          f"EUR {eur_frag:>14,.0f} ({100*eur_frag/base_eur:5.2f}% of base)")
        P("")

    # codes >=0.5% of euro, coherence
    big = {c: v for c, v in per.items() if v["eur"] >= 0.005 * base_eur}
    P(f"  codes >=0.5% of base EUR: {len(big)}")
    for c, v in sorted(big.items(), key=lambda kv: -kv[1]["eur"]):
        t = v["nouns"].most_common(1)[0]
        P(f"    `{c}` EUR {v['eur']:>13,.0f} ({100*v['eur']/base_eur:5.2f}%)  {v['pns']:>6,} PNs  "
          f"dom noun {t[0]:<12} {100*t[1]/v['pns']:5.1f}%  distinct nouns {len(v['nouns']):,}")

    # ---- AIM L1 -> ZKK with nouns ----
    P("")
    P("=" * 100)
    P("B. DOES ZKK SPLIT INSIDE AN AIM FAMILY?  (AIM L1 -> the ZKK codes that hold >=1% of the family)")
    P("=" * 100)
    fam_zkk = collections.defaultdict(lambda: collections.defaultdict(
        lambda: {"eur": 0.0, "pns": 0, "nouns": collections.Counter()}))
    fam_tot = collections.Counter()
    for pn, v in base.items():
        fam_tot[v["aim_l1"]] += v["eur"]
        z = fam_zkk[v["aim_l1"]][v["zkk"]]
        z["eur"] += v["eur"]
        z["pns"] += 1
        z["nouns"][noun(v["desc"])] += 1
    for fam, tot in fam_tot.most_common():
        if tot < 100000:
            continue
        zs = sorted(fam_zkk[fam].items(), key=lambda kv: -kv[1]["eur"])
        material = [(c, v) for c, v in zs if v["eur"] >= 0.01 * tot]
        P(f"\n  {fam}  --  EUR {tot:,.0f}, {len(zs)} ZKK codes, {len(material)} holding >=1% of the family")
        for c, v in material[:8]:
            t = v["nouns"].most_common(1)[0]
            P(f"     `{c}`  EUR {v['eur']:>12,.0f} ({100*v['eur']/tot:5.1f}% of family)  "
              f"{v['pns']:>5,} PNs  dom noun {t[0]:<14} {100*t[1]/v['pns']:5.1f}%")
        if material:
            nouns = [v["nouns"].most_common(1)[0][0] for _, v in material]
            P(f"     -> distinct dominant nouns among those codes: {len(set(nouns))} of {len(nouns)}"
              f" {sorted(set(nouns))}")

    # ---- AIM L1>L2 -> ZKK ----
    P("")
    P("=" * 100)
    P("C. AIM L1>L2 cells that ZKK splits into clearly different part types")
    P("=" * 100)
    cell = collections.defaultdict(lambda: collections.defaultdict(
        lambda: {"eur": 0.0, "pns": 0, "nouns": collections.Counter()}))
    cell_tot = collections.Counter()
    cell_l1 = {}
    for pn, v in base.items():
        key = (v["aim_l1"], v["aim_l2"])
        cell_tot[key] += v["eur"]
        cell_l1[key] = v["aim_l1"]
        z = cell[key][v["zkk"]]
        z["eur"] += v["eur"]
        z["pns"] += 1
        z["nouns"][noun(v["desc"])] += 1
    shown = 0
    for key, tot in cell_tot.most_common(40):
        if tot < 300000:
            continue
        zs = sorted(cell[key].items(), key=lambda kv: -kv[1]["eur"])
        material = [(c, v) for c, v in zs if v["eur"] >= 0.15 * tot]
        nouns = [v["nouns"].most_common(1)[0][0] for _, v in material]
        if len(material) >= 2 and len(set(nouns)) >= 2:
            P(f"\n  {key[0]} > {key[1]}  --  EUR {tot:,.0f}  split into {len(material)} material ZKK codes")
            for c, v in material[:6]:
                t = v["nouns"].most_common(1)[0]
                P(f"     `{c}`  EUR {v['eur']:>12,.0f} ({100*v['eur']/tot:5.1f}%)  "
                  f"{v['pns']:>5,} PNs  dom noun {t[0]:<14} {100*t[1]/v['pns']:5.1f}%")
            shown += 1
            if shown >= 8:
                break

    # ---- normalised purity ----
    P("")
    P("=" * 100)
    P("D. NORMALISED PURITY  (observed - 1/n_codes) / (1 - 1/n_codes)  -- removes the coarse-system bonus")
    P("=" * 100)

    def meas(kf):
        mp = collections.defaultdict(collections.Counter)
        for pn, v in base.items():
            mp[kf(v)][noun(v["desc"])] += 1
        tot = sum(sum(c.values()) for c in mp.values())
        dom = sum(c.most_common(1)[0][1] for c in mp.values())
        n = len(mp)
        obs = dom / tot
        norm = (obs - 1 / n) / (1 - 1 / n) if n > 1 else 0.0
        single = sum(1 for c in mp.values() if len(c) == 1)
        return n, 100 * obs, 100 * norm, single

    P(f"  {'system':<20} {'codes':>6} {'purity':>8} {'normalised':>11} {'single-noun codes':>18}")
    for label, kf in (("ZKK (3 char)", lambda v: v["zkk"]),
                      ("HKK (4 char)", lambda v: v["hkk"]),
                      ("HKK first 3", lambda v: v["hkk"][:3]),
                      ("AIM L1", lambda v: v["aim_l1"]),
                      ("AIM L1>L2", lambda v: v["aim_l1"] + ">" + v["aim_l2"]),
                      ("ZUK (5 char)", lambda v: v["zuk"])):
        n, obs, norm, single = meas(kf)
        P(f"  {label:<20} {n:>6} {obs:>7.2f}% {norm:>10.2f}% {single:>18}")

    # HKK codes with >=100 PNs only (fair, comparable to ZKK)
    P("")
    P("  same, restricted to codes holding >=100 part numbers (removes the many tiny HKK codes):")
    for label, kf in (("ZKK (3 char)", lambda v: v["zkk"]),
                      ("HKK (4 char)", lambda v: v["hkk"])):
        mp = collections.defaultdict(collections.Counter)
        for pn, v in base.items():
            mp[kf(v)][noun(v["desc"])] += 1
        use = {c: cc for c, cc in mp.items() if sum(cc.values()) >= 100}
        tot = sum(sum(c.values()) for c in use.values())
        dom = sum(c.most_common(1)[0][1] for c in use.values())
        n = len(use)
        eur = sum(v["eur"] for pn, v in base.items()
                  if sum(mp[kf(v)].values()) >= 100)
        P(f"    {label:<16} codes={n:<4} rows covered={tot:,} purity={100*dom/tot:6.2f}%  "
          f"codes dropped={len(mp)-n}")

    # ---- ZUK question ----
    P("")
    P("=" * 100)
    P("E. ZUK -- does it separate what ZKK and HKK do not?")
    P("=" * 100)
    zu = collections.defaultdict(lambda: {"pns": 0, "eur": 0.0, "zkk": collections.Counter(),
                                          "hkk": collections.Counter(), "nouns": collections.Counter()})
    for pn, v in base.items():
        z = zu[v["zuk"]]
        z["pns"] += 1
        z["eur"] += v["eur"]
        z["zkk"][v["zkk"]] += 1
        z["hkk"][v["hkk"]] += 1
        z["nouns"][noun(v["desc"])] += 1
    P(f"  distinct ZUK on billed book: {len(zu)}")
    P("  top 12 ZUK by EUR:")
    for c, v in sorted(zu.items(), key=lambda kv: -kv[1]["eur"])[:12]:
        t = v["nouns"].most_common(1)[0]
        z = v["zkk"].most_common(1)[0]
        h = v["hkk"].most_common(1)[0]
        P(f"    `{c}` EUR {v['eur']:>13,.0f} ({100*v['eur']/base_eur:5.2f}%) {v['pns']:>6,} PNs  "
          f"dom noun {t[0]:<14}{100*t[1]/v['pns']:5.1f}%  dom ZKK `{z[0]}` ({100*z[1]/v['pns']:.0f}%)  "
          f"dom HKK `{h[0]}` ({100*h[1]/v['pns']:.0f}%)  distinct ZKK {len(v['zkk'])}")
    # within one big ZKK, does ZUK split?
    P("")
    P("  inside the largest ZKK code, does ZUK split it further?")
    for target in ("275", "200", "283", "114"):
        sub = collections.defaultdict(lambda: {"eur": 0.0, "pns": 0, "nouns": collections.Counter()})
        te = ze = 0.0
        for pn, v in base.items():
            if v["zkk"] != target:
                continue
            te += v["eur"]
            s2 = sub[v["zuk"]]
            s2["eur"] += v["eur"]
            s2["pns"] += 1
            s2["nouns"][noun(v["desc"])] += 1
        P(f"    ZKK `{target}` EUR {te:,.0f}, {len(sub)} ZUK codes inside")
        for c, v in sorted(sub.items(), key=lambda kv: -kv[1]["eur"])[:5]:
            t = v["nouns"].most_common(1)[0]
            P(f"       ZUK `{c}` EUR {v['eur']:>12,.0f} ({100*v['eur']/te:5.1f}%) {v['pns']:>5,} PNs "
              f"dom noun {t[0]:<14}{100*t[1]/v['pns']:5.1f}%")
    # ZUK 3rd char meaning test
    P("")
    P("  ZUK third character vs dominant leading noun (does the middle letter mean one thing?)")
    mid = collections.defaultdict(collections.Counter)
    for pn, v in base.items():
        if len(v["zuk"]) == 5:
            mid[v["zuk"][2]][noun(v["desc"])] += 1
    for ch in sorted(mid):
        c = mid[ch]
        tot = sum(c.values())
        top = c.most_common(3)
        P(f"    mid `{ch}` rows {tot:>7,}  top nouns: " +
          ", ".join(f"{n} {100*v/tot:.1f}%" for n, v in top))
    return 0


if __name__ == "__main__":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    raise SystemExit(main())

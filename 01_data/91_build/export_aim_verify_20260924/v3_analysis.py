# -*- coding: utf-8 -*-
"""VERIFY steps 1, 5, 6, 7: position, stratified sample, family/euro rollup, unverifiable.

Read-only.
"""
from __future__ import annotations

import csv
import json
import random
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(r"C:\Users\jerom\Desktop\claude\ISZE")
DER = ROOT / "01_data" / "00_derived"
EQ = ROOT / "01_data" / "91_build" / "export_aim_eq_20260924"
OUT = ROOT / "01_data" / "91_build" / "export_aim_verify_20260924"

VER = list(csv.DictReader((OUT / "verify_all.csv").open(encoding="utf-8-sig")))
by_pn = {r["pn"]: r for r in VER}

PUB = list(csv.DictReader((DER / "AIM_Master_PN_Categories_Figkey_20260924.csv").open(encoding="utf-8-sig")))
pub_by_pn = {r["part_number"].strip().upper(): r for r in PUB}

REP = []
def P(s=""):
    print(s)
    REP.append(s)


def num(s):
    s = (s or "").strip().replace(" ", "").replace("\u00a0", "")
    if not s:
        return None
    # EU format: 1.177,96  |  177,06  |  8 693.31 (mixed!)
    if "," in s and "." in s:
        if s.rfind(",") > s.rfind("."):
            s = s.replace(".", "").replace(",", ".")
        else:
            s = s.replace(",", "")
    elif "," in s:
        s = s.replace(",", ".")
    try:
        return float(s)
    except Exception:
        return None


# ------------------------------------------------------------------ step 1
P("=" * 78)
P("STEP 1 - THE POSITION ON DISK (re-measured, not read from a report)")
P("=" * 78)
master = list(csv.DictReader((DER / "aim_master_v2.csv").open(encoding="utf-8")))
m_pn = Counter((r.get("part_number") or "").strip().upper() for r in master)
mm = {}
for r in master:
    mm[(r.get("part_number") or "").strip().upper()] = r


def clean(s):
    s = "" if s is None or str(s).strip().lower() in ("nan", "none", "null") else str(s).strip()
    return s


def realv(v):
    v = clean(v)
    return bool(v) and not v.lower().startswith("unknown")


pns = list(by_pn)
real = unk = blank = norow = 0
for p in pns:
    r = mm.get(p)
    if not r:
        norow += 1
        continue
    v = clean(r.get("aim_l1_fixed")) or clean(r.get("aim_l1"))
    if realv(v):
        real += 1
    elif v.lower().startswith("unknown"):
        unk += 1
    else:
        blank += 1
P("price-list part numbers          : %d" % len(pns))
P("  carry a real AIM family        : %d" % real)
P("  open                           : %d" % (unk + blank + norow))
P("    - 'Unknown' marker           : %d" % unk)
P("    - master row, blank family   : %d" % blank)
P("    - no master row at all       : %d" % norow)
P("  sum check                      : %d" % (real + unk + blank + norow))
P("")
P("duplicate part numbers on the master: %d" % sum(1 for k, v in m_pn.items() if v > 1))
P("master rows total                : %d" % len(master))
P("master rows that are one of the 1,303: %d" % sum(1 for p in pns if p in mm))
P("")

# ------------------------------------------------------------------ step 7 basis
P("=" * 78)
P("STEP 7 BASIS - what the EPC actually returned")
P("=" * 78)
pubs = list(csv.DictReader((EQ / "classified.csv").open(encoding="utf-8-sig")))
found_empty = [r for r in VER if r["eq_status"] == "FOUND" and not r["eq_fig_name"]]
P("lookups: FOUND %d | NOT_FOUND %d | ERROR %d  (of %d part numbers)" % (
    sum(1 for r in VER if r["eq_status"] == "FOUND"),
    sum(1 for r in VER if r["eq_status"] == "NOT_FOUND"),
    sum(1 for r in VER if r["eq_status"] == "ERROR"), len(VER)))
P("FOUND but NO figure name recorded : %d" % len(found_empty))
fe_real = sum(1 for r in found_empty if r["master_triple"] and r["master_triple"].split(" > ")[0])
left_open = [r for r in found_empty if not (r["master_triple"] and r["master_triple"].split(" > ")[0])]
P("  of those, placed by something else (figure key): %d" % fe_real)
P("  of those, still open                          : %d" % len(left_open))
for r in left_open:
    P("      %s  %-32s fig %s" % (r["pn"], r["desc"][:32], r["fig_key"]))
P("")

# ------------------------------------------------------------------ step 6
P("=" * 78)
P("STEP 6 - WHAT A PERSON SEES FILTERING BY FAMILY")
P("=" * 78)
fam = defaultdict(lambda: dict(n=0, rule=0, figkey=0, desc=0, eur=0.0, eur_n=0))
for r in VER:
    p = r["pn"]
    pub = pub_by_pn.get(p)
    l1 = clean(pub["aim_level_1"]) if pub else ""
    if not realv(l1):
        continue
    f = fam[l1]
    f["n"] += 1
    l3 = clean(pub["aim_level_3"]) if pub else ""
    if not (l3 and not l3.lower().startswith("unknown")):
        # blank family on master -> other
        pass
    if r["rule_triple"]:
        f["rule"] += 1
    elif clean(r["fig_key"]) and clean(r["master_source"]).find("figure") >= 0:
        f["figkey"] += 1
    else:
        f["figkey"] += 1

    e = num(r["list_eur"])
    if e is not None:
        f["eur"] += e
        f["eur_n"] += 1

# provenance from the master's own stamp, per family
stamp = defaultdict(Counter)
for r in VER:
    p = r["pn"]
    pub = pub_by_pn.get(p)
    l1 = clean(pub["aim_level_1"]) if pub else ""
    if not realv(l1):
        continue
    stamp[l1][clean(r["master_source"])] += 1

ordered = sorted(fam.items(), key=lambda kv: -kv[1]["n"])
P("%-26s %6s %6s %6s %14s" % ("family (Level 1)", "parts", "rule", "other", "list EUR"))
for k, v in ordered:
    P("%-26s %6d %6d %6d %14s" % (k, v["n"], v["rule"], v["figkey"], ("%.0f" % v["eur"])))
P("")
P("--- provenance behind the same families (master aim_source stamp) ---")
for k, v in ordered[:10]:
    P("%s:" % k)
    for s, n in stamp[k].most_common():
        P("      %4d  %s" % (n, s))
P("")

# the five biggest by euro
P("--- the five families by list-price total (Price column, EUR) ---")
for k, v in sorted(fam.items(), key=lambda kv: -kv[1]["eur"])[:5]:
    P("  %-26s %14s EUR   over %d parts" % (k, "%.0f" % v["eur"], v["eur_n"]))
tot = sum(v["eur"] for v in fam.values())
P("  %-26s %14s EUR   over %d parts" % ("TOTAL placed", "%.0f" % tot, sum(v["n"] for v in fam.values())))
P("")

# provenance of the newly placed = the stamp from today
P("--- provenance of the parts placed TODAY (stamp export_aim_eq_20260924) ---")
today = [r for r in VER if "export_aim_eq_20260924" in clean(r["master_changed"])]
P("parts carrying today's stamp: %d" % len(today))

# ------------------------------------------------------------------ step 5
P("=" * 78)
P("STEP 5 - STRATIFIED SAMPLE, RULE REPRODUCED vs FAMILY ON THE MASTER")
P("=" * 78)
placed = [r for r in VER if r["master_triple"] and realv(r["master_triple"].split(" > ")[0])]
P("placed parts to sample from: %d" % len(placed))
# strata: family x list-price band
withp = [r for r in placed if num(r["list_eur"]) is not None]
withp.sort(key=lambda r: num(r["list_eur"]))
n = len(withp)
bands = [("A: <10 EUR", 0, 10), ("B: 10-50", 10, 50), ("C: 50-200", 50, 200),
         ("D: 200-1000", 200, 1000), ("E: >1000", 1000, 1e12)]
random.seed(20260924)
sample = []
for label, lo, hi in bands:
    pool = [r for r in withp if lo <= num(r["list_eur"]) < hi]
    if not pool:
        continue
    # spread across families inside the band
    byfam = defaultdict(list)
    for r in pool:
        byfam[(pub_by_pn.get(r["pn"], {}).get("aim_level_1") or "")].append(r)
    take = max(1, round(10 * len(pool) / n))
    chosen = []
    for f, lst in byfam.items():
        chosen.append(random.choice(lst))
    while len(chosen) < take:
        c = random.choice(pool)
        if c not in chosen:
            chosen.append(c)
    chosen = chosen[:max(take, 8)]
    sample.extend(chosen)
# top up to at least 45 and include the top-value parts
sample = list({r["pn"]: r for r in sample}.values())
sample.sort(key=lambda r: -num(r["list_eur"]))
top20 = sorted(withp, key=lambda r: -num(r["list_eur"]))[:12]
for r in top20:
    if r["pn"] not in {x["pn"] for x in sample}:
        sample.append(r)
P("sample size: %d parts" % len(sample))
agree = separate = disagree = 0
P("")
P("%-12s %-28s %-9s %-46s %s" % ("part", "description", "list EUR", "family now on the master", "verdict"))
for r in sample:
    p = r["pn"]
    pub = pub_by_pn.get(p, {})
    onmaster = " > ".join([clean(pub.get("aim_level_1")), clean(pub.get("aim_level_2")),
                           clean(pub.get("aim_level_3"))])
    if r["rule_triple"]:
        v = "AGREE (rule)" if r["rule_triple"] == r["master_triple"] else "DISAGREE (rule)"
        if v.startswith("AGREE"):
            agree += 1
        else:
            disagree += 1
    else:
        v = "placed WITHOUT a rule (EPC name / key)"
        separate += 1
    P("%-12s %-28s %-9s %-46s %s" % (p, r["desc"][:28], r["list_eur"], onmaster[:46], v))
P("")
P("rule reproduced and agreed with the master : %d" % agree)
P("rule reproduced and disagreed              : %d" % disagree)
P("placed from an EPC-name/key route, counted separately: %d" % separate)
P("")

(OUT / "verify_steps_1_5_6_7.txt").write_text("\n".join(REP), encoding="utf-8")

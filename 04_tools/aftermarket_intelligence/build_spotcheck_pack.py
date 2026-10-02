# -*- coding: utf-8 -*-
"""
Build the human spot-check pack: 20 competitor numbers for someone with a browser to look at.

Why this exists
---------------
Every edge in the cross-reference graph was produced by a script. Nobody has ever looked at one.
2,004 of the 2,461 rival numbers rest on a SINGLE source file (corrected 2026-09-24). Before any money is spent on a scrape
or a licence, twenty of them should be checked by eye: does a shop really list this number as
fitting an Isuzu, is the price real, is the pack quantity what we assume.

Selection: the strongest-evidence numbers that carry NO price yet (43 exist), plus a spread across
categories so the check tests more than one family. Ties broken by how many of our parts the
number claims to fit.

Nothing is fetched. The output is a working file for a person.

Run: python 04_tools/aftermarket_intelligence/build_spotcheck_pack.py
"""
import re
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
OUTDIR = ROOT / "01_data/90_INBOX/_aftermarket_spotcheck_20260924"
OUTDIR.mkdir(parents=True, exist_ok=True)

edges = pd.read_csv(HERE / "state/crossref_edges.csv", dtype=str)
edges["price"] = pd.to_numeric(edges.competitor_price, errors="coerce")
edges["has_competitor_price"] = edges.has_competitor_price.astype(int)

# rival only
r = edges[(edges.is_our_own_line.astype(int) == 0) & (edges.is_peer_carrier.astype(int) == 0)].copy()

import sys as _sys
_sys.path.insert(0, str(ROOT / "04_tools" / "_shared"))
from classification_paths import figkey_export_for_release  # noqa: E402
# AIM figure-key export of the APPROVED release (sidecar + sha256 checked; raises otherwise)
FIGKEY_EXPORT, _FIGKEY_RELEASE = figkey_export_for_release()
master = pd.read_csv(FIGKEY_EXPORT, dtype=str)
master["part_no"] = master.part_number.astype(str).str.strip()
master = master.drop_duplicates("part_no")
desc = dict(zip(master.part_no, master.description))
l1 = dict(zip(master.part_no, master.aim_level_1.fillna("")))

g = r.groupby("cpn_key").agg(
    n_sources=("source", "nunique"),
    n_parts=("part_no", "nunique"),
    has_price=("has_competitor_price", "max"),
    brands=("competitor_brand_norm", lambda s: "|".join(sorted(set(s.dropna())))),
    sources=("source", lambda s: "|".join(sorted(set(s.dropna())))),
    newest=("source_vintage", "max"),
).reset_index()
g["priced"] = g.has_price.astype(int)
n_all, n_single = len(g), int((g.n_sources == 1).sum())

# a readable example: the biggest-billed part it claims to fit, plus its family
billed = pd.read_csv(ROOT / "04_tools/delegation/state/refresh_tiers_LOCAL.csv",
                     dtype={"part_no": str})
billed["part_no"] = billed.part_no.astype(str).str.strip()
billed["billed_eur_t12m"] = pd.to_numeric(billed.billed_eur_t12m, errors="coerce")
val = dict(zip(billed.part_no, billed.billed_eur_t12m))


def example(key):
    d = r[r.cpn_key == key]
    pns = sorted(set(d.part_no), key=lambda p: -(val.get(p, 0) or 0))
    parts = []
    for p in pns[:2]:
        parts.append(f"{p} {desc.get(p, '')} [{l1.get(p, '')}]")
    return " ; ".join(parts)


g["example_isuzu_application"] = g.cpn_key.map(example)

# ---- pick 20: strongest unpriced first, then spread across families
unpriced = g[(g.n_sources >= 2) & (g.priced == 0)].sort_values(
    ["n_sources", "n_parts"], ascending=False)

picked, seen_fam = [], set()
for _, row in unpriced.iterrows():
    fam = example(row.cpn_key).split("[")[-1].rstrip("]")
    if fam in seen_fam and len(picked) < 14:
        continue
    picked.append(row)
    seen_fam.add(fam)
    if len(picked) == 15:
        break

# fill the remaining 5 from priced numbers with 3+ sources, for contrast
priced = g[(g.priced == 1) & (g.n_sources >= 3)].sort_values(
    ["n_sources", "n_parts"], ascending=False)
for _, row in priced.iterrows():
    if len(picked) >= 20:
        break
    if row.cpn_key not in {p.cpn_key for c, p in [(None, x) for x in picked]}:
        picked.append(row)

out = pd.DataFrame(picked).head(20).copy()
out["what_we_claim"] = out.apply(
    lambda x: f"{x.brands} {x.cpn_key} fits {x.example_isuzu_application}", axis=1)
out["check_1_does_it_fit"] = ""       # yes / no / unsure
out["check_2_price_real"] = ""        # the price on the page, as seen
out["check_3_pack_quantity"] = ""     # e.g. 'per axle', 'set of 2', 'each'
out["check_4_url"] = ""
out["notes"] = ""
out["row_id"] = range(1, len(out) + 1)

cols = ["row_id", "cpn_key", "brands", "n_sources", "n_parts", "priced", "sources", "newest",
        "example_isuzu_application", "what_we_claim",
        "check_1_does_it_fit", "check_2_price_real", "check_3_pack_quantity", "check_4_url",
        "notes"]
out = out[cols]
out.to_csv(OUTDIR / "SPOTCHECK_20.csv", index=False, encoding="utf-8-sig")
out.to_excel(OUTDIR / "SPOTCHECK_20.xlsx", index=False)

# a one-page how-to
fam_mix = out.example_isuzu_application.str.extract(r"\[([^\]]*)\]")[0].value_counts()
howto = f"""SPOT CHECK — 20 competitor numbers
Built {datetime.now(timezone.utc).isoformat(timespec='seconds')} · read-only build, nothing fetched

WHY
Every link in the competitor cross-reference was made by a script. Not one has been looked at by a
person. {n_single:,} of the {n_all:,} rival numbers rest on a single source file. This pack is 20 of them,
chosen where the evidence is strongest and where we hold NO price yet, so the check is testing
whether the matches are real rather than re-testing a number we already have.

WHAT TO DO
Open SPOTCHECK_20.xlsx. One row per competitor number. For each, search the competitor number plus
the brand on any shop you use, and answer four things:

  1. does it fit   — does a shop list this number as fitting an Isuzu? yes / no / unsure
  2. price real    — the price you see on the page, and the currency
  3. pack quantity — is it each, a set of two, per axle, a kit? This is the one that quietly breaks
                     price comparisons: a pad set per axle against per wheel is a factor of two.
  4. url           — the page you looked at

Leave a row blank if you cannot check it. A blank is worth more than a guess.

HOW LONG
About 30 seconds to a minute a row, so 15 to 20 minutes for the twenty.

WHAT WE DO WITH THE ANSWER  (rule fixed 2026-09-24, BEFORE any result came back - do not move it)
Count, over the 20 rows:
  WRONG        = check 1 answered "no", or the pack quantity found does not match our part's
  UNVERIFIABLE = row left blank, or check 1 answered "unsure"

  - WRONG 4 or more                      -> stop the cross-reference approach; put the money into
                                            a paid licence instead.
  - WRONG + UNVERIFIABLE 8 or more       -> same: stop, buy a licence.
  - anything else                        -> carry on. This is "not disproven", not "validated":
                                            even 0 wrong out of 20 still allows an error rate of
                                            up to about 15%.

WHAT IS IN THE PACK
15 numbers found in 2 or more source FILES and NO price held (files, not independent witnesses).
 5 numbers with 3 or more sources and a price, to check a number we think we already have.
Families covered: {", ".join(f"{k} ({v})" for k, v in fam_mix.items())}

CAUTION ON THE EVIDENCE COLUMN
'n_sources' counts distinct FILES, not independent confirmations. The Eucon generations partly
repeat each other, so 3 sources is not three witnesses. That is exactly why this check exists.
"""
(OUTDIR / "READ_ME_FIRST.md").write_text(howto, encoding="utf-8")

(OUTDIR / "OPEN_SPOTCHECK.cmd").write_bytes(
    b'@echo off\r\nstart "" "%~dp0SPOTCHECK_20.xlsx"\r\n')

print(f"pack written: {len(out)} rows")
print(out[["row_id", "cpn_key", "brands", "n_sources", "priced"]].to_string(index=False))
print()
print("families:", dict(fam_mix))
print()
print("files:")
for f in sorted(OUTDIR.iterdir()):
    print("  ", f.name, f.stat().st_size)

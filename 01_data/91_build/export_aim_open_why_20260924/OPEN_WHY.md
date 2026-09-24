# Why are there still 1,097 open?

**Prepared 2026-09-24 · read-only · nothing changed in the AIM master, any dated file, or anything
under `01_data\00_derived\`.**

The short answer: 845 of the 1,097 are not open because the data is missing. They carry the word
`Unknown` written into the family column of the main parts table, and the file that Power BI loads
reads that word as an answer and puts it ahead of any family we would write underneath. The
remaining 252 are genuine data gaps, and 43 of those have no row in the parts table at all.

---

## First, the count

The queue holds 1,311 rows but 1,303 different part numbers, because eight parts appear twice. Of
those 1,303, today's two passes placed 206 (44 added as new rows, 162 filled in on rows that were
blank). That leaves **1,097 part numbers with no family**, and every one of them is accounted for
below. The 206 that closed all carry the stamp `export_pr00_20260924`.

One correction to a number you may have seen: the earlier note said the master had 87 part numbers
with no row at all. Measured against the master as it stands now it is **43**, because all 44 of the
part numbers that had no row were added this afternoon. The 43 still without a row are a different,
genuinely absent set. They are not a leftover of the 44.

---

## The split, all 1,097, nothing rounded away

| Why it is still open | Parts | Share | List price |
|---|---:|---:|---:|
| The word `Unknown` is written in the family column and wins over any family underneath | 845 | 77.0% | 43,837.98 |
| The wording on the part has never appeared on the main table, so there is nothing to match | 146 | 13.3% | 6,863.50 |
| The part has no row in the main table at all, so there is nowhere to write a family | 43 | 3.9% | 18,898.61 |
| The wording exists on the main table but on only one or two parts | 31 | 2.8% | 1,108.38 |
| Wordings we deliberately held back (lamps, two gaskets, a power-steering pump, a clutch cylinder) | 11 | 1.0% | 1,482.00 |
| The wording itself is split across more than one family on the main table | 8 | 0.7% | 3,624.38 |
| The only family the wording ever lands in is one of the five catch-all families | 6 | 0.5% | 5,315.53 |
| The wording is clear but the figure key behind it is not, so the check cannot pass | 4 | 0.4% | 124.07 |
| One family, but the main table files the wording under two different sub-groups | 2 | 0.2% | 84.56 |
| The figure key names one family and it is not the one the wording names | 1 | 0.1% | 0.60 |
| **Total** | **1,097** | **100.0%** | **81,339.61** |

The ten numbers add to 1,097 exactly. The script prints that check on every run and refuses to
finish if it does not reconcile.

There is a second, plainer way to read the same 1,097, and it is the one I would put in front of
anyone: 209 have a row in the published file but a blank family, 845 show `Unknown`, and 43 have no
row at all. Those three are disjoint and also sum to 1,097. Not one of the 1,097 shows a real family
in the published file, which is the check that proves nothing was placed and then hidden.

---

## The 20 highest-priced parts in the biggest group

This is the 845 that say `Unknown`. Price is the list price, ordered by price, not by part number.

| Part | List EUR | What the part says |
|---|---:|---|
| 7552440900 | 1,424.92 | CASE; RR AXLE |
| 8975027141 | 1,179.06 | CONTROLLER; ABS |
| 7552357310 | 1,177.96 | HYDRAULIC UNIT; ANTI LOCK BRK |
| 8974848540 | 1,175.65 | HYDRAULIC UNIT; ANTI LOCK BRK |
| 8978769020 | 1,157.36 | CONTROLLER; ABS |
| 8976881030 | 990.27 | HYDRAULIC UNIT; ANTI LOCK BRK |
| 8982324801 | 860.85 | HYDRAULIC UNIT; ANTI LOCK BRK |
| 8981415211 | 701.50 | AXLE; FRT |
| 8982568371 | 641.23 | COMPRESSOR ASM; A/C |
| 8973509931 | 568.34 | TANK; FUEL |
| 8975503180 | 559.10 | CONVERTER ASM; TORQUE,A/T |
| 8981512140 | 516.21 | RAIL ASM; COMMON |
| 8980563890 | 502.31 | CONVERTER ASM; TORQUE,A/T |
| 8984818621 | 447.02 | CASE; RR AXLE |
| 8974254120 | 444.74 | BACK ASM; SEAT |
| 8974641320 | 415.72 | BACK ASM; SEAT |
| 8982415692 | 414.00 | MODULATOR; RR |
| 8975451910 | 411.75 | COMPRESSOR ASM; A/C |
| 8981992711 | 401.42 | AXLE; FRT |
| 8983938821 | 397.10 | COOLER ASM; A/T SECONDARY |

Read those twenty and the point of the whole exercise is visible: a rear axle case, an ABS
controller, an anti-lock hydraulic unit, a fuel tank, a torque converter, a seat back. These are
easy. Not one of them needs the parts catalogue to tell us what it is. They are open because a
decision has not been taken about the word `Unknown`, not because the answer is hard.

Of the 845, 228 do carry wording that could be used the moment the marker is lifted: 214 name one
family, 14 name more than one. The other 617 carry no wording the main table recognises at all, so
for those the marker is only the first of two problems.

---

## What it would actually take

**(a) A rule that allows fewer than three supporting parts.** This clears **31** parts outright —
wordings the main table knows but that sit on only one or two parts. That is a small win and a
slightly riskier one, because a family backed by one example is a guess. If you also let the rule
use single-family wordings of any size, stop refusing the five catch-all families, pick a sub-group
where two are strong, and stop letting the figure key veto, the ceiling is **53**. That is the most
any softening of the rule buys, and it is 5% of the open total.

**(b) The parts-catalogue (Snap-on EPC) lookups.** These are needed for **199** parts and no rule
can substitute for them. That is the 146 with wording the main table has never carried, the 8 whose
wording is split across families, the 2 that split across sub-groups, the 43 with no row at all, and
a handful more. Every one of them has to be looked up or left alone; there is no row evidence to
reason from.

**(c) Deciding the `Unknown` marker.** This is the big one and it unlocks **845**. Clearing the
marker is not the same as placing them all, and I want to be precise about the split:

- **88** have wording that means one family with the figure key agreeing. A plain re-run places
  these the moment the marker is gone, with no change to the rule at all.
- **113** have wording the main table carries but on fewer than three parts, so they need the
  marker cleared *and* the relaxed rule from (a).
- **27** resolve to one family but stop on a sub-group split, a figure key that is itself
  multi-family, or one of the wordings we held back by hand.
- **14** have wording that is split across more than one family.
- **617** have no wording evidence at all. Clearing the marker does nothing for these; they still
  need the catalogue.

So of the 845, **228 could be placed from the row itself** (88 immediately, 140 with the relaxed
rule), and **617 cannot**.

The honest arithmetic, with the overlaps removed rather than added up twice: the most any rule
change can clear is **898 of 1,097**. The remaining **199 need the catalogue walk**, because the
main table either has never seen the wording or contradicts itself about it.

Putting it as work rather than as percentages: clearing the marker and re-running settles 88 today
and up to 228 with a softer rule; 199 parts need a real lookup; and 617 parts are waiting on both.

---

## Is anything open for a bad reason?

No processing error, no join failure, and no missing part number. I checked each one:

- **No part is lost to the join.** All 1,097 queue part numbers are found on the price extract, all
  are ten digits, none starts with a zero, and none is a non-numeric code. There are no `REBATE` or
  `TRANSPORT` style entries in this queue. Forty-three have no row in the main table, and I
  hand-checked the 44 that were added today to be sure those are not the same parts: all 44 now
  carry a family and today's stamp, so they are closed, not open.
- **No part was placed and then lost.** The published file shows a real family on **0** of the
  1,097. A blocked write would show a family on some of them.
- **No part is open because of a figure-key mistake.** The figure key explains 5 of the 1,097 and
  each one is a documented trap, not a fault: four where the key itself carries more than one
  family, and one (8943365110, GASKET; DRAIN PLUG, list EUR 0.60) where the wording says Lubrication
  on nine parts and the key says Transmission on one. The key is used as a veto only, so the rule
  stops rather than guessing.
- **The 11 "held back" parts are a decision, not a defect.** They are the lamp wordings, a
  cylinder-head gasket, an engine overhaul gasket set, a power-steering pump and a clutch master
  cylinder. In each case the main table's own label is the thing in doubt — it files the 79
  cylinder-head gaskets and 112 overhaul gasket sets under Transmission, and it splits lamp
  wordings between body and electrical with no logic in the row. The rule faithfully copies the
  table, so I did not let it place those.

If you want one sentence for the whole thing: nothing is broken, and the queue is not stuck on the
tooling.

---

## How I know these numbers hold

The earlier pass got 1,097 in one run and 1,170 in another, with the largest group at 129 or 202.
The difference came from two things, and I fixed both by rebuilding the wording dictionary the way
the published file actually builds its own label, rather than from the plain family column:

1. The published file prefers the `fixed` version of the family column over the plain one, and lays
   the separate classification file on top. Reading only the plain column loses 967 rows where the
   two disagree.
2. Part numbers are text on both sides. Comparing them as numbers drops anything that is not
   purely digits.

I then checked the dictionary against today's own work, which is the only test that matters: across
all 206 parts that were placed today, the dictionary's prediction matches the family that was
written in **206 of 206** cases, no exceptions. So this is not a second opinion about the rule; it
is the same rule, reproduced.

Two earlier counts in my own draft were wrong and I corrected them before this report. An early run
put 24 parts in a "the rule should have placed this" pile, almost all of them the lamp and gasket
wordings the rule was told to hold back. The figure-key veto and the sub-group guard were also not
modelled, which is what made that pile look like a defect. The corrected run has no such pile at
all, and the eight small groups above are each named, not swept into an "other".

---

## What I did not establish

- I did not hand-read the 845 `Unknown` parts. I read the twenty above and the wording statistics,
  and I am telling you the shape rather than claiming every row is decidable.
- I did not check the `Value` column of the price extract. It does not agree with the list price
  total and nobody has explained what it multiplies, so it is not used anywhere here.
- I did not run a single catalogue lookup, as instructed. The 199 figure is a count of parts with no
  row evidence, not the result of trying.
- I cannot say whether clearing the marker is the right call. That is the decision, and it is
  genuinely yours: the word `Unknown` was written into the table on purpose, and 4,936 rows carry it
  master-wide. Lifting it for these 845 is a change to a deliberate judgement, not a cleanup.

---

## Files

Everything for this answer sits in `01_data\91_build\export_aim_open_why_20260924\`:

- `open_why.py` — the one script. Self-checking; it fails loudly rather than rounding.
- `open_parts_classified.csv` — all 1,097 with the one reason each, the wording evidence, and the
  blocked-blocked-would-be answer.
- `open_group_counts.csv` — the counts on their own.
- `summary.json` — the headline numbers.
- `run_log.txt` and `run_console.txt` — the full output of the run.

Nothing was written under `01_data\00_derived\`. No browser, no catalogue lookup, no mail.

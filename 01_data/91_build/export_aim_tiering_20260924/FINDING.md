# Do the 1,311 IE40 parts all need the EPC lookup?

**Prepared:** 2026-09-24 · read-only · nothing changed in the AIM master, any derived file, or any dashboard.
**Question:** does every part in the queue have to go through the Snap-on EPC scraper, or can some be classified from the price row itself?

## The short answer

No. About 300 of the 1,303 part numbers can be given a family from the row itself, and those 300 carry
45% of the list value on the queue. That leaves roughly 1,000 that genuinely need the lookup, plus 15
that look decidable but are not.

The reason is not that the descriptions are good. It is that some of them are *system names* rather than
*component names*. "ENGINE ASM" names the system. "GASKET" does not: a gasket belongs to whatever it
seals, and the row does not say what that is.

## The tier split

| | rows | part numbers | list price, EUR |
|---|---|---|---|
| **Tier A — decidable from the row** | 301 | 300 | 59,275 |
| Tier A look-alikes I could not defend | 15 | 15 | 3,420 |
| **Tier B — needs the EPC lookup** | 995 | 988 | 67,482 |
| Queue total | 1,311 | 1,303 | 130,177 |

On those numbers, narrowing the run by the 300 Tier A parts takes 23% of the lookups off the queue and
45% of the list value with them. That is the whole argument for doing it: the expensive rows are exactly
the ones that can be read off the page.

I am quoting list price, the column headed `Price`. The column headed `Value` is not comparable between
parts in the way you would expect: on the export rows it totals 296,107 against a list-price total of
132,339, and on one row in nine the two are identical. I could not establish what it multiplies, so I did
not use it as the money.

## The rule behind Tier A, and why it is safe

A row is Tier A when all three of these hold:

1. **The exact description already means one family on the current AIM master, with at least three part
   numbers behind it.** So "TURBOCHARGER ASM" resolves because 38 master part numbers carry that exact
   text and all 38 sit in Intake Exhaust Emission. This is the test the file that needs the families
   already uses; for a part of this consequence I would rather resolve it the way the existing file
   resolves it than introduce a second convention.
2. **The figure key on the row does not contradict it.** Either it agrees, or the key has no master
   evidence at all. If the key says something different, the row is out.
3. **The family is not one of the residual buckets.** Nothing lands in Maintenance Service, Literature
   Marketing, Tools Equipment, Logistics Packaging or Fluids Chemicals.

Of the 301 clean rows, 291 carry a figure key that agrees with the description; 10 rest on the
description alone, and those 10 are the engine-assembly keys (`001-*`) which have no master history yet.

## Your "ENGINE ASM" example — yes, it is safe

The row is part 8981422000, list price EUR 8,693.31, the largest ticket item in the queue. Twenty-seven
part numbers on the master carry the exact text "ENGINE ASM" and all twenty-seven are on Engine. In the
separate classified price workbook, 73 rows read "ENGINE ASM" and all 73 sit on the leaf called "Engine
assembly". Two independent routes agree and the words themselves name the system.

One thing to be straight about: it is safe because the words mean what they say, not because the rule
proved anything. The rule only knows that this text has always landed on Engine. For "ENGINE ASM" that
is enough. For "GASKET" it would not be, and I have excluded those.

## What the commodity code is worth

You were right that the customs code should tell us something. It tells us less than you would expect.

The codes are real ten-digit customs codes, 117 distinct values across the queue, and 1,297 of the 1,311
rows carry one. The trouble is that a customs code classifies a *material and a broad kind of article*,
not a part's job on the truck. Measured against the parts that are already classified:

- 194 codes appear; 115 of them carry **more than one** AIM family.
- If you always take the most common family for a code, you are right on 63% of parts — one part in three
  goes to the wrong family.
- The biggest code on the queue, 8708999790 with 207 rows, is split across 14 families *within the queue
  itself*, and on the master across 19: Chassis Frame 797 parts, Accident & Body 222, Cabin Interior 144,
  Electrical 127, Fuel System 124, and so on.
- Where both a commodity-code route and a description route exist for a queue row, they disagree on 243
  of 506 rows.

So the code is a good smell test and a useless assignment. It would put every rubber part, every bracket
and every plastic trim into one bucket.

## The description is better, but it is the same trap the audit found

Descriptions work far better than codes, but they are not a clean key either, and the file you already
have is right to say so. On the current master, 3,990 distinct descriptions, 27 of them carry more than
one family. On the independent classification file, 13,541 descriptions and 2,300 of them carry more than
one family — which is where the audit's 71 came from, measured on its own basis.

The figure-key trap also reproduces exactly as documented, and two rows of the queue sit on it:

- Key `220-001` holds 38 master parts, every one labelled "Literature Marketing > Manuals > Manual",
  while the text on all of them reads "TRANSMISSION ASM; MANUAL". Queue parts 8976646550 and 8975480980
  would both have been filed as marketing literature by a figure-key shortcut. Their list prices are
  5,112.02 and 2,379.90.
- Key `011-001` holds 12 parts read as "HEAD ASM; CYL" and all 12 are Engine > Cylinder Head. Queue parts
  7553116080 and 8982703783 sit there, and Engine is the right answer for those two.

Neither row is damaged by my rule, because in both cases I use the description and the key only as a
veto, never as the source.

## The rows I could not defend

Fifteen rows look decidable and are not. I have taken them out of Tier A.

**Three rows where the master's own label is wrong.** The master files all 79 parts described "GASKET;
CYL HD" and all 112 described "GASKET SET; ENG OVERHAUL" under Transmission. A cylinder-head gasket and
an engine overhaul gasket set are engine parts. The rule is faithfully reproducing somebody else's
mistake, so I will not hand those to you as answer.

**Ten rows where the family is a convention rather than a fact.** Lamp rows are split between Accident &
Body and Electrical with no logic I can find: "LAMP ASM; HEAD" is Accident & Body on 161 parts while
"LAMP ASM; FOG" is Electrical on 35. Nothing in the row tells you which side a lamp lands on. Same for
"PUMP ASM; OIL,P/S", which sits under Fuel System and is a power-steering pump, and "CYLINDER ASM;
CLUTCH MASTER", which sits under Brakes and is a clutch part.

Together those 15 rows are only EUR 3,420 of list price, but they are the reason I would not let the rule
run unattended over the whole queue.

## The honest limit of the whole thing

Every Tier A family comes from a description join, and that join is the thing your audit flagged as
non-deterministic. The rule is safe only where the description names a system. Where the description
names a component whose family depends on where it is fitted — gasket, hose, pipe, bracket, cover, lamp —
consistency on the master is not the same as being right. I filtered for that as far as I can without
reading every row by hand. I did not read all 301.

## What I would do

Narrow the run in progress by the 300 Tier A part numbers and let it spend its time on the ~1,000 that
need it. Send the 15 carved-out rows to the lookup as well, or look at them yourself — they are cheap and
they are the ones that will embarrass the file if they go through unchecked.

Two things I did not verify and am not claiming: I did not confirm the `Value` column's arithmetic, and
I did not hand-check every one of the 301 rows. I hand-checked 20 of them across the price range and all
20 agreed with the rule.

---

Sources, all read-only:
`01_data/EXPORT.XLSX` · `01_data/91_build/export_aim_eq_20260924/queue.csv` ·
`01_data/00_derived/aim_master_v2.csv` · `01_data/00_derived/aim_pn_classification.csv` ·
`01_data/00_derived/_audit_cls_pr00_flat.csv` ·
`01_data/01_Pricing/IE40 Price list as of 13.03.2026 PR00_3_level_classified_GPT.xlsx` ·
`03_analytics/Isuzu/prism/docs/AIM_CLASSIFICATION_AUDIT_2026-09-17.md`

Working files: `01_data/91_build/export_aim_tiering_20260924/`
(`queue_final_tiered.csv` = every queue row with its tier; `tierA_audited.csv` = the 316 rule rows with
the 15 carve-outs marked; `run_log_final.txt` = the full measurement log).

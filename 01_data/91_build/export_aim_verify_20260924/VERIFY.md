# Verification of the IE40 AIM classification — 24 September 2026

**Read-only verification.** Nothing under `01_data\00_derived\` was written. No browser, no EPC
lookup, no dashboard. This note and the working files beside it are the only things created.

Working folder: `01_data\91_build\export_aim_verify_20260924\`

---

## The short answer

The labels hold up better than the write-ups suggest. I re-derived the 32 orphan placements from
the raw lookup file and the rule table rather than from the report, and all 32 reproduce exactly. I
re-derived the wording rule behind every part that carries an EPC figure name, and it agrees with
the family now on the master in every case. A stratified sample of 60 placed parts across the whole
price range, in 15 families, found no disagreement.

Three things need eyes before this leaves the machine, and only the first is a wrong label:

1. **18 parts depend on an accidental tie, not on the rules.** Where two wording rules are the same
   length, the one that happens to sit higher in the file wins. One is the flagged oil filter; a
   second puts eight switch and antenna parts on the electrical leaf when the instrument panel is
   arguably the better reading.
2. **The three connectors.** The stated reason for leaving them out does not hold as written. The
   decision to wait is still right, but it is a decision, not a measurement.
3. **The pump kit is on the wrong leaf** within the right family. One line, no euro moves.

---

## 1. Where the file actually stands

Measured on `aim_master_v2.csv` and `queue.csv` as they sit on disk now, not read from a report.
Family is taken the way the published table takes it: `aim_l1_fixed` where it is populated,
otherwise `aim_l1`.

| | part numbers |
|---|---:|
| on the price list | 1,303 |
| carry a real family | 1,224 |
| open | 79 |
| — carrying the `Unknown` marker | 45 |
| — a master row with a blank family | 23 |
| — no row on the master at all | 11 |

**1,224 + 45 + 23 + 11 = 1,303.** The count reconciles exactly.

The brief's 1,303 is the queue, and it is exact. The extract itself is a little larger: 1,318 price
lines over 1,310 distinct "newest" part numbers. Seven part numbers in the extract were never put
into the queue, and six of the seven already carry a family on the master. The seventh,
`5852530011` (clutch pilot align, €50.42), is marked `Unknown`. So the honest headline is **1,224 of
the 1,310 part numbers in the extract carry a real family (93.4%)**, or 1,224 of the 1,303 the work
was tracked on (93.9%).

The brief's "1,236 of 1,303" is 12 above anything I can measure. The main write-up says 1,240 of
1,318 *price lines*, which does measure true line by line, and that is very likely where the 1,236
came from — a line count carried onto a part-number denominator. The two are not comparable.

The brief's 67 does not reconcile either. 67 = 25 + 31 + 11. The 25 stands: the classification
overlay carries a marker on exactly 25 of the 1,303. The 11 stands. The 31 does not — the same file
has 19 usable rows with no family and the master has 23, and I measured every column of the overlay
against this list without finding 31. The split that does reconcile is 45 + 23 + 11 = 79. The
difference is not an error in the work, it is that 67 counts the overlay and 79 counts the master,
and the two files disagree on which parts are blocked.

**What a person actually sees.** The published table (`AIM_Master_PN_Categories_Figkey_20260924.csv`
and its Excel twin) reads the same as the master: 1,224 with a family, 79 open, 19 families in use.
It is not stale.

By money, the whole price list is about **€129,060** of list value. Parts with a real family carry
**€115,978 (89.9%)**; the open parts carry **€13,082 (10.1%)**. The open euros are not spread
evenly. They include a €7,603 service cab assembly, a €1,178 ABS hydraulic unit whose lookup
errored, an €861 ABS hydraulic unit, an €810 drum of coolant and a €426 blank.

A note on my own arithmetic. I read two different totals for the same thing while working, €129,060
and €131,223, and the difference was mine. The `Price` column mixes Dutch and US punctuation — 1,300
rows read `177,06` and 18 read `8 693.31` — so a parser that assumes one convention turns `1 177,96`
into 117,796. Treat the euro figures in this note as good to about a percent, not to the cent.

## 2. The 32 orphans, re-derived

I did not trust the appends. For each of the 43 parts with no master row I took the figure name out
of the raw lookup file (`eq_results.jsonl`), ran it through the 177 wording rules with my own
longest-phrase-first match and my own Level-3 alignment, and then read the master.

| | |
|---|---:|
| orphans with a figure name in the raw lookup | 32 |
| my re-derived family matches the master exactly | **32 of 32** |
| my re-derived family also matches what `classified.csv` recorded | 32 of 32 |
| orphans with a rule match and no figure name | 0 |
| orphans with no figure name, correctly left open | 11 |

Every one of the 32 landed on a triple that already exists on the master. None needed the Level-3
alignment nudged — the rule's own Level 3 was already a live leaf in every case.

The evidence is stronger than "second-hand" suggests. The figure name is not inherited prose; it is
recorded first-hand in `eq_results.jsonl` by the run that did the lookup. What was inherited is the
*reading* of it, and that is exactly what I re-did. It passes.

The 11 left open are the right 11: 8 have no EPC record at all, and the other 3 are the connectors
dealt with in §4.

## 3. The three flagged placements

**`7552062110 FILTER ASM; OIL` — written to `Cooling > Radiator > Radiator Assembly`. I would keep
it, but for a better reason than the report gives.**

This is the worst of the three and the report does not say why. The figure name is `0-50 - OIL COOLER
AND OIL FILTER`, and two rules are exactly ten characters long: `OIL COOLER` (line 70 of the file)
and `OIL FILTER` (line 172). The tie is broken by document order, so `OIL COOLER` wins because it is
written higher up. That is not a judgement about the part, it is an accident of where two lines sit.
Had `OIL FILTER` been typed first, this part would be under the maintenance oil filter.

Nine parts share that figure name. Eight are genuine oil coolers, cooler gaskets and an oil-cooler
thermostat, and the rule files all nine the same way. This is the only part on the figure whose own
description is an oil filter, and its own description's convention points elsewhere: 10 of the 11
master parts reading `FILTER ASM; OIL` sit on `Maintenance Service > Filters (unspecified) > Filter
Assembly` and none on Cooling. So the label is defensible as "which figure does it sit on" and wrong
as "which system is this part for".

**Keep it, but only if you decide once that a part takes the system of the figure it sits on.** If
you would rather it take its own system, this one and two others move — see §6.

**`7552710010 PUMP KIT` — written to `Intake Exhaust Emission > DEF System > DEF Tank`. I would
move it, one leaf across.**

The figure is `1-46 - DEF TANK AND PIPING` and only one rule matches, so there is no tie and no rule
error. But `DEF System` already has a leaf called `DEF Pump`, carrying five parts all reading `PUMP
ASM; DEF,DCM SPLY`. A pump kit for the DEF system belongs on the DEF pump leaf, not the tank leaf.
The report's alternative — a fuel pump — is the weaker of the two: its four supporting parts are the
thinnest evidence in the whole set. The right answer is the third option neither route considered:
same family, right leaf.

**`8974210030 TRAY; INST` — written to `Cabin Interior > Dashboard & Controls > Knob`. Borderline; I
would leave it and note it.**

Same shape as the oil filter. The figure is `7-40 - INSTRUMENT PANEL AND BOX`, and the authorized
rule maps `INSTRUMENT PANEL` to the knob leaf. The leaf name is the problem, not the part: that leaf
holds 90 parts and is what the master uses for everything on the instrument panel, including two
other parts reading `TRAY; INST` exactly. The part is where its own text already lives. Keep it, but
the leaf is badly named and will keep producing questions.

## 4. The three connectors

The three are `8943633640` (two-pin harness), `8980626220` and `8980680830` (both head lamp). All
three have a real EPC record with no figure name, and the stated reason for leaving them out is that
their figure key is shared by master parts in different families.

**That claim does not survive measurement.** The keys are `816-002` and `816-090`. On the master,
`816-002` has no rows at all, and `816-090` has two rows, and both of those rows are blank — they
carry no family at all. There is no family disagreement on either key, because there is no family on
either key. The same report uses exactly this situation elsewhere as a reason to leave a part open
(`5876102381`, `7553266960`, `7552126065` all have a key with no family), and those are described as
having no key evidence rather than a shared key. The connector paragraph is simply worded wrongly.

The 47 is close but not exact. I measured **50** master parts whose description begins `CONNECTOR`
and which sit on `Electrical > Harness & Connectors > Connector`. There is already a near-identical
part there: `8943633630 CONNECTOR; HARNESS (2P MAIL)` — one digit off `8943633640` — plus
`8973645310 CONNECTOR; HARNESS`. So a rule on the bare word `CONNECTOR` would place all three, with
50 parts behind it rather than 47.

**Do I agree they should stay open for now? Yes — but it is a decision, not a measurement, and a
bare `CONNECTOR` rule is the wrong fix.** The word on its own is not safe: 14 of the 64 placed parts
whose text begins `CONNECTOR` sit elsewhere — four bare `CONNECTOR` parts on `Brakes > Hydraulic >
Brake Pipe`, four `CONNECTOR; BRAKE VALVE` on the brake valve leaf, three `CONNECTOR; TURBOCHARGER
OIL FEED PIPE` on the turbocharger. They followed their figures, which is the same convention as the
rest of the file. A rule narrow enough to be right — the exact phrases `CONNECTOR; HEAD LAMP` and
`CONNECTOR; HARNESS` — has only two existing parts behind it, and nothing in the file distinguishes
a two-pin harness connector from the 50 others. What is missing is human confirmation that these
three belong on that leaf. They are worth **€8.25 together**. Leaving them open until someone
eyeballs them is right; if you would rather close them, it is one narrow line each and the count
goes to 1,227.

## 5. Accuracy against the master's own history

I re-derived the wording rule for every part whose label came from a figure name and compared it to
the family the master now holds.

| | parts | result |
|---|---:|---|
| carry an EPC figure name that a rule converts | 1,161 | rule's answer equals the master, **1,161 of 1,161** |
| disagreement | 0 | — |

Every one of the 1,161 agrees exactly at all three levels, with no Level-3 adjustment. There is no
slippage anywhere between the rule table and the file.

The parts placed by the description route are corroborated independently: **181 of the 181** that
have a figure name of their own have that name pointing at the same family that was written, read
through the same rules. The remaining 25 have no figure name to check against, and that is exactly
the group the description route exists for.

**Stratified sample: 60 parts** — five list-price bands from €1.00 to €8,693, fifteen families.

| outcome | parts |
|---|---:|
| rule reproduced from the figure name, agreed with the master | 38 |
| description route, corroborated by the part's own figure name | 21 |
| figure key route, which no wording rule can reproduce | 1 |
| disagreements | **0** |

The one part the sample could not reproduce from a rule is `1884058000 BESCO CLEAN (20L)`, €104.41,
a cleaning chemical, filed `Fluids Chemicals > Cleaning Chemicals > Cleaner` from its figure key.
That is a sensible label and the figure key is a legitimate route, but the wording rules have no
line that can produce it, so I count it separately rather than as an agreement, as asked.

Where a part was placed from a figure key rather than a wording rule, I have counted it separately
throughout.

## 6. What a person sees filtering by family

Every one of the 1,224 labels was written today — no carry-over. The route mix, on the 1,303:

| route | parts | list value |
|---|---:|---:|
| wording rule on the EPC figure name | 980 | €65,806 |
| description route, own figure name agrees | 181 | €33,579 |
| description route, no figure name of its own | 25 | €14,133 |
| figure key, unanimous on the master | 38 | €2,461 |
| **total** | **1,224** | **€115,978** |

The five biggest families by list value:

| family | parts | list value | from a figure name | from the description | from a figure key |
|---|---:|---:|---:|---:|---:|
| Electrical | 135 | €21,531 | 90 | 41 | 4 |
| Transmission | 112 | €16,184 | 102 | 10 | 3 |
| Engine | 101 | €14,738 | 82 | 19 | 0 |
| Cabin Interior | 142 | €10,802 | 126 | 16 | 0 |
| Accident & Body | 203 | €8,919 | 150 | 43 | 10 |

The remaining families: Driveline Axle €8,898 (53), Brakes €7,919 (99), Suspension €6,722 (44),
Intake Exhaust Emission €5,944 (91), Cooling €3,633 (64), Steering €3,468 (63), Fuel System €2,914
(29), Clutch €1,654 (34), Chassis Frame €1,496 (32), Wheels Hub €590 (8), Maintenance Service €380
(7), Fluids Chemicals €104 (1), Tools Equipment €77 (4), Lubrication €5 (2).

Three traps in reading that table.

`Accident & Body` holds the most parts and the least money of the big five — 203 parts averaging €44.
Sorting by part count and sorting by euro give different families.

The description route is concentrated in the expensive families: 25 parts with no figure name of
their own carry €14,133, which is 12% of the placed value from 2% of the placed parts, and one part
— the €8,693 engine assembly — is 61% of that.

And **443 of the 1,224 placed parts, 36%, are fasteners and small parts** — gasket, bolt, bracket,
clip, hose, pin, washer, stud, ring, collar, band, plug, seal and the like — taking the family of
the figure they sit on. They are only 10.7% of the value. A brake bracket filed as brakes is
consistent with how the master has always worked, and it is also why four bare `CONNECTOR` parts sit
on the brake piping leaf. If you want generic fasteners in the master's own hardware branch instead,
that is a separate cut. It moves roughly 443 rows for about a tenth of the money.

## 7. What could not be checked without the EPC

**The 1,161 figure names.** I re-read them, but I re-read the recorded name. I did not open the
catalogue, so I cannot tell you the names are right — only that every reading of them is consistent.
That is 1,161 of the 1,224 parts, or €99,385 of €115,978 of placed value, 86% of the parts and 86%
of the money.

**The description route, €47,712 over 206 parts.** These were placed by matching the description
against the master, not by the catalogue. For 181 a figure name agrees, which is corroboration but
still the same recorded name. For 25 there is no catalogue evidence at all.

**81 part numbers where the EPC returned nothing,** plus one lookup error. Of those, 32 now carry a
family placed by the description route (€11,440) and 49 remain open.

**The 60 lookups that returned a record but no figure name.** For 31 a figure key or the description
placed the part; 29 are still open. The three connectors are here, and so is the ABS unit whose
lookup errored, `7552357310` at €1,178 — the largest single open item after the service cab.

In total: **79 open part numbers, €13,082 of list value, 10.1% of the list.** Plus €2,163 in the
price extract that was never queued, of which €50.42 is the only unlabelled item and the rest is
already labelled on the master.

What I did not check, and will not claim: the `Value` column still does not reconcile with `Price`
on 136 lines. That is unrelated to this classification and the earlier passes already reported it. I
touched it only to the extent of needing a correct price parser.

## 8. Counting and consistency problems found

Bookkeeping, not labels. None should block a decision, but they will confuse the next person.

1. **The `Unknown` split is reported four different ways and none is wrong.** On this list the
   master gives 45 markers, the overlay gives 25, and the open-parts study gives a higher number
   again because it counts a wider union. Only the master's 45 is what a person sees filtering the
   published file.
2. **The 67 cannot be rebuilt** from any one file. See §1.
3. **The brief's 1,236 is 12 above measurement** and appears to be a line count on a part-number
   denominator. See §1.
4. **`queue.csv`'s `cur_*` columns are misleading.** They carry `Unknown` in `cur_aim_l1` for 845 of
   the 1,303 and a real value for none, and `Unknown` in `cur_aim_l2`/`cur_aim_l3` for 699. That
   matches nothing on the master, which now has 1,224 of the 1,303 labelled. Anything built from
   those columns is describing a state that no longer exists. Part of the cause: the extract's `P/N`
   and `Newest P/N` differ on 42 lines, so files keyed on one and described by the other disagree.
   That is how the open-parts study came to report 699 `Unknown` in `aim_l2`.
5. **Three of the four files behind the main report are dated 21 September inside a run dated 24
   September.** The work was done on the 24th; the files it wrote were named
   `…Figkey_20260921.csv`, rehashed at 16:21, and the 24 September launcher pointed at the 21
   September Excel for part of the day. The published 24 September file now holds the correct
   content, so this is not a content problem — it is a file-naming problem that will send the next
   person to the wrong date. It is already recorded in the pair-repair and restore reports.
6. **The 32 orphans carry no `fig_key`,** because the master blanks the key wherever the key number
   is not numeric. Checked and correct — but note that `orphans_43.csv` labels it `816-002` where
   the master has the key blank, so the extract and the master disagree on that column by design.

---

## Bottom line

The labels are more reliable than the write-ups make them sound. All 1,161 rule routes reproduce,
all 32 orphan placements reproduce, and a 60-part sample across the price range and fifteen families
found nothing wrong.

Before quoting these out, do three things, in this order:

1. **Decide the principle, not the part.** Does a part take the system of the figure it sits on, or
   its own system? The oil filter, the eight switch and antenna parts on `8-25 - SWITCH AND RELAY;
   INSTRUMENT PANEL`, and the 443 fastener rows all hinge on this one answer.
2. **Move the pump kit to the DEF pump leaf.** One line, right family, no euro moves.
3. **Fix the connector reasoning.** Delete "shared by master parts in different families" — the keys
   carry no family at all — and record it as a pending eyeball on three parts worth €8.25.

The remaining 79 open parts are 10% of the list value and are honest blanks, not failures.

---

## Files in this folder

| File | What it is |
|---|---|
| `v1_orphan_rederive.py` · `orphan_rederive.csv` · `orphan_rederive_report.txt` | independent re-derivation of the 32 orphans |
| `v2_fullset.py` · `verify_all.csv` · `verify_all_report.txt` | rule re-derivation for the whole set, plus the tie detector |
| `v3_analysis.py` · `verify_steps_1_5_6_7.txt` | position on disk, first sample, family rollup |
| `v4_arguable.py` · `verify_steps_3_4.txt` | the three flagged placements and the connectors |
| `v5_family_euro.py` · `verify_family_euro.txt` | family and euro rollup |
| `v6_provenance.py` · `provenance.csv` · `provenance_report.txt` | per-part route for the placed set |
| `v7_sample.py` · `sample_48.csv` · `verify_sample.txt` | first stratified sample |
| `v8_connectors.py` · `verify_connectors.txt` | CONNECTOR support |
| `v9_connector_text.py` · `verify_connector_text.txt` | the bare `CONNECTOR` placements traced |
| `v10_47.py` | testing where "47 supporting parts" could come from |
| `v11_final.py` · `final_numbers.txt` | headline counts and euro |
| `v12_final_prov.py` · `final_provenance.txt` | route mix |
| `v13_published.py` · `verify_published.txt` | the published table and the 67 reconciliation |
| `v14_ties.py` · `verify_ties.txt` | the three length ties and every part they touch |
| `v15_claims.py` · `verify_claims.txt` | numeric self-check on the claims in this note |
| `v16_definitive.py` · `definitive.txt` | the final route table and CONNECTOR support |
| `v17_sample_final.py` · `sample_final.txt` | the 60-part sample, restricted to the 1,303 |

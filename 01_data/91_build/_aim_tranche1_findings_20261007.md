# Tranche-1 AIM proposal — quality findings (2026-10-07)

Shard A. Read-only check. **No release applied.**

## Verdict

**No-go on the full 49,208-row proposal as written.** About **10,995 rows (22%)** sit on catalogue paths that look commercially wrong or conflict with a decision you already made. The other **38,213 rows** look ready once you have accepted the method — with one caveat: almost none of the proposal rows carry a part description in the CSV, so the clean subset was judged on catalogue-path agreement, not on reading each part name.

## What the proposal is

It fills true blanks where the catalogue path already points to one AIM family on at least 90% of known examples (at least five known parts). **42,845** HIGH (≥95% agreement), **6,363** MED_HIGH (90–95%).

The proposal CSV itself has a description on only **287** of 49,208 rows. The JP description cache uses different column names (`pn` / `jp_description`) than the first enrich pass expected, so a line-by-line description audit of the blanks was not available in this check. The hard fails below rest on the **known** examples that taught each map, not on blank proposal text.

## Coverage if applied (master = 165,310)

| Cut | With a family | Share | Still without |
|---|---:|---:|---:|
| Today | 21,045 | 12.7% | 144,265 |
| Full tranche 1 as written | 70,253 | 42.5% | 95,057 |
| Only unflagged rows | 59,258 | 35.8% | 106,052 |

Unknown / Unknown Review markers (**4,129**) are untouched either way. True blanks left after a full apply: about **90,930**.

## Top proposed families (volume)

- Accident & Body: 14,492
- Transmission: 6,878
- Electrical: 6,744
- Chassis Frame: 4,422
- Lighting: 3,100
- Engine: 2,889
- Fuel System: 2,137
- Intake Exhaust Emission: 1,749
- Clutch: 1,365
- Wheels Hub: 1,331
- Brakes: 1,183
- Cooling: 879
- Maintenance Service: 858
- Suspension: 584
- Steering: 241

## Paths that need your eyes (hold these back)

### Repair parts > Gaskets / seals > Gasket set → Transmission (6,550 rows, 100% agree on 228 known, HIGH)

**Hard fail.** Of the 228 known examples that taught this map, **206 already say ENG / ENGINE / HD OVERHAUL in the description and still sit under Transmission.** That is the old wrong filing you corrected on 4 Oct (engine gasket sets → Engine > Gasket & Sealing > Gasket). Applying this block would copy that error onto 6,550 blanks. Split by description (ENG vs TRANS) before any release, or hold the whole path.

### High value repair > Transmission parts > Transmission assembly → Literature Marketing (219 rows, 93% agree on 41 known, MED_HIGH)

**Hard fail.** The known set is mostly `TRANSMISSION ASM; MANUAL` filed as Literature Marketing / Manuals. That is a spare transmission assembly, not a handbook. Do not apply.

### Competitive parts > Air system > Air valve → Steering (241 rows, 94% agree on 31 known, MED_HIGH)

Commercially doubtful. Air-tank / vacuator / protection valves are not steering parts. Hold for a proper family (brakes / air system / engine vacuum — your call).

### Accident parts > Body parts > Body structure → Chassis Frame (1,788 rows, 95% agree on 93 known, MED_HIGH)

Large volume just under the HIGH bar. Plausible for structure, but worth a quick eye before it moves ~1.8k blanks.

### Accident parts > Body parts > Glass / window → Accident & Body (1,100 rows, 91% agree on 185 known, MED_HIGH)

Direction looks right (glass under Accident & Body). Held only because agreement is 91% on a four-figure volume — not because the family name looks wrong.

### Repair parts > Electrical sensors > Relay / solenoid / fuse → Electrical (576 rows, 90% agree on 130 known, MED_HIGH)

Floor of the rule (exactly 90%). Family name is plausible; confidence is thin.

### Competitive parts > Clutch parts > Clutch disc → Clutch (521 rows, 90% agree on 60 known, MED_HIGH)

Same — family name looks right, agreement is only 90% on 60 known. Hold or raise the bar.

## HIGH sample on unflagged paths

**Sample miss rate: not scored.** After description join, too few unflagged HIGH rows had usable part text to run a keyword consistency sample. Quality on the clean 38,213 therefore rests on catalogue-path majority only. That is acceptable for a first method pass if you accept the 90%/n≥5 rule; it is not a part-by-part read.

## Ready vs not

| Bucket | Rows | Call |
|---|---:|---|
| Unflagged paths | 38,213 | Ready to approve as a first release **if** you accept catalogue-majority without a description pass |
| Flagged paths | 10,995 | Needs your eyes — do not apply as proposed |
| Of which hard fails | 6,550 gasket + 219 transmission-asm (+ 241 air valve as doubtful) | Must not apply |

## Recommendation

1. **No-go on the full tranche-1 file.**
2. **Hard hold:** gasket-set → Transmission (6,550) and transmission-assembly → Literature Marketing (219). Air valve → Steering (241) should not go either until you name the right family.
3. **Conditional go** on the remaining **38,213** unflagged rows, as a dated release for your OK — not a silent write to the master.
4. Even a full apply only lifts family coverage from **12.7% to 42.5%**. The other ~91k true blanks are later work.

## Files

- Proposal (unchanged): `C:\Users\jerom\Desktop\claude\ISZE\01_data\00_derived\_releases\next_release_proposal_full_class_tranche1_catmap_2026-10-07.csv`
- This note: `C:\Users\jerom\Desktop\claude\ISZE\01_data\91_build\_aim_tranche1_findings_20261007.md`
- Machine summary: `C:\Users\jerom\Desktop\claude\ISZE\01_data\91_build\_aim_tranche1_findings_20261007.json`
- Spot-check script: `C:\Users\jerom\Desktop\claude\ISZE\01_data\91_build\_aim_tranche1_spotcheck_20261007.py`

"""Apply the section 3f reconciliation to the toner pack.

Every write goes to a temp file in the same directory and is then os.replace()d,
because appending works on this volume but truncating in place raises Errno 22.

Each replacement asserts it matched exactly once.
"""
import io, os, sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

PACK = r'C:\Users\jerom\Desktop\claude\ISZE\01_data\90_INBOX\GPT_tonnage_pack_20260920'
READ = os.path.join(PACK, '00_READ_ME_FIRST.md')
BRIEF = os.path.join(PACK, '01_BRIEF_FOR_THE_MODEL.md')
LOG = os.path.join(PACK, '02_CORRECTION_LOG.md')
CAT = os.path.join(PACK, '04_FILE_CATALOG.csv')


def read(path):
    with open(path, 'rb') as fh:
        raw = fh.read()
    text = raw.decode('utf-8')
    assert text.count('\r\n') == text.count('\n'), path + ': mixed line endings'
    return text.replace('\r\n', '\n')


def write(path, text):
    data = text.replace('\n', '\r\n').encode('utf-8')
    tmp = path + '.__tmp_3f__'
    with open(tmp, 'wb') as fh:
        fh.write(data)
    os.replace(tmp, path)
    print('  wrote', os.path.basename(path), len(data), 'bytes')


def sub(text, old, new, label):
    n = text.count(old)
    assert n == 1, 'anchor %r matched %d times' % (label, n)
    print('  [ok] %s' % label)
    return text.replace(old, new)


# ======================================================================
# 00_READ_ME_FIRST.md
# ======================================================================
t = read(READ)

t = sub(t,
"""**Version 4, 2026-09-22.** Supersedes v3 of 22 September. v4 corrects the `NMR` / `NKR` section (§7), records the withdrawn figure, and states a known defect in the headline (§14). **No number in the data files changed** — the layer was regenerated on 22 September and is current.""",
"""**Version 4, 2026-09-22.** Supersedes v3 of 22 September. v4 corrects the `NMR` / `NKR` section (§7), records the withdrawn figure, and states a known defect in the headline (§14). **No number in the data files changed** — the layer was regenerated on 22 September and is current. **§3f was reconciled against the source files later on 22 September and found wrong in four of its cells and two of its supporting figures; the correction is in §14f and the dated entry at the foot of `02_CORRECTION_LOG.md`.**""",
'read-me: version line')

t = sub(t,
"""| Families with **no** band candidates at all | **5 families, 174 PNs, EUR 5,990,933** | see §3f |""",
"""| Families with **almost no** band candidates | **5 families, 174 PNs, EUR 5,990,933** — of which brake rotor is 109 PNs / EUR 4,457,248 and **does** have 7 candidates, under a blank family label | see §3f |""",
'read-me: 3a families row')

t = sub(t,
"""### 3f. Five service families have no tonnage candidates at all — scoped on 22 September

| Family | Part numbers | Euro | In the family file | Family file's own verdict |
|---|---:|---:|---:|---|
| **brake rotor** | 109 | **4,457,248** | 109 | **92 of 109: "no vehicle reference"**, confidence low |
| blower filter | 7 | 1,349,479 | 7 | 6 single-family, 1 no vehicle |
| urea filter | 7 | 134,108 | 7 | 5 no vehicle, 2 pooled |
| clutch booster | 48 | 47,151 | 48 | 37 single-family, 11 no vehicle |
| pilot bearing | 3 | 2,947 | 3 | 2 single-family, 1 pooled |
| **TOTAL** | **174** | **5,990,933** | | |""",
"""### 3f. Five service families have almost no tonnage candidates — scoped on 22 September, reconciled the same evening

**[corrected 2026-09-22 evening]** The heading used to read "no tonnage candidates at all". That is wrong for brake rotor, which has seven part numbers carrying a band in the candidate table, under a blank family label. **The whole of §3f has now been reconciled against the source files, and four of the table's cells and the two paragraphs around it were wrong.** Full working in §14f.

**Part numbers and Euro are the service worklist basis** — `01_data\\00_derived\\epc_decode_worklist.csv`, counting rows by `pms_category` and summing `eur_all`. Brake rotor's EUR 4,457,247.81 is the same figure §3a prints for the worklist. **The two right-hand columns are counts of rows in the family file, not euro.** The family file's own money column is `eur_all_markets`, a wider basis (every line, every market) which for brake rotor reads EUR 4,642,883; the two are not comparable and are not added.

| Family | Part numbers | Euro | Rows in the family file | Of those, under this family | The family file's own resolution column |
|---|---:|---:|---:|---:|---|
| **brake rotor** | 109 | **4,457,248** | 109 | 109 | 92 no vehicle reference (low), 17 single family (16 high, 1 medium) — **the "92" is one resolution, not the family total** |
| blower filter | 7 | 1,349,479 | 12 | 7 | 6 single family, 1 no vehicle reference |
| urea filter | 7 | 134,108 | 5 | 2 | 3 shared across families, 2 no vehicle reference — **the other 5 worklist part numbers are filed under blower filter** |
| clutch booster | 48 | 47,151 | 48 | 48 | 37 single family, 11 no vehicle reference |
| pilot bearing | 3 | 2,947 | 3 | 3 | 2 single family, 1 shared across families |
| **TOTAL** | **174** | **5,990,933** | 177 rows in total | **169** | **5 worklist part numbers have no row in the family file at all** |

**The file name in the reconciliation.** `01_data\\00_derived\\vehicle_family_bands.csv` and the copy shipped in this pack as `data_context\\22_vehicle_family_by_part.csv` are byte-identical (151,025 bytes; verified 2026-09-22). Read either.""",
'read-me: 3f table')

t = sub(t,
"""**Brake rotor is the honest answer and it is a dead end for tonnage.** Of its 109 part numbers, the family file resolved **92 as having no vehicle reference at all** — 92 rows at low confidence, 16 from the EPC, **1** from the cross-reference, and precisely **one** vehicle string in the whole family: `N*R,N*S`, which is a wildcard, not a model code. A wildcard cannot be turned into a band. So brake rotor's EUR 4.46M is not blocked by a fixable join — **there is no evidence on disk that says which vehicle these rotors fit.**""",
"""**Brake rotor is not a dead end, and the "92 of 109" was a misreading of the family file.** [corrected 2026-09-22 evening] Two statements that stood here were wrong.

**First, 92 is one resolution value inside the family file, not the number of rotors the family file failed on.** Of its 109 brake-rotor rows, 92 resolve `no_vehicle_reference` at low confidence, and the other **17 resolve `single_family` — 16 of them at high confidence** — carrying **EUR 3,815,676, which is 85.6% of the family's EUR 4,457,248**. The 17 are evidence, not absence: 7 through an EPC tonnage band, 6 through an EPC vehicle class, 3 through an EPC band on the D-Max class, and 1 only through a wildcard.

**Second, the family carries more than one vehicle string, and more than one band.** `N*R,N*S` is the only string the *cross-reference* supplies — one part number, `8973872290`, EUR 41,852 — and it is a wildcard, so it is rightly not banded. But the EPC route gives the other sixteen a band: `3.5t_N35|5.5t_N50_N55|7.5t_N50_N62_N75` on five part numbers, `7.5t_N50_N62_N75` on `8981919560` (EUR 316,996, and it is `single_band` there), and the D-Max class on three worth EUR 2,472,820. **Seven brake-rotor part numbers carry a band in `13_band_candidates_297_parts.csv` and always did**, and one of them (`8981919560`) is band-exclusive. All seven sit in that file with a **blank `category`**, which is why a family check that keyed on that column read the family as empty. Six of the seven are pooled across all three rungs, so **no tonnage *trend* can be read for rotors** — that much of the old verdict survives.

**What is genuinely unbandable is the other 102 part numbers, EUR 641,572.** Where the EPC does speak for them it names either `TRUCKS N` (no weight) or `PASSENGER VEHICLE PICK UP; PASSENGER VEHICLE SUV` (a light-vehicle class off the truck ladder). So the honest reading is: **the family is not short of evidence, it is short of a *weight*, and 85.6% of its book carries a vehicle reference of some kind.** The dead-end statement survives only in the narrow sense that rotors cannot carry a tonnage trend.""",
'read-me: brake rotor paragraph')

t = sub(t,
"""**Why the other four are different.** Clutch booster (28 cross-reference hits), blower filter (3) and pilot bearing (2) do have some vehicle evidence and are plausibly recoverable. The routes are: the current EPC decode, the cross-reference's own `vehicle_model` string, or the family file's registry model tag. The candidate table is produced by a probe that reads the **first route only**, which is the mechanical reason these families are absent from it.""",
"""**Why the other four are different — and the route counts that stood here were wrong.** [corrected 2026-09-22 evening] The paragraph used to attribute "28 cross-reference hits" to clutch booster, "3" to blower filter and "2" to pilot bearing. Measured against `01_data\\00_derived\\genuine_bvp_crossref.csv`, joining on the `vehicle_model` column:

| Family | Part numbers with a cross-reference `vehicle_model`, matched on `genuine_pn` only | …the same, matching `genuine_pn` **or** `bvp_pn` | …whose string contains a non-wildcard token |
|---|---:|---:|---:|
| brake rotor | 1 | 1 | 1 (the wildcard `N*R,N*S`) |
| blower filter | **3** | 6 | 0 |
| urea filter | **1** | 2 | 0 |
| clutch booster | **28** | 37 | 18 |
| pilot bearing | **2** | 3 | 3 |

**The three published figures are the lower bound — a match on `genuine_pn` only — and the family file reads the same source with `bvp_pn` included as well.** That is why the family file raises clutch booster from 28 to 37, blower filter from 3 to 6, and pilot bearing from 2 to 3. The claim that these families have vehicle evidence holds; the counts beside them should be quoted as a lower bound with the higher one beside it. **Note also that for blower filter and urea filter not one of those strings contains a usable token** — they are `TF*,UC*` and `E*,C*,F*,N*`, all wildcards — so "has vehicle evidence" and "can be banded" are not the same sentence, and only clutch booster and pilot bearing are recoverable in practice.

**And the probe claim needs qualifying.** [verified 2026-09-22 evening] `01_data\\91_build\\pn_ammo_probe_20260918\\_tonnage_capable.py` reads the EPC editions **and** `genuine_bvp_crossref.csv`, so it is not "the first route only". What is true is broader and less convenient: the probe converts a model string to a band by looking each token up in a table of series tokens, and **a token that is not in that table — an F-series code such as `FRR`, or any wildcard — never becomes a band.** That is the mechanical reason blower filter, urea filter, clutch booster and pilot bearing are absent from the candidate table. **It is not why brake rotor is absent, because brake rotor is not absent** (see above).""",
'read-me: why the other four')

t = sub(t,
"""| Family | Part numbers | Euro | Via the EPC decode | Via the cross-reference | Via the family file |
|---|---:|---:|---:|---:|---:|
| brake rotor | 109 | 4,457,248 | 8 | 1 | 109 (92 with no vehicle) |
| blower filter | 7 | 1,349,479 | 0 | 3 | 7 |
| urea filter | 7 | 134,108 | 0 | 1 | 7 |
| clutch booster | 48 | 47,151 | 0 | 28 | 48 |
| pilot bearing | 3 | 2,947 | 0 | 2 | 3 |""",
"""| Family | Part numbers | Euro | With a band in `15_band_by_part_number.csv` | With a cross-reference string, `genuine_pn` only / incl. `bvp_pn` | Rows in the family file | Of those, under this family |
|---|---:|---:|---|---:|---:|---:|
| brake rotor | 109 | 4,457,248 | 8 · **7 of them banded, EUR 1,061,419** on that file's own basis | 1 / 1 | 109 | 109 |
| blower filter | 7 | 1,349,479 | 0 | 3 / 6 | 12 | 7 |
| urea filter | 7 | 134,108 | 0 | 1 / 2 | 5 | 2 |
| clutch booster | 48 | 47,151 | 0 | 28 / 37 | 48 | 48 |
| pilot bearing | 3 | 2,947 | 0 | 2 / 3 | 3 | 3 |

**Why this table differs from the scoping CSV it came from.** The source is `01_data\\00_derived\\tonnage_missing_families_scope_20260922.csv`, and two of its columns do not reproduce against the files it names. Its `route1_decode` column reads `8 / 0 / 0 / 0 / 0`; measured, the count of worklist part numbers that carry a band in the banded decode is `8 / 0 / 0 / 0 / 0` **if `pms_category` is read strictly, and `8 / 0 / 1 / 1 / 0` if it is read tolerantly**, so the clutch-booster and urea-filter zeros are not reproducible from the files. Its `route3_family` column reads `7 / 7 / 7 / 48 / 3` — that is the **worklist** size, not the family-file row count, which is why its urea-filter `7` counts five part numbers whose family-file row is filed under blower filter. **The scoping pass's headline recovery figures do reconcile exactly** (174 part numbers, 18 recoverable at EUR 3,502,806, 41 wildcard-only at EUR 1,483,243, 115 no-evidence at EUR 1,004,883, and the genuinely-new EUR 2,475,999); only these route columns do not.""",
'read-me: route table')

t = sub(t,
"""**What this means commercially, and it should not be buried.** The tonnage view as it stands covers filters and clutch. It has no brake rotor, and brake rotor is the second-largest service family in the service list by euro. **A tonnage story presented without that sentence would be misreading its own coverage.**""",
"""**What this means commercially, and it should not be buried.** [corrected 2026-09-22 evening] **Brake rotor is the largest service family by euro, not the second.** On the worklist basis it is EUR 4,457,248, and brake pad — the family that would have been called the largest — is EUR 4,306,071, so brake rotor leads by EUR 346,878. It is the largest of fourteen families on the worklist, on the family file, and on the additive band partition alike. **And the brake gap is wider than one family:** brake pad and brake shoe together carry EUR 5,192,029, and §3c records that both of them, with air filter and release bearing, hold **zero band-exclusive part numbers**. The tonnage view as it stands covers filters and clutch. Of the brake families it holds seven rotor part numbers under a blank label and no band-exclusive part at all. **A tonnage story presented without that sentence would be misreading its own coverage.**""",
'read-me: commercial paragraph')

t = sub(t,
"""Two evidence passes finished after v3 was written on 22 September and overturned three things v3 asserted. **Nothing in the data files changed:** the tonnage layer was regenerated on 22 September and is current. What changed is what these documents say about it. The five items below are recorded in full in `02_CORRECTION_LOG.md`; the sources are in `01_data\\90_INBOX\\` — `NMR_ruling_impact_20260922.md` and its CSV, `NMR_blast_radius_20260922.md`, `band_union_audit_20260922.md`, `isuzu_n_series_public_weights_20260922.md` and `NMR_MAPPING_DECISION_NOTE_20260922.md`.""",
"""Two evidence passes finished after v3 was written on 22 September and overturned three things v3 asserted. **Nothing in the data files changed:** the tonnage layer was regenerated on 22 September and is current. What changed is what these documents say about it. The items below are recorded in full in `02_CORRECTION_LOG.md`; the sources are in `01_data\\90_INBOX\\` — `NMR_ruling_impact_20260922.md` and its CSV, `NMR_blast_radius_20260922.md`, `band_union_audit_20260922.md`, `isuzu_n_series_public_weights_20260922.md` and `NMR_MAPPING_DECISION_NOTE_20260922.md`.

**And a sixth item, added later the same evening: §3f was never reconciled against the source files, and four of its cells were wrong.** It is recorded in §14f below. It is a different kind of defect from the five above — those corrected what a document *said* about numbers that were already verified; §14f corrects numbers that had never been checked against the files they name.""",
'read-me: 14 lead')

t = sub(t,
"""**Do not distribute new tonnage performance claims while the reconciliation and approval conditions above remain open.**""",
"""### 14f. Section 3f was reconciled on the evening of 22 September, and four of its cells were wrong

**What was wrong, and where the right number comes from.** Everything below is re-derived from files that already existed; **no data file was edited and no build was run.** Source files: `01_data\\00_derived\\epc_decode_worklist.csv` (`pms_category`, `eur_all`), `01_data\\00_derived\\vehicle_family_bands.csv` = the pack's `data_context\\22_vehicle_family_by_part.csv` (byte-identical), `01_data\\00_derived\\genuine_bvp_crossref.csv` (`vehicle_model`), the pack's `data_part_number_decode\\13_band_candidates_297_parts.csv` and `15_band_by_part_number.csv`, `01_data\\90_INBOX\\tonnage_family_recovery_proposal_20260922.csv` and `01_data\\00_derived\\tonnage_missing_families_scope_20260922.csv`.

| Was | Is | Where the number comes from |
|---|---|---|
| "Five service families have **no tonnage candidates at all**" | **Almost none.** Brake rotor has **7** part numbers carrying a band in the candidate table, one of them band-exclusive, all under a blank `category` | `13_band_candidates_297_parts.csv`, matched on `pn` |
| "**92 of 109**: 'no vehicle reference'" as the family verdict | **92 is a resolution value, not the family total.** 109 rotor rows split **92 `no_vehicle_reference` (low) + 17 `single_family` (16 high, 1 medium)**; the 17 carry **EUR 3,815,676 = 85.6%** of the family's EUR 4,457,248 | `22_vehicle_family_by_part.csv`, columns `resolution`, `confidence`, `eur_all_markets`; euro on the worklist basis |
| "the family carries exactly **one** vehicle string, `N*R,N*S`" | **One string from the cross-reference, but not one reference in the family.** The EPC route gives 16 rows a reference and 7 of them a band: `3.5t/5.5t/7.5t` ×5, `7.5t` ×1 (`8981919560`), D-Max ×3 (EUR 2,472,820) | `22_vehicle_family_by_part.csv` `from_epc`, `source_note`; `15_band_by_part_number.csv`, `13_band_candidates_297_parts.csv` |
| brief and read-me both named brake rotor "the **second**-largest service family by euro" | **Largest.** EUR 4,457,248 against brake pad's EUR 4,306,071 — a lead of EUR 346,878 | `epc_decode_worklist.csv`, summed by `pms_category`; holds on the family file and on the additive partition too |
| route counts "clutch booster 28, blower filter 3, pilot bearing 2" | **Lower bounds.** Reading `bvp_pn` as well: 37 / 6 / 3. And the strings for blower filter and urea filter are wildcards only | `genuine_bvp_crossref.csv`, `vehicle_model` column |
| route table `Via the family file` = 109 / 7 / 7 / 48 / 3 | **Those are worklist sizes.** The family-file row counts are 109 / **12** / **5** / 48 / 3, and the rows filed under the family are 109 / 7 / **2** / 48 / 3. **5 of urea filter's 7 worklist part numbers have no row in the family file at all** — they are filed under blower filter | `22_vehicle_family_by_part.csv` vs `epc_decode_worklist.csv` |
| the scoping CSV's `route1_decode` column, read as a route count | **Does not reproduce** for clutch booster and urea filter: measured `8 / 0 / 1 / 1 / 0` on a tolerant `pms_category` read, against the file's `8 / 0 / 0 / 0 / 0` | `15_band_by_part_number.csv` vs the scoping CSV |

**What this does not touch.** The five-family **euro** total, EUR 5,990,933, and the worklist euro of every family, all reproduce exactly: brake rotor 4,457,248 / blower filter 1,349,479 / urea filter 134,108 / clutch booster 47,151 / pilot bearing 2,947, summing to 5,990,933. The recovery proposal's own verdict table reconciles to the cent — **18 recoverable at EUR 3,502,806, 41 wildcard-only at EUR 1,483,243, 115 with no evidence at EUR 1,004,883, and only EUR 2,475,999 of the recoverable figure genuinely new**. The "92 at low confidence" figure in `02_CORRECTION_LOG.md` is also right about what it says — 92 rows *are* low confidence — but the family file holds 109 rotor rows, not 92.

**What could not be sourced, and has therefore been removed rather than replaced.** The scoping CSV's `route1_decode` column for clutch booster and urea filter, and the route hits of "3" for blower filter and "1" for urea filter, cannot be reproduced from the files they claim to read. The corrected table in §3f shows the reproducible measurement and names the discrepancy rather than carrying a figure forward. **The probe's behaviour cannot be stated as "first route only"** — it reads both the EPC editions and the cross-reference — and the text now says what it actually does.

**What the "dead end" verdict keeps.** Six of the seven banded rotor part numbers are pooled across all three rungs. **No tonnage trend can be read for brake rotor**, and that sentence stands. What does not stand is that the family has no evidence and no candidates.

**Do not distribute new tonnage performance claims while the reconciliation and approval conditions above remain open.**""",
'read-me: 14f subsection')

write(READ, t)

# The other three files are handled by _apply_3f_b.py, which keeps their LF line endings.
# Stop here rather than falling through to the line-ending assertion below.
raise SystemExit(0)

# ======================================================================
# 01_BRIEF_FOR_THE_MODEL.md
# ======================================================================
t = read(BRIEF)

t = sub(t,
"""**And say what it does not cover.** **Five service families have no tonnage candidates at all — 174 part numbers, EUR 5.99M**, including **brake rotor (109 part numbers, EUR 4.46M)**, the second-largest family by euro. For brake rotor this is a dead end rather than a fixable join: 92 of its 109 part numbers carry no vehicle reference at all, and the family holds one vehicle string, `N*R,N*S`, a wildcard that cannot become a band. **A tonnage story presented without that sentence would be misreading its own coverage.**""",
"""**And say what it does not cover.** **[corrected 2026-09-22 evening]** **Five service families have almost no tonnage candidates — 174 part numbers, EUR 5.99M**, including **brake rotor (109 part numbers, EUR 4.46M)**, which is the **largest** family by euro and not the second. Three figures that stood in this paragraph are withdrawn: "92 of its 109 part numbers carry no vehicle reference at all" is one **resolution value** inside the family file, not the family's total — the other 17 rotor rows resolve `single_family` at high confidence and carry EUR 3,815,676, which is 85.6% of the family book; "the family holds one vehicle string" is true of the cross-reference only, and the EPC gives 7 rotor part numbers a tonnage band; and "no tonnage candidates at all" is wrong — those 7 are in the candidate table, one of them band-exclusive, all under a blank family label. **The dead end survives only in the narrow sense that no tonnage *trend* can be read for rotors**, because six of the seven are pooled across all three rungs. **A tonnage story presented without that sentence would be misreading its own coverage.**""",
'brief: question A coverage paragraph')

write(BRIEF, t)

# ======================================================================
# 02_CORRECTION_LOG.md
# ======================================================================
t = read(LOG)

t = sub(t,
"""**And a scoping result.** Brake rotor has no tonnage data — 109 part numbers, EUR 4.46M, the second-largest service family by euro. Scoped on the 22nd: **92 of its 109 part numbers have no vehicle reference at all** in the family file, 92 at low confidence, and the entire family carries exactly **one** vehicle string, `N*R,N*S`, which is a wildcard and cannot become a band. **There is no evidence on disk saying which vehicles these rotors fit.** That is a dead end for tonnage, not a fixable join, and it is now stated in §3f of the read-me.""",
"""**And a scoping result — partly wrong, and corrected the same evening.** [corrected 2026-09-22 evening, see the §3f section at the foot of this log] Brake rotor is the **largest** service family by euro, not the second: 109 part numbers and EUR 4,457,248, ahead of brake pad at EUR 4,306,071. **"92 of its 109 part numbers have no vehicle reference at all" misread the family file.** 92 is one resolution value; the other **17 rows resolve `single_family` (16 at high confidence)** and carry **EUR 3,815,676 — 85.6% of the family book**. And the family does not carry one vehicle string: `N*R,N*S` is the only one the *cross-reference* supplies, but the EPC route bands **7** of these rotors — `3.5t/5.5t/7.5t` on five, `7.5t` on `8981919560`, D-Max on three — and all 7 sit in the candidate table under a blank `category`, which is how they were missed. **No tonnage *trend* can be read for rotors**, because six of the seven are pooled; the family is not short of evidence, it is short of a weight. The corrected text is §3f of the read-me.""",
'log: scoping result paragraph')

t = sub(t,
"""| 14 | **brake rotor has no band data at all.** 109 part numbers and **EUR 4,457,248** in the service worklist, **zero** candidate rows. The candidate table also holds nothing for blower filter, urea filter, clutch booster or pilot bearing. | The candidate table is not a random subset of the service list: 174 worklist part numbers carrying **EUR 5,990,933** have no tonnage candidate. Any tonnage story that omits brakes is omitting the second-largest service family by euro, and that must be said rather than left to be discovered. |""",
"""| 14 | **brake rotor has almost no band data.** 109 part numbers and **EUR 4,457,248** in the service worklist, and **7** candidate rows — not zero. **[corrected 2026-09-22 evening]** The seven carry a band and **one is band-exclusive**, but they sit in `13_band_candidates_297_parts.csv` under a **blank `category`**, so a family check keyed on that column reads the family as empty. Blower filter, urea filter, clutch booster and pilot bearing genuinely have none. | The candidate table is not a random subset of the service list, and its `category` column is blank on 219 of its 297 rows, so it cannot be used to decide which families are covered. **Brake rotor is the largest service family by euro (EUR 4,457,248 against brake pad's EUR 4,306,071), not the second**, and brake pad plus brake shoe add another EUR 5,192,029 with zero band-exclusive part numbers between them. Any tonnage story that omits brakes must say so rather than leave it to be discovered. |""",
'log: defect row 14')

t = sub(t,
"""### v4-7. What was NOT done in v4""",
"""### v4-7. What was NOT done in v4""",
'log: anchor check')

t = t.rstrip('\n') + """

---

## Later still on 2026-09-22 — §3f reconciled against the source files (evening)

**Trigger:** §3f of the read-me, corrected by hand on the same evening. The table it carried did not reconcile: its per-route columns did not sum, and "92 of 109" did not match the family file the pack ships.

**Method.** Read the two sections that record the v4 pass, then re-derived every figure in §3f and the two paragraphs around it from the files it names. **No data file was edited. No `build_*.py` was run.** Every replacement figure below was computed from `01_data\\00_derived\\epc_decode_worklist.csv`, `01_data\\00_derived\\vehicle_family_bands.csv` (byte-identical to the pack's `data_context\\22_vehicle_family_by_part.csv`, both 151,025 bytes), `01_data\\00_derived\\genuine_bvp_crossref.csv`, `01_data\\90_INBOX\\tonnage_family_recovery_proposal_20260922.csv`, `01_data\\00_derived\\tonnage_missing_families_scope_20260922.csv`, and the pack's own `13_band_candidates_297_parts.csv` and `15_band_by_part_number.csv`.

### 3f-1. The heading and the table, corrected

**What it said:** "Five service families have **no tonnage candidates at all**", with a table whose cells were `109 / 7 / 7 / 48 / 3` part numbers, EUR `4,457,248 / 1,349,479 / 134,108 / 47,151 / 2,947`, family-file counts `109 / 7 / 7 / 48 / 3`, and a final column reading "92 of 109: no vehicle reference", "6 single-family, 1 no vehicle", "5 no vehicle, 2 pooled", "37 single-family, 11 no vehicle", "2 single-family, 1 pooled".

**What is true.** The **part numbers and the euro all reproduce exactly**, and their total is right at 174 / EUR 5,990,933. **The two right-hand columns were wrong.**

| The cell | Was | Is | Source |
|---|---|---|---|
| brake rotor, "no tonnage candidates at all" | 0 candidates implied | **7 part numbers carry a band**, one band-exclusive (`8981919560`, EUR 7.5t) | `13_band_candidates_297_parts.csv`, matched on `pn` |
| brake rotor, family-file verdict | "92 of 109: no vehicle reference" | **92 `no_vehicle_reference` (low) + 17 `single_family` (16 high, 1 medium)** | `22_vehicle_family_by_part.csv` → `resolution`, `confidence` |
| brake rotor, the 92 | read as the family total | **EUR 641,572**; the 17 are **EUR 3,815,676 = 85.6%** | `eur_all_markets` per row; euro of the 92 confirmed on the worklist basis |
| blower filter, "in the family file" | 7 | **12 rows** — 6 `single_family` (medium), **6 `no_vehicle_reference` (low)** | same file |
| urea filter, "in the family file" | 7, "5 no vehicle, 2 pooled" | **5 rows** — 3 `shared_across_families`, 2 `no_vehicle_reference` — and **only 2 of the 7 worklist part numbers have a row under this family at all; the other 5 are filed under blower filter** | same file, joined on `pn` |
| clutch booster, "in the family file" | 48 | **48 — correct** | same file |
| pilot bearing, "in the family file" | 3 | **3 — correct** | same file |
| the route table, "via the family file" | 109 / 7 / 7 / 48 / 3 | those are **worklist** sizes; family-file row counts are **109 / 12 / 5 / 48 / 3** | `epc_decode_worklist.csv` vs `22_vehicle_family_by_part.csv` |
| the route table, route counts | 8/1, 0/3, 0/1, 0/28, 0/2 | EPC-banded: **8 / 0 / 0 / 0 / 0**. Cross-reference: **1 / 3 / 1 / 28 / 2** on `genuine_pn` only — the published numbers — and **1 / 6 / 2 / 37 / 3** including `bvp_pn`. Non-wildcard tokens: **1 / 0 / 0 / 18 / 3** | `genuine_bvp_crossref.csv`, `vehicle_model` |

### 3f-2. "92 of 109" — tested and refuted as the family verdict

The figure is **wrong as stated and right as a count of one row value**. `22_vehicle_family_by_part.csv` holds **109 brake-rotor rows**: 92 at `resolution = no_vehicle_reference`, `confidence = low`, and **17 at `resolution = single_family`, 16 of them `confidence = high`**. So 92 of 109 rows carry no vehicle reference — that is true — but the pack printed it as the family's verdict, and the remaining 17 rows are not a rounding error: they carry **EUR 3,815,676, 85.6% of the family's EUR 4,457,248**.

**The family file also carries no euro column for the 92 as a group**, so the only honest way to read it is row by row. This is the mechanism of the error: a 109-row family was summarised by its largest `resolution` bucket at a glance, and the bucket was read as the family.

### 3f-3. "The family carries exactly one vehicle string" — refuted

`N*R,N*S` is the only string the **cross-reference** supplies: one part number, `8973872290`, EUR 41,852, `wildcard_only`, correctly unbanded. **But the EPC route gives 16 of the 109 rows a reference and 7 of them a band**, and those bands are in the pack:

| Part number | Band | EUR (worklist / banded-decode basis) |
|---|---|---:|
| 8981919560 | `7.5t_N50_N62_N75` — **single_band** | 316,996 / 319,716 |
| 8982488951 | `3.5t_N35\\|5.5t_N50_N55\\|7.5t_N50_N62_N75` | 269,116 / 280,373 |
| 8983034670 | `3.5t_N35\\|5.5t_N50_N55\\|7.5t_N50_N62_N75` | 114,382 / 118,150 |
| 8982488930 | `3.5t_N35\\|5.5t_N50_N55\\|7.5t_N50_N62_N75` | 109,369 / 113,478 |
| 8983034680 | `3.5t_N35\\|5.5t_N50_N55\\|7.5t_N50_N62_N75` | 92,538 / 96,279 |
| 8982488970 | `3.5t_N35\\|5.5t_N50_N55\\|7.5t_N50_N62_N75` | 83,790 / 87,857 |
| 8981710330 | `3.5t_N35\\|5.5t_N50_N55\\|7.5t_N50_N62_N75` | 40,617 / 45,567 |
| **total** | | **EUR 1,026,807 / 1,061,419** |

**So the later pass was right and §3f overstated the dead end.** Its "EUR 1,026,807 across seven part numbers" is the worklist basis, which is the basis the table's Euro column uses; the same seven total **EUR 1,061,419** on `15_band_by_part_number.csv`'s own basis. Two further rotor part numbers carry an EPC band and are **not** in the banded decode — `8983767550`, `8979488071` and `8983767530`, all LCV_D-Max, **EUR 2,472,820** on the worklist basis, which is 55% of the family book on its own. So the family's banded euro is not EUR 1,026,807 but **EUR 3,499,626 across ten part numbers**, of which EUR 2,472,820 sits on the D-Max class rather than on a truck rung.

**Why the candidate table still reads as empty for the family:** all ten of those rows sit in `13_band_candidates_297_parts.csv` with a **blank `category`**, and the check that produced §3f keyed on that column. `category` is blank on **219 of the table's 297 rows**, so it cannot answer "which families does this cover".

### 3f-4. "The second-largest family by euro" — wrong; brake rotor is the largest

| Rank | Family | Part numbers | EUR (worklist) |
|---:|---|---:|---:|
| **1** | **brake rotor** | 109 | **4,457,248** |
| 2 | brake pad | 49 | 4,306,071 |
| 3 | fuel filter | 83 | 2,681,010 |
| 4 | air filter | 99 | 2,470,802 |
| 5 | oil filter | 74 | 2,179,491 |
| 6 | blower filter | 7 | 1,349,479 |

Brake rotor leads brake pad by **EUR 346,878**. The ranking holds on the family file (4,642,883 against 4,449,328) and on the additive band partition (brake rotor EUR 4.85M against brake pad EUR 3.99M). **Note what the correction strengthens rather than weakens:** brake pad and brake shoe together carry **EUR 5,192,029**, and §3c already records that both hold **zero band-exclusive part numbers**. The brake hole in the tonnage view is larger than the old sentence said, not smaller.

### 3f-5. The probe claim — qualified, not confirmed

`01_data\\91_build\\pn_ammo_probe_20260918\\_tonnage_capable.py` builds the candidate table from **two** evidence sources: the EPC decode JSONs (`epc_decode_batch1_20260919.json`, `epc_decode_batch2_20260919.json`) **and** `genuine_bvp_crossref.csv`. **So "reads the first route only" is wrong.** What is true is the limitation underneath it: the probe maps a model string to a band by looking each token up in `SERIES_BAND` / `series_to_tonnage.csv`, so **a token that is not one of the sourced series tokens — an F-series code such as `FRR`, or any wildcard — never yields a band**. That is why blower filter, urea filter, clutch booster and pilot bearing are absent. It is **not** why brake rotor is absent, because brake rotor is not absent.

### 3f-6. What could not be sourced, and was removed rather than replaced

- The scoping CSV's `route1_decode` column does not reproduce for **clutch booster** and **urea filter**: measured, a tolerant read of `pms_category` against `15_band_by_part_number.csv` gives **1** for each, against the file's **0**. No figure is carried forward; §3f names the discrepancy.
- The scoping CSV's `route3_family` column is the **worklist** row count, not a family-file count, so the route table built from it was wrong for blower filter and urea filter. Both are now stated from the family file.
- The cross-reference "route 2" counts have **no written definition** on disk. They reproduce exactly as a match on `genuine_pn` only — 1 / 3 / 1 / 28 / 2 — with the `bvp_pn` column excluded; read the way the workspace's own family file reads the same source, they are 1 / 6 / 2 / 37 / 3. **Both are now printed side by side rather than one being silently preferred.**

### 3f-7. What was NOT done in this pass

**No data file was edited.** Nothing in the pack was found demonstrably wrong at the data layer, and the five-family euro reconciles to the cent. **No build was run and no page was rebuilt.** Four documents were edited — `00_READ_ME_FIRST.md`, `01_BRIEF_FOR_THE_MODEL.md`, `02_CORRECTION_LOG.md`, `04_FILE_CATALOG.csv` — and all four were backed up first to `01_data\\91_build\\_backsafe_20260922_pack_3f\\`, with sha256 before and after, a `restore.ps1`, and a tested restore. **The pack still holds 20 content files.** The five `.bak_before_v4_20260922` files in the pack root are untouched and remain the v4 undo path; the catalog's file-count claim was corrected to describe them rather than the folder being changed.

**The version label was not bumped.** This pack remains **v4, 2026-09-22**, because a version change is a decision for its owner and the correction is additive. The dated entries here and in `00_READ_ME_FIRST.md` §14f are the record.
"""

write(LOG, t)

# ======================================================================
# 04_FILE_CATALOG.csv
# ======================================================================
t = read(CAT)

t = sub(t,
'''"Read before quoting a filename. 20 rows, one per file in this folder."''',
'''"Read before quoting a filename. 20 rows, one per content file. Five .bak_before_v4_20260922 backups also sit in the pack root and are deliberately not catalogued - they are the undo path for the v4 pass. The folder therefore holds 25 files and 20 content files; only the 20 are part of the pack."''',
'catalog: the file-count claim')

t = sub(t,
'''"Written on 2026-09-21. Its NMR section is superseded by read-me section 14 - the conflict was NKR, not NMR. The UTI 3.5t denominator and the drill-down are still BLOCKED."''',
'''"Written on 2026-09-21. Its NMR section is superseded by read-me section 14 - the conflict was NKR, not NMR. The UTI 3.5t denominator and the drill-down are still BLOCKED. Its brake-rotor scoping claims are superseded by read-me section 14f - see the dated entry in the correction log."''',
'catalog: evidence-of-correction caveat')

write(CAT, t)

print('\nAll edits applied.')

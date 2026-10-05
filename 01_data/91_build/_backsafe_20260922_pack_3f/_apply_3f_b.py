"""Apply the section 3f corrections to the remaining three files.

Each file keeps its own line-ending convention: the read-me is CRLF, these three are LF.
Writes go to a temp file in the same directory and are then os.replace()d.
"""
import io, os, sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

PACK = r'C:\Users\jerom\Desktop\claude\ISZE\01_data\90_INBOX\GPT_tonnage_pack_20260920'
BRIEF = os.path.join(PACK, '01_BRIEF_FOR_THE_MODEL.md')
LOG = os.path.join(PACK, '02_CORRECTION_LOG.md')
CAT = os.path.join(PACK, '04_FILE_CATALOG.csv')


def read(path):
    with open(path, 'rb') as fh:
        raw = fh.read()
    text = raw.decode('utf-8')
    crlf = text.count('\r\n')
    lf = text.count('\n')
    cr = text.count('\r')
    assert crlf == cr, path + ': lone CR found'
    ending = '\r\n' if crlf else '\n'
    print('  read %-26s %d lines, ending %r' % (os.path.basename(path), lf, ending))
    return text.replace('\r\n', '\n'), ending


def write(path, text, ending):
    data = text.replace('\n', ending).encode('utf-8')
    tmp = path + '.__tmp_3f__'
    with open(tmp, 'wb') as fh:
        fh.write(data)
    os.replace(tmp, path)
    print('  wrote %s  %d bytes' % (os.path.basename(path), len(data)))


def sub(text, old, new, label):
    n = text.count(old)
    assert n == 1, 'anchor %r matched %d times' % (label, n)
    print('  [ok] %s' % label)
    return text.replace(old, new)


# ======================================================================
# 01_BRIEF_FOR_THE_MODEL.md
# ======================================================================
t, e = read(BRIEF)

t = sub(t,
"""**And say what it does not cover.** **Five service families have no tonnage candidates at all — 174 part numbers, EUR 5.99M**, including **brake rotor (109 part numbers, EUR 4.46M)**, the second-largest family by euro. For brake rotor this is a dead end rather than a fixable join: 92 of its 109 part numbers carry no vehicle reference at all, and the family holds one vehicle string, `N*R,N*S`, a wildcard that cannot become a band. **A tonnage story presented without that sentence would be misreading its own coverage.**""",
"""**And say what it does not cover.** **[corrected 2026-09-22 evening]** **Five service families have almost no tonnage candidates — 174 part numbers, EUR 5.99M**, including **brake rotor (109 part numbers, EUR 4.46M)**, which is the **largest** family by euro and not the second. Three figures that stood in this paragraph are withdrawn: "92 of its 109 part numbers carry no vehicle reference at all" is one **resolution value** inside the family file, not the family's total — the other 17 rotor rows resolve `single_family` at high confidence and carry EUR 3,815,676, which is 85.6% of the family book; "the family holds one vehicle string" is true of the cross-reference only, and the EPC gives **7** rotor part numbers a tonnage band, one of them band-exclusive; and "no tonnage candidates at all" is wrong — those 7 are in the candidate table, all under a blank family label. **The dead end survives only in the narrow sense that no tonnage *trend* can be read for rotors**, because six of the seven are pooled across all three rungs. **A tonnage story presented without that sentence would be misreading its own coverage.**""",
'brief: question A coverage paragraph')

write(BRIEF, t, e)

# ======================================================================
# 02_CORRECTION_LOG.md
# ======================================================================
t, e = read(LOG)

t = sub(t,
"""**And a scoping result.** Brake rotor has no tonnage data — 109 part numbers, EUR 4.46M, the second-largest service family by euro. Scoped on the 22nd: **92 of its 109 part numbers have no vehicle reference at all** in the family file, 92 at low confidence, and the entire family carries exactly **one** vehicle string, `N*R,N*S`, which is a wildcard and cannot become a band. **There is no evidence on disk saying which vehicles these rotors fit.** That is a dead end for tonnage, not a fixable join, and it is now stated in §3f of the read-me.""",
"""**And a scoping result — partly wrong, and corrected the same evening.** [corrected 2026-09-22 evening; the full reconciliation is in the §3f section at the foot of this log] Brake rotor is the **largest** service family by euro, not the second: 109 part numbers and EUR 4,457,248, ahead of brake pad at EUR 4,306,071. **"92 of its 109 part numbers have no vehicle reference at all" misread the family file.** 92 is one resolution value; the other **17 rows resolve `single_family` (16 at high confidence)** and carry **EUR 3,815,676 — 85.6% of the family book**. And the family does not carry one vehicle string: `N*R,N*S` is the only one the *cross-reference* supplies, but the EPC route bands **7** of these rotors — `3.5t/5.5t/7.5t` on five, `7.5t` on `8981919560`, D-Max on three — and all of them sit in the candidate table under a blank `category`, which is how they were missed. **No tonnage *trend* can be read for rotors**, because six of the seven are pooled; the family is not short of evidence, it is short of a weight. The corrected text is §3f of the read-me.""",
'log: scoping result paragraph')

t = sub(t,
"""| 14 | **brake rotor has no band data at all.** 109 part numbers and **EUR 4,457,248** in the service worklist, **zero** candidate rows. The candidate table also holds nothing for blower filter, urea filter, clutch booster or pilot bearing. | The candidate table is not a random subset of the service list: 174 worklist part numbers carrying **EUR 5,990,933** have no tonnage candidate. Any tonnage story that omits brakes is omitting the second-largest service family by euro, and that must be said rather than left to be discovered. |""",
"""| 14 | **brake rotor has almost no band data.** 109 part numbers and **EUR 4,457,248** in the service worklist, and **7** candidate rows — not zero. **[corrected 2026-09-22 evening]** The seven carry a band and **one is band-exclusive**, but they sit in `13_band_candidates_297_parts.csv` under a **blank `category`**, so a family check keyed on that column reads the family as empty. Blower filter, urea filter, clutch booster and pilot bearing genuinely have none. | The candidate table is not a random subset of the service list, and its `category` column is blank on 219 of its 297 rows, so it cannot be used to decide which families are covered. **Brake rotor is the largest service family by euro (EUR 4,457,248 against brake pad's EUR 4,306,071), not the second**, and brake pad plus brake shoe add another EUR 5,192,029 with zero band-exclusive part numbers between them. Any tonnage story that omits brakes must say so rather than leave it to be discovered. |""",
'log: defect row 14')

t = t.rstrip('\n') + """

---

## Later still on 2026-09-22 — §3f reconciled against the source files (evening)

**Trigger:** §3f of the read-me, which had been corrected by hand earlier the same day. The table it carried did not reconcile: its per-route columns did not sum, and "92 of 109" did not match the family file the pack ships.

**Method.** Read the sections that record the v4 pass, then re-derived every figure in §3f and the two paragraphs around it from the files it names. **No data file was edited. No `build_*.py` was run.** The sources are `01_data\\00_derived\\epc_decode_worklist.csv`, `01_data\\00_derived\\vehicle_family_bands.csv` (byte-identical to the pack's `data_context\\22_vehicle_family_by_part.csv`, both 151,025 bytes), `01_data\\00_derived\\genuine_bvp_crossref.csv`, `01_data\\00_derived\\epc_decode_nseries_banded.csv`, `01_data\\90_INBOX\\tonnage_family_recovery_proposal_20260922.csv`, `01_data\\00_derived\\tonnage_missing_families_scope_20260922.csv`, and the pack's own `13_band_candidates_297_parts.csv` and `15_band_by_part_number.csv`.

### 3f-1. The heading and the table, corrected

**What it said:** "Five service families have **no tonnage candidates at all**", with cells `109 / 7 / 7 / 48 / 3` part numbers, EUR `4,457,248 / 1,349,479 / 134,108 / 47,151 / 2,947`, family-file counts `109 / 7 / 7 / 48 / 3`, and a verdict column reading "92 of 109: no vehicle reference", "6 single-family, 1 no vehicle", "5 no vehicle, 2 pooled", "37 single-family, 11 no vehicle", "2 single-family, 1 pooled".

**What is true.** The **part numbers and the euro all reproduce exactly**, and their total is right at 174 / EUR 5,990,933. **The two right-hand columns were wrong.**

| The cell | Was | Is | Source |
|---|---|---|---|
| brake rotor, "no tonnage candidates at all" | zero candidates implied | **7 part numbers carry a band**, one band-exclusive (`8981919560`, 7.5 t) | `13_band_candidates_297_parts.csv`, matched on `pn` |
| brake rotor, family-file verdict | "92 of 109: no vehicle reference" | **92 `no_vehicle_reference` (low) + 17 `single_family` (16 high, 1 medium)** | `22_vehicle_family_by_part.csv` → `resolution`, `confidence` |
| brake rotor, the 92 | read as the family total | **EUR 641,572**; the 17 are **EUR 3,815,676 = 85.6%** | `eur_all_markets` per row; the euro of the 92 confirmed on the worklist basis |
| blower filter, "in the family file" | 7 | **12 rows** — 6 `single_family` (medium), **6 `no_vehicle_reference` (low)** | same file |
| urea filter, "in the family file" | 7, "5 no vehicle, 2 pooled" | **5 rows** — 3 `shared_across_families`, 2 `no_vehicle_reference` — and **only 2 of the 7 worklist part numbers have a row under this family at all; the other 5 are filed under blower filter** | same file, joined on `pn` |
| clutch booster, "in the family file" | 48 | **48 — correct** | same file |
| pilot bearing, "in the family file" | 3 | **3 — correct** | same file |
| the route table, "via the family file" | 109 / 7 / 7 / 48 / 3 | those are **worklist** sizes; family-file row counts are **109 / 12 / 5 / 48 / 3** | `epc_decode_worklist.csv` vs `22_vehicle_family_by_part.csv` |
| the route table, route counts | 8/1, 0/3, 0/1, 0/28, 0/2 | EPC-banded: **8 / 0 / 0 / 0 / 0**. Cross-reference: **1 / 3 / 1 / 28 / 2** on `genuine_pn` only — the published numbers — and **1 / 6 / 2 / 37 / 3** including `bvp_pn`. Non-wildcard tokens: **1 / 0 / 0 / 18 / 3** | `genuine_bvp_crossref.csv`, `vehicle_model` |

### 3f-2. "92 of 109" — tested, and refuted as the family verdict

The figure is **wrong as stated and right as a count of one row value**. `22_vehicle_family_by_part.csv` holds **109 brake-rotor rows**: 92 at `resolution = no_vehicle_reference`, `confidence = low`, and **17 at `resolution = single_family`, 16 of them `confidence = high`**. So 92 of 109 rows do carry no vehicle reference — that much is true — but the pack printed it as the family's verdict, and the remaining 17 rows are not a rounding error: they carry **EUR 3,815,676, 85.6% of the family's EUR 4,457,248**.

**This is the mechanism of the error.** A 109-row family was summarised by its largest `resolution` bucket, and the bucket was read as the family. The column that would have caught it is `confidence`: the 92 are all **low** and the 17 are almost all **high**.

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

**So the later pass was right and §3f overstated the dead end.** Its "EUR 1,026,807 across seven part numbers" is the worklist basis, which is the basis the §3f Euro column uses; the same seven total **EUR 1,061,419** on `15_band_by_part_number.csv`'s own basis. **Three further rotor part numbers carry an EPC band and are not in the banded decode at all** — `8983767550`, `8979488071` and `8983767530`, all D-Max, **EUR 2,472,820** on the worklist basis, 55% of the family book on its own. So the family's banded euro is not EUR 1,026,807 but **EUR 3,499,626 across ten part numbers**, of which EUR 2,472,820 sits on the D-Max class rather than on a truck rung. **Nothing in this pass asserts that a D-Max class is a tonnage rung** — it is recorded because it is the family's evidence, and because the proposal carries it as its own band.

**Why the candidate table still reads as empty for the family:** all of those rows sit in `13_band_candidates_297_parts.csv` with a **blank `category`**, and the check that produced §3f keyed on that column. `category` is blank on **219 of the table's 297 rows**, so it cannot answer "which families does this cover".

### 3f-4. "The second-largest family by euro" — wrong; brake rotor is the largest

| Rank | Family | Part numbers | EUR (worklist) |
|---:|---|---:|---:|
| **1** | **brake rotor** | 109 | **4,457,248** |
| 2 | brake pad | 49 | 4,306,071 |
| 3 | fuel filter | 83 | 2,681,010 |
| 4 | air filter | 99 | 2,470,802 |
| 5 | oil filter | 74 | 2,179,491 |
| 6 | blower filter | 7 | 1,349,479 |

Brake rotor leads brake pad by **EUR 346,878**. The ranking holds on the family file (4,642,883 against 4,449,328) and on the additive band partition (brake rotor EUR 4.85M against brake pad EUR 3.99M). **The correction strengthens the commercial point rather than weakening it:** brake pad and brake shoe together carry **EUR 5,192,029**, and §3c already records that both hold **zero band-exclusive part numbers**. The brake hole in the tonnage view is larger than the old sentence said, not smaller.

### 3f-5. The probe claim — qualified, not confirmed

`01_data\\91_build\\pn_ammo_probe_20260918\\_tonnage_capable.py` builds the candidate table from **two** evidence sources: the EPC decode JSONs (`epc_decode_batch1_20260919.json`, `epc_decode_batch2_20260919.json`) **and** `genuine_bvp_crossref.csv`. **So "reads the first route only" is wrong.** What is true is the limitation underneath it: the probe maps a model string to a band by looking each token up in `SERIES_BAND` / `series_to_tonnage.csv`, so **a token that is not one of the sourced series tokens — an F-series code such as `FRR`, or any wildcard — never yields a band**. That is why blower filter, urea filter, clutch booster and pilot bearing are absent. It is **not** why brake rotor is absent, because brake rotor is not absent.

### 3f-6. What could not be sourced, and was removed rather than replaced

- The scoping CSV's `route1_decode` column does not reproduce for **clutch booster** and **urea filter**: measured, a tolerant read of `pms_category` against `15_band_by_part_number.csv` gives **1** for each, against the file's **0**. No figure is carried forward; §3f names the discrepancy instead.
- The scoping CSV's `route3_family` column is the **worklist** row count, not a family-file count, so a route table built from it was wrong for blower filter and urea filter. Both are now stated from the family file.
- The cross-reference route counts have **no written definition** on disk. They reproduce exactly as a match on `genuine_pn` only — 1 / 3 / 1 / 28 / 2 — with the `bvp_pn` column excluded, which is how the recovery proposal matched them; read the way the workspace's own family file reads the same source, they are 1 / 6 / 2 / 37 / 3. **Both are now printed side by side rather than one being silently preferred.**

### 3f-7. What was NOT done in this pass

**No data file was edited.** Nothing in the pack was found demonstrably wrong at the data layer, and the five-family euro reconciles to the cent. **No build was run and no page was rebuilt.** Four documents were edited — `00_READ_ME_FIRST.md`, `01_BRIEF_FOR_THE_MODEL.md`, `02_CORRECTION_LOG.md`, `04_FILE_CATALOG.csv` — and all four were backed up first to `01_data\\91_build\\_backsafe_20260922_pack_3f\\`, with sha256 before and after, a `restore.ps1`, a `MANIFEST.md`, and a **tested** restore. **The pack still holds 20 content files.** The five `.bak_before_v4_20260922` files in the pack root are untouched and remain the v4 undo path; the catalog's file-count claim was corrected to describe them rather than moving the folder.

**The version label was not bumped.** This pack remains **v4, 2026-09-22**, because a version change is its owner's decision and the correction is additive. The dated entries here and in `00_READ_ME_FIRST.md` §14f are the record.
"""

write(LOG, t, e)

# ======================================================================
# 04_FILE_CATALOG.csv
# ======================================================================
t, e = read(CAT)

t = sub(t,
'''"Read before quoting a filename. 20 rows, one per file in this folder."''',
'''"Read before quoting a filename. 20 rows, one per content file. Five .bak_before_v4_20260922 backups also sit in the pack root and are deliberately not catalogued - they are the undo path for the v4 pass. The folder therefore holds 25 files and 20 content files; only the 20 belong to the pack."''',
'catalog: the file-count claim')

t = sub(t,
'''"Written on 2026-09-21. Its NMR section is superseded by read-me section 14 - the conflict was NKR, not NMR. The UTI 3.5t denominator and the drill-down are still BLOCKED."''',
'''"Written on 2026-09-21. Its NMR section is superseded by read-me section 14 - the conflict was NKR, not NMR. Its brake-rotor scoping claims are superseded by read-me section 14f. The UTI 3.5t denominator and the drill-down are still BLOCKED."''',
'catalog: evidence-of-correction caveat')

write(CAT, t, e)

print('\nAll remaining edits applied.')

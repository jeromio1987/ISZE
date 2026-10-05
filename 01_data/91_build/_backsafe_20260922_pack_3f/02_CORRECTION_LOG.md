# Correction log — the tonnage pack, v1 through v4

**Dates:** 2026-09-20 (v1 → v2, from an external review), 2026-09-21 (the pipeline failure), 2026-09-22 (v2 → v3, the stale layer regenerated; then v3 → v4, the `NMR` question answered and the band-union defect found).
**Trigger:** an external review of the v1 pack (`01_data\CURSOR_TONNAGE_FEEDBACK_2026-09-20.md`).
**Method:** every numeric claim in that review was re-derived from the source files before anything was changed. **23 of 24 checks agreed with the reviewer.** One differed in detail only (see item 9). Nothing outside this pack folder was edited.
**Companion:** `03_EVIDENCE_OF_CORRECTION.md` — the eight minimum tests the reviewer asked for, run and reported, including the three that are blocked rather than passed.

## Later on 2026-09-22 — the tonnage layer was stale against its own source, and is now regenerated

Three days after the pack went out, the tonnage layer was found to be behind the billing it is built from. This is recorded because the mechanism will recur, and because nothing in the pipeline could see it.

**What happened.** `nseries_tonnage_evolution.csv` was built **19 September** from billing through **June 2026**. Its own metadata declares the source — `_deep_billing_cache.parquet` — and that source was rewritten on **21 September**, now carrying **July and August 2026**. So the layer was three days behind its input, and a page rebuilt on the 21st (`ISZE_PMS_Family_Evolution_v2.html`) consumed it. Every check passed throughout, because every check reads a file's *contents* and a stale file is internally consistent — which is precisely why a pass is not evidence that a file is current.

**The rebuild.** In dependency order: family bands → the modelled table → the banded decode and evolution series → the candidate tables → both pages. **The tie-out held at EUR 0.00**, which is the check that would have caught a lost family.

**What moved, and why it is small.** Only the two new months. Every complete period is unchanged.

| | through June | through August | change |
|---|---:|---:|---:|
| Tagged N-series total | 4,305,334 | 4,501,286 | **+195,953** |
| Band-exclusive, whole window | 1,289,762 | 1,340,014 | +50,252 |
| Exclusive share | 29.96% | **29.77%** | −0.19 pt |
| CY2026 months in period | 6 | 8 | +2 |

**A second instance, found by the new check.** `metrics_snapshot.json` was **3.9 days behind `sales_fact.parquet`** — reading as-of 17 September against billing through August — and was rebuilt. Two cases of the same defect in one day is the argument for the check, not a coincidence.

**The check now exists.** `freshness.no_stale_derived`, added 22 September: it reads declared pairs from `verification_fixtures.yaml` → `freshness.pairs` (8 pairs, 28 inputs) and warns when a derived file is older than an input. It **warns rather than fails** on purpose — some staleness is deliberate and a hard fail would block the pipeline for a monthly refresh. Visible is what it was not.

**Two lessons from building it, both worth keeping.**

1. **Its first version false-alarmed immediately.** It keyed off `_deep_billing_cache.parquet`, and the family-page build rewrites that cache with *identical content* on every run — so an mtime comparison against it is meaningless. It now keys off `sales_fact.parquet`, the real input.
2. **A QA script for the tonnage page had been printing FAIL and exiting 0.** `qa_pms_tonnage_evolution.py` collected its failures into a list and then fell off the end of the file with status 0, so it had never been able to fail a gate. Its expected labels had also drifted from the page's deliberately plainer wording, so it was reporting three false failures against real text. Both fixed: it now exits non-zero on failure, and its labels match the page. **A check that reports a failure and returns success is worse than no check, because the gate reads green.**

**And a scoping result.** Brake rotor has no tonnage data — 109 part numbers, EUR 4.46M, the second-largest service family by euro. Scoped on the 22nd: **92 of its 109 part numbers have no vehicle reference at all** in the family file, 92 at low confidence, and the entire family carries exactly **one** vehicle string, `N*R,N*S`, which is a wildcard and cannot become a band. **There is no evidence on disk saying which vehicles these rotors fit.** That is a dead end for tonnage, not a fixable join, and it is now stated in §3f of the read-me.

## On 2026-09-21 — the pipeline failure, diagnosed and fixed

The pack went out on 20 Sep reporting **one failing check** (152 pass / 1 warn / **1 fail**, `lost_sales.billed_ties_to_parts_base`, delta EUR 5,511,194.53). That check now reports a pass and the two warnings that remain are informative rather than cosmetic. **The cause was not a broken number**, and the diagnosis is recorded here because the same trap will catch the next person. **Note the wording deliberately: a check that passes is not a cleared pipeline, and a pass count is not evidence that the tonnage numbers are right.** See §11 of the read-me.

**What the delta was.** Exactly the **July–August 2026** billing. `lost_sales_model.csv` was built on 2026-09-18 against billing through **2026-06-30**. `sales_fact.parquet` was then extended with the Jul–Aug file (billing horizon 2026-06-30 → 2026-08-31). The model still tied the parts base to the cent — **EUR 112,089,306.89** — but the verifier compared it against *all* billing on file, not the billing the model was built from. A period movement read as a method failure.

**Why this is the same class of error as the 11% one.** The workspace already publishes a declared billing horizon: `metrics_snapshot.json` → `sales.parts_base_data_through` = **2026-06-30**, which the snapshot builder derives from `max(billing_date)` with a comment saying it exists so *"a period movement can never be mistaken for a method movement"*. The verifier ignored it. That is the second time in this workstream that a declared period boundary existed on disk and was not used.

**The fix, in the right place.** Not in the number — the tolerance stays at zero and the model must still equal the base to the cent. `verify_derived_pipeline.py` now measures the tie-out at a declared cut-off and, when the model sits behind it, tries earlier month-ends to see which one the model actually ties. If it ties one, the check reports **stale** (warn), names the month the model covers, and names the builder to run. If it ties no month-end at all, it still **fails** — so a real break cannot hide behind the new wording. Two config keys added to `verification_fixtures.yaml`: `billing_cutoff: 2026-06-30`, deliberately frozen and the same value the snapshot publishes, and `stale_billing_is_warn: true`.

**What was deliberately not done: the model was not rebuilt.** It is stale by two months, and rebuilding it is a live data change to a delivered model and a locked pricing/deliverable chain. The verifier now reports the staleness as its own check — `lost_sales.model_is_current`, a warn — so the fact stays visible even while the tie-out passes. That is the intended trade: **the tie-out passing and the model being current are two different facts**, and the original false alarm happened precisely because they were collapsed into one check.

**One consequence that should be said out loud:** the tie-out passes against a **frozen** 2026-06-30 cut-off while the model is two months behind the billing. The verifier reports both — the tie-out as a pass and the staleness as its own check, `lost_sales.model_is_current`. When the model is rebuilt, `billing_cutoff` in `verification_fixtures.yaml` and `sales.parts_base_data_through` in `metrics_snapshot.json` must move together: both are deliberately frozen so a period movement cannot be mistaken for a method movement.

## Source corrections — things v1 got wrong

| # | What v1 said | What is true | Where it is fixed |
|---|---|---|---|
| 1 | Band-exclusive share of about **11%** for 2025. | **31.8%**. The v1 denominator summed every row of the band file, including the non-additive `also_fits_band` applicability views, which repeat purchasing already counted. Correct denominator: `sums_to_n_series_total == "yes"`. | `00_READ_ME_FIRST.md` §1, §3c, §4; `data_nseries_bands\10_additive_billing_partition.csv` |
| 2 | The **297** band candidates were presented as though they described the same universe as the **835** service worklist. | They overlap on **91** part numbers. **206** candidates sit outside the worklist; **744** worklist rows never got a band read. The two euro columns are on different bases and **cannot be compared or added**. | §3a; `14_part_population_bridge.csv` |
| 3 | "Nothing sits in the 5.5 t band by itself. Zero part numbers in the whole service list are exclusive to 5.5 t." | The candidate table carries **16** exclusive 5.5 t part numbers (EUR 16,834). The accurate, narrower statement is that the **strict in-scope N-series decode** carries none. | §3b, §7 |
| 4 | The 143-part-number slice and its euro quoted without qualification. | Both true, but the euro basis differs from the worklist universe. Now stated with the basis named. | §3a |
| 5 | "the flat 1.25 … overstates ITUK filter demand by about 72%, and correcting it moves ITUK oil-filter cover from about 116% down to the 70s." | **Wrong direction, withdrawn.** Cover is `actual ÷ expected`, so a lower expected **raises** cover. Worked: 35.1% → 44.5%, up about 9 points on the deck's own example. | §5; `01_BRIEF_FOR_THE_MODEL.md` §5 |
| 6 | 14,494 km/yr labelled "ITUK N35" in one place and "IUK N35" in another. | The figure is **IUK** — the UK light commercial Grafter fleet. ITUK's own measured figure differs. | §5, §10; `data_context\21_mileage_reference.csv` |
| 7 | "CY2025 is … 11 months on the PRISM basis." | The file does not support that. 2025 `months_in_period` runs across 1, 2, 3, 5, 6, 7, 9, 10, 11 and 12 by market. | §8 |
| 8 | UTI's absent 3.5 t band presented as an explained limit. | The model carries no UTI 3.5 t fleet, yet the billing records **EUR 4,135** of exclusive 3.5 t purchases (EUR 471,921 on the pooled view). A live inconsistency, now stated as one and marked **BLOCKED** in the evidence document. | §3d, §12; `03_EVIDENCE_OF_CORRECTION.md` test 6 |
| 9 | The review states the worklist rows outside the candidate table number **629**. | Re-derived as **744** (835 − 91). The reviewer's other three figures — 835, 91, 206 — all reproduce exactly; this single one does not. Differs in detail, not in substance. | §3a |
| 9b | The conflict was described as **six** part numbers, caused by `NKR`. | **Wider and different.** Six rows are `NKR`-driven (the retired dictionary said 5.5 t, both newer tables say 3.5 t). A further **10** exclusive-5.5 t rows rest on **`NMR`**, which is the one *genuine weight conflict* between the two tables — and the model-code table contradicts itself on it, carrying band `7.5t` with the label `"5.5 t GVW"`. **[corrected in v4 — this row was wrong]** All 16 rows were called blocked. Later the same day the evidence showed **14 of the 16 name `NKR` and only 2 name `NMR`**, and six are already `3.5t_N35 / single_band` in the live file. The blocker framing is withdrawn; see the v4 section below. | §7; `03_EVIDENCE_OF_CORRECTION.md` §3 |

## Questions the review left open that this pass closed

| # | Open question | Answer found | Evidence |
|---|---|---|---|
| 10 | Does `months_in_period` count months in the available source extract, or months with purchases? | **Months with purchases of the selected parts.** `months = ("m", "nunique")` over the billing rows, then `period_is_complete = months_in_period >= 12`. | `03_analytics\Isuzu\prism\scripts\build_nseries_tonnage_bands.py` lines 573–584 |
| 11 | What is the cause of the 5.5 t / 3.5 t conflicts? | The older probe script hard-coded `NKR → 5.5t`; the sourced series table places `NKR` at **3.5 t** (JP VIN register) and leaves `NHR` unresolved. All six conflicts are `NKR`-evidenced. | `_tonnage_capable.py` vs `16_series_token_to_band.csv`; `15_band_by_part_number.csv` |

## Defects found in the pack that the review did not name

| # | Defect | Consequence |
|---|---|---|
| 12 | `period_is_complete` conflates purchase activity with source coverage. A complete source with no purchase of those parts in some months is labelled incomplete. | `comparable_to_previous` is conservative in the wrong way: "we did not buy" is indistinguishable from "we do not have the data". Needs a fix at source. |
| 13 | No 10 t band exists, so the 7.5 t grouping cannot separate 7.5 t from 10 t. | An ITUK-versus-UTI 7.5 t mix comparison cannot be built from this data, and the grouping must not be relabelled as a precise weight distribution. |
| 14 | **brake rotor has no band data at all.** 109 part numbers and **EUR 4,457,248** in the service worklist, **zero** candidate rows. The candidate table also holds nothing for blower filter, urea filter, clutch booster or pilot bearing. | The candidate table is not a random subset of the service list: 174 worklist part numbers carrying **EUR 5,990,933** have no tonnage candidate. Any tonnage story that omits brakes is omitting the second-largest service family by euro, and that must be said rather than left to be discovered. |
| 15 | `17_model_code_to_tonnage.csv` disagrees with itself on `NMR` and `NMR85`: band `7.5t_N50_N62_N75`, weight label `"5.5 t GVW (N50 / N55 ladder)"`. | A band column and a label column telling different stories on the same row. This is the row that had to be ruled on — but **only 2 of the 16 part numbers depend on `NMR` at all**, and the ruling that came back puts `NMR` at 5.5 t in Europe, so this table's band column is a filing error while its weight label is right. See the v4 section below; do not carry "the entire blocked 5.5 t band" forward. |

## Confirmed correct in v1 — no change needed

Re-derived and holding, so the corrected documents keep them: the additive partition equals the tagged N-series total (EUR 4,305,334, delta EUR 0.00); the 835 / 297 / 143 / 154 counts; the six band combinations and their euro; the 164 heavy-truck part numbers; the 53 pooled-across-families part numbers; 120 model codes with 50 unresolved; the two-lane rule; that market actuals are market-level on every row; that UTI has no 3.5 t row in the demand model; and the six named mapping conflicts.

## What was NOT done

No source file was edited. No dashboard, atlas or HTML was rebuilt or redesigned. The billing basis was not replaced. The six `NKR` records the reviewer named were **not** resolved in the v1→v3 passes — they were flagged and left visible. **That changed in v4:** the later evidence passes established `NKR` at 3.5 t, so the blocker framing was withdrawn and §7 was rewritten. The two `NMR` rows are still left `unresolved`, deliberately. The `months_in_period` defect is documented, not patched.

---

## Later still on 2026-09-22 — v4: the `NMR` question answered, a figure withdrawn, and a defect found in the headline

**Trigger:** two evidence passes that ran after v3 was written — `NMR_ruling_impact_20260922.md` with its CSV, `NMR_blast_radius_20260922.md`, `band_union_audit_20260922.md`, `isuzu_n_series_public_weights_20260922.md` and `NMR_MAPPING_DECISION_NOTE_20260922.md`, all in `01_data\90_INBOX\`.

**Method.** Every number below was re-derived from the files in this pack before anything was edited, and the pack's own copy of each file was re-added and checked against the figure printed in the documents. **Five corrections, one of them a withdrawal. No data file was edited and no build was run** — the pack's data was regenerated on 22 September and is current.

### v4-1. The sixteen-row conflict was `NKR`, not `NMR` — the blocker framing is withdrawn

**What v3 said:** sixteen part numbers are parked on an `NMR` conflict and this blocks the whole 5.5 t band; all sixteen rows are blocked.

**What is true.** Reading each of the sixteen vehicle strings in the cross-reference: **14 name `NKR` and only 2 name `NMR`**; none name both. Their `5.5 t` label comes from the retired probe dictionary `SERIES_BAND` in `_tonnage_capable.py`, which hard-codes `NKR → 5.5t`. Both newer tables and Isuzu's own UK material put `NKR` at **3.5 t** (N1, "not exceeding 3500kgs GVM"). **Six of the sixteen are already `3.5t_N35 / single_band` in the live band file today, carrying EUR 11,381.95**, with the recorded reason *"One band from the series named on this part number: NKR."*

**So the candidate table is stale and the band file is right.** This is a relabelling question, not an open weight conflict, and it does not hold up the band.

**5.5 t is not measurable on this table.** After the correction: **2 part numbers, EUR 0.00** — and even those two rest only on the wildcard `NL*,NMR`, so their honest verdict is `unresolved`, not 5.5 t.

**The money.** EUR 17,477.34 for the whole sixteen — 0.39% of the tagged N-series book, EUR 0.48 per truck in service across the 36,793 CV-standard trucks in the 18 markets (2025E). At the very most, **EUR 117,946.78 of band movement over all years** on the 7.5 t band (EUR 36,578.17 in calendar 2025). Not the large blocker v3 implied.

**`NMR` is a 5.5 t truck in Europe, and that is now sourced** — Isuzu's own German data sheet (`MODELL NMR88L`, 5,500 kg), Isuzu's own German range page (`N-SERIE 5,5 T TYP N55 NMR`, against `N75 / NPR` at 7.5 t), and a Swiss type approval for `NMR85` at 5,500 kg. **European scope only:** the same letters are 5.2 t in the Gulf, 6.0 t on the 2026 German range leaflet and 6.5 t in Taiwan, because the letter group fixes a cab, not a weight. **Never state a weight for `NMR` without the European scope label.**

**Where it is fixed:** `00_READ_ME_FIRST.md` §7 rewritten, §1, §3b, §9, §10, §12 amended, and §14a added; `01_BRIEF_FOR_THE_MODEL.md` must-not-get-wrong item on the residue and the status gate; `04_FILE_CATALOG.csv` rows for the candidate table, the bridge, the band-by-part file and the series table.

### v4-2. A previously stated figure is WITHDRAWN: the 30.02% does not hold

**Withdrawn, in the words the correction uses: "The claim that the exclusive share rises to 30.02% under the NMR correction is withdrawn. That arithmetic double-counted six rows that are already `3.5t_N35 / single_band` in the file today; their EUR 11,381.95 is most of the EUR 14,198.10 the NMR pass starts from."**

The six rows were never in the 5.5 t shared pool. Each is `in_n_series_family = yes`, `band_status = single_band`, `band_count = 1`, `tonnage_band = 3.5t_N35`. Adding their EUR 11,381.95 to the 3.5 t exclusive total counts them twice. **The headline does not move for that reason, and the part-number count behind it does not move from 44.**

**And the `NMR` correction and the v4-3 defect do not interact.** They concern disjoint part numbers — 16 and 4 respectively, 20 distinct, intersection empty — so neither one's arithmetic may be borrowed to explain the other.

### v4-3. The headline is inflated by EUR 2,645.43, and the file has NOT been corrected

**The headline the file carries:** band-exclusive **EUR 1,340,014 of EUR 4,501,286 = 29.77%** (29.7696% to four places, and it resolves exactly: 3.5 t EUR 14,198.10 on 10 part numbers plus 7.5 t EUR 1,325,815.84 on 34, plus 5.5 t EUR 0.00).

**The defect:** the exclusive set is inflated by **EUR 2,645.43**, so the true figure is **29.7108% — a fall of 0.0588 pt.** The band-exclusive file has not been rebuilt, so it still prints 29.77%. **This pack therefore states both numbers, and says which is which.**

**Two causes, both at source, and neither of them in the union step:**

1. **`series_to_tonnage.csv` carries no suffixed rows.** `NMR85` has no entry at all, so it never resolves to a band. The build writes that token into `series_unresolved` on **24 rows**; on 23 of them the row also names the bare `NMR`, which does resolve, so nothing shows. On one row it is the only 5.5 t evidence.
2. **A cross-reference string is separated by U+3001, the ideographic comma:** the row reads `NKR、NMR,NLR`. The build splits on `[,\s]+`, which does not include U+3001, so the first field arrives as `NKR、NMR`, fails the anchored whole-token test, and **`NKR` and `NMR` are both silently lost.** `NLR` survives and the row is called exclusive 3.5 t.

**The affected rows:** `5878320470`, a brake shoe carrying **EUR 2,645.43 — the whole euro of the defect** — and `5876103260`, the same cross-reference row, carrying EUR 0. 3.5 t falls from 10 exclusive part numbers to 9; 5.5 t gains the euro as `also_fits` and never as exclusive; 7.5 t is untouched. Nothing is apportioned — the row is pooled whole, per the pack's own rule.

**Do not quote `8983615742` as the money.** It is the right shape — it names `NMR85` without the bare `NMR`, so it is the one row of the 24 that turns on the missing table entry — but it carries **EUR 0.00 in this model**. Its EUR 75,052 sits in `sales_fact.parquet`, a different universe covering every market and every line, and it does not sit inside the band-exclusive set.

**Where it is fixed:** `00_READ_ME_FIRST.md` §1, §3c and §14c; `01_BRIEF_FOR_THE_MODEL.md` rules 3 and the question A figures; `04_FILE_CATALOG.csv` rows for the main brief and the one-page brief.

### v4-4. A source defect recorded, so the next reader is not misled

**The build's stated reason on the single-band branch prints the token list unconditionally.** On `8983615742` the file says *"One band from the series named on this part number: NMR85, NNR, NPR, NQR."* That reads as "the union returned one band" — and it is not. **The union step at `build_nseries_tonnage_bands.py` lines 479–483 is correct**; it was never given `NMR85` at all. The loss is upstream, in `series_to_tonnage.csv` (no suffixed rows) and in the splitter at lines 313–319 (U+3001).

**This misled one audit already**, which read the sentence as evidence that the code already believed `NMR85` was not a band and therefore looked in the wrong place. Recorded as a defect of the reason text, not of the union. Where it is fixed: `00_READ_ME_FIRST.md` §14d.

### v4-5. One open lead, recorded and deliberately NOT resolved

**`5876100771`** — clutch kit, in the N-series family, **EUR 52,174.49** over the whole window — carries a **7.5 t registry tag**, a `band_count` of **1**, and a **blank** `tonnage_band` with `band_status = no_series_found`, because the branch that would read the tag never runs when no series is named. **It does not inflate the headline:** on the band file the row has no band and is not counted as exclusive. Recorded as a lead and **not traced or fixed in this pass**; it is worth someone tracing through the evolution file, which is all v3's audit claimed for it.

### v4-6. Document figures corrected because they did not reproduce from the shipped files

Found while re-deriving the above. All are in `00_READ_ME_FIRST.md` unless stated; none changes a KPI, and each is corrected to the file shipped in this pack.

| Where | v3 printed | The shipped file says |
|---|---|---|
| §3c, CY2026 (part year) | 627,086 additive / 174,695 exclusive / 27.9% | **823,039 / 224,948 / 27.33%** |
| §3c, FY2027 (part year) | 246,120 / 70,038 / 28.5% | **442,073 / 120,290 / 27.21%** |
| §3c, whole-window line | 1,289,762 of 4,305,334 = 29.96% | **1,340,014 of 4,501,286 = 29.77%** (the v2→v3 movement, not re-applied to the line) |
| §3b, six euro figures | 12,398,839 / 7,191,312 / 3,766,594 / 260,271 / 69,936 / 16,834 | **12,877,246 / 7,536,827 / 3,965,018 / 267,403 / 81,790 / 17,477** — the counts were right, the euro did not reproduce |
| §3e, pooled and unresolved groupings | shared_across_bands 118 / EUR 3,010,701; `unresolved_series` 4 / EUR 116,097; no_series_found 32 / EUR 206,139 | **118 / EUR 3,229,690; `series_unresolved` 4 / EUR 122,962; 32 / EUR 220,164** |
| §3e, pooled-across-families | 53 part numbers / EUR 4,158,264 | **54 / EUR 4,434,662** from `22_vehicle_family_by_part.csv`. Neither v3 figure reproduces from any file checked |
| §3c, exclusive part numbers per band | "15 to 17 and 2 to 4" | **34 (7.5 t) and 10 (3.5 t)**, in-family, whole window |
| `01_BRIEF_FOR_THE_MODEL.md`, rule 3 | all-row sum EUR 24.48M; additive EUR 4.31M | **EUR 25.60M and EUR 4.50M** |
| `01_BRIEF_FOR_THE_MODEL.md`, pass count | 153 pass / 2 warn / 0 fail (2026-09-21) | **154 / 2 / 0** (2026-09-22T16:44:37Z), the report shipped in this pack |

### v4-7. What was NOT done in v4

**No data file was edited.** The pack was regenerated on 22 September and is current; nothing in it was found demonstrably wrong. **No build was run and no page was rebuilt.** The pack still holds exactly 20 files. The five corrected documents were backed up first, with the suffix `.bak_before_v4_20260922`. The `NMR` residue, the headline defect and the `5876100771` lead are **documented, not fixed** — the first two need a rebuild, and the third needs tracing.

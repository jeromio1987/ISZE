# Map of the pricing pack, 14 to 20 September 2026

This pack holds the pricing work that was done between 14 and 20 September 2026: the base-price
comparison behind the October revision, the FX view, the margin simulation by market, the AIM
information split by source, the classification work on part numbers, and the policy papers. This
page is the map of what is inside it, so you can go straight to the view you want instead of
opening folders one by one. Every path below was checked on disk on 21 September 2026. Each
numbered folder holds a full copy of the file and, beside it, a Windows shortcut to the live
original; the paths here point at the copy inside the pack, which is the one that always opens.
Where a view is also live outside the pack, that folder is shown in the last two sections.

The pack root is
`C:\Users\jerom\Desktop\claude\ISZE\01_data\01_Pricing\_PACK_AIM_Pricing_7d_20260914_20260920`

---

## 00_START_HERE — read these first

| What it answers | Where it is | Double-click to open |
|---|---|---|
| What to do next: fill the missing base prices, then rebuild in this order | `C:\Users\jerom\Desktop\claude\ISZE\01_data\01_Pricing\_PACK_AIM_Pricing_7d_20260914_20260920\00_START_HERE\INDEX.md` | none — open the file |
| A one-minute orientation to the pack | `C:\Users\jerom\Desktop\claude\ISZE\01_data\01_Pricing\_PACK_AIM_Pricing_7d_20260914_20260920\00_START_HERE\README.md` | none — open the file |
| Which part numbers still have no base price, and what is needed on each (599 rows) | `C:\Users\jerom\Desktop\claude\ISZE\01_data\01_Pricing\_PACK_AIM_Pricing_7d_20260914_20260920\00_START_HERE\BP_missing_for_price_simulation_20260920.xlsx` | `OPEN_BP_missing.cmd` |
| How much of the price list sits at each level of the parts family tree | `C:\Users\jerom\Desktop\claude\ISZE\01_data\01_Pricing\_PACK_AIM_Pricing_7d_20260914_20260920\00_START_HERE\AIM_class_status_overview_20260919.xlsx` | `OPEN_AIM_class_status.cmd` |
| The plan for the Snap-on lookup session: 744 part numbers, EUR 254,220 of billed value | `C:\Users\jerom\Desktop\claude\ISZE\01_data\01_Pricing\_PACK_AIM_Pricing_7d_20260914_20260920\00_START_HERE\EQ_HIT_SESSION_BRIEF.md` | `OPEN_EQ_HIT_SESSION.cmd` |
| What was fixed on the main part-number table on 20 September | `C:\Users\jerom\Desktop\claude\ISZE\01_data\01_Pricing\_PACK_AIM_Pricing_7d_20260914_20260920\00_START_HERE\AIM_EQ_DONE_BRIEF_20260920.md` | none — open the file |

## 01_BP_impact — the base-price comparison

| What it answers | Where it is | Double-click to open |
|---|---|---|
| The weighted price increase across the whole book, by market, with coverage on each row | `C:\Users\jerom\Desktop\claude\ISZE\01_data\01_Pricing\_PACK_AIM_Pricing_7d_20260914_20260920\01_BP_impact\ISZE_Price_BP_Weighted_Compare.html` | `OPEN_ISZE_Price_BP_Weighted_Compare.cmd` |
| Billed lines that have no matching price on one side (1,036 rows) | `C:\Users\jerom\Desktop\claude\ISZE\01_data\01_Pricing\_PACK_AIM_Pricing_7d_20260914_20260920\01_BP_impact\Unpriced_lines_no_matching_price.xlsx` | none — open the file |
| Part numbers where we do not know whether the part comes from Japan or Thailand | `C:\Users\jerom\Desktop\claude\ISZE\01_data\01_Pricing\_PACK_AIM_Pricing_7d_20260914_20260920\01_BP_impact\Parts_needing_source_or_origin.xlsx` | none — open the file |
| The missing base-price list as data, split into all, only-old-side, only-new-side | `C:\Users\jerom\Desktop\claude\ISZE\01_data\01_Pricing\_PACK_AIM_Pricing_7d_20260914_20260920\01_BP_impact\bp_missing_complete_for_simulation_20260920.csv` | none — open the file |
| The same split, one file per side | `C:\Users\jerom\Desktop\claude\ISZE\01_data\01_Pricing\_PACK_AIM_Pricing_7d_20260914_20260920\01_BP_impact\bp_missing_old_for_simulation_20260920.csv` and `bp_missing_new_for_simulation_20260920.csv` | none — open the files |
| The part-number detail behind the compare, and the record of how it was built | `C:\Users\jerom\Desktop\claude\ISZE\01_data\01_Pricing\_PACK_AIM_Pricing_7d_20260914_20260920\01_BP_impact\price_bp_weighted_compare_pn.csv` and `price_bp_weighted_compare_meta.json` | none — open the files |

## 02_FOB_FX — the October revision with the exchange rate

| What it answers | Where it is | Double-click to open |
|---|---|---|
| The October 2026 revision with the FX overlay applied, split by market and by source | `C:\Users\jerom\Desktop\claude\ISZE\01_data\01_Pricing\_PACK_AIM_Pricing_7d_20260914_20260920\02_FOB_FX\ISZE_Pricing_Revision_AIM_FX_20261001.html` | `OPEN_HTML_Pricing_Revision_AIM_FX.cmd` |
| The same revision as a workbook | `C:\Users\jerom\Desktop\claude\ISZE\01_data\01_Pricing\_PACK_AIM_Pricing_7d_20260914_20260920\02_FOB_FX\Pricing_Revision_AIM_FX_20261001.xlsx` | `OPEN_Pricing_Revision_AIM_FX_20261001.cmd` |

## 03_Simulation_stack — what each market's revision does to margin

| What it answers | Where it is | Double-click to open |
|---|---|---|
| The margin simulation by market (PR00, UTI, UMI, CIS), one row per part number | `C:\Users\jerom\Desktop\claude\ISZE\01_data\01_Pricing\_PACK_AIM_Pricing_7d_20260914_20260920\03_Simulation_stack\ISZE_Pricing_Stack_Simulation_2026-09-19.xlsx` | `OPEN_Pricing_Stack_Simulation.cmd` |
| What the simulation is built on: the inputs, the recipe and the open questions | `C:\Users\jerom\Desktop\claude\ISZE\01_data\01_Pricing\_PACK_AIM_Pricing_7d_20260914_20260920\03_Simulation_stack\ISZE_Pricing_Simulation_Spec_Basis.xlsx` | `OPEN_ISZE_Pricing_Simulation_Spec_Basis.cmd` |
| A short view of the stack that was applied | `C:\Users\jerom\Desktop\claude\ISZE\01_data\01_Pricing\_PACK_AIM_Pricing_7d_20260914_20260920\03_Simulation_stack\PRICING_STACK_APPLIED_2026-09-19.html` | `OPEN_PRICING_STACK_APPLIED.cmd` |
| The written explanation of how the weighted increase is measured, and the two items still open | `C:\Users\jerom\Desktop\claude\ISZE\01_data\01_Pricing\_PACK_AIM_Pricing_7d_20260914_20260920\03_Simulation_stack\PRICING_STACK_APPLIED_2026-09-19.md` | none — open the file |
| The two result files behind the simulation and the applied view | `C:\Users\jerom\Desktop\claude\ISZE\01_data\01_Pricing\_PACK_AIM_Pricing_7d_20260914_20260920\03_Simulation_stack\pricing_stack_simulation_2026-09-19.json` and `pricing_stack_applied_2026-09-19.json` | none — open the files |

## 04_AIM_x_revision — the revision split by parts family and source

| What it answers | Where it is | Double-click to open |
|---|---|---|
| The revision read by parts family, by market and by source of supply | `C:\Users\jerom\Desktop\claude\ISZE\01_data\01_Pricing\_PACK_AIM_Pricing_7d_20260914_20260920\04_AIM_x_revision\ISZE_Pricing_Revision_AIM_Source.html` | `OPEN_Pricing_Revision_AIM_Source.cmd` |
| The same analysis as a workbook | `C:\Users\jerom\Desktop\claude\ISZE\01_data\01_Pricing\_PACK_AIM_Pricing_7d_20260914_20260920\04_AIM_x_revision\Pricing_Revision_AIM_Source_Analysis.xlsx` | `OPEN_Pricing_Revision_AIM_Source_Analysis.cmd` |
| Trial view: every distributor on one page | `C:\Users\jerom\Desktop\claude\ISZE\01_data\01_Pricing\_PACK_AIM_Pricing_7d_20260914_20260920\04_AIM_x_revision\ISZE_Pricing_Revision_AIM_Source_PROTOTYPE_AllDB.html` | `OPEN_Pricing_Revision_AIM_Source_PROTOTYPE_AllDB.cmd` |
| Trial view: Nordic customers only | `C:\Users\jerom\Desktop\claude\ISZE\01_data\01_Pricing\_PACK_AIM_Pricing_7d_20260914_20260920\04_AIM_x_revision\ISZE_Pricing_Revision_AIM_Source_PROTOTYPE_NordicsCust.html` | `OPEN_Pricing_Revision_AIM_Source_PROTOTYPE_NordicsCust.cmd` |
| The summarised table behind the analysis, the row-level detail, and how it was built | `C:\Users\jerom\Desktop\claude\ISZE\01_data\01_Pricing\_PACK_AIM_Pricing_7d_20260914_20260920\04_AIM_x_revision\pricing_aim_source_cube.csv`, `pricing_aim_source_lines.parquet` and `pricing_aim_source_meta.json` | none — open the files |

## 05_AIM_classification — where the part numbers sit in the family tree

| What it answers | Where it is | Double-click to open |
|---|---|---|
| How the classification was done, what is settled and what is still open | `C:\Users\jerom\Desktop\claude\ISZE\01_data\01_Pricing\_PACK_AIM_Pricing_7d_20260914_20260920\05_AIM_classification\ISZE_AIM_Classification_Paper.html` | `OPEN_ISZE_AIM_Classification_Paper.cmd` |
| Which part families sit where, as a map | `C:\Users\jerom\Desktop\claude\ISZE\01_data\01_Pricing\_PACK_AIM_Pricing_7d_20260914_20260920\05_AIM_classification\ISZE_AIM_Repertoire_Map_2026-09-17.html` | `OPEN_ISZE_AIM_Repertoire_Map.cmd` |
| The same families as a spider view | `C:\Users\jerom\Desktop\claude\ISZE\01_data\01_Pricing\_PACK_AIM_Pricing_7d_20260914_20260920\05_AIM_classification\ISZE_AIM_Repertoire_Spider_2026-09-17.html` | `OPEN_ISZE_AIM_Repertoire_Spider.cmd` |
| The parts atlas, as a single browsing page | `C:\Users\jerom\Desktop\claude\ISZE\01_data\01_Pricing\_PACK_AIM_Pricing_7d_20260914_20260920\05_AIM_classification\AIM_Parts_Atlas.html` | none — open the file (no launcher in this folder) |
| How much of the price list sits at each level | `C:\Users\jerom\Desktop\claude\ISZE\01_data\01_Pricing\_PACK_AIM_Pricing_7d_20260914_20260920\05_AIM_classification\AIM_class_status_overview.xlsx` | none — open the file |
| Scoring of everything that was not on the parts family tree | `C:\Users\jerom\Desktop\claude\ISZE\01_data\01_Pricing\_PACK_AIM_Pricing_7d_20260914_20260920\05_AIM_classification\Not_on_AIM_4SIGNAL_classify.xlsx` | `OPEN_4SIGNAL_classify.cmd` |
| What was agreed and applied from that scoring | `C:\Users\jerom\Desktop\claude\ISZE\01_data\01_Pricing\_PACK_AIM_Pricing_7d_20260914_20260920\05_AIM_classification\Not_on_AIM_4SIGNAL_APPLIED.xlsx` | `OPEN_4SIGNAL_APPLIED.cmd` |
| What is genuinely still unclassified, ranked by billed value | `C:\Users\jerom\Desktop\claude\ISZE\01_data\01_Pricing\_PACK_AIM_Pricing_7d_20260914_20260920\05_AIM_classification\AIM_residual_TRUE_OPEN.xlsx` | `OPEN_AIM_residual_TRUE_OPEN.cmd` |
| The list to work through, and what remains after the tools ran | `C:\Users\jerom\Desktop\claude\ISZE\01_data\01_Pricing\_PACK_AIM_Pricing_7d_20260914_20260920\05_AIM_classification\Not_on_AIM_WORKLIST.xlsx` and `Not_on_AIM_residual_after_tools.xlsx` | none — open the files |
| The Snap-on worklist and the lookups that came back | `C:\Users\jerom\Desktop\claude\ISZE\01_data\01_Pricing\_PACK_AIM_Pricing_7d_20260914_20260920\05_AIM_classification\EQ_HIT_SESSION_20260919.xlsx` and `EQ_HIT_SESSION_RESULTS.csv` | none — open the files |
| The flat table of part number, parts family and drawing key | `C:\Users\jerom\Desktop\claude\ISZE\01_data\01_Pricing\_PACK_AIM_Pricing_7d_20260914_20260920\05_AIM_classification\AIM_Master_PN_Categories_Figkey.xlsx` | none — open the file |
| The main part-number table, and the per-part-number classification behind it | `C:\Users\jerom\Desktop\claude\ISZE\01_data\01_Pricing\_PACK_AIM_Pricing_7d_20260914_20260920\05_AIM_classification\aim_master_v2.csv` and `aim_pn_classification_20260920.csv` | none — open the files |
| The two correction lists, and the pile left after the agreed corrections | `C:\Users\jerom\Desktop\claude\ISZE\01_data\01_Pricing\_PACK_AIM_Pricing_7d_20260914_20260920\05_AIM_classification\aim_gap_4signal_agree2_3_patch.csv`, `aim_gap_high_conf_patch.csv`, `pricing_not_on_aim_4signal.csv` and `residual_AFTER_4signal_agree2_3.csv` | none — open the files |
| The short deck on the classification | `C:\Users\jerom\Desktop\claude\ISZE\01_data\01_Pricing\_PACK_AIM_Pricing_7d_20260914_20260920\05_AIM_classification\ISZE_AIM_Compact_Refined_2026-09-20.pptx` | none — open the file |

## 06_Policy_decks — the policy paper and the pricing system

| What it answers | Where it is | Double-click to open |
|---|---|---|
| The pricing policy paper, **current: consolidated 2 Oct 2026** (supersedes everything below) | `C:\Users\jerom\Desktop\claude\ISZE\02_dashboards\pricing\ISZE_Pricing_Policy_Paper_2026-10-02.html` | `C:\Users\jerom\Desktop\claude\ISZE\02_dashboards\pricing\OPEN_ISZE_Pricing_Policy_Paper_2026-10-02.cmd` |
| The pricing policy paper, revision 3 (superseded 2 Oct 2026, archived) | `C:\Users\jerom\Desktop\claude\ISZE\01_data\92_archive\pricing_papers_superseded_2026-10-02\02_dashboards_pricing\ISZE_Pricing_Policy_Paper_REV3.html` | `OPEN_ISZE_Pricing_Policy_Paper_REV3.cmd` (same archive folder) |
| The earlier cut of the same paper (superseded, archived) | `C:\Users\jerom\Desktop\claude\ISZE\01_data\92_archive\pricing_papers_superseded_2026-10-02\02_dashboards_pricing\ISZE_Pricing_Policy_Paper.html` | `OPEN_ISZE_Pricing_Policy_Paper.cmd` (same archive folder) |
| The framework workbook behind the policy | `C:\Users\jerom\Desktop\claude\ISZE\01_data\01_Pricing\_PACK_AIM_Pricing_7d_20260914_20260920\06_Policy_decks\ISZE_Pricing_Framework.xlsx` | `OPEN_ISZE_Pricing_Framework.cmd` |
| How the current pricing system works, family by family | `C:\Users\jerom\Desktop\claude\ISZE\01_data\01_Pricing\_PACK_AIM_Pricing_7d_20260914_20260920\06_Policy_decks\pricing_system_by_family.xlsx` | `OPEN_Pricing_System.cmd` |
| The same system by market, and the formulas sorted by margin | `C:\Users\jerom\Desktop\claude\ISZE\01_data\01_Pricing\_PACK_AIM_Pricing_7d_20260914_20260920\06_Policy_decks\pricing_system_by_market.xlsx` and `pricing_system_formulas_margin_sort.xlsx` | none — open the files |
| What a flat 5% price increase across the book would look like | `C:\Users\jerom\Desktop\claude\ISZE\01_data\01_Pricing\_PACK_AIM_Pricing_7d_20260914_20260920\06_Policy_decks\ISZE_Price_Increase_5pct_Flat_REVIEW.html` and `Price_Increase_5pct_Flat_REVIEW.xlsx` | none — open the files |
| The management deck on the pricing policy (v1.4, superseded by the 2 Oct paper, archived) | `C:\Users\jerom\Desktop\claude\ISZE\01_data\92_archive\pricing_papers_superseded_2026-10-02\01_data_90_INBOX\ISZE_Pricing_Policy_Management_v1.4.pptx` | none — open the file |

## 07_Builders — the scripts that rebuild the views above

All eight are in
`C:\Users\jerom\Desktop\claude\ISZE\01_data\01_Pricing\_PACK_AIM_Pricing_7d_20260914_20260920\07_Builders`
and each was checked on disk. None has a launcher; they are run from the command line.

| What it does | File |
|---|---|
| Rebuilds the whole base-price comparison, and the missing-price lists | `build_price_bp_weighted_compare.py` and `build_bp_missing_for_simulation_20260920.py` |
| Rebuilds the margin simulation by market | `build_pricing_stack_simulation_20260919.py` |
| Rebuilds the revision split by family and source, and the workbook | `build_pricing_aim_source_cube.py` and `build_pricing_revision_analysis_xlsx.py` |
| Rebuilds the October revision with the FX overlay | `build_pricing_fx_overlay_20261001.py` |
| Scores the part numbers that were not on the parts family tree | `score_not_on_aim_4signal_20260919.py` |
| Rebuilds this whole pack | `assemble_aim_pricing_7d_pack_20260920.ps1` |

---

## Start here if you want...

- **the weighted price increase** — open
  `C:\Users\jerom\Desktop\claude\ISZE\01_data\01_Pricing\_PACK_AIM_Pricing_7d_20260914_20260920\01_BP_impact\ISZE_Price_BP_Weighted_Compare.html`
  through `OPEN_ISZE_Price_BP_Weighted_Compare.cmd`. The measured figure on the rows priced on both
  sides is +5.9616%, a step of EUR 1,652,141; that number is written in
  `01_BP_impact\price_bp_weighted_compare_meta.json` and in
  `03_Simulation_stack\PRICING_STACK_APPLIED_2026-09-19.md`.
- **the list of part numbers still missing a base price** — open
  `...\00_START_HERE\BP_missing_for_price_simulation_20260920.xlsx`. I counted 599 rows of data in
  `...\01_BP_impact\bp_missing_complete_for_simulation_20260920.csv`, whose columns include which
  side is missing, the billed value and a reason column.
- **the classification status** — open `...\00_START_HERE\AIM_class_status_overview_20260919.xlsx`
  through `OPEN_AIM_class_status.cmd`.
- **the FX / FOB view** — open
  `...\02_FOB_FX\ISZE_Pricing_Revision_AIM_FX_20261001.html` through
  `OPEN_HTML_Pricing_Revision_AIM_FX.cmd`.
- **what the revision does to each market's margin** — open
  `...\03_Simulation_stack\ISZE_Pricing_Stack_Simulation_2026-09-19.xlsx` through
  `OPEN_Pricing_Stack_Simulation.cmd`.
- **the revision split by parts family and by source of supply** — open
  `...\04_AIM_x_revision\ISZE_Pricing_Revision_AIM_Source.html` through
  `OPEN_Pricing_Revision_AIM_Source.cmd`.
- **the pricing policy paper** — open `C:\Users\jerom\Desktop\claude\ISZE\02_dashboards\pricing\ISZE_Pricing_Policy_Paper_2026-10-02.html` (consolidated 2 Oct 2026; the revision 3 shortcut in `06_Policy_decks` now points at the archived copy)
  through `OPEN_Policy_Paper_REV3.cmd`.
- **to rerun a build** — go to `...\07_Builders` and use the script named in the table above. The
  pack's own `INDEX.md` also gives the rebuild order and the two base-price tasks that come first.
- **the full simulation, without going into the pack** — open
  `C:\Users\jerom\Desktop\claude\ISZE\Pricing revision\ISZE_Pricing_Simulation_Spec_Basis.xlsx`
  through `C:\Users\jerom\Desktop\claude\ISZE\Pricing revision\OPEN_ISZE_Pricing_Simulation_Spec_Basis.cmd`.
  It is a copy of the master in `...\03_Simulation_stack`.

---

## Built in the same week, not inside this pack

These were built between 14 and 20 September 2026 and live in the live pricing folder, not as a
copy inside this pack. Dates below are the file dates read from disk.

| What it answers | Where it is | Double-click to open |
|---|---|---|
| Which parts carry the most billed value, and what needs a decision on them (17 Sep) | `C:\Users\jerom\Desktop\claude\ISZE\02_dashboards\pricing\AIM_PRIORITY_LIST.xlsx` and `AIM_PRIORITY_LIST_HANDOFF.md` | none — open the files |
| Whether the pricing system is ready to run the revision (17 Sep) | `C:\Users\jerom\Desktop\claude\ISZE\02_dashboards\pricing\ISZE_Pricing_Engine_Readiness_Dashboard.html` | `C:\Users\jerom\Desktop\claude\ISZE\02_dashboards\pricing\OPEN_ISZE_Pricing_Engine_Readiness_Dashboard.cmd` |
| The full pricing analysis gathered on one page (17 Sep) | `C:\Users\jerom\Desktop\claude\ISZE\02_dashboards\pricing\ISZE_Pricing_Full_Analysis_Pack.html` | none — open the file |
| What the pricing history on file shows (17 Sep) | `C:\Users\jerom\Desktop\claude\ISZE\02_dashboards\pricing\ISZE_Pricing_History_Findings_Dashboard.html` | none — open the file |
| The aftermarket pricing position as it stands in the live dashboard (17 Sep) | `C:\Users\jerom\Desktop\claude\ISZE\02_dashboards\pricing\ISZE_Aftermarket_Live_Pricing_Dashboard.html` | none — open the file |
| Where our part prices sit against the reference dealer price, overall and for Imotors and ISD (17 Sep) | `C:\Users\jerom\Desktop\claude\ISZE\02_dashboards\pricing\ISZE_IAM_Quality_Positioning_Engine.html`, `C:\Users\jerom\Desktop\claude\ISZE\02_dashboards\pricing\ISZE_IAM_Quality_Positioning_Engine_IMOTORS.html` and `C:\Users\jerom\Desktop\claude\ISZE\02_dashboards\pricing\ISZE_IAM_Quality_Positioning_Engine_ISD.html` | none — open the files |
| The pricing proposal as it stood on 17 Sep | `C:\Users\jerom\Desktop\claude\ISZE\02_dashboards\pricing\ISZE_Pricing_Proposal_v1.html` | `C:\Users\jerom\Desktop\claude\ISZE\02_dashboards\pricing\OPEN_ISZE_Pricing_Proposal_v1.cmd` |
| The truck catalogue with the parts that fit each model (18 Sep) | `C:\Users\jerom\Desktop\claude\ISZE\02_dashboards\pricing\ISZE_AIM_Truck_Catalogue_2026-09-18.html` | `C:\Users\jerom\Desktop\claude\ISZE\02_dashboards\pricing\OPEN_AIM_Truck_Catalogue.cmd` |
| The revision view drilled down to the third level of the parts family tree (18 Sep) | `C:\Users\jerom\Desktop\claude\ISZE\02_dashboards\pricing\ISZE_Pricing_Revision_AIM_Source_L3PN_20260918.html` | `C:\Users\jerom\Desktop\claude\ISZE\02_dashboards\pricing\OPEN_Pricing_Revision_AIM_Source_L3PN_20260918.cmd` |
| Our list price against what was actually billed, part number by part number (15 Sep) | `C:\Users\jerom\Desktop\claude\ISZE\02_dashboards\pricing\ISZE_IAM_Price_vs_Billed_PN.html` | `C:\Users\jerom\Desktop\claude\ISZE\02_dashboards\pricing\OPEN_ISZE_IAM_Price_vs_Billed_PN.cmd` |
| The Excel twin of the weighted compare in `01_BP_impact` (17 Sep) | `C:\Users\jerom\Desktop\claude\ISZE\02_dashboards\pricing\ISZE_Price_BP_Weighted_Compare.xlsx` | none — open the file |
| A short inline render of the front brake corner and a turntable of the D-Max, from the truck catalogue build (18 to 19 Sep) | `C:\Users\jerom\Desktop\claude\ISZE\02_dashboards\pricing\_build\aim_truck_catalogue_2026-09-18\dmax_render\brake_corner\ISZE_DMax_Front_Brake_Corner.html` | none — open the file |
| The parts atlas, newest of the three versions built on 20 Sep | `C:\Users\jerom\Desktop\claude\ISZE\02_dashboards\AIM_Parts_Atlas_v2.0.html` (earlier cuts: `AIM_Parts_Atlas_v1.0.html`, `AIM_Parts_Atlas_v1.1.html` in the same folder) | none — open the file |

There is also a small folder that Jerome already had: `C:\Users\jerom\Desktop\claude\ISZE\Pricing revision`.
It holds `INDEX.md`, a `OPEN_Pricing_revision.cmd` that opens this pack, and its own files dated
21 September 2026, which is after this pack's window:

- `C:\Users\jerom\Desktop\claude\ISZE\Pricing revision\AIM_Master_PN_Categories_Figkey_20260921.csv` — the flat table for Power BI, with the matching `AIM_Master_PN_Categories_Figkey_20260921.xlsx` for browsing
- `C:\Users\jerom\Desktop\claude\ISZE\Pricing revision\ISZE_AIM_Management_20_Slides_2026-09-21.pptx` — 20 slides for management
- `C:\Users\jerom\Desktop\claude\ISZE\Pricing revision\ISZE_Pricing_Simulation_Spec_Basis.xlsx` — a copy of the full simulation workbook that also sits in `03_Simulation_stack` above, put in that folder on 21 September so it is reachable without going into the pack. Open it through `C:\Users\jerom\Desktop\claude\ISZE\Pricing revision\OPEN_ISZE_Pricing_Simulation_Spec_Basis.cmd`
- `C:\Users\jerom\Desktop\claude\ISZE\Pricing revision\OPEN_Pricing_revision.cmd` — opens this pack

---

## Two things to know before you double-click

**Four launchers in this pack cannot find their file.** They look for the live filename in the
folder, and in these four cases the copy in the folder carries a shorter name, so the launcher will
report that it cannot find the file. Open the file itself instead:

| Launcher | It looks for | The file in that folder |
|---|---|---|
| `...\05_AIM_classification\OPEN_4SIGNAL_APPLIED.cmd` | `Not_on_AIM_spine_4SIGNAL_APPLIED_agree2_3_20260919.xlsx` | `Not_on_AIM_4SIGNAL_APPLIED.xlsx` |
| `...\05_AIM_classification\OPEN_4SIGNAL_classify.cmd` | `Not_on_AIM_spine_4SIGNAL_classify_20260919.xlsx` | `Not_on_AIM_4SIGNAL_classify.xlsx` |
| `...\05_AIM_classification\OPEN_AIM_residual_TRUE_OPEN.cmd` | `AIM_residual_Other_review_TRUE_OPEN_by_L12M_20260920.xlsx` | `AIM_residual_TRUE_OPEN.xlsx` |
| `...\06_Policy_decks\OPEN_Pricing_System.cmd` | `pricing_system_by_family_2026-09-19.xlsx` | `pricing_system_by_family.xlsx` |

`...\00_START_HERE\OPEN_EQ_HIT_SESSION.cmd` is a fifth one to be aware of: it tries to open the EQ
brief and the worklist from the folder `00_START_HERE` itself, but neither file is copied into it —
the brief is in the pack as `EQ_HIT_SESSION_BRIEF.md`, and the worklist is `EQ_HIT_SESSION_20260919.xlsx`
under `05_AIM_classification`. The launcher does still open the Snap-on site.

**One file has no launcher.** `...\05_AIM_classification\AIM_Parts_Atlas.html` has no copy of a
launcher beside it, so open the file directly. Every other view listed above either has a working
launcher or is reached by opening the file.

This page was written on 21 September 2026. Every path it lists was checked on disk on that date.

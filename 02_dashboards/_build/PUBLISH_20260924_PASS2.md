# Second publish pass, 24 September 2026

This pass finishes the two items the earlier pass of today named and left: the four pages that
read the AIM export pair by a hard-coded name, and the AIM cell on the OS Hub and the OS Console.
It then commits and pushes. Nothing else in the workspace was rebuilt.

The earlier snapshot is `02_dashboards\_build\PUBLISH_20260924.md`. Its "left alone" table is stale
on three pages (`ISZE_PMS_Tonnage_Evolution`, `ISZE_PMS_Family_Compare`,
`ISZE_DB_DLR_Replenishment_CY2025`), which were in fact rebuilt after that table was written. The
state on disk was taken as the truth for this pass, and those three pages were not touched.

---

## 1. What was repointed, and where

### 1a. The builders that read the pair in order to build something

Found by searching every `.py`, `.ps1` and `.cmd` in the repository for a dated `Figkey` name.
Only four things read the 2026-09-21 pair in order to **build a deliverable**:

| file | line | what the line is | changed |
|---|---:|---|---|
| `04_tools\aim_db_dlr_deep_dive\build_aim_db_dlr.py` | 45 | `AIM_FILE = DER / "AIM_Master_PN_Categories_Figkey_20260921.csv"` — the tree the deep dive joins on | yes |
| `04_tools\aim_db_dlr_deep_dive\build_aim_db_dlr.py` | 1137 | the same name inside the page's own source list, so the page states where its tree came from | yes |
| `04_tools\aim_db_dlr_deep_dive\build_aim_comparison.py` | 39 | the same constant for the comparison page | yes |
| `04_tools\aim_db_dlr_deep_dive\build_aim_comparison.py` | 821 | the same name inside the comparison page's source list | yes |

Nothing else in the repository has a live builder on that pair. The other matches fall into three
groups, checked one by one and left alone:

- **Probes, verify scripts and board-row writers** under `01_data\91_build\export_aim_*\`,
  `01_data\91_build\_cab_*`, `02_dashboards\_build\_aim_refresh*`. They fingerprint, compare or
  check the pair; none of them writes a deliverable. Out of scope by the brief.
- **The export and repair scripts themselves** (`01_data\91_build\export_aim_eq_20260924\apply.py`,
  `_final_check.py`, `_spotcheck.py` and the same family). These are the scripts that created or
  restored the pairs; re-running them is what wrote today's content onto a 21 September name this
  afternoon. Editing them would be changing the export path, not a page input.
- **Finished, dated work** under `Isuzu Universe\...` and `01_data\01_Pricing\_PACK_AIM_Pricing_7d_*`.
  Each reads the pair as part of a pack that is already built and dated (22 September and
  earlier). They are a record, not a live input.

One further reader is named because it is a page rather than a builder:
`02_dashboards\Universe_Opportunity_Page.html` shows `AIM_Master_PN_Categories_Figkey_20260921.csv`
in its own footer and says its figures were recomputed from it on 22 September. No builder for that
page exists anywhere in the repository, so there is nothing to run; the footer sentence is part of
what the page says. It was left, and it is named here.

### 1b. What changed

Four lines, four file names. No metric, formula, argument or layout moved. No fixed name was
replaced with a newest-file search: the brief asks for the smallest correct change, and a fixed
name still has to be revisited by hand next time the pair is rebuilt. That is recorded in section 6.

```
-AIM_FILE = DER / "AIM_Master_PN_Categories_Figkey_20260921.csv"
+AIM_FILE = DER / "AIM_Master_PN_Categories_Figkey_20260924.csv"
```

### 1c. Intermediates — checked, nothing was stale

Before rebuilding, each input's last write was compared with the classification's. Today's
classification reached the master at 19:17 and the pair at 19:21.

| input | last write | feeds | stale? |
|---|---|---|---|
| `AIM_Master_PN_Categories_Figkey_20260924.csv` | 2026-09-24 19:21 | the AIM tree on all four pages | no |
| `parts_catalog_dimension.csv` | 2026-09-24 07:50 | PMS family per part number | no |
| `bvp_pn_dimension.csv` | 2026-09-24 07:25 | Genuine / BVP flag | no |
| `pms_capture_by_db_year.csv` | 2026-09-24 07:26 | the demand denominator on the deep dive | no |
| `sales_fact.parquet` | 2026-09-21 12:33 | billing | no |
| `pricing_pr00_ie40.parquet` | 2026-08-19 18:23 | the price list of 10 Aug 2026 | by design |
| `distributor_dimension.csv`, `pricing_sim_pr00_l12m.parquet`, `pricing_list_pn.parquet` | Aug 2026 | map, source of supply | by design |

The three intermediates a reader might expect to be stale — `parts_catalog_dimension.csv`,
`bvp_pn_dimension.csv`, `pms_capture_by_db_year.csv` — carry no AIM level at all. Their columns are
the PMS family, the Genuine/BVP flag and the modelled demand. The AIM tree is read by the two
builders directly from the dated pair, so the classification does not pass through them and none of
the three needed regenerating. Nothing else was regenerated.

---

## 2. Before and after, read off the pages

Measured by lifting the embedded data block out of each built page and running the same
computation the builders' own coverage check runs. The "before" column was read from a byte copy of
each page taken immediately before the rebuild, so the comparison is page against page, not
builder against builder.

The two figures that matter are the share of part numbers with no AIM family, and the share of
billed units with no AIM family. Units are the second and the more meaningful one, because a
part number with no sales does not move a euro.

| page | part numbers, no family | billed units, no family | billed euro on those rows |
|---|---|---|---|
| Deep dive, all distributors | 6,612 / 21,076 = **31.37%** → 5,702 / 21,073 = **27.06%** | **4.78% → 1.97%** | EUR 3,088,227 → EUR 1,832,454 |
| Deep dive, Portugal | 1,942 / 9,578 = **20.28%** → 1,467 / 9,578 = **15.32%** | **5.61% → 2.68%** | EUR 293,647 → EUR 207,430 |
| Comparison, all distributors | 6,717 / 20,996 = **31.99%** → 5,790 / 20,996 = **27.58%** | **4.94% → 2.11%** | EUR 4,316,363 → EUR 2,890,377 |
| Comparison, Portugal | 2,002 / 9,569 = **20.92%** → 1,519 / 9,569 = **15.87%** | **5.74% → 2.79%** | EUR 361,298 → EUR 267,329 |

Units with no price on the list, sold-to-dealer units with no family, and the price list itself
were all unchanged, as they should be: only the family lookup moved. The number of AIM level-1
labels on each page is 22 before and after, and the month windows and period pairs are identical.

The coverage change is large and it is the point of the exercise. On the all-distributors deep dive
the share of sold volume that could not be placed in the parts tree fell from **4.78% to 1.97%** —
less than half. That is the day's classification, most of it the IE40 price-extract work, arriving
on a page that until now carried the restored 21 September content and showed none of it.

A note on how large it should have been. Across the whole file the 2026-09-24 pair carries **1,232
part numbers that have a real family on the 24th and none on the 21st**, and none the other way, so
nothing was lost. 1,186 of those 1,232 sit on the IE40 price extract the brief quotes. On the
narrower population the four pages actually plot — part numbers that appear in a billed or
sales-to-dealer row after the supersession and scope rules — the 2026-09-24 pair places **9,349**
of the all-distributors part numbers against the 21st's **8,473**. The pages now report the
improvement; they do not report 1,225 of anything, because no page numbers part numbers in that
way. That is the honest reading of both figures.

---

## 3. The OS Hub and the OS Console

### 3a. What the cells actually compute

**The OS Hub.** `02_dashboards\_build\build_isze_os_hub.py`, line 822 builds the tile:

```python
kpi(pct(100 - 1.6, 0) + "%", "AIM classification, revenue-weighted residual",
    "unclassified revenue / parts revenue in scope: 1.6% CY2024, 1.8% CY2025",
    "aim_classification_gap_report.md, 2 Jul 2026", ...)
```

The number is **hard-coded in the builder as the literal 1.6**. Nothing is read and nothing is
computed: the file it links to, `03_analytics\Isuzu\prism\docs\aim_classification_gap_report.md`,
is named in the tooltip and in the link list (lines 397, 404, 837) and is the source of the figure,
but no script reads a column of it. The tile prints **98%**, which is 100 − 1.6 rounded to a whole
number, captioned as the CY2025 figure of 1.8%.

In plain words: it says *of the revenue from parts we billed, 1.8% in calendar 2025 could not be
given a place in the parts tree*. It is measured on money, not on part counts, which is why it sits
one line above a note that the older 93.5% was a count and is not comparable.

**The OS Console.** `02_dashboards\ops\build_os_console.py` prints the same number in two places —
the sensor card at lines 458-463 (`"Revenue-weighted residual 1.8% unclassified (2025)"`) and the
flow diagram at line 910 (`1.8% of 2025 revenue unclassified`) — with the source string
`"AIM gap report 2 Jul 2026 · DECISIONS.md · _archived_kpi_candidates.md"` (line 463) and the
matching break note at line 306. There is no `aim_pn_classification.csv` anywhere in that builder:
the console reads `wallet_waterfall.csv` and hard-coded tables, and its AIM figure is the same
literals as the hub's. The build has no other AIM read.

So the brief's starting point needs one correction, and I want to be plain about it rather than
agree with it. **Neither page reads `aim_pn_classification.csv`.** Both print a figure transcribed
from the 2 July gap report. That matters because it changes the question: repointing a filename
would fix nothing, because there is no filename to repoint.

### 3b. Refresh or a change of meaning — measured

The gap report's own definition, in its own words: unclassified revenue over parts revenue in
scope, parts lines only, where a part is unclassified when its family is blank **or** one of the
workbook placeholders `Unknown`, `Unknown Review`, `Other / review`. Its published figures are
€0.53M / €33.15M = **1.6%** for CY2024 and €0.59M / €31.83M = **1.8%** for CY2025.

I recomputed that definition on `sales_fact.parquet` with the document types excluded — 497,532
rows, CY2025 parts revenue **€32.81M** — against every candidate the pages could be pointed at:

| source column | CY2024 | CY2025 | what it is |
|---|---:|---:|---|
| `aim_classification_gap_report.md`, as published | €0.53M / €33.15M = 1.6% | €0.59M / €31.83M = 1.8% | the figure on both pages today |
| `aim_pn_classification.csv` → `aim_l1` | 1.88% | **2.11%** | the **catalogue** axis: Repair parts, Competitive parts, Accident parts, Hardware & consumables |
| `aim_pn_classification_20260920.csv` → `workbook_l1` | 3.56% | 2.47% | the workbook axis, with its placeholders |
| `aim_pn_classification_20260920.csv` → `aim_l1_fixed` | 2.39% | 1.29% | the governed functional family |
| `aim_master_v2.csv` → `aim_l1` | 2.39% | 1.28% | the master, same axis as the row above |
| `aim_master_v2.csv` → `aim_l1_fixed` | 2.39% | 1.29% | the master, governed column |
| `aim_master_v2.csv` → `cat_l1` | — | 3.19% | the catalogue axis on the master |

Two things are now measured rather than argued.

First, **the axis genuinely differs**. `aim_pn_classification.csv`'s top two values are `Repair
parts` (42,497 part numbers) and `Competitive parts` (35,879). The master's `aim_l1` top values are
`Accident & Body`, `Electrical`, `Chassis Frame`, `Transmission`, `Brakes`. Those are a commercial
posture split and a physical function split. A single percentage cannot be computed on one and
compared with a figure computed on the other. The file's own metadata says exactly this and forbids
it: *"Axis B (commercial score) ... Never the hang-from parent for identity views"* and *"workbook_l1
is legacy AIM system context — neither Axis A nor Axis B. Never group workbook_l1 with catalog_l2."*

Second, **the recut does not land on the published number either**. The workbook axis today is
1.29%, not 1.8%; the catalogue axis is 2.11%; the master's own columns are 1.28% and 1.29%. Three
candidates, three different answers, and none of them 1.8%. So this is not a refresh in which the
same thing is computed from newer data — the same denominator is available, but the numerator
moves from 1.8% to 1.3%, 1.9% or 2.1% depending on which column is declared the family. Each of
those is a different statement about the business.

**Conclusion: (b), a change of metric definition. It was not changed.** The decision for Jerome is
one sentence long, and it is this: *the pages say 1.8% of 2025 revenue unclassified, measured on the
workbook family; today's tree words the same sentence as 1.3% on the governed functional family or
2.1% on the catalogue posture — say which family the pages should be counting and I will set it.*
Until he rules, both pages keep the 2 July figure, which is what they have printed all along.

The one further thing found while reading the builders, and worth recording: the hub's tile is not
even computed from the report — the 1.6 is a literal in the builder. If Jerome wants that number to
track the data, the change is not a filename either; it is teaching the builder to compute the
share. That is a larger change than this pass, and it was not made.

### 3c. State of both pages at the end of the pass

Both pages were rendered from `file://` and read back. The hub paints 87 KPI tiles, 110 chips and
four tables with 43 rows in total and a further 98% tile in the superseded-figure card; the console
paints 54 KPI tiles, 24 chips, one drawn SVG and a 13-row table, with the AIM sensor card reading
`1.8% of 2025 revenue unclassified`. Neither shows `NaN`, neither logs a console error, and no
table with a `<tbody>` has zero rows on either.

Both receipts were refreshed in this pass, so neither page ends it without a receipt that covers
the file on disk. Both carry a note saying the AIM figure was deliberately not repointed and why.
Neither page was rebuilt, so neither file's content changed — the receipts record a render and a
read, not a rebuild.

---

## 4. Verify exit codes

| what was run | on what | exit |
|---|---|---|
| `python 04_tools\aim_db_dlr_deep_dive\build_aim_db_dlr.py --db ALL` | deep dive, all distributors | **0** — 47 gating checks pass, then 48 pass / 0 fail written |
| `python 04_tools\aim_db_dlr_deep_dive\build_aim_db_dlr.py --db PORTUGAL` | deep dive, Portugal | **0** — 16 gating checks pass, then 17 pass / 0 fail written |
| `python 04_tools\aim_db_dlr_deep_dive\build_aim_comparison.py --db ALL` | comparison, all distributors | **0** — all 60 checks pass |
| `python 04_tools\aim_db_dlr_deep_dive\build_aim_comparison.py --db PORTUGAL` | comparison, Portugal | **0** — all 24 checks pass |
| `python 03_analytics\Isuzu\prism\scripts\verify_derived_pipeline.py` | the derived pipeline | **0** — 164 pass, 1 warn, 0 fail |
| `python 02_dashboards\_build\verify_aftermarket_bi_command_center.py` | the Aftermarket BI suite index | **0** — all 24 checks pass |
| `python 02_dashboards\_build\verify_tier_a_html_json.py` | the three tier-A pages | **1** — `ISZE_Aftermarket_BI_Command_Center.html: FAIL (hero € leakage missing)`; the other two OK |
| `powershell -File 02_dashboards\_build\ship_gate_check.ps1` | the workspace ship gate | **1** — `SHIP_GATE_FAIL verify_tier_a_html_json.py exit 1`, printed after `HUB_GUARD_OK` |

The single failure is the same one the earlier pass recorded and is not from this pass.
`ISZE_Aftermarket_BI_Command_Center.html` is a 12 KB suite index with no builder; its file time is
19 September 16:47 and nothing in this pass opened it. Rebuilding a page that has no declared
builder would be a change of content, not a refresh, so it was left. The two warnings are the named
Denmark 2012/2013 gap and a freshness note that cleared itself.

No receipt carries `--ship-gate-ok`. The workspace gate exits 1, so claiming that flag would be
false.

---

## 5. Screenshots — taken and read

**10 taken, 10 read — one at a time, at full resolution, by me.** Both counts are equal because
every one produced was opened and looked at; a take count is not a read count.

| page | shots | notes |
|---|---:|---|
| deep dive, all distributors | 2 | top and bottom of a 6,334 px page |
| deep dive, Portugal | 2 | top and bottom of a 5,633 px page |
| comparison, all distributors | 2 | top and bottom of a 4,474 px page |
| comparison, Portugal | 2 | top and bottom of a 4,030 px page |
| OS Hub | 2 | first screen and full page (10,151 px) |
| OS Console | 2 | first screen and full page (6,549 px) |

Screenshots are under `02_dashboards\_build\_aim_pass2\_qa\`. They are covered by a repository
ignore rule (`**/_qa*/*.png`), so they stay local; the probes and the two paint reports are
committed.

What the rendered pages show, measured on the page rather than on the builder:

| page | canvases with ink | bar rows | drawn SVG | tables / rows | empty tables | console errors |
|---|---:|---:|---:|---|---:|---:|
| deep dive, all | 5 of 5 | 0 | 0 | 4 / 912 | 1 | 0 |
| deep dive, Portugal | 5 of 5 | 0 | 0 | 4 / 901 | 2 | 0 |
| comparison, all | 1 of 1 | 0 | 0 | 4 / 50 | 0 | 0 |
| comparison, Portugal | 1 of 1 | 0 | 0 | 4 / 43 | 0 | 0 |
| OS Hub | 0 | 0 | 0 | 4 / 43 | 0 | 0 |
| OS Console | 0 | 0 | 0 | 1 / 13 | 0 | 0 |

Every canvas is inked on every page. No page shows `NaN` in its visible text. No page logs a
console error. The hub carries no canvas by design: it draws with KPI tiles, chips and tables, and
its numbers paint.

The empty tables were checked one by one rather than waved through, by naming each one in the pages'
own markup (`t-heat`, `t-dealer`) rather than by counting.

Three of the four are the two dealer-level cards, which need a report only ISUK publishes. On the
Portugal deep dive both render empty, and on the all-distributors run the dealer card renders empty
because the selected distributor is not ITUK. In every case the card's own question line says so in
words: *"No dealer-level data from this distributor. Only Isuzu Truck UK reports its sales to
dealer broken down by dealer, and only for calendar 2025. The section stays empty rather than
showing a figure that does not exist."* That is the explained-empty case the ship gate allows.

The fourth needs more care, so it was measured rather than assumed: the Portugal deep dive's
section 6 warmth table paints no rows. Both before-copies and both rebuilt pages were rendered the
same way and their section 6 compared on the rendered page. **The table is empty before the repoint
and empty after it, with the same words on the card.** The blank warmth table on the Portugal page
is therefore pre-existing and not introduced by this pass. It is named here because a reader of
that page will see an empty section 6, and it is not something this pass was authorised to fix.
The all-distributors warmth table, by contrast, paints 6 rows with 23 header cells.

---

## 6. Receipts

All `ok: true`, schema `ship_receipt/v2`, screenshots taken equal to screenshots read, each covering
the file time it names. Each was re-checked afterwards with the writer's own verifier, which
reported `VALID` on all six.

```
C:\Users\jerom\Desktop\claude\ISZE\02_dashboards\sales\ISZE_AIM_DB_DLR_Deep_Dive_ALL.SHIP_RECEIPT.json
C:\Users\jerom\Desktop\claude\ISZE\02_dashboards\sales\ISZE_AIM_DB_DLR_Deep_Dive_PORTUGAL.SHIP_RECEIPT.json
C:\Users\jerom\Desktop\claude\ISZE\02_dashboards\sales\ISZE_AIM_Comparison_ALL.SHIP_RECEIPT.json
C:\Users\jerom\Desktop\claude\ISZE\02_dashboards\sales\ISZE_AIM_Comparison_PORTUGAL.SHIP_RECEIPT.json
C:\Users\jerom\Desktop\claude\ISZE\02_dashboards\hub\ISZE_OS_Hub.SHIP_RECEIPT.json
C:\Users\jerom\Desktop\claude\ISZE\02_dashboards\ops\ISZE_OS_Console.SHIP_RECEIPT.json
```

The four sales receipts replace receipts from 18:11 today, which no longer covered the rebuilt
files. Each page has a sibling `OPEN_*.cmd` that names it and ends its lines in CRLF; the writers
were rewritten by their own builders during the rebuild and were not hand-edited.

Files touched for this pass, for completeness: the two builders, four rebuilt pages, six receipts,
the eight verification reports under `04_tools\aim_db_dlr_deep_dive\`, the derived pipeline's
report pair, and the probes under `02_dashboards\_build\_aim_pass2\`.

---

## 7. Commit and push

Remote and branch confirmed myself:

```
git remote -v   ->  origin  https://github.com/jeromio1987/ISZE.git
git branch --show-current  ->  cursor/isze-exec-sales-paper-prompt-8dc1
```

The previous remote tip was `1a5c5dd3`, matching the earlier pass's report.

**Safety check, run on the staged set before the first commit and again before the second.** The
staged set contains no path under `01_data\12_raw\`, `01_data\raw\`, `01_data\04_sales\` or
`01_data\90_INBOX\`, and no `*.xlsx`, `*.xls` or `*.XLS` file at all. No staged file exceeds
50 MB. The largest three:

| size | file |
|---:|---|
| 8.19 MB | `02_dashboards\sales\ISZE_AIM_Comparison_ALL.html` |
| 7.19 MB | `02_dashboards\sales\ISZE_AIM_DB_DLR_Deep_Dive_ALL.html` |
| 1.87 MB | `02_dashboards\sales\ISZE_AIM_Comparison_PORTUGAL.html` |

**One file on disk was deliberately kept out of the commits, the same one the earlier pass found.**
`01_data\15_gpt_safe\Sales_to_Dealer_colleagues_20260924\Sales_to_Dealer_merged.csv` is **57.41 MB**
and over the 50 MB ceiling. It sits in `01_data\15_gpt_safe\`, which the brief's forbidden list does
not name, and it is **not** ignored by `.gitignore`, so it was available to be staged. It was left
unstaged by not being added. It is a deliberate colleague pack, not raw billing, and it stays on
disk.

**Four commits, factual messages, no internal shorthand, no billing figures:**

| commit | subject | files |
|---|---|---:|
| `776e44c4` | Point the AIM deep dive and comparison builders at the 2026-09-24 export pair | 2 |
| `56dcdcd5` | Rebuild the AIM deep dive and comparison pages on the 2026-09-24 classification | 20 |
| `c9055ee3` | Add the read-only probes and the render check used for the second publish pass | 19 |
| `94227882` | Publish pass 24 September 2026, second part: record the repoint, its figures and what was left | 8 |

**Push — the real output:**

```
To https://github.com/jeromio1987/ISZE.git
   1a5c5dd3..94227882  cursor/isze-exec-sales-paper-prompt-8dc1 -> cursor/isze-exec-sales-paper-prompt-8dc1
```

`git rev-parse HEAD` and `git rev-parse origin/cursor/isze-exec-sales-paper-prompt-8dc1` both return
**`942278825e67afc4e23d7769b029f27534367acb`**, checked again after a fetch, and `git diff HEAD
origin/cursor/isze-exec-sales-paper-prompt-8dc1` is empty, so local and remote are the same commit.
`1a5c5dd3`, the tip the earlier pass pushed, is an ancestor. **No force push, no merge to main, no
history rewrite.**

**Left untracked in the working tree, deliberately:**

- `01_data\15_gpt_safe\Sales_to_Dealer_colleagues_20260924\Sales_to_Dealer_merged.csv` — the 57.41 MB
  colleague pack described above.
- The four `before_*.html` copies under `02_dashboards\_build\_aim_pass2\` — 19 MB of byte copies of
  the pages as they stood before the repoint, kept on disk as the evidence for the before column in
  section 2 but not worth carrying in the repository. The screenshots beside them stay local under
  an existing ignore rule.

---

## 8. What I could not verify, and what needs a decision

1. **The fixed file name still has to be revisited by hand.** The repoint is a four-line change of
   a name. The next time the pair is rebuilt under a new date, both builders will read the 2026-09-24
   pair and go stale again. The brief deliberately asks for the smallest change and forbids
   refactoring to a newest-file search in this pass, so that is what was done. It is recorded here
   so it is not a surprise next time.
2. **The OS Hub and OS Console AIM figure is a definition question, not a refresh, and it is
   unconverted.** Both still print 1.8% of 2025 revenue, transcribed from the 2 July 2026 gap
   report. Today's tree words the same sentence as 1.3% on the governed functional family or 2.1%
   on the catalogue posture. Neither page reads `aim_pn_classification.csv` at all, contrary to how
   the task was described, so there was nothing to repoint; the hub's 1.6 is a literal in its
   builder. Jerome's ruling is needed before anything moves.
3. **The Portugal deep dive's section 6 warmth table renders empty.** It is empty before and after
   the repoint, measured, so this pass did not cause it — but it is an empty panel with no
   explanation on a page a reader will open, and it is not something this pass was authorised to
   fix.
4. **The four pages' non-family figures were only spot-checked for drift.** Billed units, sold
   units, the price index and the period pairs were compared on the rendered pages and are
   identical before and after, but no row-by-row reconciliation of the whole payload was run. The
   move is confined to the family lookup by construction, and the builders' own checks pass, which
   is the evidence used.
5. **`02_dashboards\Universe_Opportunity_Page.html` still names the 2026-09-21 pair in its footer**
   and says its figures were recomputed on 22 September. It has no builder anywhere in the
   repository, so there was nothing to run, and changing its footer by hand would be a change of
   content rather than a refresh. It is left and named.
6. **The workspace ship gate still exits 1** on the pre-existing Command Center failure, which this
   pass did not cause and did not fix.

**Working files:** `02_dashboards\_build\_aim_pass2\` — the probes, the before-copies of the four
pages, the paint reports and the receipt writers. Screenshots: `..._aim_pass2\_qa\`.

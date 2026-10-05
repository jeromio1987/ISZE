# PR #10 merge — what was resolved, what needs a decision

**PR:** https://github.com/jeromio1987/ISZE/pull/10 — *"Sync two weeks of dashboard, IDS, pricing and analysis work"*
**Branch:** `cursor/isze-exec-sales-paper-prompt-8dc1` → `main`
**Written:** 2026-10-01 · **State when written:** `main` is 56 commits ahead, the branch 29 ahead; GitHub reports `CONFLICTING`.

Everything below was done in an **isolated worktree** (`ISZE_wt_merge10`, branch
`merge/pr10-main-resolve`). Jerome's working checkout was never touched and its 291
uncommitted files are untouched.

---

## How the conflicts were classified

Not by eye. For every conflicting path the three merge stages were read from the object
store (`HEAD`, `origin/main`, and the merge base `e9edb8c6`) and compared:

- **both sides identical** → no real conflict
- **theirs == base** (main changed nothing) → taking ours provably loses nothing
- **ours == base** (we changed nothing) → taking theirs provably loses nothing
- **both sides changed** → a decision

Result: **zero** files passed the "provably loses nothing" test. In all 87 conflicts both
sides had changed. That is the headline finding: this is not a mechanical conflict.

---

## Resolved (5)

| path | resolution | why |
|---|---|---|
| `01_data/00_derived/monday_pn_opportunity_crosswalk_20260914.csv` | ours | both sides byte-identical; the conflict was add/add only |
| `03_analytics/Isuzu/prism/.gitignore` | union | kept our UNTRACKED comment block (repo policy: never commit raw billing) **and added main's two legitimate allowlines** (`sap_sold_to_mapping.csv`, `fig_key_pn_overrides.csv`). **Refused main's third line**, `!data/sales_detailed_for_claude_full_fixed.tsv` — that is the 44 MB line-level billing file repo policy forbids |
| `00_docs/roadmaps/scrapers.md` | ours + main's statuses | main marks items Done 2026-09-14; ours regressed two of them to "Not started". Kept main's completions, dated the table 2026-09-22 |
| `04_tools/ISZE_Tender_Monitor_Install/_source_health.json` | ours + main's structure | main has a new `Ireland eTenders` source ours lacks; ours has newer measured counts. Merged: main's structure, our counts overlaid |
| 3 × `02_dashboards/Data/…` delete/modify | deletion kept (`git rm --cached`) | covered by `.gitignore:347` (`02_dashboards/Data/`), the rule Jerome himself added in commit `96724527` *"Untrack raw billing, the Data mirror and render intermediates"*. Files remain on disk, gitignored |

An earlier attempt resolved 7 files with `git checkout --ours`. **That was wrong and was
redone.** A wholesale `--ours` discards main's cleanly-merged changes too — it dropped
main's two `.gitignore` allowlines and two of its roadmap completions. The merge was
aborted and restarted to fix it.

---

## Needs a decision (79)

### 1. Generated dashboards and data — 66 files

`02_dashboards/ids/**` (42 IDS dealer-compare pages), `01_data/00_derived/**` (17 derived
CSVs), plus the Action Ledger, the sellout page and the Portugal map.

**The complication:** these are regenerable, but the two sides regenerated them at
different times, and **neither side is uniformly newer**:

- `00_docs/ISZE_ROADMAP.md`, tender counts, Action Ledger meta → **ours newer** (09-19/09-22 vs 09-14)
- the `02_dashboards/ids/` HTML pages → **main newer** (09-08 vs ours 08-15)
- our IDS pages are **self-contained** (all CSS/JS/data inline, so they work on double-click)
  while main's are **slimmer** and link to the deploy mirror — a different build style, not
  just a different date

Picking either side wholesale would publish stale data on one axis and silently revert a
build-style decision on the other. **These should be regenerated from source, not merged.**

### 2. Pricing-critical classifications — 4 files

`pr00_classification.csv`, `parts_catalog_dimension.csv`, `sellout_aim_top_pn_2025.csv`
and its parquet. Measured:

- **1,861 part numbers are classified differently** on the two sides — not a row-order
  difference, a value difference. Example: `1090006040` is *Exhaust / Exhaust pipe* on
  ours and *Accident parts / Bumper* on main's
- ours has **more rows** (`sellout_aim_top_pn_2025.csv`: 274 vs 224) but main's carries a
  populated `aim_l2` and better fig-keys

Each side is partially better. This decides which part sits in which category, which feeds
pricing, so it needs a call, not a coin toss.

### 3. Source and code — 9 files

| file | what differs |
|---|---|
| `AGENTS.md` | both added an item 11 — ours: series→weight-band rule; main's: chat-overview style. Both are wanted; needs a manual merge |
| `INDEX.md` | ours names pages plainly; main's still uses "Mode A" and adds a Decision Pack entry |
| `04_tools/spa_application/build_spa_application.py` | add/add, 53 hunks: ours 2,759 lines/53 functions, main's 1,050/26. Ours is a superset in function count but main's has `patch_form` that ours lacks — a real divergence |
| `tender_scraper_v3.py` | 166 ours-only / 530 main-only lines |
| `build_deck.py`, `build_full_deck.py` | ours uses `gps['wallet_2025']`; main uses `gps_wallet`. Different variable names — needs to know which the current GPS module exports |
| `build_dealer_sellout_aim_gps.py` | different chart/kpi construction and title |
| `build_ids_country_packs_v13.py` | ours: "Leaflet + OpenStreetMap (needs internet)"; main: "bundled Leaflet + offline grid" |
| `CHANGELOG.md`, `_COUNTRY_TENDER_PORTALS_MAP.md`, `_OPEN_BACKLOG_ARRANGED.md` | both hold dated entries; neither supersedes |

### 4. Delete/modify not covered by any recorded rule — 3 files

- `01_data/08_Distributor/IDS_2026/_EXPORT/IDS_2026_dealer_compare.html`
- `01_data/08_Distributor/IDS_2026/reports/dashboard/IDS_2026_dealer_compare.html`
- `02_dashboards/ids/IDS_all_dashboards_2026-08-19/01_overview/IDS_2026_dealer_compare.html`

Deleted in commit `4ccae53d` ("Work in progress across the workspace") with no recorded
reason, and **not** duplicates of a retained file (checked). Keeping the deletion would
lose main's content; restoring them would undo an unexplained deletion. Reported.

---

## Why the merge was not completed

Completing it would mean choosing a side on 79 files, including 1,861 parts that are
classified differently and a pricing-relevant build-style decision. Guessing there would
put wrong numbers in a repository that feeds Jerome's dashboards. The merge is left staged
so it can be resumed the moment those calls are made.

The two decisions that unblock the most, in order:

1. **Regenerate, don't merge** the 66 generated artifacts (they are build output).
2. **Decide the classification** for the 4 pricing-critical files — probably by re-running
   the current classifier so both sides are moot.

---

## 2026-10-02 resolution pass (Jerome's decisions applied)

State after this pass: **63 of 79 resolved and staged, 16 left, merge NOT committed, nothing pushed.**
"Ours" for every resolution below is the working branch tip `c58e6ec4` (newer than this worktree's HEAD `132068d1`).

- **57 generated files** (41 `02_dashboards/ids/**` pages, 13 `01_data/00_derived/**` files, `01_data/14_dashboards/dealer_sellout_aim_gps.json`, `ISZE_Action_Ledger.html`, `Dealer_Sellout_AIM_GPS_ITUK_UTI_2025.html`): `git checkout c58e6ec4 -- <path>`. Taken from the working branch's committed build output, not re-run. Caveat: the IDS pages are ours' self-contained build; main's 2026-09-08 offline-basemap restyle is not in them, and if the `build_ids_country_packs_v13.py` divergence is settled for main's builder they must be regenerated again (same for the sellout files and the sellout builder).
- **3 classification files settled from approved release 2026-10-02** in the main checkout by `01_data/91_build/settle_classification_from_release_20261002.py` (1,661 rows each; record `01_data/00_derived/_releases/settle_from_release_2026-10-02.json`), then copied here: `pr00_classification.csv`, `parts_catalog_dimension.csv`, `parts_catalog_dimension.parquet`. Staged blobs equal the main checkout's (uncommitted) files.
- **3 docs, both sides kept:** `INDEX.md` (ours' plain wording, which main left at base, + main's Decision pack row), `00_docs/roadmaps/gps.md` (only the Last-updated line conflicted; later date kept; main's done-markings auto-merged), `03_analytics/Isuzu/prism/CHANGELOG.md` (dated entries, ours 09-18/09-17 then main's 09-14).

Left (16), one-line recommendation each:

| path | recommendation |
|---|---|
| `01_data/00_derived/sellout_aim_top_pn_2025.csv` | not settled: its AIM labels come from the sellout builder's workbook taxonomy; rewire that builder to the release and re-run it (102 of 273 rows would change label), after the builder divergence below |
| `03_analytics/Isuzu/prism/scripts/build_dealer_sellout_aim_gps.py` | decide the builder first (chart/KPI/title differ); then regenerate the sellout family |
| `04_tools/ids_dealer_ranking/build_ids_country_packs_v13.py` | choose self-contained online Leaflet (ours) or bundled offline grid (main); then regenerate the 41 IDS pages |
| `04_tools/spa_application/build_spa_application.py` | take ours (2,759 lines, has `patch_form_sized`), then port main's `patch_form` if still needed |
| `04_tools/ISZE_Tender_Monitor_Install/tender_scraper_v3.py` | real divergence (166 ours-only / 530 main-only lines); needs a code review |
| `04_tools/db_sales_review/build_deck.py`, `build_full_deck.py` | take ours: the working tree's `common.py` exports `wallet_2025`, not `gps_wallet` |
| `AGENTS.md` | hunk 1: keep both item 11s (ours series->weight band as 11, main's chat-overviews as 12); hunk 2 conflicts in substance (ours allows nicknames in agent chat, main says chat overviews follow jerome-brief-plain): Jerome's call |
| `00_docs/ISZE_ROADMAP.md` | ours (09-19) with main's "Scraper quality V2 Done 2026-09-14" status folded into row 13; drop main's duplicate rows 13/14 |
| `00_docs/agent/STATE_PACKET.md` | take ours (09-25 snapshot supersedes main's 09-14) |
| `00_docs/ISZE_OS_DATA_MAP.yaml` | one item has a different ask/artefact on each side; pick one |
| `04_tools/ISZE_Tender_Monitor_Install/_COUNTRY_TENDER_PORTALS_MAP.md` | ours (newer measured counts); keep main's "17/29" coverage wording |
| `04_tools/ISZE_Tender_Monitor_Install/_OPEN_BACKLOG_ARRANGED.md` | ours' 09-22 status row, plus main's "next DARK without a key" pointer |
| 3 x `IDS_2026_dealer_compare.html` delete/modify (`01_data/08_Distributor/IDS_2026/_EXPORT/`, `.../reports/dashboard/`, `02_dashboards/ids/IDS_all_dashboards_2026-08-19/01_overview/`) | unexplained deletion in `4ccae53d`; not decided |

---

## 2026-10-02 completion pass (Jerome's go) — all 87 resolved, merge committed, not pushed

**Route chosen: redo, not patch.** The staged merge sat on `132068d1`; the PR branch had moved to
`20b0fc90` (7 commits, incl. `dfe73041` pr00 correction). A merge commit on `132068d1` could not be
pushed to the PR branch as a fast-forward. So: merge aborted, `merge/pr10-main-resolve` reset to
`20b0fc90`, `origin/main` (`87c7907b`, unchanged since the first pass) merged again. Same 87
conflicts. Earlier resolutions re-applied from the saved index; the ours-side blob was re-checked per
file against `20b0fc90` first.

**Merge commit:** `8522d55e` on `merge/pr10-main-resolve` (parents `20b0fc90`, `87c7907b`). Not pushed. PR #10 not merged.

| path | resolution |
|---|---|
| 57 generated files (41 IDS pages, 13 derived, sellout json/page, Action Ledger) | `20b0fc90` (ours unchanged since `c58e6ec4`, so same as the first pass) |
| `pr00_classification.csv`, `parts_catalog_dimension.csv/.parquet` | `20b0fc90` (now committed there; same blobs as the first pass) |
| `sellout_aim_top_pn_2025.csv` | **ours, not regenerated.** The builder reads labels from the workbook taxonomy (`modules.aim_pn_classifier`), not the release; pointing it at the release is a builder change nobody approved, and re-running one file alone would split the sellout family. Still open |
| `monday_pn_opportunity_crosswalk_20260914.csv` | ours (byte-identical both sides) |
| `gps.md`, `scrapers.md`, prism `.gitignore`, prism `CHANGELOG.md`, `AGENTS.md` | first-pass blobs reused (ours side unchanged since). `AGENTS.md` = `20b0fc90` + main's `ISZE_BI_FRAMEWORK.md` line |
| 3 × `02_dashboards/Data/**` | deletion kept (gitignored by rule) |
| `INDEX.md` | redone on `20b0fc90` (ours changed): ours rows + main's Decision pack row |
| `_source_health.json` | redone: main's structure (Ireland eTenders) + ours' Spain PLACSP count/note from `20b0fc90` |
| `ISZE_ROADMAP.md` | ours (09-19); row 13 replaced by main's "Done 2026-09-14" text; main's duplicate 13/14 dropped |
| `STATE_PACKET.md` | ours; main's 09-14 packet appended verbatim at the end as a dated history entry |
| `ISZE_OS_DATA_MAP.yaml` (`residual_24pn`) | **main's ask + artefact** (`NO_PR00_HARDWARE_FY2026.md`), ours' schema fields kept. Deviates from "ours wins": the item's name/integrity already auto-merged to main's FY2026 basis (€67,318.49 / 21 parts, "Calendar-2025 24 … do not quote"), so ours' "price the 24 PNs" ask would contradict its own integrity line. `grain` text written from the artefact's content |
| `_COUNTRY_TENDER_PORTALS_MAP.md` | ours' rows/counts; main's "17/29 ≈ 59%" coverage paragraph |
| `_OPEN_BACKLOG_ARRANGED.md` | ours' 09-22 row + main's "next DARK without a key" pointer |
| `tender_scraper_v3.py` | union of imports (ours' ES/IT/DE module fetchers + main's `parse_xml_root`, `retry_after_seconds`, `national_fetchers_ie`); ours' delegated ES fetcher. Main's Ireland eTenders wiring auto-merged |
| `build_deck.py` | **not plain ours.** Main's `use_gps_master` / `skip_gps_pct` lines had auto-merged around the hunk and both flags are set in `db_profiles.yaml` (`use_gps_master` on PORTUGAL, `skip_gps_pct` on ISD, gps_key Ireland). Ours' bullet wording kept, pointed at main's `gps_wallet` / `gps_uio` locals; identical to ours when neither flag is set |
| `build_full_deck.py` | **main's structure + ours' wording** ("target spend", "parts mix"). Plain ours would drop the Ireland >100% guard and plot a GPS % main explicitly removed |
| `build_spa_application.py` | ours. Main's `patch_form` is defined but never called in main; ours' `patch_form_sized` already sets every cell it sets (with ours' one-column-shifted layout). Not ported |
| `build_dealer_sellout_aim_gps.py` | ours' hunks; main's auto-merged "sales to dealer" wording kept; main's Chart.js inlining removed (ours has no charts, HTML bars) |
| `build_ids_country_packs_v13.py` | main's map line ("bundled Leaflet + offline grid"), ours' "shared colleague pack" wording — the auto-merged template and `build_ids_dashboard.py` are main's offline-map build, so that is what the builder now produces |
| 3 × `IDS_2026_dealer_compare.html` delete/modify | **restored from main** (deletion in `4ccae53d` has no recorded reason) |

**Tests:** `py_compile` on all 32 `.py` files the merge changes vs `20b0fc90` — all pass. Tender
`tests/test_lifecycle_and_unknowns.py` **33 passed / 0 failed**; `test_relevance_rss.py` +
`test_national_fetchers_ie.py` 10 passed; `04_tools/_shared/tests` 17 passed. Import check OK for
`build_deck`, `build_full_deck`, `build_ids_country_packs_v13`, `build_dealer_sellout_aim_gps`. No
test exists for the SPA builder. Decks not rebuilt (would write to tracked `09_meetings/`).

**Risks / open:**
1. Committed IDS pages are ours' online-Leaflet build; the merged builder now emits main's offline,
   inlined-Leaflet map. Next IDS regeneration changes the pages' map style.
2. `sellout_aim_top_pn_2025.csv` labels still come from the workbook taxonomy, not release 2026-10-02.
3. Deck builders now honour `use_gps_master` (Portugal) and `skip_gps_pct` (Ireland) — a rebuilt deck
   can differ from the last committed one on the GPS slide.

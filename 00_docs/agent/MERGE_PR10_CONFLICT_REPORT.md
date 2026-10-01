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

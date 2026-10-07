# U26 work package E — measure, merge, report (agent E, the one writer)

Branch `cursor/2026-10-07-universe-u26-market-harvest`
Base `8729346926caf7b2265f2487ff460f98d18f2d21`
HEAD at start `115e7fad8295b7956251ef00ef2f5f83a64ba6e0`

Worktree only. Nothing merged to main, no sync, no mail, no scraping performed by
this agent, no Eucon row left this machine. The four known red checks (BASE-ENGINE,
BASE-BROWSER, ACCEPT-01 R27) were left as they were.

---

## 1. Self-contained worktree — what was copied, what was backed up, which path wins

`price_observations.parquet` and `crossref_edges.parquet` are not in git, so both were
copied from the main clone into this worktree, along with the small state files the
cross-reference step needs:

| from the main clone | into the worktree |
|---|---|
| `01_data/00_derived/price_observations.parquet` + `.meta.json` | same paths (sha256 `1bb9fd7b...` identical on both sides) |
| `04_tools/aftermarket_intelligence/state/crossref_edges.parquet` | same path |
| `.../state/crossref_graded.csv` | same path |
| `.../state/spareto_crossref.csv` + `_per_part.csv` | same path |

The ledger builder also reads six raw inputs that were missing here (they are
gitignored, so the worktree did not have them): `ks_results.csv`,
`eucon_crossref_iam_20260329.csv`, `Eucon_March.xlsx`, `Eucon_Online28072025.xlsx`,
`tmc_results.csv`, `tranzparts_results.csv`. Those were copied in as well, otherwise
`build_price_ledger.py` would have silently written a much smaller ledger.

Backups made before anything was written:

- `01_data/00_derived/price_observations.parquet.bak_20261007T072934Z_before_u26_merge`
- `01_data/00_derived/price_observations.meta.json.bak_20261007T072934Z_before_u26_merge`
- `04_tools/price_ledger/page_manifest.csv.bak_20261007T072934Z_before_u26`
- `04_tools/price_ledger/OFFERED_ROWS.csv.bak_20261007T072934Z_before_u26`
- `.../state/crossref_graded.csv.bak_20261007T0631Z_before_u26_c1_merge` (+ meta, report)

**Which path the coverage builder reads — the choice, stated.** Both were done:
`LEDGER_CANDIDATES` was **reordered** so the worktree copy is first and the main-clone
path is only a fallback, **and** `DERIVED` (the inputs: family worklist, euros, meta)
was **pointed at the worktree** instead of the main clone. The builder prints the path
it read, and it printed the worktree:

```
ledger read: C:\Users\jerom\Desktop\claude\_worktrees\ISZE_u26\01_data\00_derived\price_observations.parquet  (6,690 rows)
```

The main clone was never written to.

---

## 2. Merge into the ledger, through the existing path

The eight agents all wrote only inside their own folder, so their pages were promoted
and their rows flattened:

1. **Pages promoted.** 96 pages copied from each agent's `pages/` folder into the
   worktree `_probe` root under `_u26/<ID>/pages/`.
2. **`page_manifest.csv` appended.** 96 rows, one per page: `site` = `ks` (16, A1),
   `tmc` (5, A2 category listings), `tranzparts` (6, A2 product pages), `spareto`
   (69, C1). A1's `ks` and C1's `spareto` reuse the site keys the ledger already
   knows; `tmc` and `tranzparts` already exist as parsers but were never wired into
   the bridge's `SITE_MODULE`, so they were registered.
3. **Bridge run** `build_scraped_observations.py --emit --json`. It needed one extra
   input: the Tranzparts product page must print the number that was searched for, and
   that number is not in the product URL. It travels in a sidecar,
   `04_tools/price_ledger/_u26_e_page_query.csv`, six rows, taken from each A2 row's own
   description (`"the number we searched for is printed on this product page"` and the
   row's part number). Nothing was inferred: a page with no such statement gets no
   sidecar row and emits nothing.
4. **Ledger built.** `build_price_ledger.py`, then `verify_scraped_observations.py`.

Result of the bridge over 3,283 manifest pages:

| site | pages | rows offered | priced | rejected |
|---|---|---|---|---|
| amayama | 1,384 | 3,011 | 3,011 | 17 |
| ks | 954 | 807 | 807 | 12 |
| **tmc** | 5 | **88** | 88 | 0 |
| **tranzparts** | 6 | **6** | 6 | 0 |
| **spareto** | 69 | **759** | 759 | 2 |
| omega | 853 | 10 | 10 | 547 |
| geparden / mekster / tungen / autoline | 12 | 27 | 22 | 0 |
| **TOTAL** | **3,283** | **4,708** | **4,703** | **578** |

0 broken pages, 812 pages that returned a real "not our part" answer.

Ledger before 6,597 rows -> after **6,690 rows**. New U26 contributions:
`ks` 775->807 (the A1 OE pass, 33 relevance rows), `tmc` 0->55, `tranzparts` 20->26 (6 new
page-derived plus the 20 retired category rows), `spareto_crossref` 0->761 parsed, and
`omega` 10 unchanged (A3 emitted nothing).

**Loader tags.** `ks`, `omega`, `spareto_crossref` and `tranzparts` were reused as the
instructions asked. `ks_crossref` was not needed: A1's competitor-number pass produced
0 strict rows. **`u25_market_scrape` does not exist anywhere in this repository or in
the main clone** — the tag could not be reused because there is nothing to reuse. A2's
two sources got the names their own parsers declare: `tmc` for T&M Commercials
category pages and `tranzparts` for Tranzparts product pages. Note that `tranzparts`
now carries two vintages under one tag: the retired 2026-09-24 category rows (no Isuzu
number, `match_method=category_only`) and the 6 new page-derived rows
(`match_method=exact_oem`, the searched number printed on the page). The ledger's own
`not_loaded` note records this.

**Two deliberate exclusions from the ledger, both stated in code:**

- `spareto_crossref` rows are **not** loaded as price observations. A Spareto price is
  retail incl. VAT at a rate the page does not state, so the evidence rules exclude it
  on `TAX_RATE_NOT_STATED`; keeping them would inflate row counts without adding a
  usable comparable. They travel through
  `04_tools/aftermarket_intelligence/state/spareto_crossref.csv`, which is exactly the
  path `grade_crossref_edges.py` reads (step 3). The loader change prints
  `scrape_phase1: 759 spareto_crossref row(s) left in the crossref state file on purpose`.
- One product card can appear on two saved T&M category pages. The bridge issues
  `obs_id` from the observation's own identity (part, rival number, seller, date,
  price), not the page, so 33 rows appeared twice with the same `obs_id` and
  `validate()` refused the whole file. They are the same observation, so
  `load_scraped_phase1()` now de-duplicates on `obs_id` and prints the count:
  `scrape_phase1: 33 row(s) seen on more than one saved page — the same observation,
  counted once`.

**Verbatim check — passes.**

```
verified: 3949/3949   failed: 0
   amayama 3011/3011   autoline 16/16   geparden 5/5   ks 807/807
   mekster 5/5   omega 10/10   tmc 88/88   tranzparts 6/6   tungen 1/1
VERBATIM CHECK PASS — every price and part number is written on its source page, and every row is in the ledger
```

`spareto_crossref` was added to `SCRAPE_LOADERS` and then removed again: because the
ledger does not load those rows, checking them against it reported all 759 as "row is
not present in the ledger" and buried the real failures. It is not a loosening — those
rows are not in the ledger on purpose.

---

## 3. Cross-reference graded, not decided

`grade_crossref_edges.py` was run twice: once on the state as it stood (to get the
"before"), then again after C1's reading was merged into the shared state file.

C1's U26 rows were merged into `state/spareto_crossref.csv`: 1,177 rows -> **1,688**
(+511 new pairs the earlier pass did not have; 511 of C1's 761 rows were already
present from the 2026-10-02 pass). Parts covered 170 -> 217. C2's second-day file was
**not** merged: it is a re-reading of the same pipeline on the same day, not new
evidence.

**One-step rule — verified, held.**

| | before (Eucon only) | after (C1 merged) |
|---|---|---|
| confirmed | 1,439 | 1,450 |
| likely | 756 | 849 |
| doubtful | 4,806 | 5,146 |
| reject | 161 | 157 |

Those totals include 1,147 new Spareto-only pairs merged as `doubtful`. On the **same
6,455 Eucon edges** the movement is unambiguous: confirmed 1,395->1,450, likely
125->849, doubtful 4,663->3,999, reject 272->157. **949 edges moved up, 0 moved down, 0
moved more than one step.**

**Moves: please read 156, not 155.** On the 123 worklist numbers, 156 pairs are
corroborated by a second pipeline. C2's 155 is correct for the C1 reading alone; the
shared state file also carries the earlier 2026-10-02 pass, which agrees on one further
pair. The 1-pair difference is the earlier pass, and it is real.

---

## 4. The brief's match labels reconciled

`MATCH_METHODS` is `{exact_oem, crossref, category_only}`. The brief's
`crossref_candidate` / `crossref_corroborated` are **not** in it, `ledger_schema.row_problems()`
rejects them, and **`MATCH_METHODS` was not widened** — by any agent or by me. Every
harvested row keeps a schema-valid `match_method` (`exact_oem` where the searched
number is printed on the page, `crossref` on Spareto, `category_only` on the KS
relevance rows) and carries the grade in the separate `crossref_grade` column
(`candidate` | `corroborated` | `category_only_relevance`).

**The final rule applied:**

- A pair claimed by **one** source stays a **candidate**. It never moves a grade.
- A pair claimed by **two or more independent pipelines** moves the existing edge up
  **exactly one** step (reject->doubtful->likely->confirmed) **when the brands agree**,
  never down. The two independent pipelines are **Eucon** and **Spareto**; C1 and C2
  are two readings of one of them and count as day stability, never as two witnesses.
- Nothing is ever "approved" unless it is **Eucon-listed (Jerome-approved)** or graded
  **confirmed by the existing rules**.

---

## 5. Corroboration by NUMBER — the four C2 figures, re-measured from the files

Recomputed from `spareto_crossref.csv` (merged), `crossref_edges.parquet` and the 112
list, with brand agreement decided by `grade_crossref_edges.py`'s own alias table:

| C2 measured | E re-measured from the files | verdict |
|---|---|---|
| 58 of the 112 have >=1 Spareto pair | **58** | matches |
| 54 of those are single-source only | **54** | matches |
| 4 have >=1 corroborated pair | **4** | matches |
| 735 Spareto pairs on the 123 | **735** | matches |

The four C2 numbers stand. On the same basis: 13 pairs of the 112 are corroborated,
546 are Spareto-only (C2 said 13 and 579 for the whole 123 — 579 is right for the 123,
546 for the 112 alone; both are in the C2 file and both reproduce).

---

## 6. Coverage re-run as `build_market_data_gap_coverage_20261007.py`

A dated copy, not an edit of the 20261006 file. The change is the generator: the
worktree ledger is read first, the inputs come from the worktree, and the outputs are
dated 20261007. Output shape is identical (`market_data_gap_coverage_20261007.csv`,
`.meta.json`, `market_data_gap_empty_pns_20261007.csv`), plus one new
`.metrics.json` that answers the brief's question in order.

**Euros first, per market and family:**

| market | family | ITUK/PORTUGAL billed EUR (FY2025 GPS) | billed EUR of numbers with >=1 eligible offer | focus rows | 50-row threshold | empty numbers, billed EUR |
|---|---|---|---|---|---|---|
| UK | brake_pad | 302,366.25 | **0.00** | 79 total | sufficient (79 >= 50) | 42 - EUR 1,977,711.74 |
| UK | oil_filter | 85,096.07 | **0.00** | | | 57 - EUR 285,446.25 |
| PT | brake_pad | 66,114.04 | **0.00** | 27 total | insufficient | 47 - EUR 3,842,088.66 |
| PT | oil_filter | 10,980.50 | **0.00** | | | 71 - EUR 1,267,744.25 |

**Eligible comparable offers: 0 in UK, 0 in Portugal.** That is unchanged from the
20261006 build.

**Remaining exclusion reasons by count** (a row can carry more than one):

| market | DELIVERY_BASIS_NOT_STATED | PRODUCT_MATCH_UNRESOLVED | PACK_CONTENTS_UNKNOWN | TAX_BASIS_NOT_STATED |
|---|---|---|---|---|
| UK | **79 (every row)** | 54 | 33 | 9 |
| PT | **27 (every row)** | 27 | 13 | 27 |

**Numbers still empty with their billed euros:** UK 99 numbers - EUR 2,263,157.99;
Portugal 118 numbers - EUR 5,109,832.91. The largest are in
`market_data_gap_coverage_20261007.metrics.json`.

---

## 7. The gaps table

`01_data/00_derived/u26_gaps_table_20261007.csv` — 217 rows, one per (number, market)
still empty, with one column per source and what that source returned.

A per-number outcome is filled **only** where an agent kept one row per number and it
matched the exact queried number:

| source | per-number records |
|---|---|
| KS International (UK) | 127 |
| Omega (UK) | 123 |
| PT hosts, second sweep (B2, six hosts) | 131 |
| Spareto (crossref) | 123 |

Tranzparts and T&M Commercials were recorded by host, not per number, so they get one
honest summary line each rather than a fabricated per-number verdict. The first
Portuguese sweep recorded host-level robots verdicts for 186 hosts, none of which
passed all three gates, so its line says exactly that. A source an agent did not
attempt is written `not_attempted`.

---

## 8. Mutation check — mandatory, and it passes

Tested row: a **new** U26 row, Tranzparts `5876101170` (UFI oil filter, GBP 20.22 ex
VAT, 2026-10-07), run through `row_to_evidence_input()` and the same Node evidence
runner the coverage builder uses.

| case | delivery basis | tax basis | eligible? | reason codes |
|---|---|---|---|---|
| **D0** baseline | stated | `excl` as the page prints it | **yes** | — |
| **D1** delivery stripped | none | `excl` | **no** | `DELIVERY_BASIS_NOT_STATED` |
| **D2** delivery restored | stated | `excl` | **yes** | — |
| **T1** tax stripped | stated | none | **no** | `TAX_BASIS_NOT_STATED` |
| **T2** tax restored | stated | `excl` | **yes** | — |
| **A** as the builder maps it today | none | `excl` | **no** | `DELIVERY_BASIS_NOT_STATED` |

Both fields are genuinely read: the row drops out when either is stripped and comes
back when it is restored. Evidence: `01_data/91_build/_u26_e_mutation_20261007.json`.

**The finding that matters:** case A is what the real build produces. The ledger has
**no column that states a delivery basis**, so the builder hands the shared rule a
null, and the rule excludes every single row on `DELIVERY_BASIS_NOT_STATED` — all 79 UK
rows and all 27 Portuguese rows. That is the one field standing between the harvested
rows and an eligible comparable, and it is a **ledger-schema gap, not a scraping gap**.
No harvested page is at fault, and no further scraping fixes it.

---

## 9. Before / after, read back from disk

Both files read from disk, not from the build log:

| market | family | build | empty numbers | billed EUR of empty numbers | numbers with a row | focus rows | eligible |
|---|---|---|---|---|---|---|---|
| UK | brake_pad | 20261006 | 45 | 2,175,215.40 | 4 | 12 | 0 |
| UK | brake_pad | **20261007** | **42** | **1,977,711.74** | **7** | **21** | 0 |
| UK | oil_filter | 20261006 | 68 | 894,922.91 | 6 | 26 | 0 |
| UK | oil_filter | **20261007** | **57** | **285,446.25** | **17** | **58** | 0 |
| PT | brake_pad | 20261006 | 47 | 3,842,088.66 | 2 | 13 | 0 |
| PT | brake_pad | 20261007 | 47 | 3,842,088.66 | 2 | 13 | 0 |
| PT | oil_filter | 20261006 | 71 | 1,267,744.25 | 3 | 14 | 0 |
| PT | oil_filter | 20261007 | 71 | 1,267,744.25 | 3 | 14 | 0 |

Read in euros: on ITUK the harvest took **EUR 609,459.17 of number-billed sales off the
empty list** in oil_filter (68 empty numbers -> 57; EUR 894,922.91 -> EUR 285,446.25) and
**EUR 197,503.66** in brake_pad (45 -> 42). Fourteen UK numbers that had no price row at
all now have one — 24 numbers with a row, 79 focus rows, against 10 and 38 before.
Portugal moved not at all, because no Portuguese page was usable. `market_sufficiency`
changed from `insufficient` to `sufficient` for UK (38->79 rows against a 50-row bar);
Portugal stays `insufficient` at 27.

---

## 10. What was tried and failed, so nothing is retried blindly

**UK.** KS International allowed, 272 pages, 0 strict rows (its cards never print the
searched number; 33 relevance-only rows). Tranzparts allowed, 278 pages, 6 rows — its
search does not index our numbers. T&M Commercials allowed but has **no part-number
query at all** (every search route returns HTTP 504), so only a bounded 17-page
category walk was possible, 88 rows read across two pages sharing cards. Omega allowed,
123 pages, **0 rows** — the guard refused all 123 (59 closest-match, 64 empty search
page). Dropped: eurocarparts and carparts4less (robots disallow the search path),
gsfcarparts and ukpartsdirect (allowed, no usable route), milneroffroad (allowed, no
Isuzu coverage), japanpartsuk / truckpartsonline / buycarparts (robots unreachable or
403 — UNKNOWN means stop), tmcshop (host dead).

**Portugal.** 296 hosts robots-checked across the two sweeps, 43 allowed by robots. Six
gate-passing hosts were swept across all 123 OE and all 153 competitor numbers — 1,370
queries — and returned **no usable price**: truckparts.pt, turbopecas.pt, isuzu.pt,
ascendum.pt, sotecnica.pt, spareparts.pt. Two apparent hits were checked and discarded
(Spareparts.pt prints a price-filter widget; isuzu.pt prints a D-MAX finance banner).
Every allowed host fails at least one of the three gates: price not in raw HTML, or bot
check on the product path, or robots disallows the search. Dropped at the gate: 245
robots-unreachable, 4 explicit disallow, plus Autodoc / Oscaro / Mister-Auto / Trodo
retired earlier.

**Spareto** allowed, 123 numbers, 69 with cards, 759 cross-reference rows, 54 clean
misses, 0 refusals.

---

## 11. Could not do

- **`u25_market_scrape`** does not exist in this repo or the main clone; that tag could
  not be reused.
- **Portugal produced nothing.** Not a failure of the sweep: no Portuguese host both
  allows automated access and publishes a part price without JavaScript.
- **No eligible comparable offer can exist under the current mapping.** The ledger has
  no delivery-basis column, so the shared rule excludes every row. This is a schema
  gap and cannot be closed from the scrape side.
- **The 112 numbers cannot reach two independent sources in this pass.** With only
  Eucon and Spareto as pipelines, a number that has a Spareto pair but no Eucon edge
  can never be corroborated here, so 54 of the 58 stay single-source candidates by
  construction.
- **C2's day gap is 0 days.** Its second reading ran eight minutes after C1, on the
  same UTC date, because Spareto must not be hit in parallel. It demonstrates listing
  stability, not price movement.

---

## Final line

**No case now has a non-empty eligible comparable offer on real data: 0 rows pass in
both UK and Portugal, unchanged from the 20261006 build.** The single exclusion that
blocks the rest is `DELIVERY_BASIS_NOT_STATED` — every focus row in both markets is
excluded on it, because the price ledger has no field that says whether a listed price
includes delivery. The market is therefore still short of 50 eligible rows per market,
and no amount of further scraping changes that while the ledger cannot record a
delivery basis. The harvest did do its job on the row count: UK numbers with at least
one price row went from 10 to 24 and UK focus rows from 38 to 79, which is why UK now
reads `sufficient` on the 50-row bar while Portugal stays `insufficient` at 27.

---

## Commits

```
git rev-parse HEAD
13d334836cae4bb8d94c21c904e71fa70ba49e73

git diff --shortstat 8729346926caf7b2265f2487ff460f98d18f2d21..HEAD
662 files changed, 632526 insertions(+), 1913 deletions(-)
```

The 662 files include the eight other agents' work; agent E's own work is three commits
on top of `115e7fad8295b7956251ef00ef2f5f83a64ba6e0` —
`3e8381158aab886f3d5ec0a4db88e3247ae98dd9` (merge, grading and coverage),
`9f5573d70c03a9f140cde8c688657db50c01214f` (the report and its measured outputs) and
this one. `git diff --shortstat 115e7fad8295b7956251ef00ef2f5f83a64ba6e0..HEAD`
(agent E alone) is **54 files changed, 24,449 insertions(+), 1,875 deletions(-)**.


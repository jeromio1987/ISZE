# U26 delivery basis — ledger column, sufficiency fix, re-check

Branch `cursor/2026-10-07-universe-u26-market-harvest`
Start `730279ea04be2202eeacad8a06e5dbb7c4bf2806`

Worktree only. No merge, no sync, no mail, no deploy. No network call — everything was read
from the pages already saved under `_probe/` and `_probe/_u26/`. No scraping, no value invented.
The 4 known red checks (BASE-ENGINE, BASE-BROWSER, ACCEPT-01 R27) and the
`match_method="crossref"` + separate `crossref_grade` reconciliation were left untouched.
The exclusion codes in `market_observation.js` / `comparable.js` were NOT changed.

---

## 1. What was changed, and why

Two things, both in the generator, never in the output:

**A. The ledger gained the delivery basis.** `04_tools/price_ledger/build_price_ledger.py`
`COLUMNS` gained **two** columns, mirrored in `04_tools/delegation/parsers/ledger_schema.py`
(the schema selftest asserts the two lists agree, and it passes):

| column | holds |
|---|---|
| `delivery_note` | what the page actually says, short; blank when the page is silent |
| `delivery_included` | `yes` / `no` only, and only where the page states it for that listing or states an unambiguous threshold the listed price meets or fails; **blank when the page is silent** |

The split is deliberate: `delivery_included` supplies the value the evidence rule reads,
and `delivery_note` keeps the wording so a reader can see what was read rather than trusting
a yes/no. Blank is not `no`: the absence of a stated charge is never read as a charge, and
nothing is inferred from the price.

**B. The sufficiency label now counts usable rows only.** In
`01_data/91_build/build_market_data_gap_coverage_20261007.py` the status used to compare the
RAW focus row count to the 50 bar, which printed `sufficient` for UK on 79 rows that the
evidence rules then excluded one and all. It now compares **usable rows** (rows passing the
evidence checks) to the 50 bar. Both numbers are kept and labelled — `focus_rows` (raw) and
`usable_rows` (eligible) — so nothing is deleted, the raw count just stops deciding the label.

**Wiring order, as specified.** `build_price_ledger` COLUMNS + the schema mirror → the site
parsers (`site_tranzparts.py`, `site_ks.py`, `site_tmc.py`) → the bridge (no new logic, verified)
→ the coverage builder (`row_to_evidence_input`, the one place eligibility learns about
delivery). `site_spareto.py` was left alone: its rows are cross-reference rows and stay out of
the price ledger.

### What was read, and what was not

The delivery reader (`ledger_schema.read_delivery_basis`) reads the SERVED Page Source the
runner hands in, not a separate static file, so the runner stays the only party that fetches.
It is currency-guarded: a page not priced in GBP yields nothing rather than a threshold
compared in the wrong money.

Measured counts across the saved corpus:

| outcome | pages / rows |
|---|---|
| a stated free-delivery threshold | 6 Tranzparts pages |
| a delivery info link and nothing else | 10 saved pages (recorded as `delivery info page only`, **basis blank**) |
| nothing about carriage at all | 20 focus pages, and the rest of the corpus |

The two Tranzparts thresholds matter. The announcement bar says *"FREE DELIVERY WHEN YOU SPEND
OVER £50"* and the Delivery and Shipping panel says free tracked delivery over £80 to mainland
UK. For a basket between £50 and £80 those two disagree, so the reader claims **no** single
basis and says so in the note. It only returns `yes` when the listed price clears the HIGHER
threshold, and `no` when it is below the LOWER one — the only two unambiguous cases.

A corpus-wide scan of all 574 UK pages for any phrase saying the price *includes* delivery
(`free delivery`, `delivery included`, `includes delivery`, `carriage paid`, …) found the
Tranzparts announcement bar and nothing else. **No harvested UK page states delivery-included.**

---

## 2. Re-run chain — all passed

| step | result |
|---|---|
| `build_scraped_observations.py --emit --json` | 4,708 offered, 5,286 rows written |
| `build_price_ledger.py` | 6,690 rows, 23 columns (was 21) |
| `verify_scraped_observations.py` | **3949/3949, 0 failed** — no row lost |
| `_u26_delivery_parity.py` (new) | every pre-existing row unchanged, row for row |

The parity check is the reason the verbatim number is trustworthy: it compares the pre-change
backup with the ledger on disk on all 21 pre-existing columns, and asserts the only addition is
the two delivery columns with the same count, same order, same values. It passes.

The verbatim check never lost a row: `3949/3949 before and after`.

---

## 3. Before / after, read back from disk (euros first, then rows)

Both files read from disk, not from the build log. Backup:
`*.bak_20261007T081251Z_before_delivery_col`.

**Billed euros, FY2025 GPS, focus families:**

| market | family | ITUK/PORTUGAL billed EUR | billed EUR of numbers with ≥1 eligible offer |
|---|---|---|---|
| UK | brake_pad | 302,366.25 | **0.00** |
| UK | oil_filter | 85,096.07 | **0.00** |
| PT | brake_pad | 66,114.04 | **0.00** |
| PT | oil_filter | 10,980.50 | **0.00** |
| | **all markets, focus list** | **6,485,561.90** | |

**The three counts side by side:**

| market | build | raw focus rows | usable rows | status | empty numbers | empty billed EUR |
|---|---|---|---|---|---|---|
| UK | before | 79 | 0 | ~~sufficient~~ | 99 | 2,263,157.99 |
| UK | **now** | **79** | **0** | **insufficient** | 99 | 2,263,157.99 |
| PT | before | 27 | 0 | insufficient | 118 | 5,109,832.91 |
| PT | **now** | **27** | **0** | **insufficient** | 118 | 5,109,832.91 |

The only figure that moved is the UK label: `sufficient` → `insufficient`. That is the
sufficiency fix working — 79 raw rows were never 79 usable rows. The raw count is retained.
Nothing moved in euros, eligible counts or empty numbers, because no row became eligible.

---

## 4. The UK 79 rows, specifically

The build reads **79** UK focus rows and **all 79** carry `DELIVERY_BASIS_NOT_STATED` (the
metrics file's UK count), because none of them states a basis.

| | count |
|---|---|
| UK focus rows read by the build (E's 79; the page probe could read 72) | 79 |
| carry a delivery **note** | 22 (all `delivery info page only`, on KS pages) |
| carry a delivery **basis** (yes/no) | **0** |
| became eligible | **0** |
| excluded on `DELIVERY_BASIS_NOT_STATED` | **79 (every row)** |

Outside the build there are 4 further UK focus rows that **do** state a basis — the Tranzparts
rows from the A2 pass, now carrying `no` because their prices (GBP 19.26–32.00) sit below the
shop's stated GBP 50 free-delivery threshold, and the page also states the charge that then
applies (GBP 5.99 ex VAT standard / GBP 19.99 next day). A `no` needs a *delivered cost* to
compare with, and no cost was read into a numeric field, so those rows would be excluded on
`DELIVERY_COST_NOT_SUPPLIED`. They do not appear in the build at all: the unchanged
`RETIRED_LOADERS` list drops the `tranzparts` loader before the evidence run, exactly as it did
before this change.

**Zero UK rows carry a usable delivery basis, and zero are eligible.** The exclusion that still
blocks the 79 is `DELIVERY_BASIS_NOT_STATED`: those pages say nothing about carriage (KS's
footer link is not a basis, T&M states nothing, the Eucon rows are file-based and carry neither
note nor basis). 8 of the 79 are blocked by delivery and nothing else; **0 of them would become
eligible even if delivery were satisfied**, because their other blocker is
`PRODUCT_MATCH_UNRESOLVED`.

---

## 5. Mutation check — mandatory, both outputs

Tested row: Tranzparts `5876101170` (UFI oil filter, GBP 20.22 ex VAT, 2026-10-07) — a NEW U26
row whose listing is a single filter, so delivery and tax are the only fields that decide it.
This is a real value being stripped, not a placeholder: the page's threshold is GBP 50 and the
listed price does not meet it.

```
OUTPUT 1 — REAL BASIS (the row exactly as the copy on disk maps it)
  case       mapped delivery  eligible  reason_codes
  as_read    False            False     ['DELIVERY_COST_NOT_SUPPLIED']
  stripped   None             False     ['DELIVERY_BASIS_NOT_STATED']
  restored   False            False     ['DELIVERY_COST_NOT_SUPPLIED']

  field_is_read_on_this_row: True

OUTPUT 2 — FORCED-YES WIRING PROOF (same row, delivery_included='yes')
  case       mapped delivery  eligible  reason_codes
  as_read    True             True      []
  stripped   None             False     ['DELIVERY_BASIS_NOT_STATED']
  restored   True             True      []

  wiring_proven   : True
  mapping_is_wired: True
```

Read together these prove the mapping is wired and state the corpus answer.

**Output 1** is the row exactly as the copy on disk produces it. Stripping `delivery_included`
moves the reason from `DELIVERY_COST_NOT_SUPPLIED` to `DELIVERY_BASIS_NOT_STATED`, so the field
**is** read — but the row is ineligible either way, because a `no` needs a stated cost. It does
not "drop out of eligible" on stripping, because it was never eligible on this real value.

**Output 2** is the same row with `delivery_included` forced to `yes`, which isolates the field
from every other one. It is eligible with the basis, drops out of eligible on
`DELIVERY_BASIS_NOT_STATED` when stripped, and is eligible again when restored — exactly the
required mutation. This is the answer to "is the mapping wired": **yes**.

A third case (`D3`) confirms a `delivery_note` with no basis still drops out, so the note is kept
as evidence and is not read as a value.

---

## 6. Sufficiency fix — evidence

```
UK: before 'sufficient' on 79 RAW rows -> now 'insufficient' on 0 USABLE rows (raw 79 retained)
PT: before 'insufficient' on 27 RAW rows -> now 'insufficient' on 0 USABLE rows (raw 27 retained)
```

Both counts now travel in the metrics file (`focus_rows`, `usable_rows`), in the meta
(`sufficiency`, with `status_basis`), and in the build summary. The label reads `insufficient`
for UK and Portugal, which is what 0 usable rows against a 50-row bar is.

---

## 7. Files changed

| file | change |
|---|---|
| `04_tools/price_ledger/build_price_ledger.py` | COLUMNS gained `delivery_note`, `delivery_included`; `validate()` refuses a basis outside yes/no and a `yes` with no note; meta records the delivery rule and the count |
| `04_tools/delegation/parsers/ledger_schema.py` | COLUMNS mirror, `DELIVERY_INCLUDED_VALUES`, `read_delivery_basis()` (the shared page reader), `row_problems()` delivery checks |
| `04_tools/delegation/parsers/site_tranzparts.py` | reads the basis off the product page (the threshold rule) |
| `04_tools/delegation/parsers/site_ks.py` | reads it off the served page; normally blank, records the info-only note |
| `04_tools/delegation/parsers/site_tmc.py` | reads it per card; blank, as the page states nothing |
| `04_tools/price_ledger/build_scraped_observations.py` | carries the two keys through `normalise()`; documents why they are not in the obs_id key |
| `01_data/91_build/build_market_data_gap_coverage_20261007.py` | `delivery_basis()` maps the ledger columns into the evidence row; sufficiency now counts usable rows; metrics/meta record both counts, the correction note and the delivery finding |
| `01_data/00_derived/price_observations.parquet` | rebuilt, 23 columns (data file, gitignored) |
| `01_data/00_derived/market_data_gap_coverage_20261007.{csv,meta.json,metrics.json}` | rewritten in place, same date-named files |
| `04_tools/price_ledger/OFFERED_ROWS.csv` | rebuilt with the two columns |
| `04_tools/price_ledger/_u26_delivery_parity.py` | new — row-for-row parity check (the no-loss proof) |
| `04_tools/price_ledger/_u26_delivery_mutation.py`, `_u26_delivery_mutation_show.py` | new — the mutation check and its reader |
| `04_tools/price_ledger/_u26_delivery_before_after.py` | new — reads both outputs back from disk and compares |

Backups: `*.bak_20261007T081251Z_before_delivery_col` next to each rewritten file.

**Not changed:** the evidence rules (`market_observation.js`, `comparable.js`), the exclusion
codes, `RETIRED_LOADERS`, the `crossref` + `crossref_grade` reconciliation, and the 4 red checks.

---

## 8. Commit

One commit on `cursor/2026-10-07-universe-u26-market-harvest`, carrying the change, its
outputs (the coverage files, the stage/evidence JSON, the mutation evidence) and this report.
A commit cannot contain its own hash or diff stat without churning on every amend, so both are
in the run output and the reply, not here:

```
git rev-parse HEAD
git diff --stat 730279ea04be2202eeacad8a06e5dbb7c4bf2806..HEAD
```

The large line count in `OFFERED_ROWS.csv` is the two new CSV columns shifting every line,
not a data change: the row count (5,287 lines) and the `obs_id` order are identical to the
backup, and the ledger parity check confirms every pre-existing value is unchanged.

---

## 9. Final line

**Adding the delivery basis did not change the answer for UK: no.** The ledger now carries what
each page said about carriage, and the field genuinely decides eligibility — the wiring-proof
mutation proves it — but no harvested UK page states that its price includes delivery, so no UK
row becomes eligible and the market stays at 0 usable rows. The one real figure that moved is the
label: UK no longer reads `sufficient` on 79 raw rows that were all excluded, because sufficiency
is now counted on usable rows. The exclusion that still blocks the rest is
`DELIVERY_BASIS_NOT_STATED`.

# UK KS £10 policy scope — 2026-10-07

## Verdict

Live KS delivery page still names **only** filter / clutch / exhaust examples for the UK mainland **£10** minimum. Of **67** KS `exact_oem` rows that still lacked `delivery_cost`, **1** matched that list (`PIPE; EXH`). Wired that one row. Wider UK eligible moved **17 → 18** offers (**12 → 13** PNs). Focus cut stays **4**. Body panels, brake rotors, leaf springs, sensors, etc. stay unwired.

## Live page (re-read 2026-10-07)

URL: https://www.ks-international.com/delivery-information  
Saved HTML: `01_data/90_INBOX/_uk_ks_delivery_info_20261007.html`  
Plain extract: `01_data/90_INBOX/_uk_ks_delivery_info_20261007_text.txt`

### UK Mainland — product classes named for the £10 minimum

Exact sentence (encoding on page shows `£` as a special char; amount is **10.00** GBP):

> There is a minimum charge of UK Pounds £10.00 e.g. Filter kits, clutch kit, exhaust muffler, tail pipe etc

**Every product class named in that sentence:**

| # | Named class (as printed) | How we treat it in the ledger |
|---:|---|---|
| 1 | Filter kits | Any filter family / description containing FILTER |
| 2 | clutch kit | Clutch kit / disc / cover / pressure plate / release bearing |
| 3 | exhaust muffler | Exhaust / muffler / silencer |
| 4 | tail pipe | Tail pipe / exhaust pipe (incl. Isuzu EPC `PIPE; EXH`) |

The trailing **etc** is treated as “more of these same classes,” not as a licence to invent body or brake-disc rates.

### Explicitly **not** the £10 minimum (same page)

| Sentence | Named examples | Action |
|---|---|---|
| “There will be an additional charge for most boxed body panels…” | Bumper, Door, Front panel, Grilles | **Do not** wire £10 |
| “Large/Heavy Items: We adjust carriage charges…” | Rear springs £15–£20; Gear boxes from £50 | **Do not** wire £10 |

Isle of Wight / Highlands / NI sections mention bumpers, exhausts, wings, leaf springs at **other** night-freight rates — those are **not** the UK mainland £10 rule and were not used to stretch mainland wiring.

## Compare to the 67 KS `exact_oem` without cost

Ledger: U29b `price_observations.parquet`  
KS host `www.ks-international.com`, `match_method=exact_oem`, `delivery_cost_amount` blank: **67** rows / **53** PNs (all already `vat=excl`).

| Outcome | Rows | Notes |
|---|---:|---|
| Newly wired (£10 + `delivery_included=no`) | **1** | `f9cefffef16de794` / PN `8983682091` / desc `PIPE; EXH` / loader `ks_gen` |
| Left blank (honest skip) | **66** | Not named for £10 |

Skipped bucket (description / family):

| Bucket | Rows |
|---|---:|
| Body-panel style (bumper, grille, fender, panel…) | 12 |
| Brake rotor / disc | 5 |
| Heavy leaf spring (page £15–£20) | 1 |
| Other unnamed (EGR, injectors, sensors, turbo, bearing kits, lamps, DPD, driveshaft, generator, flywheel, sensor rotors, …) | 48 |

No filter or clutch rows remained in the 67 — those were filled in the earlier wider pass.

## Wire applied

| Field | Value |
|---|---|
| `delivery_included` | `no` |
| `delivery_cost_amount` | `10` |
| `delivery_cost_currency` | `GBP` |
| `delivery_note` | Live KS quote citing filter / clutch / muffler / tail pipe |

Backup:  
`C:\Users\jerom\Desktop\claude\_worktrees\ISZE_u29b\01_data\00_derived\price_observations.parquet.bak_20261007T155629Z_before_ks_wider_10`

Matcher update (EPC exhaust pipe):  
`01_data/91_build/_uk_wider_eligible_scan_20261007.py` — `EXHAUST_RE` now also accepts `PIPE; EXH` / `EXH; PIPE`. Still rejects body / rotor / spring.

## Wider coverage rebuild

```text
python 01_data/91_build/build_market_data_gap_coverage_20261007.py --also-uk-exact
```

| Cut | Before | After |
|---|---:|---:|
| Wider UK `exact_oem` eligible **offers** | **17** | **18** |
| Wider eligible **PNs** | **12** | **13** |
| Of which outside focus (oil filter + brake pad) | 13 | **14** |
| Focus eligible (unchanged) | 4 | **4** |
| KS exact still without cost | 67 | **66** |

New eligible PN: **8983682091** (`PIPE; EXH`, no PMS family on the worklist).

Metrics:  
`01_data/00_derived/market_data_gap_coverage_uk_wider_exact_20261007.metrics.json`  
(also under the U29b worktree derived folder)

## Not done / not invented

- No £10 on body panels, grilles, bumpers, doors, front panels.
- No £10 on brake rotors / discs.
- No £10 on leaf springs (page names £15–£20).
- No TMC delivery invent.
- No `category_only` → `exact_oem`.
- Board HTML rebuilt to focus 4 / wider **18** (banner + `universe_board_state.json`).

# UK wider eligible scan — 2026-10-07

## Verdict

Focus report stays at **4** eligible UK offers (brake pad + oil filter only).  
Wider UK `exact_oem` report is **17** eligible offers on **12** part numbers (4 focus + **13** outside). Still below the 50-row bar. Portugal untouched. No invented TMC rates, no body-panel £10, no `category_only` upgrades.

## Counts

| Cut | Eligible offers | Eligible PNs | Notes |
|---|---:|---:|---|
| Focus (`brake_pad` + `oil_filter`) | **4** | 2 | Unchanged vs prior evening |
| Wider UK `exact_oem` (all families) | **17** | 12 | New second report |
| Of which outside focus | **13** | 10 | Unlocked by KS £10 policy fill on filter/clutch rows |
| Ledger UK rows | 1,111 | — | After retired loaders removed for evidence: 217 exact_oem |
| UK `exact_oem` before patch with delivery+tax ready | 4 | — | All already in focus |
| KS `exact_oem` patched this pass | **13** | — | Policy-matched only |

### Wider eligible by family (offers)

| Family | Offers |
|---|---:|
| air_filter | 7 |
| fuel_filter | 3 |
| oil_filter | 2 (focus) |
| brake_pad | 2 (focus) |
| clutch_pressure_plate | 1 |
| blower_filter | 1 |
| unlisted PN (desc: FILTER ASM; FUEL) | 1 |

Billed euros of the 12 eligible PNs (all-market size from the worklist, not a UK-only euro): **€3.65M**.

## What was scanned

Worktree ledger:

`C:\Users\jerom\Desktop\claude\_worktrees\ISZE_u29b\01_data\00_derived\price_observations.parquet`

- UK rows: 1,111  
- `exact_oem`: 223 (217 after dropping retired loaders)  
- Already `delivery_included` + cost + VAT excl/incl: **4** (all focus)  
- Outside focus with that triple already set: **0** before this patch  

## KS £10 policy (live text)

Live page https://www.ks-international.com/delivery-information (fetched 2026-10-07):

> There is a minimum charge of UK Pounds £10.00 e.g. Filter kits, clutch kit, exhaust muffler, tail pipe etc  
> There will be an additional charge for most boxed body panels, e.g. Bumper, Door, Front panel, Grilles etc

Applied **only** where family or listing text matches filter / clutch / exhaust.  
**Not** applied to brake rotors, body panels, or other “other” classes (67 KS exact_oem left without £10). Brake-pad focus rows already carried £10 from the earlier focus fill; this pass did not re-open that rule.

Patch: `delivery_included=no`, `delivery_cost_amount=10`, `delivery_cost_currency=GBP`, note citing the live quote.  
Backup: `price_observations.parquet.bak_20261007T153455Z_before_ks_wider_10`

## Coverage builder change

File (worktree): `01_data/91_build/build_market_data_gap_coverage_20261007.py`

- Default focus report unchanged (`brake_pad`, `oil_filter`).  
- Optional `--families a,b,c` overrides focus families for the main CSV/metrics.  
- Optional `--also-uk-exact` writes a **second** report without touching the focus files:

```text
python 01_data/91_build/build_market_data_gap_coverage_20261007.py --also-uk-exact
```

Scan/patch helper:

`01_data/91_build/_uk_wider_eligible_scan_20261007.py`

## Outputs

| File | Role |
|---|---|
| `01_data/00_derived/market_data_gap_coverage_20261007.metrics.json` | Focus: UK eligible **4** |
| `01_data/00_derived/market_data_gap_coverage_uk_wider_exact_20261007.metrics.json` | Wider: UK eligible **17** |
| `01_data/00_derived/market_data_gap_coverage_uk_wider_exact_20261007.csv` | Row-level wider evidence |
| `01_data/91_build/_uk_wider_eligible_scan_20261007.json` | Pre/post patch ledger scan |

Absolute paths (worktree):

`C:\Users\jerom\Desktop\claude\_worktrees\ISZE_u29b\01_data\00_derived\market_data_gap_coverage_uk_wider_exact_20261007.metrics.json`

`C:\Users\jerom\Desktop\claude\_worktrees\ISZE_u29b\01_data\00_derived\market_data_gap_coverage_20261007.metrics.json`

## Why wider is 17 not “all filters”

Most UK `exact_oem` still die on `DELIVERY_BASIS_NOT_STATED` (191) — Eucon survey, TMC without a published under-£150 £ amount, Omega, etc. TMC still has no inventable flat carriage; VAT rate still missing on those PDPs. The 54 focus `category_only` KS walls are outside this wider cut by design (`exact_oem` only).

## How to surface on the board (when you say rebuild)

Focus banner today still says competitor shop eligible = **4**. To show the growth path without pretending focus is fixed:

1. Keep the focus metrics file as the official focus bar (4 / still << 50).  
2. Point the market-gap banner (or a second line) at the wider metrics: **17** UK `exact_oem` eligible (12 PNs), of which 13 are outside oil filter + brake pad — air / fuel / blower filters + one clutch pressure plate.  
3. Rebuild `02_dashboards/_build/build_universe_board.py` so `MARKET_GAP_NOTICE_HTML` cites this note and the wider metrics path. Do **not** silently change the focus sufficiency status; wider is a second count.  
4. INTERNAL AIM wire today only hooks the 2 focus PNs — widening that wire is a separate ask (more case hooks / real_feeds), not done here.

## Not invented

- No £10 on body panels or brake rotors.  
- No TMC delivery £.  
- No `category_only` → `exact_oem`.  
- Focus CSV/metrics still report **4**.  
- Board HTML not rebuilt (needs an explicit rebuild).

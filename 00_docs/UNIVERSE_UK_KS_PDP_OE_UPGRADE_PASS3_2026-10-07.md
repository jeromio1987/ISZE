# UK KS PDP OE upgrade — Pass 3 — 2026-10-07

## Verdict

**40 of 40** remaining filter / clutch / exhaust KS PDPs printed the linked Isuzu part number under **OE Equivalent Part Number** (also JSON-LD). **78** ledger rows upgraded `category_only` → `exact_oem` (66 primary + 12 same-SKU extras). Wider UK `exact_oem` eligible: **83 → 151** offers (**25 → 38** PNs). Focus (oil filter + brake pad) stayed **47** (new rows are clutch / exhaust / non-focus filter). Board / INTERNAL re-wired after this note (151 offers / 38 case hooks).

## Method

Pass 1/2 filled 25 filter SKUs (55 rows → wider 83 / 25 PNs). Pass 3 takes remaining UK KS `category_only` rows in **filter / clutch / exhaust** (KS £10 mainland classes), excluding the 25 already upgraded SKUs. Cap **40** distinct `competitor_pn`. Prefer clutch and exhaust (crowded out of the first 25), then remaining filters by £.

Ledger: `C:\Users\jerom\Desktop\claude\_worktrees\ISZE_u29b\01_data\00_derived\price_observations.parquet`

£10 delivery + VAT excl only for filter / clutch / muffler / tail pipe. Ten exhaust-adjacent PDPs (exhaust brake / gasket / camshaft / temperature sensor) were upgraded to `exact_oem` on OE evidence but **not** wired £10 — out of live KS policy. No body / rotor / spring wired.

## Counts

| Metric | Count |
|---|---:|
| PDPs / SKUs checked | **40** |
| Upgrades (OE on PDP) | **40** |
| Rejects | **0** |
| Ledger rows patched (primary) | **66** |
| Same-SKU extras | **12** |
| Ledger rows patched (total) | **78** |
| Distinct KS SKUs upgraded | **40** |
| Distinct Isuzu PNs touched | **29** |
| SKUs with £10 wire | **30** |
| SKUs OE-upgraded without £10 | **10** |

Family mix checked/upgraded: clutch=11, exhaust=13, filter=16

### Candidates checked

| # | KS SKU | Candidate Isuzu PN | £ excl | Family | £10 | Verdict |
|---:|---|---|---:|---|---|---|
| 1 | `0013647` | `8981698261` | 375.00 | clutch | Y | upgrade_exact_oem |
| 2 | `0012213G` | `1313100120` | 325.00 | clutch | Y | upgrade_exact_oem |
| 3 | `0012216G` | `8972553130` | 295.00 | clutch | Y | upgrade_exact_oem |
| 4 | `0001232G` | `5876101040` | 250.00 | clutch | Y | upgrade_exact_oem |
| 5 | `0012216` | `8972553130` | 195.00 | clutch | Y | upgrade_exact_oem |
| 6 | `0012213K` | `1313100120` | 195.00 | clutch | Y | upgrade_exact_oem |
| 7 | `0001238` | `1313100120` | 90.00 | clutch | Y | upgrade_exact_oem |
| 8 | `0703981` | `8979466221` | 70.00 | clutch | Y | upgrade_exact_oem |
| 9 | `0013731` | `8981698261` | 65.00 | clutch | Y | upgrade_exact_oem |
| 10 | `0013563` | `8979490060` | 40.00 | clutch | Y | upgrade_exact_oem |
| 11 | `0704352K` | `8979466261` | 25.00 | clutch | Y | upgrade_exact_oem |
| 12 | `0707740G` | `8983682091` | 1675.00 | exhaust | Y | upgrade_exact_oem |
| 13 | `0707741G` | `8983656821` | 215.00 | exhaust | Y | upgrade_exact_oem |
| 14 | `0707633G` | `8982476961` | 8.00 | exhaust | Y | upgrade_exact_oem |
| 15 | `0013683` | `8975042510` | 795.00 | exhaust | N | upgrade_exact_oem |
| 16 | `0013738` | `8983840201` | 650.00 | exhaust | N | upgrade_exact_oem |
| 17 | `0013181` | `8982582660` | 550.00 | exhaust | N | upgrade_exact_oem |
| 18 | `0013000` | `8982582670` | 515.00 | exhaust | N | upgrade_exact_oem |
| 19 | `0707631G` | `8983982341` | 220.00 | exhaust | N | upgrade_exact_oem |
| 20 | `0707731G` | `8975449280` | 55.00 | exhaust | N | upgrade_exact_oem |
| 21 | `0012574` | `1221160400` | 10.00 | exhaust | N | upgrade_exact_oem |
| 22 | `0707683G` | `8982480882` | 7.50 | exhaust | N | upgrade_exact_oem |
| 23 | `0012575` | `8973731080` | 6.00 | exhaust | N | upgrade_exact_oem |
| 24 | `0011758` | `8972630520` | 4.00 | exhaust | N | upgrade_exact_oem |
| 25 | `0013132` | `8980714220` | 85.00 | filter | Y | upgrade_exact_oem |
| 26 | `0013133` | `8980714220` | 85.00 | filter | Y | upgrade_exact_oem |
| 27 | `0013132K` | `8980714220` | 75.00 | filter | Y | upgrade_exact_oem |
| 28 | `0013133K` | `8980714220` | 75.00 | filter | Y | upgrade_exact_oem |
| 29 | `0012514` | `8980714210` | 60.00 | filter | Y | upgrade_exact_oem |
| 30 | `0013130G` | `8970622940` | 60.00 | filter | Y | upgrade_exact_oem |
| 31 | `0011765` | `8970622940` | 55.00 | filter | Y | upgrade_exact_oem |
| 32 | `0013723` | `8976739570` | 50.00 | filter | Y | upgrade_exact_oem |
| 33 | `0013130K` | `8970622940` | 40.00 | filter | Y | upgrade_exact_oem |
| 34 | `0012513` | `8980714220` | 35.00 | filter | Y | upgrade_exact_oem |
| 35 | `0013723K` | `8976739570` | 35.00 | filter | Y | upgrade_exact_oem |
| 36 | `0012514K` | `8980714210` | 35.00 | filter | Y | upgrade_exact_oem |
| 37 | `0707723G` | `8974995480` | 30.00 | filter | Y | upgrade_exact_oem |
| 38 | `0013646` | `8983214130` | 30.00 | filter | Y | upgrade_exact_oem |
| 39 | `0013026` | `8980959830` | 30.00 | filter | Y | upgrade_exact_oem |
| 40 | `0011765K` | `8970622940` | 30.00 | filter | Y | upgrade_exact_oem |

## Upgrades (evidence samples)

| KS SKU | Isuzu PN | Family | Where | Quote | £10 |
|---|---|---|---|---|---|
| `0013647` | `8981698261` | clutch | attr:OE Equivalent Part Number | `nt Part Number: 8982831940, 8983753330, 8981698261` | Y |
| `0012213G` | `1313100120` | clutch | attr:OE Equivalent Part Number | `nt Part Number: 8970388312, 8973677950, 1313100120` | Y |
| `0012216G` | `8972553130` | clutch | attr:OE Equivalent Part Number | `er: 897255313, 89804009300, 8980370040, 8972553130` | Y |
| `0001232G` | `5876101040` | clutch | attr:OE Equivalent Part Number | `er: 1098201150, 8970388312, 5876100810, 5876101040, 8971735951` | Y |
| `0012216` | `8972553130` | clutch | attr:OE Equivalent Part Number | `er: 897255313, 89804009300, 8980370040, 8972553130` | Y |
| `0012213K` | `1313100120` | clutch | attr:OE Equivalent Part Number | `nt Part Number: 8970388312, 8973677950, 1313100120` | Y |
| `0001238` | `1313100120` | clutch | attr:OE Equivalent Part Number | `OE Equivalent Part Number: 1313100120` | Y |
| `0703981` | `8979466221` | clutch | attr:OE Equivalent Part Number | `OE Equivalent Part Number: 8979466221` | Y |
| `0013731` | `8981698261` | clutch | attr:OE Equivalent Part Number | `OE Equivalent Part Number: 8981698261` | Y |
| `0013563` | `8979490060` | clutch | attr:OE Equivalent Part Number | `OE Equivalent Part Number: 8979490060` | Y |
| `0704352K` | `8979466261` | clutch | attr:OE Equivalent Part Number | `OE Equivalent Part Number: 8979466261` | Y |
| `0707740G` | `8983682091` | exhaust | attr:OE Equivalent Part Number | `OE Equivalent Part Number: 8983682091` | Y |
| `0707741G` | `8983656821` | exhaust | attr:OE Equivalent Part Number | `OE Equivalent Part Number: 8983656821` | Y |
| `0707633G` | `8982476961` | exhaust | attr:OE Equivalent Part Number | `OE Equivalent Part Number: 8982476961` | Y |
| `0013683` | `8975042510` | exhaust | attr:OE Equivalent Part Number | `OE Equivalent Part Number: 8975042510` | N |
| `0013738` | `8983840201` | exhaust | attr:OE Equivalent Part Number | `OE Equivalent Part Number: 8983840201` | N |
| `0013181` | `8982582660` | exhaust | attr:OE Equivalent Part Number | `OE Equivalent Part Number: 8982582660` | N |
| `0013000` | `8982582670` | exhaust | attr:OE Equivalent Part Number | `OE Equivalent Part Number: 8982582670` | N |
| `0707631G` | `8983982341` | exhaust | attr:OE Equivalent Part Number | `OE Equivalent Part Number: 8983982341` | N |
| `0707731G` | `8975449280` | exhaust | attr:OE Equivalent Part Number | `OE Equivalent Part Number: 8975449280` | N |
| `0012574` | `1221160400` | exhaust | attr:OE Equivalent Part Number | `OE Equivalent Part Number: 1221160400` | N |
| `0707683G` | `8982480882` | exhaust | attr:OE Equivalent Part Number | `OE Equivalent Part Number: 8982480882` | N |
| `0012575` | `8973731080` | exhaust | attr:OE Equivalent Part Number | `OE Equivalent Part Number: 8973731080` | N |
| `0011758` | `8972630520` | exhaust | attr:OE Equivalent Part Number | `OE Equivalent Part Number: 8972630520` | N |
| `0013132` | `8980714220` | filter | attr:OE Equivalent Part Number | `OE Equivalent Part Number: 8980714220, 8980714210, 8971482700, 8980370110` | Y |
| `0013133` | `8980714220` | filter | attr:OE Equivalent Part Number | `OE Equivalent Part Number: 8980714220, 8980714210, 8943910492, 8980370110` | Y |
| `0013132K` | `8980714220` | filter | attr:OE Equivalent Part Number | `OE Equivalent Part Number: 8980714220, 8980714210, 8971482700, 8980370110` | Y |
| `0013133K` | `8980714220` | filter | attr:OE Equivalent Part Number | `OE Equivalent Part Number: 8980714220, 8980714210, 8943910492, 8980370110` | Y |
| `0012514` | `8980714210` | filter | attr:OE Equivalent Part Number | `OE Equivalent Part Number: 8980714210` | Y |
| `0013130G` | `8970622940` | filter | attr:OE Equivalent Part Number | `OE Equivalent Part Number: 8970622940, 8980370110, 8971482700` | Y |
| `0011765` | `8970622940` | filter | attr:OE Equivalent Part Number | `OE Equivalent Part Number: 8970622940` | Y |
| `0013723` | `8976739570` | filter | attr:OE Equivalent Part Number | `OE Equivalent Part Number: 8976739570` | Y |
| `0013130K` | `8970622940` | filter | attr:OE Equivalent Part Number | `OE Equivalent Part Number: 8970622940, 8980370110, 8971482700` | Y |
| `0012513` | `8980714220` | filter | attr:OE Equivalent Part Number | `OE Equivalent Part Number: 8980714220` | Y |
| `0013723K` | `8976739570` | filter | attr:OE Equivalent Part Number | `OE Equivalent Part Number: 8976739570` | Y |
| `0012514K` | `8980714210` | filter | attr:OE Equivalent Part Number | `OE Equivalent Part Number: 8980714210` | Y |
| `0707723G` | `8974995480` | filter | attr:OE Equivalent Part Number | `OE Equivalent Part Number: 8974995480` | Y |
| `0013646` | `8983214130` | filter | attr:OE Equivalent Part Number | `OE Equivalent Part Number: 8983214130` | Y |
| `0013026` | `8980959830` | filter | attr:OE Equivalent Part Number | `OE Equivalent Part Number: 8980959830` | Y |
| `0011765K` | `8970622940` | filter | attr:OE Equivalent Part Number | `OE Equivalent Part Number: 8970622940` | Y |

### Same-SKU extras

| KS SKU | Extra Isuzu PN(s) | Extra rows |
|---|---|---:|
| `0013132` | `8980714210` | 2 |
| `0013132K` | `8980714210` | 2 |
| `0013133` | `8980714210` | 2 |
| `0013133K` | `8980714210` | 2 |
| `0013647` | `8982831940`, `8983753330` | 4 |

## Rejects

- (none) — 40/40 OE attribute hit

No invent: only PNs on the PDP OE attribute / JSON-LD upgraded.

## Eligible before / after

Coverage rebuild (from U29b worktree so ledger + node runner resolve correctly):

```text
python 01_data/91_build/build_market_data_gap_coverage_20261007.py --also-uk-exact
```

| Cut | Before (post pass1/2) | After pass3 |
|---|---:|---:|
| Wider UK `exact_oem` eligible **offers** | **83** | **151** |
| Wider eligible **PNs** | **25** | **38** |
| Delta offers | | **+68** |
| Delta PNs | | **+13** |
| Focus (oil filter + brake pad) | **47** | **47** |
| Outside focus | | **104** |

**Parent note:** Pass3 added **+68** wider eligible offers beyond the pass1/2 total of 83. Sibling wire-83 / INTERNAL finished (or finishes) against **83** must be **re-wired** to pick up **151**.

Metrics (U29b + copied to main derived):

`C:\Users\jerom\Desktop\claude\_worktrees\ISZE_u29b\01_data\00_derived\market_data_gap_coverage_uk_wider_exact_20261007.metrics.json`

`C:\Users\jerom\Desktop\claude\ISZE\01_data\00_derived\market_data_gap_coverage_uk_wider_exact_20261007.metrics.json`

## Backups

- `C:\Users\jerom\Desktop\claude\_worktrees\ISZE_u29b\01_data\00_derived\price_observations.parquet.bak_20261007T162448Z_before_ks_pdp_oe_pass3`

## Artefacts

| Object | Path |
|---|---|
| Candidate list | `C:\Users\jerom\Desktop\claude\ISZE\01_data\90_INBOX\_uk_ks_pdp_oe_upgrade_pass3_20261007\pdp_candidates_pass3_20261007.csv` |
| PDP HTML + checks | `C:\Users\jerom\Desktop\claude\ISZE\01_data\90_INBOX\_uk_ks_pdp_oe_upgrade_pass3_20261007` |
| Summary JSON | `C:\Users\jerom\Desktop\claude\ISZE\01_data\90_INBOX\_uk_ks_pdp_oe_upgrade_pass3_20261007\pdp_upgrade_summary_pass3_20261007.json` |
| This note | `C:\Users\jerom\Desktop\claude\ISZE\00_docs\UNIVERSE_UK_KS_PDP_OE_UPGRADE_PASS3_2026-10-07.md` |
| Runner | `C:\Users\jerom\Desktop\claude\ISZE\01_data\91_build\_uk_ks_pdp_oe_upgrade_pass3_20261007.py` |

## Not done

- Focus cut still **47** (under 50). No ACCEPT.
- Board + INTERNAL re-wire to **151**/38 landed (see `UNIVERSE_INTERNAL_ELIGIBLE_WIRE_2026-10-07.md`).


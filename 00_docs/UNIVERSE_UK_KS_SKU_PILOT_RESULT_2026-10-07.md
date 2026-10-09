# UK KS competitor-SKU pilot — result — 2026-10-07

## Verdict

**Accepted `exact_oem`: 0 of 8.** Pivot off Isuzu-PN search (already empty). Competitor/OE SKUs from disk were searched on KS International. One PN had **no SKU bridge**. Thirty-two SKU searches: **30** empty, **2** relevance cards without the Isuzu PN. Nothing appended to the U29b ledger. Wider UK shop eligible stays **17 offers / 12 PNs**.

## Method

1. Pull competitor SKUs for the same eight pilot PNs from graded/Spareto/edges (and note oe_bridge / iam_ks). Prefer `confirmed` / `likely`; if none, try up to five `doubtful` SKUs so “bridge exists, KS miss” is distinguishable from “no bridge”.
2. Dedupe by compact SKU (strip separators), cap **8** searches per PN.
3. Search `https://www.ks-international.com/catalogsearch/result/?q=<competitor SKU>` (not the Isuzu PN).
4. Parse with `site_ks.parse`; open PDP when cards appear.
5. Accept only when the **target Isuzu PN** prints on the search card or PDP (`exact_oem`). Apply KS £10 + VAT excl only for filter/clutch/exhaust (and pads only if carriage can be stated) — **not applied** (zero accepts).
6. Do not invent SKU/OE/£.

## Bridges on disk

| # | Part number | Family | Bridge | Unique SKUs | Usable (confirmed/likely) | SKUs searches run |
|---|---|---|---|---:|---:|---:|
| 1 | 5876150170 | fuel_filter | has_bridge | 25 | 7 | 5 |
| 2 | 1876100934 | fuel_filter | has_bridge | 3 | 0 (doubtful only) | 3 |
| 3 | 1876101132 | air_filter | **no_SKU_bridge** | 0 | 0 | 0 |
| 4 | 8975488420 | blower_filter | has_bridge | 22 | 6 | 6 |
| 5 | 8975425390 | fuel_filter | has_bridge | 1 | 0 (doubtful only) | 1 |
| 6 | 8982120690 | clutch_disc | has_bridge | 45 | 19 | 8 |
| 7 | 8975056801 | brake_pad | has_bridge | 26 | 0 (doubtful only) | 4 |
| 8 | 8978279610 | brake_pad | has_bridge | 33 | 6 | 5 |

Sources checked: `crossref_graded.csv`, `crossref_edges.csv`, `spareto_crossref.csv`, `crossref_spareto_new_edges.csv`, `oe_bridge_coverage.csv`, `iam_ks_price_gap.csv`.

Example usable bridges (not invented — from graded file): `5876150170` → Febi `184132`, Blue Print `ADT32381`, Bosch `F026402115`; `8982120690` → LUK `628331800` / `628334900`, DT `15.00268`; `8978279610` → Textar `2653401`, Delphi `LP3906`, Brembo `P34014`.

## KS outcomes

| Outcome | Count |
|---|---:|
| SKU searches after dedupe/cap | **32** |
| No product cards | **30** |
| Cards but target Isuzu PN not on card/PDP | **2** |
| Accepted exact_oem | **0** |
| no_SKU_bridge (no search) | **1** PN (`1876101132`) |

### The two non-empty searches (rejected)

| Isuzu PN | SKU searched | KS cards | Why rejected |
|---|---|---:|---|
| 8975488420 | `172065` (Febi, confirmed) | 1 | Card is “ENGINE FAN BELT…” KS sku `0707276`; no `8975488420` on card or PDP |
| 8978279610 | `P 34 014` (Brembo, likely) | 6 | Unrelated cups/joints/plugs; no `8978279610` on cards; PDP PNs were other Isuzu numbers / noise |

No £10 delivery fill applied (nothing to wire).

## Ledger / coverage

| Step | Result |
|---|---|
| Staging CSV for accepted rows | Header only (0 data rows) |
| Backup + append to u29b `price_observations.parquet` | **Not run** (nothing to append) |
| Wider rebuild `--also-uk-exact` | Re-run; eligible unchanged |

| Metric | Before | After |
|---|---:|---:|
| Wider UK eligible offers | **17** | **17** |
| Wider UK eligible PNs | **12** | **12** |

## What this means

Competitor-SKU search on KS for these eight high-euro parts does not unlock OE-on-card offers. Either KS does not list the IAM numbers we hold, or the few hits are relevance noise. Stopped at these eight PNs’ SKU attempts — did not invent SKUs and did not widen to the remaining harvest list with the same method.

## Paths

| Artefact | Path |
|---|---|
| This note | `C:\Users\jerom\Desktop\claude\ISZE\00_docs\UNIVERSE_UK_KS_SKU_PILOT_RESULT_2026-10-07.md` |
| Bridge extract | `C:\Users\jerom\Desktop\claude\ISZE\01_data\90_INBOX\_uk_ks_sku_pilot_20261007\sku_bridges_20261007.json` |
| Search queue | `C:\Users\jerom\Desktop\claude\ISZE\01_data\90_INBOX\_uk_ks_sku_pilot_20261007\sku_search_queue_20261007.csv` |
| Fetch summary | `C:\Users\jerom\Desktop\claude\ISZE\01_data\90_INBOX\_uk_ks_sku_pilot_20261007\sku_pilot_fetch_summary_20261007.json` |
| Reject log | `C:\Users\jerom\Desktop\claude\ISZE\01_data\90_INBOX\_uk_ks_sku_pilot_20261007\sku_pilot_rejects_20261007.csv` |
| Empty staging | `C:\Users\jerom\Desktop\claude\ISZE\01_data\90_INBOX\_uk_ks_sku_pilot_20261007\staging_exact_oem_accepted_sku_pilot_20261007.csv` |
| Eligible before/after | `C:\Users\jerom\Desktop\claude\ISZE\01_data\90_INBOX\_uk_ks_sku_pilot_20261007\sku_pilot_eligible_before_after_20261007.json` |
| Wider metrics | `C:\Users\jerom\Desktop\claude\_worktrees\ISZE_u29b\01_data\00_derived\market_data_gap_coverage_uk_wider_exact_20261007.metrics.json` |
| U29b ledger (unchanged) | `C:\Users\jerom\Desktop\claude\_worktrees\ISZE_u29b\01_data\00_derived\price_observations.parquet` |
| Prior Isuzu-PN pilot (0/8) | `C:\Users\jerom\Desktop\claude\ISZE\00_docs\UNIVERSE_UK_KS_PILOT_8PN_RESULT_2026-10-07.md` |

## Honesty

- No invented SKU / OE / £.
- `1876101132` recorded as **no_SKU_bridge** (zero rows in graded/edges/spareto/oe_bridge/iam_ks).
- No `category_only` written as ledger upgrades.
- No delivery £10 applied.
- Pilot stopped at these eight PNs’ SKU attempts.

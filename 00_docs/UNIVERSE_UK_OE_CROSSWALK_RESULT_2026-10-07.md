# UK OE / competitor crosswalk hunt — 2026-10-07

## Verdict

**Zero upgrades.** UK eligible shop offers stay at **4**. The 54 KS `category_only` rows stay `PRODUCT_MATCH_UNRESOLVED`. No parquet patch. No forced `exact_oem`. Portugal untouched. No TMC delivery invent.

## What the 54 are

UK focus-family ledger rows (brake pad / oil filter) with delivery £10 + VAT excl already set, `match_method=category_only`, loader `ks`, killed by `PRODUCT_MATCH_UNRESOLVED` in coverage metrics.

| Metric | Value |
|---|---:|
| Blocked rows | **54** |
| Distinct Isuzu PNs | **15** |
| Distinct KS SKUs (`competitor_pn`) | **32** |
| Rows whose own description says “no Isuzu \<PN\> on the card … not a confirmed exact match” | **54 / 54** |

Full list (obs_id / part_no / competitor_pn / url):

`C:\Users\jerom\Desktop\claude\ISZE\01_data\00_derived\_uk_oe_crosswalk_probe_20261007\blocked_focus.csv`

Worktree source parquet (unchanged):

`C:\Users\jerom\Desktop\claude\_worktrees\ISZE_u29b\01_data\00_derived\price_observations.parquet`

### Distinct Isuzu PN × KS SKU pairs (32)

| Isuzu PN | KS SKU(s) | n rows |
|---|---|---:|
| 8970497081 | 0001011, 0078955 | 2 |
| 8970947100 | 0001017, 0001017J | 2 |
| 8971138880 | 0007914, 0007914J | 2 |
| 8971482800 | 0001022, 0001022K | 2 |
| 8971679720 | 0078879 | 1 |
| 8973017520 | 0001036, 0013134, 0013134K | 3 |
| 8973099270 | 0011227K | 1 |
| 8973299110 | 0001004, 0001004K, 0012878, 0012878K, 0012879, 0012879K | 6 |
| 8973587200 | 0079084 | 1 |
| 8975439050 | 0013721, 0013721K | 6 |
| 8975546610 | 0707506G, 0707506K | 6 |
| 8980188580 | 0011764, 0011764K, 0012884, 0012884K | 12 |
| 8981240801 | 0703831 | 1 |
| 8981650710 | 0701999 | 3 |
| 8982705240 | 0013561, 0013561G | 6 |

`competitor_brand` is blank on all 54. URL pattern is always KS search for the Isuzu number, e.g. `https://www.ks-international.com/catalogsearch/result/?q=<PN>`.

## Crosswalks searched (honest pair = same Isuzu PN + same KS SKU)

| Source | Path | Result |
|---|---|---|
| KS graded crossref seed | `04_tools/price_ledger/KS_CROSSREF_ROWS.csv` | **0** overlap (only SB-5302 / SB-5361 for unrelated ball-joint PNs) |
| AIM edges | `04_tools/aftermarket_intelligence/state/crossref_edges.csv` | PN hits exist; **0** KS-SKU-as-`competitor_pn`; **0** honest pairs |
| AIM match index | `…/match_index.csv` | same — **0** honest pairs |
| AIM graded | `…/crossref_graded.csv` | same — **0** honest pairs |
| Spareto crossref | `…/spareto_crossref.csv`, `spareto_crossref_per_part.csv`, `crossref_spareto_new_edges.csv` | PN hits; **0** KS SKU hits; **0** honest pairs |
| Spareto recon HTML | `04_tools/delegation/parsers/_recon_crossref/spareto/oe_*.html` | HTML exists for 8975546610 + 8982705240; **neither** embeds the blocked KS SKUs |
| OE bridge coverage | `01_data/00_derived/oe_bridge_coverage.csv` | **0** of the 15 PNs |
| BVP crossref | `01_data/00_derived/genuine_bvp_crossref.csv` | 11 PN rows; **0** cells equal a blocked KS SKU |
| IAM KS price gap | `01_data/00_derived/iam_ks_price_gap.csv` | PN hits; **0** KS SKU cells; **0** honest pairs |
| Lost-sales competitor PN | `01_data/00_derived/lost_sales_competitor_pn.csv` | **0** |
| Monday PN crosswalk | `01_data/00_derived/monday_pn_opportunity_crosswalk_20260914.csv` | 1 PN mention; **0** SKU; **0** honest pairs |
| Eucon rows in parquet | `price_observations` loaders `eucon*` | crossref/exact on some same PNs, but **competitor_pn never equals** a blocked KS SKU |
| U26 bridge harvest | `04_tools/price_ledger/_u26_e_bridge_20261007.json` | some PNs appear; **0** blocked KS SKUs |
| OFFERED_ROWS | `04_tools/price_ledger/OFFERED_ROWS.csv` | other loaders have `exact_oem` on some of these PNs (Amayama / TMC / Geparden) — **different offers**, not a bridge that upgrades these KS SKU rows; **0** exact/crossref rows that carry the same KS SKU |
| epc_decode_worklist | `01_data/00_derived/epc_decode_worklist.csv` | size / family worklist only — not an OE↔IAM map |

Probe evidence JSON:

`C:\Users\jerom\Desktop\claude\ISZE\01_data\00_derived\_uk_oe_crosswalk_probe_20261007\deep_findings.json`

## Why `category_only` → `exact_oem` would be dishonest here

1. Every one of the 54 descriptions already records that the Isuzu number is **not on the KS card** and the hit is relevance-only.
2. Coverage only accepts `match.basis = exact_part_number` (ledger `exact_oem`). Even a graded IAM brand↔OE edge would need an **accepted** equivalence rule change — and we do not have a KS-SKU↔Isuzu-PN edge on disk anyway.
3. `KS_CROSSREF_ROWS.csv` is the only approved KS crossref seed; it does not cover these 54.

## Ledger / coverage action

| Action | Done? |
|---|---|
| Patch `match_method` / `competitor_pn` on u29b parquet | **No** (nothing honest to write) |
| Rebuild `build_market_data_gap_coverage_20261007.py` | **Skipped** — no input change; last metrics already current |

## Eligible before / after

| Metric (UK) | Before | After |
|---|---:|---:|
| eligible_rows / usable_rows | **4** | **4** |
| eligible_pns | 2 (`8982705240`, `8975546610`) | **2** (unchanged) |
| PRODUCT_MATCH_UNRESOLVED | 54 | **54** |
| Rows upgraded | — | **0** |

Metrics file (worktree):

`C:\Users\jerom\Desktop\claude\_worktrees\ISZE_u29b\01_data\00_derived\market_data_gap_coverage_20261007.metrics.json`

## What would unlock these later (not done here)

- A KS product page (or graded harvest) that **prints the Isuzu OE** on the card → re-parse as `exact_oem`.
- Or an approved bridge file that maps **specific KS SKU → Isuzu PN** with the same confidence bar as `KS_CROSSREF_ROWS.csv` (competitor number search, graded confirmed) — then a deliberate eligibility rule for that graded `crossref`, not a silent rename to `exact_oem`.

## Not invented

No OE invented from relevance. No KS SKU forced to Isuzu. No TMC delivery £. Portugal skipped.

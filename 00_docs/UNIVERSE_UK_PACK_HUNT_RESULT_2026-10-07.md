# UK pack hunt result — 2026-10-07

## Verdict

**Filled pack fields: 0.** UK eligible shop offers stay **4 → 4**. All 22 UK focus rows that still fail `PACK_CONTENTS_UNKNOWN` already have delivery + cost + tax, but none of the live KS product pages (or saved search HTML) state an explicit pack size. Ledger left unchanged. Portugal untouched.

## How PACK_CONTENTS_UNKNOWN is decided

Coverage builder `01_data/91_build/build_market_data_gap_coverage_20261007.py` maps each ledger row into an evidence offer:

1. **`amount_scope`** — `exact_oem` → `per_piece` (OE sellable unit). Other match methods: kit/set words in the title → `per_pack`; otherwise `per_piece`.
2. **`pack`** — filled only by `pack_from_description`, which accepts explicit size text (`set of N` / `pack of N` / `kit of N` / `N pcs` / `N pads`). Family or “PAD KIT” alone never invents a count.
3. Node evidence (`run_u19_ledger_through_evidence_20261007.mjs` → `comparable.js` / `evidence.normalisePack`) refuses with **`PACK_CONTENTS_UNKNOWN`** when:
   - `amount_scope` is not `per_piece` or `per_pack`, or
   - `amount_scope=per_pack` and pack contents are not stated (cannot normalise to a per-piece price).

## Scope hunted

| Item | Count |
|---|---:|
| UK focus rows with `PACK_CONTENTS_UNKNOWN` | **22** |
| Of those with delivery + cost + tax already set | **22** (all KS `category_only`) |
| Unique Isuzu numbers | 6 |
| Unique KS SKUs | 14 |
| Live product pages fetched | 14 |
| Saved A1 search HTML also checked | 6 OE search pages |

All 22 also carry `PRODUCT_MATCH_UNRESOLVED` (search-card relevance only). Filling pack alone would not unlock eligible until match is resolved separately.

## What the pages say (honest)

| Family wording on KS | Explicit piece count? |
|---|---|
| `FRONT BRAKE PAD SET` / `FRONT BRAKE PADS` | **No** — set name only; no “set of 4”, “4 pads”, axle set size |
| `ENGINE FILTER KIT (OIL, AIR, FUEL)` + meta “Includes Air, Oil & Fuel Filter” | **No usable pack size** — names three filter *kinds*, not a homogeneous `N pcs` for per-piece normalisation |
| Cart control `Quantity: 1` | **Ignored** — basket qty, not pack contents |
| JSON-LD Product/Offer | Price/currency only — no `packSize` / `numberOfItems` |

Saved HTML under `01_data/90_INBOX/scrape_targets/_probe/_u26/A1/pages/` (search cards) likewise has no explicit size text.

## What was not filled

No ledger `description` rewrite, no `pack` JSON forced into the coverage stage, no invented pad or filter count from the part family. Hard skip on silence.

## Coverage rebuild

```text
cd C:\Users\jerom\Desktop\claude\_worktrees\ISZE_u29b
python 01_data/91_build/build_market_data_gap_coverage_20261007.py
```

| Metric (UK) | Before | After |
|---|---:|---:|
| eligible_rows / usable_rows | **4** | **4** |
| eligible_pns | 2 | 2 (`8982705240`, `8975546610`) |
| PACK_CONTENTS_UNKNOWN | 22 | **22** |
| PRODUCT_MATCH_UNRESOLVED | 54 | 54 |
| filled pack fields this hunt | — | **0** |

## Paths

- Result note: `C:\Users\jerom\Desktop\claude\_worktrees\ISZE_u29b\00_docs\UNIVERSE_UK_PACK_HUNT_RESULT_2026-10-07.md`
- Live HTML cache: `C:\Users\jerom\Desktop\claude\_worktrees\ISZE_u29b\01_data\90_INBOX\_uk_pack_hunt_20261007\`
- Hunt log: `C:\Users\jerom\Desktop\claude\_worktrees\ISZE_u29b\01_data\90_INBOX\_uk_pack_hunt_20261007\HUNT_LOG.json`
- Metrics: `C:\Users\jerom\Desktop\claude\_worktrees\ISZE_u29b\01_data\00_derived\market_data_gap_coverage_20261007.metrics.json`
- Coverage mapper (pack rule): `C:\Users\jerom\Desktop\claude\_worktrees\ISZE_u29b\01_data\91_build\build_market_data_gap_coverage_20261007.py`
- Evidence refuse: `Isuzu Universe\05_AIM_Universe\src\data\comparable.js` (`PACK_CONTENTS_UNKNOWN`) + `evidence.js` (`normalisePack`)

## Not invented

No pack size from “PAD SET” / “FILTER KIT” alone. No use of cart Quantity. No match upgrade in this pass. No Portugal change.

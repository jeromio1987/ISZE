# UK match / pack unlock result — 2026-10-07

## Verdict

UK eligible shop offers moved **2 → 4** (usable rows still **insufficient** vs the 50 bar). Two KS pad-kit rows that already had delivery £10 + VAT excl unlocked because `exact_oem` is now treated as one OE sellable unit (`amount_scope=per_piece`), not a pack that needs an invented pad count. The 54 `category_only` rows stay blocked — pages say the Isuzu number is not on the card. No TMC delivery £ or VAT % invented. Portugal untouched.

## How the killers are decided

Coverage builder: `01_data/91_build/build_market_data_gap_coverage_20261007.py` maps ledger rows into evidence offers, then Node runs them through Universe evidence (`run_u19_ledger_through_evidence_20261007.mjs` → `comparable.js` / `market_observation.js`).

| Killer | Rule |
|---|---|
| **PRODUCT_MATCH_UNRESOLVED** | Match passes only when `match.basis = exact_part_number` (from ledger `match_method=exact_oem`). `category_only` / `crossref` stay candidates — never accepted without a declared equivalence. |
| **PACK_CONTENTS_UNKNOWN** | `amount_scope=per_pack` with no stated `pack.contents` (or no piece/pack scope). Explicit size text can fill contents; family alone never does. |

## Sample — KS rows with delivery + cost + tax already set (58)

Wired: `delivery_included=no`, `delivery_cost_amount=10` GBP, `vat=excl`.

| Bucket | n | Why blocked |
|---:|---:|---|
| `exact_oem` already eligible (oil filter 8982705240) | 2 | — |
| `exact_oem` pad kit 8975546610 only `PACK_CONTENTS_UNKNOWN` | 2 | Description `PAD KIT; CALIPER,DISC BRK,FRT` was mapped to `per_pack` with null contents |
| `category_only` → `PRODUCT_MATCH_UNRESOLVED` (± pack) | 54 | Listing text: “no Isuzu \<PN\> on the card … not a confirmed exact match”; competitor_pn is a KS SKU |

Sample `category_only` obs_ids (match stays unresolved — not invented):

`1a00973290b2c264`, `c1e31104641bb593`, `27bf61c8e03f1fe6`, `e2078cde9293e33c`, `6ddef4823f8a64c0`, `10c48e5514576672`, `a5e9a52735d41e5e`, `94daad4a5b935472`, `b8ac1f8a63185d81`, `fea3b127386b741a`, `04c00d125628cdc1`, `35bc98369a5b6f16`

Pad-kit obs_ids unlocked this pass:

`21985ab8fba990a7` (ks_am), `60af21d84a7ff389` (ks_gen)

## What was changed (honest only)

1. **Match** — no ledger patch. OE bridge / BVP crossref / `KS_CROSSREF_ROWS.csv` do not confirm the 54 KS SKUs against the searched Isuzu numbers. Upgrading `category_only` → `exact_oem` would be guessing against the page’s own “not on the card” note.
2. **Pack** — no row had explicit size text (`set of N` / `N pads`) in UK focus descriptions or the UK live HTML cache. `pack_from_description` was added for those forms; it filled **0** rows.
3. **Coverage mapper** — for `match_method=exact_oem`, `amount_scope` is `per_piece` (OE PN = sellable unit, including when the OE name is PAD KIT). That is not inventing four pads; it is OE-to-OE kit price on the same part number.

Ledger parquet was **not** rewritten for match/pack. Builder only:

`C:\Users\jerom\Desktop\claude\_worktrees\ISZE_u29b\01_data\91_build\build_market_data_gap_coverage_20261007.py`

## Coverage rebuild

```text
cd C:\Users\jerom\Desktop\claude\_worktrees\ISZE_u29b
python 01_data/91_build/build_market_data_gap_coverage_20261007.py
```

| Metric (UK) | Before | After |
|---|---:|---:|
| eligible_rows / usable_rows | **2** | **4** |
| eligible_pns | 1 (`8982705240`) | **2** (`8982705240`, `8975546610`) |
| billed EUR of eligible PNs (all-market size) | 773,803.72 | **1,180,381.37** |
| PRODUCT_MATCH_UNRESOLVED | 54 | **54** (unchanged) |
| PACK_CONTENTS_UNKNOWN | 33 | **22** (−11 exact_oem kit-name rows no longer forced to per_pack) |
| DELIVERY_COST_NOT_SUPPLIED | 9 | 9 (TMC) |
| TAX_RATE_NOT_STATED | 9 | 9 (TMC) |
| Portugal eligible | 0 | 0 |

Rows unlocked this pass: **2** (both KS `exact_oem` pad kit for 8975546610).

Metrics:

`C:\Users\jerom\Desktop\claude\_worktrees\ISZE_u29b\01_data\00_derived\market_data_gap_coverage_20261007.metrics.json`

## Still blocked (honest)

- **54 KS relevance hits** — need a page that prints the Isuzu number (or a graded crossref on disk), not a SKU-only card.
- **22 pack unknowns** — category kits/sets without an explicit piece count; leave unknown.
- **TMC** — no published mainland under-£150 carriage amount; VAT % not stated (schema says included only). Do not invent.

## Not invented

No match upgraded from silence or relevance. No pack size from “PAD KIT” alone. No TMC delivery £. No UK VAT %. Portugal skipped.

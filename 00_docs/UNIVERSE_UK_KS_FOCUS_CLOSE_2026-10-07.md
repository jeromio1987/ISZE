# UK KS focus close — oil_filter + brake_pad — 2026-10-07

## Verdict

**Focus eligible moved 47 → 58** (bar ≥50 met). Wider UK exact_oem eligible **151 → 162** offers (**38 → 41** PNs). Board / INTERNAL rebuilt to 58/162/41.

## Method

After pass1/2/3, focus (oil filter + brake pad) sat at **47** while wider was **151**. Remaining UK KS focus rows that were still `category_only` (already had VAT excl + delivery £10 from the earlier fill):

- **11** ledger rows / **7** distinct KS SKUs
- Mix: brake_pad **10**, oil_filter **1**

Opened each SKU search → PDP. Upgrade `category_only` → `exact_oem` **only** when the Isuzu PN is printed under **OE Equivalent Part Number** (or clear OE / JSON-LD).

### Delivery policy for this pass

| Family | Rule applied |
|---|---|
| oil_filter | KS mainland **£10** (named on live delivery page) |
| brake_pad | **Do not invent £10** — live page does not name pads (`UNIVERSE_UK_KS_POLICY_SCOPE_2026-10-07.md`). Keep cost only if the earlier focus fill already wired £10 on that row. |

Ledger: `C:\Users\jerom\Desktop\claude\_worktrees\ISZE_u29b\01_data\00_derived\price_observations.parquet`

## Candidates checked

| # | KS SKU | Isuzu PN | Family | £ excl | Had £10 | Verdict |
|---:|---|---|---|---:|---|---|
| 1 | `0707506G` | `8975546610` | brake_pad | 125.00 | Y | upgrade_exact_oem |
| 2 | `0001017` | `8970947100` | brake_pad | 115.00 | Y | upgrade_exact_oem |
| 3 | `0001017J` | `8970947100` | brake_pad | 25.00 | Y | upgrade_exact_oem |
| 4 | `0707506K` | `8975546610` | brake_pad | 15.00 | Y | upgrade_exact_oem |
| 5 | `0007914J` | `8971138880` | brake_pad | 15.00 | Y | upgrade_exact_oem |
| 6 | `0007914` | `8971138880` | brake_pad | 11.00 | Y | upgrade_exact_oem |
| 7 | `0079084` | `8973587200` | oil_filter | 3.00 | Y | upgrade_exact_oem |

## Upgrades (evidence)

| KS SKU | Isuzu PN | Family | Where | Quote | Delivery action |
|---|---|---|---|---|---|
| `0707506G` | `8975546610` | brake_pad | attr:OE Equivalent Part Number | `OE Equivalent Part Number: 8975546610` | keep_existing |
| `0001017` | `8970947100` | brake_pad | attr:OE Equivalent Part Number | `OE Equivalent Part Number: 8970947100` | keep_existing |
| `0001017J` | `8970947100` | brake_pad | attr:OE Equivalent Part Number | `OE Equivalent Part Number: 8970947100` | keep_existing |
| `0707506K` | `8975546610` | brake_pad | attr:OE Equivalent Part Number | `OE Equivalent Part Number: 8975546610` | keep_existing |
| `0007914J` | `8971138880` | brake_pad | attr:OE Equivalent Part Number | `OE Equivalent Part Number: 8971138880` | keep_existing |
| `0007914` | `8971138880` | brake_pad | attr:OE Equivalent Part Number | `OE Equivalent Part Number: 8971138880` | keep_existing |
| `0079084` | `8973587200` | oil_filter | attr:OE Equivalent Part Number | `OE Equivalent Part Number: 8973587200` | keep_existing |

## Rejects

None.

## Eligible before / after

```text
python 01_data/91_build/build_market_data_gap_coverage_20261007.py --also-uk-exact
```

| Cut | Before | After |
|---|---:|---:|
| Focus eligible (`oil_filter` + `brake_pad`) | **47** | **58** |
| Wider UK `exact_oem` eligible **offers** | **151** | **162** |
| Wider eligible **PNs** | **38** | **41** |
| Ledger rows patched | | **11** |
| Distinct SKUs upgraded | | **7** |

Bar ≥50 focus: **MET**.

## Backups / artefacts

- Backup: `C:\Users\jerom\Desktop\claude\_worktrees\ISZE_u29b\01_data\00_derived\price_observations.parquet.bak_20261007T163228Z_before_ks_focus_close`
- PDP HTML + checks: `C:\Users\jerom\Desktop\claude\ISZE\01_data\90_INBOX\_uk_ks_focus_close_20261007`
- Runner: `C:\Users\jerom\Desktop\claude\ISZE\01_data\91_build\_uk_ks_focus_close_20261007.py`
- Metrics (U29b + copied to main): `C:\Users\jerom\Desktop\claude\_worktrees\ISZE_u29b\01_data\00_derived\market_data_gap_coverage_uk_wider_exact_20261007.metrics.json`

## Not done

- Board / INTERNAL rebuilt to focus **58** / wider **162**/41 (this evening wire).
- No new £10 invented on brake pads (policy page still names only filter / clutch / exhaust).
- No TMC invent.


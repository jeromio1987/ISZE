# Warranty commercial datasets

**Built:** 2026-09-18 · **Builder:** `01_data/91_build/build_warranty_commercial_datasets.py`
**Read-only against every source.** Re-run the builder to regenerate the whole folder.

One file per commercial question, **all markets inside each file** — no per-market splits, so adding
a market never means adding a file.

---

## Files

| File | One row per | Use it for |
|---|---|---|
| `warranty_commercial_reconciliation.csv` | headline figure | The totals on one page. Start here. |
| `warranty_cost_by_market.csv` | D-Max distributor | Which book costs what, and what share of it Isuzu actually pays |
| `warranty_cost_by_component_family.csv` | component family (D-Max) | Where the D-Max money goes: steering, electrical, emissions |
| `warranty_cost_by_limit_position.csv` | position vs the limits (D-Max) | How much is warranty and how much is goodwill |
| `warranty_top_repair_lines.csv` | repair operation (top 150 by €) | The individual jobs that cost the most |
| `warranty_part_turnover.csv` | part number (D-Max) | Which parts actually cost, with a cumulative share column |
| `warranty_repeat_repairs.csv` | vehicle × operation repeated | The same job done twice on the same truck |
| `warranty_cv_by_market.csv` | truck market | The truck books, with part-number coverage as a column |
| `warranty_cv_top_repair_lines.csv` | repair operation (trucks, top 100 by €) | The truck counterpart of the D-Max table. **Added 2026-09-18 after a wrong truck steering figure survived two passes — there was no truck table to check against.** The steering gear is the biggest line on D-Max (€800,177) and a minor one on trucks (€29,671) |
| `warranty_cv_by_component_family.csv` | component family (trucks) | The aftertreatment story |
| `warranty_cv_part_turnover.csv` | part number (trucks) | Truck part concentration |
| `warranty_cv_dealer_concentration.csv` | dealer code | One code carries 36% of all truck claims |
| `warranty_cv_failure_code_profile.csv` | failure code | Which codes are real repairs and which are administrative |
| `warranty_cv_currency_audit.csv` | currency × market | Proof of what each euro figure is, and how it was converted |
| `Warranty_Commercial_Datasets_2026-09-18.xlsx` | — | All of the above as sheets, for reading |

---

## Read this before quoting any euro figure

### The truck file is in three currencies, and the UK one is pounds

The CV file's `CRNCY` column carries two tokens, not one:

| Token | Amount is in | Markets |
|---|---|---|
| `EUR EUR` | EUR | Israel, Portugal, Ireland, Germany, Cyprus, Malta, Greece |
| `EUR GBP` | **GBP** | **UK — 11,956 lines, the largest book in the file** |
| `JPY EUR` | **JPY** | Italy, Spain, France, Switzerland, Hungary, Poland, Czech, Romania, Croatia, Serbia, Slovakia, Bosnia, Makedonija |

Verified two ways: the string itself, and the file's own `JPY_PARTSTTL ÷ PARTAMT1` ratio, which is
~1.00 on the JPY rows and ~170 on the EUR-flagged ones.

**Summing `PARTAMT1` raw mixes three currencies and is meaningless.** An earlier pass did exactly
that and produced a €93.8m Italian figure that was really ¥93.8m. Every euro in this folder is
normalised first — EUR as-is, GBP × 1.12, JPY ÷ 163.7 — and `warranty_cv_currency_audit.csv` shows
the working for each market.

### The limits are the stated terms, not a measurement

"Inside the limits" means under 36 months **and** under 100,000 km. Both are constants at the top of
the builder. If the terms change, change them there and re-run.

### Coverage differs by market by an order of magnitude

The share of claim lines carrying **no real part number**: Czech 95%, Switzerland 90%, Italy 87%,
France 83%, Spain 74%, UK 63% — against Israel 23%, Germany 23%, Portugal 17%, Ireland 8%. Part-level
rankings are therefore thinnest in the German-owned markets. `part_number_coverage` is a column on
`warranty_cv_by_market.csv` so this travels with the data instead of living only here.

### Both files are vehicles that claimed, not fleets

The truck file is 33,416 lines over 22,732 vehicles in a 28-month window (Dec 2023 → Mar 2026). The
D-Max file is 20,383 lines, Apr 2025 → Mar 2026, and the January–March 2026 export carries 62%
labour-only lines against 17% in the earlier one. Neither can produce a fleet-wide failure rate, and
neither gives fleet age.

### Two conventions worth knowing

- **Absolute euros are indicative; shares and medians are safe.** The D-Max export is one IMG
  European export and the file's own internal JPY rate is ~170.4 against the 163.7 applied here, so
  JPY-market euros run about 4% high. Kept at 163.7 for consistency with the rest of the workspace.
- **Labour is not comparable across markets.** It is 0.3% of cost in Italy against 29.5% in the UK —
  a recording convention, not a cost difference. `labour_eur` is carried for completeness only.

### Two sources, two emissions totals — both correct

This folder's truck emissions figure (€2.84m, 61% of truck parts turnover) comes from the five claim
sheets in `01_data/06_Warranty/`. The figure of €1.82m (64% of €2.83m) in
`01_data/00_derived/warranty_raw_grain.csv` comes from the canonical grain built by
`01_data/91_build/build_warranty_canonical.py`, which covers a different workbook, a wider period and
a narrower market set. **They are different scopes, not a disagreement.** The share agrees at 61–64%;
say which file you are quoting.

---

## Sign-off (Excel pre-delivery check)

```
excel_pre_delivery_check.py  →  OK, issues=0
Merges: none (flat tables, no banner rows to break)
Wrap: on for every text column longer than 24 characters
Freeze panes: A2 on all 13 sheets
Column widths: column B ≥ 28 on every sheet, per the check
% caps: no percentage column exceeds 100
```

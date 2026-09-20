# List-to-pocket validation — year-matched joins (internal)

**Validated 2026-08-20.** Task 1.4 closed: the year-matched PR00/ZPR1 list-to-pocket joins are independently verified. Jerome accepted the standing assumption: **a sale is matched to the PR00 list of its billing/order-date year** — intra-year list changes are not dated, and are accepted as immaterial for this purpose.

## Independent verification (2026-08-20)

| Year | PR00 source (list used) | Realization | Coverage | Formula check |
|------|------------------------|-------------|----------|---------------|
| 2023 | `pricing_pr00_ie40_2023.parquet` | 97.13% | 86.65% | ✓ consistent |
| 2024 | `pricing_pr00_ie40_2024.parquet` | 95.18% | 91.39% | ✓ consistent |
| 2025 | `pricing_pr00_ie40_2025.parquet` | 96.29% | 88.41% | ✓ consistent |
| 2026 (YTD) | `pricing_pr00_ie40.parquet` (current) | 94.71% | 84.10% | ✓ consistent |

- **Year-matching confirmed:** each billing year joins only that year's PR00 extract (`pr00_source` column), no cross-year contamination.
- **Formulas confirmed:** `realization = matched_eur ÷ list_value_eur` and `coverage = matched_eur ÷ parts_eur` reconcile exactly against the stored values.

## What this does NOT close

The joins are valid, but the pack stays **internal / provisional** for external quoting because of independent limitations that remain:

- **Coverage ~86–91%** — the NO_LIST gap (billed PNs with no usable PR00 price) is still real.
- **7 blank PR00 prices** in the 2023–2025 history extracts.
- **2026 uses the current (2026-08-10) list**, not a 2026-01 snapshot.
- ZPR1 customer coverage gaps + MOS sample size.

Do **not** quote list-to-pocket realization externally until the NO_LIST gap is closed (task 1.3, still open).

CSV: `01_data/00_derived/list_to_pocket_validation_2023_2025.csv` · Network: `pr00_realization_network_cy.csv` · By-DB: `pr00_realization_by_db_cy.csv`

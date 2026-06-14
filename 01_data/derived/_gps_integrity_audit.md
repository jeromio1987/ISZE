# GPS / PMS / BVP integrity audit

**Generated:** 2026-06-12T17:25:23Z
**GPS year:** 2025 | **Warranty basis:** CY2025

Distributors: **22** | PMS summaries: **18** | Issues: **1**

## Issues

- **UMI** (warranty_gap): Israel LCV absent from warranty file — 0 is a gap, not true zero

## Per distributor (latest GPS year)

| DB | SPU incl | SPU ex-warr | Warr € | BVP contested | Verdict | PMS oil cap |
|---|--:|--:|--:|--:|---|--:|
| IRELAND | 387.6 | 376.2 | 34857.0 | 26.1% | — | 419.2% |
| UTI | 296.1 | 273.3 | 255968.0 | 92.4% | bvp_winning_contested | 138.5% |
| ITUK | 248.3 | 231.6 | 374426.0 | 20.9% | — | 162.1% |
| PORTUGAL | 209.1 | 193.1 | 130588.0 | 70.3% | bvp_winning_contested | 37.0% |
| FINLAND | 230.8 | 190.4 | 48676.0 | 2.4% | plausible_genuine_defence | 223.5% |
| BELGIUM | 219.8 | 212.0 | 74677.0 | 37.2% | — | 167.5% |
| ICELAND | 210.1 | 192.7 | 7035.0 | 0.0% | plausible_genuine_defence | 202.0% |
| MALTA | 197.1 | 179.5 | 18219.0 | 0.9% | plausible_genuine_defence | 228.0% |
| CYPRUS | 185.6 | 173.5 | 28041.0 | 44.6% | — | 249.2% |
| GERMANY | 197.1 | 176.9 | 259675.0 | 11.5% | — | 39.4% |
| NORWAY | 178.3 | 141.7 | 290712.0 | 12.1% | — | 136.6% |
| DENMARK | 173.7 | 163.0 | 9115.0 | 0.0% | plausible_genuine_defence | 141.3% |
| ROMANIA | 163.1 | 145.0 | 19377.0 | 18.0% | — | 150.5% |
| SWEDEN | 151.4 | 128.9 | 189618.0 | 1.0% | plausible_genuine_defence | 139.2% |
| UMI | 150.7 | 150.7 | 0.0 | 83.2% | bvp_winning_contested | 76.1% |
| GREECE | 139.0 | 124.0 | 56159.0 | 40.6% | — | 269.1% |
| IUK | 128.3 | 106.2 | 1054395.0 | 10.4% | — | 51.2% |
| HUNGARY | 87.3 | 66.6 | 77434.0 | 24.0% | — | 108.0% |
| UKRAINE | nan | None | None | 43.4% | — | 0.0% |
| ARMENIA | nan | None | None | 54.6% | — | 0.0% |
| KAZAKHSTAN | nan | None | None | 91.9% | bvp_winning_contested | 0.0% |
| PALESTINE | nan | None | None | 83.8% | — | 0.0% |

## Reading guide

- **Ex-warranty SPU** subtracts CY2025 claim-file warranty parts from total sales (embedded in ERP genuine revenue).
- **Low BVP % + warranty** is usually *not* contradictory — warranty parts bill as genuine; contested capture measures BVP vs genuine on paired PNs.
- **UMI warranty = 0** is a data gap (Israel LCV missing from claim file), not proof of zero warranty spend.
- Dashboards without `warranty_parts_eur` in `isze_data.json` are stale relative to GPS v9 / PRISM pipeline.

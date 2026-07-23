# GPS / PMS / BVP integrity audit

**Generated:** 2026-07-21T15:20:53Z
**GPS year:** 2025 | **Warranty basis:** CY2025

Distributors: **22** | PMS summaries: **18** | Issues: **6**

## Issues

- **IRELAND** (v9_sales_delta): Pipeline vs v9 sales -2.2%
- **UTI** (v9_sales_delta): Pipeline vs v9 sales -2.1%
- **ITUK** (v9_sales_delta): Pipeline vs v9 sales -3.6%
- **FINLAND** (v9_sales_delta): Pipeline vs v9 sales -2.8%
- **ICELAND** (v9_sales_delta): Pipeline vs v9 sales -2.3%
- **UMI** (v9_sales_delta): Pipeline vs v9 sales -2.0%

## Per distributor (latest GPS year)

| DB | SPU incl | SPU ex-warr | Warr € | BVP contested | Verdict | PMS oil cap |
|---|--:|--:|--:|--:|---|--:|
| IRELAND | 388.6 | 377.2 | 34857.0 | 26.1% | — | 11.3% |
| UTI | 322.3 | 297.6 | 255968.0 | 92.4% | bvp_winning_contested | 20.4% |
| ITUK | 248.5 | 231.8 | 374426.0 | 20.9% | — | 28.4% |
| PORTUGAL | 209.1 | 193.2 | 130588.0 | 70.3% | bvp_winning_contested | 19.4% |
| FINLAND | 230.8 | 190.4 | 48676.0 | 2.4% | plausible_genuine_defence | 12.2% |
| BELGIUM | 219.9 | 212.1 | 74677.0 | 37.2% | — | 28.2% |
| ICELAND | 210.1 | 192.7 | 7035.0 | 0.0% | plausible_genuine_defence | 9.4% |
| MALTA | 198.6 | 181.0 | 18219.0 | 0.9% | plausible_genuine_defence | 29.2% |
| CYPRUS | 185.6 | 173.5 | 28041.0 | 44.6% | — | 8.9% |
| GERMANY | 197.3 | 177.1 | 259675.0 | 11.5% | — | 13.9% |
| UMI | 179.0 | 82.4 | 1791020.0 | 83.2% | bvp_winning_contested | 1.7% |
| NORWAY | 178.7 | 142.0 | 290712.0 | 12.1% | — | 12.0% |
| DENMARK | 174.2 | 163.5 | 9115.0 | 0.0% | plausible_genuine_defence | 20.9% |
| ROMANIA | 163.6 | 145.5 | 19377.0 | 18.0% | — | 15.9% |
| SWEDEN | 151.4 | 129.0 | 189618.0 | 1.0% | plausible_genuine_defence | 10.6% |
| GREECE | 139.0 | 124.0 | 56159.0 | 40.6% | — | 8.2% |
| IUK | 128.3 | 106.3 | 1054395.0 | 10.4% | — | 7.4% |
| HUNGARY | 88.4 | 67.7 | 77434.0 | 24.0% | — | 15.8% |
| UKRAINE | nan | None | None | 43.4% | — | 0.0% |
| ARMENIA | nan | None | None | 54.6% | — | 0.0% |
| KAZAKHSTAN | nan | None | None | 91.9% | bvp_winning_contested | 0.0% |
| PALESTINE | nan | None | None | 83.8% | — | 0.0% |

## Reading guide

- **Ex-warranty SPU** subtracts CY2025 claim-file warranty parts from total sales (embedded in ERP genuine revenue).
- **Low BVP % + warranty** is usually *not* contradictory — warranty parts bill as genuine; contested capture measures BVP vs genuine on paired PNs.
- **UMI warranty resolved 2026-07-03** from a dedicated claim-file export — see gps_warranty_cy2025.json notes.
- Dashboards without `warranty_parts_eur` in `isze_data.json` are stale relative to GPS v9 / PRISM pipeline.

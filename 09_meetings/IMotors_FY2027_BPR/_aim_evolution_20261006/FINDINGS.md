# I-Motors AIM evolution — ours vs theirs (computed 2026-10-06)

## Data sufficiency

| Side | Source | PN grain | Window |
|---|---|---|---|
| ISZE → I-Motors | `sales_fact.parquet` sold-to **519**, CR/RE out | yes | hole **2025-03 … 2025-08**; then Oct 2025–Aug 2026 |
| I-Motors → dealers | `dealer_sellout_long_PORTUGAL_*.csv` MONTH rows | yes | **2025-01 … 2026-08** complete |
| AIM map | `aim_pn_classification_release_2026-10-04.csv` | ~100% list-€ match | — |
| Same euro basis | PR00 IE40 list 10 Aug 2026 | qty × list | not I-Motors net, not dealer price |
| Sep 2026 | KPI Check Sheet € only | **no PN** | out of AIM cuts |

**Clean bilateral AIM window:** October 2025 – August 2026 (11 months).  
Feb and Sep 2025 billing in parquet look incomplete (~€28k / ~€26k) and are excluded from “complete month” cuts.

Genuine/BVP (`bvp_pn_dimension`): ~89% of list € lands **unknown** on both stages — do **not** use for mix conclusions until the map is filled.

## Builder

`09_meetings/IMotors_FY2027_BPR/_build_aim_evolution.py`  
Outputs in this folder.

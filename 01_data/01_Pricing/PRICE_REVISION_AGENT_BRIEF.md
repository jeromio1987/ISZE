# Price revision — agent brief (short)

**Date:** 2026-09-17 · **Audience:** next agent working the price list / price revision · **Not** a dump of NOTES.

## Basis (do not mix)

| | |
|---|---|
| Weight base | `01_data/00_derived/price_bp_weighted_compare_pn.csv` · `in_scope == True` |
| Window | 2025-07-01 → 2026-06-30 |
| Billed | EUR 34,993,609.39 |
| Step | EUR 1,652,140.71 |
| Weighted increase | 5.9616% |

If your cut does not reconcile to step + weighted increase, stop.

## Two axes (locked — Jerome 2026-09-17)

- **Axis A — identity:** `catalog_l1/l2/l3` (or AIM spine columns when the pack already ships on AIM). Wear views hang from L2/L3 or `fig_key`, never from a commercial posture parent.
- **Axis B — commercial score:** contested / captive per part per market — sits beside Axis A. Not the parent box. Not a fourth layer.
- Full decision: `DECISIONS.md` 2026-09-17 (two-axes entry).
- **Attribute layer: on hold (roadmap)** — Jerome 2026-09-17. Do not build size/position/duty now; not locked as proceed. Attributes-before-levels remains the recommended order later.

## Which CSV for which job

| Job | File | Note |
|---|---|---|
| Corrected Axis A classification | `01_data/00_derived/aim_pn_classification_v2.csv` | Gate: `aim_classification_gate.json` must PASS |
| Focus filters (network + DB) | `01_data/00_derived/aim_catalog_focus_filters.csv` | Use **`catalog_full` only** — not `pr00_catalog_only` |
| DB × node matrix | `01_data/00_derived/aim_catalog_db_matrix.csv` | Same bases |
| Brake check | `01_data/00_derived/aim_catalog_brake_check.csv` | Strict leak test only |
| Price class cross | `01_data/00_derived/aim_catalog_x_priceclass.csv` | Class factors are IML-owned |
| AIM-spine priority list (already shipped packs) | `02_dashboards/pricing/AIM_PRIORITY_LIST.csv` | Named AIM spine — do not mix with catalogue-tree totals |
| AIM master (corrected spine) | `01_data/00_derived/aim_master_v2.csv` | For packs that already quote AIM L1 |

## Israel

Sold-to **1797 = UMI**, **1799 = UTI**. Never blend. The name column cannot split them.

## Do not

- Quote air-filter “€28k / real zeros” — withdrawn after ACL refile (now ~EUR 797k / 40 PNs on Focus `catalog_full`).
- Treat `fig_key` as evidence of competition (that is Axis B territory).
- Rebuild shared HTML unless the current message says rebuild or ship.

## Longer notes (only if needed)

`01_data/00_derived/aim_catalog_breakdown_NOTES.md` · `01_data/00_derived/HANDOFF_AIR_FILTER_AND_FOCUS_CUT.md` · `02_dashboards/pricing/AIM_PRIORITY_LIST_HANDOFF.md`

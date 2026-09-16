# distributor_dimension — canonical DB key

**Written:** 2026-08-13
**Producer:** `01_data/91_build/build_distributor_dimension.py`
**Grain:** one row per `sold_to_sap` billing in FY2026 (32 rows)
**Key:** `sold_to_sap`. **`payer_code` is not unique — do not join on it.**

The single source of truth for "which DB is this row about". Consumed by
`02_dashboards/_composable/build.mjs`, which resolves every module's raw label to
`distributor_code` and drops anything that is not a `network_db`.

---

## Why it exists

Two naming conventions for the same distributors, with no mapping table anywhere:

| Source | Count | Naming |
|---|---|---|
| `pms_summary_by_db.csv` | 18 | country / DB codes — `BELGIUM`, `DENMARK`, `SWEDEN` |
| `gps_pure_sales_2026-08-13.csv` | 27 | SAP entities — `IBX`, `ISD`, `Danmark`, `Sverige` |

Only `ITUK`, `IUK`, `UMI`, `UTI`, `Ireland`, `Norway` overlapped directly. Before this
file, "network average" meant 18 DBs in one dashboard module and 27 in another.

---

## Source lineage (derived only — no raw XLSX opened)

| File | Role |
|------|------|
| `00_derived/sales_with_crossref.parquet` | **Authoritative** `sold_to` → `distributor_code` |
| `00_derived/sales_fact.parquet` | sold-to split, FY2026 euros, SaTy + material (477k rows) |
| `00_derived/pricing_zpr1_customers.parquet` | SAP customer names |
| `02_dashboards/fleet/ISZE_GPS_Dashboard.html` (embedded `DUAL`) | CV / LCV / mixed scope |
| `00_derived/gps_pure_sales_2026-08-13.csv` | `gps_db_label`, so no module hardcodes a mapping |

Nothing is inferred from an entity name. An earlier draft guessed
`Loutsios → GREECE`; the crossref proves it is **CYPRUS**. That draft was discarded.

---

## Israel — resolved

`payer_code` 1797 carries both entities. The split is at sold-to level:

| sold_to_sap | payer | DB | SAP name | FY2026 |
|---|---|---|---|---|
| **1797** | 1797 | UMI | UNIVERSAL MOTORS ISRAEL LTD | €3,079,678 |
| **1799** | 1797 | UTI | UNIVERSAL TRUCKS ISRAEL LTD | €3,242,540 |

Consistent with `gps_pure_sales_2026-08-13.md` (`israel_split`) and with the audit
skill's Check 5. This is the fix for the UMI/UTI merge.

---

## `network_role` — what each row is

| Role | Rows | FY2026 € | Meaning |
|---|---|---|---|
| `network_db` | 25 | 34,061,722 | A distributor. 22 distinct DBs (3 bill through two sold-tos). |
| `not_a_customer` | 2 | 365,740 | Standing exclusion — see below. |
| `excluded_non_parts` | 3 | 178,453 | Billing is entirely non-parts. |
| `direct_account` | 1 | 125,863 | Trades, but is not a network distributor. |
| `excluded_entity` | 1 | 34 | Dormant, excluded per business instruction. |
| **TOTAL** | **32** | **34,731,812** | reconciles to `sales_fact` FY2026 |

Only `network_db` reaches the dashboard; the build drops every other role.

### `not_a_customer` — standing exclusion

Sold-tos 77 and 88 appear in billing and UIO/KPI source data but are **not ISZE
distributors**, and must stay out of GPS / PMS / KPI tables and projections. This is
a standing rule, encoded in `NOT_CUSTOMERS` in the builder and checked **before** any
other classification — so a future crossref row can never promote them back into the
network. The GPS file independently flags 88 as `midi_non_gps_channel`.

`excluded_non_parts` is derived from the `material` field, not a hand-written list —
a sold-to whose billing is ≥99.9% service fee / demurrage / transport / late-payment
interest (audit Check 1) is an exclusion bucket, not a distributor:

| sold_to | SaTy | material | FY2026 € |
|---|---|---|---|
| 373 | DR | `SERVICE` | 160,493 |
| 146 | ZDR | `SERVICE FEE OUTSIDE EUROPE` | 17,600 |
| 2970 | ZDR | `COST DEMURRAGE` | 360 |

`direct_account`: **IMG** (105, €125,863) — trades, has no `distributor_code` in any
source, and is not on the standing exclusion list. Left visible as its own role rather
than silently folded into an exclusion bucket.

---

## Peer groups derived from this file

| Group | n | Members |
|---|---|---|
| CV | 2 | ITUK, UTI |
| LCV | 9 | IUK, UMI, NORWAY, SWEDEN, DENMARK, FINLAND, ICELAND, ROMANIA, HUNGARY |
| Mixed | 7 | GERMANY, BELGIUM, IRELAND, CYPRUS, GREECE, MALTA, PORTUGAL |
| Nordics | 5 | NORWAY, SWEDEN, DENMARK, FINLAND, ICELAND |
| **CIS** | 3 | **UKRAINE, ARMENIA, KAZAKHSTAN** |

CIS was previously believed empty — it is not. `pms_summary_by_db.csv` simply does
not cover those DBs.

---

## Caveats — not buried

1. **Three DBs bill through two sold-tos**: GERMANY (93 → 601 + 2516), PORTUGAL
   (92 → 92 + 519), DENMARK (2027 → 2027 + 2751). Any per-DB total **must sum both**.
2. **Four network DBs have no `scope`**: UKRAINE, ARMENIA, KAZAKHSTAN, PALESTINE.
   The GPS dashboard's CV/LCV classification only covers the original 18. They are
   excluded from CV/LCV/mixed groups but included in `network_average`.
3. **`pms_summary_by_db.csv` covers 18 of 22.** Selecting CIS yields no PMS capture
   data; the dashboard states this rather than rendering an empty table.
4. **FY2026 only.** Euro column and role classification are FY2026. A DB dormant in
   FY2026 but active earlier would be misclassified — re-run per FY if that matters.
5. **`gps_pure_sales_2026-08-13.md` attributes the €17,600 to ITUK** as a CR/ZDR
   residual vs billing-clean. At line level it sits on **sold_to 146** as
   `SERVICE FEE OUTSIDE EUROPE`, not on ITUK (2575, whose FY2026 CR is €146,656).
   Both treatments exclude it; the attribution differs. Not reconciled here.
6. **`RSA` naming collision** (also flagged in the GPS file): billing `RSA` = payer 66
   = **Greece** (Petros Petropoulos); the warranty file uses `RSA` for **Norway**.
   This file follows billing.

---

## Rebuild

```powershell
python 01_data\91_build\build_distributor_dimension.py
cd 02_dashboards\_composable ; node build.mjs
```

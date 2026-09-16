# ISZE state packet

**Updated:** 2026-09-16 — workspace remediation (CURSOR_BRIEF)

Keep ≤1–2 pages. Refresh when big ISZE work ships.

## Built (this pass)

| Item | Path |
|------|------|
| Audit refresh (read-only) | `docs\WORKSPACE_AUDIT_REFRESH_2026-09-16.md` |
| Execution brief | `docs\CURSOR_BRIEF_2026-09-16.md` |
| Security report (B) | `docs\_wsB_security_report.md` |
| Alps PR land (5/5 merged) | `docs\_wsA_Alps_report.md` |
| mypens PR land (2 closed, reasons) | `docs\_wsA_mypens_report.md` |
| VC gaps C.1–C.2 | `docs\_wsC_vc_report.md` |
| Tier1 consolidation refresh | `docs\CONSOLIDATION_TIER1_REFRESH_2026-09-16.md` |
| Inventory refresh | `docs\WORKSPACE_INVENTORY.md` |

## Open / blocked

| Item | Status |
|------|--------|
| ISZE PRs | **All 8 merged** — see `docs\_wsA_ISZE_report.md`. Local dirty tree left uncommitted; both IDS stashes dropped |
| C.3 myPENS CI | **Done** — workflows on mypens `main` (`1476ccc`); see `docs\_wsC3_mypens_ci_report.md` |
| E truth audit | **Done** — `docs\TRUTH_AUDIT_2026-09-16.md` (4 confirmed disagreements; fig_key = date drift only) |
| Old GitHub PAT | Skipped per Jerome 2026-09-16 — files left; residual local-disk risk only |
| Private health `.gitignore` | Proposal in `_wsB`; awaiting confirm before write |
| cairn / pebble | Awaiting Jerome: version / park / reclaim |
| Tier1 delete 210 files (~222 MB) | **Done** — 210 deleted / 221.9 MB; receipt `docs\_tier1_delete_receipt.json` |
| Alps `.gitignore` `export_*.csv` | Done on disk, **not committed** |

## CV warranty mileage validation (2026-09-16)

| Item | Path |
|------|------|
| Validation note | `01_data\90_INBOX\_cv_warranty_mileage_validation.md` |
| Derived table | `01_data\00_derived\warranty_cv_km_age_by_market.csv` |
| Fleet/age companion (parallel worker) | `01_data\90_INBOX\_market_fleet_profile_workup.md`, `_market_fleet_profile_design.md` |

**Headline:** the PRISM mileage assumption is confirmed for UTI (measured 51,680 vs assumed 50,000) and contradicted for ITUK (measured 16,688 vs assumed 50,000). The global `annual_km_yr: 20000` is structurally wrong — mileage tracks truck weight class (N35 12,165 / N75 35,217 / F-series 45,630), a 3.7× spread. Open question: whether ITUK's 50,000 or the UK warranty VIN sample is the wrong one. **Awaiting Jerome before any PRISM rebuild.**

## Prior built (unchanged)

| Item | Path |
|------|------|
| Exec aftersales paper | `02_dashboards/sales/ISZE_Exec_Aftersales_Paper.html` |
| Command Center | `02_dashboards/sales/ISZE_Aftermarket_BI_Command_Center.html` |

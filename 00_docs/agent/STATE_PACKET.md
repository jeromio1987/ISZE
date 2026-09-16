# ISZE state packet

**Updated:** 2026-08-25 ~19:52 (overnight Tick 12 — P8 horizon fix)

Keep ≤1–2 pages. Refresh when big ISZE work ships.

## Built

| Item | Path |
|------|------|
| Action Ledger P8 | `01_data/00_derived/action_ledger*` + `02_dashboards/ops/ISZE_Action_Ledger*.html` |
| Overnight workspace audit | `docs/OVERNIGHT_PROCESS_AUDIT_2026-08-25.md` |
| Morning brief / command card | `docs/OVERNIGHT_MORNING_BRIEF_2026-08-26.md` · `OVERNIGHT_MORNING_COMMAND_CARD_2026-08-26.md` |

## Facts (snapshot)

- Verify: **116/0/0 · ok=true** (2026-08-25T17:19:54Z)
- `sales_fact`: **514,037** rows · billing max **2026-06-30**
- SaTy: **~92.9%** — Apr–Jun from Q1FY2027 lack SaTy column; min fixture **92%**
- Junctions: **restored** (`dashboards`/`derived`/`_INBOX`/…)
- Action Ledger: **23,236** open · decisions CSV header-only · **billing_horizon = 2026-06-30** (now derived from sales_fact, not hard-coded Mar-31)
- Nordics: Doffin/HILMA **OK** — **never re-ask Jerome for keys**

## Open

- Human: P4 calibration 4.9 *or* Tomoe IDS mail
- Optional: SAP re-export Q1 **with SaTy**
- P8: seed ≤5 rows in `action_ledger_decisions.csv` from top-15 € (not all 23k)
- Manual: delete retired Scheduled folders; patch freshness SKILL paths (map in AUTOMATION_REGISTER)

## Agent habit

KPIs: green `_verification_report.json` first. Process OS: overnight pack + `AUTOMATION_REGISTER.md`. Nordics keys: closed.

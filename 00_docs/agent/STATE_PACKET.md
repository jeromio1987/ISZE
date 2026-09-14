# ISZE state packet

**Updated:** 2026-09-14 (Monday OS seed · decision pack opened)

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
- Action Ledger: **23,236** open · **5 TRIAGED** (2026-09-14 seed from top-15 €; not ACTIONED; outcomes 0) · **billing_horizon = 2026-06-30**
- Decision pack: `00_docs/DECISION_PACK_20260914.md` — ticks **not applied**
- Nordics: Doffin/HILMA **OK** — **never re-ask Jerome for keys**

## Open

- Human: tick `DECISION_PACK_20260914.md` (B5 / L2P / G1 / Book B). P4 4.9 still behind B5.
- Optional: SAP re-export Q1 **with SaTy**
- P8: five REVIEW/TRIAGED rows seeded — Jerome confirm or drop; do not ACTIONED-mass
- Manual: delete retired Scheduled folders; patch freshness SKILL paths (map in AUTOMATION_REGISTER)

## Agent habit

KPIs: green `_verification_report.json` first. Process OS: overnight pack + `AUTOMATION_REGISTER.md`. Nordics keys: closed.

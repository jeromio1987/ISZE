# ISZE state packet

**Updated:** 2026-09-14 (lanes 0–4 ran; gated productize stopped)

Keep ≤1–2 pages. Refresh when big ISZE work ships.

## Built

| Item | Path |
|------|------|
| Action Ledger P8 | `01_data/00_derived/action_ledger*` + `02_dashboards/ops/ISZE_Action_Ledger*.html` |
| Decision pack 2026-09-14 | `00_docs/DECISION_PACK_20260914.md` — ticks **not applied** |
| Fig-key IE40 fill | `pr00_classification.csv` +158 empty keys; `parts_catalog_dimension` 161,325 fig_key |
| EPC validator | `pn_supersession_epc_validation.meta.json` = **BLOCKED_NO_EPC_EXPORT** |
| Overnight workspace audit | `docs/OVERNIGHT_PROCESS_AUDIT_2026-08-25.md` |
| Morning brief / command card | `docs/OVERNIGHT_MORNING_BRIEF_2026-08-26.md` · `OVERNIGHT_MORNING_COMMAND_CARD_2026-08-26.md` |

## Facts (snapshot)

- Verify: run 2026-09-14 after this pass (quote only if `_verification_report.json` ok)
- `sales_fact`: **514,037** rows · billing max **2026-06-30**
- SaTy: **~92.9%** — Apr–Jun from Q1FY2027 lack SaTy column; min fixture **92%**
- Action Ledger: **23,236** open · **5 TRIAGED** (2026-09-14 seed; not REVIEW; not ACTIONED)
- Decision pack: ticks **not applied**. Gated productize **stopped**.
- ES PLACSP **LIVE**; national **17/29**. Nordics keys **DONE** — never re-ask.
- Fig-key fill **158**. EPC **BLOCKED_NO_EPC_EXPORT**. Scraper V2 landed.

## Open

- Human: tick `DECISION_PACK_20260914.md` (B5 / L2P / G1 / Book B). P4 4.9 still behind B5.
- EPC supersession export in `90_INBOX` before MATCH is legal.
- Optional: SAP re-export Q1 **with SaTy**
- P8: five TRIAGED rows — Jerome confirm or drop; do not ACTIONED-mass

## Agent habit

KPIs: green `_verification_report.json` first. Process OS: overnight pack + `AUTOMATION_REGISTER.md`. Nordics keys: closed.

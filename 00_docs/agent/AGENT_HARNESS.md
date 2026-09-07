# Agent harness (ISZE + Claude workspace)

**Updated:** 2026-09-07

Machine-checkable gates around Cursor agents. Rules advise; **hooks + receipts enforce**.

Stop hooks are **workspace-scoped** and brief checklists are **per bucket** (7 Sep evening): `brief-checklist-ISZE.json` vs `brief-checklist-Projects-Alps-Sep2026.json`. An ISZE dealer-map brief must not appear in Alps. Helper: `Desktop\claude\.cursor\skills\verify-before-done\scripts\workspace_scope.mjs`.

ISZE-only rules (commercial layers, Nordics keys) live in `ISZE/.cursor/rules`, not `~\.cursor\rules`.

Subagent prompt (ISZE): `ISZE/.cursor/prompts/ISZE_SUBAGENT.md`

## Contract

```
Write deliverable → qa-pending marker → verify (cheap → visual) → SHIP_RECEIPT.json → stop OK
```

Escape: `SKIP_QA=1` (say so in chat). Restart Cursor after changing `~\.cursor\hooks.json` if hooks look dormant.

## Inner loops (same chat turn)

| Loop | Trigger | Gate |
|------|---------|------|
| **Visual pack ship** | Write/StrReplace `.html/.pdf/.pptx` under `Desktop\claude` | `deliverable-mark-pending.mjs` → stop `deliverable-verify-on-stop.mjs` until `*.SHIP_RECEIPT.json` `ok:true` |
| **Brief landing** | Multi-point correction | `brief_checklist.mjs` → stop `brief-checklist-on-stop.mjs` until all `pass`/`skip` |
| **DB Sales Review** | `build_*deck*` / parts analysis | ISZE `db-sales-review-*-*.mjs` + `qa_deck_gate.py` |
| **myPENS** | Dirty mobile tree | ISZE `mypens-verify-on-stop.mjs` (`tsc`) |
| **Contrast** | HTML/CSS write | user `dashboard-contrast.js` (advisory context) |

### Receipt how-to

```powershell
python "C:\Users\jerom\Desktop\claude\.cursor\skills\verify-before-done\scripts\html_screenshot.py" "C:\path\file.html" "C:\path\_qa"
# Image-Read PNGs — blank = FAIL
node "C:\Users\jerom\Desktop\claude\.cursor\skills\verify-before-done\scripts\write_receipt.mjs" --artifact "C:\path\file.html" --screenshot "C:\path\_qa\page-001.png"
```

Skill: `C:\Users\jerom\Desktop\claude\.cursor\skills\verify-before-done\`

### OPEN vs QA

User-facing `start` = `OPEN: cmd-only` / `OPEN: now` only.  
Headless Chrome + `_qa` screenshots = always allowed (QA-internal).

## Outer loops (scheduled / `/loop` / watchdog)

Recipes file:  
`C:\Users\jerom\Desktop\claude\.cursor\skills\verify-before-done\scripts\outer_loops\RECIPES.md`

| Loop | Command | Action on fail |
|------|---------|----------------|
| Pipeline freshness | `node …\outer_loops\check_pipeline_stale.mjs` | Re-verify via `isze-verify-pipeline`; rebuild only with Jerome OK |
| Dashboard health | `…\check_dashboard_health.ps1` | **Ops watchdog** may rebuild Command Center HTML (`start_loop_aftermarket_bi.ps1`). SPAR still binds chat. No new HTML filename. |
| Tender health | `node …\outer_loops\check_tender_health.mjs` | Investigate **new** BROKEN/SUSPECT; **never** re-ask Nordics keys |
| Mail proof | `isze-mail-delivery` / work-loops Loop A | SENT_PROOF or Outbox stuck — no silent Send |
| Work loops A/B/C | skill `isze-work-loops` | See skill + REFERENCE |

## Hook files

| Scope | Path |
|-------|------|
| User | `C:\Users\jerom\.cursor\hooks.json` |
| User scripts | `C:\Users\jerom\.cursor\hooks\deliverable-*.mjs`, `brief-checklist-on-stop.mjs`, `dashboard-contrast.js` |
| ISZE | `C:\Users\jerom\Desktop\claude\ISZE\.cursor\hooks.json` |

Pending markers: `C:\Users\jerom\Desktop\claude\.cursor\qa-pending\`  
Receipt mirror: `C:\Users\jerom\Desktop\claude\.cursor\qa-receipts\`

## Rules (do not duplicate essays)

| Rule | Role |
|------|------|
| `verify-before-done.mdc` (user, always) | Receipt required; OPEN/QA split |
| `a1-visual-delivery-qa.mdc` | Blank-page visual bar |
| `isze-ship-gate.mdc` | ISZE Mode A paint + verify scripts |
| `isze-verify-rendered-output.mdc` | Pointer into receipt harness (paint procedure) |
| `landing-every-brief-item` skill | Brief checklist |

## Agent habit

1. Before “ready”: receipt path in chat (or brief checklist clear).  
2. KPIs: green `_verification_report` when citing pipeline numbers.  
3. Nordics keys: closed. Mail: draft default.

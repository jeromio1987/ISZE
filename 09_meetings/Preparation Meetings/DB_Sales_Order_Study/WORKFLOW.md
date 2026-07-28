# Workflow — DB Sales / Order studies (logged for future cases)

**Agent sync:** 2026-07-26

## Pattern

1. Confirm Power BI access (`SALES DATA VP NEW` → SALES + ORDER).
2. Green `_verification_report.json` before quoting KPIs.
3. Hierarchy per DB: network → customer → SaTy → source/category → PN + GPS/PMS.
4. Periods: FY Apr–Mar from billing; H1 from PBI when needed.
5. Deliver chart-first HTML (no CDN) + Excel (pre-delivery check) + speaker notes.
6. Persist `study_state.json` for V2 / resume.

## Depth levels

| Level | When | Example |
|-------|------|---------|
| **Seed / deep** | Priority meetings | `Imotors_UMI_Sales_Study` V2 10-pager |
| **Shallow pack** | Network fan-out | `DB_Sales_Order_Study/packs/{CODE}.json` |
| **Deepen later** | After meetings | Re-run V2 template on next DB |

## Resume all-DB

```powershell
cd "$env:ISZE_ROOT\09_meetings\Preparation Meetings\DB_Sales_Order_Study"
python _build_network_study.py --resume
python _build_network_study.py --only ITUK,IUK
python _build_network_study.py --from-db GERMANY
```

Shallow packs for all ranked DBs may already be `complete` in state — check `study_state.json` before recompute. Prefer deepening with the V2 Imotors/UMI template rather than re-running shallow.

## Rules always on

- Total PMS capture primary
- UMI ≠ UTI
- No raw billing lines in chat
- External language on shared decks

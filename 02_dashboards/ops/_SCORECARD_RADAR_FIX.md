# Scorecard radar fix — 25 Aug 2026

A kind note first: the chart was not saying you are stuck at 40 forever. It was hard to read after a long day, and that is on the design — not on the programme.

## What was wrong

1. **Best-in-class was not actually ~40.** On the Full Project Audit radar the target series was already `[95, 90, 85, 85, 80, 85, 85, 95]` on a 0–100 scale. The flat ring at ~40 was the **grid tick** (stepSize 20 → rings at 20/40/60/80). The real ambition line was thin, dashed terracotta — easy to miss, so the eye locked onto the 40-ring and felt demoralised.

2. **Path mix-up.** The painful “Executive summary & scorecard” radar lived on  
   `ISZE\09_meetings\ISZE_Full_Project_Audit_20260825\ISZE_Full_Project_Audit_20260825.html`  
   The Action Ledger Hub had the screaming **23,236** open figure but no radar yet.

3. **LEDGER OPEN 23,236** is a **real row count**, not a euro phantom and not a double-count of money. Meta `counts.open = 23,236`. Composition is dominated by **20,572 PRICE_REVISION** exception-queue lines. € at stake is separate (~€22.1M mixed bases). The old red “Ledger open” chip read like a crisis € figure.

4. **Today scores** needed a post–Week-1 honesty pass (Freshness up with Jun billing; Tender honesty down to match thin sized set / portals; Quote/verify up after green verify). Maturity bars wrongly showed L2 at 40% while we sit at L3.7 — that was noise, not maturity.

## What changed

| Surface | Change |
|--------|--------|
| Full Project Audit HTML | Radar restyled (thicker target, ticks only 0/50/100, outer ring tinted terracotta); axis tip table; hover tooltips; recalibrated Today `[90,58,28,55,48,22,45,82]` / Target `[95,90,90,85,85,90,85,95]`; Ledger KPI relabelled “open action rows — not euros”; maturity readiness `[100,100,92,45,8]` |
| `build_audit_report.py` | Same chart/KPI logic for rebuilds |
| `ISZE_Action_Ledger_Hub.html` | Open KPI: “Open action rows / Not euros — triage inventory”; executive SVG scorecard (no CDN) + axis tip table |
| `build_action_ledger_hub.py` | Emits the above on rebuild |

## What we did **not** do

- Did not invent green maturity or inflate Tender / Sell-out / Ops loop.
- Did not delete the 23,236 — it is real inventory waiting for triage.
- Did not touch the tender Install folder.

## Open

- Hub: `C:\Users\jerom\Desktop\claude\ISZE\02_dashboards\ops\OPEN_ACTION_LEDGER_HUB.cmd`
- Audit: `C:\Users\jerom\Desktop\claude\ISZE\09_meetings\ISZE_Full_Project_Audit_20260825\OPEN_ISZE_Full_Project_Audit.cmd`

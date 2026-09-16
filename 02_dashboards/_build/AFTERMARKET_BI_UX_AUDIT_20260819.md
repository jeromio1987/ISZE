# Aftermarket BI UX audit — reusable patterns across ISZE dashboards

**Date:** 2026-08-19 · **Mode B internal** · **Scope:** sample read via INDEX + listed paths (not full-repo glob)

## Sources sampled

| Area | Path | What we stole |
|------|------|---------------|
| OS data map | `02_dashboards/ops/ISZE_OS_Data_Map.html` | Sticky tabs, hero KPI chips + hover tooltips, navy/terra/Georgia |
| ITUK operating | `09_meetings/ITUK_Operating_Dashboard_2026/ITUK_Operating_Dashboard.html` | Bullet bars, heat grid, sticky sales-sub nav, plan line, dealer drill |
| UTI operating | `09_meetings/UTI_Operating_Dashboard_2026/UTI_Operating_Dashboard.html` | Same shell as ITUK — lane cards, lights row, grain controls |
| IAM engine | `02_dashboards/pricing/ISZE_IAM_Quality_Positioning_Engine.html` | Sticky section tabs, KPI chipbox tooltips, chain-of-custody cards |
| PartGroups | `02_dashboards/sales/ISZE_PartGroups_Sales_Explorer.html` | Dense filters + sticky thead tables (launcher for fat JSON) |
| IDS compare | `02_dashboards/ids/IDS_2026_dealer_compare.html` | SVG radar, compare overlays, map+table dual pane |
| PMS BVP Regain | `09_meetings/PMS_BVP_Regain_2026/PMS_BVP_Regain.html` | Waterfall narrative, ranked “ask” cards, callout-first layout |

---

## Top 10 reusable patterns (steal list)

1. **Sticky stakeholder tabs** — OS Data Map / operating dashboards: tabs stay visible while scrolling; active tab = terra underline. → Command Center ISZE Director | DB Director | Pricing.

2. **Hero KPI chips with CSS tooltips** — `.hk` + `.tip` on hover/focus: formula, snapshot date, exclusions (UTI≠UMI). Never `title=` only.

3. **In-panel section nav** — IAM engine + ITUK `sales-sub`: anchor links within a tab so a director tab feels *full*, not 4 lonely cards.

4. **Callout-first narrative** — “Biggest money leak: DB · PN · €” before charts. Operating dashboards always lead with one sentence verdict.

5. **CSS/SVG SSR bars & lines** — Tier A replenishment pattern: horizontal `bar-row`, vertical SVG bars, dual polyline monthly — **no Chart.js for first paint** on `file://`.

6. **Heat grids with semantic colour** — ITUK `.heat` + Book B bucket×action: hot/warm/cool on count or €; row headers navy sticky.

7. **Ranked “money” cards** — PMS Regain ask-cards + terracotta lane headers: top-N PNs as large cards with € + action badge, not only table rows.

8. **Bullet ambition vs guardrail** — ITUK operating `.bullet` + mark line: weighted € bar + terra guardrail marker — perfect for Book B vs blocked growth.

9. **Mini sparkline strips** — Operating dashboards embed small trend context per DB; we use SVG polylines from `replenishment_bridge` monthly agg.

10. **Radar / scatter for compare** — IDS dealer radar (SVG polygon) + IAM scatter (index vs gap): compare 5 DBs without another bar chart wall.

---

## What makes operating dashboards feel “director grade”

- **Verdict in 5 seconds:** hero KPIs + one callout before any chart.
- **Nothing empty:** every card has SSR fallback content or explicit “No data” cap — never a white 280px Chart.js box.
- **Hierarchy:** network → DB → PN → dealer (ITUK) drill path matches how Jerome runs meetings.
- **Action language:** pills for pipeline signal + recommended action, not raw SAP field names.
- **Honesty row:** DATA_INTEGRITY / plan line / source chips — we mirror with footnotes on ref sell-out and five-DB cut.
- **Sticky navigation:** user never loses context switching leakage vs pricing vs Monday fix list.
- **House palette locked:** navy `#15233c`, terracotta `#c0552d`, Georgia headings, paper `#f7f4ee` — contrast rule (no white on pale).

---

## Applied to Aftermarket BI Command Center (this rebuild)

| Viz | Pattern source | Implementation |
|-----|----------------|----------------|
| € leakage waterfall | PMS Regain narrative | `SSR.waterfall_steps` network→DB→top PN |
| Pipeline heatmap | ITUK heat grid | `SSR.pipeline_db_heatmap` DB×class € |
| AIM treemap | PartGroups density | `SSR.treemap_cells` L1 € at risk |
| Sparkline strip | Operating monthly tiles | `SSR.sparkline_strip` per DB sell-out € |
| Book B bullet | ITUK bullet chart | `SSR.bullet_chart_dual` ambition vs blocked |
| IAM scatter | IAM positioning engine | `SSR.scatter_svg` KS index vs € gap |
| DB radar | IDS dealer radar | `SSR.radar_lite_svg` 5-metric normalize |
| Money cards | PMS ask-cards | `SSR.money_on_table_cards` top 5 PNs |
| ITUK leaderboard | ITUK dealer table | `SSR.mini_leaderboard` top 5 dealers |
| Bucket×action heat | Book B review | existing `SSR.heatmap_table` on Pricing tab |

---

## Gaps / not stolen (yet)

- **Sankey** — only in pricing readiness prototypes; needs pre-aggregated flow JSON >2 MB → launcher, not inline.
- **Chart.js deep drill** — PartGroups explorer stays launcher-backed; Command Center stays SSR-first by design.
- **Live PBI embed** — operating dashboards sometimes open official cut first; Command Center stays derived CSV/parquet only.

---

## Loop / QA takeaway

Previous loop only printed `AGENT_LOOP_TICK` to stdout with no verify/rebuild — Cursor never woke, PID went stale. Replaced with log file + immediate tick + `--all` rebuild on verify fail. See `LOOP_AFTERMARKET_BI.md`.

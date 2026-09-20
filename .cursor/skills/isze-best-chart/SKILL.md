---
name: isze-best-chart
description: >-
  Chooses the best chart form for each ISZE aftersales / GPS / PMS question and
  forbids bad defaults (18-line slopes, pies of many DBs, one bar form for every
  story). Use when designing, rebuilding, or reviewing any dashboard chart,
  HTML pack, shared visual, KPI graph lab, or when Jerome asks for graphs,
  dropdowns, compare views, pie/donut, fonts, or "best chart".
---

# ISZE — best chart for the question

Jerome standing preference (2026-09-16): always pick the best form for the job.
Do not default to “another horizontal bar” or “one slope for every market.”

Companion brief: `01_data/90_INBOX/_kpi_graph_design_proposal.md`  
Live compare pattern: `02_dashboards/sales/ISZE_PMS_Family_Compare.html`

Also obey: `isze-gaps-need-context.mdc`, `isze-spoken-labels.mdc`, shared language.

## Method (every chart)

1. **Name the business question** in one sentence. That becomes the title.
2. **Name the data relationship** (rank / change / deviation / part-to-whole / pattern / flow / range).
3. **Pick the form from the table below.** If two forms fit, prefer the one a reader gets in under two seconds.
4. **UI:** elegant dropdown = the *question* (or family + question), not a raw “chart type” menu.
5. **Context:** every gap carries euro + service family + fleet (UIO). Never lead with bare units.

## Form map

| Question | Form | Hard avoid |
|---|---|---|
| Who is biggest / who wins on this family? | Ranked bar, value at bar, median/reference marked | Pie of many DBs |
| Mix inside one DB for one family | Donut/pie, **≤4 segments** (genuine / BVP / not bought) | Stacked bar of 18 DBs |
| Fleet or spend: growing or shrinking? | Slope for **top 4–6 only**; rest = change-only bars or second panel | One slope with 12–18 lines |
| Capture vs expected | Split / three-way bar with **named residual** (“not bought”) | Bare % with no residual |
| Where is the euro gap? | Ranked gap bars in € | Pie; unit counts alone |
| Who is out of line vs a norm? | Two-sided deviation from reference | Dual-axis |
| Basket breadth (DB × family) | Heatmap | Slope; 18-series line |
| Quiet too long vs own reorder rhythm | Deviation vs own gap (dormancy) | Absolute silence rank only |
| Projection / method break | Fan/band between two methods + break on axis | Single forecast line as fact |
| Same metric, many markets, pattern | Small multiples, shared scale | One crowded multi-series chart |

## Hard failures (do not ship)

1. **Spaghetti slope** — more than ~6 labelled series on one slope/bump chart.
2. **Pie of a league** — pie/donut comparing many distributors or many families.
3. **One form for every story** — every canvas the same horizontal bar.
4. **Titles as section names** — must be the business question.
5. **Measured and modelled identical** — projections need a band or visible method break.
6. **Overlapping labels** — if labels collide, change the form or split the panel; do not shrink the font and ship.
7. **Gap without context** — euro + family + UIO (see gaps rule).

## Dropdown pattern (preferred UX)

- Control labels the **question** or **parts family**, not “Bar / Pie / Line”.
- Changing the control swaps to the form in the map (and the live numbers).
- Optional second control: metric (Capture % / Gap € / Billed €) when the *same* form still answers the same question.
- Click one DB → detail (mix donut). UMI ≠ UTI; never blend Israel.

## Style

House palette: navy `#15233c`, terracotta `#c0552d`, paper `#f7f4ee`, Georgia headings.
Pie/donut and alternate fonts are allowed when they serve the form map — variety is fine; wrong relationship is not.
Self-contained HTML (`file://`): no chart CDN; embed data or ship `OPEN_*.cmd`.

## Before claiming done

Paint-check the rendered chart: no overlapping labels, residual named if composition, receipt per verify-before-done when shipping HTML.

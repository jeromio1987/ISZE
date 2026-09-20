# Chart critique — all Tier A dashboards · 2026-08-19

**internal internal · brutal honest UX audit**  
Scope: every SSR chart/viz in the four rebuilt HTML packs.  
Fix pass: P0/P1 patched in `render_ssr_charts.py` + builders same day.

Legend: **P0** ship-blocker / misleading · **P1** ugly or director-grade fail · **P2** defer

---

## 1. `LEAKAGE_EXEC_SUMMARY_20260819.html`

### Network hero strip
| Viz | What it shows | Verdict | Flaws | Fix |
|-----|---------------|---------|-------|-----|
| Network comparison · € leakage by DB | Five-DB € gap side-by-side | **misleading → fixed P0** | IUK 9.4M made ITUK/UTI bars 4px hairlines; looked like Greece/UTI had zero leakage | Log-scaled bar height + compact € labels + footnote |

### Per-DB sections (×5: ITUK, UTI, IRELAND, IUK, GREECE)

Each DB repeats:

| Viz | What it shows | Verdict | Flaws | Fix |
|-----|---------------|---------|-------|-----|
| Top 10 PNs · € gap (bar) | Horizontal bars, PN labels | **good** | Long PNs truncate — OK with title hover | P2: add DB suffix only in network view |
| AIM L1 families · € gap (bar) | Family € ranking | **good** | "Intake Exhaust Emission" truncates at 140px | P2: abbreviate on canvas, full in title |
| Pipeline mix (donut) | Leakage/overstock/balanced € split | **good** | Was fine — legend already had € | — |
| Where money leaks (narrative) | Top 3 AIM callouts | **genius** | None — this is the meeting hook | — |
| What to do Monday (list) | Action bullets | **good** | GREECE correctly says hold until sell-out | — |
| Top 10 part numbers (table) | Drill rows | **good** | GREECE used to be empty with no banner | P0: DATA UNAVAILABLE banner + fallback table |
| GREECE DATA UNAVAILABLE banner | Explains zero sell-out | **good → styled P1** | Yellow alert was generic | Navy/gold GREECE-specific styling |

**GREECE-specific:** Donut showed 0% leakage € correctly but could confuse vs overstock €727k in Command Center heatmap — narrative now states "not measurable" explicitly. **P2 defer:** add mini overstock € chip on GREECE section header.

---

## 2. `ISZE_Aftermarket_BI_Command_Center.html`

### Tab: ISZE Director (network)

| Viz | Section | What it shows | Verdict | Flaws | Fix |
|-----|---------|---------------|---------|-------|-----|
| Hero KPI chips (×8) | Hero | Network €, overstock, PN count, Book B, IAM | **good** | Full € on chips is dense | P2: compact € on hero only |
| Money on table · top 5 cards | #net-money | Terracotta ranked PN cards | **good → P1** | €573,277 unreadable at glance; all 5 were IUK — looks like single-DB dashboard | Compact €573k; meta still shows DB |
| € leakage waterfall | #net-waterfall | Network → DB steps | **misleading → P1** | DB bars 2–11% width — readable numbers but visually "empty" | Min 3% width for non-zero DB steps |
| Pipeline mix (€ bar) | #net-waterfall | Stacked leakage/overstock/balanced | **good** | Duplicated later as "Pipeline mix (€ bar)" | **P0 removed duplicate** |
| Pipeline heatmap · DB × class | #net-heatmap | € in cells, hot/warm/cool | **good** | GREECE leakage column "—" correct but no row footnote | P2: GREECE row footnote |
| AIM L1 treemap | #net-heatmap | Area ∝ € at risk by AIM | **ugly → P0** | 88% block labelled "—" (unmapped AIM) — looked broken | Label "Unmapped AIM" + compact € in cell |
| Monthly bill vs sell-out | #net-trends | Dual line SVG | **good** | Dec bill line drops to zero — real data cliff, not a bug | P2: annotate Dec partial month |
| Sparkline strip · sell-out € by DB | #net-trends | Mini polylines + last month € | **good → P1** | UTI sparkline flatlines at bottom (zeros) — ugly but honest | Compact € on sv |
| Network comparison · € leakage | #net-compare | DB column bars | **misleading → P0** | Same IUK dominance; UTI 4px | Log scale + note |
| Pipeline donut · network € | #net-compare | 48/11/41% € split | **good** | 3 segments — donut OK here (not useless) | Legend already € — kept |
| Pipeline mix (€ bar) DUPLICATE | below compare | Same as waterfall pair | **ugly → P0** | Exact duplicate of mix above + donut | **Removed** |
| DB comparison radar | network | 5-metric normalized polygons | **misleading P2** | 5 DBs × 5 metrics overlaid — spaghetti without interactive toggle | P2: max 3 DBs default or tabbed |
| AIM L1 bars | network | Top 15 families | **good** | Same data as treemap — redundant | P2 defer dedupe |
| IAM scatter | network | KS index vs € gap | **good** | Dots unlabelled except hover title | P2: label top 3 outliers |
| Book B bullet dual | network | Ambition vs guardrail | **good** | Second row duplicates first visually | P2: drop duplicate row |
| Book B bucket weights | network | Horizontal bars by bucket | **good** | Bucket names truncated (`other_gf_1_0`) | P2 OK for internal |
| Top 20 PNs bar | network | PN+DB in label | **good** | Labels long | title= hover exists |
| ITUK dealer top 5 | network | Leaderboard list | **good** | Only ITUK — correct grain | — |

### Tab: DB Director

| Viz | What it shows | Verdict | Flaws | Fix |
|-----|---------------|---------|-------|-----|
| Pipeline donut · € split | Per-DB € mix | **good** | — | — |
| Top 10 leakage PNs | DB-scoped bars | **good** | — | — |
| AIM L1 families | DB-scoped bars | **good** | — | — |
| Leakage vs overstock € (SVG vbar) | 2-bar vertical | **ugly P2** | Only 2 bars — barely a chart; donut already shows split | P2 defer |
| Register counts | Text list | **ugly P2** | Duplicates donut/headline numbers | P2 defer |
| ITUK dealer table | Top dealers | **genius** | Only tab with dealer grain | — |

### Tab: Pricing / revision

| Viz | What it shows | Verdict | Flaws | Fix |
|-----|---------------|---------|-------|-----|
| Ambition vs guardrail bullet | Book B weighted vs blocked | **good** | — | — |
| Bucket × action heatmap | Count grid | **good** | No legend key for colour scale | P2: add "hot = high count" key |
| Stacked bucket × action bars | Stacked counts | **good** | No legend for colours — must hover | P2 |
| IAM / list / share tables | Registers | **good** | Table-heavy tab — expected for internal | — |

---

## 3. `ISZE_DB_DLR_Replenishment_CY2025.html`

| Viz | What it shows | Verdict | Flaws | Fix |
|-----|---------------|---------|-------|-----|
| Network comparison · € leakage | DB € bars | **misleading → P0** | IUK 120px vs UTI 4px | Log scale |
| Pipeline donut · PN counts | PN count split | **misleading → P0** | Legend said "€11,826" for PN counts — **currency lie** | `fmt_int` in legend |
| Pipeline mix bar | PN count stacked bar | **misleading → P0** | Same € prefix on counts | `fmt_int` |
| Pipeline signal mix by DB | Stacked leakage/overstock PNs | **good** | No numeric labels on segments | P2 |
| Sell-through by DB | % bars | **misleading P1** | IRELAND 243% — correct math, looks like broken scale | P2: cap display at 150% with footnote |
| Exception register table | Full drill | **good** | — | — |

---

## 4. `BOOK_B_REVISION_REVIEW_20260819.html`

| Viz | What it shows | Verdict | Flaws | Fix |
|-----|---------------|---------|-------|-----|
| Leakage unit gap by DB | Qty gap by DB | **misleading → P0** | Label said € but values were unit counts (6,227 not €6,227) | Renamed to units + fmt_int |
| Register donut | Row count split | **misleading → P0** | "REVIEW_LEAKAGE: €289" — 289 is rows not euro | fmt_int legend |
| Book B bucket × action stacked | Stacked counts per bucket | **good** | Bucket labels cryptic — OK internal | P2 |
| Recommended action mix | Horizontal count bars | **good** | Long action names truncate | title= OK |
| Revision register table | 500 rows | **good** | — | — |

---

## Cross-dashboard sins (pattern-level)

1. **IUK scale crushes everyone** — any linear DB compare without log scale or ex-IUK inset is a lie by omission. **Fixed P0** in `leakage_db_comparison(log_scale=True)`.
2. **€ symbol on non-€ metrics** — PN counts and row counts wore € prefix. **Fixed P0** via `value_fmt=fmt_int`.
3. **Duplicate pipeline mix** in Command Center (bar + donut + bar again). **Fixed P0** — one bar + one donut.
4. **Treemap "—"** — 88% unmapped AIM looked like missing build. **Fixed P0** — "Unmapped AIM".
5. **Money cards precision** — director wants €573k not €573,277. **Fixed P1** — `fmt_eur_compact` on cards/spark/compare labels.

---

## P2 deferred (not fixed this pass)

1. Radar overlay unreadable with 5 DBs — needs toggle or small-multiples.
2. IRELAND 243% sell-through bar — needs cap/annotation not silent bar to edge.
3. Dec 2025 cliff on monthly line — needs "partial month" footnote.
4. Pricing heatmap colour legend.
5. AIM bars + treemap redundancy on network tab.
6. Hero KPI chips still full € (tables keep full precision — correct).

---

## P2 fixed · 2026-08-19 evening pass

| Item | Fix |
|------|-----|
| Radar spaghetti | `radar_lite_svg` → DB checkbox toggle; default top 3 by gap share visible without JS |
| IRELAND 243% sell-through | `sell_through_bars()` caps display at 200% + footnote with actual % |
| Dec monthly cliff | `line_chart_svg` † on last month + partial-month footnote; sparkline strip same |
| Pricing heatmap legend | `heatmap_color_legend()` on bucket×action heatmap (Book B + Command Center pricing tab) |
| Hero KPI compact € | `fmt_eur_compact` on hero chips (Command Center, Leakage exec, Replenishment) — tables unchanged |
| ITUK dealer top 10 | Leakage exec summary + Command Center network/DB tabs from `replenishment_bridge_ituk_dealer.parquet` |
| Monday action CSV | `01_data/00_derived/leakage_monday_actions_20260819.csv` — top 10 PNs per DB |
| So what callouts | Terracotta `so_what()` under major charts in exec summary + Command Center |
| PN descriptions | Join `pricing_parts_master.parquet` / book_b into exec summary tables |
| Vehicle plain labels | `vehicle_plain_label()` from Book B bucket + AIM with honest VIN footnote |

---

## P2 deferred (remaining)

1. AIM bars + treemap redundancy on network tab — dedupe deferred.
2. GREECE mini overstock € chip on section header — deferred.
3. Pipeline signal mix segment numeric labels — deferred.
2. DB Director leakage vs overstock 2-bar chart + register counts dedupe — deferred.

---

## Verify checklist post-rebuild

```powershell
python 02_dashboards/_build/verify_aftermarket_bi_command_center.py
python 02_dashboards/_build/verify_tier_a_html_json.py
```

Open: sibling `OPEN_*.cmd` in each HTML folder.

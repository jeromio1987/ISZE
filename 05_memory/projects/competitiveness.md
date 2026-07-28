---
topic: competitiveness
read_when: [competitiveness, pricing, iam, aftermarket, autodoc, scraper, ituk]
canonical_metrics: FACTS.md section 7, 02_dashboards/sales/ISZE_Competitiveness_Dashboard.html, 01_data/00_derived/competitiveness_autodoc_risk.csv
last_validated: 2026-07-27
---

# Project: Competitiveness Dashboard

## Status: Active — FY2026 build live, scraper-fed. Channel chain corrected 2026-07-27.

## Canonical file

`02_dashboards/sales/ISZE_Competitiveness_Dashboard.html` — 194 KB, four tabs, title
"ISZE Price Competitiveness Dashboard — FY2026" (mod 2026-07-26).

Tabs: **Competitiveness Heatmap** · **Live Scraper Intel** · **Assumptions & Corrections** ·
**Sources & Assumptions**.

> **Superseded path.** This file previously pointed at `Isuzu/Divers/ISZE_Competitiveness_Dashboard.html`
> (70.7 KB, two tabs, Apr 2026). That artifact is legacy — copies survive at
> `91_legacy/Isuzu/Divers/*.bak` and `07_deploy/Master Dashboard/Divers/`. Do not cite it.

## ✅ FIXED 2026-07-27: channel chain was wrong, now corrected

**Which rule applies here:** this project is an **aftermarket comparison**, so Jerome's rule (b)
governs and **is the one applied throughout this file** — gross genuine → street price via
DB **+40%** then DLR **+27.5%** = **PR00 × 1.785**.

Rule (a) — ISZE's own EUR math, where 35% **margin** means dividing the sales figure by 0.65 —
does **not** apply to this dashboard and must not be mixed in. Any figure here that is not
explicitly on the ×1.785 street basis is not on a channel basis at all.

**What the dashboard actually does:** treats both steps as margins — `÷0.60` then `÷0.725`
(equivalently `×1.667` then `×1.379`) → **PR00 × 2.299**.

That was **~29% high on every street price in the heatmap**, in the direction that makes ISZE look
less competitive than it is. The underlying percentages (40% / 27.5%) are Jerome-confirmed
(30 Mar 2026); it was the **arithmetic form** that was wrong, not the inputs.

**Corrected 2026-07-27.** Both compute sites now read shared constants `CH_DB = 1.40` /
`CH_DLR = 1.275`. Every index dropped by a factor of **0.776**. Logged in the dashboard's own
Section C correction table.

**Second defect found and fixed in the same pass:** the KPI cards (`buildKpis`) were still on
`÷0.60 ÷0.75` — the 30-Mar-2026 move to 0.725 was never propagated there. The KPI bar and the
heatmap table were therefore showing *different numbers for the same parts*. Both now share one
constant, so they cannot silently diverge again.

**Consequence for anything quoted before 2026-07-27:** every exposure index taken off this
dashboard was too high (~22% on table indices, ~20% on KPI figures). Category *rankings* are
unaffected — the factor is uniform — but the RAG thresholds (critical ≥3.0×, exposed ≥1.5×) were
not retuned, so parts have legitimately moved down a band. Re-read before reusing any level.

**Still carrying the bug:** `07_deploy/Master Dashboard/ISZE_Competitiveness_Dashboard.html` and
`07_deploy/publish-site/ISZE_Competitiveness_Dashboard.html` (both 144 KB, 30 Jun 2026 build,
identical divisor code at the same lines). Deliberately not patched — older vintage, and
publish-site is outward-facing. Re-deploy from the canonical file rather than editing them.

## What it does

Interactive heatmap: ISZE genuine parts (PR00) vs aftermarket (IAM and OEM-equivalent).

- Segments: D-Max TFR/TFS (LCV) · N-Series NPR/NQR/NRR (MCV) · F-Series FRR/FVR/FVM (HCV)
- Markets: UK / DE / FR
- Price levels: ASC (PR00) → DB → DLR
- Compare modes: IAM retail / IAM → DB trade / OEM-equiv retail / OEM-equiv trade

## Data sources

- **PR00** — `01_data/01_Pricing/IE40 Price list as of 13.03.2026 PR00_3_level_classified_GPT.xlsx`
  (~164.4K lines, EUR). Same canonical file as [[pricing-basket-2026]]; re-confirmed canonical
  2026-07-14. **The price list itself has not changed since 13-03-2026** — a "new price file"
  is not an open action on this project.
- **D-Max AM (high-confidence rows)** — Autodoc UK scrape 9 May 2026, GBP × 1.17
  (300 PNs queried, 110 priced). Supersedes the Feb–Mar 2026 ×1.18 estimate.
- **Live IAM feed** — KS · Tranzparts · TMC · Mekonomen · Auto365, freshness in
  `04_tools/autodoc_scraper/scrape_asof.json` (refresh_status `done_2026-07-26`).
- **Autodoc Class C tables are frozen** — Cloudflare-retired. `autodoc_results.csv` is stuck at
  30 May 2026 and feeds `03_analytics/Isuzu/prism/scripts/build_competitiveness_autodoc_risk.py`
  → `01_data/00_derived/competitiveness_autodoc_risk.csv` (substitution flag: competitor < 75% of PR00).

## Data confidence — read before citing externally

- **D-Max (LCV) = HIGH on inputs.** Confirmed IE40 PNs + live AM scraper data. Still carries the
  chain-factor error above.
- **N-Series (MCV) = ESTIMATE ONLY.** Segment assignment by price cluster; no PN→model map
  without EQ-HIT. No live scraper run for N-Series fitment.
- **F-Series (HCV) = ESTIMATE ONLY.** Thin HCV aftermarket, AM values approximate.

**Do not quote N-Series or F-Series indices to distributors, IML, or senior management without
EQ-HIT PN validation first.** F-Series must not appear in any external document.

## Highest-risk assumption (after the chain factor)

**IAM trade discount to DB = retail × 0.65 (35% off)** — UK motor-factor industry estimate,
*not verified against ITUK actual purchasing data*. If the real discount is 40–45%, every
IAM→DB index understates genuine exposure. Note this pushes the **opposite** way to the chain-factor
error — the two partially offset, which is exactly why neither should be left unresolved.

Secondary unverified: OEM-equiv trade ×0.72 · DE market = UK AM ×0.92 · FR market = UK AM ×1.05
(both rough, no live DE/FR search — directional only).

## Mar 2026 v1 findings — SUPERSEDED, do not cite

The old exposure figures in this file (D-Max brake disc 1.9× / pads 2.3×, EGR 1.27×, cabin
filter 1.17×, ball joint 1.0×; N-Series EGR 4HK1 1.16×, brake disc 1.27×) were computed on the
v1 chain and the pre-9-May AM basis (×1.18), and inherit the chain-factor error. Do not quote
them as levels.

Directionally intact and re-derivable: PMS filters are where genuine competes well; brakes are
where D-Max is most exposed; F-Series is more competitive on brakes (fewer AM brands).

## What would make it better

1. **Re-deploy the two `07_deploy` copies** from the corrected canonical file (they still carry the old chain)
2. **EQ-HIT access** — PN → model → service interval mapping; lifts N-Series/F-Series out of estimate status
3. Verify the IAM→DB 0.65 discount against ITUK actual purchasing data
4. SAP export with customer invoice data — actual market pricing vs PR00
5. Live DE/FR scrape to replace the ×0.92 / ×1.05 market factors
6. Distributor feedback on where they lose deals

## Connections

→ Supports ITUK pricing conversations (ISZE is competitive on many parts)
→ Feeds PMS coverage narrative — genuine IS competitive on filters ([[pms-coverage]])
→ Supports Action Plan campaigns (target the exposed categories)
→ Scraper health and refresh mechanics: [[project_scraper_refresh_pipeline]]

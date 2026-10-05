# FIX_LOG — next 10 HTML (2026-09-19)

Against `ISZE_HTML_DASHBOARD_FIX_BRIEF.md` non-negotiables.

## 01_ISZE_Exec_Aftersales_Paper.html
- **Was wrong:** Banned sell-out/sell-through/parc/Book B; five-DB 54.4% ignored Portugal long; no basis strip.
- **Fixed:** Spoken labels; Portugal included → 60.0% coverage (DE+BE → 75.1%); basis strip; modelled ceiling labelled.
- **Left / disagreed:** Replenishment exception row count (1,595) still reflects the operational extract vintage — not re-counted in this pass.

## 02_ISZE_Leakage_Cockpit.html
- **Was wrong:** Generic 'leakage / won and lost / unbought' framing; risk of reading gaps as additive observed loss.
- **Fixed:** Retitled opportunity cockpit; non-additive banner; unbilled modelled demand; basis strip; shell language only.
- **Left / disagreed:** Full payload rebuild deferred. Source labels.mjs updated for next rebuild.

## 03_Warranty_Commercial_Review.html
- **Was wrong:** Used 'wallet' in shared headings.
- **Fixed:** Target spend wording; basis strip.
- **Left / disagreed:** Underlying JSON keys still use target_wallet_eur (pipeline).

## 04_ISZE_AIM_Classification_Paper.html
- **Was wrong:** Missing basis strip; possible spoken-label drift.
- **Fixed:** Basis strip + language pass.
- **Left / disagreed:** No material gap-hero issues found.

## 05_ISZE_AIM_vs_Price_Class_Case.html
- **Was wrong:** Risk of factor-first language; missing basis.
- **Fixed:** Margin tip + basis + language pass.

## 06_ISZE_Pricing_Policy_Paper_REV3.html
- **Was wrong:** Book B / spoken-label risk; missing basis strip.
- **Fixed:** Language pass + policy basis strip.
- **Left / disagreed:** REV3 label retained.

## 07_ISZE_Pricing_Revision_AIM_Source.html
- **Was wrong:** Shell wording risk; no basis strip.
- **Fixed:** Shell language + basis; embedded JSON payload left intact (field names).
- **Left / disagreed:** Full rebuild of AIM source dashboard not run in this pass (6MB payload).

## 08_ISZE_Price_Increase_5pct_Flat_REVIEW_2026-09-17.html
- **Was wrong:** Scenario could be read as committed policy.
- **Fixed:** Scenario banner + basis strip + language.

## 09_ISZE_Competitiveness_Dashboard.html
- **Was wrong:** Street wording in channel chain footnotes.
- **Fixed:** Reference dealer price; basis strip; language pass.
- **Left / disagreed:** Cross-nav links outside pack unchanged.

## 10_Dealer_Sellout_AIM_GPS_ITUK_UTI_2025.html
- **Was wrong:** Headline 'Network' / sell-out UI; overclaim risk.
- **Fixed:** Sales to dealer wording; observed-subset labels; basis strip; UTI≠UMI / ITUK≠IUK restated.
- **Left / disagreed:** Filename still contains Sellout (lineage only).

## Cross-page disagreements / notes

- **Portugal coverage:** Portugal `dealer_sellout_long_PORTUGAL_CY2025.csv` exists. Exec paper coverage updated from five-DB 54.4% → six-DB **60.0%** of the controlled €30.76M GPS billed book; DE+BE still lifts to **75.1%**. Controlled CY2025 ceiling figures unchanged (€55.253M / 55.7% / €24.497M gap).
- **Leakage Cockpit:** Full node rebuild not required for this review deliverable; UI strings patched on the snapshot. `labels.mjs` source updated so the next extract/build keeps the new wording.
- **Pricing Revision AIM Source:** Embedded JSON payload not rewritten (avoids breaking field names); shell only.
- **Filename `Dealer_Sellout_*`:** Kept for lineage; UI says sales to dealer.

## Live originals overwritten (Jerome ask)

Each fixed file was copied onto its original `02_dashboards/` path:

- `C:\Users\jerom\Desktop\claude\ISZE\02_dashboards\sales\ISZE_Exec_Aftersales_Paper.html`
- `C:\Users\jerom\Desktop\claude\ISZE\02_dashboards\sales\ISZE_Leakage_Cockpit.html`
- `C:\Users\jerom\Desktop\claude\ISZE\02_dashboards\sales\Warranty_Commercial_Review.html`
- `C:\Users\jerom\Desktop\claude\ISZE\02_dashboards\sales\ISZE_AIM_Classification_Paper.html`
- `C:\Users\jerom\Desktop\claude\ISZE\02_dashboards\sales\ISZE_AIM_vs_Price_Class_Case.html`
- `C:\Users\jerom\Desktop\claude\ISZE\02_dashboards\pricing\ISZE_Pricing_Policy_Paper_REV3.html`
- `C:\Users\jerom\Desktop\claude\ISZE\02_dashboards\pricing\ISZE_Pricing_Revision_AIM_Source.html`
- `C:\Users\jerom\Desktop\claude\ISZE\02_dashboards\pricing\ISZE_Price_Increase_5pct_Flat_REVIEW_2026-09-17.html`
- `C:\Users\jerom\Desktop\claude\ISZE\02_dashboards\sales\ISZE_Competitiveness_Dashboard.html`
- `C:\Users\jerom\Desktop\claude\ISZE\02_dashboards\sales\Dealer_Sellout_AIM_GPS_ITUK_UTI_2025.html`

GPT pack copies refreshed in parallel.

## Visual QA notes (2026-09-19)

- Screenshots: 10 taken, 10 image-read under `_qa/*_viewport.png`. Suite receipt: `SUITE.SHIP_RECEIPT.json`.
- Exec / Leakage / Dealer / Pricing Policy / 5pct / AIM case: first viewport paints with basis strip; no blank shells.
- Pricing Revision AIM Source: charts and KPIs paint; bar chart continues below fold (expected).
- Warranty: KPI cards paint; ten-line bar charts start on first viewport and continue below fold.
- AIM Classification: hero paints; lower card body text is tight at fold (pre-existing density, not blank).
- Competitiveness: fixed preload key alias (`../Data/...` vs `Data/...`) so file:// loads. KPIs now paint.
  Autodoc Class C table still shows bad scrap mins (€2.34) / 0% ratios — scrap data quality, not this language pass.

## Builders touched (for next rebuild)

- `02_dashboards/_build/build_exec_aftersales_paper.py` — rebuilt live, then basis strip polished onto copy/live
- `02_dashboards/_build/build_warranty_commercial.py` — rebuilt + basis strip
- `02_dashboards/_build/leakage/labels.mjs` — title/nav wording (full node rebuild deferred)
- `03_analytics/Isuzu/prism/scripts/build_dealer_sellout_aim_gps.py` — HTML strings patched (full data rebuild deferred this pass)

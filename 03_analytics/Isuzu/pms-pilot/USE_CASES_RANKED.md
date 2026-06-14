# ISZE Use Cases — Ranked by ROI vs Token Usage

**Inventory scanned:**
- ✅ ISZE prism Streamlit pages (9): UIO, GPS, PMS, BVP, Strategic, Scorecard, AIM_Review, ASP_Monitor, Review_Pack
- ✅ HTML dashboards (13): AIM, UIO v11/v17, AI Tools, Price Competitiveness, FY26 Year-End, Monthly Sales, Plan Tracker 2030, UTI SPA, Tender Monitor, Legal Map, ITUK ZEV, Mission Control
- ✅ Snap-on EPC (catalogue tool, anti-bot-throttled)
- ✅ BVP Parts Catalog Excel (31 sheets, all 27 BVP categories, full attributes)
- ✅ Sales data: `sales_fact.parquet` (434k rows) + `sales_with_crossref.parquet` (35k BVP-paired)
- ✅ Eucon (referenced in file v3 changelog — assumed available)
- ⚠️ Actual cloud Power BI reports — not accessed (paste screenshots if relevant)

**Token tiers:** 🟢 LOW (<5k) · 🟡 MED (5-30k) · 🔴 HIGH (>30k)
**ROI tiers:** ★★★ HIGH (ITUK / Kosha / mgmt ask) · ★★ MED (dashboard quality) · ★ LOW (hygiene)

---

## Ranked use cases — highest ROI ÷ tokens first

### Tier S — top of every list (do these first in your 1h window)

| # | Use case | Token | ROI | Why top |
|---|---|---|---|---|
| 1 | **BVP Addressable Basket per distributor** (Cursor brief already written, sitting at `prism/docs/cursor_brief_bvp_addressable.md`) | 🟢 | ★★★ | Already specified. Cursor does the build. Unlocks the dashboard expansion. Zero further effort from you. |
| 2 | **Genuine PMS "white space" map per distributor** — for each (distributor × subgroup), flag zero-Genuine-sales as either out-of-market or price-killed. Pure SQL/Python on `sales_fact` + BVP catalog. | 🟢 | ★★★ | Direct input to ITUK pricing. Shows where Genuine is uncompetitive even where market exists. |
| 3 | **Pricing-gap per Genuine↔BVP pair** — for the 544 pairs, compute price ratio (Genuine €/unit ÷ BVP €/unit). Identify pairs where BVP is winning on price. | 🟢 | ★★★ | Foundational for the "is Genuine pricing killing us?" argument. Direct quantification. |
| 4 | **YoY Genuine vs BVP momentum (substitution detector)** — already exists in `mix_genuine_bvp_*` but rarely surfaced. Build one-page export ranking distributors by "Genuine declining + BVP rising" signal. | 🟢 | ★★★ | The smoking-gun chart for management. |
| 5 | **ITUK SPU/GPS vs network median per PMS subgroup** — extends existing GPS dashboard with subgroup detail. Quantifies "ITUK is paying X% more than network median for fuel filters." | 🟢 | ★★★ | Hard data appendix for ITUK position paper. |

### Tier A — high ROI, manual or single-pass

| # | Use case | Token | ROI | Why |
|---|---|---|---|---|
| 6 | **Per-vehicle PMS basket for ITUK** (EPC manual click-through, ~30 min). 5-10 catalogue editions × 4 PMS FIGs. Output: "what NPR75 RHD 2016 EURO6 owners should actually buy" sheet. | 🟡 | ★★★ | Concrete deliverable for ITUK conversation. Manual = no anti-bot fight. |
| 7 | **Kosha plan PMS gap quantification** — combine UIO × frequency × ASP × (1 − current capture) per distributor, scaled to network. Single number: "€X locked up if every distributor matched best-in-class BVP penetration." | 🟢 | ★★★ | Direct input to Kosha narrative. |
| 8 | **Cross-dashboard KPI consistency audit** — UIO, AIM, BVP, ASP, GPS each compute "capture", "share", "gap" — verify they use the same definitions. Single doc, ~30 row table. | 🟡 | ★★ | Prevents "the number is different in this report vs that one" blow-ups in meetings. |
| 9 | **Dashboard rationalisation map** — 13 HTML + 9 prism + various Excel = which overlap? Which are stale? Which should retire? Single matrix. | 🟡 | ★★ | Clears clutter. Important pre-deployment hygiene if Mission Control becomes the single front door. |
| 10 | **AIM Dashboard ↔ BVP cross-link** — for each product family, AIM tells you which IAM brand is competing; BVP tells you ISZE's own competitive offer. Highest substitution opportunity = AIM-heavy + low BVP penetration combos. | 🟢 | ★★ | Tactical "where to push BVP" map. |

### Tier B — useful, defer if time-poor

| # | Use case | Token | ROI | Why |
|---|---|---|---|---|
| 11 | **OE-only basket per distributor** — the 400k non-BVP-paired sales. What % of revenue is uncontested OE (engine internals, body, hoses)? Per distributor. | 🟢 | ★★ | Frames how much of the business is "safe" vs IAM-exposed. |
| 12 | **FY26 year-end review enrichment** — pull BVP white-space + addressable basket findings into the existing FY26 deck. | 🟡 | ★★ | Year-end narrative material. |
| 13 | **Master Dashboard refresh** — wire latest BVP + PMS + ITUK pricing findings into Mission Control single-page view. | 🟡 | ★★ | Personal-cockpit polish. |
| 14 | **ITUK pricing position paper data pack** — single Excel/PDF combining GPS, ASP, BVP penetration, DVLA fleet (22,389), price-leakage, PMS gap. One artifact for the conversation. | 🟡 | ★★★ | High value AS a deliverable; Tier B because pieces 1-7 above feed into it — sequence after them. |
| 15 | **Newest P/N reconciliation via EPC (spot)** — pick 30-50 PNs flagged stale in v7, verify via EPC manual lookups, patch the file. | 🟡 | ★ | Hygiene. Only valuable if FIG-KEY sheet keeps being used. |
| 16 | **Companion-parts kit definition for top 10 PMS PNs** — manual EPC click-through to capture drain plug / gasket / washer per oil-filter PN. | 🟡 | ★ | Enables "sell the kit not the filter" sales narrative. Not urgent. |
| 17 | **AdBlue/UREA filter quick-win sheet** — single PN (€79k Genuine lifetime), Euro 6-only, find which distributors sell it vs which should. | 🟢 | ★★ | Tiny scope, fast win. |

### Tier C — skip unless someone asks

| # | Use case | Token | ROI | Why skip |
|---|---|---|---|---|
| 18 | **Bulk EPC scrape of all 254 newest PNs** | 🔴 | ★ | Anti-bot blocks it. We already proved this. |
| 19 | **IAM/TecDoc cross-ref bulk pull** | 🔴 | ★★ | Snap-on doesn't expose it; would need Eucon API. Worth a separate Eucon-feasibility task first. |
| 20 | **Build new dashboards from scratch** | 🔴 | ★ | You already have 22 of them. Rationalise (#9) before adding. |

---

## What I'd do in the 1-hour fresh-token window

If it were my budget:

1. **#2 + #3 + #4 + #5 in one Python pass** (~10-15 min). All four read the same parquets, share the same join logic. One script, four outputs, one Excel deliverable. Token cost: ~10k total.
2. **#7 (Kosha PMS gap one-number)** — extends the same script. ~5 min more. ~3k tokens.
3. **#10 (AIM↔BVP cross-link map)** — already-computed data, just join & sort. ~5 min. ~2k tokens.
4. **#17 (UREA quick-win)** — 1 PN, 5-min sanity check. ~1k tokens.

Total budget: ~25 min wall-clock, ~16k tokens. **Output: 7 high-ROI deliverables in one window**, leaving plenty of buffer for clarifications and a second round.

Manual / Cursor-side (no token cost to you here):
- **#1** ships when Cursor consumes the brief.
- **#6** is your 30-min EPC click-through whenever convenient.

---

## What I'd actively defer

- Anything in Tier C — wrong tool, throttled, or duplicative
- #15, #16 — useful but not on the critical path for the ITUK conversation
- #13 Master Dashboard polish — wait until #1 lands so there's actual new data to pull in
- New Cursor briefs beyond the one already written — let the addressable-basket build complete first

---

## File output if we proceed with my recommendation

**Single Excel:** `ISZE_ITUK_DataPack_v1.xlsx` with sheets:
1. `WhiteSpace_PerDistributor` (#2)
2. `Pricing_Gap_Pairs` (#3)
3. `Substitution_Momentum` (#4)
4. `ITUK_vs_Network_PMS` (#5)
5. `Kosha_Gap_OneNumber` (#7)
6. `AIM_BVP_Cross` (#10)
7. `UREA_QuickWin` (#17)

Each sheet ≤ 300 rows, all derived from already-on-disk data. Self-contained appendix for ITUK / management / Kosha conversations.

**Ready to start?**

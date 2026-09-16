# V3 → V4 tabs fix — cause + what was restored

**Date:** 2026-08-25  
**Files:** `build_dashboard_v4.py` → `isze_dashboard_v4_opportunity.html`  
**Open:** `OPEN_isze_dashboard_v4_opportunity.cmd`

---

## 1. What v2 / v3 had (tabs + sheets)

### Dashboard UI tabs (`isze_dashboard_v2.html` / `build_dashboard_v2.py`)

| Tab | Purpose |
|---|---|
| **Executive** | Headline cards, action queue, decision mix |
| **Bid Desk** | Owner / desk / enrich lanes |
| **Opportunity Pipeline** | Filterable opportunity (or raw notice) table |
| **Scoring Guide** | Plain + detailed Fit / Win / Econ explainer, decision thresholds, evidence labels |

Supporting copy lived *inside* the Scoring Guide tab (“How tenders are scored”), not as a separate “How tenders work” product explainer.

### Excel workbook sheets (`isuzu_tenders_v3.xlsx`)

| Sheet | Role |
|---|---|
| UK Tenders | Find a Tender |
| UK Contracts Finder | UK CF |
| EU TED Tenders | TED Europa |
| Germany National | DE national |
| Norway Doffin | Nordics |
| Finland HILMA | Nordics |
| Israel Tenders | IL |
| Belgium | BE |
| Netherlands | NL |
| France BOAMP | FR |
| Poland BZP | PL |

These are **source worksheets**, not dashboard tabs — but operators treated “tab sheets” as either UI tabs *or* xlsx sheets. v4 showed neither as a navigable explainer.

---

## 2. What v4 kept vs dropped

| Surface | v4 before this fix | After fix |
|---|---|---|
| Opportunity table + GPS / vehicle KPIs | Kept (single long page) | **Opportunities** tab |
| By market + coverage | Kept (same page, above table) | **By market** tab (simplified: Vehicle potential primary, GPS € secondary; detail cols behind toggle OFF) |
| Aftersales chips / Fleet early / IDS / product-fit | Kept (sibling ships) | Preserved |
| Scoring Guide / Fit·Win·Econ | **Dropped** | Restored as **Method / scoring** |
| Plain-English “how tenders work” | **Never ported** | New **How tenders work** tab |
| Sources / health detail | Banner only | **Sources / health** tab + banner |
| Excel sheet inventory | Invisible in UI | **Export / Data sheets** tab |

---

## 3. How the error happened (plain English)

v4 was **rebuilt as a single “addressable opportunity” surface** focused on GPS €, product-fit, and later vehicle potential. The builder intentionally stopped cloning the v2 tab chrome (Executive / Bid Desk / Pipeline / Scoring Guide).

That was a **scope cut, not a tender-engine failure**. Notices still scrape, score, and size. What disappeared was the **operator education layer**: no Scoring Guide tab, no glossary of notice / CPV / fleet / unsized, and no link from the UI to the multi-sheet Excel workbook. Stale “€30k GPS” copy in older method notes made it worse — live floor is ~€1,488 with vans excluded.

---

## 4. What was restored (crystal clear)

Top nav on v4:

1. **Opportunities** — hero KPIs (18 addressable vehicles first), GPS explain, opportunity table (Fleet + Aftersales early; 39/228 aftersales)
2. **How tenders work** — notice, CPV, deadline, fleet vs GPS €, product segments, **aftersales play** note, live counts (~228 / 18 / €1,488)
3. **By market** — Vehicle potential (terracotta) primary; GPS € secondary; detail columns toggle default OFF (no 10-column sprawl)
4. **Sources / health** — full `_source_health.json` table
5. **Method / scoring** — Fit / Win / Econ + thresholds (from v2 guide) + GPS product-fit note
6. **Export / Data sheets** — `isuzu_tenders_v3.xlsx` sheet names + row counts + pointer to `isze_dashboard_v4_opportunities.xlsx`

**Preserved intentionally:** IDS linkage, product-fit gate, FR/PL merge rows, Aftersales chips, vehicle-potential hero, simplified market table.

---

## 5. Verify

```text
grep -c "How tenders work\|switchView\|workbook_sheets\|aftersalesChips\|th-veh" isze_dashboard_v4_opportunity.html
# tabs present; Aftersales + Vehicle potential still in builder + HTML
```

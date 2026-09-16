# CV tender investigation — urgent

**Date:** 2026-08-25  
**For:** Jerome  
**Install:** `C:\Users\jerom\Desktop\claude\ISZE\04_tools\ISZE_Tender_Monitor_Install\`  
**Live feed:** `C:\Users\jerom\Desktop\claude\ISZE\01_data\14_dashboards\tender_data.json`  
**Dashboard:** `C:\Users\jerom\Desktop\claude\ISZE\04_tools\ISZE_Tender_Monitor_Install\isze_dashboard_v4_opportunity.html`  
**Open:** double-click `C:\Users\jerom\Desktop\claude\ISZE\04_tools\ISZE_Tender_Monitor_Install\OPEN_isze_dashboard_v4_opportunity.cmd`

---

## Verdict

**CV present** — not stripped by the Isuzu gate, not missing from sources, not wiped by product-fit.

There are **130** opportunity rows with `product_segment` ∈ `{pickup, truck}` out of **228** total (post-gate). Germany matches the expected mix: **5 pickup / 17 truck**.

What looked like “no CV” was almost certainly a **definition / filter / search trap**, not an empty pipeline:

| Trap | What happens |
|---|---|
| KPI **Addressable vehicles (pickup/truck) = 18** | That is a **fleet-unit sum** on 8 notices with an extracted count — **not** the tender count. Tender count = **130**. |
| Filter **Has GPS € only** | Only **3** rows (all truck). 127 CV rows have null GPS € for honest reasons (no fleet / no SPU map). |
| Search box **`CV`** (before fix) | Matched only **`lcv_van`** via the substring inside **“LCV”** — **0** pickup/truck. Fixed this rebuild. |
| Expecting a column literally named “CV” | Engine label is **Product** = Pickup / Truck / Postal van / … |

---

## Exact figures (rebuild 2026-08-25T… from live JSON)

| Metric | Value |
|---|---:|
| Notices (post gate) | 254 |
| Opportunities (post gate) | 228 |
| Gate dropped opportunities | **1** (UK “Fleet Management Services”, segment `rm_only` — **not** CV) |
| Gate dropped pickup/truck | **0** |
| **pickup** | **48** |
| **truck** | **82** |
| **CV = pickup + truck** | **130** |
| lcv_van | 48 |
| rm_only | 5 |
| weak | 45 |
| Addressable vehicles KPI (fleet sum pickup/truck) | 18 (8 rows) |
| Stated fleet all segments | 156 (15 rows) |
| CV with GPS € | 3 |
| CV with extracted fleet | 8 |
| CV decision mix | Ignore 98 · Watch 26 · Selective 6 |

### By country (pickup / truck)

| Market | Pickup | Truck |
|---|---:|---:|
| Poland | 14 | 6 |
| France | 2 | 20 |
| Germany | 5 | 17 |
| Czechia | 6 | 7 |
| Belgium | 1 | 6 |
| Romania | 5 | 3 |
| Italy | 1 | 5 |
| + others | … | … |

---

## Top CV examples (real rows in this snapshot)

Use Product filter **CV (pickup + truck)** — or search `CV` after this rebuild.

| # | Seg | Country | Fleet | Decision | Title (short) | Buyer | Link |
|---|---|---|---:|---|---|---|---|
| 1 | truck | France | 3 | Watch | Location 3 camions 7/8T benne ampliroll | Régie La Créole | https://www.boamp.fr/pages/avis/?q=idweb:26-81250 |
| 2 | truck | France | 3 | Selective | Repair/maintenance + LLD camions (TED) | Régie La Créole | https://ted.europa.eu/en/notice/-/detail/574767-2026 |
| 3 | truck | Germany | 3 | Ignore | 3× Elektro-Transporter DoKa-Pritsche Kipper | Stadt Solingen | https://ted.europa.eu/en/notice/-/detail/531382-2026 |
| 4 | pickup | Poland | 3 | Ignore | 3 pick-up terenowych | KW PSR Wrocław | https://ted.europa.eu/en/notice/-/detail/544668-2026 |
| 5 | truck | Germany | 2 | Ignore | 2 LKW mit Kran und Abrollk | Bauamt Passau | https://ted.europa.eu/en/notice/-/detail/580242-2026 |
| 6 | pickup | Poland | 2 | Ignore | 2 szt. pick-up policyjnej | Komenda Stołeczna Policji | https://ted.europa.eu/en/notice/-/detail/575258-2026 |
| 7 | pickup | France | 1 | Selective | Pick-Up Nacelle | CACEM Martinique | https://www.boamp.fr/pages/avis/?q=idweb:26-83096 |
| 8 | truck | Romania | 1 | Ignore | Flatbed / ridicari autovehicule | Municipiul Bacău | https://ted.europa.eu/en/notice/-/detail/517726-2026 |
| 9–15 | truck | FR/BE | — | mostly Ignore | camion / vrachtwagen / BOM / châssis cabine 26T | various | BOAMP / publicprocurement.be |

Full table: open the dashboard → Product → **CV (pickup + truck)** → sort Fleet.

---

## Investigation checklist

### 1. Live feed contents
- Live JSON + embedded v4 DATA both carry the segment mix above.
- No invented notices; counts taken from `isze_dashboard_v4_data.json` after rebuild from live `tender_data.json`.

### 2. UI hiding?
- Default filters are **All** (country / decision / GPS / segment / aftersales).
- Default sort is **Fleet desc** (market-simplify already in builder).
- With defaults, CV rows are visible (130 of 228; trucks dominate top when fleet-sorted).
- **Not** Watch-only by default.
- Clear traps: **Has GPS € only** (3 rows) and old search **`CV` → vans only**.

### 3. Isuzu gate / product-fit
- Pre-gate live opps: 229 → post-gate: 228 (−1 `rm_only` UK).
- Re-gate on v4: would drop **0**; CV among drops: **0**.
- Product-fit only nulls **GPS €** for van/weak/rm — it does **not** remove pickup/truck rows from the table.

### 4. Source coverage
- `isuzu_tenders_v3.xlsx`: EU TED ~605 rows; FR BOAMP 20; PL BZP 23; BE 9; DE national sheet nearly empty (DE CV arrives via **TED**, not the national sheet).
- Vehicle-ish keyword density on TED is high; many are filtered earlier by CPV/score/gate into the commercial shortlist that becomes the 254 notices — **not** a silent wipe of truck/pickup after they land in v4.

### 5. Definition: what “CV” means here

| Jerome may mean | Engine field | Count this snapshot |
|---|---|---:|
| Medium/heavy + pickup commercial (Isuzu addressable shape) | `pickup` + `truck` | **130** |
| Postal / panel vans | `lcv_van` | 48 |
| Fleet units with a published count (pickup/truck only) | KPI addressable vehicles | **18** |
| Rows with GPS € | GPS-sized | **3** |

Vans are **not** counted as CV in the new Product filter **CV (pickup + truck)**.

---

## Fix shipped (UX only — no fake tenders)

In `build_dashboard_v4.py` → rebuilt HTML/JSON/XLSX:

1. Product filter option **`CV (pickup + truck)`**.
2. Search `CV` / `commercial vehicle` maps to pickup+truck (no longer LCV substring trap).
3. Opportunity-table hint text documents the CV count.

Preserved: IDS dealer column, addressable-vehicle KPIs, aftersales tags, product-fit GPS gate, market why-blank chips, source-health banner.

---

## Where to look (operator)

1. Double-click `OPEN_isze_dashboard_v4_opportunity.cmd`
2. Opportunity table → Product → **CV (pickup + truck)** → footer should show **130 of 228**
3. Or type **`CV`** in search
4. For Germany: Country = Germany + Product = CV → **22** rows (5+17)
5. Do **not** use **Has GPS € only** if you want the full CV list

**CV count to quote:** **130 tenders** (48 pickup + 82 truck). KPI **18** = addressable *vehicles* with a published fleet count, not tender volume.

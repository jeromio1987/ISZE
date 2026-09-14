# ISZE BI framework (critical)

**Last updated:** 2026-09-14  
**Audience:** Jerome’s job first (list price, %GM, GPS, official Power BI). Builders second.

This file is the filter. If a number does not sit on a layer below, it is not a KPI for a sales review or a pricing conversation. The 2026-08-19 aftermarket build menu is a **build list**. This file is **which numbers to quote**.

Formulas live in `03_analytics/Isuzu/prism/docs/metric_dictionary.md`. Do not quote a formula as a headline if it fails a rule in §0.

---

## 0. Rules that apply to every number

1. **Fiscal year first.** GPS and Power BI: **FY2026 = 1 April 2025 – 31 March 2026** (complete). **FY2027 = 1 April 2026 – 31 March 2027** (billing exists through June 2026). Calendar year is not the default. Sales-review packs that still say calendar H1 are the old grain — do not rebuild until asked.
2. **Euros first.** Name the part in words. Piece counts are not a headline. A gasket and a cab are not comparable in pieces.
3. **Never blend** UTI with UMI, IUK (UK pickup) with ITUK (UK truck), Ireland with IUK. MIDI / Spain is not this book.
4. **Do not invent official sales from SAP** when the Power BI row is missing. Skip the official slide.
5. **Sales-to-dealer pieces are not a KPI.** Billed vs sales-to-dealer in pieces is stock movement (destock / restock). It is not lost sales, not a work list, and not a reason to change list price. If mix is needed, use **euros**, and only where that file exists (UK pickup, UK truck, Ireland, UTI, Greece).

### Label conversion (builders only)

| Window | GPS / Power BI name | Billing integer `fiscal_year` |
|--------|---------------------|-------------------------------|
| 1 Apr 2024 – 31 Mar 2025 | FY2025 | 2024 |
| 1 Apr 2025 – 31 Mar 2026 | FY2026 | 2025 |
| 1 Apr 2026 – 31 Mar 2027 | FY2027 | 2026 |

Do not write “FY2025” for April 2025–March 2026 in a brief. That is the billing integer, not the GPS name. Code: `03_analytics/Isuzu/prism/modules/fiscal.py`.

---

## 1. The stack (top to bottom)

Use in this order. Lower layers do not override a higher one.

### L0 — Official

**Question:** did this distributor beat budget and last year, in the FY months on the slide?

**Metric:** Power BI **sales / budget / last year**, same months.

**Need:** the published monthly row for that distributor. Same shape as the IUK row (three columns per month).

**Without it:** skip the official slide. Do not fill from SAP.

**ITUK:** this row is missing. Sold-to **2575** is already set. GPS is fiscal. The only ask is the Power BI months for Isuzu Truck UK.

### L1 — GPS wallet

**Question:** how much of the fleet parts potential did we bill this FY?

**Metric:** billed net (ex-warranty) ÷ fleet potential. Show **%** unless it is over 100% — then show **amount**, do not plot a fake “best”.

**Need:** signed UIO and the published GPS FY figure. Do not invent a calendar GPS %.

**ITUK:** already published on the operating GPS (FY, not calendar). UIO 22,389.

### L2 — Mix in euros

**Question:** of the **money**, how much is genuine, BVP, genuine-with-a-BVP-alternative?

**Metric:** euro share, not piece share. Sales is sales (total first). Genuine mix is an extra lens, not a substitute that hides BVP.

### L3 — List reach and %GM (pricing)

**Question A — list reach:** of billed euros this FY, how much has a list price so %GM can be set, vs how much does not.

**Question B — %GM:** only on the euros that have a list. No list → no %GM. Billed ZPR1 is not a list price. Do not invent one.

**The leftover parts with billed sales and no list price are this layer.** They are not a stock story and not a piece count. Shell oils (`5500*`) stay out of that leftover on purpose.

**FY2026 recut (1 Apr 2025 – 31 Mar 2026):** we billed **€67,318.49** on **21 parts** with no list. Almost all UTI. Two UMI lines. One Kazakhstan transfer. Three parts from the old calendar-2025 list billed only in Jan–Mar 2025 (that is FY2025) — they are not in FY2026. This is about **0.2%** of network billed FY2026. The job is a list price on the money (cabs first), not chasing pieces.

**FY2027 year-to-date (1 Apr – 30 Jun 2026) on the same leftover set:** **€14,722.81** (UTI cabs / sensors / steering, plus one Portugal transfer). Still no list, still no %GM.

### L4 — PMS capture (service parts only)

**Question:** of expected service demand, how much did we sell?

**Metric:** **total** capture first. Skip Best if over 100%. Genuine capture is extra.

### L5 — Warranty vs commercial

**Question:** is this year’s mover a campaign, or commercial sales?

Split warranty euros from commercial before narrating YoY.

---

## 2. What is not a KPI

- Sales-to-dealer **pieces**, or billed pieces vs sales-to-dealer pieces
- Calendar year when GPS / Power BI is FY
- “Hardware PN” as a term — say **parts we billed with no list price**
- Ranking an account that is still buying as lost euros
- Forecast accuracy, mail cycle time, Book B allocation (unsigned)
- Mixing UTI+UMI or IUK+ITUK into one “Israel” or “UK” number next to IDS / GPS

---

## 3. Default period for a distributor review

1. Last complete FY (**FY2026**).
2. Current FY year-to-date next to official Power BI when that row exists (**FY2027 Apr–Jun** today).

Do not lead a review with calendar H1 unless Jerome names that window.

---

## 4. ITUK — have vs need

| Have | Need |
|------|------|
| Sold-to **2575** (not IUK 2574, not MIDI) | **Power BI monthly row** for Isuzu Truck UK: Apr / May / Jun **sales, budget, last year** (Q1 FY2027), same three columns as IUK |
| GPS FY figure, UIO 22,389 | Nothing else to invent a GPS % |
| Billed SAP, warranty grain separate from IUK | Do not use IUK warranty or IUK Power BI for ITUK |
| Sales-to-dealer file exists | Do not use it as a piece KPI |

Until the Power BI row is pasted, the official sales-review slide stays off. SAP billed is not a substitute.

---

## 5. Builder pointers

| Topic | Where |
|-------|--------|
| FY label helpers | `03_analytics/Isuzu/prism/modules/fiscal.py` |
| Leftover no-list billed, FY | `01_data/00_derived/NO_PR00_HARDWARE_FY2026.md` |
| Calendar-2025 leftover (do not quote) | `01_data/00_derived/NO_PR00_HARDWARE_CY2025.md` |
| List-to-pocket coverage (still calendar in the 2026-08-19 pack) | recut to FY before quoting as L3 network % |
| Sales-review windows | `04_tools/db_sales_review/db_profiles.yaml` defaults are still calendar H1 — wrong vs this file until a rebuild is asked |

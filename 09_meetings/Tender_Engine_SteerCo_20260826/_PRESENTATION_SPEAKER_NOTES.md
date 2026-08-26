# Speaker notes — ISZE Tender Engine SteerCo

**Pack:** `C:\Users\jerom\Desktop\claude\ISZE\09_meetings\Tender_Engine_SteerCo_20260826\ISZE_Tender_Engine_SteerCo.html`  
**Open:** double-click `C:\Users\jerom\Desktop\claude\OPEN_ISZE_SteerCo.cmd`  
**Freeze:** 2026-08-25 20:20 Europe/Berlin · overnight runlog **326 notices / 291 opps** · stated fleet p+t **174** · CV opps (pickup+truck) **215** · aftersales **54** · national LIVE **~55%** (16/29)  
**Audience:** SteerCo / management · formal · JP-company register  
**Tone:** Status and progress. Not a product pitch. Not a forecast.

If overnight runlog moved again before the meeting, re-read `_OVERNIGHT_RUNLOG.md` and update the three hero numbers (stated fleet · CV tenders · national LIVE %) before you walk in.

---

## Slide 1 — Cover

**Say:**  
“This is the Tender Engine briefing. Public-procurement radar for Isuzu commercial vehicles and aftersales. Snapshot frozen after Nordics and Denmark national feeds came live. Every figure is labelled so we do not confuse extract with market.”

**Do not say:** market potential, addressable market for the 174, expected revenue.

**If asked “is this revenue?”:** No — radar and desk. GPS € is addressable wallet *if* won.

---

## Slide 2 — Why we built this

**Say:**  
“Public buyers publish LCV, truck and fleet R&M notices every week across our footprint. They sit on TED above threshold and on national portals below threshold. We had no single Isuzu-relevant desk. The engine scrapes, gates noise, sizes GPS only when the notice and the map allow it, and points to a real IDS dealer where rankings exist.”

**One sentence close:**  
“Radar and desk — not a sales forecast.”

**Bridge:** “First: what counts as for us.”

---

## Slide 3 — What “for us” means

**Say:**  
“In: pickup and D-Max-shaped, truck and chassis cab, and real fleet R&M or parts. Out: postal and courier panel vans — Poșta-style utilitare, Transporter, Kastenwagen. Those buyers buy Ford, Fiat, Stellantis, VW. Showing them with GPS blank still wastes the desk. Same for passenger, SEND, route transport, pure tyres.”

**Point to KPIs:**  
“Desk defaults to CV filter. Three van rows left are parts-only survivors. Fifty notices carry aftersales language we actually found in the text.”

**If challenged on postal:**  
“Hard drop is deliberate. Product-fit also blocks van GPS even if a weak row survives.”

---

## Slide 4 — Three layers (critical — slow down)

**Say this verbatim or near-verbatim:**  
“Three layers. Do not conflate them.

(a) Network scale — about twenty thousand LCV and seventy-eight thousand CV per year. Indicative. Ask if stale. Not from this scrape.

(b) CV tenders we currently capture — about one hundred ninety-nine pickup and truck opportunities out of two hundred sixty-five.

(c) Stated fleet units on those notices where a count was printed — one hundred seventy-four units across seventeen notices.

One hundred seventy-four is not one hundred ninety-nine is not seventy-eight thousand.”

**Then:**  
“Earlier extracts showed eighteen. Germany Open Data lifted the extract; Nordics and Denmark added national volume. Still an extract-subset. Still not demand. When (c) is tiny versus (a), the diagnosis is coverage — not a tiny Isuzu market.”

**GPS line:**  
“Sized GPS wallet is about thirty-seven thousand euro a year on ten rows. Addressable if won. Null is not zero. Not expected revenue.”

**Pause.** Let the ≠ line land.

---

## Slide 5 — Coverage reality

**Say:**  
“Why the extract looks small: national LIVE is about forty-one percent of twenty-nine footprint countries — twelve markets, now including Norway and Denmark. Was roughly thirty-four percent before NO+DK. About fifty-two percent are still TED-only for below-threshold. Lead coverage overall is roughly thirty-five to fifty-five percent of the Isuzu-relevant stream — medium confidence.”

**Roadmap, left to right:**  
“Spain PLACSP is code-ready but WAF-blocked on this runner. Germany OV, Romania SEAP, Austria USP are live. Nordics: Norway Doffin and Finland HILMA are LIVE — keys DONE, do not re-ask. Denmark udbud is LIVE. Next probes: Portugal, Hungary, Ireland.”

**If someone wants a big vehicle number:**  
“We will not invent one. Honesty over vanity.”

---

## Slide 6 — Live dashboard walkthrough

**Say / demo:**  
Open the Install dashboard (`OPEN_isze_dashboard_v4_opportunity.cmd`).

1. **Opportunities** — hero chips; hover tooltips explain formulas; CV filter on.  
2. Type **CV** in search or leave product filter on CV.  
3. Filter **Aftersales** — fifty hooks.  
4. Scroll to **IDS dealer** — mapped from five hundred nineteen real dealers; Germany has distributor but no IDS dealer sheet yet.  
5. **Sources / health** — OK vs CODE_READY vs RETIRED (Nordics no longer AWAITING_KEY).  
6. **How tenders work** — same three-layer story baked into the product.

**Timebox:** three to four minutes. Do not drown in Ignore rows.

---

## Slide 7 — Asks

**Say:**  
“Three asks.

One — next portals: unblock Spain, keep Germany healthy, then Portugal, Hungary, Ireland. Nordics keys are CLOSED — do not re-ask.

Two — UMI and IEC: domestic Electric Company tenders are geo-blocked from abroad. The UMI Electric Company vehicle follow-up remains a Bart / UMI commercial open item. It is not a FOUND row in the radar. We need an Israel-side view or UMI confirmation — we will not invent a notice.

Three — criticality: stated fleet in captured notices is not network CV potential. Keep three-layer honesty on every external slide.”

**Close asks:**  
“Everything else is maintain and probe.”

---

## Slide 8 — Appendix A · Method & sources

**Use only if asked “how / from where?”**

**Say:**  
“Thirty-day lookback. TED spine across twenty-nine countries. Selection gate, not-for-us, then product-fit for GPS. Fleet KPI sums extracted counts on pickup and truck only. Germany dominates tonight’s stated fleet — one hundred forty-eight of one hundred seventy-four — including a large conservation framework. Still layer (c).”

**Sources table:** walk OK / CODE_READY / GEO_BLOCKED / RETIRED in one pass. NO/FI/DK are LIVE. No need to read every count aloud.

---

## Slide 9 — Appendix B · Not-for-us gate

**Use only if challenged on postal / vans.**

**Say:**  
“Hard drop means leave the desk. Poșta Română is gone. Remaining van rows are rare parts-only. Complementary product-fit still blocks van GPS.”

**Freeze reminder (optional close):**  
“One hundred seventy-four ≠ one hundred ninety-nine ≠ seventy-eight thousand. National LIVE about forty-one percent. Nordics keys closed. UMI still a human follow-up.”

---

## Q&A crib

| Question | Answer |
|---|---|
| Is 174 our market? | No. Stated fleet in captured notices only. |
| Why so few GPS €? | Need printed fleet + pickup/truck + SPU map. Most notices lack counts. |
| Did coverage improve? | Yes — RO+AT+NO+FI+DK+PT+BG+CZ national LIVE; share ~55% (16/29). Majority of the remainder still dark. |
| When Nordics? | Done. Keys CLOSED. NO Doffin + FI HILMA LIVE. |
| Where is the UMI IEC tender? | Not in scrape. Domestic IEC geo-blocked. Commercial open with UMI. |
| Can we show postal vans “just in case”? | No. Hard not-for-us. |

---

## Deliberately left out of the pack (chat / operator only)

- Agent/browser cookie limits that blocked key capture  
- Internal file/script names as slide heroes  
- Historical buggy GPS totals (€30k with vans) as current commercial floor  
- Personal overnight workspace audit (sales_fact / SaTy) — separate morning brief  

Those stay in Install docs / chat, not on SteerCo slides.

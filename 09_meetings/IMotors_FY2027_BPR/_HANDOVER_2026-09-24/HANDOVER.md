# Handover — I Motors (Astara Portugal) FY2027 Business Performance Review, merged dark deck

Written 24 Sept 2026 from a cloud session that stopped before building anything. Jerome wants the build done in a **local session** on his PC (`C:\Users\jerom\Desktop\claude\ISZE`), where the real files and Outlook are available.

Nothing was built or edited. This folder contains only what was gathered and decided.

---

## 1. What Jerome asked for

Merge the I Motors review decks into **one full deck (~25+ slides)** for Astara Portugal. The deck is also meant to show **Yoshimoto-san (ISZE MD)** how we present, so it has to be clean, external-grade and honest.

1. **Keep the first seven slides of the 685 KB deck**, especially the executive summary with all the KPI tiles. Fix the clipping issues only (see §5).
2. **Whole deck on dark charcoal**, like `user_screenshots/03_PMS_service_demand_cover_slide_dark.png`.
3. On **every insight slide**, use the right-hand **"Observations / Questions" panel** from `user_screenshots/02_observations_panel_style.png`: a red dot for the main signal, amber dots for supporting points and questions to I Motors. Use it for our own observations and questions.
4. **Include the PMS service-demand cover slide** from screenshot 03, which refers to GPS, PMS and UIO. Jerome is **not 100% sure the numbers are right**, so recheck everything. He gives carte blanche.
5. **Use Portugal's own sales-to-dealer data** and **explain in the deck how we used it**, with a method slide. Astara expects real insight from the data they gave us.
6. Come up with **very strong GPS, PMS and sales-to-dealer observations**. Jerome explicitly asked to think hard about these.
7. **New slides**: lubricants centralised purchasing (IML) and R&M contracts (see §4).
8. External language: no "IML v7" or "Model B", no internal model names, no personal names on slides (rule from `00_docs/CLAUDE_DESKTOP_ONBOARDING.md`).

Jerome's working rule: ask questions before building, not rebuild afterwards. The answers already given are in §3.

---

## 2. Files

### In this folder
| File | What |
|---|---|
| `I_Motors_FY2027_Business_Performance_Review_DRAFT_685KB_as_uploaded.pptx` | The **main base deck** (14 slides, white theme, Calibri, 16:9). Jerome uploaded this copy. The original is at `C:\Users\jerom\Desktop\claude\ISZE\I_Motors_FY2027_Business_Performance_Review_DRAFT.pptx` and has **never been pushed to GitHub**. |
| `base_deck_render/r_base_01..14.png` | LibreOffice renders of the base deck. **Calibri was not installed**, so fonts were substituted (DejaVu/Liberation). Text is wider than in PowerPoint, so confirm any clipping in real PowerPoint. |
| `user_screenshots/01_deck_titlebar.png` | Title bar of the deck Jerome means ("the first presentation"). |
| `user_screenshots/02_observations_panel_style.png` | The Observations / Questions panel style to reuse (dark panel, red and amber dots). |
| `user_screenshots/03_PMS_service_demand_cover_slide_dark.png` | The dark PMS table slide to include (from the **140 KB** second draft). |
| `user_screenshots/04_two_draft_files_686KB_140KB.png` | The two DRAFT files on Jerome's PC, both modified 24/09/2026 06:42. |

### Still only on Jerome's PC (not in git)
- The **second draft, 140 KB**, same name `I_Motors_FY2027_Business_Performance_Review_DRAFT…pptx`. It holds the dark style of screenshots 02 and 03. **Open it locally and use it as the dark style reference.**
- `KPI Master File.xlsx`, the source for sales to dealer in €, fill rate, MOS and back orders (slides 2, 5, 6, 7).
- The supplied **I Motors FY2027 sales-plan report**, the source for slides 2–4.
- **Jerome's email to Pedro Serrano (sent 23 Sept 2026)** with R&M questions. **Read it in Outlook** and reuse its questions on the R&M slide.

### In git, but only on branch `origin/cursor/isze-exec-sales-paper-prompt-8dc1` (pushed 23 Sept, not on `main`)
The local PC is probably ahead of both. Check local first.
- `01_data/00_derived/dealer_sellout_long_PORTUGAL_CY2025.csv` (~21.6k lines)
- `01_data/00_derived/dealer_sellout_long_PORTUGAL_CY2026YTD.csv` (~15.8k lines, Jan–Aug 2026)
- `01_data/91_build/normalize_dealer_sellout_portugal.py`, which normalised the source `PORTUGAL_Sales_to_Dealer_2025_2026YTD_Aug.xlsx` (sheets '2025' and '2026': Data da Fatura | Referencia | Sum of Quantidade)
- Genuine/BVP mapping: `01_data/00_derived/genuine_bvp_crossref.(csv|parquet)`, `bvp_pn_dimension.(csv|parquet)`, `mix_genuine_bvp_by_family.csv`, `aim_bvp_family_risk.csv`, `bvp_downtrade_gp.csv`
- Pricing (old vs new, +5% flat increase): `02_dashboards/pricing/ISZE_Price_Increase_5pct_Flat_REVIEW_2026-09-17.html`, `01_data/01_Pricing/Price_Increase_5pct_Flat_REVIEW_2026-09-17.xlsx` (see ROUTING `delegator_pricing_review`: those pricing files are **read-only**)
- Base-deck sources: `ISZE_ZKK_AIM_Independent_Review_Pack/…/source_summaries/01_parts_billed_vs_target_by_market.csv`, `04_original_vs_value_parts_mix.csv`. The files `03_service_capture_by_market_family.csv` and `07_fleet_trucks_in_service.csv` are **not in git**: find them locally.
- Earlier Portugal work worth mining: `04_tools/ppt_template_v2/build_portugal_gps_target_deck.py` (charts: target_bridge, uio_trend, pms_portugal_capture, pms_portugal_filters, h1_category_movers, q1_portugal_monthly), `09_meetings/PORTUGAL_Sales_Review_2026/` (older FY2027 deck + **29 July 2026 minutes**), `01_data/00_derived/pms_briefs/PORTUGAL_pms_capture.md`, `02_dashboards/Data/_OKF_assessment/PORTUGAL_PMS_age_weighted_wear_items.md`, `01_data/08_Distributor/Portugal_annual_km_mileage.md`, IDS 2026 Portugal dealer pack and fiches.

Number hierarchy (CLAUDE.md): green `01_data/00_derived/_verification_report.json` → `metrics_snapshot.json` → `FACTS.md` wins over decks, memory and GPT. **Do not load `01_data/raw/sales/*.XLSX`**; use parquet and derived CSVs. New files go to `01_data/90_INBOX/`.

---

## 3. Decisions already taken with Jerome

| Topic | Decision |
|---|---|
| **Periods** | **We work in fiscal years.** ISZE FY runs **April–March** (FY2027 = Apr 2026–Mar 2027; the deck's "Apr–Sep" = H1, "Oct–Mar" = H2). The base deck's GPS / PMS / fleet slides (8–12) and the screenshot 03 slide are in **calendar years 2023–2025**. Restate them in FY where the data allows, and never mix FY and CY on one slide without labelling it. The sales-to-dealer file is by invoice month, so it can be cut to FY2026 (Apr 2025–Mar 2026) and FY2027 YTD (Apr–Aug 2026). |
| Theme | **Whole deck dark charcoal.** |
| Length | **Full, ~25+ slides** (plus appendix if useful). |
| Obs panel | **Yes on every insight slide.** Red = main signal, amber = supporting point / question. Same position every slide. |
| Audience | For **Astara**; it also serves as a presentation example for **Yoshimoto-san**. External language, no personal names. |
| Genuine-share stretch (+1.8%) | Jerome says **Astara mentioned they could reach that target**, so present it as reachable. ⚠ The 29 July minutes say the opposite ("Astara sceptical… asked ISZE to revisit the genuine-share stretch"). Flag this to Jerome once more before it goes on a slide; the minutes are an auto-transcript. |
| Sales-to-dealer prices | **No prices exist and none will come.** Distributors won't share them (margin, and they fear we'll use it against them). Quantity by PN by month is the maximum we get from most distributors. Work with it. |
| Lubricants slide | One slide: IML centralised lubricant purchasing (for ISZE, Africa, ME) is **postponed**. We are **adding more areas to increase volume and get better prices**. |
| R&M slide(s) | **No contract conditions.** Short **history** of what happened. **Skip the €25k MOU (it never happened).** Mention the **last known contract numbers** and **ask for an update**, and above all ask **how the current R&M programme is going**. Reuse the questions from Jerome's 23 Sept email to Pedro Serrano. |

---

## 4. R&M background (from Jerome's Outlook summary, 24 Sept)

Only for building a short history. **No conditions and no personal names on the slide.**

- **Dec 2024:** Portuguese maintenance-contract programme ("Contratos de Manutenção") collected and translated. Contracts are sold with new vehicles, cover scheduled and corrective maintenance, and have national coverage through the official Isuzu network. (Conditions such as max 5 years / 200,000 km and risk at I Motors are **not to be shown**.)
- **2024–2025:** the "Isuzu Easy Maintenance" programme was being updated; sales plans and presentations for the R&M programme; I Motors worked with **Allianz** on an LCV offer; pricing for new N- and F-Series contracts; ISZE wanted R&M sales targets. The €25k incentive/MOU was discussed but **did not happen**, so don't mention it.
- **Late 2025 → 2026:** the Astara contact moved to the Parts & Accessories Manager; aftersales is also heavily involved.
- **29 July 2026 meeting:** **12 active CV** and **29 active LCV** contracts. Concern about profitability if major engine or transmission failures hit. Customers still require contracts. Allianz not interested at current volume; Real Garant (Zurich-backed) suggested as an alternative partner. ISZE asked for **written feedback on obstacles and weaknesses** in the current offer. Leasing tenders often bundle R&M, leaving fewer R&M opportunities for Astara.
- **July 2026:** Jerome asked whether a public-tender customer was interested in an R&M contract.

Slide asks to Astara: an update on the active contract count since July, how the current programme is performing (sales, penetration on new registrations, claims experience), the written obstacle list, the status of the Allianz / Real Garant track, and the questions from the Pedro Serrano email.

---

## 5. Base deck review (the 685 KB one, 14 slides)

Slides 1–7 are kept, dark-themed and with clipping fixed. Slides 8–14 feed the rest of the deck and must be rechecked.

| # | Title (short) | Keep? | Issues seen in render |
|---|---|---|---|
| 1 | Cover: "I Motors, FY2027 Business Performance Review" | Keep | Date says "Review draft, 23 September 2026": update. |
| 2 | Executive view: 8 KPI tiles + management read + takeaways | **Keep (Jerome's favourite)** | **Title wraps to 2 lines and collides with the red rule** below it: shorten the title or move the rule down. KPI sub-labels are tight in the tiles. |
| 3 | FY27 plan monthly bars (sales / budget / orders) | Keep | **Legend is clipped** under the chart and overlaps the summary box. |
| 4 | H2 recovery requirement | Keep | OK. |
| 5 | Sales to dealer Apr–Aug 2025 vs 2026 | Keep | **Bad clipping:** the three KPI boxes are cut off at the bottom and the big numbers overlap their sub-labels ("Reported sales to dealer", "+25.0% vs comparable period", "May 2026"); the legend square is orphaned; the boxes touch the ISUZU logo. |
| 6 | Individual fill rate line (target 95%) | Keep | Point labels overlap on dips (82%, 90% near the target line). |
| 7 | MOS + back-order lines | Keep | OK. |
| 8 | Fleet context: billed vs vehicles in service | Recheck | See §6. |
| 9 | Commercial potential: billed vs modelled target spend (cover 50.7 → 51.5 → 56.0%) | Recheck | Legend and footer text overlap. |
| 10 | PMS filters: oil / fuel / air cover 2023–25 | Recheck | Legend clipped. |
| 11 | PMS wear parts: pad / rotor / clutch / shoe | Recheck | Legend clipped. |
| 12 | Genuine & BVP evolution + family table | Recheck | Legend overlaps the BVP-share line. |
| 13 | Three discussion priorities | Rework | Cards are half empty. |
| 14 | Action points table | Rework | Fine; merge with the new asks. |

Every slide has a "TAKEAWAYS" column on the right. For insight slides, replace it with the dark **Observations / Questions** panel (screenshot 02).

### Text of the Observations panel in screenshot 02 (style reference; the content belongs to the GPS/target-spend slide)
- 🔴 This slide is called Genuine parts share because it is the GPS-style view: ISZE parts billed versus a modelled target-spend ceiling.
- 🟠 Target-spend cover means parts billed divided by the modelled spend the fleet should generate. It is not measured competitor spend.
- 🟠 FY2026 improved versus FY2025, but roughly four tenths of the modelled spend is still outside ISZE billing.
- 🟠 Question: which families explain the remaining gap, and where should I Motors receive category support first?

### Screenshot 03 slide content (PMS service-demand cover, dark)
Title: "Filters and brakes show opposite movements; the denominator is the modelled service demand". Portugal / I Motors, calendar 2023–2025, current PMS model base.

| Category | 2023 | 2024 | 2025 | Observation / question |
|---|---|---|---|---|
| Air filter | 27% | 48% | 56% | Improving; what practice can be copied? |
| Oil filter | 46% | 71% | 46% | 2025 reversal; why did it fall back? |
| Fuel filter | 36% | 60% | 40% | Same reversal as oil filter. |
| Brake pad | 51% | 20% | 55% | Recovered strongly; what changed? |
| Clutch kit | 26% | 29% | 30% | Low but slowly improving. |
| Brake shoe | 8% | 8% | 11% | Persistent underdevelopment. |

Note on the slide: the PMS denominator is expected replacement units by service family, not full GPS target spend, and it uses the 2025 model base consistently.
Panel: the biggest leakage signal is the oil/fuel filter reversal after a strong 2024; air filter keeps improving, so this is not general filter weakness; the denominator is expected service units on the current model base; question: what changed 2024→2025 for oil/fuel filters (price, BVP availability, dealer stocking, competitor supply)?

---

## 6. Numbers that must be rechecked (conflicts already spotted)

1. **Fleet / UIO:** the deck uses **7,208** (2025 estimate; 2024 actual 6,903; 2023 6,091). The 29 July minutes cite the ISZE scrap-rate model at **≈7,909**, and Astara uses 10-year registrations. Pick one base, state it, and reconcile against `06_uio/` and `metrics_snapshot.json`.
2. **GPS / genuine share:** the deck's target-spend cover is **56.0%** (CY2025, €1.710M / €3.052M). The July meeting and a mail subject quote **GPS capture 63.3%**, and the minutes say "mid-50%s if warranty excluded". Explain which definition is used, then use one consistently. Screenshot 02 says "FY2026 improved versus FY2025", which doesn't match the CY2023–25 series on slide 9: check the period labels.
3. **Brake pad 2024 dip (20%) and filter 2024 spike (71% / 60%):** the minutes attribute the brake drop to **prior-year campaign stock build**. Test whether the 2024 filter spike is also a campaign or stock build (I Motors buying ahead). If so, the 2025 "reversal" may be a normalisation, not leakage. That would be a key honest insight, and it should be confirmed with the sales-to-dealer data (dealer offtake is smoother than distributor purchasing).
4. **MOS "3.7 in Sep 2025"** (slide 2) vs the Apr–Aug 2026 series: check against the KPI Master File.
5. **Sales-to-dealer € (KPI Master File)** €1.864M Apr–Aug 2026 vs €1.491M (+25%) vs the minutes' FY dealer-sales base **~€4.047M**. Check that the annualisation is consistent.
6. Slide 12 BVP share 61.4 → 63.4 → 58.1% is from `04_original_vs_value_parts_mix.csv` (selected families only). Reconcile with `mix_genuine_bvp_by_family.csv` and `metrics_snapshot.json`.
7. **Fiscal vs calendar year:** slides 8–12 and screenshot 03 are calendar-year. Rebuild them on FY (Apr–Mar) where the derived files allow; otherwise label them "calendar year" clearly.
8. All FY2027 plan numbers (€774K sales, €924K budget, €1.858M target, €790K orders) come from the supplied plan report. Re-add them from source.

---

## 7. Insight ideas for the new slides (not yet computed)

Sales-to-dealer (quantity only, PN × month, 2025 full + 2026 Jan–Aug, network level, no dealer split):

- **Genuine vs BVP in their sales to dealer over time** (map PNs via `genuine_bvp_crossref`). Are dealers buying more BVP? Is that shift faster in 2026 than 2025, and in which families (filters, brakes, clutch)?
- **Old vs new price effect:** value their quantities at old and new ISZE prices (before/after the ~5% March increase). Did volume per family move after the price change? Did the Genuine→BVP down-trade accelerate after it? This is the "old prices / new prices" analysis Jerome asked for. Label all € as "quantity × ISZE price", never as their margin.
- **Sell-in vs sell-out:** ISZE billing to I Motors (quantity by PN) vs I Motors quantity to dealers. That shows stock build or depletion by family (links to MOS 2.9 → 2.2), PNs sold to dealers but rarely bought from ISZE (possible other source), and the lag between the two.
- **Explain the Aug–Sep plan gap:** dealer offtake stayed strong while I Motors cut replenishment (destocking). Check month by month.
- **PMS in sales to dealer:** units per PMS family vs expected replacement units (same PMS denominator). This measures cover at dealer level, not distributor purchasing, and is a better leakage read.
- **Seasonality and concentration:** the top-N PNs that make up X% of quantity; new PNs appearing in 2026; PNs that stopped.
- **Method slide:** what Astara gave (file, period, fields), how PNs were mapped (Genuine/BVP, PMS family), what we did not assume (no dealer prices, no margin), and the limits.

Deck flow proposal (to confirm with Jerome): Cover → Exec summary → FY27 plan (2) → Sales to dealer → Fill rate → Stock → *[section: their data]* method → Genuine vs BVP in sales to dealer → price-change effect → sell-in vs sell-out → *[section: GPS/PMS]* fleet/UIO base → GPS cover → PMS table (screenshot 03) → filters → wear parts → Genuine/BVP billing mix → *[section: programmes]* extended target (+9% UIO, +1.8% genuine share, reachable) → R&M history + asks → lubricants centralised purchasing (postponed) → other open items from the minutes (SPA proposals, EDI, monthly feed, BCS F-series brackets, obsolete stock, dealer visits) → priorities → actions/next review.

---

## 8. Practical notes for the local build

- The cloud session had to `apt-get install libreoffice-impress` to render; locally, use PowerPoint for visual QA.
- The base deck looks machine-generated (author "OpenAI"), with shapes as free text boxes and charts partly as native charts. Simplest route: rebuild with python-pptx on a dark master, reusing the numbers, rather than recolouring shape by shape.
- Charcoal palette to match screenshot 03: background ~#2B2B2B, panel ~#333 with a light border, ISUZU red for the header table and the red dot, amber for the secondary dots, green/amber/red for the % values.
- Open question to ask Jerome before building: any content from the 140 KB draft beyond screenshots 02 and 03 that must be kept?

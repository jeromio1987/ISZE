# I-Motors Portugal — competitive parts vs aftermarket brand prices

Computed 2026-10-06. Primary lens: **other aftermarket brands** (Blue Print, Bosch, Delphi, Febi, Herth+Buss, etc. in the price ledger). OEM peer / grey import is secondary only and does **not** gate the shortlist.

## Data sufficiency

**Thin but usable for a first shortlist.** Aftermarket brand prices cover only 32% of Competitive-parts sales-to-dealer list € in CY2025 (120 part numbers). Treat hits as evidence where the join exists; do not generalise to every competitive part.

| Source | What it gives | Limit |
|---|---|---|
| Portugal sales to dealer MONTH files | PN × month qty through **2026-08** | No Sep PN; network total, not by dealer |
| AIM release 2026-10-04 | Catalogue **Competitive parts** + AIM family | Competitive is catalogue L1; AIM remaps into Brakes / Suspension / … |
| `price_observations` aftermarket types | Brand prices + cross-ref IAM (Eucon, KS AM, …) | Mostly **DE / NO / UK**, not Portugal shops |
| PR00 IE40 list | Our list €; reference dealer price = list × 1.40 × 1.275 | Not I-Motors net; actual Portugal %GM may differ |
| Genuine↔BVP cross-ref | Fills a few missing AM prices via the paired number | Small lift only |

**Coverage (Competitive catalogue L1, Portugal sales to dealer):**  
120 part numbers with an aftermarket brand price = **31.7%** of CY2025 competitive sales-to-dealer list € (€209,925 of €663,174).

## Direction — is competitive sales to dealer dropping?

List € = qty × ISZE list (same basis as the AIM evolution pack).

- **Competitive parts (catalogue L1):** CY2025 sales to dealer list €663,174 → 2026 Jan–Aug €535,078 (annualised vs CY2025: +21.0% on list €). FY Apr–Aug: €263,192 → €324,107 (+23.1%).
- **Contested AIM L1 basket:** CY2025 sales to dealer list €540,075 → 2026 Jan–Aug €437,950 (annualised vs CY2025: +21.6% on list €). FY Apr–Aug: €221,454 → €265,629 (+19.9%).
- **Union (competitive OR contested):** CY2025 sales to dealer list €897,064 → 2026 Jan–Aug €704,710 (annualised vs CY2025: +17.8% on list €). FY Apr–Aug: €367,668 → €422,921 (+15.0%).

Inside Competitive catalogue, AIM families with the softest FY Apr–Aug (FY2026 → FY2027) list €:

- Tools Equipment: FY Apr–Aug list €11 → €0 (-100.0%)
- Unknown Review: FY Apr–Aug list €730 → €235 (-67.7%)
- Cabin Interior: FY Apr–Aug list €3,242 → €1,108 (-65.8%)
- Unknown: FY Apr–Aug list €7,251 → €4,551 (-37.2%)
- Accident & Body: FY Apr–Aug list €762 → €612 (-19.7%)
- Chassis Frame: FY Apr–Aug list €2,053 → €1,664 (-18.9%)
- Fluids Chemicals: FY Apr–Aug list €2,595 → €2,263 (-12.8%)
- Fuel System: FY Apr–Aug list €27,399 → €24,258 (-11.5%)

## End-goal shortlist — dropping **and** expensive vs aftermarket brands

Rule: sales to dealer list € dropping (FY Apr–Aug −15%+ or CY run-rate −20%+) **and** our **reference dealer price** more than 10% above the aftermarket brand **median** on that part (or its genuine/BVP pair).

Ranked by impact = list € lost × overprice gap ratio.

**Hits: 26 part numbers.** Combined working list € lost on those hits: €13,805.

1. **DPD ASM** (`8981776324`) — Intake Exhaust Emission / DPF/DPD. Sales to dealer list € lost (working cut): €1,348. Our reference dealer price €2,406.77 vs aftermarket brand median €449.00 (index 5.36, brands: Ahg, Greencar Automotive, Kamoka, Vegaz). FY Apr–Aug list €: €1,348 → €0.
2. **BUMPER; FRT,CENTER** (`8975809452`) — Accident & Body / Panels. Sales to dealer list € lost (working cut): €743. Our reference dealer price €663.54 vs aftermarket brand median €81.41 (index 8.15, brands: ). FY Apr–Aug list €: €1,115 → €372.
3. **PANEL; DEFLECTOR** (`8981032020`) — Accident & Body / Panels. Sales to dealer list € lost (working cut): €1,084. Our reference dealer price €483.93 vs aftermarket brand median €118.17 (index 4.10, brands: Blic, Easy Part France). FY Apr–Aug list €: €1,084 → €0.
4. **RADIATOR ASM** (`8983355671`) — Cooling / Radiator. Sales to dealer list € lost (working cut): €449. Our reference dealer price €802.04 vs aftermarket brand median €127.93 (index 6.27, brands: ). FY Apr–Aug list €: €1,348 → €899.
5. **FILTER ASM; FUEL** (`8982399830`) — Maintenance Service / Filters (unspecified). Sales to dealer list € lost (working cut): €277. Our reference dealer price €98.76 vs aftermarket brand median €10.94 (index 9.03, brands: AMC Filter, Bogap, Bosch, Eurorepar, HERTH+BUSS JAKOPARTS, Hella, Hengst, Hengst). FY Apr–Aug list €: €277 → €0.
6. **PANEL; DEFLECTOR** (`8973873800`) — Accident & Body / Panels. Sales to dealer list € lost (working cut): €306. Our reference dealer price €546.57 vs aftermarket brand median €69.78 (index 7.83, brands: ). FY Apr–Aug list €: €306 → €0.
7. **BUMPER ASM; FRT** (`8974056285`) — Accident & Body / Bumpers. Sales to dealer list € lost (working cut): €1,051. Our reference dealer price €312.54 vs aftermarket brand median €127.93 (index 2.44, brands: ). FY Apr–Aug list €: €1,401 → €350.
8. **FILTER; ACL** (`5876150021`) — Maintenance Service / Air Filter. Sales to dealer list € lost (working cut): €711. Our reference dealer price €23.08 vs aftermarket brand median €8.22 (index 2.81, brands: BLUE PRINT, Blue Print, Febi, Febi Bilstein, Wilmink Group (BLUE PRINT), Wilmink). FY Apr–Aug list €: €711 → €0.
9. **ROTOR; DISC BRK,FRT** (`8982488951`) — Brakes / Discs & Drums. Sales to dealer list € lost (working cut): €476. Our reference dealer price €283.51 vs aftermarket brand median €87.22 (index 3.25, brands: BLUE PRINT, Febi). FY Apr–Aug list €: €1,112 → €635.
10. **PAD KIT; CALIPER,DISC BRK,FRT** (`8975056801`) — Brakes / Pads & Shoes. Sales to dealer list € lost (working cut): €740. Our reference dealer price €146.82 vs aftermarket brand median €77.65 (index 1.89, brands: BLUE PRINT, Blue Print, Febi, Febi Bilstein, Herth+Buss Jakoparts, KGK (Febi), M). FY Apr–Aug list €: €4,935 → €4,195.
11. **BUMPER ASM; FRT** (`8974068144`) — Accident & Body / Bumpers. Sales to dealer list € lost (working cut): €613. Our reference dealer price €273.46 vs aftermarket brand median €139.56 (index 1.96, brands: ). FY Apr–Aug list €: €1,379 → €766.
12. **ARM; UPR CONT** (`8979458412`) — Suspension / Suspension Arm. Sales to dealer list € lost (working cut): €272. Our reference dealer price €243.06 vs aftermarket brand median €81.41 (index 2.99, brands: ). FY Apr–Aug list €: €272 → €0.
13. **CYLINDER; WHEEL,RR BRK** (`1476012190`) — Wheels Hub / Wheel Rim. Sales to dealer list € lost (working cut): €1,307. Our reference dealer price €388.83 vs aftermarket brand median €302.37 (index 1.29, brands: ). FY Apr–Aug list €: €871 → €871.
14. **ARM; UPR CONT** (`8983894321`) — Suspension / Suspension Arm. Sales to dealer list € lost (working cut): €239. Our reference dealer price €212.99 vs aftermarket brand median €87.22 (index 2.44, brands: ). FY Apr–Aug list €: €358 → €358.
15. **CLUTCH KIT** (`5876102060`) — Clutch / Clutch Kit. Sales to dealer list € lost (working cut): €1,138. Our reference dealer price €290.28 vs aftermarket brand median €226.78 (index 1.28, brands: ). FY Apr–Aug list €: €1,951 → €813.

## Near-misses

**Dropping, but no aftermarket brand price** (priority to get a brand quote):

- PIPE; EXH (`8983682091`), Intake Exhaust Emission: list € lost ~€6,469 — **no aftermarket brand price on file**
- TANK ASM; DEF (`8972746690`), Intake Exhaust Emission: list € lost ~€2,199 — **no aftermarket brand price on file**
- DPD ASM (`8983320764`), Intake Exhaust Emission: list € lost ~€2,134 — **no aftermarket brand price on file**
- COOLER; EGR (`8981521221`), Intake Exhaust Emission: list € lost ~€2,089 — **no aftermarket brand price on file**
- PUMP ASM; FUEL,SUPPLY (`8983320621`), Fuel System: list € lost ~€1,984 — **no aftermarket brand price on file**
- RAIL;COMMON (`8983300400`), Fuel System: list € lost ~€1,773 — **no aftermarket brand price on file**
- STEERING UNIT (`8981017801`), Steering: list € lost ~€1,597 — **no aftermarket brand price on file**
- BODY ASM; REAR (`8975536860`), Accident & Body: list € lost ~€1,460 — **no aftermarket brand price on file**
- STEERING UNIT (`8979461321`), Steering: list € lost ~€1,359 — **no aftermarket brand price on file**
- GLASS; WINDSHIELD (`8980290621`), Accident & Body: list € lost ~€1,252 — **no aftermarket brand price on file**

**Looks expensive vs aftermarket brands, but sales to dealer is growing** (price pressure, not volume loss yet):

- ELEMENT KIT; FUEL FILTER (`5876150240`): reference dealer €16.15 vs AM median €5.81 (index 2.78) but sales to dealer list € is **rising**
- PAD KIT; CALIPER,DISC BRK,FRT (`8982169220`): reference dealer €144.58 vs AM median €55.40 (index 2.61) but sales to dealer list € is **rising**
- ROTOR; DISC BRK,FRT (`8979488071`): reference dealer €161.49 vs AM median €63.02 (index 2.56) but sales to dealer list € is **rising**
- PAD KIT; CALIPER,DISC BRK,FRT (`8982447940`): reference dealer €159.06 vs AM median €64.59 (index 2.46) but sales to dealer list € is **rising**
- ARM; UPR CONT (`8983894311`): reference dealer €212.99 vs AM median €87.22 (index 2.44) but sales to dealer list € is **rising**
- ARM; LWR CONT (`8983894331`): reference dealer €269.57 vs AM median €133.74 (index 2.02) but sales to dealer list € is **rising**
- PUMP ASM; DEF,DCM SPLY (`8982688122`): reference dealer €1,984.97 vs AM median €1,017.76 (index 1.95) but sales to dealer list € is **rising**
- DRUM; BRK,RR (`8980618131`): reference dealer €129.39 vs AM median €67.50 (index 1.92) but sales to dealer list € is **rising**

## Supply marks on the shortlist (re-verified 2026-10-06)

Join of the 26 shortlist PNs to (1) ISZE open sales orders sold-to **519** (EXPORT 6 Oct) and (2) any populated month in Nuno’s Backordered lines 2026 (Jan–Aug; Sep+ empty in the 29-Sep file). Same sources as the BO AIM deep dive. No invented BO euros on the shortlist page.

| Cut | Count | Part numbers |
|---|---:|---|
| Either open and/or earlier BO | **9** | see below |
| Open on our order now | **4** | `1476012190`, `8982488951`, `8983313830`, `8981226920` |
| Earlier BO 2026 only | **5** | `8974068144`, `8980873901`, `8983894341`, `8983313840`, `8982120690` |
| Neither | **17** | rest of shortlist |

Two of the four open PNs also appeared on Nuno BO earlier (`1476012190`, `8982488951`). HTML labels: **Open on our order** / **Earlier BO 2026**.

Empty Brands cells on KS-only ledger rows now display **KS International (no brand on listing)** instead of a dash.

## What this does **not** prove

- That Portuguese workshops pay the Eucon/KS listing — those are foreign aftermarket observations.
- That list € lost is all lost to aftermarket brands (stock, campaigns, and mix also move the line).
- That every Competitive part is overpriced — most have **no** brand price on file.
- OEM peer / Amayama grey as a substitute for aftermarket brand competition (kept in the full table as a secondary column only).
- That an earlier BO mark equals a current fill-rate miss (Sep+ Nuno tabs empty; open marks use our 6 Oct EXPORT only).

## Output files

| File | Content |
|---|---|
| `shortlist_dropping_and_overpriced_vs_am.csv` | End-goal hits |
| `shortlist_bo_open_marks.csv` | Open-order / earlier-BO marks for the 26 hits |
| `near_miss_dropping_no_am_price.csv` | Dropping, no brand price |
| `near_miss_overpriced_but_std_growing.csv` | Expensive, StD rising |
| `basket_std_period_compare.csv` | Basket CY / FY direction |
| `competitive_catalog_by_aim_l1_periods.csv` | Competitive remapped to AIM L1 |
| `monthly_std_competitive_contested.csv` | Monthly series |
| `pn_competitive_contested_full.csv` | Full PN table |
| `summary.json` | Machine summary + coverage |
| `IMotors_Competitive_AM_Price_Shortlist_20261006.html` | Self-contained shortlist page |

Builder: `build_competitive_price_overlap.py` · HTML: `_build_html_shortlist.py`

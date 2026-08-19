# ISZE — Units In Operation (UIO), CY2026 by distributor

**Purpose:** hand-off file for the UIO V20 rebuild. Corrected CY2026 fleet figures per distributor (DB).  
**Generated:** 30 July 2026 · **Source:** ISZE UIO Overview workbook V19 (dated 18 June 2026), sheet `1.UIO Overview`, read cell by cell.

---

## READ THIS BEFORE USING ANY NUMBER

1. **The V19 column is wrong and must not be quoted.** V19 rolls every forecast year forward as `previous_year x 0.97 + registrations` — a flat 3% annual scrap rate implying a 33-year vehicle life. The survival curves that build the file's own history imply 9.9 years for trucks (10.2%/yr) and 8.1 years for pickups (12.3%/yr). This was verified against all 195 forecast cells in the file; every one fits the 0.97 rule exactly.
2. **Only one figure here is exact: IUK LCV = 44,926.** That is a locked, board-approved number (30 July 2026), computed as `47,783 x (1 - 0.123) + 3,020`. Use it verbatim for FY27 GPS and Extended Target. V19's 49,280 (+3.1%) must not be used; the correct move is -6.0%.
3. **Every other corrected figure is an ESTIMATE, not a rebuild output.** They apply a constant-hazard equivalent (10.2% CV / 12.3% LCV) to size the error. The actual V20 rebuild will apply the full cohort survival curve and will land a few per cent away from these. Do not present these as V20 results.
4. **Israel CV (UTI, rows 7 and 8) is NOT corrected here and is still wrong.** It sits ~23% below the Israeli Ministry of Transport figure of **14,019** registered vehicles at 30 June 2026 (model shows 10,760). That is a separate defect — a block of vehicles missing from the weight-class mapping, not a scrap-rate problem — and it needs a rebuild on government data. Do not apply a 1.25 multiplier. Israel pickups (UMI, row 9) are a normal LCV row and ARE corrected here.
5. **UK CV (ITUK, rows 22-24) is deliberately unchanged.** Those rows already use a proper cohort survival model with an age floor and are correct. Left at V19 values on purpose.
6. **MIDI Europe is excluded from all totals.** MIDI (France, Switzerland, Spain, Italy, Poland, Serbia) is not an ISZE distributor. Warning: cell **B4 on sheet `1.UIO Overview` of the live file is currently set to "Include"**, so the workbook's own Grand Total row is carrying MIDI right now (95,395 vehicles in 2025, ~37% of the total).
7. **Unit** = vehicles in operation (fleet/parc), calendar year 2026. Not registrations, not shipments.

---

## Summary by distributor — CY2026, excluding MIDI Europe

| Distributor (DB) | V19 2026 — do not use | Corrected 2026 | Delta | vs V19 |
|---|---:|---:|---:|---:|
| IUK | 49,280 | **44,926** | -4,354 | -8.8% |
| ITUK | 24,173 | **24,173** | +0 | +0.0% |
| UMI | 18,886 | **17,161** | -1,725 | -9.1% |
| ISD-Lang | 14,757 | **13,490** | -1,267 | -8.6% |
| UTI | 10,760 | **10,760** | +0 | +0.0% |
| IBX | 10,180 | **9,290** | -890 | -8.7% |
| Isuzu Sverige | 9,090 | **8,304** | -786 | -8.6% |
| Imotors | 8,444 | **7,825** | -619 | -7.3% |
| RSA | 8,111 | **7,374** | -737 | -9.1% |
| Petros Petropoulos | 4,285 | **3,938** | -348 | -8.1% |
| AutoWallis | 3,992 | **3,645** | -347 | -8.7% |
| Isuzu Ireland | 2,778 | **2,594** | -184 | -6.6% |
| Loutsios & Sons | 2,634 | **2,423** | -211 | -8.0% |
| Nordic Auto. | 1,308 | **1,196** | -112 | -8.6% |
| Isuzu Rom Auto | 1,209 | **1,109** | -100 | -8.2% |
| GasanZammit | 1,108 | **1,016** | -92 | -8.3% |
| Isuzu Denmark | 945 | **866** | -79 | -8.3% |
| BL | 439 | **401** | -38 | -8.6% |
| **TOTAL ex-MIDI** | **172,379** | **160,494** | **-11,886** | **-6.9%** |

> ITUK and UTI show zero delta by design — see notes 4 and 5 above. UTI's zero is *not* a clean bill of health.

---

## Row-level detail

| Row | Country | DB | Seg | Model | UIO 2025 | V19 2026 | Regs 2026 | **Corrected 2026** | Status |
|---:|---|---|---|---|---:|---:|---:|---:|---|
| 7 | ISRAEL | UTI | CV | LD | 6,059 | 6,101 | 224 | **6,101** | NOT FIXED |
| 8 | ISRAEL | UTI | CV | MD | 4,277 | 4,659 | 510 | **4,659** | NOT FIXED |
| 9 | ISRAEL | UMI | LCV | LCV | 18,542 | 18,886 | 900 | **17,161** | ESTIMATE |
| 10 | ICELAND | BL | CV | LD | 0 | 0 | 0 | **0** | ESTIMATE |
| 11 | ICELAND | BL | CV | MD | 0 | 0 | 0 | **0** | ESTIMATE |
| 12 | ICELAND | BL | LCV | LCV | 406 | 439 | 45 | **401** | ESTIMATE |
| 13 | NORWAY | RSA | CV | LD | 0 | 0 | 0 | **0** | ESTIMATE |
| 14 | NORWAY | RSA | CV | MD | 0 | 0 | 0 | **0** | ESTIMATE |
| 15 | NORWAY | RSA | LCV | LCV | 7,929 | 8,111 | 420 | **7,374** | ESTIMATE |
| 16 | SWEDEN | Isuzu Sverige | CV | LD | 0 | 0 | 0 | **0** | ESTIMATE |
| 17 | SWEDEN | Isuzu Sverige | CV | MD | 0 | 0 | 0 | **0** | ESTIMATE |
| 18 | SWEDEN | Isuzu Sverige | LCV | LCV | 8,443 | 9,090 | 900 | **8,304** | ESTIMATE |
| 19 | DENMARK | Isuzu Denmark | CV | LD | 1 | 1 | 0 | **1** | ESTIMATE |
| 20 | DENMARK | Isuzu Denmark | CV | MD | 0 | 0 | 0 | **0** | ESTIMATE |
| 21 | DENMARK | Isuzu Denmark | LCV | LCV | 850 | 944 | 120 | **866** | ESTIMATE |
| 22 | U KING | ITUK | CV | LD | 22,191 | 23,210 | 1,685 | **23,210** | OUT OF SCOPE |
| 23 | U KING | ITUK | CV | MD | 0 | 0 | 0 | **0** | OUT OF SCOPE |
| 24 | U KING | ITUK | CV | F-Series | 877 | 963 | 113 | **963** | OUT OF SCOPE |
| 25 | U KING | IUK | LCV | LCV | 47,783 | 49,280 | 3,020 | **44,926** | LOCKED |
| 26 | IRELAND | Isuzu Ireland | CV | LD | 731 | 925 | 216 | **872** | ESTIMATE |
| 27 | IRELAND | Isuzu Ireland | CV | MD | 0 | 36 | 36 | **36** | ESTIMATE |
| 28 | IRELAND | Isuzu Ireland | CV | F-Series | 92 | 89 | 0 | **83** | ESTIMATE |
| 29 | IRELAND | Isuzu Ireland | LCV | LCV | 1,338 | 1,728 | 430 | **1,603** | ESTIMATE |
| 30 | NETHLDS | IBX | CV | LD | 0 | 0 | 0 | **0** | ESTIMATE |
| 31 | NETHLDS | IBX | CV | MD | 0 | 0 | 0 | **0** | ESTIMATE |
| 32 | NETHLDS | IBX | LCV | LCV | 0 | 0 | 0 | **0** | ESTIMATE |
| 33 | BELGIUM | IBX | CV | LD | 113 | 145 | 35 | **136** | ESTIMATE |
| 34 | BELGIUM | IBX | CV | MD | 0 | 0 | 0 | **0** | ESTIMATE |
| 35 | BELGIUM | IBX | LCV | LCV | 9,452 | 10,008 | 840 | **9,129** | ESTIMATE |
| 36 | LUXMBRG | IBX | CV | LD | 0 | 0 | 0 | **0** | ESTIMATE |
| 37 | LUXMBRG | IBX | CV | MD | 0 | 0 | 0 | **0** | ESTIMATE |
| 38 | LUXMBRG | IBX | LCV | LCV | 0 | 0 | 0 | **0** | ESTIMATE |
| 39 | FRANCE | MIDI Europe | CV | LD | 0 | 0 | 0 | **0** | EXCLUDE |
| 40 | FRANCE | MIDI Europe | CV | MD | 0 | 0 | 0 | **0** | EXCLUDE |
| 41 | FRANCE | MIDI Europe | LCV | LCV | 0 | 0 | 0 | **0** | EXCLUDE |
| 42 | GERMANY | ISD-Lang | CV | LD | 697 | 1,066 | 390 | **1,016** | ESTIMATE |
| 43 | GERMANY | ISD-Lang | CV | MD | 35 | 34 | 0 | **31** | ESTIMATE |
| 44 | GERMANY | ISD-Lang | LCV | LCV | 13,048 | 13,657 | 1,000 | **12,443** | ESTIMATE |
| 45 | SWITZLD | MIDI Europe | CV | LD | 0 | 0 | 0 | **0** | EXCLUDE |
| 46 | SWITZLD | MIDI Europe | CV | MD | 0 | 0 | 0 | **0** | EXCLUDE |
| 47 | SWITZLD | MIDI Europe | LCV | LCV | 0 | 0 | 0 | **0** | EXCLUDE |
| 48 | AZORS | Imotors | CV | LD | 0 | 0 | 0 | **0** | ESTIMATE |
| 49 | AZORS | Imotors | CV | MD | 0 | 0 | 0 | **0** | ESTIMATE |
| 50 | AZORS | Imotors | LCV | LCV | 0 | 0 | 0 | **0** | ESTIMATE |
| 51 | PORTUGL | Imotors | CV | LD | 2,206 | 2,596 | 456 | **2,437** | ESTIMATE |
| 52 | PORTUGL | Imotors | CV | MD | 0 | 96 | 96 | **96** | ESTIMATE |
| 53 | PORTUGL | Imotors | CV | F-Series | 269 | 261 | 0 | **242** | ESTIMATE |
| 54 | PORTUGL | Imotors | LCV | LCV | 4,733 | 5,491 | 900 | **5,051** | ESTIMATE |
| 55 | SPAIN | MIDI Europe | CV | LD | 0 | 0 | 0 | **0** | EXCLUDE |
| 56 | SPAIN | MIDI Europe | CV | MD | 0 | 0 | 0 | **0** | EXCLUDE |
| 57 | SPAIN | MIDI Europe | LCV | LCV | 0 | 0 | 0 | **0** | EXCLUDE |
| 58 | ITALY | MIDI Europe | CV | LD | 58,690 | 56,929 | 0 | **52,704** | EXCLUDE |
| 59 | ITALY | MIDI Europe | CV | MD | 1,732 | 1,582 | -98 | **1,457** | EXCLUDE |
| 60 | ITALY | MIDI Europe | LCV | LCV | 34,973 | 38,424 | 4,500 | **35,171** | EXCLUDE |
| 61 | MALTA | GasanZammit | CV | LD | 243 | 260 | 24 | **242** | ESTIMATE |
| 62 | MALTA | GasanZammit | CV | MD | 0 | 0 | 0 | **0** | ESTIMATE |
| 63 | MALTA | GasanZammit | LCV | LCV | 797 | 848 | 75 | **774** | ESTIMATE |
| 64 | FINLAND | Nordic Auto. | CV | LD | 0 | 0 | 0 | **0** | ESTIMATE |
| 65 | FINLAND | Nordic Auto. | CV | MD | 0 | 0 | 0 | **0** | ESTIMATE |
| 66 | FINLAND | Nordic Auto. | LCV | LCV | 1,204 | 1,308 | 140 | **1,196** | ESTIMATE |
| 67 | POLAND | MIDI Europe | CV | LD | 0 | 0 | 0 | **0** | EXCLUDE |
| 68 | POLAND | MIDI Europe | CV | MD | 0 | 0 | 0 | **0** | EXCLUDE |
| 69 | POLAND | IBX | LCV | LCV | 28 | 27 | 0 | **25** | ESTIMATE |
| 70 | AUSTRIA | ISD-Lang | CV | LD | 0 | 0 | 0 | **0** | ESTIMATE |
| 71 | AUSTRIA | ISD-Lang | CV | MD | 0 | 0 | 0 | **0** | ESTIMATE |
| 72 | AUSTRIA | ISD-Lang | LCV | LCV | 0 | 0 | 0 | **0** | ESTIMATE |
| 73 | HUNGARY | AutoWallis | CV | LD | 0 | 0 | 0 | **0** | ESTIMATE |
| 74 | HUNGARY | AutoWallis | CV | MD | 0 | 0 | 0 | **0** | ESTIMATE |
| 75 | HUNGARY | AutoWallis | LCV | LCV | 3,734 | 3,992 | 370 | **3,645** | ESTIMATE |
| 76 | SERBIA | MIDI Europe | CV | LD | 0 | 0 | 0 | **0** | EXCLUDE |
| 77 | SERBIA | MIDI Europe | CV | MD | 0 | 0 | 0 | **0** | EXCLUDE |
| 78 | SERBIA | MIDI Europe | LCV | LCV | 0 | 0 | 0 | **0** | EXCLUDE |
| 79 | GREECE | Petros Petropoulos | CV | LD | 37 | 56 | 20 | **53** | ESTIMATE |
| 80 | GREECE | Petros Petropoulos | CV | MD | 0 | 5 | 5 | **5** | ESTIMATE |
| 81 | GREECE | Petros Petropoulos | LCV | LCV | 3,705 | 4,224 | 630 | **3,879** | ESTIMATE |
| 82 | ROMANIA | Isuzu Rom Auto | CV | LD | 0 | 0 | 0 | **0** | ESTIMATE |
| 83 | ROMANIA | Isuzu Rom Auto | CV | MD | 0 | 0 | 0 | **0** | ESTIMATE |
| 84 | ROMANIA | Isuzu Rom Auto | LCV | LCV | 1,071 | 1,209 | 170 | **1,109** | ESTIMATE |
| 85 | BULGAR | Petros Petropoulos | CV | LD | 0 | 0 | 0 | **0** | ESTIMATE |
| 86 | BULGAR | Petros Petropoulos | CV | MD | 0 | 0 | 0 | **0** | ESTIMATE |
| 87 | BULGAR | Petros Petropoulos | LCV | LCV | 0 | 0 | 0 | **0** | ESTIMATE |
| 88 | CYPRUS | Loutsios & Sons | CV | LD | 203 | 227 | 30 | **212** | ESTIMATE |
| 89 | CYPRUS | Loutsios & Sons | CV | MD | 0 | 5 | 5 | **5** | ESTIMATE |
| 90 | CYPRUS | Loutsios & Sons | LCV | LCV | 2,105 | 2,402 | 360 | **2,206** | ESTIMATE |

**Status key** — `LOCKED` exact, board-approved · `ESTIMATE` constant-hazard sizing, V20 will differ · `NOT FIXED` Israel CV, still ~23% low · `OUT OF SCOPE` UK CV, already correct · `EXCLUDE` MIDI Europe, not an ISZE distributor

---

*Companion data file: `UIO_CY2026_by_DB_for_rebuild_2026-07-30.csv` (same folder, same figures, machine-readable).*
# ISZE Warranty Parts — CY2025 value per Distributor / Country (EUR)

**Created 2026-06-12.** Authoritative reference for the warranty-parts value used in the GPS
"ex-warranty" adjustment. When adjusting GPS, **take every DB below into account** — do not leave
LCV markets at 0 the way the pre-2026-06-12 build did.

Wired into: `Data\_build\build_gps_v8.py` (`warranty` dict) → `Data\ISZE_GPS_Calculator_v8.xlsx`,
sheet **GPS_2025_Warranty**, column F (blue INPUT).

---

## Sources & methodology

| Segment | File | Sheet | Basis |
|---|---|---|---|
| CV (trucks) | `Data\Warranty_CV_2025.xlsx` | `ITUK`, `UTI`, `Sheet4` (country pivot) | qty × ISZE EUR price |
| LCV (D-Max) | `Data\Warranty_LCV_2025.xlsx` | `ExportClaimAssessment202501-202` split by `DistributorName`, priced via `Sheet2` (part → ISZE EUR) | qty × ISZE EUR price |

- **Basis = ISZE list/transfer price in EUR** (qty × price), identical to the existing CV figures
  (this reproduces the prior dict exactly: ITUK 374,426 / UTI 255,968 / Germany 5,593 / Greece 1,450
  / Malta 1,470 / Cyprus 406).
- **LCV price coverage = 99.8% of pieces** (parts without an ISZE price are negligible).
- Period = CY2025 claim-assessment export (underlying repair dates Dec-2024 → Nov-2025); CV filtered on `BILLYMD` 2025.

---

## Warranty parts CY2025 per GPS DB (EUR)

★ = one of the 12 DBs requested 2026-06-12.

| DB | CV (€) | LCV (€) | **Total (€)** | Note |
|---|--:|--:|--:|---|
| ITUK | 374,426 | — | **374,426** | CV only |
| ★ IUK | — | 1,054,395 | **1,054,395** | LCV (D-Max). PM-sensor campaign + steering/brake/engine. Verified real. |
| ★ UMI | — | 1,791,020 | **1,791,020** | **RESOLVED 2026-07-03** — dedicated claim file `UMI warranty data 202301 - 202605 (1).xlsx` (Jerome). CY2025 = sum of `Approved part cost` per line, `Written Date_YMD` in CY2025 (12,042 lines / 201 claims). Cross-checked against `distributor_warranty_expense_fiscal.csv` fiscal-year totals — exact match. |
| UTI | 255,968 | — | **255,968** | CV only (Israel trucks) |
| GERMANY | 5,593 | 254,082 | **259,675** | ISD |
| ★ BELGIUM | — | 74,677 | **74,677** | IBX Belgium (no CV warranty rows in file) |
| ★ IRELAND | 3,908* | 30,949 | **34,857** | *CV = truck price-map **lower bound** (82% priced) |
| ★ NORWAY | — | 290,712 | **290,712** | RSA |
| ★ SWEDEN | — | 189,618 | **189,618** | Isuzu Sverige |
| ★ DENMARK | — | 9,115 | **9,115** | Isuzu Danmark |
| ★ FINLAND | — | 48,676 | **48,676** | NAT |
| ★ ICELAND | — | 7,035 | **7,035** | BL ehf |
| CYPRUS | 406 | 27,634 | **28,041** | Loutsios |
| GREECE | 1,450 | 54,708 | **56,159** | Petros Petropoulos |
| MALTA | 1,470 | 16,749 | **18,219** | GasanZammit |
| ★ ROMANIA | — | 19,377 | **19,377** | Isuzu Rom Auto |
| ★ HUNGARY | — | 77,434 | **77,434** | WAE / AutoWallis |
| ★ PORTUGAL | 28,836* | 101,752 | **130,588** | *CV = truck price-map **lower bound** (52% priced) |
| **TOTAL (GPS base)** | | | **€4,719,992** | Updated 2026-07-03 for UMI resolution (was €2,928,972) |

---

## Caveats (read before adjusting)

> **2026-07-27:** Caveats 2–3 below are **superseded** for “is GPS parts warranty missing?”. Sheet4 €314k is a PARTNBR-0 parse artifact (labour, skip). IE/PT remaining issue is optional list-price on real PNs, not missing claims. Periods and how-to-find: `01_data/90_INBOX/warranty_audit_2026-07-27/SANITY.md`.

1. **UMI resolved 2026-07-03** (was: LCV warranty file had no ISRAEL rows; only UTI Israel trucks
   CV was present). Value now sourced from a dedicated UMI claim-assessment export — see table note.
2. **Ireland & Portugal CV are lower bounds.** Their CV truck warranty is valued via the ITUK/UTI
   part price-map, which only covers 82% / 52% of their part cells, so CV is undercounted. LCV for
   both is clean.
3. **CV "0" bucket = €314,214 unattributed.** `Sheet4` in the CV file lumps €314K of parts under a
   blank "0" country — the reason Ireland/Portugal don't resolve cleanly there. Source-side data issue.
4. **Price basis = ISZE list/transfer (claim) price, not ISZE-net.** Per the in-sheet verified note
   (2026-06-11), ISZE-net ≈ **×0.74** (ITUK GP 34% + FX). Apply that haircut to column F if you want
   the net-level correction — the field is an adjustable INPUT.
5. **Warranty is embedded in normal sales.** ERP has no separate warranty document type
   (`SaTy` = SOR/VOR/RUSH/PRD only), so `VP Sales incl. Warranty` already contains these parts; the
   "ex-warranty" column subtracts column F to isolate non-warranty GPS.

---

## Non-GPS-base markets (LCV warranty, for completeness)

Present in the LCV file but not separate rows in the GPS calculator:

| Market (distributor) | LCV warranty (€) |
|---|--:|
| France (MIDI) | 254,504 |
| Italy (MIDI) | 126,268 |
| Poland (Benelux) | 88,328 |
| Switzerland (MIDI) | 73,135 |
| Austria (ISD) | 59,130 |
| Spain (MIDI) | 41,469 |
| Serbia (MIDI) | 10,705 |
| Netherlands (Benelux) | 10,601 |
| Czech (ISD) | 7,548 |
| Bosnia-Herz. (MIDI) | 3,861 |
| Slovakia (ISD) | 2,859 |
| Macedonia (MIDI) | 2,483 |
| Slovenia (MIDI) | 1,025 |
| Iraq (Zamzam) | 6 |

LCV grand total across **all** distributors (incl. above) = **€2,938,838**.

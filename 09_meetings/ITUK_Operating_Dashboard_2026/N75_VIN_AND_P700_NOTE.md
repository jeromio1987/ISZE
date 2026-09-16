# N75 VIN list + clutch 47% + brake 6–8 weeks + P700 unpriced

**As of:** 15 Aug 2026 · ITUK only · do not mix UMI/UTI · no GPS% invented.

Working VIN copy (Outlook, not Downloads):

`C:\Users\jerom\Desktop\claude\ISZE\01_data\90_INBOX\Duncan_VIN_20260723\2026-07-23_VIN_List_23_07_2026.xlsx`

Derived:

- `C:\Users\jerom\Desktop\claude\ISZE\01_data\00_derived\ituk_n75_vin_summary.csv`
- `C:\Users\jerom\Desktop\claude\ISZE\01_data\00_derived\ituk_n75_by_year.csv`
- `C:\Users\jerom\Desktop\claude\ISZE\01_data\00_derived\ituk_clutch_47pct.csv`
- `C:\Users\jerom\Desktop\claude\ISZE\01_data\00_derived\ituk_p700_unpriced_fastmovers_20260729.csv`

---

## 1. Which VIN file

**Use the 23 Jul 2026 list.** Duncan Young, *RE: Meeting today*, attachment `VIN List 23_07_2026.xlsx`.

Mail quote (23 Jul 2026): *Please see attached “VIN List 23_07_2026”. Is it possible for our colleagues at IML to populate the complete engine, cab with electrics and cab without electrics part numbers…*

Columns in the file: `vin`, `model`, `registration_date`, plus three empty PN slots (Complete Engine / CAB wo electrics / CAB with electrics). **No transmission. No mileage.**

Older lists (do not treat as the recent full list):

| File | Mail | What it is |
|---|---|---|
| `2026-07-23_VIN_List_23_07_2026.xlsx` | Duncan 23 Jul 2026 | **This one.** 29,926 unique VINs, regs 2008 → 1 May 2026 |
| `2026-01-15_Fleet_VIN_list_2014_-_2024_study.xlsx` | Duncan 15 Jan 2026 | N35+N75 only, 8,199 VINs, stops 5 Feb 2024 |
| `2026-03-17_CBU_Master_Data_-_Appended.xlsx` | Duncan 17 Mar 2026 | CBU / order / registration — still no transmission |
| `2026-07-27_VIN_engine_cab_enquiries_2020_2026.xlsx` | Jerome → James/Duncan 27 Jul | Enquiry list, not the parc |

Raw sheet has **103,515 rows** / **29,926 unique VINs** (73,575 duplicate extras). Counts below are unique VIN.

---

## 2. N75 counts

| Cut | Unique VINs |
|---|---:|
| All unique | 29,926 |
| N-series (`model` starts with N) | 28,562 |
| **N75\*** (`model` starts with N75) | **14,308** |
| VIN-mid **NPR75** | 10,390 |
| VIN-mid **NPR88** | 1,665 |
| **NPR75 + NPR88** (Phase-1 pack codes) | **12,055** |

N75\* = N75 11,550 + N75.190 2,717 + N75 CC 37 + glider 3 + written-off 1.

NPR75+NPR88 is the Phase-1 pair from Duncan’s 13–14 Aug PMS pack (NPR75 / 4HK1 and NPR88 / 4JZ1). Older N75.190 rows often sit on NPR85 in the VIN — keep them out of the Phase-1 pack count.

### By registration year (N75\*)

2008 312 · 2009 586 · 2010 598 · 2011 615 · 2012 786 · 2013 858 · 2014 801 · 2015 866 · 2016 844 · 2017 777 · 2018 837 · 2019 843 · 2020 744 · 2021 786 · 2022 861 · 2023 1,095 · 2024 990 · **2025 847** · **2026 262**.

### Sold these days

File max date is **1 May 2026** (3 units that day). Sent 23 Jul, so May–Jul 2026 registrations are not in it.

**2026 YTD in file = 582 unique / 262 N75\* / 268 NPR75+NPR88.**

N75\* by month 2026: Jan 66 · Feb 42 · Mar 94 · Apr 57 · May 3.

That is **registrations**, not deliveries after 1 May. Future P700 arrivals (`P700 ITUK TRUCK ARRIVALS.xlsx`, Duncan 17 Jul) are a plan (N75 100 in Oct-26, then 50–118/month) — not sold.

### Still in parc vs sold

**Cannot split.** No licensed / re-tax / scrapped flag (one row says WRITTEN OFF). The file is a registration extract from 2008. DVLA 2024A N75 UIO is **9,359** — smaller than 14,308 N75\* in the file — so many older regs have left the live parc. Do not treat 14,308 as current licensed UIO. Do not invent GPS% from this list.

---

## 3. Clutch — 47% used

**Used. Cannot derive from the VIN file.**

Duncan 17 Mar 2026 (*RE: PMS data request*): VIN / model-year format **not available**. The 23 Jul file still has no transmission column. Engine/cab PN columns are empty.

Outlook body search did not find Duncan writing the digits “47%” in mail. The figure we already run is the **ITUK/Duncan-side v7 convention**: *“~47% DVLA fleet manual”* (interval UIO Lookup; v7 clutch UIO 10,549 of 22,389). Jerome’s instruction: if the file cannot give MT/AT, **use 47% and cite Duncan + date**.

| Convention | Implied manuals (not VIN-verified) |
|---|---:|
| 47% of 14,308 N75\* | 6,725 |
| 47% of 12,055 NPR75+NPR88 | 5,666 |
| v7 full DVLA (context only) | 10,549 |

Source row: `ituk_clutch_47pct.csv`.

---

## 4. Brakes — 6–8 weeks quote and 0.4

### What Duncan said

**13 Aug 2026** pack (`PMS Project 18_08_2026.pptx`), slide “Why the UK launch must be N75-led”:

> **6-8 wks** · Safety events · *Regular inspection cycle gives practical brake conversion trigger*

Same slide: *At 50,000 km/year, ISUZU is shown at approx. 1.25 services/year versus DAF at 0.5.*

That is a **UK safety-inspection / visit cycle**, not “ITUK data arrives in 6–8 weeks”, and not a brake **replacement** interval.

**14 Aug 2026 09:05** Rev2 (`PMS Project 18_08_2026_Rev2.pptx`). Duncan: *Please use this version and not the previous one I sent.* The 6–8 week safety slide is **dropped**. Rev2: brakes are **condition-based; no promotional trigger**. R&M / safety targeting out of the PMS hour.

### Mileage fact-check

VIN file has **no km**. Use Duncan’s own 50,000 km/year (13 Aug slide + v7).

| If 6–8 weeks is a visit | At 50,000 km/yr |
|---|---|
| 6 weeks | ~5,770 km between visits · ~8.7 visits/yr |
| 8 weeks | ~7,690 km between visits · ~6.5 visits/yr |

GIDSS N75 (Rene 16 Jul): brake pads **inspect every 20,000 km**, not replace. Treating 6–8 weeks as wear would imply 6.5–8.7 replacements/year — not a brake figure.

ITUK wear **0.4** is already sourced: 40,000 / 100,000, front+rear as one paired job (`pms_capture_assumptions.yaml`, ITUK override; Jerome 14 Jul 2026 O-Licence note). IML v7 full-parc brake freq is **0.5** (50,000/100,000) — different model; do not blend.

### Conclusion

**Keep 0.4 until ITUK wear/sales data.** Date the wait: still open on 15 Aug 2026.

6–8 weeks is an **operating visit** figure (13 Aug), then **taken out of the PMS hour** (14 Aug Rev2). Combining it with 50k km/yr gives an inspect-opportunity band only. **Do not lock a new wear factor.** Label if shown: *Duncan 6–8 weeks, not locked.*

---

## 5. P700 unpriced fast-movers — on disk

**On disk.** James Marsh, *Unpriced Parts*, 29 Jul 2026, attachment `Unpriced P700 Parts .xlsx`.

Working copy:

`C:\Users\jerom\Desktop\claude\ISZE\01_data\90_INBOX\P700_Unpriced_JamesMarsh\2026-07-29_Unpriced_P700_Parts_.xlsx`

PN csv: `C:\Users\jerom\Desktop\claude\ISZE\01_data\00_derived\ituk_p700_unpriced_fastmovers_20260729.csv`

Mail: *the attached are the predicted fasted moving parts for P700. I need costs asap.* Same workbook first sent **2 Jun 2026** (108 lines, all BP blank). 29 Jul is the **32-line predicted fast-mover** subset (all 32 were already on the June list). **Every BP cell is still empty.**

### 32 PNs (all unpriced)

8977938870 ROTOR; SENSOR · 8976788990 LAMP; LICENSE PLATE · 8978757492 / 8978757482 LAMP ASM; HEAD · 8978233282 / 8978233192 GRILLE; RAD · 7552762530 LINER; LEAF SPR,FWD FRT · 7552578110 / 7552365471 PIPE; HTR · 7552666980 PANEL ASM; FRT · 8972731430 PIN; RR SPR · 8976639460 HOSE; WASHER · 7552040890 CABLE; BATTERY · 7552704250 BACK ASM; SEAT · 7552950730 / 7551934290 SWITCH; COMB · 7552743670 / 7552743660 SPRING ASM; LEAF,FRT · 7552348641 RUBBER; CUSHION,FRT SPR · 8977954220 LOCK; DOOR,FRT DOOR · 7552035740 PUMP ASM; WATER · 8978255150 GENERATOR ASM · 7552683720 TRANSMITTER ASM; AUTO DOOR LOC · 7552426960 SWITCH; POWER WINDOW · 8978394202 SENSOR; STEERING POSITION · 7552125680 GLASS; WINDSHIELD · 8979352602 BACK ASM; PASSENGER SEAT · 8976633560 PIVOT ASM; FRT WIPER · 7552005440 RING SET; PISTON,STANDARD · 7475448400 SHAFT ASM; STRG · 7552191086 PUMP ASM; OIL · 7552777500 CONTROL UNIT; BCM

Separate open: **James Marsh PMS SPA template + ITUK sales price** — asked 17 Jun, chased 23 Jun. Still open. Not the same file as the P700 fast-movers.

This note does not propose an ISZE cut.

---

## Duncan mail dates (this pack)

| When | Subject | Why |
|---|---|---|
| 15 Jan 2026 | RE: Cabs ordering process | Older Fleet VIN 2014–2024 |
| 17 Mar 2026 | RE: PMS data request | VIN format not available; CBU Master sent |
| 2 Jun 2026 | Unpriced P700 (James) | First 108-line unpriced list |
| 17 Jun / 23 Jun 2026 | PMS follow-up (Jerome → James) | SPA template + ITUK sales price still owed |
| 17 Jul 2026 | RE: P700 order | P700 truck arrivals plan (not sold) |
| **23 Jul 2026** | **RE: Meeting today** | **Full VIN list** |
| 29 Jul 2026 | Unpriced Parts (James) | 32 predicted P700 fast-movers, BP still blank |
| 13 Aug 2026 12:44 | ITUK\IML Meeting Material | PMS pack with **6–8 wks safety events** |
| 13 Aug 2026 15:59 | RE: ITUK\IML Meeting Material | Happy with Jerome’s draft direction |
| **14 Aug 2026 09:05** | RE: ITUK\IML Meeting Material | **Rev2 — use this; 6–8 week targeting removed** |

---

## Paste block (briefing)

```
ITUK VIN (Duncan 23 Jul 2026, unique): 29,926 total · 14,308 N75* · 12,055 NPR75+NPR88.
Sold these days = 2026 regs in file to 1 May: 262 N75* (268 NPR75+NPR88). File has no later months.
Parc vs sold: cannot split — no licensed flag. Do not treat 14,308 as current DVLA UIO (2024A N75 = 9,359).
Clutch: 47% used. File has no transmission (Duncan 17 Mar: VIN format not available). Cite v7 ~47% DVLA fleet manual.
Brakes: keep 0.4 until ITUK data. Duncan 13 Aug: “6-8 wks / Safety events / Regular inspection cycle gives practical brake conversion trigger.” That is a visit cycle, not data arriving, not replace-every-6-8-weeks. Rev2 14 Aug took it out of the PMS hour. At his 50,000 km/yr, 6–8 weeks ≈ 5.8–7.7k km inspect gap. Label “Duncan 6–8 weeks, not locked” if shown. Do not lock a new wear factor.
P700 unpriced fast-movers: on disk — James Marsh 29 Jul, 32 PNs, all BP blank (chased since 2 Jun). IML base costs still owed. SPA template (17/23 Jun) still open.
```

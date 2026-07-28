# Figure comparison — mailbox vs this study (Jerome prep)

## What Rene / GIDSS actually show (N & F workshop manuals)

Source: Rene Paul (ISD Germany) · **Re: Interval maintenance** · 16 Jul 2026  
Attachments already in `01_data/03_PMS/service_schedules/`:
- `GIDSS_maint_N_MY14.pdf` / `GIDSS_maint_N_MY24.pdf`
- `GIDSS_maint_F_MY14.pdf` / `GIDSS_maint_F_MY24.pdf`

These are **OEM GIDSS maintenance schedules**, not an annual-mileage table. Mileage is still a planning input.

### NPR75 / N75 (4HK1) — what the sheets say

| Item | MY14 (older NPR75) | MY24 (current NPR75 / 4HK1) | Our Apr study |
|------|--------------------|-----------------------------|---------------|
| Engine oil + oil filter | **every 22,500 km** (or 14 mo) | **every 40,000 km** (or 12 mo) · *except Israel = 22,500* | **40,000 km** ✓ matches MY24 |
| Fuel filter element | **every 45,000 km** | **every 40,000 km** (or 12 mo) | **40,000 km** ✓ |
| Air cleaner | Inspect ~11.25k · Replace **45,000 km** | Indicator / condition-based | Modelled **40,000 km** (planning) |
| Clutch fluid (M/T) | Replace ~22.5k | Replace **40,000 km** (fluid) | Disc/kit still **100,000 km** wear assumption |
| Brake pads / rotors | Inspect frequently | Inspect every **20,000 km** | Replace modelled **100,000 km** |
| Service light (MY24 note) | — | Illuminates by **max 40,000 km** | — |
| Severe 4HK1 oil/filter | **every 10,000 km** | more frequent (severe table) | not used in headline |

**Verdict for the meeting:** current NPR75 GIDSS supports **oil/fuel every 40k**, not the Mar kick-off oil-at-20k row. Keep Scenario B (50k km/yr ÷ 40k) as the study standard; cite GIDSS as the interval source when asked.

Annual mileage is **still not in GIDSS** — kick-off used **20,000 km/yr** as an example; Apr study uses **50,000 km/yr**.

---

## What mailbox shows (IML / ITUK process)

### IML kick-off (Mar 2026) — FIG-KEY potential table
- Example mileage for potential: **20,000 km/yr**
- Oil filter interval listed at **20,000 km**
- Fuel/air **40,000 km**; clutch/brake **100,000 km**
- Ask for: UIO with VIN + model year + model; annual mileage; replacement frequency by PMS category

### ITUK replies (Duncan)
- VIN / model-year format: **not available**
- Sent: UIO, CBU master (from 2021), R&M 7 years, **Sales to Dealers + fig-key (CY2025)**
- Execution: review frequencies → target items → promotion plan; N75 / brake+air first

### Apr 2026 analysis (aligned study — full DVLA)
| Item | Value |
|------|-------|
| Mileage | **50,000 km/yr** |
| Oil / fuel / air interval | **40,000 km** → freq **1.25**/yr |
| Clutch / brake | **100,000 km** → freq **0.5**/yr |
| Clutch UIO | **~47%** of fleet (manual convention) |
| Oil cover DB | **35.1%** (9,818 / 27,986) |
| Oil cover DLR | **40.6%** |
| 5-cat gap | **~€2.04M** |

### N75 pilot cut (same schedule, UIO = 9,359)
From `ISZE_ITUK_PMS_Interval_Model_2026-07-22.xlsx` (N75 Method A = both engine gens):

| Layer | Oil cover | 5-cat gap |
|-------|-----------|-----------|
| ASC→DB (N75) | **~40.0%** | **~€666k** |
| DB→DLR WS2025 (N75) | **~46.2%** | **~€647k** |

ASC→DB N75 actuals are **share-scaled estimates**; DLR N75 is **bottom-up PN split** (exclude N35 + F-Series).

---

## Why % can disagree (same actuals)

| Scenario | Mileage | Oil interval | Expected oil | Cover on 9,818 actual |
|----------|---------|--------------|--------------|------------------------|
| A Kick-off example | 20k | 20k | ~22,389 | **~43.9%** |
| B This study (meeting) | 50k | 40k | 27,986 | **35.1%** |
| C Mixed (dangerous) | 50k | 20k | ~55,972 | **~17.5%** |
| D N75 cut (same B schedule) | 50k | 40k | 11,699 on UIO 9,359 | **~40.0%** oil DB |

Scenario C is how an old ~17% oil baseline appears — **do not mix with B**.

## Deliverable

`ISZE_ITUK_UTI_PMS_Study_CY2025_for_IML.xlsx` — live formulas; yellow = inputs;  
sheets `02b_ITUK_N75_DB` / `03b_ITUK_N75_DLR` = pilot cut; `04_Figure_Bridge` = A/B/C + GIDSS note.

# PMS / Service / Maintenance Intervals — Authoritative Mailbox Sources Only

**Created:** 2026-07-27  
**Author filter (hard rule):** only intervals traceable to mail and/or PDF attachments from:

| Person | Role / entity | Email (from Outlook) |
|--------|---------------|----------------------|
| **Duncan Young** | Parts Director, Isuzu Truck (UK) Ltd (ITUK) | `duncan.young@isuzutruck.co.uk` |
| **Takayoshi Suzuki** | ISZJ / IML International Parts | `Takayoshi_Suzuki@isuzu.com` |
| **René Paul** | Aftersales Service Specialist, Isuzu Motors Germany GmbH (IMG) | `rene.paul@isuzu.de` |

**Search method:** Outlook COM across Jerome’s mailbox stores (`jerome.van.der.pluym@isuzu-e.com`, Sales, Parts), Restrict filters on sender name/email, subject search for `Interval maintenance` / `maintenance schedule` / `service interval` / `PMS interval`, PDF attachment save + text/visual extraction.

**Deliverable path:**  
`C:\Users\jerom\Desktop\claude\ISZE\01_data\90_INBOX\PMS_Intervals_Authoritative_Sources.md`

**Working pull folder (attachments + OCR/render helpers):**  
`C:\Users\jerom\Desktop\claude\ISZE\01_data\90_INBOX\pms_intervals_mail_pull\`

---

## Executive result

| Sender | Interval numbers found? | Primary evidence |
|--------|-------------------------|------------------|
| **René Paul (IMG)** | **YES** — GIDSS workshop-manual maintenance schedules (N & F series, MY14 & MY24) | Email 2026-07-16 + 4 PDFs |
| **Duncan Young (ITUK)** | **NO** numeric service intervals | 12 inbox mails; 1 PDF (strategy/accessories, no PMS km grid) |
| **Takayoshi Suzuki (ISZJ/IML)** | **NO** numeric service intervals | 19 inbox mails; PMS = parts promotion / APL / BVP filters, not service schedule |

**Interval entries in this document:** ~55+ discrete replace/inspect intervals with explicit km/mi/months (René / GIDSS only).  
**Explicit gaps:** listed in §4 (ITUK visits/yr, IML schedule PDF from Suzuki, D-Max/RT schedules only from Georg Fischer on same thread — excluded).

---

## 1. René Paul (IMG) — authoritative

### 1.1 Source email

| Field | Value |
|-------|-------|
| **Sender** | René Paul (`Rene.Paul@isuzu.de` / `rene.paul@isuzu.de`) |
| **Date** | 2026-07-16 07:24 |
| **Subject** | `Re: Interval maintenance` |
| **Source type** | Email + PDF attachments |
| **Folder** | `\\jerome.van.der.pluym@isuzu-e.com\Inbox` |
| **Outlook EntryID** | `…0008C5EDB49F0000` (full ID in `pms_intervals_mail_pull\pdf_hits.json`) |
| **Context** | Jerome asked (2026-07-15) for N & F series (P700 + previous model) schedules; René replied with GIDSS workshop-manual PDF prints. |

**Attachments (saved under):**  
`C:\Users\jerom\Desktop\claude\ISZE\01_data\90_INBOX\pms_intervals_mail_pull\attachments\`

| Attachment filename | Saved as |
|---------------------|----------|
| `GIDSS_maint_N_MY24.pdf` | `20260716_Rene_Paul_isuzu_de_GIDSS_maint_N_MY24.pdf` |
| `GIDSS_maint_N_MY14.pdf` | `20260716_Rene_Paul_isuzu_de_GIDSS_maint_N_MY14.pdf` |
| `GIDSS_maint_F_MY24.pdf` | `20260716_Rene_Paul_isuzu_de_GIDSS_maint_F_MY24.pdf` |
| `GIDSS_maint_F_MY14.pdf` | `20260716_Rene_Paul_isuzu_de_GIDSS_maint_F_MY14.pdf` |

**Legend (all GIDSS schedules):** I = Inspect; A = Adjust; R = Replace; T = Tighten; L = Lubricate.  
Intervals are typically **odometer or months, whichever comes first**.

---

### 1.2 Market / model: N-series MY24 (P700 era) — `GIDSS_maint_N_MY24.pdf`

**PDF:** `C:\Users\jerom\Desktop\claude\ISZE\01_data\90_INBOX\pms_intervals_mail_pull\attachments\20260716_Rene_Paul_isuzu_de_GIDSS_maint_N_MY24.pdf`  
**Source type:** PDF (from René)  
**Sender / date / subject:** René Paul · 2026-07-16 · Re: Interval maintenance  
**Attachment:** `GIDSS_maint_N_MY24.pdf`

#### A) NLR88 / NMR88 / NPR88 — **4JZ1** (pages 1–3)

| Category / part | Value | Units | Action | Notes |
|-----------------|-------|-------|--------|-------|
| Engine oil | When “engine oil and filter indicator light” displayed **or** every **12** months | alert / months | R | Note *2: light illuminates by **max 40,000 km (24,000 mi)** |
| Engine oil filter | Same as engine oil | alert / months | R | Same *2 cap |
| Fuel filter element | **40,000** (also 80/120/160) | km | R | or every **12** months; Severe X |
| Fuel filter element | **24,000** (49/75/99) | miles | R | same row |
| Pre-fuel filter | **40,000** cycle | km | R | or every **12** months; Severe X |
| Air cleaner element | **I** at 20/60/100/140; **R** at **40/80/120/160** | ×1,000 km | I/R | or every **24** months R; Severe X |
| Drive belt | every **20,000** | km | I | or every **12** months |
| Engine coolant | every **12** mo I; every **24** mo R | months | I/R | when Isuzu recommended coolant used |
| Brake fluid | **40,000** | km (24,000 mi) | R | or every **24** months |
| Brake lining/pad/fluid level | every **20,000** | km (12,000 mi) | I | or every **12** months; Severe X on several items |
| Transmission oil (MYY / MYR) | **R** every **40,000** | km (24,000 mi) | R | I on alternate 20k steps; or every **24** months; Severe X |
| [M/T] Clutch fluid | **R** every **40,000** | km | R | I alternate 20k; replace every **24** months |
| [DCT] DCT clutch oil | **R** every **40,000** | km | R | or every **24** months; Severe X |
| Differential gear oil | **R** every **40,000** | km | R | or every **24** months; Severe X |
| PM sensor | **240,000** | km (149,000 mi) | R | or every **180** months |
| NOx sensor | **280,000** | km (174,000 mi) | R | or every **180** months |
| O2 sensor | **240,000** | km (149,000 mi) | R | or every **180** months |

**Grid base for this schedule:** columns at 20 / 40 / 60 / 80 / 100 / 120 / 140 / 160 ×1,000 km (12 / 24 / 37 / 49 / 62 / 75 / 87 / 99 ×1,000 miles).

#### B) NPR75 — **4HK1** / N75 (pages 3–5) — *N75 flagship for ITUK PMS math*

| Category / part | Value | Units | Action | Notes |
|-----------------|-------|-------|--------|-------|
| Engine oil (except Israel) | **40,000** | km | R | at 40/80/120/160; or every **12** months; Severe X |
| Engine oil (except Israel) | **24,000** | miles | R | same |
| Engine oil (Israel) | **22,500** | km (14,000 mi) | R | or every **12** months; Severe X |
| Engine oil filter | same as oil (ex-Israel / Israel) | km / mi | R | Severe X |
| Fuel filter element | **40,000** cycle | km | R | or every **12** months; **also** when fuel-filter indicator light on |
| Pre-fuel filter | when fuel-filter indicator light | alert | R | |
| Air cleaner element | when air-cleaner inspection indicator light | alert | I (else) | indicator-driven |
| AdBlue filter | **200,000** | km (124,000 mi) | R | Severe X |
| Brake fluid | **40,000** | km (24,000 mi) | R | or every **24** months |
| Brake pad / fluid level inspect | every **20,000** | km | I | Severe X on pad/fluid |
| Transmission oil (MZZ) | **R** every **40,000** | km | R | or every **24** months; Severe X |
| [M/T] Clutch fluid | **R** every **40,000** | km | R | or every **24** months |
| [SA] Smoother clutch oil | **R** every **40,000** | km | R | or every **24** months; Severe X |
| Differential gear oil | **R** every **40,000** | km | R | or every **24** months; Severe X |
| Power steering fluid | **40,000** | km | R | or every **24** months |
| Power steering hose | **80,000** | km (49,000 mi) | R | or every **48** months |
| PM sensor | **240,000** | km | R | or every **180** months |
| NOx sensor | **280,000** | km | R | or every **180** months |

#### C) NLR87 — **RZ4E** (pages 6–8)

| Category / part | Value | Units | Action | Notes |
|-----------------|-------|-------|--------|-------|
| Engine oil | **20,000** | km (12,000 mi) | R | every 20k step; or every **12** months; Severe X |
| Engine oil filter | **20,000** | km | R | same; Severe X |
| Oil/filter alert (*2 on later note page) | if alert shown at **&lt; 20,000** km (12,000 mi) | km | R | follow indicated interval |
| Fuel filter element | **40,000** cycle | km | R | or every **12** months |
| Pre-fuel filter | **40,000** cycle | km | R | or every **12** months |
| Air cleaner element | **R** at **60 / 120**; **I** other 20k steps | ×1,000 km | I/R | or every **24** months R; Severe X |
| Drive belt | every **20,000** | km | I | or every **12** months |
| PM sensor | **240,000** | km | R | or every **180** months |
| NOx sensor | **300,000** | km (186,000 mi) | R | or every **180** months |
| O2 sensor | **240,000** | km | R | or every **120** months (per table) |
| Power steering fluid | **40,000** | km | R | or every **24** months |

---

### 1.3 Market / model: N-series MY14 (previous) — `GIDSS_maint_N_MY14.pdf`

**PDF:** `...\attachments\20260716_Rene_Paul_isuzu_de_GIDSS_maint_N_MY14.pdf`  
**Sender / date / subject / attachment:** René Paul · 2026-07-16 · Re: Interval maintenance · `GIDSS_maint_N_MY14.pdf`

#### A) Normal schedule — NLR85 / NLS85 / NMR85 / NNR85 / NPR85 (models No. 1–2)

| Category / part | Value | Units | Action | Notes |
|-----------------|-------|-------|--------|-------|
| Engine oil (Israel) | **10,000** | km | R | or every **12** months |
| Engine oil (no PTO, except Israel) | **15,000** | km | R | or every **12** months |
| Engine oil (with PTO, except Israel) | **10,000** | km | R | or every **12** months |
| Engine oil filter | same splits as oil | km | R | Israel / PTO / no-PTO |
| Fuel filter element | **40,000** | km | R | or every **12** months |
| Pre-fuel filter | **40,000** | km | R | or every **24** months |
| Air cleaner element | **R** every **40,000**; **I** every **10,000** | km | I/R | or every **24** months |
| Clutch fluid [M/T] | **R** every **45,000** | km | R | I every ~20k; or every **27** months |
| Transmission oil | **R** every **45,000** | km | R | or every **24** months |
| Smoother clutch oil | **R** every **45,000** | km | R | or every **24** months |
| Differential gear oil | **R** every **45,000** | km | R | or every **24** months |

#### B) NPR75 model No. 1–2 (chassis continuation pages)

| Category / part | Value | Units | Action | Notes |
|-----------------|-------|-------|--------|-------|
| Brake fluid | **45,000** / **90,000** | km | R | or every **27** months |
| Power steering fluid | **40,000** / **80,000** | km | R | or every **24** months |
| Power steering hose | **80,000** | km | R | or every **48** months |
| Wheel hub bearing grease | **40,000** / **80,000** | km | R | or every **24** months |
| AdBlue filter (if equipped) | **200,000** | km (124,000 mi) | R | |
| Kingpin (rigid front) | every **10,000** | km | L | or every **12** months |
| Brake system inspect | ~ every **5,000–10,000** | km | I | table dense; see PDF p2–p3 |

#### C) Severe-condition schedule (PDF text extract, pages 4–5)

| Category / part | Value | Units | Action | Engine / note |
|-----------------|-------|-------|--------|---------------|
| Engine oil | **10,000** | km (6,000 mi) | R | **4JJ1** without PTO (except Israel) — conditions A/B |
| Engine oil | **7,500** | km (4,500 mi) | R | **4JJ1** with PTO (except Israel); also **4JJ1 Israel** |
| Engine oil | **10,000** | km (6,000 mi) | R | **4HK1** |
| Engine oil filter | same as oil rows above | km | R | 4JJ1 / 4HK1 splits |
| Air cleaner element | **I** every **5,000**; **R** every **20,000** | km | I/R | dusty (C) marked |
| Transmission oil | **20,000** | km (12,000 mi) | R | |
| Smoother clutch oil | **20,000** | km | R | |
| Differential gear oil | **20,000** | km | R | |
| Brake shoe/drum wear | **I** every **10,000** | km | I | |
| Disc pad/disc wear | **I** every **5,000** | km | I | |

---

### 1.4 Market / model: F-series MY24 — `GIDSS_maint_F_MY24.pdf`

**PDF:** `...\attachments\20260716_Rene_Paul_isuzu_de_GIDSS_maint_F_MY24.pdf`  
**Sender / date / subject / attachment:** René Paul · 2026-07-16 · Re: Interval maintenance · `GIDSS_maint_F_MY24.pdf`

#### A) Italy, Israel, Portugal, United Kingdom, Ireland — **4HK1** (section header on p1)

| Category / part | Value | Units | Action | Notes |
|-----------------|-------|-------|--------|-------|
| Engine oil | when “engine oil and filter indicator light” on MID | alert | R | Severe X |
| Engine oil filter (main + partial) | same indicator | alert | R | Severe X |
| Fuel filter (engine-side + chassis-side) | when “fuel filter indicator light” on MID | alert | R | |
| Air cleaner element | when “air cleaner inspection indicator light” on MID | alert | R (else I) | |
| Oil separator element | every **12** | months | R | |
| Fuel hose | every **48** | months | R | |
| Engine coolant | **12** mo I; **24** mo R | months | I/R | Isuzu recommended coolant |
| AdBlue filter (4HK1-TCH) | **80,000** | km (50,000 mi) | R | Severe X |
| DPD pressure check / filter cleaning | **100,000** | km (62,000 mi) | I | or every **12** months |
| PM sensor | **240,000** | km (149,000 mi) | R | |
| NOx sensor | **280,000** | km (174,000 mi) | R | |
| Brake fluid | **R** every **40,000**; **I** alternate 20k | km | I/R | or every **12** months (table) |
| Brake lining wear | every **20,000** | km | I | or every **12** months; Severe X |
| Brake hose | **R** at **80,000 / 160,000** | km | R | or every **24** months |
| ABS modulator rubber parts | every **24** | months | R | |
| Brake chamber piggy-back | every **36** | months | R | |
| Brake expander overhaul | every **36** | months | OH | |
| Brake valve / EPM | every **10** | years | R | |

#### B) Australia / New Zealand — **4HK1** & **DB6A** (later sections)

Header text in PDF (extractable): schedules split by fuel consumption **≥ / &lt; 18.2 L/100 km** (4HK1), plus separate **DB6A** block.  
**Transmission oil (ES-9306A)** extractable text includes:

| Category / part | Value | Units | Notes |
|-----------------|-------|-------|-------|
| Oil level check (linehaul) | up to **20,000** | km (12,000 mi) | |
| Manual TX oil change — Extended Eaton PS-386 | **400,000** | km (248,000 mi) | GCW &lt; 50 t |
| Manual TX oil change — Standard Eaton PS-321 | **120,000** | km (74,000 mi) | |
| MTF Gear Oil API GL-4 | **100,000** | km (62,000 mi) | |
| First TX oil change (*3 note) | initial **5,000** | km (3,000 mi) | Italy/UK block note also cites this |

**Differential / Meritor axle** (text extract p23): petroleum oil change linehaul **160,000 km** / city **80,000 km** / vocational **40,000 km** (or annually); synthetic much longer (up to **800,000 km** linehaul).

> Full engine-oil km grids for AU/NZ pages are largely image-only; treat indicator-driven EU/UK/IL/PT/IE block above as the confirmed F-MY24 4HK1 European set from this PDF.

---

### 1.5 Market / model: F-series MY14 — `GIDSS_maint_F_MY14.pdf`

**PDF:** `...\attachments\20260716_Rene_Paul_isuzu_de_GIDSS_maint_F_MY14.pdf`  
**Sender / date / subject / attachment:** René Paul · 2026-07-16 · Re: Interval maintenance · `GIDSS_maint_F_MY14.pdf`

#### A) Normal schedule (page 1 table — dense 5.5k / 11k-style columns)

| Category / part | Value | Units | Action | Notes |
|-----------------|-------|-------|--------|-------|
| Engine oil | **R** on ~**11,000** km pattern; **I** on mid steps | km | I/R | time: **I** every **3** months; **R** every **6** months |
| Engine oil filters (main/partial/combined/separator) | **R** every **22,000** | km | R | or every **6** months |
| Fuel filter | **R** at **44,000 / 88,000** | km | R | or every **9** months |
| Air cleaner element | **R** at **44,000** and **104,500** | km | R | also time-based I/R rules on table |
| Clutch fluid [M/T] | **R** at **55,000 / 115,500** | km | R | I frequent; **R** every **15** months |
| Engine coolant | every **24** | months | R | |

#### B) Severe-condition (text extract pages 5–6) — mentions **4HK1** oil separator

| Category / part | Value | Units | Action | Conditions |
|-----------------|-------|-------|--------|------------|
| Air cleaner element | **24,000** | km (15,000 mi) or after 6th cleaning | R | dusty (C) |
| Engine oil | **10,000** | km (6,000 mi) | Change | A/B/C marked |
| Engine oil filter | **10,000** | km | Change | A/B/C |
| Engine oil separator (4HK1) | **10,000** | km | Change | A/B/C |
| Transmission oil | **24,000** | km (15,000 mi) | R | A/B |
| Clutch fluid [M/T] | **24,000** | km | Change | A |
| Smoother clutch oil | **24,000** | km | Change | A/B |
| Rear axle differential oil (Isuzu axle) | **24,000** | km | Change | A/B |
| Brake lining wear | **I** every **2,500** | km (1,500 mi) | I | A/B/C/D |
| Brake drum wear | **I** every **20,000** | km | I | A/B/C/D |

---

## 2. Duncan Young (ITUK) — searched; **no interval numbers**

### 2.1 Mailbox hits (Inbox Restrict on “Duncan”)

**12 messages** from `Duncan Young` / `duncan.young@isuzutruck.co.uk` (Jun–Jul 2026 sample in live Inbox). Subjects include P700 order, BPFY revision, Parts Month End, Meeting today, engine VIN queries, etc.

**Keyword scan of full bodies:** no `oil change` / `xx,000 km` / air-fuel filter **service interval** statements.

### 2.2 PDF from Duncan

| Field | Value |
|-------|-------|
| **Date** | 2026-07-23 14:41 |
| **Subject** | `RE: Meeting today` |
| **Attachment** | `Parts Business & Service product.pdf` |
| **Saved as** | `C:\Users\jerom\Desktop\claude\ISZE\01_data\90_INBOX\pms_intervals_mail_pull\attachments\20260723_Duncan_Young_Parts_Business_Service_product.pdf` |
| **Content** | IML/ISZE parts strategy, Vision 2030, R&M programme framing, D-Max accessories — **no PMS km/mi service grid** |

### 2.3 What Duncan mail *does* say (non-interval)

- Mentions PMS Parts as a discussion point (`RE: P700 order`, 2026-07-20).  
- No oil/air/fuel/brake/clutch interval values.

**→ Duncan section: zero authoritative interval entries.**

---

## 3. Takayoshi Suzuki (ISZJ / IML) — searched; **no interval numbers**

### 3.1 Mailbox hits

**19 messages** from `Takayoshi Suzuki ISZJ` / `Takayoshi_Suzuki@isuzu.com` in Inbox (Restrict). Topics: PMS **parts promotion**, BVP air filters, APL zip, SPA, meetings, Russian steel priority lists, SPI sheets.

### 3.2 Closest PMS-adjacent content (not service intervals)

| Date | Subject | What it contains | Interval? |
|------|---------|------------------|-----------|
| 2026-07-27 / 07-24 | Demand forecast PN `5876102500` ELEMENT AIR CLEANER | BVP filter on **PMS Parts Promotion list**; ITUK awareness | **No** km interval |
| 2026-07-23 | Recommended parts list ITUK | APL zip `20260714_1037.zip` | Parts list, not schedule |
| 2026-07-24 | RE: Meeting | PMS promotion schedule for Aug 18 meeting | Meeting agenda, not service km |

**→ Suzuki section: zero authoritative interval entries.**  
IML “official” service schedule PDF was **not** found as an attachment from Suzuki in this mailbox pull.

---

## 4. Explicit gaps (do **not** treat as authoritative under the three-sender rule)

| Gap | Why excluded / missing |
|-----|------------------------|
| **D-Max / RT56 / RT88-93 / RG / RG21 / BEV RG20 Service Maintenance Schedules** | Present in mailbox on **same thread** (`Interval maintenance`) but sent by **Georg Fischer** (`Georg.Fischer@isuzu.de`, 2026-07-15), **not** René/Duncan/Suzuki. PDFs saved for reference under `attachments\20260715_Georg_Fischer_*` but **not** entered as interval rows above. |
| **ITUK “visits per year” / annual service visit count** | Not stated in Duncan mail/PDF in this search. |
| **IML factory schedule PDF from Suzuki / ISZJ** | Not found as Suzuki attachment. René’s GIDSS prints are workshop-manual extracts (IML copyright on footers), but **channelled via IMG René**, not Suzuki mail. |
| **N35-specific schedule** | Not labelled “N35” in René PDFs; closest is N-series MY14/MY24 model codes (NLR/NMR/NPR…). |
| **Online Archive deep history** | Outlook Restrict returned **0** Duncan/Suzuki/René hits under `Archive\…\customers\ITUK|IMG|IML` in this pass (likely incomplete local sync). Live **Inbox** is where the GIDSS PDFs were found. Older interval mails may exist only in online archive / another mailbox. |
| **Jerome’s own interval models (xlsx/docx)** | Present in Sent (`PMS`, `IML PMS`) — **excluded by design** (not from the three senders). |

---

## 5. Quick reference — PMS-critical replace intervals (René / GIDSS only)

Useful for N75 / 4HK1 / 4JZ1 potential calculations. All from René 2026-07-16 PDFs.

| Vehicle / engine | Oil change | Oil filter | Air cleaner | Fuel filter | Brake fluid | Clutch fluid / oil |
|------------------|------------|------------|-------------|-------------|-------------|--------------------|
| **NPR75 MY24 4HK1 (N75)** | **40,000 km** / 12 mo (Israel **22,500 km**) | same | indicator | **40,000 km** / 12 mo (+ indicator) | **40,000 km** / 24 mo | **40,000 km** / 24 mo |
| **NLR/NMR/NPR88 MY24 4JZ1** | indicator (max **40,000 km**) / 12 mo | same | **R 40,000 km** | **40,000 km** / 12 mo | **40,000 km** / 24 mo | **40,000 km** / 24 mo |
| **NLR87 MY24 RZ4E** | **20,000 km** / 12 mo (alert may be earlier) | same | **R 60,000 km** | **40,000 km** / 12 mo | *(see PDF chassis pages)* | *(see PDF)* |
| **N85 MY14 family** | **10k / 15k / 10k** km (Israel / no-PTO / PTO) | same | **R 40,000 km** | **40,000 km** | *(chassis pages)* | **45,000 km** clutch |
| **N MY14 severe 4HK1** | **10,000 km** | **10,000 km** | **R 20,000 km** | *(see PDF)* | inspect denser | TX **20,000 km** |
| **F MY24 4HK1 (IT/IL/PT/UK/IE)** | MID oil indicator | same | MID air indicator | MID fuel indicator | **R 40,000 km** | *(F brake-heavy pages)* |
| **F MY14 severe** | **10,000 km** | **10,000 km** | **24,000 km** / 6th clean | *(normal table 44k)* | lining **2,500 km** I | clutch **24,000 km** |

---

## 6. Provenance checklist (per user rules)

For every interval row in §§1.2–1.5:

- [x] Value + unit recorded  
- [x] Part / category recorded  
- [x] Vehicle / model / engine recorded when stated on the PDF page  
- [x] Source type = **PDF** (René)  
- [x] Sender = **René Paul**  
- [x] Date = **2026-07-16**  
- [x] Subject = **Re: Interval maintenance**  
- [x] Attachment filename = one of the four `GIDSS_maint_*.pdf` names  

Duncan / Suzuki: searched; **no interval rows** added.

---

## 7. Files created during this pull

| Path | Purpose |
|------|---------|
| `C:\Users\jerom\Desktop\claude\ISZE\01_data\90_INBOX\PMS_Intervals_Authoritative_Sources.md` | This reference |
| `C:\Users\jerom\Desktop\claude\ISZE\01_data\90_INBOX\pms_intervals_mail_pull\attachments\` | PDFs from René (+ Duncan strategy PDF; Georg out-of-scope copies) |
| `C:\Users\jerom\Desktop\claude\ISZE\01_data\90_INBOX\pms_intervals_mail_pull\pdf_pages\` | Rendered PNG pages of René GIDSS PDFs |
| `C:\Users\jerom\Desktop\claude\ISZE\01_data\90_INBOX\pms_intervals_mail_pull\sender_hits.json` | Outlook sender Restrict hits |
| `C:\Users\jerom\Desktop\claude\ISZE\01_data\90_INBOX\pms_intervals_mail_pull\fullbody_Re_Interval_maintenance.txt` | Full René thread body |

---

*End of authoritative extract. Do not merge Georg Fischer or local PC spreadsheet intervals into this list without a new mail/PDF from Duncan, Suzuki, or René.*

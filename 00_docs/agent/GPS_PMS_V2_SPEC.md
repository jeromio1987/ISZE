# GPS / PMS V2 — product & status spec (Mode B)

**Role:** single V2 **status spine** (not a second dashboard)  
**Updated:** 2026-09-05  
**Audience:** Jerome / agents · Mode B only  
**Companion concept:** [`GPS_PMS_V2_CONCEPT.md`](GPS_PMS_V2_CONCEPT.md) (formula + dual-lane locks)  
**UI shell:** Aftermarket BI Command Center tab **GPS/PMS V2 LCV** only

---

## 1. Verdict (read this first)

**Car park is NOT fully fixed.**

| Layer | Truth today |
|-------|-------------|
| **Live UIO workbook** | **V19** still drives network LCV denominators |
| **V20** | **Draft only** — survival / scrap rebuild **not applied** to `ISUZU_UIO_Overview_2026.xlsx` |
| **Only locked GPS figure from V20 math** | **IUK LCV CY2026F = 44,926** (Decision 30 Jul 2026) — use for FY27 GPS / Extended Target; **do not** quote V19’s 49,280 |
| **Network LCV shape** | Still mostly **flat `LCV` mtype** — no Trooper / RT / RG rows on UIO Overview |
| **V2 demand** | **Opt1 mileage shadow live**; Opt2/Opt3 = skeleton / partial; **not** Mode A cutover |

Do **not** tell anyone “the car park is fixed.” Forecast columns (2026–2030) still carry the 3 % scrap bug until V20 is built and applied.

---

## 2. What IS fixed / live for V2

| Item | Status | Evidence / path |
|------|--------|-----------------|
| **Opt1 mileage shadow** | Live default | `eu_mileage_by_db_lcv.csv` · `pms_capture_by_db_year_v2_mileage.csv` · builder `build_gps_pms_v2_shadow.py` — **16** DBs with LCV km mapped |
| **Trooper interval = RT** | Locked | `gps_pms_v2_config.yaml` → `generation_interval_km.trooper: 20000` · [`GPS_PMS_V2_TROOPER_SCHEDULE.md`](GPS_PMS_V2_TROOPER_SCHEDULE.md) |
| **UIO accuracy ranks A–D** | Framework live (hover) | `lcv_uio_accuracy_by_db.csv` — almost all LCV DBs still **C** or **B**; **no rank A** yet |
| **Portugal Opt2 skeleton** | Partial enable | Matriculas RT/RG shares scaled to UIO; Trooper=0; **rank B**, not A · `pms_v2_lcv_opt_skeleton.csv` |
| **Ireland Opt2 skeleton** | Enabled (aggregate) | SIMI Trooper vs D-Max+TFS; **RT/RG not separable** — D-Max on RT col, RG=0; Trooper interval = RT 20k · rank B |
| **Portugal Opt3** | Enabled (Matriculas) | Share age ≤10 at 2025-12-31 from Matriculas SUM year columns — **preferred over VIN proxy** |
| **Opt1 sensitivity** | Live CSV | `pms_v2_lcv_opt1_sensitivity.csv` — mid/low/high = DB km ±20%; mid = current Opt1 |
| **EQ-HIT priority ranking** | Artefacts on disk | `eqhit_priority_ranking_cy2025.md` / `.csv` + top PNs — **attack order by EUR gap**, full catalogue accepted (not a top-20 cut) |
| **EQ-HIT pull playbook** | Doc only | [`EQ_HIT_PULL_PLAYBOOK.md`](EQ_HIT_PULL_PLAYBOOK.md) — skip oil_filter; clutch/brake first; extract schema |
| **EQ-HIT extract → V2 fitment** | **Wired (shadow)** | `eqhit_extract_priority_cy2025.csv` (2311×37) → `pms_v2_fitment_weights.csv` + gap CSVs · oil stays BVP · seed-PN scope · Mode B pack [`GPS_PMS_V2_EQHIT_ANALYSIS_2026-09-05.md`](GPS_PMS_V2_EQHIT_ANALYSIS_2026-09-05.md) |
| **Aftermarket BI V2 tab** | Live shell | `02_dashboards/sales/ISZE_Aftermarket_BI_Command_Center.html` — tab **GPS/PMS V2 LCV** (Opt chips + EQ-HIT gap list + sensitivity) |
| **Dual-lane rule** | Hard lock | **V1** = network KPI / verify · **IML Model B** ITUK = external IML · **V2 shadow** = Mode B + BI tab only — **V1 CSVs untouched** · V1↔V2 claims: [`GPS_PMS_V2_CLAIM_FRAMEWORK.md`](GPS_PMS_V2_CLAIM_FRAMEWORK.md) |
| **IUK CY2026F lock** | Number locked for GPS | **44,926** (−6.0 % vs 2025E 47,783) — see [`06_uio/_CURRENT/V20_SPEC.md`](../../06_uio/_CURRENT/V20_SPEC.md) Decision |

---

## 3. What is NOT fixed

| Item | Why it matters |
|------|----------------|
| **Subtype SSOT for most DBs** | Opt2 stays **off** except Portugal (RT/RG) + Ireland (Trooper vs D-Max aggregate) — see [`GPS_PMS_V2_LCV_SUBTYPE_SSOT.md`](GPS_PMS_V2_LCV_SUBTYPE_SSOT.md) |
| **IUK SMMT / DVLA LCV file** | Not in repo — needed for Opt2 + rank A on IUK · chase sheet [`IUK_SMMT_LCV_DATA_ASK_SPEC.md`](IUK_SMMT_LCV_DATA_ASK_SPEC.md) |
| **SCR cutoffs (15k vs 20k)** | Still need from IMIT — not applied in shadow (`gps_pms_v2_findings.md`) |
| **Opt3 reg-year network-wide** | Portugal Matriculas live; VIN `cohort_date` proxy for ~6 other DBs; most Opt3 still off · [`GPS_PMS_V2_10Y_DEFINITION.md`](GPS_PMS_V2_10Y_DEFINITION.md) |
| **V20 survival rebuild applied to workbook** | Draft exists; live file still V19 3 % rule → fleet grows when regs fall |
| **Rank A UIOs** | Zero DBs at gov+subtype bar today (Portugal B with RT/RG; Ireland B Trooper vs D-Max aggregate, no RT/RG) |
| **Israel gov extract / UTI≠UMI for IDS** | V20 Problem 4 still open (file, not slide photo); IDS Israel = UMI only |
| **CV / N75 V2 league** | Deferred — LCV-first |
| **Mode A cutover / overwrite V1** | Explicit rebuild/ship OK required — not done |
| **Full EQ-HIT catalogue** | Extract is **37 seed PNs** only — clutch_kit / air / urea / bearings still BVP stub; Opt2 PN generation intensity thin |

---

## 4. Car park vs V2 demand engine

Two different jobs. Fixing one does not fix the other.

| | **Car park (UIO denominator)** | **V2 demand engine (expected)** |
|--|--------------------------------|----------------------------------|
| **Question** | How many vehicles are on the road (and of which generation / age)? | How many service events / parts should that parc generate? |
| **Live source** | UIO Overview **V19** + IMIT LCV bucket | Opt1: UIO_LCV × (km/yr ÷ interval) × parts × addressable × weights |
| **Broken / draft** | V20 scrap fix **not applied**; forecast inflated; IUK 2026F locked only as a **number** for GPS |
| **V2 options** | Rank A–D quality of the denominator | Opt1 mileage · Opt2 generation · Opt3 age≤10y |
| **Formula (concept)** | Survival / regs / scrap on the workbook | `expected = Σ(UIO_opt × km ÷ interval × parts × …)` |
| **SSOT notes** | `06_uio/_CURRENT/V20_SPEC.md` | `GPS_PMS_V2_CONCEPT.md` + this SPEC |

**Rule of thumb:** Opt1 can improve **intensity** (svc/yr) on a flat LCV park today. It **cannot** invent Trooper/RT/RG counts or fix a wrong 2026–2030 UIO path. Rank A + V20 application are car-park work; EQ-HIT is fitment for Opt2 PN-level demand later.

---

## 5. Shadow status snapshot (derived)

| Artefact | Role | Snapshot (2026-09-05) |
|----------|------|------------------------|
| `eu_mileage_by_db_lcv.csv` | LCV km/yr | 16 DBs mapped |
| `lcv_uio_accuracy_by_db.csv` | Rank + Opt2 flag | Mostly **C**; Ireland/Portugal **B**; Opt2 True **Portugal + Ireland** |
| `pms_v2_lcv_opt_skeleton.csv` | Opt1/2/3 expected | Opt1 on; Opt2 PT+IE; Opt3 PT Matriculas + VIN proxy elsewhere |
| `pms_v2_lcv_opt1_sensitivity.csv` | Opt1 mid/low/high | DB km ±20%; mid = current Opt1 |
| `pms_capture_by_db_year_v2_mileage.csv` | Capture V1 vs V2 | Shadow only — do not quote as network KPI |
| `gps_wallet_v2_by_distributor.csv` | Wallet index | Shadow |
| `gps_pms_v2_findings.md` | Read-out | EQ-HIT overlay + V1→V2 movers + wallet |
| `pms_v2_fitment_weights.csv` | Fitment | BVP baseline + EQ-HIT extract overlay (7 cats); oil = BVP skip |
| `pms_v2_eqhit_*` | Coverage + gaps | `fitment_coverage` · `category_gap_cy2025` · `contested_by_db_cy2025` |
| `eqhit_priority_ranking_cy2025.*` | Pull sequence | Ranking done |
| `eqhit_extract_priority_cy2025.*` | Extract SSOT | **2311 rows / 37 PNs** — wired into shadow |
| `EQ_HIT_PULL_PLAYBOOK.md` | Pull SOP | Skip oil_filter; no further pulls unless Jerome asks |
| `GPS_PMS_V2_EQHIT_ANALYSIS_2026-09-05.md` | Mode B pack | Movers / wallet / contested / stub |

---

## Solo progress (2026-09-05)

- Ireland Opt2 **ON** — SIMI Trooper vs D-Max aggregate (RT/RG not separable).
- Portugal Opt3 **ON** — Matriculas share age ≤10 preferred over VIN.
- Opt1 sensitivity CSV live (±20% DB km).
- Aftermarket BI V2 tab shows Opt status chips + sensitivity + EQ-HIT contested gaps.
- EQ-HIT extract **wired into shadow fitment** (analysis, not more pulls).
- Monday Outlook draft left alone.

---

## 6. Next Monday — human actions (agent: no send)

Draft/reminder only. **Do not** Send Outlook from agent unless Jerome explicitly says send/verstuur for that mail.

| # | Who | Action | Path / note |
|---|-----|--------|-------------|
| 1 | Jerome → **Koen** | Push **sales-to-dealer (StD)** from DBs still missing it; SPA / price complaints only after StD data is on the table | Self-reminder body: `09_meetings/_MONDAY_SELF_REMINDER_StD_SPA/body.txt` |
| 2 | Jerome → **Aaron / John (IUK)** or Koen routes | Chase **SMMT/DVLA LCV** car park by vintage + model (Trooper / RT / RG mappable) | Ask sheet: [`IUK_SMMT_LCV_DATA_ASK_SPEC.md`](IUK_SMMT_LCV_DATA_ASK_SPEC.md) · V20 Still open · **do not re-ask** locked **44,926** |

Independent of EQ-HIT pull status.

---

## 7. Pointer map (do not fork status elsewhere)

| Doc | Owns |
|-----|------|
| **This SPEC** | Fixed / not fixed / Monday actions / car park vs demand |
| [`GPS_PMS_V2_CONCEPT.md`](GPS_PMS_V2_CONCEPT.md) | Opt1/2/3 formula, dual-lane, EQ-HIT lock, UI shell |
| [`GPS_PMS_V2_CLAIM_FRAMEWORK.md`](GPS_PMS_V2_CLAIM_FRAMEWORK.md) | V1↔V2 metric contracts, evidence grades, EQ-HIT claim gate, dig protocol |
| [`ISZE_BI_OPTIMIZATION_FRAMEWORK.md`](ISZE_BI_OPTIMIZATION_FRAMEWORK.md) | BI homes / pack registry / visual canon — V2 lives only on CC GPS/PMS V2 tab |
| [`GPS_PMS_V2_LCV_SUBTYPE_SSOT.md`](GPS_PMS_V2_LCV_SUBTYPE_SSOT.md) | Per-DB subtype map |
| [`GPS_PMS_V2_10Y_DEFINITION.md`](GPS_PMS_V2_10Y_DEFINITION.md) | Opt3 age lock |
| [`GPS_PMS_V2_TROOPER_SCHEDULE.md`](GPS_PMS_V2_TROOPER_SCHEDULE.md) | Trooper = RT interval |
| [`IUK_SMMT_LCV_DATA_ASK_SPEC.md`](IUK_SMMT_LCV_DATA_ASK_SPEC.md) | Monday IUK chase sheet |
| [`EQ_HIT_PULL_PLAYBOOK.md`](EQ_HIT_PULL_PLAYBOOK.md) | EQ-HIT browser pull SOP + extract schema |
| [`06_uio/_CURRENT/V20_SPEC.md`](../../06_uio/_CURRENT/V20_SPEC.md) | Car park rebuild draft + IUK 44,926 + Still open |

---

## 6-bullet status (fixed / not fixed)

1. **Fixed (shadow):** Opt1 mileage-aware LCV demand + V1 dual-lane untouched.  
2. **Fixed (lock):** Trooper interval = RT 20k; IUK CY2026F **44,926** for GPS only.  
3. **Fixed (shell):** Accuracy A–D framework + Aftermarket BI V2 tab + EQ-HIT ranking artefacts.  
4. **Not fixed:** Network car park still **V19**; V20 survival rebuild **not applied**.  
5. **Not fixed:** Subtype SSOT / SMMT / SCR / network Opt3 / **rank A** UIOs.  
6. **Not fixed:** Full EQ-HIT catalogue (37 seed PNs only) — Opt2 PN generation intensity incomplete; remaining cats BVP stub.

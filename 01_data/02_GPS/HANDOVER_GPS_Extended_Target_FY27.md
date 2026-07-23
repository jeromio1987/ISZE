# HANDOVER — FY2027 GPS Extended Target

**Date:** 2026-07-17 · **For:** Cursor / next session · **Owner:** Jerome (VP Sales ISZE)
**Deadline:** distributor agreement by **Mon 31/08/2026** — treat **Fri 28/08** as real (31st = UK bank holiday).

---

## 1. What this is

Masumi-san (MH — **he/him**) asked for the GPS reworked with the annual price increase, and for
**stretch amounts to "impose" on distributors**. Jerome calls the output the **extended target**:
each DB's FY27 BP **plus** a stretch, communicated as a business review, not a target call.

## 2. Deliverables (both built, both QA'd through Excel COM recalc)

| File | What |
|---|---|
| `C:\Users\jerom\Desktop\claude\ISZE\01_data\02_GPS\ISZE_GPS_Extended_Target_FY27.xlsx` | The model. 20 tabs. |
| `C:\Users\jerom\Desktop\claude\ISZE\09_meetings\FY27_Extended_Target_Roadmap.xlsx` | The campaign plan. 6 tabs. |

**Model tabs:** `Dashboard` · `Waterfall VP` · 16 DB tabs · `Waterfall VP (original)` · `Method`
**Roadmap tabs:** `Gantt` · `Roadmap` · `Split` · `Meeting Agenda` · `Calendar` · `Checkpoints`

## 3. THE LOGIC — do not change without Jerome

1. **UIO shifted ONE COLUMN RIGHT.** `FY25 <- CY2024`, `FY26 <- CY2025E`, `FY27 <- CY2026F`.
   Use the **detail rows** of `'1.UIO Overview'`, NOT the summary tables (rows 148/200) — those are
   themselves off by one AND carry a different, *declining* forecast (U KING LCV 2030: 43,313 vs
   the detail's 52,804 — 21.9% apart). This shift was MH's correction; every prior file has the bug.
2. **Spend/unit LCV (MH's chain):** `291.2 x 1.16 (EUR/GBP) = 337.792 -> x0.65 = 219.5648` ISZE-net FY26 base.
3. **Spend/unit CV (Jerome's call):** keep v9 rates `296 / 739 / 887`, **+5%** -> `310.80 / 775.95 / 931.35`.
4. **Price increase:** FY27 = **+5%**. FY28–FY31 = **+3%/yr** (IML policy, per MH's email).
5. `max spend = UIO x rate` · `stretch = max spend x stretch%` · **`extended target = BP FY27 + stretch`**
6. **Stretch default = 1.8%** (MH). Input cell per tab. Identical to "+1.8pp on GPS" — same arithmetic.
7. **ISZE->DB is where the target lives.** Dealer level is **amount only, never a %** — see §6.

## 4. Cell map

**LCV tabs** (IUK, UMI, NORWAY, SWEDEN, HUNGARY, FINLAND, ROMANIA, DENMARK, ICELAND):

| Cell | What |
|---|---|
| `C9:E9` | UIO CY2024 / CY2025E / CY2026F |
| `B14 C14 D14` | 291.2 -> x1.16 -> x0.65 = 219.5648 |
| `E14` `F14` | FY27 x1.05 · FY28 x1.03 |
| `E19` | max spend FY27 |
| `E20` | BP FY27 |
| `E21` | GPS % |
| **`E22`** | **stretch % — INPUT (1.8%)** |
| `E23` | stretch EUR |
| `E24` | **extended target** |
| `E25` | new GPS % |
| `A28` | DB->DLR block header — **MH method** (35% margin gross-up) |
| `C30`/`D30` | KPI dealer sales FY25 / FY26 |
| **`B31`** | **DB margin % — INPUT (35%)** — same as MH testcase `B15` |
| **`E32`** | dealer stretch `=−E23/(B31−1)` ≡ ISZE stretch / 0.65 — same as MH `E29` |
| **`E33`** | FY27 amount to reach `=D30+E32` (FY26 actual + dealer stretch) |

**Mixed tabs** (GERMANY, BELGIUM, PORTUGAL, IRELAND, GREECE, CYPRUS, MALTA) — six rows lower:
UIO `C9:E12` (LD/MD/F-Series/LCV) · rates `C17:D20` · `E25` max spend · `E26` BP · `E27` GPS ·
**`E28` stretch %** · `E29` stretch EUR · `E30` extended target · `E31` new GPS ·
DB->DLR from **`A34`** · KPI `C36`/`D36` · margin **`B37`=35%** · dealer stretch **`E38`=`−E29/(B37−1)`** ·
amount to reach **`E39`=`D36+E38`**.

`Dashboard` and `Waterfall VP` read these live. **Dashboard column offsets are `br-4 .. br+2`** where
`br` = the stretch-EUR row (23 LCV / 29 mixed). Getting this wrong shifts BP/max-spend/GPS by one — it
already happened once.

### Waterfall VP — GPS block + surplus (U/V)

Live values sit **outside** `C3:S16` so `SUM` does not eat them.

| Cell | What |
|---|---|
| `P4` | `=SUM(V13:V30)` — GPS step in the staircase (**€1,163,774**) |
| `Q4` | `=T7-C16-SUM(D5:S16)-P4` — **must stay negative** (−€211,736); bridge arithmetic needs it |
| `T5` | `=SUM(C3:S16)` — checks to Plan **€35,284,444** exactly |
| **`V9`** | **`=−Q4`** — **SURPLUS vs FY2027 Plan** (+€211,736). Same number as Q4, stated positively for Japan |
| `U9`/`U10` | Labels: surplus framing + note that Q4 stays negative on purpose |
| `U13:V30` | **18 customers with a computable stretch** (ITUK, UTI + 16 DB tabs) |
| `V13`/`V14` | ITUK / UTI as presented (V4 basis) — hardcoded |
| `V15:V23` | LCV tabs → `!E23` |
| `V24:V30` | Mixed tabs → `!E29` |
| `V31` | `=SUM(V13:V30)` — GPS total (reconciles to `P4`) |

**Not in the per-DB split (and not padded at zero):** Kazakhstan, Armenia, Ukraine (CIS ~€1.70M), MIDI, KIMA, IMG — BP but no UIO → no max spend / no stretch. That is the **€2.06M** outside the 18-country block.

## 5. Sources (all verified this session)

| Source | Path |
|---|---|
| UIO v19 | `01_data\ISUZU_UIO_Overview_2026_v19.xlsx` · `'1.UIO Overview'` detail rows (md5-identical to `06_uio\_CURRENT\`) |
| BP FY27 per DB | `01_data\91_build\bp_fy27_reviewed.json` (from `11_planning\budget_per_DB_reviewed_24042026.xlsx`) |
| BP network | `11_planning\ISZE PL Plan FY2026 2027 2028 20260205_2 -.xlsx` · `'IX study'` **row 186** (車両部品) · **G=FY27 … K=FY2031** |
| ISZE billing | `00_derived\gps_billing_fy_ALLCUSTOMERS.csv` (net_gps, GPS-audited, FY-aligned, **lubricants IN**) |
| Dealer sales | `11_planning\KPI Master File june 2026.xlsx` · `'Parts Handling'` · block row 82 |
| DB mapping | `03_analytics\Isuzu\prism\data\distributor_master_mapping.csv` |
| Waterfall | `01_data\FY2027 ISZE VP+IE Business Plan Waterfall 20263006.xlsx` · sheet `VP` (**replicated, never modified**) |
| ITUK/UTI | `01_data\ISZE_GPS_Kickback_Stretch_Proposal_FY27 _V4.xlsx` · `'Proposal FY27'` col G |

**BP row 186 runs to FY2031** (€52.096M) — my memory said FY30 was the end; that was wrong.

## 6. Findings that must not be lost

- **The KPI dealer figure is NOT ISZE billing marked up.** It runs **2.2–3.7x** (IUK 3.58x, Denmark 3.67x,
  Romania 2.19x). A 35% DB margin implies 1.54x. Observed markup ≠ MH's factor — **do not use observed
  markup to set the target.** Per Jerome (2026-07-17): use **MH's exact factors** instead —
  `dealer stretch = ISZE stretch / (1−0.35) = ISZE stretch / 0.65` (testcase `E29 = −E41/(0.35−1)`),
  then `FY27 dealer amount = FY26 KPI + dealer stretch`. Margin input sits in `B31` (LCV) / `B37` (mixed).
  Still **never quote a GPS % at dealer level** against the parc wallet (that is what broke >100%).
- **`V4` carries the pre-MH UIO bug.** `ISZE_GPS_Kickback_Stretch_Proposal_FY27 _V4.xlsx` (2026-07-06) maps
  FY27 to **CY2027F** — one year too far — and has **no +5%**. IUK: `50,202 x 250 = 12,550,500` vs this
  file's `49,280 x 230.543 = 11,361,161`. **ITUK (€376,074) and UTI (€159,024) are carried AS PRESENTED
  on that basis.** ⚠ **OPEN: rebase them, or ratify V4?** The €1,163,774 GPS subtotal mixes two vintages.
- **ITUK's stretch is not 1.8%** — it is 2.88%, from "Target Study +9% dealer sell-out". Different method.
- **Payer 66 = GREECE, not Norway.** The billing file labels it `'RSA'`; the warranty file uses `RSA` for
  **Norway**. Join those on the name and Greece's sales merge into Norway. **Live bug at source.**
  Norway = payer **86** only. Verified: Norway 1,471,434 − 407,230 warranty = 51.8% vs V4's 52.48% ✓;
  Greece 460,634 − ~23K = 437,642 = V4's 35.69% ✓.
- **Five DBs are over/near the ceiling after stretch:** FINLAND **121.3%**, ICELAND **105.2%**,
  IRELAND **104.6%**, BELGIUM 96.7%, NORWAY 96.2%. Finland breaks under the old rate too (104.9%) — that
  one is **the BP, not the model**. Pattern across 5 of 18 points at the **per-unit rate**, not the DBs.
- **BELGIUM 96.7% is a scope bug**, not a share: `ISUZU BENELUX NV` covers **BE/NL/PL/LUX** but the max
  spend counts the **Belgium parc only**. Numerator carries a parc the denominator excludes. Not fixed.
- **GERMANY:** mapping says `segment_cv=No`; UIO carries LD 1,066 + MD 34. Built as **mixed**. Mapping stale.
- **ROMANIA** absent from `distributor_master_mapping.csv`. LCV-only per v9 + UIO. Mapping gap.
- **MH's chain double-counts:** `291.2` already = `GBP400 x 0.65 x 1.12`; his `x1.16 x0.65` applies FX and
  margin **again** -> 219.5648. His own `B16` (`291.2/0.65 = 448.00 = GBP400 x 1.12`) implies ISZE-net of
  **291.2**, not 219.5648 — **24.6% apart**. The same GBP400 under v9's CV convention gives **296**.
  **Carried, not fixed, per Jerome.** LCV and CV sit on different conventions throughout.
- **Waterfall (surplus framing):** former plug was **€952,037**; GPS of **€1,163,774** over-covers by
  **€211,736**. `Q4` stays **−€211,736** so the bridge still closes to Plan (`T5` = €35,284,444 exactly).
  **`V9` = SURPLUS vs FY2027 Plan = +€211,736** (`=−Q4`) — same number, stated positively for Japan:
  identified initiatives + GPS now exceed the plan by ~€212K. Do **not** flip Q4 positive.
- **Σ per-DB BP = €33,222,362 vs €35,284,444 network** — €2.06M sits outside the split (CIS ~€1.70M of it:
  Kazakhstan / Armenia / Ukraine, plus MIDI / KIMA / IMG). Those have BP but no UIO → no stretch → omitted
  from `U13:V30` (not shown as zeros). Per-customer targets do **not** sum to the network number.
  Jerome: "not important for now".

## 7. Traps (cost me time — don't repeat)

- **`cell._style` cannot cross workbooks.** It is an array of *indices* into the source workbook's style
  tables. Copying it produces a file **Excel refuses to open**. Copy `font/fill/border/alignment/number_format`
  objects instead. See `restyle()` in `patch_waterfall.py`.
- **The waterfall's own `SUM(D5:R16)` will eat anything numeric you place in it.** MH's `-> ITUK 376,074`
  notes are **text**, which is why they never polluted it. Live values must sit **outside** `C3:S16` — they
  are now in **U/V**. The plug also needs an explicit `−P4` because row 4 is deliberately excluded from the sum.
- **openpyxl does not calculate.** Always QA via Excel COM `CalculateFullRebuild()` before reporting.
- **cp1252 crash:** always `PYTHONIOENCODING=utf-8`.
- **Partial-year KPI:** Finland FY26 = 6/12, Norway 11/12, Portugal FY25 7/12, Belgium FY25 10/12.
  Never sum a partial year and present it as full-year.
- **No dealer data at all:** UMI ("Internal only"), Cyprus (0/12), Germany (FY26 0/12).

## 8. Next steps

1. **Jerome decides:** rebase ITUK/UTI onto MH's basis, or ratify V4's? Blocks a single clean subtotal.
2. **Wave-2 roadmap dependency:** the mixed model had to exist by **Fri 24/07** for the July blitz — done.
3. **FY28–FY31** deferred by Jerome ("ask me in a later stage"). Rates and BP both reach FY31; the open
   question is which UIO series (detail = rising, summary = declining, 21.9% apart by 2030).
4. **Roadmap `Gantt` v2 is staged but unwritten** (file was locked): adds an `Invite sent` column with a
   dropdown, personalised topics per DB, a team-availability band, **2 Masumi reviews** (Thu 30/07 and
   Mon 24/08), and a meeting-load row. Script: `build_gantt2.py`.
5. **CAPACITY WARNING (from the load row):** W/c 10 Aug is 9 first meetings + up to 7 follow-ups in
   **three** working days — **Bart alone carries 7**. Suggest moving Sweden/Denmark/Romania (€1.85M,
   none time-critical) to W/c 24 Aug deliberately.

## 9. Build scripts

Scratchpad (session-temp — copy anywhere permanent if still needed):
`C:\Users\jerom\AppData\Local\Temp\claude\C--Program-Files-Git\972ec3d9-2eae-410e-b9fa-73bf8c2fa27d\scratchpad\`
`build_final.py` (model) · `patch_waterfall.py` (original-style waterfall) ·
`build_roadmap.py` + `build_gantt2.py` (roadmap) · `qa.py` (Excel COM QA)

**Order:** `build_final.py` -> `patch_waterfall.py` -> QA. Both rebuild from source; safe to re-run.

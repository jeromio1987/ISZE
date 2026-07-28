# Target Study + Attrition vs N75 PMS study (Mode B)

**Jerome-only.** Sources: Apr 24 Wrap-Up zip → `outlook_extracts/ITUK_Parts_Sales_Target_Study_20260409.xlsx` + `Attrition_Rate.xlsx`. Author of Target Study = **Masumi** (ISZE); Duncan reviewed.

**Deep mail analysis (verbatim + point-by-point):**  
`outlook_extracts/DEEP_ANALYSIS_WrapUp_Target_Attrition_N75.md` ·  
`outlook_extracts/Duncan_WrapUp_thread_verbatim_2026-04.md`

These are **complementary lenses**, not two versions of the same %. Do not quote Target Study “share %” as oil cover.

---

## One-line verdict

| Workbook | Answers | Does **not** answer |
|----------|---------|---------------------|
| **Target Study** | How much **total parts £** vs UIO potential · stretch ~£500k · share path | Category PMS cover (oil/air/brake) |
| **Attrition Rate** | Cohort scrap curve N35/N75 (SMMT vs sales) → feeds UIO projection | Capture / cover |
| **Our N75 study** | Oil/air/brake/fuel/clutch **cover %** on pilot parc **9,359** | Network £/UIO stretch target |

---

## UIO lineup (the only number that must reconcile)

| Source | Label | Value | Note |
|--------|-------|------:|------|
| **Our N75 pilot** | DVLA Method A, both gens | **9,359** | Meeting standard |
| Target Study · UIO Projection | N75 **2025** (cohort × survival + v17 override) | **9,506** | **+147 (~1.6%)** vs us — close enough to call “same N75 story” |
| Target Study · Sales Share F9 | Row labelled “N75” **2024** | **10,684** | **Duncan flag:** this cell is **not pure N75** — folds in other LD (N50/55, N62/65, UNSPEC, etc.). Do **not** use F9 as pilot UIO |
| Target Study · Section D check | “N75 Total UIO (2025)” | **7,142** | Older / partial block — ignore for meeting |
| Target Study · TTL 2024 | Full ITUK UIO | **22,389** | **Exact match** to our full DVLA total car park |
| Projection Total 2025 | All models | **~23,068** | Forecast after attrition override |

**Meeting line:** Pilot UIO stays **9,359**. If someone waves 10,684, that is the **Sales Share F9 bucket error** Duncan already called out — Projection’s **9,506** is the Target Study’s own clean N75.

---

## What Target Study actually models

**Sheet `Sales Share and Stretch`**

| Assumption | Value |
|------------|------:|
| £ parts / unit N35 | £400 |
| £ parts / unit N75 | £1,000 |
| £ parts / unit F (MD) | £1,200 |
| GP | 34% (FY2025 actual) |
| GBP/EUR | 1.12 (IML rate note) |

- **Potential** = UIO × £/unit (not FIG-KEY × km/interval).
- **2024 share** ≈ **77%** of potential (actual parts sales ÷ potential).
- **2026 stretch idea** ≈ **+£509k** (~+4% y-o-y) → share ~**80%**.
- Feedback pack already frames: stretch OK in principle; **Isuzu IX 76% growth** on the far column = too ambitious.

**Sheet `ITUK UIO Projection` (V15/V17)**

- Cohort × **ITUK-specific** N35/N75 survival (from attrition PPTX / this Attrition workbook).
- **v17 override:** pre-2008→2010 cohorts held at **90% survival** (10% attrition) as owner-operator rule.
- N50/55 & N62/65 use **N75 survival curve**; F-series uses IML CV Adv. Economy.

---

## What Attrition Rate.xlsx is

Single sheet: for vintage years **2010–2020**, N35 and N75:

1. Row A — units (sales / Niguri-side)
2. Row B — **SMMT** car park still observed
3. Diff = A − B
4. Rate = diff / A → **attrition** (share of that cohort no longer in SMMT parc)

Pattern (expected): old cohorts high attrition (N75 2010 ~**77%**); recent low (N75 2020 ~**4%**). N35 attrition runs **higher** than N75 at the same age.

This feeds the Target Study survival curves — it does **not** change our CY2025 oil cover math.

---

## Line up vs N75 PMS (same world, different question)

| Question | Target Study | Our N75 study |
|----------|--------------|---------------|
| Parc | Inflated F9 10,684 / clean proj. 9,506 | **9,359** |
| Demand model | Flat £/UIO | **50k km/yr ÷ 40k** oil/fuel (GIDSS MY24) + wear for brake/air |
| Output | Parts **£** potential · **share %** · stretch £ | Category **cover %** · **€ gap** |
| 2025 N75 oil | — | DB **~40%** / DLR **~46%** |
| Gap | Stretch ~£509k on **all** parts potential | N75 5-cat ~**€0.65M** (subset — don’t add to €2.04M) |
| Phase-one | Not scoped here | **Brake + air** first |

### How to talk about both without mixing

1. **UIO:** “Pilot = 9,359. Target Study’s own projection puts N75 at ~9,506 — aligned. The 10,684 on Sales Share is the mixed LD cell Duncan flagged.”
2. **Cover vs share:** “~40% oil cover ≠ 77% parts share. Cover = PMS category vs service demand; share = total parts £ vs £/UIO potential.”
3. **Stretch vs gap:** “£509k stretch is a **commercial target** on total parts. €0.65M is **unserved PMS demand** on five categories inside N75. Both can be true; they don’t sum.”
4. **Attrition:** “Used to grow/shrink the parc in Target Study. Our cover % already sits on a **fixed** 2024A/2025 DVLA cut — no need to reopen attrition tomorrow unless someone attacks UIO.”

---

## Files on disk

```
mp/JEROME_ONLY/outlook_extracts/
  ITUK_Parts_Sales_Target_Study_20260409.xlsx
  Attrition_Rate.xlsx
  DEEP_ANALYSIS_WrapUp_Target_Attrition_N75.md
  Duncan_WrapUp_thread_verbatim_2026-04.md
```

Canonical N75 numbers: Interval Model + `mp/SHARE/ISZE_ITUK_UTI_PMS_Study_CY2025_for_IML_CLEAR.xlsx` sheet `01`.

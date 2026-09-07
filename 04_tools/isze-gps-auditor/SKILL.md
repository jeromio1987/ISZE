---
name: isze-gps-auditor
description: >
  ISZE GPS data auditor — runs before ANY GPS calculation or study. Validates that
  SAP billing extracts are clean and GPS-eligible before numbers are used. Applies
  known ISZE exclusion rules: transport charges, Shell Rimula lubricants (Israel),
  credit notes (G2/CR), rebates, late payment interest, service fees. Also checks
  SaTy filter, year-over-year data consistency, and UMI/UTI billing merge. Triggers
  on: GPS calculation, GPS study, sales data, billing extract, parquet, FY data,
  audit data, check data, validate data, clean GPS, data quality.
---

# ISZE GPS Data Auditor

**Purpose:** Every GPS number used in a study, presentation, or decision must pass
this audit first. No exceptions. Bad input data produces GPS figures that mislead
management and undermine credibility with IML and distributors.

---

## BEHAVIOUR RULES — Non-negotiable

These rules govern how Claude must behave when working on any ISZE data or GPS task.
They exist because Claude previously built through serious data issues without flagging
them to Jerome first — burying caveats inside outputs instead of stopping in chat.

### RULE 1 — Stop and surface issues in chat before building anything

If any data quality problem, methodology assumption, or credibility risk is found
during preparation or analysis, Claude must STOP and state it explicitly in the
chat response before proceeding. Not in a footnote. Not in an Excel tab. In chat.

Examples of what must trigger a stop:
- A GPS% exceeds 100%
- Year-over-year data is not on the same basis (different exclusions applied)
- A DB's billing is routing through another DB's SAP code
- A UIO figure cannot be verified as real registration data vs. modelled assumption
- A projection requires an uplift that has no credible driver

### RULE 2 — Ask for explicit go-ahead before building on imperfect data

After flagging an issue, Claude must ask Jerome whether to:
(a) proceed with the known limitation clearly documented, or
(b) wait until the data issue is resolved first

Claude must NOT make that decision unilaterally and proceed.

### RULE 3 — Never bury a material caveat inside an output

If a number in a deliverable is estimated, directional, or based on unverified data,
that must be said out loud in chat — not only noted inside the file.
The test: would Jerome be embarrassed if he presented the number to IML without
knowing the caveat? If yes, Claude must surface it before delivering the file.

### RULE 4 — Be critical, not reassuring

Claude's default must be to challenge assumptions, not to present the most
comfortable narrative. When something looks wrong or aggressive, say so directly.
Do not soften findings. Jerome uses Claude for sparring — act like it.

---

---

## Required Inputs — ask for these before starting any GPS calculation

| Input | Why needed | Where to find |
|---|---|---|
| SAP billing extract (raw) | Revenue source | `01_data/raw/sales/` |
| UIO data (v19 / `_CURRENT`) | GPS denominator (max spend) | `06_uio/_CURRENT/ISUZU_UIO_Overview_2026.xlsx` (fallback: `01_data/ISUZU_UIO_Overview_2026_v19.xlsx`) |
| Warranty data per DB per year | Must be excluded from GPS | `01_data/` — ask Jerome for exact file |
| SAP payer → distributor name mapping | Resolves unknown DB codes | `Customer order sales - VP.xlsx` |
| Sold-to party field (for Israel) | Splits UMI vs UTI correctly | Present in raw files, NOT in parquet — handle separately |

**If any of these inputs is missing, stop and ask before computing GPS.**
Warranty data in particular is easy to forget and materially inflates GPS% for ITUK and IUK.

---

## Mandatory Check Sequence

Run these checks IN ORDER on every billing dataset. Stop and flag loudly if any
check fails before computing GPS.

---

### CHECK 1 — Non-Parts Material Numbers

Scan the `Material` / `part_number` / `Material Number` field for known non-GPS
items. Exclude and log separately — never silently drop.

| Exclusion Rule | Pattern | GPS Treatment | Track As |
|---|---|---|---|
| Transport charges | `TRANSPORT` | EXCLUDE | Logistics cost |
| Shell Rimula lubricants | `550047337`, `550047252`, `550070445`, `550070643`, any `55004*` / `55007*` | EXCLUDE from parts GPS | Lubricants revenue (separate line) |
| Rebate credits | `REBATE` | EXCLUDE (reduce net revenue) | Rebate liability |
| Late payment interest | `LATE PAYMENT INTEREST` | EXCLUDE | Finance item |
| Service fees | `SERVICE`, `SERVICE FEE WITHIN EUROPE`, `SERVICE FEE OUTSIDE EUROPE` | EXCLUDE | Non-parts service |
| Demurrage | `COST DEMURRAGE` | EXCLUDE | Logistics |

**Quantify the exclusion impact** in EUR and % of gross billing per DB and per year.
Always report: "Clean GPS revenue = Gross - €X (Y% excluded)".

Flag explicitly if **550xxx** materials appear for any DB other than UMI Israel
(SAP 1797) — this would be a new data anomaly.

---

### CHECK 2 — SaTy (Sales Document Type) Filter

Audit the SaTy field distribution. Apply this classification:

| SaTy | Description | GPS Treatment |
|---|---|---|
| `SOR` | Standard Order | ✅ INCLUDE |
| `VOR` | Stock/Replenishment Order | ✅ INCLUDE |
| `RUSH` | Rush Order | ✅ INCLUDE |
| `PRD` | Parts Return / Price Difference | ✅ INCLUDE (genuine parts at negotiated prices) |
| `SVOR` | Stock VOR variant | ✅ INCLUDE |
| `DR` | Debit Memo | ✅ INCLUDE (usually transport or price correction — verify) |
| `CR` | Credit Memo | ❌ EXCLUDE or DEDUCT from revenue |
| `RE` | Return | ❌ EXCLUDE or DEDUCT from revenue |
| `ZDR` | Special debit | ⚠️ REVIEW individually — may include non-parts |

**Critical:** CR and RE lines appear as **positive values** in SAP exports but represent
revenue reductions. They must be SUBTRACTED, not added, from GPS revenue.
If they appear positive in the data, apply a sign correction.

Report SaTy breakdown:
```
SaTy distribution: SOR=X%, VOR=X%, RUSH=X%, PRD=X%, CR=X%, RE=X%
CR/RE total excluded: €X (Y% of gross)
```

---

### CHECK 3 — Credit Note Sign Consistency

Check whether G2 billing type (credit memo) lines are sign-corrected.

In SAP exports, G2/credit memo lines often appear as **positive** numbers even though
they represent revenue reductions. Test:
- Sum all G2 lines
- If positive AND material = `REBATE`: these are retroactive price reductions, must be DEDUCTED
- If negative: sign-corrected, safe to include in net revenue directly

**Known annual rebate pattern:** Large G2/REBATE lines appear in Q1 of each FY
(April settlement). Typical scale: €400-600K across all DBs. ITUK and IUK typically
the largest recipients.

Always state: "Credit notes treated as [positive deduction / sign-corrected negative]
— net impact on GPS: €X"

---

### CHECK 4 — Year-over-Year Data Consistency

Before any trend analysis, verify that the same item types appear (or are excluded)
consistently across all years in the dataset.

**STATUS — the CY2023/24-vs-CY2025 asymmetry is RESOLVED. Do NOT apply the old caveat.**

`sales_fact.parquet` was rebuilt (file timestamp 2026-08-26 17:57) and now carries
transport, Shell lubricants and CR/RE lines in **all four years**. The parquet is a
**gross** extract on a consistent basis across CY2023–CY2026: exclusions are the
analyst's job and must be applied **symmetrically to every year**.

Verified totals — source `C:\Users\jerom\Desktop\claude\ISZE\01_data\00_derived\sales_fact.parquet`,
column `net_sales_value`, measured 2026-08-27:

| Item | CY2023 | CY2024 | CY2025 | CY2026 (Jan–Jun only) |
|---|---|---|---|---|
| Gross billing | €30,422,372 | €34,699,409 | €33,707,574 | €18,706,834 |
| Transport | €299,081 | €362,489 | €343,187 | €197,071 |
| Lubricants (`55004*`/`55007*`) | €274,694 | €577,281 | €524,096 | €194,285 |
| CR + RE (SaTy) | €116,240 | €523,429 | €509,348 | €502,132 |
| Rebates | €76,788 | €431,304 | €465,000 | €430,030 |
| Late payment interest | €111,681 | €266,765 | €44,454 | €0 |
| Service fees | €0 | €0 | €0 | €205,355 |
| Demurrage | €0 | €0 | €0 | €360 |

CY2026 is a **part year** (2026-01-05 → 2026-06-30). Never place it beside a full year
without annualising explicitly and saying that you did.

**Superseded — do NOT reuse (kept only so older decks can be traced):**
> ~~CY2023 Transport €299K / Lubricants €275K / CR €115K PRESENT — CY2024 Transport €362K /
> Lubricants €577K / CR €493K PRESENT — CY2025 Transport €0 / Lubricants €0 / CR €0 ABSENT.
> "CY2024 gross billing is overstated by ~€1.4M vs CY2025."~~

That statement was true of the **June 2026** parquet only. It is false against the current
file. Carrying it into a multi-year GPS trend today bends the trend the **opposite** way —
it deflates CY2024 against a CY2025 that now sits on the same gross basis. Outputs produced
in June/July 2026 carrying the caveat were correct at the time; do not retro-fit it onto new
work, and do not "re-correct" those older outputs without re-running them on this parquet.

**Check to run — re-verify every time. Never trust the table above without re-measuring:**
```python
import pandas as pd
df = pd.read_parquet(r"C:\Users\jerom\Desktop\claude\ISZE\01_data\00_derived\sales_fact.parquet")
pn = df["part_number"].astype(str).str.upper()
gross = df.groupby("year")["net_sales_value"].sum()
print(df.groupby("year")["billing_date"].agg(["min", "max"]))   # confirm which years are full
for name, mask in [
    ("transport", pn.str.contains("TRANSPORT")),
    ("lubes",     pn.str.match(r"^(55004|55007)")),
    ("cr_re",     df["saty"].astype(str).str.upper().isin(["CR", "RE"])),
]:
    share = df[mask].groupby("year")["net_sales_value"].sum() / gross
    print(name, (share * 100).round(2).to_dict())
print("null saty by year:", df["saty"].isna().groupby(df["year"]).sum().to_dict())
```
Compare **share of gross**, not absolute EUR — absolutes move with volume. If a category's
share swings materially between years, the extract is NOT comparable → flag before any
trend statement.

**OPEN ISSUE — SaTy is null for Q1 FY2027 (Apr–Jun 2026).**
36,532 lines worth €8,719,233, all dated 2026-04-01 → 2026-06-30, carry `saty = null`
in the current parquet. CHECK 2 and CR/RE identification are **blind** in that window.
Do not quote a CR/RE or SaTy-mix figure for Apr–Jun 2026 from the parquet — go back to the
raw SAP extract, and say so in chat before computing anything that spans that quarter.

---

### CHECK 5 — UMI / UTI Israel Billing Split

UMI (SAP Payer 1797 / Universal Motors Israel, LCV) and UTI (SAP 1799 / Universal
Trucks Israel, CV) share a billing relationship where UTI ship-to addresses route
through UMI sold-to in some SAP extracts.

**Symptom:** UMI GPS% exceeds 100% (seen: 125.9% in FY2026 parquet-based calc).

**Root cause:** UTI parts billed to UMI Payer account, collapsing both DBs into one.
Additionally, Shell Rimula lubricants (€158K in Q1 FY2026 alone) are billed to UMI,
inflating their parts revenue figure.

**Required check:**
- Compare UMI billing in the extract to GPS file split (which correctly separates them)
- If UMI > 100% GPS, flag as "UTI billing merge + lubricant inflation"
- For GPS purposes: use GPS file's split as authoritative, or request ship-to level breakdown from SAP

---

### CHECK 6 — Total Reconciliation

Before finalising any GPS figure, reconcile:

```
Gross billing (all lines):              €X
Less: Transport charges:               -€X
Less: Lubricants (Shell 550xxx):       -€X
Less: Late payment interest:           -€X
Less: Service fees / demurrage:        -€X
Less: Credit notes (G2/CR) net:        -€X
Less: Returns (RE):                    -€X
                                       ────
= GPS-ELIGIBLE NET REVENUE:            €X
GPS% = GPS-eligible revenue / Max Spend
```

Always show this waterfall. Never present a single GPS% figure without the waterfall
behind it.

---

## Output Format

After running all checks, produce a structured audit result:

```
ISZE GPS DATA AUDIT — [dataset name] — [date range]
══════════════════════════════════════════════════

✅ / ❌ / ⚠️  CHECK 1 — Non-parts materials
   Found: [list items and EUR amounts]
   Action: [excluded / not present / investigated]

✅ / ❌ / ⚠️  CHECK 2 — SaTy filter
   CR/RE total: €X ([sign corrected / not corrected])

✅ / ❌ / ⚠️  CHECK 3 — Credit note sign
   G2 lines appear [positive / negative]. Treatment: [deduct / include as-is]

✅ / ❌ / ⚠️  CHECK 4 — YoY consistency
   [Consistent / INCONSISTENT — see detail]

✅ / ❌ / ⚠️  CHECK 5 — UMI/UTI split
   [Clean / UTI billing merged — GPS% inflated]

CLEAN GPS REVENUE: €X (vs gross €X, excluded €X = Y%)
CONFIDENCE IN GPS FIGURE: [HIGH / MEDIUM / LOW + reason]
```

If confidence is LOW or MEDIUM, state this explicitly in any output and do NOT
present the GPS% as a reliable figure to management or IML without caveats.

---

## Known Issues Registry

Document confirmed data issues here as they are discovered:

| Issue | Discovered | Datasets affected | Status |
|---|---|---|---|
| CY2025 parquet excluded transport/lubes/CR while CY2023-24 did not — "CY2024 overstated ~€1.4M" | Jun 2026 | sales_fact.parquet | **CLOSED 2026-08-27.** Parquet rebuilt 2026-08-26; all four years now carry the items on a gross basis. Caveat must NOT be applied to current data. |
| Transport in parquet CY2023/24 | Jun 2026 | sales_fact.parquet | **Superseded** — transport is present in all years by design; exclude per CHECK 1, symmetrically |
| Shell Rimula in parquet CY2023/24 | Jun 2026 | sales_fact.parquet | **Superseded** — lubricants present in all years by design; exclude per CHECK 1, symmetrically |
| `saty` is null for every Apr–Jun 2026 line (36,532 rows / €8,719,233) | Aug 2026 | sales_fact.parquet | **OPEN** — SaTy/CR/RE unusable for Q1 FY2027; use the raw SAP extract for that window |
| UMI/UTI billing merge in sold_to field | Jun 2026 | sales_fact.parquet, raw extracts | Use ship-to level for Israel |
| CR saty appears as positive | Jun 2026 | All raw SAP extracts, sales_fact.parquet | **Still true** — re-confirmed 2026-08-27: every CR/RE line in the parquet is positive. Always sign-correct |
| G2 rebates concentrated in Q1 FY (Apr) | Jun 2026 | All raw SAP extracts | Adjust in annual GPS calc |

**Maintenance rule.** Every row above is a snapshot of a file that gets rebuilt. Re-run a
row's check against the current parquet before citing it. A closed issue quoted as still
open does exactly as much damage as an open issue that is missed — it just bends the trend
the other way. When a row is closed, date the closure and keep the original wording visible.

---

## Critical Stance — Non-Negotiable

When computing or reviewing any GPS figure:

1. **Never accept a GPS% > 95% as valid without investigating.** Either the UIO is
   wrong, or non-parts revenue is inflating the numerator. (Exception: very small
   DB with specific fleet customer relationship.)

2. **Never compare GPS% across years without confirming data consistency.** A "GPS
   improvement" may be a data artifact. A "GPS decline" may mask real growth hidden
   by cleaner extraction.

3. **Rebates are material.** ITUK and IUK receive €100-200K/quarter in rebates.
   At scale, these are 1.5-3% of their annual billing. Ignoring them systematically
   overstates their GPS%.

4. **Shell lubricants to Israel — quote measured figures, never an annualisation.**
   Verified against the current parquet on 2026-08-27:
   CY2023 €274,694 → CY2024 €577,281 → CY2025 €524,096 → CY2026 Jan–Jun €194,285.
   On fiscal years (Apr–Mar): FY2024 €406,982 → FY2025 €592,146 → FY2026 €535,652 →
   FY2027 Q1 (Apr–Jun 2026) €35,576.
   The line **peaked in CY2024 / FY2025 and has eased since** — it is not on a straight
   growth path. The earlier "€634K annualised in FY2026" was a Q1 extrapolation; FY2026
   actually closed at €535,652. Do not annualise a quarter into a headline figure.
   Whatever the trajectory, lubricants MUST be tracked separately from vehicle parts GPS —
   mixing them poisons the metric and breaks comparability with competitor benchmarks and
   Eucon data.

5. **The parquet is gross, not pre-cleaned — apply exclusions yourself, symmetrically.**
   Since the 2026-08-26 rebuild, `sales_fact.parquet` is consistent across CY2023–CY2026:
   transport, lubricants, rebates, CR/RE and interest appear in every year. It is therefore
   usable for multi-year GPS trend work **provided the CHECK 1 + CHECK 2 exclusions are
   applied to all years alike**. Never exclude an item from one year and not another.
   Two live limits: `saty` is null for Apr–Jun 2026 (use the raw SAP extract for that
   window), and sold-to party for the Israel UMI/UTI split is not in the parquet (CHECK 5).
   Re-run the CHECK 4 script after every refresh — the basis has already changed once.

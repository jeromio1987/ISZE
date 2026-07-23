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

**Known inconsistency (discovered June 2026):**
- CY2023 parquet: Transport €299K, Lubricants €275K, CR €115K — **PRESENT**
- CY2024 parquet: Transport €362K, Lubricants €577K, CR €493K — **PRESENT**
- CY2025 parquet: Transport €0, Lubricants €0, CR €0 — **ABSENT**

This means the `sales_fact.parquet` pipeline cleaned 2025 data but NOT 2023-2024.
CY2024 gross billing is overstated by ~**€1.4M** vs CY2025. Any GPS trend showing
"GPS% fell from 2024 to 2025" must be read with this in mind — the drop is partly
a data artifact, not real performance decline.

**Check to run:**
```python
for year in years_in_dataset:
    transport_pct = rows_with_TRANSPORT / total_rows
    lubricant_pct = rows_with_550xxx / total_rows
    cr_pct = rows_with_CR_saty / total_rows
    print(f"{year}: transport={transport_pct:.2%}, lubes={lubricant_pct:.2%}, CR={cr_pct:.2%}")
```
If these percentages vary significantly across years → data is NOT comparable → flag before any trend statement.

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
| Transport in parquet CY2023/24 | Jun 2026 | sales_fact.parquet | Parquet pipeline fix needed |
| Shell Rimula in parquet CY2023/24 | Jun 2026 | sales_fact.parquet | Parquet pipeline fix needed |
| CY2025 parquet excludes above items, CY2023/24 does not | Jun 2026 | sales_fact.parquet | Confirms inconsistency |
| UMI/UTI billing merge in sold_to field | Jun 2026 | sales_fact.parquet, raw extracts | Use ship-to level for Israel |
| CR saty appears as positive | Jun 2026 | All raw SAP extracts | Always sign-correct |
| G2 rebates concentrated in Q1 FY (Apr) | Jun 2026 | All raw SAP extracts | Adjust in annual GPS calc |

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

4. **Shell lubricants to Israel are growing** (€275K in CY2023 → €577K in CY2024 →
   €634K annualised in FY2026). If the lubricants project proceeds, this line will
   scale significantly and MUST be tracked separately from vehicle parts GPS — mixing
   them poisons the GPS metric and cannot be compared to competitor benchmarks or
   Eucon data.

5. **The parquet pipeline needs fixing.** Until it consistently applies exclusions
   across all years, use raw SAP extracts (cleaned manually) as the source of truth
   for any multi-year GPS trend analysis. Do not present trend charts from the parquet
   without this caveat.

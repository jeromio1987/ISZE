# DATA_INTEGRITY — UMI one-distributor operating dashboard

**TARGET_DB** UMI · sold_to **1797** · payer 1797 · LCV · Israel
**AS_OF** 2026-08-14 · **audience** ISZE internal
**Anchor** `_verification_report.json` green (106 pass / 0 warn / 0 fail, as_of **2026-08-03**)

Ten pings, numbered, worst first. **1–4 are blockers** — the dashboard can be built without
answers, but four things stay hidden or hedged until you answer, and I have marked exactly which.
5–10 are things I have already handled; they are here so you can overrule me.

---

## BLOCKERS

### 1. `mix_genuine_bvp_by_group.csv` will make UMI look 22× more BVP-heavy than it is

Section B of the prompt says "Genuine vs BVP inside captured demand" and points at that file.
For UMI it reports **BVP = 81.6%** of its basket. That basket is **5.0% of UMI's euros**
(€165,196 of €3,301,443 CY2025). On the whole book UMI is:

| Basis | Genuine | BVP | Covers |
|---|---|---|---|
| Whole parts book | **96.3%** | **3.7%** | 100% (€3,301,443) |
| `mix_genuine_bvp_by_group.csv` | 18.4% | 81.6% | **5.0%** |

The whole-book figure is not my invention — the definition **reproduces
`metrics_snapshot.json` to the decimal** (UTI 88.9%, ITUK 97.3%) and is independently
corroborated by `wallet_waterfall.csv` `bvp_share_of_captured_pct = 3.7`. Three files agree.

**What I did:** the ledger carries both, with `THIS_IS_THE_ONE_TO_SHOW` on the whole book and a
`DANGER` note on the other. The by-group breakdown is retained but must render with
"within the crossref-paired basket only — 5.0% of euros" on the chart itself.

**Question:** confirm the hero/spine uses the whole-book 96.3 / 3.7 split. If you have ever
quoted "UMI is heavily BVP" from that file, it needs retracting.

**Commercial consequence, and it is the real finding:** BVP is not eating UMI's genuine —
BVP euros are *falling* (€149,530 CY2024 → €123,678 CY2025). So the €1,316,156 addressable
uncaptured wallet is **not** a value-tier switch. That euro is not in the tent at all.

---

### 2. RESOLVED — UIO V19 is actual, D-Max rate is €262.50, GPS% is released

**Jerome, 2026-08-14:** "UIO V19 IS actual" and "262.50 this is the current".

- The derived files stamping `uio_source = v18_actual` are **stale**, not authoritative.
  V3.1 is built on V19 (`06_uio\_CURRENT\ISUZU_UIO_Overview_2026.xlsx`, V19 internally —
  never read an archived `vN` copy). GPS% is therefore signed and on screen.
- **Rate: €262.50 (FY2027) / €250.00 (base).** 262.50 ÷ 1.05 = 250.00 exactly, which is
  `gps_model_targets.csv` `LCV_D_Max`. So 250.00 is the base and 262.50 is the FY2027 +5%
  figure; today sits inside FY2027. This reconciles both sources rather than choosing one.
- **Independent confirmation:** UMI FY2026 max spend re-rated at the 250 base =
  **€4,635,500**, which is *exactly* `wallet_waterfall.csv`'s separately-built UMI CY2025
  ceiling (18,542 × 250). Two independently produced files agree to the euro.
- **V3.1's MH LCV chain (219.5648 / 230.5430) is superseded.** It applied FX 1.16 and the
  0.65 margin twice — V3.1's own Method tab records that conflict at A19–A21 as "carried,
  not fixed", 24.6% apart. The current rate resolves it.

**Impact on UMI FY2026:**

| | V3.1 as published | At current €262.50 |
|---|---|---|
| Max spend | €4,071,171 | **€4,635,500** |
| GPS % | 60.06% | **52.75%** |
| GPS % ex-warranty | 19.95% | **17.52%** |

Every DB drops between 2.9pp (Portugal) and 12.9pp (Finland). Ireland still reads 116.79% —
`SHOW_GPS_PCT` stays false there, and for Finland and Iceland.

The rate is one constant in `04_tools\db_operating_dashboard\build_ledger.py`
(`LCV_RATE_CURRENT_FY27`), overridable with `--lcv-rate`. CV rates are untouched — the D-Max
rate applies to the LCV segment only, so mixed DBs are re-rated per segment and their
LD/MD/F-Series rates hold at v9 +5%.

---

### 3. `pms_summary_by_db.csv` contains **only** the broken partial year

Prompt §A hero 3 pulls PMS capture from that file. It has **one year: 2026**. CY2026 is
**Jan–Mar actual measured against a full-year `expected_qty`** — `sales_fact.parquet` ends
2026-03-31. It reports UMI capture **1.70%** and genuine **0.35%**. Both are artefacts.

Correct complete-CY figures, from `pms_capture_by_db_year.csv` year 2025, `line_type == 'total'`:

| | UMI | Network (18 DB, same model) | Gap |
|---|---|---|---|
| Total capture | **21.34%** | 28.37% | −7.0pp |
| Genuine capture | **7.13%** | — | — |
| Quotable revenue gap | **€1,760,114** (11 of 14 categories) | — | — |

**What I did:** hero uses CY2025. `do_not_use` block names the file and the reason. The
blueprint agrees — "PMS year = `latest_complete_pms_year()` (full CY only)" and "never YTD vs
full-year expected". No question needed unless you disagree.

**Also confirmed:** `uio_units` is **frozen identical across 2023/2024/2025/2026 for every one of
the 18 DBs**. There is no PMS trend in that file. The dashboard charts capture by *category*
against the network, never over time.

---

### 4. FY2024 ex-warranty for UMI is **−€60,442** — an impossible KPI

`gps_pure_sales_2026-08-13_v2.csv`, UMI FY2024: pure sales €2,842,371, warranty €2,902,813,
`pure_sales_ex_warranty_eur` = **−€60,442**. UMI and MIDI are the only two negatives in the file.

Two independent causes, both real:

1. **Basis mismatch.** `warranty_eur` is **claim price**; `pure_sales_eur` is **ISZE net**
   (claim × ~0.74 per `db_profiles.yaml`). Subtracting one from the other is not a clean euro
   *anywhere* in this file — UMI is just where it goes visibly negative.
2. **A genuine 2023 warranty event.** `warranty_raw_grain.csv` V17130 shows CY2023 claims of
   **€3,223,498**, far above every other year. FY2024 (Apr 2023–Mar 2024) catches that spike.

The blueprint says for UMI "warranty fiscal is large vs net — **always** show GPS excl. warranty".
That instruction and this bug collide.

**What I did:** `flags.SHOW_FY2024_EX_WARRANTY = false`; FY2024 carries
`ex_warranty_renderable: false`. FY2025 (€1,235,074) and FY2026 (€812,249) render normally.
FY2023 has no warranty figure at all (`warranty_missing`).

**Question:** show FY2024 ex-warranty as an explicit "not a valid euro" marker, or omit the bar
entirely? I defaulted to the marker — silence looks like missing data.

---

## HANDLED — overrule me if you disagree

### 5. The ex-warranty PN exclusion would delete 27 of the top 30 PNs

**27 of UMI's top 30 PNs by euro also appear on UMI warranty claim lines** (1,210 distinct claim
PNs in `warranty_raw_grain.csv` V17130). The blueprint's binary rule — drop every PN that appears
on a claim line — would destroy the working set, and the blueprint admits the limitation
("drops all billing of that PN, including any genuine commercial demand").

This is structural for UMI, not a data error: UMI's euro top-line **is** warranty-adjacent
hardware. #2 is DPD ASM (€213,056), #3 and #7 are PM sensors (€136,265 + €46,111) — the known
PM-sensor campaign item — #6 is ENGINE ASM (5 units, €71,645).

**What I did:** did **not** apply the binary exclusion. §D/§E show the commercial and blended
lenses side by side with the limitation labelled. Flagging rather than filtering.

### 6. Section E: verified, but the data does not say "did not participate"

Your live example checks out. All **29** Israel LCV dealers score exactly **0** on Section E.
Country 0.00% vs network **73.21%** (564 dealers, pack v1.4, built 2026-08-12).

Two corrections:

- **Unit.** Section E is **18 questions** but **27 points**. "0/18" is the question count;
  any scoreboard must read **0/27**.
- **No participation flag exists.** No dealer carries `totals_only` or `excluded_from_average`.
  The file says 0; it does not say "not scored". So I labelled it
  **"not scored / participation to confirm"** rather than asserting non-participation — a flat
  grey 0% bar reads as "they are bad at selling vehicles", which the file does not support.

**Question:** can you confirm Israel LCV genuinely did not participate in Section E? That
converts a hedge into a headline.

**The parts finding is stronger than Section E anyway:** Section **D (Parts & Accessories)
61.63% vs network 78.71% = −17.1pp**, against Section C (Service) −7.3pp. Parts is the worse
gap. That is the one that belongs to you.

### 7. `PRD` is 7.5% of UMI's euros and is not in the 80/20 taxonomy

SaTy codes present for UMI: `SOR`, `VOR`, `CR`, `PRD`, `FD`. The prompt's taxonomy is
SOR / VOR / RUSH / SVOR. **`PRD` carries 7.5% of CY2025 euros** (€246,968) and is rising
(4.1% → 6.8% → 7.5%). I did not fold it into stock or rush — it renders as its own band.

**Question:** what is PRD, and does it count as stock or rush for the 80/20 guideline?

### 8. No fill-rate series for UMI

Nothing found. `01_data\11_planning\KPI Master File june 2026.xlsx` exists but I did not open it
and cannot confirm it carries a UMI series. The only digitised fill-rate work in the workspace is
IBX. §C renders an empty state.

### 9. CORRECTED — the IAM lane does have data, and one derived file is poison

My first pass said this lane had no data. That was wrong — I had only looked at the Eucon raw
files. Actual state:

- **`eucon_price_gap.csv` is usable:** 44 PNs with real ISZE-vs-competitor prices. **25 of them
  appear in UMI's CY2025 book, covering 9.2% of UMI's euros; 6 are in the top 30.**
- **Revenue-weighted, UMI is +38.0% — i.e. ISZE is *cheaper* than the aftermarket average** on
  its covered revenue. Only €81,984 of UMI revenue sits on PNs where ISZE is above market.
  Sign convention: positive = ISZE cheaper = good. Inverting it inverts the section.
- **Live scrapers:** 5 sources refreshed 2026-08-03, weekly task, 300/300 PNs, 0 errors —
  including **Auto 365 (Israel)**. Hit rates are low though: autodoc 143/300, KS 64/300,
  mekonomen 7/200.

**BLACKLISTED: `01_data\00_derived\competitiveness_autodoc_risk.csv`.** All 298 rows carry
`autodoc_min_eur ≤ 2.34`, median exactly 2.34 — the £2.00 "no results" placeholder converted to
EUR and propagated as though it were a competitor price. It implies ISZE engine assemblies
(€4,835) face €2.34 competition. Never read it.

**Also caught and fixed:** `gp_at_risk_eur` in `eucon_price_gap.csv` is **network-level per PN**.
Summing matched rows gives every DB the whole network's €2.2M — Germany came out at exactly the
network total. Replaced with a DB-scoped revenue-at-stake figure.

**Open gap (updated 2026-08-14):** Auto 365 still has **no OEM part number** (see
`04_tools/autodoc_scraper/AUTO365_PN_JOIN.md`). Family-level local catalogue only —
**do not write `iam_israel_price_gap.csv`**. PN-level coverage for UMI 1797 now also comes from:

| Probe | UMI matches | Share of CY2025 euros | Notes |
|---|---|---|---|
| Eucon DE/NO | 25 PNs | 9.2% | Existing probe. Network `gp_at_risk` is **not** attributed. |
| KS International UK (ex-VAT) | 7 PNs | 0.73% | `iam_ks_price_gap.csv`. URLs on the SPA/IAM table. |
| Mekonomen SE | 4 PNs | 1.06% | `iam_mekonomen_price_gap.csv`. URLs on the SPA/IAM table. |

Do **not** add the three coverage percentages. Positive delta = ISZE cheaper. SPA list is the
exposed lines (delta < 0) with no Best Value in the crossref. Customer HTML must not contain
the word “street”.

Limitations that stand: competitor sourcing is DE + NO, it is 44 PNs (a probe, not a catalogue
position), and the underlying Eucon survey is 2023 UK/ITUK. The lane is still never summed with
the other two.

### 10. Three of four hero sources sit **outside** the green verification report

The anchor is green — but it was generated **2026-08-03**, and it checks 106 items covering
`gps_spu_by_distributor.csv`, `pms_capture_by_db_year.csv`, `pms_summary_by_db.csv`,
`genuine_bvp_crossref.csv`, `sales_fact.parquet` and 28 others. It does **not** reference:

| Hero source | In green report? |
|---|---|
| `gps_pure_sales_2026-08-13_v2.csv` (heroes 1 + 2) | ❌ — extract is 10 days newer than the report |
| `wallet_waterfall.csv` (hero 4) | ❌ |
| `pms_capture_by_db_year.csv` (hero 3) | ✅ |
| `distributor_dimension.csv`, `warranty_raw_grain.csv`, `q1fy2027_export_with_saty.csv` | ❌ |

So the canonical GPS numerator the prompt names has never been through the verifier.

**What I did:** every ledger source carries `in_green_verification_report: true|false`, and I ran
my own reconciliations instead. **Four independent checks pass:**

| Check | Result |
|---|---|
| `sales_fact` FY2026 vs `distributor_dimension` `fy2026_net_sales_eur` | €3,079,678.34 vs €3,079,678 — **match** |
| Q1 FY2027 extract sold_to 1797 vs locked Power BI Apr+May+Jun | €643,950 vs €644,000 — **match, Δ€50** |
| Whole-book BVP share vs `wallet_waterfall.bvp_share_of_captured_pct` | 3.7% vs 3.7% — **match** |
| Anchor definition reproduced (`metrics_snapshot` UTI / ITUK) | 88.9 / 97.3 both ways — **match** |

**Suggestion:** re-run the verifier so the 2026-08-13 GPS extract is inside the green set.

---

## Corrections to existing workspace files

Two claims in circulation are wrong. Both are worth fixing at source.

### A. The "IUK extract is only 35% of Power BI" claim is a mis-diagnosis

`db_profiles.yaml` IUK `watch` says *"The Apr-Jun 2026 SAP extract holds only EUR 586,024 for IUK
against Power BI's EUR 1,663K (~35%). Never cut PN detail on that window for this DB."*
Prompt §I repeats it.

In `q1fy2027_export_with_saty.csv`:

| Measure | Value |
|---|---|
| sold_to 2574 total | **€1,662,974** |
| Power BI Q1 FY2027 (929+357+377) | **€1,663,000** |
| SaTy-**coded** euros, excl CR | **€585,113** (35.1%) |
| The watch note's figure | €586,024 (Δ €911) |

The extract is **complete** — it matches Power BI to €26. What is 35% is the **SaTy coding
coverage**. Two different 35%s got conflated: an older raw `Q1FY2027.XLSX` really was short
(the blueprint records that), but the derived CSV in use today is not.

**Consequence: PN-mover analysis for IUK is unblocked.** Someone has been declining to cut IUK PN
detail on a window that is actually complete.

*Not fixed by me — `db_profiles.yaml` is outside this build's scope. Flagging only.*

### B. Credit notes are unsigned in `sales_fact.parquet`

Confirmed: UMI `SaTy == 'CR'` sums to **+€350,837** across 26 rows — stored **positive**. The
blueprint warns this is network-wide and that only `q1fy2027_billing_tagged.csv` signs them.
Any naive total from `sales_fact.parquet` overstates by twice the credit value.

Every aggregate in the ledger **excludes** CR rather than subtracting it, and says so.

One loose end: the blueprint lists UMI Q1 2026 credits at **€113K**; `sales_fact` CY2026 Jan–Mar
CR is **€79,176**. Different windows or definitions — worth reconciling before any Q1 CY2026
number is published, though nothing in this dashboard depends on it.

---

## What I did not find

**Open issues are now on the dashboard** (live Outlook 14 Aug 2026, full Bart × UMI pull). Split:

| Lane | n | What |
|---|---|---|
| Mail (Shelly / Netanel / planning) | 9 | 12 Aug call: send the deck; Shell table to review (no ISZE cut on this screen); Aftersales Awards survey; July StD + news; SPA PN list; Shell €2.2/L; oil-business conference follow-up; action-plan UMI scrap €80K; support €20K + Credit Control signed-MOU ask on CN 202647076. |
| Bart follow-ups | 8 | 12 Aug notes Bart sent Jerome: 5L Shell packaging, genuine-share incentive, Dealer Standards Section E, SPA proposal, Electric Company tender, StD part-level from Jan 2025; training 26 Aug + EQ-Hit; older 27 Oct 2025 minutes still on file. |
| Minutes file | 2 | Inbox attachments (not the empty `archive/customers/UMI/UTI/meeting minutes` folder): 12 Aug 2026 UMI notes and 27 Oct 2025 ISZE–UMI minutes. Did not copy Portugal/Ireland/ISD. |

Sources: local Outlook COM (Bart Symons × UMI 1797), `01_data/90_INBOX/_umi_bart_outlook_full.json`, `01_data/11_planning/Action plan FY2027 VPACC_July update.xlsx`.

| Prompt asks for | Status |
|---|---|
| §G latest meeting minutes | **Found in Inbox**, not in the empty named folder. 12 Aug 2026 notes (Bart → Jerome) and 27 Oct 2025 minutes (Hadi, Bart on copy). |
| §J sales-to-dealer | **UMI sends nothing as a file series.** `_registry.yaml` covers IRELAND, ITUK, IUK, UTI, GREECE. June StD €190,016 was given in Shelly’s 30 Jun mail, not a monthly extract. UTI (1799) PartSales is not this book. |
| §F open email issues | **On the Open issues tab** — 9 mail/planning lines from Shelly/Netanel plus the two UMI action-plan rows. |
| §C weekly order cadence | **Found, with a caveat.** 91 distinct billing dates across 51 ISO weeks in CY2025 — daily grain is real. But it is the **ISZE invoice date**, not UMI's order date. Zero Sunday billing despite Israel's Sun–Thu business week proves it is the European invoicing calendar. Titled accordingly. |
| §C fill rate | Not found — ping 8. |
| §E IAM / Eucon prices | Not found for Israel — ping 9. |
| §H Section E participation | Score verified, participation flag absent — ping 6. |

---

## Two things that are good news and should be rendered as such

1. **UMI is already past the 80/20 guideline and has been improving for three years.**
   Rush class as a share of order euros: **20.0% (2023) → 12.9% (2024) → 10.7% (2025)**, and
   3.5% in Apr–Jun 2026. SaTy is coded on ~100% of euros Jan 2023–Mar 2026, so this is a solid
   series, not a sample. **The terracotta "same-day warehouse" remark must not fire for UMI.**
   The Apr–Jun 2026 window renders **amber** only because coded coverage there is 65.9% (<70%) —
   the mix is excellent, the coverage is too thin to sign.

2. **UMI is the network's best oil-filter capture: 85.16% vs network 60.49% (+24.7pp).**
   Set against the rest of the CY2025 basket, that is the whole operating agenda:

| Category | UMI | Network | Gap | Revenue gap | Avg SP |
|---|---|---|---|---|---|
| Oil filter | **85.16%** | 60.49% | **+24.7pp** | €11,141 | €4.05 |
| Brake shoe | 13.78% | 9.47% | +4.3pp | €224,773 | €28.12 |
| Fuel filter | 26.44% | 46.55% | −20.1pp | €96,457 | €7.07 |
| Brake pad | 8.74% | 29.51% | −20.8pp | **€332,399** | €49.11 |
| Air filter | 22.95% | 52.23% | −29.3pp | €81,695 | €11.44 |
| Brake rotor | 11.97% | 54.46% | **−42.5pp** | €216,996 | €53.18 |
| Blower filter | 0.70% | 16.25% | −15.6pp | €246,608 | €13.39 |

**UMI captures the cheap consumables and loses the high-value wear items.** Oil filters at
€4.05 are 85% captured; brake rotors at €53.18 are 12% captured. Urea filter, pilot bearing and
clutch booster are all 0.00% and all carry `revenue_gap_quotable = False` — 3 of 14 categories
are not quotable and are excluded from the €1,760,114.

# Decision memo — FY2027 price adjustment ambition — 2026-09-16

> **Rules.** One page. Every euro figure carries the source path it came from. A memo without a
> signature line and a date is not a memo.

## The question

Which ambition applies to the FY2027 price adjustment: **+4% weighted on forecasted demand**, **+5% on the same basis**, or **an open increase on the new-launch part families only** (P700 and D-Max 2.2L launch numbers) while the rest of the book stays at the locked **+3%**?

## Options

| # | Option | Annual euro consequence | What it unlocks | Evidence |
|---|--------|-------------------------|-----------------|----------|
| A | **+4%** on forecasted demand — forecast weights replace past-sales weights | **+€581k/yr** on the forecast weights · **+€510k/yr** on past 12 months (L12M). That is **€145k/yr more** than the locked +3%. | A number the allocation run can solve to, so the revision queue becomes a price move instead of a review list. Smallest step that changes the basis. | `01_data/00_derived/forecast_weight_sensitivity_provisional_20260812.csv` (`sum_l12m_eur` €12,761,293 · `sum_forecast_weight_eur` €14,517,268) · `00_docs/REVIEW_EXEC_AFTERSALES_PAPER_20260915.md` §4.5 (prints €581k / €510k) |
| B | **+5%** on the same forecast-weighted basis | **+€726k/yr** on the forecast weights · **+€638k/yr** on L12M. **€290k/yr more** than the locked +3%. | Same as A, with the largest published euro. It also places more of the rise on lines where independent-brand prices already sit below our reference dealer price. | same two sources (review §4.5 prints €726k / €638k) |
| C | **Open on new-launch families only** — no fixed network ambition; the legacy book stays at +3% | **Not in the files.** 1,167 P700 new-only part numbers carry no L12M revenue and their seed values are `NEED_SEED`, so no euro figure exists today. The legacy book keeps **+€383k/yr on L12M · +€436k/yr** on forecast weights. | Prices the new numbers where there is no previous price and no weight in the +3% index, so the constraint does not bind on them. | `01_data/00_derived/forecast_weight_scaffold_20260812.meta.json` (`need_seed` 2,219 · bucket counts 826 + 341) · `01_data/01_Pricing/PLAN_FORECAST_WEIGHTED_AMBITION.md` |

Locked baseline for comparison: **+3% = €383k/yr on L12M · €436k/yr on the forecast weights** (`forecast_weight_sensitivity_provisional_20260812.csv`; review §4.5 prints the same). Both bases cover the same **6,326 part numbers**; the forecast weights are **1.1376×** the past-sales base, i.e. €14.52M against €12.76M.

## Recommendation

**Option A, +4% on forecasted demand.** It is the smallest step that puts the increase on where demand is going instead of on last year's sales, adds about €145k a year over the locked +3%, and leaves room to step to +5% in a later cycle without reopening the basis — but sign nothing until sub-question 1 is settled, because it moves the whole euro.

## What this unblocks / what stays blocked

**Unblocks:** the allocation run on the 6,326 weighted part numbers (both builds carry `no_alloc_run: true` today); the guardrail overlay can move from review to action — 4,287 PN × distributor rows held for leakage review, 1,542 for overstock and 1,193 for high list exposure across ITUK, UTI, IRELAND and IUK (`01_data/00_derived/revision_book_b_action_summary.csv`); the FY2027 GPS target gets a defined price line instead of a placeholder; and the same engine can be used off-cycle on new model launches, where a new part number has no previous price and no weight in the index, so there is nothing for a distributor to push back against (spec §9, §10).

**Stays blocked until signed:** no allocation run, no price list change and no distributor-facing number (roadmap §2 B1 and B8; spec §10 cadence); 9,591 seeded part numbers with no L12M revenue stay out of every euro ranking until seed values land — 2,219 of them P700-related and carrying `NEED_SEED` (roadmap §2 B2); the GPS bridge cannot separate the price effect from the volume effect, so FY2027 spend per truck cannot be told apart from the increase (spec §10); leakage euro stays internal (roadmap §5; `DECISIONS.md` 2026-08-25).

## Open sub-questions (must be answered before signing)

**1. Is the FY2027 target measured before or after the distributor support payment? This is the blocker.**

- **Reading 1 — before support (headline basis).** The target is measured on the net price to the distributor as invoiced, and the support payment sits on top. +4% = **€581k/yr** on forecast weights (€510k on L12M); +5% = **€726k/yr** (€638k). The full amount lands.
- **Reading 2 — after support (net basis).** The target is measured on what remains once support is paid. At the 20% figure the spec uses, €1.00 of headline increase lands as **€0.80**. So +4% headline nets **+3.2% — €465k/yr on forecast weights, €408k on L12M**; +5% headline nets **+4.0% — €581k/yr, €510k**. To *net* +4% the headline must be **+5.0%**; to net +5% it must be **+6.25%, i.e. €908k/yr on forecast weights and €798k on L12M**.
- **What the files assume.** The spec's own illustration assumes the *after-support* reading: it prints 3% netting about 2.4%, which is 3% × 0.80 (spec §13 Q2). The euro tables above are built on `sales_fact`, which is net-to-DB only — roadmap §5 records that gross, discount and condition columns are not available, so whether the support payment sits inside the €12.76M base cannot be determined from the files.
- **The 20% is not a signed FY2027 term.** It appears in the spec (§12 row 4, §13 Q2) and in a FY2025 message to UTI ("80% target and 20% KPI", `02_dashboards/Data/90_INBOX/outlook_scan_masumi_hadi_2026/hits.json`). The signed scheme terms — percentage, base, and whether support scales with purchases — are **not in the files** and must come from IML. The FY2027 GPS rework with the annual price increase was requested by Masumi-san, and the FY2028–FY2031 +3% a year is IML policy per her email, so the scheme terms are hers to confirm (`01_data/02_GPS/HANDOVER_GPS_Extended_Target_FY27.md` §1 and §3.4).

**2. Sign the growth factors.** The forecast weights rest on unsigned midpoints: 1.24 for service-interval families, 1.25 for first-failure wear families, 1.05 for P700 carryover, and ×1.25 network scale on the UTI recommended list (roadmap §2 B3). The whole €1.76M difference between the €12.76M and €14.52M bases rests on these four numbers.

**3. Decide the per-line cap.** The spec sets +8 percentage points on any priceable line, +5pp for a part number in a distributor's top-50 basket, and a −12pp floor (spec §7). Decide whether +8pp is survivable or lower — this is a decision, not a discussion (spec §13 Q3).

**4. Seed values for the P700 new-only numbers.** 826 P700 new-only part numbers have no past revenue (§2 B2). Without seed values, option C cannot be priced at all and those numbers stay out of every euro ranking.

## Decision

Option chosen: ________________________________________________________________

Signature: ________________________  Date: __________

---

**Sources (all paths under `C:\Users\jerom\Desktop\claude\ISZE\`):** `01_data/00_derived/forecast_weight_sensitivity_provisional_20260812.csv` · `01_data/00_derived/forecast_weight_scaffold_20260812.meta.json` · `01_data/00_derived/book_b_bucket_summary.csv` · `01_data/00_derived/revision_book_b_action_summary.csv` · `01_data/01_Pricing/PLAN_FORECAST_WEIGHTED_AMBITION.md` · `01_data/01_Pricing/BOOK_B_CONCLUSIONS_20260819.md` · `01_data/01_Pricing/DB_DLR_COMMERCIAL_STACK.md` · `01_data/02_GPS/HANDOVER_GPS_Extended_Target_FY27.md` · `00_docs/REVIEW_EXEC_AFTERSALES_PAPER_20260915.md` §4.5 · `00_docs/ISZE_Pricing_Spec_v1.md` §1, §7, §9, §10, §12, §13 · `00_docs/ISZE_ROADMAP.md` §1, §2 (B1, B2, B3, B8), §5 · `FACTS.md` §4 · `DECISIONS.md` 2026-08-25.

**Figure notes — where the sources disagree** (appendix detail, not part of the one-page body). (1) Launch-related share of the forecast weight: about **60%** in the 2026-08-19 conclusions file (every tagged bucket except the flat 1.0 bucket) against **77.8%** in the sensitivity CSV (`share_fw_launch_tagged`, which also counts UTI-recommended rows that sit inside the flat bucket). Both are correct on their own definition; do not quote them interchangeably. (2) Part numbers without L12M revenue: **9,591** in the conclusions file (all 15,917 seeds less the 6,326 with revenue) against **2,219** `NEED_SEED` in the plan file (P700-related only). Different scope, not a contradiction. (3) Base quality: the €12.76M is billed for **5,604** part numbers and a simulated proxy (quantity × 2025 planned price) for **722** (`forecast_weight_scaffold_20260812.meta.json`).

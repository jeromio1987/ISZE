# PRISM Data Integrity — Flag List
### Verify before quoting any of these numbers externally

**Date:** 2026-05-28
**Scope:** `sales_fact.parquet` (434,858 rows, €97,429,989 total) + all `01_data/derived/*.csv`
**Status:** flags raised by automated scan + code review. Each needs a human verify/decision before the data is presented.

Severity: 🔴 high (corrupts headline numbers) · 🟠 medium (misleads if unguarded) · 🟡 low (confirm & move on)

---

## Resolution status — updated 2026-05-28 (post-fix, verify 86/0)

| Flag | Status | Note |
|---|---|---|
| A non-part lines | ✅ **fixed** | `line_kind` tag added at load (`sales_loader.py`); freight/rebate/finance/adjustment excluded from GPS revenue + Top Parts. **Found a 3rd: LATE PAYMENT INTEREST €378K.** GPS-facing impact €1.14M (1.19%) → parts base €94.55M. |
| B "Rim"=oil SKU | ✅ **fixed** | Description override for `550047337` → "Engine Oil 15W40 CK4". Wider lubricant-SKU audit still advisable. |
| C interval-aware capture | ⚠️ **mitigated 2026-07-02** | Interval-aware air:oil implemented: `air_filter` consumable_factor 1.0 → **0.5 (PROVISIONAL — air element ~every 2nd service)** in `pms_capture_assumptions.yaml`; air capture now directionally comparable across categories. **IML-confirmed ratio still open** — one IML number replaces the assumption (see `pms_service_intervals.md` §6). |
| D 2025 fleet proxy | ✅ **resolved** (confirmed 2026-07-03) | 2025 UIO refreshed to V19 (DVLA-based) on 2026-06-18 — `uio_proxy_used=False` on all 2025 capture rows, no longer a 2024 proxy. Banner remains as a display-layer guard for any future gap. |
| E FY-incomplete | ✅ **fixed, and data gap closed 2026-07-03** | GPS banners partial fiscal years; `sales_2026tillApril.XLSX` now lands in `sales_fact` so FY2025 (Apr 2025-Mar 2026) is a complete 12 months for the first time. |
| F BRK classification | ✅ **fixed** | `BRK/ROTOR/CALIPER/SHOE` patterns added; column relabelled "keyword — not AIM". |
| G YoY blow-ups | ✅ **fixed** | YoY% suppressed where prior-year base <10 units (`build_bvp_p2_mix.py`). |
| H credit notes / returns | ⚠️ **acted on 2026-07-03, not ERP-confirmed** | Zero negative-value rows, but SaTy CR/RE codes exist on positive-value lines (280 rows, €1.65M network-wide). Now excluded from GPS/parts-base/PMS-capture as a documented, reversible judgment call — ERP confirmation not expected soon. See `DECISIONS.md` 2026-07-03. |
| I minor outliers | ⏳ **verify** | Spot-check only. |

**Note on the €97.4M figure:** that is the *raw* `sales_fact.parquet` total (includes internal/excluded codes e.g. Germany service dept). The GPS-facing base after distributor exclusion is €95.69M all-lines / **€94.55M parts-only**.

---

## 🔴 A. Non-part lines inflating revenue
- **TRANSPORT = €661,570** (2,423 lines) and **REBATE = €508,092** (21 lines) sit inside `sales_fact` as if they were parts. Combined **€1.17M (1.2% of all revenue)**.
- They appear in "Top Parts by Revenue" (GPS page) and inflate any €-based ranking or capture denominator.
- **Action:** exclude or bucket separately (a `line_kind` flag: part / freight / rebate / adjustment).

## 🔴 B. Mislabelled SKU — "Rim" that is engine oil
- **`550047337` "Rim R4L15W40 CK4_3*5L" = €669,912, qty 17,700.** `15W40 CK4 5L` is **engine oil**, not a rim.
- Corrupts classification and any rim/lubricant split. There may be more mis-described SKUs — this one surfaced only because it's top-15 by revenue.
- **Action:** audit the master description for this and similar lubricant SKUs.

## 🔴 C. PMS capture denominator is not interval-aware  *(this is your 9% → 92% concern — confirmed)*
- Expected demand uses a **flat service rate across filters: oil / fuel / air = 0.35/yr each**; brake = 0.175; clutch = 0.07.
- Air filters are physically replaced far less often than oil filters, so the **air-filter denominator is overstated → its capture (9.3% network / 28% ITUK) is artificially deflated.** Capture rates are **not comparable across categories** as built.
- **48 of 378 capture cells (13%) are pinned at exactly 1.0** because actual > expected — oil & fuel denominators are too *low*; true over-index is hidden by the cap.
- **Action:** replace the flat rate with category-specific replacement intervals before any cross-category capture comparison leaves the building.

## 🟠 D. 2025 fleet is a proxy
- **All 357 of the 2025 capture rows use 2024 UIO as a proxy** (`uio_proxy_used = True`). Every 2025 capture / GPS figure is computed against **last year's fleet**.
- **Action:** caveat all 2025 numbers as "vs 2024 fleet proxy" until 2025 V17/DVLA UIO lands.

## 🟠 E. CY vs FY — 2025 completeness  *(answers the CY/FY question)*
- Data spans **Jan 2023 – Dec 2025**. **CY2025 is complete** and selectable in calendar mode. The Top-30 showing 2024 is a hardcoded `default_year = 2024` (2_GPS.py:293), **not** a data gap.
- ISZE **FY = Apr–Mar**. **FY2025 = Apr 2025 – Mar 2026 → only 9 of 12 months present** (missing Jan–Mar 2026). Selecting FY2025 today returns a **partial-year number with no UI warning** — a trap for anyone reading it as full-year.
- **To report a complete FY2025 you need sales data through 31 March 2026.**  ← yes, the answer to "do we need 2026 till end of March" is **yes**.
- **Action:** (1) add an "incomplete fiscal year" banner when the selected FY extends past the last billing date; (2) decide reporting basis (CY vs FY) before publishing.

## 🟠 F. "Unclassified" is a keyword heuristic, not the AIM classifier  *(answers "Unclassified according to what?")*
- The GPS "Category Hint" comes from `_classify_hint` (2_GPS.py:935) — it checks the 55-PN PMS registry, then **keyword-matches the description**, else "Unclassified". **It is NOT the AIM classification (the 93.5% figure) — different system.**
- **87% of revenue (€85M) shows "Unclassified."** Most is legitimately non-PMS (sensors, engine/DPD assemblies, steering). **But real wear parts are missed** because descriptions abbreviate "BRAKE" as **"BRK"**:
  - `8983767550 ROTOR; DISC BRK` (brake rotor) — **€1.6M** → Unclassified
  - `8982447940` / `8975056801 PAD KIT; …DISC BRK` (brake pads) — **€922K / €893K** → Unclassified
- **Action:** add `BRK`, `ROTOR`, `CALIPER`, abbreviation patterns; and label the column "keyword hint — not AIM coverage" so it isn't mistaken for the classification rate.

## 🟠 G. YoY % blow-ups in mix / benchmark files
- `genuine_qty_yoy_pct` max = **192,500%**, `total_qty_yoy_pct` max = **3,180%** across `mix_genuine_bvp_*` and `db_benchmark_mix*`. Caused by division on a near-zero prior-year base (1 unit → many).
- Makes YoY charts unreadable / misleading.
- **Action:** winsorize/cap YoY %, or suppress rows where prior-year base < threshold (e.g. < 10 units).

## 🟡 H. No credit notes / returns present — RESOLVED 2026-07-03 (not ERP-confirmed)
- **Zero negative `net_sales_value` or `billed_qty` rows**, but SaTy carries explicit `CR` (credit) / `RE` (return) codes on positive-value lines — 280 rows, €1,651,149 (2023-2026 network-wide, current `sales_fact`).
- These are now excluded from GPS revenue, the parts base, and PMS capture actuals (`is_credit_note` in `sales_loader.py` extended beyond sign to also catch SaTy CR/RE) — same treatment as flag A's TRANSPORT/REBATE exclusion.
- **This is a judgment call, not an ERP-confirmed netting rule.** Jerome does not expect ERP confirmation soon. If SAP later clarifies these codes mean something other than credit/return, revert by narrowing the `is_credit_note` definition back to sign-only.

## 🟡 I. Minor
- 3 rows with unit price > €50K (max €75K) — plausible engine assemblies; spot-check.
- 5 rows zero-EUR / non-zero-qty — likely free goods/samples.
- `price_premium_pct` min = −0.54 (genuine 54% cheaper than BVP in some cells) — verify it's a real mix effect, not a pairing error.

---

## Bottom line
Before these numbers go external: **(C)** interval-aware capture and **(A/B)** removing non-part/mislabelled revenue are the two that move headline figures. **(E)** the FY2025-incomplete trap and **(D)** the 2025 fleet proxy are the two most likely to embarrass in a meeting if unguarded.

*Scan reproducible from `sales_fact.parquet` + `01_data/derived/`. Regenerate derived via `python scripts\build_strategic_contracts.py` then `python scripts\verify_derived_pipeline.py`.*

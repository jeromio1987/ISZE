# ISZE state packet

**Updated:** 2026-09-22 — PMS price-response pack closed (2024→2025); V20 adjudication still open below

## PMS price response 2024→2025 (closed this session)

Combined brief: `01_data/90_INBOX/PMS_PRICE_RESPONSE_PACK_2024_2025_2026-09-22.md`.

**Five-customer refresh (2026-09-22 evening):** new `2025_ZPR1.XLSX` ingested for **CBC / GA / UTI / UMI / KIMA only**. Write-up `01_data/90_INBOX/ZPR1_FIVE_CUSTOMER_PMS_MOS_2024_2025.md`. CBC+GA still ~+29% above list; Israel ~−11/−16%; KIMA ~−33%. KPI MOS (days of stock): UTI ~143d (2025), UMI ~147d, KIMA ~30d; CBC/GA not in KPI.

- Stocking: ~**EUR 1.08M** PMS volume impact with **flat list** (not a clean elasticity story).
- Sales to dealer YoY: **ITUK only**; price pass-through blocked (no dealer invoice prices).
- Genuine→BVP substitution signal: ~**EUR 45k** share-gain (small).
- Open follow-ups: network ASP-vs-list for non-ZPR1 customers; more CY2024 sales-to-dealer files.

## V20 candidate b — IMPOSSIBLE RETENTION ON CYPRUS (parent-found, 2026-09-22)

Candidate b: `06_uio/_CURRENT/ISUZU_UIO_Overview_2026_V20_CANDIDATE_2026-09-22b.xlsx`. Harness improved **V19 7 fails → a 3 → b 1**, and `check1`/`check5` now PASS with zero flagged rows. **Not promotable.**

**The defect — `r90 CYPRUS LCV` implies retention `k = 1.365`** on the first forecast step, which is physically impossible (the fleet cannot retain >100% of itself *and* absorb new registrations):

| Candidate | r90 2025→2030 | implied retention |
|---|---|---|
| a (sane) | 2105 → 2238 → 2339 → 2445 → 2521 → 2614 | 0.883, 0.879, 0.886, 0.884, 0.895 |
| **b (defect)** | 2105 → **3252** → 3506 → 3708 → 3811 → 3868 | **1.365**, 0.964, 0.952, 0.931, 0.921 |

b's own `V20 REGS USED` sheet discloses ~361-400/yr for r90, yet solving `UIO_t = k × UIO_{t-1} + regs_t` gives **1.365** — the row contradicts its own documentation. Root cause: the seam repair treated Cyprus's 2014 splice as a **recoverable registration input**. It is not. **Ireland r26 and Portugal r51 have the same signature and are already handled as splices; r90 and r54 should be too.** r54 Portugal also degraded (non-monotonic, weaker retention than a).

**Harness blind spot — the systematic finding.** `check1`'s ratio test only fires near 0.97, so **an impossible k > 1 passes silently**. The harness improved while the file got worse: a harness that cannot see this is not a gate. New `check10_retention_sanity` being added; it must convict b and pass a.

**Also in b:** r59 Italy MD recovers a **negative** input (−10.8, −4.5); six rows total recover negatives (r28, r43, r53, r58, r59, r69). Greece r79 is `INPUT DERIVED` (no Greek source exists) and still numerically linear. `check7` residual got **worse** (max |Δ| 2.26 pp vs 1.6) — reported, not forced. Totals: V19 1,446,918 · a 1,190,448 · b 1,197,489 (−17.24% vs V19).

**Queued:** candidate c — treat r90/r54 as splices or revert to a and flag `SEAM - NOT RECONSTRUCTABLE`; add the retention check; no row may print k > 1 or k < 0.

## V20 four-row adjudication (2026-09-22) — parent-verified

Report: `01_data/90_INBOX/UIO_V20_FOUR_ROW_ADJUDICATION_2026-09-22.md`. **The builder's "all four are false positives" was also wrong.**

| Row | Verdict | Evidence |
|---|---|---|
| r33 BELGIUM CV LD | **CURVE** | deltas 24/23/21/21/21 (decaying); settles 345 not 1,167 |
| r54 PORTUGL LCV | **CURVE** (caveat) | not constant; **hits the ceiling exactly**, settles 7,024. Caveat: pre-2013 history is not a cohort history |
| **r79 GREECE CV LD** | **STRAIGHT-LINE, NO ATTRITION — REAL DEFECT** | **deltas exactly +14.0 five times (parent-verified from the workbook)**; input is a flat 20/yr on a 43-unit fleet, so the curve is mathematically present and numerically invisible. This is a defect the harness flagged for the wrong reason but correctly |
| r90 CYPRUS LCV | **CURVE** | deltas 133/101/106/76/93, not constant |

**Harness methodology faults found (both correct):** (a) the `k`-ratio test averages ratios — r33's actual per-pair ratios are `[0.913, 1.000, 1.000]` which *average* to ~0.97; the mean of ratios is not a ratio of means. (b) `n_indeterminate: 50` is a **candidate artefact, not a coverage gap** — V19 left those rows blank (so 36 tested); V20 wrote zeros, making 49 empty rows classifiable-but-indeterminate, **holding 0 units**. The classifiable 34 rows hold **99.9996%** of units. The four disputed rows are **3.52%** of units — the verdict was being set by a sliver.

**check7 is a pass-with-residual, not a disagreement.** The harness recompute (6.84/13.40/19.63/25.72/31.48) reproduces exactly; the spec's 7.8→37.7% came from the **v18 dashboard**, not the workbook. The ±1.5 pp tolerance is narrower than the **6.3 pp** that legitimately separates an instant rate from a full convolution.

**Two files in `_CURRENT` are orphans from an aborted run, not authored artefacts:** `_uio_v20_verification_report_CANDIDATE_2026-09-22.json` and `_V20_CANDIDATE_AUDIT_OUTPUT.txt`, both 20:13:47. Their only differences from the canonical report are `generated_utc` and `harness_version`; same workbook, same 3 failures. **Do not cite them.** Kept for provenance.

**Queued scoped pass (before promotion):** (1) write `regs_used` into the workbook — it exists in `06_uio/_Scripts/_v20_engine.json` but nowhere in the workbook, which is why the adjudication had to invert answers; (2) fix r79 Greece; (3) decide r54/r90's missing 2005/06/12 and 2014 seam registrations, which currently cannot be generated by the curve as written (inverting gives negative registrations); (4) re-run the harness and expect check1/check5 to pass and check7 to be re-stated rather than forced.

## Data-loss incident + register repair (2026-09-22)

**`DECISIONS.md` was truncated to zero** by an agent's write-open probe (used only to test writability). The uncommitted **2026-09-20 entry was lost** — Cursor local history stops 11 Aug, no git object in range, no backup. Restored from git and the entry rebuilt: sections 1-3 verbatim from a pre-truncation read, a closing block marked `RECONSTRUCTED`. Pre-fix backup `02_dashboards/pricing/_build/price_5pct_review_2026-09-22/_qa/DECISIONS.md.bak_pre_20260922`. **If Jerome holds a copy of that entry, paste it back.**

**Parent check of the reconstruction: the D24-D26 clauses are CORRECT** — they match the authoritative register on all three (D24 share accepted 0.6364 / ceiling not authorised; D25 no pricing change through the register; D26 Command Center stays retired, tier-A gate outstanding). No correction needed there.

**Register twin was stale and is now regenerated.** `04_tools/workspace/render_decisions_register.ps1 -Check` failed: **D24 sat under "High — 2" listing its old open wording** while the JSON had it decided. Re-rendered; `-Check` now MATCH. Header moved from "18 open, 8 decided" to **"17 open, 9 decided"**.

**Counts block contradicted its own entries and was recomputed.** It read 18 open / 8 decided / blocking 0 / high 2 / normal 16 while the entries summed to **17 / 9 / 0 / 1 / 16**. Cause: D24 was closed on 2026-09-20 and the counts were never recomputed. Corroborated by D24's own `decided_on`/`decision_source` fields and the 2026-09-20 `DECISIONS.md` entry.

**D24 status: CLOSED 2026-09-20.** Portugal `n35_share` **0.6364** accepted on the existing **2,206** N-series base (`imotors_parc_bands`); the share file already carried it. **The ceiling rebuild is explicitly NOT authorised by that closure** — so D24 no longer gates the fleet rebuild, but the ceiling is still held.

## UIO data inventory + the 2013/14 splice (2026-09-22)

Inventory: `01_data/90_INBOX/UIO_DATA_INVENTORY_2026-09-22.csv` (35 sources graded A/B/C) + `.md`.

**Five markets have registration-grade data, not two:** Portugal (I-Motors/SAP, 14,412 unique chassis, 2005-2026), Ireland (SIMI 2010-2025), **Israel** (MOT band flow 1994-2025 + parc 14,019 at 30/06/2026), **Germany** (Helwig parc snapshot 31/12/2025), **UK** (SMMT/DVLA via `UIO.xlsx`). The other 22 market rows have no registration-grade source.

**Implied scrap where measurable:** Ireland CV 14.3% pooled → ~16.5% on 2020-24 · Portugal CV 8.3% on 2020-24 · Israel CV ~4.1% and drifting up · Irish pickups ~9.6% (last 5 yrs). **Germany and UK cannot be computed** from what we hold.

**Spec corrections:** §Problem 5 names the right four markets but reads the "0.3-3% scrappage" as evidence about them. It is not — a fleet carried forward on an assumed low rate measures as scrapping at that rate. Cyprus and Malta also have tiny doubling fleets where near-zero net scrappage is arithmetically normal. **Germany (7.2%, highest of the four) belongs in its own category: "current level known (Helwig), history unknown."**

**PARENT-VERIFIED — the 2013/14 splice is real and worse than reported.** Read directly from `ISUZU_UIO_Overview_2026.xlsx` sheet `1.UIO Overview`:

| Year | Ireland r26 | Portugal r51 |
|---:|---:|---:|
| 2012 | 2,848 | 17,166 |
| 2013 | 2,390 | 16,605 |
| **2014** | **12** | **23** |
| 2015 | 190 | 96 |
| 2016 | 359 | 323 |

Both rows lose **99.5% / 99.9% in one year** — two different populations with no join. **Any scrap rate, trend, or per-truck rate computed across 2013/14 for Ireland or Portugal is meaningless**, and both are among the five A-grade markets. This also explains the Ireland GPS-vs-wallet gap (3,056 vs 2,161). **Must be resolved before any per-market scrap rate is trusted, and before V21.**

**Israel PDF is on disk in the workspace** (the spec said it was not): `01_data\מצגת לחלפים בלגיה - אפריל 2026.pdf`, 3,558,501 bytes, mtime 2026-09-19. Hebrew filename.

## UIO V21 — HELD (Jerome, 2026-09-22)

Jerome: *"for UIO V21 I think we need better spend per unit data"* — then chose **hold until V20 is promoted**. No V21 spec, no GPS denominator rebuild, no re-pointing of `gps_spu_by_distributor.csv` until V20 goes live. Findings parked in `00_docs/roadmaps/gps.md` §"UIO V21 — spend-per-unit data quality (HOLD)".

**Five defects proven by parent check on `01_data/00_derived/gps_spu_by_distributor.csv` (88 rows):**
1. Fleet is v18-era — `uio_source`: 68 `v18_actual`, 16 `v18_proxy_2025`, 4 `ituk_dvla_2026`.
2. `uio_proxy` is **False on all 88 rows** while 16 carry a proxy source — the flag is inert.
3. **Two published fleets disagree per market:** IRELAND 3,056 (GPS) vs 2,161 (wallet) = **+41.4%**, PORTUGAL +13.4%, GERMANY −6.7%; totals (163,459 vs 163,198) hide it. Ireland is the 2013/14 splice.
4. Four markets bill parts with **zero fleet** (UKRAINE, ARMENIA, KAZAKHSTAN, PALESTINE).
5. **`RATE_N35` is applied only to ITUK** — `gps_v9_loaders.py::max_spend_from_buckets()` prices `LD * RATE_N75` for every other market. Not fixed (moves a published ceiling).

**The accuracy is in the band mix, not in new sources:** rates span 3× and the 3.5 t share runs 22% (DE) to 63.6% (PT), so a per-truck figure moves 20-30% on mix alone — currently an assumption because the rate is applied to a lumped `LD` row. Also: the measure `total_sales_eur ÷ uio_units` is **what we invoice the distributor**, not market spend; true market spend needs dealer sell-out, held for UTI only.

## Tonnage band set — LOCKED (Jerome, 2026-09-22)

Report: `01_data/90_INBOX/UIO_HISTORY_AUDIT_2026-09-22.md` (+ per-year reconciliation CSV). Workbook untouched.

- **Grand Total reconciles exactly in all 41 years** (max gap 5.8e-11). The spec's "~2,500/yr shortfall" is an **appendix printing omission** (22 rows printed, 39 carry inputs; true input 18,478 vs printed 15,924 in 2026). Largest omission is **UK CV row 22 at 1,685 units** — 19× the 90-unit row-25 issue the spec leads with. Row 2 has 41 live formulas; rows 7-90 have none.
- **Perimeter rule found:** IMIT `EUROPE - ISZE Only` = 10,845 for 2026; gap decomposes exactly **495 (no pickup row: Ukraine/Armenia/Palestine) + 119 (six stale cells, UK −90)**. Four tests written: LCV/D-Max only; ISZE-served, MIDI excluded; IMIT's market list governs; take IMIT's figure.
- **History only partly sound.** Ireland 731 rebuilds to **730.48** (via the 7.5 t band with a **2-year lag**, not the N-series total). **Portugal 2025 does NOT rebuild** (best of 84 constructions 2,123 vs 2,206) — marked "reported, not verified". Only Germany LD/MD carry the backwards 3% signature. Five rows have no history before their rebuild start; **two are spliced at 2013/2014** (Ireland, Portugal — losing 99.5% / 99.9% in one step), so Check 1 validates only the post-2014 half.
- **Two workbook defects the spec does not mention:** (a) the MIDI subtotal row 5 ≠ the sum of `MIDI`-tagged rows (short by up to 5,500 in 2000) because France/Switzerland carry distributor `MIDI Europe` but tag `ISZE` — **the tag column is wrong, row 5 is right**; anyone filtering on the tag understates MIDI by a third. (b) The two summary tables at the foot of sheet 1 are pinned to 2020/2022/2024/2025 while row 2 runs to 2030 — from 2027 they diverge by **43,409 trucks**, and summary table 1 is not MIDI-consistent (2020 total 209,670 vs row 2's 204,155).
- **Helwig Germany gap open:** Helwig parc 623 vs workbook Germany LD 2025 697 — 74 units unexplained. Helwig is Germany's only tonnage source; sort before any Germany rebuild.

**BVDB pack is CLEAN of the MIDI tag defect.** Parent check of the shipped table `01_data/00_derived/uio_by_market_type_year.csv` (1,279 rows): **18 markets, zero MIDI / France / Switzerland / Italy rows** — the pack ships ISZE-served markets only, so the broken tag column never reaches BVDB. `band_note` carries the LD-label caveat per market.

## Tonnage band set — LOCKED (Jerome, 2026-09-22)

Car park rows and all dashboards show **four bands**, matching the GPS wallet bands in `prism/data/gps_model_targets.csv`:

| Band | Models | Wallet €/truck/yr |
|---|---|---:|
| **3.5 t** | N35 Grafter (NLR) | **296** |
| **5.5 – 7.5 t** | N55 / N65 / N75 (NMR 5.5, NNR 6.5, NPR 7.5) | **739** |
| **11 – 13.5 t** | F110 / F135 (FRR 11, FSR 13.5) | **887** |
| **Pickup** | D-Max / LCV | **250** |

Top band is **"11-13.5 t", not "13.5 t"** — 284 FRR (11 t) against 30 FSR (13.5 t), so a 13.5-named band would be ~90% eleven-tonne trucks. **No 10 t and no 11.5 t truck exists** in the European range (confirmed against Isuzu UK range guide + spec sheets; N55 5.5 and N65 6.5 confirmed, not N50/N62 as earlier spec text said). Israel is the exception: their ministry publishes 6.5-7.5 / 7.6-10 / 10.1-12 / 12.1-16 and is **mapped onto** these four bands, not reproduced as rows.

Constants recorded in `03_analytics/Isuzu/prism/scripts/build_nseries_tonnage_bands.py` (`CANONICAL_FOUR_BANDS`, `CANONICAL_BAND_LABEL`).

**Confirmed 2026-09-22 (second pass — Jerome asked whether 3.5→7.5 is too big a leap).** The second band **starts at 5.5 t**, so the step is 3.5→5.5, not 3.5→7.5; "7.5" is only the top of that band. Wallets cannot be split for 5.5/6.5 anyway: car park rows say only light/medium per market, and only two sources separate the mid-weights (our 2020+ VIN file, and Helwig for Germany, which publishes 3.51-5.50 and 5.51-6.50 as its own rows). The €296 → €739 step is 2.5×, inherited from the £400 vs £1,000 study behind the wallet — **not re-measured**, and that limit is recorded.

**Weights — corrected 2026-09-22 after a claim-check.** Source: `01_data/07_UIO/vin/VIN_register.csv`, 3,238 rows, all `scope_cv_ex_ituk_uti = True`.

| Series | Weight | Units | % of register |
|---|---:|---:|---:|
| NLR | 3.5 t | 1,377 | 42.5% |
| NPR | 7.5 t | 1,290 | 39.8% |
| FRR | 11 t | 284 | 8.8% |
| NMR | 5.5 t | 149 | 4.6% |
| NNR | 6.5 t | 108 | 3.3% |
| FSR | 13.5 t | 30 | 0.9% |

The two main weights are **82.3% of the register**, and 5.5+6.5 are **7.9% combined**. An earlier parent statement said "91% across everything we shipped since 2020" — **wrong on scope and on the ratio**: the register holds only **Belgium, Cyprus, Germany, Greece, Ireland, Malta, Portugal** (zero UK, zero Israel rows), and 91% is only reached by dropping the F-series from the denominator. The register is CV-only and excludes our two largest fleets, so **the European mix is not measurable from it**. The four-band conclusion stands on the narrower base.

## P4 account-health fix (2026-09-22) — and a parent misdiagnosis corrected

Builder `p4-v2`, 108 insertions / 11 deletions. Report: `01_data/90_INBOX/P4_TIMESTAMP_FIX_2026-09-22.md`. Backups `*.bak20260922`.

**I misdescribed this defect to Jerome and the correction matters.** I said the builder "filtered on a belief that billing ended in March and wrote NULL where orders existed". Both halves were wrong: the March date existed **only as a meta comment field and was never in the windowing code**, and the real bug was the **opposite direction** — the 90-day window had **no upper bound at all**, so months joined orders billed *after* their own cut-off. Non-null `signal_to_order_days` went **157 → 151** (it *fell*; two gained, eight lost). `signal_to_order_lift` non-null 137 → 130, 119 of 130 changed.

Verdicts moved on **13 of 215 rows**; latest month **RED 10/AMBER 6 → RED 11/AMBER 5**, the single change being **GREECE AMBER → RED** (mail-to-order +159% once the window was right). Thresholds untouched (`thresholds_calibrated: false`) — RED is still not a business signal. Added: coverage dates derived from the files, a 14-day mail-staleness guard (currently firing at 18 days), and `mode_a` renamed to `internal_only` (nothing read it).

**Downstream stale, needs Jerome:** `action_ledger_open.csv` holds 16 `ACCOUNT_HEALTH` rows on the **old** verdicts, and the exec paper HTML still prints "10 RED / 6 AMBER".

## UIO V20 candidate (2026-09-22) — NOT yet promoted

Workbook: `06_uio/_CURRENT/ISUZU_UIO_Overview_2026_V20_CANDIDATE_2026-09-22.xlsx` (+ assumptions log, 170-cell changelog, verify JSON, receipt). Flat 3% rule removed; 2026-2030 now on the same curve as 1990-2025. Row 25 = 44,926 then 12.3% + IMIT regs. Plan-only MD rows zeroed and out of Grand Total. **V19 and v18 archive byte-identical** — mtimes unchanged.

| Year | V19 incl MIDI | V20 incl MIDI | Overstated |
|---|---:|---:|---:|
| 2026 | 269,314 | **252,218** | 6.8% |
| 2027 | 279,502 | **245,214** | 14.0% |
| 2028 | 289,529 | **237,873** | 21.7% |
| 2029 | 299,448 | **230,873** | 29.7% |
| 2030 | 309,125 | **224,270** | 37.8% |

Harness on candidate: **3 FAIL of 10** (check1, check5, check7). Builder calls check1/check5 false positives; **parent read the four rows directly and does not accept that yet** — r79 Greece CV LD is a constant +14/yr straight line with no attrition, which is curve-free. Two agents are settling it (`v20-adjudicate`) and the LCV age-12 value (`v20-lcv12`, worth ~5.6% on every LCV row and possibly the 44,926 lock).

## GPS model-group defects corrected (2026-09-22)

Two fixes + one live defect recorded, from the tonnage audit:

1. **Fixed — `NMR` was priced as a 3.5 t truck.** `prism/modules/gps_model_targets.py` grouped NMR with NLR in the N35 Grafter branch, so a 5.5 t N50/N55 drew the **€296** wallet instead of **€739**. NMR now maps to N75/N50/N62, matching the VIN register (NMR 5.5 t) and `build_nseries_tonnage_bands.py`. Verified by direct call: `NLR→296`, `NMR/NNR/NPR/LD→739`, `D-MAX→250`, `F110→887`.
2. **Corrected two stale spec claims in `V20_SPEC.md` §Problem 6.** (a) "the N35 Grafter row is dead configuration" was true before the 2026-09-17 fix and is now false — an explicit `N35`/`NLR` row does return €296. (b) The tonnage total read 19,687 t / 6.08 t; the shipped register is **19,545 t / 6.036 t** (284 FRR at 11.0 t, not 11.5 t; the 142 t gap is a deliberate FRR choice).
3. **OPEN — worse version of the same fault in `01_data/91_build/gps_v9_loaders.py`.** `max_spend_from_buckets()` applies `LD * RATE_N75` (€739) for every non-ITUK distributor; `RATE_N35` is used only in the ITUK branch. So the six markets the 18 Sep split was built for — Portugal (~68% 3.5 t), Germany, Ireland, Belgium, Malta, Cyprus — still have their whole LD block priced at the 7.5 t rate. `uio_v19_gps.json` already carries `rates.N35 = 296`, so the two GPS paths disagree. **Not changed** — it moves a published ceiling. Needs Jerome's call.

## UIO forecast defect — containment done (2026-09-22)

Impact map: `01_data/90_INBOX/UIO_UPGRADE_IMPACT_MAP_2026-09-22.md` (+ CSV) — **104 artefacts** (46 live / 49 shared pack / 9 archive); 30 need no rebuild. Classes separated: forecast years move, 2025 history (163,198) does not, ceiling chain held under D24.

**Contained:** the defect page `02_dashboards/fleet/ISUZU_UIO_Dashboard_2026.html` now carries a "2026-2030 under revision" band; **both deploy copies quarantined** in `07_deploy\Master Dashboard\` and `07_deploy\publish-site\` (renamed `_QUARANTINE_*FORECAST_UNDER_REVISION.html.disabled`, 941-byte stub left in place). Nothing was deleted. Page's own KPI was wrong: prints "+0.8% vs 2025E" where its printed values give **+17.8%**.

**Overstatement figure is a RANGE, not 37.7%.** The independent harness (`03_analytics/Isuzu/prism/scripts/verify_uio_v20.py`, run 2026-09-22) recomputes **9.0% → 45.7%** against the spec's 7.8% → 37.7%; both are stated residuals. The symptomatic band on the page and in the BVDB caveat now reads **8-9% → 38-46%**. The harness also convicts V19 on **7 of 10 checks** (14 rows switch method mid-series; 15 rows carry the 3% signature; UK LCV still 49,280; plan-only MD rows counted in Grand Total). Conviction report: `06_uio/_CURRENT/_uio_v20_verification_report_V19_CONVICTION.json`. Procedure: `01_data/90_INBOX/UIO_V20_AUDIT_PROCEDURE_2026-09-22.md`.

**Three spec anchors the harness could NOT reproduce** (do not quote as settled): Ireland 2030 1,382/2,527 (harness gives ~1,175/~2,774); measured scrappage 13.3%/7.4% (now 15.1%/9.0% from the register rebuilt 2026-09-18); the overstatement curve itself.

**BVDB pack caveat added and zip rebuilt twice** — first for the caveat, then to carry the corrected range. `09_meetings/BVDB_PBI_Data_Upload_2026-09-23/00_START_HERE/HOW_TO.md` §4. Prior zip kept as `.bak_before_forecast_caveat_20260922`. **Still holds the broken forecast rows** — see open question to Jerome.

## Internet / universe scrape (2026-09-22)

KS top-300 + brakes/filters/steering deepen, Tranzparts, TMC = **PASS** (dated CSVs). Mekonomen + Auto365 robots-blocked; Autodoc/Oscaro Cloudflare 403; dealer sell-out, OEM MSRP, web fleet = **FAIL**. Report: `01_data/90_INBOX/INTERNET_UNIVERSE_SCRAPE_REPORT_2026-09-22.md`. **Parent correction:** B3 first compared web stock against the 258,594 workbook total (includes MIDI Italy, not our customers) — corrected to the 163,198 customer fleet; verdict unchanged.

## Mail project — "go ahead" (2026-09-22)

Governance pack ready to submit: `00_docs/governance/mail/` (README, DPIA outline, LIA, Art.13/14 notice, works-council ask, retention schedule). Decision sheet: `01_data/90_INBOX/MAIL_NEXT_STEP_2026-09-22.md`. **Two names needed: B1b approved LLM route, and who signs G0b.** Deterministic layer: 9 of 12 §7 KPIs computed. Two defects found: P2a tables 41 days stale; `account_health` filtered orders on a `sales_fact` end date misdated by five months (fix in progress, `p4-fix`).

## Truth repairs (2026-09-22)

Fig-key labels: **392 / 392** verified on live `parts_catalog_dimension` (bumper / door / air guide / wiper), bak `…_191756`. EPC thin-index on 925 supersession PNs: almost no coverage — pricing untouched. ISD Stage 0: headline € identical, PN drivers moved. UTI deletes: nothing removed — proposal awaits Jerome. Write-up: `01_data/90_INBOX/TRUTH_REPAIRS_2026-09-22.md`.

## D08 fleet-figure rebuild (2026-09-22)

Executed. Worksheet fleet **163,198**; matched GPS rate **€188.46**; published ceiling **€55,253,312** kept (wallet engine not re-run; D24 open). Leakage packs and live price lists untouched.

Rebuilt + receipt: OS Console, OS Hub, KPI Dashboard, AIM Classification Paper, AIM Truck Catalogue, BPR deck. Write-up: `01_data/90_INBOX/D08_EXECUTION_2026-09-22.md`. Backups `*.bak_d08_20260922`.

**Held:** any builder that would re-base the ceiling to €54,323,455; prism_map €60.22M bake (D10); Portugal share write.

---

**Prior updated:** 2026-09-22 — ES/IT/DE national tenders wired + warranty + D01/D02

## National tender portals ES / IT / DE (2026-09-22)

Wired into live monitor. Probe gated: ES **10** · IT **2** · DE OV **163**. Published `01_data/dashboards/tender_data.json` **689** notices. RESULT: `01_data/90_INBOX/RESULT_national_portals_ES_IT_DE_2026-09-22.md`. Optional ES monthly ZIP for deeper lookback; DTVP still paid/retired.

## Warranty commercial follow-ups (2026-09-22)

Internal brief: `02_dashboards/ops/Warranty_Commercial_Followups_2026-09-22.html` (+ OPEN cmd + receipt). Steering-gear campaign **€837k** (not the old ~€1.6M mixed-currency figure). Who-pays bands €1.87M / €1.18M / €0.63M. Belgium 47% vs Poland 173% settlement. Israel €68/truck vs UK €26 / Portugal €9.

## D01/D02 exception queue (2026-09-22)

Authorised regeneration run. Band **0.80 / 1.10**; labels correct (undercut = peer cheaper). Live price list and pricing config **not** touched. Undercut **140 / €1.52M**; raise **35 / €236k**; brakes undercut **25 / €722k**. Write-up `01_data/90_INBOX/RESULT.md`. Review HTML + receipt under `01_data/01_Pricing/BOOK_B_REVISION_REVIEW_2026-09-22.*`.

---

**Prior updated:** 2026-09-22 — BVDB PBI upload pack (UIO + GPS + PMS + AIM)

## BVDB Power BI data pack (2026-09-22, for meeting 2026-09-23)

Hand-off for BVDB: enrichment only (he already has SAP sales / orders / pricing).
No line billing, no order dump, no price-list / simulation files.

- Folder: `09_meetings/BVDB_PBI_Data_Upload_2026-09-23/`
- Zip: `09_meetings/BVDB_PBI_Data_Upload_2026-09-23.zip`
- Start: `00_START_HERE/HOW_TO.md` + `MANIFEST.csv`
- Private talk sheet: `00_START_HERE/MEETING_BRIEF_Jerome.md`
- Contents: `01_UIO` (incl. Sold-to bridge + IUK 2026 override 44,926), `02_GPS`, `03_PMS`, `04_AIM` (slim — not the 12 MB AIM master)

---

**Prior updated:** 2026-09-21 — figure-key labels: 873-042 is a cabin blower filter, not a urea filter

## Figure-key labels — 873-042 is a cabin blower filter, not a urea filter (2026-09-21)

The AIM and figure-key table that goes to Power BI and purchasing
(`AIM_Master_PN_Categories_Figkey_20260921.csv`, byte-identical in `Pricing revision\` and
`01_data\00_derived\`, with an Excel twin of the same numbers) carried figure key **873-042** as
"Urea (AdBlue) filter". Every part on it is a cabin blower or pollen filter (`FILTER; BLOWER UNIT`)
and the rest of the 873 group is blower and heater hardware, so the label was simply wrong. It reads
**Cabin / blower filter** now — 28 rows, **EUR 620k** of 12-month billing. The real DEF element sits
on key **146-152** (`FILTER KIT; PUMP ASM,DEF DCM S`). Three places in the figure-key list that tied
urea counting to the cabin key were pointed at the DEF key, four DEF filter kits that disagreed with
each other now agree, and 67 part-number overrides were added. The parts tree
`parts_catalog_dimension.csv` had 89 label cells corrected across 89 rows.

**The urea share the packet first carried did not come from the table the shared pages read — measured again 2026-09-21.** "1.210% before and after" is a reading of `bvp_pn_dimension.csv`, and that file carries no urea share at all: it is a 919-row list of part numbers, of which the same two genuine kits (`1876102341`, `8983507161`, both `filter_part_role = element`) are the only urea rows. The table that feeds the shared pages is `pms_capture_by_db_year.csv`, and on that table the share moved: **1.1173% → 0.6116%**, billed euro **EUR 133,770 → EUR 186,473**, units **5,901 → 3,230**.


**Two open decisions.** First, do not run the tree's own builder
(`03_analytics\Isuzu\prism\scripts\build_fig_key_dimension.py`), because the tree on disk was last
built in July, the PR00 catalogue behind it has moved since, and the live file is maintained by
targeted edits. That was measured today against the live table: a rebuild would re-cut **1,744
figure keys and 2,586 labels**. The euro beside that is traffic, not exposure: the rows whose label
text differs carry **EUR 5.4m of billed history across the whole table, 3 January 2023 to 31 August
2026, and about EUR 2.5m of it is the last twelve months**. None of it is money at risk, none of it
has to be rebooked, and none of it says anything is wrong — only the wording on the row might
change. Most of those 2,586 are not errors either: 963 are two reasonable names for the same part,
679 sit on parts with no description to judge against, 395 are the clean build naming something the
live file leaves as "Review needed", 381 the part description contradicts, 93 the clean build would
make worse, 75 undecided. Only the 381, and the overlap with the other buckets, is a real error.
A rebuild would also undo this morning's cabin-filter correction (key 873-042), take the DEF filter
kits `1876102341` and `8983507161` (EUR 48,813) off key 146-152 and label them "Cabin / blower
filter", and turn 116 rows that carry real labels today into "Review needed". A clean build was run
to show that, and its output is kept:
`01_data\90_INBOX\_parts_catalog_dimension.fresh_build_20260921.csv` and `_blast_20260921.py` (no
`parts_catalog_dimension.csv.fresh_build_20260921.csv` is in that folder).
Second, moving the urea counting is now scoped, and it is not the one-file edit first written. The
five rows are in `03_analytics\Isuzu\prism\data\pms_capture_supplement.csv`, not under
`01_data\00_derived\` — cabin blower filters `8980250061`, `8973870961`, `8980413270`, `7552049740`
and `7552162240` filed as urea. The two genuine DEF kits `1876102341` and `8983507161` already
carry `urea_filter` in `01_data\00_derived\bvp_pn_dimension.csv` and stay. Moving the five rows
alone makes the reported figure worse and must not be applied by itself — measured without touching
any file, network urea capture falls from 1.21% to 0.32% and billed urea euro from EUR 144,102 to
EUR 97,332, because ten of eighteen markets sold no urea at all: the whole figure was cabin
filters. ITUK falls from 37.1% to 15.5% on 2025 (28.6% to 12.8% in 2023, 28.0% to 7.6% in 2024,
30.3% to 8.3% in 2026). The reason is on the other side: two of the three real DEF filter kits are
not counted today although they sell, because their description (`FILTER KIT; PUMP ASM,DEF DCM S`)
reads as a kit and the rule deliberately skips anything that looks like an assembly — `8983507160`
(EUR 78,344 all years) and `1876102340` (EUR 10,797) carry billing and are counted nowhere. Done
properly both halves happen in one pass: the five rows move to `blower_filter`, and `1876102340`,
`8983507160` and `8981694030` join the same definition of genuine DEF filter elements in the three
tables that feed the capture — reading **0.61%, EUR 186,473 billed, 3,230 units**. On the AIM file's own twelve-month basis,
EUR 21,704 of cabin filters leaves and EUR 40,455 of genuine DEF kits comes in - a different
window from the network capture basis in the outcome paragraph below, so the two are not in
conflict. One earlier number is wrong and must stop being repeated: no file on disk holds 11
urea part numbers — the parts tree `parts_catalog_dimension.csv` went from 23 urea rows to 5 and
the capture list from 7 to 2.

Both halves were applied on 2026-09-21, in one pass, in
`03_analytics\Isuzu\prism\modules\aim_pn_classifier.py` and
`03_analytics\Isuzu\prism\data\pms_capture_supplement.csv`. Five shared dashboards still print a
urea figure the correction moved:
`02_dashboards\sales\ISZE_Leakage_Cockpit.html` (ITUK 2023 urea 8.71%),
`02_dashboards\sales\ISZE_PMS_Family_Compare.html` (network urea 1.31%, gap EUR 916,329, billed
EUR 52,784, 1,988 units),
`02_dashboards\sales\ISZE_DB_Leakage_Review_CY2025.html` (ITUK 2025 urea 37.1%),
`02_dashboards\ops\ISZE_OS_Console.html` (EUR 916,329 uncaptured),
`02_dashboards\hub\MASTER_DASHBOARD.html` (AdBlue filter 0.2%); plus the ITUK, Belgium and Sweden
packs under `02_dashboards\sales\leakage_packs\`. Counted from the entries of
`_FILES_WITH_STALE_UREA_FIGURE_20260921.txt`, not its header: 93 paths written out, the 18
country-dashboard folders it names but does not open add 43 on disk, so it points at **136 files,
all present, 135 naming urea** (all but GREECE `_qa_sales.json`) **and 40 still printing a moved
number** (the old 1.31%, ITUK 2025 37.06%, ITUK 2023 8.71%); 23 also carry a corrected figure. Its
header says 135, its entries do not support that; a count of filenames of any kind in it gives 94.
Left alone, by decision. The three tables that feed them were regenerated
(`pms_capture_by_db_year.csv` 12:35, `pms_capture_by_family.csv` 13:19,
`pms_opportunity_matrix.csv` 12:40). `metrics_snapshot.json` and `FACTS.md` do not mention urea.

**Urea outcome, measured 2026-09-21, from `pms_capture_by_db_year.csv`.** Network urea capture
**1.1173% → 0.6116%**; billed **EUR 133,770.37 → EUR 186,473.21**; units **5,901 → 3,230** — fewer
parts, worth more, actually counted. The packet earlier carried 1.2096% / EUR 144,102 / 6,388 as the
"before"; those come from the before/after captures the session kept
(`_urea_measure_BEFORE_20260921.txt`), a read taken part-way through the repair, and do not equal the
previous published file. ITUK urea by year: 28.57%→16.49% (2023), 27.98%→22.67% (2024),
37.06%→17.17% (2025), 20.20%→24.02% (2026); the 2026 "before" is 20.20%, not 30.31%. Blower capture
**14.2339% → 15.6563%**, billed EUR 1,329,622 → EUR 1,446,992. On the total line — the basis these
pages are read on — **23 market-years moved to zero**; on the genuine-parts-only line, 24, the extra
being PORTUGAL 2026, where genuine fell to zero while business-value parts stayed at 0.7% and the
total stayed non-zero. Quote 23 against the two published files. The network total is not unchanged:
billed rose by **EUR 92,579** (EUR 19,347,676.17 → EUR 19,440,254.70) and units by 1,135, of which
urea is EUR 52,703 and 3,230 units. The EUR 89,142 the packet gave came from the capture model's own
read, not the published file, and does not reproduce there. **EUR 89,141.56 of the urea movement is
the three DEF filter kits counted nowhere at all** (1,536 units, from `sales_fact.parquet`); there is
**no EUR 835 discount line** — that split does not reproduce. The five cabin parts that left carry
EUR 43,147.66 over the same years, which is why the net urea move is EUR 52,703 and not EUR 89,142.
Every other category's movement is the ordinary billing refresh, not this correction. The parts
tree's own builder `build_fig_key_dimension.py` still cannot reproduce its output, so the pipeline
was run with that one step left out, recorded in `_run_pipeline_no_figkey_20260921.ps1`.

**The regenerated family tables move a page that is on screen in the Command Center.** The only file
reading `pms_capture_by_family.csv` / `pms_family_evolution_both_clocks.csv` /
`pms_family_part_number_map.csv` (all 13:19) is
`02_dashboards\sales\ISZE_PMS_Family_Evolution_v2.html`, embedded 19 September and linked from
`ISZE_Aftermarket_BI_Command_Center.html`; nothing under `04_tools\` reads them. Its 2026 is
EUR 2,889,151.64 against EUR 3,825,175.57 in the table — **EUR 936,023.93 open**, urea EUR 17,733
against EUR 55,485, blower EUR 231,493 against EUR 313,399; other years out by EUR 11,299 / 18,585 /
17,941. Nothing else is out of step; the page stands, by decision.

**Rebuilt 2026-09-21, and the page now ties.** It had been showing a copy of the 19 September family
numbers, which left its 2026 EUR 936,023.93 low; the rebuilt page agrees with
`01_data\00_derived\pms_capture_by_family.csv` at no difference on all four years and all fourteen
service families (2026 EUR 3,825,175.57, against EUR 2,889,151.64 before), confirmed by an independent
check that also held the page's own arithmetic on every displayed row, it opens from a double-click
with no server and no internet connection, the 19 September page is kept beside it as a backup, and two
display defects were corrected: a rounding note on the tile whose four terms miss its headline by one
cent, and a blank basis cell in the fleet totals row.

**Worth a short patch, not a rebuild.** Rows genuinely wrong in the live file today: **359 rows
carry a label their own part description contradicts, about EUR 196,763 of twelve-month billing** —
`BAR; FRT BUMPER` labelled "Leaf / suspension spring" (156 rows, EUR 144,290), `REGULATOR ASM; DOOR`
labelled "Voltage regulator" (107 rows, EUR 16,556), `GUIDE; AIR,FRT BUMPER` labelled "Other air
system" (34 rows, EUR 4,667). Separately **110 rows have no label where one is obvious**, mostly
`BLADE; WIPER`, about EUR 152,207 of twelve-month billing. These are a modest, known, pre-existing
gap that predates today's work and was not caused by it, and a short targeted patch could take them.

**Six files changed today**, each with a `.bak_before_figkey_urea_20260921` copy beside it: the
figure-key list and the part-number overrides in `03_analytics\Isuzu\prism\data\`,
`parts_catalog_dimension.csv` and `.parquet` in `01_data\00_derived\`, and the delivered CSV and
Excel in both locations. Pipeline verification after the work: **153 pass, 2 warn, 0 fail** — the
same counts and the same two warnings as before it (a Denmark gap in the older years of the fleet
workbook, and the lost-sales model a couple of months behind the billing). The report on disk,
`01_data\00_derived\_verification_report.json` (and its `.md` twin), was written **12:48:27**; its
own `generated_at` field reads `2026-09-21T10:47:20Z`, i.e. 12:47:20 local, a minute and a bit
earlier than the file, which is the timezone offset and not a second run.

The amount column that went to BVDV, `l12m_billed_eur`, covers eighteen months of billed sales, 1 January 2025 to 30 June 2026, and its name is a legacy abbreviation that does not mean twelve months; the window is now written down in the file's Coverage sheet and in `Pricing revision\INDEX.md`, and `build_aim_master.py` carries an explicit end date of 2026-06-30 so the figure cannot stretch if the billing table is refreshed.

**The wrong-figure-key list turned out to be mostly a timing story, not a list of mistakes.** The delivered table's `figure_key` agrees with the parts tree as it stood before 17 September on all **161,129 rows that carry a key**, so the roughly 600 rows flagged earlier are largely the **568 rows the tree itself moved on 17 September**, which the table was never refreshed to follow. Genuinely wrong keys, where independent evidence names a better one, are **210 rows carrying EUR 80,872 of billing — 0.15% of the file** (43 high confidence at EUR 52,001, 167 medium at EUR 28,871; twelve rows hold EUR 60,676 of it, and the largest, `8983167030` WRENCH;WHEEL PIN at EUR 34,607, has no key today and belongs on `901-009`), against **1,348 rows (EUR 147,850) that could not be resolved** — 916 with no part description anywhere, 308 where the table's own convention and the tree point at different keys, 84 with too few rows to establish a convention, and 1,129 carrying no billing at all. The evidence is the 2011 TRUCKS F&G parts list in `01_data\00_derived\epc_catalogue_heavy_20260919.csv` (3,062 figure keys, one edition only, covering 2,719 of 165,213 part numbers), and **nothing was changed**: two rows that would shift a part between PMS categories, `8972010610` SHOE; BRK,FRT (`305-124` to `301-001`) and `8980480` fuel filter (`041-055` to `041-002`), were held back, and Jerome's decision is to leave the keys alone, because acting on this means bringing the whole table up to the newer tree revision rather than making 210 corrections, and that cannot be done safely while the table's own builder must not be run.

---

**Prior update:** 2026-09-20 — AIM residual top-N by L12M (`residual_topn_20260920`)

## AIM residual Other/review — highest euro (2026-09-20)

Top-100 still-open by L12M; applied **42** clear leaves · **EUR 198,714** · stamp `residual_topn_20260920`.
Still-open after: **EUR 84,540** (catalog Other still 9,459 / EUR 717k until classification rebuild).
Gate **PASS** 18/18. Backup `aim_master_v2.csv.bak_pre_residual_topn_20260920_054954`.
Worklist: `01_data/90_INBOX/AIM_residual_Other_review_topN_by_L12M_20260920.csv`.

Prior same day: EQ overnight **384** PROPOSE_PATCH (`eq_session_20260919`). Attribute layer on hold. No shared HTML. No commit.

---

**Prior update:** 2026-09-19 — boardroom: MapChart banned; Europe footprint uses IDS ~564-dealer map

**Boardroom maps:** never `mapchart.net` / yellow-blue clip-art. Footprint slide uses
`01_data/90_INBOX/data_join_questions/assets/ids_europe_dealer_network_564.png` (from
`02_dashboards/ids/_qa_map_triple/master_map_live_tiles.png`). Rule gate:
`.cursor/rules/isze-boardroom-deck-process.mdc` — PNG export + image-Read per slide before done.

## Built (2026-09-19) — PMS family evolution v2, forms 2 / 8 / 10 with both percentages

**Page:** `02_dashboards/sales/ISZE_PMS_Family_Evolution_v2.html` (+ `OPEN_ISZE_PMS_Family_Evolution_v2.cmd`,
CRLF, cmd-only). Rebuilt from `_build/build_family_evolution_v2.py`, then verified independently here.
Default is **form 2** (two columns and the difference), with 8 and 10 one click away on the same rows.

**The point of the page, on the real ITUK book — N-series truck, CY2023 → CY2025:**

| | first year | second year | change |
|---|---|---|---|
| Billed euro | 727,731 | 753,204 | **+3.5%** |
| Vehicles in service (workbook's own count) | 19,559 | 22,191 | +13.46% |
| Euro per vehicle | 37.207 | 33.942 | **−8.78%** |

They disagree, and that is the finding: `(1 + 0.0350) ÷ (1 − 0.0878) = 1.1346`, which is the fleet
ratio `22,191 ÷ 19,559`. Every form prints both percentages, so a euro move cannot be read without the
fleet move beside it. Read on the rendered page, not from the build.

**Verified here, not taken from the builder's word:** `verify_derived_pipeline.py` 153 pass / 1 warn /
0 fail · `ship_gate_check.ps1` → `SHIP_GATE_OK` · page gate `QA PASS` (decomposition identity holds to
**EUR 0.0000**) · receipt `ISZE_PMS_Family_Evolution_v2.SHIP_RECEIPT.json` (mtime 15:40 covers the page
at 15:38). Both percentages confirmed as rendered table headers (`Change in billed euro`, `Change in
euro per vehicle`, `Fleet this period`, `Fleet last period`, `Fleet change`), 18 customer options, no
console error, nothing fetched, no CDN.

**Two harness limits, found while checking:** form 8's canvases read `0x0` after a switch while the
page shows their bars (see the canvas section above — the check is now bar-colour pixels on the
composited screenshot, `_build/qa_forms_painted_v2.py`), and form 8's fleet switch is asserted only on
the comparison-year bar because the current-year denominator **is** the 2025 estimate and cannot move.

## Error register updated

`01_data/90_INBOX/ISZE_Agent_Error_Register_2026-09-18_19_v2.xlsx` — **28 rows, 12 Critical, 10 High,
6 Medium, 10 root causes**. E27 (the fleet in the denominator, 9 of his turns against the 4 a reply
gave), E28 (a capability reported missing without testing it), R9 (a count answered from memory) and
R10 (a limit asserted from one bad test). Totals are derived from the rows. Gates:
`_qa_error_register.py`, `_fix_register_mojibake.py`.

## Excel on this machine

Office 16 ClickToRun is installed (`Root\Office16\EXCEL.EXE`, 16.0.20326.20144; resolved via the App
Paths registry key). The excel connector reads a workbook, cell by cell and structurally, **without
Excel on PATH** — that is how the register above was read back. Only COM recalculation needs Excel
(`EXCEL_ENABLE_COM=true`, off). `shutil.which('EXCEL.EXE')` returns None for ClickToRun: **not** a
test for Excel.

## Pricing stack — where it stands (2026-09-19)

**The move is the weighted increase of all prices, measured.** Not a formula. Jerome: *"you need to
look at the weighted increase of all prices not the formula."*

| Measure | Weighted increase |
|---|---:|
| Whole priced book | **+5.9616%** |
| Japan (IML) | **+6.2081%** |
| Thailand (IMIT) | **+6.3088%** |
| PR00 | +5.9211% |
| UTI | +5.5808% |
| UMI | +5.6370% |
| CIS | +4.8455% |

All four markets inside 4–6%. Recipe `in_scope == True` AND `unpriced_reason IS NULL`, 47,617 rows,
reproducing the published 5.9616% exactly.

**What it replaced.** A factor chain — `(1+revision) × (163.7/178.5) × (0.673/0.620)` — that
multiplied by a rate and a discount **already in force**. It put Thailand at −2.45%, a reduction,
against the measured +6.31%. The exchange rate is corporate and applied; a "pass-through dial" was
invented and has been removed from every artefact.

**What the base price is.** The IML Export Base Price is built up from IML's own costs; our purchase
price is a discount **off** it — 62% vehicle parts, 73.5% industrial engines (Hayakawa, 10 Nov 2025).
So the base carries a margin that is not ours, and the class letter sets ours on top.

**Artefacts.** Workbook `01_data/01_Pricing/ISZE_Pricing_Stack_Simulation_2026-09-19.xlsx` with a
sibling launcher; write-up `01_data/90_INBOX/PRICING_STACK_APPLIED_2026-09-19.md`; roadmap
`00_docs/roadmaps/pricing.md` (hub item 16). Receipt regenerated 12:52 to cover the current file.

**NOT VERIFIED:** that Excel opens it and that it scrolls. No Excel or COM on this machine. The two
mechanical causes of the earlier scroll failure were removed and are asserted in the receipt.

**Open from this session:** the industrial-engine discount rate (config applies the vehicle-parts rate
to everything Japanese); IML's "around 3%" against our measured 5.9616%; the override rows; the
no-source-label rows (1,801 rows, 9.2% of weight, +3.06%).

**Error register:** `01_data/90_INBOX/ISZE_Agent_Error_Register_2026-09-18_19_v2.xlsx` — **28 rows,
12 Critical, 10 High, 6 Medium, 9 root causes**. Updated 19 Sep with **E27** (the fleet must sit in
the denominator; his own turns on it counted from the transcript at 9, not the 4 a reply gave) and
**E28** (a capability reported missing without testing it), plus **R9**. Severity totals and the
register total are now derived from the rows, not typed — typed totals were wrong twice on 19 Sep.
Row heights derive from the longest cell, so a long evidence entry cannot clip. Two defects found
and fixed while doing this: corrupted dashes in E11's text (UTF-8 read as cp1252), and five error
rows that had counter-measure text but no row on the Counter-measures sheet. Gates:
`_qa_error_register.py` (28 rows, no clipping, totals reconcile, every error has a counter measure)
and `_fix_register_mojibake.py` (zero corrupted sequences).

**Excel on this machine — read/write works, and it was wrongly reported missing.** Office 16
ClickToRun is installed at `C:\Program Files\Microsoft Office\Root\Office16\EXCEL.EXE`
(16.0.20326.20144; the App Paths registry key resolves it). The excel connector opens a workbook,
returns any cell or sheet, runs structural render checks and exports — that is how the register
above was read back. **A workbook can therefore be read, cell-level checked and exported with no
Excel on the machine at all.** The one thing that needs Excel itself is driving COM to recalculate
(`EXCEL_ENABLE_COM=true`, currently off). `shutil.which('EXCEL.EXE')` returns None for a ClickToRun
install because Office is not on PATH — do not use it to test for Excel.

## CV warranty — "LD" weight class and the parts wallet (2026-09-18)

**The `LD` label is not a weight class.** It reads 6.5/7.5 t in Israel and 3.5 t in most of Europe,
and the same token drives the parts-wallet rate per market. Israel's `LD` row was **priced
correctly all along** (€739, the 7.5 t rate) — the label was the defect, not the number. Two
independent sources confirm the market holds no 3.5 t Isuzu truck: the CV warranty VIN register
(2,360 VINs, Dec 2023 → Mar 2026: NPR75 895, FRR90 817, FSR90 627, zero NLR/NMR/NKR) and the
Ministry of Transport band table, whose smallest class is 6.5–7.5 t.

| Item | Path |
|------|------|
| Workbook (relabelled; numbers untouched) | `06_uio/_CURRENT/ISUZU_UIO_Overview_2026.xlsx` — note in **B92** of `1.UIO Overview`, Changelog V19-5..V19-7 |
| Pre-edit backup | `06_uio/_Archive/ISUZU_UIO_Overview_2026_backup_before_ld_relabel_20260918.xlsx` |
| Evidence note | `01_data/90_INBOX/_ld_weight_class_and_wallet_correction_20260918.md` |
| Per-market split table | `03_analytics/Isuzu/prism/data/uio_ld_n35_share.csv` |
| ITUK mileage question (draft, not sent) | `09_meetings/ITUK_MILEAGE_QUESTION_2026-09-18.md` |

**Applied, not proposed.** (1) The workbook is relabelled — every chart, image, formula and numeric
cell is byte-identical to the prior revision, verified by comparing zip parts. (2) PRISM now splits
the collapsed `LD` row **per market**, not just the UK (`data_prep.py`). (3) The JP VIN register
tonnage decode is fixed: it read the number in the chassis code as a tonnage, so NLR 3.5 t trucks
were recorded at 8.7 t and both FRR90 and FSR90 at 9.0 t. Rebuilt: **19,545 t over 3,238 trucks,
6.04 t average** (was 26,689 t / 8.24 t). New `gvw_t_source` column.

Measured 2025E target-wallet effect of the split: **PORTUGAL ×0.801, MALTA ×0.895, IRELAND ×0.979,
BELGIUM ×0.981, GERMANY ×0.982, CYPRUS ×0.993. ISRAEL and ITUK deliberately unchanged.** Germany is
**22%** 3.5 t on the Helwig parc bands and Malta **37%** — `V20_SPEC` §Problem 6 listed both as
"0% — no change", corrected in that file. Portugal's GPS percentage rises about a quarter.

**Then the shares themselves were audited (2026-09-18, later).** Every row of the share file was
recomputed from the source it names. **IRELAND was wrong: 0.063 → 0.3089.** It was tagged `simi_bands`
but carried the JP VIN register number (36/570). The SIMI parc basis is **464 of 1,502** at 2025;
flow basis 663/1,963 = 0.3377. **BELGIUM 0.918 → 0.8571** (NLR 42 of 49). **PORTUGAL 0.620 →
0.6899** (1,299 of 1,883 N-series; the old row divided by all 2,111 rows). **MALTA and CYPRUS marked
`unmeasured`, rates held** — both rested on reading NMR88 as an N35, but NMR88 is 9.5 t and Cyprus
holds zero 3.5 t. Germany, Greece, ITUK and UTI confirmed. Target wallet (computed, waterfall **not**
rebuilt because it is locked): Ireland €935,912 → €856,281, Portugal €2,446,187 → €2,377,877,
network −0.46%. Verifier 143 pass / 0 fail. Audit: `01_data/00_derived/n35_share_audit_20260918.csv`.

**Two mistakes made and fixed during the pass, recorded so the next agent does not repeat them:**
a zero share initially *deleted* Israel's 6,059 trucks instead of passing them through (would have
dropped UTI's ceiling by €8.3M); and the workbook note was first put in **D7**, which the loader
reads as the model field, so a paragraph became a model name. Both caught and corrected before
leaving this session. Backup taken before the workbook edit.

**Nothing published, no mail sent, no price moved.** PRISM suite green (71 passed).

### Warranty commercial datasets (2026-09-18) — folder + workbook, with a currency correction

**`01_data/00_derived/warranty_commercial/`** — 13 CSVs, a 13-sheet workbook, a README and an
`OPEN_*.cmd`, all regenerable from `01_data/91_build/build_warranty_commercial_datasets.py`. One file
per commercial question, all markets inside each file. Excel pre-delivery check **OK, issues=0**.

**A currency error was found and corrected in doing this.** The truck claim file's `CRNCY` column
carries two tokens: `EUR GBP` means the amount is in **pounds** (UK — 11,956 lines, the largest book
in the file) and `JPY EUR` means **yen** (Italy, Spain, France, Switzerland and others). The earlier
note summed that column raw, mixing three currencies. Corrected: truck parts turnover **€4.66M** (not
€2.83M), emissions **€2.84M = 61%** (not €1.82M = 64%), truck steering gear **~€1.15M** (not
€800k). The D-Max figures were already normalised and are unaffected. Every euro in the new folder is
normalised first (EUR as-is, GBP ×1.12, JPY ÷163.7) and `warranty_cv_currency_audit.csv` shows the
working per market.

### Warranty data — what else it carries (2026-09-18, read-only)

A third pass over the claim files with a commercial lens. **Findings and limits:
`01_data/90_INBOX/_warranty_data_what_else_it_carries_20260918.md`.** Nothing was built or published.

- **The claim files hold no maintenance.** Oil filter 8 CV lines / 2 LCV, air element 0 / 2, brake pad 0 / 33.
  A consumable is not a defect and is not claimed, so **measured replacement intervals cannot come from
  warranty** — the `air_filter: 0.5` factor needs dealer repair-order data or a parts basket.
- **The single dominating line is the power steering gear**: €800,177 on 329 D-Max claims at €2,432 a
  truck, present in 22 of 30 markets, failing at 2.7 years — inside warranty. On trucks €800,191 on 329
  claims, same per-claim cost. One part family, both fleets, ~€1.6M.
- **42% of D-Max parts turnover sits outside the 3-year / 100,000 km limits**, and overwhelmingly on age
  rather than distance. Per market it runs from **25% (Sweden) to 68% (Norway)** — a loyalty decision
  per book, not a technical one.
- **Settlement rates diverge 3.7×**: Belgium recovers 47% of claimed parts, Poland 173%.
- **`PARTNBR2` is empty on all 33,416 CV lines**, which settles the 33,416-vs-16,480 question — the line
  count is the true claim count and 16,480 was a double-count.
- **Dealer code `V19010` carries 36% of all CV claim lines.**
- **The UK duty-cycle story is downgraded, not confirmed.** Sweden replaces the steering gear sooner
  (17,008 km vs UK 29,624) and the 25th-percentile claim odometer is 526 km in Sweden against 12,112 km
  in the UK, so the near-zero readings are a booking convention. The clean UK issue remains the mileage
  assumption (in `ISZE_ROADMAP.md` B11), not duty cycle.

## Delegator watch + the +5% review (2026-09-17 late evening)

Three things, all new files. Nothing existing was overwritten.

**A 20-minute AIM watch is armed and detect-only.** Windows task `ISZE_DelegatorWatch_20min` ticks every
20 minutes, fingerprints five AIM and pricing-base files, and writes a row to a shared agent board only
when a fingerprint actually moves. It wakes no agent, rebuilds nothing, and refuses to write any locked
pricing deliverable. Agents cannot ping each other — Cursor has no such tool — so the board is the
substitute: each agent reads it at the start of a run and appends a row at the end.

| Item | Path |
|------|------|
| Script / launcher | `04_tools\workspace\isze_delegator_watch.ps1` · `run_delegator_watch.cmd` |
| Self-test (15 assertions, all pass) | `04_tools\workspace\_test_delegator_watch.ps1` |
| Board / state | `00_docs\agent\DELEGATOR_BOARD.md` · `DELEGATOR_STATE.json` |
| Change procedure / rule | `00_docs\agent\DELEGATOR_REFRESH_HOWTO.md` · `.cursor\rules\isze-delegator-board.mdc` |
| Task XML | `04_tools\workspace\ISZE_DelegatorWatch_20minTask.xml` |

**A +5% flat increase is computed as a paper exercise on new dated files.** On the in-scope L12M base
(EUR 34,993,609.39 billed over 48,653 lines, 15,872 part numbers): **+5% = EUR 1,749,680.47**. The filed
revision on the same base is EUR 1,652,140.71 at 5.9616% published — two separate proposals, never added.

**The step ties out; the published rate does not.** Recomputed on the file, the quantity-weighted move is
5.9787% across all in-scope lines and 6.2347% across priced rows only; the published 5.9616% implies a
denominator of about EUR 27.71M that no column reproduces. The page claims the step, not the rate.
1,647 lines carrying EUR 4.48M (12.81% of billed) cannot move at all — no base price on one side.

| Item | Path |
|------|------|
| Workbook | `01_data\01_Pricing\Price_Increase_5pct_Flat_REVIEW_2026-09-17.xlsx` |
| HTML + receipt | `02_dashboards\pricing\ISZE_Price_Increase_5pct_Flat_REVIEW_2026-09-17.html` (+ `.SHIP_RECEIPT.json`) |
| Launcher | `02_dashboards\pricing\OPEN_ISZE_Price_Increase_5pct_Flat_REVIEW.cmd` |
| Builder / verifier | `02_dashboards\pricing\_build\price_5pct_review_2026-09-17\` |

Gates: verifier **57 pass / 0 warn / 0 fail, `SHIP_GATE_OK`**; `excel_pre_delivery_check.py` 0 issues;
4 charts painted in real Chrome at 2 widths, no console errors, 19 PNGs on disk of which 6 were
image-read at full size. **Nothing published, nothing mailed, no live list touched.**

**Two things waiting on Jerome** (in `DECISIONS.md` 2026-09-17): whether IML re-bases the list at the new
SPA rate of 172.6 rather than the engine's 163.7 — a re-base cuts euro cost about 5.2%, roughly the whole
increase — and whether the +5% is flat across the book or follows the AIM priority ranking.

**Locked read-only (Jerome, 2026-09-17).** The shipped revision pack and page, the AIM priority list, and
anything already under `01_data\00_derived\` — plus `03_analytics\isze_pricing\config.yaml`, whose FX fork
stays open. New work goes to new dated files. Procedure: `00_docs\agent\DELEGATOR_REFRESH_HOWTO.md`.

## AIM classification — paper rebuilt on 18 Sep master (2026-09-18)

Shared paper refreshed from live `aim_master_v2.csv` (**165,213** rows, **2,417** `gap_auto_20260918`)
and `aim_pn_classification_v2.csv` (catalogue **7 / 27 / 176 · 164,667**). Hero no longer prints 164,667.
Builder for the refresh: `01_data\91_build\rebuild_aim_classification_paper.py`.
Two-axes lock and attribute-layer hold from 17 Sep still stand.

| Item | Path |
|------|------|
| Gate | `01_data\00_derived\aim_classification_gate.json` |
| v2 + meta | `01_data\00_derived\aim_pn_classification_v2.csv` |
| Focus CSVs | `01_data\00_derived\aim_catalog_focus_filters.csv` (+ matrix / brake / priceclass) |
| Paper + OPEN | `02_dashboards\sales\ISZE_AIM_Classification_Paper.html` · `OPEN_ISZE_AIM_Classification_Paper.cmd` |
| Receipt | `02_dashboards\sales\ISZE_AIM_Classification_Paper.SHIP_RECEIPT.json` |

Still open: Axis B scoring build; EQ column fill; Other/review residual needs figure majority
(~9.5k PNs); gasket/harness/pipe home. **Attribute layer: on hold (roadmap)** — Jerome 2026-09-17;
do not build; not proceed; attributes-before-levels stays recommended when resumed.

## Price revision — AIM source pack rebuilt on 18 Sep master (2026-09-18)

Cube → Excel → HTML rebuilt after the master gap fill. **Step EUR 1,652,140.71 / weighted 5.9616%** still
ties. Not-on-AIM in-scope euro **EUR 6,883,707.71 → EUR 1,660,928.43** (spine coverage **80.33% → 95.25%**).
Excel COM Checks sheet: diff 0. Customer-first drill unchanged.

| Item | Path |
|------|------|
| HTML + OPEN | `02_dashboards\pricing\ISZE_Pricing_Revision_AIM_Source.html` · `OPEN_Pricing_Revision_AIM_Source.cmd` |
| Excel + OPEN | `01_data\01_Pricing\Pricing_Revision_AIM_Source_Analysis.xlsx` · `OPEN_Pricing_Revision_AIM_Source_Analysis.cmd` |
| Receipts | `…AIM_Source.SHIP_RECEIPT.json` · `…AIM_Source_Analysis.SHIP_RECEIPT.json` |

## Price revision — AIM source analysis shipped (2026-09-17)

Two deliverables, both verified: an Excel workbook and a self-contained HTML page, built on the
**price-revision weight base** (`01_data\00_derived\price_bp_weighted_compare_pn.csv`,
`in_scope == True`), window 1 Jul 2025 to 30 Jun 2026 — **48,653 in-scope lines over 15,872 part
numbers, EUR 34,993,609.39 billed**.

**The headline ties out to the published revision: step EUR 1,652,140.71 and weighted increase
5.9616%**, both verified by recalculating through Excel with zero formula errors.

The analysis is on the **AIM spine** (`aim_l1_fixed` / `aim_l2_fixed` / `aim_l3` from
`aim_master_v2.csv`), with **source of supply** as J (Japan through IML) or T (Thailand through
IMIT), which is what was asked for. Coverage is named, not hidden: AIM level 1 covers 80.3% of
in-scope euro, level 3 is filled on 80.3%, source of supply is held on 93.6%; the remainders
appear as explicit buckets.

| Item | Path |
|------|------|
| Excel workbook (11 sheets, live formulas over a 48,653-row data sheet) | `01_data\01_Pricing\Pricing_Revision_AIM_Source_Analysis.xlsx` |
| HTML (self-contained: data and Chart.js inlined) · launcher | `02_dashboards\pricing\ISZE_Pricing_Revision_AIM_Source.html` · `OPEN_Pricing_Revision_AIM_Source.cmd` |

Sheets: DB summary, DB × AIM L1/L2/L3, TH-JP source, Source × AIM L1, Customer, Top movers,
PN data, Checks. An FX cell on Checks revalues the whole file. The HTML has a distributor
dropdown, a source filter, a weighted % / step EUR / billed EUR metric switch, and click-to-drill
L1 → L2 → L3. No CDN and no server needed.

Prior step pack (upload of the new base price) remains at
`02_dashboards\pricing\ISZE_Price_BP_Weighted_Compare.html` and
`01_data\00_derived\price_bp_weighted_compare_{pn,customer}.csv`.

**Prior pass on the step pack (2026-09-17, same day).** The "what this comparison does not cover"
table now names each bucket and its owner instead of three anonymous totals (the lubricant bucket
as UMI's engine oil, 7 PNs, sold-to 1797), and the ranked table carries a Description sourced from
the text as billed in SAP. A latent defect was closed while doing it — three of six Checks rows
returned an Excel error instead of OK because their Expected cells held formatted text and one
tolerance was too tight at `ROUND(...,3)`. Gates: Excel recalculated via COM, 6/6 reconcile checks
OK; `excel_pre_delivery_check.py` passed; HTML verifier 44/44 checks OK; render QA read at 4 widths
(0 blank canvas, 0 clipped, 0 white-on-pale, 0 console errors).

**Israel split — resolved and still the rule.** `sold_to_sap` is the key (1797 = UMI, 1799 = UTI).
The `sold_to` NAME column was relabelled 2026-04-01 and now reads UNIVERSAL MOTORS ISRAEL LTD for
both codes, so it can never split them.

Next: the pricing spec is at `00_docs\ISZE_Pricing_Spec_v1.md` (v1, 2026-08-05) with the engine at
`03_analytics\isze_pricing\`. Phase 2 (FX) and phase 3 (price playing) build on step 1.

## Air filter — handoff for the next agent (2026-09-17)

**Read `01_data\00_derived\HANDOFF_AIR_FILTER_AND_FOCUS_CUT.md` before touching air filter or the
Focus cut.** It is the working brief for the next agent and these are its fixed points.

- Use `aim_catalog_focus_filters.csv` on the **`catalog_full`** basis, not `pr00_catalog_only`.
  The literal restriction looks like 13% of in-scope euro and drops the air-filter leaf entirely,
  because `aim_source` is a precedence label for which vocabulary won `aim_l1`, not a completeness
  flag for the catalogue columns. `catalog_full` ties out to the shipped pricing comparison.
- The `ACL` → air-cleaner classification patch **landed** on 2026-09-17 at 19:50. The air-filter
  leaf is now **EUR 796,783.16 on 40 part numbers** for the 12 months to 2026-06-30, and **all 22
  in-scope markets bill air filtration** (smallest is Palestine at EUR 574).
- Two older claims are **withdrawn** — delete them if they reappear: that the leaf was "a network
  number in name only at EUR 28,469", and that some markets showed "real zeros". Both were side
  effects of the misfile.
- The catalogue tree and the AIM spine place the same 40 part numbers differently; do not put a
  catalogue-tree filter total beside an AIM-spine total without saying which is which.

## Open items (2026-09-17)

**Decisions waiting on Jerome are tracked separately** in `01_data\90_INBOX\DECISIONS_AWAITING_JEROME_2026-09-19.json` (readable `.md` twin in the same folder, read by the stop hook) — 20 open, 3 decided on 2026-09-19. The entries below are data-item gaps, not those decisions.

- **RESOLVED 2026-09-20 — the air-cleaner misfile was wider than recorded, and the first fix
  landed in the wrong place.** The old entry here read: 12 elements misfiled under
  `Cleaning Chemicals > Cleaner`, worth EUR 124,951.56, "recorded, deliberately not fixed".
  What is actually true now, measured:
  - That `Cleaning Chemicals` branch holds **0 part numbers** on the master today. The misfile
    is gone, but it was not moved to Filters. The 20 Sep pass `figkey_aim_fix_20260920` moved
    them to **`Air conditioning > Other A/C` (124 PNs / EUR 998,360)** and
    **`Air system > Other air system` (8 PNs / EUR 162,252)** — **132 PNs / EUR 1,160,612**, not
    12 PNs / EUR 124,952. The real set is roughly 8x the recorded value.
  - **Root cause: the master's tree columns are a stale one-time copy.**
    `build_aim_master.py` copied `pr00_classification.csv`'s `family`/`group`/`level3_type` into
    `cat_l1/l2/l3` when it built the master on **17 Sep 22:06**. `pr00` was then corrected twice
    — `pr00_classification.csv.bak_pre_pad_supersession_2026-09-17` (19:50, the ACL air-cleaner
    patch) and `bak_pre_eq_doubt_20260918` (22:22) — and **the master was never re-copied.** So
    the master sits at 98.34% agreement with its own declared upstream, while the older
    `aim_pn_classification.csv` sits at 99.36%. Today's passes read the stale column and could
    only stay wrong.
  - **Second, quieter loss: the competitive flag went off.** `cat_pms_flag` is `1` when the tree
    family is in the PMS list in `build_aim_master.py` (line 151). That list contains
    `Air system` but **not** `Air conditioning`. So the 124 moved to Air conditioning all read
    `cat_pms_flag = 0`. Across the whole pricing basis the understatement is **1,090 part
    numbers / EUR 1,518,350** — the flagged share prints **53.91% where it should read 57.71%**.
    Families that regain the flag: steering 184 PNs, filters 183, transmission 119, belts 116,
    exhaust 108, fuel system 100, brake parts 47.
  - **Fixed by rebuilding from the declared source, not the copy.** New dated file
    `01_data/00_derived/aim_pn_classification_20260920.csv` (164,907 rows, 26 columns) reads the
    tree live from `pr00_classification.csv`, so the air filter is back at **254 PNs / EUR 1.2M**
    against the upstream's 254 of 260. Every row that moved against the master is flagged
    `catalog_changed_vs_master=1`. Builder:
    `01_data/91_build/build_aim_classification_20260920.py`. Gate: 17 of 18, see below.
  - **Not affected: the pricing numbers Jerome has seen.** The pricing cube and the packs group
    by the AIM families (`aim_l1_fixed`), a different axis. `pricing_aim_source_lines.parquet`
    and `pricing_aim_source_cube.csv` contain **no tree column and no flag column**. Step
    EUR 1,652,140.71 and 5.9616% stand.
  - **Still open, needs Jerome:** `recalc_aim_pricing_single_basis.py` prints the flagged share
    from `aim_master_v1.csv` (the oldest copy) and is understated by 3.80 points. The line was
    never written to a file — `aim_pricing_recalc_2026-09-17.json` carries only the 80.33% AIM
    figure and the 100% tree figure — so no report or page carries the wrong number. Also open:
    the two deployed Repertoire pages (`ISZE_AIM_Repertoire_Map` / `_Spider`, 17 Sep) chart the
    tree and are **EUR 103,348 / 0.30%** out against the corrected upstream on 931 rows.
  - **And the master itself is unchanged** — it still holds the stale tree. The new file works
    around it. Re-copying the master's `cat_*` from `pr00` is a PRISM-owned change and needs its
    own decision.
- **Country of origin is a separate, already-built field** (`country_of_origin`, more than 40
  countries) and was deliberately not used. A study that wants origin rather than supplying entity
  reads a different column and is a rebuild.
- **Dealer level cannot be built from this pricing file.** It carries the sold-to account only,
  25 of them, which is what the revision was run on. The billing data has no dealer key.

## PRISM parts base (2026-09-17) — closed

The "two published values" question is **answered, and it was not two numbers**.
`€103.57M` and `€112.09M` are the same method at two cut-off dates (2026-03-31 vs 2026-06-30);
the difference is the Apr–Jun 2026 billing wired in on 2026-08-25.

Chasing it exposed a **live leak**, now fixed: on 2026-09-03 the SAP sold-to map sent four
non-part entities to a code (`NON_PARTS`) that was never in `EXCLUDED_CODES`, so 9 CY2026 rows /
**€180,715.11** of service fees and demurrage entered the parts base. A recompute read
€112,270,022 against the published €112,089,307; after the fix it returns **€112,089,307.0 exactly**.

| Item | Path |
|------|------|
| Bridge + fix record | `FACTS.md` §4.1 · `DECISIONS.md` 2026-09-17 |
| Fix sites | `03_analytics\Isuzu\prism\modules\data_prep.py` (`EXCLUDED_CODES`) · `modules\sales_loader.py` (`NON_PART_LINE_KIND`) |
| Derived bridge keys | `scripts\build_metrics_snapshot.py` → `sales.parts_base_data_through`, `sales.parts_base_through_prior_quarter_eur` |
| Anchors | `prism\data\facts_anchor.yaml` (both cut-offs) |
| New open flag | `01_data\00_derived\_data_integrity_open_issues.md` → **CR/RE-FY26** |

Verify: **116 pass / 0 warn / 0 fail**; facts-drift **ALIGNED**. CY2025 untouched, so 51.1% never moved.

## Built (2026-09-16 workspace remediation)

Nine reports only, all on disk and unchanged: audit refresh, execution brief, security, Alps PR
land, mypens PR land, VC gaps C.1–C.2, Tier1 consolidation refresh, inventory. Index:
`docs\WORKSPACE_AUDIT_REFRESH_2026-09-16.md` · `docs\CONSOLIDATION_TIER1_REFRESH_2026-09-16.md` ·
`docs\WORKSPACE_INVENTORY.md`.

## Open / blocked

| Item | Status |
|------|--------|
| ISZE PRs | **All 8 merged** — see `docs\_wsA_ISZE_report.md`. Local dirty tree left uncommitted; both IDS stashes dropped |
| C.3 myPENS CI | **Done** — workflows on mypens `main` (`1476ccc`); see `docs\_wsC3_mypens_ci_report.md` |
| E truth audit | **Done** — `docs\TRUTH_AUDIT_2026-09-16.md` (4 confirmed disagreements; fig_key = date drift only) |
| Old GitHub PAT | Skipped per Jerome 2026-09-16, files left; residual local-disk risk only |
| Private health `.gitignore` | Proposal written in `_wsB`; awaiting confirm before use |
| cairn / pebble | Awaiting Jerome: version / park / reclaim |
| Tier1 delete 210 files (~222 MB) | **Done** — 210 deleted / 221.9 MB; sign-off log `docs\_tier1_delete_receipt.json` |
| Alps `.gitignore` `export_*.csv` | Done on disk, **not committed** |
| AIM spine misfile (12 air-cleaner elements) | **Superseded 2026-09-20** — was 12 PNs / EUR 124,952; actually 132 PNs / EUR 1.16M moved to the wrong leaf, plus the competitive flag off on 1,090 PNs / EUR 1.52M. Rebuilt from the declared source. See the Open items entry above |
| Retire orphaned UTI artifacts | **Still open, needs Jerome** |
| Roll out remaining 15 leakage packs | **Open** — and decide whether packs go to distributors (no mail sent) |

## CV warranty mileage validation (2026-09-16)

| Item | Path |
|------|------|
| Validation note | `01_data\90_INBOX\_cv_warranty_mileage_validation.md` |
| Derived table | `01_data\00_derived\warranty_cv_km_age_by_market.csv` |
| Fleet/age companion (parallel worker) | `01_data\90_INBOX\_market_fleet_profile_workup.md`, `_market_fleet_profile_design.md` |

**Headline:** the PRISM mileage assumption is confirmed for UTI (measured 51,680 vs assumed 50,000) and contradicted for ITUK (measured 16,688 vs assumed 50,000). The global `annual_km_yr: 20000` is structurally wrong — mileage tracks truck weight class (N35 12,165 / N75 35,217 / F-series 45,630), a 3.7× spread. Open question: whether ITUK's 50,000 or the UK warranty VIN sample is the wrong one. **Awaiting Jerome before any PRISM rebuild.**

## Built (aftersales KPI — 2026-09-16 evening)

| Item | Path |
|------|------|
| KPI questions board (15 live views) | `02_dashboards\sales\ISZE_PMS_Family_Compare.html` + `OPEN_ISZE_PMS_Family_Compare.cmd` |
| Graph lab (design only) | `02_dashboards\_design\kpi_graph_lab\OPEN_KPI_Graph_Lab.cmd` |
| Graph proposal | `01_data\90_INBOX\_kpi_graph_design_proposal.md` |
| **BPR 2.0 deck (40 slides, all charts in)** | `09_meetings\Business_Performance_Review_2026\ISZE_Business_Performance_Review_2026.pptx` + `OPEN_Business_Performance_Review.cmd` |
| BPR builders + charts | same folder — `build_numbers.py`, `build_kpi_numbers.py`, `build_core_charts.py`, `build_leakage_charts.py`, `build_aim_prism_ids_charts.py`, `build_ids_charts.py`, `build_bpr_deck.py` |
| BPR QA (geometry preview + structural) | same folder — `_qa_preview.py`, `_qa_deck.py`, `_qa\slides\` |
| Car park V19 vs V20 (both chapters) | `02_dashboards\fleet\ISZE_UIO_Car_Park_V19_V20.html` + `OPEN_ISZE_UIO_Car_Park_V19_V20.cmd` |
| **Distributor leakage cockpit (internal, 11 panels)** | `02_dashboards\sales\ISZE_Leakage_Cockpit.html` + `OPEN_ISZE_Leakage_Cockpit.cmd` |
| **Sales performance review packs (customer, 10 panels)** | `02_dashboards\sales\leakage_packs\ISZE_Sales_Performance_Review_{ITUK,SWEDEN,BELGIUM}.html` |
| **GPS/PMS truth + alignment reports (read-only)** | `00_docs\GPS_PMS_TRUTH_REPORT_20260917.md` · `00_docs\GPS_PMS_ALIGNMENT_20260917.md` |

## GPS / PMS alignment — GPS root cause FIXED, downstream rebuilt 2026-09-17

GPS re-split complete and **every page that derives from the ceiling rebuilt**. ITUK 32.4% →
**45.6%**, ITUK ceiling €17.18M → **€12.21M**, network anchor 51.1% → **55.7%** (wallet €60.22M →
€55.25M). Only ITUK moved; the other 17 markets are unchanged.

**Rebuilt on the corrected anchor:**
| Artifact | Shows now |
|---|---|
| `sales\ISZE_Exec_Aftersales_Paper.html` | 55.7% · €30.76M / €55.25M · 40% flat €250 |
| `ops\ISZE_OS_Console.html` | 55.7% cover · €55.25M ceiling · €24.54M uncaptured |
| `hub\ISZE_OS_Hub.html` | 55.67% cover · ceiling €55,253,312 |
| `_composable\dist\isze_cockpit.internal.html` | ceiling €12,212,051 |

Ceiling figures in the paper and console are now **derived at build time** from
`wallet_waterfall.csv` rather than typed literals — that was why they went stale within an hour of
the split. `SHIP_GATE_OK`; exec-paper gate PASS; hub guard OK.

**Two pre-existing breaks found while sweeping (not caused by the split):**
1. **RESOLVED 2026-09-17** — `02_dashboards\_composable\build.mjs` no longer reads the archived
   `gps_pure_sales_2026-08-13.csv`. The fallback now points at the live `_v2.csv` sibling. (The
   module already declared the correct file, so this was a landmine, not an active break.)
2. **RETIRED 2026-09-17 (Jerome decision)** — `md_pack\ISZE_MD_Pack_Capture_FY27_FY28.html` had no
   builder and showed the superseded 51.1% / €60.22M. Its three hub links and the `md_pack`
   manifest family were removed; hub rebuilt and `HUB_GUARD_OK`. The file itself is left on disk,
   unreferenced.

**Still open, needs Jerome:** retire the orphaned UTI artifacts.

**Resolved 2026-09-17 (Jerome decisions):**
- **Addressable 70 vs 100 — keep 100%.** The percentage scales modelled expected demand only
  (`pms_engine.py:333`), so at 70% every capture figure rises 43% (ITUK oil filter 65.9% → 94.2%).
  It does not touch GPS. Evidence argues for 100%: three ITUK families already exceed modelled
  demand (oil filter 116.4%, fuel filter 157.0%, brake rotor 197.7%) — the denominator is too
  small, not too big. The knob is `services_per_year` on wear parts, not the fleet share.
- **Clutch population — cannot be measured.** The VIN register carries `transmission` /
  `transmission_source` / `transmission_confidence` columns but every row is `unknown` / `none`:
  `build_vin_register.py` states Europe JAA VINs encode series/GVW/wheelbase/serial, not
  transmission, and refuses to invent AT/MT. Duncan's VIN list has no transmission column either.
  The 10,549 was 22,389 × 0.47, a convention, not a count. PRISM prices clutch on the full 23,068;
  publish clutch as an **upper bound** until a VIN decode or a market answer arrives.
- **GPS dashboard — already composition-based, not a flat rate.** Its €11.84M is DVLA vintage
  (22,389) priced by model mix: 10,900 N35 × €296 + 10,684 N75-class × €739 + 805 F × €887 =
  €11,835,911. Same method as the rebuilt ceiling; it differs only by fleet vintage and, for
  Ireland / Portugal / UTI, by a real composition difference (Ireland +€435K, Portugal −€442K,
  UTI −€756K, Germany +€396K). See `00_docs/GPS_PMS_ALIGNMENT_20260917.md` §6.

**Fixed alongside:** forked `gps_dashboard/modules/pms_engine.py` marked deprecated;
`capture_recovery_model.csv` no longer partial-year; `metrics_snapshot.json` provenance corrected;
`gps_master.csv` flat rate carries a quotation block; reconciliation prints PARTIAL not PASS when
hard checks are skipped.

## Prior built (unchanged)

| Item | Path |
|------|------|
| Exec aftersales paper | `02_dashboards\sales\ISZE_Exec_Aftersales_Paper.html` |
| Command Center | `02_dashboards\sales\ISZE_Aftermarket_BI_Command_Center.html` |
| Distributor leakage cockpit | `02_dashboards\sales\ISZE_Leakage_Cockpit.html` |
| Customer packs (3 pilot markets) | `02_dashboards\sales\leakage_packs\` |

## Distributor leakage tool (2026-09-16)

Internal cockpit + per-distributor customer packs from one shared data file; pilot packs for ITUK
(critical), SWEDEN (mid), BELGIUM (strong). Gates: `verify.py` 45 checks and `qa_leakage_tool.py`
44 rendered checks in real Chrome, both exit 0. The customer build strips other markets, dealer
names and internal registers, and fails if any other market code appears. All year comparisons
are like for like (same months each year plus an average month) — this corrected a headline that
read −58% where the true movement was +34.2%. Part numbers to act on are included per market.
Build chain: `02_dashboards\_build\leakage\` — `extract.py`, `build.mjs`, `verify.py`,
`qa_leakage_tool.py`.

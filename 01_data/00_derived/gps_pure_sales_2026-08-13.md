# gps_pure_sales_2026-08-13 — true / pure sales (GPS-eligible, Shell out)

**Written:** 2026-08-13  
**Grain:** one row per distributor × FY (FY2023–FY2026)  
**Canonical numerator:** `pure_sales_eur`  
**Not a GPS% file.** No UIO, no max spend, no v20, no `gps_pct`. Warranty is a column so include/exclude can be a filter later.

This file is **not** the plan/billing-clean extract. An older pipeline nickname for that *other* extract was "Kosha basis"; this file is not that.

---

## What `pure_sales_eur` means

GPS-eligible **parts** net revenue after:

- BillT S1/G2/RE/S2 and SaTy CR/ZDR (full GPS-clean taxonomy in `gps_reconcile.py`)
- Transport charges
- Service fees / late payment interest / demurrage (`excl_other`)
- **Shell Rimula 550047\* / 550070\* — out**, stored separately as `shell_lubricants_eur`

Then surcharge-neutralised (same convention as `gps_billing_fy_ALLCUSTOMERS.csv` `net_gps`).

Shell is **never** merged into UMI `pure_sales_eur`. Lubricants stay a separate line.

---

## Source lineage (derived only — no raw XLSX opened)

| File | Role | File date (mtime) |
|------|------|-------------------|
| [`C:\Users\jerom\Desktop\claude\ISZE\01_data\00_derived\gps_billing_fy_ALLCUSTOMERS.csv`](C:\Users\jerom\Desktop\claude\ISZE\01_data\00_derived\gps_billing_fy_ALLCUSTOMERS.csv) | **Primary numerator.** `net_gps` → `pure_sales_eur`. Israel UMI/UTI already split via dedicated extract. | 2026-07-23 |
| [`C:\Users\jerom\Desktop\claude\ISZE\01_data\00_derived\gps_billing_fy_waterfall.csv`](C:\Users\jerom\Desktop\claude\ISZE\01_data\00_derived\gps_billing_fy_waterfall.csv) | Network Check 6 waterfall (gross → exclusions → clean). `clean` is **not** surcharge-neutralised. | 2026-07-23 |
| [`C:\Users\jerom\Desktop\claude\ISZE\01_data\00_derived\gps_billing_clean.json`](C:\Users\jerom\Desktop\claude\ISZE\01_data\00_derived\gps_billing_clean.json) | Plan/billing-clean extract (**Shell still in**). Used only to prove per-DB Shell / other gaps. | 2026-07-06 |
| [`C:\Users\jerom\Desktop\claude\ISZE\01_data\00_derived\gps_billing_transport_excluded.json`](C:\Users\jerom\Desktop\claude\ISZE\01_data\00_derived\gps_billing_transport_excluded.json) | Per-DB `transport_eur`. Sums match waterfall `excl_transport` exactly every FY. | 2026-07-06 |
| [`C:\Users\jerom\Desktop\claude\ISZE\01_data\00_derived\gps_billing_surcharge_stripped.json`](C:\Users\jerom\Desktop\claude\ISZE\01_data\00_derived\gps_billing_surcharge_stripped.json) | Per-DB `surcharge_stripped_eur` (`net_raw` − `pure_sales_eur`). | 2026-07-06 |
| [`C:\Users\jerom\Desktop\claude\ISZE\01_data\00_derived\distributor_warranty_expense_fiscal.csv`](C:\Users\jerom\Desktop\claude\ISZE\01_data\00_derived\distributor_warranty_expense_fiscal.csv) | Fiscal warranty € (FY2024–FY2026 only). Same file cited by `gps_dual_basis.json` as `warranty_fy_basis`. | 2026-06-18 |
| [`C:\Users\jerom\Desktop\claude\ISZE\01_data\91_build\gps_dual_basis.json`](C:\Users\jerom\Desktop\claude\ISZE\01_data\91_build\gps_dual_basis.json) | Cross-check of fiscal warranty € and of the live-dashboard UMI FY2026 25.8% **numerator**. Not used as sales. | 2026-07-03 |

`gps_master.csv` was **not** used and was **not** modified. Live dashboard HTML was **not** edited. Nothing under `01_data/` or `02_dashboards/Data/` was deleted.

Producer of ALLCUSTOMERS / waterfall: `04_tools/gps_reconcile.py --rebuild` (full GPS-clean).  
Producer of billing-clean + sidecars: `04_tools/rebuild_gps_billing_and_surcharge_check.py` (narrower exclusion set: BillT + SaTy CR/RE + transport only).

**Lineage date gap:** billing-clean JSON is 17 days older than ALLCUSTOMERS (6 Jul vs 23 Jul). Gap identities below still hold to the cent. Do not treat that as a refresh of the JSON.

---

## Exclusions applied

| Bucket | Column | Treatment |
|--------|--------|-----------|
| Transport | `transport_eur` | Excluded from pure sales. Per-DB from sidecar; network identity vs waterfall holds. |
| Shell Rimula 550xxx | `shell_lubricants_eur` | Excluded from pure sales. **Per-DB only where the billing-clean − ALLCUSTOMERS gap equals network `excl_shell`.** That identity holds for **UMI in FY2024, FY2025, FY2026**. All other DBs in those years: `0.00` by exhaustion (network Shell fully explained by UMI). FY2023 network `excl_shell` = 0 — recorded as 0 with `fy23_shell_zero`, not inferred from a line scan. |
| Service / late / demurrage | `other_excl_eur` | Excluded from pure sales. Identity: **ITUK FY2024 €150,028.97** and **ITUK FY2025 €246,996.72** = entire network `excl_other`. FY2026 network `excl_other` = **€0 — not silently filled**. |
| CR / ZDR still sitting in billing-clean | `saty_cr_excl_eur` | Full-clean drops these; billing-clean keeps some. Proven residuals only: Ireland FY2024 €1,120.50; ITUK FY2026 €17,600; IMG FY2026 €10,000. Remainder of FY2026 waterfall `excl_saty_cr` €27,960 is UNK_2686 €360 (no ALLCUSTOMERS row — unmapped payer). |
| Warranty | `warranty_eur` | **Not** subtracted from `pure_sales_eur`. `pure_sales_ex_warranty_eur` = pure − warranty **when warranty is known**. Blank if unknown. Not invented. |

---

## Settled vs provisional

| Item | Status |
|------|--------|
| True-sales numerator (Shell out, GPS-eligible parts) | **Settled** as the canonical sales basis for this file (Jerome 2026-08-13, option A). |
| Shell as a separate lubricants line, never inside UMI pure sales | **Settled** |
| Warranty as a filter column, not baked into a GPS% | **Settled** |
| Live dashboard 25.8% left as-is | **Settled** (different extract — see below) |
| UIO / max spend / GPS% | **Provisional — not in this file.** Do not treat any implied % as a management figure. |
| v20 / `UIO_carpark_for_GPS_recalc` | **Not adopted** |
| FY-to-FY trend of pure sales | **Not comparable until Check 4 is fixed** (see below) |

---

## Live dashboard 25.8% is a different extract — not comparable

UMI FY2026 on the live GPS dashboard (25.8%) comes from **plan/billing-clean (Shell still in) minus warranty**, then ÷ UIO max spend.

| UMI FY2026 figure | EUR | Extract |
|-------------------|-----|---------|
| Billing-clean (Shell **in**) | 2,853,277.40 | `gps_billing_clean.json` / dual-basis `sales_gross_eur` |
| Shell Rimula (this file) | 407,942.16 | = entire network FY2026 `excl_shell` |
| **Pure sales (Shell out)** | **2,445,335.24** | this file `pure_sales_eur` |
| Warranty (column, not baked) | 1,633,086.00 | fiscal warranty file |
| Dashboard 25.8% **numerator** | 1,220,191.40 | billing-clean − warranty (Shell still in that numerator) |
| Pure sales − warranty | 812,249.24 | this file `pure_sales_ex_warranty_eur` |

Difference between the two ex-warranty numerators = Shell €407,942.16.  
No new GPS% is published here. Do not convert 2,445,335 or 812,249 into a % against any UIO.

---

## UMI 125% is rejected

The 125% figure is **UTI + UMI billed onto the UMI wallet**, with Shell still in. Dual-basis UMI FY2026 max spend €4,721,500:

- (UMI billing-clean 2,853,277 + UTI 3,056,797) / 4,721,500 ≈ **125.2%**
- Warranty toggle does **not** produce 125%. (UMI+UTI billing-clean − UMI warranty) / same wallet ≈ 90.6%.
- This file keeps the Israel split (`israel_split` on UMI and UTI). Both rows currently carry payer `1797` because UTI ship-to routes through the UMI sold-to in SAP; the dedicated Israel extract is what separates the money.

Do not put UTI revenue on the UMI wallet.

---

## FY2026 `excl_other` = 0 — flagged, not fixed

Waterfall FY2024 `excl_other` = €150,028.97 (all ITUK).  
Waterfall FY2025 `excl_other` = €246,996.72 (all ITUK).  
Waterfall FY2026 `excl_other` = **€0.00**.

That is a **data-basis break**, not evidence that ITUK stopped billing service / late / demurrage. Every FY2026 row is flagged `fy26_other_excl_zero`. No prior-year run-rate was imputed.

ITUK FY2026 still has a €17,600 residual vs billing-clean; that is CR/ZDR (`saty_cr_excl_eur`), **not** a substitute for the missing `excl_other`.

---

## Other material caveats (not buried)

1. **FY2023 is partial.** Network gross €8.03M vs €31.9–34.7M in FY2024–26 (~Q4 only: Jan–Mar 2023 if the CY2023 extract starts at calendar 2023). Flag `fy23_partial`. FY2023 also has `excl_shell` = 0 and `excl_other` = 0 (`fy23_shell_zero`, `fy23_other_excl_zero`).
2. **Check 4 currently FAILS.** Do not compare GPS% — or even raw pure-sales trends — across FY2025 vs FY2026 without stating that FY26 dropped the other-exclusion bucket to zero. A “GPS decline” or “GPS improvement” across that boundary is partly a data artifact.
3. **UMI FY2024 warranty €2,902,813 > pure sales €2,842,371** → `pure_sales_ex_warranty_eur` = **−€60,442**. Arithmetic is honest; an ex-warranty GPS% for UMI FY2024 would be nonsense. MIDI FY2025 is also slightly negative (−€3,087).
4. **RSA naming collision.** Billing `RSA` = payer 66 = Greece (Petros Petropoulos). Billing `Norway` = payer 86. Warranty file uses `RSA` = Norway and `Greece` = Petros. Joins are flagged `warranty_joined_as_RSA` / `warranty_joined_as_Greece`.
5. **Warranty missing** for all FY2023 rows, and for CBC, CIS-KTK, GA, IMG, IMIO, KIMA, TR, Sverige2 in later years (blank, not 0).
6. **UNK_2686 €360** sits in billing-clean FY2026 and is not a distributor row here.
7. **Waterfall `clean` ≠ network `pure_sales_eur`.** Waterfall clean is pre-surcharge-neutralisation. FY2026: waterfall clean €33,067,066.71 vs network pure sales €32,858,918.54. The gap is the surcharge strip, not a second exclusion.
8. **Per-DB Shell is identity, not a material-number scan.** Raw XLSX was not opened (instruction). If 550xxx appeared on a non-UMI DB it would be a new anomaly; derived gaps show no Shell-sized hole on any other DB.
9. **Checks 2–3 were not re-run at line level** (no raw SaTy / G2 sign test this pass). They are inherited from the 23 Jul ALLCUSTOMERS rebuild.

---

## ISZE GPS DATA AUDIT — gps_pure_sales_2026-08-13 — FY2023–FY2026

```
ISZE GPS DATA AUDIT — gps_pure_sales_2026-08-13 — FY2023–FY2026
══════════════════════════════════════════════════

⚠️  CHECK 1 — Non-parts materials
   Found (network waterfall, not a fresh line scan):
     Transport  FY23 €83,657 / FY24 €314,512 / FY25 €357,942 / FY26 €327,501
     Shell      FY23 €0 / FY24 €387,681 / FY25 €519,794 / FY26 €407,942
     Other      FY23 €0 / FY24 €150,029 / FY25 €246,997 / FY26 €0
   Action: excluded from pure_sales_eur; Shell tracked as shell_lubricants_eur (UMI only).
   FY23 Shell=0 and FY26 other=0 are anomalies, not “clean years”.

⚠️  CHECK 2 — SaTy filter
   Line-level SaTy % not recomputed (raw XLSX not loaded).
   Waterfall excl_saty_cr: FY23 €0 / FY24 €1,120.50 / FY25 €0 / FY26 €27,960
   FY26 split of that €27,960 vs billing-clean: ITUK €17,600 + IMG €10,000 + UNK_2686 €360.
   CR/RE total: inherited from ALLCUSTOMERS rebuild (excluded / deducted in net_gps).

⚠️  CHECK 3 — Credit note sign
   G2 lives in waterfall excl_billt (FY23 €251,947 / FY24 €1,117,640 / FY25 €708,137 / FY26 €901,342).
   Sign treatment: inherited from gps_reconcile full-clean (not re-tested on raw this pass).
   Net impact on GPS: already inside ALLCUSTOMERS net_gps.

❌  CHECK 4 — YoY consistency
   INCONSISTENT — do not trend GPS% or pure sales across years without this caveat.
   FY2023: partial year; Shell=0; other=0.
   FY2024–25: Shell + other present and material.
   FY2026: Shell present (UMI €407,942); other=0 (ITUK service/late/demurrage vanished from the extract).
   Automated gate: never compare GPS% across years without consistency — this gate FAILS.

✅  CHECK 5 — UMI/UTI split
   ALLCUSTOMERS already splits UMI vs UTI via the dedicated Israel extract. Split kept.
   UMI 125% is rejected (UTI+UMI on UMI wallet + Shell in). Warranty toggle does not produce 125%.

✅  CHECK 6 — Waterfall (network FY2026)
   Gross billing (all lines):                         €34,731,811.80
   Less: BillT (G2/RE/S1/S2):                         −€901,341.68
   Less: SaTy CR/ZDR:                                 −€27,960.00
   Less: Transport:                                   −€327,501.25
   Less: Lubricants (Shell 550xxx):                   −€407,942.16
   Less: Other (service / late / demurrage):          −€0.00          ← ANOMALY
                                                      ──────────────
   = waterfall clean (pre-surcharge-neutralisation):  €33,067,066.71
   Less: surcharge strip (ALLCUSTOMERS vs waterfall): ~€208,148
   = network pure_sales_eur (this file):              €32,858,918.54

   FY2025 waterfall (for Check 4 contrast):
   Gross €34,173,214.87 − billt €708,137.43 − saty €0 − transport €357,942.44
   − Shell €519,794.24 − other €246,996.72 = clean €32,340,344.04

CLEAN GPS REVENUE (network FY2026, this file): €32,858,918.54
  vs waterfall clean €33,067,066.71 (surcharge) vs gross €34,731,811.80
  excluded from gross to waterfall clean: €1,664,745.09 (4.8% of gross)
CONFIDENCE IN GPS FIGURE: MEDIUM
  Reason: numerator identity vs ALLCUSTOMERS is tight; Shell-on-UMI identity holds;
  Check 4 fails (FY26 other=0; FY23 partial/zero buckets); Checks 2–3 not re-run at
  line level; warranty FY2023 missing; UIO/GPS% not settled. Do not present a GPS%
  from this file to management or IML.
```

Automated gates: GPS% is not written, so the >95% gate is not triggered. The cross-year GPS% consistency gate **fails** (Check 4).

---

## Columns

| Column | Meaning |
|--------|---------|
| `fy` | Fiscal year Apr–Mar, labeled by the March-end calendar year (**FY2026 = Apr 2025–Mar 2026**). Same labels as ALLCUSTOMERS. |
| `db` | Billing canonical name (UMI, UTI, ITUK, IUK, …) — same keys as ALLCUSTOMERS |
| `payer_codes` | SAP payer(s) |
| `net_raw` | Full-clean net **before** surcharge neutralisation |
| `billing_clean_eur` | Plan/billing-clean (Shell **in**) — for filters / recon, not the canonical numerator |
| `transport_eur` | Transport excluded (0 if none in sidecar) |
| `surcharge_stripped_eur` | `net_raw` − `pure_sales_eur` |
| `shell_lubricants_eur` | Shell Rimula; UMI only where proven; 0 elsewhere in FY24–26 by network exhaustion |
| `other_excl_eur` | Service / late / demurrage; ITUK FY24–25; **0 in FY26 (anomaly)** |
| `saty_cr_excl_eur` | CR/ZDR residual vs billing-clean (credits), where proven |
| `pure_sales_eur` | **Canonical numerator** |
| `warranty_eur` | Fiscal warranty €; blank if unknown |
| `pure_sales_ex_warranty_eur` | `pure_sales_eur − warranty_eur` when warranty known (can be negative) |
| `notes` | `israel_split`, `warranty_missing`, `fy26_other_excl_zero`, `fy23_partial`, `fy23_shell_zero`, `fy23_other_excl_zero`, `shell_all_on_umi`, `other_excl_all_on_ituk`, `taxonomy_gap_vs_billing_clean`, `warranty_joined_as_RSA`, `warranty_joined_as_Greece`, `midi_non_gps_channel`, `thin_or_unmapped` |

---

## What this file is not

- Not a replacement for `gps_master.csv` (sales-review scripts still read that).
- Not a GPS% study. UIO remains provisional.
- Not a fix of the FY2026 other-exclusion hole.
- Not a live-dashboard rebase.

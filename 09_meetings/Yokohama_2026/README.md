# Yokohama 2026 — GPS extended target FY27–FY31

| File | What |
|------|------|
| `ISZE_GPS_Extended_Target_FY27_V3.3.xlsx` | Working model, FY2027 target + FY2028–FY2031 outlook (Japanese format on `Dashboard (2)`) |
| `ISZE_GPS_Extended_Target_FY27_V3.2.xlsx` | Jerome's input file (23-10-2026), unchanged |
| `GPS_FY27_Extended_Target_Masumi_v3.3.docx` | Summary for Masumi-san (22-10-2026) |
| `_build/build_v33.py` | Rebuilds V3.3 from V3.2 + repo data |

Rebuild:

```
python -I _build/build_v33.py ISZE_GPS_Extended_Target_FY27_V3.2.xlsx ^
  ../../01_data/00_derived/uio_by_market_type_year.csv ^
  ../../01_data/00_derived/gps_billing_fy_ALLCUSTOMERS.csv ^
  ISZE_GPS_Extended_Target_FY27_V3.3.xlsx
```

## What changed from V3.2 (Jerome's answers, 23-10-2026)

1. **LCV rate EUR 250** (FY26, ISZE net) → 262.50 in FY27 → +3% a year. Replaces 219.56.
2. **Vehicle numbers stay V19**, one year shifted (FY27 ← CY2026F … FY31 ← CY2030F).
3. **No cap (Jerome, 23-10-2026).** Every distributor gets the same stretch. Finland (104.9% at budget) and Ireland (100.2% after stretch) read above 100%: quote the amount, not the %. Ireland's fleet is national registration data (SIMI 2010-2025). Optional cap: `Dashboard (2)` Q1 = YES.
4. **ITUK / UTI** kept as presented for FY27.
5. **Two stretch inputs** on `Dashboard (2)`: FY27 1.8% (N1), FY28–FY31 1.0% a year (N2). Cap switch Q1 (default NO), price T1.
6. FY25/FY26 ISZE sales refreshed from the GPS-audited billing file.
7. **Distributor level (販社) filled for all 18, amounts only.** Dealer spend per vehicle as in the ITUK row (£400 / £1,000 / £1,200 × 1.12 = €448 LCV, €1,120 LD, €1,344 MD/F). FY26 actual = KPI sales to dealer. FY27 target = FY26 + ISZE stretch ÷ 0.65. FY28–31 moves with the ISZE target. No dealer share %: KPI sales to dealer run 2.2–3.7× our billing, so Norway, Denmark, Belgium, Ireland and Iceland would read 108–184%.
8. **`Inputs` sheet.** Every constant a formula uses sits there (rates, +5%, dealer GBP spend and FX, 35% margin, network BP, ITUK/UTI fleet). No calculation has a number typed into it, except Masumi-san's ITUK/UTI FY27 inputs (blue) and two cells from V3.2 left as they were (`Dashboard` col L `=G*0.33/2`, `Waterfall VP` N7). Checked by `_build/scan.py`; totals re-computed independently by `_build/indep.py` (match within EUR 900 a year: one Danish truck the Denmark tab does not count).
9. Fixes in `Dashboard (2)`: links to the old September file removed; Malta LCV row used the F-Series rate; Greece and Cyprus medium trucks were missing from the potential.

## Headline (FY27 1.8%, FY28–31 1.0%, no cap)

| | FY27 | FY28 | FY29 | FY30 | FY31 |
|---|---:|---:|---:|---:|---:|
| Target, 18 distributors (EUR M) | 34.46 | 38.25 | 42.35 | 46.81 | 51.54 |
| + customers outside the 18, flat | 2.06 | 2.06 | 2.06 | 2.06 | 2.06 |
| Network budget (PL plan row 186) | 35.28 | 37.53 | 41.53 | 46.39 | 52.10 |
| Above budget | +1.24 | +2.78 | +2.89 | +2.48 | +1.50 |

FY27 stretch EUR 1,239,483 against EUR 952,037 needed → EUR 287,446 buffer (identical to the Masumi document v3.3).
Max spend 18 distributors FY27 EUR 61,019,133 (the v3.3 document still shows 56,813,054 from the earlier rate), GPS 54.4% at budget, 56.5% after stretch.

Sensitivity on the FY28–31 input (FY27 at 1.8%): 1.8% → +3.3 to +4.3M a year above budget; 0.8% → FY31 +0.84M.
FY27 at 1.0% gives about EUR 926K, EUR 26K short of EUR 952K — so FY27 stays 1.8%.

## Open points

- Ireland reads 117% on FY26 actual sales against a fleet from national registration data: the spend-per-vehicle estimate is low for Ireland. Quote amounts only.
- Corrected CY2026 vehicle file (30-07, ~9% fewer LCV) not used: V20 is not adopted. If it is, every share goes up about 10%.
- Belgium potential counts Belgian vehicles only (IBX also serves NL / PL / LU).
- Price: plan bridge uses +2%, potential uses +5% — question 6 to Masumi-san still open.

Note: the delivered V3.3 is saved after a full recalculation (LibreOffice), so every formula cell carries its value for previews. The builder output alone has formulas without values until Excel recalculates.

## How the file is checked

| Check | What | Result (23-10-2026) |
|---|---|---|
| `Checks` sheet (live, in Excel) | 57 formula checks: waterfall closes, totals tie across sheets, every distributor's target agrees on tab / Dashboard / Dashboard (2), no share above the ceiling, no error cells | ALL OK |
| `_build/audit.py` A | 340 inputs against the repo sources: fleet V19 per segment and year, FY25/FY26 billing, BP FY27, ITUK/UTI fleet, network BP | 340 / 340 |
| `_build/audit.py` B | Every formula on the 16 distributor tabs identical to IUK (LCV) or GERMANY (mixed) | 16 / 16 |
| `_build/audit.py` C | 493 outputs recomputed independently in Python (potential, share, target, dealer potential and target, FY26–FY31) | 493 / 493 |
| `_build/audit.py` E | Every formula cell carries a value, no error cells, no external links | OK |
| Negative test | Broke a target cell and forced a stretch above the ceiling: the `Checks` sheet flagged both | Caught |

Run: `python -I _build/audit.py <builder output.xlsx> <recalculated.xlsx> <ISZE root>` → `audit_result_V3.3.json`.

**Not verifiable inside the repo** (source workbooks are not in git): KPI sales to dealer (Dashboard col Q), ITUK/UTI V4 figures, the waterfall bars. They are carried from V3.2 unchanged.
**Known, not an error:** ITUK / UTI potential differs between `Dashboard` (V4: 13.05M / 8.83M) and `Dashboard (2)` (2026 fleet: 12.54M / 8.49M). Both as presented; the targets agree.

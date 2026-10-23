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
3. **Ceiling per distributor (100%).** The stretch never pushes a share above 100%. Finland (104.9% at budget) gets no stretch.
4. **ITUK / UTI** kept as presented for FY27.
5. **Two stretch inputs** on `Dashboard (2)`: FY27 1.8% (N1), FY28–FY31 1.0% a year (N2). Ceiling Q1, price T1.
6. FY25/FY26 ISZE sales refreshed from the GPS-audited billing file.
7. Fixes in `Dashboard (2)`: links to the old September file removed; Malta LCV row used the F-Series rate; Greece and Cyprus medium trucks were missing from the potential.

## Headline (FY27 1.8%, FY28–31 1.0%)

| | FY27 | FY28 | FY29 | FY30 | FY31 |
|---|---:|---:|---:|---:|---:|
| Target, 18 distributors (EUR M) | 34.45 | 38.22 | 42.29 | 46.71 | 51.39 |
| + customers outside the 18, flat | 2.06 | 2.06 | 2.06 | 2.06 | 2.06 |
| Network budget (PL plan row 186) | 35.28 | 37.53 | 41.53 | 46.39 | 52.10 |
| Above budget | +1.23 | +2.75 | +2.83 | +2.39 | +1.36 |
| GPS share, 18 distributors | 57.3% | 58.5% | 59.7% | 60.9% | 62.1% |

FY27 stretch EUR 1,230,452 against EUR 952,037 needed → EUR 278,415 buffer.

Sensitivity on the FY28–31 input: 1.8% → +3.3 to +4.2M a year above budget, Iceland reaches 99.8%; 0.8% → FY31 only +0.2M.
FY27 at 1.0% gives EUR 923K, EUR 29K short of EUR 952K — so FY27 stays 1.8%.

## Open points

- Ireland is already at 117% on FY26 actual sales — the per-vehicle rate for Ireland is too low, not the sales too high.
- Corrected CY2026 vehicle file (30-07, ~9% fewer LCV) not used: V20 is not adopted. If it is, every share goes up about 10%.
- Belgium potential counts Belgian vehicles only (IBX also serves NL / PL / LU).
- Price: plan bridge uses +2%, potential uses +5% — question 6 to Masumi-san still open.

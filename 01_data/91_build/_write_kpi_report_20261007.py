TEXT = r'''# KPI panel exercise - 2026-10-07

Read-only work. Nothing was sent, moved, flagged or replied to in the mailbox.
New folder only: `01_data/90_INBOX/_kpi_panel_20261007/`.

## Job 1 - the two IMIT fill-rate mails

Both found. Both carry the same attachment, `Graph Fill Rate - Direct biz - ISZE 2025.xlsx` -
the numbers are in the workbook, not in the message body.

| mail | sent | sender | attachment | numbers read |
|---|---|---|---|---|
| `IMIT Fill Rate to ISZE - July 2026` | 2026-09-08 | Peeraya Sawangsaensuk IMIT | Graph Fill Rate - Direct biz - ISZE 2025.xlsx | yes |
| `IMIT Fill Rate to ISZE - April 2026` | 2026-05-26 | Peeraya Sawangsaensuk IMIT | Graph Fill Rate - Direct biz - ISZE 2025.xlsx | yes |

The April mail was not saved by the earlier run because the scan capped each
folder at 3,000-4,000 items and the mail sits past item 4,000 in the Inbox.
Re-scanning without that cap found it immediately. Both mails are plain -
two sentences, no table, no inline image.

IMIT fill rate to ISZE (sheet `ISZE Fill Rate`, row 29 "1st Fill Rate %"):

| month | Apr25 | May25 | Jun25 | Jul25 | Aug25 | Sep25 | Oct25 | Nov25 | Dec25 | Jan26 | Feb26 | Mar26 | Apr26 | May26 | Jun26 | Jul26 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1st fill rate | 76.3% | 68.0% | 81.8% | 79.7% | 80.2% | 78.5% | 82.4% | 83.1% | 76.1% | 79.6% | 81.9% | 78.6% | 75.2% | 76.0% | 69.7% | 78.3% |

The perfect-fill target in the same sheet is a flat 87%. The July sheet is the
same file re-issued with May/Jun/Jul added - April's read stops at Apr26.

Saved under `imit_fill_rate/` with `IMIT_MANIFEST.json`. The full series
(Sep25 to Jul26) was also recovered.

## Job 2 - the panel

`kpi_panel.csv` - 9,013 rows, 63 source files, 22 metrics, columns exactly as specified.

Layouts found (detected per file, not assumed):

| layout | files | description |
|---|---|---|
| flat | 68 files/sheets | metric rows in col C, month columns D..O |
| country | 1 file/sheet | same, plus a Country column D, month columns E..P - `BavoJacobs_...Isuzu OE...` (rows for BeLux / Netherlands / Poland / Shared stock) |

Sheet names are not uniform: `Checklist` in most, `2026 Checklist Monthly` /
`2025` / `2026` in the Isuzu OE and UMI/Nordic files.

Things the panel preserves rather than "cleans":

- `N/D` and `N/A` stay as literal values (a non-reporting distributor is a finding).
- Free text is kept, e.g. `No data.`, `NA combination between delivery from ISZE and from IDA to dealer`, `Isuzu Belgium provides this figure`, `262 items / 70 K Euro`, `92,5%`.
- Percentages are recorded as written - `unit` says whether the form is ratio (`0.97`) or percent (`92,5%`). Nothing was rescaled.
- Some sheets carry a second block below the monthly one (e.g. BL row 26 = annual days). Both are captured; the source file disambiguates.

Seven sheets are present but entirely blank (`JeromeVanDerPluym_20260110/0202/0302/0402`,
`..._2026_ISD`, `..._26_Greece` x2) - listed in `kpi_panel_meta.json`. Four files are not
check sheets (3 x `BL Fill Rate details`, 1 x `Graph Fill Rate`).

## Job 3 - consolidated master vs primary submissions

`master_vs_panel.csv` / `master_vs_panel.md`. Blocks in `Parts Handling`:

| block | title cell | header row | data rows | Jul-26 column |
|---|---|---|---|---|
| Days of Parts in Stock | A1 | 3 | 4-25 | AC |
| First Fill Rate | A28 | 30 | 31-52 | AC |
| Back Order Lines | A55 | 57 | 58-79 | AC |
| Parts Sales DB to DLR | A82 | 84 | 85-107 | AC |

Ireland confirmed. `AC39 = 0.99` (First Fill Rate block from A28, header 30) and
`AC66 = 20` (Back Order Lines block from A55). Both match the primary Ireland
sheet of 2026-09-03 and 2026-10-05 exactly.

Verdicts across 89 master cells:

| verdict | n |
|---|---|
| agree | 29 |
| unit diff (master in days, primary in months) | 7 |
| master blank/N-D, primary has a value | 7 |
| both non-numeric (N/A / free text) | 6 |
| not submitted in primary files | 36 |
| primary is text, master has a number | 2 |
| DISAGREE | 1 |
| source conflict | 1 |

The real disagreements:

1. The `Imotors` row is Portugal, not MIDI. Master A7 (days) and A34 (fill rate) trace to NunoMachado's Portugal April-July (2.8722/0.8455 ... 2.6208/0.8362). MIDI is master A47 (0.967) and matches Menini's MIDI sheet.
2. `Imotors` days 79 vs Portugal 2.62. Ratio about 30, so the master stores days while the primary writes months. Ireland (123 vs 4.01 = 30.7), ITUK (121 vs 3.98 = 30.4), AIOS (171 vs 5.5 = 31.1), KIMA (30 vs 1) show the same factor.
3. BL days: master 119 is the annual row 26 of BL's sheet; July MOS is 5, with 119 in a second block. Two rows in one sheet, not an error.
4. ISD and RSA: master shows `N/D` but the primary gives a value (ISD 6.38 months, First Fill 96.21, BO 48; RSA days 3.7, First Fill 0.95). The master is behind the primary file.
5. `IBX (BE LUX)` and every other IBX/Isuzu OE row is blank for July in the master, while the primary sheet of 2026-10-05 has full Mar-Sep.
6. Romania fill rate 0.978 vs 0.918. Different values; 0.978 is the 09-03 vintage, the 10-05 file says 91.80% = 0.918. The master holds the older number.

Verdict: stale, partial and partly mis-attributed - not a fair summary of what was
submitted. It is frozen at July 2026 (the Aug26 column is empty for every row)
while primary sheets run to September. 36 of 89 cells have no primary submission
behind them. At least one row (Imotors) carries another distributor's numbers, and at
least one metric (Romania fill rate) is an earlier vintage than the latest submission.

## Job 4 - coverage

See `coverage_grid.md`. Reported through July 2026: AIOS (also Nov/Dec
forward-filled), BL, Denmark, Hungary, ITUK, IUK, Iceland, Isuzu OE
(BeLux/NL/Poland/shared), Isuzu Polska (January only), KIMA, Loutsios, MIDI, Malta,
Portugal, RSA, Romania, UTI, Isuzu Nordic. Through September: BL, Iceland, IUK,
Isuzu Nordic, Portugal, ISD, Isuzu OE, Ireland (to August), and Denmark/Hungary/ITUK
where September is N/D.

Never report a real number: Greece (sheet blank) and UMI (blank). WAE has no primary
sheet at all. Finland & Baltics is `NA` for every month.

Tomoe Baumann sent a full set on 2026-09-03 and again on 2026-10-05 (26 files the
first time, 28 the second), which is why most July figures now have two independent
sources.

## Surprises, and the numbers Jerome most wants

- The consolidated master is a July snapshot presented as the August file, with no August data in it.
- `Imotors` equals Portugal in the master, and Portugal's own numbers are in months while the master stores days.
- ISD and RSA submitted real July numbers that the master shows as `N/D`.
'''

import pathlib
out = pathlib.Path(r"C:\Users\jerom\Desktop\claude\ISZE\01_data\90_INBOX\_kpi_panel_20261007\REPORT.md")
out.write_text(TEXT, encoding="utf-8")
print("wrote", out, out.stat().st_size, "bytes")

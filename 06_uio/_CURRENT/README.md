# UIO — Canonical Working Files

**Last updated:** Jul 2026
**Canonical Excel:** `ISUZU_UIO_Overview_2026.xlsx` — **v19** (Changelog sheet); no version in filename.
**Canonical Dashboard:** `02_dashboards/fleet/ISUZU_UIO_Dashboard_2026.html` (HTML renamed 2026-07-16; workbook v19)
**Previous versions:** archived in `_Archive/`.

---

## What is in this folder

| File | Purpose |
|------|---------|
| `ISUZU_UIO_Overview_2026.xlsx` | The only working UIO model. Overwrite in place or create a date-stamped copy in `_Archive/` before making changes. Version is on the Changelog sheet — not in the filename. |

---

## MIDI toggle — policy

**Default: Exclude MIDI** (set Sheet 1, cell B4 = `"Exclude MIDI"`)

⚠ **2026-07-09 check: the live file currently has B4 = `"Include"`, not `"Exclude MIDI"`.** Anyone pulling the Grand Total straight off Sheet 1 right now gets the incl.-MIDI number, not the ISZE-only default this policy calls for. Fix in the workbook (Sheet 1, cell B4) before quoting, or use the ex-MIDI column below.

MIDI Europe distributors (FR, CH, ES, IT, PL, RS) contribute ~103,768 units by 2030F (was ~92,585 in 2024 — see table below, recalculated 2026-07-09 from the live file).
Exclude for ISZE-only KPIs (action plan, Kosha reporting).
Include when analysing cross-category synergies (lubricants scale, accessory campaigns).

---

## 2026F dip — SUPERSEDED, do not use this section

⚠ **2026-07-09: this section describes a v17-era artifact that no longer exists in the live file.** Changelog entries V18-16 through V18-20 (2026-06-11) replaced the pure-decay 2026-2030 forecast with one driven by actual IMIT/CV-plan new-registration inputs. Per the Changelog itself (V18-18): *"Grand total now shows market growth instead of decline. Key 2025→2026 change: LCV +5% (was −3%)."* The −3.7% 2026F dip is gone — see the real current trajectory below. Do not repeat the old "explain the dip" line to anyone externally; it would now be actively wrong.

---

## Workbook structure (9 sheets)

1. **Cover** — scope, assumptions, FY→CY mapping
2. **1.UIO Overview** — main pivot: 40+ distributor × model-type × 1990–2030
   - B4 = MIDI toggle (`"Include"` / `"Exclude MIDI"`)
   - Row 2 = Grand Total (SUMPRODUCT)
   - Row 5 = MIDI contribution subtotal
   - U KING rows 22 + 24 (cols 2025–2030) = live-linked to Sheet 4 Section C
3. **2. Vehicle Volume** — underlying volume data
4. **3. UIO Calculation** — roll-forward worksheet
5. **4. ITUK UIO Projection** — cohort × survival model
   - Section A: SMMT actuals 2008–2024
   - Section C: 2025–2030 projection (drives Sheet 1)
   - Section D: assumptions
   - Section E: survival curves (N35/N75 from ITUK PPTX)
   - Section F: Niguri registrations
6. **Charts** — survival curve + registrations
7. **Assumptions & Mapping**
8. **Data Sources** — distributor → source mapping
9. **Changelog** — v11→v19 audit trail

---

## Key figures — pulled live from this file 2026-07-09 (supersedes everything below this line before today)

**Grand Total, Sheet 1 row 2 (SUMPRODUCT), as the file stands right now (B4 = "Include"):**

| Year | Incl. MIDI | MIDI contribution | Ex-MIDI (ISZE-only, use this for Kosha/action plan) | YoY % (incl. MIDI) |
|------|-----------:|-------------------:|------------------------------------------------------:|--------------------:|
| 2023 | 242,338 | 90,623 | 151,715 | +7.7% |
| 2024 (actual) | 252,710 | 92,585 | 160,125 | +4.3% |
| 2025E | 258,594 | 95,395 | 163,199 | +2.3% |
| 2026F | 269,314 | 96,935 | 172,379 | +4.1% |
| 2027F | 279,502 | 98,654 | 180,848 | +3.8% |
| 2028F | 289,529 | 100,411 | 189,118 | +3.6% |
| 2029F | 299,448 | 102,115 | 197,333 | +3.4% |
| 2030F | 309,125 | 103,768 | 205,357 | +3.2% |

No dip anywhere in this trajectory — steady growth every year. The old "2026F dip" table below is wrong, kept only so the history is traceable.

**ITUK Only, Sheet 4 "4. ITUK UIO Projection" row 28** — this sheet's own header still says **"V15"** internally (not V19) and the Changelog confirms it: none of the V18/V19 change entries (Portugal, Germany, UTI Israel, forecast methodology) touched Sheet 4. These numbers are genuinely current — they just haven't needed a change, so don't be alarmed that they match what you may remember from months ago:

| Year | ITUK UIO |
|------|---------:|
| 2025E | 23,068 |
| 2026F | 24,173 |
| 2027F | 25,392 |
| 2028F | 26,435 |
| 2029F | 27,363 |
| 2030F | 28,209 |

**Israel UTI parc (CV LD + MD), from V19-1/V19-2 Changelog entries:**

| Year | UTI parc |
|------|----------|
| 2024 | 10,049 |
| 2025 | 10,336 |
| 2026 | 10,760 |
| 2027 | 10,972 |

## Old "Key v17 figures" table — WRONG, superseded 2026-07-09, kept for history only

| Year | Grand Total (incl. MIDI) | ITUK Only |
|------|--------------------------|-----------|
| 2024 (actual) | 254,117 | 22,389 |
| 2025E | 260,449 | 23,068 |
| 2026F | 250,718 ⚠ dip — NO LONGER TRUE, see table above | 24,173 |
| 2027F | 253,228 | 25,392 |
| 2028F | 256,011 | 26,435 |
| 2029F | 259,165 | 27,363 |
| 2030F | 262,559 | 28,209 |

Note the ITUK column was already correct in this old table — only the Grand Total (non-ITUK markets) changed.

---

## Connections to other projects

- → PMS Coverage: ITUK gap a material amount on 22,389 DVLA base
- → Lubricants BC: UIO × service interval = lube demand model
- → AIM Opportunity Engine: Parc × Age Factor × Category Factor = Spend Index
- → Action Plan KPIs: UIO = market size denominator

---

## Next refresh triggers

- FY2026 year-end actuals (when ISZE closes, ~May–Jun 2026)
- SMMT/DVLA extract from ITUK (annual, ~Mar 2027 for CY2026 car park)
- Niguri updated internal forecast (when ITUK releases next FY forecast)

---

## Folder structure

```
UIO/
├── _CURRENT/          ← this folder — only the active working file lives here
├── _Scripts/          ← build_isuzu_uio.py (note: not updated for v17 — do not regenerate)
├── _SourceData/       ← LCV UIO Study (IMIT), UIO.xlsx source inputs
└── _Archive/          ← v8 through v16b — do not touch
```

**Build script warning:** `_Scripts/build_isuzu_uio.py` predates the current canonical (last updated Apr 2026). It has a runtime guard — running it without `--force` will abort with an explanation. Two patches must be embedded before using it: (1) 90% override fix, (2) Sheet 1 → Sheet 4 live links. Check the Changelog sheet inside the workbook for details.

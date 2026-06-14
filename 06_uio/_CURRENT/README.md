# UIO — Canonical Working Files

**Last updated:** Jun 2026
**Canonical Excel:** `ISUZU_UIO_Overview_2026.xlsx` — no version in filename; version tracked on Changelog sheet inside the file.
**Canonical Dashboard:** `ISZE/Dashboards/ISUZU_UIO_Dashboard_2026_v18.html` (HTML dashboard rename pending)
**Previous versions:** archived in `_Archive/`.

---

## What is in this folder

| File | Purpose |
|------|---------|
| `ISUZU_UIO_Overview_2026.xlsx` | The only working UIO model. Overwrite in place or create a date-stamped copy in `_Archive/` before making changes. Version is on the Changelog sheet — not in the filename. |

---

## MIDI toggle — policy

**Default: Exclude MIDI** (set Sheet 1, cell B4 = `"Exclude MIDI"`)

MIDI Europe distributors (FR, CH, ES, IT, PL, RS) contribute ~92,585 units in 2024.
Exclude for ISZE-only KPIs (action plan, Kosha reporting).
Include when analysing cross-category synergies (lubricants scale, accessory campaigns).

⚠ MIDI contribution not re-verified after v17 — confirm row 5 SUMPRODUCT before quoting externally.

---

## 2026F dip — explanation for external use

The Grand Total shows a −3.7% dip in 2026F (260,449 → 250,718). This is a genuine model output.

**Root cause:** IML backbone roll-forward for non-ITUK distributors (deregistration cohorts aging out in several markets). ITUK itself grows +4.8% in 2025→2026 per the cohort model.

**Recovery:** +1.0–1.3%/yr from 2027 onward.

Proactively explain this when sharing externally to avoid "calculation error" confusion.

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
9. **Changelog** — v11→v17 audit trail

---

## Key v17 figures

| Year | Grand Total (incl. MIDI) | ITUK Only |
|------|--------------------------|-----------|
| 2024 (actual) | 254,117 | 22,389 |
| 2025E | 260,449 | 23,068 |
| 2026F | 250,718 ⚠ dip | 24,173 |
| 2027F | 253,228 | 25,392 |
| 2028F | 256,011 | 26,435 |
| 2029F | 259,165 | 27,363 |
| 2030F | 262,559 | 28,209 |

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

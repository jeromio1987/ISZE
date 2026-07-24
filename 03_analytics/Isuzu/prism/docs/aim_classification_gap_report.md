# AIM classification gap report — 2026-07-02

**Status after this session: residual unclassified revenue is 1.6% (CY2024) / 1.8% (CY2025), down from 14.5% / 16.0%.**
Verification green after rebuild (104 pass / 0 fail, `01_data/00_derived/_verification_report.json`).

## What the "residual 5% / €1.6M" actually was

The memory figure (~€1.6M CY2024 unclassified) predated the workbook taxonomy refresh. Measured
against the current pipeline (`aim_pn_classification.csv` joined to PRISM sales, parts lines only):

| Measure | CY2024 | CY2025 |
|---|---|---|
| Parts revenue (PRISM scope) | €33.15M | €31.83M |
| Workbook placeholder classes (`Unknown`, `Unknown Review`, `Other / review`) — before fix | €4.82M (14.5%) | €5.08M (16.0%) |
| Residual after fix | €0.53M (1.6%) | €0.59M (1.8%) |

The CY2025 "~87% revenue classified" from `AIM_CY2025_Analysis.xlsx` is consistent with the
pre-fix 16% placeholder share (scope differences explain the ~1pp gap).

## What was implemented

### Rule 1 — placeholder fallback (closed ~€8.4M of 2024+2025 combined)
`modules/aim_pn_classifier.py`: workbook L1 values `Unknown` / `Unknown Review` / `Other / review`
are now treated as *not classified*. Priority becomes:
workbook real class → gap suggestion (confidence ≥ 3.0) → PR00/IE40 catalog class (only if the
catalog class is itself not a placeholder) → keep the workbook placeholder.
99.8% of the placeholder € already had a real PR00/IE40 catalog class — nothing is guessed;
an existing, documented taxonomy is used. `aim_source` records provenance per PN
(`aim_workbook` 16,148 / `pr00_catalog` 139,718 / `gap_suggestion` 196 PNs).

### Rule 2 — description-precedent suggestions (closed ~€0.4M)
New script `scripts/build_aim_gap_suggestions_precedent.py` → `aim_gap_suggestions_20260702.csv`
(replaces `aim_gap_suggestions_20260522.csv` as the newest file; the May rows are merged in
verbatim so nothing is lost). For each still-open PN it inherits the workbook class of already
classified PNs sharing the same normalized description (exact desc first, then the root before
`;`), only when one L1 holds ≥70% of the precedent pool by € with minimum support. 190 PNs,
€307K (2024+2025). Provenance is in `sug1_desc` (dominance, pool €, pool PN count) and
`validated = precedent_desc_20260702`.

### Not closed — honest residual (€1.12M over 2024+2025, 635 PNs)
Workbook says placeholder, catalog says `Other / review`, no description precedent. Top 100 PNs
carry 90% of it. These need a human call — the descriptions are readable but no in-taxonomy
precedent exists, so nothing was auto-applied.

## Top open PNs — proposed classes (NOT applied; validate before use)

Proposals below are description-based suggestions for Jerome to confirm. To apply: set
`confidence ≥ 3` (or add rows) in the newest `aim_gap_suggestions_*.csv` and rerun
`build_aim_pn_classification.py`.

| PN | Description | € 24+25 | Proposed L1 | Confidence |
|---|---|---|---|---|
| 8975536860 | BODY ASM; REAR | 83,076 | Body Exterior | high |
| 8982473951 | THROTTLE ASM; INT | 78,950 | Intake Exhaust Emission | high |
| 8974807975 | RADIO CONTROL ASM; STEREO,AM-F | 71,150 | Cabin Interior | high |
| 8974807965 | RADIO CONTROL ASM; STEREO,AM-FM | 43,276 | Cabin Interior | high |
| 8983487480 | CHAMBER; POWER | 40,129 | Brakes (air brake power chamber) | medium |
| 1476010870 | EXPANDER | 38,424 | Brakes (brake expander, CV) | medium |
| 8980537880 | BLADE; WIPER | 33,085 | Maintenance Service | high |
| 8977988660 / 8976492820 / 8977988670 / 7552283740 / 8972660360 | TRANSFER ASM | 107,295 | Driveline Axle (transfer case) | medium |
| 5876100341 / 8975568060 / 8980537900 / 5876150780 / 5876150770 / 8975568070 | BLADE; WIPER | 88,719 | Maintenance Service | high |
| 8974807974 / 8974807964 / 8974808238 | RADIO CONTROL ASM / CONTROL ASM; STEREO | 49,921 | Cabin Interior | high |
| 8976598981 / 8976598991 | COVER; RADAR | 39,908 | Body Exterior (ADAS radar cover) | medium |
| 8982482610 | ADJUSTER; VLV LASH | 11,478 | Engine | high |
| 8980435960 | CHAMBER; POWER | 10,571 | Brakes | medium |
| 7552430370 | BATTERY | 8,708 | Electrical | high |
| 8983863874 | BOLSTER; RR END,RR BODY | 8,670 | Body Exterior | medium |

Top 30 open PNs = €741K of the €1.12M. Full list: scratch output regenerable via
`build_aim_gap_suggestions_precedent.py` (prints residual) or the residual analysis in this doc's
history.

## Method notes / guardrails

- Everything is provenance-tagged (`aim_source`); no keyword guessing was added.
- CY2026 (Jan–Mar, actual billing) coverage after fix: **97.6% of clean revenue**, open residual €210K.
- Do not compare "93.5% CY2024 count-based" with "87% CY2025 revenue-weighted" with the new
  numbers above without naming the basis — three different denominators.

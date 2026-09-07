# IDS dealer ranking / dashboard — changelog (Mode B)

**Scope:** Internal notes for `04_tools/ids_dealer_ranking/` builds, MIDI packs, and IDS HTML/Excel rebuilds.  
**Not** for Mode A client HTML changelogs (those stay stripped per `isze-ids-delivery.mdc`).

Newest first. Append only.

---

## [Unreleased]

### OSM streets back on v1.5 maps (2026-09-07)

- Restored OpenStreetMap raster tiles (`tile.openstreetmap.org`, no key) under
  dealer pins. Pale pin-grid is not the product. Still v1.5 (no v1.6).

### Country packs v1.5 (2026-09-07) — same average rule as master

- New folder `09_meetings/IDS_2026_Country_Packs_v1.5/` (v1.4 left intact).
- Same extract as full-network compare: zeros / non-responders out of averages
  in every market including Italy and Switzerland; FR/ES red-marks stay.
- MIDI 4 removed on single-country packs. Leaflet inlined. Changelog still stripped.
- OPEN_*.cmd beside each HTML.

### One average rule every market (2026-09-07) — Jerome: treat all countries as Swiss

- Removed Italy + Switzerland `AVG_ALL_IN` exception in `ids_report_extract.py`.
- Every market: blank / zero / did-not-answer dealers **out of averages**, still on list + map.
- France/Spain keep Tomoe’s named red-marked list (FR 20 / ES 5).
- Full-network compare **v1.5** rebuilt. Country packs **v1.5** in a new folder
  (`IDS_2026_Country_Packs_v1.5`); v1.4 left intact.
- Notes: “Z did not answer (still on the list and map).” Italy no longer “all dealers in”.

### Section E not_scored (2026-08-15) — leave E out of scoring, record it

- Israel LCV (UMI): all 29 dealers 0/18 questions, 0/27 points, **fill not_scored**.
  Not a vehicle-sales fail. Totals restated on **A–D only** (max 253).
- Those 29 zeros are **excluded** from the network Section E average and from
  the network total (no fake fail in the 280-point mix).
- Hover on the network-average figure in **every** live IDS HTML explains the
  exclusion. Heatmap shows NS (grey), not 0% red.
- Operating headline for Israel remains **Section D (Parts)** vs the network.
- Live HTML restamped: `02_dashboards/ids/` + `09_meetings/IDS_2026_Country_Packs_v1.4/`.
  v1.3 / archive packs not rewritten.

### Full country pack v1.4 (2026-08-15) — all dealer sheets, one network average

- Authorized rebuild of **all 19 country packs** into `09_meetings/IDS_2026_Country_Packs_v1.4/`
  (Belgium, NL, LUX, DK, PL, GR, NO, HU, RO, MT, CY, UK CV, UK LCV, Portugal,
  Israel LCV, FR, IT, ES, CH). Benelux rollup not rebuilt.
- Anonymous **network average 79.0%** on every sheet (FR 20 / ES 5 red-marked out of
  averages; IT/CH all-in). Section E network 73.2% still includes UMI’s 29 zeros —
  scoring change for Israel LCV Section E is a Masumi decision, not applied here.
- Mirrored HTML → `02_dashboards/ids/`. Full-network compare rebuilt (564 dealers).
- Master zip rewritten. INDEX scope text corrected (no longer claims UK LCV / Portugal /
  Israel / MIDI are excluded).

### Belgium country pack v1.4 (2026-08-12) — corrected network averages

- Authorized rebuild: **Belgium v1.4** under `09_meetings/IDS_2026_Belgium_v1.4/`
  (does **not** overwrite `IDS_2026_Country_Packs_v1.3/Belgium`).
- Same average codepath as MIDI v1.4 / Baumann wave (`build_ids_country_packs_v13.py`
  + `ids_report_extract.py`). BE has no FR/ES red-mark exclusions.
- **National avg unchanged** ~78.5% (34 dealers). **Network avg** ~75.7% → ~79.0%
  (anonymous full-network benchmark after FR/ES reds out / IT+CH all in).
- Mirrored HTML → `02_dashboards/ids/IDS_2026_dealer_compare_Belgium.html`.
- Outlook **draft** to Jerome via `draft_ids_belgium_v14.py` (Save — not Sent).
- IBX SaTy Fill draft attach updated to prefer Belgium **v1.4** zip.

### DB feedback sheet v0.4 (2026-08-11) — DB rollup leverage OS blocks

- Generator `VERSION = v0.4` → `09_meetings/IDS_2026_DB_Feedback_Sheet_v0.4/`
  (does **not** overwrite v0.1 / v0.2 / v0.3).
- Layer C rollup is the **primary DB artefact**. New blocks:
  - **Hit list** — priority visits (below avg and/or Needs improvement; cap 12)
  - **Incomplete / not-completed lane** — FR/ES Baumann reds; other markets zeros or None
  - **Suggested DB-level next steps** — 3–5 network actions; Owner/date/proof blank
  - **Pull scorecard** — blank monthly scaffold (% visited, % closed, incomplete cleared, escalations)
- Dealer packs regenerated under v0.4 as annexes (same A/B as v0.3 content pattern).
- Mode B OS doc: `05_memory/projects/ids-db-leverage-os.md` sharpened to rollup-first.

### DB feedback sheet v0.3 (2026-08-11) — suggested next steps on exec summary

- Generator `build_db_feedback_sheet.py` → `VERSION = v0.3`, output under
  `09_meetings/IDS_2026_DB_Feedback_Sheet_v0.3/` (does **not** overwrite v0.1 / v0.2).
- Layer A exec summary: “Suggested next steps — edit in the meeting” table pre-seeded
  with 2–3 actions from the same top checklist gaps as Kaizen; Owner / Target date /
  Proof blank. Mode A English; starters only.
- Kaizen on workshop pack unchanged (still 3–5 gap-seeded rows).
- Layout: slight padding tighten so three suggestion rows still fit one A4 page.

### Locked rule (2026-07-31) — Tomoe Baumann / MIDI averages — NEVER FORGET

**On behalf of Tomoe Baumann (IMG).** Agents must apply this on every future MIDI FR/IT/ES/CH rebuild. Do not silently drop or re-include without Jerome’s explicit OK.

**Mail (exact):** 2026-07-31 08:58 — subject `Re: IDS 2026 - MIDI dealer files (Excel + HTML)`:

> red marked DLRs in the ranking list are to be excluded for the average calculation.  
> For Italy and Switzerland, all DLRs are to be included.

**Teams context (same period):** zeros / very low scores = MIDI “not completed” → better to exclude.

| Market | Rule |
|--------|------|
| **France + Spain** | Red-marked dealers (font red in her ranking attachments) → **exclude from averages** (country / network / section avgs). |
| **Italy + Switzerland** | **Keep all dealers in** averages — **including zero-score shells** (no zero-shell hygiene on IT/CH). |

**Scope from her words:** averages only. She did **not** say remove them from the dealer list / HTML.

**Canonical red-marked list (her attachments):**

- Pull folder: `01_data/90_INBOX/tomoe_ids_mail_pull/`
  - `20260731_0858_MIDI_exclude_mail_body.txt`
  - `20260731_0858_France_dealer_ranking.xlsx`
  - `20260731_0858_Spain_dealer_ranking.xlsx`
  - `20260731_0858_red_marked_dealers.json`
- **France (20):** LABESQUE VEHICULES INDUSTRIELS… (35%), CHAUMONT POIDS LOURDS… (23.21%), GARAGE PRESTIGE AUTOS SARL (17.14%), THEOBALD AUTOMOBILES S.A.S. (16.43%), ZENITH MOTORS SAS (11.07%), UTILITAIRE SERVICE S.A.S. (7.86%), plus **14 at 0%**: AUBERT DIFFUSION, AUTO CONSEIL LOCATION (ACL), BAYI TRUCKS, BEKE GASPARD, CARS 2000-1, ESSONNE POIDS LOURDS (ESPL), GARAGE AUBREE, LEFEVRE LORRAINE, LOGIC AUTOMOBILES, MANTES VEHICULES INDUSTRIELS (MVI), MDH SA, SOCIETE DES GRANDS GARAGES DU GARD, SORELOC, TRANS-SERVICES.
- **Spain (5):** CAMIONES DEL PISUERGA SA (6.79%), ESPAWAGEN SAU (0), GAURSA ARABAUTO S.L. (0), MIDI SPAIN AUTOMOCION SL (0), TALAUTO PLUS S.L. (0).

**Status 2026-08-11:** **Applied in v1.4** — `ids_report_extract.py`: FR/ES red-marked out of averages (20 / 5); **IT/CH all dealers in** (zeros included). First v1.4 build wrongly dropped IT/CH zero shells — corrected same day under authorized v1.4 rebuild. Packs: `09_meetings/IDS_2026_Country_Packs_v1.4/`. Outlook **draft** to Tomoe (not Sent) via `draft_ids_midi_v14.py`. Jerome must Send.

**Superseded 2026-09-07 (Jerome):** Italy/Switzerland all-in is **off**. Every country uses the same exclusion (zeros/blanks out of average, still on list/map). FR/ES named red-marks stay. Country packs remain v1.4; full-network compare v1.5.

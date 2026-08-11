# IDS dealer ranking / dashboard — changelog (Mode B)

**Scope:** Internal notes for `04_tools/ids_dealer_ranking/` builds, MIDI packs, and IDS HTML/Excel rebuilds.  
**Not** for Mode A client HTML changelogs (those stay stripped per `isze-ids-delivery.mdc`).

Newest first. Append only.

---

## [Unreleased]

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
| **Italy + Switzerland** | **Keep all dealers in** averages. |

**Scope from her words:** averages only. She did **not** say remove them from the dealer list / HTML. Jerome’s later plan to also drop them from list/HTML + bump **v1.4** is a **pending decision** — do **not** rebuild or ship until he says rebuild/ship and confirms list vs avg-only.

**Canonical red-marked list (her attachments):**

- Pull folder: `01_data/90_INBOX/tomoe_ids_mail_pull/`
  - `20260731_0858_MIDI_exclude_mail_body.txt`
  - `20260731_0858_France_dealer_ranking.xlsx`
  - `20260731_0858_Spain_dealer_ranking.xlsx`
  - `20260731_0858_red_marked_dealers.json`
- **France (20):** LABESQUE VEHICULES INDUSTRIELS… (35%), CHAUMONT POIDS LOURDS… (23.21%), GARAGE PRESTIGE AUTOS SARL (17.14%), THEOBALD AUTOMOBILES S.A.S. (16.43%), ZENITH MOTORS SAS (11.07%), UTILITAIRE SERVICE S.A.S. (7.86%), plus **14 at 0%**: AUBERT DIFFUSION, AUTO CONSEIL LOCATION (ACL), BAYI TRUCKS, BEKE GASPARD, CARS 2000-1, ESSONNE POIDS LOURDS (ESPL), GARAGE AUBREE, LEFEVRE LORRAINE, LOGIC AUTOMOBILES, MANTES VEHICULES INDUSTRIELS (MVI), MDH SA, SOCIETE DES GRANDS GARAGES DU GARD, SORELOC, TRANS-SERVICES.
- **Spain (5):** CAMIONES DEL PISUERGA SA (6.79%), ESPAWAGEN SAU (0), GAURSA ARABAUTO S.L. (0), MIDI SPAIN AUTOMOCION SL (0), TALAUTO PLUS S.L. (0).

**Status 2026-08-10:** Documented only. No v1.4 rebuild/ship. Workspace ranking copies under `IDS_2026/rankings/` are unmarked; always prefer Tomoe’s Jul-31 attachment copies above for the red list.

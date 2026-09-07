# EQ-HIT pull playbook (CY2025 priority)

**Mode B** · markdown only · sibling agent may be pulling live — do not block on completion.  
**Ranking SSOT:** `01_data/00_derived/eqhit_priority_ranking_cy2025.md` (+ `.csv` / top PNs).  
**Output target:** `01_data/00_derived/eqhit_extract_priority_cy2025.csv`

---

## Rules

1. Follow ranking **EUR gap order** (largest unpaid expected demand first).
2. **Skip `oil_filter`** in the live pull (already well-covered offline / not the attack priority).
3. **Clutch + brake first** — ranks 1–4 and related brake/clutch rows before filters/other.
4. Full catalogue accepted (Jerome) — ranking is **sequence**, not a top-20 cut.
5. Append-only to the extract CSV; do not overwrite V1 league files.
6. No browser work in the solo shadow track; this playbook is for the browser/EQ-HIT session agent.

---

## Pull order (skip oil_filter)

| Step | Rank | Category | Why first |
|-----:|-----:|----------|-----------|
| 1 | 1 | `clutch_disc` | Largest EUR gap |
| 2 | 2 | `brake_shoe` | Brake cluster |
| 3 | 3 | `brake_pad` | Brake cluster |
| 4 | 4 | `clutch_pressure_plate` | Clutch cluster |
| 5 | 5 | `blower_filter` | Next gap |
| 6 | 6 | `brake_rotor` | Brake remainder |
| 7 | 7 | `fuel_filter` | Filters (non-oil) |
| 8 | 8 | `clutch_kit` | Clutch remainder |
| 9 | 9 | `air_filter` | Filters |
| 10 | 10 | `clutch_booster` | Clutch remainder |
| 11 | 11 | `release_bearing` | Clutch remainder |
| 12 | 12 | `urea_filter` | Filters |
| — | 13 | `oil_filter` | **SKIP** |
| 13 | 14 | `pilot_bearing` | Last |

Seed PNs: `eqhit_priority_top_pns_cy2025.csv` (top billed EUR per category). Expand from EQ-HIT applicability, not only the seed list.

---

## Session steps

1. Open EQ-HIT with network/session already authenticated (sibling browser agent).
2. For each category in the table above (skip oil_filter):
   - Start from seed PNs in the ranking MD / top-PN CSV.
   - Pull **vehicle / engine applicability** EQ-HIT exposes (chassis / model / engine where available).
   - Prefer rows that map to LCV Trooper / D-Max RT / D-Max RG when tagged; else keep bucket unknown.
3. Write/append rows to `eqhit_extract_priority_cy2025.csv` with the schema below.
4. After each category, note `rows_added` + `status=ok|partial|blocked` in the extract `notes` or a one-line ledger comment.
5. When a category is partial, leave `status=partial` and continue — do not stall Monday asks.

---

## Output schema — `eqhit_extract_priority_cy2025.csv`

| Column | Type | Notes |
|--------|------|-------|
| `pull_date` | ISO date | Session day |
| `rank` | int | From ranking (skip 13 / oil_filter) |
| `pms_category` | str | e.g. `clutch_disc` |
| `part_number` | str | 10-digit Isuzu PN |
| `description` | str | EQ-HIT / seed description |
| `vehicle_model` | str | Free text from EQ-HIT |
| `engine_code` | str | If exposed |
| `chassis_family` | str | e.g. RT56 / RG21 / UBS / unknown |
| `lcv_generation` | str | `trooper` / `dmax_rt` / `dmax_rg` / `unknown` |
| `bucket` | str | `lcv` / `cv_std` / `f_series` / `unknown` |
| `applicable` | bool/str | `true` / `false` / `unknown` |
| `eqhit_source` | str | screen / export label |
| `status` | str | `ok` / `partial` / `blocked` / `skipped_oil_filter` |
| `notes` | str | Short; no billing dump |

One row per PN × applicability slice (do not collapse engines into one row if EQ-HIT splits them).

---

## Done when

- Clutch + brake categories (ranks 1–4, 6, 8, 10–11) have at least seed-PN coverage with applicability filled or explicitly `unknown`.
- Extract CSV exists under `01_data/00_derived/` and is append-safe for later categories.
- Shadow Opt1 continues on BVP fitment until extract lands; no V1 cutover.

---

## Pointers

| Artefact | Path |
|----------|------|
| Ranking MD | `01_data/00_derived/eqhit_priority_ranking_cy2025.md` |
| Ranking CSV | `01_data/00_derived/eqhit_priority_ranking_cy2025.csv` |
| Seed PNs | `01_data/00_derived/eqhit_priority_top_pns_cy2025.csv` |
| Extract (target) | `01_data/00_derived/eqhit_extract_priority_cy2025.csv` |
| V2 config | `03_analytics/Isuzu/prism/data/gps_pms_v2_config.yaml` |
| V2 status spine | `00_docs/agent/GPS_PMS_V2_SPEC.md` |

# GPS file lineage — do not fork the wrong workbook

**Last updated:** 2026-07-03  
**Audience:** agents, build scripts, anyone touching GPS planning files.

---

## Canonical roles (memorise this)

| Artifact | Path | Role |
|----------|------|------|
| **GPS planning workbook** | `01_data/ISZE_GPS_v5.xlsx` | **The** network GPS plan: actuals FY24–26, projection FY27–30, Kosha gap, DB rates. **Update in place via `04_tools/build_gps_v5.py`.** |
| **Reviewed BP FY27 loader** | `01_data/91_build/load_bp_fy27.py` | Single source for per-DB VP turnover (reviewed 24 Apr 2026). Writes `bp_fy27_reviewed.json`. |
| **Kickback + ITUK stretch** | `01_data/91_build/ISZE_GPS_Kickback_Stretch_Proposal_FY27.xlsx` | Tab 1: **9 kickback DBs** (+1.5pp). Tab 2: **other DBs — ITUK excluded**. Tab **ITUK FY27**: Target Study only. Built by `build_gps_kickback_proposal.py`. |
| **GPS calculator (audit engine)** | `01_data/ISZE_GPS_Calculator.xlsx` / `ISZE_GPS_Calculator_v9.xlsx` | Per-DB GPS% audit tool. Built by `91_build/build_gps_v9.py`. **Not the planning workbook.** |
| **Kosha capture workbooks** | `01_data/14_dashboards/kosha/ISZE_GPS_Kosha_v4*.xlsx` | Historical net/gross toggle + Option A inputs for v5 builder. |

---

## What went wrong (2026-07-03)

`ISZE_GPS_v6.xlsx` was created by **`91_build/build_gps_v6.py`**, which **clones `ISZE_GPS_Calculator_v9.xlsx`** (calculator lineage) and patches BP + stretch tabs.

That is **not** an update to `ISZE_GPS_v5.xlsx`. The user’s planning model lives in **v5** (Kosha merge + projection tabs). Forking v9 → “v6” looked like a version bump but was the **wrong product**.

### Rule

> **Never introduce `ISZE_GPS_v6.xlsx` (or v7, …) as the planning successor to v5 unless explicitly requested.**  
> BP / stretch changes belong in **`build_gps_v5.py`** (plan) and/or **`build_gps_kickback_proposal.py`** (stretch proposal).

---

## Where FY27 BP lives

| Layer | FY27 BP source |
|-------|----------------|
| v5 projection FY27 column | **Reviewed per-DB** from `budget_per_DB_reviewed_24042026.xlsx` via `load_bp_fy27.py` |
| v5 FY28–30 | Network Kosha totals + **Option A** uniform X (until multi-year reviewed BP exists) |
| Kickback stretch | Reviewed BP base + ITUK study / +pp kickback rules (`build_gps_kickback_proposal.py`) |
| v9 calculator | Per-DB audit; may lag v5 — do not treat as plan of record |

Network total reviewed FY27: **€35.284M** (`VP_NETWORK_TOTAL_EUR` in `load_bp_fy27.py`).

---

## Build order (safe)

```text
1. load_bp_fy27.py          → bp_fy27_reviewed.json
2. build_gps_v5.py          → ISZE_GPS_v5.xlsx   ← planning
3. build_gps_kickback_proposal.py → stretch proposal xlsx
4. build_gps_v9.py          → calculator only (if audit refresh needed)
```

**Do not** run `build_gps_v6.py` for planning updates — script exits with deprecation notice.

---

## v5 DB name ↔ reviewed BP GPS code

Used in `04_tools/build_gps_v5.py` (`V5_TO_GPS`):

| v5 tab name | GPS / BP code |
|-------------|---------------|
| ISD | GERMANY |
| IBX | BELGIUM |
| Imotors | PORTUGAL |
| RSA | NORWAY |
| Sverige | SWEDEN |
| AutoWallis | HUNGARY |
| ROM Auto | ROMANIA |
| Loutsios | CYPRUS |
| Nordic FI | FINLAND |
| Danmark | DENMARK |
| BL Iceland | ICELAND |
| GasanZammit | MALTA |
| Ireland | IRELAND |
| Greece | GREECE |
| ITUK, IUK, UTI, UMI | same |
| MIDI | non-GPS channel — no reviewed row; Option A retained |

---

## Archived mistake

`01_data/_archive/ISZE_GPS_v6_mistaken_fork_2026-07-03.xlsx` — calculator fork, **not** canonical. Keep for audit only.

---

## Agent checklist before touching GPS files

1. Is the user asking for **planning** (network view, Kosha gap, FY27–30)? → **v5 only**
2. Is it **kickback / ITUK stretch**? → kickback proposal workbook
3. Is it **per-DB GPS% audit**? → v9 calculator
4. Did you almost save-as `v6`? → **Stop.** Extend `build_gps_v5.py` instead.
5. FY27 BP always from **`load_bp_fy27.py`** — never Kosha €35.3M sales-share proxy.
6. **ITUK never on kickback or Other DBs tabs** — only **ITUK FY27** + v5 network plan. See `.cursor/rules/isze-gps-ituk.mdc`.

---

## Post-mortem — 2026-07-03 (GPS / ITUK session)

### Errors made

| # | Error | Impact | Fix |
|---|--------|--------|-----|
| 1 | **v6 fork** as planning successor | Wrong workbook lineage | Archived; rule in this file |
| 2 | **N35 @ €739** in v5 (LD bucket) | ITUK wallet ~€18M vs ~€13M | `build_gps_v5.py` + `gps_v9_loaders` |
| 3 | **£17M vs €13M** not explained early | User confusion “which total is right?” | Both right — different layers (dealer GBP vs ISZE EUR) |
| 4 | **ITUK on Other DBs tab** | Treated like Cyprus/Malta “small DB” with kickback-style columns | Removed from tab 2; **ITUK FY27** only |
| 5 | **HTML “ITUK excluded, no stretch”** while xlsx had stretch | Contradictory messaging | HTML + subtitles aligned |
| 6 | **Over-focused on €295.68 vs €296** | Noise vs real €739 bug | Document €296 as canonical rounded rate |

### Correct mental model

```
Kickback file                    Planning (v5)
─────────────                    ─────────────
Tab 1: 9 DBs (+1.5pp)            All DBs incl. ITUK
Tab 2: other GPS (no ITUK)       Class-weighted max spend
Tab ITUK FY27: Target Study      ITUK: N35/N75/F buckets
HTML: kickback only              Dashboard + projection
```

### Agent rule file

`.cursor/rules/isze-gps-ituk.mdc` — apply when touching `build_gps*.py`, `gps_v9_loaders.py`, or GPS xlsx.

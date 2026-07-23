# ISZE workspace cleanup plan

**Date:** 2026-06-12  
**Goal:** One clear mental model — edit in one place, archive the rest, stop agents (and humans) opening the wrong copy.

**Start here:** `INDEX.md` → this file when tidying. Do **not** bulk-move without checking scheduled tasks and deploy scripts.

---

## The problem (why it feels messy)

| Layer | What you have today | Risk |
|-------|---------------------|------|
| **4 UI stacks** | HTML, Streamlit, Evidence, Dash | Same KPIs in four places — maintenance drift |
| **3 HTML deploy trees** | `02_dashboards/` (source) + `07_deploy/Master Dashboard/` + `publish-site/` | Editing the wrong folder gets overwritten on sync |
| **2 PRISM analytics copies** | `03_analytics/Isuzu/prism/` + `isze-prism-analytics/` (archived) | Triple maintenance — **resolved 2026-06-13** |
| **Context mirror** | `07_deploy/Master Dashboard/context/` | Auto-synced MD copy — not a second source of truth |
| **Legacy + experiments** | mockups, old tender scraper, 44 MB TSV, 468 MB txt dump | Agents glob into noise |
| **Many maps** | `INDEX.md`, `ISZE_Tooling_Map_*`, `AUDIT_2026-05.md`, `ROADMAP.md` files | Correct but overlapping |

---

## Target layout (numbered — implemented 2026-06-13)

```
ISZE/                           ← $env:ISZE_ROOT · contract: paths.yaml
├── INDEX.md                    ← only entry point for agents
├── AGENTS.md / CLAUDE.md / paths.yaml
├── 01_data/                    ← raw + derived + dashboards/*.json
├── 02_dashboards/              ← HTML source of truth
├── 03_analytics/Isuzu/prism/   ← pipeline + Streamlit + Evidence + Dash
├── 04_tools/                   ← scrapers, SPA, isze-tools
├── 05_memory/                  ← durable project facts + briefs
├── 06_uio/                     ← UIO workbook + scripts
├── 07_deploy/                  ← Master Dashboard + publish-site (deploy only)
├── 08_gpt/                     ← GPT Enterprise knowledge pack
└── 90_archive/ / 91_legacy/    ← cold storage
```

Everything else either **feeds** this tree or **lives in `90_archive/` / `91_legacy/`**.

**Deploy-side compatibility:** GitHub Pages HTML still uses `fetch('../Data/...')` — intentional until coordinated deploy migration.

---

## Archive zone: `_archive/`

**Path:** `ISZE/_archive/`  
**Rule:** moved items keep their original relative path inside `_archive/` so you can trace provenance.

Example: `prism/mockups/` → `_archive/prism_mockups/mockups/`

| Subfolder | Intended contents |
|-----------|-------------------|
| `_archive/prism_mockups/` | HTML UI experiments (v01–v10) |
| `_archive/Tools_tender_scraper_legacy/` | Old `Tools/tender scraper/` |
| `_archive/isze-tools-github/` | Stale GitHub mirror |
| `_archive/duplicate_repos/` | `isze-prism-analytics/` after merging launchers into monorepo |
| `_archive/legacy_data/` | `sales_detailed*.tsv`, oversize txt dumps |
| `_archive/versioned_docs/` | Superseded pptx/xlsx (v1–v2 when v3 is canonical) |

**Implications of archiving:**

- **Scheduled Windows tasks** under `Documents\Claude\Scheduled\` may still point at old paths — grep before moving.
- **Git / GitHub Pages:** `_archive/` should stay out of public deploy repos or be clearly non-production.
- **Agents:** add `_archive/**` to `.cursorignore` (already listed in `INDEX.md` for some paths).
- **Recovery:** nothing deleted — only moved. Restore = move back.

---

## Phased cleanup (recommended order)

### Phase 0 — Documentation only (done / safe)

- [x] `INDEX.md` lists Evidence + Dash + launchers
- [x] `PROJECT_HUB.html` lists all four UI stacks
- [x] `ISZE_Tooling_Map` updated with Evidence/Dash section
- [x] This cleanup plan

**Implication:** zero runtime risk.

### Phase 1 — Quick wins (low risk, ~1 hour)

| Action | Move to | Implication | Status |
|--------|---------|-------------|--------|
| `prism/mockups/v01–v10*.html` | `90_archive/prism_mockups/mockups/` | Stub README left at old path | ✅ 2026-07-16 |
| `prism/run-prism.ps1` (duplicate) | deleted — use `run_prism.ps1` (port **8503**) | Wrong-port 8501 launcher removed | ✅ 2026-07-16 |
| `new files/iszj_parts_master (1).txt` (468 MB) | `_archive/legacy_data/` or outside repo | Frees disk + agent noise | already gone |
| `prism/data/UIO_v13.xlsx` | `_archive/versioned_docs/` | Confirm nothing reads v13 | already gone |
| `ISZE_GPS_PMS_Conf26_v1/v2.pptx` | `_archive/versioned_docs/` | Keep v3 at root | leave |

**Implication:** broken links only if something still referenced moved paths — grep first.

### Phase 1b — HTML share surface (done 2026-07-16)

| Action | Result |
|--------|--------|
| Primary external UI | Already decided: **GitHub Pages HTML** (`UI_STACK.md`) — unchanged |
| Canonical GPS | `02_dashboards/fleet/ISZE_GPS_Dashboard.html` |
| Canonical UIO | `02_dashboards/fleet/ISUZU_UIO_Dashboard_2026.html` |
| `_v9` / `_v18` HTML | Thin redirects only |
| Orphan `gps/ISZE_GPS_Dashboard_v9.html` | → `02_dashboards/_archive/gps_orphan_2026-07-16/` |
| Hub / nav / manifest / `gps_reconcile` DASHBOARDS | Point at canonical fleet GPS |
| `build_gps_dashboards.py` | Writes canonical HTML + redirect stub (no dual full copy) |

---

## Before / after — what an outsider should open

| Intent | BEFORE (wrong / ambiguous) | AFTER (open this) |
|--------|----------------------------|-------------------|
| External share hub | Any of 4 UI stacks | `02_dashboards/hub/MASTER_DASHBOARD.html` → sync → GitHub Pages |
| Project tile hub | `PROJECT_HUB` tiles → `_v9` / `_v18` | Same hub → `fleet/ISZE_GPS_Dashboard.html` · `fleet/ISUZU_UIO_Dashboard_2026.html` |
| GPS numbers | `gps/ISZE_GPS_Dashboard_v9.html` (stale orphan) **or** fleet `_v9` | **Only** `fleet/ISZE_GPS_Dashboard.html` |
| UIO fleet | `…_v18.html` | `fleet/ISUZU_UIO_Dashboard_2026.html` |
| Day-to-day analysis | — | PRISM `run_prism.ps1` · **8503** (not `run-prism.ps1`) |
| Verify before quote | — | `01_data/derived/_verification_report.json` green |

### Archived this pass

| Item | Where |
|------|-------|
| `prism/mockups/*` (11 files) | `90_archive/prism_mockups/mockups/` |
| `gps/ISZE_GPS_Dashboard_v9.html` | `02_dashboards/_archive/gps_orphan_2026-07-16/` |
| `run-prism.ps1` | deleted |

### What breaks if you rename further (do **not** yet)

| Rename | Breaks |
|--------|--------|
| `gps_v9_snapshot.json` → only `gps_snapshot.json` | `build_gps_v9.py`, `gps_reconcile.py` dual-compare, `build_gps_integrity_audit.py`, memo Fix 5 sequence |
| Drop `uio_v18_gps.json` alias | Older scripts until all callers use `uio_v19_gps.json` / `uio_gps.json` |
| Flatten deploy URL paths | GitHub Pages `fetch('../Data/...')` contract |
| Archive Evidence / Dash / ISZE_Dashboard | Needs Jerome Phase-3 call — ops pages may lack PRISM equivalents |

### Sequenced PR plan (remaining — risky)

1. **PR-A (HTML done):** this pass — share surface + redirects + reconciler list.
2. **PR-B (GPS snapshot primary):** after go-ahead on `GPS_RECONCILE_MEMO_2026-07-16.md` Fix 1–5 order: echarts self-contain → rebuild dashboards → copy/align `gps_snapshot.json` ← `gps_v9_snapshot.json` → then flip writers to unversioned primary.
3. **PR-C (UIO JSON alias retire):** drop `uio_v18_gps.json` write once grep shows zero readers.
4. **PR-D (Phase 3 UI):** Jerome decides ISZE_Dashboard merge timeline; only then archive Evidence/Dash overlap.

**Not done this pass:** sync_to_deploys / GitHub Pages publish, GPS memo rebuild, ISZE_Dashboard merge.

### Phase 2 — Dedupe deploy mirrors (medium risk)

- [x] `isze-prism-analytics/` → `_archive/duplicate_repos/` (2026-06-13)
- [x] `Master Dashboard/prism-analytics/` → `_archive/duplicate_repos/` (2026-06-13)
- [ ] Delete stale `02_dashboards/*.json` if sync no longer needs them

**Implication:**

- `sync_to_deploys.ps1` must remain the only path to Pages/Netlify.
- If `isze-prism-analytics` is a **separate Git repo**, archive the local copy here but keep the remote if you still deploy Evidence from it.

### Phase 3 — Consolidate UI stacks (strategic, 1–2 weeks)

Pick **one primary** analytics UI for day-to-day work:

| Stack | Keep if… | Archive if… |
|-------|----------|-------------|
| **Streamlit PRISM** | You need filters, PDF export, decision models | — |
| **Evidence** | You want shareable static BI, SQL-native boards | Overlap with Streamlit pages you never open |
| **Dash** | Offset Insights interactivity | Evidence `offset-insights.md` covers same data |
| **ISZE_Dashboard** | Ops pages not yet in PRISM | After merge into PRISM |

**Implication:** archiving a UI stack does **not** remove derived CSVs — only the front-end. Pipeline stays one spine (`01_data/derived/`).

### Phase 4 — Map consolidation (done 2026-06-13)

- [x] `INDEX.md` slim boot + `docs/REFERENCE.md` extended map
- [x] `docs/MAPS.md` + `docs/MAP_REGISTRY.yaml` (three-tier + machine registry)
- [x] `docs/roadmaps/` hub — HTML, scrapers, GPS, tools
- [x] `README.md` merged with sync guide; `README_SYNC.md` → stub
- [x] `docs/agent/AI_STACK.md` tier protocol extracted from full AI stack memo
- [x] `CANONICAL.md` wired into INDEX + context whitelist
- [x] `05_memory/briefs/` — consolidated weekly/analyst briefs
- [x] `03_analytics/Isuzu/pms-pilot/` — moved from `Isuzu/PMS project/`
- [x] `Isuzu/*.html.bak` → `_archive/legacy_html/`
- [x] `05_memory/context/isuzu.md` → merged into `05_memory/glossary.md`
- [x] Domain roadmap stubs at old paths

**Implication:** fewer files for agents to read; old paths resolve via stubs.

---

## What must NOT be archived

| Path | Why |
|------|-----|
| `01_data/derived/` | Pipeline output — all UIs depend on it |
| `01_data/raw/sales/` | Source billing (never in git/chat) |
| `06_uio/_CURRENT/` | Canonical UIO workbook |
| `02_dashboards/` | HTML source |
| `07_deploy/Master Dashboard/`, `publish-site/` | Deploy targets (mirrors, not archive) |
| `07_deploy/Master Dashboard/context/` | Auto-synced — regenerated by `sync_context_to_github.ps1` |
| `05_memory/projects/*.md` | Agent durable memory |
| `03_analytics/Isuzu/prism/scripts/` | Build + verify pipeline |
| Scheduled skill paths | External to repo — use `$env:ISZE_ROOT` |

---

## One-page “where do I work?”

| I want to… | Open / run |
|------------|------------|
| Edit a published dashboard | `02_dashboards/*.html` → `sync_to_deploys.ps1` |
| Explore KPIs interactively | `03_analytics/Isuzu/prism/run_prism.ps1` (8503) |
| SQL/Markdown BI boards | `03_analytics/Isuzu/prism/run_evidence.ps1` (3000) |
| Offset Insights charts | `03_analytics/Isuzu/prism/run_dash.ps1` (8050) |
| Hub navigation | `02_dashboards/hub/MASTER_DASHBOARD.html` |
| Verify numbers before quoting | `01_data/derived/_verification_report.json` (green only) |
| Archive old stuff | `90_archive/` per table above |

---

## Decision needed from Jerome

Before Phase 2–3, confirm:

1. ~~**Is `isze-prism-analytics/` still a separate git remote you deploy?**~~ Local copy archived 2026-06-13; remote unchanged if still used.
2. ~~**Primary UI for external sharing:** static Evidence build vs GitHub Pages HTML?~~ **Decided 2026-06-13:** HTML (GitHub Pages). Evidence = internal. See `docs/UI_STACK.md`.
3. **ISZE_Dashboard merge:** timeline to fold into PRISM or keep as ops sandbox?

### Phase 2 workspace (done 2026-06-13)

- [x] `GPT_VectorStore/` → `_archive/GPT_VectorStore/` (stub at root)
- [x] `isze-deploy/` → `_archive/isze-deploy/` (stale Apr 2026 HTML)
- [x] Prive trip: source=`gents_trip_video`, deploy=`gents_trip_netlify`, sync script + zips archived
- [x] UI stack decision recorded in `docs/UI_STACK.md`

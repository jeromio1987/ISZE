# ISZE dashboards and tools

**Agents:** [`../INDEX.md`](../INDEX.md) → [`ROUTING.yaml`](ROUTING.yaml) → [`../AGENTS.md`](../AGENTS.md).

**Humans:** start at [HUMAN_ONBOARDING.md](HUMAN_ONBOARDING.md) for onboarding; programme status in [`ISZE_ROADMAP.md`](ISZE_ROADMAP.md). Map overview in [`MAPS.md`](MAPS.md).

**Holiday / other laptop:** [`HOLIDAY_LAPTOP.md`](HOLIDAY_LAPTOP.md) — clone `ISZE` only for work (PRISM is inside the monorepo).

---

## Daily workflow

| I want to… | Open / run |
|------------|------------|
| Explore KPIs | `03_analytics/Isuzu/prism/run_prism.ps1` (8503) |
| Edit a published dashboard | `02_dashboards/` → `02_dashboards/sync_to_deploys.ps1` |
| Verify numbers before quoting | `01_data/derived/_verification_report.json` (green only) |
| Monthly sales refresh | [`RUNBOOK_MONTHLY_REFRESH.md`](RUNBOOK_MONTHLY_REFRESH.md) |
| Check what's next | [`ISZE_ROADMAP.md`](ISZE_ROADMAP.md) |

---

## Deploy

**GitHub Pages** publishes `07_deploy/Master Dashboard/`.

1. Edit **`02_dashboards/`** (HTML source of truth).
2. Run **`02_dashboards/sync_to_deploys.ps1`** → refreshes deploy mirrors.
3. JSON feeds: **`01_data/dashboards/*.json`** only.

Do not edit deploy mirrors directly — they are overwritten on sync.

---

## Data layer (`01_data/`)

See **`01_data/DATA_MANIFEST.md`** for paths, phase pipeline, and GPT-safe flags.

| Subfolder | Contents |
|-----------|----------|
| `raw/sales/` | CY billing extracts (local only) |
| `derived/` | `sales_fact.parquet` + PRISM CSVs |
| `dashboards/` | `isze_data.json`, `tender_data.json` |
| `gpt_safe/` | Files safe for GPT Enterprise upload |
| `_INBOX/` | Drop zone for new exports |

Pipeline build: `03_analytics/Isuzu/prism/scripts/run_pipeline_and_verify.ps1`

---

## GitHub context mirror

Selected markdown syncs to **`07_deploy/Master Dashboard/context/`** → GitHub repo `isze-dashboard`.

| Step | Action |
|------|--------|
| Edit | Canonical MD at ISZE root + numbered folders — never edit deploy `context/` |
| Whitelist | `00_docs/context_sync_whitelist.txt` |
| Sync | `02_dashboards/sync_context_to_github.ps1` or `.cmd` |

**Live dashboards:** https://jeromio1987.github.io/isze-dashboard/

**PRISM code:** separate repo [jeromio1987/PRISM](https://github.com/jeromio1987/PRISM).

---

## Repo layout

```
ISZE/
├── INDEX.md, AGENTS.md, FACTS.md, paths.yaml   ← bootstrap
├── 00_docs/ … 09_meetings/                       ← numbered folders
├── 90_archive/, 91_legacy/                       ← cold storage
```

See [`ISZE_Cleanup_Plan.md`](ISZE_Cleanup_Plan.md) for archive policy.

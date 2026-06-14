# ISZE — Human onboarding

**Audience:** Jerome's successor, contractor, or future-you after time away  
**Last updated:** 2026-06-13  
**Agents:** start at [`INDEX.md`](../INDEX.md) → [`ROUTING.yaml`](ROUTING.yaml) → [`AGENTS.md`](../AGENTS.md) — not this file.

---

## 1. What this workspace is (60 seconds)

ISZE is a **local-first analytics workspace** for Isuzu Motors Europe vehicle parts sales: SAP billing → Excel Power Query → parquet/CSVs → PRISM Python → static HTML dashboards on GitHub Pages.

| Concept | Meaning |
|---------|---------|
| **Workspace root** | `$env:ISZE_ROOT` (default `C:\Users\jerom\Desktop\claude\ISZE`) |
| **Folder contract** | [`paths.yaml`](../paths.yaml) — numbered folders `00_docs/` … `09_meetings/` |
| **Quantitative spine** | `01_data/derived/` — all UIs read from here |
| **External share** | Static HTML via GitHub Pages (`02_dashboards/` → sync → `07_deploy/`) |

Personal satellites (recovery check-in, private notes) live outside ISZE under `Documents\Claude\Scheduled\` — see [AUTOMATION_REGISTER.md](AUTOMATION_REGISTER.md).

---

## 2. Where truth lives

| Question | Go here first |
|----------|----------------|
| Can I quote this KPI externally? | Green `01_data/derived/_verification_report.json` → `metrics_snapshot.json` → [`FACTS.md`](../FACTS.md) |
| How is this metric defined? | `03_analytics/Isuzu/prism/docs/metric_dictionary.md` |
| What column is this? | `01_data/DATA_DICTIONARY.md` |
| What file is on disk? | `01_data/DATA_MANIFEST.md` |
| Why did we choose X? | [`DECISIONS.md`](../DECISIONS.md) |
| What changed structurally? | [`CHANGELOG.md`](../CHANGELOG.md) |
| Which job runs when? | [AUTOMATION_REGISTER.md](AUTOMATION_REGISTER.md) |

**Rule:** Memory (`05_memory/`) and GPT pack (`08_gpt/`) are **views** — they never override KPIs. If a number conflicts with `FACTS.md`, fix the other copy.

---

## 3. The monthly ritual (overview)

Full steps: [RUNBOOK_MONTHLY_REFRESH.md](RUNBOOK_MONTHLY_REFRESH.md)

```
SAP export → 01_data/_INBOX/ → raw/sales/
    → Excel Phase 1–3 Power Query
    → sales_fact.parquet + phase CSVs
    → PRISM build + verify (0 fail)
    → FACTS.md if intentional drift
    → dashboard JSON → optional HTML sync
    → GPT pack (month-end)
```

**Bus-factor warning:** Excel Power-Query refresh clicks are not yet fully documented — Jerome must complete § Step 2–3 in the runbook.

---

## 4. Daily / weekly / monthly tasks

| Cadence | Task | Doc / script |
|---------|------|--------------|
| Daily | Explore KPIs interactively | `03_analytics/Isuzu/prism/run_prism.ps1` (**8503**) |
| Daily | Edit published dashboard | `02_dashboards/` → `sync_to_deploys.ps1` |
| Weekly | Intelligence brief | `isze-weekly-intelligence-brief` → `05_memory/briefs/` |
| Weekly | Tender scrape | `isze-weekly-tender-scrape` → `01_data/dashboards/tender_data.json` |
| Weekly | KS price scrape | `isze-weekly-ks-scrape` |
| Weekly | Scraper health (propose-only) | `isze-scraper-healthcheck-autofix` |
| Weekly | Memory hygiene | `isze-memory-review` |
| Monday | Dashboard freshness | `isze-dashboard-freshness-check` |
| Monthly | Autodoc refresh reminder | `autodoc-monthly-refresh` |
| Monthly | Pricing basket check | `isze-pricing-basket-monitor` |
| Monthly | AIM classification check | `isze-aim-classification-refresh` |
| Monthly | UIO staleness alert | `isze-uio-staleness-alert` |
| Monthly | GPT Enterprise upload | `08_gpt/` + [UPLOAD_STATUS.md](../08_gpt/UPLOAD_STATUS.md) |

---

## 5. UI stacks (which tool when)

From [UI_STACK.md](UI_STACK.md):

| Role | Stack | When |
|------|-------|------|
| **External / email links** | Static HTML → GitHub Pages | Default shareable URL |
| **Day-to-day analysis** | Streamlit PRISM (:8503) | Filters, decision models, PDF |
| **Internal SQL boards** | Evidence (:3000) | Deep dives — not public face |
| **Sandbox** | Dash (:8050) | Offset Insights experiments |
| **Legacy ops** | ISZE_Dashboard | Until merged into PRISM |

One spine (`01_data/derived/`). UI choice is presentation only.

---

## 6. What never to do

- Edit `07_deploy/` mirrors by hand — they are regenerated on sync.
- Commit or paste `01_data/raw/sales/*` line-level billing into chat, GPT, or git.
- Quote capture %, GPS, or BVP mix without green verify.
- Run production pipeline changes, UIO promotion, or scheduled-skill edits without Jerome ([AGENTS.md](../AGENTS.md)).
- Write weekly intel briefs to `07_deploy/` (publish risk to GitHub Pages).

---

## 7. Escalation & ownership

| Area | Owner | Ask Jerome before |
|------|-------|-------------------|
| Excel Phase 1–3 models | Jerome | Changing PQ logic or export paths |
| UIO workbook promotion | Jerome | `config.py` PRISM_BETA toggle |
| New unattended scheduled jobs | Jerome | Any auto-apply Edit job |
| GPT knowledge upload | Jerome | New files or figure changes |
| Deploy URL migration | Jerome | Changing `fetch('../Data/...')` contract |
| Raw billing ingest | Jerome | New CY file or SAP schema change |

---

## 8. First week checklist

- [ ] Read this file + `01_data/DATA_MANIFEST.md` + `03_analytics/Isuzu/prism/ARCHITECTURE.md`
- [ ] Run verify-only: read `01_data/derived/_verification_report.md` (do not rebuild unless asked)
- [ ] Open PRISM locally (`run_prism.bat` or `run_prism.ps1`)
- [ ] Trace one KPI: `FACTS.md` → derived CSV → PRISM page
- [ ] Review [AUTOMATION_REGISTER.md](AUTOMATION_REGISTER.md) open items
- [ ] Open hub: `02_dashboards/hub/MASTER_DASHBOARD.html`

---

## 9. Related docs

- [RUNBOOK_MONTHLY_REFRESH.md](RUNBOOK_MONTHLY_REFRESH.md) — W1 Excel PQ → verify → publish
- [AUTOMATION_REGISTER.md](AUTOMATION_REGISTER.md) — 12 scheduled jobs
- [DECISIONS.md](../DECISIONS.md) — architecture & policy log
- [CHANGELOG.md](../CHANGELOG.md) — structural changes
- [REFERENCE.md](REFERENCE.md) — full doc map
- [00_docs/README.md](README.md) — daily workflow shortcuts

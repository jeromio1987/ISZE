# ISZE decision log (append-only)

**Format:** Newest at top. Do not edit past entries — supersede with a new entry referencing the superseded date.

**Related:** [CHANGELOG.md](CHANGELOG.md) · [00_docs/AUTOMATION_REGISTER.md](00_docs/AUTOMATION_REGISTER.md) · [AGENTS.md](AGENTS.md)

---

## 2026-06-13 — ISZE root .gitignore policy approved

**Status:** Accepted  
**Context:** Root `.gitignore` was a placeholder (md-only). Git versioning implementation plan (`audit-export/git-versioning-implementation-plan.md`) defined tier-0 exclusions (raw billing, models, deploy mirror, archives).  
**Decision:** Replace placeholder with the full root `.gitignore` from the implementation plan §3. Track docs, code, governance artifacts, and verification JSON only. Never track `01_data/raw/**`, Excel living models, `07_deploy/**`, `90_archive/**`, `91_legacy/**`.  
**Alternatives considered:** Track derived parquet/CSVs (rejected — regenerable, large, PN-level detail).  
**Consequences:** Run `04_tools/workspace/git_preflight.ps1` before first commit; optional pre-commit hook.  
**Docs updated:** `.gitignore`, `04_tools/workspace/git_preflight.ps1`, `CHANGELOG.md`.

---

## 2026-06-13 — PRISM stays a git submodule (not monorepo merge)

**Status:** Accepted  
**Context:** `03_analytics/Isuzu/prism/` is a nested repo (`jeromio1987/prism`). Archived duplicate `isze-prism-analytics` lives in `90_archive/`. Root Git init requires explicit nested-repo policy.  
**Decision:** Keep **`jeromio1987/prism` as a git submodule** at ISZE root init. Do not merge PRISM into root monorepo or delete `prism/.git` without a migration plan. `90_archive/duplicate_repos/` remains ignored.  
**Alternatives considered:** Full monorepo merge (deferred — loses independent PRISM remote history and deploy cadence).  
**Consequences:** After `git init`, run `git submodule add https://github.com/jeromio1987/prism.git 03_analytics/Isuzu/prism` when wiring remote (resolve existing `.git` if needed). Root tracks submodule pointer only.  
**Docs updated:** `DECISIONS.md`, `.gitignore`, `00_docs/RUNBOOK_MONTHLY_REFRESH.md` rollback table.

---

## 2026-06-13 — Deploy repo visibility check (manual confirmation pending)

**Status:** Open — agent pre-check done  
**Context:** `07_deploy/Master Dashboard/` → `jeromio1987/isze-dashboard.git`. Secrets sweep flagged aggregate JSON on GitHub Pages as potential public exposure.  
**Agent check (2026-06-13):** Unauthenticated GitHub API returns **404** for `jeromio1987/isze-dashboard` and `jeromio1987/prism`; default `*.github.io` URLs also **404**. Consistent with **private repos** and/or Pages not enabled at default paths — not proof of privacy.  
**Decision:** Treat deploy repo as **separate publish surface** — fully gitignored at ISZE root. Jerome must confirm visibility in GitHub → Settings → Danger Zone / Pages before assuming data exposure level.  
**Manual action:** Revoke old PAT in `90_archive/root_files/` (see `audit-export/secrets-sweep-report.md`) — agent scan found **no token patterns** in non-archive ISZE paths.  
**Docs updated:** This entry.

---

## 2026-06-13 — Unattended scraper auto-fix is propose-only

**Status:** Accepted  
**Context:** `isze-scraper-healthcheck-autofix` runs unattended on a schedule. Auto-applying code patches to scrapers without human review risks breaking production ingest or publishing stale data.  
**Decision:** The healthcheck job may **detect** staleness and **propose** patches (diff/report only). It must **never** auto-apply edits to scraper scripts or publish outputs without Jerome review.  
**Alternatives considered:** Full auto-fix with rollback; manual-only checks with no scheduled job.  
**Consequences:** Scheduled job output is `04_tools/scraper_health_report.md` (+ optional diff). Jerome reviews before any patch is applied. Path preflight aborts if required scripts missing.  
**Docs updated:** [00_docs/AUTOMATION_REGISTER.md](00_docs/AUTOMATION_REGISTER.md), [00_docs/agent/NOTES.md](00_docs/agent/NOTES.md), audit-export `scheduled-path-fix-report.md`.

---

## 2026-06-13 — Deploy-side Data/ paths are compatibility paths (for now)

**Status:** Accepted  
**Context:** GitHub Pages HTML uses `fetch('../Data/...')` and deploy-side `Projects/` URLs. Local source moved to numbered folders (`01_data/`, `03_analytics/`). `sync_to_deploys.ps1` rewrites paths on publish.  
**Decision:** Deploy-side `Data/` and `Projects/` remain **compatibility paths** for published runtime URLs. Agents and local edits use numbered canonical paths only. Never edit `07_deploy/` as source.  
**Alternatives considered:** Rewrite all HTML fetch URLs to numbered paths (deferred — breaks live URLs without coordinated deploy).  
**Consequences:** Document both local source (`01_data/dashboards/`) and deploy fetch target when describing dashboard JSON. Path consolidation Batch 2 preserved deploy rewrites.  
**Docs updated:** [AGENTS.md](AGENTS.md), [00_docs/UI_STACK.md](00_docs/UI_STACK.md), [CHANGELOG.md](CHANGELOG.md) § 2026-06-13.

---

## 2026-06-13 — 07_deploy is generated mirror only

**Status:** Accepted  
**Context:** `07_deploy/Master Dashboard/` and `publish-site/` are synced from `02_dashboards/` and whitelist context docs. Agents were reading deploy-side context mirror and treating it as editable source.  
**Decision:** `07_deploy/` is **generated only**. Edit `02_dashboards/` + run `sync_to_deploys.ps1`; edit bootstrap/numbered MD + run `sync_context_to_github.ps1`. Never hand-edit `07_deploy/Master Dashboard/context/`.  
**Alternatives considered:** Make deploy repo the source of truth (rejected — splits edit workflow).  
**Consequences:** `.cursorignore` hides deploy context from Cursor index. Weekly intel brief must not write to `07_deploy/` (publish risk).  
**Docs updated:** [INDEX.md](INDEX.md), [AGENTS.md](AGENTS.md), [00_docs/ROUTING.yaml](00_docs/ROUTING.yaml) global_ignore.

---

## 2026-06-13 — Verify-before-quote is mandatory

**Status:** Accepted  
**Context:** KPIs appear in HTML, memory, GPT pack, and correspondence. Legacy PMS denominators and pre-PRISM captures persist in archived docs.  
**Decision:** No agent or human may quote capture %, GPS, BVP mix, or headline figures without green `01_data/derived/_verification_report.json` → `01_data/derived/metrics_snapshot.json` → [FACTS.md](FACTS.md). Formulas: `03_analytics/Isuzu/prism/docs/metric_dictionary.md`.  
**Alternatives considered:** Trust memory or GPT pack as KPI source (rejected).  
**Consequences:** Pipeline changes require `isze-verify-pipeline` skill or `run_pipeline_and_verify.ps1` before citing numbers. Memory and `08_gpt/` are views — never override KPIs.  
**Docs updated:** [AGENTS.md](AGENTS.md), [INDEX.md](INDEX.md).

---

## 2026-06-13 — 01_data/derived is the quantitative spine

**Status:** Accepted  
**Context:** Multiple UIs (PRISM, Evidence, Dash, HTML) and JSON builders consume analytics outputs. A single derived layer prevents divergent KPI definitions.  
**Decision:** `01_data/derived/` (CSVs, parquet, verification artifacts) is the **quantitative spine**. All UIs read derived outputs; UI choice is presentation only (`00_docs/UI_STACK.md`).  
**Alternatives considered:** Per-UI derived caches (rejected — drift risk).  
**Consequences:** Build scripts write to `01_data/derived/`; dashboard JSON in `01_data/dashboards/`; HTML reads JSON via deploy compatibility paths.  
**Docs updated:** [00_docs/UI_STACK.md](00_docs/UI_STACK.md), [03_analytics/Isuzu/prism/ARCHITECTURE.md](03_analytics/Isuzu/prism/ARCHITECTURE.md).

---

## 2026-06-13 — paths.yaml is the folder contract

**Status:** Accepted  
**Context:** Pre-reorg layout used inconsistent names (`Data/`, `Projects/`, `Tools/`, `memory/`). Hardcoded paths broke after reorg.  
**Decision:** [`paths.yaml`](paths.yaml) at ISZE root is the **folder contract**. PRISM reads via `config.py`; non-PRISM Python uses `04_tools/_shared/paths.py` or `04_tools/workspace/isze_paths.py`; PowerShell uses `04_tools/workspace/isze_root.ps1`. Use `$env:ISZE_ROOT` + numbered folders in new docs and skills.  
**Alternatives considered:** Environment-only path config (rejected — not self-documenting in repo).  
**Consequences:** New folders require `paths.yaml` update + `INDEX.md` + `CHANGELOG.md` entry.  
**Docs updated:** [paths.yaml](paths.yaml), [INDEX.md](INDEX.md), [CHANGELOG.md](CHANGELOG.md).

---

## 2026-06-13 — Numbered folder layout is canonical

**Status:** Accepted  
**Context:** 2026-06-13 workspace reorg consolidated top-level sprawl into numbered folders (`00_docs/` … `09_meetings/`, `90_archive/`, `91_legacy/`).  
**Decision:** Numbered folders are the **canonical local layout**. Legacy names (`Data/`, `Dashboards/`, `Projects/`, `Tools/`, `memory/`, `UIO/`, `GPT_Enterprise/`) are deprecated for local edits; deploy-side `Data/` remains a compatibility exception (see above).  
**Alternatives considered:** Keep semantic names without numbers (rejected — sort order and agent routing benefit).  
**Consequences:** Tier-1 docs, skills, and scripts use numbered paths. Path consolidation Batches 1–3 completed 2026-06-13.  
**Docs updated:** [INDEX.md](INDEX.md), [CHANGELOG.md](CHANGELOG.md), audit-export path-consolidation reports.

---

## 2026-06-13 — ISZE remains local-first file-based analytics monolith

**Status:** Accepted  
**Context:** ISZE is a solo-operator analytics workspace: Excel Power Query → parquet → PRISM Python → derived CSVs → HTML/PRISM/Evidence. No central database or multi-tenant service.  
**Decision:** ISZE stays a **local-first, file-based analytics monolith** on Jerome's machine. GitHub Pages publishes selected HTML/JSON; scheduled Claude jobs live outside the repo under `Documents\Claude\Scheduled\`.  
**Alternatives considered:** Cloud warehouse + BI tool (deferred); full git monorepo (open — see documentation-rebuild-plan open questions).  
**Consequences:** Monthly refresh is file-copy + script driven. Automation register indexes external scheduled skills. Raw billing never leaves `01_data/raw/sales/` into chat or GPT.  
**Docs updated:** [00_docs/REFERENCE.md](00_docs/REFERENCE.md), [01_data/DATA_MANIFEST.md](01_data/DATA_MANIFEST.md).

---

## 2026-06-13 — Primary external UI is HTML (GitHub Pages)

**Status:** Accepted  
**Source:** [00_docs/UI_STACK.md](00_docs/UI_STACK.md)  
**Decision:** Static HTML (`02_dashboards/` → sync → GitHub Pages) is the default external share surface. PRISM is day-to-day analysis; Evidence is internal SQL boards; Dash is sandbox only.  
**Consequences:** Do not rebuild the same KPI in HTML and Evidence unless HTML is the published export of that view.

---

## 2026-06-02 — PMS service frequency 0.5/yr (not 1.5)

**Status:** Accepted  
**Source:** `03_analytics/Isuzu/prism/docs/metric_dictionary.md`, `ARCHITECTURE.md`  
**Decision:** PMS expected-quantity denominator uses **0.5 services/year** per UIO, not legacy 1.5× multiplier.  
**Consequences:** Do not cite legacy single-PN / 1.5×UIO denominators from old HTML or `91_legacy/` without PRISM check.

---

## Open — ISZE_Dashboard merge timeline

**Status:** Open  
**Source:** [00_docs/UI_STACK.md](00_docs/UI_STACK.md), [00_docs/ISZE_Cleanup_Plan.md](00_docs/ISZE_Cleanup_Plan.md)  
**Question:** Timeline to fold legacy Streamlit ops sandbox into PRISM, or keep indefinitely?

---

## Open — latest_weekly_brief.txt publish target

**Status:** Open  
**Source:** audit-export `scheduled-path-fix-report.md`  
**Question:** Internal `05_memory/briefs/latest_weekly_brief.txt` vs disabled output vs deploy path? Writing to `07_deploy/` would publish internal intel to GitHub Pages.

# Teach-skills drafts (Claude Desktop)

Draft skill bodies for Jérôme to encode via **Claude Desktop → Record a skill**, or by pasting into **Settings → Custom skills**.

These are **not** scheduled jobs. They do not run on their own. Live scheduled ISZE automations live under `Documents/Claude/Scheduled/` (see `ISZE/00_docs/agent/NOTES.md`).

## Drafts

| Folder | Purpose |
|--------|---------|
| `scraper-triage/` | Weekly review of scraper health report + optional patch diff under `04_tools/` |
| `dashboard-qa/` | Visual QA for GPS/ISZE HTML dashboards under `02_dashboards/` |
| `mypens-release-checklist/` | Pre-release checks for myPENS web + mobile (Next.js / Expo / Supabase) |

## How to encode

1. Open the `SKILL.md` in the folder you want.
2. In Claude Desktop: **Record a skill** (or create a custom skill manually).
3. Paste the body; keep the YAML `name` and `description` — they drive when Claude picks the skill.
4. Refine triggers, allowlists, and verifier thresholds from your own habits; these drafts are starting points.

## Path conventions

- **ISZE:** `$env:ISZE_ROOT` + numbered folders (`04_tools/`, `02_dashboards/`, …). See `ISZE/paths.yaml` and `ISZE/AGENTS.md`.
- **myPENS:** `Projects/mypens/` (web) and `Projects/mypens/mypens-mobile/` (Expo). Junction `mypens/` at workspace root points to the same tree.

## Model tier

All three drafts specify **Model tier: CHEAP** — routine checklists and triage, not frontier planning.

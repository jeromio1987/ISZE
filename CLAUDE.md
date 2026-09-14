# Claude — ISZE workspace

Same rules as Cursor. **Start:** [`INDEX.md`](INDEX.md) → [`00_docs/ROUTING.yaml`](00_docs/ROUTING.yaml) → [`AGENTS.md`](AGENTS.md). Chat overviews to Jerome: `.cursor/rules/jerome-brief-plain.mdc` (his working English; no agent OS; Spain / MIDI is not his book).

- Do not load `01_data/raw/sales/*.XLSX` (or any line-level billing) into context; use parquet / derived CSVs.
- **New / unsorted files go to `01_data/90_INBOX/` only** — never dump into `01_data/` root. Sort per `01_data/DATA_MANIFEST.md` §0–§1.
- Numbers: green `01_data/00_derived/_verification_report.json` → `metrics_snapshot.json` → `FACTS.md` wins over decks/memory/GPT.

**Claude Desktop (standalone) users:** paste `00_docs/CLAUDE_DESKTOP_ONBOARDING.md` into the Project's custom instructions so the app boots from the same maps. That paste includes the external IML language rule (no “IML v7” / “Model B” / personal names in shared decks).

## Dynamic workflows (Claude Code)

| Command | What |
|---------|------|
| `/dashboard-html-audit` | Fan-out HTML safety/path audit under `02_dashboards/` + independent verifier (default max 20) |

```
cd ISZE
claude
/dashboard-html-audit
# or: /dashboard-html-audit with maxFiles 20 under 02_dashboards/sales
/workflows
```

Never graph P0–P5 KPI builds or load `01_data/raw/sales/*.XLSX`. Anchors stay: green `_verification_report.json` → `metrics_snapshot.json` → `FACTS.md`.

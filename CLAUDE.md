# Claude — ISZE workspace

Same rules as Cursor. **Start:** [`INDEX.md`](INDEX.md) → [`00_docs/ROUTING.yaml`](00_docs/ROUTING.yaml) → [`AGENTS.md`](AGENTS.md). Chat overviews to Jerome: `.cursor/rules/jerome-brief-plain.mdc` (his working English; sales to dealer / %GM; Spain / MIDI is not his book).

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

## Rules Claude loads (the same files Cursor loads)

@AGENTS.md
@.cursor/rules/isze-best-chart.mdc
@.cursor/rules/isze-boardroom-deck-process.mdc
@.cursor/rules/isze-dashboards.mdc
@.cursor/rules/isze-db-sales-review.mdc
@.cursor/rules/isze-exec-aftersales-paper.mdc
@.cursor/rules/isze-external-iml-language.mdc
@.cursor/rules/isze-gaps-need-context.mdc
@.cursor/rules/isze-gps-ituk.mdc
@.cursor/rules/isze-html-openable.mdc
@.cursor/rules/isze-ids-delivery.mdc
@.cursor/rules/isze-israel-uti-umi.mdc
@.cursor/rules/isze-no-ship-without-ok.mdc
@.cursor/rules/isze-nordics-keys-closed.mdc
@.cursor/rules/isze-open-on-his-pc.mdc
@.cursor/rules/isze-pms-sales-is-sales.mdc
@.cursor/rules/isze-pricing-no-street-ui.mdc
@.cursor/rules/isze-prism.mdc
@.cursor/rules/isze-scope-lock.mdc
@.cursor/rules/isze-ship-gate.mdc
@.cursor/rules/isze-spoken-labels.mdc
@.cursor/rules/isze-tender.mdc
@.cursor/rules/isze-verify-rendered-output.mdc
@.cursor/rules/isze-workspace.mdc
@.cursor/rules/jerome-brief-plain.mdc
@.cursor/rules/jerome-talk-clear.mdc

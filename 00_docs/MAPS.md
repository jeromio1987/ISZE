# ISZE — which map when

**Agent sync:** 2026-06-13 · Registry: `MAP_REGISTRY.yaml`

```
                    ┌─────────────┐
                    │  INDEX.md   │  ← always start (paths only)
                    └──────┬──────┘
                           │
              ┌────────────┼────────────┐
              ▼            ▼            ▼
     ROUTING.yaml     AGENTS.md    CANONICAL.md
     (task → files)   (rules)      (00_docs/)
              │
              ▼
     REFERENCE.md  (topic → doc, if no task key fits)
              │
     ┌────────┴────────┐
     ▼                 ▼
agent/NOTES.md    roadmaps/*.md
                  ISZE_ROADMAP.md (hub)
```

All paths above are under **`00_docs/`** unless noted as ISZE root.

## Tier 1 — Bootstrap (every session)

| Map | Read when |
|-----|-----------|
| `INDEX.md` (root) | First file — canonical paths, no globbing |
| `00_docs/ROUTING.yaml` | Task type known — open only listed paths |
| `AGENTS.md` (root) | Rules: numbers, deploy, data safety |

## Tier 2 — Reference (depth when needed)

| Map | Read when |
|-----|-----------|
| `00_docs/REFERENCE.md` | No ROUTING task fits; topic lookup |
| `00_docs/CANONICAL.md` | Which filename is authoritative; pending renames |
| `00_docs/MAPS.md` | This file — navigation confusion |
| `00_docs/MAP_REGISTRY.yaml` | Machine index of all maps |
| `00_docs/agent/NOTES.md` | Scheduled tasks, decision-model caveats |
| `00_docs/agent/AI_STACK.md` | Claude vs GPT routing, tier protocol |

## Tier 3 — Domain (one domain only)

| Map | Domain |
|-----|--------|
| `00_docs/ISZE_ROADMAP.md` | Programme hub — links to all roadmaps |
| `00_docs/roadmaps/html.md` | Static HTML dashboards |
| `00_docs/roadmaps/scrapers.md` | Tender, Autodoc, KS, discount |
| `00_docs/roadmaps/gps.md` | GPS / fig-key / AIM integration |
| `00_docs/roadmaps/tools.md` | Jarvis, isze-tools, IDS ranking |

## Tier 4 — Memory & data (topic-specific)

| Map | When |
|-----|------|
| `05_memory/projects/*.md` | Programme status, open questions |
| `05_memory/glossary.md` | Terms |
| `01_data/DATA_MANIFEST.md` | File registry, ingest |
| `03_analytics/Isuzu/prism/docs/metric_dictionary.md` | Metric formulas (edit only) |

**Numbers:** green `01_data/derived/_verification_report.json` → `metrics_snapshot.json` → `FACTS.md`

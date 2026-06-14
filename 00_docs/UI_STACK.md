# ISZE UI stack — decision record

**Decided:** 2026-06-13 · **Owner:** Jerome

---

## Primary external share: **HTML (GitHub Pages)**

| Role | Stack | When to use |
|------|-------|-------------|
| **External / ITUK / IML / email links** | Static HTML `02_dashboards/` → sync → GitHub Pages | Default for anything shareable by URL |
| **Day-to-day analysis** | Streamlit PRISM (`run_prism.ps1` · 8503) | Filters, decision models, PDF export |
| **Internal SQL-native boards** | Evidence (`run_evidence.ps1` · 3000) | Deep dives, SQL boards — not the public face |
| **Sandbox interactivity** | Dash (`run_dash.ps1` · 8050) | Offset Insights experiments only |
| **Legacy ops** | ISZE_Dashboard | Until merged into PRISM — no new pages |

**Rule:** One spine (`01_data/derived/`). UI choice is presentation only. Do not rebuild the same KPI in HTML *and* Evidence unless HTML is the published export of that view.

**Deploy-side compatibility:** Published HTML uses `fetch('../Data/...')` URLs — these are GitHub Pages runtime paths, not local source paths. Local JSON lives in `01_data/dashboards/`; `sync_to_deploys.ps1` rewrites to deploy-side `Data/` on publish.

---

## Evidence vs HTML (resolved)

| Question | Decision |
|----------|----------|
| Primary external UI | **GitHub Pages HTML** — already deployed, shareable, no local server |
| Evidence role | **Internal / workshop** — rebuild static HTML when a view is ready to publish |
| Dash role | **Keep** for Offset Insights until ported or retired |
| ISZE_Dashboard | **Sandbox** — fold into PRISM when ops pages have PRISM equivalents |

---

## Workflows

```
Pipeline → 01_data/derived/
              ├─→ PRISM (explore, verify, decision models)
              ├─→ build_isze_dashboard_json.py → 01_data/dashboards/*.json
              └─→ 02_dashboards/*.html → sync_to_deploys.ps1 → 07_deploy/ → GitHub Pages
```

Evidence reads the same derived CSVs via `sync_evidence_derived.py` — **does not** replace HTML deploy.

---

## Hub reference

`02_dashboards/hub/MASTER_DASHBOARD.html` → tab **Stacks** reflects this decision.

Registry: `MAP_REGISTRY.yaml` · Cleanup: `ISZE_Cleanup_Plan.md`

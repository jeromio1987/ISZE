# ISZE Dashboards — HTML source

**Hub (browser):** open `hub/PROJECT_HUB.html` locally, or run sync and use GitHub Pages.

**Deploy:** flat URLs (`/MASTER_DASHBOARD.html`) — source is grouped below; `sync_to_deploys.ps1` flattens on copy. JSON comes from `01_data/14_dashboards/` (alias `01_data/dashboards/`). `02_dashboards/Data` is a junction to `01_data` so local `../Data/dashboards/` links keep working.

**Machine list:** `manifest.yaml` (regenerated from disk 2026-08-13) · Programme: `../00_docs/roadmaps/html.md`

| Folder | Dashboards |
|--------|------------|
| **hub/** | PROJECT_HUB, MASTER_DASHBOARD, index, AI Operations Explorer |
| **sales/** | AIM, Competitiveness, Sell-out, Monthly Sales, SPA, Part-groups, UTI replenishment |
| **pricing/** | Live pricing, engine readiness, history, proposals |
| **fleet/** | UIO, GPS canonical, ZEV Golden Window, Plan 2030, FY2026 Year End |
| **gps/** | Kickback proposal (Network SPU / Target Study are stubs → fleet GPS) |
| **ids/** | IDS 2026 dealer compare (network + country packs) |
| **ops/** | Tender Monitor, Tools Legal Map, AI Tools, Commercial Model |
| **md_pack/** | MD pack FY27–FY28 |
| **side/** | PROPERTIQ |
| **_composable/** | PRISM map (front door) + master desk (internal / customer) |
| **_archive/** | Superseded versions (not deployed) |

```powershell
.\sync_to_deploys.ps1          # flatten → 07_deploy/Master Dashboard + publish-site
.\sync_context_to_github.cmd   # context mirror (from this folder)
```

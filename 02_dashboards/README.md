# ISZE Dashboards — HTML source

**Hub (browser):** open `hub/PROJECT_HUB.html` locally, or run sync and use GitHub Pages.

**Deploy:** flat URLs (`/MASTER_DASHBOARD.html`) — source is grouped below; `sync_to_deploys.ps1` flattens on copy.

| Folder | Dashboards |
|--------|------------|
| **hub/** | PROJECT_HUB, MASTER_DASHBOARD, index, AI Operations Explorer |
| **sales/** | AIM, Competitiveness, Sell-out (×2), Monthly Sales, SPA Run Rate |
| **fleet/** | UIO v18, ZEV Golden Window, Plan 2030, FY2026 Year End |
| **gps/** | GPS v9, Target Study redirect, Network SPU |
| **ops/** | Tender Monitor, Tools Legal Map, AI Tools Overview |
| **side/** | PROPERTIQ |
| **_archive/** | Superseded versions (not deployed) |

Machine list: `manifest.yaml` · Programme: `../00_docs/roadmaps/html.md`

```powershell
.\sync_to_deploys.ps1          # flatten → 07_deploy/Master Dashboard + publish-site
.\sync_context_to_github.cmd   # context mirror (from this folder)
```

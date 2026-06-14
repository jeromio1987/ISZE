# Workspace maintenance scripts

Run from ISZE root or any folder (scripts resolve `..\..\` as ISZE root).

| Script | Purpose |
|--------|---------|
| `reorganize_layout.ps1` | Apply numbered folder layout (`paths.yaml`) |
| `delete_phases.ps1` | Phases A–D cleanup (stubs, cache, duplicate TSV, Evidence deps) |
| `delete_stubs.cmd` | Remove locked empty `Dashboards/` / `Projects/` after closing Cursor |

```powershell
powershell -ExecutionPolicy Bypass -File "04_tools\workspace\reorganize_layout.ps1"
powershell -ExecutionPolicy Bypass -File "04_tools\workspace\delete_phases.ps1"
04_tools\workspace\delete_stubs.cmd
```

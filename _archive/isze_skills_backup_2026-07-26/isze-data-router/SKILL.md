---
name: isze-data-router
description: >
  Automatically route any file Jerome uploads to the correct ISZE folder without him specifying where.
  Triggers when a file is uploaded or mentioned without an explicit destination — especially for:
  UIO workbooks (ISUZU_UIO_Overview, UIO_v*.xlsx), SAP billing extracts (CY20*.XLSX), price lists
  (PR00, IE40, BP FY), dealer sell-out data (UTI PartSales, ITUK pivot), KPI/Action Plan files,
  GPS/Eucon competitor data, AIM/PRISM data, parts catalog (BVP), Phase models, lubricant data,
  tender/scraper outputs. Use whenever Jerome says "here is the new data", "I have a new file",
  or uploads something without naming the target path.
---

# ISZE Data Router

When Jerome uploads or names a file without specifying where it goes, determine the correct destination and file it — no clarifying questions unless genuinely ambiguous.

## Decision process

1. **Match filename** against the routing table in `references/routing-table.md`
2. **If ambiguous**: read the first sheet of the file (column headers + 3 rows) to confirm type
3. **State the destination** + any side-effects (archiving old version, PRISM copy, README update)
4. **Execute** immediately — copy/move the file, run any side-effect steps
5. **Report**: one-line confirmation per action taken

## When to ask (rare)

Ask only if:
- Two routing rules match with equal confidence and the destinations conflict
- The file appears to overwrite an existing file of the same name but a different apparent purpose
- The action is irreversible and the routing confidence is <80%

Otherwise, file it and say what you did.

## Side-effect rules (apply automatically, do not skip)

| Trigger | Required side-effect |
|---------|---------------------|
| New UIO workbook with higher version (vN > v18) | Move old `_CURRENT/` xlsx to `_Archive/`; copy to `Projects/Isuzu/prism/data/UIO_v{N}.xlsx`; update `UIO/_CURRENT/README.md` canonical line and version table; update `isze-uio-staleness-alert` scheduled task prompt (v18 → vN) |
| New SAP billing year file (CY20XX.XLSX) | Drop to `Data/_INBOX/` first; confirm with Jerome before moving to `raw/sales/` if a same-year file already exists |
| New KPI Master | Check for existing file in `Data/planning/` — if present, move old to `Data/planning/_archive/` before filing new |
| New Action Plan | Same archive-first rule as KPI Master |

## Root path

All paths are relative to: `C:\Users\jerom\Desktop\claude\ISZE\`

## Routing table

→ Full routing table: `references/routing-table.md`

Read the routing table before filing any file. It contains filename patterns, folder destinations, version handling rules, and notes per file type.

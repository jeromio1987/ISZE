# UMI Sales Review — retro 2026-08-12

**Status:** Locked lesson. Do not repeat.

## What went wrong (root causes)

1. **UTI blended into UMI** — `load_sales` filtered by payer name `UNIVERSAL MOTORS ISRAEL LTD` only. That name covers sold-to **1797 (UMI)** and **1799 (UTI)**. Story became fake boom (+318% commercial) while PBI showed −14%.
2. **Narrated before reconcile** — Built shared takeaways from contaminated CY H1 without proving Apr–Jun vs Power BI monthals.
3. **IBX pattern copy** — Excluded Filters / Best>100% / orders / SaTy GPS framing from IBX without UMI-specific Jerome OK.
4. **internal on shared** — SaTy notes with sold-to / export / blank-% jargon.
5. **Stale rebuild** — PPTX rebuilt on old `_summary.json` after loader intent changed.
6. **Shell** — `5500*` left UNCLASSIFIED / buried; later forced to “Shell lubricants”.
7. **Deep-dive zeros** — brake pads showed €0 from `billing_qty` vs `billed_qty`.

## Corrections that stuck

- `common.py` `load_sales`: when `sold_to` set, filter Sold-to; Apr+ use export CSV by Sold_to (PBI-aligned).
- PMS: never plot Best market if best > 100%.
- PBI slide: skip orders when profile says so.
- SaTy: customer = coded SOR/VOR only; GPS relevance yes/no.
- IDS Israel = UMI network only (UTI ≠ UMI rule already existed — still violated via sales blend).

## Prevention artefacts (same day)

| Artefact | Path |
|----------|------|
| Rule | `.cursor/rules/isze-db-sales-review.mdc` |
| Skill | `.cursor/skills/isze-db-sales-review/SKILL.md` |
| Gate script | `.cursor/skills/isze-db-sales-review/scripts/qa_deck_gate.py` |
| Hooks | `.cursor/hooks.json` + `db-sales-review-*.mjs` |

## Customer truth (UMI 1797-only, after fix)

- Official PBI Apr–Jul FY27: sales ~€875K, −14% vs PY (lock from profile).
- Apr–Jun SAP ≈ PBI (~€644K).
- Gross H1 mild decline; commercial +; Shell `5500*` spike then quiet / on hold.

## Do not

- Average UTI+UMI for IDS-linked or “Israel” shared slides.
- Lead with commercial boom while PBI is down.
- Copy another DB’s exclude list without an explicit ask.

---
name: isze-db-sales-review
description: >-
  Build and QA ISZE distributor Sales Review decks (shared + deep dive). Use when
  rebuilding IBX/UMI/Hungary/etc packs, editing db_sales_review, PBI slides, PMS
  Best bars, SaTy/GPS notes, sold_to Israel UMI≠UTI, or after loader changes.
---

# ISZE DB Sales Review

## When to use

Any `build_parts_analysis.py` / `build_deck.py` / `build_full_deck.py` work, or shared critique of a `09_meetings/*_Sales_Review_*` PPTX.

## Mandatory pipeline

1. Read profile in `04_tools/db_sales_review/db_profiles.yaml`.
2. If `sold_to` is set → billing **must** be sold-to filtered (never payer-only for Israel).
3. `python build_parts_analysis.py --db <KEY>`
4. Run gate: `python .cursor/skills/isze-db-sales-review/scripts/qa_deck_gate.py --db <KEY>`
5. Only if gate green: `python build_full_deck.py --db <KEY>`
6. If canonical PPTX locked → use `*_share.pptx`; tell Jerome.

## Gate checklist (fail closed)

| Check | Fail if |
|-------|---------|
| Sold-to | Profile has `sold_to` but Apr–Jun gross matches payer-blended total (±5%) |
| PBI align | `pbi.sales` months exist and SAP month totals differ by >€2K |
| SaTy note | Contains `sold-to`, `export`, `blank`, `NAN`, or % that ≠ coded mix ±2pt |
| PMS Best | Generated `charts_out/pms.png` path logic would include best>100 (code must skip) |
| EXT TARGET | `use_isze_ext_target` and profile ≠ V3.1 Dashboard col I for `dashboard_key` |
| Stale summary | `_summary.json` older than last `common.py` / profile sold_to change without re-analysis |
| Exclude cats | `exclude_movers_cats` set without a profile comment citing Jerome ask |

## shared slide rules

- **Audience first** — see `presentation.md`. No jargon; every line for the distributor in the room.
- Lead with official Power BI when present; skip orders if `skip_pbi_orders`.
- Urgency mix: plain “stock vs urgent” (or SOR/VOR only if that customer already uses those labels) — is / is not lifting price.
- Shell lubricants called out in plain words; never bury as unclassified.
- IDS Israel = UMI dealers only.
- Do not plot PMS Best >100%.

## Presentation skill (customer lens)

Read `presentation.md` **before** writing takeaways. Audience test: if a parts manager would need a glossary, rewrite.

## Retro

`09_meetings/UMI_Sales_Review_2026/RETRO_2026-08-12_UTI_blend_and_ModeA_failures.md`

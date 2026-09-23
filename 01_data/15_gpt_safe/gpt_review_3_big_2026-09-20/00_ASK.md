# Multi-hour GPT review — work order

**Prepared:** 2026-09-20 · Internal / private · **Expected effort: 4–6 hours of careful work**
**Folder:** `01_data/15_gpt_safe/gpt_review_3_big_2026-09-20/`
**Deliverables:** five files only. No line-level billing is included on purpose.

This is not a skim. Jerome wants a review that takes **hours**: recompute from the tables,
reconcile contradictions between documents, and pressure every open decision with evidence.
If you finish in under an hour, you did not do the job.

---

## Files

| File | Role | Size class |
|------|------|------------|
| `00_ASK.md` | This work order | short |
| `01_PRICING.md` | Full pricing programme brief + policy paper | large |
| `02_PARTS_FAMILY.md` | Classification switch + Japanese codes corpus | very large |
| `03_AFTERSALES_CEILING.md` | GPS/PMS ceiling + opportunity + open decisions | large |
| `04_DATA_TABLES.csv` | Valid 3-col file: `table,row_id,payload_json` | large |
| `04_DATA_TABLES.md` | Same data for upload if CSV is blocked (upload this instead) | large |

---

## Session plan (do in order, do not skip)

### Block 1 — Pricing (90–120 minutes)

Read `01_PRICING.md` and every `table=pricing_stack` / related rows in `04_DATA_TABLES.csv`.

Required outputs:
1. Recompute (or verify arithmetic of) whole-book, Japan, Thailand, PR00/UTI/UMI/CIS weighted increases from the stated recipe. Say PASS/FAIL per figure.
2. CONFIRM/REJECT/UNKNOWN on every numbered claim in §C of the pricing brief.
3. Rank the open decisions by commercial damage if left unanswered (top 5, with one sentence each).
4. Explicitly state whether flat +5% paper and the measured ~5.96% step may be combined (yes/no + why).
5. Flag any number in the policy paper that conflicts with the stack JSON / CSV.

### Block 2 — Parts family & Japanese codes (120–180 minutes)

Read all of `02_PARTS_FAMILY.md` (Parts I–V). Use `table=jp_codes`, `classification`, `benchmark_*` in the CSV.

Required outputs:
1. Independent verdict on **switch today?** — with the mtime/staleness argument tested against the brief’s own evidence.
2. For the claim table in the settled-position section: mark each major claim CONFIRMED / CORRECTED / STILL OPEN as you read it; list any new contradiction between Part II, Part III, Part IV, Part V.
3. Re-state in your own words why ZKK cannot be a chart axis (cite euro shares / fragmentation).
4. Separate verdicts for ZUK meaning, HKK usability, EPLE usability.
5. Name the single highest-ROI next build step (not “rebuild everything”).

### Block 3 — Aftersales ceiling & opportunity (90–120 minutes)

Read `03_AFTERSALES_CEILING.md`. Recompute from CSV tables `wallet_*`, `opportunity_*`, `gps_*`, `n35_share`, `capture_*`.

Required outputs:
1. Rebuild the network 2025 maths: ceiling, captured, coverage %, flat-€250 count and share — from CSV only. Compare to the brief.
2. Confirm ITUK / UTI / UMI rows separately (never blend Israel).
3. Produce your own top-10 opportunity ranking (category and category×market) from the CSV; say if oil-filter-as-hero would be wrong.
4. Portugal 0.6364 vs shipment mix: what Jerome must answer before any ceiling rebuild.
5. CONFIRM/REJECT/UNKNOWN on every numbered claim in §D of the aftersales brief.

### Block 4 — Cross-programme synthesis (30–45 minutes)

Required outputs:
1. Three contradictions that cut **across** pricing / classification / ceiling (not inside one file).
2. Three forcing decisions for Jerome — one per programme — worded so a yes/no or a single number closes them.
3. **What not to do this week** (hard stop list).
4. Agent-error pattern: where earlier agents clearly failed, in plain English.

---

## Hard rules (non-negotiable)

- Do not invent ceilings, capture %, price moves, or ZKK dictionaries.
- Do not blend UMI (1797) and UTI (1799); do not blend IUK and ITUK.
- Banned outward labels: Mode A/B, wallet, street, sell-out, Book B, IML v7, Model B, “AIM v2”.
- Findings need euro + parts family + trucks in service.
- Primary aftersales lens = **total** capture.
- Retired figures: 51.1% and €60.22M.
- Review only — do not instruct a rebuild or a ship.

---

## Return format

Write four sections titled exactly:

`## Block 1 — Pricing`
`## Block 2 — Parts family`
`## Block 3 — Aftersales ceiling`
`## Block 4 — Synthesis`

Under Blocks 1–3, use subheadings for each required output numbered above.
Under Block 4, use the four numbered items.

If a check is impossible from the pack, write **UNKNOWN — missing X**, not a guess.

---

## Paste prompt

> Execute the multi-hour work order in `00_ASK.md`. Work block by block. Recompute from `04_DATA_TABLES.csv`. Challenge every numbered claim. Return the four Block sections exactly as specified. Do not skim.

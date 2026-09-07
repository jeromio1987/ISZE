---
name: isze-work-loops
description: >-
  ISZE delivery loops: mail Sent proof (Loop A), Mode A truth HOLD (Loop B),
  A-lite story compiler (Loop C), and ledger. Use when verifying Outlook send,
  drafting sales-review mail, HOLD/go on Mode A packs, or compiling A_LITE
  story/brief. Read REFERENCE.md on verify/HOLD anomalies.
---

# ISZE work loops

Three named loops + an append-only ledger. Failure modes: [`REFERENCE.md`](REFERENCE.md).

This skill is **ISZE only**. If the current workspace is Alps / myPENS / Private: do not run these loops. Skip foreign `STOP: BRIEF_CHECKLIST` artefacts. Alps checklists live in `brief-checklist-Projects-Alps-Sep2026.json`; ISZE in `brief-checklist-ISZE.json`.

Subagent paste: `ISZE/.cursor/prompts/ISZE_SUBAGENT.md`. Image-Read the rendered pack; receipt without that read is a fail.

Harness overview (receipts, stop hooks, outer ticks):  
`C:\Users\jerom\Desktop\claude\ISZE\00_docs\agent\AGENT_HARNESS.md`

## Loop A — Mail delivery proof

- Skill: `isze-mail-delivery` + rule `isze-mail-delivery-loop.mdc`
- Default: **Draft + Display** only. **Send** only on explicit current ask.
- After send (or when he says he sent): prove **Sent Items** (subject + To + attachments) or report **Outbox stuck**.
- Do not let an unrelated Outbox item hide SENT_PROOF for the mail you care about. See REFERENCE.

## Loop B — Truth HOLD

- Before Mode A mail / client-facing numbers: run truth HOLD against `db_profiles.yaml` + `_summary.json` + Mode A pptx presence.
- HOLD = do not ship that DB’s Mode A claim. Override only with Jerome OK (`--force` / `--allow-internal` as documented in scripts).
- Truth HOLD does **not** rebuild decks.

## Loop C — Story compiler

- Script: `scripts/story_compiler.py`
- Needs `_summary.json`. Missing → HOLD; do not invent EUR / YoY.
- `A_LITE_STORY.md` = internal; `A_LITE_BRIEF.md` = external language (no IML jargon).
- Verify fails if recommended slide count > 10; keep A-lite ≤8 beats.

## Ledger

`09_meetings/_work_loops/delivery_ledger.jsonl` — append-only.

## Related harness loops (not this skill)

| Loop | Entry |
|------|--------|
| Visual ship receipt | `verify-before-done` skill + user stop hooks |
| Brief landing | `landing-every-brief-item` + `brief_checklist.mjs` |
| Pipeline green | `isze-verify-pipeline` + `outer_loops/check_pipeline_stale.mjs` |
| Dashboard health | `outer_loops/check_dashboard_health.ps1` / Aftermarket BI watchdog |
| Tender health | `outer_loops/check_tender_health.mjs` (Nordics keys closed) |
| myPENS | `mypens-verify-on-stop.mjs` |

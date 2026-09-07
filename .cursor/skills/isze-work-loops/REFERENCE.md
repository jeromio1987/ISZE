# ISZE work loops — REFERENCE (failure modes)

Companion to `SKILL.md`. Agents: read this when verify/HOLD looks “wrong”.

---

## Mail (Loop A)

### Outbox stuck ≠ not sent for another query

Unrelated mail (e.g. `RE: Action plans update` with Koen on the To line) keeps `outbox`/`status` at exit **2**.  
`verify` for Sweden/Loutsios can still return **`SENT_PROOF` exit 0** and print `WARN_OUTBOX_KOEN`. Do not let Action-plans Outbox hide Sent proof.

### Display-name To (false NOT_SENT)

Outlook Sent Items often store `To` as **display name** (`Koen Matheussen`), not SMTP.  
Matching only `koen.matheussen@isuzu-e.com` against `To` → false `NOT_SENT`.  
Fix: use `--to Koen` / alias map / Recipients Name+Address (script does this).

### Timezone window

`SentOn` may be naive local or UTC. Script normalizes to aware UTC before comparing `--minutes` window. If still missing, widen `--minutes` (e.g. 180–1440) before declaring NOT_SENT.

### don sentu

Never call `Send()`. Never flush Outbox with Send unless Jerome waives **in the current message**. Draft + Display + verify only.

---

## Truth HOLD (Loop B)

### Unknown profile key

`db_profiles.yaml` shape is `{defaults, distributors: {...}}`. Profiles live under **`distributors`**. Loading top-level keys → every DB “unknown”. Fixed in `truth_hold.load_profiles()`.

### PBI null Nordics / thin DBs

`FINLAND`, `SWEDEN`, `CYPRUS`, `DENMARK`, etc. may have `pbi: null` until Jerome supplies the Power BI cut.  
→ **HOLD** for Mode A mail to Koen (exit 1).  
Override only with Jerome OK: `--force` on `draft-sales` or `--allow-internal` on truth_hold.

### Profile vs `_summary.json` mismatch

If profile has `pbi.sales` but summary `pbi` is null (or sales lists differ) → WARN: re-run `build_parts_analysis.py --db KEY` before trusting story/deck numbers. Truth HOLD does **not** rebuild decks.

### Missing Mode A pptx

HOLD if no `ISZE_*_ModeA_only.pptx` (or full FY2027 pptx) under `09_meetings/<KEY>_Sales_Review_2026/`.

---

## Story compiler (Loop C)

### Missing `_summary.json`

→ HOLD; do not invent EUR / YoY / fights. Run parts analysis first (only when Jerome asks rebuild).

### Mode A vs Mode B files

- `A_LITE_STORY.md` = internal (Mode B nicknames OK in chat; file stays factual)
- `A_LITE_BRIEF.md` = external language (no IML v7 / Model B)

### Slide bloat

Verify fails if recommended slide count > 10. Keep A-lite ≤8 beats.

---

## Ledger

`09_meetings/_work_loops/delivery_ledger.jsonl` — append-only.  
`seed-sweden-loutsios` adds historical SENT_PROOF for 2026-08-31 15:31 if missing; skips if already present.

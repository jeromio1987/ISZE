---
name: isze-mail-delivery
description: >-
  ISZE Outlook delivery loop: draft/Display by default; Send only when Jerome
  explicitly says send/verstuur; always verify Sent Items or Outbox stuck.
  Use for Koen packs, colleague mail, “prove it was sent”, Outbox stuck.
---

# ISZE mail delivery loop

## Authority

| Current message | Action |
|---|---|
| draft / pop up / email / mail | `draft` + Display — **no Send** |
| **send** / **verstuur** | `send` then `verify` |
| prove / did he get it | `verify` / `status` only |

Never Send from an older turn’s wording.

## Scripts

```powershell
cd C:\Users\jerom\Desktop\claude\ISZE\.cursor\skills\isze-mail-delivery\scripts

# Draft + Display (default)
python outlook_delivery.py draft --to koen.matheussen@isuzu-e.com --subject "..." --body-file body.txt --attach path1.pptx --attach path2.pptx

# Explicit send (Jerome said send) — sends matching draft or builds then sends
python outlook_delivery.py send --to koen.matheussen@isuzu-e.com --subject "..." --attach ...

# Proof
python outlook_delivery.py verify --to koen.matheussen@isuzu-e.com --subject-contains "Sweden"
python outlook_delivery.py status --hours 48
python outlook_delivery.py outbox
```

Ledger: `C:\Users\jerom\Desktop\claude\ISZE\09_meetings\_mail_delivery_ledger.jsonl`

## Agent checklist

1. Resolve To, Subject, attachment paths (exist on disk).
2. Scope = only DBs named this turn.
3. Draft path unless current message has send/verstuur.
4. After Send or after Jerome says he sent → `verify` until SentOn found or Outbox stuck reported.
5. Paste proof table in chat. Update `_DRAFT_email_*.md` if that pack has a note.

## Outbox stuck

If `verify` → OUTBOX_STUCK: Display Outbox, list EntryIDs/subjects/att counts.  
If Jerome says **send** on the stuck item → `send --entry-id ...` or `send --subject-contains ... --from-outbox`.  
Do not silently Send wrong-scope Outbox copies (extra DBs).

## Related

- Rule: `.cursor/rules/isze-mail-delivery-loop.mdc`
- Ship gate mail §: `.cursor/rules/isze-no-ship-without-ok.mdc`
- Proposal: `09_meetings/_PROPOSAL_ISZE_work_loops.md`

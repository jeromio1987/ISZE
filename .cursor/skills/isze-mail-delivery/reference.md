# Mail delivery — deep reference

## Why this exists

2026-08-31: Sweden/Loutsios packs sat in **Outbox** after Send was attempted. Agents reported “draft ready”; Koen received nothing. Root cause = no verify step.

## States

| State | Meaning |
|---|---|
| `DRAFTED` | Saved + optional Display; Sent=False |
| `SEND_CALLED` | `mail.Send()` invoked |
| `SENT` | Found in Sent Items (SentOn + To + subject) |
| `OUTBOX_STUCK` | Still in Outbox — **not delivered** |
| `NOT_SENT` | Not in Sent, not matching Outbox (or wrong needle) |
| `SEND_REFUSED` | Script refused — no `--i-was-told-to-send` |

## Explicit Send words (current message only)

Accept: send, verstuur, “send it”, “send to Koen”, “stuur het”.  
Reject: earlier-turn “send”, “he needs it”, urgency alone, “pop the draft”.

## Agent reply contract after verify

```
STATUS=SENT|OUTBOX_STUCK|NOT_SENT
| SentOn | To | Subject | Atts |
```

Never: “should be with him”, “I sent it” without STATUS=SENT.

## Ledger

`09_meetings/_mail_delivery_ledger.jsonl` — one JSON object per line.

## Next loops (not this skill)

- B: Truth HOLD (PBI + Original BP) before draft  
- C: A-lite story compiler  
See `_PROPOSAL_ISZE_work_loops.md`

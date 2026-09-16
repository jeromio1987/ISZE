# Decision discipline

**Created:** 2026-09-16 · **Owner:** Jerome · **Related:** [`ISZE_ROADMAP.md`](ISZE_ROADMAP.md) §2 · [`DECISIONS.md`](../DECISIONS.md) · [`templates/DECISION_MEMO_TEMPLATE.md`](templates/DECISION_MEMO_TEMPLATE.md) · [`DECISION_RECONCILE_20260916.md`](DECISION_RECONCILE_20260916.md)

## Why this file exists

Decisions were being taken in conversation and were not landing where the work starts. The
clearest example: the price adjustment ambition was discussed and at one point recorded in a
conversation note as launch-only, while the roadmap still listed it as an open question to
Jerome. On 2026-09-16 Jerome confirmed it is **still open**. So the note was wrong, the roadmap
was right, and the cost is real: every reader of that list, human or agent, re-opens an item that
was never actually closed. This file is the fix. Nothing gets closed on the strength of a
conversation snippet again.

## 1. The weekly decision slot

45 minutes, once a week, one list only: roadmap §2 "Waiting on Jerome". Nothing else is on the
agenda.

Every item on that list gets exactly one of three outcomes, and no fourth:

| Outcome | What it means | What must be written |
|---|---|---|
| **Decided** | One option is chosen, on the record | The chosen option in one sentence, plus the date |
| **Killed** | Explicitly not doing it | The reason, then moved to roadmap §5 "closed - do not reopen" |
| **Delegated** | Someone else carries it, with a date | A named person or role **and** a date |

"Later", "still thinking", "needs more analysis" are not outcomes. Those are the categories that
grew the list to its present length. If an item cannot get one of the three, it stays on the list
for exactly one more week, and the date it was first raised is noted next to it.

## 2. The three-place rule

A decision is taken only when **all three** of these are true. If one is missing, the decision is
not taken and the item stays open.

1. **`ISZE_ROADMAP.md` §1 or §2 reflects it.** Absolute path:
   `C:\Users\jerom\Desktop\claude\ISZE\00_docs\ISZE_ROADMAP.md`
   The row is closed, re-labelled, or moved to §4 Shipped / §5 Closed.
2. **`ISZE/DECISIONS.md` has a new top entry** with the date, the decision in one sentence, and
   the reason. Absolute path: `C:\Users\jerom\Desktop\claude\ISZE\DECISIONS.md`
   Append-only, newest first. Do not edit an older entry; supersede it with a new one that names
   the date it replaces.
3. **The build or spec file that was waiting carries `status: decided`.** The file named in the
   roadmap row's Detail column is the one that gets the line, at the top of its status block.

Bumping one or two of the three is the failure mode this rule exists to prevent.

## 3. What "delegated" must contain

A named person or role **plus a date**. "Someone should", "operations will", "IML need to" are
not delegations. A delegation that names Jerome is valid - he can be the owner as long as a date
is attached.

## 4. Where each artefact lives

| Artefact | Absolute path |
|---|---|
| This rule | `C:\Users\jerom\Desktop\claude\ISZE\00_docs\DECISION_DISCIPLINE.md` |
| Decision log (append-only, newest first) | `C:\Users\jerom\Desktop\claude\ISZE\DECISIONS.md` |
| Queue and waiting list | `C:\Users\jerom\Desktop\claude\ISZE\00_docs\ISZE_ROADMAP.md` |
| Decision memo, one page, signed | `C:\Users\jerom\Desktop\claude\ISZE\00_docs\templates\DECISION_MEMO_TEMPLATE.md` |
| Reconciliation of the waiting list | `C:\Users\jerom\Desktop\claude\ISZE\00_docs\DECISION_RECONCILE_YYYYMMDD.md` |
| Automated drift report (Mondays) | `C:\Users\jerom\Desktop\claude\ISZE\05_memory\briefs\automation_drift_YYYY-MM-DD.md` |

## 5. What does not count as a decision

- A chat message, however clear it sounded at the time.
- A note in a brief, a memory file or a deck, unless Jerome wrote the choice down himself or the
  file states it as instruction.
- An agent's summary of what was discussed.
- Silence. No answer is not consent.

The Monday live-state audit now also reports decision drift: for every row in roadmap §2 it checks
whether a `DECISIONS.md` entry dated after the roadmap's "Last updated" line mentions the same
subject, and prints a line saying the item may already be decided but still reads as waiting.
That report is a prompt to check, not a closed decision - only the three-place rule closes one.

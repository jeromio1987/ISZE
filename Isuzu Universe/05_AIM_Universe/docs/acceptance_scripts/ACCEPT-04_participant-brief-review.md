# ACCEPT-04 — Read the participant brief and say what should not be in it

**Task:** Examine the actual participant-facing release candidate.
**Participants:** one reviewer. Must not be the person who built or briefed the case.
**Time:** about 30 minutes.
**Where:** the internal build, on this machine. Internal only.

## What this proves

That the export a participant would receive is safe to hand over: it carries the decision
they need and does not carry parts purchase cost, gross profit, margin, supplier discount,
another participant's records, or anything marked private.

## Before you start

1. Open the internal build (double-click, or the path on the sheet). It opens from Explorer.
2. Produce one participant brief for a chosen case. On the case, choose the export for a
   participant and save the file. Keep the file. It is the object being judged.
3. Read `CONSENT_AND_INTERNAL_ONLY.md` to the reviewer. Tell them which parts are test data.

## The task, in the reviewer's words

> "Here is a brief we would send to someone outside this team. Read it as if you had just
> received it. Tell me:
> 1. What is the decision being asked for?
> 2. Are the numbers you would need to judge it all here?
> 3. Is there anything in it that should never leave the company — a cost, a margin, a
>    supplier term, a private note, another person's information?
> 4. Is anything labelled in a way you would not understand, or that looks wrong?"

Do not answer any of the four for them. Do not hint. If they ask whether something is
private, say "what do you think it is?" and record their answer.

## What counts as a pass

- The reviewer names the correct decision unaided, **and**
- the reviewer names every one of these that is present in the file — cost, gross profit,
  margin, supplier discount, private notes, another participant's records — as something that
  must not be there, **and**
- nothing on that list is actually present.

If the reviewer cannot name the decision, the brief fails whatever else is right. If the
reviewer cannot spot a private item that is present, that is a fail of a different kind: a
leak that a careful reader would miss.

## Record

Use `RECORDING_SHEET.md`. Under "the one line that decides it", write the reviewer's answer
to question 3, in their words.

## After

- Save the brief you judged, and its file name, on the sheet. A later reviewer must judge the
  same bytes.
- If a private item is found, stop. Do not start ACCEPT-05 until it is removed and the brief
  is rebuilt and re-judged.

## What this does not prove

It does not prove the tool works, only that this one output is safe to hand over. The
judgement is one person's; a second reviewer is stronger, and worth doing if this is going to
a customer.

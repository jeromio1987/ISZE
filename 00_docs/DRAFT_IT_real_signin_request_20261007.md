# Real sign-in for the AIM pricing tool — what we are asking IT to decide

**From:** Jerome (ISZE Pricing)
**To:** IT owner
**Status:** draft. Jerome sends it. Not sent by anyone else.

## What the tool is

A pricing-decision tool for the aftersales business. A person opens it, sees where a part or a
market stands, works through the options and the money, records the decision, and produces a brief
for someone else. It is a single self-contained file today, opened on one machine.

It is an early internal version. Two feeds are real (the weekly tender feed, and national fleet and
spend figures). The parts, prices and dealer standards in it are still test data, and every screen
says which is which.

## What we need from IT

The tool has no real sign-in. Until it does, nobody is a signed-in person inside it: it runs in a
development-only mode that says so on every record, and it cannot be opened by more than one person
at a time.

We are asking IT to decide **how a real identity is established**, so that:

1. a person is who they say they are, before they see anything;
2. each person has a **role**, and the role decides what they can see and do;
3. access can be **withdrawn** when someone changes role or leaves, and any link already handed out
   stops working;
4. the tool does not have to store its own passwords.

We are not asking IT to build the tool, host it, or pick our reports.

## The roles we need, in plain terms

The tool already understands six roles. They are what the screens are built around:

| Role | What they do | What they must not see |
|---|---|---|
| requester | raises the question and asks for evidence | anything about cost or margin |
| case owner | owns a case and drives it to a decision | anything outside their own cases |
| reviewer | checks the evidence and the reasoning | nothing extra by role, but read-only |
| approver | signs the decision off | nothing extra by role, but read-only |
| support owner | answers availability and supply questions | the commercial figures |
| viewer | read-only, for a wider audience | cost, margin, other people's cases |

The two that matter most for a decision are **who may approve** and **who may not see cost and
margin at all**.

## What IT has to decide

1. **Which identity system** the tool should trust — whatever is already standard here, rather than
   anything new.
2. **How a role is attached to a person** — in that system, or in the tool.
3. **How withdrawal reaches the tool** — how quickly, and by what route.
4. **Whether the tool may keep case records on a shared service**, and if so which one. Today the
   case record lives only in the browser on one machine, so a second person cannot see it. A shared
   record needs a service with the same sign-in.
5. **Who owns the set-up afterwards** — the account, the roles, and the withdrawal.

## What stays development-only until IT answers

- No real person is signed in. Every record carries a visible "development-only" label.
- No shared case service. Cases are on one machine, in one browser.
- No attachment storage, so attachments are refused rather than stored insecurely.
- The tool cannot be given to anyone outside the team.

## What we are not asking

- Not a hosted product, not a website, not an integration project.
- No change to any live system.
- No customer or dealer data in the tool while it is being tested.

## What we would like back

One answer per numbered item above, in whatever form is easiest. If the answer is "use what we
already have", that is the best answer, and this becomes a short piece of configuration rather than
a project.

---

*Draft, 2026-10-07. Prepared from the tool's own access notes (`SAFE-01` approved identity and
`SAFE-07` role changes, departure and record use). Internal working document; the tool's own
limitations are stated on every screen.*

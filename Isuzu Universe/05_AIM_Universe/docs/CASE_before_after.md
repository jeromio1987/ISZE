# AIM case record and recipient exports - before and after

22 September 2026. The corrective work on the two defects this build owns: the
case record behind the frozen contract, and the recipient export that has to
enforce its own restriction.

Two frozen inputs were read and not modified:

- `..\reference\ISZE_AIM_Pricing_Decisions_v03_FROZEN.html`
  SHA-256 `7494CEA1955BE820D0082EEF15473610945663FBEFC7A06D7969C15822423E14` (verified on this machine before any work started)
- `src\data\contracts.js` - the shared records. Read, honoured, not edited.

Everything below is reproducible with the two commands at the end. No real part
number, customer, price or supplier cost appears in anything in this record; the
figures are synthetic.

---

## Part 1 - F12 / CASE-01 to CASE-08: the case record

### Before

A case was one object in browser storage under the key `ISZE_AIM_PRICING_02`,
written by `saveNote`:

```js
function saveNote(){
  const c = current();
  saved[c.id] = {...collectNote(c), savedAt: new Date().toISOString(), scenario: {...getScenario(c)}};
  localStorage.setItem('ISZE_AIM_PRICING_02', JSON.stringify(saved));
  ...
}
```

What that means in practice, and why each one is a defect rather than a
limitation:

- Saving again replaced the object. There was **no version**, so nobody could say
  what the case said before the last edit.
- There was **no history**. `delete-note` removed the case outright; a note that
  was wrong left no trace that it had ever said something else.
- The **owner** was a free-text box labelled "Review owner / role", and the screen
  said so itself: "A suggested role is not a person's acceptance of ownership."
  So the record could name someone who had accepted nothing.
- The **status** was a dropdown with five values in the screen's own words
  ("Draft review", "Evidence requested", "Ready for human review", "No change
  recommended", "Test proposed"). These were not the states published in
  `contracts.js`, and a proposal, an approval, a delivery and an outcome were the
  same box with a different label on it.
- Two people, or one person in two tabs, **silently overwrote each other**. The
  last save won and the loser was never told.
- Nothing recorded **who owed the next action or when**. A case sat at "Ready for
  human review" indefinitely with no date a reader could act on.
- Storage was **never tested across a real restart**, and the persistence that
  exists is one browser profile on one machine.

### After

Three new files, behind the frozen contract:

| File | What it is |
|---|---|
| `src\case\schema.js` | The record shape, the published states, the legal moves, and the rule that a correction replaces rather than duplicates. No input or output. |
| `src\case\store.js` | Persistence, versioning, the concurrency guard, links, the roll-up, export and restore. |
| `src\output\recipients.js` | The recipient exports and the one permission check. |

**The record.** A case is now `{ case_id, version, state, owner_role, next_action,
next_update_due, history[], support, outcome, links[], ... }`. The field list is
closed: `store.js` refuses to persist a key that is not declared in
`RECORD_FIELDS`, so a caller cannot grow the stored shape by accident.

**The version.** Every accepted write increases it by exactly one and appends one
entry to the log. That is enforced, not hoped for - `validate()` refuses any
record where the log length and the version disagree. This caught a real bug in my
own first draft: linking a case bumped the version without logging anything.

**The history.** Append-only. Nothing in these files removes or rewrites an
entry. Each entry carries the fields that step set and a snapshot of what was
proposed, delivered and achieved at that point, so `reopen(case, version)`
rebuilds the case as it actually stood rather than re-deriving it.

**The four stages, kept apart.** `ready_for_review` is a *proposal*,
`approved` is an *approval*, `delivered` is a *delivery*, `outcome_recorded` is
an *outcome*. They are four distinct stages in `STATE_STAGE`, and the schema
refuses a record that conflates them: one at `approved` may not carry support,
one at `delivered` may not carry an outcome. Check `C08` walks a case through all
four and reports the stage at each step: `proposal -> approval -> delivery ->
outcome`.

**One occasion, counted once.** A delivery carries a commercial event id, and the
rule book refuses a second delivery on the same case
(`DUPLICATE_SUPPORT`) - so closing an action cannot be booked as a second
commercial event. A correction of a delivery keeps the same event id, so it
replaces the figure without adding a second occasion: `C14` corrects a support
amount from 500 to 250 and the occasion count stays at 1. A finished case refuses
to be reopened (`CASE_IS_FINISHED`); a genuinely new decision gets a new case.

**Who owes what, and when.** `next_action` and `next_update_due` are required to
leave the draft for review, and `queue()` returns open cases overdue-first. `C12`
shows the queue head is the overdue case.

**Concurrency.** Optimistic, on the version. A caller reads a case, keeps the
version it read, and passes it back as `expected_version`. If the stored record
has moved on, the write is refused with `STALE_WRITE` and nothing is written.
`C05` is the lost race: two editors read version 4, editor two saves, editor one's
stale save is refused with `expected_version: 4, actual_version: 5`, and the
stored value is still editor two's.

**Corrections.** `correct()` names the entry it replaces. It never deletes it, it
never adds a commercial occasion, and it cannot move the case - a correction fixes
evidence, it does not un-record an outcome.

**Migration is not new business.** `outcome.counts_as_new_business` must be
stated as true or false, and a migration cannot claim true. The roll-up reports
newly won units and migrated units on separate lines. `C17` runs one migration of
40 units and one genuinely new 60 units:

```
newly won 60 units, migrated 40 units, support EUR 1000 across 2 occasions
```

**Storage, and what it honestly is.** Three adapters behind one interface:

| Adapter | Survives | Shared | On this machine |
|---|---|---|---|
| `memory` | nothing | no | a test, or a demonstration |
| `browser` | a page reload | no | one browser profile; a real restart was never tested |
| `files` | a real restart | no | **the default here** - one JSON file per case, written to a temporary file and moved into place |

`C19` proves the file case is real: the service that wrote everything is thrown
away, a new service is built from the folder, and the case reads back with its
correction and one commercial occasion intact - 19,940 bytes at
`%TEMP%\...\case-store\cases\CASE-TEST-STAGES.json`.

`describe()` reports kind, durability and shared status on every service, so a
screen can say what it is holding rather than implying a service. **A folder of
files on one machine is not a shared service**: it has no identity, no
permission, no revocation, and two people on two machines do not see each other.
That is recorded as the next bounded step, not hidden.

**Secrets.** A record carrying a key that looks like a credential (`api_key`,
`password`, `token`, `secret`, ...) is refused rather than stored. Settings and
secrets belong outside the case store. (`C21`.)

---

## Part 2 - F08 / SAFE-03, SAFE-04, SAFE-05: the recipient export

### Before

The v03 helper exported the whole internal record and then deleted field names it
did not like. Copied verbatim from the frozen HTML, lines 179306-179328:

```js
var V03_FORBIDDEN = ["cost_eur","parts cost","parts_cost","gross profit","grossprofit",
  "grossmargin","gp_before","gp_after","gp_change","margin_before","margin_after",
  "verifiedcosts","cost_bases","cost_basis","source_discount","base_price_jpy",
  "costrecord","jpy_per_eur","markup","fob_eur"];
function v03strip(obj, depth){
  ...
  var bad = V03_FORBIDDEN.some(function(f){ return lk.indexOf(f) >= 0; });
  if(bad) return;
  ...
}
function v03audit(obj){
  var text = JSON.stringify(obj).toLowerCase();
  return V03_FORBIDDEN.filter(function(f){ return text.indexOf(f) >= 0; });
}
```

`cost_eur` is on the list. `cost` is not. So a scenario carrying `cost` and
`margin_pp_change` came out of the stripper untouched, and the audit - which
searches for the same names it just removed - found nothing to report.

### Reproduced, in this build, on the bytes

`tests\export_bytes.test.mjs` reproduces the helper exactly and runs it against a
synthetic internal record. Read back:

```
E01  after stripping: scenario.cost=60, scenario.margin_pp_change=-3.4,
     result.margin_after_pct removed; cost_eur removed and cost not
E02  v03audit returned ["gross profit"] - an incidental mention of the phrase
     "gross profit" in a flag message - while scenario.cost=60 and
     scenario.margin_pp_change=-3.4 remained in the same object unreported
E03  the sentence "Our cost on this item is 60 EUR per unit" survived v03
     stripping with no finding
```

Two details worth stating, because I did not expect either and one of them
corrects a reasonable assumption:

1. The old audit is not *completely* silent. It returned `["gross profit"]` - not
   because it found the figure, but because one of the engine's own flag messages
   happens to contain the phrase in prose. **No finding named the unit cost or the
   margin, which is what actually matters.** The audit reports a word, not a
   value, and cannot tell them apart.
2. Its coverage is arbitrary rather than reasoned. It removed `margin_after_pct`
   by accident - that name happens to contain the listed substring `margin_after`
   - while keeping the sibling `margin_pp_change`, which does not. Two margins,
   treated opposite ways, by luck.

And the third shape, which a field-name filter structurally cannot handle: a
figure written into a sentence. It cannot see inside a string, and the audit
searches for the same field names, so it sees nothing there either.

### After

Nothing is exported and then trimmed. Each output is **built up** from an
allowlist - `buildAllowed(source, allowedKeys)` copies a key across only when the
recipient declared it, so a field nobody declared cannot appear however deeply it
is nested and whatever it is called. The check and the construction are the same
act, not two steps that can disagree.

`E05` asserts this on the produced bytes, not on a label:

```
1525 bytes; restricted names found: none;
carried: price_before, price_after, part_number, support_eur, change_pct
```

It also asserts by shape (`"cost":`, `"margin_pp_change":`, `"gp_before":`) in case
a value survived under a harmless name, and it asserts the fields that *should* be
there so the check cannot pass by carrying nothing.

Two things a construction cannot catch, and how each is handled rather than
hidden:

- **A restricted figure typed into a sentence.** `checkForRestrictedWords` looks
  for the names of the restricted measures, and for a restricted word sitting
  within about 60 characters of a figure. When it finds one the brief is
  **refused** - `RESTRICTED_WORD_IN_FREE_TEXT`, no payload produced - rather than
  the sentence being quietly deleted and the brief sent as though it were clean.
  A silent deletion is the same class of mistake as the blacklist: it makes the
  output look clean without anyone deciding that it is.
- **The brief's own limit lines.** The brief says "It contains no ISZE supplier
  purchase price and no ISZE margin." Saying so is not disclosing it, so the
  limit statements are excluded from the check.

Derived values were examined one by one, and there is exactly one:
`change_pct`, the price change percentage. It is computed only from
`price_before` and `price_after`, both of which the recipient is given, so it
discloses nothing they were not handed. No margin, cost, profit or contribution
value is derived for a participant, and `MEMBER_CONSTRUCTED_FIELDS` lists the
exceptions so an addition is a visible change to a list rather than an accident.

The internal record is marked `ISZE internal only`, and `assertInternalOnly()`
refuses to hand it to a participant by name:

> This is the internal record for recipient "internal". It carries parts cost and
> margin and must not be given to a distributor or dealer participant. Build a
> "member" brief instead; do not trim this one.

`E07` is the test that the brief is *constructed* rather than *filtered*: the
parts cost is moved from 60 to 41.75 and the margin from -3.4 to -11.9, and the
brief bytes are **identical**. A filter would have leaked the change.

`E11` is the negative control on the harness itself: a cost and a margin are
planted by hand into a produced brief, and the same finder that reported "none"
above is required to find them. Without that check, "restricted names found:
none" could be a vacuous assertion.

### Permissions, and what is not implemented

`canRead(identity, resource)` is implemented against a permission table with one
row per role and resource. The row that matters most is the one that would have
stopped the combined file being offered as a distributor handout: a participant
may read the shared brief and **may not** read the internal record.

**Real identity does not exist in this component.** There is no identity provider
configured, so `canRead` runs against a development-only shim and every result
says so (`identity_authenticated: false`, `development_only: true`). An identity
that claims to be approved but carries no verified organisation is refused
(`TENANT_NOT_VERIFIED`), and an identity claiming an unknown mode reads nothing.
`requireApprovedIdentity()` states the position plainly in code rather than in a
footnote:

> No approved identity provider is configured for this component, so no signed-in
> person can be established. [...] Production sign-in, organisation membership and
> revocation remain unimplemented.

**Attachments (SAFE-06).** There is no approved file store, so **no attachment
bytes are written anywhere by these files**. What is implemented is the permission
check, and it refuses three ways: a participant cannot attach at all, a file
declared restricted is refused, and a file whose name suggests a restricted source
(`supplier-cost-detail.xlsx`) is refused. A clean file is permitted, and the
answer says plainly that nothing was stored and why.

---

## What is implemented, and what is not

**Implemented and unit-tested here**

- A durable case record with a stable id, an owner role, created and updated
  timestamps, and an append-only history that records what each step set.
- A version that increments on every accepted write, enforced against the log.
- Optimistic concurrency: a stale write is refused with a clear conflict result
  and the other writer's value survives. Proven by a lost race.
- Duplicate submission refused, so a double click is not a second decision.
- Proposal, approval, delivery and outcome as four distinct stages, with the bad
  transitions refused and the wrong roles refused.
- Owner role plus a next-update date on an open case; an overdue-first queue.
- Corrections that replace a declared predecessor without multiplying the
  activity or the commercial occasion.
- Delivered support and its outcome linked without double counting; migration
  reported separately from newly won business.
- File storage that genuinely survives a restart, behind the same interface as
  memory and browser storage.
- Allowlist-based recipient exports, asserted on the produced bytes in a plain
  field, a nested object, a free-text note and a derived value.
- The permission check, and the refusal to hand the internal record to a
  participant.

**Not implemented, and why**

- **A shared case service.** The requirement was the smallest reusable shared
  backend, with configuration, secrets and restricted working files kept
  separate. There is no approved backend on this machine, and `INDEX.md` says not
  to invent one until a work order says so. What is delivered is a file-based
  adapter with the interface a server would implement, so the record genuinely
  survives a restart and swapping in a server does not change a case record or a
  caller. **A folder on one machine is not a shared service**, and `describe()`
  says so rather than implying otherwise. Server-backed storage is the next
  bounded step.
- **Production identity, tenant policy and revocation (SAFE-01).** No identity
  provider and no hosting. The permission logic is implemented and tested;
  sign-in, organisation membership and revocation need a server and an IT
  decision.
- **Attachment storage (SAFE-06).** No approved file store, so no bytes are
  written. The permission check runs and the gap is recorded as unresolved.
- **Server-side permission on a hosted page.** A browser-side filter is not access
  control. The v03 review said this plainly and nothing here changes it.
- **Cross-case transactions.** `linkCases` writes two files and is not a
  transaction. That is stated in its return value, and `linkIssues()` detects a
  half-written pair. The two-write window is open; a server with a transaction
  would close it.

One correction to the requirement as given, so it is not read as more than it is:
the SPEC says the blacklist "removes `cost_eur` but not `cost`, so a nested object
containing `scenario.cost` and `margin_pp_change` survives stripping and the audit
returns no findings." The preconditions reproduce exactly. The audit is not
completely empty - it returns one incidental prose match - but it names neither
the unit cost nor the margin. E02 asserts the precise behaviour and says so.

---

## Unresolved, carried forward

| Item | Why it is open | What would close it |
|---|---|---|
| Server-backed case store | No approved backend exists | A work order naming the service, plus IT sign-off |
| Real sign-in and tenant policy | No identity provider | An approved provider and a tenant decision |
| Attachment storage | No approved file store | The same backend decision, plus a retention rule |
| Cross-case transaction | Two files, one write window | A server that can transact |
| Browser restart durability | Never tested across a real restart | A test on the authorised machine, by a person |
| State-to-stage mapping | `contracts.js` publishes the states; the stage mapping lives in `schema.js` | A wording change to the shared file by its owner - I do not own it |

---

## Exact commands, and what they returned

Run from `C:\Users\jerom\Desktop\claude\ISZE\Isuzu Universe\05_AIM_Universe`.

```
node tests\case_store.test.mjs
```

Exit code `0`. `27 passed, 0 failed, of 27`.

```
node tests\export_bytes.test.mjs
```

Exit code `0`. `11 passed, 0 failed, of 11`.

Both suites print every check with its evidence, so a reader can see what was
observed rather than only a total. Neither suite skips a check and no supplied
assertion was relaxed to obtain a green result; the two suite files are new and
belong to this build.

---

## Files

Created by this build (the only files touched):

```
src\case\schema.js
src\case\store.js
src\output\recipients.js
tests\case_store.test.mjs
tests\export_bytes.test.mjs
docs\CASE_before_after.md
```

Read and not modified: `src\data\contracts.js`, the frozen reference HTML, the
extracted UI source and the extracted business payload. Not touched at all:
`src\engine\`, `src\ui\`, `src\data\`, `tests\accept_*`, `build\`, `dist\`.

The frozen reference was verified against the SHA-256 in the brief before any
work started:

```
(Get-FileHash reference\ISZE_AIM_Pricing_Decisions_v03_FROZEN.html -Algorithm SHA256).Hash
7494CEA1955BE820D0082EEF15473610945663FBEFC7A06D7969C15822423E14
```

---

## A note on scope

These six files are a **case record and an export guard**, behind a frozen
contract, in a workspace with no server. They are not a product: nothing here is
deployed, nothing is published, no mail is sent, and no production capability is
claimed. The combined HTML stays **internal**; nothing in this build makes it safe
to hand to a distributor, and the internal record now refuses to be passed off as
a participant document even by accident.

One thing I did not do, deliberately. The natural temptation was to leave the two
suites green by weakening whichever assertion was inconvenient when it failed.
Three did fail on the first run and all three were real: a link that bumped a
version without logging it, an invariant nobody had written down about the log and
the version agreeing, and an attachment result that returned a permission decision
in a shape the caller could not read. Fixing those is what the C-series checks are
for. Weakening them would have produced a green report and a case record that
could not be rebuilt - which is the defect this build exists to remove.

# The case service - CASE-01 to CASE-05

Written 2026-09-22 by the workflow developer. Everything below is measured on
this machine, and every claim names the command that produced it. Nothing here
was committed, pushed, sent or deployed.

---

## 1. Which module is authoritative, and why

There were two case implementations in this tree, and they were not equivalent.
That is the defect this project has already lost time to - two engines, two
export builders, two view layers - so one of them had to become the base and the
other had to be retired on purpose rather than left beside it to drift.

**The base is `src/case/schema.js` plus `src/case/store.js`.**

The reasoning, in the order it decided the question:

1. **It holds the lifecycle.** `transition()`, the nine states, the allowed
   moves, the role each move belongs to, the correction rule book, the
   `create()` that a case record actually needs. The other module had none of
   that. `docs/DEDUP_and_VAT.md` already recorded this, measured: `shipped has
   create()? undefined`, `shipped has transition()? undefined`.

2. **It holds the file adapter.** `makeFileAdapter` is the only thing in the
   tree that makes a case survive a restart. CASE-01 requires exactly that.

3. **Out of 27 checks written against it, none can be repointed at the other
   module**, because the behaviour they test does not exist there. A repoint
   that silently changes what is being tested is worse than the duplicate.

4. **The plan needs what is in it.** CASE-03's separate clocks, CASE-04's
   versioned proposals, CASE-05's support and outcome records and the stable
   action identifier had nowhere else to go.

**`src/data/cases.js` is retired as an implementation and kept as a caller
surface.** It is what `src/ui/app.js`, `tools/build.py` and five test files
already load. It now holds no state machine, no second version counter, no
second duplicate guard and no second log format: every call goes to the base.
`tests/case_service.test.mjs` check C45 asserts that mechanically - it reads the
file and fails if any of `STATE_STAGE`, `TRANSITIONS`, `applyTransition`,
`applyCorrection`, `stageOf`, `commercialEventCount` or `openWork` appears in it.

### The compatibility projection, and why it is not a second shape

The old repository stored a case whose log was an array of *revisions*, each
carrying a whole `{ scenario, result }` snapshot. The base stores a log of
*entries*, each carrying the fields it set plus a snapshot of the commercial
content. Same information, two shapes.

So the base shape is the one stored, and the old shape is **projected on read**
by `revisionsOf()` in `src/data/cases.js`. Two readers need the old shape and
both are outside this task's ownership: the browser journey
(`tests/accept/accept_02_journey.py`) and `tests/ux_reopen.test.mjs`. The
projection is read-only and derived, so there is no second copy on disk that can
drift, and `load().revisions` cannot disagree with `history()`.

One behavioural difference is deliberate and is asserted rather than hidden: the
old `save(caseId, record, meta)` applied `meta.state` to the record. It no
longer does. A case reaches a state by a recorded move, with a responding
function and a date. A save that could put a case straight into `approved` is the
CASE-04 rule's whole subject. The caller is told what was stored:

```
The case was created at "draft", not at "approved": a case reaches a state by a
recorded move with a responding function and a date, not by being saved into it.
```

`tests/run_tests.cjs` A22 and A26 were migrated for this and each keeps the
original claim beside the change. See section 6.

---

## 2. CASE-01 - the durable repository

**What was built.** A persistence adapter for cases, exposed through one
repository contract. `src/case/store.js` provides three adapters - memory,
browser Web Storage, and files - and `makeRepository()` in `src/data/cases.js`
re-exports the same surface.

**Evidence.**

- **A created draft survives a process restart, and the restart is a real second
  `node` process.** `node tests/case_service.test.mjs`, check C08. The parent
  writes the case, then runs `tests/case_restart_child.cjs` in a separate
  process via `execFileSync`. The child shares nothing but the folder. It reports
  `ok: true, state: submitted, version: 2` and a different pid; the parent also
  asserts the file's bytes and mtime are unchanged afterwards, so the child
  provably did not write to a case it was only asked to read.

  A test that rebuilds the service object in the same process does not test a
  restart: the module is already loaded and nothing has to be parsed again. That
  is why this one spawns a process.

- **A saved case refers to one identified source and scenario version.** Check
  C09. The record carries `schema_version`, `contract_version`, and a `scenario`
  carrying `scenario_id` and `version`; the proposal carries
  `active_proposal_version`.

- **No storage is presented as a shared service.** Check C10, and check C27 in
  the older suite. Measured, the file adapter describes itself as:

  ```
  One JSON file per case in a folder on this one machine. Survives a restart.
  It is NOT a shared service: two people on two machines do not see each other,
  the folder has no identity, no permissions and no revocation, and this
  component cannot tell one reader from another.
  ```

  **This should be read plainly: the storage is internal-only local files.** It
  is not a shared service and it is not claimed to be one. The memory and browser
  adapters say the same in their own words, and the exported bundle repeats
  `not_a_shared_service: true` in the file a reader opens rather than only on a
  screen. The interface is the same one a server would implement, so moving to a
  server later does not change a case record or a caller - but there is no server
  today, and a folder on one machine is not a substitute for one.

**Not implemented, and why.** There is no access control, no identity, no
permission and no revocation. `attach()` asks the permission question and
refuses a restricted file, and records that the bytes were never stored, because
there is no approved file store. That gap is stated in the returned value, not
hidden.

**Open decision for a human.** Where the real internal store should live before
any restricted real case is put in it, and whether `src/case/schema.js` and
`src/case/store.js` should be assembled into the artifact. See section 7.

---

## 3. CASE-02 - case, evidence, support and outcome kept apart

### The state table now in force

Nine states, from `src/case/schema.js`. `CASE_STATES` is built from
`contracts.CASE_STATES_TARGET`, because version 4 of the shared contract still
publishes the retired eight in `contracts.CASE_STATES` - see section 7, item 1.

| State | Stage | Meaning | Terminal |
|---|---|---|---|
| `draft` | prepare | Being prepared. Nothing is owed by anyone yet. | no |
| `submitted` | submitted | Sent. The waiting clock starts here. | no |
| `assessment` | assessment | The responsible function is working on it. | no |
| `awaiting_input` | assessment | Waiting on a named function for a stated thing. | no |
| `response_issued` | response | An answer has gone back. **Not** support, **not** a result. | no |
| `action_agreed` | agreed | The parties agreed an action. Nothing is delivered. | no |
| `resolved` | closed | Finished, and the outcome is known. | yes |
| `withdrawn` | closed | Taken back by the side that raised it. | yes |
| `closed_outcome_unknown` | closed | Finished, and nobody knows what came of it. | yes |

### The valid transitions

| Action | From | To | Responding function | Requires |
|---|---|---|---|---|
| `submit` | draft | submitted | case_owner | next_action, next_update_due |
| `withdraw` | draft, submitted, assessment, awaiting_input, response_issued, action_agreed | withdrawn | requester | approval_note |
| `begin_assessment` | submitted | assessment | reviewer | next_action, next_update_due |
| `request_input` | submitted, assessment | awaiting_input | reviewer | evidence_requests |
| `provide_input` | awaiting_input | assessment | case_owner | next_action, next_update_due |
| `issue_response` | assessment, awaiting_input | response_issued | case_owner | response, next_action, next_update_due |
| `accept_proposal` | response_issued | action_agreed | approver | proposal, approval_note, next_action, next_update_due |
| `terminal_no_change` | response_issued, action_agreed | closed_outcome_unknown | case_owner | approval_note |
| `close_resolved` | action_agreed | resolved | case_owner | outcome |

A finished case cannot be reopened. That would let one commercial action be run
twice; a new case, linked to the first, is the honest move and it gets its own
action identifier.

### Four moves that are deliberately not states

Evidence, support, the customer outcome and the recorded assessment each have
their own move and their own log entry, and **none of them is a lifecycle
state**. That is the point: a support payment recorded after a case closed must
not move the case, and an outcome recorded months later must not reopen it.

| Move | Function | What it records | Moves the state? |
|---|---|---|---|
| `recordAssessment` | reviewer | `assessment` - internal thinking | no |
| `proposeTerms` | case_owner | `proposal.versions[]` - the terms, versioned | no |
| `expireProposal` | case_owner, reviewer | `proposal.versions[].availability` | no |
| `recordSupport` | support_owner | `support` - the money, once | no |
| `recordOutcome` | case_owner, reviewer | `outcome` - the result, once | no |

`stageEvidence(record)` reads the log, so a case that was never assessed cannot
claim it was.

### No state carries a monetary value

`monetaryWeightOf(state)` returns `0` for every state, and check C13 asserts it
for every state rather than asserting it about the set. A state that acquired a
euro value would let a reader start summing states, which is the double count
this component exists to stop. An unknown state returns `null`, not zero: a
missing value is not zero.

### Evidence

- **Issuing a response, and closing a case, create no support, no won outcome
  and no monetary benefit.** Checks C14 and C15. After `issue_response` the
  record carries `support: null`, `outcome: null`, `approval_note: null` and zero
  commercial occasions. After `terminal_no_change` the same, with the case at
  `closed_outcome_unknown` and the benefit account reporting one case without a
  recorded outcome.
- **Invalid transitions are rejected with the current state retained.** Check
  C16. Three refusals, then: state, version, `support`, `outcome` and history
  length all exactly where they were.
- **Every valid transition carries dated attribution.** Check C18: every entry
  that moved the state has a parseable `recorded_at`, a `role`, and a
  `recorded_by` that is not `unspecified`.

### The change history, stated honestly

The log is append-only inside this component. **It is not tamper-proof
certification**, and the store publishes that sentence rather than leaving a
reader to assume otherwise:

> The change history is append-only inside this component: nothing here rewrites
> or removes an entry, and a correction names the entry it replaces. It is NOT
> tamper-proof certification. There is no server, no signature and no trusted
> clock, and anyone with write access to the stored file can edit it.

Check C11 asserts the statement says so, and that the store publishes the same
words the rule book writes.

---

## 4. CASE-03 - who owes the next action, and when

**Fields on the record:** `owner_role`, `owner`, `assigned_to`, `deputy_role`,
`escalation_route`, `next_action`, `next_update_due`, and the five separate
clocks from `contracts.CASE_TIMESTAMPS`: `submitted_at`, `assigned_at`,
`acknowledged_at`, `answered_at`, `resolved_at`.

**Dealer commitments are separated from ISZE support.** `evidence_requests[]`
carries `from_role`, and `openWork()` splits them into `dealer_commitments` and
`isze_commitments`. `obligationStatement()` prints the difference in one
sentence a screen can use directly.

**Evidence.**

- **A dealer awaiting ISZE guidance is shown as awaiting that guidance, not
  inactive and not at fault.** Check C21, in both directions:

  ```
  Waiting on an ISZE or distributor function for: A cost position from the
  product function (product, due 2026-10-12). The dealer has supplied what was
  asked of it.
  ```

  The queue also sorts a case ISZE owes ahead of one the dealer owes (check
  C24), so the two obligations are not interleaved into one list where "oldest"
  secretly means "person to chase".

- **Reassignment records the change without resetting total waiting time.**
  Check C23: 3.0 days waiting before the reassignment, 6.0 days after, same
  `submitted_at`, new owner. `total_waiting_days` is measured from
  `submitted_at`, never from the last edit, so a case changing hands adds time
  to the new owner without taking it off the dealer.

- **The clocks stay separate.** Check C22, on a case walked one move per day: the
  submission and the answer carry different times. A clock earlier than the case
  was created, or a clock that runs backwards against a later one, is refused
  rather than stored.

**No service guarantee is invented.** Check C25 sweeps the record, the owner
table, the history statement and the storage description for an SLA, a response
promise or a retention period and finds none. `next_update_due` is a date
somebody wrote down for one case, and the source says so:

> There is also no service guarantee here. A `next_update_due` is the date
> somebody wrote down for this case; it is not an SLA, and no network-wide
> response promise is declared anywhere in this file.

If ISZE publishes one, it belongs in a decision record, not in a date field.

---

## 5. CASE-04 and CASE-05

### CASE-04 - versioned proposals, approval route preserved

A proposal is versioned in `record.proposal.versions[]`. **An amendment names
the version it amends and the former terms stay readable** (check C26):
`repo.reopen(caseId, v1)` still shows the August price after the September
amendment.

Three rules the plan names, each asserted:

- **A draft cannot become approved by saving it.** Check C28. The state is not a
  field a record write can set - `saveRecord` refuses a changed `state` - and
  `accept_proposal` is not offered from `draft`.
- **A draft cannot become approved by choosing the highest-ranked row.** Check
  C29. A ranking is carried as `candidate_keys` on the proposal and nothing else;
  the proposal stays `proposed` and the case stays where it was.
- **The approval route is preserved.** Check C30: accepting with a different
  `approval_route` from the one on the proposal is refused, because swapping the
  route at the moment of acceptance is what makes an approval meaningless.

**No live prices are set and no approver is impersonated.** A version cannot be
accepted without either a genuine `approval_reference` or an explicit
`synthetic_approval: true`, and a synthetic approval must say so in the note a
reader will see. Check C29 asserts both refusals.

**Expiry is a separate field from approval, and that separation is deliberate.**
An approved offer that lapses was still approved - the decision was taken and the
record must not be rewritten. So `proposal_state` stays `accepted` and
`availability` becomes `expired`. A reader sees both facts:

```
The accepted proposal expired on 2026-10-15. It is not presented as available.
It was approved, and it lapsed: both facts stay on the record.
```

Expired support cannot be paid against (`SUPPORT_NOT_AVAILABLE`, check C27), and
a second expiry of the same version is refused (`ALREADY_EXPIRED`).

### CASE-05 - linking support and outcomes without double counting

**The stable action identifier.** Every case carries one from creation
(`ACT:<case-id>`), and every support payment names the action it pays for. AIM,
IDS, PRISM and SPA can each refer to an action; recording the same identifier on
both cases is what makes it one action.

**The four measures are kept distinct and are never added together.**
`purchase_cost_difference_eur`, `gross_profit_eur`, `capacity_released_units`,
`programme_expenditure_eur`. `benefitAccount()` returns four lines per action
with their units and a `known` flag, and returns `total_benefit_eur: null` -
deliberately, because printing one figure would invite exactly the double count
the function prevents.

**Evidence.**

- **A paid credit does not automatically create incremental profit or a won
  quotation.** Check C32. After a payment with no outcome: the gross-profit line
  is `null` with `known: false` (not zero - a missing measure is not zero),
  `newly_won_units` is 0, and the payment appears once, as support.
- **One action used by several modules appears once.** Check C33. Two cases, each
  naming `ACT:SHARED-ACTION-1`: one action, support counted once at 300 rather
  than 600, 60 newly-won units rather than 120, one gross-profit line rather than
  two.
- **Unknown outcomes stay unknown.** Check C35. An unmeasured action reports
  `outcome_state: 'unknown'`, `units: null`, `counted_as: 'unresolved'`, and its
  measure lines are `null` and flagged unknown. **Closing the case does not
  resolve it** - the case moves to `closed_outcome_unknown` and the outcome stays
  absent.
- **A migration is not newly won business.** Check C36: 60 genuinely new units
  and 40 migrated units are reported on separate lines and not added. An outcome
  claiming a migration is new business is refused outright.
- **One case cannot record a second payment for the same action.** Check C37,
  `DUPLICATE_SUPPORT`.

---

## 6. The vocabulary migration, in one change

CASE-02's first piece of work was adopting the nine-state vocabulary. It was done
in one change that moved the state values, the transition table and every
reference together, not by switching the states and repairing the fallout
piecemeal.

| Reference | What happened |
|---|---|
| `src/case/schema.js` | `CASE_STATES`, `STATE_STAGE`, `TRANSITIONS`, `TERMINAL_STATES`, `NO_NEXT_ACTION_STATES`, `OWNER_BY_STATE` and every message rewritten in one pass |
| `tests/case_store.test.mjs` | Migrated. Every check id and name kept; the header carries the old-to-new table so a reviewer can diff the two runs |
| `tests/run_tests.cjs` | A22, A25, A26 migrated, each keeping its original claim beside the change |
| `src/data/cases.js` | `CASE_STATES` published from the shared contract, not copied; the one write path and the one correction rule book |
| `tests/case_service.test.mjs` | New suite for CASE-01..05 in the new vocabulary |
| `src/data/export.js`, `src/data/evidence.js`, `src/data/candidates.js`, `src/ui/app.js` | Read and considered; none carries a case state literal except `candidates.js`, below |

**Two references were deliberately not migrated.**

`tests/ux_reopen.test.mjs` passes `state: 'ready_for_review'` with each save (six
places), and `tests/export_shipped.test.mjs` carries the same word in two
fixtures. Those files are on this task's **do-not-touch** list, and neither
asserts on the state - they pass through it. Under the facade the value is not
applied and the save reports that in its notes, which neither file reads, so both
suites stay green while carrying a word that is no longer a case state. Reported
rather than edited. It is dead text, not a failing assertion, but it will mislead
the next reader of those files.

`src/data/candidates.js` line 699 builds a candidate-promotion record with
`state: 'evidence_requested'`. That object is a proposal built from a candidate
row; nothing stores it, and nothing validates it. Migrating it would mean
guessing whether the author meant `awaiting_input` or `assessment` - the two are
genuinely different - so it is reported instead. It is also outside this task's
ownership. It becomes a live fault the first time that object is handed to the
case service.

### What was NOT done, and why

**No assertion was weakened, deleted or relaxed.** Every original claim is still
asserted. Three needed their expression changed, and each keeps the original
wording beside the correction:

| Check | Original claim | Why it changed |
|---|---|---|
| `run_tests.cjs` A22 | `role A` as `owner_role`; `meta.state` applied | A responding function is now a named list, and a state is reached by a move. The version and reopen claims are unchanged; the state rule is now asserted in its own right |
| `run_tests.cjs` A25 | `correct(corrects_revision)` | The base's correction requires a date, a function and a reason. The two-entry, names-its-predecessor, still-readable claims are unchanged |
| `run_tests.cjs` A26 | `state: 'approved_by_ai'` refused by the save | A save can no longer set a state, so the nonsense input is refused one step earlier. Both halves are kept: the save reports the state was not applied, and writing the state onto a record is refused with the original wording |

### The vocabulary is enforced in `src/case/schema.js`, not read from `contracts.js`

This is the one part of the migration that is not complete, and it is incomplete
because of an ownership boundary rather than a technical one. See section 7,
item 1.

---

## 7. What is open, and what needs a human decision

### 1. `contracts.CASE_STATES` still publishes the retired eight

`src/data/contracts.js` is **read only** for this work. Version 4 publishes the
nine target states in `CASE_STATES_TARGET`, marked "NOT YET ADOPTED", and still
publishes the retired eight in `CASE_STATES`, which it describes as "the
vocabulary currently in force".

That description is now wrong. The nine are in force: they are what `validate`,
`TRANSITIONS`, `STATE_STAGE` and every check enforce. To avoid a half-migrated
tree, `src/case/schema.js` builds its enforced list from `CASE_STATES_TARGET` and
publishes the divergence rather than hiding it:

```js
schema.CASE_STATES              // the nine, in force
schema.CASE_STATES_RETIRED      // the eight that are no longer used
schema.CONTRACT_VOCABULARY_STALE // true
```

**The change its owner needs to make** is one line in `src/data/contracts.js`:

```js
var CASE_STATES = CASE_STATES_TARGET;
```

and the version-history comment beside it. Nothing else in `contracts.js` needs
to move: `CASE_TIMESTAMPS` and the CASE-03..06 field names are already declared
and are being used as declared.

**Nothing downstream breaks while this is open.** `schema.CASE_STATES` is what
`validate` uses, and check C12 asserts it equals `CASE_STATES_TARGET`. The only
cost is that a reader of `contracts.js` alone would be told the wrong set is in
force.

### 2. **The artifact cannot be rebuilt, and the build's guard has a blind spot**

This is the most important open item, and it is a genuine defect that arrived
with this work.

`tools/build.py` assembles `src/data/cases.js` but retires `src/case/schema.js`
and `src/case/store.js`. In a browser there is no `require`, so the facade
resolves its dependency from `root` and finds `undefined`:

```
$ node tests/case_build_wiring.cjs
FAIL W04  A browser has no require, so the facade must not depend on one
      -> Cannot read properties of undefined (reading 'describeStorage')
```

`src/ui/app.js` calls `AIMCases.makeRepository({...})` at its module scope, so
this throws before any view paints. The build printed `labels : clean` because
the guard that should have caught it looks for the wrong name:

```
tools/build.py computes:  holder = "root.AIM" + stem[0].upper() + stem[1:]
so for src/case/store.js it searches for:  root.AIMStore
and the file actually publishes:           root.AIMCaseStore
```

The guard searched for a string that never occurs, found nothing, and passed.
This is the first pair where its file-name derivation disagrees with the
published global - for others the two happen to match (`src/ui/views.js` ->
`root.AIMViews`) - which is why the fault arrived now rather than earlier.
`tests/case_build_wiring.cjs` W01 measures this directly and reports **nine**
retired modules whose guard name does not match their published name.

**Two changes, and they belong together:**

1. `tools/build.py`: read the global from the assignment line each module already
   carries (`root.AIMCaseStore = API;`) instead of building it from the path.
2. Decide whether `src/case/schema.js` and `src/case/store.js` are assembled. If
   they are, add both to `MODULES` **before** `src/data/cases.js`. If they are
   not, the dependency has to come out of `src/data/cases.js`, which means
   putting the logic back there - the duplicate this work exists to remove.

`docs/DEDUP_and_VAT.md` already recorded this as the integration owner's
decision. It is now blocking.

**No broken artifact was left on disk.** The synthetic build produced while
investigating this was removed. The real-payload artifact
`dist/ISZE_AIM_Pricing_Decisions_v04_INTERNAL.html` predates this work and is
intact; it is stale against the new source but it is functionally correct, and
W03 measures each artifact against its own code so an older artifact is reported
as older rather than as broken.

`tests/case_build_wiring.cjs` is a **failing test on purpose**. It is the
reproduction of a defect in a file this work does not own.

### 3. The facade still exists

`src/data/cases.js` is a caller surface over the base, not an implementation. It
holds no rules. But it is still a second file for one concern, and the tidy
end-state is for `src/ui/app.js` to load the base directly and for the facade to
be deleted. That is four test files, the browser journey and `src/ui/app.js` -
and `src/ui/` is owned by another agent. Reported, not done.

### 4. Two suites carry a retired state name, and both are outside this task

`tests/ux_reopen.test.mjs` passes `state: 'ready_for_review'` with each save (six
places) and `tests/export_shipped.test.mjs` carries the same word in two fixtures.
Neither asserts on the state; both pass it through. Under the facade the value is
not applied and the save says so in its notes, which neither file reads, so both
suites stay green while carrying a word that is no longer a case state. Both
files are on the do-not-touch list for this work, so this is reported rather than
edited. It is dead text rather than a failing assertion, but it will mislead the
next reader.

`src/data/candidates.js` line 699 carries `state: 'evidence_requested'` on a
candidate-promotion record. Unstored and unvalidated today; a live fault the
moment it reaches the case service. Reported, not patched - outside this task's
ownership and genuinely ambiguous between `awaiting_input` and `assessment`.

### 5. Fields the base needs that `contracts.js` does not declare

`docs/CASE_service.md` section 1 and `schema.UNDECLARED_IN_CONTRACTS` list them:
`assessment`, `response`, `proposal`, `evidence_requests` and the support and
outcome sub-fields. **Measured today, no live path is affected**:
`src/ui/app.js` builds its export object from the payload case, not from the
stored case record, so none of these reaches `src/data/export.js`, which builds
its allowlist from `contracts.declaredFields()`. It becomes a real gap the moment
an export reads a stored case instead - which CASE-08 would do.

### 6. Attachment storage is not implemented

No approved file store, so `attach()` asks the permission question, refuses a
restricted file, and records that the bytes were never written. Not new; carried
forward from SAFE-06 and unchanged.

### 7. `history_statement` is published but nothing renders it

`repo.history_statement` and `bundle.history_statement` carry the sentence about
what the log is. `src/ui/app.js` does not print it, because that file is another
agent's. A screen that shows a change history should show it.

---

## 8. What CASE-06, 07 and 08 inherit

- **CASE-06** (explanations and corrections as separate evidence) inherits a
  working `explanations` field on the record, the correction rule book
  (`applyCorrection`, with `correction_of` naming the entry replaced, and a
  refused second correction of the same entry), and the `review` section. It has
  to add the contributor's words, scope, period, source and audience, and the
  distinction between a source correction, a later recollection and a
  disagreement with an interpretation. `journal`-style free text is not there
  yet.
- **CASE-07** (duplicate submissions and lost concurrent edits) inherits the
  version guard (`expected_version`, `STALE_WRITE`), the duplicate guard
  (`DUPLICATE_SUBMISSION`), and validation in the service layer rather than in
  browser forms. It still has to add a **request identifier** so a retried
  timed-out submission creates one case rather than two - today a retry is caught
  only if the content is byte-identical.
- **CASE-08** (actionable internal queue and reusable history) inherits
  `queue(asOf)` with overdue-first ordering and the two obligations separated,
  `openWork`/`obligationStatement` for the row text, `reopen(caseId, version)`,
  and `list()`. It still has to add scoped search and filtering, and the rule
  that a search returns only records the current user may receive in shared mode.
  Today there is no scoping, because there is no identity.

---

## 9. Every claim in this document, and the command for it

```
# The five suites named in the brief, and the acceptance wiring.
node tests/run_tests.cjs                       # expect 60 passed, 0 failed
node tests/case_store.test.mjs                 # expect 27 passed, 0 failed
node tests/case_service.test.mjs               # expect 46 passed, 0 failed
node --test tests/data_contracts.test.mjs      # expect 74 pass, 0 fail
node --test tests/ux_flow.test.mjs             # expect 14 pass, 0 fail
node --test tests/ux_reopen.test.mjs           # expect  7 pass, 0 fail

# The rest of the tree, for a change that touched shared modules.
node --test tests/export_shipped.test.mjs      # expect 25 passed, 0 failed
node --test tests/export_bytes.test.mjs        # expect 11 passed, 0 failed
node --test tests/market_evidence.test.mjs     # expect 32 pass, 0 fail
node tests/accept/guard_09_module_scope.cjs    # expect  5 passed, 0 failed

# The decision on which implementation is the base.
node -e "const c=require('./src/data/cases.js');console.log(c.AUTHORITATIVE_IMPLEMENTATION)"

# The state table, the transitions and the monetary weight.
node -e "const s=require('./src/case/schema.js');console.log(s.CONTRACT_VOCABULARY_STALE, s.CASE_STATES)"

# The defect in tools/build.py. EXPECTED TO FAIL until its owner changes it.
node tests/case_build_wiring.cjs               # expect  1 passed, 3 failed
```

Checked and unchanged, recorded for completeness: `python tools/build.py`
succeeds but produces an artifact that fails at runtime - see item 2 in section
7; `python tools/orphan_audit.py` reports `ORPHANS : 0`;
`python tools/retirement_safety_check.py` exits 0 with `SAFE`;
`python tools/paint_check.py` reports 8/8 against the existing artifact;
`node tests/accept/accept_01_engine.cjs` reports 46 pass / 1 fail, the same
`R27` failure that was there before this work started.

# Duplicate modules and the VAT unit defect

Written 2026-09-22 by the integration and data developer, continuing the AIM
Universe corrective build. This is the record of two pieces of work on the same
component: closing the duplicate-module problem, and making the tax-rate unit
explicit so a rule can no longer infer it from the size of a number.

Everything below is measured on this machine. Where a number is quoted, the
command that produced it is named. Nothing here was committed or pushed.

---

## Part 1 - The duplicate modules

### The problem in one paragraph

`tools/build.py` assembles nine (now ten) modules into the artifact and retires
eleven that stay in the working tree. Parallel developers built a module for the
same concern more than once, and some tests were pointed at the copy that does
not ship. A test aimed at a retired copy is worse than no test: it reports on
code the product never runs, while looking exactly like evidence about the
product. The specific risk in the headline case was that the two calculation
engines were byte-identical on the day, so the arithmetic suite was green - and
would have stayed green against a stale copy the first time the shipped engine
was edited.

### The method

Taken one pair at a time. For each pair: count the tests before, determine
whether the shipped module actually covers the retired one's behaviour, repoint
or retain on that evidence, then count again. A repoint that silently changes
what is being tested is worse than the duplicate, so "the suite is still green"
was never accepted as the reason to repoint. Where the coverage did not exist,
the module was retained and the reason written down.

### Pair by pair

| # | Ships | Retired | Decision | Evidence |
|---|---|---|---|---|
| 1 | `src/engine/engine.js` | `src/engine/pricing.js` | **Deleted** | Byte-identical; full equivalence proven below |
| 2 | `src/data/export.js` | `src/output/recipients.js` | **Retained** | Repointing takes the byte suite from 11/0 to 2/9 |
| 3 | `src/data/cases.js` | `src/case/store.js` + `src/case/schema.js` | **Retained** | The shipped store has no `create()` and no `transition()` |
| 4 | `src/data/candidates.js` | `src/ui/candidates.js` | **Retained** | No test loads the retired view; nothing to repoint |
| 5 | *(the engine's basis resolution)* | `src/data/costbasis.js` | **Retained** | 0 of 14 basis checks repointable; 14 functions exist only there |
| 6 | `src/ui/app.js` | `src/ui/views.js`, `src/ui/render.js`, `src/ui/viewmodel.js`, `src/ui/scenario.js`, `src/ui/failure.js` | **Already repointed before this work** | Verified, not changed - see below |

---

#### Pair 1 - the two engines: deleted

The claim was that the two files were byte-identical, so nothing was
arithmetic-wrong yet but any future edit to the shipped engine would leave the
arithmetic suite validating a stale copy. Verified rather than assumed:

```
engine.js  sha256 1db7f3fb6fa8f399
pricing.js sha256 1db7f3fb6fa8f399
byte identical       : true
export count         : engine 48  pricing 48
same export names    : true
same CONTRACT_VERSION: true  1
calculate identical  : true
```

48 identical exports, identical contract version, and an identical result object
from the one calculation entry point on the same synthetic scenario.

`tests/module_audit.py` reported `tests/fin_math.test.mjs` as loading
`pricing.js`. It did:

```
tests/fin_math.test.mjs:24
const engine = require(join(ROOT, 'src', 'engine', 'pricing.js'));
```

That is the arithmetic suite - the most important suite in the component - and
it was aimed at the retired copy. The one other mention of `pricing.js` under
`tests/` was a prose note in `tests/accept/accept_01_engine.cjs` recording that
the file the brief named does not exist. No test loaded it.

Repoint, with the count on both sides:

| | loading `pricing.js` (retired) | loading `engine.js` (shipped) |
|---|---|---|
| `tests/fin_math.test.mjs` | 58 pass / 0 fail | 58 pass / 0 fail |

The count is identical because the files were identical. That is what makes this
repoint safe here, and it is the only reason: the suite is now measuring the
module that ships, and the next edit to `engine.js` will be caught instead of
being compared against a frozen copy.

The file was then deleted. `tools/build.py` keeps its `UNWIRED_MODULES` entry as
a labelled tombstone rather than removing it, for a reason that is stated in the
comment there: `tests/accept/guard_09_module_scope.cjs` G04 names
`src/engine/pricing.js` and asserts it classifies as retired. Pruning the entry
without changing that probe would fail a check this developer does not own, so
the pruning is reported to the integration owner rather than done unilaterally.
The entry is inert either way - the file is absent, so nothing can load it, and
`tools/module_audit.py` now lists it separately as a deleted tombstone instead of
counting it as a live retired load.

---

#### Pair 2 - the two export builders: retained

This is the pair the brief flagged as important, and the flag was right.

`src/data/export.js` (shipped) exposes 15 names. `src/output/recipients.js`
(retired) exposes 23, and the extra ones are the permission and safety layer:

| Only in the retired `recipients.js` | What it is |
|---|---|
| `IDENTITY_MODES`, `PERMISSIONS`, `RESOURCES` | the role/permission table |
| `makeDevIdentity`, `requireApprovedIdentity`, `permissionFor` | identity, and the honest refusal when production identity is not available |
| `canRead`, `canAttach` | whether a role may read or attach a given resource |
| `findRestrictedInBytes`, `decodeUtf8`, `utf8Bytes`, `priceChangePct` | byte-level scanning for restricted content |

The shipped builder has no permission code at all. Measured, not asserted: a
throwaway copy of `tests/export_bytes.test.mjs` with its single import line
changed from `recipients.js` to `export.js` gives

```
2 passed, 9 failed, of 11
```

against `11 passed, 0 failed, of 11` on the retired module. Nine of the eleven
byte-level safety checks exist only because that module exists.

So it is retained, and the checks that ask it what it does are kept. Those loads
carry in-file declarations (`// RETIRED-MODULE-USE: src/output/recipients.js -
<reason>`) precisely so the guard permits them, and
`tests/accept/guard_09_module_scope.cjs` reads those declarations and passes at
5/5 with them in place. Deleting this module would not tidy the tree; it would
delete the permission table and the restricted-word scanner.

---

#### Pair 3 - the two case stores: retained

`src/data/cases.js` (shipped) exposes
`makeStore, makeRepository, KEY, CASE_STATES`. The retired pair -
`src/case/store.js` and `src/case/schema.js` - exposes 6 and 33 names
respectively, and holds the entire case lifecycle.

The decisive measurement is the shipped store's own surface:

```
shipped cases.js  makeRepository() -> save, load, list, history, reopen, correct,
                                     queue, exportAll, importAll, summarize, store
shipped has create()?     undefined
shipped has transition()? undefined
```

There is no `create`, no `transition`, no stage, no role check and no state
machine. `src/case/schema.js` is where `applyTransition`, `requiredProblems`,
`stageOf`, `commercialEventCount` and the 8 declared case states live, and it is
the only implementation of them anywhere in the tree:

```
$ rg -n "applyTransition|makeCaseService" src/
src/case/store.js:232,448,460,776,803
src/case/schema.js:557,597,606
```

`tests/case_store.test.mjs` runs 27 checks across the lifecycle - create, version
increment, race refusal, stage ordering, wrong-role refusal, duplicate refusal,
correction, migration, restart. **None of the 27 can be repointed**, because the
behaviour they test does not exist in the shipped module.

This is worth stating plainly rather than burying: the durable case store is a
capability the artifact does not carry. The shipped store persists a single
snapshot of a scenario with a version counter and a concurrency guard. The
lifecycle - proposal, approval, delivery, outcome, and the refusal to count one
occasion twice - is retired. If the lifecycle is intended to ship, this is not a
duplicate to delete; it is work that has not been wired up, and the wiring is the
integration owner's decision.

---

#### Pair 4 - the two candidate modules: retained

`src/ui/candidates.js` is a *view* over the candidate data, not a second data
module. No test in the tree loads it. The only files that name it are
`tools/build.py`, `tools/retirement_safety_check.py` and two generated reports.

Nothing needed repointing and nothing needed deleting. It is retained: removing
it would be a change under `src/ui/` with no test evidence behind it, and the
`src/ui/` tree is owned by another agent working concurrently.

---

#### Pair 5 - the engine against `costbasis.js`: retained, and it is a real hazard

`tools/build.py` retires `src/data/costbasis.js` because it "overlaps the
engine's basis resolution". That overlap is genuine, so it was measured instead
of waved away, in two parts.

**Part one: can the checks be repointed?** `tests/data_contracts.test.mjs`
contains 14 checks against the retired module. Every one of them calls a
function the shipped engine does not have:

```
resolveBasis, basisById, windowOf, authoriseOfferBasis, comparableBases,
guardBasisUse, basisCompatibility, costForDate
  -> 6 of the 8 are absent from src/engine/engine.js

0 of 14 F04 checks could be re-pointed.
```

**Part two: is the overlap actually equivalent?** For the four things both
modules implement, every decision on every input tested agrees:

```
resolveBasis vs basisForDate   10 of 10 inputs agree (5 valid, 2 outside the
                               window, 1 unusable, 1 blank, 1 null)
windowOf vs basisWindow         3 of 3 agree
basisById                       3 of 3 agree
costForDate                     4 of 4 agree
                               ---------------------------
                               20 of 20 comparisons agree
```

So today's answers match and there is no live arithmetic defect. That is not the
same as safety: two implementations of one decision that currently agree will
drift the first time one of them is edited, and the drift will be silent. The
retired copy also carries 14 functions with no counterpart in the engine
(`resolveBasis`, `windowOf`, `allWindows`, `forwardWindows`,
`declaredWindowsText`, `deriveEffectiveDate`, `comparableBases`, `costOnBasis`,
`authoriseOfferBasis`, `guardBasisUse`, `basisCompatibility`, `parseISODate`,
`isoFromHuman`, `bases`), including the whole basis-authorisation layer and the
check that refuses a forward cost on a recorded historical quantity.

Retained, and reported as the one pair where the duplication is real rather than
a test aimed at a dead file.

---

#### Pair 6 - the retired view layers: already done, verified

`tests/ux_flow.test.mjs` previously loaded `src/ui/render.js` and
`src/ui/views.js`. It now loads `src/ui/app.js`, the module the build actually
assembles, and it carries the reasoning in its own header. This was corrected
before this work began and was not touched here.

Verified rather than assumed. `tests/module_audit.py` still reports the file
under `render.js` and `views.js`, but the two remaining hits are not loads:

- line 77 defines `RETIRED_LAYERS = ['src/ui/views.js', 'src/ui/render.js']` so
  the suite can assert it does **not** load them;
- the assertion itself reads the build's module list to confirm neither is
  assembled.

Both are named strings, not `require` calls, and the obvious way to make the
audit output zero for this file would be to delete the assertion - which would
remove the guard. Left alone deliberately, with the reason stated in
`tools/module_audit.py`.

---

### What changed in the audit tools, and why

`tools/module_audit.py` is a raw text scan and it was measuring the wrong thing
in both directions.

**False positive, found by doing the work.** Repointing `fin_math` meant writing
a comment explaining which retired module it used to load - and the scan then
reported it as still loading it. A real load names a path inside quotes or comes
through the acceptance harness's `PATHS` map; prose does not. The scan now
matches those two shapes only.

**False negative, found by the fix.** The acceptance checks load modules as
`H.requireModule(H.PATHS.recipients)` and never write a path, so tightening the
scan made seven real retired loads disappear from the count. Two of them
(`tests/accept/_diag_attach.cjs`, `tests/accept/_diag_brief.cjs`) had been
invisible to the old scan all along. The harness map is now parsed from
`tests/accept/lib/harness.cjs` itself and its keys resolved, so the count went
*up* rather than down.

**Tombstones counted separately.** A retired entry whose file has been deleted is
not a live duplicate. It is listed under its own heading instead of being
counted, because counting it would make the number wrong in the other direction.

The honest limitation is recorded in the generated report rather than left for a
reader to discover: the scan still cannot tell a load from a module named in a
string for an assertion, which is exactly what `tests/ux_flow.test.mjs` does on
purpose. `tests/accept/guard_09_module_scope.cjs` is the authority, and it reads
the in-file declarations.

### Before and after

| Measure | Before | After |
|---|---|---|
| `module_audit.py` - test files loading a source module | 15 | **18** (harness-form loads now detected) |
| `module_audit.py` - of those, loading a retired one | **11** | **11** |
| ... of which are genuine misdirected loads | 2 (`fin_math`, `export_shipped`) | **0** |
| `tests/fin_math.test.mjs` | 58/0 against a retired copy | 58/0 against the shipped engine |
| `tests/export_shipped.test.mjs` | names recipients in prose only | never loaded it - removed from the count |
| `tests/data_contracts.test.mjs` | 70/0 | **74/0** (four VAT-unit checks added) |
| `tests/run_tests.cjs` | 60/0 | 60/0 |
| `tests/case_store.test.mjs` | 27/0 | 27/0 |
| `tests/export_bytes.test.mjs` | 11/0 | 11/0 |
| `tests/market_evidence.test.mjs` | 32/0 | 32/0 |
| `tests/ux_flow.test.mjs` | 14/0 | 14/0 |
| `orphan_audit.py` | 1 orphan (`src/data/comparable.js`) | **0 orphans** |
| `retirement_safety_check.py` | SAFE | SAFE |

The retired-load count staying at 11 is the correct outcome and not a failure to
make progress. What changed is that the eleven are now *justified*: the pairs
that could be repointed were repointed and the two genuine misdirected loads are
gone, while the ones holding behaviour the shipped modules do not have are
retained with the gap named.

One movement in that table is not mine: `orphan_audit.py` went from 1 orphan to 0
and the shipped list from 9 to 10 because the market-evidence developer wired
`src/data/comparable.js` into `MODULES` while this work was running, not because
of any change here.

---

## Part 2 - The VAT unit defect

### The mechanism

`src/data/evidence.js`, `adjustToComparable()`, computed:

```js
var net = value / (1 + rate / 100);
```

The `/ 100` in that expression is the whole fault. It is not a wrong formula; it
is a formula that quietly assumes the rate arrives as a **percentage**. The
payload stores it as a **fraction** (`vat: 0.2`). Handing `0.2` to a rule that
expects `20` divides by `1.002` instead of `1.20`, which removes 0.2% of the tax
and leaves the rest in the figure.

On the row that exposed it:

| | amount | rate read as | net |
|---|---|---|---|
| Correct | 76.99 GBP incl. 20% VAT, at the payload's documented 1.17 EUR/GBP | 20% | **EUR 75.07** |
| The fault as written | same | 0.2 read as 0.2% | EUR 89.90 |
| | | | **19.8% too high** |

The direction matters more than the size. Overstating a competitor's price by a
fifth is exactly the inference `MARKET-05` exists to prevent: an advertised
retail price is not proof that our own net terms are too high, and a figure that
inflates it by 20% manufactures that proof.

### The unit was resolved from the data, not assumed

`node tools/_vat_unit_probe.cjs` tests the payload's own `net` column against
both readings:

```
seller                 price     vat   net(payload)   price/(1+vat)   price/(1+vat/100)
AUTODOC UK            76.99    0.2   64.1583        64.1583 YES     76.8363
Truckstop Group       77.7     0     77.7000        77.7000 YES     77.7000 YES
AUTODOC Portugal      22.49    0.23  18.2846        18.2846 YES     22.4384
Ashika France         25.2     0.2   21.0000        21.0000 YES     25.1497
Balleydier Parts      18.03    0     18.0300        18.0300 YES     18.0300 YES

rows with price, vat and net : 5
fit as a FRACTION           : 5
fit as a PERCENT            : 2  (both zero-VAT rows, where both units agree trivially)
```

Five of five rows fit a fraction, including all three rows where the two units
would give different answers. The two rows that also fit a percentage are the
zero-VAT rows. The payload proves its own unit, so this needed no assumption.

### The choice, and why

Two options were open: hold the rate as a fraction throughout and adjust the
divisor, or declare the unit on the records. **The unit is declared, and the rule
accepts one unit only.**

The reason is that a fraction-held convention is only safe while every caller
copies the convention correctly. Nothing would enforce it, the field is called
`vat_rate` and not `vat_rate_fraction`, and the payload's own field is `vat`. The
next adapter written against it would be one careless `/100` away from the same
defect in the other direction. A declared unit is checked at the boundary
instead, and a wrong declaration is refused rather than computed.

What this looks like end to end:

1. The observation record carries `vat_rate` **and** `vat_rate_unit`.
2. `src/data/comparable.js` converts a declared fraction to a percentage
   (`round2(rate * 100)`) and passes the unit it used.
3. `src/data/evidence.js` accepts `vat_rate` as a percentage and requires
   `vat_rate_unit === 'percent'`. It records both on the step it writes.
4. A row whose unit is not declared leaves the amount **unresolved**. Not
   guessed, not defaulted, not zero.

`src/data/comparable.js` already refused to infer the unit from the size of the
number and returned `VAT_RATE_UNIT_NOT_STATED`. That refusal is correct and is
unchanged. What was missing was the other half: the rule it calls was still
willing to guess, and the unit was not travelling with the value.

### The refusal is not weakened

This is asserted, not asserted-about. A `0.2`-shaped rate with no declared unit
is refused, and that is the check that would have to be deleted for this defect
to come back:

```
$ node -e "..."   # the same amount, no declared unit
ok=false  value=null
the observation carries a tax rate of 0.2 but does not state whether that is a
percentage or a fraction
```

There is a matching negative test in the suite
(`MARKET-04a`), and a regression test (`MARKET-04b`) that proves the digits do
not decide the unit: `0.2` declared as a percentage removes 0.2% and returns
119.76, `20` declared as a percentage returns 100.00. A rule that "helpfully"
treated a small number as a fraction would collapse those two into one answer and
fail that check.

Four checks were added to `tests/data_contracts.test.mjs` for this:

| Check | What it holds |
|---|---|
| `MARKET-04a` | An undeclared unit leaves the amount unresolved, and the unit is the *only* thing missing |
| `MARKET-04b` | Declared as percentages, `0.2` and `20` differ; nothing infers from magnitude |
| `MARKET-04c` | An unrecognised unit (`'twenty percent'`) is refused, not coerced |
| `MARKET-04d` | A declared fraction is converted before the call, and the old 19.8%-high answer is not returned |

Two existing checks were updated rather than relaxed. `MARKET-04` in
`tests/data_contracts.test.mjs` passed a bare `vat_rate: 20` twice; both calls now
declare `vat_rate_unit: 'percent'` and the expected figures are unchanged - what
changed is that the unit is stated rather than inferred. Its new assertion
(`steps[0].rate_unit === 'percent'`) checks that the rule records the unit it
used, which the old rule never did.

### Before and after, on the row

| | Before the fix | After the fix |
|---|---|---|
| AUTODOC UK, 76.99 GBP incl. 20% VAT, 1.17 EUR/GBP | EUR **89.90** | EUR **75.07** |
| Error against the correct net | +19.8% | 0 |
| The same row with no declared unit | silently computed at a guessed magnitude | refused: `ok: false`, `value: null` |
| The unit in the recorded step | absent - the rule's own prose asserted "20%" while it had been given 0.2 | `rate: 20, rate_unit: 'percent'` |

---

## What was not resolved

Three things are reported rather than closed, because closing them would mean
changing another developer's file or making a decision that is not mine.

1. **`tools/build.py` still lists the deleted `src/engine/pricing.js`.** The entry
   is a labelled tombstone. Pruning it needs the matching change to
   `tests/accept/guard_09_module_scope.cjs` G04, which asserts that path
   classifies as retired. That guard belongs to the acceptance reviewer, so the
   two changes go together and the integration owner should make them.

2. **`src/data/costbasis.js` is a live duplication of the engine's basis
   resolution.** Twenty of twenty decisions agree today and the basis suite
   cannot be repointed. This is the one pair where the hazard is real: two
   implementations of one decision, currently in step. Folding the fourteen
   retired-only functions into `src/engine/engine.js` and re-pointing the fourteen
   checks is the durable fix, and it is a build, not a repoint.

3. **The case lifecycle does not ship.** `src/case/store.js` and
   `src/case/schema.js` hold the whole proposal-to-outcome state machine and 27
   passing checks. The shipped store has no `create()` and no `transition()`.
   Either the capability is meant to ship - in which case it needs wiring, not
   deleting - or it is retired on purpose, in which case the 27 checks should be
   moved to whatever carries the lifecycle instead. Both answers are the
   integration owner's to give.

4. **A concurrent suite has one failing assertion, and it is not this work.**
   `tests/ux_market.test.mjs` appeared in the tree while this work was running
   (it is untracked and was absent from `tools/module_audit.py` at the start).
   It reports 11 pass / 1 fail. The failure is `MK02`, which asserts the price
   position screen renders:

   ```
   Every row the panel read was retained</span><b>yes
   ```

   and the screen now renders `...<b><span class="mk-tip" data-tip="...">yes</span>`.
   The value is wrapped in a tooltip element that the assertion does not expect.
   That is a view-layer change under `src/ui/`, made by the agent who owns that
   file, and its own test has not been updated to match yet.

   This is recorded rather than fixed for two reasons: `src/ui/` is out of scope
   for this work, and the failure is not caused by anything changed here. The
   evidence for that is in the assertion itself - it concerns markup the data
   layer does not produce - and in `MK07` ("a row whose tax-rate unit is not
   declared shows unresolved, and is not converted") and `MK10` ("no banned label
   and no invented figure reaches the price-position screen") both passing, which
   are the two checks in that suite that the tax-rate work could have reached.
   The owner of `src/ui/` should update `MK02` or the tooltip wrapper, not this
   developer.

---

## Commands used

```
python tools/module_audit.py
python tools/orphan_audit.py
python tools/retirement_safety_check.py

node tests/run_tests.cjs --payload payload/aim_payload_20260922.json
node --test tests/fin_math.test.mjs
node --test tests/data_contracts.test.mjs
node --test tests/market_evidence.test.mjs
node --test tests/case_store.test.mjs
node --test tests/export_bytes.test.mjs
node --test tests/export_shipped.test.mjs
node --test tests/ux_flow.test.mjs
node --test tests/ux_reopen.test.mjs

powershell -ExecutionPolicy Bypass -File tests\run_all.ps1
node tools/_vat_unit_probe.cjs
```

The payload is excluded from version control (`.gitignore: payload/*.json`) and
was regenerated by another agent during this session, so its SHA-256 moved from
`477bd0b41cda8f3d` to `6aea4a23ef43a399` part-way through. Every count above was
taken after the change and is reported against the current file. The arithmetic
input is synthetic throughout; the real payload was read for arithmetic and cited
by field name, and no price list, supplier cost table or customer data was copied
into any file created here.

Two other agents were working in the same tree while this was done: one in
`src/ui/` (which produced `tests/ux_market.test.mjs` and the tooltip wrapper that
`MK02` does not yet expect) and the owner of `src/data/comparable.js`'s wiring
into `tools/build.py`. Neither was edited here. `src/ui/app.js` and
`tests/ux_market.test.mjs` show as modified or untracked in `git status` because
of that concurrent work, not because of this one.

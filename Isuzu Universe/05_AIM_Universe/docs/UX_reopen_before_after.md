# AIM Universe — reopening a saved case (view layer)

Corrective build, 22 September 2026. This is the record for the two defects that
were in my area: what was wrong on screen, what it does now, and the command that
shows it.

The defect numbers are the reviewer's, from `tests/accept/`.

Nothing here is deployed, committed or pushed. Nothing under `src/engine/`,
`src/data/`, `src/case/`, `src/output/` or `tools/build.py` was edited.

---

## The short version

A saved case did not come back. You opened a case you had already priced, and the
page showed a record that was neither what you saved nor a clean starting point.

The saved revision on disk was always intact — `J08` and `J09` passed before any of
this. What was broken was the page's own reading of it.

Two separate faults, both in the same four lines:

1. The restore ran before the address was read, so it looked the case up under the
   wrong id and found nothing.

2. The restore then called the store's *edit* function to write the saved values
   back. Editing is not restoring. `set()` diffs the patch, and any difference
   bumps the version and re-derives the record's own id. So the page landed one
   version behind the revision it had just read — `ITUK-PADS:v2` on screen against
   `ITUK-PADS:v3` on disk.

The first was already fixed before I started. I fixed the second, and there was no
way to reach the acceptance criterion without it, because the version and the
record id are two of the seventeen keys the check compares.

---

## Defect 1 — reopening a saved case showed the wrong revision

**Reported as.** ACCEPT-02 `J10-*`: five failures, one per case.
`matches_saved_revision: false` **and** `matches_a_fresh_default: false` — a third
state, not the saved revision and not a default.

**What I measured first, before changing anything.**

```
powershell -ExecutionPolicy Bypass -File tests\run_all.ps1
```

`ACCEPT-02  47 pass / 5 fail / 52`. The five failures were `J10-ITUK-PADS`,
`J10-IMOTORS-CABIN`, `J10-ITUK-TURBO`, `J10-ITUK-DISCS`, `J10-IMOTORS-OIL`.

Then the actual difference, which is one field, so I want to be exact about it:

```
python -c "import json;d=json.load(open('tests/accept/_out/accept_02_journey.json'));\
[print(r['id'],r['status']) or print('  saved:',json.loads(r['evidence'])['saved']['scenario_id'],\
' live:',json.loads(r['evidence'])['live']['scenario_id']) for r in d['results'] if r['id'].startswith('J10')]"
```

```
J10-ITUK-PADS     FAIL   saved: ITUK-PADS:v3     live: ITUK-PADS:v2
J10-IMOTORS-CABIN FAIL   saved: IMOTORS-CABIN:v3 live: IMOTORS-CABIN:v2
J10-ITUK-TURBO    FAIL   saved: ITUK-TURBO:v3    live: ITUK-TURBO:v2
J10-ITUK-DISCS    FAIL   saved: ITUK-DISCS:v3    live: ITUK-DISCS:v2
J10-IMOTORS-OIL   FAIL   saved: IMOTORS-OIL:v3   live: IMOTORS-OIL:v2
```

Only `scenario_id` differed. Every one of the other sixteen compared keys — the
prices, the quantities, the cost basis, the selected option, the objective — was
already identical. `scenario_id` carries the version number, and it read `:v2` on a
page whose saved revision was `:v3`.

**Cause.** The store has one write path for a change and I had been using it for a
restore. `src/data/scenario.js` `set()` ends with:

```javascript
var changes = contracts.diff(current, next);
if (changes.length) {
  next.version = current.version + 1;
  next.scenario_id = caseId + ':v' + next.version;
}
```

So restoring a v3 record onto a fresh v1 record wrote the saved *values* but called
the result v2. The page then described itself as a version that had never been saved.

**Fix.** In `src/ui/app.js`, the restore no longer goes through `set()`. It is now a
named function, `restoreSavedScenario(caseId)`, which writes the saved revision onto
the working record with its own `version` and `scenario_id` intact, carrying only
fields the scenario contract declares. Reopening is the only caller. Switching case
inside a live session deliberately does not call it, so an unsaved edit is not
silently thrown away by a case click.

`scenario()` also stopped having a side effect. It used to be `store.get(state.caseId)`,
and `get()` in the shipped store materialises a default record for whatever id it is
handed — so a helper named "read the scenario" was creating a record for the *wrong*
case on a `__none__` address before the restore ran. It now returns null when no case
is named, and the caller decides.

**After.**

```
powershell -ExecutionPolicy Bypass -File tests\run_all.ps1
```

`ACCEPT-02  52 pass / 0 fail / 52`. Re-run to confirm it holds:

```
ACCEPT-02  52 pass / 0 fail / 52     (second consecutive full run)
```

And the five checks specifically:

```
PASS J10-ITUK-PADS     matches_saved_revision=True   matches_a_fresh_default=False
PASS J10-IMOTORS-CABIN matches_saved_revision=True   matches_a_fresh_default=False
PASS J10-ITUK-TURBO    matches_saved_revision=True   matches_a_fresh_default=False
PASS J10-ITUK-DISCS    matches_saved_revision=True   matches_a_fresh_default=False
PASS J10-IMOTORS-OIL   matches_saved_revision=True   matches_a_fresh_default=False
```

**Developer test beside it.** `tests/ux_reopen.test.mjs` drives the same load
sequence in Node, on the shipped modules, with the reviewer's seventeen-key list
copied rather than paraphrased:

```
node --test tests/ux_reopen.test.mjs
```

```
✔ a saved revision reopens into the live scenario, on every compared key
✔ the reopened record keeps the saved version and record id instead of treating a restore as an edit
✔ a quantity derived from the selected alternative survives the reopen as a value, not as a re-derivation
✔ a case with no saved revision still opens on its fresh default
✔ the restore carries only declared scenario fields, and never an undeclared one
✔ only the reopened case is restored; the other cases keep their own defaults
✔ the reopened page reports the same consistency verdict as the saved revision
ℹ tests 7 / pass 7 / fail 0
```

The third one is the specific worry named in the brief. `quantity_after` is derived
when an alternative carries a volume assumption, and is `null` in a fresh default. In
this payload the case that exercises it is `ITUK-PADS`: default `null`, saved `1750`.
It survives as a value on the record, so the reopen neither re-derives it nor falls
back to `null`.

I checked the test can actually catch the defect rather than passing for its own
reasons. Putting the pre-fix restore back and re-running gives:

```
ℹ tests 7 / pass 3 / fail 4
AssertionError: ITUK-PADS: the reopened page does not show the saved revision.
  Differences: scenario_id: "ITUK-PADS:v2" -> "ITUK-PADS:v3"
AssertionError: ITUK-PADS: the reopen bumped the scenario version (3 on disk, 2 live). A restore is not an edit.
AssertionError: ITUK-PADS: not restored
AssertionError: record id moved on reopen
```

Three other cases did not exercise a restart and still passed, which is correct —
they are the controls.

**What the reopened tab shows.** Not only a JSON verdict. `_qa\_qa_reopen_text.py`
repeats the save, closes Chrome, reopens the Internal-action tab and reads the
labelled values the reader actually sees:

```
python _qa\_qa_reopen_text.py
```

```
ITUK-PADS      differences=[]  saved=ITUK-PADS:v2 live=ITUK-PADS:v2
  Selected option PADS-VOL · Scenario version 2 · Proposed net price €77.32
  Revenue change +€15,036 · Gross-profit change −€2,040
  One scenario, checked — "The selected option, the manual inputs and the saved record use one scenario."
IMOTORS-CABIN  differences=[]  Selected option CABIN-BVP
ITUK-TURBO     differences=[]  Selected option TURBO-INC
ITUK-DISCS     differences=[]  Selected option DISC-BVP
IMOTORS-OIL    differences=[]  Selected option OIL-NONE
```

Zero differences on all five, no page error on any reopened session, and the
consistency panel on the reopened tab states that the selected option, the manual
inputs and the saved record agree. Raw: `_qa\reopen_after\reopen_text_evidence.json`.

---

## Defect 2 — ACCEPT-04 `D03` was a false positive

**Reported as.** `D03` reported 8 hits of "a brief contains another participant's
customer", which would either block a legitimate release or teach a reader to ignore
the check.

**It was not a disclosure, and I confirm that independently of the reviewer.** The
payload has five cases and two customers: `ITUK` on PADS, TURBO and DISCS; `I Motors`
on CABIN and OIL. So every pair of cases sharing a customer produced a hit. All eight
were a brief of ITUK containing "ITUK", or a brief of I Motors containing "I Motors".
No other case's id appeared in any brief, and no other case's part number did.

The old comparison asked "does this brief contain another case's customer name",
without ever asking whose customer that name is. A name that is the brief's own
customer is not another participant.

**Fix — detection, not product.** `D03` now asserts that a brief carries no other
case's **id**, no other case's **part number**, and no **distinct** customer (its own
customer excluded). The original comparison is still in the file, reproduced inside
the check and recorded under `d03_superseded_comparison` with the eight original
findings and the reason it was superseded, so nothing is deleted and the reviewer can
see what it used to say.

**It is not vacuous.** I crafted a leak — one brief of ITUK carrying `I Motors`,
the case id and the part number the case actually holds — and the corrected
check refuses it:

```
FAIL D03: cross-participant content:
["ITUK-PADS_leakprobe_participant_brief.out contains the case id of IMOTORS-CABIN",
 "ITUK-PADS_leakprobe_participant_brief.out (customer \"ITUK\") contains the customer \"I Motors\" of IMOTORS-CABIN",
 "ITUK-PADS_leakprobe_participant_brief.out contains the part number of IMOTORS-OIL",
 "ITUK-PADS_leakprobe_participant_brief.out (customer \"ITUK\") contains the customer \"I Motors\" of IMOTORS-OIL"]
```

The probe file was deleted afterwards, and the real run is:

```
node tests/accept/accept_04_participant.cjs
```

`PASS D03 ... Superseded comparison would have reported 8 hit(s); all were the
brief's own customer.` `ACCEPT-04  13 pass / 0 fail / 13`.

---

## Before and after

| Check | Before | After |
|---|---|---|
| ACCEPT-02 complete browser journey | **47 pass / 5 fail** of 52 | **52 pass / 0 fail** of 52 |
| ACCEPT-04 participant-facing output | **11 pass / 2 fail** of 13 | **13 pass / 0 fail** of 13 |

Both measured with `powershell -ExecutionPolicy Bypass -File tests\run_all.ps1`.
Full console output: `_qa\BEFORE_run_all.txt`, `_qa\AFTER_run_all_1.txt`,
`_qa\AFTER_run_all_2.txt`, `_qa\FINAL_run_all.txt`.

`D13` in ACCEPT-04 also went from FAIL to PASS in that run. That is a real change
but it is not mine: `src/data/export.js` was being edited by another agent at the
same time, and the rebuilt artifact now carries that agent's version of the module.
`ACCEPT-04`'s before-count of 11/2 includes that failure, so if it is counted out,
`D03` alone accounts for 12 pass / 1 fail of 13 before and 13/0 after.

---

## What remains

Still failing, and all outside this task's two defects — these are the reviewer's
other findings and none of them was in my area:

- `BASE-ENGINE` 11 pass / 19 fail of 30. The frozen v03 baseline; a failure there is
  *expected* and is what the baseline exists to show.
- `BASE-BROWSER` no result file in any run. This is an environment fault, not a
  product verdict: the log ends with `Executable doesn't exist at
  C:\Users\jerom\AppData\Local\Temp\cursor-sandbox-cache\...\chromium_headless_shell-1208\...`
  and `playwright install`. That check drives the frozen page and does not touch the
  built artifact, so it cannot say anything about this fix either way.
  `ACCEPT-02` does run Chrome for real, because it is given the installed
  `chrome.exe` by `run_all.ps1`.
- `ACCEPT-01` 46 pass / 1 fail of 47 — `R27`, candidate records declaring their
  reporting period. Engine/candidate area.
- `ACCEPT-03` 16 pass / 1 fail of 17 — `C17`, the conservation check after a row is
  set aside. Conservation area.
- `SAFE-05/08` 14 pass / 2 fail of 16 — `S09b` (a restricted word hidden inside a
  compound file name is accepted) and `S10c` (the internal record no longer carries
  its declared limits). Safety/export area.

`R27`, `C17`, `S09b` and `S10c` are identical before and after this fix and were
already failing in the 47/5 and 11/2 baselines. `D13` in ACCEPT-04 is the only
status change in that file that is not mine — `src/data/export.js` was being edited
by another agent while I worked, and the rebuilt artifact now carries that agent's
version of the module. `S10c`'s failure names that same module.

---

## A fault in a check rather than in the code

One candidate, and I am not asserting it as settled.

`J10` compares seventeen scenario keys including `scenario_id`, which is a
**derived** field: the store builds it as `<case>:v<version>`. Comparing a derived
identifier means the check is sensitive to the version number of the page's working
record, which is bookkeeping rather than commercial state. In the defect above that
sensitivity is exactly what caught the fault, so I am not asking for it to be
removed.

I am flagging the consequence: because `scenario_id` embeds `version` and `version`
is not on the compared list, a page that showed the right numbers but an incremented
version would pass — the id moves with it. The version is visible to the reader on
the Internal-action tab ("Scenario version 2"), so if the reviewer wants that to be
part of the contract it needs its own key on the list rather than riding along
inside `scenario_id`.

`tests/ux_reopen.test.mjs` asserts `version` directly, separately from `scenario_id`,
so the developer test covers what the acceptance key list leaves implicit. I did not
change `J10`'s comparison: it was not wrong.

---

## Files

Changed:

- `src/ui/app.js` — `restoreSavedScenario()` replaces the patch-through-`set()`
  restore; `scenario()` no longer materialises a default for an unnamed case.
- `tests/accept/accept_04_participant.cjs` — `D03` comparison only; the original is
  retained and recorded.
- `tests/ux_reopen.test.mjs` — new.
- `docs/UX_reopen_before_after.md` — new.

Not changed: `src/engine/`, `src/data/`, `src/case/`, `src/output/`,
`tools/build.py`, `tests/run_tests.cjs`, `tests/accept/accept_02_journey.py`.
`dist\` was regenerated by `tools/build.py` because the acceptance journey runs
against the built artifact:

```
python tools/build.py --payload payload/aim_payload_20260922.json
```

`built ... bytes 5108633 ... sha256 3127e7349555442b24b937a061359fff85b5a414ba51fdd53bacd99d0236fd6b
labels: clean`

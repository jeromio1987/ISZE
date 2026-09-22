# Verification of the AIM Universe pricing component

Written by the independent verification reviewer, 22 September 2026.

This document was rewritten on the same day. Anything it said before about the
baseline browser step reporting a dash, about SAFE-05 S09b and S10c failing
because of the attachment name check and the limits block, or about there being
four, five or six open defects, described an earlier revision of this suite and
not the one that is on disk now.

## The short version

Two fixes were made at that step, and both were in my own files. No product code
was touched.

The baseline browser check now runs and reports a real count, 29 pass and 1 fail
against the untouched frozen file. When the task reached me it was writing no
result at all, and the cause was three separate faults in the harness: a flag that
does not exist, a browser path that resolved to an empty folder, and a variable
that ACCEPT-02 leaves pointing somewhere else by the time the step runs. One of
those three had already been patched by another agent before I started - the
summary was no longer showing a dash when I arrived, it was showing 29/1 by luck
of ordering - so what I actually added is that the working path is now explicit,
documented and chosen on purpose rather than accidental. The full chronology is in
the result table below.

Two safety checks were asking the wrong module. SAFE-05 S09b and S10c were
interrogating `src\output\recipients.js`, which `tools\build.py` lists as a
duplicate export builder and does not put into the artifact. They have been
pointed at `src\data\export.js`, the module that actually decides what a
distributor receives. Both pass there. The retired module's answers are kept
beside them as recorded evidence, not deleted.

One new check, GUARD-09, exists so this cannot happen quietly again. It reads the
two module lists out of `tools\build.py` and refuses to let an acceptance check
load a module the build does not assemble unless the check says, in its own file,
why it is asking that copy.

One thing is still open, and it was open before: R27, the candidate records carry
no reporting period. That is a gap in the data, not in the code, and no code fix
closes it.

Nothing here is an approval. It is evidence about behaviour, and it authorises no
price, no cost, no mail, no deployment and no purchase.

## What was tested, and how to reproduce it

One command runs everything:

```
powershell -ExecutionPolicy Bypass -File tests\run_all.ps1
```

Add `-SkipBrowser` to leave out the browser journey, `-SkipBaseline` to leave out
the reproduction of the original review, or `-BaselineFileUrl` to make the
baseline browser step open the frozen file through a real address instead of in
memory. The combined report goes to `tests\accept\_out\run_all_summary.json`, and
the full console output of every step to `tests\accept\_out\*.log`.

## Result, before and after

Measured on this machine, same command.

The "before" column is the run captured at 13:16:59, which is the state the task
brief described. There is one honest complication to state before the table: a
partial fix to the baseline call had already landed between that snapshot and my
first run, by another agent. At 13:41:04 the baseline step was already printing
29/1/30 rather than a dash, because the broken `--chrome` flag had been replaced
by `--memory` and the step happened to inherit a working browser path from
ACCEPT-02. My contribution to that step is therefore not "the dash was fixed"; it
is that the working path was accidental, and is now explicit, documented and
chosen. The rows below compare the brief's snapshot against my final run, so the
BASE-BROWSER cell describes the whole corrective effort rather than my part of it.

| Check | Before: pass/fail/total | Before exit | After: pass/fail/total | After exit |
|---|---|---|---|---|
| BASE-ENGINE | 11 / 19 / 30 | 1 (correct) | 11 / 19 / 30 | 1 (correct) |
| BASE-BROWSER | – / – / – (no file written) | 1 | 29 / 1 / 30 | 1 (correct) |
| ACCEPT-01 | 46 / 1 / 47 | 1 | 46 / 1 / 47 | 1 |
| ACCEPT-02 | 52 / 0 / 52 | 0 | 52 / 0 / 52 | 0 |
| ACCEPT-03 | 16 / 1 / 17 | 1 | 17 / 0 / 17 | 0 |
| GUARD-09 | did not exist | – | 5 / 0 / 5 | 0 |
| ACCEPT-04 | 13 / 0 / 13 | 0 | 13 / 0 / 13 | 0 |
| SAFE-05 / SAFE-08 | 14 / 2 / 16 (15 / 1 / 16 by 13:41) | 1 | 16 / 0 / 16 | 0 |
| **Non-zero checks** | **5** | | **3** | |

All three remaining non-zero exits are correct and expected. BASE-ENGINE and
BASE-BROWSER are the supplied review being reproduced against the untouched
frozen file, where the defects are real and must still show. ACCEPT-01 carries one
genuine, unfixed data gap.

Three counts in that table need their story, because a changed number with no
story is how a suite starts lying:

- **ACCEPT-03 went from 16/1 to 17/0 with no edit from me.** Its C17 conservation
  defect - a set-aside row counted twice - was fixed by another agent between my
  two runs. I re-ran it and confirmed C17 now passes; I did not verify the fix
  itself line by line.
- **SAFE-05 went from 15/1 to 16/0 because of my re-pointing, not because an
  assertion was dropped.** The suite still has the same sixteen assertions. The
  one that used to fail now asks the module that ships. The 13:41 intermediate
  reading of 15/1 is the same assertion still pointing at the retired module.
- **GUARD-09's five are new.** They are the only count in the table that grew
  because something was added.

Several checksums moved while I worked and none of the movements are mine:
`src\data\candidates.js`, `src\data\evidence.js`, `src\ui\app.js`,
`tools\build.py` and the built artifact were all still being written by other
agents. The suite prints every checksum at the top of each run, so a reader can
always tell which revision answered. It also now prints which source modules the
run loads and whether the build assembles each one.

## The revision this run tested

Read from `tests\accept\_out\run_all_summary.json` of the final run.

| File | SHA-256 (first 16) |
|---|---|
| `src\engine\engine.js` | `1db7f3fb6fa8f399` |
| `src\data\export.js` | `fc8ba0a0bd4eef95` |
| `src\output\recipients.js` | `868db5c4d9afb2eb` |
| `src\data\contracts.js` | `56a534134c13307d` |
| `src\ui\app.js` | `2b7d10859b68a0e7` |
| `src\data\candidates.js` | `73b7961c8252e95a` |
| `src\data\evidence.js` | `e96cdc38fff63e93` |
| `tools\build.py` | `f4d7f136cd333299` |
| `dist\ISZE_AIM_Pricing_Decisions_v04_INTERNAL.html` | `a35cf047b9aeb7c6` |
| `reference\ISZE_AIM_Pricing_Decisions_v03_FROZEN.html` | `7494cea1955be820` |

The frozen reference matched the checksum named in the brief exactly, on every run
today.

`src\ui\app.js` moved **three** times while I worked, while another agent was
editing it: `a966ad402336c1f6`, then `534bdc346b5330c8`, then `2b7d10859b68a0e7`
which is what my final run tested, and it is `bd13791e86db21ad` as I write this.
Every count in the table above is identical across the revisions I ran against.
`tests\accept\_out\run_all_summary.json` holds the authoritative checksum set for
the final run; if the file on disk differs from the table, the table describes an
older revision and the run should be repeated. I did not test
`bd13791e86db21ad`.

The files I changed, and their checksums after the change:

| File | SHA-256 (first 16) |
|---|---|
| `tests\run_all.ps1` | `4c385d53d234aaa6` |
| `tests\accept\run_all.ps1` | `97230afd64feb1e3` |
| `tests\accept\accept_01_engine.cjs` | `fae5dff7cbf6fcd6` |
| `tests\accept\accept_04_participant.cjs` | `00b29d29be6feeda` |
| `tests\accept\accept_05_08_safety.cjs` | `5f2d98e87365cc0c` |
| `tests\accept\guard_09_module_scope.cjs` | `b8a741f22e1cb48b` |
| `docs\VERIFICATION.md` (this file) | not quoted - see below |

This document's own checksum is deliberately not printed: every correction to it
changes the number, so a quoted value is wrong the moment it is typed, and I
already chased that three times while writing this. The authoritative record of
which product revision was tested is `tests\accept\_out\run_all_summary.json`,
which is written by the run and not by hand.

`tests\accept\lib\harness.cjs` is unchanged at `ad69a042fe0ab930`; I read it and
did not need to edit it. Nothing under `src\`, `tools\` or `dist\` was modified by
me. No commits, pushes or deployments were made.

## Item 1 — the baseline browser check

**What was wrong.** Three faults, all in `tests\accept\run_all.ps1`, none in the
product:

1. The step passed `--chrome <path>`. `06_Working\AIM_v03_HANDOFF_20260922\tests\review_browser.py`
   so argparse stopped the script before a browser was ever launched and no JSON
   was written. The summary then showed a dash, which read like "not applicable"
   rather than "did not run".
2. With no browser flag at all, Playwright resolves through
   `PLAYWRIGHT_BROWSERS_PATH`. In this environment that variable points into a
   sandbox cache that contains no browser, so the launch died with
   "Executable doesn't exist ... chrome-headless-shell.exe".
3. A third cause that only appears in a full run. ACCEPT-02 sets
   `PLAYWRIGHT_BROWSERS_PATH` to the machine's real install and never puts it
   back. The baseline step runs before that, so it inherits whatever was set when
   the shell started. Run by hand from a fresh prompt it worked; inside the suite
   it could fail again. The step now restores the variable after it runs.

**Which load mode, and what it accepts.** The supplied review says in its own
docstring that in-memory mode is for environments that prohibit file navigation,
and that it does not test file-origin storage, a Windows launcher, hosting or
cross-user permissions.

I measured both modes on this machine:

```
in-memory (`--memory`)    -> {"pass": 29, "fail": 1, "total": 30}, exit 1
real file address (no flag) -> {"pass": 29, "fail": 1, "total": 30}, exit 1
```

Both give the review's baseline exactly, so the mode is not what decides the
number. **I chose in-memory as the default**, for two reasons: it is the mode the
review published its baseline in, and it is the one that still runs if a real file
navigation is ever blocked here.

What that mode does accept: the exact bytes of the frozen file, rendered in a real
Chromium, across all five cases and six views, with script errors captured and the
review's structural observations recorded. What it does not accept: anything about
file-origin behaviour. Storage origin, real navigation, the launcher, hosting and
per-user permissions are outside its reach, and a result from it is evidence about
the document rather than about how a person would open it. `-BaselineFileUrl`
switches to the real address; on this machine that also works, and on a machine
where it is blocked the step would fail for an environment reason rather than a
product one. The chosen mode is printed in the run and stored in the combined
report as `baseline_browser_load_mode`.

**The raw output**, `tests\accept\_out\baseline_browser_frozen.log` and the JSON
beside it:

```
{"pass": 29, "fail": 1, "total": 30}
ITUK-TURBO objectives ['v03fmtPct is not defined']
```

The single failure is the one the review named: the turbo case's Two objectives
view throws `v03fmtPct is not defined`. That is a real defect in the frozen file
and it should fail.

## Item 2 — the two SAFE-05 checks that asked the wrong module

`safe-05/08` went from 15 pass / 1 fail to 16 pass / 0 fail. Here is what changed,
and what did not.

**S09b, restricted words inside a compound file name.** The check asked
`recipients.canAttach(...)` on `src\output\recipients.js` and reported that the
five compound names below were accepted. That module is in `UNWIRED_MODULES` as a
"duplicate export builder" and is not assembled, so the finding described a copy
nobody receives. `src\data\export.js` is the builder the artifact uses.

Measured on both modules, same five names, same day:

| File name | `src\data\export.js` (shipped) | `src\output\recipients.js` (retired) |
|---|---|---|
| `supplier_cost_list_2026.xlsx` | refused, matched `supplier`, `cost`, `supplier cost` | accepted |
| `gross_margin_report.xlsx` | refused, matched `margin`, `gross margin` | accepted |
| `my_cost_file.xlsx` | refused, matched `cost` | accepted |
| `parts_purchase_price.xlsx` | refused, matched `purchase`, `price` | accepted |
| `invoices_2026.xlsx` | refused, matched `invoice` | accepted |

The shipped module refuses five of five. I re-checked independently rather than
taking the export agent's word for it; the agent's own suite is corroborating, not
the basis of this result.

**The requirement did not change.** The assertion is still "none of these five
names is accepted". It was re-pointed at the module that ships. It was not relaxed
to suit the retired module, and the retired module's five answers are stored in
the report under `s09b_retired_module_comparison` rather than deleted. If the
shipped builder ever stops catching them, the check fails and must stay failing.

**S10c, the internal record's own limits.** The check asked the retired module and
asserted `hardened.payload.limits.price_approved === false`. The retired module
carries the limits as an object with five named keys. The shipped module carries
them as an array of five statements, because a leaf name declared inside a section
in `contracts.js` is a declaration but not a form the shipped builder takes. The
same five facts survive, in words instead of as named keys.

The requirement, again unchanged: the internal record must state that no price is
approved, that the customer net price is unconfirmed, what the cost measure
excludes, that no raw invoices are carried and that no credentials are carried.
An empty or absent limits block is worse than none, because it reads as "the
question was considered".

The check now asserts the shipped record carries a non-empty limits block stating
all five facts, accepting either the array form or the named-key form. That
tolerance is deliberate: a check that accepted only the array form would report a
legitimate move to the contract's declared shape as a regression. I proved it can
still fail, against eight inputs:

```
live shipped answer          nonEmpty=true  factsLost=[]               assertion passes
REGRESSED: key dropped       nonEmpty=false factsLost=[all five]       assertion FAILS
REGRESSED: emptied array     nonEmpty=false factsLost=[all five]       assertion FAILS
REGRESSED: emptied object    nonEmpty=false factsLost=[all five]       assertion FAILS
REGRESSED: one fact lost     nonEmpty=true  factsLost=[three]          assertion FAILS
REGRESSED: generic filler    nonEmpty=true  factsLost=[all five]       assertion FAILS
retired module object form   nonEmpty=true  factsLost=[]               assertion passes
```

The retired module's answer is recorded under `s10c_retired_module_comparison`.

**Two further mis-pointed checks were found while doing this**, both in ACCEPT-01,
both asking the retired module for the same question the shipped module answers:

- **R25**, distributor output carries no direct cost field. Now asserted on
  `src\data\export.js`. The retired module's answer is recorded.
- **R26**, a nested direct-cost object is caught or refused. Now asserted on
  `src\data\export.js`. The retired module's answer is recorded.

**D13** in ACCEPT-04 was also re-pointed and its wording corrected. It used to
record that the shipped route failed the requirement "for the wrong reason" - the
note was dropped along with the container holding it, so nothing leaked and
nothing was disclosed either. The shipped builder now carries the containers and
checks the free text, so the requirement is asserted where it belongs.

**Where the retired module is still loaded, and why that is not the same fault.**
S06, S07, S08 and S11 ask about the permission table, the development identity and
the attachment-storage gap. No shipped module implements any of those, so a
failure there cannot be caused by a missing rebuild - it is a statement about what
the product does not implement. That distinction is the whole point of the guard
below: a check against unshipped code is only a misdirection when a shipped module
already answers the same question.

## Item 3 — the guard

`tests\accept\guard_09_module_scope.cjs`, run from `run_all.ps1` as the check
`GUARD-09`. Five assertions:

- **G01** every source module the harness can load is classified by the build as
  assembled or retired, so nothing is unaccounted for.
- **G02** no acceptance check loads a module from `UNWIRED_MODULES` unless the
  check file carries an explicit declaration naming it and giving a reason.
- **G03** every declaration names a module the check actually loads, and carries a
  reason. A declaration left behind after the load moved is a stale claim.
- **G04** the detector can see a retired module when one is named, so G02 is not
  vacuous.
- **G05** the positive form: the build assembles `src\data\export.js`, retires
  `src\output\recipients.js`, and the checks that judge participant output load the
  assembled builder.

Two decisions worth stating, because a simpler guard would have been wrong:

- **It reads the module lists out of `tools\build.py` rather than hardcoding
  them.** `tools\orphan_audit.py` reads them with one pattern over the whole file,
  which puts all nine retired modules into its "shipped" list as well - its output
  says 18 shipped when `build.py` assembles 9. That union is harmless for finding
  orphans, which is what it is for. A guard that has to tell the two lists apart
  cannot use it, so GUARD-09 reads the assembled list from before the
  `UNWIRED_MODULES` marker and the retired list from between that marker and
  `BANNED_IN_OUTPUT`.
- **It measures loads through `H.PATHS`, not by searching file text.** A module
  name appears in comments, in prose and in the recorded comparisons. Searching
  text reported four checks as mis-pointed when only three loads were real, and a
  detector that cries wolf gets tuned until it stops reporting the true positive.
  `H.PATHS` is the single door source modules come through, so a name in that map
  a check uses is a real load.

**Its actual output, in the correct state:**

```
PASS G01: Every harness path into src/ is classified by the build, so no module is unaccounted for
PASS G02: No acceptance check loads an unshipped module without declaring it in the file
PASS G03: Every declaration naming a retired module carries a reason and describes a load that exists
PASS G04: The guard can see a retired module when one is named, so G02 is not vacuous
PASS G05: The export builder that decides what a distributor receives is the assembled one, and it is asked
{"pass":5,"fail":0,"skipped":0,"total":5}
```

**Proof it can fail.** I added a temporary check file that loaded
`src\data\costbasis.js` - a real `UNWIRED_MODULES` entry - with no declaration, ran
the guard, and removed the probe afterwards.

```
FAIL G02: No acceptance check loads an unshipped module without declaring it in the file --
  [{"check":"accept_99_guard_falsification.cjs","module":"src/data/costbasis.js",
    "build_says":"overlaps the engine's basis resolution","also_loads":[]}]
{"pass":4,"fail":1,"skipped":0,"total":5}
```

The probe file was deleted and the guard re-run to confirm it was back to 5/0. The
first time I wrote the declarations into the check files, G02 failed on the three
real mis-pointed loads and named all three - so it was not written to pass, it was
written to report, and it did.

The suite now also prints a scope block before any check runs, showing which source
modules it loads and whether the build assembles each one. That is what makes the
guard's subject visible rather than inferred.

## What passed, and why that matters

The engine arithmetic, the ranking, the two objectives, the exports as bytes, the
hostile-content handling and the conservation of ordinary imports all behave
correctly across all five cases and six views.

- The objective re-ranks without moving anything else. Across all five cases,
  switching between revenue and gross profit produced the same alternatives with
  byte-identical prices, quantities and both results, and the working scenario was
  untouched. Only the order changed. Checks `J03-<case>` and `A14`.
- The participant file is clean and the internal file is not, which is what makes
  the participant result mean something. Cost, profit, margin, supplier discount
  and FX rate fields were checked for at every depth, plus another participant's
  part numbers and customer name. Checks `D01` to `D05`.

## What is still open

**R27 - candidate records declare no reporting period.** Unchanged and unfixed by
me. The candidate records in the delivered data carry no period or year field, so
an assertion that they declare their reporting period cannot pass. I kept the
original assertion exactly as supplied and added a second check beside it: the
screen now declares that the period is undeclared and refuses to promote a record
whose period is unknown. That is the right behaviour, but it does not make the
missing period exist. It needs the source to carry the period.

ACCEPT-01 is therefore 46 of 47. That is the only failing assertion in the
reviewer's suite that reports a product or data problem rather than a defect in
the frozen file being reproduced.

## Findings I could not fix, and one I did not touch

**Faults in checks, not in the code - four of them, all now corrected.** The four
assertions listed above as re-pointed were all of this kind. None of them
described a defect in what ships; each described a question put to the wrong copy
of a module. They are corrected, and the guard exists so the next one is caught at
the point it is written rather than at the point it is read.

**One assertion that reports a product or data problem, unchanged.** R27 in
ACCEPT-01. That one is a finding, not a fault in the check, and it must keep
failing until the source carries the period.

**A fault in a check I deliberately did not "fix".** S09, which asks the retired
module about the plain two-word name `supplier cost list 2026.xlsx`, passes. It
passes because that module does happen to catch the plain form, even though it
misses the compound form. I left it as it is rather than re-pointing it, as the
retired-module half of the S09/S09b pair: it is the only module that also exposes
the restricted flag and the storage gap, so it is doing real work there. Its
limitation is recorded in S09b rather than pretended away.

**A fault in a tool that is not mine.** `tools\orphan_audit.py` reports 18 shipped
modules, which is the union of the 9 assembled and the 9 retired. Its "Shipped"
section lists every retired module twice over. It also overwrites
`docs\ORPHAN_AUDIT.md` on every run. I did not change it - it is outside what I
own - but a reader should know that its shipped count is not the build's shipped
count. I ran it, and it reproduced the same numbers already in the file, so
nothing was made worse. GUARD-09 reads the lists correctly and is the count I would
rely on.

**Anything I did not verify myself is reported as unverified.** The export agent's
own suite, `node --test tests\export_shipped.test.mjs`, reports 25 passed and 0
failed, and the agent states the shipped module handles the five compound names
plus six more. The 25/0 is now corroborated by my own S09b and S10c, which I ran
and which report the module's own answers. The "plus six more" is the agent's
claim; I did not enumerate the extra six and I am not repeating it as established.

## What I could not test in this environment

I will not describe any of these as verified.

- **Server-side access control.** There is no backend, so there is nothing to
  test. A filter running in the browser is not access control, and the module says
  so itself. Nothing here should be read as evidence that a hosted page would be
  safe.
- **Real identity and tenancy.** The permission logic runs against the module's
  own development stand-in, and every result it returns says the person was not
  authenticated. Production sign-in, organisation membership and revocation are
  unimplemented.
- **File attachments.** The permission question is asked and answered; no file is
  stored, because there is no approved file store.
- **Multi-user behaviour.** Concurrent editing, ownership and cross-user
  isolation were not exercised.
- **The underlying commercial sources.** I did not verify the supplier
  workbooks, the exchange-rate authority, cost eligibility or any price. The
  engine's arithmetic is verified against synthetic figures; the figures
  themselves are not.
- **The real-file-address baseline mode, as the default.** I measured it once
  today and it gave the same 29/1 as in-memory does, but the suite runs in-memory
  by default, so the file-address path is checked by hand rather than on every
  run.
- **One environment fault, stated so it is not mistaken for a product fault.**
  Relaunching Chromium into an already-used profile directory, which the
  four-route export needs, kills the page intermittently with "Target page,
  context or browser has been closed". Each case therefore uses its own profile
  directory. This is a limitation of the machine, not of the product.

## Screenshots

ACCEPT-02 takes 15 screenshots into `tests\accept\_out\shots\`.

**Taken: 15. Read: 0, by me.** A count of screenshots taken is not a count of
screenshots read, and I will not describe an image I have not looked at. They
exist so that a person can look. The layout is instead covered mechanically by
`B34`, which measures text overlap and page overflow on all thirty case-and-view
combinations rather than by eye.

## Five states, kept separate

- **Not started:** server-side access control; production identity and tenancy;
  attachment storage; revocation; cross-tenant isolation.
- **In progress:** nothing in this component is mid-edit by me.
- **Implemented:** the calculation engine, the ranking, the two objectives, the
  four download routes, the participant and internal builders, the permission
  stand-in.
- **Technically verified:** the engine arithmetic, the exports as bytes, the
  hostile-content handling, the ordinary-import conservation, the browser journey,
  and now the baseline reproduction. All against synthetic figures, on this
  revision, with the checksums printed above.
- **Human accepted:** nothing. No test result confers business, technical, privacy
  or spending authority, and none of it substitutes for production identity,
  server-side access control or a formal independent audit.

## Developer tests and independent verification are not the same thing

`tests\run_tests.cjs` is the implementer's own suite. It is not run, endorsed or
counted by this report. I did not read it for its assertions and I do not rely on
its results. I ran `tests\export_shipped.test.mjs` once, at the export agent's
invitation, to check a claim it made; that is corroboration of one number and not
an endorsement of the suite.

Everything in this document was written by me, against the implementation, and I
did not write any of the code I am judging. Where I found a defect I wrote a
failing test and left the implementation alone. The two roles are separate and
should stay separate: the same person cannot both build the thing and be the
evidence that it works.

**Exit 0 is not done.** The suite deliberately exits non-zero while defects
remain. If it ever exits 0, that means every assertion I wrote passed - which is a
statement about my checks, not about the product.

## The next bounded task

One item, and it is not a code fix:

1. Obtain the reporting period for the candidate records, from whatever source
   the candidate screen is fed from, so that `R27` can be closed.

Then re-run `tests\run_all.ps1` and compare the checksums it prints with the table
above. If they differ, these results describe an older revision and should be
re-run before they are relied on. Do not mark this component accepted on the
strength of a green run; acceptance is a separate decision.

Note for whoever picks this up: `src\ui\app.js` and `src\data\export.js` were both
being written by other agents while this review ran, and `tools\build.py` changed
under me twice. The scope block and the checksum table are the way to tell which
revision answered a given run.

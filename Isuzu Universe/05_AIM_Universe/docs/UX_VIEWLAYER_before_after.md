# Two view layers, one component: what was reconciled and what was not

Written 2026-09-22 by the experience developer, on the AIM Universe corrective
build. This file is internal working evidence, not a reader-facing pack.

## The problem, in one paragraph

`tools/build.py` assembles nine modules into the artifact, and the one that draws
the screen is `src/ui/app.js`. Two other view modules existed in the tree —
`src/ui/views.js` (the six views) and `src/ui/render.js` (the shell around them) —
and neither was in the shipped list nor in the build's retired list. The build's
safety check only refuses a shipped module that reads a *known* retired one, so a
module in neither list was invisible to it. Both orphans were loaded by
`tests/ux_flow.test.mjs`, so that suite's 13/13 described a layer the product does
not run. Measured by `python tools/orphan_audit.py` before this work:

```
shipped : 18   retired : 9   ORPHANS : 2
   src/ui/render.js - loaded by: tests/ux_flow.test.mjs
   src/ui/views.js  - loaded by: tests/ux_flow.test.mjs
```

The two layers were **not** supersets of each other. `app.js` had the failed-render
guard and the verified reopen fix; the orphans had the amber unavailable states.
So neither could simply be deleted.

## The approach

`app.js` is authoritative: it ships, it holds the F05 guard, and it carries the
verified F01 reopen fix (`restoreSavedScenario()`, which took ACCEPT-02 from 47/5
to 52/0). So the orphan's features were **ported into `app.js`**, the test was
**re-pointed at `app.js`**, and the orphan was left to be retired by the
integration owner, who owns `tools/build.py`.

## The full gap list

Every gap below was found by rendering both layers over the same five cases and
six tabs and comparing the bytes. The evidence command is the same for all of
them:

```
node _qa/_app_render_probe.cjs      # 30 renders of src/ui/app.js into _qa/app_html/
node _qa/_assertion_probe.cjs       # how many of those renders carry each marker
```

Measured on the shipped layer **before** the ports, 30 case/tab renders:

| # | Feature | Orphan (`views.js`/`render.js`) | `app.js` before | Ported? |
|---|---|---|---|---|
| 1 | UX-06 amber unavailable state (`unavailableBlock`: `panel unavailable`, `Unavailable` eyebrow, "What is required") | present, 8 states | **absent** — 0 of 30 renders | **yes** |
| 2 | UX-08 empty-search state (`No candidate row matches this search`, "the filter excluded them") | present | **absent** | **yes** |
| 3 | UX-08 empty pagination (`No rows match the current search`, disabled last-page control) | present | **absent** | **yes** |
| 4 | REVIEW-04 part strip on every view (`Exact part references`) | present on all views | **absent**; present incidentally on 2 of 6 views | **yes** |
| 5 | F10 route into a part (`data-open-part`, a review of that exact part) | present | **absent** | **yes** |
| 6 | UX-02 "Ordering only / Assumptions differ" invariant statement | present | **absent** | **yes** |
| 7 | UX-07 failed-render card as a first-class block (`render-failure`, `data-render-state`, the shell status line) | present | **partial** – a failure panel existed but carried none of these | **yes** |
| 8 | F11 turbo conflict stated as resolved ("already settled") | present | **absent** — still asked the reader to settle it | **yes** |
| 9 | Sorted candidate columns (`data-sort`) | present | **absent** | **yes** |
| 10 | Break-even / tolerable-volume-loss panel on the ranking | present (`breakEvenTable` on the top-ranked option) | on the economics tab only | **yes, in part** — see below |
| 11 | Amber *styling* for the unavailable class | declared in a QA harness builder only, so not in the artifact either | n/a | **yes, inline** — see below |
| 12 | `views.bannedWords()` guard run before paint | present | **absent** | **yes** |
| 13 | Version status read from the payload rather than typed prose | present (`viewmodel.js`) | **partial** — no literal version, and the three status sentences are payload-derived | already largely sound; stated false panel and cost sentence corrected |
| 14 | Candidate coverage tiles stated as rows *and* parts | present | **partial** — "Rows with a cost and a list" (row count) with a separate "Distinct part numbers" tile | corrected wording |
| 15 | The part strip on the selected-part review | describes the part being reviewed | (feature did not exist) | **yes**, and it must describe the reviewed part, not the open case |

Two further faults were found in `app.js` itself, not in the gap list, while
porting the assertions:

- The review tab had no route into it, and when a route was added, the strip above
  it named the **open case's** part number while the review was of a **different**
  part. A reader was told two contradictory things at once. Prevented now by
  `partRouteSummary()`, which builds the strip from the reviewed part.
- The chrome's status strip printed a fixed `10 review findings`. The payload's own
  list happens to be 10, so a text check could not tell a counted number from a
  typed one; the count now comes from `D.packAudit.issues.length`, and the test
  asserts on the source that no count is typed.

## What was **not** ported, and why

**The break-even table verbatim.** The orphan put a full worked-detail panel and a
break-even table on the objectives view, for the top-ranked option. In this layer
the price-and-profit test is the one place a scenario is entered and calculated,
and the results region is the one place it is stated. Placing an editable-looking
copy of the same figures on a second tab would reintroduce, in this component, the
very fault the one-record work exists to remove: two screens showing one price.
What *was* missing on the ranking was the volume the top alternative needs, so that
table is stated there and the single point of entry stays on the tab that owns it.
The wording is honest about it: "The volume the top-ranked option needs".

**The orphan's separate case view over a selected candidate's rows as a *view***.
`app.js` already had a candidates screen derived from the same workbench module
(`src/data/candidates.js`), so the route reuses it rather than becoming a second
candidate screen.

**Re-formatting the economics or candidates views to match the orphan's templates.**
The brief was to add, not to rewrite. The existing blocks were left as they are
except where a specific gap or a specific wrong statement is listed above.

## The commands, and what they actually returned

### 1. Everything renders

```
node _qa/_app_render_probe.cjs
```
```
probe: 30 rendered, 0 failed of 30
interaction states: 6
```
Writes 30 case/tab renders plus six interaction states (empty search, second page,
worked-case review, unworked-part review, resolved turbo position, cost-free
economics) into `_qa/app_html/`.

### 2. The gap list, measured

```
node _qa/_assertion_probe.cjs
```
Before, the markers the orphan had and `app.js` lacked were 0 of 30. After the
ports, on the 36 rendered states:

| marker | renders carrying it |
|---|---|
| `panel unavailable` | 12 |
| `Unavailable` eyebrow | 12 |
| `What is required` | 12 |
| `No candidate row matches this search` | 2 |
| `the filter excluded them` | 2 |
| `No rows match the current search` | 2 |
| `data-last-page` | 7 |
| `Exact part references` | 36 of 36 |
| `data-open-part` | 5 |
| `Ordering only` | 5 |
| `already settled` | 2 |
| `data-sort` | 7 |

### 3. The test now guards the shipped layer

```
node tests/ux_flow.test.mjs
```
```
{"pass":14,"fail":0,"total":14}
layer  : src/ui/app.js
```

`UX00` was added to make the re-pointing self-checking: it reads the module list
out of `tools/build.py`, asserts that `src/ui/app.js` is in it, asserts that
neither orphan is, and asserts that this test file does not require either of them.
If the build is ever re-pointed at a different layer, that check fails rather than
the suite quietly testing the wrong thing again.

Three assertions could not move across as written. Each is kept beside its
replacement in the file, with the reason:

1. **The one-record check** drove `shell.scenario`, `shell.caseById` and
   `shell.build` from `render.js`. `app.js` publishes its own store, and the
   equivalence is now asserted against that, through the view's own controls.
2. **The stale-content check** patched `views.render`, because in the orphan the
   shell looked that function up as a module property. `app.js` calls the engine
   directly and closes over it. The same fault is now created by handing the shell
   an engine with one function missing — which is the real failure mode, not a test
   hook. `UX03` also asserts, first and separately, that an engine without its
   formatters still renders, so a pass cannot be confused with the failure path.
3. **The part-reference check** asserted every view carries the strip. That holds
   now. The counter-example was added: on a review of a different part the strip
   must name the reviewed part, not the open case.

### 4. The regression guard is untouched

```
node --test tests/ux_reopen.test.mjs
```
```
ℹ tests 7
ℹ pass 7
ℹ fail 0
```
7/7, as required. `app.js`'s reopen fix was not modified; the reopen block,
`restoreSavedScenario()`, and the hash ordering comment are byte-identical.

### 5. The artifact still assembles and still checks out

```
python tools/build.py            # 9 modules, labels clean
python tools/paint_check.py      # 8/8 paint checks passed
```

**Read the next two paragraphs before treating either result as evidence for this
work.** Two things have to be separated:

- `python tools/build.py` with its default synthetic payload now writes
  `dist/ISZE_AIM_Pricing_Decisions_v04_SYNTHETIC.html`, not the real artifact. That
  change is the integration owner's (`tools/build.py` mtime 13:52:20), made because a
  synthetic rebuild had earlier overwritten the real-payload artifact. My build run
  wrote the synthetic copy, so the real artifact was not touched by me.
- `dist/ISZE_AIM_Pricing_Decisions_v04_INTERNAL.html` — the real-payload artifact,
  5,151,727 bytes — was assembled at **13:52:29, before my changes to
  `src/ui/app.js`**. So the artifact on disk does **not** contain the ported features,
  and `paint_check.py` 8/8 is a statement about the pre-change artifact.

In other words: my work is in `src/ui/app.js` (plus the test and this document). The
deliverable artifact needs a rebuild with the authorised payload to pick it up, and
that rebuild is the integration owner's call — `tools/build.py` configuration is
theirs, and rebuilding the real-payload artifact is a ship action I was told not to
take. The evidence that the *corrected module* assembles and paints with the real
payload is the browser sweep in the next section, which builds a harness from the
same nine modules and the same real payload and photographs 30 combinations.

## One fault found in the styling, worth recording

The unavailable state's amber came from `.panel.unavailable`, and **that rule only
existed in a QA harness builder** (`_qa/build_qa_harness.cjs`), which is not
assembled into anything. In the artifact the class had no styling at all. Measured
in real Chrome on the artifact's own stylesheet: a `.panel.warn` panel computes
`background-color: rgb(255,250,241)` — the *same pale fill* as the amber block —
with a 1px pale border and no accent. So in the artifact the amber state and an
ordinary warn panel were visually identical, which defeats the whole point of
having a distinct state.

The state now carries its own colours inline in `app.js`: amber `#96620d` on
`#fffaf1` with a 4px amber left border, so it is distinguishable from a warn panel
without depending on a stylesheet rule that never ships. Measured after the fix, in
the element's own bounding box:

```
01_amber_unavailable_oil_economics.png
   fill  (255,250,241)   123224 px  (84.7% of the crop)
   accent (150,98,13)       873 px
07_candidates_empty_search_amber.png
   fill  (255,250,241)   166607 px  (90.4% of the crop)
   accent (150,98,13)       725 px
```

## The browser sweep

```
node _qa/build_shipped_harness.cjs   # 9 modules, read from tools/build.py
node _qa/sweep_shipped.cjs
python _qa/crop_evidence.py
```

Report: `_qa/sweep_report_shipped.json`. Screenshots: `_qa/shots_shipped/`.

```
combinations : 30 built, 0 failed of 30
console      : 0 errors/exceptions (out of 1 message, the deliberate self-test)
screenshots  : 15 taken
```

The harness reads the module list out of `tools/build.py` rather than copying it,
so a sweep over it cannot drift from the artifact. It refuses to run if a retired
view layer is ever re-added to the build.

Two faults in the sweep itself were found and fixed, both of which had made it
prove less than it appeared to:

- `location.hash` fires `hashchange` asynchronously, so the first version read each
  combination in the same expression as the navigation and reported the **previous**
  tab. It now waits until the content region has settled on the requested case —
  `data-render-state` is no longer `building` and the part strip carries that case's
  own part number — before reading. That is the same confusion this whole piece of
  work exists to remove, so it was worth fixing rather than noting.
- Screenshots were viewport-relative while element boxes were document
  coordinates, so a crop landed in the wrong place. Captures now scroll to the top
  and take the whole document, and every crop is taken from the element's own box.

The console capture is self-tested: the sweep raises a deliberate exception and
records the log length before and after, so "0 errors" is a measurement rather than
an assertion. `console_capture_self_test.captured` is `true` and the self-test entry
is subtracted from the product's error count.

### Screenshots: taken and read

**15 screenshots taken, 7 read by the parent agent.** The person who read them
was the agent writing this file, one at a time, at full resolution. A take-count is
not a read-count, and a note claiming images were read is not evidence of reading,
so what was seen in each is stated here:

| file | read? | what is visible in it |
|---|---|---|
| `01_amber_unavailable_oil_economics.png` | yes | IMOTORS-OIL, Price & profit test. The scenario controls are filled in; the results area states gross profit is not calculated. The amber block sits below it: pale cream panel, amber left edge, "UNAVAILABLE" eyebrow, the reason, and "What is required" with the parts purchase cost. Below that, the volume-requirement table. |
| `crop_01_...` (element box) | yes | The amber block alone: cream fill 84.7% of the crop with 873 px of `#96620d` along its left edge. Legible heading, reason and required line. |
| `07_candidates_empty_search_amber.png` | yes | Candidates tab with the search box holding `zzzz-no-such-part-zzzz`, the amber block saying no candidate row matches and that the filter excluded the rows, and the pager reading "No rows match the current search." with Next and Last page greyed. |
| `crop_07_...` (element box) | yes | The empty-search amber block alone: cream fill 90.4%, 725 px of amber accent, the amber heading and the reason in full. |
| `09_selected_part_review.png` | yes | The selected-part review of a screened part. The strip at the top names that part, and the panel says no case record exists for it yet. No route control inside the review. |
| `crop_09_...` (element box) | yes | The part strip alone: `EAVY500574` in monospace, the description, "screened candidate row, not a worked case", 79.3% of the crop in the strip's own fill. |
| `03_pads_objectives_revenue.png` and `04_..._grossProfit.png` | yes | The same case under both objectives. The "Ordering only" panel is present in both; the same nine rows are shown with both measures on each; the ranked table's order differs between the two while the baselines and prices do not. |
| `06_candidates_search_reached.png` | yes | The candidate table narrowed to a single row with pager "Rows 1 to 1 of 1 matching · page 1 of 1". |
| `11_action_saved.png` | yes | The internal action tab with the save status line reading "Case at revision 1, state draft, last saved ...". |
| `14_final_decision_tab.png` | yes | ITUK-PADS Sales evidence tab: the four stat tiles with euro figures, both charts, the part strip, and the six-tab strip with any previously added tab no longer present. |
| `12_narrow_720x1000.png` | yes | The objectives tab at 720 px. The three-quarter grid collapses to a single column and the ranked table does not clip. |
| `02_turbo_position_resolved.png`, `05_candidates_first_page.png`, `08_candidates_before_route.png`, `10_economics_after_keystroke.png`, `13_narrow_full.png`, `15_candidates_panels.png` | **not read** | Taken for the record; their claims are asserted from the DOM and the report instead. Listed here so the gap between taken and read is explicit rather than implied. |

No screenshot is offered as proof of a fix. Each claim above is carried by a DOM
read in `_qa/sweep_report_shipped.json` (computed colours, element geometry, counts)
and by the pixel measurement in `_qa/crop_evidence.py`; the images are how a person
checks that claim, not the evidence itself.

## Retirement: the entries to add to `tools/build.py`

The two tuples, to be added to `UNWIRED_MODULES` by the integration owner. Do not
apply them as a change here; this file only reports them.

```python
    ("src/ui/views.js", "retired second view layer; every view it held is ported into src/ui/app.js"),
    ("src/ui/render.js", "retired second shell; the F05 guard and routing live in src/ui/app.js"),
```

### Evidence that retiring them is safe

```
python tools/retirement_safety_check.py
```
```
shipped modules : 9
retired modules : 9
SAFE: no shipped module reads AIMUI.views, AIMUI.render, AIMViews or AIMRender.
```

The check reads the shipped list out of `tools/build.py` and scans every shipped
module for a **read** of the orphan globals, ignoring an assignment (a module's own
export line is not a read). The only remaining textual references to the orphans
are:

- `src/ui/app.js` — a comment naming them as the source of the ported features
- `tests/ux_flow.test.mjs` — the `RETIRED_LAYERS` constant, named precisely so
  `UX00` can assert they are **not** loaded
- `tools/retirement_safety_check.py`, `tools/_findings_probe.cjs`,
  `docs/ORPHAN_AUDIT.md`, `docs/MODULE_AUDIT.md`, `docs/UX_before_after.md` —
  audit tooling and documentation

None of those is a runtime read.

## The F11 finding, stated plainly

The previous agent reported that cost, price and version status come from "one
source-backed view model". That view model is `src/ui/viewmodel.js`, which is in
the **retired** list and is not assembled into the artifact. So the claim was true
of the orphan layer and not of the shipped one.

Checked directly in `app.js`:

- **Version** — no literal. There is no `Decision component` string and no `0.2`
  anywhere in the file. The chrome version line is now `D.meta.version`, read from
  the payload, and the finding count comes from `D.packAudit.issues.length`. Both
  are exposed on the chrome element and asserted in `UX07`.
- **Cost** — the retracted demand reached the page, but only in one place, and the
  sentence beside it was app.js's own paraphrase rather than the payload's words.
  The supplier-cost field now prints `D.meta.confirmedRules.costTypeRequired`
  verbatim, which is the sentence that contains "no longer required", and the
  manual-cost field now says outright that a missing cost is not zero.
- **Price status** — this was **not** sound. The turbo case still displayed
  "Conflicting recorded list prices" and asked the reader to settle a conflict the
  payload had already resolved in `turboPriceResolution`. That was the stale-prose
  case the brief asked about, and it is now fixed: the position view states the
  resolution, the resolved amount, the sensitivity observation and what remains
  open, all read from the payload.

So: **version was already payload-derived; cost was payload-derived in
substance but paraphrased in wording; price status was stale and is now
payload-derived.** The old "one source-backed view model" description does describe
the retired orphan, not the artifact.

## Faults in a check rather than in the code

Recorded because the brief asked for them and because each one would otherwise look
like a code defect:

1. **`tools/orphan_audit.py` misattributes loaders.** Its loader scan is a substring
   match: `if stem in text and folder in text`. `tests/ux_flow.test.mjs` names
   `views.js` and `render.js` in its `RETIRED_LAYERS` constant, so the audit reports
   that the suite loads them. It does not; it asserts the opposite. After this work
   the audit reads:

   ```
   ORPHANS : 3
      src/data/comparable.js   loaded by tests/market_evidence.test.mjs
      src/ui/render.js         loaded by tests/ux_flow.test.mjs   <- false positive
      src/ui/views.js          loaded by tests/ux_flow.test.mjs   <- false positive
   ```

   Fixing it means a real import check rather than a name match, which is the
   integration owner's call. The audit is deliberately left unedited.

2. **`orphan_audit.py` reads shipped and retired lists better than it did, but the
   tuple shape is shared.** Both lists use `("src/x.js", "reason")`, so a naive
   regex catches the retired ones as shipped. `tools/build.py`'s own guard does not
   have this problem (it iterates the two lists separately), but any new tool reading
   the file should slice between `MODULES` and `UNWIRED_MODULES`. My
   `_qa/build_shipped_harness.cjs` does that, and it caught the same mistake in its
   own first version (it listed 18 "shipped" modules where there are 9).

3. **A bare `#fffaf1` pixel check cannot identify this component's amber state.**
   `.panel.warn` shares that fill in the frozen stylesheet. The distinguishing
   feature is the amber accent on the left border, and even that appears in the
   shell's own chrome (the `.badge.review` and `.inputsnote` tones are close
   enough to collide at a tolerance of 10). Element-box measurement was the only
   reliable method. Recorded because the first two versions of the crop script
   produced false failures and a false pass respectively.

4. **`tests/ux_flow.test.mjs` was renamed in effect, not in file.** Its filename and
   suite id (`aim-ui-ux-flow`) are unchanged, but it no longer describes the same
   layer. Any older note that says "ux_flow drives the view layer" now means
   `src/ui/app.js`. `UX00` states this in its evidence string, and the file header
   states it at the top.

5. **The payload holds two views of the oil case's cost.** `verifiedCosts[]` holds a
   parts purchase cost for part `5876150530` while
   `cases[IMOTORS-OIL].packEvidence.costRecordPresent` is `false`, and the engine
   resolves the cost from `verifiedCosts`. So the objectives tab ranks a
   gross-profit alternative for that case (on the held cost) while the economics tab
   reports that no cost is applied to the scenario yet. The two are consistent once
   the distinction is read — a record held versus a cost applied to the scenario —
   but the case's own evidence flag contradicts `verifiedCosts[]`. **That is a data
   defect, not a view defect, and it is outside the files this work owns
   (`src/data/`, which the reviewer owns).** It is reported, not patched. If the
   flag is right, the oil case's cost should not be resolvable and the objectives
   tab should show the amber gross-profit state; if the cost record is right, the
   flag should be `true`.

## Files changed by this work

| file | change |
|---|---|
| `src/ui/app.js` | ported features added: the amber unavailable block (with inline amber), the part strip, the banned-word guard, the turbo resolution, the ordering-only invariant, the volume-requirement panel, sorted candidate columns, the part route and the selected-part review, the empty-search state, the payload-derived status strip, the F05 failure card and render gate, `data-part-strip`/`data-render-state`/`data-unavailable` hooks, and the `openPart`/`openCase`/`go`/`setCandidateQuery` surface the checks drive. Nothing restructured; the reopen fix untouched. |
| `tests/ux_flow.test.mjs` | re-pointed at `src/ui/app.js` through the same `<script>` shim `ux_reopen` uses; `UX00` added so the re-pointing is self-checking; every existing assertion kept, three re-expressed with their originals beside them; extended for the ported features, including that the unavailable state is asserted as an explicit amber block carrying its own accent. 14/14. |
| `docs/UX_VIEWLAYER_before_after.md` | this file |

Not changed, deliberately: `tools/build.py` (the integration owner applies the
`UNWIRED_MODULES` tuples), `src/data/`, `src/engine/`, `src/case/`, `src/output/`,
`tests/accept/`, and the reopen fix inside `app.js`.

Supporting QA material written for this work, all inside the gitignored `_qa/` and
`tools/`:

```
_qa/build_shipped_harness.cjs     the harness, its module list read from tools/build.py
_qa/sweep_shipped.cjs             the Chromium sweep, its own faults documented above
_qa/crop_evidence.py              element-box crops with pixel measurement
_qa/_app_render_probe.cjs         the 30 renders plus six interaction states
_qa/_assertion_probe.cjs          marker counts per render
_qa/_partref_probe.cjs            part-reference coverage per view
_qa/_failure_probe.cjs            why the render gate refused a view
_qa/_fault_injection_probe.cjs    the formatter and missing-helper faults
_qa/_binding_probe.cjs            which binding style each control uses
tools/retirement_safety_check.py  the ship-time safety check for the retirement
```

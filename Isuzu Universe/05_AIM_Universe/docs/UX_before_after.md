# AIM Universe — UX defect record

Corrective build, 22 September 2026. This is the view-layer record: what was
wrong on screen, what it does now, and the command that shows it.

The frozen reference `reference/ISZE_AIM_Pricing_Decisions_v03_FROZEN.html`
(sha256 `7494CEA1955BE820D0082EEF15473610945663FBEFC7A06D7969C15822423E14`) was
read, never modified. The engine and the data modules are another agent's work;
nothing under `src/data/`, `src/engine/`, `src/case/` or `src/output/` was edited
by this build.

---

## The short version

A reader could be shown the wrong evidence and not be told. That was the real
defect, and it was not the missing formatter — the missing formatter was just
what made it happen on one tab.

In v03, opening **ITUK-TURBO → Two objectives** threw
`ReferenceError: v03fmtPct is not defined`. The tab turned active anyway and the
content region was never replaced, so **the previous tab's evidence stayed on
screen underneath the new tab**. A reader had no way to know the numbers they
were looking at belonged to the tab they had just left.

Three things now hold that shut:

1. Every view is built inside a guard that either returns content or returns a
   named failure. There is no third outcome.
2. The content region is cleared *before* the new view is built, so a failure
   cannot leave the old view in place.
3. A failure paints a card that names the failing view, the case, the error and
   what kind of failure it was, and says in one sentence that nothing from
   another view is being shown.

The candidate screen had a quieter version of the same problem: it printed the
first **300** of **10,543** rows, with no search, no paging and no way to act on
a row, and it described cost-and-list coverage as decision readiness. It now
searches and pages the whole permitted set and keeps "coverage" and "cleared
decision" apart in words a reader can check.

---

## Defect by defect

### F05 (BASE-06) — turbo objectives fail to render, and stale content survived

**Was.** The view called a formatter that only existed inside the engine's
closure. It threw; the tab became active; the old view stayed visible.

**Now.** Two defences, because there were two faults.

The formatter fault: the views never call a formatter they do not own. They read
`engine.fmtNum` and `engine.fmtPct` from the engine's exports and fall back to
their own local formatting if those are absent. Passing the objectives view an
engine object with both formatters deleted **still renders**.

The stale-content fault: the shell in `src/ui/render.js` clears
`#content` first, sets `data-render-state` to `building`, then to `built` or
`failed`. A failure paints a card with `data-failed-view` on it. The surrounding
page frame is wrapped separately, so a card or control that fails cannot undo the
decision just made about the content region.

**Proof.**

```
node tests/ux_flow.test.mjs
```

`UX03` passes, and `UX12` counts all five cases × all six tabs:

> 30 rendered, 0 failed, of 30 case/tab combinations

and the headless sweep, on the real page:

> turbo_objectives_render_state: "built", turbo_has_failure_card: false,
> turbo_stale_content: false

Reintroducing the exact v03 throw on purpose, in the real browser:

> render_state: "failed", failed_view: "objectives", has_failure_card: true,
> stale_was_on_screen_before: true, stale_content_still_present: false

### F01 (UX side) — the scenario was split in two

**Was.** "Two objectives" read the new engine functions; "Price & profit test",
"Internal action" and the case export read an older `E.scenario` object. A ranked
option could be shown on one screen and a different scenario saved on another,
and nothing detected it.

**Now.** One record per case, held in `src/data/scenario.js` and reached through
`src/ui/scenario.js`. Selecting a ranked alternative writes that record; a manual
edit updates the same record; the price test, the internal action screen, the
save and the export all read it. The screen also states what it is doing: the
price test shows the scenario id, the version, the selected alternative and
whether the ranked option and the working record agree.

**Proof.** `UX01` and `UX13`. Selecting `PADS-TGT` and editing support to 5000
gives record `ITUK-PADS:v3`; the price field on the economics view reads 1118.55,
which is the record's `price_after`; the action view prints the same scenario id
and the same selected alternative; saving and reopening reproduces both the
revenue and the gross-profit result. In the browser, clicking "Use this option in
the scenario" on `TURBO-INC` gives `record_selected: "TURBO-INC"`,
`record_price_after: 1118.55` and `economics_newP: 1118.55`.

### F10 (REVIEW-01) — the candidate list was not a workbench

**Was.** 10,543 records, first 300 rendered, no search, no paging, no route into a
part.

**Now.** Filtered search over the full permitted set, real paging with a "Last
page" jump, sorting on the columns that matter, an account filter and a cost
filter that can show *either* side of the coverage gap, and a per-row button into
that exact part. Searches run over all rows, not the page on screen.

Row counts and distinct part numbers are labelled as two different counts in the
KPI tiles, in the table caption and in the coverage paragraph.

**Proof.** `UX04` and `UX05`, and the browser:

> candidate_search: searched "8983487290" (file index 3000), rows_returned 2
> candidate_last_page: "Rows 10,526 to 10,543 of 10,543 matching · page 422 of 422"
> candidate_route: routed_to "8983487290", view "case", render_state "built"

In `06_candidates_search_beyond_300_full.png` the result is a real table with the
part number in the Part column, its desk description, billed quantity 430,
observed billing €164,615.63, observed unit price €382.83, and "not held" in
**both** the List and Parts purchase cost columns. In
`07_candidates_last_page_full.png` the counter reads "Rows 10,526 to 10,543 of
10,543 matching · page 422 of 422 · 100% of the matching rows reached" with 18
rows under it.

### F11 — stale wording, driven from one source-backed view model

**Was.** The header said "Decision component 0.2" while the payload said 0.3. The
turbo header asked a reader to settle a price conflict the payload had already
resolved. Panels demanded an accounting-cost source the declared rule no longer
requires.

**Now.** `src/ui/viewmodel.js` assembles every cost, price and version sentence
from the payload, and each one carries the pointer it came from
(`/meta/confirmedRules/costTypeRequired`, `/turboPriceResolution`,
`/cases/<id>/packEvidence`). The header prints the payload version.

The two things the brief specifically names are now stated correctly:

- *Acceptance of an embedded supplier-cost formula is not approval of a customer
  net price.* The view model carries that as its own sentence and the economics
  and price-position views print it.
- *A record existing is not a status being verified.* The cost status row is
  `partial`, not `held`, and says so: "A supplier purchase-cost record exists for
  `8981654483` … The record existing is not the same as the cost being verified
  for this offer."

**Proof.** `UX07`. On screen: the header badge reads "AIM Pricing Decisions 0.3";
the pack strip reads "Applicable net / actual cost: unresolved" was replaced by
"Evidence: 2 of 7 status items are held without qualification · Commercial
priority: High". In `02_turbo_objectives_full.png` the header badge is "TURBO
LIST PRICE RESOLVED", the card reads "The turbo list price is already resolved.
It is not a question for the reader", and the resolution line reads "EUR 1,076.18
and EUR 1,114.96 are both held · Applicable list price for billing €1,114.96 ·
Second observation, kept as a sensitivity €1,076.18 / €1,114.96 · Resolved by the
framework's own precedence rule". The 0.2 string is gone from all 30 views.

### UX-06 — partial, failed and empty states must be recoverable and must not look like success

**Was.** A blank panel where data was simply absent.

**Now.** One amber state, built in one place (`failure.unavailable`), used three
ways: an empty search, a case with no cost record, and a route with no part
selected. Each prints the reason, what is required to fill it, and the scope. A
failed view is separate from an unavailable value: the failure card is red, the
unavailable block is amber, and both say which they are.

**Proof.** `UX08`. In the browser, an empty search produces 1 amber block reading
"No candidate row matches this search / The search ran over all 10,543 screened
rows and none matched. The rows are not missing; the filter excluded them."
Clearing the offer effective date on the turbo economics view produces 1 amber
block and the "One scenario record" panel turns amber with "The ranked option and
the working record disagree" — the numbers are not silently recomputed on the
stale date. Across the 30 painted views there are 7 amber states and 0 blank
panels.

### UX-07 — keyboard and small screen

**Was.** `.month-hit` cells already took a `tabindex` and answered Enter/Space.

**Now.** That pattern is kept and delegated through the shell, so it survives a
repaint. Everything new is a native control: the pager, the sort headers, the
search box and the per-row review button are `<button>`, `<input>` and `<select>`.

**Proof.** `UX09` and the browser. 36 month cells carry `tabindex="0"` and
`role="button"`; focusing the first and pressing Enter changes
`readout-billingEUR` from "Select a month to inspect its values." to "Jan: 2024
€84,186.94; 2025 €0.00"; a second cell answered with Space gives "Aug: 2024
€20,021.20; 2025 €23,118.92" (`enter_worked: true`, `space_worked: true`). At
390×844 the candidate screen paints 25 rows with 25 review buttons, the search
box and the pager visible, and **zero horizontal overflow**. In
`10_candidates_small_screen.png` the coverage paragraph then four full-width KPI
tiles stack vertically with no clipping.

### REVIEW-02 — commercial priority is not evidence completeness

**Was.** "Cost and list held" was presented as a cleared price decision, and 15
customer-part rows were presented as 15 unique parts.

**Now.** Two separate blocks on the price-position view, two separate axes in the
candidate KPIs, and the counted statement is derived from the data module rather
than written: "price and cost records are held for 15 of 10543 matching rows,
which is 8 distinct part numbers. That is coverage, not approval of a price or of
a cost."

**Proof.** `UX06`. The browser shows four tiles: Screened rows 10,543 · 7,798
distinct part numbers; Rows matching this search 10,543; Rows with a price and a
cost record 15 · 8 distinct part numbers · coverage, not approval; Rows with
competitor evidence 5 · 2 distinct part numbers.

### REVIEW-04 — the exact original part reference stays visible

**Now.** Every view begins with a part strip carrying the exact part number, the
case name, the unit and the recorded related numbers. The shell also refuses to
paint a case view that does not carry its own part number.

**Proof.** `UX10` checks the part reference on all 30 case/tab combinations. The
part strip is visible at the top of `05_candidates_first_page_full.png`
("EXACT PART REFERENCES 8982447940 Front brake-pad kit · Genuine · unit: kit ·
Related numbers recorded: 8982447939 8982447940 8982447941 8982447942").

---

## What was looked at, and what was seen in it

16 screenshots were taken into `_qa/shots/`; 14 remain after two were removed as
photocopies of each other — see the note under "What was not done". Every one
that remains was inspected. Three are worth naming because they carry the
findings:

**`02_turbo_objectives_full.png`** — the view that used to throw. It opens with
the part strip for `8981654483`, a purple "TWO OBJECTIVES, ONE ENGINE, ONE
SCENARIO RECORD" note, then a green "ORDERING ONLY" panel: *"Changing the
objective changed the order of the rows and nothing else: the baseline, the offer
effective date and every alternative quantity are identical under both
objectives."* Below it, three baseline cards: unchanged offer €1,031.79 / 18
units / €18,572.22; objective 1, revenue growth, `+€2,586.95` from "Test a 3%
increase on the observed record"; objective 2, gross-profit growth, `+€3,224.75`
from the same alternative. Then the ranking table, then nine amber "What remains
conditional" paragraphs, then the break-even table stating 18 units to preserve
revenue and 16 to preserve gross profit, and finally the dark "What this does not
say" panel.

**`12_failure_card_turbo_objectives_full.png`** — the failure state, forced by
reintroducing the v03 throw. A red card headed "THIS VIEW FAILED TO BUILD / Two
objectives did not render", reading "**ReferenceError:** v03fmtPct is not defined"
and "The Two objectives view for ITUK-TURBO could not be built. ReferenceError:
v03fmtPct is not defined. Nothing from another view is being shown in its place."
Failing view `objectives`. Case `ITUK-TURBO — Complete turbocharger`. "What kind
of failure: a name the view referenced does not exist in scope." Below it the
recovery routes. There is no table, no figure and no part data anywhere on the
page — the previous view is genuinely gone.

**`06_candidates_search_beyond_300_full.png`** — a part at file position 3,000,
which the old screen could not reach. The KPI row reads 10,543 screened rows /
7,798 distinct part numbers; 2 rows matching; 15 rows with a price and a cost
record over 8 distinct part numbers; 5 rows with competitor evidence over 2
distinct part numbers. Then "Read the coverage before the ranking" in amber, then
the search panel, then one table row for `8983487290` with "not held" in both the
List and Parts purchase cost columns, and the footer "Rows 1 to 2 of 2 matching ·
page 1 of 1 · 100% of the matching rows reached".

**One defect found by looking, not by the tests.** `09_candidates_empty_state_full.png`
showed the pagination counter reading "Rows 1 to 0 of 0 matching". That is
nonsense to a reader. It is now guarded: an empty result set shows "No rows match
the current search" instead of a reversed range.

---

## What was not done

- **F12, the shared case service.** Notes are still local to one browser. The
  save path now writes versioned case revisions through
  `src/data/cases.js`, and the export carries a change journal, but there is no
  server, no authenticated owner and no concurrent-write protection across
  machines. That is a backend increment, not a view-layer one.
- **A real "create a case" action from a candidate row.** The route opens a review
  of the exact part and names the promotion blockers another agent's module
  reports. It deliberately does not write a case, because the current customer net
  price and the applicable cost basis are not on the screened row and inventing
  them is exactly what this build exists to stop.
- **`src/ui/app.js` is not mine and overlaps this work.** Another agent wrote a
  complete single-file view layer there (76 KB, starting with a literal
  `<script>` tag), and it renders the same six tabs from the same shared scenario
  store. I did not edit it, and nothing I built is loaded by it. Two view layers
  now exist for the same component. Mine is the one that is loaded, tested and
  photographed; `app.js` has no test and is not in the harness. Someone has to
  choose one, deliberately, before this ships. It also cannot be `require()`d —
  it is a document fragment, not a module — so if it is the one that survives it
  needs the same kind of harness mine has.
- **`src/engine/pricing.js` and `src/engine/engine.js` are byte-identical
  duplicates** written by the engine agent. I did not touch either. It is worth
  someone confirming which one is authoritative.
- **No test covers the visual layout.** The layout numbers in the sweep
  (`any_clipped: 0`, `max_overflow_x: 0` across 30 views) come from measuring
  `scrollHeight` against `clientHeight`, which catches clipping but not ugly. The
  screenshots are the check for that, and that check is a person looking at 14
  images, not an assertion.
- **Two screenshots were taken and then removed, because they were photocopies.**
  The sweep originally shot ITUK-TURBO objectives both before and after the
  objective switch. ITUK-TURBO ranks `TURBO-INC, TURBO-NONE, TURBO-SUP` under
  *both* objectives, so the two images were byte-identical — the same picture
  filed twice. The second one is gone, and the sweep now says in its report why
  it is not taken. The ordering change is photographed where it genuinely
  happens, on ITUK-PADS, where revenue puts `PADS-VOL` first and gross profit puts
  `PADS-TGT` first. `11_turbo_objectives_half_width.png` was also replaced: it
  clipped a blank vertical slice of the page, so it proved nothing; a clean
  720×1000 resize of the same view replaced it.

---

## Commands

```
cd "C:\Users\jerom\Desktop\claude\ISZE\Isuzu Universe\05_AIM_Universe"

node tests/ux_flow.test.mjs                    # 13 pass / 0 fail
node tests/ux_flow.test.mjs --results _qa/evidence/ux_flow_results.json
node tests/run_tests.cjs                       # 60 pass / 0 fail (engine suite, unchanged)

node _qa/build_qa_harness.cjs                  # assemble the QA page from the frozen shell
node _qa/sweep.cjs                             # 30/30 built, 0 failed, 0 console errors, 14 shots
node _qa/capture_objective_switch.cjs          # the ordering change, photographed both ways
```

Raw output is kept in `_qa/evidence/`: `ux_flow_run.txt`,
`ux_flow_results.json`, `sweep_console.txt`, `objective_switch.txt`,
`engine_suite.txt`.

`_qa/` is gitignored because the harness embeds the restricted payload. It is
generated from the authorised local file, not committed.

## Files

**Created**

| File | What it holds |
|---|---|
| `src/ui/views.js` | the six working views, plus the selected-part review |
| `src/ui/render.js` | tab and shell routing, the render guard, the failed-render state |
| `src/ui/scenario.js` | the one shared scenario record, its journal and its change listener |
| `src/ui/candidates.js` | candidate screen state: search, filters, paging, the route into a part |
| `src/ui/viewmodel.js` | the source-backed cost / price / version / coverage status model |
| `src/ui/failure.js` | failure records, the failure statement and the amber unavailable state |
| `tests/ux_flow.test.mjs` | the 13 flow checks |
| `docs/UX_before_after.md` | this record |
| `_qa/*.cjs`, `_qa/harness.html`, `_qa/shots/*`, `_qa/evidence/*` | QA harness, sweep driver, screenshots, raw command output (gitignored) |

**Read, not modified**

`src/data/contracts.js`, `src/data/scenario.js`, `src/data/cases.js`,
`src/data/candidates.js`, `src/data/manifest.js`, `src/data/evidence.js`,
`src/engine/*`, `src/case/*`, `src/output/*`, `reference/*`, and the frozen
reference HTML.

**Not mine, and not loaded**

`src/ui/app.js` — another agent's single-file view layer for the same six tabs.
Left exactly as written; not in the harness, not in the tests.

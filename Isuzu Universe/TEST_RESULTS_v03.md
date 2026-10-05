# Test results

Two suites. Both are re-run on every build and their raw output ships beside this file.

## Arithmetic suite - 43 of 43 pass

Run by `validate_v03.py`. The engine is loaded the way the browser loads it - by
extracting the embedded payload and the engine block out of the built HTML - and driven
under Node. This is the same code path the page uses, not a reimplementation.

| ID | What is asserted | Result |
|---|---|---|
| T01 | gross margin is gross profit over revenue, from price and parts cost | pass |
| T02 | the class-implied margin is not the customer margin | pass |
| T03 | the combined margin is revenue-weighted, not a simple average of margins | pass |
| T04 | revenue break-even quantity is R0 / p1 | pass |
| T05 | gross-profit break-even quantity is GP0 / (p1 - cost) | pass |
| T06 | the additional quantity to exceed revenue is above the preserve quantity | pass |
| T07 | an all-volume reduction with unchanged volume loses revenue and gross profit | pass |
| T08 | the discount given away on existing volume is reported for an all-volume cut | pass |
| T09 | revenue up with gross profit down is flagged | pass |
| T10 | gross profit up with revenue down is flagged | pass |
| T10b | no trade-off flag is raised when both revenue and gross profit rise | pass |
| T11 | tolerable volume loss is computed for both measures and the binding one reported | pass |
| T12 | a missing cost is not treated as zero | pass |
| T13 | a zero cost is a value and is flagged as one | pass |
| T14 | a missing cost does not block revenue or the revenue break-even | pass |
| T15 | a cost above the proposed price makes the gross-profit break-even unattainable | pass |
| T16 | all-volume and incremental offers produce different revenue on the same quantities | pass |
| T17 | the discount on existing volume is zero for an incremental-only offer | pass |
| T18 | a September offer takes the September cost basis and an October offer the October basis | pass |
| T19 | the historical basis is separate and reproduces the price file | pass |
| T20 | the current cost is not the historical cost | pass |
| T21 | cost for 5876150530 is present and computed from verified inputs | pass |
| T22 | cost for 5876150531 is present so an alternative including it is not blocked | pass |
| T23 | a Genuine/BVP migration alternative exists and is labelled as migration | pass |
| T24 | the migration alternative carries the instruction not to count it as new business | pass |
| T25 | a negative base quantity is rejected rather than producing a meaningless margin | pass |
| T26 | ranking returns each alternative once, so a repeated join cannot double a result | pass |
| T27 | every ranked row carries a baseline-consistent result or an explicit error | pass |
| T28 | unchanged inputs give unchanged results | pass |
| T29 | an unchanged price changes neither revenue nor gross profit | pass |
| T30 | the baseline is identical under both objectives | pass |
| T31 | the volume assumptions are identical under both objectives | pass |
| T32 | both objective outputs are produced from one scenario | pass |
| T33 | the revenue ranking is sorted by revenue change descending | pass |
| T34 | the gross-profit ranking is sorted by gross-profit change descending | pass |
| T35 | a distributor export strips restricted cost and margin fields | pass |
| T36 | the audit catches an embedded cost that a shallow strip would miss | pass |
| T37 | no minimum margin or profit sacrifice is set, and that does not block calculation | pass |
| T38 | a conditional test states the quantity required, not a false optimum | pass |
| T39 | the candidate screen exists and states its cost coverage | pass |
| T40 | every screen row carries a selection reason or an unresolved input | pass |
| T41 | the turbo price is resolved to the billable record | pass |
| T42 | the excluded turbo records are marked unusable rather than dropped silently | pass |

## Paint and interaction suite - 19 of 19 pass

Run by `paint_seq.py` in headless Chrome on the built file. Tab switching goes through
`location.hash`, so the probe is a chain of steps with a wait between each rather than a
synchronous read.

| ID | What is asserted | Result |
|---|---|---|
| P01 | the embedded payload is reachable from the page | pass |
| P02 | six tabs render including the two new ones | pass |
| P02b | the Two objectives tab exists | pass |
| P03 | the view actually switched to objectives | pass |
| P04 | the two-objective view paints both objectives | pass |
| P05 | the unchanged offer is present as the baseline | pass |
| P06 | the confirmed measure is stated on the page | pass |
| P07 | the unset approval controls are stated rather than filled | pass |
| P08 | the ranking table rendered rows | pass |
| P09 | the objective selector exists | pass |
| P10 | changing the objective re-renders the view | pass |
| P11 | the baseline does not move when the objective changes | pass |
| P12 | the candidate screen switches and paints rows | pass |
| P13 | the candidate screen states its cost coverage | pass |
| P14 | the candidate screen states the confirmed measure | pass |
| P15 | a distributor export carries no cost or gross-profit field | pass |
| P16 | no tab throws on click | pass |
| P17 | both measures are produced for a real case in the page | pass |
| P18 | September and October cost bases resolve differently in the page | pass |

## What the two suites do not cover

- No test asserts that a proposed price is commercially right. The suites test arithmetic,
  wiring, labelling and the guards. They cannot test judgement.
- The canvas is a real Chrome run on this machine, not a matrix of browsers.
- The export strip is tested against the fields the engine emits today. A new field with a
  cost or margin in its name would need the forbidden list extended, and the test would
  catch it only if the field is present in the export.

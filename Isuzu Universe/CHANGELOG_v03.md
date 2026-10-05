# AIM pricing-decision engine - v0.2 to v0.3

**Built:** 2026-09-22  **Base:** `ISZE_AIM_Pricing_Decisions_v02.html` (the existing
0.2 component)  **Output:** `ISZE_AIM_Pricing_Decisions_v03.html`

This is a revision of the existing component. No new application, no rebuild of Atlas, no
production price change, and no new general data export. The engine reads the same
embedded payload plus the additions listed below.

## 1. The gross-profit measure changed

The confirmed rule is now in the engine: **revenue** = applicable ISZE net parts selling
price x quantity; **gross profit** = revenue minus parts purchase cost of the quantities
sold; **gross margin** = gross profit / revenue. Freight, duty, overheads and distributor
kickbacks are excluded, and an invoice discount is not deducted twice.

What was removed:

- The requirement that cost be an accounting, landed, standard or moving-average cost.
  Cost is now the documented supplier purchase calculation, with its inputs, source and
  effective date carried alongside.
- `cost === null` no longer disables gross profit by default. A missing cost is reported
  as a condition and the revenue side still calculates. A cost of zero is treated as a
  stated value and confirmed, not as a missing field.
- The price-class margin is no longer presented as the customer margin. It is computed
  from the applicable selling price and the parts cost, and the two are shown to differ.

The excluded line in the old formula was **not** kept. The old engine also did not deduct
freight or duty, so the measure itself is unchanged in that respect; what changed is that
the exclusion is now stated, and the double-deduction guard is explicit.

## 2. Two objectives, one engine

`v03rank(case, objective)` returns the alternatives ordered by the selected objective.
`revenue` is the default. Every row carries both measures, the volume assumption and the
flags, so the ranking never hides the measure it is not sorting on.

The baseline is computed once per case and passed into every alternative, so changing the
objective cannot move the baseline, the eligible quantity or the volume assumption. Two
tests assert exactly that (T30, T31).

## 3. Trade-off flags

- `REV_UP_GP_DOWN` - revenue rises while gross profit falls.
- `GP_UP_REV_DOWN` - gross profit rises while revenue falls.
- `DISCOUNT_ON_EXISTING` - an all-volume reduction gives away a stated amount on units
  that were already buying.
- `PRICE_AT_OR_BELOW_COST` - the proposed price does not exceed the parts cost.

Neither trade-off is automatically approved, and the page says so where it raises one.

## 4. Volume is never predicted

Every alternative must carry a label: **observed history**, **stated commitment**,
**modelled expectation** or **manual scenario**. The engine does not multiply a modelled
gap by a recovery rate. Where volume cannot be predicted it returns the quantity required
and a conditional test, and a test asserts that the wording is a required-quantity
statement rather than an optimum (T38).

## 5. Cost inputs completed

- **5876150530** had no cost because it is absent from `Price_file_2026_full.xlsx`
  entirely. Base price **701 JPY** is now carried from the Price CD export and corroborated
  by the base-price comparison file.
- **5876150531** is costed the same way, so a scenario that names the superseded number is
  not blocked.
- Both are marked `filled by this revision`, not `verified`, so the provenance is not
  overstated.

Three named bases replaced the single cost figure, because both inputs changed:

| Basis | JPY/EUR | Rate window | Japan discount | Thailand discount |
|---|---|---|---|---|
| HIST | 163.7 | 1 Oct 2025 - 31 Mar 2026 | 0.620 | 0.611 |
| SEP26 | 172.6 | 1 Apr 2026 - 30 Sep 2026 | 0.673 | 0.611 |
| OCT26 | 178.5 | 1 Oct 2026 - 31 Mar 2027 | 0.673 | 0.611 |

The HIST basis is the one that reproduces the price file's own FOB column, and it is the
only basis on which a historical actual gross profit may be stated. September and October
are held separately and never blended: `v03costForDate(part, effectiveDate)` selects by
the offer date. The current cost is not applied to past quantities.

Note on the Japan discount: the v0.2 component's own note said 0.620 was the 2026-09-18
revision. It is the reverse - 0.620 was in force and 0.673 is the revision. The engine now
carries both.

## 6. The turbo price records resolved

Four records existed for one part. The resolution and the reason each other record is
excluded is now in the payload (`turboPriceResolution`):

- **1114.96 - billable.** The carried list price in the price file, which the framework's
  own rule makes the authority for anything billed.
- blank PR00 cube row - no usable amount, so not a price.
- 1799.74 derived - does not reproduce from the current class factor (class C is 0.47, and
  reaching 1114.96 would need 0.7583). Model output, not a price.
- 1076.18 SAP pull return - a second observation four days later, kept as sensitivity.

Placing these correctly moved the size of this case's increase from +5.3% to +5.1% against
the 2025 snapshot, which is now stated rather than left ambiguous.

## 7. Why the engine did not load at first, and what now prevents it

The first build produced a file in which `JSON.parse` threw and no case rendered. Python's
`json.dumps` writes the literal `NaN` for a missing float, and JavaScript rejects that
token. **21,304 NaN values** were in the payload, all from empty cells and division by a
zero quantity in the candidate screen.

Two guards now exist: every write uses `allow_nan=False`, so a NaN raises at build time
instead of shipping, and non-finite values are converted to `null` on the way out. The
whole build chain fails loudly rather than producing a page that will not open.

A second, unrelated bug was also found by the paint check: `readHash()` reset any view not
listed in its registry, and the content dispatcher had been patched inside a different
function. Both are fixed and both are covered by the paint checks now.

## 8. What is in the payload

| Addition | What it holds |
|---|---|
| `verifiedCosts` | 9 parts, each with the formula, the inputs, all three bases, the sources and the effective dates |
| `costReconciliation` | the HIST basis against the price file's own FOB column, per part |
| `turboPriceResolution` | the four records, which one bills, and why the others do not |
| `alternatives` | 4 for the pad case and 3 for each other case, with type, scope, volume label and flags |
| `candidateScreen` | 10,543 rows over both pilot accounts with list, verified cost where held, base-price movement, selection reason and unresolved inputs |
| `screenRule` | what the screen is and what it is not |

Cost coverage on the screen is **15 of 10,543 rows** and that is stated on the page rather
than padded. The screen says `not held` rather than guessing, which is why it narrows
sharply after cost coverage is applied. Only 2 part numbers have competitor evidence, and
every other row says so.

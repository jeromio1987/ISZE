# Defect record: AIM Pricing Decisions, v03 to the corrected build

Built 2026-09-22. Every row below is a reproduced defect from the independent
review of the supplied v03 artifact, with what was actually changed and where it
is now checked. "Verified by" names a test that fails if the defect returns.

The frozen v03 reference is `reference/ISZE_AIM_Pricing_Decisions_v03_FROZEN.html`,
SHA-256 `7494CEA1955BE820D0082EEF15473610945663FBEFC7A06D7969C15822423E14`. The
original artifact was not modified.

---

## F01 | The scenario ranked was not the scenario saved | HIGH | fixed

**v03:** "Two objectives" called the new functions, while "Price & profit test",
"Internal action" and the case export read an older state object. A user could not
carry a ranked option into the saved decision, and nothing detected the split.

**Now:** one scenario record per case (`src/data/scenario.js`). Selecting a ranked
alternative writes to that record; editing a field writes to the same record; the
ranking, both objectives, the manual test, the save, the reopen and every export
read it. `AIMScenario` exposes `consistency()`, which replays the working scenario
through the ranking path and refuses a save when the two disagree.

**Verified by:** A14 (one scenario shared by ranking, manual input and
recalculation); B11 (browser, consistency holds); B12 (a manual assumption
reaches the calculation).

## F02 | Gross margin was not profit over revenue | HIGH | fixed

**v03:** `margin_after_pct` was `1 - cost / proposed_price`, which is the margin on
one discounted unit. For 100 units at 100 plus 20 at 80 on a 60 cost it reported
25.0% where the offer earns 4,400 on 11,600 = 37.93%. With support it reported 40%
on profit its own screen printed as 3,500 of 10,000 = 35%.

**Now:** `margin_after_pct = gross profit / revenue`, and the unit margin is a
separate field, `margin_unit_after_pct`, labelled as a different measure. A profit
bridge (`revenue - cost - support`) is published with every result and checked
against the reported change.

**Verified by:** R09, R10, A01 (bridge reconciles across five scenarios), A03 (the
two margins are different reported measures).

## F03 | Break-even used the all-volume equation for incremental offers | HIGH | fixed

**v03:** the revenue and profit calculation branched by eligibility, the break-even
did not. Unchanged units were priced at the reduced price, so a required volume was
reported far above the real one: 125 where 100 was right, 200 where 100 was right,
210 where 110 was right.

**Now:** separate equations. In an incremental-only offer the existing units keep
their current price, so they already hold revenue and gross profit, and only the
additional units recover the support at their incremental contribution.
Required quantities round up to a real pack.

**Verified by:** R11, R12, R13, A09, A10.

## F04 | One advertised baseline contained several cost bases | HIGH | fixed

**v03:** no-action rows used SEP26 while some alternatives used OCT26, so
`gp_before` differed between rows of a screen that promised one unchanged-offer
baseline. `v03costForDate` fell back to OCT26 for an invalid or unknown date, and
baseline revenue was rebuilt by rounding an average price and then labelled as
recorded history.

**Now:** the offer effective date and the cost basis are explicit fields on the
scenario, and ranking resolves every alternative against one offer date. Where the
alternatives still declare different bases, the ranking reports the distinct
unchanged-offer gross profits it found instead of claiming one baseline. An
unusable or out-of-window date returns unresolved and names the declared windows.
A baseline whose rounded price does not reproduce the recorded billing is labelled
a rounded scenario, and the recorded amount is carried beside it.

**Verified by:** R19, R21, R22, R23, B16 (an unusable date stays unresolved),
B17 (September and October resolve to different named bases). On the real payload
the ITUK PADS, IMOTORS cabin, ITUK turbo, ITUK discs and IMOTORS oil rankings each
now report one distinct baseline where the review found three cases with two.

## F05 | The turbo objectives view threw instead of rendering | HIGH | fixed

**v03:** the view called `v03fmtPct` without its `E.` qualifier, so opening
ITUK turbo / Two objectives raised `ReferenceError: v03fmtPct is not defined`. The
active tab changed while the previous tab's body stayed on screen, which is worse
than an error because the visible evidence then belongs to a tab that is no longer
selected.

**Now:** the formatter is called through the engine. A view that fails renders an
explicit "this tab did not load" panel naming the failure, and the previous view's
content is removed rather than left underneath.

**Verified by:** B06 (turbo objectives renders, no reference error), B08 (a forced
failure produces the explicit panel and does not leave the previous body), B05
(all 30 case and tab combinations render with the active tab correct).

## F06 | Invalid proposed quantities were accepted | HIGH | fixed

**v03:** `quantity_before` was validated, `quantity_after` was not, so a negative,
NaN or infinite proposed quantity returned `ok: true`. An invalid support string
became zero. An incremental quantity below the existing volume was clamped rather
than refused.

**Now:** strict finite validation at the calculation boundary, with every reason
reported rather than the first. Zero, blank, returns and an invalid entry are four
distinct states: blank means unchanged, zero is refused as a full withdrawal, and
an incremental total below the existing volume is refused. No numeric output is
non-finite.

**Verified by:** R14, R15, R16, R17, A04, A05, A06, A07, B14, B15.

## F07 | Genuine/BVP migration was a label, not a calculation | HIGH | fixed

**v03:** the oil alternative named a move to a Genuine counterpart but used the
original BVP price, cost and quantity, so it returned the same zero change as no
action - a fabricated "no effect" on a real decision.

**Now:** a migration alternative returns `migration_status: 'unresolved'` with no
financial figure, and states what has to be supplied: the transferred quantity and
the applicable price and parts cost of both product lines. The screen shows it in
its own panel rather than as a ranked row.

**Verified by:** R24; B05 (the oil case renders in every tab); the IMOTORS oil
ranking on the real payload returns `ok:false` for `OIL-GEN`.

## F08 | The export helper did not enforce its own restriction | HIGH for external use | fixed

**v03:** `v03strip` removed names from a blacklist. A key `cost` survived while
`cost_eur` was removed, and a nested object containing `scenario.cost` survived
into the output while `v03audit` reported nothing. The visible exports were marked
internal, so no distributor had received a file; the helper simply could not be
accepted as a distributor-safe mechanism.

**Now:** each recipient's output is built from an explicit allowlist, so an
undeclared field cannot appear however it is nested. The audit checks the
structure, not the rendered text, so a sentence stating that a brief contains no
supplier cost is not mistaken for one.

**Verified by:** R25, R26, A16, A17, B21, B22, B23, B24 (both exports produce real
bytes, and the participant brief contains no cost, gross-profit or margin field).

## F09 | The two entry points normalised volume differently | MEDIUM | fixed

**v03:** `v03rank` applied the alternative's volume assumption; `v03both` ignored
it unless an override was supplied, so PADS-VOL produced different quantities and
economics through the two exported paths.

**Now:** one `quantityAfter()` normalisation, and `bothObjectives()` accepts the
working inputs so the ranking path can be replayed exactly.

**Verified by:** R20 (both entry points report the same quantity), A14, A15.

## F10 | The candidate list was not an actionable workbench | MEDIUM | fixed

**v03:** 10,543 records, of which the first 300 rendered, with no search and no
paging. 15 customer-part rows covering 8 distinct part numbers were described as
15 parts. Cost-and-list completeness was called "decision-ready". The records
carry no period, and the totals did not match the worked cases.

**Now:** search and paging reach the whole permitted set (10,543 rows over 211
pages), row counts and distinct part counts are reported as two numbers (10,543
rows, 7,798 distinct parts), completeness is named completeness and separated from
approval, and the undeclared reporting basis is stated rather than inferred from
similar-looking values.

**Verified by:** R27, A18, A19, A20, A21, B18, B19, B20.

## F11 | Older v02 wording survived the v03 change | MEDIUM | partly fixed

**v03:** the visible turbo header still asked to settle the price conflict, some
panels said cost records were outside the HTML although verified costs were
embedded, older screens still demanded an accounting-cost source that the declared
rule no longer requires, and the header said "Decision component 0.2".

**Now:** the version label is written from the build, so the header cannot claim an
older build, and the cost wording describes the declared parts-purchase-cost
measure with its named basis and effective date. **Not finished:** the turbo header
and some snapshot wording still come from the retained shell and have not been
rewritten from the accepted state. Those strings are carried by the frozen
reference, so they are a named remaining item, not an unnoticed one.

**Verified by:** the build fails on a banned label, and the version span is
overwritten at build time. No test yet asserts the individual retained phrases.
**Remaining:** rewrite the turbo header and snapshot wording from one accepted
state (tracked as part of DATA/CONNECT work).

## F12 | Notes were local mutable state | NOT A SHARED SERVICE | partly fixed

**v03:** one mutable `localStorage` blob with no revision, no history, no owner,
no separate proposal and outcome, and a second edit silently overwrote the first.

**Now:** an append-only revision log per case. Each save is a numbered revision
that names the one it supersedes; a correction is a new revision and never
replaces its predecessor; a stale write is refused and reported instead of
overwriting a newer revision; a duplicate submission is refused; states are a
declared list and an unknown state is refused; reopening reproduces the same
assumptions and both results. A recovery bundle exports and restores every case.

**Not finished:** this is still browser storage, not a shared service with
authenticated ownership. `INDEX.md` records that there is no product application
folder named UNIVERSE on this machine, and choosing the shared backend is RUN-01,
an owner decision. The record is written behind an interface so that changing the
store does not change the case shape or its callers.

**Verified by:** A22, A23, A24, A25, A26, A27, B25, B26, B27, B28, B29, B30, B31.

---

## Reproduced checksum and counts

| | v03 artifact | corrected build |
|---|---|---|
| Independent engine checks | 11 pass / 19 fail (30) | 60 pass / 0 fail (60) |
| Browser, cases and tabs | 29 pass / 1 fail (30) | 30 pass / 0 fail (30) |
| Browser acceptance, full | not runnable in the review environment | 34 pass / 0 fail (34) |
| Artifact size | 5,935,584 bytes | 5,084,059 bytes with the real payload |

The v03 failure count is the review's own result, reproduced here with the
supplied tool unchanged.

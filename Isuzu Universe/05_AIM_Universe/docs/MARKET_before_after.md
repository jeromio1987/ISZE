# Market evidence — the comparable-price panel, and the request for what is missing

Corrective build of the AIM Universe market-evidence layer, 22 September 2026.
This is the MARKET developer's record. It states what already existed, what was
found wrong with it, what was added, and what remains open.

## Verdict

I read the existing market work honestly and it is better than a task ID in a
comment, but it is not the task. Four of the six rules `MARKET-01` to `MARKET-06`
are properly implemented inside `src/data/evidence.js`; two are partly
implemented; and the single most important sentence in `MARKET-05` — that an
advertised retail price is not proof our own net terms are too high — is written
in prose but never enforced anywhere.

The two rules that were entirely missing are `MARKET-07` and `MARKET-08`, which
is the work I was given. They are now built as `src/data/comparable.js`: a
computation with a declared contract that renders nothing, because the view layer
is being edited by someone else right now. Thirty-two checks pass against it, and
the sixty checks that were green before I started are still green.

## What a comparison is, and why this file exists

An advertised price on a competitor's website is a dated observation by another
seller. It is evidence of what that seller advertised on a day. It is not a
quotation, it is not a market price, and it is not proof that our own net terms
are wrong. Every rule below follows from taking that sentence literally.

The second reason this file exists is a file-ownership constraint, not a design
preference. `src/ui/app.js` is being edited by another agent while I write this. I
therefore cannot wire a panel into a screen. So the panel computes a result and
declares its own shape, and someone wires it later. That turns out to be the
better shape anyway: the interesting questions in this task are about what a
comparison *means*, and those are answered in one place instead of being spread
across a render function.

## Files

| File | What it holds |
|---|---|
| `src/data/comparable.js` | The panel computation (`MARKET-07`) and the request for the smallest missing comparison detail (`MARKET-08`). New. Renders nothing; declares a contract. |
| `tests/market_evidence.test.mjs` | The 32 checks. New. |
| `docs/MARKET_before_after.md` | This document. New. |

I did not edit any other source file. In particular `src/data/evidence.js` was
read and is assessed below, not rewritten; `src/data/contracts.js` was read and
not edited; and `src/ui/app.js` was not opened for writing.

## Commands, and what they actually returned

All three run from `Isuzu Universe\05_AIM_Universe`.

```
node tests\run_tests.cjs --payload payload\aim_payload_20260922.json
  {"pass":60,"fail":0,"total":60}
  This is the "before" baseline, confirmed first, and it is the "after" result too.

node --test tests\market_evidence.test.mjs
  tests 32   pass 32   fail 0

node tests\accept\guard_09_module_scope.cjs
  {"pass":5,"fail":0,"skipped":0,"total":5}
```

Two further checks passed, run because the panel calls into `evidence.js` and I
wanted independent evidence that the call was not a rewrite:

```
node --test tests\data_contracts.test.mjs
  tests 70   pass 70   fail 0
```

`src/data/comparable.js` is not assembled into the artifact. `tools/build.py`
lists the modules the build ships, and this new file is not among them. I did not
run `tools/build.py` and did not add it to that list, because neither is mine. See
"What still needs a decision" below.

## MARKET-01 to MARKET-06 — the honest audit

A task ID in a comment is not implementation, so each verdict below names the
function, the behaviour, and the specific REQUIRED EVIDENCE item it does or does
not satisfy.

### MARKET-01 — store dated competitor observations as evidence, not truth — **partly met**

*Function:* `evidenceStrength(observation, opts)`, `evidence.js` line ~962.

*What it does:* collects the limitations of an observation — no retrieval date,
no source location, no tax basis, no match statement, not marked approval-ready —
and returns a strength of complete, partial or thin. It carries
`evidence_not_truth: true` and says in words that a dated observation is not a
quotation.

*What it does not do, against the BUILD text.* The task asks for a record
containing source, **observed date**, original/alternative reference, seller,
market, currency, tax, **pack**, **channel** and **availability meaning**. The
function reads `retrieved` and `url`, but has no notion of seller, market,
currency, pack, channel or availability. It scores an observation; it does not
model one. The ten real observations in the payload carry all of those fields
(`seller`, `market`, `currency_original`, `pack_quantity`, `kit_contents`,
`availability`, `delivery_market`, `use`), so the model in `evidence.js` is
narrower than the data behind it.

*REQUIRED EVIDENCE 1 — "an observation retains source and date through a review
and saved case":* **not satisfied, and not testable here.** `evidenceStrength`
returns limitations but no source-and-date pair, and the case record
(`src/data/cases.js`, contract `CASE_FIELDS`) has no field that carries an
observation reference. `src/data/comparable.js` now copies
`observation_id`, `seller`, `retrieved` and `source_reference` into every panel
row and marks it `raw_unchanged`, which is the mechanism the item needs — but the
panel is not yet wired to a review or a saved case, so the end-to-end claim is not
made.

*REQUIRED EVIDENCE 2 — "a missing currency or reference remains missing instead
of borrowing the previous row's values":* **satisfied.** `statesNoValue` treats
`null`, `''`, `n/a`, `unknown`, `not stated`, `tbc` and `-` as the same thing, and
`evidenceStrength` reports each as a limitation rather than substituting anything.
There is no row-to-row carry in the function at all. The panel asserts the same
property directly.

### MARKET-02 — record product equivalence separately from lexical similarity — **met**

*Functions:* `lexicalSimilarity(a, b)` line ~987, `productEquivalence(candidate)`
line ~1015.

*Behaviour:* similarity is computed as a word-overlap ratio and returned as a
number with an explicit warning that similar wording is not equivalence.
Equivalence is claimed **only** when the source declares it *and* names who
declared it; a declaration with no owner named returns `equivalent: null` with the
basis recorded as "a declaration with no owner named". A bare declaration cannot
buy equivalence.

*REQUIRED EVIDENCE 1 — "a housing and element, or incomplete kit and full kit, do
not form an accepted price comparison":* **satisfied in the module, and now
enforced downstream.** `productEquivalence` cannot be talked into equivalence by a
similar description. `normalisePack` separately refuses to total an incomplete
content list ("an incomplete content list is not treated as a complete pack"), and
`comparable.js` maps `contents_equivalent: false` to a named exclusion.

*REQUIRED EVIDENCE 2 — "rejected and unresolved evidence stays traceable and is
excluded from the eligible comparison":* **satisfied.** `relationships()` carries
`validation_status`, `fitment_approved`, `relationship_type_raw` and
`original_reference_preserved: true` on every row, and `relationshipSummary()`
reports approved fitment as a separate count. The panel keeps every rejected or
unresolved observation on an `ineligible_offers` row with a named reason and the
raw record attached.

*One gap, in the BUILD text rather than the evidence:* the task asks for "exact
match, documented candidate, rejected match and unresolved application"
*separately*. The function returns equivalent / not equivalent / not established —
three states, not four. The payload's own vocabulary is `accepted`, `unresolved`,
`rejected`, which is also three. A fourth "documented candidate" state is not
distinguishable in what exists.

### MARKET-03 — normalise packs and kit contents only when supported — **met**

*Functions:* `normalisePack(observation)` line ~1036, `perPiecePrice(amount, pack)`
line ~1070.

*Behaviour:* the quoted price and the declared unit are kept; a per-piece figure
is derived only from a content list whose every line carries a quantity; an
incomplete list returns `normalised: false`; and `perPiecePrice` refuses whenever
the pack is not normalised. Both bases can therefore be shown together.

*REQUIRED EVIDENCE 1 — "a synthetic pack of four and one piece compare correctly
when equivalence is accepted":* **satisfied, and now asserted end to end.** In
`tests/market_evidence.test.mjs`, a pack of four at 40 and a single piece at 12
both become eligible, the pack keeps 40 as its quoted price and states 10 per
piece, the piece states 12, and both carry `bases_shown` of quoted, adjusted and
per-piece. With an approved median rule the summary is 11 and the two offers it
came from are still returned individually.

*REQUIRED EVIDENCE 2 — "unknown pack contents prevent the derived comparable unit
price, not retention of the original observation":* **was partly met, now fully
met.** `normalisePack` and `perPiecePrice` were right, but no caller existed to
prove that retention actually happened: nothing took the refusal and then still
kept the row. `comparable.js` does both — an unstated pack gets the named reason
`PACK_CONTENTS_UNKNOWN`, keeps `adjustment.value` at the auditable 40 and leaves
`comparable_value.value` null. I had this wrong in my first draft (I discarded the
adjusted amount along with the derived figure) and the test caught it; see "Two
faults found in my own first draft" below.

### MARKET-04 — make currency, tax and delivery adjustments auditable — **met**

*Function:* `adjustToComparable(amount, ctx)` line ~1087.

*Behaviour:* every adjustment is a row in `steps` with the rule that produced it —
remove tax at the stated rate, convert at the stated rate taken on the stated
date, add the stated delivered cost. A tax-inclusive amount with no stated rate
leaves the figure unresolved. A non-EUR amount with no rate, or a rate with no
date, leaves it unresolved. An unstated delivery basis leaves it unresolved. No
live rate is fetched and no tax rate is assumed.

*REQUIRED EVIDENCE 1 — "a converted observation can be reproduced from the
retained original and dated inputs":* **satisfied.** `value_before_adjustment`
retains the original, `steps` carries the from-value, the to-value and the rule
for each move, and the panel keeps each step on the row. The test converts 5,000
JPY at a stated rate taken on 2026-09-01, asserts the original 5000 is retained,
and asserts a conversion step exists.

*REQUIRED EVIDENCE 2 — "unknown tax or delivery treatment is not silently assumed
equal between offers":* **satisfied.** Each of the unknown cases produces a
distinct unresolved sentence rather than a default, and the panel maps each
sentence to a named reason code — `TAX_BASIS_NOT_STATED`, `TAX_RATE_NOT_STATED`,
`NO_DATED_RATE_TO_EUR`, `FX_DATE_NOT_STATED`, `CURRENCY_NOT_STATED`,
`DELIVERY_BASIS_NOT_STATED`, `DELIVERY_COST_NOT_SUPPLIED`.

*One finding I could not resolve myself.* Two of those sentences from
`evidence.js` could not be mapped by anything but a substring match. The sentence
for a missing dated rate is built as `'the amount is in ' + currency + ' and no
dated rate to EUR was supplied'`. My first mapping looked for `'no dated rate to
EUR'` but lowered the sentence before comparing, so `EUR` became `eur` and the
match failed: a missing conversion rate was being reported as an unmapped
"adjustment not auditable" instead of as a missing rate. I fixed it on my side by
lowering both sides of the comparison. The cleaner fix belongs to `evidence.js`:
return a stable code beside each unresolved sentence, so a caller never has to
match on prose. That is a small change to a file I do not own.

### MARKET-05 — keep different commercial price levels separate — **partly met**

*Functions:* `PRICE_LEVELS` line ~108, `priceLevel(levelId)` line ~149,
`assertSamePriceLevel(a, b)` line ~159.

*What it does well:* five levels are named and each carries a statement of what it
is. `assertSamePriceLevel` refuses to treat two different levels as one figure and
says why in plain words. `comparability()` additionally refuses mixed periods,
sales stages, units, entities and purchasing accounts before any arithmetic runs.

*What is missing, against the BUILD text.* The task names four levels: **ISZE net
distributor price**, **reference dealer price**, distributor/dealer transaction
prices, and **public advertised retail**. The module's five are `list`,
`observed_billing_average`, `competitor_advertised`, `reference_dealer` and
`supplier_cost`. The mapping is close but not one-to-one: there is no distinct
level for our own net distributor terms as against a carried list figure. I did
not add them, because two definitions of a price level is exactly the duplication
this project has been damaged by twice. `comparable.js` declares them and reports
them in `REQUESTED_SHARED_LEVELS` for the owner of `evidence.js` to fold in.

*REQUIRED EVIDENCE 1 — "an ISZE-net-versus-retail fixture is excluded from a
direct price index unless an accepted bridge is explicitly supplied":* **satisfied
by the new panel.** With the basis named as our own net terms, an advertised retail
row is excluded with the reason `NO_ACCEPTED_LEVEL_BRIDGE`, and the reason text
says in as many words that an advertised retail price is not proof our own net
terms are too high. Supplying an accepted bridge — one with an identifier, a named
approver and a statement — makes both rows comparable; supplying a bridge with no
approver does not. This is the sentence in the task text that had no enforcement
anywhere before now.

*REQUIRED EVIDENCE 2 — "a reference valuation cannot be displayed as actual
downstream revenue or dealer margin":* **satisfied by the new panel, and it was
the clearest gap.** Nothing in `evidence.js` prevented a reference dealer price
being used as revenue or margin; it had a label and a statement and no gate.
`comparable.js` adds `assertLevelUse(level, intendedUse)`, and a reference dealer
price is refused for `dealer_revenue` and for `dealer_margin` while being allowed
for `competitiveness_comparison`. A parts purchase cost is refused for every
selling use, including the comparison itself.

### MARKET-06 — make outdated and conflicting observations visible — **partly met**

*Function:* `observationConflicts(observations, opts)` line ~1173.

*What it does well:* groups observations by part and price level, collects
observations retrieved before a review point, and reports groups that carry more
than one distinct amount — with the explicit statement that both stay visible and
neither is selected as correct. That is `REQUIRED EVIDENCE 2` and it is properly
met: conflicting sources remain visible with their amounts, and the cheapest is
not chosen.

*REQUIRED EVIDENCE 1 — "a newer price does not silently rewrite an earlier saved
comparison":* **not satisfied by `evidence.js`, satisfied by the new panel.** There
is no saved-comparison concept in `observationConflicts` at all — it compares
observations to each other and knows nothing about a comparison that was already
saved. This is arguably a real gap rather than a scoping choice, because the item
is about persistence and the function is about display. `comparable.js` fills it:
a saved comparison comes back with its original `value`, `rewritten: false`, and a
list of the newer observations that supersede its rows, plus a sentence stating
that the saved figure stands as the figure that was saved.

*Two things to note about the freshness handling.* First, this function is the
only place with a default of any kind: `stale_after_days` defaults to 180, against
a task that says only a recorded freshness policy may decide eligibility and that
no universal expiry may be invented. A default review point applied inside a
function whose name is `observationConflicts` is not an approved policy. The panel
does not use that default; it flags past-review-point observations and asks for a
review, and applies a policy only when one is named with an approver and a stated
maximum age. What the default affects in `evidence.js` itself is the flag, not the
money. Second, both `observationConflicts` and my panel read the date with
`Date.parse`, which accepts some strings a reader would not call a date; a strict
parser would be better, and I left it alone because it works on the dates actually
in use.

## MARKET-07 — the comparable-price panel — **met**

*New file:* `src/data/comparable.js`, functions `panel()`, `candidateBases()`,
`assertLevelUse()`, `levelInfo()`, `bridgeCheck()`, `explainExclusion()`.

The panel takes a case and its observations and returns, for each observation
it was given, either a place in the comparable set or a named reason it was left
out. It explicitly does **not** choose one. With no approved selection rule,
`selected_observation_id` is null, every eligible row is marked `selected: false`
with the wording "the cheapest is not treated as the right one", and the three
deliberately different prices in the test stay visible as three different prices.

Four things the task asks for, and where each lives:**Eligible observations, the selected basis, and explicit exclusions.** The result
carries `eligible_offers`, `ineligible_offers`, `selected_basis` and
`candidate_bases`. The basis is named by the reviewer through
`basis_level` and `basis_unit`; the panel will list which levels are present and
stop there, because naming the basis is a commercial decision and there is no
approved rule that makes it for you.

**A summary only under an approved aggregation rule.** `aggregation.declared` is
false by default and `summary` is null. A rule is accepted only when it carries an
identifier, a named approver and a statement. The only method the panel computes
is a median; a rule asking for an arithmetic mean is refused rather than silently
computed as a median, on the grounds that a summary computed another way would not
be the rule that was approved. Even when a summary is stated, every offer it came
from is still returned individually.

**Purchasing movement and price positioning as two separate outputs.** They are
two differently named fields with different declared evidence kinds.
`purchasing_movement` is about our own recorded volumes and realised prices and
carries `is_proof_of_price_positioning: false` and a `must_not_be_read_as` list;
`price_positioning` is about dated prices published by other sellers and carries
`is_proof_that_our_terms_are_too_high: false` and its own list. Each sentence
states what the other is not.

**Only the supported comparison links into the scenario.** `scenario_link.linked`
is true only when a basis is named and at least one observation reached it. It
carries the eligible observation identifiers and the excluded ones separately, so
an excluded observation cannot travel into the scenario by being left unstamped.
With nothing eligible the link is false and the reason code is
`NO_ELIGIBLE_COMPARABLE`; with no basis it is `NO_BASIS_NAMED`. In every case
`price_action_certified` is false.

### The exclusions the panel actually makes, and why

There are 25 declared reason codes — 15 that exclude and 10 that leave something
unresolved. A code that is not declared is reported as unknown rather than
presented as a reviewed reason, and the test asserts that every code on every real
payload row resolves in the list.

| Reason | What produced it | Why |
|---|---|---|
| `NO_OBSERVATION_ID` | no traceable identifier | a comparison that cannot be traced back is not a comparison |
| `OBSERVATION_FOR_ANOTHER_CASE` | the row names a different case | a row for another case is not attached to this one |
| `ROLE_NOT_STATED` | not our terms and not a competitor | the reader cannot tell whose price it is |
| `NO_PRICE_LEVEL_DECLARED` | no level | it may not be compared with any other figure |
| `RESTRICTED_COST_IS_NOT_A_SELLING_PRICE` | a purchase cost | what we pay is not a selling price at any level |
| `LEVEL_NOT_LIKE_FOR_LIKE` | two different levels | shown side by side, never averaged into one number |
| `NO_ACCEPTED_LEVEL_BRIDGE` | our terms against advertised retail | an advertised retail price is not proof our net terms are too high |
| `PRODUCT_MATCH_REJECTED` | the source rejected the match | a rejected match stays visible and stays out |
| `PRODUCT_MATCH_UNRESOLVED` | a cross-reference or a candidate | a shared family creates a candidate to inspect, not an equivalent |
| `NO_PRODUCT_EQUIVALENCE_DECLARATION` | no owner named for the declaration | equivalence has to be declared by someone |
| `KIT_CONTENTS_NOT_EQUIVALENT` | a housing against an element | not the same product, whatever the pack price normalises to |
| `UNIT_NOT_LIKE_FOR_LIKE` | per-axle against per-piece | per-axle, per-kit and per-piece are not the same thing |
| `SUPERSEDED_OBSERVATION` | a newer row replaces it | it stays visible; it is not the row to build a current comparison from |
| `NO_AMOUNT_RECORDED` | no price on the row | a missing price is not a price of zero |
| `CURRENCY_NOT_STATED` | no currency | not inherited from the row above it |
| `VAT_RATE_UNIT_NOT_STATED` | a rate with no unit declared | 0.2 as a fraction and 20 as a percentage are the same digits and a hundred-fold different amount |
| `NO_DATED_RATE_TO_EUR` | another currency, no rate | no live rate is fetched |
| `FX_DATE_NOT_STATED` | a rate with no date | a rate with no date is not reproducible |
| `TAX_BASIS_NOT_STATED` | no tax treatment | tax-inclusive and tax-exclusive are not the same number |
| `TAX_RATE_NOT_STATED` | tax-inclusive with no rate | no tax rate is assumed |
| `DELIVERY_BASIS_NOT_STATED` | no delivery treatment | an undelivered price is not a delivered one |
| `DELIVERY_COST_NOT_SUPPLIED` | excludes delivery, no cost | the delivered cost is missing, not zero |
| `PACK_CONTENTS_UNKNOWN` | no pack contents, or no piece/pack basis | a per-piece figure cannot be derived from a part name |
| `AGE_BEYOND_DECLARED_POLICY` | past an approved policy's limit | the one case where age decides eligibility, and only then |
| `ADJUSTMENT_NOT_AUDITABLE` | a missing-fact sentence I could not map | reported with its own words rather than dropped |

### On the real payload

Across the five cases and their ten observations, each case panel reports
`raw_records_retained` equal to `observations_in`, `raw_input_unmodified: true`,
`price_action_certified: false`, and `all_exclusion_codes_named: true`. Every
excluded offer carries at least one reason.

The dominant reasons on this payload are `PRODUCT_MATCH_UNRESOLVED` and
`PACK_CONTENTS_UNKNOWN`, and both are correct rather than pessimistic. Every
payload offer is matched on a seller cross-reference or a claimed OE number — the
source says as much, with `match_status: accepted` for some and `unresolved` or
`rejected` for others — and none is an approved equivalence. And no payload offer
declares whether its quoted amount is for a piece or a pack, so no per-piece
figure can be derived. The payload's own note field says the same thing in words:
"Price lead; product / net comparison not approved."

**The panel returns nothing eligible on the authorised payload, and that is the
finding.** With `public_advertised_retail` named as the basis, each case panel
comes out with zero comparable offers and a stated gap. I am reporting that rather
than working around it. **The honest reading is that the authorised payload does
not currently contain a comparison that can be made** — not that the panel is
broken. Making one would need the payload's own stated unknowns to be filled in,
which is what MARKET-08's request asks for.

When a person supplies the facts the payload leaves open, the panel does produce
a comparable offer, and the arithmetic differs from what the payload's numbers
imply if you take them at face value. The AUTODOC UK observation for the pad case
is `76.99 GBP` including 20% VAT at a documented `1.17`. The correct figure is
`76.99 ÷ 1.20 × 1.17 = 75.07 EUR`. Three ways of getting it wrong, all
reproducible from the retained inputs:

| What is done with the rate | Figure | Error |
|---|---|---|
| The unit is declared as a percentage (`20`) | **75.07 EUR** | — correct |
| The 0.20 fraction handed over as if it were a percentage | 89.90 EUR | 19.7% too high |
| Tax not removed at all | 90.08 EUR | 20.0% too high |

That 19.7% is not a rounding question, so the arithmetic is asserted directly in
the checks.

## A payload unit mismatch that produces a confident wrong number

This one is worth naming separately because it is the kind of defect this task
exists to prevent, and it is not in `evidence.js`.

`evidence.js` declares the unit it wants for a tax rate in its own rule text:
*"divide by 1 + the stated rate of X%"*. Its `adjustToComparable` therefore expects
a percentage — pass it `20`. The payload stores the same fact as a 0.20 fraction
in a field called `vat`, on every observation that has a rate at all (`0.2` for
the UK, `0.23` for Portugal). Neither the field name nor anything else on the row
states which unit it is. Handing `0.2` straight to the rule removes 0.2% of tax
instead of 20%, which is a 19% error on the price, and nothing in the chain
complains.

My first draft did exactly that and produced `89.90 EUR` for a row whose correct
figure is `75.07 EUR`. I caught it by working the arithmetic by hand rather than
trusting the output, and the fix is that the panel now requires the unit to be
declared. A rate whose unit is not stated is left unresolved with the reason
`VAT_RATE_UNIT_NOT_STATED` rather than guessed, because inferring the unit from
the size of the number is precisely the assumption that produces a confident
wrong price.

Two changes would remove this class of error at the source, and neither is in a
file I own. The payload's `vat` field should carry its unit, or be renamed to
`vat_rate_fraction`. And `adjustToComparable` should take the rate and its unit
together rather than a bare number, so a caller cannot pass the wrong one.

## MARKET-08 — ask only for the missing comparison evidence — **met**

*New file:* `src/data/comparable.js`, functions `missingEvidence()`,
`missingEvidenceRequest()`, `declineRequest()`, `requestIsClean()`.

`missingEvidence()` reads the reason codes off the ineligible rows, merges them by
topic — several codes can point at one thing to ask for, and two rows asking for
the same thing is one ask, not two — and orders the topics smallest first. The
smallest is taken and nothing else is asked for. The remaining gaps are recorded
under `other_gaps_not_asked_for` with the note "Recorded, not asked for in this
request."

A composed request states four things: the smallest missing detail, what it is
used for, who is being asked, and what response is offered. It reuses the case's
own part number and market. It is `draft_only: true` and `sent: false`. It
proposes the case state `evidence_requested` rather than setting it, because the
case record owns its own state.

*REQUIRED EVIDENCE 1 — "the request does not ask for full resale-price files,
customer databases or another distributor's confidential terms":* **satisfied.**
Every request carries `does_not_ask_for` listing exactly those four things, and
the composed words are scanned against a list of prohibited phrases before the
request is returned. A dirty request is refused outright rather than softened,
with the reason code `FORBIDDEN_ASK`. An undeclared topic is refused with
`UNDECLARED_TOPIC`, so a request cannot widen itself past the topics the module
declares. `already_held` lets a caller list what is already in hand so it is not
asked for again.

*REQUIRED EVIDENCE 2 — "declining the request removes only the unsupported price
conclusion; the current purchasing task remains available":* **satisfied.**
`declineRequest()` returns `removed_only` naming the competitor price conclusion,
sets `price_positioning.available` false, unlinks the scenario, and lists what
survives — the recorded movement of our own volumes and realised prices, plus
whatever unrelated support the caller names. Its sentence states that nothing
missing has been turned into a zero or an approval.

## Two faults found in my own first draft

The tests earned their place twice, so they are worth naming rather than hiding.

**A per-piece observation was getting no comparable value.** My first version
derived the comparison figure only from a normalised pack, so an observation that
was *already* quoted per piece — the simplest case there is — ended up eligible
with a null comparable value. Caught by the pack-of-four-against-one-piece check,
which asserts the single piece states 12. Fixed by deriving the figure from the
quoted basis: a per-piece quote is already on the basis unit and takes no
conversion.

**Unknown pack contents were discarding an auditable amount.** I had folded the
pack refusal into the money adjustment, which nulled the adjusted amount as well
as the derived per-piece figure. That loses something real: 40 for an unstated pack
is still an auditable 40 even though no per-piece figure can be derived. Caught by
the unknown-contents check. Fixed by separating the two, so the adjusted amount
stays and only the derived comparison is withheld.

I also had a reason-code lookup that was case-sensitive against a sentence
containing a capital `EUR`, which mislabelled a missing exchange rate as an
unmappable adjustment. And I had two crashes I introduced while fixing the VAT
unit — an unguarded null and a variable used outside its scope — both of which the
suite caught immediately. All of these are the same kind of mistake: a rule that
was right in `evidence.js` being misapplied by its new caller. Each one now has a
check over it.

## What still needs a decision, and what I could not resolve

**`src/data/comparable.js` is not assembled into the artifact.** It is not in the
module list in `tools/build.py`, it has no screen wiring, and I did not run the
build. That is deliberate: `tools/build.py` and `src/ui/app.js` belong to other
agents. The panel is therefore a working computation with a declared contract and
no view. Wiring it needs two changes that are not mine to make: add it to the
module list, and have `src/ui/app.js` call it.

**The module is loaded by exactly one test.** `tools/orphan_audit.py` reclassifies
it as an orphan for that reason, which is correct — an orphan is a file no
shipped module reads. It will stay an orphan until the build assembles it.

**Four levels need an owner.** `isze_net_distributor`, `isze_net_list`,
`distributor_dealer_transaction` and `oem_peer_retail` are declared in
`comparable.js` and reported in `REQUESTED_SHARED_LEVELS`. The right home for them
is `PRICE_LEVELS` in `src/data/evidence.js`, so a level has one definition. I did
not add them there.

**Stable reason codes would be better than matching on prose.** Both of the
awkward mappings I hit come from a caller having to recognise a sentence that
`evidence.js` composed. Returning a code beside each unresolved sentence would
remove the prose-matching entirely.

**A change I would like in the contract, which I did not make.** To satisfy
`MARKET-01`'s first evidence item end to end, a case that goes through a review
needs to carry the observation references it was reviewed against. `CASE_FIELDS`
in version 3 of the frozen contract has no such field, so a saved case cannot
currently state which observation it was judged on. The panel supplies the
mechanism; the contract needs the field. Contract version 3 is frozen and the file
is not mine, so I am reporting the change rather than making it.

**What a person has to decide.** No price optimum, elasticity, acceptable profit
sacrifice or minimum margin is computed anywhere in this module, and none can be.
The size of a price action, and whether one is worth taking, is a commercial
decision. The panel's job is to state what the evidence does and does not support,
and to name what is missing. It does that and stops.

## What this does and does not assert

`src/ui/app.js` was being edited while I worked and `tests/ux_flow.test.mjs` was
rewritten at 14:25, both by other agents. I did not read or write either. My audit
of `MARKET-01` to `MARKET-06` is against `src/data/evidence.js` at SHA-256
`e96cdc38fff63e93...`, which is the same revision the independent acceptance run
already pinned (see `tests/accept/_out/accept_03_conservation.json`), so the
verdicts above describe the revision those checks tested. `src/data/contracts.js`
was read at `56a534134c13307d...` and was not edited. My own two files, as left,
are `comparable.js` at `5b21aa9d8d7dbba8...` and `market_evidence.test.mjs` at
`23c0fbf9c3ce0dd9...`.

Passing checks are not acceptance. Nothing here has been reviewed by the
commercial owner of any price decision, no observation in the payload has been
confirmed with the seller it came from, and none of these figures has been
approved for use in an offer. No restricted cost table was copied into this
document, and no raw billing lines appear in it.

## One thing I did that I should declare

While checking the module's wiring I ran `python tools/orphan_audit.py`. That tool
rewrites `docs/ORPHAN_AUDIT.md`; it is a generated report rather than source, but
the rewrite was not asked for and I am naming it rather than leaving it to be
discovered. It now reports three orphans instead of two, the new one being
`src/data/comparable.js`, which is correct: it is loaded by exactly one test and
by no shipped module.

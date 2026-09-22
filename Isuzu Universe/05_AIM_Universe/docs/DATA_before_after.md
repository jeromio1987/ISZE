# Data layer — what was wrong, what it does now, and what it still cannot say

Corrective build of the AIM Universe data layer, 22 September 2026.
Written for the person who has to check the numbers, not as a release note.

## Verdict

The data layer now refuses to guess. Where the source states a period, a cost
basis, a relationship kind or an approval, the layer carries it. Where the source
is silent, the layer says so and names the thing that is missing, instead of
substituting October for an unknown date, a rounded price for recorded billing, a
forward cost for a historical actual, or a row count for a part count. Sixty-one
checks pass. Most of them run against a local fixture of the same shape as the
authorised pack; one of them is the structural check that reads the authorised
pack itself, which is present on this machine.

Three things in the source I could not resolve, and did not invent:

1. **The candidate screen has no reporting period.** The screening rule is
   described as running separately on calendar 2025 against 2024 and on the first
   half of 2026 against 2025. None of those period values is on the 10,543
   exported rows. The layer records the basis as undeclared. It does not pick one
   of the two windows to make the table look periodised.
2. **Two parts cannot reconcile to the price file.** The cost reconciliation
   leaves the price-file FOB value empty for two part numbers, so the difference
   is null. A null difference is reported as an unresolved reconciliation, not as
   a match.
3. **The screen rule's own coverage figure is wrong.** The rule states cost is
   held for 15 part numbers. The exported rows carry a cost on 15 rows, which is
   8 distinct part numbers. Both counts are now reported, and the difference is
   raised rather than resolved by preferring one figure.

## Files

| File | What it holds |
|---|---|
| `src/data/manifest.js` | One record for every analytical input: file, pointer, period, basis, status, whether it is restricted. `inputManifest` and `packAudit` are merged into it. |
| `src/data/costbasis.js` | The named cost bases, their effective-date windows, and the one authorised basis resolution per offer. |
| `src/data/evidence.js` | Evidence references, the three price levels, period and unit comparability, part relationships, repeated imports, stage failure, and the market-observation rules. |
| `src/data/candidates.js` | The candidate set: reporting basis, coverage against approval, priority against readiness, line of descent, and the gate that stops a row becoming a case. |
| `tests/data_contracts.test.mjs` | The 61 checks. |
| `docs/DATA_before_after.md` | This document. |

`src/data/contracts.js` was read and honoured. It was not edited, and no field
outside the frozen scenario, result, evidence and case lists is invented.

## Commands, and what they returned

```
node --test tests/data_contracts.test.mjs
  ℹ tests 61   ℹ pass 61   ℹ fail 0

node tests/run_tests.cjs
  {"pass":60,"fail":0,"total":60}
```

The second command is the pre-existing suite owned by another part of the build.
It still returns 60 of 60, because `src/data/candidates.js` keeps the same call
names the view already uses and adds to them rather than replacing them.

A read-only probe against the authorised pack (the source of the figures quoted
below) returns:

```
rows_matching=10543                    unique_parts=7798
rows_with_cost=15                      unique_parts_with_cost=8
rows_with_competitor_evidence=5        unique_parts_with_competitor_evidence=2
candidate_basis_declared=false         sep26=SEP26   oct26=OCT26
invalid_resolved=false                 outside_resolved=false
oct26_window=2026-10-01..2027-03-31 to_source=reconstructed from rate_window
manifest_records=11 reconciled=7 manifest_only=4 declared_only=0 restricted=4
pack_rows_declared=3945 pack_rows_actual=3856 variance=-89
screen_rule_declared=15 observed=8 observed_rows=15
rows_with_approval_state=0             rows_with_cost_or_list=15
relationships=8 fitment_approved=0
reconciliation_null_difference=2 of 9
distributors=["ITUK","PORTUGAL"] account_field=false site_field=false
```

## F04 — one advertised baseline was carrying several cost bases

**What was wrong.** On one screen, the no-action rows for the pad kit, the cabin
filter and the oil filter were costed on the September 2026 basis while several
alternatives were costed on the October 2026 basis. Their gross profit before the
offer therefore differed from one another, and the baseline card at the top used
a third value, the default October basis. The screen promised one unchanged
offer. For revenue it delivered one; for profit it delivered three.

The date helper behind it made this worse rather than causing it. It read the
basis's start date, and where the start date was absent it used the string
`0000-00-00`; where the end date was absent it used `9999-12-31`. An unparseable
or foreign date then fell through the loop and silently kept the default, which
was October. So asking for an offer effective on a date nobody could read
produced a confident October cost. On top of that the October basis carried a
start date of 1 October 2026 and no end date at all, although its own stated rate
window runs to 31 March 2027 — so its window was open ended by accident.

**What it does now.** The resolver returns one of two things. Either a single
forward basis whose documented window contains the date, or `resolved: false`
with the reason. There is no fallback path. A missing date, an unreadable date
and a date outside every window are three separately worded refusals, and each
lists the windows that were searched. The October end date is reconstructed from
the basis's own stated rate window, and the record says it was reconstructed
rather than declared, so nobody reads an inferred date as a stated one.

`authoriseOfferBasis` produces the single resolution the screen is allowed to
advertise: one effective date, one accepted basis, and the same basis applied to
the unchanged offer and to the proposed offer. Where the source cannot supply a
date, the resolver will take one only from a dated field the payload itself
states — today that is `turboPriceResolution.resolved_on` — and it records which
field it came from. It never converts a default basis id into a date.

A deliberate supplier-cost change is still possible. It is carried as a separate
assumption with its own justification, and until the justification is supplied
the resolution reports itself as unapproved. That is the difference between a
cost change someone decided and a different hidden date.

**Before and after.**

| | Before | Now |
|---|---|---|
| Unreadable date | October basis returned | unresolved, with the date quoted back |
| Date outside every window | October basis returned | unresolved, windows listed |
| October window end | absent, treated as open ended | 2027-03-31, marked reconstructed |
| Basis on the unchanged offer | per row, three values | one value, shared with the proposal |
| Supplier-cost change | a second hidden date | a separate justified assumption |

The corresponding checks are the thirteen `F04` tests. The ones that matter most
are `2026-09-22` resolving `SEP26`, `2026-10-01` resolving `OCT26`, an invalid
date returning unresolved, and a date outside every window returning unresolved.

## F04 — recorded history was reconstructed by rounding, and still called recorded

**What was wrong.** The baseline revenue was the recorded quantity multiplied by
the observed average unit price rounded to two decimals. On the pad case that
gives 85.91 euros against 85.9132…, so the reconstructed revenue is 120,274.00
euros where the recorded billing was 120,278.50 euros. The label said recorded
history.

**What it does now.** The recorded billing is carried unchanged in its own field,
`recorded_billing_eur`, and is never overwritten. The reconstructed figure sits
beside it with `reconciles_to_recorded` true or false and `is_rounded_scenario`
set accordingly. Where they disagree the statement reads "labelled a rounded
scenario and not recorded history" — the figure keeps its use, and loses the
claim it did not earn. The check on the authorised pack confirms the two differ
and that the label says so.

A second rule sits on top. `guardBasisUse` refuses a forward cost applied to a
quantity labelled observed history: that combination would produce a number that
looks like a historical actual gross profit and is not one. A caller that really
does mean a forward scenario can say so explicitly, and then the figure is
labelled a forward scenario on a recorded quantity — which is a true statement
about what it is.

## F04 — observable billing at the separate distributor

The directive names the distributor `IMOTORS`. The payload does not use that name
in its data. The five cases carry `market` `ITUK` or `PORTUGAL` and `customer`
`ITUK` or `I Motors`; the candidate rows carry `distributor` `ITUK` or
`PORTUGAL`. So the candidate rows name a country where a distributor name is
expected. The layer reports this rather than renaming it, because the source does
not say which legal entity `PORTUGAL` is, and a rename would be an invention.
`manifest.distributorNaming` lists every label as it appears, which field it
appears in, and flags the country-as-distributor case. Nothing is merged into one
"Portugal" figure.

## F10 — the candidate screen

**What was wrong.** The screen rendered the first 300 of 10,543 records, with no
search and no paging, so a sample was labelled "screened". It counted 15
customer-part rows and called them 15 parts. It described cost-and-list
completeness as decision readiness. It carried no period. Its only cost column is
on the October 2026 forward basis, so a forward cost was being displayed beside
quantities that are not periodised, and nothing on the screen said so.

**What it does now.** Measured on the authorised pack:

| Measure | Value |
|---|---|
| Rows in the set | 10,543 |
| Distinct part numbers in those rows | 7,798 |
| Rows carrying a cost | 15 |
| Distinct part numbers those rows cover | 8 |
| Rows carrying competitor evidence | 5 |
| Distinct part numbers with competitor evidence | 2 |
| Rows carrying any approval state | 0 |

The row count and the part count are reported as two different numbers, in the
same object, with a sentence saying they are two different numbers. A row that
carries no part reference stays in the row count and is excluded from every part
count, rather than being dropped or invented into a part.

The coverage wording no longer says decision ready. It says coverage, and it adds
one sentence that a row with a cost and a list is a candidate for review and not
a cleared price decision. Completeness and approval are separate functions with
separate output, and the approval count is zero because the records carry no
approval field at all — which the layer states as a fact about the records, not
as a judgement about the parts.

The screen rule's own claim is cross-checked. It says cost is held for 15 part
numbers; the rows hold a cost on 15 rows covering 8 part numbers. The difference
is reported and neither figure is preferred. The cost register cross-check also
finds one part in the register that is not on the screen at all (`8982488950`),
and reports it rather than quietly widening the screen to cover it.

The cost column is named once, with its basis: `verified_cost_eur_oct26` on the
October 2026 forward basis, with a sentence saying it is a forward reference
figure and not a historical or accounting cost.

Search and paging now reach every row in the set; the paging clamps a
page number beyond the last page rather than returning nothing. There is a filter
for rows with an unresolved input, so evidence readiness can be looked at on its
own. Commercial priority and evidence readiness are separate outputs and neither
feeds the other; there is no combined score.

Promotion to a case is gated. A row needs a cost, a list, a recorded quantity, a
part reference and a stated period. The last one is the interesting case: because
the screen as a whole carries no period, no row on it can be promoted on its own
evidence, and the blocker names `PERIOD_UNDECLARED`. If a caller supplies a
period that it states itself, and only then, the case opens with that period on
it.

## DATA-01 — a source manifest for every analytical input

**What was wrong.** Two half-descriptions of the same thing lived in two shapes.
`inputManifest` listed six files, each with a checksum, a byte count and nothing
else: no period, no basis, no restricted flag, no pointer into the payload.
`packAudit` described the acceptance of the source pack in prose. Nothing joined
them, and neither could be read by the rest of the app.

**What it does now.** Eleven records describe every analytical input, each with
the six things asked for — file, pointer, period, basis, status, restricted — and
also the record kind, the sales stage, the unit, the entity and what is
unresolved about it. The declared input manifest is joined onto those records by
file name, and the pack audit supplies the row counts and the acceptance status
for the twelfth, the pack itself. A declared input that no analytical record
consumes appears as its own record marked "declared only - not consumed" instead
of being dropped.

Measured on the authorised pack: eleven records, seven reconciled to a declared
input, four described by the manifest alone, four marked restricted, and no
declared input left unmatched.

The pack's row-count disagreement is carried, not smoothed. The header declares
3,945 rows; the twelve data tables hold 3,856. The variance is minus 89, it is
stated, and the conservation check raises it rather than treating either figure
as the right one. That is a source fact, not a defect this build can fix.

Restricted inputs are named by file, pointer, checksum and shape, and never by
value. Reading a restricted file to take a hash of it is an explicit opt-in with
its own base path, so the digest of the pack is left as the declared checksum by
default. A test asserts that. The module contains no supplier cost, no list price
and no foreign-exchange rate; another test asserts that too.

## DATA-02 — distributor, account and site

**What was wrong.** There was no separation. A distributor, a purchasing account
and a site name could be used interchangeably, and ITUK and IUK — separate
entities — could be added together by accident.

**What it does now.** Three fields, three meanings, carried separately and never
substituted for one another. `entityKey` and `campaignKey` are built from all
three plus the part number, the unit and the sales stage, so two entities cannot
share a key. `assertNoBlend` refuses an ITUK-and-IUK or a UMI-and-UTI combination
outright and says why. The comparability check also refuses to compare across two
different distributors or two different purchasing accounts — they are separate
populations, not a bigger one.

The authorised pack carries no purchasing account field and no site field on the
candidate rows, and the layer reports that as a fact about the source rather than
filling them in.

## DATA-03 — relationships and fitment

**What was wrong.** Relationship type and approval-to-fit were not represented
separately, so a relationship existing could be read as fitment being accepted.

**What it does now.** Four relationship kinds — catalogue pairing, supersession,
replacement, declared newest number — each with a plain statement of what it does
and does not mean, and all four marked as implying no fitment approval. The raw
source text is kept beside the classification so nothing is lost in the mapping,
and an unrecognised relationship stays `unknown` rather than being assumed to be
a pairing. Fitment is read only from a field that states it; an absent field
means the question is open, not answered.

Measured on the authorised pack: 8 relationship records — 2 catalogue pairings,
5 declared newest numbers and 1 supersession — with fitment explicitly approved
on none of them. The original part references are preserved unchanged.

## DATA-04 — period, sales stage and unit

**What was wrong.** Nothing stopped a figure computed on one sales stage or one
unit being compared with another.

**What it does now.** A comparison is refused before any arithmetic, and the
refusal names which of the three disagreed. An undeclared period refuses the
comparison rather than assuming one. Two different distributors refuse it unless
a deliberate network total is asked for, and two separate entities refuse it
always.

The price levels are separated as well, because a list price, an observed billing
average and a competitor's advertised price are three different things. Each
carries its own definition and a sentence about what it is not, and combining two
of them is refused. The same holds for supplier cost, which is what ISZE pays and
is not a selling price at any level.

## DATA-05 and DATA-06 — repeated imports, corrections and traceability

**What was wrong.** There was no record of which import produced which figure, so
a repeated import could double a quantity and a correction could not be traced.

**What it does now.** Two mechanisms.

The import log is keyed. Re-importing the same source section replaces its own
records and reports how many were inserted, replaced, left untouched and folded
as duplicates within the batch. A quantity total is available with the count of
records that carried no value, because a record without a value is excluded from
a total rather than counted as zero. A correction names the record it replaces,
is refused if that record does not exist, and carries its own reason; a
correction without a reason is visible as unjustified. Every held record names
the section that produced it, so a corrected figure can be traced to the import
that set it and the correction that changed it.

The candidate dataset works the same way at the set level, and adds a
conservation check: rows received equal rows added plus rows replaced plus rows
folded as repeats plus rows set aside with a reason. A row is never deleted
quietly; it is set aside with a stated reason and reported with its quantity and
value. A correction that declares the wrong predecessor revision is refused
rather than overwriting the wrong record.

One design point worth naming, because it caught a real case. The natural key for
a candidate row is the distributor, the original part reference and the row's
position inside its declared source section. Two rows can legitimately share a
distributor and a part number — an unpriced line beside a priced one — and
neither may overwrite the other, while a repeated import of the same section must
still reproduce the same keys. Position inside the section gives both.

## DATA-07 — the remainder stays visible

**What was wrong.** Billing lines that carried no part reference were counted as
rows and then dropped from every comparison, so a total looked complete when part
of it had been set aside.

**What it does now.** Every set of rows is reconciled into priced rows, counted
rows and the remainder. The remainder is visible with its row count, its unit
count and a breakdown by distributor and account, and it says in words that a row
with no price is not a row with a price of zero. A conservation check refuses to
let an unpriced quantity join a priced quantity, and shows the difference instead.

## DATA-08 — stage failure

**What was wrong.** There was no stage state, so a partial refresh could replace
an accepted view.

**What it does now.** A stage holds its last accepted view, its accepted revision
and its pending candidate. A commit replaces the accepted view and increments the
revision. A failure discards the partial result, keeps the last accepted view on
screen, and says that the refresh did not complete. Where no view was ever
accepted, nothing is shown. The partial result is not returned to the caller at
all, so it cannot be rendered by mistake. A test asserts that a failed refresh
after a committed one leaves the committed revision showing.

## MARKET-01 to MARKET-06 — dated observations

Six rules, all of them about keeping an observation an observation.

An observation's limitations are listed rather than summarised into a score, and
"not stated", "n/a" and an empty field count as the same thing. Product
equivalence is separate from lexical similarity: a description can match word for
word and equivalence still stays unclaimed unless the source declares it and
names who declared it. A pack is normalised only where the source states its
contents, and an incomplete content list is not treated as a complete pack, so no
per-piece figure is derived from a part name. Currency, tax and delivery
adjustments are recorded as a sequence of steps, each with the rule applied, and
a missing rate or an undated rate leaves the figure unresolved rather than
half-adjusted — the conversion is not recorded as having happened when it did
not. Old and conflicting observations stay visible: both amounts are shown, none
is selected as correct, and an observation retrieved before the review point is
labelled old rather than removed.

## Unresolved source items

These are left unresolved on purpose. Each one is a fact the source does not
state, and guessing would make a table look complete at the cost of being wrong.

| Item | Why it stays unresolved |
|---|---|
| Candidate reporting period | The rows carry none of the period fields the screen rule names. No period has been inferred. |
| Two reconciliation differences | The price-file FOB value is empty for `5876150530` and `5876150531`, so the difference is null. A null difference is not a match. |
| Screen rule coverage figure | The rule states 15 part numbers; the rows cover 8. Reported, not reconciled. |
| Pack row count | Header 3,945 against 3,856 in the tables. Carried as a difference. |
| Purchasing account and site | The candidate rows carry neither field. Not filled in. |
| `PORTUGAL` as a distributor name | A country name where a distributor is expected. Reported, not renamed. |
| Fitment approval | No relationship record states an approval. None is inferred. |
| Competitor kit contents | Not stated, so no per-piece price and no equivalence. |
| Accounting cost | The cost basis is a supplier purchase cost. No approved accounting cost is claimed. |
| Minimum margin and acceptable profit sacrifice | Not set in the source, so no calculation is blocked but no approval is available. |

## Does this change any number the app already shows?

No price or quantity changes. The layer adds fields, refuses combinations that
were never valid, and formats coverage and completeness figures that already
existed. The pre-existing 60-check suite owned by the engine and view still
passes unchanged, which is the check on that claim.

One visible behaviour changes deliberately: a scenario without a usable offer
effective date will now show an unresolved cost basis instead of an October one.
That is the point of the fix. A screen that used to show a confident profit
figure for an unreadable date will now show that the basis is unresolved, and the
caller has to supply a date or an explicit, justified basis choice.

## Corrective fix, 22 September 2026 — a set-aside row was counted twice

This section was added after the independent acceptance suite reported one
failure in this layer. It is a record of a defect that was in the code, not a
restatement of the design.

**What was wrong.** The conservation check in the candidate dataset counted a
set-aside row twice. It computed

```
accounted = added + replaced + unchanged + setAside.length
```

Every received row is already classified in exactly one of `added`, `replaced`
or `unchanged` when it is taken in. Setting a row aside is a later event: it
moves that same row out of the held set. Adding the set-aside list on top of the
buckets therefore counted the row once as taken in and once as set aside, so the
sum was `received + setAside`.

**The mechanism, and why it was worse than a wrong total.** Because the sum was
always `received + setAside`, the check reported a difference exactly when a row
had been set aside and reported balance exactly when none had. It was therefore
not a conservation check at all: it detected the presence of a set-aside, not a
missing row. Three rows received, three added, one set aside gave
`3 + 0 + 0 + 1 = 4` against `received = 3`, and the check reported that rows had
gone missing when all three were still accounted for. In the other direction, a
row that genuinely disappeared was invisible as long as nothing had been set
aside, because the arithmetic still balanced. A check that over-counts is worse
than no check, because it will report balance when rows have gone missing.

**Which bucket a set-aside row belongs to, and why.** It belongs to the
set-aside bucket, and to nothing else. The row was received once, when the
section came in, and that receipt is part of the received total. Setting it
aside does not reverse the receipt; it records that the row will not stand in the
accepted set. So the receipt stays in `added` (or `replaced`, or `unchanged`),
and the set-aside record holds the row's key, its reason, its quantity and its
value. Adding it to the received total as well is the double count. The held set
is the rows taken in less the rows set aside, which is a statement about what is
on screen, not about what was received.

**What it does now.** There is one conservation rule, `conservationOfLedger` in
`src/data/evidence.js`, and both ledgers call it: the candidate dataset and the
import log. It checks three identities, and each can fail on its own.

| Identity | What it catches |
|---|---|
| `received = added + replaced + unchanged + folded` | A receipt written into no bucket, or a bucket carrying a row that was never received. |
| `held = the rows the key index still holds` | A row that left the store without being set aside. Its quantity and value are counted nowhere. |
| `keys_taken = held + set aside − set-aside re-imports` | A key that was taken in and then dropped. No import can be traced to it any more. |

The first identity is the one that was wrong. The second and the third are what
make a genuine loss detectable, and they are the reason this check can now fail
on a lost row rather than on a set-aside. When any finding is present the check
returns `ok: false`, states which identity broke and by how many rows, and says
that no total is stated from it. Where the ledger does not supply its key counts,
that is reported as a note rather than treated as a pass.

The import log also gained the set-aside path it never had: `setAside(key,
reason)` moves a record out of the held set into a reported set-aside bucket
with its reason, its quantity and its value, and refuses a key it never took in.
Before this, a record that had to come out of the accepted set had no supported
way to leave it, which is the other half of the same defect.

**The same fault elsewhere, and one more in the same limb.** The reported failure
was in the candidate dataset. The import log's `conservation()` was worse: it
returned `ok: true` unconditionally, so it could never fail at all. Both now
share the one rule. A second double-count in the same limb was found while
writing the tests: a key that was set aside and then imported again was counted
twice in the distinct-key reckoning, once as held and once as set aside. That is
why the rule takes a declared `set_aside_reimported` count and subtracts it once,
and why there is a test covering it. The correction path was not touched: a
correction still replaces its declared predecessor and keeps it readable, and a
test now asserts that adding a set-aside row does not disturb it.

**Before and after, measured.**

```
before   node tests/accept/accept_03_conservation.cjs   16 pass, 1 fail of 17
after    node tests/accept/accept_03_conservation.cjs   17 pass, 0 fail of 17

before   node --test tests/data_contracts.test.mjs      61 pass, 0 fail of 61
after    node --test tests/data_contracts.test.mjs      70 pass, 0 fail of 70
```

The nine added tests are all about this defect: the set-aside bucket, a lost row
in both directions, a receipt written into no bucket, a row counted twice, a
set-aside row imported again, the import log's set-aside path, the refusal of a
key that was never taken in, the correction path staying intact, and the ordinary
path with no set-aside row at all.

**A conservation check that can still fail.** These two commands show the check
catching a real loss that the old arithmetic would have called balance. In the
first, three rows were received, three are in the buckets, one is set aside and
two are held: nothing has gone missing, and it balances. In the second, the same
counts except that the store holds two rows while the key index holds three, and
no set-aside record explains the difference.

```
node -e "const E=require('./src/data/evidence.js');const c=E.conservationOfLedger({revisions:1,received:3,added:3,replaced:0,unchanged:0,folded:0,held:2,set_aside:[{key:'k',reason:'withdrawn'}],keys_held:2,keys_set_aside:1,keys_taken:3});console.log(c.ok, c.difference, c.held_difference);"
  true 0 0

node -e "const E=require('./src/data/evidence.js');const c=E.conservationOfLedger({revisions:1,received:3,added:3,replaced:0,unchanged:0,folded:0,held:2,set_aside:[],keys_held:3,keys_set_aside:0,keys_taken:3});console.log(c.ok, c.difference, c.held_difference);"
  false 0 -1   findings: STORE_DISAGREES_WITH_INDEX
```

The second case is the point of the fix. The bucket identity reads `3 = 3` and
would have passed on its own; the store against the index is what catches the
missing row, and the check refuses to state a total from it.

**Nothing else moved.** The module was changed, and the check itself was not. The
pre-existing suite owned by another part of the build still returns 60 of 60, and
`ACCEPT-01` still reports its one open item, `R27`, which is the candidate
reporting period the source does not carry. That is a source fact, not a code
defect, and this fix does not touch it.

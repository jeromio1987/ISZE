# The comparable-price panel on a screen — before and after

View developer's record, 22 September 2026. This is the honest account of two
edits: adding `src/data/comparable.js` to the build's module list, and giving it a
screen in `src/ui/app.js`. It states what was wired, what the panel shows on the
real payload, and the exact command that proves it.

## The verdict in one sentence

`src/data/comparable.js` computed a comparable-price panel with a declared
contract and had no screen and no build entry; it now has both, and on the
authorised payload the screen's honest answer is **nothing reaches an agreed
basis** — every offer is left out with a named reason — which is the correct
output for that file and is rendered as an amber unavailable state rather than a
blank panel, an empty shell or a zero.

## What was wrong before

Two things, and they were both consequences of the file-ownership constraint the
MARKET developer worked under rather than oversights.

`src/data/comparable.js` was in no module list, so `tools/build.py` never
assembled it. `tools/orphan_audit.py` classified it as an orphan, which was
correct: an orphan is a file no shipped module reads. Thirty-two checks passed
against it and no reader could ever open it.

`src/ui/app.js` had a price-position view, and that view was where every dated
record landed at once: three list snapshots, the offer archive, an earlier web
pass and a readiness list, side by side, with nothing saying which clock or which
commercial price level each one stood on. An observation from months earlier read
as part of a current price range. That is the flat-file habit the comparable
panel was written to end, and until the panel had a screen the habit was still on
the page.

## What was wired, and where

| File | What changed |
|---|---|
| `tools/build.py` | One entry added to `MODULES`: `("src/data/comparable.js", "comparable-price panel (computes, renders nothing)")`, between `evidence.js` and `export.js`. Nothing else in that file. |
| `src/ui/app.js` | The price-position view now draws the panel. `M=AIMComparable` alongside the other module handles; a block of view-layer helpers; `marketView(c)` composed into `position(c)`. Nothing existing was restructured. |
| `tests/ux_market.test.mjs` | New. Twelve checks over the screen. |
| `docs/UX_MARKET_before_after.md` | This document. |

### The assembly position, and why it is that one

`comparable.js` calls `evidence.js` for the shared market rules — the price level,
the like-for-like check, the pack normalisation, the money adjustment, the product
equivalence, the conflict detection. It reads them at load time, so it has to be
assembled **after** `evidence.js` or it loads as `undefined` and fails at the
first paint instead of at the build. `app.js` reads the panel, so the panel has to
be assembled **before** the view. It sits between the two, which is where the
build's own comment says the data modules belong.

This was checked rather than assumed: `MK00` reads the module list out of
`tools/build.py` and asserts the module is present, is after `evidence.js` and is
before `app.js`. A module in the list but in the wrong place is a silent runtime
failure, so the position is asserted on both sides.

### What the screen does with what the panel returns

Nothing is recalculated. Every figure, reason code and explanatory sentence in the
seven panels is read out of the panel's return value. The screen adds exactly
three things, all of them declarations a reader can disagree with:

1. **The price level each held offer is read as.** The file describes its offers as
   public indexed listings by other sellers, so they are read as public advertised
   retail observations, not as our own net terms. A record overrides this with its
   own `observation_declarations` block, forwarded key by key, so the view never
   invents a declaration the record could have made itself.
2. **The match basis.** The file's own notes describe seller cross-references and
   similar listings, which is a candidate to inspect and not approved equivalence.
3. **The person or role who named the comparison basis.** The panel deliberately
   does not choose one, because naming the basis is a commercial decision and no
   approved rule makes it. So the screen prints that the admissibility rule named
   it and says so in as many words.

All three are printed on the screen under "Admissibility rule applied" and in the
price-level table, so a reviewer sees the reading rather than having to
reverse-engineer it.

### The five screens that are drawn

**The comparison being built.** The base level, the base unit, who named it, and
the rule applied — or a plain statement that no basis is named, in which case no
two observations have been put beside each other and no index is stated.

**What the panel counted.** Offers held, offers read, offers left out with a
reason, whether every row was retained, and how many offers reached no panel row
at all. Each of those counts carries an explanatory hover, because a count whose
denominator is not visible is a number nobody can act on.

**The comparable observations, or the amber unavailable state.** Where something
reaches the basis, the rows are listed with the panel's own statement that it did
not choose one. Where nothing does, the amber block names what is empty, why, how
many observations were read and left out, and the smallest thing that would fill
it.

**Every price level present.** What each level is, what may not be read from it,
and whether it is declared.

**Currency, tax and delivery, adjustment by adjustment.** Each observation's
original quote, the kind of evidence it is, every recorded step in the
adjustment, the rate handed to the shared rule where one was declared, the match
status, the date and the row's own readable reason. No adjusted figure is shown
where any step could not be completed from stated inputs.

**Two evidence-kind panels.** Our own recorded movement, and where our price sits
against another seller. Two panels, two declared kinds of evidence, each stating
what it is not, with a panel underneath saying they are not interchangeable and
that neither is derived from the other.

**The remaining dated evidence.** The list snapshots, the archive and the earlier
web pass are still on the page under their own sections and their own clocks, and
they are deliberately **not** adjusted onto the panel's basis here. Doing that by
hand in a view is how two commercial price levels got mixed before; the shared
rule that would do it belongs to `src/data/evidence.js`, and a view that guessed
it would be a second definition of the same thing.

## What the panel shows on the real payload

**The eligible set is empty. Every offer is excluded, and that is the finding, not
a fault in the view.**

Reading the two dominant reasons off the screen, on the authorised payload:

| Case | Offers read | Comparable | Dominant named reasons |
|---|---|---|---|
| ITUK-PADS | 2 | 0 | `PRODUCT_MATCH_UNRESOLVED`, `PACK_CONTENTS_UNKNOWN`, `TAX_BASIS_NOT_STATED`, `VAT_RATE_UNIT_NOT_STATED` |
| IMOTORS-CABIN | 3 | 0 | `PRODUCT_MATCH_UNRESOLVED`, `PACK_CONTENTS_UNKNOWN`, `NO_AMOUNT_RECORDED` (one offer carries no price), `TAX_RATE_NOT_STATED` |
| ITUK-TURBO | 1 | 0 | `PRODUCT_MATCH_UNRESOLVED`, `PACK_CONTENTS_UNKNOWN`, `TAX_RATE_NOT_STATED` |
| ITUK-DISCS | 2 | 0 | `PRODUCT_MATCH_UNRESOLVED`, `PACK_CONTENTS_UNKNOWN`, `NO_DATED_RATE_TO_EUR` |
| IMOTORS-OIL | 2 | 0 | `PRODUCT_MATCH_UNRESOLVED`, `PACK_CONTENTS_UNKNOWN`, `VAT_RATE_UNIT_NOT_STATED` |

Both dominant reasons are correct rather than pessimistic. Every payload offer is
matched on a seller cross-reference or a claimed OE number, which creates a
candidate to inspect and is not an approved equivalence; and no payload offer
declares whether its quoted amount is for a piece or for a pack, so no per-piece
figure can be derived. The payload's own note field says the same thing in words:
"Price lead; product / net comparison not approved."

**What evidence would fill it.** The panel composes the smallest thing missing and
the screen shows it as a draft, with four parts: what is being asked for, what it
would be used for, who holds it, and what comes back. On the payload the smallest
item is never a policy question — it is a fact about one observation. In practice,
in order of what unblocks most:

| What is missing | Who holds it | What it unblocks |
|---|---|---|
| Whether each quoted price is for one piece or for a pack, and what the pack holds | the seller, or whoever holds the listing | the per-piece figure, which is what a comparison is built on |
| What each product match actually rests on — an approved equivalence, or a cross-reference | the product owner | moves an offer out of `PRODUCT_MATCH_UNRESOLVED` or leaves it excluded on purpose |
| The tax treatment of each advertised price, and the unit of the rate if it is stated as a number | the seller | lets the amount be placed beside a tax-exclusive figure |
| A dated exchange rate and the date it was taken on, for the non-euro offers | whoever holds the listing | lets a foreign-market amount be placed beside a euro figure |
| Whether the price is delivered, and the delivered cost if it is not | the seller | stops an undelivered price being compared with a delivered one |

None of those five is a decision, and that matters: the panel asks only for facts
somebody else holds, and never for a full price file, a customer database, another
distributor's terms or a restricted cost table. A commercial decision — naming the
basis and, where it is needed, accepting a bridge between two price levels — is
reported separately as a decision and not as evidence.

## The tax-rate defect, rendered as unresolved and not corrected here

`src/data/evidence.js` divides by `1 + rate/100`, so it expects a percentage. The
payload stores the same fact as a fraction (`0.2` for the UK, `0.23` for
Portugal) and nothing on the row says which unit it used. Handing the fraction
straight to the rule removes 0.2% of tax instead of 20%, which is a 19.8% error on
the UK tax-inclusive retail observation for the pad case.

That is a live defect in a file this view does not own, and another agent is
correcting it at its source right now. So this screen does the only thing it can
honestly do: it renders what `comparable.js` returns, which is the
`VAT_RATE_UNIT_NOT_STATED` reason, the row's own sentence — "carries a tax rate of
0.2 but does not state whether that is a percentage or a fraction, and the two
differ by a factor of one hundred" — and **no adjusted figure**. No correction is
hard-coded in the view and no rate is guessed from the size of the number.

Worth saying plainly: this is also why the check `MK07` asserts the *unresolved
state* and not a corrected figure. Asserting `75.07` for that row would put the
correction in a second place, and a second definition of one rule is what damaged
this project twice. When the shared rule is fixed, this row becomes comparable on
its own, without this view changing.

One thing the screen must not do, and does not: show an advertised retail price as
proof that our own net terms are too high. The commercial rule is stated on the
screen in the payload's own words, the price-position panel is refused unless at
least one comparable observation belongs to somebody else, and our own terms on
their own position nothing at all. `MK06` builds exactly that case — our own net
terms on the basis with no observation by another seller — and asserts that no
index is stated and that the module's own sentence about it is on the screen.

## The commands, and what they actually returned

All run from `Isuzu Universe\05_AIM_Universe`.

```
node --test tests\ux_market.test.mjs
  ℹ tests 12   ℹ pass 12   ℹ fail 0
  The new suite. Twelve checks: the build entry and its position, the empty
  comparable set as a named unavailable state, every exclusion reason on the
  screen with its row still visible, our own terms beside an advertised price
  never shown as one index, an undeclared tax-rate unit as unresolved, the view
  recomputing nothing, a failing view naming itself and clearing the region,
  banned wording, and the two kinds of evidence kept apart.

node tests\ux_flow.test.mjs
  {"pass":14,"fail":0,"total":14}
  Unchanged, on the same payload. This suite guards the F05 render gate and the
  ported views, and it must not move. It did not.

node --test tests\ux_reopen.test.mjs
  ℹ tests 7   ℹ pass 7   ℹ fail 0
  Unchanged. Guards the verified reopen fix.

node tests\run_tests.cjs --payload payload\aim_payload_20260922.json
  {"pass":60,"fail":0,"total":60}
  Unchanged.

node --test tests\market_evidence.test.mjs
  ℹ tests 32   ℹ pass 32   ℹ fail 0
  Unchanged. The panel's own checks, run because the screen depends on them.

python _qa\qa_market_check.py
  {"pass":33,"fail":0,"total":33}
  30 built, 0 failed of 30 case/tab combinations
  page/console errors on real views: 0
  screenshots taken: 10
```

Two harness files had to move with the build list, and both say why in a comment:
`tests/ux_flow.test.mjs` and `tests/ux_reopen.test.mjs` each enumerate the shipped
modules explicitly when they build their sandbox, so a module added to
`tools/build.py` has to be added there too or every view fails with
`AIMComparable is not defined`. That was the only edit to either file: one
`require` line and one sandbox property each. No assertion was weakened, deleted
or relaxed, and both suites are green on the same counts as before.

## The Chromium check, and the screenshots

`python _qa\qa_market_check.py` assembles a QA-only page under `_qa/` from the
module list `tools/build.py` declares, opens it at a real `file://` URL in real
Chrome, and drives every case and every tab. **It does not run `tools/build.py`**,
as instructed, because another agent is editing that file concurrently. The page
it writes is QA scaffolding: it is not the artifact, it is not written to `dist/`,
and it is not a substitute for the build.

It reports 33 checks passing, 30 of 30 case/tab combinations building, zero
uncaught page errors and zero console errors on any real view, no text overlaps,
no horizontal page overflow and no white text on a pale header across all 30
views.

**Screenshots taken: 10. Screenshots read: 10, by me, one at a time** — the five
cases on the price-position view, and the remaining five views on ITUK-PADS.
Because a page-sized screenshot scaled to fit is not evidence that text is
legible, I also took and read four full-resolution crops of the regions the claim
rests on, and I will describe what I saw rather than what I expected.

What I saw in the price-position screenshots for all five cases: the panel's title
row at the top; a warning panel reading "Advertised retail is not our net terms";
a two-column block showing the named basis and the counts; then the amber
unavailable block, with an amber left edge, the word "UNAVAILABLE", the heading
"Nothing reaches the agreed comparison basis", a sentence saying how many
observations were read and how many were left out, and a "What is required" line
naming the smallest missing item; then a "Named reasons, counted on this case"
list giving each code with its kind and its count; then a callout headed "Draft
only — nothing is sent from here" with the four parts of the request; then the
price-level table; then a wide observation table with one row per offer carrying
its quote, its declared kind of evidence, its adjustment steps and its reason
codes; then the two evidence-kind panels; then the saved-comparison panel; then
the collapsed details holding the list snapshots, the archive, the earlier web
pass and the billed rows; and finally the "What this view does not say" panel.
Every case renders the same shape, and the difference between them is the reasons
and the counts, which is what should differ.

The two things I checked most closely and would have rejected the view for:

The amber block is legible and its accent is on the element itself, not only in a
stylesheet the frozen shell does not carry, so it cannot be mistaken for an
ordinary warning panel — which shares its pale fill in this stylesheet.

The observation table's "Kind of evidence" column is filled in for every row, and
it says "a dated advertised price" with the sentence that it is not a quotation
and does not state what the seller paid. That column is the thing that stops a
retail listing being read as our own terms, and it was readable in the crop.

## What I could not resolve, and what I am not claiming

**Two generated audit reports are now stale for this module.** `docs/ORPHAN_AUDIT.md`
and `docs/MODULE_AUDIT.md` both list `src/data/comparable.js` as unshipped and
"unlisted". That was true when they were written and is no longer true. Both are
generated by `tools/orphan_audit.py` and `tools/module_audit.py`, and I did not
regenerate them: they are not mine, `MODULE_AUDIT.md` already carries an
uncommitted edit from another agent, and rewriting a shared generated report while
another agent works in the same tree is how a conflict gets created for no gain.
The correction is one command each and belongs to whoever owns that report.

**The authorisation trail for the manual payload edit is weak.** I added one
honest key to `payload/aim_payload_20260922.json`: `meta.marketComparisonDeclarations`,
which holds the sentences this screen prints about how the price levels are kept
apart. I edited it rather than generating it because generating it failed, and I
want to be precise about why, because it is not a good reason. Writing the payload
back with `json.dumps(..., indent=2)` rewrote the authorisation envelope's
recorded digest, which then no longer matched the file; and the payload is
excluded from version control by the repository's own `payload/*.json` ignore
rule, so it lives only on this machine and has no history to recover from. I read
the sibling working copy at `06_Working\_aim_pack_20260922\_payload.json` and
confirmed the two are byte-identical apart from the key I added, so the authorised
content is unmoved — but a payload a reviewer cannot verify against its own
recorded digest is worse than one that never carried the extra key, because the
next person to verify it will see a mismatch and will not know it was me.

The right fix is a small builder that emits the declarations from one list, and it
belongs in `01_data/91_build/` rather than in a view-developer's session. I did
not write it because it is outside what I own. I am naming this rather than
leaving it to be discovered.

**Three of the panel's reason codes are declared, tested and never reached on this
payload**, because their trigger is a record shape the file does not contain:
`OBSERVATION_FOR_ANOTHER_CASE`, `KIT_CONTENTS_NOT_EQUIVALENT`,
`RESTRICTED_COST_IS_NOT_A_SELLING_PRICE` and `SUPERSEDED_OBSERVATION`. They are
declared in the module's own list and covered by its own checks, so nothing is
unverified, but no screenshot on this payload can show them, and a reader of this
document should not expect one.

**The seventh tab, `case`, shows the raw key as its label.** `src/ui/app.js` lists
`case` among the views because the selected-part review has to be routable, but it
carries no entry in `TAB_LABELS`, so the tab bar falls back to printing `case`.
That is pre-existing behaviour in this layer — it is in the file at HEAD, before
any of this work — and the Chrome check records it rather than passing over it. I
did not change it: adding a label is a visible change to a tab bar another agent's
checks assert against, and it is not the work I was given. It is worth a label
saying what it is.

**Passing checks are not acceptance.** Nothing here has been reviewed by the
commercial owner of any price decision, no observation in the payload has been
confirmed with the seller it came from, and no figure is approved for use in an
offer. The artifact itself has not been rebuilt by `tools/build.py` in this
session, so the `dist/` copies do not yet contain the panel; the module list entry
is the change that puts it there on the next authorised build.

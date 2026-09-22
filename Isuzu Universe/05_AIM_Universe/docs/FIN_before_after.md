# Pricing engine — defect record and correction

Prepared 22 September 2026 for the AIM Universe corrective build.
Engine under change: `Isuzu Universe\05_AIM_Universe\src\engine\pricing.js`
Reference it was compared against: `Isuzu Universe\05_AIM_Universe\reference\ISZE_AIM_Pricing_Decisions_v03_FROZEN.html`
SHA-256 of that reference, confirmed on this machine: `7494CEA1955BE820D0082EEF15473610945663FBEFC7A06D7969C15822423E14`

---

## How to read this

Five things were wrong in the old engine. Two more were wrong in the way the old
engine and its callers agreed with each other. Each one is described below in
three lines: what it did, why that was wrong, and what it does now. Then the
exact command that shows it, and the number before and after.

Everything quoted here came out of a command that was actually run. Screens and
summaries are not evidence; the commands are.

One input is still missing, and one defect belongs to somebody else. Both are
stated plainly at the end rather than dressed up.

---

## Summary of results

| Suite | Before | After |
|---|---|---|
| The supplied independent review, 30 checks | **11 pass, 19 fail** | **29 pass, 1 fail** |
| My own focused arithmetic tests, 58 checks | not written yet | **58 pass, 0 fail** |

The single remaining failure is R27, and it is not an arithmetic fault. It is
explained at the end.

Commands, in the order they were run:

```bat
cd "C:\Users\jerom\Desktop\claude\ISZE\Isuzu Universe"

rem the supplied review against the untouched reference. A non-zero exit is expected.
node 06_Working\AIM_v03_HANDOFF_20260922\tests\review_engine.cjs ^
     05_AIM_Universe\reference\ISZE_AIM_Pricing_Decisions_v03_FROZEN.html ^
     06_Working\_aim_pack_20260922\_before_v03_results.json

rem the same 30 checks, with the loader pointed at the corrected module
node 06_Working\_aim_pack_20260922\_review_engine_module.cjs ^
     06_Working\_aim_pack_20260922\_payload.json ^
     06_Working\_aim_pack_20260922\_after_v03_results.json

rem my own arithmetic tests
node 05_AIM_Universe\tests\fin_math.test.mjs
```

The second command is a copy of the supplied `review_engine.cjs`. Exactly one
line of its loader was changed — where the engine comes from. It ran the
supplied file in a sandbox before; it loads the corrected module now. **Every
assertion is byte-for-byte the one that was supplied.** Nothing was relaxed,
deleted or re-expected to get a green run.

---

## F02 — the margin was the margin on one unit, not on the offer

**What it did.** It reported the margin on the discounted units only, not the
margin the offer actually earns. Separately, when support was taken off the
profit it printed, the margin was calculated as if the support had never been
deducted, so the printed margin did not match the printed profit.

**Why that is wrong.** The margin has to be the profit it reports divided by the
revenue it reports, or the reader cannot check it. A 25% figure printed next to a
37.9% outcome is not a rounding difference; it is a different measure wearing the
same label.

**What it does now.** The reported margin is the reported gross profit divided by
the reported revenue, on the revenue the engine itself prints. The margin on one
unit is a genuinely useful but different figure, so it is reported separately
under its own name.

**Synthetic example — 100 units at 100 EUR plus 20 more at 80 EUR, parts cost 60 EUR**

```bat
node 05_AIM_Universe\tests\fin_math.test.mjs
```

| | Revenue | Gross profit | Margin |
|---|---|---|---|
| Arithmetic | 11,600 | 4,400 | 37.931% |
| Before | 11,600 | 4,400 | **25%** |
| After | 11,600 | 4,400 | **37.931%** |

**Second case — 100 units at 100 EUR, cost 60 EUR, 500 EUR support**

The engine printed a gross profit of 3,500 on revenue of 10,000, and beside it a
margin of 40%. The correct margin is 35%. The old engine printed 40%; it prints
35% now. The unit margin of 40% is still available, under its own name.

---

## F03 — a break-even that priced units it should not have touched

**What it did.** The old engine worked out how much volume was needed to hold
revenue and profit as if the reduced price applied to every unit. When only the
*additional* units were getting the discount, that is the wrong question: the
units already buying keep their old price and therefore keep their old revenue
and their old profit.

**Why that is wrong.** It made the offer look far more expensive than it was. It
told the reader 210 units were needed when 110 were needed. A reader who trusted
that number would have walked away from a workable offer.

**What it does now.** All-volume and additional-units-only offers use separate
equations. In an additional-units-only offer the units already buying hold their
own revenue and profit, and only the new units, at their own contribution per
unit, have to recover any support. A required quantity that has to be ordered is
rounded **up** to a whole pack, so an orderable quantity is never left below the
threshold it is supposed to clear.

**Synthetic example — 100 units at 100 EUR, cost 60 EUR, additional units at 80 EUR**

| What is being held | Before | After |
|---|---|---|
| Revenue | 125 units | **100 units** |
| Gross profit | 200 units | **100 units** |
| Gross profit with 200 EUR support | 210 units | **110 units** |

**Pack rounding.** All-volume, price 80:
a threshold of 125 kits with 4 kits per pack needs **128** kits to be ordered,
not 125. A threshold of 125 with 25 per pack needs **150**, because 125 only
equals the offer it is meant to beat.

---

## F06 — impossible inputs were accepted as valid

**What it did.** The starting quantity was checked. The proposed quantity was
not. A negative, `NaN` or infinite proposed quantity came back with `ok: true`. A
support amount that was not a number quietly became zero. And an additional-units
offer with a proposed quantity *below* what was already selling was quietly
clamped rather than refused.

**Why that is wrong.** Three of those produce a number a reader would act on, and
the number is nonsense. Transforming one is the same as inventing one. A support
figure that silently becomes zero understates the cost of the offer.

**What it does now.** The proposed quantity, the support and the cost are all
validated strictly at the boundary. Every reason for a refusal is returned
together, so nobody is sent round the form four times. Zero volume, an unknown
volume, a return and an invalid entry are kept as **four separate states** and
each is treated differently:

| State | Example | What happens |
|---|---|---|
| Zero | proposed quantity 0 | Refused. A full withdrawal is a decision to stop supplying, not a price. |
| Unknown | proposed quantity left blank | The starting quantity is used, and the result says the volume is unknown rather than zero. |
| Return | negative quantity, labelled as a return of goods | Accepted and reported as its own case, with a flag, and not presented as a price offer. |
| Invalid | negative, `NaN`, infinite, text, object, boolean | Refused with the reason. |

A missing cost still suppresses profit only. Revenue, and the revenue break-even,
are still calculated and reported.

| Check | Before | After |
|---|---|---|
| Negative proposed quantity | accepted, `ok: true` | refused |
| `NaN` proposed quantity | accepted, `ok: true` | refused |
| Infinite proposed quantity | accepted, `ok: true` | refused |
| Support of `"invalid"` | accepted, treated as 0 | refused |

---

## F09 — one alternative, two different answers

**What it did.** The ranking screen applied an alternative's stated volume
assumption. The side-by-side objective view ignored it unless something was
passed in by hand. So the same option, on the same base of 1,400 units with a
stated 25% volume response, was 1,750 units in one place and 1,400 in the other.

**Why that is wrong.** Two screens disagreeing about the same option is worse
than either being wrong. It is the defect a reader cannot see and therefore
cannot allow for. It also means the ranking's own order cannot be trusted,
because the rows were not all priced at the quantity they claimed.

**What it does now.** There is one volume normalisation and one calculation
function, and both views call them. The stated assumption always applies; a
hand-supplied override for a replay still wins.

| | Before | After |
|---|---|---|
| Ranking view | 1,750 units | 1,750 units |
| Objective view | **1,400 units** | **1,750 units** |

The check now runs across all 15 alternatives in all 5 cases, and every one
agrees. The old names (`v03run`, `v03rank`, `v03both`, ...) are kept as aliases
pointing at the corrected functions, so the existing screens keep working.

---

## F04 (the date part) — an unusable date silently picked October

**What it did.** When an offer effective date was missing, malformed or outside
every declared cost window, the cost helper fell back to the October cost basis
and said nothing.

**Why that is wrong.** October 2026 and September 2026 are different supplier
costs and the declared rule says they are never blended. A September offer
costed at October prices is a wrong number presented as a right one. And because
the fallback was silent, nobody could see that a date had been rejected.

**What it does now.** An unusable date resolves to nothing, with the reason. The
engine will not choose a basis for a date it cannot place. The October basis
also declares its own end date, so it is no longer treated as running forever.

Valid dates still separate cleanly, which is the check that must not regress:

| Offer effective date | Basis | Parts cost |
|---|---|---|
| 2026-09-22 | SEP26 | the September cost |
| 2026-10-01 | OCT26 | the October cost |
| `"not-a-date"` | before: OCT26, silently | **unresolved** |
| 2035-01-01 | before: OCT26, silently | **unresolved** |

The two bases do resolve to different purchase costs; the test asserts that the
two figures differ rather than printing them. For the same reason the other
business figures in this document are quoted as the arithmetic that was checked,
not as a table to copy from.

**One basis for one comparison.** The ranking now prices every comparable row on
a single named basis, and says which one and why. Where an alternative names a
different basis, that difference is *stated* in the row and in a flag — it is not
applied behind the reader's back. A supplier-cost change has to be raised as its
own assumption, not smuggled in through a different date.

Before, three of the five cases carried more than one profit baseline across their
own alternatives while presenting themselves as a single unchanged-offer
comparison. Each now carries exactly one — for the ITUK pad case, all four rows
share a single baseline figure — and the ranking reports whether it found one or
several rather than asserting that it found one.

**A recorded figure is not rebuilt.** The ITUK pad baseline records 120,278.50
EUR of billing on 1,400 kits. Rebuilding that from the rounded average price
gives a slightly different number — 4.50 EUR lower. The old engine called that
reconstruction recorded history. It is now labelled a **rounded scenario**, with
the recorded billing reported beside it and the difference stated.

---

## F07 — a migration that was a label, not a calculation

**What it did.** The oil-filter option named a move to the Genuine counterpart
(8982705240). The engine then priced the original BVP part at its unchanged price
and quantity, and returned the same zero change as doing nothing.

**Why that is wrong.** The option claims to measure a mix shift and actually
measures nothing. A reader would conclude the move is financially neutral. The
two lines do not have the same price or the same parts cost, so it is not
neutral — and the difference is exactly what the option was supposed to show.
Returning a fabricated zero is worse than returning nothing, because a zero looks
like an answer.

**What it does now.** Until the transferred quantity and the applicable price and
parts cost of **both** lines are supplied, the result is
`migration_status: 'unresolved'` with `revenue_change` and `gp_change` both
**null**. No zero. The unchanged-offer figures are still reported beside it, so
the row stays comparable with the others without pretending the migration has
been measured.

What is missing in this case, precisely: no transferred quantity is stated, and
the Genuine line has no applicable net selling price in the case's price record —
only a list price quoted in the option's own prose. I read both lines' parts costs
for the arithmetic and I am not copying them, or any price table, into this
document or into any file I created. I scanned every file I created for that, and
two supplier cost figures and two recorded-billing figures that had slipped into
an earlier draft were found and removed.

When the inputs *are* supplied, the engine now does the real two-product sum:

> A stated quantity moves from the BVP line to the Genuine line, at the stated
> price and parts cost of each line. The profit change is the contribution taken
> up less the contribution displaced, and it is flagged as **not new business**.
>
> The test runs this on synthetic figures throughout — one price, one cost and
> one transferred quantity per line made up for the test — and checks that the
> revenue change, the profit change and the bridge all reconcile. No real price
> or cost from the business payload is used or printed.

---

## Finance-04 — support counted once, and a bridge that reconciles

The printed profit is now guaranteed to equal:

> revenue after − parts cost of the units actually sold − support

with support taken off exactly once. The engine also prints the three movements
that make up the change in profit — the revenue movement, the cost movement and
the support — and checks that they add up to the profit change it reports. If
they ever do not, it raises a flag saying the result must not be used rather than
printing it as if it were sound.

For the additional-units example: revenue +1,600, cost +1,200, support 200,
profit +200. Those four numbers reconcile exactly, and the test asserts it for
six different scenarios.

---

## Finance-08 — ranking without manufacturing advice

The ranking orders alternatives by the objective the reader selected, and by
nothing else. Revenue and gross profit stay two separate objectives. There is no
composite score, no invented price optimum, no assumed elasticity, and no stated
minimum margin or acceptable profit sacrifice — the payload itself records both
of those controls as **NOT SET**, and an unset control blocks approval, not the
arithmetic. Changing the objective now changes the order and nothing else: same
baseline, same basis, same quantities.

---

## What still fails, and why

**R27 — candidate records declare their actual reporting period.** Still fails.
The 10,543 candidate rows carry no period, year or date field. This is not an
engine defect: the engine never reads candidate records. It belongs to the
candidate screen, which another agent owns under a different finding (F10, and
B05/B02). It cannot be fixed by inventing a period — the supplied review says
explicitly do not infer one from similar values. The correct behaviour is to
state that no period is carried, which is what the separate candidate screen
does in this build. I did not weaken the assertion to hide it.

**R25 and R26 — the distributor strip.** These pass here, but read them with
care. The production control is not this. The real member brief is built field by
field from a declared allowlist in `src/data/export.js`, which is a stronger rule
than deleting names from a finished record — a blacklist is what lost to a nested
`cost` field in the first place. I added a small strip-and-audit shim to the
engine so those two supplied assertions could be evaluated rather than deleted,
and I have labelled it as a shim in the code. It is not the control.

**The rest of the reviewer's findings are not in this engine** and were not
touched: F01 (the saved case not matching the ranking), F05 (the turbo tab's
render error), F08 (recipient-specific exports), F10 (the candidate workbench),
F11 (stale version wording) and F12 (shared case records). Several of them are
already addressed in the other modules under `src\`, but that is not my evidence
to quote and I have not verified them.

---

## Two honesty notes

**The corrected engine holds no business data.** It never reads a payload by
itself. A caller hands it the payload once. That is why the arithmetic can be
tested on synthetic figures with no restricted data anywhere near it. My own test
file runs on synthetic figures by default; the restricted payload is loaded only
when it is asked for by name, and it is read for arithmetic only — no cost table
and no price list is reproduced in this document or in any file I created.

**Where I had to make a judgement, I made it visible.** Two cases were genuinely
ambiguous and I chose the reading that keeps one comparison on one cost rather
than one that would have made a test pass:

1. **The October basis has no end date of its own.** Its own rate-window text
   says it runs to 31 March 2027, so I read the end from there. That is the basis
   stating its own window, not the engine inventing one. Without it, October
   would have run forever and any date in 2035 would have been accepted.
2. **One alternative names September while the comparison uses October.** I could
   have applied the named basis per row and made the "one baseline" check pass
   that way. That would have hidden the inconsistency instead of reporting it. I
   priced every row on one basis and added a flag and a sentence saying that a
   different basis was named and not applied.

Both choices are asserted in `tests\fin_math.test.mjs`, so they are testable
rather than merely asserted here.

# Guarantee term sheet — €300,000 conditional commitment

21 September 2026 · internal · for the business owner to take into a meeting

---

## 1. Purpose and the decision being asked for

This is a cap and a release schedule, not an investment case. It sets the maximum ISZE would spend behind
Universe, names what is purchased with it, and states the evidence required before any part of it is released.

The decision being asked for is whether to approve €300,000 as a ceiling against staged, evidenced delivery
by a named pilot market. Approval does not release money. Each stage is released only when its named artefacts
exist, a named individual has signed for them, and someone who did not build them has re-derived them from
source.

---

## 2. The honest position on €300K

No euro return is evidenced anywhere on disk, so this term sheet cannot be justified as a return calculation.
It buys deliverable things — files, responses, mappings, a working monthly review in one market — rather than
promised profit. Any sentence that presents €300,000 as earning a multiple is unsupported.

The proposal paper says this in its own words. On page 47, under the symbolic incremental-contribution
example: *"This is deliberately not a programme ROI estimate. No approved Universe budget, realised
distributor margin improvement or causal uplift is established by the supplied material."* On page 29: *"The
paper recommends the measurement design, not unearned numerical targets."* Page 54 repeats it: the paper
*"does not repeat superseded network ceilings or use a modelled opportunity to invent a programme return."*

Two comparables exist on disk. Neither supports €300,000, and neither should be used as if it did.

The first is a support commitment, not a product commitment. One FY26 support mail states a €30k incentive to
ITUK (source: `UNIVERSE_STRATEGY_REVIEW_CRITIQUE_2026-09-21.md` §3d, line 140). It is one distributor, one
year, paid as a rebate against a defence programme, and it is not independently verified by the package that
records it. It shows that ISZE does commit support money to a distributor; it does not show what a new product
is worth.

The second is a list-price decision, and it is not a Universe return. The FY2027 price-revision memo puts the
locked +3% at **+€383k per year on the last 12 months of billed value and +€436k per year on forecast weights**;
+4% at **+€581k / +€510k**, which is **€145k per year more** than the locked +3%; +5% at **+€726k / +€638k**,
**€290k per year more** (source: `DECISION_MEMO_PRICE_ADJUSTMENT_20260916.md`, options table and the
locked-baseline line, 16 September 2026). Those figures cover the same 6,326 part numbers on both bases, and
the forecast base is 1.1376× the past-sales base (€14.52M against €12.76M). They are a price move on the
parts catalogue, decided separately, and they carry a decision that is still open (see §7).

So: €300,000 cannot be justified on a return basis from anything on this disk. What it can be justified as is
the ceiling on a bounded pilot whose outputs are specified in §3 and whose release conditions are in §7. If the
business requires a return number before approving, that number does not exist yet and must not be invented
here.

The scale is defensible only against a stated ceiling, not against a return. For context, and not as a
forecast: the 2025 modelled target-spend ceiling is €55.3M across 18 markets against €30.8M billed, and eight
markets sit on a flat €250 per truck, holding about 40% of that ceiling, €22.3M of €55.3M (source:
`15_STRATEGY_ROADMAP_AND_CRITIQUE.md` §1, quoting the reviewed strategy paper). That is a modelled ceiling,
not available revenue, and the same file says: *"Do not slice a pilot return from 55M."*

---

## 3. What can be guaranteed

Each row below is written so a contract can observe it. "Named" means a person's role and an individual's
name on the release note — a team name is not an owner. Response-time classes are the five the paper defines
on page 27; the paper explicitly does not invent the targets, so the targets are agreed against a measured
baseline (§7, item 2).

| Guarantee | Who delivers | How it is verified | Consequence of failure |
|---|---|---|---|
| The named artefacts in the milestone list exist by their named dates, as files at stated paths | The implementation owner, per milestone | One hashing pass per milestone by a verifier who did not build it, checked against the pinned manifest | That milestone is not reached; its release does not occur |
| A named accountable individual per service and per case — not a team name, and one person who cannot hand ownership to another function | The ISZE business owner names them; the named individuals accept | The case record shows an owner on every open case; the release note names them | No release until the owner is named; an unowned case does not count as delivered |
| A substantive response within the agreed time, in the agreed class: routine information, application check, commercial decision, supply investigation, service analysis | The named specialist for the class | Time to substantive response on the case record; an acknowledgement or an administrative close does not count | The response milestone fails, and any release conditional on it is withheld |
| The monthly sales-to-dealer file with its four minimum fields — dealer identifier, part number, period, quantity — and a coverage declaration, by an agreed date each month | The distributor parts function | The file arrives, carries the four fields, and its coverage declaration is present; a month is complete only with coverage evidence | That month does not count toward the recurring-delivery milestone |
| A named pilot market participating with a named distributor owner | The business owner and the distributor | The distributor owner is named on the pilot agreement, and the pilot market is written into the milestone list | No pilot release; the cap stays uncommitted |
| Data accuracy and coverage thresholds: stable dealer and part identifiers, reversible corrections, no silent overwrite | The implementation owner | Re-run the import twice on the same file; corrections show as corrections, not as new events; identifiers do not silently change | A failed re-import test stops the affected release until it passes |
| Completion of the defined milestones, each evidenced rather than reported | The implementation owner | The milestone's own evidence, re-derived by the verifier | Unreached milestones do not release |

Two things about the monthly file are part of the guarantee, not commentary. First, the file already exists
for one year: ITUK calendar 2025 holds 64 dealers across 12 months. Second, a historical file proves it was
sent once and not that it will recur — the confirmations needed are format, cadence and an owning role, and
the distributor produces the file today without a new system (source: `16_OPEN_QUESTIONS_BY_RECIPIENT.md` §3,
question 5).

---

## 4. What cannot be guaranteed

Each line below is a thing the business might reasonably want and cannot have as a guarantee. The page
references are to the proposal paper's own statement, so the limit is the paper's, not this sheet's.

- **Incremental profit.** The paper's symbolic incremental-contribution example on page 47 says no causal
  uplift is established by the supplied material, and that the formula defines what later evidence must
  support rather than filling the gap with illustrative earnings. Gross profit also requires cost of goods
  sold, displacement and timing that are not in the file.
- **That a won quotation would otherwise have been lost.** Page 15: linking an approved case to an order *"is
  stronger evidence than recollection, but it still does not establish the counterfactual that the business
  would otherwise have been lost."*
- **Dealer resale behaviour.** Page 15: the initial record *"need not include the end customer's personal
  details or the dealer's resale margin"*, and page 24: *"resale margins are not mandatory"*. Nothing on disk
  measures what a dealer sold to a truck owner.
- **Freedom from displacement between dealers.** Page 26: *"Additional purchases by one dealer may be
  business transferred from another part of the network. Moving the same business to a different month is not
  new annual business."* Page 26 also lists displacement between Genuine and Best Value as an explanation to
  consider, so a value-tier gain is not automatically incremental either.
- **Market growth.** Page 27: *"A modelled market-spend ceiling can describe strategic context. It should not
  be multiplied by an arbitrary recovery percentage to invent Universe's revenue case."* Universe can describe
  the market it observes; it cannot promise the market grows.
- **Causation from a documented decision plus a measured result.** Page 26: a credible evaluation can begin
  from a documented decision and a measured subsequent result *"without claiming full causal attribution"*,
  and *"Do not reconstruct an attractive counterfactual after seeing the data."* The honest guarantee here is
  the decision record, not the cause.
- **A return euro for the €300,000.** Page 47, as quoted in §2. A guarantee of a return would be a guarantee
  the paper explicitly declines to make.

---

## 5. The recommended instrument

Stage the money against milestone gates, hold back the final stage until the pilot's own evidence is in, and
claw back any release whose evidence is not produced inside the cycle. Concretely: an amount per named
milestone, released on the verifier's pass, with the last stage held until the recurring exchange has repeated
at least once and its corrections are handled. Any release that later fails to evidence itself inside its cycle
is recovered or offset against the next milestone.

The alternatives are weaker for specific reasons, not by preference. Milestone gates without a holdback pay
the whole commitment on artefacts that can all be produced before anyone discovers whether the monthly
exchange repeats — the paper's own test (page 28: repeated use for eligible work; page 29: the participant
would continue if the reporting incentive disappeared) is exactly the thing that only shows up afterwards.
Payment on evidence without gates pays after the fact and gives the delivery team no staged commitment to plan
against, so the schedule and the money stop being connected. A KPI-linked release needs a baseline and a
target; the baseline has not been measured and the paper refuses to set unearned targets (page 29), so a KPI
release would be negotiated against numbers neither side can defend. Clawback with no staging has the
weakness of both the first two: it pays everything up front and then tries to recover on the strength of an
argument rather than a gate.

---

## 6. How delivery is verified

The mechanism already exists and has been exercised on the ITUK worked case: 104 checks, 0 failures
(`ITUK_CASE_2026-09-21_01\evidence\C04_verify_return.json`, 21 September 2026). Reuse it rather than inventing
a second one.

One hashing pass per milestone, run by someone who did not build that milestone, against a pinned manifest:
before-and-after SHA-256 snapshots of the named sources and the milestone's own outputs, with the instruction
given to the independent verifier on the ITUK work — re-derive from source; do not read another audit's output
and agree with it. The prior exercise is documented in `18_INDEPENDENCE_AND_VERIFICATION_LOG.md`: every
workstream hashed its own read-only position, 58 files were byte-identical across the window, and zero primary
sources changed. That log is also explicit about its own limit, and it is the limit this term sheet must carry:

> **It proves the bytes did not change, not that the data is correct.**

The log says so in §7 in those words: the read-only proofs *"do not claim the DATA in those files is correct —
only that the bytes did not change."* So the hash pass is necessary and not sufficient. For the data itself,
each milestone needs a second, separate check that re-derives the figures from the source and tests them
against the claims made about them — the instrument the log itself names as the strongest available is an
assertion script that asserts every headline number against the JSON that produced it and lets a reader re-run
it (56 checks, 0 failures, on the expected-demand work). That is the model for the data check; the hash pass
answers "did anything move", the assertion pass answers "is the number right".

---

## 7. What must be true before any money moves

1. **A stated beneficiary and benefit type per release.** Not a programme total. The paper's benefit record
   (page 26) requires a beneficiary — ISZE, distributor, dealer or another identified party — and a benefit
   type, because a benefit to ISZE is not automatically a benefit to the distributor.
2. **A measured baseline of the existing process before any target is set.** Page 29 requires observing how
   information is assembled, how many functions are involved, what is typed repeatedly and how long the
   participant waits, and then comparing the proposed experience on an equivalent task. Response-time and
   adoption targets come after that measurement, not before.
3. **A pinned classification release, with filename and build date.** Three candidate files exist and no
   authority is declared: `aim_pn_classification_v2.csv` (read by the dashboards),
   `aim_pn_classification_20260920.csv` (the corrected rebuild, whose own baseline calls it a candidate not
   yet live) and `aim_master_v2.csv` (whose catalogue columns are stale on the drifted numbers). The drift is
   recorded as 2,728 part numbers, including 132 air-cleaner elements worth 1,160,612 filed in the wrong
   family. Until a decision names file, version and coverage, no family label may be printed outside ISZE
   (source: `16_OPEN_QUESTIONS_BY_RECIPIENT.md` §3, question 2).
4. **A named distributor owner and an agreed recurring refresh route.** A single 2025 file does not establish
   a monthly operation: 2023, 2024 and 2026 exist only as network totals and cannot be allocated backwards or
   forwards (source: `17_WHAT_IS_IMPLEMENTABLE_NEXT.md` §4). What is needed is confirmation of format,
   cadence and owning role for the file the distributor already produces.
5. **The dealer-name-to-account-number list.** The billing system identifies a customer as a sold-to account
   and the sales-to-dealer file identifies a dealer as a name; no mapping exists. All 65,619 rows of the
   replenishment bridge read "not computable at dealer grain" (verified at 65,619 rows, all ITUK, one grain,
   twelve months covered — source: `18_INDEPENDENCE_AND_VERIFICATION_LOG.md` §2.4, R1), and 0 of 3 ITUK
   purchasing accounts are mapped to a dealer site (source:
   `06_Working\_work\ITUK_IDS_AIM_EXPORT\_pack20\19_COVERAGE.csv`, identity layer, "not possible — ISZE
   invoices the distributor, not dealers"). One spreadsheet column pair closes the buildable part of this.
6. **An agreed audience and access design.** There is no host: no authentication exists in the analysis app,
   no static-site deployment is configured, and the publishing folder's contents are not safe to publish as
   they stand. External sharing is a data-separation problem before it is a login problem (source:
   `17_WHAT_IS_IMPLEMENTABLE_NEXT.md` §5, items 9 and 10).
7. **A written position on whether the FY2027 target is measured before or after the distributor support
   payment.** This single choice moves the whole euro. On the headline basis the +4% option is +€581k per year
   on forecast weights and +€510k on the last 12 months; on the net basis, where €1.00 of headline increase
   lands as €0.80, the same headline nets +3.2% — €465k and €408k; and to net +4% the headline must be +5.0%
   (source: `DECISION_MEMO_PRICE_ADJUSTMENT_20260916.md`, "Open sub-questions", item 1). The supporting
   payment's own terms — percentage, base, and whether it scales with purchases — are not in the files and
   must come from IML.

Two further points belong beside these, because they change what a release can claim rather than whether it
can occur. The workshop money is of undeclared currency: the workbook carries no currency column, symbol or
code, and VAT at UK standard rate on 337,275 of 345,069 testable lines makes sterling the working assumption,
not a finding (source: `16_OPEN_QUESTIONS_BY_RECIPIENT.md` §3, question 7). Until that is answered, any money
figure beside a workshop prints with its basis named and the absence of a source declaration stated, or it
does not print. And the four-layer comparison — ISZE billed to the distributor, the distributor's purchases,
workshop lines, and dealer-to-end-customer — is deliberately not reconciled: the first layer has no dealer
column and the fourth has no source at all (source: `17_WHAT_IS_IMPLEMENTABLE_NEXT.md` §6 and
`02_DISPUTED_CLAIMS_AND_RESOLUTIONS.md` §8, M-39). No release may present it as reconciled.

---

## 8. The weakest link

The guarantee breaks on the response, not the data. The product's value is redeemed only when ISZE answers a
distributor's or dealer's question, and nothing on disk shows that function exists, is owned, or is funded.

There is no support-case register at case level. Searches returned 75 filename hits on `*case*` and none of
them a case register, and `DLOD` returns 0 hits across every column of all 538,346 billing rows (source:
`04_SOURCE_MANIFEST_AND_HORIZONS.md` §3, and `17_WHAT_IS_IMPLEMENTABLE_NEXT.md` §5, item 8). The paper
itself makes the point on page 27: *"Software cannot substitute for an operating commitment... Otherwise,
better data collection simply makes unanswered requests easier to count."* Page 27 also states the reciprocal
obligation — the receiving organisation must have the capacity and authority to answer — and page 25 states
the commercial consequence: *"A low marginal cost for software does not mean the response service is free."*
The capacity is unbudgeted today.

The organisation has already demonstrated the specific failure. A mileage question to the ITUK Parts Director
was drafted on 18 September 2026 and never sent; the file exists at
`09_meetings\ITUK_MILEAGE_QUESTION_2026-09-18.md` (3,624 bytes, last written 18 September 2026 17:17), and
`16_OPEN_QUESTIONS_BY_RECIPIENT.md` §2 records it as "already drafted, unsent", with the instruction not to
re-draft it but to fold it into the pilot conversation. Three days later it is still unsent. That is not a
data gap; it is a response gap, and it is the one the money depends on.

Whatever else this term sheet guarantees, it cannot guarantee the answer. It can only name the owner, the
class and the time, and withhold the release if the answer does not come.

---

## 9. The decision question

**Do we approve €300,000 as a ceiling against staged, evidenced delivery by a named pilot market, with the
money released only on a verifier's pass at each milestone — yes or no?**

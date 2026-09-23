# ISUZU UNIVERSE YELLOW PAPER v0.2 — RED-TEAM REVIEW

**Reviewed:** `Isuzu Universe\Universe_Yellow_Paper_v0.2_2026-09-21.pdf` — 34 pages, 10,119 words, built 21 September 2026 19:49:35, file written 22 September 05:13.
**Reviewer:** Cursor agent, 22 September 2026.
**Standing:** internal / private. This is a review, not a product, not a release and not a decision.

## What I actually did before writing this

I read every page of the PDF myself, twice. I read the v0.1 paper, the handover note, the 15,000-word complete draft on disk, the master prompt that produced it, and the four surrounding commercial documents. I then checked the paper's own factual claims against the files it says it used:

- The three source hashes in its source register. **Both are correct.** v0.1 hashes to `6f58b43f…`, the handover to `9bdac9f4…`.
- Whether the paper's central evidence claim holds. **It does not.** See issue 3 below.
- The ITUK sales-to-dealer file, row by row: 101,341 rows, 66,018 monthly rows carrying 223,897 units, 35,323 annual control rows carrying 224,001 units, 64 named dealers, twelve months. **Matches** what the draft's Appendix B claimed.
- The Portugal file: 21,636 rows, 51,363 monthly units, and the dealer-name column **empty on every single row**. The paper never says this.
- One worked commercial case, rebuilt from the raw file (Warrington Vehicle Centre — numbers below). **The numbers reproduce.**
- A price comparison file: 105 rows, of which **16** match an ITUK part number. I read those 16 and they contain the price evidence the paper says does not exist.
- The rendered PDF itself: no blank pages, no text clipped outside the frame, no overlapping text blocks, 34 out of 34 bookmarks present and pointing at the right pages, seven page images checked visually. The layout is clean. I am not going to criticise the typesetting, because it is the best-made thing in this folder.

---

## A. TEN-LINE EXECUTIVE ASSESSMENT

1. This is not a product specification. It is an evidence-governance rulebook wearing a product's cover, and it should not be approved as the basis for building anything.
2. Its central claim — that the underlying data was not supplied — is false on the machine it was written on: the 15,000-word draft, the master prompt, six commercial and data documents, and the extracted dealer-level files were all in the same folder, hours before it was built.
3. It contains no decision rule. No threshold, no trigger, no ranking, no queue, no alert. "Prioritise when the signal is material" — and "material" is never defined anywhere in 34 pages.
4. It contains no worked commercial example. I searched the extracted text for every business figure in the draft it claims to revise. **Every one of them is gone.** The whole document contains no euro amount, no percentage, no unit count, no dealer count and no period.
5. Meanwhile a complete worked case exists on the same disk and reproduces exactly: Warrington Vehicle Centre, 13,801 units, first half 7,813 units, second half 5,988; five wheel and hub numbers falling from 452 to 40 while the rest of their family falls 386 to 78 but keeps running.
6. It has no users. The words "pricing team", "parts sales", "product management", "account manager" and "aftersales management" appear zero times. The word "user" appears once. Its five roles are people who sign things off, not people who open the thing on Monday morning.
7. It has no screens. The word "screen" appears twice, in passing. No button, no panel, no layout, no filter, no workflow state, no simulation. There is nothing to demonstrate.
8. Both real pilot markets are structurally limited in ways the paper handles honestly but never quantifies: Portugal has a complete national file with **no dealer name in it at all**, and ITUK has dealer names for **one year only**, no fleet denominator and no validated link between a dealer and a buying account.
9. Its best halves are genuinely good and must be protected: the three flows that may never be added, "a missing file is not a zero month", counted versus modelled, and supersession not being the same as equivalence.
10. The honest verdict: as a rulebook for how not to lie with parts data it is excellent. As a product description, a pilot plan, a funding case or a management approval paper, it does not exist yet — and three of those four already exist elsewhere in the same folder, better.

---

## B. OVERALL ASSESSMENT

**What the paper is trying to become.** Reading it closely, it wants to be the constitution for a monthly distributor review: a document that fixes what a number is allowed to mean before anybody builds a screen that shows one. On its own terms that is a serious and worthwhile ambition, and parts of it are better than anything else in this workspace.

**What is strongest.** The evidence discipline. The separation of the three transaction flows and the ban on adding them. The treatment of a missing file as unknown rather than zero. The distinction between what was counted and what was modelled, including the correction of its own earlier draft's wrong claim that every figure here is a floor. The refusal to let a family classification pass as a fitment approval. The refusal to treat a dealer self-assessment as a distributor audit. The idea of recording both what a blocker stops and what useful work may continue anyway. Those are real assets and they are worth protecting through every future revision.

**Where it remains conceptual.** Everywhere the product is supposed to live. There is no detection logic, no materiality threshold, no prioritisation, no queue, no screen, no simulation, no named user, no named owner, no cost, no timeline and no worked case. The paper describes the rules an answer must obey and never describes the machine that produces one or the person who reads it.

**The structural diagnosis.** This document is two things fused badly, and the fusion is why the whole review feels slippery.

It is, first, a very carefully written proof that nothing has been claimed that cannot be proved. Its own front matter says its existence is not evidence anything was built, its status page lists what was and was not inspected, and roughly 120 of its sentences are caveats. It was built to survive a hostile reader by refusing to assert anything.

It is, second, meant to be the product and operating specification for a commercial decision engine.

Those two intentions are in direct conflict. Every time the paper had a choice between saying something concrete and saying something safe, it said something safe. So the price comparison evidence exists and the paper says it was not inspected. The worked case exists and the paper says it cannot be given. The funding paper exists and the paper says no budget is substantiated. The result is a document that cannot be attacked — and equally cannot be built from.

**What must change before this becomes an implementation blueprint.** Three things, in order.

First, the paper has to admit what it has. Its evidence boundary is stated as fact and it is wrong. That single correction unlocks everything else: with the draft, the datasets and the worked case in scope, the paper can carry a real example, real price evidence and real blockers instead of general principles about them.

Second, it has to name the decision rule. Even a crude, arguable threshold — a family moves more than X units or Y euro against its own twelve-month run rate while its fleet base and coverage are stable — is worth more than the current sentence about materiality, because a wrong threshold can be argued with and no threshold cannot.

Third, it has to put the first screen on the page. One opportunity page, filled in with the Warrington case, would convert this document from a description of a decision environment into a demonstration of one.

---

## C. WHAT HAS BECOME STRONG

These should be carried forward unchanged into any future edition.

**The three flows and the ban on adding them (page 12).** ISZE billing, sales to dealer, and the dealer's own retail sales are three different records of the same physical part, and the paper forbids merging them. It also states the right consequence: if the middle flow is missing, activity beyond it is unknown, not zero. This is the single most valuable paragraph in the document and I verified the underlying position — seven of the twelve derived distributor files have no dealer names at all.

**A missing file is not a zero month, and a zero must be asserted (page 11).** The paper pushes this further than most people would: a dealer missing from a file may be outside scope, unmapped, inactive or genuinely at zero, and the file alone does not choose between those. That is exactly right and it is the kind of rule that stops a chart lying.

**Counted is not modelled, and a count is a floor while a rate is not (page 13).** This is the correction of a real error in the earlier draft, and the paper says so. The distinction it draws — observed counts and observed money are floors, but rates, per-vehicle figures and expectations are not — is subtle and correct.

**Supersession, catalogue pairing and fitment are three different things (page 17).** "A family match alone does not establish interchangeability." "No pair exists is not no product exists." "Wherever a substitution is proposed, application must be validated separately." And the operational rule that follows: no validated match means no substitute recommendation, but it can still be a precisely defined technical question.

**Pricing precision as a routing decision rather than a discount generator (page 18).** The four routes — a normal price review, a bounded special-price case, a Genuine/alternative product discussion, and a supply or ordering investigation — with the rule that missing supply evidence does not prove that a price cut is the remedy. Most commercial papers in this territory end up as a recommendation to discount. This one refuses.

**Gross-profit discipline including substitution (page 19).** Baseline gross profit, scenario gross profit, the break-even quantity formula, and the rule that Genuine volume replaced by the alternative part is not counted a second time as new business. Correct, and rarely written down.

**Two pilots with deliberately different proofs (page 21).** The paper refuses the temptation to pretend both markets can show the same thing. "Passing the national Portugal pilot does not validate ITUK's identity links."

**Recording what a blocker stops and what may continue (page 27).** "A missing dealer-site map blocks that join, not all account-level analysis." A genuinely useful management device that prevents one missing field from freezing an entire programme.

**The distributor participation framing (pages 6 and 9).** Separating the recorded starting point from the contractual evidence from the proposal is the right structure, and the promise that the minimum quantity feed will not silently become a request for selling prices, margins, stock, customers or vehicle identities is exactly the promise a distributor needs to hear.

---

## D. TOP CRITICAL ISSUES

Ten. Each with what the paper says, why it matters, and what to do.

### 1. The paper describes a decision product and defines no decision

**Why it matters.** This is the reason the question "what does this mean on Monday morning" cannot be answered. A decision environment whose surfacing logic is undefined is not a decision environment.

**Evidence from the paper.** Page 15, "Select by materiality, evidence and ability to act" — "Prioritise questions that matter to the selected scope and have an accountable response route." Page 5 lists the loop as Observe, Fix the scope, Explain, Test the change, Act, Assign the response, Review, Revisit the result. Nowhere does the paper state what causes something to appear, how one opportunity is ranked above another, or what volume or value makes a movement worth looking at.

**Required correction.** Add a section that defines surface rules explicitly. Minimum: a named measure to watch, a comparison basis (the same family's own prior twelve months, or the same period last year), a minimum size expressed in both units and euro, a stability condition on the fleet base, a coverage condition that suppresses the signal when the feed is incomplete, and a stated maximum number of items the queue will show. It does not have to be right. It has to exist so that it can be argued with.

### 2. There is not one worked commercial example in 34 pages

**Why it matters.** The brief that produced the draft asked for five. A commercial paper about a decision system that cannot show a single decision is not reviewable by a management reader, because they have no way to judge whether the output is useful.

**Evidence from the paper.** I extracted the full text and searched for every business figure that appeared in the draft's Appendix B — €117.6m, €55.3m, €248.54, 22,389, €2.11m, 50.85%, 223,897, 2,402, 1,930, 72 trucks, 27,543, 1,627, 719, 836, 47,923, 40,000, 20,000, 249 to 425, 538,346, 66,018. **Not one of them appears anywhere in the document.** A regular-expression sweep for anything shaped like money, a percentage or a quantity returned only "2026", "0.2" and "15,000" (the word count of the draft). Page 22's "worked scope decision: Portugal" is a worked *scope* decision — whether national data may be attributed to named dealers — and it ends by saying the quantitative case "is required at the pilot gate, not fabricated in this edition."

**Required correction.** Put one real example on the page, marked as what it is. One is enough. Use the Warrington case (page 25 of this review) because it is already verified and it demonstrates the discipline the paper preaches: a real decline, tested against real alternatives, with an honest inconclusive result.

### 3. The evidence-boundary claim is factually wrong, and it is the claim the whole document leans on

**Why it matters.** The paper's entire protective strategy is "I only had two files, so I assert nothing." That framing is not accurate, and a management reader who opens the folder will discover it. The paper risks losing the one asset it is most carefully protecting.

**Evidence from the paper.** Page 3: "The v0.1 PDF and handover were inspected. The approximately 15,000-word complete draft, its master prompt, underlying datasets and running application were not supplied." Page 33: "Not supplied: Universe_Yellow_Paper_COMPLETE_DRAFT_2026-09-21.md and UNIVERSE_YELLOW_PAPER_MASTER_PROMPT_2026-09-21.md… the raw commercial, identity, workshop, fleet and pricing packs behind its numerical claims; the two outstanding commercial documents."

**What is actually on disk, all written before the paper was built at 19:49 on 21 September:**

| File | Size | Written |
|---|---|---|
| `01_Strategy\Universe_Yellow_Paper_COMPLETE_DRAFT_2026-09-21.md` | 96,846 bytes, 15,260 words | 21 Sep 21:22 |
| `01_Strategy\UNIVERSE_YELLOW_PAPER_MASTER_PROMPT_2026-09-21.md` | 74,882 bytes | 21 Sep 21:18 |
| `01_Strategy\UNIVERSE_300K_GUARANTEE_TERM_SHEET_2026-09-21.md` | 19,430 bytes | 21 Sep 20:28 |
| `01_Strategy\UNIVERSE_VALUE_EXCHANGE_MODEL_2026-09-21.md` | 24,989 bytes | 21 Sep 13:51 |
| `01_Strategy\Universe_Commercial_Participation_Model.md` | 21,003 bytes | 21 Sep 13:51 |
| `01_data\90_INBOX\UNIVERSE_DATA_EXCHANGE_AUDIT_2026-09-21.md` | 28,217 bytes | 21 Sep 13:33 |
| `01_data\00_derived\dealer_sellout_long_ITUK_CY2025.csv` | 12.6 MB | on disk |
| `01_data\00_derived\dealer_sellout_long_PORTUGAL_CY2025.csv` | 3.1 MB | on disk |
| `01_data\01_Pricing\_raw\ks_aftermarket_price_compare_20260819.csv` | 105 rows, 16 matched | on disk |

The two documents named in the paper as revised commercial model and feedback disposition genuinely do not exist under those filenames. That part is accurate. But the paper presents this as "the commercial chapter is provisional because the material is missing", when six usable documents covering exactly that ground were in the folder. It also never mentions them, so a reader cannot find them.

**One fair qualification, because I checked the timestamps rather than assuming.** The complete draft and the handover were both written at 21:22, which is after the internal build time recorded in the PDF (19:49:35) and before the file was written to disk (22 September 05:13). So a writer working only from the two files named in the handover may genuinely not have had the draft in front of it when the words were composed. That defence covers the draft and the handover. It does not cover the four documents written between 13:33 and 20:28 — the data exchange audit, the two commercial models and the funding term sheet — which were all on disk before the build time, and none of which appears in the paper.

**Required correction.** Replace the evidence-boundary paragraph with a truthful one: state which files were read for this edition, name the ones that exist and were not read, and state the specific gap as it is — no updated participation model and no record of which review comments were accepted. Then add the six existing documents to the source register.

### 4. The money question is deleted, and the paper is meant for approval

**Why it matters.** Page 30 says the sponsor must approve a resource envelope before recurring operation. The paper gives that sponsor nothing to approve. It has no figure at all — not a ceiling, not an order of magnitude, not even a count of roles.

**Evidence from the paper.** Page 30: "Before recurring operation, identify preparation, validation, response and maintenance effort; the sponsor then approves the resource envelope. No budget, staffing estimate, financial return or service-time target is substantiated by the supplied materials." The words "€300,000", "budget", "full-time" and "FTE" appear nowhere in the document.

**What exists on disk.** A term sheet written the same evening (20:28, roughly eighty minutes before the paper's own build time) that does exactly this: a €300,000 ceiling with staged release, a warning that no euro return is evidenced, and two comparables it refuses to use as a return calculation — a €30,000 distributor support payment, and the coming price revision at roughly €383k to €726k depending on the increase.

**Required correction.** Either state the ceiling and the reasoning honestly, as the term sheet already does, or state that a funding decision is deliberately out of scope for this document and say which document carries it. Silently omitting it is the one option that makes the paper unusable for its stated purpose.

### 5. There are no users, so the user-problem test cannot be attempted

**Why it matters.** The product question is not "is this interesting" but "which person's week gets better, and how". The paper cannot answer it.

**Evidence from the paper.** I searched for pricing team, parts sales, product management, account manager, aftersales management, business network development, parts manager, sales director — **zero occurrences of every one**. The word "user" appears once, on page 33. The paper defines five roles (page 26): product owner, source and metric owners, commercial approver, IDS and technical authorities, technical owner. Those are governance roles — who signs off — and the paper says so itself: "These are proposed accountable roles. Named appointments and available capacity are not established by this paper."

**Required correction.** Add a short section naming four real users with the one task each does differently because Universe exists: the ISZE parts analyst preparing the monthly distributor review; the ISZE pricing owner evaluating a support request; the distributor's parts manager in the review conversation; the ISZE commercial owner closing a follow-up. For each, name the thing they stop doing — rebuilding a pivot, chasing a file, guessing at coverage — because that is the only form of the benefit that is not "better visibility".

### 6. There are no screens

**Why it matters.** The paper claims the workspace is one of its two main subjects, and there is no workspace in it.

**Evidence from the paper.** Page 23 names four destinations (Portfolio, Network, Commercial review, Actions) and says "Distributor view and dealer/account view remain distinct", with a list of required behaviours on context change. Page 23's illustration is a data-flow diagram, not an interface — it shows Context that travels, then four boxes. The words button, click, wireframe, mock and layout do not appear in the document. "Screen" appears twice in passing. The four finding statuses on page 16 (ready for review, needs validation, context only, withheld) are the only workflow states defined anywhere.

Note also that the paper never resolves whether the Actions destination and the dealer self-assessment action register it criticises on page 20 ("it has rows, it has no owners and no due dates, and every row reads open") are the same object. A reader cannot tell.

**Required correction.** Add one screen, described properly — what is at the top, what carries the headline, what the evidence panel contains, what the simulation shows, what the reader can do next, and what it looks like when the evidence is missing. The draft's own page count and the on-disk prototype both prove the team can describe a screen when it wants to.

### 7. AIM is a pillar in name only

**Why it matters.** The brief's whole commercial case rests on AIM: the parts intelligence that explains a movement and recommends a response. The paper treats it as a label on a page of relationship rules.

**Evidence from the paper.** AIM appears on pages 2, 5, 13, 15, 17, 23 and 32, but there is no AIM section. The closest thing is page 17, which correctly defines supersession, catalogue pairing, kit relationships and unverified candidates — good definitions, no method. Page 15 lists the five decision patterns and adds "These are decision patterns, not findings about a named market or dealer." So the paper says, correctly, that these are shapes rather than examples, and never supplies the example.

**Specifically missing.** No rule separates a genuine commercial decline from the seventeen alternative explanations a careful analyst would test — fleet decline, model ageing, a part superseded, distributor stock timing, one large historical order, missing dealer data, alternative-part migration, a special-price agreement expiring, a supply shortage, a lost tender, a range gap, a changed service interval, seasonality, one customer's behaviour, competitor pressure, and price. The paper names perhaps five and specifies a test for none. Page 15's "Test available supply, supersession, promotion and competitor evidence" is a to-do list, not a rule.

**Required correction.** Write the seven or eight tests that eliminate alternatives mechanically before any price conclusion is allowed — for example: if the fleet base for the applicable band fell by at least as much as the purchasing, the signal is closed as explained, no action; if any contributing part number has a validated supersession pair whose replacement rose in the same period, that volume is re-attributed before the decline is measured; if the decline sits in one or two months and one account, it is a stock or ordering event and not a demand signal. Each test should be checkable against the data the paper already defines.

### 8. The price position evidence exists, is good, and is in another file the paper did not read

**Why it matters.** This is the paper's flagship commercial outcome — "pricing precision" — and it treats competitor evidence as a promise rather than a dataset. The comparison data is on disk, mapped to real part numbers, and it says something more interesting than "we are expensive".

**What I verified myself in `ks_aftermarket_price_compare_20260819.csv`** (105 rows; 16 carry a match to an ITUK part number):

| Part number | Description | Competitor genuine | Competitor non-genuine | Our dealer price | Our index vs competitor genuine |
|---|---|---|---|---|---|
| `8970622940` | Air filter element | £55.00 | £30.00 | €49.98 | **0.777** |
| `8971482700` | Oil filter element | £13.50 | £7.50 | €19.81 | **1.255** |
| `8980370110` | Fuel filter element | £13.00 | £10.00 | €16.21 | **1.066** |
| `8976739570` | Air filter | £50.00 | £35.00 | €48.98 | **0.837** |
| `8975439050` | Oil filter | £15.00 | £12.00 | €10.73 | **0.611** |
| `8983752250` | Fuel filter | £20.00 | — | €16.97 | **0.725** |
| `1313100120` | Clutch release bearing | £90.00 | — | €122.50 | **1.163** |

Read that table carefully, because it is the finding of the year and the paper cannot see it. Against the competitor's **genuine** listing we are competitive on the air filters and cheap on two oil filters and a fuel filter — one of which is 39% below. Against the competitor's **non-genuine** listing we are 42% above on the same air filter. So the commercial question is not "should we cut the price". It is "which is the real reference for this fleet, and what do we do about the gap to the cheaper equivalent" — which is a product and positioning decision, and in one case it is a case for raising a price that sits materially below the comparable genuine part.

**Evidence from the paper.** Page 17 gives excellent rules for normalising a competitor observation (product, market, capture date, seller, currency, tax treatment, pack size, freight, availability; keep the source price separate from the normalised value; a public retail offer and a distributor price occupy different commercial levels). Page 18 routes it. Page 18 also says the applicable rules must be kept separate and that "the handover names Israel and blend traps but supplies no authoritative formula or current rate; none is reconstructed here." Nothing in the paper tells the reader that 16 real matched comparisons already exist with a computed index.

**Required correction.** Publish the matched set, its match basis, its date and its limitations, and add the "which reference applies" question as a named decision. This one table would carry a management meeting.

### 9. Confidence is handled well in principle and with no mechanism in practice

**Why it matters.** Page 16 says a finding carries one of four statuses with the reason shown, and page 25 refuses a single confidence percentage. Both are right. But nothing says who decides, on what basis, or how the reader sees the parts that make up the judgement.

**Evidence from the paper.** Page 16: "Ready for review — The named claim meets its required checks; this does not mean the intervention is approved. Needs validation — A specified identity, source, applicability or calculation check prevents the stronger conclusion." The checks are never listed. The brief's section 16 asked for per-analysis coverage indicators — billing 100%, fleet 95%, competitor pricing 71%, sales to dealer 64% and so on. The paper has the concept ("Coverage precedes ranking", "state which conclusions are restricted") but no format, no per-analysis display and no worked example of a partial-coverage result.

**Required correction.** Define the fixed set of checks that a finding must pass — coverage, identity, period alignment, unit compatibility, price comparability, applicability — and show them as a small panel on every finding, each marked pass, fail or not applicable. The four statuses then follow mechanically from the panel instead of being a judgement call, which is the point.

### 10. Nothing in the paper is owned, funded or dated, so it cannot be executed or refused

**Why it matters.** The paper's own next milestone requires five named people to exist. They do not, and the paper correctly says it cannot create them. But it also does not put the appointment in front of anyone as a decision with a consequence — it sits in a table on page 30 alongside nine other items of equal weight.

**Evidence from the paper.** Page 30: "Do not convert a proposed role into an appointment. The business owner must assign people and dates." Page 26's role table is marked "These are proposed accountable roles. Named appointments and available capacity are not established by this paper." Page 20 shows a written-out request to a distributor for one column of account numbers — the single highest-value action in the whole document, which the paper itself says would close the largest gap — and it is presented as proposed text that has not been sent.

**Required correction.** Take the two decisions that block everything else and put them on the cover as the ask: name one person for each of the five response classes with allocated time, and send the one-column request. Everything else in the paper can wait behind those two. If they cannot be obtained, that is the finding, and the paper should say so in the executive summary rather than on page 30.

---

## E. STRATEGY REVIEW

**Does Universe have a clear business purpose?** Yes, and it is the paper's strongest strategic instinct: ISZE holds parts purchasing, dealer-network data and fleet context in separate places, so a commercial question gets rebuilt by hand every time it is asked. The purpose — connect a question to its evidence, a response and a review of the result — is coherent and worth doing.

**Does the paper express it well?** Partly. Page 4 is clear: "A decision environment, not another collection of dashboards." The four named outcomes on page 4 are the right four: sales explanation, pricing precision, market comparison, service-range opportunity. The scope boundaries are unusually disciplined for this kind of paper — the aggregate sales view stays removed rather than deferred, product photography stays deferred, and Universe is explicitly not an ERP replacement, not an automatic price setter and not a distributor audit tool. Those three exclusions are correct and should survive.

**Where the strategy is weak.** It never states what ISZE gets in money, in time or in decisions, and page 2 explicitly declines to: "Better decisions are the proposition. Revenue uplift, time saved and improved capture remain outcomes to test." That is honest for a paper about a product that does not exist. It is fatal for a paper being taken to management for approval, because there is nothing to approve. There is also no competitor or alternative considered — no statement of what happens if ISZE builds nothing, which is the strongest comparator available and the one a controller will reach for.

**Strategic omission.** The paper does not address the actual decision it sits inside. Elsewhere in the folder is a funding request for €300,000, a funding case with a ceiling and released stages, and a proposal to ask distributors for one column of account numbers. None of those appear here. So the strategy is described in a vacuum: the reader is told what Universe would be, and never told what is being asked of them.

---

## F. PRODUCT REVIEW

**Does the paper describe a usable product?** No. It describes the rules a product would have to obey.

**What is present.** Four destination names (Portfolio, Network, Commercial review, Actions). Two view names (distributor view, dealer/account view). Required behaviours on context change: keep the period, clock and flow; show a change of basis on the face of the screen; distinguish missing, withheld, unpriced, unresolved and recorded zero; carry source versions into an action; show a restatement wherever a corrected result is used. Those are good product rules and they show someone has thought about interaction.

**What is absent.** The user, the task, the trigger, the queue, the opportunity page, the evidence panel, the simulation, the workflow states beyond four finding statuses, the permissions model beyond a paragraph, and the export. There is no "Price Lab", no opportunity detail page, no home. There is no description of what the reader sees on a screen that is itself described only as a diagram of data movement.

**The most telling absence.** Page 23's diagram is titled "CONTEXT THAT TRAVELS" and lists: population, period, flow, measure, coverage. That is a specification for a filter bar. A product with a better filter bar than any product screen is a product that has been designed from the data inward rather than from the user outward.

**Verdict on product readiness.** Not ready for approval as a build specification. The correct next artefact is one screen and one worked case, not a longer version of this document.

---

## G. AIM DEEP REVIEW

AIM is the commercial engine and the paper gives it three pages. This is the longest section of the review because it is where the gap is widest.

**Signal detection.** Nothing. The paper does not define what makes an opportunity appear, how large a movement must be, over what window, measured against what. This is the single largest omission in the document.

**Causality.** The paper's discipline is right and its method is missing. It repeatedly warns against claiming cause — page 5 on dealer self-assessment: "without claiming causation"; page 12: "timing differences can motivate questions about stock or ordering cycles but do not prove either"; page 19: "a before/after increase is an observation, not automatic proof that the special-price agreement caused it." Every one of those warnings is correct. But the paper never says how to move from a plausible explanation to a defensible one. It has no equivalent of a differential diagnosis: a fixed sequence of alternative tests that a decline must survive before a price conclusion is even permitted.

**Pricing logic.** Page 18 is a genuinely good routing page: four evidence patterns map to four different responses (normal price review, bounded special price case, a Genuine/alternative product discussion, a supply investigation), with the correct warning that unresolved product or market evidence produces a validation request rather than a pricing instruction. The commercial basis rules on page 18 are also correct — use the right ISZE net price, cost, currency, rebate and effective dates, and do not substitute a reference valuation for monetary evidence.

**Where the pricing logic fails.** It has no price-response assumption at all, and it honestly says so nowhere. There is no elasticity, no expected volume response, no way to size the consequence of the change. The only quantitative statement in the whole document that touches the question is the gross-profit break-even formula on page 19, which tells you how much volume you would need to preserve gross profit, not how much volume you would get. A pricing decision process without a volume assumption produces a well-documented guess.

**Competitor evidence.** The normalisation rules on page 17 are the best-written paragraph in the paper and I will not repeat them. What is missing is the dataset. Sixteen matched comparisons exist on disk with a computed price index against both the competitor's genuine and non-genuine listings, and the paper treats the whole subject as a promise. It also does not answer the question the data raises: when a fleet can be served by a cheaper equivalent, which comparison is the right one to act on.

**Fleet base.** The paper gets the hard part right — a parts list that fits several weight bands must stay pooled, and a market total repeated beside bands is not additive — and it puts a specific implementation rule in place for the band file. It is also honest that the model's service demand is not built. What it never states is the measured position: the demand model uses a flat 50,000 km a year while the measured figures are materially lower and vary by class, and 63.6% of the Portuguese parc is one model. A management reader cannot see from this document that the biggest modelled number in the programme rests on an assumption that the programme's own measurements contradict.

**Genuine and alternative parts.** Page 17 is strong on the rules: fitment, function, contents, package quantity, commercial unit and validation authority must all be established, and a candidate relationship stays excluded from substitution recommendations until then. It also correctly bans inferring quality from tier or country of origin in either direction. What is missing is the pattern analysis that makes the rule useful: a market that buys the alternative part exclusively while buying none of the genuine number for four years is a completely different commercial situation from a market that buys both, and the paper has no vocabulary for either.

**Sales trends.** Page 16 requires a dated monthly series, comparable periods, explicit missing months, no line drawn through an unreported month, quantity separated from price effect where price records allow, and part-level contributions reconciled to the selected total including an "other parts" remainder. It also bans combining pieces, kits and sets into one volume without a validated conversion. All correct. There is no trend method beyond that — no run rate, no seasonality handling, no treatment of a one-off large order.

**Decision rules.** See section L. The paper supplies the anatomy of a finding and no rules that produce one.

**Action recommendations.** Page 15's five patterns each end with a permitted next step, and the permitted steps are properly cautious: "a targeted investigation or supported offer, not a claim of lost market demand"; "an applicable distributor discussion or range review; no validated match means no substitution recommendation." Good discipline, but every permitted step is still an investigation. There is no action in the paper that a person could complete, and no example of one being completed.

**Financial logic.** Page 19 has the formulas. Nothing else.

**Confidence.** Correct in principle (no single score), undefined in practice (four statuses, no dimensions, no mechanism).

**False positives.** This is the paper's weakest practical area after detection. The brief's list of things a good system should suppress — low-value parts, tiny movements, parts with a declining fleet base, superseded parts, known supply constraints, incomplete data, one-off orders, uncertain applicability, ordinary variation — is addressed by a single sentence on page 15 about materiality. There is no minimum value, no volatility test, no suppression rule, no maximum queue length. A system built to this specification will produce either nothing or everything, and the paper does not say which.

**Overall AIM verdict.** The evidence rules are publishable. The engine is not designed. Three things are needed before AIM can be called an engine: a surface rule, an elimination sequence for alternative explanations, and a size floor with a queue limit.

---

## H. PRISM REVIEW

**Does PRISM materially improve decisions?** Not as described, and the paper half-admits it.

**What PRISM contributes.** Three things and no more: fleet composition and the installed base, applicability of a part to a vehicle family, and modelled service demand. Page 14 is precise about what each view may show and what it may not — recorded exclusive-applicability purchasing is a subset and not the band's demand; a modelled expectation is not observed servicing; a market-level total repeated beside bands is not additive and must not become a band's measured numerator. Those distinctions are correct and important.

**Why it is currently decorative.** Because the one thing that would make it decisive — the approved service schedule — is unapproved, so the demand model cannot be computed, so PRISM cannot change any recommendation. Page 14 says so: "Until an applicable schedule is approved, show observed purchasing. Do not manufacture a precise service-demand estimate." Page 5 goes further: "Its proposed role is fleet composition, relevant vehicle segments, applicability and modelled service-demand context. The functional boundary requires confirmation before implementation."

**The honest consequence, which the paper does not state.** With the schedule unapproved and the demand model unbuilt, PRISM currently reduces to a fleet denominator — and the denominator itself is contested. If PRISM's contribution to a decision today is a fleet count, then "three pillars" is really one pillar plus a parts tree plus a self-assessment survey. That is worth saying plainly to a management reader, because it changes what they are approving.

**What would make PRISM change a decision.** One thing: a measured annual distance for the relevant class, replacing the flat assumption, applied to the same family the review is about. Then a purchasing figure becomes a rate per vehicle and can be compared with another market. The paper has this concept — "billing or reference valuation per relevant vehicle is a purchasing-intensity lens" — and does not pursue it, even though measured distances for the relevant model groups exist elsewhere in the folder and disagree with the assumption being used.

---

## I. IDS REVIEW

**Is the representation correct?** Yes, and this is the paper's most carefully handled risk. Page 5: "Dealer self-assessments contribute reported practices, assessment context and follow-up… it is never a distributor audit score." Page 20 repeats it and adds the operational limits: attach an assessment only through an accepted relationship and the available assessment timing; if no per-dealer date exists, show that limitation rather than manufacturing a chronology. Page 26 assigns interpretation to a standards owner. All correct, and consistent with what the underlying files actually are.

**Is it commercially useful?** Not yet, and the paper is honest about why. Page 21 limits the Portuguese pilot to "an independently labelled dealer-assessment view. Do not allocate national purchasing to named dealers." Page 15's fifth decision allows a dealer-support conversation and forbids claiming that a self-assessed weakness caused a commercial result.

**The three things that keep IDS out of the decision engine.** The paper mentions the first two and understates both.

1. **One round only, with no per-dealer date.** So no comparison over time is possible, and no statement of the form "as at this date this dealer scored this" can be made. Without a date you cannot put an assessment beside a purchasing period, which is the entire commercial use of the data.
2. **The self-assessment is not independently verified.** The paper's language is "dealer self-assessments" and it is accurate. But the underlying files make the position sharper than the paper's wording conveys: an independent assessor column exists in the Portuguese round and is empty on every file. So the data is what a dealer says about itself plus a site visit, with no independent rating. A commercial reader needs that stated, because it changes what a disagreement with a dealer can be based on.
3. **Coverage is partial and market-dependent.** 519 records across 19 country lists, one market totals-only. The paper says to describe the assessed population every time, which is right; it does not put the coverage figure on the page.

**The genuine insight the paper misses.** The Portuguese round is the clearest worked example in the whole programme, and it is a contradiction: the highest-scoring section in the dealer self-assessment is parts and accessories, at a very high average, in a market whose parts capture against the modelled ceiling is under half. Both are real. Explaining that gap — is the self-assessment measuring process rather than outcome, is the ceiling wrong, or is the market genuinely buying elsewhere — is the single best use of IDS anywhere in this folder, and it needs no new data. The paper does not know about it.

**IDS verdict.** Correctly described, correctly restricted, not yet earning a place in a commercial decision engine. Keep it as context and do not let it vote.

---

## J. DISTRIBUTOR VALUE REVIEW

**Is the exchange compelling in the paper?** Conceptually yes, practically no.

**What is right.** Pages 6 and 9 are the best strategic writing in the document. The three-position separation — recorded starting point, contractual evidence, proposal — is exactly the right way to handle an incentive that ISZE does not fully control. The promise that the minimum quantity feed will not silently become a request for prices, margins, stock, customers, vehicle identities or workshop records is the promise that makes a distributor say yes. Page 9's rule about additional contribution buying a visible additional return, with a limitation written beside each item, is the correct design.

**What is missing.** The tiering the brief asked for. Page 9 lists five optional exchanges in a table, but there is no numbered ladder, no statement of what each level buys and costs, no worked example of what a distributor receives, and no euro figure anywhere. Compare that with the value-exchange document on disk, which sets out five numbered levels — ISZE data only; sales to dealer with no prices; dealer and network identity; commercial context; optional operational information — each with what it unlocks and what it costs the distributor, plus a minimum ask of exactly three things. Its treatment is materially better than the paper's, because it is a proposal someone could accept rather than a principle someone must interpret.

**Three gaps the paper leaves that matter commercially.**

1. **The mechanic is never stated.** The paper says part of the distributor support is linked to supplying sales-to-dealer information. The folder audit states the actual split and the fact that this year's proposal was to attach the sales-to-dealer file to the data leg of it. The paper does not need to print commercial terms, but a paper about the exchange needs to say what it is deliberately not stating, or the reader cannot judge whether the design is plausible.
2. **The honesty is positioned as a hedge rather than as a finding.** Page 6 says the incentive "can encourage submission; it does not by itself establish that the file is useful". That is the right conclusion and it is buried. It is arguably the most important commercial statement in the document: the current arrangement reliably produces a file and unreliably produces a good one, which is why the product has to earn the good one. That belongs in the executive brief.
3. **No worked example of what a distributor gets.** The draft on disk says what a distributor receives in one sentence each; the paper describes the return as a process ("Receive and validate the submission; return an acceptance receipt; prepare the review…"). A process is not a benefit. A distributor does not want a receipt; it wants to know why its brake purchasing fell.

**Verdict.** The design principle is right, the commercial case is unproven in the document, and the better version of this chapter already exists in another file.

---

## K. DATA ARCHITECTURE REVIEW

**Sources and ingestion.** Page 10 gives a real minimum data contract: distributor and account identifier, reporting period with a closed or provisional state, original part number preserving leading zeros with a separate normalised key, signed quantity and declared unit, transaction and channel, submission identity with revision and schema version, coverage declaration, and a controlled population including zero-activity accounts where supported. Wholesale is handled correctly — name the known purchasing entity and do not push a wholesaler's purchases onto dealers further down the chain without a supported relationship. Preference for full-replacement revisions over increments is right. This is a competent specification and it is the most buildable page in the paper.

**Identifiers.** The paper states the principle well and the measured position not at all. Page 20 distinguishes organisation, purchasing account, physical site and assessment correctly, and says a name-to-account match can close identification while leaving site attribution unresolved. What it does not print is the actual state of the join, which the draft it revises did contain: the two columns a join would need are blank on all 66,018 rows of the replenishment bridge; none of the three ITUK purchasing accounts are mapped to a dealer site; and of the 64 dealer names, roughly sixteen match exactly, about thirty-four reach a strong name overlap and about twenty have no plausible match. Those three facts are the reason the product cannot show a dealer-level comparison today. Removing them from the paper removes the reader's ability to understand why the programme is stuck.

**Coverage.** The principle is stated — coverage precedes ranking, never invent a completeness percentage — and the display format is absent. The brief asked for per-analysis coverage (billing, fleet, competitor, sales to dealer, assessment population, alternative-part mapping). The paper's context strip on page 23 lists coverage as one of six things a strip carries and never fills it in. Note also that this strip is not in the delivered PDF text — the paper's illustration is a diagram, not a screen.

**Provenance.** Page 25's registers are genuinely good: a source and coverage register, a metric definition register, a quantitative claim register requiring an exact source and version, a capability register, and a decision register. Page 13's rule that every quantitative business statement needs a retrievable record that another reviewer can reproduce is exactly right and is the kind of requirement most organisations never write down.

**Join logic.** Page 24's rules are correct and practical: test the expected row count of every join; multi-band applicability must not multiply a purchasing total; one account linked to several sites must not duplicate the result; keep unresolved keys visible rather than discarding their quantities. The paper calls join multiplication "amplification" once and does not define it, which is a small register slip in an otherwise careful document.

**What the architecture does not address.** No source system is named, no refresh cadence is agreed (page 10 says monthly is proposed and the ten-working-day deadline is explicitly not approved), no hosting, no authentication (page 26 says there is no host today and the folder that would be published is not safe to publish, which is a serious and well-made admission), no user-permission model beyond a paragraph, and no audit trail beyond the registers.

**Data architecture verdict.** The rules are sound and the registers are worth building. The missing element is the measured state of the identity join, which is the one fact that determines what the first release can show.

---

## L. COMMERCIAL DECISION ENGINE — THE LOGIC THE PAPER SHOULD SPECIFY

The brief asked for this reconstructed in the form: signal, evidence, interpretation, confidence, action, owner, expected effect, measurement. Below is that chain, written so it could be dropped into the next edition. Where the paper supplies nothing, I say so, because the blanks are the finding.

**Step 1 — Signal.** *Missing from the paper.* Proposed: a part family's monthly purchasing in one flow moves by more than a stated floor, in both units and euro, against its own prior twelve months; measured on monthly rows only; with the family's coverage unchanged and the fleet base for its applicable bands not falling by more than the movement.

**Step 2 — Evidence.** *Present in outline, page 16.* A dated monthly series with missing months explicit; part-level contributions reconciling to the family total with an "other parts" remainder; signed returns separated from sales; quantity separated from price where price records exist; original and normalised part numbers; coverage statement.

**Step 3 — Elimination.** *Absent from the paper.* Proposed, in order, and each one able to close the case with no action:

1. Fleet base fell at least as much as purchasing → explained, close.
2. A contributing part number has a validated supersession pair whose replacement rose in the same period → re-attribute, then re-measure.
3. The movement sits in one or two months and one account → treat as a stock or ordering event, and raise it as a replenishment question rather than a demand question.
4. A known supply constraint or backorder covers the period → close as supply, not demand.
5. The movement is within the family's own normal variation over the prior two years → close as noise.
6. A price change on our side, or a recorded change of commercial terms, coincides → re-measure at constant price.
7. Only then: is there a comparable external price observation, and does it say we are above the credible reference for this application?

**Step 4 — Interpretation.** *Partly present.* The paper's rule is right: a supported explanation, the plausible alternatives that remain, and what would change the conclusion. It needs the elimination record above attached, so a reader can see which alternatives were tested and dropped rather than merely absent.

**Step 5 — Confidence.** *Present as principle, absent as mechanism.* Proposed: the fixed check panel from section D.9 — coverage, identity, period alignment, unit compatibility, price comparability, applicability — each marked pass, fail or not applicable, with the finding's status derived from the panel rather than chosen.

**Step 6 — Action.** *Present as a routing decision, pages 15 and 18.* Four routes: a normal price review; a bounded support case; an alternative-part or range discussion; a supply or replenishment investigation. Plus two non-actions the paper correctly allows: investigate a defined technical question, and take no commercial action. What is missing is any action specific enough to be completed. Every permitted step in the paper is an investigation.

**Step 7 — Simulation.** *Absent entirely.* The paper has the formulas on page 19 and no tool, no scenario, no baseline definition, no volume assumption and no output. This is the largest functional gap after detection, because the paper's flagship outcome is "pricing precision".

**Step 8 — Approval.** *Present and correct, pages 18 and 19.* "The commercial owner approves the route and economics. Universe assembles the evidence; it does not set prices automatically."

**Step 9 — Measurement.** *Present as a record, deliberately not as an attribution engine, page 19.* "A before/after increase is an observation, not automatic proof that the special-price agreement caused it." That is the honest position and it is also the limitation: the paper states no counterfactual method, so no intervention can ever be shown to have worked. A workable compromise exists and is not in the paper: compare the treated family against a control family of similar size and seasonality in the same market over the same window. That is not proof either, but it is a defensible observation, and without it the programme will accumulate decisions with no results attached.

---

## M. FINANCIAL MODEL REVIEW

**What the paper provides.** Page 19 defines gross profit in currency and gross margin as a percentage, requires baseline and scenario to share a defined period and scope, distinguishes an actual historical baseline from a modelled no-intervention case from a future commitment, and gives four formulas: baseline gross profit, scenario gross profit, the change between them, and the break-even quantity needed to hold gross profit flat when unit margin changes. It also correctly handles the awkward cases: zero or negative unit margin means more volume is not the answer; rebates, headquarters support and freight belong in the cost definition and must not be double counted; Genuine volume replaced by the alternative part is not new business; currency and unit must be compatible and an unidentified workshop money unit must not be given a euro label.

**What is missing.** No distributor discount mechanic, and therefore no way to model the room a distributor needs before a price change reaches a dealer. No support-cost model for a special price agreement — no duration, no volume commitment, no payback, no expiry treatment. No baseline definition in practice: the paper says the scenario must have a baseline and does not say whether the baseline is the last approved version, the actual prior period, or a forecast. No elasticity and no volume assumption. No outcome-tracking method. No worked numbers of any kind, and the document contains no euro figure at all.

**What exists elsewhere and is better.** A funding paper on disk covers the money question properly: a ceiling with staged release, an explicit statement that no euro return is evidenced, two comparables examined and refused as a return calculation, and a warning not to slice a pilot return out of the modelled ceiling. That is the financial chapter this paper does not have.

**Financial verdict.** The formulas are correct and the discipline is good. A commercial opportunity engine without a way to estimate the volume response to a price change, and without a way to say afterwards whether the change worked, has no financial model — it has a profit calculation.

---

## N. UX REVIEW

**Does the interface make commercial losses obvious?** There is no interface, so the honest answer is that the question cannot be answered from this document. What can be assessed is the specified behaviour.

**What the specification gets right.** Context is preserved across a drill-down, and where the next view cannot support it, the restriction is explained before the selection changes. A change of basis between actual billing, reference valuation and modelled demand is shown on the face of the screen rather than in a tooltip. Missing, withheld, unpriced, unresolved and recorded zero are five distinct states and none renders as a zero. A review leads to an action without retyping the scope, and the action returns to the analysis it came from. Corrections are visible wherever the affected result appears. Complete paths are preferred over many incomplete pages. Maps do not establish responsibility.

Those eight rules are better than most commercial dashboards' actual behaviour, and the five-state distinction in particular is a genuinely good idea that most products get wrong.

**What is missing.** The opportunity page, the evidence panel layout, the price-position display, the queue, the workflow states, the permissions view, the export, and the empty-state design. Page 23's illustration is a data-flow diagram. The paper never describes a single screen — not its headline, not its panels, not its actions. "Screen" appears twice in passing; "button", "click", "wireframe", "mock" and "sidebar" appear zero times.

**One specific inconsistency.** The paper criticises an existing dealer self-assessment action register on page 20 — rows with no owners, no due dates, every row open, and correctly warns that a blank register does not prove the network is inactive. Page 23 then names "Actions" as one of four product destinations. The paper never says whether these are the same register, and a reader will assume the new product's Actions destination will inherit the problem the paper has just criticised.

**UX verdict.** No interface exists to review. The interaction principles are unusually good and should be kept; the screens have not been designed.

---

## O. PROPOSED HERO SCREEN

The single screen that should make an ISZE manager understand the value in ten seconds. Filled in, because an empty mock-up is what the paper already has.

**Title.** Brake, clutch and hub fasteners — ITUK, Warrington Vehicle Centre — 13,801 units in 2025, first half 7,813, second half 5,988.

**Row 1 — the headline, in one sentence.** "This account bought 452 wheel and hub fastener units in the first half of 2025 and 40 in the second. The rest of the same family fell from 386 to 78 but kept running. Coverage and identity are unchanged, no part number is superseded, and no price change was recorded. This looks like a stop in demand or a change of supply route, not a price problem."

**Row 2 — three figures, each with its basis printed beside it.** 13,801 units for the year across 1,270 part numbers, monthly rows only, one account. First half 7,813 against second half 5,988. The five contributing part numbers at 452 units against 40, against a family rest-of 386 against 78.

**Row 3 — the evidence panel, as a strip of small charts.** The monthly series with the five numbers and the rest-of-family series drawn together, so the stop and the continuing line are visible at once. The same account's total by month behind it. A coverage note: this account carries all twelve months; the feed covers one year only; no fleet figure exists for this dealer.

**Row 4 — the elimination record, which is the part that makes it a decision product rather than a chart.** Six rows, each marked tested or not testable, with the reason: fleet base — not testable, no dealer-level fleet exists. Supersession — tested, all five map to themselves. Supply — tested, no backorder record for this account. Price — tested, no price change recorded in the period. Seasonality — tested, the family as a whole does not show the same pattern. Stocking cycle — plausible, unresolved.

**Row 5 — the alternative explanations that remain, and what would settle them.** Two: a stocking cycle that ran down, or work moving to another supplier or another workshop. What would settle it: the account's next three months of purchasing, and a question to the distributor's parts manager.

**Row 6 — the recommended action, and the honest non-action.** "Raise this as a supply and ordering question with the distributor. Do not treat it as a pricing opportunity. Do not treat it as evidence that this dealer under-serves its trucks, because the file cannot support that sentence."

**Row 7 — the workflow strip.** Raise a question to the distributor, assign an owner, set a review date, record the answer, link the next three months' data to the case when it arrives. Buttons: raise, assign, request input, close as inconclusive, reopen.

**Why this is the hero screen.** It shows a decline, shows the size, shows that five alternatives were tested and three of them eliminated, shows that one explanation remains and what would settle it, and then recommends the smaller action. Nothing on it is a number the system cannot reproduce from a file. It is the paper's own discipline made visible — and it is exactly what page 16 says every finding should be, which is the point: the standard is right and the paper never shows it applied.

---

## P. FIVE CONCRETE COMMERCIAL USE CASES

Where a number is real I label it measured and give the file. Where a step is my judgement I label it. No invented ISZE figures are used.

### Example A — a case for lowering a price: the air filter against the cheaper equivalent

**Measured.** Air filter `8970622940`. Our dealer price €49.98. The competitor's genuine listing for the equivalent is £55.00 ex VAT and its non-genuine listing is £30.00. Our price index is 0.777 against the genuine and 1.424 against the non-genuine — that is, we are 42% above the cheaper alternative and 22% below the comparable genuine one. Source: `ks_aftermarket_price_compare_20260819.csv`, rows matching this part number; 105 rows in the file, 16 carry an ITUK match.
**Illustrative.** A second air filter `8976739570` sits in the same position: index 0.837 against the competitor's genuine, 1.196 against its non-genuine.
**Diagnosis.** The gap is not against the genuine market. It is against the cheaper equivalent, which the same file shows is a real purchase alternative.
**Recommended action.** Not a price cut. First: establish how many of these units go to applications where the cheaper equivalent is a genuine fitment substitute. Second: if a validated alternative exists in our own range, that is a range and positioning action. Third: only if neither holds, and only for a named set of accounts, a bounded support case.
**Owner.** Product owner for the applicability and substitution question; commercial owner if it becomes a support case.
**Expected effect.** Recovered volume on part numbers where the alternative is being bought. Not stated in euro because the applicable fleet and the account-level split are not known.
**Measurement.** Monthly units on the part number, split between our genuine and any alternative, before and after, with a comparable family as a control.

### Example B — a case for raising a price, or at least for not cutting one

**Measured.** Oil filter `8975439050`. Our dealer price €10.73. The competitor's genuine listing is £15.00 and its non-genuine £12.00 — our index is 0.611 against the genuine, meaning we sit about 39% below the comparable genuine part. Fuel filter `8983752250`: our index 0.725. Source: same file, same method.
**Illustrative but evidenced in direction.** The Portuguese file shows real volume on the oil filter at national level.
**Diagnosis.** On these numbers our dealer price sits below the comparable genuine reference with no visible volume decline. That is a candidate for a price increase, not a discount.
**Recommended action.** A normal price review for the named part numbers at the correct commercial level, checking the distributor's room before and after, with the applicable net price, cost and effective dates taken from the price system rather than from a reference valuation.
**Owner.** The commercial owner, since this is a level decision, not a case-by-case support decision.
**Expected effect.** Higher gross profit per unit; the volume effect is the unknown and must be stated as such.
**Measurement.** Units and gross profit per month for two quarters, with the distributor's ordering pattern checked for a one-off stock effect.

### Example C — an alternative-part opportunity, and the trap inside it

**Measured.** Two air filter numbers sit in the price file side by side, `8970622940` and `8976739570`, each with a competitor genuine and non-genuine listing, and ours at €49.98 and €48.98 respectively. Both are far above the competitor's non-genuine listing and both are below its genuine one.
**Reported, not personally verified by me.** The pilot pack records that within the ITUK dealer file, 38 of 64 dealers buy both numbers, 17 buy only the second and 2 buy only the first. I verified the two part numbers and their price positions; I did not re-run the dealer split.
**Diagnosis.** A network in which 59 of 64 dealers buy one or both of two part numbers that look like a supersession pair but may be separate applications is either an application-confusion problem, a range-rationalisation opportunity, or a normal two-application split. The paper's own rule applies: a family or catalogue match is not evidence of interchangeability, and no validated match means no substitution recommendation.
**Recommended action.** First a technical question — are these two applications or two versions of one? — with the answer recorded against both part numbers. Then, if they are two versions, a range review; if two applications, a fitment-clarity action in the parts catalogue. Not a substitution recommendation until the technical authority has ruled.
**Owner.** Technical authority for the question; product owner for the catalogue action.
**Expected effect.** Fewer wrong-part purchases and a clearer offer. Not a price effect.
**Measurement.** Dealer-level purchase mix on the two numbers before and after; the number of accounts buying the wrong one for their applications.

### Example D — the correct answer is to do nothing

**Measured.** Account: Warrington Vehicle Centre. 13,801 units in 2025 across 1,270 part numbers; first half 7,813, second half 5,988. Five wheel and hub fastener numbers: 112, 104, 92, 88 and 56 units in the first half falling to 8, 6, 6, 8 and 12 in the second, a total of 452 against 40. The remaining 29 numbers in the same family fell from 386 to 78 but continued. All five map to themselves in the part replacement table; the largest negative anywhere in the year on those numbers is one return of eight units at a different account. The monthly series peaks at 212 units in May 2025 and the five numbers show no units at all from July onwards. Source: `dealer_sellout_long_ITUK_CY2025.csv`, split by month and part number, reproduced by me.
**Also measured, and relevant.** The same account scores highly in the dealer self-assessment round, and that must not be used as explanation because the round has no per-dealer date.
**Diagnosis.** A genuine stop, with the family around it continuing. Two explanations remain — a stocking cycle that ran down, or work moving elsewhere — and the file cannot choose between them.
**Recommended action.** No price action and no conclusion. Raise it as a supply and ordering question with the distributor, put the next three months against it, and record the outcome either way. This is the example that proves a decision engine is real: it declines to conclude.
**Owner.** The commercial owner for the question; the distributor's parts function for the answer.
**Expected effect.** If it is a stocking cycle, purchasing resumes and the question closes. If it is not, the answer is worth more than a dashboard.
**Measurement.** The next three months of units on those five numbers, and the answer recorded on the case.

### Example E — the opportunity belongs in a support case, a tender or a distributor conversation, not in the price list

**Measured.** Portugal: a complete national sales-to-dealer file, 21,636 rows and 51,363 monthly units for 2025, with the dealer-name column empty on every row. Two of the sixteen dealers in the Portuguese self-assessment round are the distributor's own retail sites. The same file shows that a defined set of genuine/alternative part number pairs is bought exclusively on the alternative side.

**And here is a genuine unresolved problem I found while checking, which is an example in its own right.** The fleet file records Portugal twice in 2025: one row for the CV class split into F-Series (269) and LD (2,206), and one row for the LCV class (4,733). Whether the correct fleet denominator is the CV reading alone (2,475) or CV plus LCV (7,208) is not stated anywhere. On the same billed value that is the difference between roughly €690 and roughly €237 of parts per truck — a factor of nearly three. That is exactly the trap the paper's own rules warn about, and neither the paper nor this review can resolve it without a scope decision.
**Diagnosis.** A national offer question and a range question, not a dealer-performance question, because no dealer purchasing attribution is possible and the paper correctly forbids creating one.
**Recommended action.** A national offer review with the distributor covering the families where the modelled spend per truck sits furthest below the comparable markets, built on actual billed value and on the alternative-part pattern. If a specific fleet opportunity appears, the route is a bounded support case with named parts, scope, duration and review; if a public fleet tender appears in the market, the route is tender support with the parts exposure and historical pricing attached. Do not adjust the national price list on the strength of a modelled ceiling.
**Owner.** Commercial owner with the distributor's parts function.
**Expected effect.** Higher spend per truck in the named families, on an offer the distributor has agreed rather than a list change.
**Measurement.** Quarterly spend per truck in those families, and the number of support cases raised with the distributor's own evidence attached.

---

## Q. MVP

The smallest version that produces real value. Chosen so that every element is available today, and so that the first thing a user sees is the Warrington case rather than an empty shell.

**Scope.** One market — ITUK — because it is the only one with named dealers. One year, calendar 2025, because that is what exists. Monthly rows only, with the annual control row used as a check and never added. 66,018 monthly rows carrying 223,897 units across 64 dealers and 5,559 part numbers, 60 of the 64 dealers present in all twelve months.

**What it contains.**

1. **A portfolio view** at family level with the genuine-versus-alternative split, on actual billed quantity, with coverage printed on the face of it.
2. **One working opportunity page**, pre-loaded with the Warrington fastener case (section O), including the elimination record and the honest non-conclusion.
3. **An opportunity list** limited to a stated maximum number of items, ranked by measured value at risk, produced by a surface rule that is written down even though it is crude.
4. **The two purchasing flows side by side** for ITUK — what ISZE billed to ITUK and what ITUK's dealers bought — never added, never reconciled by assumption, and each labelled with its own coverage.
5. **The matched price position**, published with its match basis, its date and its limitations — 16 matched part numbers, not 105.
6. **The finding standard as an actual template**, so a second case can be built by someone else and come out in the same shape.
7. **The action record** — question, owner, decision, review date, answer — with five states and no workflow engine behind it.
8. **An honest unavailable state**: what the product cannot show, why, and what data would change it.

**What it deliberately excludes.** Dealer self-assessment linkage (no assessment date exists). The service-demand model (no approved schedule). Price simulation (no volume assumption). Any second market. Any dealer-facing page. Tender support. Any hosting decision or external access. Alternative-part substitution recommendations pending technical validation.

**Definition of done for the MVP.** One named person at ISZE can open it, reproduce the Warrington numbers from the source file, explain the case to the ITUK parts director without leaving the screen, have their explanation challenged on one point, correct the underlying record, and see the case and the numbers update. That is the paper's own exit test, and it is the right one.

---

## R. PILOT PLAN

Two pilots, because the two markets genuinely prove different things. The paper is right about this and I am not changing it. What I am adding is the measured state of each.

### Pilot 1 — ITUK, dealer-level monthly review

**Hypothesis.** A distributor will change a commercial decision because this review shows it something it could not see from its own files.

**Data that actually exists.** One year, 66,018 monthly rows carrying 223,897 units across 64 named dealers and 5,559 part numbers, all twelve months present, 60 of 64 dealers complete for the year, 399 monthly rows carrying negative quantities. A second unreconciled purchasing file of about 90,000 rows exists for the same period and disagrees with the first; it must be parked, not blended.

**Data that does not exist.** No dealer-level fleet, so no rate per vehicle at dealer level — the fleet figure on the fleet table is the same national number on every dealer row. No link between a dealer and a buying account: the two columns a join would need are blank on all 66,018 rows of the replenishment bridge, and none of the three ITUK purchasing accounts is mapped to a dealer site. No second year, so no dealer-level trend. No usable assessment date for the self-assessment round.

**What the pilot can genuinely demonstrate.** A monthly review at dealer grain on one year; a real decline explained down to part numbers; the two flows side by side; a correction exercised end to end; a question routed to a named person and answered.

**What it must not claim.** Any rate per dealer. Any dealer ranking. Any statement that a dealer under-serviced its fleet. Any joined assessment score. Any year-on-year at dealer level.

**Success criteria.** One review reproduced from source by someone who did not build it. One correction accepted and the affected results restated and the earlier version retained. One question assigned to a named person with an agreed date and answered. One decision changed, evidenced by a written record rather than by a login. One honest demonstration of something the product cannot show.

**Participants.** A named ISZE analysis owner, a named ISZE commercial owner, a named person for each of the five response classes, and a named parts owner at ITUK. The paper says none of these can be created by writing a document. It is right, and that is the binding constraint on this pilot.

**Duration.** One full review cycle plus one correction and one question, which is to say roughly one quarter of elapsed time. Not one month, because the question-and-answer leg is the part being tested and it is the part that has never happened.

### Pilot 2 — Portugal, national review

**Hypothesis.** A distributed market will engage with a national review even without dealer attribution, and the review will change how ISZE defines a parts family.

**Data that actually exists.** A complete national sales-to-dealer file for 2025 and 2026 to August, with **no dealer name in any row**; 51,363 monthly units in 2025 across 5,712 part numbers. National parts billed of about €1.71m against a fleet that the fleet file records twice for the same market and year, with no stated rule for which reading applies. Sixteen dealer self-assessments with dated site visits in spring 2026, two of which are the distributor's own retail sites, and an independent-assessor column that is empty on every file. A set of genuine/alternative part number pairs where the market buys the alternative exclusively.

**What the pilot can genuinely demonstrate.** That a family total moves substantially depending on how the family is defined on the same file — the draft on disk measured the same oil filter family three ways on the same 51,363 units and got readings that differ by more than half. That a replacement-part mapping changes the story on a market that appears to have stopped buying three part numbers and has in fact moved to their current versions. That a market can be reviewable nationally without any dealer attribution.

**What it must not claim.** Any dealer-level purchasing. Any share of the national total attributed to a site. Any dealer performance conclusion. Any statement that the self-assessment contradicts or confirms the purchasing position.

**Success criteria.** One review prepared, explained to the distributor's parts function, corrected on at least one point, and followed into one owned action. Plus: the family definition question settled and written down, because if it is not, every subsequent number in that market is arguable.

**Participants.** As above, plus the distributor's source owner for the file.

### What must not be assumed

The two pilots do not validate each other. Passing the national review says nothing about whether a dealer-level join is possible. Passing the dealer-level review does not create Portuguese dealer attribution. The paper already says this on page 21 and it should stay.

---

## S. SUCCESS CRITERIA

Split into three, as the paper does, because they measure different things. Every one is checkable by a person rather than by a system.

**Data reliability.** Can a second person reproduce the headline numbers in a review from the source file without asking anyone? Is the coverage position printed on every result? Is every missing month shown as missing and every declared zero shown as a zero? Does reprocessing the same submission change nothing? Does a correction restate the affected results and keep the earlier version?

**Use.** Did the review reach the recipient and did they engage with a specific part number? Was at least one question answered by a named person within an agreed date? Was at least one correction received from the distributor rather than requested by ISZE? Did the distributor use the review in a conversation with its own dealers? Did the second month's file arrive without a reminder?

**Commercial.** Was at least one decision recorded with a reason, an owner and a date? Can that decision's effect be observed in the following months' numbers, with a comparable family as an approximate control? Did the first support case or range discussion arise from the review rather than from a distributor's complaint?

**The go/no-go question, stated so it can fail.** If the incentive that currently produces the file were removed tomorrow, would the distributor keep sending it? The paper states this test and it is the right one. Everything above is a way of gathering evidence for it.

**What must never be used as a success measure.** Logins, page views, the number of findings generated, the modelled value of the opportunities identified, uploaded row counts, and the reference value of workshop lines. The paper bans all of these on page 31 and it is right to.

---

## T. IMPLEMENTATION REALITY MATRIX

| Capability | Ready now | Pilot ready | Data work needed | Logic validation needed | Future |
|---|---|---|---|---|---|
| ISZE billing history by distributor, family and month | ✔ | | | | |
| Three-flow separation and the coverage rules | ✔ | | | | |
| Minimum data contract for the monthly quantity feed | ✔ | | | | |
| Source, metric, claim, capability and decision registers | ✔ | | | | |
| The finding template and its statuses | ✔ | | | | |
| The one-column dealer-to-account request (written text) | ✔ | | | | |
| ITUK dealer-level monthly review, one year | | ✔ | | | |
| Portugal national review | | ✔ | | | |
| Two purchasing flows shown side by side | | ✔ | | | |
| Matched competitor price position, 16 part numbers | | ✔ | | | |
| Correction and restatement end to end | | ✔ | | | |
| Named response owners and allocated time | | | ✔ | | |
| Dealer-to-account identity join | | | ✔ | | |
| Classification release pinning and family labels outside ISZE | | | ✔ | | |
| Currency declaration for the workshop workbook | | | ✔ | | |
| Assessment date for the dealer round | | | ✔ | | |
| A second dealer-level period, for any trend | | | ✔ | | |
| Dealer-level fleet denominator | | | ✔ | | |
| Materiality floors, surface rules and queue limits | | | | ✔ | |
| Elimination sequence for alternative explanations | | | | ✔ | |
| Price volume-response assumption | | | | ✔ | |
| Outcome measurement approach, including a control | | | | ✔ | |
| Predicted response to a price change | | | | | ✔ |
| Service-demand model (blocked on the schedule) | | | | | ✔ |
| Dealer-facing pages and access model | | | | | ✔ |
| Tender panel | | | | | ✔ |
| Hosting, authentication and external access | | | | | ✔ |
| Second and later markets | | | | | ✔ |

**How to read this.** Nothing in the top block needs a decision. Everything in the "data work needed" block needs a person, and several of them are one afternoon's work — pinning a classification release is one file, declaring a currency is one word, sending the account-number request is one email. Everything in "logic validation needed" is where the paper has nothing at all, and it is the block that determines whether this becomes a decision product or another dashboard.

---

## U. ASSUMPTION REGISTER

| Assumption | Current evidence | Status | Risk | Validation required |
|---|---|---|---|---|
| Competitor pricing is available and comparable | 105 rows, 16 matched to ITUK part numbers, one capture date, one competitor | Partially validated | Medium | Re-run on a schedule; decide which comparison level is the relevant reference |
| Dealer-level purchasing can be linked to a buying account | Join columns blank on all 66,018 rows; 0 of 3 accounts mapped; roughly 16 of 64 names match exactly | Unvalidated | **High** | The one-column request, then a measured match rate |
| Dealer data quality is adequate for a monthly return | One market, one year, no second month anywhere; a second file for the same period disagrees with the first | Unvalidated | **High** | A second month from one market, then a reconciliation between the two ITUK files |
| Fleet data is current enough to interpret purchasing | No dealer-level or territory fleet anywhere; the fleet column repeats one national figure on every dealer row | Unvalidated | **High** | A market-level measurement per class, and a decision not to compute dealer rates until one exists |
| Part applicability is reliable enough to compare families | Classification releases disagree and no authority is declared; supersession table carries no date, no source and no reversal flag | Unvalidated | **High** | Pin one classification release; name the axis; establish what the replacement table is |
| Distributor participation can be increased | Seven markets sent one file each; nothing has arrived a second time | Unvalidated | **High** | One second submission, and one optional contribution given voluntarily |
| Pricing interventions can be measured | No baseline taken, no counterfactual method, no control group | Unvalidated | Medium | Agree a control-family comparison before the first intervention, not after |
| Users will follow an action workflow | No case register exists at case level; no name is attached to any response class | Unvalidated | **High** | Name the owners and route one real question through the process |
| The service-demand model produces a usable expectation | The schedule is unapproved; the flat distance assumption contradicts measurements elsewhere | Unvalidated, and currently contradicted | Medium | Approve the schedule, or stop publishing the model and publish observed purchasing only |
| The three pillars are independent analytical assets | PRISM cannot compute its main output; IDS cannot be attached to a period | Partially validated | Medium | State honestly that the current decision value is concentrated in one of the three |

---

## V. FAILURE MODES

Ten plausible ways this ends badly, with the prevention.

**1. It ships as a dashboard.** The most likely outcome, because the rules are written and the engine is not. *Prevention:* the first release contains one screen and one case, and nothing is added until that case has been challenged and used.

**2. Opportunity spam.** With no size floor and no queue limit, the first machine that implements these rules will produce either a hundred items or none, and in either case nobody will use it. *Prevention:* a stated maximum number of items at the top of the list and a written floor.

**3. False causality.** A price falls in the same month a competitor listing is captured and the pair is published as a cause. The paper's warnings will not survive contact with a desire to act. *Prevention:* the elimination record is mandatory on every finding, and a finding without it is not publishable.

**4. The identity join never happens.** The one-column request is never sent, or is sent and not answered, and dealer-level comparison stays blocked indefinitely while national work proceeds. *Prevention:* put it in the executive summary as one of two decisions, with a named sender and a date.

**5. Nobody answers the questions.** The paper's own diagnosis: no case register exists, no name is attached to any response class, and capacity is unfunded. *Prevention:* do not launch a recurring promise until one named person with allocated time exists for each class. Start with two of the five, and route real questions through them.

**6. The classification freezes family work.** Family labels cannot be published outside ISZE while no release is pinned, and no release is pinned. *Prevention:* pin one. It is a single decision and it is the smallest of all the blockers.

**7. The commenters win.** Precisely because the paper refuses to assert anything, the review will produce a longer list of caveats and a thinner product. *Prevention:* the next edition removes caveats as it adds evidence, and the test of success is that the number of concrete examples goes up, not that the number of words does.

**8. A number gets out and is wrong.** A model figure is quoted as a measurement, or a workshop money figure acquires a euro sign, or a dealer name is attributed to a national total. *Prevention:* the flow, measure and coverage labels travel with the number on the face of the screen, and the values that are not publishable are listed in one place the user can see.

**9. The €300,000 question never gets asked properly.** The funding paper sits beside this one, neither refers to the other, and the decision is deferred by confusion rather than by judgement. *Prevention:* decide which document is the approval paper, and put the money in it.

**10. It becomes a reporting layer with better manners.** After a year, the reviews are produced, nobody has changed a decision, and the programme is judged on the quality of the papers. *Prevention:* the paper's own test is the right one and should be applied quarterly — can you name a decision that changed because of this? If not after two quarters, the product has failed regardless of how good the paper is.

---

## W. PAGE-BY-PAGE REVIEW

| Page | Purpose | What works | Problem | Required change | Action |
|---|---|---|---|---|---|
| 1 | Cover | Named pillars, version, date, clear internal marking | Subtitle promises a product and operating specification that the pages do not deliver | Keep the cover; change the subtitle to what the document is: an evidence and operating rulebook | REWRITE |
| 2 | Executive brief | Honest about outcomes not being established; names the four commercial outcomes | This is the page management reads and it contains no ask, no number and no example | Add the two decisions being asked for and one worked case reference | REWRITE |
| 3 | Status and reading guide | Status vocabulary; explicit source boundaries; six status words | The evidence boundary is factually wrong — the draft, the master prompt and the datasets are on the same disk | Restate the boundary truthfully; list what exists and was not read | REWRITE |
| 4 | The proposition | "A decision environment, not another collection of dashboards"; three correct exclusions | No user, no example, no trigger | Add the user and a one-line example | REWRITE |
| 5 | Three pillars | Clean separation; IDS correctly not a distributor audit; PRISM boundary honestly unconfirmed | The three pillars are given equal weight when their current decision value is not equal | State the current decision value of each pillar plainly | REWRITE |
| 6 | Participation should pay back | Three-position separation of starting point, contract and proposal; the promise not to expand the ask silently | Honesty reads as hedging; the real conclusion is buried; no tiering, no numbers | Lead with the finding that the current arrangement produces a file and not a good one | REWRITE |
| 7 | The monthly distributor return | Core versus conditional returns; a stable result or explicit limitation is a valid outcome | A process description where a benefit should be; nothing a distributor would want | Replace the process list with what the distributor receives, in its own words | REWRITE |
| 8 | The response obligation | Five classes; acknowledgement is not an answer; refuses to invent response times; names the capacity problem | The most important operational chapter is buried at position eight with no names against it | Move to the executive brief; make naming the owners one of the two asks | MERGE |
| 9 | Earn additional information | Additional contribution buys a visible additional return; limitation printed beside each item | No numbered levels, no costs, no return per level | Replace with the staged exchange already written on disk | REWRITE |
| 10 | The minimum data contract | Real fields with real controls; wholesale handled correctly; revision preference | Nothing wrong. This is the best structural page in the document | Keep. Add the dealer-roster and zero-activity requirement more prominently | KEEP |
| 11 | Acceptance and corrections | A missing file is not a zero month; explicit zero; return versus correction; acceptance receipt | Long for principles that fit in fewer words | Compress; keep both slogans | MERGE |
| 12 | Evidence that can be trusted | The three flows and the ban on adding them; the five permitted interpretations of a number | This is the single most valuable page and it is buried in the middle | Move the flow diagram and the never-add rule to the executive brief | KEEP |
| 13 | Counted is not always a floor | Corrects the earlier draft's error; distinguishes counts and totals from rates and expectations | Dense; the correction is interesting internally and unnecessary for a management reader | Keep the rule, cut the story of the correction | MERGE |
| 14 | Fleet, GPS, PMS and warranty | Correct separation of the lenses; the band-file rule; warranty not maintenance history | No measured position — the reader cannot see that the model's distance assumption is contradicted | Add the measured distance position and the contradiction | REWRITE |
| 15 | Five decisions to support | Good permitted next steps; the no-quota principle | Patterns, not cases; no trigger, no size, no example | Add one fully worked case, or move this page behind the example | REWRITE |
| 16 | The standard for every finding | Excellent: scope, records, interpretation, action; the chart rules; quantity separated from price | A standard with no specimen | Add the filled-in specimen | KEEP then ADD |
| 17 | Genuine, BVP and market evidence | Best paragraph in the paper: normalising a competitor observation; no validated match means no recommendation | The dataset exists on disk with 16 matched part numbers and a computed index, and the page implies it does not | Publish the matched set | REWRITE |
| 18 | Pricing precision is a decision process | Four routes; correct commercial basis rules; the system does not set prices | No simulation, no volume response, no example | Add the price lab specification and one routing example | REWRITE |
| 19 | Gross profit and the review basis | Correct formulas including the break-even quantity; substitution not double counted; no invented causes | The only financial page in a paper that asks for money | Add the baseline definition, the support-cost model and the outcome method | REWRITE |
| 20 | Identity, accounts and IDS | Correct four-entity distinction; the one-column request; assessment attaching only through a validated relationship | The measured state of the join is missing, so the biggest blocker is invisible | Print the measured position: blank columns, unmapped accounts, match rates | REWRITE |
| 21 | Two pilots, different proofs | Refuses false symmetry; correct prohibitions | Both markets' real limits are unstated | Add the measured availability for each pilot | REWRITE |
| 22 | A worked scope decision: Portugal | Genuinely useful; a decision made from evidence and correctly bounded | It is a scope decision, not a commercial case, and the paper presents it as the example | Relabel it and add a real commercial case | KEEP then ADD |
| 23 | The workspace experience | Eight interaction rules better than most shipped products: context preserved, basis visible, five-state distinction, review leads somewhere | The illustration is a data-flow diagram; there is no screen | Replace with one real screen | REWRITE |
| 24 | Logical data architecture | Correct join rules; no invented volume; versions that explain a result | Standard good practice, not a differentiator | Keep short | KEEP |
| 25 | Registers that make claims reviewable | Real and worth building: source, metric, claim, capability, decision | Five registers with no owner for keeping them current | Add the owner and the cadence, or cut to three | REWRITE |
| 26 | Governance, access and release | Honest that there is no host and the folder is not safe to publish; correct on imported text not being instructions | No names, no dates, no consequences | Keep the honesty; move the two blocking asks to the front | KEEP |
| 27 | Delivery gates | Bounded decisions; the continue-work rule; distinguishes a requirement from a demonstration | One gate per page of its own would be better than four in a table | Keep the continue-work rule, which is the valuable part | MERGE |
| 28 | Acceptance tests that protect trust | Good test list: duplicate, revision, missing versus zero, multi-band, unit gap, unvalidated match, access | A specification with no executed test | Execute three of them and print the results | KEEP then ADD |
| 29 | Open decisions: evidence and identity | Real decisions with real consequences; smallest closure stated; bounded effect stated | No owner, no date, no consequence if unanswered | Name an owner and a date, or state that the decision is being escalated | REWRITE |
| 30 | Open decisions: service and release | Correct that a document cannot create an appointment; correct on the resource envelope | The money is here in the abstract and nowhere in the paper | Add the ceiling and the staged release, or point at the document that holds them | REWRITE |
| 31 | Success and the next milestone | Three separate success dimensions; the independent reader test; the right milestone | No numeric criterion of any kind; the reader test is pending | Set the go/no-go criteria and run the reader test | REWRITE |
| 32 | Definitions | Careful, consistent, one meaning per label | A few internal artefacts named without definition | Finish the glosses | KEEP |
| 33 | Source register and decision trail | Hashes present and correct; lineage traced; says what was not inspected | Claims the draft was not supplied; omits six documents that were | Correct the register | REWRITE |
| 34 | What changed in v0.2 | Honest about what is and is not claimed | Lists document revisions where a reader wants to know what changed for the business | Keep, but in an annex | MERGE |

**Count:** KEEP 4, KEEP then ADD 3, REWRITE 17, MERGE 6, REMOVE 0, ADD elsewhere 1. Nothing in this paper should be deleted outright. The problem is not what is in it; it is what is missing from it.

---

## X. WHAT TO REMOVE

The instruction was not to lengthen the document. These are the things that dilute it.

**The self-referential status apparatus.** Pages 3, 25 and 34 spend roughly three pages telling the reader what the document is, what it was built from, what it does not claim, and what changed. A management reader needs one paragraph of that. The rest belongs in an annex for the reviewer.

**The running argument with v0.1.** Page 13's explanation of which earlier generalisation was wrong, the repeated source notes distinguishing retained material from additions, and the "v0.2 proposal" tags throughout are internal working notes. They cost space on every page and they tell a business reader that they are reading a document written for its author's protection.

**The five registers reduced to three.** Source, metric and claim registers earn their keep. Capability and decision registers duplicate what the delivery gates and the open-decisions pages already say.

**The three-pillar equivalence framing.** PRISM cannot currently produce its main output and IDS cannot currently be attached to a period. Presenting them as equal pillars overstates the product. Say what each contributes today.

**The analogy-heavy opening.** "From parts data to accountable commercial action" and the loop diagram are acceptable; the layered illustration on page 23 is not, because it shows data layers where a screen should be.

**Nothing should be deleted from the evidence rules.** Protect pages 10 to 14 and 16.

---

## Y. WHAT IS MISSING

Ranked by how much each would change the document.

1. **A decision rule.** What surfaces, at what size, ranked how, capped at how many items.
2. **One worked commercial case, filled in.** Warrington, section O, is ready to use.
3. **The elimination sequence.** Seven or eight tests that kill an alternative explanation before a price conclusion is permitted.
4. **A baseline definition.** Actual prior period, last approved version, or forecast — the paper must choose.
5. **A volume-response assumption, however crude.** Even a stated planning assumption with its source, or an explicit statement that no response is assumed and the decision rests on judgement. Silence is worse than a bad assumption, because a bad assumption can be argued with.
6. **An outcome measurement method.** Treated family against a comparable control family, agreed before the intervention.
7. **The coverage panel** with named dimensions, shown on every finding.
8. **One screen.**
9. **Users and their tasks**, by role, with what each stops doing.
10. **Cost and effort**, or an explicit pointer to where that decision lives.
11. **Failure and stop conditions.** The paper has delivery gates and no stop rule. It should say what result would cause ISZE to abandon this.
12. **A data dictionary tie-out.** The paper states the requirement that every quantitative claim carry a retrievable source, and it does not apply that to its own two pilot contracts' field lists.
13. **The measured state of every blocker**, in the same place. The paper's own principle is that coverage needs a mechanism; the open-decisions table is the right place and it currently has no numbers.
14. **A short note on what happens if nothing is built.** The strongest comparator a controller will raise, and it is absent.

---

## Z. RECOMMENDED STRUCTURE FOR THE NEXT EDITION

Fourteen pages. Rewritten as a narrative, not a rearrangement. Every page ends in a decision or a question somebody owns.

**Page 1 — Cover and the ask.** *Central message:* we are asking for two decisions and we can show one worked case today. *Content:* the two asks — assign a named person with time for each response class, and send the one-column account-number request — plus a one-line statement of what Universe is and what this document is not. *Visual:* the ask box, nothing else. *Decision created:* the reader knows what they are being asked for before they turn the page.

**Page 2 — The worked case, in full.** *Central message:* this is what a Universe finding looks like. *Content:* section O as written — the Warrington fastener stop, the five numbers, the family around them, the elimination record, the surviving explanation, the recommended action, and the honest non-conclusion. *Visual:* the opportunity page itself. *Decision created:* the reader either finds it useful or does not, and either answer is evidence.

**Page 3 — What changed because we looked.** *Central message:* the first run produced real findings at real part numbers. *Content:* the price position table from section D.8 with its index against genuine and non-genuine references; the family-definition sensitivity on the Portuguese file; the supersession-remapping finding; the identity blockers at their measured size. *Visual:* the price corridor for the six matched families, with our position marked and both reference levels visible. *Decision created:* a recognisable commercial question that somebody wants answered.

**Page 4 — The problem and the consequence.** *Central message:* the data exists in fragments and every commercial question is rebuilt by hand. *Content:* the three flows and why they are never added; what is in each; the coverage measured against the billed book; the identity gap at its measured size. *Visual:* the three flows with coverage labelled on each, and the blocked join marked where it breaks. *Decision created:* agreement that the problem is real and is not a reporting problem.

**Page 5 — The product, in one screen.** *Central message:* here is what the user opens. *Content:* the screen from section O, annotated once with what each panel is for. *Visual:* the screen. *Decision created:* a product-shaped conversation rather than a data-shaped one.

**Page 6 — How a finding is produced and when it is suppressed.** *Central message:* the engine has rules and they are written down. *Content:* the surface rule with its floor and its cap; the elimination sequence; the check panel; the four statuses and how they follow from the panel; the suppression list. *Visual:* a decision tree, signal in, action or no-action out. *Decision created:* the reader can argue with a specific rule instead of with the concept.

**Page 7 — Pricing, honestly.** *Central message:* we can tell you where we sit; we cannot tell you what happens if we move. *Content:* the routing table; the commercial basis rules; the gross-profit formulas including break-even; an explicit statement of the volume-response assumption used or the admission that none exists. *Visual:* the price corridor again with the break-even overlay, showing what volume would be needed and labelling clearly that it is not a forecast. *Decision created:* agreement on the volume assumption, or on who provides one.

**Page 8 — Who this is for.** *Central message:* four named jobs do one thing differently. *Content:* the parts analyst, the pricing owner, the distributor's parts manager, the commercial owner; for each, the task and the task that disappears. *Visual:* a small before-and-after per role. *Decision created:* each reader finds themselves or does not.

**Page 9 — What the distributor gets, and what it costs.** *Central message:* a staged exchange with a defined return at each level. *Content:* the five levels with what each buys and what each costs the distributor; the minimum ask of three things; the finding that the current arrangement produces a file and not a good one. *Visual:* the exchange table. *Decision created:* approval of the offer to be made.

**Page 10 — What we know, what we infer, what we do not know.** *Central message:* the evidence position in one place. *Content:* measured versus modelled versus inferred, with the measured state of every blocker in a single table. *Visual:* a coverage bar per source. *Decision created:* no reader can leave believing a modelled number is a measured one.

**Page 11 — The pilots.** *Central message:* two markets, two different proofs, and here is what each can and cannot show. *Content:* section R, with the participant names. *Visual:* two columns, capability against limitation. *Decision created:* the pilots are agreed with their limits attached.

**Page 12 — What it costs and what we would stop.** *Central message:* the ceiling, the stages and the stop condition. *Content:* the ceiling and its staged release; the effort order of magnitude labelled as an estimate; the two comparables and why neither is a return; the conditions including the ones no analysis can close; and the result that would make us stop. *Visual:* the release ladder with the stop condition marked. *Decision created:* the funding decision, framed so it can be answered.

**Page 13 — The next ninety days.** *Central message:* what happens, by whom, by when. *Content:* one page of dates and names — the one-column request sent, the classification release pinned, the currency declared, the response owners named, the first review produced, the first question answered, the first correction processed. *Visual:* a simple dated list. *Decision created:* commitment.

**Page 14 — Annex: how to check a number.** *Central message:* nothing in this document needs to be taken on trust. *Content:* source, metric and claim registers; the definitions; the source register including the files that exist and were not read; the page-by-page evidence trail. *Decision created:* none. It is for the reader who wants to check.

---

## FINAL TEST

### "Show me exactly how Universe helps me earn more money or prevent lost sales next month."

Nine days after you say go, here is what happens. Somebody opens the ITUK dealer file and the price comparison file together and puts them on the screen in section O. Three things come out of it.

First, the air and oil filters. Sixteen part numbers where we have a real matched competitor observation, and on four of them we sit below the comparable genuine reference while on the same part numbers we sit well above the cheaper equivalent. That produces a named list of part numbers with a price question attached to each, and a rule for which reference applies. It is small and it is real, and it is the kind of thing a pricing owner can act on this month.

Second, the Warrington fastener stop. Five part numbers where an account bought 452 units in six months and 40 in the next six while the family around them kept running. Nobody was looking at it. It might be a stocking cycle and it might be work moving elsewhere, and either way the answer is worth having.

Third, the Portuguese family definition. The same oil filter family measured three ways on the same file gives totals that differ by more than half. That is not a sales finding; it is worse, because it means every family number in that market is arguable until it is settled.

That is three specific things, worth a defined amount of gross profit on the price list and an unknown amount on the account question. It is not a claim of recovered revenue and it does not need to be. What it prevents is the thing that actually costs money here: a question that nobody was in a position to ask.

### "What can Universe prove today, what can it infer, and what does it still not know?"

**Can prove today.** What ISZE billed to each distributor, by part number, family and month, for about three and a half years across twenty-two distributors. What one distributor's sixty-four named dealers bought from it, by part number and month, for calendar 2025. That the Portuguese national file has no dealer name in it anywhere. That the two columns a dealer-to-account join needs are blank on every one of 66,018 rows, and that none of three buying accounts maps to a dealer site. That on sixteen part numbers we can place our dealer price against a competitor's genuine and non-genuine listing on a stated date with a stated index. That a real account bought 452 units of five fastener numbers and then 40, while the family around them continued. That family totals move by more than half depending on the definition. That the workshop workbook declares no currency. That the dealer self-assessment round has one round and no per-dealer date.

**Can infer, with limits.** That a market buying only the alternative part number and never the genuine one is making a range or channel decision rather than a price decision. That a decline confined to two months and one account is more likely a stocking or ordering event than a demand change. That a part number with volume for two months and then nothing is a supersession, not a mix decision. That a market's spend per truck well below comparable markets suggests an offer problem, while accepting that the ceiling it is measured against is modelled and partly flat.

**Does not know, and should say so on the screen.** Whether a dealer-level rate per vehicle is good, bad or normal, because no dealer-level fleet exists anywhere. Whether a stock position caused an ordering gap, because there is no stock file. Whether a competitor observation reflects what anyone actually paid. Whether a price change would recover volume, to any degree. Whether a service interval is being met, because the schedule is unapproved. Whether an intervention worked, because there is no control and no baseline. What a dealer sold onward. Whether the current level of support activity is adequate, because nobody has measured how many questions are asked or how long they take to answer.

### "What is the single most important thing to build first?"

The opportunity page, filled in, for the Warrington case, with the elimination record on it. Not the platform, not the data pipeline, not the registers. One page, one real case, produced end to end from source, showing what was measured, what was tested, which explanations were eliminated and which survived, and what the reader should do next.

The reason is not that it is quick, although it is. It is that this single page forces every unanswered question in this review to be answered. To fill it you must define what makes a case surface, how large it has to be, what gets tested and in what order, how confidence is shown, what the recommended action looks like, who owns it and how it will be measured afterwards. Every one of those is currently missing from a 34-page specification, and all of them fall out of building one honest page.

Everything else in this document — the flows, the coverage rules, the registers, the data contract — is scaffolding around that page. The scaffolding is already good enough. The page does not exist.

### "What should we absolutely avoid building?"

**Anything that scores or ranks the network.** Dealer rankings, league tables, composite dealer scores, a "weak dealers" view. The paper already bans these and the ban must hold, because the data cannot support them: no dealer-level fleet, no second year, no validated identity, and a self-assessment with no independent rating. A ranking built on this data would be a ranking of dealer size wearing a performance label.

**Anything that changes a price.** No automatic price setting, no optimisation, no dynamic pricing. The paper says this and it is right, and the reason is worth restating: there is no volume response assumption, so an optimiser would be optimising against nothing.

**A general-purpose data portal.** No ERP replacement, no warehouse, no all-purpose search across the estate. The paper's own line — a decision environment, not another collection of dashboards — is the correct boundary, and it is the boundary that will be lost first if the product is driven by requests rather than by cases.

**Dealer-facing pages, before there is a validated relationship.** The paper is unusually good on this: there is no host, no authentication, and the folder as it stands contains material that would be wrong to publish. A dealer page built now would either show an account total repeated across sites or a national total attributed to a name, and both would be worse than showing nothing.

**The service-demand model, until the schedule is approved.** A modelled consumption estimate resting on an unapproved interval and a flat distance assumption that the programme's own measurements contradict will be quoted as a measurement within a month of being published.

**Any new platform decision.** No hosting, no framework, no database, no user accounts — until one page and one case are agreed and somebody has used them. The paper already says the choice of storage platform is a separate decision. It should say it louder, because that is the decision that will consume the next six months if it is taken first.

---

## One last thing, which belongs in the review rather than in the response

The most striking fact in this whole exercise is not in the paper. It is that four documents written on the same evening describe the same product, and not one of them knows about the others.

There is a 34-page specification that describes the rules and cannot show a case. There is a 15,000-word draft that has the case, the figures and the decision patterns, and is never mentioned. There is a value-exchange model with a proper five-level ladder and a worked dealer example, and it is never mentioned. There is a funding paper with a ceiling, staged release and two refusals to invent a return, written on the same evening and never mentioned. And there is a delivery road map, 53,000 words of it, with the gates, the acceptance tests, the owners, the costs and the pilot design — which is the document that actually answers most of the questions this review was asked to raise.

The specification's own front matter says its purpose is to make the relationship between a claim, its evidence and the next decision explicit. The most useful thing anyone could do next is apply that standard to the folder rather than to the paper: say which of these five documents is the one ISZE is working from, and delete the other four from the decision path.

---

*Review written 22 September 2026. Nothing was rebuilt, regenerated, sent or overwritten to produce it. The only files written were this review and three temporary scripts outside the workspace.*

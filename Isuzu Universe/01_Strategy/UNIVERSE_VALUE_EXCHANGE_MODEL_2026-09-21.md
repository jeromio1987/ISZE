# Isuzu Universe — the value-exchange model

**Prepared:** 21 September 2026
**Status:** design proposal. Internal. Nothing on disk was changed to produce it.
**Purpose:** define what each participant gives, what Universe adds, what comes back, which decision improves, and why they contribute again — level by level, with a data dividend attached to every contribution.

---

## 1. The starting principle

The existing distributor kickback requirement starts the data exchange. It gets us a file with dealer, part number, period and quantity. It does not get us a file anyone cares about, and a file sent to satisfy a condition is the minimum that satisfies the condition.

ITUK calendar 2025 is the proof. That file exists because it had to. It carries 64 named dealers and 224,001 units of parts — enough to paint a map, not enough to join to the dealer standards round, and no prices, no vehicle, no reason codes. It is a compliant file.

So the design has to do two separate jobs:

1. Keep the obligation for the one file nobody would send voluntarily.
2. Make every level above that worth sending for the contributor's own reasons.

Universe earns data by being useful, not by being mandatory. The obligation opens the door; the return is what keeps the participant in the room.

### The three motors of participation

| Motor | How it works | How strong it is |
|---|---|---|
| **Requirement** | The kickback condition. Buys frequency and coverage. | Strong enough to get a file. Not strong enough to get a good one. |
| **Self-interest** | The parts team already has to explain its own numbers every month. If Universe assembles that explanation, contributing is cheaper than the spreadsheet. | Strong, recurring, and the main engine. |
| **Defensive** | A reason code saying "the customer bought elsewhere at a lower price" protects the parts manager from being read as a weak seller. | Underrated. This is what keeps the file coming in month six. |

---

## 2. Capabilities are not evidence layers

Pillars and evidence layers are different things and should not be counted together.

**Capabilities** own a calculation and have one accountable owner:

| Capability | What it owns | Its unique question |
|---|---|---|
| **AIM** — Aftermarket Intelligence Model | The parts classification and the family / Genuine-versus-BVP view | What did we sell, in which family, at which tier? |
| **IDS** — Isuzu Dealer Standards | The 2026 dealer self-assessment round and the improvement conversation | What did the dealer record about itself, and what did we agree to do about it? |
| **PRISM** | The validated commercial calculations: parts billed, modelled expected demand, mix, replenishment signals | Is the commercial evidence strong enough to act on? |

**Evidence layers** are inputs any capability may read. They do not each need to become a pillar:

- distributor aftermarket intelligence (sales to dealer and whatever the distributor already reports internally)
- observed public competitor pricing
- tender and quotation intelligence
- future operational data (stock, backorders, workshop)

**Universe itself is neither.** It holds the shared parts: context that follows the user between views, navigation, permission boundaries, the evidence record behind each number, and the follow-through on agreed actions. It coordinates; it does not own a calculation.

If every layer becomes a pillar, the result is a diagram nobody can act on and three teams arguing about ownership of the same number.

---

## 3. The exchange, participant by participant

For each participant: what they contribute, what Universe adds to it, what they receive back, which decision improves, and why they contribute again.

### 3.1 ISZE

**Contributes.** Parts billing to distributors (complete to 30 June 2026), the parts classification, the fleet by market and weight class, the 2026 dealer self-assessment round, modelled expected demand, observed market price references, the tender feed, the funding, and the method for the whole exchange.

**What Universe adds.** The only thing we do not have: a common language between those sources, and comparability between markets on a stated basis. Today each source is read in its own file by its own owner, on its own clock. Universe puts a distributor, a period, a family and a measurement basis in one place and keeps them there.

**Receives back.** Dealer-level demand below the distributor. Reason codes behind movement. A validated dealer identity map. Coverage statements that say what we do not know.

**Decision that improves.** Where to spend field effort; which support cases are worth funding; whether a range or value-tier problem is ours or the market's; whether a "gap" is a real shortfall or a missing denominator.

**Why contribute again.** It is the only route below the distributor, and the dividend ledger lets us prove the return rather than assert it.

### 3.2 Distributor management

**Contributes.** The monthly sales-to-dealer file as the condition of the kickback. The dealer-name-to-account map, once. Agreement that a reviewed brief can be taken to the dealer.

**What Universe adds.** One screen where the parts conversation, the standards results, the market references and last month's agreed actions sit side by side — with coverage and unknowns printed next to the number, not hidden in a help page.

**Receives back.** A defensible monthly dealer conversation. An evidence base for a support, stock or price request. An early warning when one dealer or one family starts moving away from the rest of the network.

**Decision that improves.** Where the month's effort and support go, and which dealer principal is worth a call this week.

**Why contribute again.** The review replaces preparation they already do, and gives them a document to walk into the dealer meeting with. That is a real reduction in duplicated work, not an added reporting obligation.

### 3.3 Distributor parts team

**Contributes.** The same file — but their stake is different, and they are the people who will actually make it accurate. Their interest is demand and availability, not management reporting.

**What Universe adds.** The part of the picture they cannot build alone:

- what we billed them against what moved onward
- which families their dealers do not buy at all
- which part numbers look short relative to their own dealers' purchasing pattern
- the observed market price reference beside our list and reference dealer price

**Receives back.** A stocking and range argument. A way to record "we could not supply this" instead of wearing it as a demand failure.

**Decision that improves.** What to hold, which range to push, and what to escalate to us.

**Why contribute again.** A backorder reason attached to a part number changes the conversation from blame to a supply question. That is worth ten minutes of typing every month.

### 3.4 Dealer principal / aftersales manager

**Contributes.** Validated site identity. Correction of their own record. The agreed improvement actions with an owner and a date. Later, and optionally, the dealership's own service population.

**What Universe adds.** The dealer's own purchasing pattern placed against comparable dealers on a stated basis. Its own self-assessment in context rather than as a score appearing out of nowhere. Visible follow-through on the action agreed at the previous review.

**Receives back.** One owned action per review, and sight of whether the last one moved the number.

**Decision that improves.** Which improvement to run next. Whether to ask the distributor for support, stock or price. Whether the workshop is genuinely under-served or simply small.

**Why contribute again.** They leave each review with something they chose, and the previous one is visibly being tracked. That is the difference between a review and an inspection.

### 3.5 Dealer parts manager

**Contributes.** Small, frequent context, which is the only kind of context a counter can produce:

- what was out of stock
- what a customer bought elsewhere, and roughly at what price
- where a part did not fit the vehicle
- which local quotes or tenders are live

**What Universe adds.** The local frame: the parts this counter should be moving, the jobs worth chasing, and a record that goes somewhere.

**Receives back.** A short counter-relevant list — and the knowledge that reporting friction produces a response rather than a form.

**Decision that improves.** What to order next. Which quote to defend. When to offer the value-tier part instead of holding out for genuine.

**Why contribute again.** The alternative — saying nothing — keeps getting them judged on demand they never had.

### The asymmetry worth designing around

The person who benefits most from levels 2 to 4 is rarely the person who can authorise them. The parts team and the counter gain; management and the principal grant permission. So each level's dividend has to be aimed at whoever has to say yes to the next level — not only at the person who does the work.

---

## 4. The progressive participation model

**Rule for every level:** a participant sees the whole review experience. The depth of the dealer and reason picture unlocks as they contribute. Nothing is hidden out of spite — the deeper views cannot be computed from less data.

### Level 0 — ISZE data only

**What useful Universe experience can we already provide without asking for anything new?**

- Parts billed against target spend per truck, by distributor and period
- Family mix, and the genuine versus value-tier split
- The distributor's own dealer self-assessment results, with the assessed population and round stated
- Position against comparable markets, on a stated basis
- The tender panel for the participant's country and segment

For ITUK specifically, we can also show the 2025 named-dealer picture we already hold. That is a real experience on day one and a deliberate demonstration of what the format is worth — "this is what you get when the file has dealer names."

Level 0 must be genuinely useful, not a teaser. A participant who finds level 0 thin has no reason to believe level 1 will be better.

### Level 1 — sales to dealer

**The ask:** dealer identifier, part number, quantity, reporting period. **No prices.**

**What unlocks:**

- What share of what we billed actually moved onward, by dealer and by family
- A stocking position by dealer and family
- Part-number level demand below the distributor
- Once a location attaches to a dealer, the geographic weak-spot picture — a dealer cluster buying nothing in a family while neighbours buy. A national total can never show this.

**Why excluding prices is deliberate.** It removes the distributor's margin exposure, keeps us out of rebuilding their price list, and still buys the map. Prices are the field we least need and the one they most resist.

### Level 2 — dealer and network identity

**The ask:** validated account and site relationships, and an approved link to the dealer standards round.

**What unlocks:**

- One dealer review rather than two selections: this account's parts pattern and its own self-assessment in the same place
- Multi-site accounts handled honestly instead of double-counted across site markers
- Unmapped accounts kept visible in a list and in the correct totals

**The honest position.** This link does not work today. For ITUK, of the 64 sales-file dealer names, roughly 16 match the standards network exactly after normalisation, about 34 reach a strong name overlap, and about 20 have no plausible match. The sales names carry branch suffixes the standards list splits into separate rows.

Level 2 is where the distributor fixes that — and it is in their interest to, because the alternative is being described by a dealer list that does not reconcile with their own.

### Level 3 — commercial context

**The ask:** structured explanations rather than documents —

- competitor price quote
- availability or backorder situation
- tender or quotation involvement
- customer requirement
- existing stock
- application or fitment mismatch

**What unlocks:** the reason behind a movement. Not "this family is down 12%" but "this family is down 12%, of which roughly half is a price difference, a third is supply, and the rest is demand." Over a few cycles this becomes a reason library.

A reason library is information no single participant can build alone. It needs the parts-billed side as well as the distributor's side, and it needs consistency across periods.

### Level 4 — optional operational information

Assessed honestly, one item at a time:

**Backorders — worth asking for now.** The highest-value operational ask on the list. The format already exists in the workspace: forty dated open-order files for Ireland, weekly from late October 2025 to August 2026, each carrying part number, open quantity, required delivery date, ETA and a supplier note. That converts a missing purchase into a supply fact.

**Stock and inventory position — not yet.** There is no stock measure anywhere in the workspace today, only a comparison of what we billed against what moved on. High sensitivity on their side, no engine on ours to use it. Asking early teaches the distributor that contributing costs more than it returns, and that lesson is expensive to reverse.

**Dealer fleet / service population — the highest-value long-term ask, and not one to request from the distributor.** It is the only thing that would let us distinguish a small dealer from a weak one, and no dealer-level fleet exists anywhere today. It should be built jointly with the dealers who benefit from being measured fairly. Allocating a national fleet across dealers would be worse than having no denominator at all, because it would look like one.

**Workshop and service activity — later, and only on a trigger.** Open the discussion after two completed reviews produce a repeated, decision-relevant question that genuinely needs service evidence and cannot be answered another way. Warranty-linked odometer readings are not that evidence: they cover a biased minority of vehicles, mix very different duty cycles, and have been misread before. Keep them out of any dealer-level claim.

**Local competitor information and tender/quotation feedback — light, optional, never a condition.** The moment tender feedback or reason codes become a condition of access to the parts review, the review stops being a product and becomes a form.

### Level summary

| Level | The ask | What it unlocks | Who it is really for |
|---|---|---|---|
| 0 | Nothing new | Billing, mix, tier, standards, market comparison, tenders; ITUK 2025 dealer map as demonstration | Distributor management |
| 1 | Dealer + part + quantity + period, no prices | Movement onward, stocking position, geographic weak spots | Distributor parts team |
| 2 | Validated account/site relationships, approved standards link | One connected dealer review, honest multi-site handling, visible unmapped accounts | Dealer principal, distributor management |
| 3 | Structured reasons: price, availability, tender, customer requirement, stock, fitment | The reason behind the movement; a reason library over time | Distributor parts team, dealer principal |
| 4 | Backorders first; fleet/service population with the dealer; workshop only on a trigger | Missing purchase becomes a supply fact; per-vehicle rates; service explanation | Dealer parts manager, dealer principal |

---

## 5. The data dividend

Every additional contribution must generate an identifiable return to the contributor. Three rules make a dividend real rather than declared.

**Rule 1 — it lands in the same cycle.** If a reason code is entered in September, the September review shows what it changed. A dividend delivered in quarter three for a contribution made in January is not a dividend; it is a promise.

**Rule 2 — it attaches to a decision, not a chart.** Every contribution must answer "so what do I do differently", in one sentence, in the place where the contribution was made. A new view is not a dividend.

**Rule 3 — the contributor can audit it.** Keep a plain, per-participant list: what they gave, what was returned, and which of their own decisions it touched. That is also how we prove internally that the return is real. It is what lets the exchange survive a change of distributor staff, which is when most data programmes quietly die.

**Three kinds of dividend**, and each level should carry all three:

| Kind | What it is | Example |
|---|---|---|
| **Immediate** | Visible in this cycle | The map lights up once locations are supplied |
| **Compounding** | Only exists because others also contributed | Comparable dealers; the reason library; a shared dealer identity |
| **Defensive** | What the contribution stops | A validated list stops a third of the network being described wrongly; a backorder note stops a supply failure being read as a sales failure |

The defensive dividend is the one that gets left out of most exchange designs and the one that keeps contributors in.

---

## 6. The rule that governs every ask

**Do not request a field unless you can complete:**

> "If the participant gives Universe X, Universe can return Y, which helps them decide Z."

Every request we are actually making, completed:

| If they give | Universe returns | Which helps them decide |
|---|---|---|
| Dealer, part, period, quantity | What share of our billing moved onward, by dealer and family | Where to focus the month's effort |
| A location per dealer | Purchasing activity mapped across the network, with unmapped accounts kept in the totals | Which area to visit or support next |
| Dealer-name-to-account map | Per-dealer movement of what we billed, and a dealer review that reconciles | Whether a dealer is short of parts or short of demand |
| Approved dealer-to-standards link | Parts pattern and the dealer's own self-assessment in one view | Which improvement to run next |
| A reason code on a movement | The split between price, supply and demand behind the change | Whether to ask us for price support or stock |
| Backorder lines against a part | A missing purchase reclassified as a supply fact | Whether to escalate supply rather than push the dealer |
| Jointly built dealer service population | Activity measured per vehicle instead of in absolute units | Whether a dealer is small or genuinely weak |
| One agreed action per review | Visible follow-through, and its effect by the next cycle | Whether to continue, change or drop the action |

Everything in that table is a decision. Anything that only produces a view does not belong in the exchange yet.

---

## 7. Minimum viable exchange

**Ask for exactly three things, and nothing else:**

1. **The monthly file** — dealer identifier, part number, period, quantity, no prices, in a stable agreed format. One recurring ask, with notification when coverage changes.
2. **The dealer-name-to-account map** — once. It closes a gap that currently blocks per-dealer sell-through anywhere in the business.
3. **One agreed action per review** — with an owner and a date, captured during the meeting rather than reconstructed afterwards.

Everything else — reason codes, backorders, stock, tender feedback, fleet — is invited, not required.

**Give back:** the level 0 and level 1 experience, and the action record. Parts billed against target spend per truck, family mix, genuine versus value tier, the dealer map, the pipeline signal, and one action logged with its evidence. Not a demonstration — a working monthly review for one market.

**Then prove it.** Take one review task — find and explain a supported change in one family for one dealer — and compare it against the current email-and-spreadsheet route on time spent and correctness, including whether the user can tell a modelled value from a measured one.

---

## 8. Strongest long-term exchange

The strongest version is not more fields. It is the point at which Universe becomes the only place where three things live together:

- the **validated dealer identity** (which account is which site, approved by the business)
- the **reason behind each movement** (price, supply, demand, fitment, tender, customer requirement)
- the **action history with its review** (what was agreed, by whom, and what happened next)

Once the reason library and the dealer-validated population exist, a distributor that stops contributing does not merely lose access to a dashboard. It loses the record of why its own numbers moved. That is the real lock-in, and it is a fair one, because the record is theirs and it is portable back to them.

**The asks that get you there:** the monthly file at a specified quality, the dealer map, structured reason codes, backorder lines, and a dealer service population built jointly with the dealers rather than about them.

**The commercial return still comes through actions, never through charging for data access:** better targeted support, better placement of genuine versus value tier, focused effort on genuinely weak areas, fewer repeat standards failures, and tenders with real parts content. A data-access fee would turn Universe into a tollbooth and destroy the voluntary contribution above level 1.

---

## 9. What we should explicitly avoid asking for now

| Avoid | Why |
|---|---|
| Prices on the sales-to-dealer file | Exposes their margin, invites us to rebuild their price list, and we have already undertaken not to collect dealer resale margin. |
| Dealer resale prices, or anything implying a required resale price | Monitoring and reporting is one thing. Anything that reads as price coordination is a legal and relationship risk with no upside. |
| Full stock and inventory valuation at entry | High sensitivity on their side, no engine on ours to use it, and it would be the first contribution we cannot pay back. |
| Warranty odometer as a fleet or service-population source | Biased sample, duty cycles differing by an order of magnitude, and a history of being misread as fleet truth. |
| Dealer-level trucks-in-service derived by allocating a national fleet | It looks like a denominator and is not one. It would let us rank a small dealer as weak and defend that with a fabricated number. |
| Individual customer or VIN-level detail, and workshop job cards, before a repeated question needs them | Not needed for the first useful release, and expensive in trust if requested early. |
| Tender feedback as a condition of anything | Turns a useful alarm panel into a compliance chore. |
| Any standards or improvement compliance scorecard, or dealer league table | Turns the improvement conversation into a scoreboard, and kills the reason a dealer principal would participate. |
| Uploaded row counts, login counts, or "reference-price value of workshop lines" as benefit measures | None of these is incremental gross profit, and each one rewards volume of typing over quality of decision. |

---

## 10. Known weaknesses this design does not fix

State these plainly, because a promise made to a distributor depends on them and the exchange design does not make them true:

- **The parts classification has a corrected rebuild dated 20 September 2026.** About 2,700 part numbers had drifted from their source, including air-cleaner elements worth roughly €1.16M filed in the wrong family. Any label shown to a distributor must pin the release file and its build date.
- **The service intervals behind every demand percentage are stated assumptions, not measurements.** One file controls all of them. Parts actually sold are real; the demand they are measured against is modelled on placeholder factors.
- **The value figures on the dealer file are a reference valuation** at our own billed average prices, unvalued on between 0% and about 24% of a dealer's quantity (5.5% average). They are never invoiced money, and dealers are not understated equally.
- **One pipeline check is currently failing** on a €5.51M gap between two derived totals. Any headline euro figure must be traced to its own source until that is resolved.
- **There is one dealer standards round only, and no per-dealer assessment date.** A "what changed since last time" view does not exist and cannot be promised.
- **No dealer-level fleet exists anywhere,** so no per-dealer rate can be computed honestly today.
- **The dealer-to-account map does not exist,** which is why it is a level 2 ask rather than a level 0 feature.

The exchange design does not depend on these being fixed first. Any promise made to a distributor does.

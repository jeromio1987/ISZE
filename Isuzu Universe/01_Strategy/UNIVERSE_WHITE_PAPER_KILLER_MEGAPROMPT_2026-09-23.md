# ISUZU UNIVERSE — WHITE PAPER MEGAPROMPT

**Purpose:** instruct an AI to write one definitive Isuzu Universe white paper that takes the best of every
earlier edition, organised around five pillars — **AIM, IDS, PRISM, DLOD and Tenders** — complete with an
index, figures and tables, in the house red and charcoal style.
**Written:** 23 September 2026. Supersedes the megaprompt of 22 September 2026.
**Audience of the resulting paper:** shared / external (management, and possibly distributors). Not an
internal note.
**Audience of this prompt:** internal. It may name files, tools and internal distinctions.

---

## 0. HOW TO USE THIS PROMPT

Paste it whole into the AI, then attach or grant access to the folder
`C:\Users\jerom\Desktop\claude\ISZE\Isuzu Universe\`.

If the AI cannot read the folder, it must say so before writing a single word and ask for the files it
needs. It must never write document-specific judgments from memory of an older conversation, and it must
never claim to have reviewed a file it could not open.

Do not let it stop at an outline. The deliverable is the finished paper, rendered and inspected.

---

## 1. YOUR ROLE

Act as one person wearing five hats, in this order of priority:

1. **White-paper editor** writing for a management reader who has twenty minutes.
2. **Parts commercial strategist** who knows how a distributor's parts manager actually thinks.
3. **Evidence auditor** who will not print a number he cannot defend to the person who owns the source.
4. **Product designer** who can describe what a user sees on a screen without inventing a system that exists.
5. **Data-visualisation designer** who builds figures that answer a question rather than decorate a page.

You are not a copywriter and not a proofreader. You are deciding what is true, what is worth saying, and
what the reader should see.

---

## 2. THE ONE-SENTENCE JOB

Write a single definitive Isuzu Universe white paper that explains what the programme is, proves it with the
best material from every earlier edition, organises it around five pillars, illustrates it with real worked
examples, and carries an index — in the house red and charcoal style — so that a management reader finishes
it understanding exactly what to approve and what remains unproven.

Before you build anything, write that sentence back in your own words at the top of your working file. If
what you are about to produce would not satisfy it, stop and say so.

---

## 3. READ THESE FILES FIRST — AND SAY WHAT YOU READ

Older papers exist. Your job is to take the best of **all** of them, not to start clean and not to copy the
newest one. Read these before you form an opinion. Then list, at the top of your working file, which you
opened and which you could not.

### 3.1 The current edition, and what is already settled

| File | What it is | What to take from it |
|---|---|---|
| `01_Strategy\ISUZU_UNIVERSE_3_0_2026-09-23.md` | The current 25-page vision and participation paper | The scope boundary, the five-tool portfolio, the participation assessment, the money chapter, the four evidence labels |
| `01_Strategy\ISUZU_UNIVERSE_3_0_ANNEX_2026-09-23.md` | 15-page companion | The tender framework, the IDS Studio in full, the reference rules on measures, periods and identities |
| `_build_30\ISUZU_UNIVERSE_3_0.html` and `_build_30\figures.py` | How the current edition is built and how its charts are generated | The house palette, the chart construction, the fact that figures are generated from source at build time |

### 3.2 The earlier papers — where the good writing and the hard thinking live

| File | What it is | What to take from it |
|---|---|---|
| `ISUZU_UNIVERSE_WHITE_PAPER_2026-09-21.pdf` (58 pages) | The first full white paper, clean | Its analytical-rules chapters, its glossary, its acceptance tests and its field catalogue. These were called "a clearer statement of measurement discipline than the earlier internal notes" |
| `ISUZU_UNIVERSE_WHITE_PAPER_VISUAL_EDITION_2026-09-21.pdf` (71 pages) | The illustrated edition | Its figure concepts only. It carries a printing defect — every diagram is drawn twice over itself — so do not reuse its rendering |
| `ISUZU_UNIVERSE_COMMERCIAL_VISION_3_0.pdf` (80 pages, withdrawn) | The big withdrawn edition | The tender framework chapter and the full IDS chapter, which were cut for length and now live in the annex |
| `ISUZU_UNIVERSE_COMMERCIAL_TOOLS_WHITE_PAPER.pdf` (33 pages, withdrawn) | The tools edition | The **scope boundary** — the written statement that routine service is not the product. This is the single most valuable paragraph in any earlier edition |
| `01_Strategy\Universe_Yellow_Paper_v0.5_2026-09-22.md` | The product and operating paper | The worked commercial case, the written rule for what surfaces an opportunity, the go/no-go test and the stop condition |
| `01_Strategy\Universe_Yellow_Paper_COMPLETE_DRAFT_2026-09-21.md` | The long Yellow Paper draft | Its glossary definitions and its module give/ask reasoning |
| `01_Strategy\ISUZU_UNIVERSE_WHITE_PAPER_REVIEW_2026-09-21.md` | The 12-section review of the two 21 September editions | **Read this twice.** It is the reason the current edition exists |
| `01_Strategy\UNIVERSE_STRATEGY_REVIEW_CRITIQUE_2026-09-21.md` | The internal critique with the business owner's locked direction | The ITUK-pilot decision, distributors-first, the DLOD chapter, tenders inside Universe rather than beside it |
| `ISUZU_UNIVERSE_WHITE_PAPER_REVIEW_2026-09-21.md` § 5 | The credited strengths | UTI is not UMI; ITUK is not IUK; disputed figures are not repeated; the glossary; the acceptance tests |

### 3.3 The evidence base you will be held to

| File | What it is |
|---|---|
| `_MERGED_MASTER_2026-09-21\00_THE_MAP.md` | The map of the whole programme. Open first |
| `_MERGED_MASTER_2026-09-21\02_DISPUTED_CLAIMS_AND_RESOLUTIONS.md` | **Every figure in dispute, and what was decided.** Your number one reference |
| `_MERGED_MASTER_2026-09-21\04_SOURCE_MANIFEST_AND_HORIZONS.md` | Which file each measure comes from, and to what date each is valid |
| `_MERGED_MASTER_2026-09-21\05_WORKED_CASE_ITUK_CORDWALLIS.md` | The one case that is fully worked and verified |
| `_MERGED_MASTER_2026-09-21\17_WHAT_IS_IMPLEMENTABLE_NEXT.md` | What can be built now with no new permission |
| `_MERGED_MASTER_2026-09-21\19_GLOSSARY_AND_PLAIN_LANGUAGE.md` | The plain-English definitions to reuse |
| `_STRATEGY\_ORCHESTRATION\CONSOLIDATED_ITUK_2026-09-21_01\work_d_reconcile\D_CLAIM_REGISTER_2026-09-21.csv` | **The authority for disputed figures.** Not the paper, not the metrics snapshot |
| `_STRATEGY\_ORCHESTRATION\...\ITUK_CASE_2026-09-21_01\evidence\C04_verify_return.json` | The Cordwallis case, 104 checks, 0 failures |

### 3.4 The style source

`Pricing revision\ISZE_AIM_Management_20_Slides_2026-09-21.pptx` is the house style reference. Open it. The
cover combines a red panel with a charcoal field. Section 8 below gives the exact values; confirm them
against the actual file before you finalise the palette.

### 3.5 Do not re-emit

`whitepaper_megaprompt` (55 KB, 22 September 2026) already carries a long list of analytical boundaries. Reuse
its rules. Do not paste it back into the new paper, and do not let its instruction list become the paper's
structure. Those rules are tests the paper must pass, not chapters the reader should read.

---

## 4. BUILD THE MERGE LEDGER BEFORE YOU WRITE

Complete this table in your working file before drafting prose. It is the proof that you took the best of
everything rather than rewriting the newest edition.

| Element of the new paper | Comes from (file, section) | Decision | Why |
|---|---|---|---|
| e.g. The scope boundary | Tools Edition, adopted in 3.0 §1.2 | Keep verbatim | It is the paragraph that changes how a distributor reads the approach |
| e.g. The response-time obligation | First white paper, "The response ISZE owes" | Cut | It names an obligation and sets no clock; unresolved by design |
| e.g. Participation scores per step | 3.0 §8 | Keep and sharpen | It is the only place the design is argued with honestly |
| … | … | … | … |

Rules for the ledger:

- If an element existed in an earlier paper and was cut in a later one, say which and why. Do not silently
  lose good material.
- If two editions contradict each other, print the contradiction and resolve it explicitly. Never average
  them.
- If a correction was already made and verified, protect it. Do not reopen a settled correction to look
  thorough.

---

## 5. THE FIVE PILLARS

The paper is organised around five fixed pillars: **AIM, IDS, PRISM, DLOD and Tenders**. All five are
locked by the business owner. Your job is to write each one well, not to renegotiate the set.

### 5.1 AIM — the product and parts knowledge pillar

AIM is the classification that turns an original part reference into a navigable commercial range: family,
product group, detailed part type, product form. It is what lets a distributor move from "our parts business
moved" to "brake pads moved, and here is the reference behind it".

Write this pillar so it answers: what does a user do with it, what does it separate that a total cannot, and
what does it deliberately refuse to do. The refusals matter as much as the capability: a product is not an
opportunity merely because a dealer has not bought it; an element, a housing, an assembly and a kit cannot be
averaged into one unit price; a missing relationship stays a visible gap rather than a plausible guess.

**Hard constraint:** the classification release must be pinned to one named file, version and build date. An
earlier audit found roughly 2,728 part numbers disagreeing between candidate files, with no authority declared
between them.
Until one release is named, AIM is buildable inside ISZE only. Say so.

### 5.2 IDS — the dealer self-assessment pillar

IDS is the dealer self-assessment already conducted across the network. It is **not** a distributor audit.
A distributor node must never show an implied distributor score derived from dealer assessments, and any
aggregation must state the dealer population, the period and the coverage.

The commercial asset here is under-used and you should say so plainly: of the 519 dealers with a recorded
assessment across 19 networks, 334 carry an individual score today (average 77.5). That is ISZE holding
something a dealer wants to look at and cannot easily assemble itself. Three quarters of the estate has an
assessment and no way to explore it.

Write the pillar around the difference between three things that must never update each other: completing a
development initiative, a later reassessment changing the recorded answers, and an actual commercial
improvement.

### 5.3 PRISM — the market and fleet context pillar

PRISM supplies vehicle composition, fleet age, model mix and expected demand. It changes the interpretation
of a commercial movement rather than decorating it with a fleet graphic.

Three rules, and state them where the reader can see them:

- A national vehicle total cannot be allocated to dealers by sales, visits or geography.
- A part that serves several vehicle classes stays shared unless exclusive applicability proves which
  model it belongs to. Pool multi-band parts rather than splitting them by fleet share.
- A modelled gap is not recoverable sales, and it is not a business case. Spend per truck is a measured
  purchasing rate on a stated fleet basis; target spend depends on assumptions.

### 5.4 DLOD — the competitive-defence pillar

DLOD is **Don't Lose the Deal**, ITUK's existing programme for competitive quotations — support that helps a
dealer defend a job when the customer has an alternative in front of them. It is a real programme, not a
slogan: it runs on a memorandum of understanding with a rebate credit note and Japan-side sign-off, and the
billing ledger carries rebate lines labelled with it. One prior-year memorandum states a €30,000 incentive.

Write this pillar as the worked example of a support programme that cannot currently prove it worked, and
show why that matters to the whole programme:

- The programme is a **commercial defence tool**, a **documented incentive**, and a **data gap**.
- Searching for the label across all 538,346 billing rows returns nothing usable at case level. A rebate
  records that money moved; it does not record that a question was asked, what the competitor quoted, or
  whether the job was kept.
- Therefore: **DLOD spend is not proof of incremental profit.** A credit note proves support was paid.
  It does not prove the customer was kept or that Genuine share grew.

Then make the constructive half of the argument, because this is a pillar and not a criticism: what Universe
would have to show for a DLOD case to be judgeable — the part, the dealer, the competitor evidence, the
outcome, and the before-and-after view on the affected dealers and families. State the caution that support
which cannot show a before-and-after should not be called successful from rebate volume alone.

### 5.5 Tenders and fleet opportunities — the fifth pillar

**This pillar is locked. Do not substitute another one, and do not leave it vague.** The business owner has
already decided that **tenders belong inside Universe rather than beside it**, and that a tender pillar is a
first-class part of the product and a second-class hero. Write it as a full pillar on the same footing as the
other four.

What the pillar is: relevant open opportunities, each carrying its source and the date it was observed, turned
into a qualified shortlist with a pursuit decision — whether to go after it, with what support, and who owns
the next step.

Four rules that go on the page:

- A tender's overall value is **not** expected Isuzu parts revenue, and an award is **not** parts billed.
- A notice count is not pipeline. The useful output is a shortlist, not an alarm feed.
- Every opportunity carries its source and observation date. A stale notice is worse than a missing one.
- Pursuit is a decision, and declining is a valid outcome. Record why, because a declined tender teaches the
  next qualification more than a won one usually does.

The give and the ask are both real. **Give:** country-relevant opportunities with the aftersales content made
visible, so a distributor sees the parts and service footprint early enough to act. **Ask:** lightweight
feedback when a tender is won, lost or ignored — without it the feed is noise and the pillar cannot improve.

State plainly what the pillar cannot yet do. There is no won-or-lost case log at case level, so the pillar can
qualify and prioritise but cannot currently prove it won anything. That gap is the pillar's honest limit, and
it is the same gap that weakens the DLOD pillar — say so, because the two belong together and a reader who
sees it twice will understand it is a data decision rather than two separate faults.

### 5.6 Why five pillars and not one application

Address this once, directly, because a management reader will ask it. A single application forces every user
through one opening screen and makes the first experience depend on evidence the participant may not have.
Five pillars answer five different questions, and a participant usually starts with the one it can answer for
itself today. Connect them through a shared selection — entity, account, period, product range, source basis,
permitted audience — and connect them because the next decision gets better, not because every box needs an
arrow to every other box.

---

## 6. THE EXAMPLES — REAL, LABELLED, AND COMPLETE

The paper must carry worked examples. Use the ones the evidence already supports, and label each one. An
example is not an illustration; it is the proof that a pillar does commercial work.

### 6.1 The examples that survive, and how to label them

| Example | The movement | Label and limit |
|---|---|---|
| ITUK brake pads | ISZE billing to Isuzu Truck UK in the brake-pad source category fell from €347,389.58 in calendar 2024 to €302,366.25 in 2025, down €45,023.33 or 13.0%. Recorded quantity fell from 4,562 to 3,402, down 25.4% | *Measured*, source-category aggregate, snapshot 19 September 2026, arithmetic rechecked 23 September 2026. The 22,389-truck context is not the eligible population for every pad reference and is not divided among dealers |
| Where the reduction sits | Across the selected brake categories — pads, rotors, shoes — the combined reduction is €47,068.77, of which pads are 95.7% | *Measured*, same source and period. It changes the question from "braking products are down" to "brake pads are down" |
| Portugal clutch kits | Combined billing rose from €29,959.87 in 2024 to €31,702.47 in 2025, up 5.8%. Genuine fell from €2,901.92 to €2,057.86 while BVP rose from €27,057.95 to €29,644.61. Quantity barely moved: 462 kits in 2024, 461 in 2025 | *Measured*, same source and period. **This is the example that proves the tool's worth by preventing a mistake**: a Genuine-only view would have proposed a recovery campaign for a line whose total business grew |
| Where the concession sits | PMS billed €6.65M across 24 distributors in 2025; 8.4% of it sat at least 20% under the reference price and 2.8% at least 30% under. The 2024 shares were 13.0% and 4.0% of €7.11M | *Measured*. The improvement is real. The trap is that the highest deep-discount shares sit in the smallest markets — Ukraine 28.2% of €203k, Portugal 20.2% of €338k, IUK 16.9% of €1.27M, Germany 16.6% of €416k — so a programme paying per campaign without a size floor spends most of its money in the smallest markets |
| What is settled and what is not | Brake rotors at 3.4% of €1.30M and oil filters at 1.5% of €557k carry almost no deep discount; brake-pad-front at 36.0% of €423k and blower filter at 25.2% of €374k carry a lot on modest bases | *Measured*. The settled lines are the shape of large single deals rather than a broad pricing position, which means their opportunity is not price |
| The Cordwallis case | 72 trucks, 70 on part lines, 269 jobs, 1,627 lines, one dealer at Heathrow, one year, one family | *Measured*, verified at 104 checks with 0 failures. This is the one case with a matched workshop book and sales file, and it is the model for what a per-dealer example requires |

### 6.2 The two examples you must NOT build this way

- **Quotation outcomes.** No quotation record, no case log, no won-or-lost outcome exists. The event happens
  between a distributor and a dealer and leaves no trace on ISZE's side beyond a part that eventually ships
  months later. Do not write a competitive-quote case as though the outcome is known.
- **Availability and stock.** What ISZE holds is what was billed, which is what left our side. What was
  available at the counter, in what quantity, at the moment the customer asked, exists only in the
  distributor's system. Do not write a range gap as though a stock record existed.

Where an example cannot be built, say what is missing and what would close it. A well-explained "not enough
evidence to change a price" is a valid and important product outcome, and it belongs in the paper.

### 6.3 What every example must carry

For each example, on the page, in this order: the business question; the market or account and the sales
stage; the period; the product family and the actual part references where supported; the observed signal;
the relevant fleet context and what it is not; the Genuine and BVP evidence; comparable competitor evidence
where it exists; the alternative explanations considered; the evidence limits; the proposed decision; who
owns it; the expected financial mechanism; and how the outcome would be measured.

**One reporting clock at a time.** Never add a calendar year to a financial year. Isuzu's fiscal year runs
April to March; the historical examples compare full calendar years. The 2026 billing reference is a half
year through 30 June 2026, and a missing month is not zero.

---

## 7. THE EVIDENCE LAW — NON-NEGOTIABLE

This paper already has a history of being told a number was wrong. These rules exist because of that.

### 7.1 Label every substantive claim

Use four labels and nothing else. *Measured* is counted in a source file you can name. *Inferred* is a
conclusion drawn from measured data. *Proposed* is a design or a decision not yet taken. *Unknown* is
recorded as unknown and is not filled with an assumption. State on the page that an unlabelled number should
be read as an error in the paper.

### 7.2 The claim register is the authority, not the health check

A green workspace check does not certify a commercial claim. The check verifies that the pipeline runs and
its own expectations hold; the dispute records state directly that it "contains none of the disputed
numbers". Read `02_DISPUTED_CLAIMS_AND_RESOLUTIONS.md` and the claim register alongside any figure, not
instead of it.

### 7.3 Figures that must not be printed

| Figure | Why it cannot travel |
|---|---|
| The 32.4% ITUK rate | It predates the split that moved ITUK to 45.6%, and pairing it with the current parts base mixes two methods |
| 61,791 and 37,019 km/yr | Must never appear as an all-models pair |
| Any ITUK capture rate above 100% | Unplottable at face value. Two sit at 106% and 133%, which happens when the units billed are measured against a smaller expected population than the one actually buying |
| The 54.4% coverage share | It could not be re-derived from any cited source, so there is no defensible way to print it |

**The 47% figure is usable only with its denominator named**, because there are four ways to count the fleet
and each gives a different percentage. Two live ITUK percentages differ by 14.6 points on identical billing —
the same euros, two answers. Until that split is closed, naming the denominator is the only honest way to use
either number.

### 7.4 Figures that are safe, with this exact wording

Use these forms, and if you cannot reproduce one from its source on the day you build, do not print it:

> €117.6m of parts billed across 22 distributors, 2023-01-03 to 2026-08-31; the UK lane ends 2026-06-30.

> ITUK spent €248.54 per truck in 2025 against a reference ceiling of €11,835,911 on 22,389 trucks — 47.0% on
> the upper-reference basis.

> ITUK's uncaptured service-demand value is €2.11m in 2025, on a 50.85% capture rate measured against the
> N75-scoped denominator. (50.85%, not 50.9%; the denominator is 23,068 N75 buckets, not vehicles.)

> ITUK's 64 named dealers took 223,897 units in CY2025 (month rows only).

> €55.3m ceiling, of which eight markets sit on a flat €250-per-truck placeholder holding 40.3%.

> 519 dealer self-assessment records across 19 country lists, one round, no per-dealer date; 514 distinct
> names.

**The €55.3m ceiling must never be presented as a revenue forecast.** It is a modelled target-spend ceiling:
what the market could spend, not money available to us. Multiplying it by a recovery percentage invents a
revenue case this programme refuses to make.

### 7.5 Boundaries that apply to every commercial sentence

- ISZE billing measures ISZE-to-distributor purchasing. Distributor-to-dealer sales are a different stage.
  Dealer-to-end-customer sales are a third. Never treat them as interchangeable.
- Missing sales-to-dealer information means **unknown, not zero**. A missing purchase in an incomplete
  extract is not proof that a dealer buys from a competitor.
- Warranty records failures, claims and settlements. It is not evidence of scheduled maintenance, filter
  replacement or service capture.
- Billing carries no vehicle identifier of its own. Name a model or a tonnage band only where exclusive
  applicability has been validated.
- A sales decline is a signal, not a diagnosis. Consider supply constraints, backorders, stock timing,
  supersession, product mix, BVP migration, one-off orders, special-price-agreement expiry, tender effects,
  seasonality and incomplete coverage before naming a cause.
- Do not infer a competitive problem from comparing a net distributor purchase price with an online retail
  listing. State what comparison is possible at each stage.
- There is no reliable measured price response in the current evidence base. One family shows a steeply
  negative direction with almost no explanatory power; another is inconclusive; a third cannot be identified
  because the list-price movement was nearly uniform. **No scenario in this paper forecasts a demand
  response.** A threshold says what would have to happen; it does not say what will.
- Never blend UTI with UMI, and never blend ITUK with IUK. They are separate distributors with separate
  systems. A blended Israel figure puts one distributor's numbers against a network that was never assessed.

---

## 8. VISUAL SYSTEM — RED AND CHARCOAL

The paper is the house style. Confirm these values against the AIM deck before you finalise, and use them
consistently.

| Role | Value |
|---|---|
| Page and section field (charcoal) | `#24282C` |
| Isuzu red — emphasis only | `#D71920` |
| Primary text | `#FFFFFF` |
| Secondary text | `#CCD1D2` |
| Secondary dark panel | `#353B3E` |
| Navy (charts, structure) | `#15233C` |
| Terracotta (second series, accent) | `#C0552D` |
| Pale rule and table band | `#E4E9F0`, `#F2F4F7` |

Type: Arial or a metrically compatible substitute. Strong hierarchy, generous spacing, clean geometry.

### 8.1 Non-negotiable visual rules

- Charcoal carries the body, not only the cover. Do not revert the content pages to a light background and
  then call the cover the style.
- **Never white or near-white text on a pale panel.** A dark section header keeps white text; a pale row
  keeps ink text. If a later row style overrides a header style, that is the bug — fix the specificity, do not
  patch the colour.
- Red is emphasis. It is not an instruction to colour every paragraph or make every chart alarming. Budget
  red for the thing you want the reader to act on.
- Do not use low-contrast grey for body text. If it is worth reading, it is white or `#CCD1D2`.
- One figure per reader question. Short annotations, in the figure, saying what to look at. Legends must name
  the series, not the variable.
- Never dual axes. Never inconsistent scales on a shared axis. Never a chart sized to exaggerate a
  divergence.
- Real numbers only, generated from source at build time. No hand-typed values in a chart. If a page needs a
  number you cannot source, the page carries a labelled structural diagram instead of a fake chart.
- Every figure carries: source, period, population, sales stage, unit, method where necessary, measured or
  modelled status, and its material limitation.
- Do not sum heterogeneous part quantities into an apparent family-volume figure.
- Colour must never be the only way to read a chart. Pair it with a label or a pattern.
- A mock-up is labelled as a proposed interface. Never manufacture convincing figures to make a mock-up look
  real. Use supported values or obvious placeholders.

### 8.2 Figures the paper should carry

Select the strongest; do not add all of them mechanically. Each must answer a question a reader has.

Product architecture — how the five pillars contribute to one class of decision. Decision loop — how a
signal becomes evidence, a decision, an action and a measured result. The ITUK brake-pad value-and-volume
chart, which is the whole argument on one figure: value fell 13.0% while quantity fell 25.4%. Where the
reduction sits across the three brake categories. The Portugal Genuine-versus-BVP chart, which is the
mistake this product prevents. Deep-concession share by distributor, showing that the most exposed
distributors are not the largest ones. The hurdle chart: how many beneficial actions each envelope implies at
two contribution levels. The campaign-structure comparison showing why an additional-only concession is
cheaper than a concession on all volume. What is measured, inferred, proposed and unknown. What each
participant gives and receives. The participation score by step, with the reason beside each number. The
dealer self-assessment distribution. The Cordwallis case scope. The evidence coverage map: what is known,
partial, unavailable or not applicable.

---

## 9. STRUCTURE AND INDEX

The paper is complete: an index, a figure list and a table list, with page numbers, plus a glossary and a
source table. A reader must be able to find any claim from the front of the document.

Front matter, in this order: cover; a one-page summary that states the recommendation and the one thing that
is unproven; contents; figure list; table list; then the chapters.

Recommended chapters — improve them where the evidence supports something stronger, but keep this pressure
order, because a management reader reads the first four and skims the rest:

1. **The commercial problem.** A specific problem, not a general desire for better data. The mechanism: ISZE
   has asked distributors for information for years with insufficient visible value returned, and a reporting
   obligation can start an exchange where only a useful tool continues it.
2. **The scope boundary.** What Universe is not. A normal service is not a reward for participation, and
   participation is not the price of a normal service. This chapter is the offer as much as the limit.
3. **The five pillars.** One section each, with what each contributes, what it cannot establish, and which
   decision it improves.
4. **The examples.** The worked cases, labelled, complete, including the one that shows the product preventing
   a wrong decision.
5. **What the paper proves, and what it does not.** Measured, inferred, proposed, unknown. Put the weak
   elasticity evidence in the body, not an appendix, because silence lets a reader assume whatever
   responsiveness suits the conclusion being argued.
6. **Participation.** What a dealer does, what a distributor does, and an honest score per step with the
   reason beside each number.
7. **The money.** The denominator, the hurdle, the price of a dealer, and what a campaign should cost. State
   the hurdle rather than a predicted outcome.
8. **The decisions.** Numbers small enough to answer, each with what has to be true first.
9. **What to build first, and what stops.** The sequence, the go/no-go, and the stop condition.
10. **Ownership, delivery and risk.** Who owns what, what no amount of code closes, and the boundaries.
11. **Reference.** Measures, periods, populations and identities; sources and revision record; glossary.

Appendices: the field catalogue and acceptance tests from the first white paper, the case states, the
contribution record, and the measurement definitions.

**Do not write the paper as a series of questions.** Use questions to test the argument, then write a
narrative. Do not inflate the page count to look thorough. A shorter paper that answers more is the goal.

---

## 10. LANGUAGE FOR A SHARED PAPER

This paper leaves ISZE, so the shared rules apply.

- Plain business English. Define a term once, then use it. Prefer "what we billed", "the distributor's
  onward sales", "dealer price" and "target spend per truck" over internal shorthand.
- **Never use audience labels such as "Mode A" or "Mode B".** If a distinction is needed, say shared or
  internal.
- Do not use internal product-story nicknames. Say **IML service schedule** and point to the real business
  source rather than an internal version name.
- **Talk in margins, never in factors.** Write "53% margin", not "factor 0.47". The factor is the divisor;
  the margin is the decision.
- Never write **sell-out**. Write **sales to dealer**.
- Never write **street**, **wallet** or **capture** as a bare label. Write "OEM peer retail", "parts billed"
  versus "target spend per truck", and "the share of expected demand we actually billed".
- No personal names in the paper. Roles only.
- No agent vocabulary: no ship-gate, receipt, harness, packet, drift, lane, surface, payload, artefact,
  rollup, granularity, instantiate.
- Spell country and entity codes out on first use. ITUK is Isuzu Truck UK; UMI and UTI are two different
  Israel distributors and are never blended.
- Every acronym is expanded at first use, in the sentence that uses it.
- State uncertainty in plain words. Do not convert a judgment into a precise confidence score.

---

## 11. PRODUCTION, AND WHAT "DONE" MEANS

A builder exit code of zero is not done. Verify the rendered page.

1. **Source.** Write the paper as markdown in `01_Strategy\`, dated, with a revision record that names which
   older editions it supersedes and which remain on disk for reference.
2. **Figures.** Generate every figure from source at build time through the existing figure generator in
   `_build_30\`, so the paper cannot carry a chart that disagrees with its data. Regenerate, do not reuse the
   raster images from the visual edition — that edition prints each diagram twice over itself.
3. **Render.** Build the PDF from the markdown.
4. **Check every page.** Look at the pages, one at a time, at full resolution. Clipped text, overlapping
   elements, unreadable chart labels, low contrast, an inconsistent background, a wrong total, an unsourced
   claim, a broken page reference or inconsistent terminology are all failures. Fix them and look again. If
   you took N screenshots, read N, and say how many you read.
5. **Check the index.** Every page number in the contents, the figure list and the table list must be
   correct in the rendered file. Verify them after the last content change, not before.
6. **Check the numbers against the register.** Each figure that appears in prose must match its source row and
   the claim register. Where a figure is disputed and unresolved, it does not appear.
7. **Deliver.** PDF plus an editable source, in the folder, with a sibling launcher for the PDF. Report what
   you inspected and what you could not.
8. **Do not circulate.** Produce the paper as a draft for the business owner. Do not send it anywhere and do
   not describe it as approved.

---

## 12. INSTANT FAILS

Any one of these means the paper is not finished.

- The paper reads as a rewrite of the newest edition rather than a merge. No merge ledger, or a ledger with
  nothing cut from anything.
- Oil filters, or any single part family, used as the opportunity hero. The opportunity hero follows the
  category gaps; a method illustration is not the opportunity.
- A disputed figure appears. The 32.4% rate, the 61,791 and 37,019 km/yr pair, a capture rate above 100%, or
  the 54.4% coverage share.
- The €55.3m ceiling presented as revenue, or multiplied by a recovery rate to invent a revenue case.
- A unit or quantity count presented without euro, without a part family, and without the fleet it is a rate
  against. A count is an ingredient, never a finding.
- An unlabelled number. A chart with a hand-typed value. A dual axis. A pale panel with white text.
- A pillar explaining what it could do with data it does not have.
- A dealer case built as though a quotation outcome or a stock position were known.
- A tender count presented as pipeline value.
- A participation score without the reason beside it.
- A page count inflated to look thorough, or a diagram that exists because the section felt thin.
- The word "done", "complete" or "final" used about a build that failed the page check.

---

## 13. WHAT TO PRODUCE, IN ORDER

1. **Reconnaissance.** The list of files you opened, and the files you could not. One page.
2. **The merge ledger.** Section 4's table, filled in. This is where you prove you read the older papers.
3. **The pillar map.** One table: each of the five pillars, the question it answers, and the evidence behind
   it. This is where the AI proves each pillar stands on something real.
4. **The figure plan.** Each figure, the question it answers, and its source.
5. **The paper.** Markdown source, then the rendered PDF, checked page by page.
6. **A closing note in chat, not in the paper.** Ten lines maximum: what the paper now argues, the strongest
   evidence behind it, the single most important thing still unproven, and what you could not verify.

Be sceptical but constructive. Do not confuse ambition with evidence, and do not confuse caution with a
reason to build nothing. Preserve the strongest ideas from the earlier editions. Make the trade-offs visible.
Make the product tangible. Make the funding choice understandable. Make the visual presentation recognisably
the house style.

The goal is not a longer white paper. The goal is a white paper that makes Universe harder to misunderstand,
easier to defend, and more likely to earn the participation it depends on.

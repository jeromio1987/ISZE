# Universe: the ten moves as ready-to-run prompts

23 September 2026. One prompt per move from the success framework
(`C:\Users\jerom\Desktop\claude\ISZE\Isuzu Universe\UNIVERSE_SUCCESS_FRAMEWORK_2026-09-23.html`).

## Routing

| # | Move | Runs on | Why that model |
|---|------|---------|----------------|
| 1 | Name an owner for the answers | DeepSeek 4.1 | Pure drafting, no files |
| 2 | Deputy and run-book | Claude Code, **Sonnet 5** | Needs to read the build folders; routine documentation |
| 3 | Three director conversations | DeepSeek 4.1 | Talking guide, no files |
| 4 | Mock dealer scorecard, Isuzu Truck UK | Claude Code, **Opus 5.5** | Real data, joins, and a hard no-invention rule |
| 5 | Ask for vehicle sales by selling dealer | DeepSeek 4.1 | Email draft |
| 6 | Fix the classification release | Claude Code, **Opus 5.5** | Compares candidate files; wrong call breaks everything downstream |
| 7 | Outcome line on every credit note | DeepSeek 4.1 | Field spec and instruction note |
| 8 | Legal review brief | DeepSeek 4.1 | Memo draft |
| 9 | Euro value of the 20% rebate share | DeepSeek 4.1 | Short email |
| 10 | Funded dealer setup pack | DeepSeek 4.1 | Invitation, task and tracking sheet |

**DeepSeek prompts are self-contained and sanitised.** They carry no dealer names, no
distributor-level euro figures and no rebate percentage (placeholders like `[X]` instead),
because DeepSeek is an external service. Fill the placeholders yourself after the draft comes back.

**Claude Code prompts** run from `C:\Users\jerom\Desktop\claude\ISZE` so CLAUDE.md, the
workspace rules and the data guardrails load. Pick the model in the app before pasting.

---

## 1 · Name an owner for the answers (DeepSeek 4.1)

```text
You are drafting for a VP Sales at a European truck-parts importer (part of a Japanese OEM group).
Write in plain, formal British English. No em dashes. No consultant or AI buzzwords
("leverage", "unlock", "synergy", "seamless", "robust", "empower"). Short sentences.

Context: we are launching a programme that gives our distributors and their dealers analytical
tools (a parts classification atlas, a dealer maintenance scorecard, a dealer self-assessment
profile). The tools will raise questions such as "why is this dealer only buying a quarter of the
oil filters its trucks need?". Nobody is currently named to answer those questions. Software is
cheap; a person's time is not. Without a named owner the tools will look finished and deliver
nothing.

Produce two things:
1. A one-page role description, "Universe answer owner": purpose, the questions this person
   answers, expected volume in a pilot (two distributors, ten dealers), response standard
   (e.g. five working days), what they may decide alone and what they escalate, and the share of a
   working week required. Give the time share as a range with the reasoning, not a single number.
2. A half-page memo to the Managing Director asking for this person to be named before the first
   dealer is invited. State the risk of not naming one in one sentence.

Leave [NAME], [TEAM] and [START DATE] as placeholders.
```

## 2 · Deputy and run-book (Claude Code, Sonnet 5)

```text
Work in C:\Users\jerom\Desktop\claude\ISZE. Read CLAUDE.md and INDEX.md first.

Goal: make the Isuzu Universe programme survivable if Jerome is unavailable for a month.

1. Inventory what runs the Universe deliverables: the build scripts under
   "Isuzu Universe\_build_final\" (build.py, build2.py, charts.py), the source files they read in
   01_data\00_derived\ and 01_data\14_dashboards\tender_data.json, the Isuzu Dealer Standards tools in
   02_dashboards\ids\, and the Parts Atlas prototype in "Isuzu Universe\02_Atlas\".
2. For each: what it produces, how to run it (exact command), what it depends on, how to check the
   output is right, and what breaks most often. Run each build once to confirm the command works;
   report any failure verbatim, do not fix silently.
3. Write "Isuzu Universe\RUNBOOK_UNIVERSE.md": one section per deliverable, plus a "first day for
   a deputy" checklist. Plain English, no internal nicknames.
4. List what a deputy cannot do today without Jerome (access, knowledge, credentials) as an open
   list. Do not invent workarounds.

Do not change any build script or source file. Do not load 01_data\raw\sales\*.XLSX.
Report the file path and the list of open dependencies at the end.
```

## 3 · Three director conversations (DeepSeek 4.1)

```text
You are preparing a VP Sales for 30-minute conversations with the managing directors of three
truck-parts distributors in Europe. Formal, plain British English, no em dashes, no buzzwords.

What we want to learn, not sell: whether the distributor feels the same blindness about its own
dealers that we feel about the distributor. Today the importer sees what it invoices to the
distributor, and almost nothing below that: most distributors send no sales-to-dealer data, and
only one sends it by named dealer. We will show one anonymised chart: parts bought by each dealer
of one distributor in one year, ranked, with a very wide spread, and the point that nobody can say
whether a dealer buying the median amount is strong or weak without knowing how many trucks it
looks after.

Produce:
1. A conversation guide: opening (two sentences, no pitch), the chart moment, six open questions
   (e.g. how do you decide which dealer to visit; what would you need to judge a dealer's
   maintenance business; would you use a per-dealer scorecard in your own dealer meetings; what
   would stop you sharing monthly sales to dealer), and a close that asks for nothing.
2. A one-page note-taking template: per question, verbatim quote, interest level 1-5, objections,
   what they would need.
3. Five objections we should expect and a one-sentence honest answer to each. One of them must be
   "this is the importer looking at my business", and the answer must not promise anything we
   cannot guarantee.

Do not include any figures beyond those in this prompt.
```

## 4 · Mock dealer scorecard, Isuzu Truck UK (Claude Code, Opus 5.5)

```text
Work in C:\Users\jerom\Desktop\claude\ISZE. Read CLAUDE.md, INDEX.md and FACTS.md first.
Before building, state in one paragraph whether the data supports this (sufficient / insufficient /
what is missing), then continue.

Goal: a mock "dealer maintenance scorecard" for the 64 Isuzu Truck UK dealers, to test with the
distributor. It must be honest about the one input we do not have: trucks sold or serviced per dealer.

Sources:
- 01_data\00_derived\dealer_sellout_long_ITUK_CY2025.csv (dealer x part number, quantities)
- 01_data\00_derived\dealer_sellout_gps_2025.csv (dealer-level euro, ITUK rows)
- the current parts classification used by the Universe white paper (ask me if more than one
  candidate exists; do not choose silently)
- 01_data\00_derived\pms_capture_by_db_year.csv (network-level expected units, context only)

Build per dealer, calendar 2025: maintenance-parts units and euro by family (oil, fuel, air, urea,
blower filters; brake pads, rotors, shoes; clutch), Genuine vs Best Value split, share of the
network total, rank within the network. Add a column "trucks looked after" left EMPTY with the
note "to be supplied by the distributor", and a "capture" column that stays empty until it is
filled. Show, for three example dealers, exactly how capture will be calculated once the truck
count arrives. Do not estimate a per-dealer fleet from the national figure; that is forbidden.

Output: a self-contained HTML (no CDN), charcoal and Isuzu red, one page per dealer plus a network
overview, saved to "Isuzu Universe\02_Atlas\ITUK_DEALER_SCORECARD_MOCK_2026-09.html" with an
OPEN_*.cmd beside it. No capture figure above 100% anywhere. State every source in a small footer.
Report the path, the data gaps, and any dealer names that did not match between the two files.
```

## 5 · Ask for vehicle sales by selling dealer (DeepSeek 4.1)

```text
Draft a short business email from a VP Sales at a European truck-parts importer to the managing
director of one of its distributors. Formal, plain British English, no em dashes, no buzzwords,
under 200 words.

Ask: vehicle sales by selling dealer for the last five years (dealer, model, model year, units),
in any format they already have. Explain why in two sentences: combined with the distributor's
sales to dealers, it lets us prepare a maintenance scorecard per dealer for the distributor's own
dealer meetings, showing how much of its trucks' maintenance-parts need each dealer actually buys.
Make clear that this is for the distributor's benefit first, that the data stays within the
importer's parts team, that no customer or chassis-level data is needed, and that nothing in their
normal service depends on it. Offer a 20-minute call. Placeholders: [NAME], [DISTRIBUTOR], [DATE].
```

## 6 · Fix the classification release (Claude Code, Opus 5.5)

```text
Work in C:\Users\jerom\Desktop\claude\ISZE. Read CLAUDE.md, INDEX.md, DECISIONS.md first.

Problem: the parts classification that every Universe example relies on is not pinned. Several
candidate classification files exist, and earlier reviews measured different amounts of movement
between them. Until one release is named, no family label can go to a distributor.

1. Find every candidate classification file (look under 01_data\00_derived\ for
   aim_pn_classification*, pr00_classification*, the AIM master, and anything DECISIONS.md or
   01_data\00_derived\HANDOFF_AIR_FILTER_AND_FOCUS_CUT.md names). List path, row count, build date,
   declared upstream.
2. Compare them pairwise on part numbers and on family/group/product-form labels. Quantify the
   disagreements, and weight them by 2025 billed euro using the derived billing parquet (never the
   raw XLSX).
3. Check each against the three white-paper examples: Isuzu Truck UK brake pads, Portugal clutch
   kits, the ranked family view. Does the example reproduce?
4. Recommend one release with a reason, and write a one-page decision memo:
   "Isuzu Universe\01_Strategy\CLASSIFICATION_RELEASE_DECISION_2026-09.md" (release, version,
   build date, what changes for users, what is still open).

Do not modify any classification file. Do not declare the decision taken: it is a recommendation
for Jerome to approve. Report the recommendation and the top five disagreements by euro.
```

## 7 · Outcome line on every credit note (DeepSeek 4.1)

```text
You are writing an operational instruction for a truck-parts importer. Formal, plain British
English, no em dashes, no buzzwords.

Context: the importer pays a distributor support credits so dealers can match a competitor's quote
and keep a job ("Don't Lose the Deal"). Money has been paid for three years and not one case has
been recorded: no part, dealer, competitor price or outcome. We want every future credit note to
carry a short case record, filled in at the moment the credit is raised, taking about five minutes.

Produce:
1. The record specification: eight fields (part number; dealer; competitor evidence with its date;
   support requested; support granted; outcome as won / lost / no decision; date; follow-on order
   reference when won). For each: definition, allowed values, who fills it, and why it cannot be
   reconstructed later.
2. A one-page instruction for the distributor's staff who raise the request.
3. A one-page instruction for the importer's staff who approve it, including the rule that a case
   with no outcome is "no decision", never "lost", and that the follow-on order reference is what
   verifies a win.
4. A simple monthly summary layout (one table) that shows cases, support paid, won/lost/no decision.

No figures, no names.
```

## 8 · Legal review brief (DeepSeek 4.1)

```text
Draft a memo from a VP Sales to the legal function of a European truck-parts importer that sells
through independent national distributors. Formal British English, no em dashes, no buzzwords.
State clearly that the memo asks for review and makes no legal determination.

Items for review:
1. Rebate tiers: a share ([X]%) of the normal distributor rebate is already linked to KPI reporting.
   Proposal: release it in three tiers. Tier 1 today's KPI report. Tier 2 monthly sales to dealers
   by part number and dealer. Tier 3 plus vehicles sold per dealer and recorded outcomes of
   supported deals. Released for meeting a standard, never paid per record.
2. Three proposed standing rules: no exclusivity in exchange for information; no price
   coordination between distributors (each compared only with its own history and anonymous
   aggregates); no resale-price instruction (the importer sets its net price to the distributor and
   neither prescribes nor keeps dealer resale prices).
3. Workshop data from dealers: date, mileage, vehicle model and year with the vehicle identifier
   pseudonymised, operation, parts fitted. No customer names, no prices.
4. A promotional mechanism ("Deal of the Day") where the importer part-funds a time-limited
   distributor offer, paid only on volume above a documented baseline.

Frame questions against the EU vertical and motor-vehicle block exemption rules (motor-vehicle
regime currently valid to 31 May 2028) and GDPR. End with a list of specific questions and the
date we need an answer: [DATE].
```

## 9 · Euro value of the rebate share (DeepSeek 4.1)

```text
Draft a short internal email from a VP Sales to the finance controller of a European truck-parts
importer. Formal, plain British English, no em dashes, under 120 words.

Ask for: the euro value, per distributor and in total, of the share of the normal distributor
rebate that has been linked to KPI reporting since 2025, for calendar 2025 and year to date 2026,
and how much of it was actually paid versus withheld. Say why in one sentence: we need to weigh a
new programme against the incentive we already pay before the funding discussion. Ask for the
figures by [DATE]. Placeholder [NAME].
```

## 10 · Funded dealer setup pack (DeepSeek 4.1)

```text
You are writing a pilot pack for a truck-parts importer that will invite ten dealers, through
their distributors, to connect a monthly workshop data export. Each dealer that completes the
setup receives a fixed setup payment of [AMOUNT]. Formal, plain British English, no em dashes, no
buzzwords.

Produce:
1. The invitation (sent by the distributor, not the importer), under 250 words. First sentence:
   nothing about the dealer's normal service or terms changes, whether it joins or not. Then what
   the dealer gets: its own dealer-standards profile, a list of trucks in its own workshop history
   due for maintenance in the next 90 days, and a workshop benchmark against anonymous peers.
2. The data record: job date, mileage, vehicle model and year, pseudonymised vehicle identifier,
   operation, parts fitted (part number, quantity, whether bought through the brand channel).
   Explicitly excluded: customer names, prices, labour rates.
3. The setup task definition: what "done" means (first export received and readable), who
   confirms it, and when payment is released.
4. A tracking sheet layout for the ten dealers: invited, accepted, setup done, export month 1,
   month 2, month 3, minutes spent by the dealer, reason for stopping if any. The pilot's key
   question is whether exports keep arriving in months 2 and 3 without chasing.

No league table, no names, no figures other than placeholders.
```

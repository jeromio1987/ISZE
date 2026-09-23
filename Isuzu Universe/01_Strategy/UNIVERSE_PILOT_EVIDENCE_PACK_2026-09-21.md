# Universe — the first real data-flywheel pilot

**Evidence pack for the pilot design**
Built 2026-09-21 · Internal / private · **Evidence only. No implementation, no application change, no source file touched.**

Purpose: establish, from what is actually on disk, which distributor is the best currently supported pilot for
testing whether mandatory sales-to-dealer reporting can be turned into a recurring exchange — and show one
complete worked exchange with real numbers behind it.

Everything below was read or computed on this machine on 2026-09-21. The commands and the machine-readable
output are listed in §11. Where a number could not be established, it is marked **not verified** rather than
guessed.

---

## 1. The recommendation, and why it is not the reason that was assumed

**Pilot on ITUK — but the reason is not the one in the brief.**

The brief says ITUK's dealer data looks strongest, and that is true: it is the only distributor on disk with
dealer names against part numbers at all. But that is not what makes ITUK the right pilot, because that layer
is **units, not money**. It cannot on its own support a "what is this dealer worth" conversation, and it cannot
answer whether a distributor's reporting is worth paying for.

What makes ITUK the pilot is the second layer that already exists behind it and nobody is using: **the only
64-row, dealer-level money table in the entire workspace is also ITUK.** Those two files — one in units, one in
euro — are already on disk, already reconcile to each other, and are produced from two different things. That
pair is the flywheel. It means Universe can already demonstrate, today and without asking ITUK for anything, a
return that no other distributor can produce: a dealer's buying pattern in parts, valued, against a market
reference and a price reference.

The one thing that is missing to close the loop is a number ITUK already once offered in a different form —
and, notably, the request for it was **drafted five days ago and never sent** (§8).

So the honest answer to "is ITUK genuinely the best test case rather than just the assumed one" is: **yes, and
for a stronger reason than the brief gave.** But ITUK is a good test of the *data* flywheel and a poor test of
the *geography* flywheel, and §4 says why that matters for what the pilot should claim.

---

## 2. What "best test case" has to mean, stated so it can fail

Three tests, applied in order. A candidate that fails an earlier test cannot be rescued by a later one.

| Test | The question | Why it decides the pilot |
|---|---|---|
| **T1 — depth below the distributor** | Is there a named dealer layer under the distributor at all? | Without it, the exchange returns a national number. A distributor does not need ISZE to be told its own national total. |
| **T2 — is that layer in money, or only in units?** | Can a single dealer be valued? | Units alone cannot prioritise. "40 units of air filter" and "40 units of engine" are the same sentence. |
| **T3 — can one request close a loop the distributor can see?** | Is there an open uncertainty that one extra item would resolve? | This is the whole thesis of the exchange. Without it there is no second cycle, only a report. |

T1 and T2 are also the two tests that a per-vehicle measure depends on. Both are answered by measurement, not
assumption, so they are the right gates.

---

## 3. Candidate comparison

Sixteen points were asked for. They are answered from files, and the source of each is in §11.

### 3.1 The matrix

Legend: **Y** = present and usable · **P** = partial, with the limit stated · **N** = absent · **—** = not applicable.

| # | Point | **ITUK** (UK trucks) | IUK (UK D-Max) | IRELAND (Harris) | PORTUGAL (Imotors) | GREECE (Petros) | UTI (Israel) | ROMANIA |
|---|---|---|---|---|---|---|---|---|
| 1 | Sales-to-dealer history | **Y** 2025 dealer-level; 2023/24/26 network only | **P** 2025 + 2026 YTD, network only | **P** 2025 + 2026 YTD, network only | **P** 2025 + 2026 YTD, network only | **P** 2025 only | **P** 2025 (Feb–Jul missing) + 2026 YTD | **P** 2026 only, no 2025 |
| 2 | Named dealer coverage | **Y 64 named dealers** | **N** one "All" row | **N** aggregate | **N** no dealer dimension | **N** aggregate | **N** no dealer column | **N** explicitly none |
| 3 | Period granularity | **Y** month, all 12 months, 60/64 dealers complete | **P** month + YTD | **P** month + YTD | **P** month + YTD | **P** month + SUM | **P** month + YTD | **P** month (from filename only) |
| 4 | Part-number granularity | **Y** 5,559 numbers | **Y** 4,248 | **Y** 5,501 | **Y** 5,712 | **Y** 2,101 | **Y** 1,752 | **Y** 688 |
| 5 | Euro present in source | **P** not in the units file; **Y for all 64 dealers** in a separate euro table | **N** qty-only by design | **N** qty-only | **N** qty-only | **N** qty-only | **N** in the long file | **N** qty-only |
| 6 | AIM coverage | **Y 5,556 / 5,559 PNs = 99.95%** | not verified | not verified | not verified | not verified | not verified | not verified |
| 7 | Genuine / BVP coverage | **P** euro-only split; 126 ITUK numbers on the genuine side of the cross-reference, 74 on the BVP side | **N** | **N** | **N** | **N** | **N** | **N** |
| 8 | Competitor-price evidence | **P** one UK source (KS International, weekly scrape), **16 rows matched to 8 Isuzu numbers**; plus a 2023 Eucon UK survey | **P** same single UK source | **N** | **N** | **N** | **N** | **N** |
| 9 | PRISM fleet / service context | **Y** 22,389 vehicles, €248.54 goods billed per truck in 2025 — market level only | **P** market level | **P** market level | **P** market level | **P** market level | **P** market level | **P** market level |
| 10 | IDS participation | **Y** 44 UK CV dealers assessed | **Y** 43 UK LCV dealers | **N** | **Y** 16 | **Y** 34 | **N** (UTI did not take part) | **Y** 15 |
| 11 | Validated dealer / site identity | **P** 16 of 44 IDS names match the 64 sales names exactly; a further 34 are candidate overlaps needing review; about 20 have no plausible match; no name→account crosswalk exists | **P** same problem | **P** | **P** | **P** | **P** | **P** |
| 12 | Tender relevance | **P** 3 UK notices in the live feed, all repair-and-maintenance only; two deadlines already expired | **P** same feed | **P** | **P** | **P** | **N** | **P** |
| 13 | Distributor aftermarket information | **Y** an active PMS/data thread with a named contact, including a VIN list and a monthly parts report | **P** | **P** | **P** | **P** | **P** | **P** |
| 14 | **Fleet denominator per dealer** | **N** | **N** | **N** | **N** | **N** | **N** | **N** |
| 15 | **Sell-through (billed vs sold-on)** | **N** blocked: all 65,619 rows read `NOT COMPUTABLE AT DEALER GRAIN` | **N** | **N** | **N** | **N** | **N** | **N** |
| 16 | **A second year of dealer-level history** | **N** 2023/24/26 are network-only | **N** | **N** | **N** | **N** | **N** | **N** |

### 3.2 Reading the matrix

**ITUK passes T1 and T2. Every other candidate fails T1.** That is the whole result, and it is not close. Six
distributors have some sales-to-dealer data — ITUK, IUK, Ireland, Greece, Portugal, UTI and Romania — and
**six of them have a national volume per part number and nothing below it.** One of them measures a named
dealer's purchase of a specific part number in a specific month. There is therefore no credible alternative to
compare against on the question the pilot is actually testing, and saying so plainly is more useful than
manufacturing a shortlist.

The best runner-up, if a second site is wanted later, is **IRELAND**, for a reason that has nothing to do with
the matrix: it is the only market on disk with dated open-order lines (40 `IE_BO_OVERVIEW` extracts, 2025-10-30
to 2026-08-11) carrying part number, open quantity, required delivery date and a supplier note. That is supply
evidence, and supply investigation is one of the actions in §7. But it has no dealer layer, so it cannot carry
this pilot on its own. **Ireland is a second-cycle candidate, not a first-cycle one.**

### 3.3 What each candidate would actually test

| Candidate | What a pilot on it would really demonstrate |
|---|---|
| ITUK | Whether a dealer-level parts picture, valued, changes a decision — and whether a distributor will keep feeding it monthly. **The real test.** |
| IRELAND | Whether backorder and open-order evidence is worth collecting. Different question, and it needs a dealer layer built first. |
| PORTUGAL | Whether a market with a long file and no dealer dimension can be made useful. Answered already: not on its own. |
| UTI | Whether national volume is enough. It is not, and Israel adds a further problem — the fleet denominator is absent and the IDS round it did not join must never be blended in. |
| ROMANIA | Whether a market with no prior year can enter. It cannot: no 2025 file, so no year-on-year. |

---

## 4. Where ITUK is weak — read this before designing anything on it

Four limits, all of them measured, and all of them constraints on what the pilot may claim.

**One year, not a series.** 2025 is the only year with dealer names. The 2023, 2024 and 2026 ITUK files are
national aggregates even though they sit in the same folder. A dealer-level trend **cannot** be built from
anything held today. The pilot can say exactly what each dealer bought in 2025; it cannot say whether a dealer
bought more or less than the year before.

**The dealer layer has no vehicle model and no Genuine/BVP split.** The `vehicle_scope` column is empty on all
101,341 rows, `description` is empty on all of them, and `qty` is genuine and BVP together. The genuine/BVP
split exists only in the euro table. So the units layer and the quality layer have to be joined, not read off
each other.

**No dealer is tied to a billing account, and that kills sell-through.** All 65,619 rows of the replenishment
bridge return `NOT COMPUTABLE AT DEALER GRAIN` / `bill_basis = UNAVAILABLE - network billing has no dealer key`.
Universe cannot currently say what ISZE billed ITUK for versus what ITUK passed on, per dealer. It can say it per
market. One list — dealer name to account number — closes that, and it is the single highest-value item on the
ask list.

**No fleet denominator below the market.** Trucks in service stop at market everywhere in the workspace. The
44 IDS UK CV dealers and the 64 sales dealers cannot carry a per-dealer vehicle rate today. Worse, the euro
table has a `uio_units` column reading exactly **22,389 on all 64 rows** — the national fleet copied onto every
dealer. The R1 work already caught this and quarantined it, correctly: it is a market reference valuation, not
dealer turnover, and `sellout_spu_eur` must not be read as a per-dealer figure.

**And one number in the analysis chain is an assumption, not a measurement.** The parts-demand model applies
**50,000 km per vehicle per year**. Measured against the UK's own warranty odometer records, the same fleet
comes out at **16,688 km/yr across all classes, 12,891 for N35 and 35,478 for N75**. Everything modelled per
vehicle inherits that. This is not a footnote — it is the uncertainty the worked exchange turns on, in §6.

---

## 5. One complete evidence-backed worked exchange

This is the finished article. Every figure is measured from the files named in §11. Names are ITUK's own dealer
names, so **this pack is internal and must not go to a distributor as written** — the distributor-facing version
would replace them with cohorts.

The subject is the air-filter family, chosen because it is a scheduled maintenance part, it is the family where
the UK has matched competitor prices, and it is already classified.

---

### Step 1 — What ISZE already knows

ISZE holds a parts classification that tells it what an air filter is, which part numbers are air filters, and
how the portfolio divides into families. It holds the market context: **22,389 trucks in service in the UK**,
and **€248.54 of parts billed per truck in 2025** (€231.82 excluding warranty parts of €374,426). And it holds
one genuinely useful comparison: the dealer list against the IDS self-assessments.

What ISZE does **not** know is anything about a specific dealer's parts behaviour, because until the 2025 file
arrived it had no dealer-level sales to dealer at all.

### Step 2 — What the distributor contributed

ITUK handed over `Sales to Dealers_ITUK_CY2025.xlsx`: **64 named dealers × 5,559 part numbers × 12 calendar
months**, 101,341 rows, 223,897 units in the monthly rows with the annual control rows showing 224,001 — a
**104-unit residual (+0.05%)** that is genuine and stays visible. No duplicate dealer/part/month keys. 60 of the
64 dealers carry all twelve months.

This is the only such file in the workspace. It cost ITUK an export, not a project.

### Step 3 — What Universe returns

Four things, all of them things ITUK cannot produce for itself from that export.

**(a) The classification.** 99.95% of ITUK's part numbers resolve to a family (5,556 of 5,559; three do not).
The air-filter family is 260 part numbers.

**(b) The family picture.** 5,259 air filters in the year across **59 of the 64 dealers**. The median dealer
buys **63**; the range runs from **2** to **318**. That range is the conversation starter, and it is the first
thing a distributor will look at.

**(c) The specific finding.** ITUK's air-filter buying is split across two current part numbers, and the split is
lopsided:

| Part number | What it is | Units CY2025 | Dealers buying (of 64) |
|---|---|---|---|
| `8970622940` | air cleaner element | **684** | **40** |
| `8976739570` | air cleaner element | **767** | **55** |

Cross-tabulated, **38 dealers buy both**, **17 buy the second but not the first**, and only **2 buy the first
but not the second**. So 17 of ITUK's 64 dealers bought nearly the same filter from a different part number in
the same year.

**(d) The price reference.** The UK competitor file holds a live price for the first number — a UK parts
specialist listing both a genuine and a non-genuine air filter for this application:

| | Price |
|---|---|
| Our equivalent dealer price for the genuine number | **€49.98** |
| The specialist's own genuine listing | £55.00 ex VAT = **€64.35** |
| The specialist's non-genuine equivalent | £30.00 ex VAT = **€35.10** |
| **Our dealer price against the non-genuine listing** | **index 1.42** |

Read carefully, because the honest reading is not the flattering one. Against the same application's
non-genuine alternative, our dealer price is about 42% higher — normal for genuine versus non-genuine, and not
by itself a problem. Against that shop's genuine listing **we are cheaper** (index 0.78). So the price evidence
does not say "we are too expensive". It says: **a dealer who can be persuaded the non-genuine part is
equivalent has a €14.88 saving per unit on a part that dealer buys 12 times a year.** That is a
counter-argument-weaken-with-evidence question, not a price-cut question.

### Step 4 — The uncertainty that remains

Here is the point where Universe must stop, and say so.

Take any of those 24 dealers who bought no air filter of this number all year, or the 17 who bought the second
number but not the first. **We cannot tell whether that is a service behaviour or a counting artefact.** The
expected number we would compare them against is built as:

```
expected units  =  vehicles in service  ×  (km per year ÷ service interval)  ×  filter factor
```

Three of those four inputs are weak in exactly this market:

- **vehicles in service** — market level only, so it is the same number for a small rural dealer and a large
  fleet specialist. It cannot separate them.
- **km per year** — modelled at 50,000; the UK's own odometer records say 16,688 across classes, 12,891 for
  N35 and 35,478 for N75. **A factor of 1.4 to 3.0 in the wrong direction.**
- **filter factor** — the air-filter replacement ratio is a placeholder awaiting a manufacturer number.

So a claim like "these 24 dealers are under-servicing" is not supported. It might be true. It might be that
those dealers sit on a lower-mileage part of the fleet. **We cannot currently tell these two apart, and the
existing leakage file on disk does not resolve it** — see §6.

### Step 5 — The one optional item that would resolve it

**Average annual mileage of the N-series fleet, split by N35 and N75, from ITUK's own service records.**

One number per model family. Not a data feed, not a project, not an integration. It is the input that converts
a *relative* benchmark ("this dealer buys less than the network median, which may just mean the median dealer is
bigger") into an *absolute* one ("this dealer's fleet should need about N filters a year").

There is a second item, worth flagging because it is nearly as valuable and costs ITUK the same kind of effort:
**a list mapping each dealer name to its account number.** That single list unblocks the sell-through measure
that is currently 65,619 rows of `NOT COMPUTABLE`.

Both are small. The first has already been written up as a question to ITUK's Parts Director and **never sent**
(§8).

### Step 6 — What Universe returns once that arrives

With the mileage split, the exchange becomes a two-sided statement rather than a ranking:

> Your 64 dealers bought 5,259 air filters in 2025. On your own fleet size and your own mileage, the N75 parc
> alone implies roughly *X* filters a year. [Named dealers] are at a small fraction of that; [named dealers]
> are above it. Here is what each of them actually pays for the part, against both the genuine and the
> non-genuine alternative available in the UK today.

And the second cycle is automatic: once the monthly feed recurs, the same page shows what moved since the last
observation, against the same fixed denominator. **That is the flywheel** — not the report, the fact that the
report gets better each time the same distributor sends the same file.

---

## 6. One correction that matters to the design

The obvious objection is: *"this analysis already exists, I could just show them the leakage file."* It does
exist — `08_ITUK_dealer_leakage_by_category.csv`, 260 dealer-by-category rows, **4,226 units** of gap and
**€79,118** across nine families, built from real ITUK data.

**It should not be shown to a distributor, and the reason is in its own notes.**

- Its expected value is `dealer total units × network-median category share`. The file's own
  `benchmark_note` says it plainly: this is *"a relative benchmark, NOT modelled demand"*. So its output is
  "this dealer buys less than the median dealer" — which is largely a statement about dealer size, dressed up
  as a gap.
- Its category mapping is soft: the share of each dealer's units actually mapped into a category runs from
  **6.5% to 38.8%, median 16.3%**. Most of the units are not mapped. Dealers with zero mapped units are
  excluded, which removes exactly the cases the report is looking for.
- And it carries a euro figure with no fleet denominator beside it — the thing that makes a gap number
  meaningless, because a small dealer and a large one with the same gap need opposite responses.

The current view is a relative ranking built on an assumption. **The pilot's job is to replace it with a
sourced expected number** — which is precisely what the mileage item in Step 5 delivers, and precisely why the
pilot's first promised return is smaller than the existing file pretends to be. That is the point, not a
weakness.

---

## 7. The action is not always "sell more parts"

The brief asked for this explicitly, and it is the right ask, because a system that only ever concludes "sell
more" teaches the distributor to stop reading it. The evidence above supports at least seven different
outcomes, and in several of the cases below the correct answer is to do **nothing about parts**.

| Outcome | When the evidence points here | What it looks like in this pilot's terms |
|---|---|---|
| **No action** | The pattern is explained by fleet size or mileage once measured. | The 24 zero dealers may dissolve entirely. Reporting "nothing here" is a valid, and valuable, result. |
| **Technical validation first** | The part-number evidence is contradictory. | The 17-dealers-buy-the-other-number pattern may be a supersession or an application difference, **not** a behaviour. Confirm the two numbers' applications before anyone says a word to a dealer. This must come before any commercial read. |
| **BVP** | The dealer is choosing non-genuine, and the price gap is the reason. | The €14.88 per-unit gap against the non-genuine listing is a genuine-versus-competitive **range** question. Note also that the air filter `8970622940` already has a BVP pair in the cross-reference, so a Best Value conversation is technically available — it is a positioning decision, not a missing product. |
| **SPA** | A dealer's whole-book purchasing is below the network and the cause is commercial, not behavioural. | A targeted support arrangement, with the delta measured before and after. Already the live thread with ITUK (an SPA template request and a brake-parts target ask are both open). |
| **Supply investigation** | The gap is availability, not choice. | Ireland is the only market with real backorder lines; for ITUK the file is empty by design. If a dealer is not buying because they could not get it, this pilot cannot currently see that — and saying so is the honest output. |
| **Tender support** | There is a live opportunity the dealer's parts position affects. | Currently thin: **3 UK notices** in the live feed, all repair-and-maintenance, **two with deadlines already expired**. Treat tenders as a future panel and do not let them gate anything. |
| **Dealer discussion** | The finding is real, absolute, and the distributor should own the conversation. | The output is a brief the distributor takes into its own dealer relationship — not an ISZE message to a dealer. |

The general lesson for the design: **the deliverable of a cycle is a decision, and "no action, here is why" is
one of the valid decisions.** A flywheel that only produces asks will be switched off.

---

## 8. Missing prerequisites

Grouped by who has to supply them, because that is what turns into an ask list.

### 8.1 The five hard gates before any distributor sees anything

These are not data gaps. They are the conditions the R1 work already identified, and no amount of analysis
closes them.

1. **An approved dealer-to-IDS link**, if IDS is to appear beside a named dealer. Today 16 of 44 UK CV
   assessment names match the sales names exactly, with roughly 20–26 unresolved. Until approved, IDS must
   stay a separate pane with its own population, as R1 recommends.
2. **A permitted-sharing decision** — what an internal distributor note is allowed to contain versus what
   ISZE may see, and the reverse.
3. **A host and an access design.** The expected application host is absent, and hidden menus do not protect
   embedded all-network data.
4. **A named owner for the monthly refresh** at ITUK. A pilot with no owner becomes a one-off report.
5. **A decision on the four open business defaults** already logged in the R1 decision log (name mapping,
   Kaizen handling, support-case capture, tender phasing).

### 8.2 Data items, cheapest first

| Item | Who | What it unlocks | Cost |
|---|---|---|---|
| **Dealer name → account number** | ITUK | Sell-through per dealer; currently 65,619 rows uncomputable | One list |
| **Average annual mileage, N35 and N75** | ITUK service records | Absolute expected demand instead of a relative benchmark | One number per model — **already drafted, never sent** |
| **A true invoice-date extract** | ITUK | Proper period alignment; the current file has no invoice date | Export change |
| **Monthly (not annual) recurrence, dealer-level, 2026 onward** | ITUK | The second cycle — the whole point | Standing commitment |
| **Dealer-level fleet or territory** | ITUK | A real per-dealer rate instead of the national 22,389 | Hard, and may not exist |
| **Genuine / BVP split in the units file** | ITUK or ISZE | Quality of the mix, not just its size | Join exists; split does not |
| **The air-filter replacement ratio** | manufacturer | Removes the last placeholder in the demand formula | One number |

### 8.3 What exists but should not be trusted yet

- **The UK competitor source is one shop.** KS International, scraped weekly, most recent snapshot today. Only
  **16 rows match an ITUK part number**. Useful for illustration; **not** a market price index.
- **The 2023 Eucon UK survey** is genuine UK workshop purchase evidence and is three years old. Label the
  vintage whenever it is used.
- **The parts-demand model's own inputs** — mileage, the air-filter ratio, and the brake factors — are
  assumption-marked. Anything derived per vehicle inherits them.

---

## 9. What can be demonstrated immediately, and what needs ITUK

This is the split that decides how the pilot is scoped. The test is: *does this need a new message to ITUK?*

### Demonstrable today, from files already on disk, with no ask

- A named-dealer view for CY2025: all 64 dealers, quantity, parts, months active, share of network.
- A valuation for every one of those dealers — with the valuation basis printed next to it, and the
  unvalued share shown (median 4.4%, up to 23.6% on the worst dealer).
- Family and parts-level composition per dealer, from a classification that covers 99.95% of the numbers.
- A market reference: €248.54 goods billed per truck in 2025, 22,389 vehicles.
- Genuine-versus-contested/BVP proportions per dealer from the euro table.
- The UK competitor price comparison on the **8** part numbers where a match exists.
- The dealer-versus-IDS name-match position, with the unresolved cases shown as unresolved.

### Requires ITUK participation

- Any statement of the form "this dealer should be buying N units a year" — needs the mileage split.
- Sell-through, or anything about what ISZE invoiced versus what ITUK passed on per dealer — needs the
  account crosswalk.
- A recurring monthly review — needs the standing feed and a named owner.
- Anything a dealer sees — needs the sharing decision.
- Supply explanations for a gap — needs open-order data, which ITUK has not been asked for and Ireland is the
  only market currently supplying.
- Tender support at scale — needs a UK feed that survives the relevance gate, which it currently does not.

### Not demonstrable at all, and should not be promised

- A dealer-level trend, in any market, in any district. One year exists.
- A per-dealer vehicle rate. No dealer fleet exists anywhere.
- Any statement of market share, or of a dealer's retail sales. The layer stop at distributor-to-dealer; nothing
  in the workspace measures a dealer selling to a truck owner.

---

## 10. What we ask ITUK for next, and what ITUK gets in return

### The ask

**One message, three items, in descending order of value and ascending order of effort:**

1. **Keep sending it.** The same dealer-level, part-number, monthly sales-to-dealer file, for 2026 as it
   completes, on a monthly cadence, with a named owner for the send.
2. **The average annual mileage of the N-series parc, split N35 and N75 if available** — from service records or
   from the dealer network. A rough figure beats the assumption.
3. **The list that maps each dealer name to its account number.**

Item 2 has already been written as a message to Duncan Young, Parts Director at ITUK, and is **sitting unsent
in the workspace** dated 2026-09-18. It should be folded into the pilot conversation rather than sent
separately — it is the same relationship and the same subject.

Note carefully what is **not** being asked: no new format, no new system, no dealer-facing obligation, no
change to what ITUK already produces. Two of the three items are a number and a list.

### The return

Stated in the terms a distributor buys in, and no larger than the evidence supports:

| ITUK gives | ITUK gets |
|---|---|
| The monthly file they already produce | Their own 64-dealer parts picture, by family, with the outliers named — which they cannot currently see |
| — | A valuation basis printed on every figure, so nobody in the room argues about the number |
| A mileage number | An absolute expected-demand figure, which converts "this dealer buys less than the average" into "this dealer's fleet should need N" |
| A dealer-to-account list | Sell-through per dealer: what was billed versus what was passed on |
| The standing cadence | A monthly view of what changed since the last observation, against a fixed denominator |

### What must be said out loud when it is handed over

Three sentences, because leaving them out is what turns a useful tool into a credibility problem:

- The euro figures are a **reference valuation** at observed billing prices, not ITUK's turnover and not
  ISZE's invoices. Parts with no billing history value at zero, so the figures understate.
- The expected-demand numbers depend on a mileage assumption that is **currently 50,000 km/yr and is under
  review** — and the review is the reason for the question being asked.
- The parts-demand model is a model. It does not say a dealer is failing.

---

## 11. Evidence, commands and sources

### 11.1 What was run

All scripts are read-only and sit in this folder's `work/` directory. Nothing outside
`_STRATEGY\_ORCHESTRATION\PILOT_2026-09-21_01\` was written.

| Script | Produces | What it establishes |
|---|---|---|
| `work/verify_candidates.py` | `candidate_facts.json` | Grain, dealers, part numbers, periods and euro columns of all 15 sales-to-dealer files; ITUK month coverage; classification coverage; the fleet-denominator duplication; the competitor match count |
| `work/build_worked_example.py` | `worked_example_facts.json` | The Genuine/BVP cross-reference overlap; the family view; dealer-versus-IDS name matching |
| `work/build_worked_example_detail.py` | `worked_example_detail.json` | The air-filter split between the two part numbers; per-dealer spread; the parts-family layer |
| `work/check_alternatives.py` | `alternative_candidates.json` | Proof that every other distributor has one network row and no dealer row; the contents of the existing leakage file |
| `work/check_returnable.py` | `returnable_analyses.json` | Quality of the leakage file's own mapping; early-warning and attachment-rate coverage |
| `work/pin_numbers.py` | `quoted_numbers.json` | Every figure quoted in §5, re-derived |
| `work/final_checks.py` | `final_checks.json` | Source-file name, empty columns, the 65,619-row bridge, the unvalued-share range, the market fleet rows |

Run with `python <script>` from the `work/` directory. Python 3.14.3, pandas 2.3.3 present; the scripts use the
standard library only.

### 11.2 Sources read

**ITUK sales to dealer**

- `01_data\00_derived\dealer_sellout_long_ITUK_CY2025.csv` — 101,341 rows, the dealer layer.
- `01_data\90_INBOX\ITUK_dealer_sales_and_PRISM_2026-09-21\` — the pack built 2026-09-21: `03_ITUK_dealer_totals.csv`,
  `06_ITUK_dealer_euro_and_context.csv` (the 64-dealer euro table), `08_ITUK_dealer_leakage_by_category.csv`,
  `09_ITUK_replenishment_bridge_dealer.csv`, `00_START_HERE.md`, `07_..._NOTES.md`.
- `01_data\12_raw\dealer_sales\_registry.yaml` — the per-distributor source registry.
- `03_analytics\Isuzu\prism\data\dealer_sales\DEALER_SELL_OUT.md` — the layer definition.

**Classification, Genuine/BVP, fleet, prices**

- `01_data\00_derived\aim_pn_classification_v2.csv` — 164,667 rows.
- `01_data\00_derived\genuine_bvp_crossref.csv` — 544 rows, 431 genuine and 356 BVP numbers.
- `01_data\00_derived\gps_spu_by_distributor.csv` — the market context, including the warranty split.
- `01_data\01_Pricing\_raw\ks_aftermarket_price_compare_20260819.csv` — 105 rows, 16 matched.
- `01_data\00_derived\competitor_common_basis.csv` and `competitor_evidence_inventory.csv`.

**Identity, IDS, tenders**

- `01_data\00_derived\ids_dealer_network.csv` — 519 assessed dealers over 19 tabs.
- `01_data\90_INBOX\IDS_ATLAS_DATA_INVENTORY_2026-09-20.md` — the identity findings.
- `01_data\14_dashboards\tender_data.json` — 686 notices, 3 United Kingdom.

**The uncertainty**

- `09_meetings\ITUK_MILEAGE_QUESTION_2026-09-18.md` — the unsent question.
- `01_data\00_derived\_data_integrity_open_issues.md` — the mileage item and the warranty-limitation note.

**Universe's own prior work**

- `Isuzu Universe\ISUZU_UNIVERSE_CURSOR_PACKAGE_R1\UNIVERSE_R1_CURSOR_PACKAGE_2026-09-21\` — `02_UNIVERSE_ROADMAP_R2.md`,
  `03_CURSOR_R1_WORK_ORDER.md`, `04_DATA_AND_METRIC_CONTRACT.md`, `05_PILOT_STORY_AND_CONTEXT.md`.
- `Isuzu Universe\_STRATEGY\_ORCHESTRATION\R1_2026-09-21_01\R1_RETURN\` — the completed R1 return, including
  `SOURCE_MANIFEST.json` and `EVIDENCE\RECONCILIATION.md`.

### 11.3 Independent checks run

Two read-only searches were run to answer questions the file names alone could not settle, and both are
independently reproducible:

- **Competitor price coverage.** Verdict: a live UK source exists and is thin — one shop, weekly scrape, 16
  matched rows. The vendor feeds named for other markets (PartsPool, Autodoc) contain **no United Kingdom at
  all**, and the derived 18-market comparison files are **one UK price list repeated across 18 market labels**
  with no market dimension of their own. Treat any "UK competitor position" built from them as one shop, not a
  market.
- **Tenders and ITUK correspondence.** Verdict: UK tender sources are configured and healthy, but the relevance
  gate leaves **3** UK notices, all repair-and-maintenance, two already past their deadline. The ITUK contact
  is Duncan Young, Parts Director; the mileage question is drafted and unsent; the open SPA, P700 pricing and
  brake-evidence items are all on the same thread.

### 11.4 Not verified

- Whether the KS scraper is still yielding new prices — the files were read, the scraper was not run.
- Whether the 2023 Eucon UK survey workbooks hold anything beyond what their QA notes describe.
- Whether a per-dealer fleet or territory figure exists at ITUK and has simply never been asked for. **This is
  the single most valuable unknown in the pack** and it changes what the pilot can eventually promise.
- Whether `8970622940` and `8976739570` are a supersession pair, two different applications, or two
  concurrently-sold numbers. §5 Step 3(c) flags it; **it must be answered by ITUK before any commercial read of
  the 17-dealer pattern.**
- Anything about the second IDS round, because it does not exist. There is one round, with no per-dealer
  assessment date anywhere in the workspace.

---

## 12. Stop line

This pack is evidence and design input only.

- **No application change** was made, and none is proposed here.
- **No source file** was modified, rebuilt or regenerated.
- **No message** was drafted, sent or altered. The mileage question remains unsent, as it was.
- **No distributor has been approached** about a pilot.

The next step is the design pass on this evidence: turning §5 into the actual first cycle, §9 into a scoped
build, and §10 into the single message that starts the relationship. That design work should decide one thing
above all others — **whether the pilot's first promise is a better report, or a second cycle.** The evidence in
this pack supports the second, and only the second, being called a flywheel.

# Review of the Universe white paper and its visual edition

21 September 2026 · internal · for the business owner

Two PDFs were written this evening and both sit in this folder. Between them they carry one paper in two
editions, plus a printing defect that affects only one of them. The findings below come from eight separate
pieces of work on those two files: the text of both, the figures, the data behind the figures, the
guarantee term sheet, and the PDFs themselves inspected page by page.

---

## 1. What I reviewed

The files are `ISUZU_UNIVERSE_WHITE_PAPER_2026-09-21.pdf`, version 1.0, 58 pages and 882,485 bytes,
last written at 19:58 this evening, and `ISUZU_UNIVERSE_WHITE_PAPER_VISUAL_EDITION_2026-09-21.pdf`, the
"visual dynamics edition", version 1.1, 71 pages and 2,566,959 bytes, last written two minutes earlier at
19:56. The visual edition is almost three times the size of the other one, and once you have read section 3
you will understand that it does not carry three times the content.

Version 1.0 is the clean one. It contains no embedded images at all, only 441 vector drawings, which means
its diagrams are drawn on the page as lines and curves rather than placed as pictures. It prints exactly
what it says it prints.

Version 1.1 is not clean. It carries ten diagrams, and it prints each of them twice over itself in a way I
describe in section 3. That defect is visible on the page, and it is the most likely cause of the blur you
noticed.

The decision that follows is short: **version 1.0 is safe to circulate today and version 1.1 is not.** If
something has to go out before the duplication is fixed, send 1.0. It has no diagrams at all, but nothing on
its pages misprints.

The text of both editions, the admissibility notes on the figures, and the €300,000 guarantee term sheet at
`01_Strategy\UNIVERSE_300K_GUARANTEE_TERM_SHEET_2026-09-21.md` were all read for this review. Where a number
appears below it carries its period and the basis it was measured on. Where a file or a value could not be
confirmed on this machine, it is described rather than cited, so that nothing here points you at a path or a
figure that may not exist.

---

## 2. The verdict in one page

Your complaint is correct, and it is correct for a bigger reason than the writing. The paper is too general
for our use case because **five of the eight services it proposes cannot be built from anything on this disk
today**, and two of those five have no source at all. The writing is a real but secondary cause. This is a
strategy document being read as a build specification, and a strategy document is under no obligation to
carry screen inventories, field lists and refresh schedules. It chose not to, said so four times in its own
words, and that choice is exactly what makes it feel thin when what you want is something to build.

The reason five of the eight have nothing to stand on is worth stating plainly, because it is not laziness
and it is not an oversight in the data collection. The eight services divide by where the event happens, not
by how important they are. Some of them describe events ISZE's own billing already records: what was billed,
to which account, on which day. Those are buildable. Others describe events that happen between the
distributor and the dealer, or between the dealer and the truck owner — a quotation that was put in, a job
that was won or lost, stock sitting on a shelf, what the dealer then sold on. ISZE is not a party to any of
those, so on ISZE's side they leave no record at all beyond a part that eventually shipped. And a third group
describes events that would have needed a reason to be written down at the moment they happened — why a
purchasing pattern changed, what a follow-up achieved. Nobody ever designed a field to hold those reasons, so
the reason was never captured and cannot now be recovered by any amount of analysis. That is the mechanism
behind "too general": the paper is describing a product whose inputs live in three different places, and only
one of those places is ours.

The most damaging single gap is not a missing report. **Nothing on disk links a dealer to the entity that
bills it.** ISZE invoices the distributor, not the dealer. From our billing system's point of view the dealer
is the distributor's customer, not ours, so there was never a reason to hold a dealer's identity in it. The
consequence is that the file `14_ITUK_purchasing_monthly.csv` already contains the two columns the join needs
— `source_account_id` and `source_account_name` — and both are blank on all 66,018 rows. They are blank for a
concrete reason: there are only three purchasing accounts in scope on our side, all three of them ITUK's own
accounts, so there is nothing on the ISZE side to place beside a dealer site. The coverage file
`Isuzu Universe\06_Working\_work\ITUK_IDS_AIM_EXPORT\_pack20\19_COVERAGE.csv` states the position literally:
"purchasing accounts mapped to a dealer site, 0, 3, 0.000", with the note "not possible —
ISZE invoices the distributor, not dealers". All 65,619 rows of `replenishment_bridge_ituk_dealer.parquet`
read "not computable at dealer grain", for the same reason. One column pair from ITUK's own customer master
closes the part of this that can be closed, because ITUK is the only party that holds both halves.

The two services that matter most exist at dealer level in exactly one market for exactly one year: ITUK,
calendar 2025, 64 named dealers. Every other market — IUK, IRELAND, GREECE, UTI, PORTUGAL and ROMANIA — has
national totals with the dealer names stripped out. That was true before anyone looked, and it will stay true
until a distributor decides to send the dealer names, which is why the request in section 11 is framed as
plainly as it is. There is also no dealer trend to show, because 2023, 2024 and 2026 exist only as national
totals and cannot be split back down to dealers after the fact.

The paper's stated foundation does not hold up either. It asserts, citing its own source [U01], that dealer
self-assessment information and sales-to-dealer information "can be supplied", and treats that on page 4 as a
settled foundation rather than a question to reopen. What is on disk is seven markets that each sent one
file, and a registry covering seven distributors out of eighteen. One file from each of seven markets is not a
cadence; it is seven single events. Nothing in the material shows a second round for any of them.

---

## 3. The two printing defects

The first defect is duplication, and it is worse than it looks. **The visual edition prints each of its ten
diagrams twice.** Every figure page carries a raster copy of its own diagram laid over the sharp vector
original, so each figure shows a ghost of itself, offset by a small amount. That doubled edge is almost
certainly the blur you saw, and it is a printing fault rather than a design choice.

The cause is visible in how the file is assembled. A page that carries both a placed picture and a drawn
original has been built twice from the same source figure: once as a picture, and once as the drawing itself.
The giveaway is in the image pool. All ten raster images are referenced on all 71 pages, not only on the ten
figure pages, which is what happens when a document is exported with one shared image library covering the
whole file rather than a picture attached to each page. The figures were therefore generated or inserted
twice in two different forms, and both survived into the final print. Because the source document is not on
this machine, I cannot name the exact setting that produced it; what I can say with confidence is that this
is an assembly fault at the point where the figures were added, not something a reader or a printer did.

The waste is measurable. On every figure page, 171 KB of the 197 KB of image data is the leftover raster crop
that should not be there, which is where the extra 1.7 MB of file size largely goes. The clearest way to
describe what happened is that each of the ten diagrams exists twice on its page — once as a placed image and
once as the drawing itself — and that duplication, not the image count, is what produces the doubled edge. It
is also worth clearing up one earlier misreading: pages 25 and 37 do
paint their pictures, and a note claiming they were missing was wrong.

The second defect is how the images are stored at all. **All ten raster images are referenced on all 71
pages, but only drawn on the ten figure pages.** They are document-wide resources added for viewer
compatibility, and that is why they inflate the file by roughly a megabyte over what it actually needs. A
reader opening the file carries the whole library on every page whether or not that page shows a picture.

Neither defect can be fixed here, and the reason is worth being precise about. The source file does not exist
on this machine. There is no mark-of-the-web on either PDF and the owner is the local Windows account, so
neither arrived as a browser download. More decisively, there is no LibreOffice installed anywhere on the
drive: no `.odt` or `.fodt` file, nothing relevant in the recycle bin, no recent-documents entry. The PDFs
carry a LibreOffice 25.2.3.2 producer stamp, and nothing on this PC can produce that stamp. That is not a
guess about where the file went; it is a statement that the tool that made it is not installed here. The paper
was authored and printed elsewhere, so **the duplicated figure layer has to be fixed at the source**, by
whoever holds the original document. An earlier claim that the source had been "swept up" locally was wrong.

---

## 4. Why it reads as too general

The paper tells you what it is, four times, and the four statements are the key to the whole complaint. It is
"not a specification for a single dealer page". It states that "the paper does not invent response-time
targets". It says that "no calendar deadline or adoption target is invented by this sequence". And it says of
itself that "it does not establish implementation". A document that announces four times that it is not a
specification will inevitably read as general to someone holding it to a specification's standard. That is a
category mismatch rather than a writing failure, but the mismatch is real, and it is why the complaint lands
even though the sentences are clear.

The mechanism is worth following through, because it explains something you have run into before. The
document was written at the level where decisions are still open: what the product is for, what principles
govern it, who owes what to whom. A build specification needs the layer below that, where the decisions have
been made: which fields, from which system, refreshed how often, owned by whom. Those two layers cannot be
written by the same pass, because the second one requires choices that belong to the people who will own the
work. Someone writing a strategy paper that explicitly refuses to invent targets cannot then supply the
thresholds a builder needs, and the four self-limits are the author telling you so in advance. The paper
chose the honest boundary and drew it in the wrong place for your purpose.

It is also not a thin document, and that matters because the first impression is misleading. Measured
properly, the median page carries **452 words in version 1.0 and 402 in version 1.1**. An earlier claim that
the paper was unusually thin came from dividing its word count by a 250-word A4 page, which does not apply to
10.5-point type on a 6.2-inch measure. Applied properly, the paper is normal for its kind. The only genuinely
thin pages are the ten diagram pages, and those are thin on purpose.

What it genuinely lacks is a specific list, and each item on that list is missing for the same reason: it
needs a decision rather than more words. There is no screen and journey inventory showing the fields on each
screen. There is no table mapping each field to the system that supplies it, with how often it refreshes and
how it is validated. There are no named owners with the capacity they would need to carry the work. There is
no sequenced plan with effort and dependencies attached to each step. And there is no threshold anywhere at
all: no response times, no retention durations, no adoption targets, every one of them deferred by design.
Roughly a third of its "should" statements could be tested as written, and about one in six concerns attitude,
trust or culture, which cannot be built or tested no matter how carefully they are worded.

Its proportions are wrong for its own subtitle. Roughly **40% of the words argue participation, trust and
economics** that nobody will act on, while each of the eight services gets a single page. That is a strange
allocation for a paper whose purpose is to make eight services happen, and it has a cause: arguing for the
principle is open-ended work that a writer can do alone, whereas specifying a service requires the owner to
exist and to agree to be named. The paper spent its length where it had freedom, and went quiet where it
needed someone else's decision.

The clearest example is the chapter titled "The response ISZE owes". It names the obligation and then declines
to define it, setting no response times at all. Response classes are the one thing a strategy paper could have
made concrete at no cost, and the paper itself lists the five it would use: routine information, an
application check, a commercial decision, a supply investigation and a fuller service analysis. It defines the
categories and withholds the clock, which leaves the most useful half of that chapter unwritten. I come back
to why in section 9, because that same gap is what breaks the guarantee.

The visual edition did not fix the complaint; it diluted it. Version 1.1 added about 8% more words across 13
more pages, and pages carrying under 250 words went from four to eighteen. Its appendices are identical to
version 1.0's, section for section, so an earlier claim that the visual edition shortened its appendices is
wrong. What happened is that the concrete material was left exactly as it was while air and diagrams were
added around it. Adding explanation is easy authoring; adding a field list is a decision, and the diagrams
were cheaper to produce than the specification. That is why the second edition reads more general than the
first, not less.

---

## 5. What the paper does well

This is not a hatchet job, and the credit belongs in writing rather than as a courtesy. The analytical-rules
chapters — pages 44–45 in the visual edition — are a clearer statement of measurement discipline than the
earlier internal notes produced. The paper keeps UTI and UMI separate and records that **UTI did not
participate in the 2026 assessment round**; that matters because the two are separate distributors with
separate systems, and a blended Israel figure would put one distributor's numbers against a network that was
never assessed. It keeps ITUK and IUK apart for the same reason, never blends the commercial flows, and
refuses to repeat figures that are in dispute. It carries a glossary, and it carries acceptance tests and a
field catalogue that are genuinely usable as a starting point. It also identifies its own weakest link
correctly. It simply leaves that link unfunded, which is the subject of section 9.

---

## 6. The data position, service by service

"With gaps" means a real file exists and something on the page would have to carry a warning. "Not buildable"
means no source on disk supports the service as described.

| # | Service | What exists, with grain | Buildable? |
|---|---|---|---|
| 1 | Connected dealer review | ITUK sales-to-dealer file, calendar 2025, dealer-month grain, 64 named dealers. IUK, IRELAND, GREECE, UTI, PORTUGAL and ROMANIA hold the same grain with zero dealer names; 2023, 2024 and 2026 are national totals only | With gaps — one market, one year, no trend |
| 2 | Quotation and commercial support | No quotation record, no case log, no won-or-lost outcome anywhere | Not buildable |
| 3 | Parts availability and range | Only what was billed is held, not what was available; no stock record at any grain | Not buildable |
| 4 | Application and Genuine/BVP guidance | AIM parts classification exists, but the release is not pinned: three candidate files, no authority named, 2,728 part numbers recorded as drifted | With gaps — inside ISZE only, until a release is named |
| 5 | IDS improvement follow-up | 519 dealer self-assessment records across 19 country lists, one round, no per-dealer date; 514 distinct names. Registry covers 7 distributors of 18 | Not buildable — a follow-up needs two comparable rounds and there is one |
| 6 | Fleet and workshop support | The Cordwallis (Heathrow) calendar 2025 case, built and verified at 104 checks with 0 failures. No per-dealer fleet exists anywhere | Buildable now, in that scope only |
| 7 | Tender and fleet-opportunity service | No won-or-lost outcome record and no tender case log at case level | Not buildable |
| 8 | Participant record of decisions and benefits | Nothing records why a purchase changed: no reason field, no decision log, no explanation record | Not buildable |

Five of the eight sit in the right-hand column, and two of those five — services 2 and 8 — have no source at
all. The pattern behind that column is not about effort or importance, and it is worth taking service by
service, because each one fails for its own concrete reason.

Service 2, quotation and commercial support, fails because the event happens outside ISZE and nobody wrote it
down. A quotation is put together by a distributor or a dealer for a truck operator, and whether it was won or
lost is known to them. The only trace it can leave on our side is a part that eventually ships several months
later, which tells you the job was won but never that a quotation existed, what was in it, or what it was up
against. Service 7, the tender and fleet-opportunity service, fails identically and for the same reason: there
is no case log and no outcome record at case level, so the service has nothing to review.

Service 3, parts availability and range, fails because the file records a shipment rather than a shelf. What
ISZE holds is what was billed, which is what left our side. What was available at the dealer's counter, in
what quantity, at the moment the customer asked, exists only in the distributor's own system, and no record of
it has ever been sent. That is not a gap that better analysis closes.

Service 5, the IDS follow-up, fails on a date rather than on a missing file, and the detail matters. The
self-assessment workbook does carry a `Date:` field; it is simply unpopulated. So 519 dealer self-assessment
records across 19 country lists, 514 distinct names, arrive with no per-dealer date, and a follow-up is by
definition a comparison between two rounds. With one round in hand, there is nothing to follow up against yet,
and with no dates there is no way to order even the round that exists.

Service 8, the participant record of decisions and benefits, fails because the billing system records what
moved and never why. There is no reason field, no decision log and no explanation record anywhere in the
material. A dealer's purchasing pattern can be seen to change; the reason for the change was never captured at
the moment it happened, and it cannot be reconstructed afterwards. This is the one gap on the list that no
external party can close for us either, because the reason existed only in a conversation.

Services 4 and 6 are the two that can move, and both move for reasons worth naming. The Cordwallis case is
buildable now because the workshop book and the sales file happen to overlap in calendar 2025 at dealer level
for one dealer, and the work has already been done once and verified. The classification service is buildable
internally because AIM exists, but the release is not pinned: there are three candidate files with no
authority declared between them and 2,728 part numbers recorded as drifted, so a family label cannot yet be
printed outside ISZE.

**The gap that governs everything else is the dealer-to-account link, and it is structural rather than
technical.** ISZE's billing system identifies a customer as a sold-to account, and the account it holds is
the distributor's. The distributor's sales-to-dealer file identifies a dealer as a name. Those are two
different namespaces held by two different organisations, and nothing has ever bridged them, because from
ISZE's side there was no commercial event that required a dealer's identity. The three purchasing accounts
that exist are ITUK's own accounts, which is why the coverage check reads 0 of 3 rather than a partial
number. Everything priced, everything compared per truck and everything measured per dealer needs that bridge,
and section 11 is the ask that builds it.

---

## 7. The numbers

The workspace health check is green, at
`C:\Users\jerom\Desktop\claude\ISZE\01_data\00_derived\_verification_report.json`. The verdict sits at the
nested key `summary.ok`, value `true`, beside 153 passes, 2 warnings and 0 failures, generated
2026-09-21T12:51:06Z. It is `summary.ok` and not a top-level flag; an earlier note that placed the key at the
top level was wrong about the path and right about the result. It is worth noting that the check was
regenerated at 14:51 this afternoon, roughly five hours before the two PDFs were written, so the paper was
produced with a current green check available to it.

That green report does not certify any figure in this paper, and the reason is a design feature rather than a
fault. The check verifies that the pipeline runs and that its own declared expectations hold. It does not hold
the disputed commercial claims, and the dispute records say so directly: the report "contains none of the
disputed numbers — not 365,093, not 223,897, not 248.54, not 2,402". Its only hit is 22,389. **The claim
register is the authority for these numbers, not the health check**, which is why a green dashboard and a
disputed figure can both be true at once and why the dispute record has to be read alongside the report rather
than instead of it.

The snapshot is stale, and again the cause is worth stating because it will recur. `metrics_snapshot.json` is
frozen at `as_of: 2026-09-17T13:47:43Z`, and the file itself was last written on 17 September at 15:47. It is
produced by its own script, `scripts/build_metrics_snapshot.py`, on its own schedule, which is separate from
the health check that ran this afternoon. Billing, meanwhile, kept arriving. The current parts base is
**€117,600,501 through 2026-08-31**, not the €112,089,307 the snapshot carries, which was the 2026-06-30 cut.
The three values €103,573,715, €112,089,307 and €117,600,501 are one series at three cut-off dates, not three
different numbers. The report itself warns that the lost-sales model is current only to 2026-06-30 while
billing runs to 2026-08-31, leaving €5,511,194.53 of later billing outside it. Every one of those facts points
the same way: the snapshot lags the billing by whatever period nobody has re-run the script, so any figure
quoted from it is a figure for a two-month-old cut unless someone says otherwise.

**Four figures must not be published.** The **32.4%** ITUK figure predates the split that moved ITUK to 45.6%,
and pairing it with the current parts base mixes two methods, which is why it cannot travel even though it was
once correct. The **61,791** and **37,019** km/yr mileages must never appear as an all-models pair. Any single
ITUK capture rate **above 100%** is unplottable at face value, and the reason is a denominator problem rather
than a data error: two of them sit at 106% and 133%, which happens when the number of units billed is
measured against a smaller expected population than the one actually buying. And the **54.4%** sales-to-dealer
coverage share could not be re-derived from any cited source, so there is no defensible way to print it.

The **47%** figure is usable only with its denominator named, because there are four ways to count the fleet
and each gives a different percentage. The metric dictionary records that the two live ITUK percentages differ
by 14.6 points on identical billing — the same euros, two answers — and instructs: "Do not put either on a
page that leaves the building until that split is resolved." Until that split is closed, naming the
denominator is the only honest way to use either number.

**Six figures are safe, with this exact wording:**

> €117.6m of parts billed across 22 distributors, 2023-01-03 to 2026-08-31; the UK lane ends 2026-06-30.

> ITUK spent €248.54 per truck in 2025 against a reference ceiling of €11,835,911 on 22,389 trucks — 47.0% on
> the upper-reference basis.

> ITUK's uncaptured service-demand value is €2.11m in 2025, on a 50.85% capture rate measured against the
> N75-scoped denominator. (50.85%, not 50.9%; the denominator is 23,068 N75 buckets, not vehicles.)

> ITUK's 64 named dealers took 223,897 units in CY2025 (month rows only).

> €55.3m ceiling, of which eight markets sit on a flat €250-per-truck placeholder holding 40.3%.

> 519 dealer self-assessment records across 19 country lists, one round, no per-dealer date; 514 distinct
> names.

Two corrections to earlier claims. The N35 mileage median rests on **74 vehicles, not 35** — too small a
sample to headline, whatever it says. And the ITUK capture denominator is a bucket sum, not a count of
vehicles, which is the kind of distinction that changes what the percentage means.

None of this is a revenue forecast, and the €55.3m ceiling must never be presented as one. It is a modelled
target-spend ceiling: it describes what the market could spend, not money available to us, and multiplying it
by a recovery percentage would invent a revenue case the paper itself refuses to make. Drafting any of these
figures into the paper is a rebuild of a shared document and needs your explicit go-ahead. It does not have
it, and the check that governs anything leaving ISZE is not passed.

---

## 8. The €300,000 question

**€300,000 cannot be justified as a return from anything on disk.** It is defensible only as a capped, staged
fund released against things a contract can observe. The paper itself refuses to be a return estimate, and
the term sheet at `01_Strategy\UNIVERSE_300K_GUARANTEE_TERM_SHEET_2026-09-21.md` reaches the same conclusion
in its own words.

The reason it cannot be justified is not that the money is unwise; it is that the thing being bought does not
have a measurable starting point. A return calculation needs two measurements, one before and one after, on
the same basis. The product's benefit is redeemed when a question is answered and somebody acts differently
as a result, and nobody has ever measured how many questions are asked today, how long they take to answer,
or how often the answer changes anything. The term sheet says this in its own conditions: a starting
measurement of the existing process comes before any target. Until that measurement exists, a return figure
would be an invention, and the honest form for the commitment is a ceiling on deliverables rather than a claim
on a gain.

A contract can enforce named deliverables by named dates; a named individual per service and per case, not a
team name; a substantive answer within an agreed class and time; the monthly sales-to-dealer file with its
four minimum fields — dealer identifier, part number, period, quantity — plus a coverage declaration; a named
pilot market with a named distributor owner; data accuracy and coverage thresholds; and defined milestones,
each evidenced rather than reported. Those are all things that either exist as a file or do not, which is what
makes them enforceable.

No contract can enforce incremental profit; that a won quotation would otherwise have been lost; dealer resale
behaviour; freedom from displacement between dealers; market growth; or a chain of cause running from a
documented decision to a measured result. The paper says each of these itself, and the reason each resists
contracting is the same: every one of them requires knowing what would have happened instead, and no
measurement of an alternative that did not occur exists anywhere. The honest guarantee is the decision record,
not the cause.

Two comparables exist and neither supports €300,000. The first is a **€30k** ITUK support incentive: one
distributor, one year, paid as a rebate against a defence programme. It shows ISZE does commit support money
to a distributor, and that is all it shows, because a rebate records that money moved rather than what the
money bought. The second is the FY2027 price revision — locked **+3% = +€383k per year on the last 12 months
and +€436k per year on forecast weights**, +4% = **€581k / €510k**, +5% = **€726k / €638k**. That is a
decision about the price list, taken on the same 6,326 part numbers on both bases, and it must never be
presented as a Universe return: it is money we would collect by charging more for the same parts, which is a
different question from whether a new service earns its keep.

The recommended instrument is a staged release against milestone checks, with the final stage held back until
the recurring exchange has actually repeated once and its corrections have been handled, and with recovery or
offset of any release that fails to evidence itself inside its cycle. The reason for holding the last stage
rather than the first is that the paper's own test of success is repetition — repeated use for eligible work,
and a participant who would continue if the reporting incentive disappeared. Repetition only shows up after
the first cycle, so the release schedule has to leave something behind to pay for it. Linking release to key
performance numbers is the weakest option of all, because it needs a starting measurement and a target, the
starting measurement has not been taken, and the paper refuses to set targets it cannot earn. A key-number
release would therefore be negotiated against numbers neither side could defend.

**The recurring cost, offered as an estimate and not as a figure found on disk.** Once two or three markets
are live, a fractional internal function covering roughly 2–4 case types at 30–80 substantive cases a month
implies about **1.5–2.5 full-time equivalents**, plus distributor-side owner time, plus product maintenance.
At an indicative €90–130K fully loaded per person per year that is roughly **€150–350K a year, recurring,
before any software** — the same order of magnitude as the amount being asked for, and it recurs every year
while the €300,000 does not. The case volume is inferred from the shape of the service rather than measured,
so treat the range as a reasoning aid and not as a quotation. The point of putting it beside the €300,000 is
not to argue against the money; it is to make clear that the €300,000 buys the first step, and that whatever
steps follow have a running cost that is already the size of the request.

---

## 9. The weakest link

**The guarantee breaks on the response, not the data.** The product's value is redeemed only when ISZE answers
a distributor's or dealer's question, and nothing on disk shows that this function exists, is owned, or is
funded. There is no support-case register at case level. Where a response owner is recorded it is a role with
no person attached: the worked ITUK case reads "ROLE: ITUK commercial / parts operations" with no individual
named, and "Nothing has been sent to ITUK".

The mechanism behind that gap is the most important thing in this review, because it explains why the same
failure will repeat. Software is cheap at the margin and a person's time is not. The paper says so in its own
words on page 25: "A low marginal cost for software does not mean the response service is free." Page 27 sets
out the consequence: "Software cannot substitute for an operating commitment... Otherwise, better data
collection simply makes unanswered requests easier to count." That is exactly the trap this product is built
over. The data collection is the half that can be specified, budgeted and built by a project. The answer is the
half that requires a named person with hours in the week, and it has no home in a project budget because it is
a recurring cost with no measured return attached to it. So the cheap half gets built and the expensive half
gets deferred, and the product arrives looking complete while the thing it was for never happens. The paper
even names the three separate responsibilities — the function that triages, the specialist who answers, and
the case owner who keeps the participant informed — and leaves all three unnamed.

The one named support programme makes the same point from the other direction. Don't Lose the Deal is ITUK's
programme for competitive quotes, defending the job when a dealer faces an alternative, and it returns **0
hits across every column of all 538,346 billing rows**. What a programme like that can leave on the billing
side is a payment, and a payment records that money moved rather than that a question was asked or answered. A
case register would have to hold the part, the dealer, the competitor evidence and the outcome; the glossary
notes for comparison that a credit note proves support was paid but does not prove the customer was kept. One
searches in vain for the label and the other describes what the programme is, and the distance between them is
the missing register. I flag it as a discrepancy to resolve with the sender rather than a settled fact, but
either way the conclusion is the same: at case level, there is nothing to review.

The organisation has already demonstrated the specific failure, and recently enough to be discouraging. A
mileage question to the ITUK Parts Director was drafted on 18 September 2026 and **never sent**. The file is at
`C:\Users\jerom\Desktop\claude\ISZE\09_meetings\ITUK_MILEAGE_QUESTION_2026-09-18.md`, 3,624 bytes, last
written on 18 September at 17:17, and
`Isuzu Universe\_MERGED_MASTER_2026-09-21\16_OPEN_QUESTIONS_BY_RECIPIENT.md` §2 records it as "already
drafted, unsent" with an instruction not to re-draft it. Three days later it is still unsent. That is a
response gap and not a data gap,
and it is the honest reason to be careful about the €300,000: the money would buy the machinery for asking
questions in a week when a question we already wrote down is still sitting on disk.

---

## 10. What can be built now with no ask

There is a pilot that needs no answering desk at all, and the reason it needs none is that it asks nothing of
anybody: every input is already a file on this machine, and it promises no response from any person. That
single design choice is what separates it from the other seven services.

The scope is one distributor (ITUK), one dealer — Cordwallis Commercials at Heathrow, workshop 15 — one family
(engine filters, oil and fuel), and one year (calendar 2025). The reason this scope works is that the workshop
book and the dealer-level sales file overlap in calendar 2025 for this one dealer, and nowhere else at dealer
grain.

It has already been built once and verified: the case ran **104 checks with 0 failures** (`all_pass: true`) at
`C:\Users\jerom\Desktop\claude\ISZE\Isuzu Universe\_STRATEGY\_ORCHESTRATION\ITUK_CASE_2026-09-21_01\evidence\C04_verify_return.json`.

The figures that reconcile, each verified directly from source: **72 trucks, 70 on part lines, 269 jobs and
1,627 lines**; a parts value reference of **27,543.79** in the workbook's own money unit, with no currency
declared, so it must never be labelled euro; **147** fitted units on the twelve named numbers and **148** on
the consumable family; **719** bought on the twelve, **836** on the consumable elements and **852** on the
wider family, monthly rows only. Measured intervals print as a band with the count beside them, never as a
single number.

How each of those is labelled is not a choice. The truck count is what was seen in the contract workshop book,
which makes it a floor rather than the dealer's fleet, and the reason is that vehicles move between workshops:
**55.7% of the vehicles in the network were serviced at more than one workshop**, so a per-workshop count
undercounts any dealer's fleet by construction. The parts value prints with no currency attached because the
workbook declares none, and sterling is a working assumption rather than a finding. Fitted units print with
the population named on the face of the figure, so nobody reads 147 as a network number. And the
fitted-against-bought comparison prints as **explicitly blocked**, because those two sets come from different
populations and different channels and cannot be joined; the difference between them is never a gap, a leak or
a shortfall, and the page has to say so rather than leave a reader to work it out.

It cannot show what was needed, what the dealer sold onward, why fitted and bought differ, any profit, any
chain of cause, or anything about a second cycle. The reason a second cycle is impossible today is concrete:
the sales file is complete on 2025 and the workshop extract ends 2026-03-17, so the two overlap in 2025 only,
and there is no later matched period to compare against. It also cannot generalise, because 32 accounts match
one-to-one under the audit's own normalisation
(`Isuzu Universe\_MERGED_MASTER_2026-09-21\11_DEALER_PAGE_SPECIFICATION_CORRECTED.md` §2 — "32 such
accounts on the audit's own normalisation, not 38") and every one of them still needs individual inspection
before
anything is said about it. A name match is identity, not approval.

Run it internally and file-based, with one named owner of the folder and a stated rule that nothing leaves
ISZE. The hosting problem shrinks in that mode but does not disappear, and it is worth being clear about the
order of the two problems: the publishing folder carries wider-network data that does not belong on a
dealer-facing page, and hiding a menu does not protect data that is embedded underneath it. External sharing
is a data-separation question before it is a login question.

---

## 11. The one-column ask

A single two-column list from ITUK's own customer master: the dealer name, and the account number ITUK bills
that dealer under. Both halves have to come from ITUK, and that is exactly why the two columns sit blank in
our file today: ITUK is the only party that holds both the dealer names and the accounts it bills them under,
and we hold neither. This is the smallest possible request that closes the largest gap, and it is small
deliberately.

The acceptance test the sender runs is measurable, which is what makes the list worth having. Each of the 64
names must appear exactly once and each account number must appear exactly once; if either count differs from
the distinct count, the list is not one-to-one and must come back as groups rather than forced into pairs.
State how many of the 64 are covered. Where there is no account, write `UNRESOLVED` — never leave it blank and
never fill it by matching a similar name, because a plausible-looking guess is worse than an admitted gap and
would carry silently into every figure that uses it. Where one dealer trades under several names, or one
account covers several names, say so in a third column. The three ISUZU TRUCK (UK) LIMITED accounts 2575, 2194
and 146 must not appear mapped to a dealer site; those are the distributor's own accounts, so if one of them
turns up beside a dealer name the mapping is pointing in the wrong direction and the list has to come back.

The ask itself, as it can be sent:

> Please send the dealer name and the account number you bill that dealer under, one row per dealer, for the
> 64 dealers in the calendar 2025 sales-to-dealer file. If a dealer has no account, mark it UNRESOLVED rather
> than leaving it blank. If one dealer trades under several names, or one account covers several names, add a
> third column saying so. Send it as a spreadsheet with the two columns as text, so the account numbers keep
> their leading digits.

What it must not ask for, and the reason: prices, margins, stock, customer names, fleet or customer data, VIN,
workshop repair orders, competitor invoices or a full price list. Bundling any of those makes the request look
like ISZE trying to see through the distributor rather than fill a gap in our own records, and once that
impression forms it is hard to undo. The earlier records put the risk sharply: asking early "teaches the
distributor that contributing costs more than it returns, and that lesson is expensive to reverse". A request
that takes one person an hour to answer teaches the opposite lesson.

Be honest about what it unlocks, because the honest account is smaller than it looks. It fully unlocks one
thing: the fitted-against-bought comparison for the one dealer, which is currently blocked. Five other
services get partial help, in the sense that a dealer name tied to an account makes a page possible without a
collision. Two get no help at all: there is still no per-dealer fleet anywhere in the material, so no
per-dealer rate can be computed from it, and there is still only one dealer-level year, so no trend is
possible. And it resolves identity rather than billing. An account map connects identities; it does not create
dealer-level ISZE billing, it does not establish stock, and it is not proof of onward sale. Anyone who reads
it as a way to see the distributor's sales will be disappointed, and that is worth saying before the list
arrives rather than after.

---

## 12. The decision in front of you

Three decisions are open, and each is a yes or no.

First, do we authorise the file-based ITUK / Cordwallis pilot to run internally, with one named owner of the
folder and a stated rule that nothing leaves ISZE? Yes or no.

Second, do we approve €300,000 as a ceiling against staged, evidenced delivery by a named pilot market, with
release only on a verifier's pass at each milestone — understanding that it is a cap and not a return, and
that no return number exists? Yes or no.

Third, do we send the two-column dealer-to-account request to ITUK as it stands, or hold it until the pilot
conversation so the two arrive together? The earlier records warn that asking too early is expensive to undo,
so this one is worth answering deliberately rather than by default.

What remains unresolved, and it is a single thing: nobody has yet named who answers the distributor's
question. Every other gap in this review has an owner somewhere who could close it. That one does not, and it
is the one the money depends on.

---

## Appendix — page-reference map

The two editions number their pages differently, so any citation of the paper must say which edition it refers
to. This mapping was verified page by page.

| Passage | v1.0 (58 pages) | v1.1 (71 pages) |
|---|---|---|
| "Software cannot substitute for an operating commitment" | page 27 | page 36 |
| "The paper does not invent response-time targets" | page 27 | page 36 |
| "The paper recommends the measurement design, not unearned numerical targets" | page 29 | page 39 |
| "This is deliberately not a programme ROI estimate. No approved Universe budget…" | page 47 | page 60 |
| "No calendar deadline or adoption target is invented by this sequence" | page 37 | page 50 |

One further point belongs here. The guarantee term sheet at
`01_Strategy\UNIVERSE_300K_GUARANTEE_TERM_SHEET_2026-09-21.md` cites the paper at pages 47, 29, 26, 27 and
25, which are version 1.0 page numbers, while also referring to content that appears in the visual edition. It
also renders one quotation as "do not invent response-time targets", where the paper's actual wording is "The
paper does not invent response-time targets". Its references need re-cutting against one named edition before
it goes to anyone, otherwise a reader holding the wrong edition will look at the wrong page and conclude the
quote is missing.

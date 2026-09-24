# Aftermarket intelligence — what we hold, what it is worth, how to proceed

**Written:** 2026-09-24, internal. Read-only pass; nothing built, nothing fetched, no price moved.
**Why:** Opus reviewed the competitor-price plan and asked one question it could not answer from the
brief — *what is the cross-reference coverage of the 491 Tier A parts?* Jerome then added two more
Eucon files and asked to structure the data, look at the cross-references, merge the scraper work
with the AIM work, and think forward.

**Verified by:** eight read-only probes, listed at the bottom. Every number below was computed today
from files on disk. Where a number replaces an earlier published one, it says so.

> **CORRECTIONS, 2026-09-24 16:45 — three claims in the first version of this note were wrong.
> They were made from a first reading of the two new files and did not survive being checked.**
>
> 1. **"4,652 rows in the July file are our own list price, worth €3.70M."** Wrong twice over.
>    Those 4,652 rows carry a column called `OE RRP` — a price **for our part number**. It is not
>    our list: on the eight numbers where both exist it runs **2.46× to 3.14×** our list. And it is
>    not an aftermarket rival's price either. **I have not established what it is.** The €3.70M does
>    not exist in that context; €3.70M is the billed value of the 88 part numbers, and separately
>    the 2024 RRP sheet carries €3.70M of our own prices. Two different things, one number.
> 2. **"Two duplicate part numbers in the seed list."** False. The ranked list is 16,511 rows and
>    16,511 distinct numbers. The duplicate I saw was in the **price list**, which is a different
>    file and a different question.
> 3. **"We hold one price per part number, not one per country."** The opposite: `OE RRP` is
>    **country-specific**. Only 9 of the 88 part numbers hold one value across all countries.
>
> One of the four findings stands, and it is now confirmed with examples: **108 competitor numbers
> in the July file appear under two brand spellings**, and the pattern is agent or subsidiary names
> against the manufacturer — `BOSCH` vs `KGK (BOSCH)`, `GMB` vs `GMB OCEANIA`. That is real and it
> would corrupt any join on brand alone.
>
> The match index now carries these corrections in its own build report.
> `04_tools/aftermarket_intelligence/state/MATCH_INDEX_REPORT.md`.


---

## 1. Verdict

**Opus is right that cross-reference coverage decides the plan, and the answer is that we hold far
more than we were using — but still less than a third of Tier A.**

Two things are true at once.

- **We were sitting on a lot.** The matching material on disk covers **149 of the 486 Tier A parts —
  30.7%, worth €7.77M — once we count all four Eucon generations, the UK survey and the peer-number
  map.** The plan was carrying only one of those sources: the 2026-03 cross-reference, at 35 Tier A
  parts and €3.69M. So the audit is not 7.1% of Tier A. It is 30.7%. Break that down honestly,
  though: **only 77 of the 486 have a price we can use today.**

**And the ceiling is lower than the plan assumes.** Even counting every match we hold, **342 of the
486 Tier A parts — 63.5%, worth €13.54M — have no competitor number and no peer number at all.**
Those are not unsearched. They are unsearchable by the method we have chosen, because there is
nothing to search *with*. That is the honest ceiling, and it is the number the plan should be
built around.

**What I would do differently from the Opus answer.** Opus says build identity checks first and
size the cross-reference before scaling. Agreed on the identity checks. But it treats the
cross-reference as a purchase decision. It is not, yet: we hold five generations of it and have
loaded one. The next move is a single readable file that merges those five, plus a seed list that
says which of the 486 we can reach *today* — costs a day, no scrape, no licence.

---

## 2. The direct answer to the open question

Against the billed book, 12 months to the latest billing date, 16,511 lines, €34.61M. Five of those
lines are not parts (two drummed lubricants, one diagnostic tool, two service-fee lines) worth
€587k; the real parts base is **16,447 lines, €33.97M**. Tier A is **486 parts, €20.73M**.

| What we hold | Tier A parts | % of A | Billed € |
|---|---:|---:|---:|
| Eucon cross-reference 2026-03 (the one the plan uses) | 35 | 7.2% | 3,691,390 |
| Eucon Online file, July 2025 **(new today)** | 53 | 10.9% | 4,110,394 |
| Eucon March 2024, online sheet **(new today)** | 29 | 6.0% | 2,491,416 |
| Eucon March 2024, RRP sheet **(new today)** | 47 | 9.7% | 3,315,110 |
| Eucon UK 2023 IAM survey | 24 | 4.9% | 2,622,003 |
| Isuzu genuine → the BVP value line | 60 | 12.3% | 2,191,381 |
| **Any competitor equivalent** | **129** | **26.5%** | **6,490,358** |
| **+ peer-number map (DAF / Toyota / Ford)** | **153** | **31.5%** | **7,901,819** |
| Tier A with nothing at all | 333 | 68.5% | 12,823,788 |

Whole book, same shape: **342 of 16,447 parts (2.1%) carry a competitor number, worth €7.33M,
21.6% of what we bill.** Add the peer-number map and it is 414 parts, €9.09M, 26.7%.

**This corrects the 18 September figure.** `competitor_coverage_truth.csv` states the union with a
usable price was **76 part numbers, 16.5% of the book**. That was right for what had been loaded
then. It is now 342 parts and 21.6% because of three things: the two new Eucon files, the wide file
that carries our own price with no competitor (10.9% of the book), and the UK survey's match
content, which was never read. The old 16.5% should not be quoted again.

**One number Opus should see, because it changes its arithmetic.** We hold **2,812 searchable
competitor brand + number objects** — 2,598 competitor numbers across 629 brands. Those sit under
95 of our part numbers, **13.6% of the book.** That is the seed list that makes "search by the
competitor number instead" a real plan rather than an idea.

---

## 3. What the two new files actually are

Both landed at 15:59 and 16:00 today. They are not one more extract of the same thing. They are
three more generations of a programme that has been running since 2021.

| File | Sheet | Rows | What it is |
|---|---|---:|---|
| `Eucon_Online28072025.xlsx` | `Fresh list_Export_28072025_0932` | 5,081 | 88 Isuzu numbers with their competitor numbers, 561 brands, five countries |
| `Eucon_March.xlsx` | `Online 15032024` | 894 | 42 Isuzu numbers with competitor numbers and four web-shop prices each |
| `Eucon_March.xlsx` | `RRP MODE` | 552 | 97 Isuzu numbers with **our own 2024 price and Eucon's recommended retail**, EUR, five countries |
| `Eucon_March.xlsx` | `RRP comparison`, `Online comparison` | 463 / 174 | Pivots of the above. Reference only |

Earlier generations already on disk: the **2021 UK/Israel OEM and IAM benchmark** (there is a real
report, 1.3 MB, in the mail attachments) and the **2023 UK/ITUK IAM and OEM survey**.

So there are **five Eucon generations** of matching data on disk and the loaded file is the
smallest one.

### Three things the new files give us that we did not have

**One — 46 Isuzu numbers we have never matched, 19 of them in Tier A.** The July file holds 2,593
brand-and-number pairs; **2,429 of them, 94%, are not in the cross-reference we have been using.**
It adds 46 numbers, 45 of them billed, €744k, and 19 Tier A parts.

**Two — the 2024 RRP sheet is the only place we hold our own price against a competitor's
recommended retail, per market, in euro.** 97 numbers. That is a different measurement from a
web-shop price and it does not belong in the same column as one.

**Three — a fourth-generation cross-reference sitting unused inside the 2023 survey.** The ledger
loads that file as *prices* (68 rows). Its match content — 38 Isuzu numbers against 98
brand-and-number pairs, of which **29 are not in any newer file** — has never been read. 24 of
those are on the book, €962k.

### Four defects found in the new files. One is confirmed; three were my own reading errors, corrected above.

**The real one: some of the 2,429 "new" pairs are the same competitor number under two names.**
108 competitor numbers in the July file sit under more than one brand spelling, and the pattern is
agent or subsidiary names against the manufacturer name — `BOSCH` alongside `KGK (BOSCH)`, `GMB`
alongside `GMB OCEANIA`. Merge on brand and number and you get false new matches; merge on number
alone and you split a part across two brands. The match index keeps the raw brand and a normalised
brand side by side and flags every number that collides.

**The one I got wrong, and it matters more than the four put together.** The July file has **two**
price columns and neither is what its name suggests.

`RRP`, with a declared currency, is a **real competitor price**: 904 rows, 18% of the file, covering
59 of the 88 part numbers. Use it.

`OE RRP` is a price for **our part number** — 4,652 rows, 92%. It is **not our IE40 list**: on the
eight numbers where both exist it runs **2.46× to 3.14×** our list (`8983767540` 249.10 against
79.26; `8975056801` 229.90 against 82.25). Nor is it an aftermarket price. And `OE Currency` is
filled on all 4,652 rows while `Currency (RRP)` is filled on 904, so 4,177 rows carry a price with
no usable label on the competitor side and a labelled price on ours — consistent with a vendor's
own quote layer, but that is a guess and I am not putting it in a column. **What `OE RRP` is
remains unestablished, and it should not be loaded anywhere until it is.**

### Two data-quality checks it passes, which is worth knowing

**Our supersession map adds almost nothing here — 2 Tier A parts, €40.5k.** That is the right
answer: the Eucon searches already run on the current number, so a billed old number has normally
been matched under its successor. The path matters for the *fetch* stage, not the matching stage,
because we must search the number a shop actually lists. Worth knowing before anyone spends a day
building it as a matching improvement.

**Our classification and our price list agree on the electronic parts figure.** The AIM master's
figure key equals the price list's figure and key number on **159,233 of 161,471 rows — 98.6%**.
The 1,654 that differ are a real data-quality item on their own.

---

## 4. The structure I would build

Not a new database. One readable file and one seed list, both already half-built.

**One index of matches.** Every row is one match, and it says: our part number, the competitor
brand, the competitor number, which file it came from, the date of that file, what the row can be
used for, and what the competitor price (if any) is **and what kind of price it is**. One row per
match, not one row per observation. Today that is five Eucon generations, the BVP map and the
peer-number map in one place, about **4,600 rows before de-duplication**.

Two rules on it, both from today's defects:
- **A row is only a price row if the file actually holds a competitor price.** The July file's
  4,652 self-price rows are match rows with no price, and the file's own provenance columns are
  empty. Say so per row, not per file.
- **Brand and number together identify a competitor part; neither alone does.** The 108 rows that
  break that rule are flagged, not dropped.

**One seed list.** Five columns: part number, tier, what we can search for it today, the most
recent file it came from, and the euro billed. For the 486 Tier A parts, today, it reads:

| Can we search for it today? | Tier A parts | Billed € |
|---|---:|---:|
| Yes — we hold a competitor brand and number | 129 | 6,490,358 |
| Yes — we hold a peer maker's number (DAF / Toyota / Ford) | 24 | 1,411,461 |
| Only by our own number, on the one UK shop that answers 21% of the time | ~13 | ~1.35M |
| **No — nothing to search with** | **333** | **12,823,788** |

That table is the whole argument of the programme in four lines, and it is the thing to put in
front of anyone who asks why the coverage is what it is.

---

## 5. State of play: step 1 is built

**Built and run 2026-09-24.** `04_tools/aftermarket_intelligence/build_match_index.py`, read-only on
every source. Four outputs, all in `04_tools/aftermarket_intelligence/state/`:

| File | What it is |
|---|---|
| `match_index.csv` | 7,701 rows. One row = our part number × competitor brand + number × source × source date. Eight sources merged, duplicates removed. |
| `seed_reach_tierA.csv` | the 491 Tier A lines with a graded reach column |
| `reachable_pairs.csv` | the competitor brand + number objects we may search with |
| `MATCH_INDEX_REPORT.md` | the build log, including the three corrections |

What it contains: **647 of our part numbers matched, 3,197 competitor numbers, 537 brands.
1,694 rows (22%) carry a usable competitor price.** Two flags ride on every row — a competitor
number that appears under more than one brand, and one that sits under more than one of our part
numbers — so a join can never split either silently.

**The reach table, graded — and the grading is the point.** "We hold a competitor number" and "we
hold a price we can use today" are different claims, and so is a rival's number versus a rival
carrier's own number. Tier A, 486 parts:

| Reach | Parts | Billed € | % of Tier A |
|---|---:|---:|---:|
| A real competitor price exists today | 77 | 5,628,518 | 26.4% |
| A rival's number, no price | 15 | 357,204 | 1.7% |
| Only inside our own brand (BVP line, or our own number) | 57 | 1,783,251 | 8.4% |
| Nothing to search with | 342 | 13,543,552 | 63.5% |

Whole book: **402 of 16,511 parts carry some number, €8.90M, 25.7% of billed. Parts carrying an
actual rival's number: 181.**

**One exclusion I would ask Jerome to confirm, because it changes the top of the table.** The
Isuzu genuine → BVP map is **our own cheaper line**, not a competitor. I have kept it in the index
with its source named, and counted it as "inside our own brand" rather than as a competitor match.
If it belongs in the competitor view, the market-intelligence reading changes materially.

---

## 6. How to proceed — the merge

Yesterday and today we were building the same thing on three floors and calling it three projects.
They are one:

| Was treated as | Actually is |
|---|---|
| "The scraper programme" | The *fetcher* for one table |
| "The AIM classification write-back" | The *filing system* for the same parts |
| "The dealer demand model" | The *customer* of the same euro |

The AIM work has classified 165,257 part numbers and given 161,471 of them an electronic parts
figure. The scraper work has a 16,511-line list ranked by billed euro and 2,812 competitor numbers.
Neither can finish alone: the scraper cannot say what a part *is*, and the classification cannot say
what it *costs* against a competitor. The join between them already exists in the data — the figure
key on the classification master matches the price list on 98.6% of rows.

**Proceed in this order. Nothing here needs a scrape go, a licence or a rebuild of anything Jerome
opens.**

**Step 1 — merge the five generations into one match index with the price-provenance rule.**
Roughly a day. Output: two CSV files and a *build log that names every excluded row and why*. This
is the step that turns 7.1% into 26.5% and makes the 92 `Unknown` part numbers from the AIM
write-back decidable at the same time, because both jobs need the same list.

**Step 2 — build the seed list and the reach table above.** Half a day. It becomes the input to
every later step and the honest answer to "why is coverage not 100%".

**Step 3 — check the licence status of the new files before anything goes to DeepSeek.** There are
calendar entries titled **"Eucon annuleren"** in January, February and March 2026, a budget approval
for a Eucon invoice in August 2025, and the 2021 report itself in the mail. Two files arriving on a
Thursday afternoon a week before a quarter end is consistent with a final extract, and it is
consistent with a renewal. **We do not know which, and the difference decides whether those 4,600
rows may leave the EU.** This is a question for Jerome, not a check I can run.

**Step 4 — settle what `OE RRP` in the July file actually is, then decide whether to load it.**
4,652 rows carry a price for our part number that is not our list and not an aftermarket price. Two
candidates, both checkable: it is the vendor's own recommended retail for the part, or it is a
converted price in a currency the file does not declare. Ask Eucon. Small question, and it decides
whether that column is an asset or a liability.

**Step 5 — then, and only then, decide how to price the gap.** Three routes, in order of cost:
- the **2024 RRP sheet** (97 numbers, our price against a recommended retail, in euro) — already
  on disk, no licence, no scrape;
- **searching by the competitor number** on the shops that already answer, using the competitor
  objects we hold — a fetch question, not a licence question;
- a **paid cross-reference** (TecAlliance) — the only route that reaches the 342 Tier A parts with
  nothing, and the only one that needs money.

---

## 7. Five things only Jerome can decide

1. **Is Eucon still under contract?** If yes, the new files are billable data and the licence terms
   decide whether they can be used for price monitoring and whether they may go to DeepSeek. If no,
   treat them as a final extract. *Blocks step 3 and every use of the new files.*
2. **The Eucon password.** A plain-text login is still sitting in `NOTE_Eucon.txt` (54 bytes,
   untracked, not on GitHub). Any agent that reads that folder can read it. I did not open it.
3. **Which of the three candidate purposes is the real one** for this work — defending the UK truck
   book, the next price revision, or a maintenance-parts campaign. It changes what the seed list
   sorts by. This has been open since 2026-08-18.
4. **The 92 parts blocked by an `Unknown` marker** in the classification. That decision is still
   waiting, and step 1 makes it cheaper to take because the same list serves both jobs.
5. **Do we drop the non-part lines out of the ranked list?** Five Tier A lines worth €587k are
   lubricants, a tool and two service fees. They cannot have a competitor price and they push real
   parts down the ranking. Two minutes to fix; needs a yes.

---

## 8. Probes and files, for anyone re-running this

Read-only, all under `01_data/91_build/`, nothing written outside them:

| Probe | Answers |
|---|---|
| `_tmp_eucon_coverage_20260924.py` | coverage per source, per tier |
| `_tmp_eucon_prices_20260924.py` | what prices each file holds, and the price-provenance trap |
| `_tmp_eucon_newmat_20260924.py` | how much new match material the new files carry |
| `_tmp_eucon_survey_crossref_20260924.py` | the 2023 survey read as a match source, not a price source |
| `_tmp_supersession_lift_20260924.py` | what the supersession map adds (almost nothing) |
| `_tmp_asset_inventory_20260924.py` | every match asset on disk and its value as a seed list |
| `_tmp_crossref_quality_20260924.py` | collisions and duplicate brand spellings |
| `_tmp_union_definitive_20260924.py` | the union against parts only, which is the number to quote |
| `_tmp_project_overlap_20260924.py` | where the three projects overlap |
| `_tmp_ks_objects_20260924.py` | the 2,812 searchable competitor objects and what they reach |

**A caution on one thing I did not verify.** The July 2025 file's brand list includes the UK
specialist shop we already scrape and the German and Portuguese web shops. So a share of the "new"
2,429 pairs are matches we could also have got ourselves. I extracted the pairs mechanically and did
not quality-check them by hand, because there are 2,429 of them. Treat the 46 extra part numbers and
€744k as sound, and the 94%-is-new figure as an upper bound.

# Opus 5.5 — prompt 2, aftermarket intelligence (2026-09-24)

Paste into a **new** chat. This one starts from the answer Opus gave to prompt 1, adds the two new
Eucon files and the measured cross-reference coverage, and asks for the design rather than a review.

No price-list values, no distributor-level numbers, no part-level billed values. Aggregates only.

---

```
You are a senior aftersales pricing analyst and data architect. You previously reviewed a
competitor-price plan for a European Isuzu parts operation and asked one question you could not
answer: what is the cross-reference coverage of the 491 Tier A parts? That question has now been
measured. Challenge what follows; do not agree by default. Verdict first. Plain business English.

WHAT IS ON DISK
Billed book, trailing 12 months: 16,447 part numbers, 33.97M EUR. Ranked into tiers by billed value:
A = 486 parts / 20.73M, B = 1,809 / 9.80M, C = 14,152 / 3.50M.

Matching material, five generations of it, never merged:
1. Eucon cross-reference 2026-03: 45 Isuzu numbers, 432 competitor numbers, 155 brands, DE and NO.
2. Eucon Online extract 2025-07: 88 Isuzu numbers, 2,593 brand+number pairs, 561 brands, five
   countries (DE, PT, NO, SE, DK).
3. Eucon March 2024, online sheet: 42 Isuzu numbers, 295 brand+number pairs, four web shops.
4. Eucon March 2024, RRP sheet: 97 Isuzu numbers with our own 2024 price and a recommended retail,
   EUR, five countries.
5. Eucon UK 2023 IAM survey: 38 Isuzu numbers, 98 brand+number pairs, UK workshop prices.
Plus two non-Eucon maps: Isuzu genuine to our own cheaper value line (431 numbers) and a peer-maker
number map to DAF/Toyota/Ford (120 numbers).

FOUR DEFECTS FOUND IN THE NEW FILES
- The July 2025 file mislabels our own list price as a competitor price on 4,652 of 5,081 rows
  (92%), worth 3.70M EUR. The value equals our list to the cent on every one. Only 904 rows (18%)
  carry a real competitor price. The columns that label legal provenance are empty on the rest.
- 108 competitor numbers in that file sit under more than one brand spelling, including reseller
  names that duplicate the manufacturer name.
- We hold one price per part number, not one per country: our own price is identical across all five
  countries on all 88 numbers.
- Two duplicate part numbers in the ranked list: one physical part billed under two numbers.

MEASURED COVERAGE
Against the 486 Tier A parts:
- 129 parts (26.5%) carry a competitor number, worth 6.49M EUR.
- 153 parts (31.5%) carry a competitor number or a peer-maker number, worth 7.90M EUR.
- 333 parts (68.5%) have nothing to search with at all, worth 12.82M EUR.
Whole book: 342 of 16,447 parts (2.1%) carry a competitor number, 21.6% of billed value.
We also hold 2,812 searchable competitor brand+number objects (2,598 numbers, 629 brands), sitting
under 95 of our part numbers.
Two checks that passed: our price-list supersession map adds only 2 Tier A parts, because the
Eucon searches already run on current numbers. And our classification master's figure key equals the
price list's figure+key on 159,233 of 161,471 rows (98.6%).

WHAT I INTEND TO BUILD
One match index: one row per our-part-number x competitor-brand x competitor-number x source, with
the source date, what the row can be used for, the competitor price if any, and the kind of price it
is. About 4,600 rows before de-duplication. Two rules: a row is a price row only if the file
actually holds a competitor price, and brand plus number together identify a competitor part, so
neither alone can join. Then one seed list of the 486 Tier A parts with a column saying what we can
search for each of them today.

THE OTHER TWO WORKSTREAMS, WHICH I THINK ARE THE SAME PROJECT
A part classification master, 165,257 part numbers with a three-level family path, 161,471 of them
carrying an electronic parts figure. And a dealer-level demand model that would consume the same
euro figures. My claim: the scraper cannot say what a part is, the classification cannot say what it
costs against a competitor, and the join between them already exists in the data. So they are one
system with three jobs, not three projects.

QUESTIONS
1. Is the one-match-index design right, or is there a better shape? Say what you would change and
   what you would keep.
2. The 333 Tier A parts with nothing to search with are 61.9% of Tier A value. What is the right
   response: buy a licensed cross-reference, change which parts we consider contestable, or
   something else? Give one recommendation, not a menu.
3. What is the smallest set of script-checkable rules for the match index that would have caught
   all four defects above? Give them as rules, not prose.
4. Where does the classification master and the match index actually join, and what breaks when they
   disagree?
5. What is the single metric you would put on one page to tell management whether this programme is
   working, and what number would make you stop?

CONSTRAINTS
- Do not invent figures. Write "not given" where the brief is silent.
- No prices from our own price list, no distributor names, no part-level billed values.
- I did not hand-check the 2,429 pairs that the July file adds, so treat its "94% is new" claim as
  an upper bound and say where that matters.
- One recommendation per question. If you disagree with the direction, say which step and why, not
  that everything needs rethinking.
```

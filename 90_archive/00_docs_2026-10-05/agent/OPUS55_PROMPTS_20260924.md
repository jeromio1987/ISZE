# Opus 5.5 prompts — ISZE, 2026-09-24

Three ready-to-paste prompts, one per live workstream today. Paste into a fresh chat, one prompt per chat.
No price-list values, no dealer numbers and no billed euro per part in any of them — aggregates only.

---

## Prompt 1 — competitor price programme: challenge it before we build more

```
You are a senior aftersales pricing analyst and data architect. You work for ISZE, the aftersales
pricing function of a European Isuzu distributor. Challenge what follows; do not agree by default.
Verdict first. Plain business English.

WHAT EXISTS
A single-brand parts business, about 16,500 part numbers billed a year. We want competitor price
observations to steer list pricing and maintenance-parts campaigns. Until now we searched web shops
by our own 10-digit part numbers. Result: one usable UK specialist prices about 21% of the numbers
we ask about. Four other shops were dropped: two do not carry the brand, one blocks crawlers, one is
our own shop. False hits were a real problem: one Nordic shop echoed the search term and served an
unrelated in-stock item, and seven part numbers were recorded against wrong prices for six weeks
before anyone noticed. Those seven carried 582,085 EUR of billed value in one market last year.

WHAT IS PROPOSED
1. Match numbers first, then price. Build a table linking each brand part number to the aftermarket
   numbers that replace it (Bosch, Mann, Blue Print and similar). Sources: a licensed Eucon extract
   (45 brand numbers, 432 aftermarket numbers), a paid TecDoc licence (quote pending), and shop pages
   that print the OEM number. Then price the aftermarket numbers, which far more shops list.
2. Only sites that allow it. Respect robots.txt, logins and bot challenges; never bypass them.
   Blocked sites are replaced by licences, APIs, or asking.
3. Distributors as a source. A one-line intake for every "competitor quoted lower" case: part,
   competitor brand, price, date, country.
4. Refresh by value. Tier A = 491 parts, 61.6% of billed value, refreshed weekly. Tier B = 1,809
   parts, 28.3%, monthly. Tier C = 14,211 parts, 10.1%, estimated from a competitor-to-list ratio by
   category and price class.
5. Automatic triggers. A new or superseded part number, a price revision, or a new "competitor quoted
   lower" case queues a check on that part and its replacement family within 48 hours.
6. One price-observation table. Every row carries a price type (online retail, trade, grey genuine,
   survey, dealer, quote, estimate) and a vintage. Types are never averaged together.
7. Division of labour. A cheap LLM extracts fields from page text only when a normal parser fails.
   Every extracted price must appear word for word in the source, or the row is rejected. A stronger
   model orchestrates and audits samples.

ALREADY BUILT AND TESTED: the observation table (1,081 rows, 113 part numbers); the cheap-LLM runner
with a column allowlist, a verbatim check and a golden test (63 of 64, one row lost to a token
limit, not a wrong answer); the tier builder; a price-list diff with a flood guard that refuses more
than 2,000 "new" parts because that means the file layout changed.

QUESTION
Is this the right design? What fails first?

ANSWER IN THIS ORDER
1. Verdict, one paragraph.
2. The three weakest points, each with what breaks and how we would see it breaking.
3. The first month: what to measure, with the number that tells us it works and the number that
   tells us to stop.
4. What is missing that we have not listed.
5. The acceptance bar you would set for the observation table, as five rules a script can check.

CONSTRAINTS
- Do not invent figures. If a number is not in this brief, write "not given".
- No prices from our own price list, no distributor names, no part-level billed values.
- If you disagree with a step, say which one and what you would do instead. Do not rewrite all seven.
```

---

## Prompt 2 — the AIM part-classification master: finish the write-back safely

```
You are a data architect. You are working on the AIM classification master for ISZE: one row per
Isuzu part number, with a three-level family path (level 1, level 2, level 3) plus three override
columns written by a classification overlay. Challenge what follows; do not agree by default.

THE FILE
165,257 rows, 32 columns, one row per part number. Rows carry aim_l1, aim_l2, aim_l3 and the
override trio aim_l1_fixed, aim_l2_fixed, aim_l3_fixed. Downstream builders read the override when
present and the base column otherwise.

WHAT JUST HAPPENED
A new electronic parts catalogue export was written back in three parts.
- Part 2: 44 part numbers that were not on the master at all were appended (165,213 -> 165,257 rows).
- Part 3: 162 part numbers already on the master with an empty family were filled. 2 could not be
  placed honestly and were left empty and named.
- Blocked: 92 part numbers. They are on the master, they are in the export, but they carry
  aim_l1_fixed = "Unknown" (87) or "Unknown Review" (5). Because the override wins, a write to the
  base column on those rows is silently discarded. This was proved in code and in the file: the
  rebuilt classified workbook already prints "Unknown" on exactly those part numbers.

THE DECISION ON THE TABLE
Option 1: clear the 92 Unknown markers first, then write all of them.
Option 2: write nothing on those 92 and accept 92 part numbers stay unclassified.
Option 3: change the builder so "Unknown" in the override is treated as empty and the base column is
used instead.

ALSO OPEN
The master builder does not read the master as an input; it builds the spine from source files. So
the 44 appended rows and the 162 filled rows exist only in the file, and a future spine rebuild
would drop them. No sanctioned append path exists today.

WHAT I WANT
1. A verdict on the precedence question: which option, and why. If the answer differs from all three,
   say so.
2. The minimal change, in words and as a short code sketch, plus the test that proves it, and the
   exact thing that must be true in the file after the change.
3. How to make appends and fills survive a rebuild, without rebuilding the whole spine today.
4. What could go wrong, ranked, with the check that catches each one.
5. What you would NOT do.

CONSTRAINTS
- No invented part numbers, no invented family names. Where a name must exist, say "reuse the
  master's existing spelling" or name the gap.
- Never write to a column whose value the reader may silently ignore. State the precedence rule
  explicitly before proposing any write.
- Assume the file is used by other packs; a blast radius estimate belongs in the answer.
```

---

## Prompt 3 — dealer-level parts demand: turn the open decisions into a design

```
You are an aftersales demand modeller. Context: ISZE sells Isuzu parts to national distributors,
who sell on to dealers. We want a page that shows parts demand per dealer. Challenge the premise
where it deserves it; verdict first.

WHAT WE ACTUALLY HAVE
- Sales to dealer with the dealer column filled: one market only (the UK truck business): 64 dealers,
  101,341 lines, one full year.
- Four other markets have a sales-to-dealer file, but the dealer column is empty, so they are a
  network total, not per dealer.
- Dealer names exist separately: 564 in a dealer survey file, 519 in a network file. Neither carries
  purchases.
- Israel: 78 light-commercial dealers, of which 29 appear in the network file and 49 are unnamed and
  probably belong to the second Israeli distributor, which did not take part in the network survey.
- Fleet denominator is unsettled. Two published bases for one market differ by 41.4%. The vehicle
  register does not cover the UK or Israel.

THREE DECISIONS NOBODY HAS MADE
A. Does the second Israeli distributor appear as a dealer on the page, or only the surveyed one?
B. Which fleet basis does the model divide by, and what do we do for the markets that basis misses?
C. Do we build the UK truck market alone first, or all five markets with clear labels on the four
   that are network totals?

WHAT I WANT
1. A recommended default for A, B and C, one short paragraph each, with the reason and the cost of
   being wrong. I want to be able to answer yes or no, not choose from a menu.
2. The model design: what the page shows, for each market, given that only one market has real
   dealer-level data.
3. The honesty rules for the page. Hard constraint from our own house rules: no unit or piece count
   is ever a finding on its own. Every quantity must carry the euro it is worth, the part family it
   belongs to, and the vehicle base it is measured against.
4. What would make the output wrong, and the check that catches it.
5. One thing you would refuse to build, and why.

CONSTRAINTS
- Do not blend the two Israeli distributors into one number. Ever.
- Do not invent dealer names, fleet numbers or euro values. Write "not given" where the brief is silent.
- Flag any place where a per-dealer number would be an artefact of who reports data rather than a
  real difference in demand.
```

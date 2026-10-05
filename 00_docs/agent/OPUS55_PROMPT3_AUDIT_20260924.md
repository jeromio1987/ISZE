# Opus 5.5 — prompt 3, audit of what was built today (2026-09-24)

Paste into a **new** chat. This is not a design question. Everything here already exists on disk and
has never been checked by anyone except the script that made it. The job is to find what is wrong
with it.

No price-list values, no distributor names, no part-level billed values. Aggregates only.

---

```
You are auditing work that another agent produced today. Assume nothing is correct. You previously
reviewed a competitor-price plan for this business and found the flaw the author had missed - that a
word-for-word check would not have caught a wrong-part match. Do that again, on the code that has now
been written. Verdict first. Plain business English.

WHAT WAS BUILT TODAY, AND WHY IT MATTERS
A European Isuzu parts operation wants competitor price observations. The approach: match part
numbers first, then price them. Three things were built.

1. A MATCH INDEX. One row per our-part-number x competitor-brand x competitor-number x source file x
   source date. Eight sources merged (four generations of a licensed Eucon extract, a 2023 UK
   survey, our own cheaper value line, a peer-carrier number map, and shop listings).
   Result: 7,701 rows, 647 of our part numbers, 3,197 competitor numbers, 537 brands.
   1,694 rows (22%) carry a usable competitor price; the rest are matches with no price.
   Two rules are enforced on every row:
     - a row carries a price only if the source file genuinely holds a competitor price;
     - a competitor part is identified by brand AND number together, never by either alone.

2. A CROSS-REFERENCE GRAPH. Same data, one edge per our-part-number x competitor-number x source x
   country, with provenance. 7,443 edges, 0 refused for a missing source or date (that was the
   acceptance rule). 2,446 competitor numbers rest on one source, 463 on two or more, 168 on three
   or more. Plus a fetch seed ranked by how many sources agree rather than by what we bill.

3. A RATIO MODEL, for the 14,152 low-value parts that will never be scraped. Competitor price
   divided by our list price, by category and price band. Back-tested leave-one-part-number-out:
   for each held-out part, the model is refitted on all other parts in the same cell; if the cell is
   too thin it falls back to the category, then to the whole price type.

THE RATIO MODEL'S OWN BACK-TEST, which is the main thing I want you to attack:
  price type "competitor recommended retail", 94 held-out parts:
      typical error 11.1% (median absolute), 9 in 10 within 31.0%, actual inside the 10-90 band 66%
  price type "online median", 44 parts:
      typical error 36.3%, 9 in 10 within 93.5%, in band 61%
  price type "online retail", 42 parts:
      typical error 28.8%, 9 in 10 within 164.1%, in band 60%
  price type "survey workshop", 37 parts:
      typical error 35.3%, 9 in 10 within 79.3%, in band 68%
  Where the prediction actually came from: whole price type 49%, category 32%, category x price band
  only 19%.

WHAT I ALREADY KNOW IS WRONG, so you do not spend your answer on it:
  - Three claims in my own written note did not survive checking and are corrected: a price column I
    described as our own list is not our list; a duplicate-part-number claim was false; a
    one-price-per-part claim was the opposite of the file.
  - A silent bug: the part-number normaliser stripped non-digits, so seven non-part lines (rebate,
    freight, service fees) collapsed into one key and were counted as a single row. The run exited 0.
  - 166 competitor numbers exist in more than one written form ('F 026 402 115' and 'F026402115' are
    the same Bosch number). Counting confirmation on the written form understates agreement;
    counting it on the loose form inflates it. Both keys are now kept.
  - "Number of sources" counts distinct FILES, not independent witnesses. The four Eucon
    generations partly repeat each other.

WHERE THE PARTS STAND, for context
Of the 486 highest-value parts: 77 (EUR 5.63M) have a real competitor price today; 15 (EUR 357k)
have a rival's number but no price; 57 (EUR 1.78M) are matched only inside our own brand, mostly our
own cheaper value line; 342 (EUR 13.54M) have nothing at all to search with. A 20-number manual spot
check by a person with a browser is running now, because nobody has ever looked at a single edge.

QUESTIONS
1. Is leave-one-part-number-out the right test for this model? If not, what is, and what would it
   change about the error figures above?
2. Given that only 19% of predictions come from a category x price-band cell and 49% from the
   whole-book average: is this model salvageable, or is the honest answer to publish nothing for the
   14,152 long-tail parts? If you would publish something, say exactly what, with what label.
3. The 11% error on competitor recommended retail is the only good result. Is that result real, or
   is it an artefact of the one price type where the two sides of the ratio come from the same
   vendor? What would falsify it?
4. The four Eucon generations overlap. Give me one rule a script can run that counts independent
   confirmation honestly rather than counting files. It has to be checkable mechanically.
5. Name the three highest-risk assumptions underlying the match index and the graph that I have not
   checked, and for each, one specific check that would falsify it.
6. The 20-number spot check returns next. What result would make you abandon the whole
   cross-reference approach and put the money into a paid licence instead? Give the number before
   the result is known, not after.

CONSTRAINTS
- Do not invent figures. Write "not given" where the brief is silent.
- Do not redesign the programme. Answers 5 and 6 are the only places I want new proposals.
- One recommendation per question. If you disagree with something, say which step and why.
- Where you are guessing rather than reasoning from the numbers above, say so.
```

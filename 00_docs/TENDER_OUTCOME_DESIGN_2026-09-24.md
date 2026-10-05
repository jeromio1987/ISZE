# Tender outcomes: the smallest record that gets filled in

24 September 2026 · design only · internal

**Recommendation.** Do not ask a distributor to fill in anything. Ask one question per
week, in the reply to the list they already receive: "which of these numbers will you
pursue, and which will you pass?". The ISZE market owner for that country types the
answer into the outcome column the same day. Ask "won or lost?" only about tenders the
distributor said it would pursue, and ask it again each week until the award is known.
Start with the notices that have a published deadline, which is 23 notices across six
distributors in today's list, not all 113.

Terms used below: **R&M** is repair and maintenance. A **notice** is one published tender
announcement. **TED** (Tenders Electronic Daily) is the European Union's official tender
journal; a **national portal** is a country's own tender site. A **CSV** is a plain
spreadsheet file. The **outcome store** is the file `tender_outcomes.json` that holds
recorded outcomes between weekly rebuilds.

---

## What is true today (checked against the files)

The brief's counts are correct.

| Count | Value | Where it comes from |
|---|---|---|
| Opportunities in the live feed | 619 | `01_data\14_dashboards\tender_data.json`, built 22 Sep 2026 |
| R&M contracts | 279 | `rm_contract` is true |
| R&M with no vehicle purchase | 236 | `product_segment` = "R&M only, no vehicle buy" |
| Open R&M, deadline on or after 24 Sep | 29 | 18 Selective, 7 Watch, 3 Ignore, 1 Attack |
| Outcomes recorded | 0 | the outcome store holds an empty list; every opportunity's `outcome` is empty |
| Minimum sample before a win rate shows | 20 | `MIN_WIN_RATE_SAMPLE = 20` in `tender_outcomes.py`; counts won plus lost only |

The weekly digest built today selected 222 of the 279 (the 3 Ignore rows among the 29 are
left out, so 26 of the 222 carry a deadline). 113 are on ten distributor pages, 109 on an
internal page with no distributor. Every one of the 113 codes in the CSVs exists in the
live feed.

Five further facts decide the design, and none of them is in the brief:

1. **Most of the list has no deadline, because most of it comes from TED.** 211 of the 279
   R&M opportunities come from TED; 196 of those carry no deadline. Of the 222 notices in
   the digest, 196 have no deadline. A notice with no deadline gives nobody a moment at
   which to decide.
2. **The same tender often appears twice.** A TED copy with no deadline sits beside the
   national-portal copy with a deadline, under two different codes, because the code is
   built from title, buyer and country and TED spells both differently. On the Belgian
   page, 13 lines are at most 8 distinct tenders, probably 7 (lines 1 and 11, 2 and 10,
   3 and 12, 4 and 8, 5 and 13 are the same tender, and 6 and 7 carry the same title).
   Across all R&M, a strict title match finds at least 26 TED copies of a national
   notice. An outcome typed on one copy leaves the twin blank or, typed on both, counts
   twice toward the 20.
3. **The page and the record use different words.** The distributor page asks for
   "pursue / pass / already known". The CSV asks for "pursue / pass / won / lost /
   no decision". The store's summary counts a row as decided only if it reads "won",
   "lost", "no-bid", "bid" or "not pursued", so a "pursue" or "pass" would be stored but
   not counted as a decision. The older tender dashboard adds a fourth list (Submitted,
   Won, Lost, Contract live, and others) that saves only in the viewer's own browser and
   never reaches the store. The CSV also has both an `outcome` and a `status` column for
   the same word.
4. **The CSV cannot be filled by a distributor.** It holds a 12-character code per row and
   nothing else: no title, buyer or deadline. The page numbers its notices 1, 2, 3. The
   CSV rows are in the same order as the page (checked on the Belgian list), so someone at
   ISZE can map "3 pursue" to row 3. A distributor could not.
5. **None of the R&M notices names Isuzu.** The brand check is empty for all 279. These
   are general fleet repair contracts, or vehicle purchases with maintenance bundled in.
   Winning one means a dealer's workshop, or the distributor, wins a multi-brand contract.
   What ISZE gains is parts billed through that workshop, and nothing in the files links a
   contract to parts billed.

Codes are stable from week to week as long as the source text does not change: all 113
codes in today's CSVs were already in the 21 September build, and 34 of the 41 R&M codes
from the 15 September build are still present. Outcomes keyed on the code will survive the
weekly rebuild. The seven that dropped out may have expired rather than changed code; I
could not tell which.

---

## 1. Who fills it in, when, and from where

Two people, two moments.

**The distributor's tender contact** (whoever receives the weekly list) decides pursue or
pass. The moment is the week the notice first appears, and in any case before its
deadline. They do it from the list itself, by replying with the notice numbers and one word
each, which is exactly what the page already asks for. They never open the CSV.

**The ISZE market owner for that country** (the owner role the feed already suggests for
every R&M opportunity, for example the Central and Eastern Europe lead or the Benelux lead)
types the reply into the CSV the same day, by row number. The same person asks about the
result later (see below) and records "won" or "lost" when the distributor answers.

The result moment is different. An R&M contract is awarded weeks or months after the
deadline, and there is no award date in the feed. So the question "did you win?" goes back
only for notices marked "pursue", on each weekly list, in a short section at the top:
"Earlier you told us you would pursue these. Is the result known?" Once answered, the
notice drops off that section.

The 109 notices with no distributor (Poland 29, France 17, Spain 15, Italy 12, Bulgaria
11, Czechia 7, Slovakia 6, Netherlands 4, Lithuania 4, Latvia 3, Croatia 1) have no one
to ask. Leave them out of the outcome record. They should not count toward the 20 and
should not be marked "pass" by ISZE, because a pass that nobody chose would make the
distributors look less engaged than they are.

## 2. What the five options mean

One vocabulary, used on the page, in the CSV and in the store. One column (`outcome`); the
`status` column is ignored.

| Word | Means | Set by | When |
|---|---|---|---|
| **pursue** | The distributor, or a named dealer of theirs, will submit a bid for this contract or for at least one of its lots. | distributor, typed by ISZE | before the deadline |
| **pass** | Looked at, and no bid will be made. | distributor, typed by ISZE | before the deadline |
| **no decision** | Looked at, not decided yet. It is a holding word and is asked again the next week. If the deadline passes while it still reads "no decision", it stays that way; it is never turned into "pass" by default. | distributor, typed by ISZE | any time |
| **won** | A bid was made and the buyer awarded the contract, or at least one lot, to the distributor or its dealer. For a vehicle purchase with maintenance bundled in, won means the whole award, vehicles included, as the buyer made it. Name the lot in the notes if only part was won. | ISZE, on the distributor's word or the published award | after the award |
| **lost** | A bid was made and the buyer awarded the contract to someone else. | ISZE, on the distributor's word or the published award | after the award |

What does **not** count:

- No bid made means **pass**, never "lost". Lost always needs a bid.
- A tender the buyer cancelled, withdrew or never awarded is neither won nor lost. It stays
  "pursue" with the note "cancelled" and never enters the win rate.
- A tender where our dealer is only a parts supplier to the winning bidder is not "won".
  That is worth knowing, but it belongs in the notes.
- "Already known", the third word on today's page, is not a decision. Drop it from the
  page's answer words. If a distributor says they knew about a notice already, put that
  in the notes; it tells us whether the list adds anything, which is a separate question.

The win rate is won divided by won plus lost, as the store already calculates. A second
figure, pursued divided by pursued plus passed, is the answer to "does anyone act on this
list?". It can be read long before 20 results exist.

## 3. How the entry gets back into the feed, and what stops it

**The route, as it exists today.** The market owner fills the `outcome` column in the
distributor's CSV. Someone at ISZE runs the short import in the digest's
`README_IMPORT.md`, which writes each filled row into `tender_outcomes.json` beside
`tender_outcomes.py`. At the next weekly feed build, the builder attaches each stored
outcome to its opportunity and refreshes the summary in the feed (`meta.outcomes_summary`),
which the Action Centre and the pillar board read. Nothing in that chain is automatic: the
import is a snippet in a readme, not a step in the weekly run.

**What stops it being filled in**, most serious first:

1. **Nobody is asked.** As far as the files show, no list has gone to any distributor yet.
2. **The distributor is handed work instead of a question.** A CSV of codes cannot be
   filled from outside ISZE. The reply-by-number route removes this.
3. **Four vocabularies.** Until the page, the CSV and the store use the same five words,
   entries will be stored but not counted, or will be written in words the store does not
   recognise.
4. **Duplicate lines.** A distributor who sees the same tender twice will answer once, or
   answer twice and be counted twice. Until the duplicates are merged, the market owner
   copies an answer to both twins and counts the pair as one tender.
5. **No moment to decide.** 196 of the 222 notices say "deadline not published". A list
   of undated notices invites no reply.
6. **The result question is never asked.** Without a standing "is the result known?"
   section, won and lost will never be recorded, because nobody remembers to ask months
   later.
7. **The import is a manual step with no owner.** If it is not tied to the weekly build,
   filled CSVs will sit in a folder.
8. **Nothing comes back to the distributor.** If the answers vanish into ISZE, the reply
   stops by the third week. The small return is the "you said pursue" section itself: it
   shows the distributor that their answer was read.

## 4. What the list looks like at 20 results, and what it can then say

A single internal list, one line per distinct tender (twins merged):

| Distributor | Buyer | Tender | Deadline | Answer | Answered on | Result | Awarded to (if lost) | Notes |
|---|---|---|---|---|---|---|---|---|

with three lines above it:

- Answered: *x* of *y* tenders sent, by distributor.
- Pursued *a*, passed *b*, still undecided *c*.
- Of the pursued: won *w*, lost *l*, result not yet known *p*, cancelled *k*. Win rate shown
  only once *w* + *l* reaches 20.

The cells are empty today because no answer exists; the figures come only from what is
entered.

What it can say then that it cannot say now:

- **Whether the list is used at all**, by distributor. This is readable after the first
  few weeks of replies, well before 20 results.
- **Why distributors pass**, if a one-word reason is added to "pass". A run of passes on
  vehicle purchases with maintenance bundled in, for example, would show that the R&M
  filter lets through tenders a distributor does not regard as repair work.
- **Which distributors bid**, and which never do.
- **A first win rate**, once 20 bids are decided. With 20, it is rough: the margin of error
  is up to about 20 percentage points either way. It separates "we win most of these" from
  "we almost never win", and not much finer than that.
- **Who beats us**, where the distributor or the award names the winner.

What it still cannot say: how much parts business a won contract brings. The
`actual_parts_revenue_12m` field exists in the store, but nothing links a repair contract
to parts billed through the winning workshop. Leave that field empty rather than guess.

When 20 results arrive depends on how many tenders are pursued, and no pursue rate exists
yet. Only tenders pursued and then awarded can count, and today's list holds 26 dated
notices, fewer distinct tenders than that. It will be months, not weeks. I cannot give a
date.

## 5. The smallest version that survives contact with a distributor

1. **Send only dated notices.** 23 today across six distributors (Romania 8, Belgium 6,
   Norway 4, Portugal 3, Germany 1, Ireland 1). Twins merged, so each tender appears once.
   Undated notices stay on an internal page until a deadline is found.
2. **One question, by number:** "Reply with the number and one word: pursue, pass or not
   decided yet." Nothing else is asked, and there is no file to fill in.
3. **The market owner types the answer** into the `outcome` column the same day. Only that
   column. Decision date, loss reason, competitor and parts revenue are left empty in the
   first version, apart from a one-word reason on a pass if the distributor gives one.
4. **One standing section at the top of each week's list:** "You said pursue on these. Is
   the result known: won, lost, or not yet?" Pursued notices only.
5. **The import runs just before the weekly feed build**, by the same person, every week.
   If it cannot be relied on to happen, the loop fails there first.
6. **Before the first list goes out, make three wording changes on paper:** the page's
   answer words match the record; "already known" becomes a note; the `status` column is
   declared unused.

This asks a distributor for one line a week. Anything that asks for more, such as a
spreadsheet, a portal login, reasons for every line or a revenue estimate, will get no
answers by the third week, and an empty outcome store will look exactly as it does today.

---

## What I read

- `04_tools\ISZE_Tender_Monitor_Install\tender_outcomes.py` and `tender_outcomes.json`
  (empty store, version 1)
- `01_data\14_dashboards\tender_data.json`: meta and opportunity fields (parsed by script;
  the counts above come from it)
- `04_tools\ISZE_Tender_Monitor_Install\rm_digest\2026-09-24\`: `README_IMPORT.md`,
  `_run_report.json`, all ten distributor CSVs, the Belgian page's visible text
- `build_rm_digest.py`, `build_dashboard_v2.py`, `build_dashboard_v4.py`,
  `publish_live_tender_json.ps1` (how outcomes are merged at build time)
- The 21 and 15 September feed backups, used only to check whether codes stay the same
  from week to week

Nothing was written into the outcome store, and no code or schema was changed.

## What I could not establish

- Whether the seven R&M codes that disappeared between 15 and 24 September expired or
  changed code.
- Whether lines 6 and 7 on the Belgian page (same title, buyers "Facilitair Beheer" and
  "stad Brugge") are one tender.
- The winner of any awarded tender: the feed holds 60 notices marked as results, 5 of them
  inside today's digest, but no field naming who won.
- Whether any distributor has agreed to receive the list.

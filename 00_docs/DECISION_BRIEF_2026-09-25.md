# Decision brief — four opens from the 24 September work order

25 September 2026 · internal · bundles four of the eleven memo outputs (24 Sep work
order + Opus tasks) into one page, each with the specific question that needs your
sign-off. Nothing built, no dashboard touched, no decision taken on your behalf.

The other seven outputs (pillar board attack, the two weak-tool designs, the tender
outcome design, the Eucon data inventory, the distributor-page term scan, the UK truck
pilot baseline) are status or design memos, not yes/no decisions — nothing in them is
waiting on you the way these four are.

---

## 1 · Purpose — what should the competitor/aftermarket work sort by?

**Status quo.** No purpose has been chosen since this was first raised on 18 August.
Today's ranked list sorts every part by raw euro billed, across every family.

**Recommendation (memo).** Option (c) — the maintenance-parts campaign (oil filter, fuel
filter, air filter, brakes, clutch). 57.5% of all Tier A euro that has a usable
competitor price today sits in these five families; the other two options are held back
by evidence we don't have, not by ranking.

**Your call:** approve (c), or pick (a) defend the UK truck book, or (b) feed the next
price revision?

**If you approve (c):** the ranked list narrows to the five maintenance families; PRISM's
maintenance capture page (port 8503, `3_PMS.py`) becomes the working view; the UK-defence
and price-revision tracks drop out of *this ranking* (not out of the business — pricing
stays yours to run, ITUK stays in as the pilot site).

**This changes the stakes of item 2 below.** Under (c), the competitor-search gap that
matters shrinks from 342 Tier A lines / EUR 13.54M (whole book) to 122 maintenance lines
/ EUR 2.03M — worth deciding this one first.

Full memo: `00_docs\PURPOSE_DECISION_2026-09-24.md`

---

## 2 · Coverage — keep building our own cross-reference, buy a licence, or stop?

**Status quo.** Our own cross-reference reaches 131 of 16,511 part numbers (EUR
5,639,298 billed). 342 Tier A lines (EUR 13,543,552) have no competitor number and no
peer number at all — our own methods can never reach them, regardless of effort.

**Recommendation (memo).** Freeze the own-build. Get two quotes, each run as a sample
against the same 50 of the 342 lines: TecAlliance's OE Parts Data, and re-opening Eucon
PartsPool. **Buy only if the sample clears 12.3% of that sample's billed euro** — the
threshold below which a licence adds nothing our own route couldn't add for free.

**Your call:** approve requesting the two sample quotes? (No purchase — a test only.)

**Depends on item 3.** If Eucon's terms forbid continued use of what we already hold,
our own route falls from 131 parts to zero immediately, and this becomes licence-or-stop
for the whole book, not only the 342-line gap.

Full memo: `00_docs\COVERAGE_DECISION_2026-09-24.md`

---

## 3 · Eucon — contract ended 31 July 2026, four questions still open

**Status quo.** Eucon confirmed in writing (8 Jan 2026) that the PartsPool contract ends
31 July 2026 — as of today it has ended. 93% of our current cross-reference (7,157 of
7,701 match rows) is Eucon-sourced. Four questions are unanswered: (1) is any related
Eucon contract still live; (2) do the terms allow price monitoring; (3) do they allow
outside-EU processing — i.e. sending Eucon-derived rows to DeepSeek; (4) now that it has
ended, may we keep using what we already downloaded, or must it be deleted/returned.

**Your call:** who chases these four — Legal, the contract owner in Sales – Vehicle
Parts, or both? The memo names roles, not people; it needs a name from you.

**Already in force regardless of your answer** (no sign-off needed, already being
followed): no Eucon-derived row goes to DeepSeek or outside the company; nobody logs
into the Eucon portal; nobody asks Eucon what the `OE RRP` column means until Legal
clears it; no Eucon file is touched, moved or deleted.

Full memo: `00_docs\EUCON_LICENCE_BRIEF_2026-09-24.md`

---

## 4 · Ireland / Portugal 2013–14 — exclude as a standing rule?

**Status quo.** Two fleet rows (Ireland CV LD, Portugal CV LD) drop 99.5% and 99.9% in
one year. Confirmed: not fixable from any source on disk — the pre-2014 figures count a
different population and no registration source reaches back far enough.

**Recommendation (memo).** A clean exclusion, not a repair: treat 1990–2018 as unusable
fleet levels on the affected rows; trusted window becomes 2019–2025; the BVDB pack's
existing (empty) `fleet_quality_note` column carries the caveat text instead of a number.

**Your call:** approve this as the standing rule — no rebuild, just a labelling
convention going forward?

**Flagged, not part of this decision:** the 41.4% Ireland GPS-vs-ceiling gap is *not*
caused by this break. It's a stale version-17 fleet value (3,056) still sitting in
`gps_spu_by_distributor.csv` from before the June 2026 UIO rebuild. That sits under the
existing UIO V21 hold and isn't reopened by this brief.

Full memo: `00_docs\IE_PT_BREAK_2026-09-24.md`

---

*Sources: the four memos named above, each independently verified against its own text
before this brief was written (no figure re-typed from a summary or the board log).*

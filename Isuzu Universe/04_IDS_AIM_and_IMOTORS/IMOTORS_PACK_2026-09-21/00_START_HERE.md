# Imotors (Portugal) — start here

**Pack built:** 2026-09-21 · **internal** · every figure was read from a file that already existed on
this machine. Nothing was rebuilt, and no message was drafted or sent.

**Folder:** `C:\Users\jerom\Desktop\claude\ISZE\Isuzu Universe\IMOTORS_PACK_2026-09-21\`

---

## The ask

Design and draft **the first Imotors page**: sixteen named Portuguese dealers, each read against the
Portuguese market rather than against each other. The page is a conversation starter for Imotors, not
a league table — the same idea as the ITUK dealer page, but built on what Portugal actually has, which
is different in two important ways (below).

Folders in this pack:

| File | What it is |
|---|---|
| `00_START_HERE.md` | This file: the ask, the five facts that decide the design, the hard rules, the paste prompt |
| `01_IMOTORS_DATA_INVENTORY.md` | Every Portugal file on disk: path, grain, figures, and what is missing |
| `02_DEALER_DIMENSION.md` | The sixteen dealers: score, section scores, city, address, coordinates, visit date — readable |
| `03_DATA_TABLES.md` | The data tables, readable |
| `04_DATA_TABLES.csv` | The same tables machine-readable: `table,row_id,payload_json` |
| `05_WE_PACK_AND_OPEN_ITEMS.md` | The 12 August Astara WE business review: what was asked of whom, and what is still open |
| `06_CUSTOM_INSTRUCTIONS.txt` | Paste this into the custom-instructions box before uploading the files |
| `07_UPLOAD_GUIDE.md` | What to upload, in what order |
| `08_REVIEW_BRIEF.md` | What to return, and in what shape |
| `09_dealer_dimension.csv` | The dealer table as a file |
| `10_checklist_areas.csv` | The subcategory view as a file |
| `_FACTS.json` | Every headline number in one place, so nothing has to be recomputed |

---

## The five facts that decide the design

**1. Sixteen dealers are assessed, and sixteen are the whole population.** The 2026 dealer-standards
round covers Amatoscar (three sites), Auto Reno Minho (four), Astara Retail (two), and seven
independent sites — Rolmax, Auto Industrial Leiria, Auto Imperial, Socarros Caldas, MCar, Soter Máquinas
and Xanauto. Four of the sixteen are Astara's own retail outlets. Nothing below the distributor exists
for any other Portugal number in this workspace.

**2. The score on every dealer is the dealer's own self-assessment.** The same scorecard carries an
IMG/ISZE column, and on all sixteen sheets that block is **zero** — it was never filled in. So the
scores are not evidence of what a dealer does; they are evidence of what a dealer says about itself,
plus a visit by an ISZE evaluator in April 2026 who recorded the site details. Any page must say that
plainly, and the honest read is the *relative* position of a section, not the absolute score.

**3. The market number that matters sits in Portugal's own file, not in the network average.**
Portugal's billed parts in 2025 were €1,709,794 against a target-spend ceiling of €3,494,069 — **48.9%
captured, and that is the second-lowest of eighteen markets** (only Hungary is lower). Portugal
therefore cannot be shown as a dealer that is failing against a well-performing average; the market
itself is the problem, and a dealer page that does not say so will read as unfair.

**4. There is no per-dealer purchase or fleet figure anywhere in the workspace.** The sales-to-dealer
file Imotors sent is a single national row: 51,363 units in 2025 across 5,712 part numbers, no dealer
name. No Portugal file connects a dealer name to a billing account, so a "what this dealer bought"
figure cannot be produced, and no dealer has a vehicle count. The page must be designed to work without
both, and must say they are missing rather than quietly using a market figure as if it were a dealer one.

**5. Portugal's parc is measured, and this is a strength the page should use.** Official I-Motors
registrations convolved with the survival curve give a 2025 N-series parc of 2,390 vehicles, of which
**63.6% are the 3.5 t N35**. The 69.0% that earlier papers used was a Japanese shipment mix, not a parc
share, and has been corrected. The fleet denominator actually in use for billing, though, is different
again — **8,176 trucks** in the GPS file — and which of the two becomes the base is an open decision,
not a fact. Say which one a figure uses, every time.

---

## Hard rules for whatever is drafted

- **No league table as the headline.** Ranking dealers on a self-assessed score rewards whoever marked
  themselves generously. Rank inside a section, with the number stated as self-assessed.
- **No per-dealer fleet, no per-dealer purchase, no share of market, no sell-through.** None of the four
  exists for Portugal. Writing one in from a market figure is the failure this pack exists to prevent.
- **The market's own 48.9% capture must be on the page**, because without it the sixteen scores read as
  a dealer problem.
- **One year, one round.** The assessment dates all fall in March–April 2026. There is no earlier round
  to compare against, so no trend and no year-on-year.
- **No euro label on a workshop figure.** And no figure without its source named.
- **Plain business English.** "The dealer's own assessment", "what the market is billed", "trucks in
  service". No internal short names, no codes without a plain gloss the first time.

---

## What the assistant is asked to return

Work the four blocks in `08_REVIEW_BRIEF.md`, in order, with those headings. Where this pack
contradicts an idea you bring with you, say so and revise your idea. Name every gap as a gap, with the
file or the person that would close it. Do not invent a number — write **not in the pack** and say what
would settle it. Do not propose rebuilding any existing dashboard.

---

## Paste prompt

> You are designing the first Imotors (Portugal) page for ISZE, a parts and aftersales business that
> supplies Isuzu distributors in Europe. Read `00_START_HERE.md` first, then `02_DEALER_DIMENSION.md`,
> `05_WE_PACK_AND_OPEN_ITEMS.md` and `03_DATA_TABLES.md`. Then work the four blocks in
> `08_REVIEW_BRIEF.md` in order and return them under those headings. The sixteen dealers in
> `02_DEALER_DIMENSION.md` are the whole population and their scores are their own self-assessment —
> the independent assessment column is empty. Nothing anywhere in the pack gives a dealer its own
> purchase volume or its own vehicle count; design around that and say so, rather than substituting a
> market figure. Do not invent a number. Where the pack does not contain something, write "not in the
> pack" and name what would settle it.

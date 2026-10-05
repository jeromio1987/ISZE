# Upload guide — the Imotors (Portugal) pack

**Pack:** `C:\Users\jerom\Desktop\claude\ISZE\Isuzu Universe\IMOTORS_PACK_2026-09-21\`
**Built:** 2026-09-21 · internal

Ten files. Upload them in the order below. If the interface caps you, stop after file 4 — that is the
set that carries the argument. The rest make the answer better rather than enable it.

| # | File | Size | Why |
|---|---|---|---|
| 1 | `00_START_HERE.md` | 6.6 KB | The ask, the five facts that decide the design, the hard rules, and the paste prompt |
| 2 | `02_DEALER_DIMENSION.md` | 6.5 KB | The sixteen dealers: score, five section scores, city, visit date, and what the scores do and do not say |
| 3 | `05_WE_PACK_AND_OPEN_ITEMS.md` | 6.2 KB | The August Astara review: the fleet-base argument, the dealer-standards tool, and the fourteen open actions with their owners |
| 4 | `03_DATA_TABLES.md` | 11 KB | The data tables, readable |
| 5 | `01_IMOTORS_DATA_INVENTORY.md` | 13 KB | Every Portugal file on disk and the limits of each — this outranks anything the assistant assumes is available |
| 6 | `06_CUSTOM_INSTRUCTIONS.txt` | 2.4 KB | Paste this into the custom-instructions box, not as a file |
| 7 | `04_DATA_TABLES.csv` | 28 KB | The same tables machine-readable: `table,row_id,payload_json` |
| 8 | `09_dealer_dimension.csv` | 3.9 KB | The dealer table as a file, including addresses and coordinates |
| 9 | `10_checklist_areas.csv` | 0.8 KB | The checklist subcategory view |
| 10 | `08_REVIEW_BRIEF.md` | 3 KB | What to return, and in what shape |

## What to paste

Put the contents of `06_CUSTOM_INSTRUCTIONS.txt` into the assistant's custom-instructions box first —
about 2,400 characters, so it fits comfortably. Then upload the files. Then paste the prompt from the
end of `00_START_HERE.md`.

## Four things to know before sending it

**There is no per-dealer purchase figure and no per-dealer fleet in this pack, and that is deliberate.**
Neither exists anywhere in the workspace for Portugal. The custom instructions and the brief both say so
in as many words, so an assistant that produces one has ignored the instruction rather than found
something new.

**The dealer scores are self-assessed.** The independent assessment column is empty on all sixteen
sheets. This is stated in four places in the pack because it is the single easiest thing to misread.

**The parc in this pack is measured; the fleet denominator used for billing is a different number.**
Portugal's own rebuild gives a 2025 N-series parc of 2,390, 63.6% of it the 3.5 t N35. The GPS file bills
against 8,176 trucks. Both are in the tables, labelled, and which one becomes the base is still an open
decision — do not let the answer quietly pick one.

**One thing in the pack is a meeting record, not a measurement.** `05_WE_PACK_AND_OPEN_ITEMS.md` is the
12 August review, and its action status column was simply read from the minutes — it was not checked
against the mailboxes. If the assistant treats an action as still open, that is where it came from.

## What the pack deliberately does not answer

- **What Imotors has asked for, beyond the August meeting.** There may be later threads this pack does
  not carry.
- **Anything about Spain or the wider Astara Western Europe region.** This is Portugal only. The August
  meeting covered Belgium, the Netherlands and Poland as well, and those numbers are not here.
- **Line-level billing.** Every table is an aggregate. No customer names, no invoice lines.
- **Any second year.** One assessment round, March–April 2026, and no earlier one.

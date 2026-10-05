# Verification record — Isuzu Universe folder index

**Document:** `UNIVERSE_FOLDER_INDEX_2026-09-23.pdf`
**Staged at:** `_build_index\UNIVERSE_FOLDER_INDEX_2026-09-23.pdf` — see "Where the rebuild sits"
**Source text:** `_build_index\UNIVERSE_FOLDER_INDEX_2026-09-23.md`
**Renderer:** `_build_index\build_index.py`
**Launcher:** `OPEN_UNIVERSE_FOLDER_INDEX.cmd` beside the document at the folder root
**Revised:** 23 September 2026, second issue · internal · not circulated

---

## Where the rebuild sits

The root file `UNIVERSE_FOLDER_INDEX_2026-09-23.pdf` is held open by a reader on this machine.
The rebuild therefore could not replace it, and it is staged instead at:

```
C:\Users\jerom\Desktop\claude\ISZE\Isuzu Universe\_build_index\UNIVERSE_FOLDER_INDEX_2026-09-23.pdf
```

The root file on disk is the earlier issue, dated 18:04 and 206,504 bytes. The staged rebuild is
the current issue, 158,939 bytes. Close the reader and the same build command will write to the
root path without further change; nothing else needs doing.

## What changed in this issue

Two things, both asked for after the first issue:

1. **The charcoal house style now carries the whole document.** Every page field is `#24282C`,
   edge to edge, in the same visual system as the white paper and megaprompt section 8. The
   mechanism is the one the white paper already proved: the charcoal plate is drawn into each
   page's own content stream underneath the text, because headless Chrome paints an element
   background only inside the printable box and a naive `body` background prints white pages with
   a coloured block in the middle.

2. **Every reference to build tooling has been removed.** The page that listed the build folders
   and their scripts is gone, and so is every other mention of them: no `_build_*` folders, no
   `.py` names, no receipt or verification filenames, no `_qa` folders, no probe scripts, and no
   counts of scripts. What replaced it is one plain paragraph saying that each document is
   generated from its own source text so a chart cannot drift from the data behind it, and that
   each finished document carries a short record of what was checked. No filenames in that
   paragraph.

One content correction was carried in at the same time: the undated showcase has been deleted, so
the document now names only the dated one as the showcase, with no note that two copies ever
existed.

## Banned-term search, before and after

Measured on the extracted text of the finished document. The "before" column is the first issue;
the "after" column is this one.

| Term | Before | After |
|---|---|---|
| `_build` | 10 | 0 |
| `.py` | 23 | 0 |
| `.cmd` | 9 | 0 |
| `SHIP_RECEIPT` | 2 | 0 |
| `VERIFICATION` | 1 | 0 |
| `_qa` | 8 | 0 |
| `_probe` | 3 | 0 |
| `build_` | 15 | 0 |
| `figures` | 5 | 1 |
| `docbuild` | 1 | 0 |
| `check_` | 5 | 0 |
| `receipt` | 4 | 0 |
| `script` | 8 | 0 |
| `_raw` | 0 | 0 |
| **total** | **94** | **1** |

A second scan for the shapes rather than the words: folders beginning with an underscore (none),
`.py` filenames (none), `.cmd` filenames (none), receipt or verification filenames (none), the word
"probe" (none), `_qa` (none), `_build` (none), and any count of scripts such as "eighteen",
"fourteen" or "forty" (none).

**The one remaining hit, justified:** the word "figures" appears once, inside the description of
`UNIVERSE_WHITE_PAPER_KILLER_MEGAPROMPT_2026-09-23.md` — "the five pillars, the figures wanted, and
the audience". That is the chart list a brief asked for, in a sentence about a document a reader
may open. It is not a reference to a script, and no filename is attached to it.

## Page-field colour, measured

From `check_charcoal.py`, sampling the painted pixels of every page including the margins. Quoted
as measured:

| Page | Dominant colour | Share | Margin sample | Verdict |
|---|---|---|---|---|
| 1 | `(36, 40, 43)` = `#24282C` | 72% | `(36, 40, 44)` | OK |
| 2 | `(36, 40, 43)` | 66% | `(36, 40, 44)` | OK |
| 3 | `(36, 40, 43)` | 61% | `(36, 40, 44)` | OK |
| 4 | `(36, 40, 43)` | 48% | `(36, 40, 44)` | OK |
| 5 | `(36, 40, 43)` | 47% | `(36, 40, 44)` | OK |
| 6 | `(36, 40, 43)` | 51% | `(36, 40, 44)` | OK |

No page is white, and no page has a white margin: the edge sample on every page is the charcoal
field, which is the fault this check exists to catch.

## Contrast check output

```
== text sitting on a pale panel
  0 spans found on a pale panel; all ink

== body text colour
  (255, 255, 255)     79 spans  OK
  (204, 209, 210)     12 spans  OK
  (215, 25, 32)       11 spans  OK

== markdown left unrendered: none
== unmapped glyphs: 0

PASS - every page is charcoal, no page is white, and no white text sits on a pale panel.
```

The check exits non-zero on any failure and prints FAIL with the offending page, so a regression
fails the build loudly rather than warning. Body text is white or `#CCD1D2`; red `#D71920` is used
on 11 spans only, which is the emphasis budget; no low-contrast grey is used.

## Layout

Reported by the folder's own layout checker on the rendered document: stranded headings none,
figures parted from their caption none, tables split from their introduction none. No page is a
near-empty sheet. Column occupancy by page: 0.95, 0.66, 0.36, 0.88, 0.82, 0.90 — page 3 is the
contents page and ends where its list ends, which is intended.

## Page count, images taken, images read

**Pages: 6. Images taken: 12. Images read: 12.** Two sets of six were taken:

- `_build_index\_qa\p01.png` … `p06.png` — by the build itself, at 110 dpi
- `_build_index\_qa_read\page01.png` … `page06.png` — at 150 dpi (1240 x 1754 px), which is what I
  read page by page

I read all twelve myself, one at a time, at full resolution, and I am the one reporting this.

## Names printed

30 distinct names are printed. All 30 resolve to a file or folder on disk. 0 failed. They are the
seven documents, the eight source files in `01_Strategy\`, the three files of the handover pack,
the eight working folders, and the two withdrawn papers plus the kept-aside older showcase — all of
which a reader may want to open. Nothing prints a launcher filename any more: the launchers are
described in words.

## Launcher

`OPEN_UNIVERSE_FOLDER_INDEX.cmd`, 65 bytes, CRLF throughout (hex ends `...22 0D 0A`), opening
`UNIVERSE_FOLDER_INDEX_2026-09-23.pdf` in its own folder. The root target exists. I did not run it.

## What I could not verify

- **That the staged rebuild can take the root path.** It cannot while the reader holds the old file
  open. The write path is exercised and correct — the same build wrote the root file successfully
  before the reader opened it — but the final placement of this issue is unproven.
- The internal workings of the papers' own builds are described from their headers and file names
  only. This document no longer names them, so nothing here turns on it.

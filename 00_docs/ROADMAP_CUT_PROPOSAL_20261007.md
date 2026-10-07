# ISZE_ROADMAP.md — proposed cut (NOT applied)

Written 2026-10-07 as part of U29 task F. **Nothing in this file has been applied.** Jerome
decides.

## What it is now

`00_docs/ISZE_ROADMAP.md` is **35.9 KB** (36,785 bytes, 236 lines). The cap is **15 KB**. At least
**21.4 KB** has to go.

Its own header says what it should be: *"This hub stays short on purpose — it is a queue, not an
archive."* The size is not spread evenly. One block is almost half the file.

## Where the size actually is

| Lines | Bytes | What |
|---|---|---|
| 80–107 | **14,572** | the "Answered 2026-09-19 — six items decided, three still open" narrative block, plus the nine decided/closed D-rows (D01, D02, D03, D08, D13, D15, D24, D25, D26 = 9,262 B of it) |
| 23–51 | 5,634 | §1 Open queue (16 items) |
| 108–166 | 3,754 | §3 Live now |
| 167–195 | 3,805 | §4 Shipped |
| 52–79 | 3,806 | §2 Waiting on Jerome (the B-table itself is fine) |
| 196–215 | 1,758 | §5 Closed — do not reopen |
| 216–230 | 1,376 | §6 Domain roadmaps |
| 231–236 | 619 | §7 Integrity and hygiene |

## The cut, in order of return per line moved

1. **Lines 80–107 → `DECISIONS.md` (saves ~14,000 B).** This is the single cut that gets the file
   most of the way. All nine rows in it are *decided or closed*, not open work — the header of the
   file says decided rationale lives in `DECISIONS.md` and `CHANGELOG.md`, and these are already
   recorded there. Leave behind three lines: "D01–D26 decided; the register still has **two open
   items (D05, D24)**; full record in `DECISIONS.md`." The register status itself
   (`DECISIONS_AWAITING_JEROME_2026-09-19.json`) does not move; only the prose recounting of it.
2. **§4 Shipped, rows dated 2026-07 and 2026-08 → `CHANGELOG.md` (saves ~2,400 B).** The file says
   "one line each"; several of those lines are multi-sentence incident write-ups (the 2026-10-06
   PriceLedger row alone is 976 B). Keep the two 2026-10 rows and one 2026-08-25 line, point the
   rest at `CHANGELOG.md`.
3. **§1 Open queue — tighten five long cells (saves ~2,500 B).** Items 16 (pricing programme),
   9 (residual PR00 gaps), 4 (tender portal coverage), 13 (scraper quality — already "Done", so it
   is a shipped line in the queue), and 8 (fig-key) carry measured detail that belongs in the
   `roadmaps/*.md` files they already link to. Keep the state and the blocker; move the numbers.
4. **§2 intro paragraphs above the B-table → `DECISION_DISCIPLINE.md` (saves ~2,000 B).** The
   "How this list gets shorter" and register-status narrative is rule text, not a queue row.

That is ~21 KB, which lands the file just under 15 KB. Nothing is deleted — every cut item moves to
the file that already owns that kind of content.

## Deliberately NOT cut

- **§2's B-table.** It is the waiting list; every row is a live decision.
- **§5 Closed — do not reopen.** 1.8 KB and it is the file's protection against re-litigating
  settled questions.
- **§6 and §7.** Small, and they are the routing.

## One honest note

The 15 KB cap is a rule from `jerome-token-friction.mdc`. The biggest block in the file is a recount
of decisions **already recorded in `DECISIONS.md`**, so the cut above is not a loss of information —
it is removing a second copy. If the cap is not worth enforcing this week, doing nothing costs only
the reading overhead.

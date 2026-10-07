# Universe decisions locked 7 Oct 2026

From the approved U1–U26 assessment plan. Internal.

| # | Decision | Locked as | Evidence |
|---|---|---|---|
| 1 | Merge PR 70 (U28 stack) | **YES — MERGED** | https://github.com/jeromio1987/ISZE/pull/70 · merge `66a746a4` · 2026-10-07T11:20:42Z |
| 2 | Delivery / tax basis (U29-B) | **Verified; eligible still 0** | Field + mutation proven. PR 71 retargeted to `main` → now **MERGEABLE** but **631 files / ~635k lines** (U26 scrape cache). Do **not** smash-merge; follow code-only path in `UNIVERSE_PR71_FIX_LIST_2026-10-07.md`. Detail: `UNIVERSE_U29B_LEDGER_VERIFY_2026-10-07.md` |
| 3 | Portugal competitor scrape | **UK first; Portugal insufficient for now** | Two host sweeps; no usable PT shop pages; bar 50 rows, PT ~27. No third automated sweep. Hand collection only if you later ask |
| 4 | First real INTERNAL feeds | **Tender + PRISM + IDS (ITUK + Portugal I-Motors)** | PR 72 MERGED `41cddad1` (tender + PRISM). PR **77** MERGED `7d2c1630` — real IDS answers for Ferndown (ITUK) and Astara Lisboa (Portugal). Stock still optional later — needs a real stock observation file, not billed-vs-sales-to-dealer |
| 5 | ACCEPT-04 / 05 participants | **Names blank — you fill** | Roster: `UNIVERSE_ACCEPT_PARTICIPANT_ROSTER_2026-10-07.md`. Scripts on PR 73 |
| 6 | Universe board scores | **Re-graded 7 Oct 2026** | Live rebuild: groundwork **43%** (26/60). AIM accuracy sample file still missing (scores 0). Launcher `OPEN_ISZE_UNIVERSE_BOARD.cmd`. |

## Landed after the assessment pack (7 Oct, small pieces)

- PR **73** MERGED (`3b28c340`) — acceptance scripts on main.
- PR **74** MERGED (`3af2f752`) — IT sign-in draft + module audit + roadmap cut proposal.
- PR **75** MERGED (`0a9d5b2d`) — delivery-basis schema/parsers only.
- PR **76** MERGED (`545f1a02`) — coverage CSVs; eligible still 0.
- PR **71** CLOSED (superseded by 75/76; fat scrape cache stayed out of main).
- PR **77** MERGED (`7d2c1630`) — real IDS for ITUK (Ferndown) + Portugal I-Motors (Astara Lisboa) on INTERNAL.

## Still open (your call)

- Fill participant names on the roster before any ACCEPT run.
- Hand a **real stock observation** file if you want CONNECT-06 filled on INTERNAL (not inventable from billing).
- Universe board re-graded 7 Oct (see decision #6). Accuracy sample CSV still missing.

# Incident: Universe status answered from September papers, not from U1-U8

Date: 2026-10-06
Audience: Claude (next session / Desktop). Internal.
Trigger: Jerome asked "where are we with isuzu universe". The parent agent answered from the 23 Sep Universe 3.0 papers, the 24 Sep universe board (0 of 5 tools), and the 5 Oct Isuzu Truck UK dealer pages labelled P1-P5 and R6-R8. Jerome then said, verbatim: "Look you build today and yesterday on a lot it s was called U1 to U8". He then asked for this report: how that miss was possible.

Do not treat this file as a status update to send him. It is the mechanism of the miss.

## 1. Incident one-liner

The agent reported last month's paper and a dealer-page folder naming scheme (P1-R8), and did not open the live 5-6 Oct work that is actually named U1 to U8.

## 2. What he asked vs what was answered

He asked where Universe is now. That is a recency question.

What was answered:

- The 23 Sep Universe 3.0 paper / annex / deck / showcase under `ISZE\Isuzu Universe\` (INDEX.md still points at those as "the current edition").
- The 24 Sep universe board, file `01_data\00_derived\universe_board_state.json`, `built_at` 2026-09-24T22:39:23, headline "0 of 5 tools a distributor can open".
- The 5 Oct folder `Isuzu Universe\07_Pilot_ITUK\pages` with dealer packs named P1-P5 and R6-R8 (Ferndown, Cordwallis, Norfolk, Aquila, Cymru, Cumbria, RH Northampton, Allports).

Those P/R labels are the eight ITUK dealer page folders. They are not the programme names U1-U8. The files themselves say P1 / R8, not U1 / U8. U1 and U2 produced those pages; they are not the same label.

He then had to correct the agent in chat. That is the miss.

## 3. What U1-U8 actually are (found on disk, 2026-10-06)

They are Cursor briefs (and their reports), written 5-6 Oct 2026, sitting **outside the ISZE repo**:

`C:\Users\jerom\Desktop\claude\docs\cursor_briefs\`

Run order file (not a brief): `2026-10-05_U0_universe_RUN_ORDER.md` (mtime 2026-10-05 21:21). It originally listed U1 then U2 then U3-U5. U6, U7, U8 were added as later briefs on 5-6 Oct.

| ID | Brief (mtime) | Report (mtime) | What it is |
|----|---------------|----------------|------------|
| U1 | `2026-10-05_U1_pilot_parts_pages.md` (2026-10-05 20:38) | `2026-10-05_U1_pilot_parts_pages_REPORT.md` (2026-10-05 21:24) | One 2025 parts page per ITUK pilot-side dealer, at reference dealer price. Output lives under `ISZE\Isuzu Universe\07_Pilot_ITUK\pages\` as P1-P5 / R6-R8 `Parts_2025.html` (pages mtime 2026-10-05 about 20:56). |
| U2 | `2026-10-05_U2_pilot_ids_profiles.md` (2026-10-05 20:54) | `2026-10-05_U2_pilot_ids_profiles_REPORT.md` (2026-10-06 06:21) | One 2026 Dealer Standards page per the same eight dealers (`Dealer_Standards_2026.html` in those same P/R folders; IDS check screenshots 2026-10-06 about 06:18). |
| U3 | `2026-10-05_U3_pricing_wave1.md` (2026-10-05 21:21) | `2026-10-05_U3_pricing_wave1_REPORT.md` (2026-10-05 23:04) | Pricing tool wave 1: DATA-01, UX-01, CASE-06 in `Isuzu Universe\05_AIM_Universe`. Ran as part 1 of `2026-10-05_U3U5_pricing_run.md` in worktree `_worktrees\ISZE_u35`. |
| U4 | `2026-10-05_U4_pricing_wave2_screens.md` (2026-10-05 21:21) | `2026-10-05_U4_pricing_wave2_screens_REPORT.md` (2026-10-05 23:04) | Pricing tool wave 2a: UX-02, UX-05, UX-06 (screens). Same U3-U5 run. |
| U5 | `2026-10-05_U5_pricing_wave2_data_cases.md` (2026-10-05 21:21) | `2026-10-05_U5_pricing_wave2_data_cases_REPORT.md` (2026-10-05 23:04) | Pricing tool wave 2b: DATA-02, DATA-03, CASE-08. Same U3-U5 run. Jerome on 5 Oct: "let it run straight to U 5". |
| U6 | `2026-10-05_U6_pricing_wave3.md` (2026-10-05 23:05) | `2026-10-05_U6_pricing_wave3_REPORT.md` (2026-10-06 00:03) | Pricing tool wave 3: DATA-07, UX-03, UX-04, UX-08, UX-07. Worktree `_worktrees\ISZE_u6`. Touched AIM `src` and tests. |
| U7 | `2026-10-06_U7_ux07_narrow_shell.md` (2026-10-06 00:20) | `2026-10-06_U7_ux07_narrow_shell_REPORT.md` (2026-10-06 05:53) | UX-07 via maintained `src\shell\shell_narrow.css`. Worktree `_worktrees\ISZE_u7`. |
| U8 | `2026-10-06_U8_review_wave.md` (2026-10-06 07:00) | `2026-10-06_U8_review_wave_REPORT.md` (2026-10-06 08:32) | Purchase-review wave REVIEW-03, 04, 06, 07, 08. Worktree `_worktrees\ISZE_u8`. Scratch files and shots also under the briefs folder. |

`TASKS_96.txt` is **not** U1-U8. It is the 96-task pricing-tool plan (BASE-01, DATA-01, UX-01, REVIEW-03, and the rest). The U labels are the Cursor waves that execute slices of that plan. `05_AIM_Universe\progress\progress.json` was written 2026-10-06T06:11:31Z (`total_tasks` 96; counts in that file: technically verified 49, implemented 3, not started 44). Quote those counts only from that file; do not invent a U1-U8 scoreboard from them.

There is no folder named U1, U2, ... U8 under `Isuzu Universe`. A filename search for U1 through U8 inside that tree returned zero hits. The names live in `docs\cursor_briefs\` and in 5-6 Oct agent transcripts (example: transcript `0ebf4920-2ba4-4d7b-a3d5-937ce8916230.jsonl` on 2026-10-06: "Cursor brief U8").

Do not call the P1-R8 pages "U1-U8". Only U1 (parts) and U2 (Dealer Standards) write those eight dealer folders. U3-U8 are the pricing tool.

## 4. Why the agent could miss it (mechanism)

Several independent traps stacked. Any one would have been enough.

**1. Cursor does not search `Isuzu Universe\`.**
`ISZE\.cursorignore` contains `Isuzu Universe/**` with the comment that it is about 13k files and you must search it by naming the path. Grep / Glob / Read from the ISZE workspace therefore skip the live folder. INDEX.md and the strategy papers are in that ignore. The U1 report already recorded the same fact: Write / image-Read cannot open paths under `Isuzu Universe\` (permission denied) on this machine.

**2. The U names are not in the ISZE repo.**
U1-U8 briefs sit in `C:\Users\jerom\Desktop\claude\docs\cursor_briefs\`, one directory above ISZE. An agent that only searches the workspace will never see `2026-10-05_U1_pilot_parts_pages.md`. `00_docs\ISZE_ROADMAP.md` contains the word "universe" zero times and "U1" zero times. There is no status line for him to copy.

**3. Recency was not used.**
"Where are we" means: what was written yesterday and today. On disk that is obvious if you sort by last-write time: `07_Pilot_ITUK` 2026-10-05 20:46, AIM `progress.json` 2026-10-06 08:28, AIM `src` and tests through 2026-10-06 morning, briefs U1-U8 5-6 Oct. The agent instead opened INDEX.md (still the 23 Sep edition) and `universe_board_state.json` (`built_at` 24 Sep). Stale files that still call themselves current will always win if you do not check last-write time.

**4. The nearest eight labels were treated as the answer.**
Once the agent got into `07_Pilot_ITUK\pages`, the folders are named P1-P5 and R6-R8. That looks like a complete set of eight. It is the dealer pack, not the workstream names. The agent did not search the string U1. Jerome's correction is exactly this mix-up.

**5. September artefacts still look authoritative.**
INDEX.md leads with Universe 3.0 of 23 Sep. The board still says 0 of 5 tools. `TASKS_96.txt` header still says 22 Sep, and the BASE task blocks in that text file still say "Not started", even while `progress.json` has moved. Quoting the paper or the board without the 48-hour file list is how you report a frozen programme while eight briefs ran overnight.

**6. Transcripts were not opened.**
5-6 Oct transcripts under `C:\Users\jerom\.cursor\projects\c-Users-jerom-Desktop-claude-ISZE\agent-transcripts` mention "Cursor brief U8" and the U-named worktrees. "Where are we" should have started there, or in `docs\cursor_briefs\*U*.md`, not in the 23 Sep PDF.

None of this is mysterious. The live names were sitting in a folder the status search never opened, under a Cursor ignore the status search never overrode, labelled in a scheme (U) the agent never typed.

## 5. What a correct "where are we" would have opened first

In this order:

1. `C:\Users\jerom\Desktop\claude\docs\cursor_briefs\` files matching U1 through U8 with last-write 5-6 Oct (the table in section 3).
2. `2026-10-05_U0_universe_RUN_ORDER.md`.
3. Agent transcripts dated 2026-10-05 and 2026-10-06 containing U1 / U8.
4. Last-write times under `ISZE\Isuzu Universe\` via Shell (`cmd /c dir` or Python walk), because Read/Glob are blocked: `07_Pilot_ITUK` and `05_AIM_Universe\progress\progress.json` / `src` / `tests`.
5. Only then the 23 Sep paper, and only as background. The 24 Sep board is twelve days stale for this question.

## 6. Rule for next time

If Jerome asks where Universe is:

1. Search U1 U2 U3 U4 U5 U6 U7 U8 in `docs\cursor_briefs\` and in the last 48 hours of transcripts **before** quoting any September paper.
2. List files under `Isuzu Universe\` touched in the last 48 hours (Shell, not workspace Grep).
3. Do not answer from INDEX.md, the 3.0 PDF, or `universe_board_state.json` until those two lists are in front of you.
4. Do not rename P1-R8 as U1-U8. P/R are dealer folders from U1/U2 only.
5. `TASKS_96.txt` is the 96-task list, not the U wave names. Read `progress.json` for what the pricing tool currently records.

## 7. Provenance / what this file does not claim

- Numbers in this report are file last-write times, brief titles, and counts copied from `progress.json` / the board JSON as read on 2026-10-06. No new KPIs.
- This file does not grade whether each U wave is accepted by Jerome. It only names the briefs and reports that exist.
- This file does not rebuild, ship, or mail anything.

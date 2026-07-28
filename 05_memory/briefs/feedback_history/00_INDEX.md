# Feedback history — index

This collects all "Feedback" scheduled-task runs. Runs #1–11 (through 3 Jul 2026) were reconstructed from chat transcripts — **not** the original files, which lived in isolated per-session sandboxes with no lasting access. Runs #12–15 (17 Jul onward) are original, written directly to this folder. 15 entries total as of 26 Jul 2026. See each file's header for whether it's full recovered text or a reconstruction from the assistant's own chat summary.

Best-guess chronological order (oldest → newest). Where a run gave itself an explicit date/filename, that's used; otherwise marked approximate.

| # | File | Date | Recovery quality |
|---|------|------|-------------------|
| 1 | `feedback_jerome_2026-05_run1.md` | ~early May 2026 (approx) | Reconstructed from summary |
| 2 | `feedback_jerome_2026-05_run2.md` | ~May 2026 (approx) | Reconstructed from summary + follow-up Q&A |
| 3 | `feedback_jerome_2026-05-15.md` | 15 May 2026 (explicit) | Reconstructed from summary + follow-up Q&A |
| 4 | `feedback_jerome_2026-05_run4.md` | ~mid/late May 2026 (approx) | Reconstructed from summary (short) |
| 5 | `feedback_jerome_2026-05_run5.md` | May 2026 (explicit in header, no day) | **Full text recovered** |
| 6 | `feedback_jerome_2026-06.md` | June 2026 (explicit in header, no day) | **Full text recovered**, incl. a PENS/moving-project addendum |
| 7 | `feedback_jerome_2026-06_loops-addendum.md` | shortly after #6 (approx) | **Full text recovered** — X/Twitter bookmarks review, not a standalone report |
| 8 | `feedback_jerome_2026-07-03.md` | 3 Jul 2026 (explicit) | Reconstructed from summary |
| 9 | `feedback_jerome_undated_A.md` | between #8 and #10 (approx) | Reconstructed from summary (very short) |
| 10 | `feedback_jerome_2026-07-10.md` | 10 Jul 2026 (explicit) | **Full text recovered** — includes follow-up Q&A (drift questions, patches shipped, dashboard fix) |
| — | (duplicate/continuation, not saved separately) | — | A session titled "Feedback" with content identical to #10's tail appears to be a re-opened continuation of #10, not a distinct new report. Noted here for completeness, not filed separately. |
| 12 | `ai_feedback_2026-07-17.md` (saved in `ISZE/05_memory/briefs/`, one level up) | 17 Jul 2026 | Original |
| 13 | `feedback_jerome_2026-07-18.md` | 18 Jul 2026 | Original — first run of the upgraded two-layer prompt (work + Claude usage), run interactively with workspace connected |
| 14 | `feedback_jerome_2026-07-24_bookmarks.md` | 24 Jul 2026 | Original — X bookmarks via `Projects/twitter-mcp` (50 posts); maps to ISZE / myPENS / agent gaps |
| 15 | `feedback_jerome_2026-07-26.md` | 26 Jul 2026 | Original — run interactively after the same day's automated firing aborted (no folder access); verified live scheduled-task list + `FACTS.md`/`DECISIONS.md`/`AUTOMATION_REGISTER.md` against the written record rather than trusting it |

*(Note: `efficiency_eval_multitask_2026-07-24.md`, also in this folder, is a related but separate artifact — a self-audit of multitask/subagent usage from the same day, not a numbered "Feedback" run. Not indexed above; see run #15 and #14 for how it's used.)*

## The pattern across the runs

Runs #1–12 all flag the same two things: (1) the Kosha/ITUK strategic framing is genuinely strong, and (2) analysis consistently outruns closure — the same CLAUDE.md staleness (oil filter capture rate, lubricants margin, AIM CY2024, UIO version), the same "lubricants awaiting IML go-ahead," the same overdue UIO refresh, get flagged, acknowledged, and then reappear in the next run. Runs #3, #8, and #9 name this explicitly as a "building vs. closing" pattern.

**Run #13 (18 Jul) is the first to break the pattern:** tender scraper fixed (data fresh 16 Jul after ~7 weeks stale), price-file canon decided, PMS baseline retired, dead projects deleted — all within a week of the 10 Jul run reformatting its findings as numbered questions instead of prose diagnosis. Refined diagnosis in #13: the loops weren't being avoided, they were buried in report format. Still open as of #13: app-level CLAUDE.md stale (~10 weeks), isze-context skill unverified, three dead scheduled tasks, scraper self-patch decision. Future runs: end with a numbered "waiting on you" list, nothing else.

**Run #15 (26 Jul) finds the 24 Jul package didn't fully land, and the CLAUDE.md fix would have made things worse if it had.** Two independent discrepancies, both found by checking live state instead of the written record: (1) `AUTOMATION_REGISTER.md` calls `isze-weekly-open-loops` Active and `autodoc-monthly-refresh` Retired — the live scheduled-task list shows the former doesn't exist and the latter is still enabled, next-firing 1 Aug; everything else in the register checked out, so this is specific to the newest entries, not general drift. (2) The `isze-context` skill got edited since #13 (0.3% → "9.8%/17.3%" oil-filter capture) — but `FACTS.md`'s own do-not-quote list blacklists both numbers; the correct current figure is 35.1% (IML v7 lane) or the PRISM-lane series in §1b. The 21 Jul CLAUDE.md patch file, still unapplied, carries the wrong one. Refined diagnosis: closure isn't blocked by discipline, it's blocked by the last step (open Settings, find an unlocatable file) never having been turned into something doable from inside a session — hard technical loops close in days when the tools are at hand; this one doesn't have the tools at hand yet. Also new: today's own scheduled firing of `feedback` aborted for lack of folder access, a `feedback`-specific config gap (other jobs retain access on automated runs).

# Cursor brief F3 - automation register matches the live Windows tasks - 2026-10-06
Status: WAITING FOR GO
Written by: Claude, from the live-state audit runs 2026-09-28 / 2026-10-05 / 2026-10-06 and `Get-ScheduledTask`
Run on: a Claude model in Cursor (not Auto)
Start state (I = `C:\Users\jerom\Desktop\claude\ISZE`, T = `C:\Users\jerom\Desktop\claude\_worktrees\ISZE_f3_register`):
T does not exist. After `git -C I fetch origin`, origin/main is `64d9ae26bb4160e2339362eaec5f0585a8241953` or later. I may be on
any branch and hold other jobs' files: expected. Never switch, stage, commit, pull, reset or write in I's working tree. Every git
command below runs in T.
Cursor: follow C:\Users\jerom\.cursor\rules\claude-brief-intake.mdc - read it first.

## Goal
`00_docs/AUTOMATION_REGISTER.md` carries one current row per live ISZE Windows task, with the schedule, the action path and the last
result that `Get-ScheduledTask` / `Get-ScheduledTaskInfo` actually return, so the weekly live-state audit reports no task as live but
missing from, or misdescribed by, the register.

## Why
The audit compares `AUTOMATION_REGISTER.md` against Task Scheduler, and on 2026-10-05 it printed (line 26 of
`05_memory\briefs\automation_drift_2026-10-05.md`, the same line sits at line 26 of `automation_drift_2026-09-28.md`):

```
 9. **[MEDIUM]** (register) Task ISZE_PriceLedger_Weekly is live but appears nowhere in AUTOMATION_REGISTER.md
    - Add a row to the live-state table, or delete the task if it was a one-off.
```

That line is now historical: `ISZE_PriceLedger_Weekly` was added at register line 85 on 2026-10-05 (commit `d49c4235`, merged in
origin/main), and a fresh audit run on 2026-10-06 (step 3) finds no "appears nowhere" line. What remains is the reason the repeat
happened: the register's live-state table is only refreshed by hand, so a row can be added with a stale action path. The PriceLedger
row still names `run_price_ledger_weekly.bat`, while the live task now runs `pythonw.exe ... run_price_ledger_hidden.pyw`. This brief
makes the whole table match reality, once, row by row.

## In scope / out of scope
In:  T; `00_docs/AUTOMATION_REGISTER.md` only (the `## Windows Task Scheduler - live state` table, its `checked` date, and the
     `**Last audited:**` line); this brief's report.
Out: every other file; every scheduled task's definition (no create, delete, enable, disable, import, re-register or edit of XML);
     `04_tools\workspace\isze_live_state_audit.ps1` and `run_live_state_audit.cmd` (the audit is right to complain; fix the register,
     not the audit); the rows for disabled or personal tasks (`ISZE_DelegatorWatch_20min`, `ISZE_EQ_Hit_Session_20260919`,
     `ISZE_DiscountScanner_Weekly`, `SMID_DataFeed_0700`, `SMID_DataFeed_1200`, the claude.ai / Claude Code tab rows);
     `## ISZE active skills`, `## P8 pipelines`, `## Open items (Jerome)`, `## Adding a new job`; I's working tree; any other brief.

## Read first
1. C:\Users\jerom\.cursor\rules\claude-brief-intake.mdc
2. `T\00_docs\AUTOMATION_REGISTER.md` lines 79-91 (the live-state table)
3. `T\04_tools\workspace\isze_live_state_audit.ps1` lines 115-215 (checks 2, 3, 4 - what an audit finding is keyed on)
4. `T\05_memory\briefs\automation_drift_2026-10-05.md` (the quoted line, and the live-task table at the end)
5. C:\Users\jerom\Desktop\claude\docs\cursor_briefs\2026-10-05_F2_priceledger_interrupt.md (house style)

## Steps
1. `git -C I fetch origin`, then `git -C I worktree add W\_worktrees\ISZE_f3_register -b cursor/<run date>-automation-register origin/main`
   (W = `C:\Users\jerom\Desktop\claude`; if a branch of that name exists, stop and ask rather than reusing it).
   Check: `git -C T status --porcelain` empty; `git -C T rev-parse HEAD` equals `git -C I rev-parse origin/main`; record that hash.
2. Capture the live truth, from T, into the report. Check the three commands run and their output is pasted:
   `Get-ScheduledTask | Where-Object TaskName -match 'ISZE' | Get-ScheduledTaskInfo` and
   `schtasks /Query /FO CSV /V | ConvertFrom-Csv | Where-Object TaskName -match 'ISZE'`.
   Expect the eight ISZE tasks in the table below, with these exact values:

| Live task | State | Cadence | Action (live) | Last result |
|---|---|---|---|---|
| ISZE Tender Monitor | Ready | Mon 07:30 | `...\04_tools\ISZE_Tender_Monitor_Install\run_tender_monitor.bat` | 0 |
| ISZE_PMS_IAM_Refresh | Ready | Mon 07:00 | `...\04_tools\autodoc_scraper\run_refresh_scheduled.bat` | 0 |
| ISZE_LiveStateAudit_Weekly | Ready | Mon 08:00 | `...\04_tools\workspace\run_live_state_audit.cmd` | 0 |
| ISZE_PriceLedger_Weekly | Ready | Mon 09:00 | `C:\Python314\pythonw.exe "...\04_tools\delegation\run_price_ledger_hidden.pyw"` | 0 |
| ISZE_CursorWeekDigest_Weekly | Ready | Sun 20:00 | `...\04_tools\workspace\run_cursor_week_digest.cmd` | 0 |
| ISZE_DiscountScanner_Weekly | Ready | Thu 07:00 | `...\04_tools\run_discount_scraper.bat` | 0 |
| ISZE_DelegatorWatch_20min | Disabled | - | `...\04_tools\workspace\run_overnight_orchestrator.cmd` | 0 |
| ISZE_EQ_Hit_Session_20260919 | Disabled | - | `powershell.exe -File ...\01_data\91_build\run_eq_hit_session_20260919.ps1` | 1 |

   Any value that differs: stop and ask Jerome.
3. Run the audit in T with T as its root, and copy its finding lines into the report verbatim:
   `$env:ISZE_ROOT = 'C:\Users\jerom\Desktop\claude\_worktrees\ISZE_f3_register'` then
   `powershell -NoProfile -ExecutionPolicy Bypass -File T\04_tools\workspace\isze_live_state_audit.ps1`
   Check: it writes `T\05_memory\briefs\automation_drift_2026-10-06.md`; quote every line matching
   `(register)` and every `appears nowhere in AUTOMATION_REGISTER.md`. Expect: the PriceLedger absence line from 2026-09-28 / 2026-10-05
   is gone (its row exists on origin/main); record whether that is so.
4. Reconcile the register table, in T. For each live task in step 2, the table must hold exactly one row whose State, Cadence and
   Batch / script cells match the live values, written in the table's own shape (backticked action, relative path under `ISZE\`).
   Change at least: the `ISZE_PriceLedger_Weekly` row's action, `run_price_ledger_weekly.bat` -> the `pythonw.exe` launcher
   `04_tools/delegation/run_price_ledger_hidden.pyw`, with a one-clause note saying why (windowless, so the scheduler gets the real
   exit code). Put each row's real last result in its Notes cell as `Last result <n> (2026-10-06)`. Bump the section heading's
   `(checked 2026-10-05)` to the run date, and the top `**Last audited:**` line to `2026-10-06 (brief F3)`. Do not reorder rows,
   do not touch rows for disabled or personal tasks, do not add a column.
   Check: `git -C T diff --stat` lists only `00_docs/AUTOMATION_REGISTER.md`; `Select-String` finds
   `run_price_ledger_hidden.pyw` and no `run_price_ledger_weekly.bat` in the PriceLedger row.
5. Re-run step 3 in T. Check: the new `automation_drift_<run date>.md` contains no `(register)` line that names a live task as missing
   from, or renamed in, the register, and no line saying a register row is not live. If the audit was already clean in step 3, the
   check is that steps 4's edits did not add one.
6. Commit on `cursor/<run date>-automation-register`, push with `git push -u origin HEAD`, `gh pr create` against `main` titled
   "Automation register: match the live Windows tasks", merge it the way this repo's recent PRs were merged (`gh pr merge <n> --merge`).
   Check: `gh pr view <n> --json state` is `MERGED`; `git -C I fetch origin` then `git -C I log origin/main -1 --format=%H` returns
   the merge commit.
7. Remove T (`Set-Location W` first; no `--force`). Check: `git -C I worktree list` has no `ISZE_f3_register`.

## Landed means
`origin/main` carries the merged commit; the register's live-state table names the PriceLedger action as
`04_tools/delegation/run_price_ledger_hidden.pyw`, every live ISZE task has one row whose values match `Get-ScheduledTask`, and the
audit prints no register-absence line for a live task. Commit hash, PR number and merge commit in the report.

## Stop and ask Jerome if
step 2 values differ from the table; a live task has no row and it is not one of the two disabled ones; a fix would need a change to
a task definition, to the audit script, or to a file outside the "In" list; step 5's check fails twice with the same cause; the audit
cannot run from T or writes its output somewhere the brief does not name.

## Never
create, delete, enable, disable, import, re-register or edit any scheduled task or its XML; edit `isze_live_state_audit.ps1`,
`run_live_state_audit.cmd`, or anything under `04_tools\workspace\`; touch rows for disabled, personal or claude.ai/Claude Code jobs;
invent a schedule, an action path or a last result - read each from `Get-ScheduledTask`; stage or commit in I; use
`git worktree remove --force`; widen to another brief.

## Report back
`2026-10-06_F3_automation_register_REPORT.md` next to this brief, README format: line 1 start-state evidence, one line per step with
the command output, the audit's own quoted `(register)` lines from steps 3 and 5, the corrected table rows, commit hash, PR number and
merge commit. Last line: `git -C I worktree list`.

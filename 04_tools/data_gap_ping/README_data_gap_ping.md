# Data gap ping - usage note

**What it is.** A small read-only command-line tool that answers one question on demand:
*which source-data gaps are still open, and which of them are waiting on me?* It is the
"ping me for data" reminder for the ISZE parts / aftersales analytics work. It does not
run a pipeline, it does not build a dashboard and it does not change anything.

**Where the list comes from.** The tool reads one file:

`ISZE\01_data\00_derived\_data_integrity_open_issues.md`

That file is the single source of truth. Rows added there appear in the tool automatically,
rows removed there disappear - nothing is hardcoded in the script. The tool picks up every
markdown table in that file whose header has an **ID** column and an **Action owner** column.
Other tables in the same file (closed issues, out-of-scope markets, feed staleness) are
deliberately skipped, and the normal output prints how many tables and rows were skipped so
the difference is visible rather than silent.

**Nothing is written.** The tool is read-only: no cache, no log, no state file, no temp file,
no scheduled task, no change to the source markdown. It only reads the file and prints. If the
table format changes so that a row can no longer be read safely (missing ID / Action owner
column, row with a different number of cells than its header, or an escaped pipe inside a cell),
it stops with an error instead of quietly reporting a shorter list.

---

## How to run it

Double-click this file in the same folder:

`C:\Users\jerom\Desktop\claude\ISZE\04_tools\data_gap_ping\RUN_Data_Gap_Ping.cmd`

It opens a window, prints the list, and waits for a key press. To pass a mode, either run it
from a command prompt or drop a shortcut with the argument on the end:

| What you want | Command |
|---|---|
| All open gaps, grouped by action owner (your own group is flagged and printed first) | `RUN_Data_Gap_Ping.cmd` |
| Only what you owe | `RUN_Data_Gap_Ping.cmd -WhatIOwe` |
| Scheduled-run mode | `RUN_Data_Gap_Ping.cmd -Quiet` |
| JSON for a dashboard or another tool | `RUN_Data_Gap_Ping.cmd -Json` |
| Point at a different markdown file | `RUN_Data_Gap_Ping.cmd -Path "<file.md>"` |

The same modes work if you prefer to call PowerShell directly:

```
powershell -NoProfile -ExecutionPolicy Bypass -File "C:\Users\jerom\Desktop\claude\ISZE\04_tools\data_gap_ping\Get-DataGapPing.ps1" -WhatIOwe
```

### Reading the output

- Normal mode: one block per **action owner**, so it is obvious which gaps are not yours.
  The block for `Jerome (you)` is marked `*** YOUR ACTION ***` and always printed first.
  Each gap shows the ID, a one-line summary, the period, what is blocked, who owns the action,
  and the source file(s) named in the row.
- `-WhatIOwe`: a short numbered list of just your items, each with what you owe and what it blocks.
- `-Quiet`: designed for a timer. When you owe something it prints exactly one line naming the gap
  IDs; when there is nothing owed it prints nothing at all and exits 0. It never repeats itself
  and never nags twice.
- `-Json`: a single JSON object - counts (total, owed by you, per owner), the parsed gaps, the
  source file path with its SHA-256 and last-write stamp, and a small glossary (UIO = vehicles in
  service, GPS = spend per unit, UTI = Israel, ITUK = UK). The output is valid JSON on stdout only,
  verified, so a dashboard can read it directly.

Exit codes: `0` fine, `1` source file missing or unreadable, `2` source format changed,
`3` no open-gap table found in the file, `4` bad arguments. Codes 1-3 are also possible from
`-Quiet`, so a scheduled task can tell "nothing owed" apart from "could not read the source".

---

## Wiring it to a Windows scheduled task later (described, not done)

No scheduled task has been created and Task Scheduler has not been touched - this is only the
recipe for when you want it. When you do:

1. **Start** menu -> **Task Scheduler** -> **Create Task** (not "Basic Task", so you can set the
   exit behaviour yourself).
2. **General** tab: name it e.g. `ISZE data gap ping`. Leave "Run whether user is logged on or
   not" unticked for a simple reminder; tick it only if you want it to fire while you are away.
3. **Triggers** tab: add a trigger, e.g. weekly on Monday at 08:00.
4. **Actions** tab -> New -> **Start a program**:
   - Program/script: `powershell.exe`
   - Add arguments: `-NoProfile -ExecutionPolicy Bypass -File "C:\Users\jerom\Desktop\claude\ISZE\04_tools\data_gap_ping\Get-DataGapPing.ps1" -Quiet`
   - Start in: `C:\Users\jerom\Desktop\claude\ISZE\04_tools\data_gap_ping`
5. **Conditions** tab: untick "Start the task only if the computer is on AC power" if you want it
   to run on battery too.
6. **Settings** tab: untick "Stop the task if it runs longer than..." - the tool finishes in about
   a second - and leave "If the task is already running, do not start a new instance".

Two useful notes when you get there:

- `-Quiet` is the right mode for a timer. It stays silent when you owe nothing, so the reminder
  only appears when there is actually something to supply. Use `-Json` instead if you would rather
  write the result into a file for a dashboard later.
- To see the reminder even when nobody is watching the screen, either leave the task set to run
  only when you are logged on (the console window shows for a moment), or add your own logging line
  in front of it (`... -Quiet | Out-File -Append <somewhere>`). The tool itself writes no files.

If you later want the daily version of this in chat rather than on a timer, the same script backs
it: the JSON mode is the intended input for any dashboard or reminder that follows.

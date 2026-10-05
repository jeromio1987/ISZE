# Arming the 20-minute cycle in-session

**Companion to:** `00_docs/agent/DELEGATOR_BOARD.md` · `04_tools/workspace/isze_overnight_orchestrator.ps1`
**Written:** 2026-09-17

Two ways to run the cycle every 20 minutes. They are independent and can both run.

| | Scheduled task | In-session loop |
|---|---|---|
| Runs when | Always, Cursor open or not | Only while Cursor is open and this chat is alive |
| Arming | Already registered — `ISZE_DelegatorWatch_20min`, do nothing | Type the command below |
| Good for | The overnight window, unattended | Watching it work, and getting a chat reply per cycle |

The scheduled task and the in-session loop are safe together: both are read-only and both append to
the board one line at a time. If both fire at once, one of them may skip a fingerprint comparison —
that is a missed observation, never a corrupted state.

---

## The in-session command

Type this in the Cursor chat:

```
/loop 20m Run one delegator cycle: powershell -NoProfile -ExecutionPolicy Bypass -File "C:\Users\jerom\Desktop\claude\ISZE\04_tools\workspace\isze_overnight_orchestrator.ps1" -Quiet, then read the newest file under 00_docs\agent\overnight\ and tell me any high-severity findings.
```

That wakes this session every 20 minutes, runs one cycle, and reports what the cycle found.

**Stop it** by typing `/loop stop` in the same chat, or by killing the loop's shell task.

### Why the prompt says "read the newest file"

The cycle prints very little on purpose. The evidence is written to
`00_docs/agent/overnight/`. The loop prompt points the agent at that file so each tick produces a
judgement rather than a log line.

---

## What runs each cycle

Inside **22:00–08:00 local**:

1. fingerprints the watched AIM and pricing-base set
2. checks the evidence of every workstream discovered on disk (87 of them at the last count)
3. runs **one** audit angle from the rotating queue — see the queue in
   `00_docs/agent/OVERNIGHT_ANGLE_QUEUE.json`
4. writes `00_docs/agent/overnight/audit_<stamp>_<angle>.md`
5. appends high-severity findings to `OVERNIGHT_TASKS_QUEUE.md` **for you to approve**

Outside the window it fingerprints and exits. It stays cheap on purpose.

Every cycle consumes exactly one angle. An angle is not repeated until all 16 have run.

---

## Changing the window

The window is a parameter, not a constant:

```powershell
powershell -File isze_overnight_orchestrator.ps1 -Force                        # ignore the window once
powershell -File isze_overnight_orchestrator.ps1 -WindowStart 21:00 -WindowEnd 06:00 -Quiet
powershell -File isze_overnight_orchestrator.ps1 -RunAngle locked_file_integrity
powershell -File isze_overnight_orchestrator.ps1 -Status                       # cycle and next angle
powershell -File isze_overnight_orchestrator.ps1 -ResetQueue                   # restart the queue
```

To change it for the scheduled task, edit the window defaults in the script, not the XML.

---

## Stop it

| To stop | Do this |
|---|---|
| The in-session loop | `/loop stop` in this chat |
| The overnight activity only | Set `-WindowStart` and `-WindowEnd` to the same minute, or let it pass 08:00 |
| The scheduled task | `schtasks /change /tn "ISZE_DelegatorWatch_20min" /disable` |
| Everything | `schtasks /delete /tn "ISZE_DelegatorWatch_20min" /f` and `/loop stop` |

Nothing is left half-done by stopping: the cycle is stateless between ticks. The only state is the
fingerprint file and the angle queue, both of which are safe to leave.

---

## What this cannot do — stated plainly, because it was asked for

**Agents cannot message each other.** Cursor exposes no tool for one agent to wake, command or read
another chat's context. There is no ping.

So "keep the agents working" means exactly this: **wake, check the evidence on disk, and queue
corrective work for Jerome to approve.** It does not mean commanding another agent's session, and it
cannot restart a chat that has stopped. The board is the only channel between agents — one appends,
the next reads.

If a workstream has stopped, the orchestrator reports the staleness and queues it. Starting it again
is a human action.

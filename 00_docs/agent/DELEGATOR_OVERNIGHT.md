# Overnight orchestrator — angles, limits, and what it found

**Companion to:** `DELEGATOR_BOARD.md` · `DELEGATOR_LOOP_COMMAND.md` · `DELEGATOR_REFRESH_HOWTO.md`
**Written:** 2026-09-17 · **Scripts:** `04_tools/workspace/isze_overnight_orchestrator.ps1` + `_overnight_angles.py`

---

## 1. What it is, and what it honestly cannot do

**It cannot ping another agent.** Cursor exposes no tool for one agent to wake, command or read
another chat's context. There is no message channel between agents on this machine.

So "keep the agents working" means: **wake, check the evidence every workstream left on disk, and
queue corrective work for Jerome to approve.** It does not mean commanding another agent's session,
and it cannot restart a chat that has stopped. The shared board is the only channel — one agent
appends a row, the next one reads it.

---

## 2. What each 20-minute cycle does

| Window | What happens |
|---|---|
| **22:00 – 08:00 local** | fingerprint → check every workstream's evidence → run **one** audit angle → write an audit note → queue high-severity items for approval → append a board row |
| **Outside the window** | fingerprint, compare, exit. Detect-only and cheap. |

Stops at **08:00 local** by itself. The window is a parameter (`-WindowStart` / `-WindowEnd`), not a
constant.

Every cycle consumes exactly one angle. An angle never repeats until all 16 have run.

---

## 3. The rotating angle queue

Seed order in `OVERNIGHT_ANGLE_QUEUE.json`. One per cycle.

| # | Angle | The lens |
|---|---|---|
| 1 | `workstream_scan` | Per-workstream evidence: newest artifact, does its receipt still cover it, is it stale past cadence |
| 2 | `numbers_tie_out` | Re-derive the pricing headline figures from source and compare to what was published |
| 3 | `receipt_mtime_drift` | Every receipt whose `artifact_mtime_ms` no longer covers its file |
| 4 | `language_sweep` | Banned spoken labels (Mode A/B, street, sell-out, Book B, wallet) in visible text |
| 5 | `locked_file_integrity` | Hash the locked files and report any modification |
| 6 | `html_first_paint` | `file://` risks: external asset loads, `fetch()` with no embedded payload, no launcher |
| 7 | `coverage_honesty` | AIM figures must disclose spine coverage, unpriced share, T5 share |
| 8 | `entity_separation` | UTI vs UMI never blended; IUK vs ITUK never mixed |
| 9 | `excel_formula_errors` | Cached formula errors in recently touched workbooks |
| 10 | `gaps_need_context` | Unit counts with no euro, part family or fleet denominator |
| 11 | `cross_artifact_consistency` | The same figure across artifacts must mean the same basis |
| 12 | `chart_form_quality` | Mechanical chart-form proxies: one form everywhere, fat pies, canvas missing |
| 13 | `blank_pages` | Near-blank pages in printed PDFs |
| 14 | `orphan_artifact` | Launchers pointing at nothing |
| 15 | `memory_markdown_drift` | Memory notes and anchors gone stale |
| 16 | `receipt_quality` | Receipts that assert `ok` while listing no checks |

Add an angle by writing a function in `_overnight_angles.py`, registering it in `ANGLES`, and adding
its name to `$AngleQueue` in the orchestrator.

### Two things the angles deliberately do NOT flag

Both were false positives found by smoke-testing, and both are now fixed:

- **`wallet_eur` and other pipeline field names.** The spoken-label rule explicitly permits JSON
  field names; only the spoken label is banned. The pattern uses boundaries that exclude underscores.
- **Plain `<a href="https://...">` hyperlinks.** A clickable link is allowed; only an *asset* the page
  must load to paint (`<script>`, `<link>`, `<img>`, …) is a `file://` risk.

`language_sweep` also skips `.csv`/`.txt`/`.xlsx` for the same reason, and strips `<script>`/`<style>`
before searching, so it reads visible text only. That took it from 100 seconds to under 4.

---

## 4. Findings are split into "recent" and "backlog"

Every finding records whether the artifact that produced it was written at or after this toolkit's
stamp (2026-09-17 19:00 UTC). A finding on an older artifact is **pre-existing backlog**: worth
knowing, but not tonight's regression, and it is not reported as if it were.

**Attribution is by artifact age only, and it cannot name an agent.** Two agents write in this
workspace concurrently, so "recent" does **not** mean this workstream did it. The field is named
`artifact_is_recent` for that reason — an earlier draft called it `produced_by_this_workstream`,
which claimed something the evidence cannot support, and that was corrected.

This distinction matters because the first honest run found a lot of backlog. Reporting it all as
"found tonight" would be misleading.

---

## 5. Hard limits — non-negotiable

The cycle is **read-only on all deliverables**. It may **not** rebuild, publish, sync, mail, bump a
version, or move a price.

It may write only to:

| Path | What |
|---|---|
| `00_docs/agent/DELEGATOR_STATE.json` | fingerprint state |
| `00_docs/agent/OVERNIGHT_*` | cycle state, angle queue, corrective queue |
| `00_docs/agent/overnight/` | internal audit notes and raw angle JSON |
| `04_tools/workspace/overnight_orchestrator.log` | its own log |
| `00_docs/agent/DELEGATOR_BOARD.md` | one appended row per cycle, never a rewrite |

Every fix it believes is needed is written to `OVERNIGHT_TASKS_QUEUE.md` as a **queued task for
Jerome to approve**. It is never applied.

Authority: `00_docs/RUNBOOK_ROUTINE_HANDOVER.md` §5 and `.cursor/rules/isze-no-ship-without-ok.mdc`.

### Concurrency safety

Another agent rewrote `02_dashboards/pricing/ISZE_Pricing_Revision_AIM_Source.html` at **21:46:43**
with a fresh receipt at **21:47:05**, *after* Jerome locked it at 21:38. The locked-file angle detects
exactly this class of event and logs it; it does not fix the file.

Two agents share the board, so:
- board appends are **single-line appends**, never a read-modify-write (which would drop the other
  agent's row)
- if the board is briefly locked by another writer, the append is skipped and logged rather than
  retried in a loop
- a skipped fingerprint comparison is a missed observation, never a corrupted state

---

## 6. What the first runs found

Recorded as observations. **None of these were fixed** — they are queued.

| Finding | Count | Note |
|---|---|---|
| Receipts that no longer cover their file | 10+ | Including `ISZE_Exec_Aftersales_Paper.html`, `ISZE_OS_Hub.html`, `ISZE_OS_Console.html`, `Pricing_Revision_AIM_Source_Analysis.xlsx` |
| Workstreams discovered | 87 | Evidence scanned for each |
| `html_first_paint` findings | 105 | Mostly backlog across older packs |
| `language_sweep` findings | 68 | 6 on artifacts from this workstream, 62 backlog |

The most useful single result: **a shipped pack whose receipt no longer covers its file is a finding,
not a pass.** At least ten packs in this workspace are in that state right now, which means their
"done" claim is currently unsupported by their own evidence.

---

## 7. Running it by hand

```powershell
cd C:\Users\jerom\Desktop\claude\ISZE\04_tools\workspace

powershell -File isze_overnight_orchestrator.ps1 -Status            # cycle count and next angle
powershell -File isze_overnight_orchestrator.ps1 -Force             # one cycle now, ignore the window
powershell -File isze_overnight_orchestrator.ps1 -RunAngle blank_pages
powershell -File isze_overnight_orchestrator.ps1 -ResetQueue

python _overnight_angles.py --list                                  # every angle and what it checks
python _overnight_angles.py --angle language_sweep --hours 48
powershell -File _test_overnight_orchestrator.ps1                   # 26 assertions
python _test_overnight_angles.py                                    # all 16 angles execute
```

The in-session loop command is in `DELEGATOR_LOOP_COMMAND.md`.

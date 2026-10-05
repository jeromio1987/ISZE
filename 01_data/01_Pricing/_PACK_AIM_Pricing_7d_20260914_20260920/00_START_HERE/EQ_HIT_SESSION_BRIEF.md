# EQ-Hit session — 19 Sep 2026, 23:00 local

Plain English brief for tonight. **No AIM master apply** from this session.

## What this is

A one-shot lookup pass on Snap-on EQ (Isuzu EPC) for part numbers that are still
**Not on AIM** after the this-morning agree2 / agree3 apply, and that the
five-signal scorer marked as needing EQ.

Live site: https://isuzu.snaponepc.com/epc/#/

## Scope (queue)

| Bucket | PNs | Billed € (L12M) |
|--------|----:|----------------:|
| needs_eq | 523 | 126,429.23 |
| conflict_needs_eq | 217 | 113,871.34 |
| eq_last_resort | 4 | 13,919.76 |
| **Total** | **744** | **254,220.33** |

Tools / MX2 were already stripped before the 4signal score. Agree2 / agree3 rows
are already on `aim_master_v2` and are **not** in this queue.

Ranked by billed € descending. Each row carries description, HS6, figure key /
figure no / key no, weight kg, list €, price class, billed / step €, dimension
labels, five-signal status / method / notes, proposed AIM levels (where any),
and any prior EQ verdict from 18 Sep.

## Top 5 by billed €

| Rank | PN | Description | € | Status |
|-----:|----|-------------|--:|--------|
| 1 | `8979490060` | CYLINDER; SLAVE,CLU | 10,333 | conflict_needs_eq |
| 2 | `8979477650` | CYLINDER; SLAVE,CLU | 9,206 | conflict_needs_eq |
| 3 | `8975335391` | PIPE; INJ,C/R | 6,540 | conflict_needs_eq |
| 4 | `8980896771` | CYLINDER; SLAVE,CLU | 5,589 | conflict_needs_eq |
| 5 | `8973305460` | RING; FUEL INJ | 5,332 | conflict_needs_eq |

## Files

| What | Path |
|------|------|
| This brief | `C:\Users\jerom\Desktop\claude\ISZE\01_data\90_INBOX\_EQ_HIT_SESSION_20260919_BRIEF.md` |
| Queue CSV | `C:\Users\jerom\Desktop\claude\ISZE\01_data\90_INBOX\_EQ_HIT_SESSION_20260919_queue.csv` |
| Queue JSON | `C:\Users\jerom\Desktop\claude\ISZE\01_data\90_INBOX\_EQ_HIT_SESSION_20260919_queue.json` |
| Excel worklist | `C:\Users\jerom\Desktop\claude\ISZE\01_data\01_Pricing\EQ_HIT_SESSION_20260919.xlsx` |
| Open pack | `C:\Users\jerom\Desktop\claude\ISZE\01_data\90_INBOX\OPEN_EQ_HIT_SESSION_20260919.cmd` |
| 23:00 runner | `C:\Users\jerom\Desktop\claude\ISZE\01_data\91_build\run_eq_hit_session_20260919.ps1` |
| Agent wake prompt | `C:\Users\jerom\Desktop\claude\ISZE\00_docs\agent\EQ_HIT_SESSION_20260919_PROMPT.md` |
| Results (written tonight) | `C:\Users\jerom\Desktop\claude\ISZE\01_data\90_INBOX\_EQ_HIT_SESSION_20260919_RESULTS.csv` |
| Session log | `C:\Users\jerom\Desktop\claude\ISZE\01_data\90_INBOX\_EQ_HIT_SESSION_20260919_log.txt` |

## How to run (human or agent)

1. Double-click `OPEN_EQ_HIT_SESSION_20260919.cmd` **or** wait for the 23:00 scheduled task.
2. Sign in to Snap-on EQ if the browser asks (session cookie required — scrape cannot run fully unattended without a logged-in browser).
3. Work the Excel / CSV **top-down by €**.
4. Paste the console scraper from `_eq_hit_doubt_console_scraper_20260918.js` (or the overnight agent equivalent) and feed open PNs from the queue JSON.
5. Write hits to `_EQ_HIT_SESSION_20260919_RESULTS.csv` / `.json` under `90_INBOX` only.

## Do not apply until Jerome says

- Do **not** patch `aim_master_v2.csv`.
- Do **not** run `apply_not_on_aim_*` scripts from this session.
- Results stay in the inbox for review. Apply is a separate, explicit ask.

## Honest limit

EQ lookups need a **logged-in** Snap-on browser tab. The 23:00 runner will always
open the pack + EQ URL and leave an agent wake note. Full unattended scrape only
works if Jerome (or an agent with a live session) is already signed in at fire time.

Built: 2026-09-19T09:23:58+02:00

# EQ-Hit session — overnight agent prompt (2026-09-19)

**Fire time:** 23:00 local Europe/Brussels / Windows local, 2026-09-19  
**Job:** Look up residual Not-on-AIM part numbers in Snap-on EQ. Write results only.  
**Hard ban:** Do **not** patch `aim_master_v2.csv`. Do **not** run any `apply_not_on_aim_*` script.

---

## Paths

| Role | Absolute path |
|------|----------------|
| Brief | `C:\Users\jerom\Desktop\claude\ISZE\01_data\90_INBOX\_EQ_HIT_SESSION_20260919_BRIEF.md` |
| Queue CSV | `C:\Users\jerom\Desktop\claude\ISZE\01_data\90_INBOX\_EQ_HIT_SESSION_20260919_queue.csv` |
| Queue JSON | `C:\Users\jerom\Desktop\claude\ISZE\01_data\90_INBOX\_EQ_HIT_SESSION_20260919_queue.json` |
| Excel | `C:\Users\jerom\Desktop\claude\ISZE\01_data\01_Pricing\EQ_HIT_SESSION_20260919.xlsx` |
| Log | `C:\Users\jerom\Desktop\claude\ISZE\01_data\90_INBOX\_EQ_HIT_SESSION_20260919_log.txt` |
| Results CSV | `C:\Users\jerom\Desktop\claude\ISZE\01_data\90_INBOX\_EQ_HIT_SESSION_20260919_RESULTS.csv` |
| Results JSON | `C:\Users\jerom\Desktop\claude\ISZE\01_data\90_INBOX\_EQ_HIT_SESSION_20260919_RESULTS.json` |
| Console scraper | `C:\Users\jerom\Desktop\claude\ISZE\01_data\90_INBOX\_eq_hit_doubt_console_scraper_20260918.js` |
| EQ URL | https://isuzu.snaponepc.com/epc/#/ |
| Queue rebuild (safe) | `python C:\Users\jerom\Desktop\claude\ISZE\01_data\91_build\build_eq_hit_session_20260919.py` |

---

## What to do

1. Read the brief. Confirm queue size (~744 PNs, ~EUR 254k billed) by status bucket.
2. Open EQ. If login is required and you have no interactive signed-in session, **stop**, append to the log, and leave the wake note. Do not invent FIG / catalogue hits.
3. Process **top-down by billed euro** (`rank` ascending). Prefer `needs_eq` and `conflict_needs_eq`; re-check `eq_last_resort` when you reach those four rows.
4. For each PN use the useful fields already on the queue row: description, HS6, fig_key / fig_no / key_no, weight_kg, list €, price class, billed / step €, dim_* labels, status / method / notes, proposed_aim_*, prior_eq_* from 18 Sep.
5. Write one results row per PN looked up:
   - `pn`, `eq_status` (FOUND / NOT_FOUND / ERROR / SKIPPED), `eq_total`, `eq_fig_name`, `eq_part_name`, `eq_catalog`, `verdict` (CONFIRM_OK / PROPOSE_PATCH / NO_EQ_HIT / NEEDS_HUMAN), `proposed_l1`, `proposed_l2`, `proposed_l3`, `notes`, `looked_up_at`
6. Append progress lines to the session log every batch (e.g. every 10 PNs or every 15 minutes).

---

## How to scrape (when browser is logged in)

Preferred: paste `_eq_hit_doubt_console_scraper_20260918.js` into DevTools on the EQ tab, load open PNs from the queue JSON, run the batch, download hits JSON into `90_INBOX`, then merge into `_EQ_HIT_SESSION_20260919_RESULTS.*`.

If Cursor browser / CDP has an already-authenticated Snap-on tab, use that. Do not try to bypass login.

---

## Stop conditions

- Queue finished, or
- Snap-on login wall with no session, or
- Jerome says stop, or
- Repeated ERROR on controls (site layout changed) after three consecutive failures — document and stop.

---

## After results

Leave results in the inbox. Summarise for Jerome: PNs looked up, FOUND vs NOT_FOUND, top euro still open, and remind him that **apply is a separate ask**.

# Cursor brief — scraper redo, Windows-side work

**From:** Claude (orchestrator) · **Date:** 2026-09-24 · **For:** Cursor agent working with Jerome on his laptop
**Plan:** `C:\Users\jerom\Desktop\claude\ISZE\00_docs\agent\SCRAPER_REDO_DELEGATION.md`, which has the task cards and the data rules (§3, §5). Read it first.
**Board:** append one row to `C:\Users\jerom\Desktop\claude\ISZE\00_docs\agent\DELEGATOR_BOARD.md` per finished task.

## Hard rules (repeat of the plan, not optional)

- **UPDATE 2026-09-24 (chat, this session): Jerome gave the scrape go.** Phase 1 (all six platforms) is now unblocked — see task block C7 below. Live fetching may start, but every other rule on this list still applies unchanged.
- **Eucon-sourced competitor numbers may be used to drive the scrape now** (Jerome's explicit call, same turn, risk accepted ahead of legal clearing the licence terms — see `DECISIONS.md` 2026-09-24 and `00_docs/EUCON_LICENCE_BRIEF_2026-09-24.md`). **This does not change the next rule.**
- **Nothing internal goes to DeepSeek or GPT:** no price list, no billed sales, no dealer details. Queue items carry only allowlisted fields; `deepseek_batch.py` refuses anything else. **Eucon-sourced rows are additionally barred from DeepSeek specifically** (outside-EU transfer, licence terms unreviewed) — the scrape-go did not touch this boundary. Public page text and public prices you fetch from the target sites are fine for DeepSeek as before; it's the Eucon match rows (our part → competitor brand/number pairs sourced from Eucon files) that stay EU-side.
- **Never `deepseek_agent.py --yolo`.**
- **No deletes without Jerome's "yes" in chat.**
- Don't edit `refresh_and_check_drift.py`, `tender_scraper_v3.py`, bat/ps1/yaml files or scheduled tasks unless Jerome approves that specific change.
- `check_scrape_consent.py` before every new fetch, no exceptions, same as before the go. The go authorizes scraping happening, not skipping the consent/robots check.

## What Claude already built (tested in Claude's sandbox)

| File | What it does | Check result |
|---|---|---|
| `04_tools\price_ledger\build_price_ledger.py` | Builds `01_data\00_derived\price_observations.parquet` (+ `.meta.json`) | 1,081 rows, 113 Isuzu part numbers. Refuses rows missing price type or vintage. |
| `04_tools\delegation\deepseek_batch.py` | DeepSeek runner: allowlist, verbatim, placeholder and golden checks; `run_log.csv` | Offline test with fake clients: a correct client scores 10/10; a hallucinating one gets all 10 rows rejected; a queue carrying internal data is refused |
| `04_tools\delegation\make_ks_golden.py` + `tasks\ks_products_golden.json` | Splits the KS product strings exactly (by regex) and uses them as a free golden test for DeepSeek | 64 KS rows → 94 products |
| `04_tools\delegation\build_refresh_tiers.py` | Tiers from the last 12 months of billing | A 491 parts / 61.6% of billed € · B 1,809 / 28.3% · C 14,211 / 10.1% |
| `04_tools\delegation\price_list_triggers.py` | Diffs the price list against its snapshot → new, superseded and revised parts → `trigger_log.csv` + `state\trigger_queue.csv` | Baseline snapshot stored (165,366 rows). A guard refuses more than 2,000 "new" parts, because that means a changed file layout, not real new parts. |

## Tasks for Cursor, in order

### C1 — First real DeepSeek run (golden test) · no approval needed, cost is tiny (~2k input tokens)
```powershell
cd C:\Users\jerom\Desktop\claude\ISZE
python 04_tools\delegation\deepseek_batch.py ks_products_golden --dry-run
python 04_tools\delegation\deepseek_batch.py ks_products_golden --golden
```
**Accept:** golden hits ≥ 61 of 64 (95%). Report the golden score, the reject count with reasons (from `deepseek\rejects\ks_products_golden.jsonl`) and the tokens from `run_log.csv`. Below 95%: do not tune the prompt yourself. Report back, and Claude adjusts the task spec.

### C2 — Weekly ledger job (needs Jerome's yes before registering the task)
Create `04_tools\delegation\run_price_ledger_weekly.bat` to run these, in order, after the Monday 07:00 `ISZE_PMS_IAM_Refresh`:
1. `python 04_tools\delegation\build_refresh_tiers.py` (monthly is enough; weekly is harmless)
2. `python 04_tools\delegation\price_list_triggers.py`
3. `python 04_tools\price_ledger\build_price_ledger.py`

Propose a scheduled task for Monday 09:00. Register it only after Jerome confirms. Don't touch the existing `ISZE_PMS_IAM_Refresh`.

### C3 — Retire Mekonomen, Auto365, Tranzparts from the weekly run (card 0.4) · Jerome's yes needed
Prepare the minimal change in the wrapper or bat that stops calling these three, show Jerome the diff, and apply only on his yes. Evidence for each is in `04_tools\autodoc_scraper\PROPOSAL_EUCON_AND_SCRAPER_EXPAND.md` §3c.

### C4 — Healthcheck task fixes (propose, Jerome approves)
In the scheduled task `isze-scraper-healthcheck-autofix`:
- the live tender path is wrong: `01_data\dashboards\` → `01_data\14_dashboards\tender_data.json`
- add a row to the check: the count of `trigger_log.csv` rows past their serve window with an empty `served_at`
- after C3, drop Mekonomen and Auto365 from the freshness check

### C5 — Offline parser skeletons for Phase 1 (no web)
Using only saved pages (e.g. `01_data\90_INBOX\scrape_targets\_probe\v_amayama.html`), write parser functions for Amayama, Omega, geparden.no and tungen-bil.no. Each returns the ledger schema from `build_price_ledger.py` (`COLUMNS`, `price_type`, `vintage`). Each must call `04_tools\autodoc_scraper\check_scrape_consent.py` before any future fetch, and must fall back to a `deepseek_batch.py` task spec when the selector returns nothing. **Do not fetch anything.** Where a site has no saved page, write the stub plus a TODO, not a guess.

### C6 — Cleanup (only after Jerome says yes)
Two test leftovers from Claude's boundary test could not be deleted from the sandbox:
- `04_tools\delegation\deepseek\queue\_leak.jsonl`
- `04_tools\delegation\tasks\_leak.json`

## ⚠ Security finding — for Jerome, not for Cursor to fix alone

`02_dashboards\Data\90_INBOX\eucon_mail_extracts\NOTE_Eucon.txt` holds a **Eucon login in plain text**. It is gitignored and not tracked, so it isn't on GitHub. But any agent that reads that folder can read it, including DeepSeek via `deepseek_agent.py`. Recommended: Jerome changes the Eucon password, then the file is deleted (on his yes). Never print or copy the value.

### C7 — Build and run all six Phase 1 platforms in parallel (scrape go given 2026-09-24) · no further approval needed for fetching itself, per Jerome's chat go

Site list, worker, and where each stands today:

| Site | Status today | What's needed |
|---|---|---|
| Amayama | Parser written, proven against a saved page | Run `check_scrape_consent.py`, then go live |
| Omega | Stub only — throws rather than returns empty | Write real parser first |
| geparden.no | Stub only | Write real parser first |
| mekster.no | Stub only | Write real parser first |
| tungen-bil.no | Not started | Parser + tag `price_type = dealer` (it's the Isuzu dealer price list, not aftermarket) |
| autoline.dk | Not started | Parser + tag `price_type = marketplace` |

Rules for this batch, all carried over from §5 of the plan and non-negotiable:
1. `check_scrape_consent.py` exit 0 before any fetch, per site, every run.
2. ≥ 2 s spacing per request per site (§8 of the plan). No bypassing Cloudflare or login walls.
3. Selector-first; DeepSeek flash (prompt 6.1) only on parser failure, per the self-healing pattern in §2. Public page text only into DeepSeek — never the Eucon match rows.
4. §5 acceptance: verbatim check, schema check, placeholder check, plausibility check on every row; then Claude samples 5% (min 20) before anything is trusted.
5. Seed the runs from `04_tools/aftermarket_intelligence/state/reachable_pairs.csv` (the 2,812 competitor brand+number objects, Eucon-sourced included per the 2026-09-24 go) and `seed_reach_tierA.csv` for what to prioritise — Tier A first.
6. Each site's first run is small (≤ 50 items) and reported before scaling, same discipline as the KS golden test (C1) — do not run all six at full volume on the first pass.
7. One row per finished site on `DELEGATOR_BOARD.md`; a `CURSOR_REPORT_20260924.md` update if anything needs Claude's judgement (a site blocks with a bot check, a parser can't get selectors, price/currency ambiguity).

## Report back

One line per task on `DELEGATOR_BOARD.md`. Anything that needs Claude's judgement goes in `C:\Users\jerom\Desktop\claude\ISZE\04_tools\delegation\CURSOR_REPORT_<date>.md`.

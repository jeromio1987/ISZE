# Cursor report — scraper redo, Phase 0 · 2026-09-24

**Agent:** Cursor (this laptop) · **Brief:** `00_docs\agent\CURSOR_BRIEF_SCRAPER_REDO_20260924.md`

## C1 — DeepSeek golden (`ks_products_golden`) · PASS

| Run | Result |
|---|---|
| 08:25 `--golden` | FAIL before scoring — 64/64 rejected, API 401 (dead key) |
| 08:31 `--golden` | FAIL before scoring — same dead key, `.env` had not actually been saved |
| **11:36 `--golden`** | **PASS — accepted 63, rejected 1, golden 63/63, tokens 15,171 in + 28,506 out, ~3 min** |

**Acceptance bar (brief):** golden hits ≥ 61 of 64 (95%) → **met, 100% of comparable rows**.
No prompt change was made. `temperature 0.0`, model `deepseek-v4-flash`.

**The one rejection is not a correctness fault:**
`item_id ks_8970622940` — the model spent its whole `max_tokens` (1,500) on internal reasoning and
returned no answer. Mechanical check never ran. Documented failure mode in `deepseek_readme.md`.

**Proposed fix (Claude's call — task specs are Claude's to change):** raise `max_tokens` in
`04_tools\delegation\tasks\ks_products_golden.json` from 1,500 to 3,000. Not applied.

**Key history:** the old key ending `45e3` was deleted on the DeepSeek site — it is not in the
account's key list. Jerome created a new key; `.env` saved 2026-09-24 11:35:26.

## C3 — Mekonomen, Auto365, Tranzparts retired · DONE (Jerome's go, this session)

### 1. Stopped the weekly run from calling them

`04_tools\autodoc_scraper\refresh_and_check_drift.py`, `JOBS` list: their three entries removed,
so the scheduled refresh no longer calls them. Only the *calling* stopped — the three scrapers, their
CSVs and their snapshots stay on disk, re-pluggable by re-adding one line each. A comment above
`JOBS` records the reason per source.

### 2. Removed the false prices from the table, at the source

Jerome asked for the seven false part numbers to be dropped **and** the views rebuilt. Dropping them
from the CSV alone would have been undone by the next rebuild, so the block is in the two builders
that read the source:

| File | Change |
|---|---|
| `04_tools\db_operating_dashboard\build_iam_street_joins.py` | New `MEKONOMEN_RETIRED = True` + `MEKONOMEN_FALSE_PNS` (the seven). `load_mekonomen_am()` returns an empty frame while retired, and excludes those seven by part number even if the source is switched back on. |
| `02_dashboards\spa_internal\_build\build_umi_spa_proposed_prices.py` | Same guard; the file is no longer read while retired (it is empty now, and reading it crashed the builder — fixed). Also removed the Mekonomen tier claims from the page and replaced the Auto 365 section with an honest "Retired sources" table. |

**Rebuild results:**
- `01_data\00_derived\iam_mekonomen_price_gap.csv` — **67 rows → empty file (2 bytes)**. No Mekonomen row survives, so no Mekonomen price can be read from it by anything.
- `01_data\00_derived\iam_ks_price_gap.csv` — rebuilt, unaffected: 359 rows, KS coverage unchanged.
- `02_dashboards\spa_internal\UMI_SPA_Proposed_Prices.html` — rebuilt. `n_mek: 0`, UMI scored set
  **8 part numbers (KS only)**, was 12. The four PNs that existed *only* because of a Mekonomen row
  are gone from the pack. One SPA candidate survives on KS evidence.
- No Mekonomen price remains on the page. The only mentions are in the new "Retired sources" table,
  which states plainly what was wrong.

### What the Mekonomen file actually contained — all seven rows were false

Verified 2026-09-24 against the scraper's own diagnostic dump
(`04_tools\autodoc_scraper\_diag\MEK_8975056801.txt`).

| PN | Description we searched | What Mekonomen returned | Price | Brand |
|---|---|---|---|---|
| 8975056801 | PAD KIT; CALIPER,DISC BRK,FRT | **Spiralfjäder** (coil spring) | 957 SEK | Kilen |
| 8983373180 | SENSOR ASM; DEF TANK | unrelated | 259 SEK | NB Parts |
| 8982932120 | DRIVE ASM; FINAL,RR | unrelated | 259 SEK | NB Parts |
| 8982924321 | SENSOR; SPD,FRT WHEEL | unrelated | 1,929 SEK | NB Parts |
| 8983937793 | SUPPORT; RR BUMPER | unrelated | 113 SEK | Raufoss |
| 8983288004 | LAMP ASM; RR COMB | unrelated | 106 SEK | Raufoss |
| 8982606011 | DOOR ASM; FRT,WO/TRIM | unrelated | 269 SEK | NB Parts |

**Signature of the failure:** every PN returns exactly **one** result, on every snapshot from
2026-07-09 to 2026-09-22, byte-stable. A shop carrying Isuzu would return zero for most of these
numbers, not exactly one each. Mekonomen's search echoes the query and serves an unrelated in-stock
item; the scraper reads the first price on the page and records it against our part.
**False positives, not misses.** The seven "hits" the health report counted as evidence the source
works were the defect itself.

**Scale of what was mis-priced:** the seven PNs carried **€582,085** of UMI CY2025 billed revenue
(largest: the brake pad kit, €308,819, priced against a €85 coil spring). Because the false price is
low, the effect was to make our position read as undercut by far more than it is.

### Still open on this — needs Jerome's word

Three artefacts still quote the old numbers and were **not** touched:
1. `02_dashboards\pricing\ISZE_Pricing_Action_Map.html` — built 16 Jul from the same source, carries
   a "Mekonomen" price-evidence block and the line "Sweden: 5 of 6 aftermarket price hits were page
   artifacts". Its builder (`build_pricing_action_map.py`) still reads `mekonomen_results.csv`, so a
   rebuild re-imports the seven false prices.
2. `09_meetings\UMI_Operating_Dashboard_2026\DATA_INTEGRITY.md` — "Mekonomen SE | 4 PNs | 1.06%".
3. `04_tools\autodoc_scraper\competitive_bi.py` — lists Mekonomen as a live BI source.
   There is also a **healthcheck scheduled task** (`isze-scraper-healthcheck-autofix`) that still
   expects Mekonomen, Auto365 and Tranzparts to be fresh and will start reporting them stale.

## Auto365 / UMI ownership — what I could and could not establish

Jerome asked me to check it myself. What I have:

| Evidence | Reading |
|---|---|
| `01_data\90_INBOX\scrape_targets\israel.md` (18 Sep) | States "contact email is `auto365@umi.co.il`" — **the only place in the workspace with this claim** |
| `04_tools\autodoc_scraper\PROPOSAL_EUCON_AND_SCRAPER_EXPAND.md` | Repeats it, citing the above |
| `AUTO365_PN_JOIN.md` (14 Aug) | Says nothing about UMI |
| DNS, checked 2026-09-24 | auto365.co.il and umi.co.il **share Cloudflare nameservers** (`melinda`/`miles.ns.cloudflare.com`); mail differs: auto365 → `*.mail.protection.outlook.com`, umi → `mailmx.avis.co.il` |

**Honest verdict:** *likely UMI-owned, not proven.* Shared nameservers is weak evidence — those two
Cloudflare hosts serve a large share of the internet. Different mail providers is mildly against the
claim. The real evidence is the quoted contact address, which now exists only as a citation of a
September research pass; re-checking it needs a look at the live site, which needs a scrape go.
**Jerome's decision (this session): check it at the next scrape go.**

**Why it matters less than it looks:** Auto365 is retired either way — it exposes no Isuzu part
number, so it can never answer a PN price question. Ownership only matters if it is ever used as a
*competitor* reference.

## C2 — weekly price-ledger job · DONE, tested end to end

**Built:** `04_tools\delegation\run_price_ledger_weekly.bat` — four steps, each logged:
1. `build_refresh_tiers.py` (rank by billed value)
2. `price_list_triggers.py` (diff the price list vs its snapshot)
3. `build_price_ledger.py` (rebuild the price-observation table)
4. `price_parsers.py --selftest` (see C5 below)

Order matters and is stated in the file: it must run **after** the Monday 07:00
`ISZE_PMS_IAM_Refresh` (`04_tools\autodoc_scraper\run_refresh_scheduled.bat`) so it reads that
run's fresh scraper output rather than last week's. Log: `04_tools\delegation\_logs\ledger_<date>.log`.
Exit 2 if any step fails, so a scheduled run goes red rather than green. The existing
`ISZE_PMS_IAM_Refresh` task was **not** touched.

**Test run (2026-09-24, exit 0):** tiers A 491 parts / 61.6% of billed €, B 1,809 / 28.3%,
C 14,211 / 10.1%; price-list diff "triggers none" (list unchanged vs snapshot, expected);
ledger 1,081 rows / 113 part numbers; parser selftest PASS.

**One thing the test caught:** the ledger writes its own `.meta.json`, so my hand-edit to its
"not loaded" note was overwritten on the first run. Fixed at the source in `build_price_ledger.py`
rather than in the JSON, so it survives every future run.

## C5 — offline parsers · DONE for the one site that has a page, stubs elsewhere

**Built:** `04_tools\delegation\parsers\price_parsers.py`. No network call in the package.

| Site | Status | Evidence |
|---|---|---|
| **Amayama** | **Working parser**, proven | Parsed against the real saved page `_probe\v_amayama.html` (97,737 bytes). Returns `8974995480` at **54.25 USD**, `price_type = genuine_grey`, from the JSON-LD `Product` block, plus the per-warehouse rows (Japan / Latvia EU ex-UAE). Selftest asserts the part number, the price, the price type, and that every part number is 10 digits — a parser that returns nothing **fails loudly** instead of looking empty-but-fine. |
| **Omega** | Stub + TODO | No product page on disk. The research pass did fetch one and recorded the fields (internal code `0011765K`, OEM `8970622940`, £40.80, and a `Dealer Price: 66.86` comparison line). **Domain corrected to `omegaspareparts.com`** — the earlier `.co.uk` form does not resolve. Reach by HTML search; robots disallows `/wp-json/`. |
| **geparden.no** | Stub + TODO | No page on disk. Pattern known (SKU *is* the OEM number, `ISU` + 10 digits). `/search` is disallowed, so sitemap route only. |
| **tungen-bil.no** | Stub + TODO | No page on disk. Pattern known (table: Varenummer / Beskrivelse / Antall / Pris ex. mva, order by form). Tag `price_type = dealer`. |

**Why stubs raise instead of returning `[]`:** an empty list is indistinguishable from "the site had
no price for this part", which is exactly the kind of quiet failure that let the Mekonomen problem
sit in a dashboard for six weeks. A stub now throws.

**Consent gate extended** (`check_scrape_consent.py`): the new targets are listed, so no future
fetch can open a connection without the gate being asked first. Running it also independently
confirmed the retirement decision — **auto365.co.il and mekonomen.se are reported BLOCKED by the
gate itself**, which is the third independent line of evidence for retiring them.

## Verified / not verified

- Verified myself: the Mekonomen page content (diagnostic dump, full text read); the seven-row
  behaviour across 13 snapshots; the revenue figures; both rebuilds' output; the HTML for leftover
  Mekonomen claims; the Amayama parser against the real file; the weekly bat end to end (exit 0).
- Not verified: the Auto365 ownership claim (labelled as such above); Omega/geparden/tungen selectors
  (**deliberately not written** — no page to write them against).
- Not done: C4 (healthcheck task changes — the task is not on this machine); C6 (deleting the two
  `_leak` test leftovers still waits for Jerome).

## Blocked on Jerome

1. **C4** — the healthcheck task the brief names (`isze-scraper-healthcheck-autofix`) is not in this
   machine's scheduled tasks. Either it lives elsewhere or it was never registered. Not touched.
2. **Omega / geparden / tungen parsers** — need a saved page each. That needs a scrape go, or Jerome
   (or Claude) saving the page manually.
3. **Security note** — Eucon login in plain text under a Data inbox folder. Not opened by Cursor.

## Done after the two approvals (2026-09-24, later)

- **Task registered:** `ISZE_PriceLedger_Weekly` → `04_tools\delegation\run_price_ledger_weekly.bat`,
  weekly on **Monday 09:00**, runs as `jerom`, state Ready, next run 28 Sep 2026 09:00. It runs two
  hours after the existing Monday 07:00 `ISZE_PMS_IAM_Refresh`, which is the order the file requires.
  The existing task was not touched.
- **C6 done:** `deepseek\queue\_leak.jsonl` and `tasks\_leak.json` deleted (both confirmed gone).

### What the Mekonomen file actually contained — all seven rows are false

Verified 2026-09-24 against the scraper's own diagnostic dump
(`04_tools\autodoc_scraper\_diag\MEK_8975056801.txt`).

| PN | Description we searched | What Mekonomen returned | Price | Brand |
|---|---|---|---|---|
| 8975056801 | PAD KIT; CALIPER,DISC BRK,FRT | **Spiralfjäder** (coil spring) | 957 SEK | Kilen |
| 8983373180 | SENSOR ASM; DEF TANK | (rør/nippel-shaped price group) | 259 SEK | NB Parts |
| 8982932120 | DRIVE ASM; FINAL,RR | unrelated | 259 SEK | NB Parts |
| 8982924321 | SENSOR; SPD,FRT WHEEL | unrelated | 1,929 SEK | NB Parts |
| 8983937793 | SUPPORT; RR BUMPER | unrelated | 113 SEK | Raufoss |
| 8983288004 | LAMP ASM; RR COMB | unrelated | 106 SEK | Raufoss |
| 8982606011 | DOOR ASM; FRT,WO/TRIM | unrelated | 269 SEK | NB Parts |

**Signature of the failure:** every PN returns exactly **one** result, on every snapshot from
2026-07-09 to 2026-09-22, byte-stable. A shop that carried Isuzu would return zero for most of
these numbers, not exactly one each. Mekonomen's search echoes the query and serves an unrelated
in-stock item; the scraper reads the first price on the page and records it against our part.
**These are false positives, not misses.** The seven "hits" that the health report counted as
evidence the source works are the defect itself.

### Where the false prices went

| Consumer | File / artefact |
|---|---|
| Ledger | `01_data\price_ledger\build_price_ledger.py` (Mekonomen is **not** loaded — good) |
| Operating table | `01_data\00_derived\iam_mekonomen_price_gap.csv` — **67 rows, 7 distinct PNs, across 18 markets** |
| UMI SPA pack | `02_dashboards\spa_internal\_build\build_umi_spa_proposed_prices.py` reads it for UMI and prints "Mekonomen SE — 4 PNs · 1.06%" |
| Position engine | `04_tools\autodoc_scraper\position_engine.py` (`load_mek`) — feeds the aftermarket table and `ISZE_Pricing_Action_Map` |
| UMI operating dashboard | `09_meetings\UMI_Operating_Dashboard_2026\DATA_INTEGRITY.md` § "Live scrapers" |

**Scale of what was mis-priced:** the 7 false PNs carry **€582,085** of UMI CY2025 billed revenue
(`Rev_CY2025_EUR`). The largest single one is the brake pad kit at **€308,819**, which the pack
priced against a €85 coil spring. Because the false price is low, the effect is to make our position
look worse than it is — those lines would read as undercut by far more than they are.

**The pack already knew the rows were dirty.** `position_engine.py` and the SPA builder both carry a
`mek_suspect()` check and a note that "suspect Mekonomen titles … stay review, not auto-cut". The
flag was a label, not a block: the rows were still scored and still counted in coverage.

**Not done — needs Jerome's word (this touches a dashboard he opens):**
1. Remove the 7 false PNs from `iam_mekonomen_price_gap.csv` (or retire the whole file).
2. Rebuild the UMI SPA pack and the aftermarket/position views without the Mekonomen source.
3. Correct the "Mekonomen SE 4 PNs" coverage claim in `DATA_INTEGRITY.md`.
   Cursor has not touched any of these.

## Auto365 / UMI ownership — what I could and could not establish

Jerome asked me to check it myself. What I have:

| Evidence | Reading |
|---|---|
| `01_data\90_INBOX\scrape_targets\israel.md` (18 Sep) | States "contact email is `auto365@umi.co.il`" — **the only place in the workspace with this claim** |
| `04_tools\autodoc_scraper\PROPOSAL_EUCON_AND_SCRAPER_EXPAND.md` | Repeats it, citing the above |
| `AUTO365_PN_JOIN.md` (14 Aug) | Says nothing about UMI |
| DNS, checked today | auto365.co.il and umi.co.il **share Cloudflare nameservers** (`melinda`/`miles.ns.cloudflare.com`); mail: auto365 → `*.mail.protection.outlook.com`, umi → `mailmx.avis.co.il` |

**Honest verdict:** *likely UMI-owned, not proven.* Shared nameservers is weak evidence — those two
Cloudflare hosts serve a large share of the internet. The real evidence is the quoted contact
address, and it now exists only as a citation of a September research pass; re-checking it means
looking at the live site, which needs a scrape go. The two domains do use different mail providers,
which is mildly against the claim.

**Why it matters less than it looks:** Auto365 is retired either way — it exposes no Isuzu part
number, so it cannot answer a PN price question. The ownership question only matters if it is ever
used as a *competitor* reference; if UMI owns it, its prices are the importer's own retail and using
them as a competitor price would be a category error.

## Blocked on Jerome

1. Whether to clean the 7 false PNs out of `iam_mekonomen_price_gap.csv` and rebuild the two packs that read it.
2. **C2** — weekly ledger bat + Monday 09:00 task: approved this session, not started.
3. **C5** — offline parsers (Amayama, Omega, geparden.no, tungen-bil.no): approved this session, not started.
4. **C6** — delete `deepseek\queue\_leak.jsonl` and `tasks\_leak.json`. Not started.
5. **Security note** — Eucon login in plain text under a Data inbox folder. Not opened by Cursor.

## Not done

C2, C4, C5, C6; the Mekonomen clean-up above.

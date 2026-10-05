# Eucon data inventory

24 September 2026 · internal · read-only pass: no Eucon file opened for editing, moved or deleted · `NOTE_Eucon.txt` not opened
Full list, one row per file: `00_docs\EUCON_DATA_INVENTORY_2026-09-24.csv` (997 files). Rebuild: `01_data\91_build\_eucon_inventory_20260924.py`.

**Verdict.** Eucon data is not in a few files. It is in 997, and 663 of them also sit on GitHub. The repo is private, but three things stand out. The Eucon password note is still on GitHub. So are the raw PartsPool cross-reference, the 2021 benchmark report and 60 Eucon mail files. And Eucon competitor prices are built into 18 per-distributor dashboards and two ITUK packs. PartsPool is Eucon's online parts-price service. ITUK is our UK truck distributor. A same-day delete can be done on this machine. It cannot be done on GitHub the same day without rewriting the repo history.

## Counts by kind

| Kind | Files | What it is |
|---|---:|---|
| original | 45 | Eucon deliveries: 2024 and 2025 exports, 29 Mar 2026 PartsPool batch output, 2023 survey raw data, the 2021 report, and 34 files in the 2021 project folder on company OneDrive |
| mail | 119 | mail extracts, attachments and mail-scan JSON: 60 in the main checkout, and most of them again in the Cursor worktree |
| derived | 90 | tables built from Eucon rows: match index, cross-reference graph, price gaps, price ledger, ratio model, peer-number map |
| dashboard | 163 | HTML and JSON pages that carry or quote Eucon figures |
| export | 61 | decks, workbooks, zips and GPT (ChatGPT) review packs |
| backup | 257 | `.bak` files, archives, the two git worktrees, the July clone and the pre-change safety copies |
| doc | 174 | notes that mention Eucon. Some quote single Eucon figures. They were not checked line by line |
| builder | 88 | scripts that read Eucon files or their outputs. They hold no Eucon rows, but they would rebuild the data if run |

## Places from which the data could leave, or already has left, this machine

1. **GitHub (private repo `jeromio1987/ISZE`).** 663 files have a copy there. Among them, 150 files are no longer tracked here but are still in the `origin/main` tree. This includes `NOTE_Eucon.txt` (added 19 Aug 2026 in commit 91156f63; removed only on this branch on 20 Sep in 96724527, which is not in `main`). It also includes `eucon_crossref_iam_20260329.csv`, all four copies of the 2021 benchmark PDF and the `eucon_mail_extracts` folder. The match index, cross-reference graph, ratio model and seed files were committed today (4ccae53d) and pushed to `origin/cursor/isze-exec-sales-paper-prompt-8dc1`. Commit 91156f63 sits in 13 of the 19 remote branches, and the repo has 11 pull requests. *The state note of today says the password file is "untracked, not on GitHub". That is not true for `origin/main`.*
2. **Company OneDrive:** `C:\Users\jerom\OneDrive - Isuzu Motors Europe NV\pricing\Eucon\` (33 files) plus `pricing summary Eucon.xlsx`. These are 2021 PartsPool exports and comparisons, and they are synced to the Microsoft cloud.
3. **Per-distributor operating dashboards:** 18 in `09_meetings\*_Operating_Dashboard_2026\`, each an HTML page plus a `NUMBERS_LEDGER.json`. They carry Eucon prices, brands and part numbers per part. Whether any were sent to a distributor is not established.
4. **ITUK packs:** `ITUK_PMS_Aftermarket_Compare_DRAFT.xlsx` and `ISZE_PMS_Aftermarket_vs_List.xlsx`, two copies each (ISZE root and `09_meetings`). Their `Brand_prices` sheet holds Eucon UK 2023 survey prices. They were built by scripts in `09_meetings\Preparation Meetings\IML_ITUK_PMS\mp\SHARE\` for the ITUK contact. Whether they were sent is not established.
5. **AI and GPT folders:** `08_gpt\` (19 files; the last upload on record was 12 May 2026), `90_archive\02_dashboards_gpt_review_2026-09-19\` (moved there 2026-10-05) (31), `01_data\90_INBOX\PPT_GPT_commercial_pack_2026-09-19\` and `01_data\15_gpt_safe\`. Which files reached ChatGPT Enterprise, or any other outside service, is not recorded per file.
6. **Deploy mirrors:** `07_deploy\publish-site\` (27) and `07_deploy\Master Dashboard\` (32; own local git, no remote). The README says there is no approved public host. It also refers to "the earlier public drop".
7. **Other copies:** `ISZE_worktree_pr10\` (82), Cursor worktree `C:\Users\jerom\.cursor\worktrees\default\9ofw\` (80, including a second `NOTE_Eucon.txt`), an older clone at `C:\Users\jerom\ISZE\` (4), and `C:\Users\jerom\Downloads\eucon_pricing*.xlsx` (3, including the raw 29 Mar 2026 download).

## What a same-day delete or return would touch

- **Originals, 45 files.** `01_data\Eucon_March.xlsx`, `01_data\Eucon_Online28072025.xlsx`, `01_data\01_Pricing\_raw\eucon_pricing_partspool_20260329.xlsx`, the three `Eucon_PriceSurvey_*2023*.xlsx`, `02_dashboards\Data\01_Pricing\_raw\eucon_crossref_iam_20260329.csv`, the 2021 report PDF (4 copies of the same file), the OneDrive folder and the Downloads files. For a *return*, these are the files to send back or to certify as destroyed.
- **Mail, 119 files.** `02_dashboards\Data\90_INBOX\eucon_mail_extracts\`, `eucon_mail_attachments\`, `_eucon_*.json`. The mails themselves also remain in Outlook, which this pass did not inventory.
- **Derived, dashboards and exports.** See the switch-off rules below, then rebuild or retire the readers: the 18 operating dashboards, the five IAM quality positioning pages, the IAM price vs billed page, the pricing action map, the exec aftersales paper, the pricing policy paper and decks v1.1/v1.2/v1.4, the UMI SPA proposed prices page (UMI is a distributor; SPA a special price agreement), the part-groups explorer and its offline zip, and the PRISM Evidence app cache (PRISM is our internal analytics app). IAM means the independent aftermarket, the non-carmaker parts brands.
- **Backups and copies, 257 files.** Everything under the two worktrees, the July clone, `_backsafe_*`, `_archive`, `91_legacy`, `90_archive`, `*.bak*` and `_HANDOFF_BUNDLE`.
- **GitHub.** Deleting the files and pushing is not enough, because every earlier commit keeps them. A full purge needs a history rewrite of all 19 remote branches (for example with `git filter-repo`), a force-push, GitHub support to clear cached views and pull-request refs, and re-cloning every local copy. The password in `NOTE_Eucon.txt` should be treated as exposed to anyone with repo access since that commit was pushed (commit dated 19 Aug), whatever legal decides.

## What "switch off the Eucon rows" means per derived file

| File (`04_tools\aftermarket_intelligence\state\` unless stated) | Eucon rows | Switch-off |
|---|---|---|
| `match_index.csv` | 7,157 of 7,701 | Keep rows whose `source` is `Isuzu genuine to BVP catalogue` (544). Drop every `source` starting `Eucon`, and `Peer carrier number (Eucon OEM survey)`, because that map also comes from an Eucon survey |
| `crossref_edges.csv` / `.parquet` | 6,899 of 7,443 | Rebuild from the filtered index. Equivalent to dropping `source_family` EUCON, UK_WORKSHOP_SURVEY and PEER_CARRIER |
| `evidence_seed.csv`, `check_eucon_dropped_matches.csv`, `check_brand_alias_candidates.csv`, `ratio_backtest.csv`, `ratio_model.csv` | all rows | Delete. Nothing is left without Eucon. The ratio model is only aggregates, but it was fitted solely on Eucon prices |
| `seed_reach_tierA.csv`, `reachable_pairs.csv` | grades / 3,041 of 3,397 pairs | Rebuild from the filtered index. Without Eucon, the reach grades collapse to our own BVP line |
| `01_data\00_derived\price_observations.parquet` | 889 of 1,081 | Drop loaders `eucon_crossref` and `eucon_survey_2023` |
| `eucon_price_gap.csv` (+ PRISM copy, street QA copy, Evidence cache), `eucon_uk_survey_2023_price_gap.csv`, `eucon_comparable_oem_gap_20260810.csv` | whole file | Delete. Then check how at least 15 readers behave when the file is missing. This was not tested |
| `03_analytics\isze_pricing\oem_peer_basket.csv` (+ 2 `.bak`, raw seed mirror) and `runs\*\alloc_detail.csv` | rows marked Eucon | Filter the basket on its source column. Delete the old run folders |
| `db_aftersales_risk.csv`, `margin_opportunity_top200.csv` | aggregate / flag | Diluted to distributor totals or a yes/no flag, with no part-level Eucon value. Recompute once the price-gap file is gone |
| `04_tools\delegation\drafts\partspool_basket_tierA.csv` | 0 | Our own part numbers prepared as a PartsPool search list. No Eucon rows, so no action |

## What I could not establish

- Whether anything was sent: the ITUK packs, the 18 operating dashboards, the decks, the "earlier public drop" of `publish-site`, or GPT uploads after 12 May.
- Whether pages, decks and notes with fewer than 20 mentions hold Eucon values or only the word. The counts are mechanical, and a page with many mentions is marked "embeds".
- The content of the OneDrive files (not opened) and of the July clone beyond file names. Whether the sales-named OneDrive files hold Eucon data.
- Compressed parquet, PDF and image contents are only partly searchable, and a false hit on "Streucontainer" was removed. Lineage was traced two steps from each builder. Files that hold only totals are stated as such, not chased further.
- Outlook, SharePoint/Teams, the work laptop and Eucon's own portal were out of reach.
- Whether the GitHub copy of `NOTE_Eucon.txt` matches the local one (not compared, so as not to read it).

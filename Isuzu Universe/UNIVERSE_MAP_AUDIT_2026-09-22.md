# Isuzu Universe — what is on disk, who made it, and where the map is wrong

**Audit date:** 22 September 2026
**Scope:** `C:\Users\jerom\Desktop\claude\ISZE\Isuzu Universe\` — 16 folders, 57 files at the root, 12,395 files in total, 1,075,886,628 bytes (about 1.03 GB).
**Nature:** read-only inspection. Nothing was moved, renamed, edited or committed. This report is the only file created.
**Restricted material:** this report names no pilot account, no part number and no supplier purchase cost. Where a restricted thing has to be referred to, it is described or its field name is given, never its value.

Everything below is measured from the filesystem or read from a file whose path is named. Where a document makes a claim I did not check myself, it is marked **claimed, not verified**.

---

## 1. The map as it actually is

### 1a. What the project says it is

Two documents claim to be the entry point. `INDEX.md` at the root calls itself "the working map for the Isuzu Universe project. Everything has a place." `_MERGED_MASTER_2026-09-21\00_THE_MAP.md` calls itself "the whole map" and says it is a consolidation only: "It is not new analysis. Nothing in this folder was measured here. Every figure is carried from a source that is named at the foot of the file it appears in."

The merged map says the folder holds "20 files", grouped by topic, merged out of "a vertical evidence audit, a design specification, seven workstream reviews, a reconciliation, an adversarial verification, two orchestration returns, two strategy proposals, four atlas documents and two Cursor packages." It defines what is current (the `CONSOLIDATED_ITUK_2026-09-21_01` return) and what is superseded, lists eleven closed decisions, seven open questions, and states plainly that two named documents "exist in the source conversation and no local copy was available when this review was built". I confirmed that is still true: a recursive filename search of the whole folder finds neither `UNIVERSE_VALUE_EXCHANGE_MODEL_REVISED_2026-09-21.md` nor `UNIVERSE_FEEDBACK_DISPOSITION_2026-09-21.md`.

So the project's own picture is: a large evidence exercise about the UK distributor's parts business, consolidated into one 20-file map, with the underlying workings kept in a separate evidence folder and a set of strategy papers above it.

### 1b. The folders

Measured. "Newest" is the most recent modification time of any file anywhere beneath that folder.

| Folder | Files | Bytes | Newest | What it holds |
|---|---:|---:|---|---|
| `06_Working` | 2,123 | 410,733,022 | 2026-09-22 15:22 | Working material. Dominated by a large delivery-roadmap scratch tree (1,853 files), the extracted UK purchasing pack, the v03 pricing application, and the review handoff written for v03. |
| `05_AIM_Universe` | 8,880 | 365,780,785 | 2026-09-22 19:26 | The corrected v04 pricing component: 21 source modules, the restricted data file and the frozen v03 reference, 345 test files, 11 build/audit tools, 15 documents, and 8,471 browser-check screenshots. |
| `_STRATEGY` | 1,013 | 229,040,473 | 2026-09-21 19:14 | The evidence behind the map. Under `_ORCHESTRATION`: R0 and R1 returns, the UK audit, the consolidated return, the superseded earlier draft, the Cordwallis case, and the pilot copy. |
| `02_Atlas` | 11 | 13,618,210 | 2026-09-21 19:13 | Network and parts atlases (two large HTML files), the IDS data inventory, platform and access plan, concept note, and two shortcuts pointing into other ISZE folders. |
| `03_Packages` | 82 | 9,323,430 | 2026-09-21 19:13 | Two Cursor work packages, R0 and R1, plus their zip drops and the handoff folder. |
| `04_IDS_AIM_and_IMOTORS` | 18 | 6,051,297 | 2026-09-21 19:14 | The IDS-to-AIM bridge, the IMOTORS pack, the data request, and a real-data HTML page for the UK distributor. |
| `01_Strategy` | 15 | 3,692,028 | 2026-09-22 06:21 | Strategy papers, the critique of them, the commercial and value-exchange drafts, the yellow-paper drafts, the master prompts, and the pilot evidence pack. |
| `Universe_IDS_AIM_Cursor_Handoff` | 25 | 3,475,258 | 2026-09-21 13:53 | An unpacked handoff pack for Cursor; a zip twin sits at the root. |
| `_qa_pdf` | 23 | 3,163,896 | 2026-09-22 06:45 | Page images from the yellow-paper PDF check. |
| `GPT_HANDOVER_2026-09-22` | 98 | 2,440,601 | 2026-09-22 19:30 | A copy-pack of the v04 component plus the two notes written to explain it. Audience is the other chat tool; producer is the Cursor side (see §2). |
| `_qa_page` | 12 | 1,775,903 | 2026-09-22 06:29 | Screenshots of the opportunity page. |
| `_qa_yellow` | 7 | 1,296,313 | 2026-09-21 21:07 | Earlier yellow-paper QA images. |
| `_MERGED_MASTER_2026-09-21` | 22 | 721,984 | 2026-09-22 06:40 | The project's own map: the 20 documents (numbered 00–19), a two-line `README.md`, and one scratch text file. |
| `_qa_logo` | 3 | 152,410 | 2026-09-22 19:12 | Logo checks for the business-performance-review deck. |
| `_build_v05` | 5 | 98,988 | 2026-09-22 06:44 | The v0.5 yellow-paper build script, the coverage check, two verified page-data files, and the rendered intermediate HTML. |
| `_assets` | 1 | 7,444 | 2026-09-22 19:09 | One white Isuzu logo PNG. |

The three largest items by size, in order: `06_Working` at 410,733,022 bytes; `05_AIM_Universe` at 365,780,785 bytes; `_STRATEGY` at 229,040,473 bytes. Those three alone are 1,005,554,280 bytes, about 93% of the total.

`05_AIM_Universe` is 8,880 files but only 365 MB, because 8,471 of those files are screenshots under its own `_qa` folder. Its actual source, documents, tests and build tools are 400 files and about 3.9 MB.

### 1c. The root files

57 files at the root, 24,514,586 bytes total. The newest five:

| File | Bytes | Written | What it is |
|---|---:|---|---|
| `AIM_OPPORTUNITY_REVIEW_SOURCE_2026-09-22.zip` | 1,236,251 | 22/09 21:24:37 | Source pack for the opportunity review page. |
| `AIM_Opportunity_Review_v0.1.html` | 105,243 | 22/09 21:24:36 | A self-contained opportunity review screen, five selected purchasing cases, two pilot distributors. |
| `Universe_Yellow_Paper_v0.5_2026-09-22.pdf` | 282,128 | 22/09 21:24:29 | The paper `INDEX.md` calls the current edition. |
| `AIM_CONTINUATION_PATCH_2026-09-22.zip` | 74,406 | 22/09 20:57:02 | A tested source patch against the v04 component. |
| `ISUZU_UNIVERSE_2_1_COMMERCIAL_TOOLS.html` | 245,688 | 22/09 20:20:09 | Commercial tools page. |

The rest of the root splits into: ten PDF editions (white papers, yellow papers, a roadmap, a review), around twenty html/pptx deliverables, seven launchers, four ChatGPT-side instruction files (`CURSOR_FIRST_TASK.txt`, `CURSOR_START_FULL_BUILD.txt`, `TASKS_96.txt`, `AIM_CONTINUATION_REVIEW_2026-09-22.txt`), eight zip packs, two ship receipts, and a handful of extracted text files used to read the PDFs.

### 1d. The two new items

**`05_AIM_Universe\`** — the folder the review-and-repair exercise produced. Its own `README.md` describes it as "a correctness-and-continuity revision of the supplied v03 pricing component. It is the existing product, corrected — not a replacement application, not a framework migration, and not a new dashboard." It is tracked in git: 81 files under version control, on the last four commits, all local and unpushed.

**`.gitignore` at the Universe root** (2,447 bytes, written 22/09 19:02) — new, and deliberately keeps restricted material out of version control. Its own header explains why: a single `git add -A` would have staged 3,177 files, including three large HTML files with pilot accounts embedded and, across nine files in `06_Working`, 259 lines carrying restricted supplier purchase cost figures. Its rules ignore `06_Working/`, `_STRATEGY/`, `_build_v05/`, `_MERGED_MASTER_2026-09-21/`, the Cursor handoff folder, `GPT_HANDOVER_*/`, `03_Packages/**/RETURNS/`, every `_qa*` folder, the HTML files under `02_Atlas/` and `04_IDS_AIM_and_IMOTORS/`, and the component's own restricted data and test output.

I verified the rules bite with `git check-ignore`. `06_Working`, `_STRATEGY`, `_MERGED_MASTER_2026-09-21`, `GPT_HANDOVER_2026-09-22`, the network atlas HTML, and the component's restricted data file are all ignored as intended.

**The consequence is worth stating plainly, because it changes what a reader should expect to find.** A large share of this folder's most interesting content is not in version control at all. `_MERGED_MASTER_2026-09-21` — the project's own map — is untracked. `_STRATEGY` — all the evidence behind it — is untracked. So is the handover pack written for the other chat tool. Anyone who clones the repository and reads the map will find that the map points at folders that are not in the clone.

There is a second, sharper consequence. **The `.gitignore` file itself is untracked.** `git ls-files` returns nothing for `Isuzu Universe/.gitignore`. The rule that keeps restricted data out of the repository is not itself in the repository. On a fresh clone, the protection does not exist.

---

## 2. Who built what, and the evidence for it

I did not attribute anything from style or from the brief's own summary. For each group below I name the header, the field, or the sentence I read, and quote it.

### 2a. Built by the other chat tool (ChatGPT)

Its own documents say so, in the first person, and distinguish themselves from Cursor.

| Artefact | Evidence |
|---|---|
| `06_Working\AIM_v03_HANDOFF_20260922\` — the independent review package | `ENGINE_REVIEW.txt` ends with a section headed **"Tool distinction"**: *"ChatGPT here can write and run bounded patches, calculations, test fixtures, schema proposals and code reviews against uploaded files. Cursor can apply the same work in the maintained local repository, run the project and connect approved infrastructure."* A document that describes ChatGPT in the first person and Cursor as the other party was produced by ChatGPT. |
| `06_Working\AIM_v03_HANDOFF_20260922\CURSOR_SOURCE_NOTES.txt` | Titled *"OFFICIAL CURSOR DOCUMENTATION CHECKED 22 SEPTEMBER 2026"* and lists Cursor product pages. Written to brief Cursor, by the other side. |
| `06_Working\...\READ_FIRST.txt` | *"ISZE AIM v03 - independent review and Cursor handoff"*, with `CURSOR_FIRST_TASK.txt` described as *"the first bounded implementation instruction"*. |
| `CURSOR_FIRST_TASK.txt` and `CURSOR_START_FULL_BUILD.txt` at the root | Imperative briefs addressed to Cursor: *"Implement a correctness-and-continuity revision of the existing ISZE AIM Pricing Decisions component"* and *"Build the existing ISZE Universe/AIM product through the expanded internal release"*. These are instructions to this side, not work by it. |
| `TASKS_96.txt` (101,908 bytes) | Header: *"ISZE UNIVERSE - ACCELERATED WORK PLAN / 22 September 2026 \| Proposed tasks, not completed application work"*. This is the 96-task plan `05_AIM_Universe`'s progress record names as its source. |
| `AIM_CONTINUATION_REVIEW_2026-09-22.txt` | *"AIM UNIVERSE \| CONTINUATION REVIEW AND PATCH RESULTS / Patch AIM-CONTINUATION-20260922-01"*. Reports reproducing the correction work and finding further failures; describes itself as a delivery of patches *to* the local code. |
| `AIM_CONTINUATION_PATCH_2026-09-22.zip` | Its own `START_HERE.txt`: *"This continues the exact source supplied in `GPT_HANDOVER_2026-09-22.zip`."* It quotes the Cursor-side pack by name as its input and returns a patch. Not this side's output. |
| `AIM_RANGE_DECISION_PROTOTYPE_2026-09-22.zip` | `START_HERE.txt`: *"Prepared 22 September 2026. Separate development prototype, not an installed update."* Contains `src/engine/range.js`, two test files, an integration brief and a worked-examples note. |
| `AIM_OPPORTUNITY_REVIEW_SOURCE_2026-09-22.zip` and `AIM_Opportunity_Review_v0.1.html` | The zip's own `START_HERE.txt`: *"AIM COMMERCIAL OPPORTUNITY REVIEW v0.1 / Prepared 22 September 2026 \| Internal working application."* It ships its own build and browser test scripts and an integration brief, in the same delivery idiom as the other two packs. **This attribution is inferred from the pack structure and voice, not from a stated author — it is the weakest of the group and should be treated as likely rather than certain.** |
| `whitepaper_megaprompt` (55,278 bytes) | A prompt, not a product: *"Act as a combined: senior OEM aftersales strategist; ISZE parts commercial specialist; pricing and gross-profit analyst..."* |
| `_MERGED_MASTER_2026-09-21\` — the 20-file map | `00_THE_MAP.md`: *"**Built:** 2026-09-21 · **Internal / private** · Consolidation only."* and, in §10, it distinguishes itself from another producer working at the same time: *"Two files at the `Isuzu Universe` root and a separate working folder under `01_data\90_INBOX\` were written **during** the same window by another session ... **They are not part of this consolidation and were not touched by it**."* **Claimed by the document, not independently verified**: it says it is a separate producer's consolidation, and its voice and its "Tool distinction"-style honesty about sources are consistent with the review package above. I could not find a field that names the tool. |
| `01_Strategy\` papers, the root white papers and yellow-paper editions | The strongest single piece of evidence is **negative and dated**: `ISUZU_UNIVERSE_WHITE_PAPER_REVIEW_2026-09-21.md` (21 Sept) and `Universe_Yellow_Paper_v0.2_REDTEAM_REVIEW_2026-09-22.md` are critiques *of* these papers, and the second one is signed *"**Reviewer:** Cursor agent, 22 September 2026."* The critique of a paper is not written by the paper's author, so the papers themselves came from the other side. `_MERGED_MASTER_2026-09-21` §7 also lists the strategy papers and atlas material as inputs to that map. **Claimed, not verified** for the individual papers: no paper carries an author field. |

### 2b. Built by this Cursor session

The evidence is the four local commits and the component's own record, not the file dates.

| Artefact | Evidence |
|---|---|
| `05_AIM_Universe\` in full | Git log: `5f05ee5` *"Add AIM Universe v04 pricing component: corrected engine, one scenario record, acceptance suite"*, then `b07ed47`, `e157e29`, `5d4570a` *"Build the case service and fix the build guard that was not guarding"*. 81 files tracked. `docs\CASE_service.md`: *"Written 2026-09-22 by the workflow developer. Everything below is measured on this machine."* `docs\VERIFICATION.md`: *"Written by the independent verification reviewer, 22 September 2026."* |
| `GPT_HANDOVER_2026-09-22\` and its zip | `_MANIFEST.md`: *"Refreshed 2026-09-22 from the working copy as it stands after commit `5d4570a`."* That commit is this session's. `00_START_HERE.md` is addressed to the reviewer: *"written for you, because your original review and execution brief started this work and you have not seen what was built since."* **The audience is the other tool; the producer is this side.** I flag this because a reader opening the folder could easily mistake the address for the authorship. |
| `.gitignore` at the Universe root | Its header is written in this work's voice and cites this side's own measurement: *"Measured 2026-09-22 - a single `git add -A` at the repo root would have staged 3,177 files..."* and refers to *"`05_AIM_Universe`, whose own `.gitignore` governs what within it is tracked."* It knows about the component by name. |
| Five uncommitted working-tree changes | `git status` shows four modified files and one deleted probe under `05_AIM_Universe`, plus one new untracked probe: the restricted-value scrub still in the working tree, not yet committed. |

### 2c. Pre-existing ISZE material that neither produced

| Material | Evidence |
|---|---|
| The pricing component that was revised — `ISZE_AIM_Pricing_Decisions.html` and `..._v02.html` at the root | `CHANGELOG_v03.md`: *"**Base:** `ISZE_AIM_Pricing_Decisions_v02.html` (the existing 0.2 component) **Output:** `ISZE_AIM_Pricing_Decisions_v03.html`"* and *"This is a revision of the existing component."* The v03 review is explicitly a review of *"the supplied HTML"*, and the v04 work is a revision of v03. The chain starts at a component that predates both tools. |
| The two shortcuts in `02_Atlas\` | Both resolve to files outside this folder, verified by reading the shortcut targets: the IDS dealer comparison points at `ISZE\02_dashboards\ids\IDS_2026_dealer_compare.html`, and the parts-atlas handoff points at `ISZE\01_data\90_INBOX\`. Both targets exist. |
| The data every paper cites | `_MERGED_MASTER_2026-09-21` §7 names it: the 83 MB workshop workbook under `03_analytics\Isuzu\pms-pilot\`, the derived CSVs under `01_data\00_derived\`, `sales_fact.parquet`, `HKK.xlsx`, the AIM classification files, the ten schedule PDFs, the IDS workbook and `tender_data.json`. All of it lives in ISZE proper. |
| The logo asset | `BPR_AIM_EDITION_STYLE_NOTE.md` names the red official mark at `ISZE\04_tools\ppt_template_v2\assets\isuzu_logo_red.png` as the source; `_assets\isuzu_logo_white.png` is derived from it. |

### 2d. Unattributed

I am marking these unattributed rather than picking a side. There are two distinct kinds of ambiguity, and they are not the same problem.

**First: the earlier Cursor-side work of 22 September, 05:00–11:00.** This is a real body of work — the yellow paper v0.5 and its build, the opportunity page, the v02 and v03 pricing pages, their change log and test results. The tooling says Cursor: two artefacts carry `*.SHIP_RECEIPT.json` files in the Cursor workspace's own receipt format (schema `ship_receipt/v2`), and `Universe_Yellow_Paper_v0.2_REDTEAM_REVIEW_2026-09-22.md` is signed *"Cursor agent"*. But **that is a different Cursor session from this one**: it ran roughly six to fourteen hours before the first component commit, and the brief's attribution for this session is the `05_AIM_Universe` work. I cannot tie any of these files to this session, and I will not claim them for it. The specific files are:

`Universe_Yellow_Paper_v0.5_2026-09-22.pdf` and `.SHIP_RECEIPT.json`; `Universe_Opportunity_Page.html` and `.SHIP_RECEIPT.json`; `Universe_Yellow_Paper_v0.2_REDTEAM_REVIEW_2026-09-22.md`; `ISZE_AIM_Pricing_Decisions_v02.html`, `_v03.html`, `_v03.zip`, `_v03_OBJECTIVES.csv`, `_v03_OUTPUTS.json`; `CHANGELOG_v03.md`; `TEST_RESULTS_v03.md`; `ISZE_AIM_Cursor_Pack_Review_2026-09-22.pdf`; `_build_v05\`; `_qa_pdf\`, `_qa_page\`, `_qa_yellow\`; `06_Working\AIM_v03_APP_20260922\`.

**Second: the 21 September evidence work under `_STRATEGY\` and `03_Packages\`.** `_MERGED_MASTER_2026-09-21` §3 states that *"The completed returns are `R0_RETURN\`, `R1_RETURN\`, the vertical evidence audit and its outputs, and the two consolidated returns"*, and the package start notes assign Cursor to *"inspect and implement"* and the other tool to *"specify, prioritize and review returned evidence"*. That assigns the returns to a Cursor-side session. But the packages themselves were *"Prepared for the user to run locally; not dispatched by ChatGPT"* — a sentence written by the ChatGPT side — so the packages are the other tool's work orders, and the returns inside them are Cursor's. Which session ran those returns I cannot establish. **Claimed, not verified.**

**Third, genuinely unresolved: `_MERGED_MASTER_2026-09-21`.** Its own §1 says it was *"merged by topic"* from the evidence work, and §10 distinguishes it from *"another session"* working at the same time. That is a claim by the document about itself. Nothing on disk names its producer. I am recording it under the other tool because its voice matches that group and because it does not match the component work, but the honest label is **unattributed by direct evidence**.

---

## 3. The gap between the map and the disk

### 3a. `INDEX.md` — stale or wrong claims

The file is 2,925 bytes, last written 22/09 06:32. Every launcher it names resolves, but it misdescribes the folder in ways that matter.

**1. The folder-numbering collision.** `INDEX.md` lists, in its own "Folders in this map" table:

> | `05` — `_STRATEGY` | Orchestration evidence (R0, R1, audit, consolidated returns, Cordwallis case) |

On disk, **`05_AIM_Universe`** is the folder that carries the number 05. `INDEX.md` shows 00 through 06 and never mentions `05_AIM_Universe` anywhere — I searched the file for `05_AIM`, `AIM_Universe` and `gitignore` and got no hits. So the reader is told 05 is the evidence folder, while the folder actually named 05 is something else entirely.

**2. The omission of the component.** This is the important one. `INDEX.md` says nothing about `05_AIM_Universe`. What a reader of `INDEX.md` would not know:

- that the folder holds the one thing the whole review-and-repair exercise produced — a working pricing component, `ISZE_AIM_Pricing_Decisions_v04_INTERNAL.html`, 5,404,107 bytes, buildable and testable, with its own launcher;
- that it is the only part of this tree under version control on a named branch, with four commits;
- that it carries a written defect record, a verification document and 15 documents in total;
- that it holds restricted material (the extracted data file and the frozen v03 reference) and deliberately excludes it from version control;
- that it has a launcher of its own, `05_AIM_Universe\dist\OPEN_AIM_Pricing_Decisions_v04.cmd`, which works and which nothing in `INDEX.md` would lead you to.

**3. "Twenty files" undercounts.** `INDEX.md` calls the map *"Twenty files, one topic each."* `00_THE_MAP.md` also says twenty. On disk that folder has **22 files**: the 20 documents (00 with 19 numbered files), a two-line `README.md`, and `_tmp_horizons.txt`, a 23,389-byte scratch file written 22/09 06:40 which no map mentions.

**4. The "current edition" is no longer the newest work.** `INDEX.md` says:

> **`Universe_Yellow_Paper_v0.5_2026-09-22.pdf`** — the product and operating paper, rebuilt from the review of v0.2.

The file exists — 282,128 bytes. But it is no longer the newest thing in the folder. Nine bundles were written after it on 22 September evening: the opportunity review page and its source pack at 21:24, the v04 continuation patch at 20:57, the commercial tools page, presentation and white paper at 20:18–20:20, the range-decision prototype and its worked examples at 20:05, the handover pack for the other tool at 19:30, the continuation review at 19:19, and the business-performance-review deck at 19:09. A reader following `INDEX.md` would believe the paper is the frontier; it is about two hours behind the folder.

**5. The v0.5 receipt no longer covers the v0.5 file.** `Universe_Yellow_Paper_v0.5_2026-09-22.SHIP_RECEIPT.json` was written at `2026-09-22T04:46:00Z` and records an artifact time of `1790052299800`, which is 04:44:59Z — the file as it stood then. The PDF on disk is stamped 22/09 21:24:29 local (19:24:29Z), a rebuild about fourteen and a half hours later. **The receipt therefore does not cover the file that is on disk.** By the workspace's own rule, an artefact whose receipt does not cover its current modification time is not verified. Either the PDF was rebuilt without a new receipt, or it was replaced from elsewhere. I did not determine which. The same check on `Universe_Opportunity_Page.SHIP_RECEIPT.json` passes — that receipt does cover its file.

**6. The `_build_v05` claim does not match the PDF.** `INDEX.md` says `build_v05.py` *"renders the PDF and QA-checks every page"*. Both scripts exist (14,464 and 6,080 bytes). But the newest file in `_build_v05` is the intermediate HTML at 06:44:56, and the PDF on disk is stamped 21:24:29. **Claimed, not verified** that the PDF on disk came from that build.

**7. No mention of the ignore rules, or of what they hide.** `INDEX.md` does not mention `.gitignore`. A reader would reasonably expect `06_Working`, `_STRATEGY`, `_MERGED_MASTER_2026-09-21`, the atlas HTML files and the handover packs to be in the repository. They are not. Nor is `INDEX.md` itself — `git status` lists `?? "Isuzu Universe/INDEX.md"`. **The project's own entry point is untracked.**

**8. What is still correct.** To be fair to the file, the parts that matter for opening things all check out, and I verified each one: the v0.5 PDF exists; the opportunity page exists and so does its copy and launcher in `02_dashboards\`; the red-team review exists; the source markdown `01_Strategy\Universe_Yellow_Paper_v0.5_2026-09-22.md` exists; the map folder and its `00_THE_MAP.md` exist; the orchestration folder and the consolidated return exist; `_build_v05\build_v05.py` and `check_coverage.py` exist.

### 3b. `_MERGED_MASTER_2026-09-21\00_THE_MAP.md` — the same problem

The master map has the same omission, and it is more defensible there for a date reason.

The map is stamped *"**Built:** 2026-09-21"*, and it is explicit that it is a consolidation of what existed then: *"No application was rebuilt. No dealer page was created. No scraper or collection service was run ... Nothing outside this folder was modified, moved, renamed or deleted."* The component work happened on 22 September, after the map's stated build date. I searched `00_THE_MAP.md` for `05_AIM`, `AIM Universe`, `AIM_Universe`, `gitignore` and `Opportunity_Review` — no hits.

So: the map is not wrong about its own date, but **a reader who treats it as the current picture of the folder is reading a 21 September picture of a folder that added its most substantial artefact on 22 September.** The map is presented by `INDEX.md` as *"The whole map (read first)"*, and nothing in either document warns that the newest and most consequential folder is missing from it.

The map does contain one thing worth flagging as still true but easy to misread. §10 says two root files and a working folder under `01_data\90_INBOX\` were *"written **during** the same window by another session"* — naming `Universe_IDS_AIM_Bridge.html`, `AIM_PRISM_Five_Action_Studies.pdf` and the SPA engine folder. That honest note is the map's own account of a parallel producer. It is about 21 September, not about the 22 September component work.

### 3c. Launchers

I tested every launcher named in `INDEX.md`, plus the ones it does not name. **There is no broken launcher in this folder.** Every target resolves.

| Launcher | Target | Target exists |
|---|---|---|
| `OPEN_THE_MAP.cmd` | opens the `_MERGED_MASTER_2026-09-21` folder | yes |
| `OPEN_Universe_Yellow_Paper_v0.5.cmd` | `Universe_Yellow_Paper_v0.5_2026-09-22.pdf` | yes (282,128 bytes) |
| `OPEN_Universe_Opportunity_Page.cmd` | `Universe_Opportunity_Page.html`, preferring Chrome | yes (31,305 bytes) |
| `OPEN_Yellow_Paper_REVIEW.cmd` | `Universe_Yellow_Paper_v0.2_REDTEAM_REVIEW_2026-09-22.md` | yes (117,598 bytes) |
| `04_IDS_AIM_and_IMOTORS\OPEN_IMOTORS_PACK.cmd` | the IMOTORS start note | yes |
| `02_Atlas\IDS dealer comparison.lnk` | `ISZE\02_dashboards\ids\..._dealer_compare.html` | yes |
| `02_Atlas\Parts atlas handoff 2.1.lnk` | `ISZE\01_data\90_INBOX\AIM_Atlas_2.1_handoff_2026-09-20` | yes |
| `02_dashboards\OPEN_Universe_Opportunity_Page.cmd` (the copy `INDEX.md` mentions) | `02_dashboards\Universe_Opportunity_Page.html` | yes |
| `OPEN_AIM_Pricing_Decisions_v03.cmd` *(not named in `INDEX.md`)* | `ISZE_AIM_Pricing_Decisions_v03.html` | yes (5,935,584 bytes) |
| `OPEN_BPR_AIM_Edition_v2.1.cmd` *(not named in `INDEX.md`)* | the v2.1 business-performance-review deck | yes (299,007 bytes) |
| `05_AIM_Universe\dist\OPEN_AIM_Pricing_Decisions_v04.cmd` *(not named in `INDEX.md`)* | the v04 internal component HTML | yes (5,404,107 bytes) |

One thing a reader should know about the launcher list: `INDEX.md`'s "Quick opens" table names four launchers, and the folder holds seven. Three working launchers — the v03 page, the business-review deck, and the v04 component — are invisible from the map.

### 3d. The `INDEX.md` claim about the missing application

`INDEX.md` says:

> ## Not on this PC
> There is still no product application folder named `UNIVERSE` (login / product). That gap is recorded. Do not invent one until a work order says so.

**Strictly, it is still true, and I verified it:** no folder anywhere beneath the Universe root is named `UNIVERSE`. `05_AIM_Universe` is the only folder carrying an "Universe" name, and it is a pricing component rather than a product application with a sign-in.

**But it is now materially misleading, and this is the strongest single finding in this audit.** `05_AIM_Universe` contains an application-shaped thing with exactly the surface that sentence describes. Its own source includes a permission table, a development identity, a `requireApprovedIdentity` gate, a `canRead` / `canAttach` pair and a case store. Its `docs\VERIFICATION.md` has a section headed *"Real identity and tenancy"* and another headed *"Server-side access control"*. So a reader who takes `INDEX.md` at its word — "there is no product application, do not invent one" — would be excluding from consideration the one component in the tree that has a sign-in surface, an access model and an acceptance suite.

The sentence needs one added line: there is no hosted application and no approved sign-in, but a candidate application component now exists at `05_AIM_Universe\`, and its own documents say plainly which halves of the application problem it does and does not close.

---

## 4. The three open gaps the project records, and whether this session changed them

These three are named in the brief and each is also recorded in the project's own files. I checked each against what the session actually did.

### Gap 1 — no shared case service

**What the project records.** The component's `README.md`: *"The case record is browser storage, not a shared service with authenticated ownership. There is no approved backend on this machine, so choosing one is an owner decision, not a coding task."*

**What the session did.** It narrowed the gap and then deliberately stopped. Commit `5d4570a` is titled *"Build the case service and fix the build guard that was not guarding"*, and `docs\CASE_service.md` records the outcome with its own evidence: *"A draft survives a REAL process restart: the parent writes the case, then runs `tests/case_restart_child.cjs` in a SEPARATE node process and reads its answer. The same check asserts the file's bytes AND its mtime are untouched, so the child provably only read."* It also records the honesty markers that stop the local store being dressed up as a service: *"A folder of files on one machine is not a shared service, and every description says so: `describeStorage()` states it, the bundle carries `not_a_shared_service: true`, and the app warns when storage is not durable."*

**Verdict: not closed, and closed was never the aim.** What changed is that the case record is now durable, append-only, versioned and proven to survive a real restart — and that every description of it refuses the word "service". The shared service itself needs infrastructure and an owner, and there is none on this machine.

### Gap 2 — no production identity

**What the project records.** Open finding `F08-IDENTITY`, severity medium, owner *"integration owner"*: *"there is no approved identity provider on this machine, so `requireApprovedIdentity` REFUSES an authenticated identity rather than accepting one. That refusal is deliberate - accepting one would be inventing authority - and a development identity is a declared role, not an authentication."* The finding's impact note adds: *"Real tenant policy, revocation and server-side enforcement remain unimplemented, because no backend exists here to provide them. A browser-side allowlist is not access control, and it is not described as one anywhere in the code."*

**What the session did.** It closed the disclosure half and refused the rest. `F08-IDENTITY` records that the permission table and related functions were moved into the shipped code so the case store's attachment check works in a browser, *"so the component-level permission logic is closed, and a participant cannot read the internal record through this component. What remains is narrower."* `docs\VERIFICATION.md` lists under *"Not started"*: *"server-side access control; production identity and tenancy; attachment storage; revocation; cross-tenant isolation."*

**Verdict: not closed, and the honest position was chosen over a passing test.** The component now refuses an authenticated identity instead of faking one. That is the right behaviour and it does not make production identity exist.

### Gap 3 — candidate records carry no reporting period

**What the project records.** Open finding `R27-CANDIDATE-PERIOD`, severity medium, owner *"source owner (not an agent)"*: *"ACCEPT-01 R27 fails and should stay failing. The [candidate] rows have no period, year or date field, though the screening rule is described as running on 2025/2024 and H1 2026/2025. ... Guessing the period is the one thing the brief forbids."*

**What the session did.** Nothing to the data, and it says so. `docs\VERIFICATION.md`, under *"What is still open"*: *"**R27 - candidate records declare no reporting period.** Unchanged and unfixed by me. The candidate records in the delivered data carry no period or year field, so an assertion that they declare their reporting period cannot pass. I kept the original assertion exactly as supplied and added a second check beside it: the screen now declares that the period is undeclared and refuses to promote a record whose period is unknown. That is the right behaviour, but it does not make the missing period exist. It needs the source to carry the period."* The independent acceptance suite is recorded as 46 of 47, with that single failure retained on purpose.

**Verdict: not closed. Changed only in that the gap is now visible in the product and refuses to advance a record whose period is unknown, instead of being assumed.**

**On all three, the same pattern holds.** The session closed the parts a coding session can close, named the parts it cannot, and left failing checks failing rather than relaxing them. Two further open findings in the same record point the same way — `MARKET-DATA-GAP` (high) says the data file has no usable comparable price observation, and `PAYLOAD-PROVENANCE` says the data file carries no recorded digest so an added key cannot be verified. Both are assigned to owners who are not agents.

---

## 5. If someone opened this folder cold

They would think they had walked into a finished, well-documented product programme: a folder called Isuzu Universe, numbered 01 to 06, an entry-point map that tells them everything has a place, a current paper with a version number, a settled list of closed decisions, and an attractive set of charts and decks at the root. On that reading the story is clean — the map explains the evidence, the evidence supports the papers, and the papers are the deliverable. What would surprise them is everything the map leaves out. They would find that the most recent and most substantial thing in the tree, a working pricing component with an acceptance suite behind it, is not mentioned in the entry point at all — and worse, that it occupies the folder number the map assigns to something else. They would find that a whole second programme is running alongside the first: a review-and-repair loop that produced the component, four local commits, a handover pack written for the other chat tool, and a patch series answering it back, none of it in the map. They would find that the map's reassuring "everything has a place" is false in a second, quieter way, because the newest work is not under version control — the map itself, the entire evidence folder behind it, and the rule file that keeps restricted data out of the repository are all untracked, so a fresh clone would contain the map's pointers and none of its destinations. And they would find the restricted material the folder is careful not to talk about: pilot accounts and private supplier purchase costs sitting in the data file, the frozen reference and several HTML pages, with the `.gitignore` doing real and deliberate work to keep them unversioned. The honest summary is that this is two projects sharing one folder — a largely complete planning and evidence programme that is carefully documented and mostly not in version control, and a newer engineering programme that is in version control and almost entirely absent from the documentation.

---

*Prepared by the Cursor agent, 22 September 2026. Read-only audit; no file was modified, moved, renamed, deleted or committed, and no remote branch was touched.*

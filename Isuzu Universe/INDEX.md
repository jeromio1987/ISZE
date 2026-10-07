# Isuzu Universe

This is the working map for the Isuzu Universe project. It holds **two programmes** sharing one folder: a planning and evidence programme, and an engineering programme that builds the software. Both are below.

## Where the engineering build stands (read this first)

The pricing-decision component in `05_AIM_Universe\` is the live product, and its
own record is the answer to "what is built":

- `05_AIM_Universe\progress\progress.json` - 96 planned tasks with the state each
  one really holds. 90 verified, 1 implemented, 5 not started. A verified task
  means a named check ran and its output was recorded; it is not a person's
  acceptance, and nothing here is deployed or published.
- `..\02_dashboards\hub\ISZE_UNIVERSE_MAP.html` - the same status in plain
  language, rebuilt from that record.
- `..\00_docs\ISZE_ROADMAP.md` - the programme roadmap, with one Universe block
  listing what is on main and what still sits on a branch.
- `05_AIM_Universe\docs\VERIFICATION.md` - what passes and what remains.

**What waits for a person, not for effort:** `ACCEPT-04` to `ACCEPT-08` need real
participants; real sign-in needs IT and was parked; the `R27` check needs a
candidate reporting period the source data does not carry; and how the pilot
performed needs ITUK sales-to-dealer from after December 2025.

---

## The working software

**`05_AIM_Universe\`** — the maintained pricing-decision component, and the only part of this folder under version control. It carries corrected pricing arithmetic, one shared scenario record, a durable case record, recipient-specific exports and an independent acceptance suite. Its own `README.md`, `docs\` and `progress\progress.json` explain what is verified and what is not.

Source lives in `src\` and is assembled by `tools\build.py` into `dist\`. Tests run with `powershell -File tests\run_all.ps1`. Read `docs\VERIFICATION.md` for what passes and what remains unaccepted.

Three checks are deliberately red and should stay that way: the two unchanged baselines that reproduce the original v0.3 defects, and one that asks for a candidate reporting period the source data does not carry.

**Not yet integrated:** three packages supplied by the other tool sit at this folder's root as zips - a range-decision prototype, a patch to the engine, and an opportunity-review module. None is applied. See `UNIVERSE_MAP_AUDIT_2026-09-22.md`.

## The planning papers (September 2026 - not the live product)

**`ISUZU_UNIVERSE_3_0_2026-09-23.pdf`** — the commercial vision and participation paper, 25 pages, rebuilt from the 23 September review of the two editions written on 22 September. It carries the scope boundary, the five-tool portfolio, the money chapter, the participation assessment with a score per step, and the decision it asks for. Source: `01_Strategy\ISUZU_UNIVERSE_3_0_2026-09-23.md`. Double-click `OPEN_ISUZU_UNIVERSE_3_0.cmd`. Check `ISUZU_UNIVERSE_3_0_2026-09-23.SHIP_RECEIPT.json`.

**`ISUZU_UNIVERSE_3_0_ANNEX_2026-09-23.pdf`** — the companion, 15 pages. Part A restores the tender and headquarters-support framework, Part B the IDS Development Studio in full, Part C the reference rules (measures, identities, periods, the recurring exchange, record structures). It carries design detail only: no recommendation and no number in it overrides the main paper. Source: `01_Strategy\ISUZU_UNIVERSE_3_0_ANNEX_2026-09-23.md`. Double-click `OPEN_ISUZU_UNIVERSE_3_0_ANNEX.cmd`.

**`ISUZU_UNIVERSE_3_0_DECK_2026-09-23.pptx`** — 24 slides, for talking from. One idea per slide, the argument in the speaker notes, and the same charts the paper uses so the two cannot disagree. Built by `_build_30\build_deck.py`. Double-click `OPEN_ISUZU_UNIVERSE_3_0_DECK.cmd`.

**`ISUZU_UNIVERSE_3_0_SHOWCASE_2026-09-23.html`** — the working showcase, rebuilt to match. Its embedded copy of the paper was still the withdrawn 80-page edition and every tool pointed at a page number that no longer existed; it now carries the current 16 sections and points at the sections that actually answer each tool's question. Built by `_build_30\patch_showcase.py`, which writes the old file aside as `ISUZU_UNIVERSE_3_0_SHOWCASE_SUPERSEDED_2026-09-22.html`. Double-click `OPEN_ISUZU_UNIVERSE_3_0_SHOWCASE.cmd`.

**Both editions of 22 September are withdrawn by this one.** `ISUZU_UNIVERSE_COMMERCIAL_VISION_3_0.pdf` (80 pages) and `ISUZU_UNIVERSE_COMMERCIAL_TOOLS_WHITE_PAPER.pdf` (33 pages) remain on disk for reference and must not be quoted as current. The 80-page edition omitted the scope boundary; the 33-page edition stated it and carried a different five-tool product range. The new edition adopts the boundary and one portfolio. What the review cut from the 80-page edition but still belongs in a reference — the tender framework, the IDS chapter in full and the definitions — now sits in the annex rather than being lost.

**`Universe_Yellow_Paper_v0.5_2026-09-22.pdf`** — the product and operating paper, rebuilt from the review of v0.2. It carries a worked commercial case, a written rule for what surfaces an opportunity, a go/no-go test and a stop condition. Source: `01_Strategy\Universe_Yellow_Paper_v0.5_2026-09-22.md`. Double-click `OPEN_Universe_Yellow_Paper_v0.5.cmd`.

**`Universe_Opportunity_Page.html`** — the working opportunity screen, filled in with a real finding on a real account. Built from files ISZE already holds. Double-click `OPEN_Universe_Opportunity_Page.cmd`.

A copy of the opportunity page and its launcher also sits in `..\02_dashboards\`, beside the other dashboards, so it can be opened from the usual place.

**`Universe_Yellow_Paper_v0.2_REDTEAM_REVIEW_2026-09-22.md`** — the adversarial review of v0.2 that v0.5 answers. Double-click `OPEN_Yellow_Paper_REVIEW.cmd`.

**`_build_30\`** — the build for the current edition: `build.py` renders the main PDF and checks every page; `build_annex.py` does the same for the annex; `build_deck.py` builds the talk deck; `patch_showcase.py` rebuilds the showcase from the current markdown and remaps its page references; `check_coverage.py` proves each correction from the review landed and sweeps for banned language; `figures.py` regenerates every chart from `..\01_data\00_derived\` so the paper cannot carry a chart that disagrees with its source. `docbuild.py` is the shared renderer they all use.

**`_build_v05\`** — the build and the two checks for the Yellow Paper: `build_v05.py` renders the PDF and QA-checks every page; `check_coverage.py` proves each demand from the review landed.

Earlier editions (v0.1, v0.2, the white papers) are kept where they were and are superseded.

## Start here

1. **The whole map (read first)**  
   `_MERGED_MASTER_2026-09-21\` — open `00_THE_MAP.md` inside it.  
   Or double-click `OPEN_THE_MAP.cmd` in this folder.  
   It is stamped 21 September, so it predates the engineering programme above and does not mention it.

2. **Evidence behind that map**  
   `_STRATEGY\_ORCHESTRATION\` — returns, workstreams, the Cordwallis case.  
   Canonical return: `CONSOLIDATED_ITUK_2026-09-21_01\`

## Folders in this map

| Folder | What is in it |
|---|---|
| `00` — `_MERGED_MASTER_2026-09-21` | The merged master map (open this first) |
| `01_Strategy` | Strategy papers, critique, commercial / value-exchange drafts, pilot pack |
| `02_Atlas` | Network and parts atlas (HTML + concept notes + shortcuts) |
| `03_Packages` | Cursor packages R0 / R1 and their zip drops |
| `04_IDS_AIM_and_IMOTORS` | IDS↔AIM bridge, IMOTORS pack, ITUK real-data HTML |
| `05` — `05_AIM_Universe` | **The working software component.** Not `_STRATEGY` — see the note below |
| `_STRATEGY` | Orchestration evidence (R0, R1, audit, consolidated returns, Cordwallis case) |
| `06_Working` | Build scripts, export packs, PRISM screen grabs |

**Numbering note:** earlier editions of this file described `_STRATEGY` as folder 05. The folder actually numbered 05 is now `05_AIM_Universe`. `_STRATEGY` keeps its name and has no number.

## What is and is not under version control

Only `05_AIM_Universe` and a handful of its neighbours are tracked. Everything else here — the strategy papers, this map, the evidence returns — exists on this disk and is **not** backed up by git. `Isuzu Universe\.gitignore` sets out what is deliberately excluded: the embedded-data HTML, the working and generated folders, and the screenshots, because they carry pilot accounts and private supplier purchase costs.

## Quick opens

| Double-click | Opens |
|---|---|
| `OPEN_THE_MAP.cmd` | The merged master folder |
| `04_IDS_AIM_and_IMOTORS\OPEN_IMOTORS_PACK.cmd` | IMOTORS pack start note |
| `02_Atlas\IDS dealer comparison.lnk` | Live IDS dealer compare dashboard |
| `02_Atlas\Parts atlas handoff 2.1.lnk` | Parts atlas handoff folder |

## Not on this PC

There is still no product application folder named `UNIVERSE` (login / product). That gap is recorded. Do not invent one until a work order says so.

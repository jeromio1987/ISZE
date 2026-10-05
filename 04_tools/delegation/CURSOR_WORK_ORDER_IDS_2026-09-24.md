# Cursor work order — IDS build-out (24 September 2026)

Jerome, 2026-09-24: *"anything else can you start building the IDS things, build as much as
you can, we will review later."*

Build, do not ask. Two blocks, both now. Everything is reviewable afterwards.

**Authority:** this is an explicit build instruction from Jerome. It does **not** override the
shared-pack rules below — an IDS page that reaches a distributor must obey `isze-ids-delivery.mdc`
and `isze-external-iml-language.mdc` in full.

---

## Rules for every block

- Read `CLAUDE.md`, `INDEX.md`, and the last 10 rows of `00_docs\agent\DELEGATOR_BOARD.md` first.
  When done, append one row.
- **Never load `01_data\raw\sales\*.XLSX`** or line-level billing. Use derived CSVs / parquet.
- **Numbers:** green `01_data\00_derived\_verification_report.json` → `metrics_snapshot.json` →
  `FACTS.md`. Never invent a number. Missing data shows as missing, never as zero and never as a guess.
- Write files as UTF-8 **without BOM** (Python `open(..., "w", encoding="utf-8")`; not
  PowerShell `Set-Content`).
- **Self-contained HTML.** No CDN. No `fetch()` of a sibling file — Jerome opens with a
  double-click (`file://`). Embed the data or ship a launcher. Sibling `OPEN_*.cmd`, **CRLF**.
- **English only, everywhere.** No Dutch anywhere client-facing: `goed` → **good**,
  `slecht` → **weak**. Country names spelled out in English. `MIDI_CH` → **Switzerland**,
  `BE` → **Belgium**, `NL` → **Netherlands**, `FR` → **France**. Never leave an internal code
  as a shown label.
- **No internal terms** on anything a distributor could see: AIM, PRISM, DLOD, IDS as an
  acronym, GPS, BVP, IML, ITUK, IUK, UMI, UTI, `.csv`, `.json`, `.py`, "campaign". Scan for
  them and report the count. **Every count must be 0.**
- **No changelog / agent build notes** in any shared page. Notes go in `CHANGELOG.md` internal.
- **UTI ≠ UMI** (never blended). **IUK ≠ ITUK** (pickup vs truck; the label maps in
  `04_tools\ids_dealer_ranking\ids_paths.py` are correct — do not flip them).
- **Do not rebuild the dealer compare pages** unless a block says to. They were reworked today
  and carry receipts. Read them, reuse them, link to them.
- **No emails. No publishing to GitHub Pages. No new scheduled task, no change to an existing one.**
- Report in **under 150 words**: files changed, checks run with results, banned-term count,
  anything left open or uncertain. If a check fails, say so plainly — do not call it done.

---

## E · File B — the country action board (the big one)

```text
Work in C:\Users\jerom\Desktop\claude\ISZE. Follow the rules in
04_tools\delegation\CURSOR_WORK_ORDER_IDS_2026-09-24.md.

Context. An empty wireframe already exists and was never built:
02_dashboards\ids\IDS_2026_Country_Action_UX_proposal.html — "Two files. Not eight studies."
File A (the network + country dealer compare) is built and stays as-is. File B is the missing
piece: ONE country action board that folds the separate study pages into a pairing view plus a
short action list, so a distributor sees one page per country instead of eight studies.

Read first:
- 02_dashboards\ids\IDS_2026_Country_Action_UX_proposal.html  (the wireframe: Pair / Act / Other
  data tabs, the KPI chips, the dealer hit list, and section "3. What we drop from the eight")
- 02_dashboards\ids\IDS_2026_dealer_compare.html               (File A — reuse, do not rebuild)
- 02_dashboards\ids\IDS_2026_Kaizen_Belgium.html and 02_dashboards\ids\IDS_2026_Portugal_dealer_map.html
- 04_tools\ids_dealer_ranking\ : ids_paths.py (country labels + paths), IDS_2026_LOGIC_CHECK.md,
  ids_dashboard_qa.py, and the build_* scripts to see the house pattern
- 01_data\00_derived\ids_dealer_network_cleaned_2026-09-20.csv  — the dealer assessment spine
  (inspect its header first; do not assume column names). Also ids_dealer_network.csv.
- The derived data behind any chip you show: 01_data\00_derived\pms_capture_by_db_year.csv
  (PMS total capture — total first, genuine as an extra lens, never genuine-only),
  wallet_waterfall.csv (GPS euros), gps_spu_by_distributor.csv.

Build 02_dashboards\ids\IDS_2026_Country_Action.html — ONE self-contained page that selects a
country and shows File B for it, following the wireframe's structure:

1. A country selector. Default to one real market with good data; make every country with an
   assessment reachable.
2. The four chips at the top, each with a hover explanation of its formula, snapshot date and
   what it does NOT include:
   - Section D parts score against that country's own dealers
   - PMS total capture (total first; genuine is a second lens)
   - GPS euro (the euro from the extract). Show a GPS percentage ONLY where the fleet figure for
     that market is signed off; otherwise show the euro and say the percentage is not shown.
   - Open actions (a count, plus the list — see 4)
3. Pair tab: the two views the wireframe asks for — the parts-vs-commercial-capture scatter with
   this country circled and peers as grey dots, and the sections-vs-country/network comparison
   (A Service, B, C, D Parts, E). Label "not scored" where a dealer or country did not sit a
   section. Do not plot a section as zero when it was not assessed.
4. Act tab: three to five actions for that distributor, each with action / why (which section or
   which commercial gap) / owner / confirm-by date. Read the existing Kaizen pack to copy its
   shape. Where we have no minutes, show the action with owner and date blank — do not invent them.
5. A dealer hit list for that country only: the bottom dealers against the country average on
   parts and service, as one table. Hover must show the dealer's score against the NATIONAL
   (country) average — that is a hard rule for IDS.
6. Other data tab: if we hold it (sales to dealer, fill, stock vs urgent, last meeting follow-ups)
   show it; if we do not, show an empty state plus ONE ask card saying what the distributor should
   send. Never a data dump.

Hard rules for this page:
- Self-contained: no CDN, no fetch of a sibling file. If the payload is large (> ~2 MB), ship a
  .cmd/.ps1 launcher that serves it locally and opens the http:// URL, and say so.
- If a map is included, confirm basemap tiles paint in the rendered page (not a blank outline
  box). Inline tiles or ship the launcher; do not depend on a CDN.
- English only. No internal terms (scan and report, count must be 0).
- A national vehicle total must never be allocated to dealers by sales, visits or geography.
- Do not average UTI into UMI.
- Where a distributor we cannot name is involved, show the aggregate only.

Then: write a sibling OPEN_IDS_2026_Country_Action.cmd (CRLF). Render the page in headless Chrome
(Chrome is at "C:\Program Files\Google\Chrome\Application\chrome.exe"; --headless=new --disable-gpu
--no-sandbox --screenshot=... on the file:// or localhost URL), and READ the PNG yourself at full
size. Check 3 countries including one thin-data market. Also run the existing IDS QA you can
(ids_dashboard_qa.py / ids_logic_check.py) and confirm you did not break the existing pages.

Write 02_dashboards\ids\CHANGELOG.md entries (internal). Report banned-term count, the countries
you checked, and anything you could not fill from real data.
```

---

## F · The development half — priority, milestones, evidence

```text
Work in C:\Users\jerom\Desktop\claude\ISZE. Follow the rules in
04_tools\delegation\CURSOR_WORK_ORDER_IDS_2026-09-24.md.

Context. The strategy paper calls this tool "IDS Development Studio" and describes it as: "The
dealer explores its actual assessment, chooses a development priority with its distributor,
records milestones with evidence, and sees progress separately from any score. The value is that
the assessment becomes a management tool rather than an archive." Only the assessment half exists
today (the country compare pages). Nothing records what a dealer decides to DO, or whether it moved.
This block builds that half as a real, usable page.

Read first:
- Isuzu Universe\01_Strategy\ISUZU_UNIVERSE_3_0_2026-09-23.md — chapter 2 (the five tools) and
  chapter 7 (how IDS Development Studio is meant to work).
- 02_dashboards\ids\IDS_2026_dealer_compare.html and one country page, to see how a dealer and its
  sections are presented today.
- 01_data\00_derived\ids_dealer_network_cleaned_2026-09-20.csv — inspect the header; the sections
  and scores per dealer live here.
- 04_tools\ids_dealer_ranking\IDS_2026_LOGIC_CHECK.md — the IDS logic and section rules.

Build 02_dashboards\ids\IDS_2026_Development_Progress.html — self-contained, English only,
house look (navy #15233c, terracotta #c0552d, paper #f7f4ee):

1. Pick a dealer (from the assessment data). Show its sections A–E and its standing against the
   country average, so the starting point is visible.
2. A development priority: the dealer (with its distributor) chooses ONE priority from a short,
   fixed list derived from the weakest sections. Store nothing to a server — this is a file.
3. A milestone record: for the chosen priority, a small set of milestones, each with a date, a
   one-line note, and an evidence slot (what was sent, what happened). Progress must be shown
   SEPARATELY from the assessment score — a completed milestone is not a higher score, and the
   page must say that.
4. Progress over time for that dealer on the chosen priority.
5. A printable one-page summary a distributor could take to a dealer meeting.

Two hard requirements:
- The page must be honest about what it does not know: where the workspace holds no milestone
  history, ship the page with the mechanism and an explicit empty state, not invented milestones.
- Because a plain HTML file cannot save data, provide the mechanism explicitly: either a small
  editable table the user fills and prints, or a CSV template plus a "load your filled table"
  file picker that works from file:// (a file input reading a local file is allowed; a fetch is not).
  Say in the page which route it uses.

Then: sibling OPEN_IDS_2026_Development_Progress.cmd (CRLF). Render in headless Chrome and READ
the PNG. Confirm the empty state renders as an explanation, not a blank panel. Report what you
could and could not build from real data.
```

---

## What is deliberately out of scope

- Do not rebuild the 19 existing country compare pages or the Belgium Kaizen page.
- Do not send anything to any distributor, and do not create a scheduled task.
- Do not publish to GitHub Pages.
- Do not change PRISM, the pillar board, or the tender work.

## Done earlier today, do not duplicate

- The pillar board (`02_dashboards\hub\ISZE_UNIVERSE_BOARD.html`) and the universe map
  (`ISZE_UNIVERSE_MAP.html`).
- The weekly R&M tender digest under `04_tools\ISZE_Tender_Monitor_Install\rm_digest\2026-09-24\`.
- Block A: PRISM's tender page now reads the live feed via `modules\tender_feed.py`.

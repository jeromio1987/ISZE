# ISZE exec aftersales paper — paste-ready prompt

**Status:** this file is the **brief**. Ready to paste into a **new** Cursor/Claude session.  
**Do not write the HTML until the current message says `rebuild` or `ship`.**  
**Not on the programme queue:** this is a prompt spec, not a new `ISZE_ROADMAP.md` §1 item.

**Retro (mandatory read before any rebuild):** `00_docs/REVIEW_EXEC_AFTERSALES_PAPER_20260915.md`  
First HTML (2026-09-15) was **audit-grade diagnostic, weak opportunity case**. Rules below close that gap. Cursor rule: `.cursor/rules/isze-exec-aftersales-paper.mdc`. Gate: `python 02_dashboards/_build/verify_exec_aftersales_paper.py`.

**Purpose:** turn a vague “analyse all the Isuzu data, SWOT, 10–20 page HTML” ask into a **Grade A** shared **opportunity + commercialisation** paper that ISZE + IML top management would thank an analyst for — chart-first, money-backed, honest about holes.

**How to use:** paste the fenced block at the bottom into a fresh session with full ISZE repo access. Chat with Jerome in that session stays **internal**. The HTML the later rebuild produces is **shared**. Keep a internal speaker/source annex out of the paper body.

If this prompt is pasted into a session that is already mid-rebuild: **stop and say so**. Do not mix briefs.

---

## What he actually asked (do not dilute)

> So you did a lot of sales analysis, come up with a 10-20 page html with infographics, a paper where you analyze all the data of Isuzu, and do a SWOT analysis? if you have questions ask them first, I want the result as a grade a one analyst, but it should be so good, the top managment would pet you

**Job of this prompt:** force a board-grade **aftersales** paper, not a dashboard dump and not an MBA SWOT.

| Rough phrase | What goes wrong | Grade-A rewrite |
|---|---|---|
| “all the data of Isuzu” | Vehicle, manufacturing, Japan HQ, IAM volume, and the ISZE hub get blended into one mush | **ISZE aftersales parts hub** across the European distributor network. Vehicle wholesale and factory P&L are out unless a cited figure is needed as context. |
| “10–20 page html with infographics” | Chart junk, CDN, `file://` dead, 40 pages of screenshots | **16 ± 4 A4 pages**, print CSS, one story per page, Chart.js **inline**, paints on double-click. |
| “SWOT analysis” | Strengths = “strong brand”. No euros. Unfalsifiable. | Every SWOT cell = claim + € or volume + source + UNKNOWN + what would change a decision. |
| “grade a / top management would pet you” | Adjectives, “insights”, agent slang, two ITUK capture % on one slide | One thesis a managing director can repeat in 12 seconds. Honesty about holes. Decisions, not vocabulary. |
| “ask questions first” | Agent either starts anyway, or pings Jerome overnight | **Phase 0 lives in this file with locked defaults.** Overnight must not ping. A current-message override of one row is allowed. |

**Siblings (do not overwrite):**  
`00_docs/DASHBOARD_CAPTURE_AUDIT_PROMPT.md` (dashboard quality + OEM/IAM scoreboard) ·  
`00_docs/IAM_CAPTURE_PRICE_HUNT_REVIEW_PROMPT.md` (price hunt, not volume) ·  
`00_docs/PROMPT_ACTION_LEDGER_P8.md` (closed-loop euros).  
This prompt **synthesises** those surfaces into one printable paper. It does not reopen AIM 0–100 scoring.

**Proposed later paths (write only after rebuild/ship):**  
`02_dashboards/sales/ISZE_Exec_Aftersales_Paper.html`  
`02_dashboards/sales/OPEN_ISZE_Exec_Aftersales_Paper.cmd`  
internal annex (private, never inside the HTML): `00_docs/SPEAKER_NOTES_ISZE_Exec_Aftersales_Paper.md`

**Grounding (as of 2026-08-25, re-check live):** pipeline verify **116 pass / 0 fail**; `sales_fact` billed through **2026-06-30**. If `_verification_report.json` is not green, **stop quoting headlines**.

---

## This file is the brief

The original ask was: *do a lot of sales analysis, come up with a 10–20 page HTML with infographics, a paper that analyses all the data of Isuzu, and a SWOT — ask questions first — Grade A, good enough that top management would pet you.*

**This session (the one that created or is only editing this markdown) writes the prompt, not the paper.**

A later session that actually builds HTML must see **`rebuild` or `ship` in that session’s current message**. “The prompt exists” is not permission. No `sync_to_deploys`. No version bump. No Outlook Send. No “fix if safe.”

---

## Phase 0 — questions, with locked defaults

The original ask said to question first. Overnight / autonomous runs **must not ping Jerome**. Lock these defaults unless the **current** message overrides one in a single explicit sentence.

| # | Question | Locked default |
|---|---------|----------------|
| 1 | Who is the audience? | **ISZE + IML top management** for the paper (**shared**). Chat + speaker/source annex = **internal** private. No personal names in the paper. |
| 2 | What “all the data of Isuzu” means | **ISZE aftersales commercialisation** across the European distributor network: GPS, PMS **total**, mix, pricing, IDS, tenders, UIO, **gross margin where derived (Eucon/GP)**, **warranty (billed + claim expense)**, and **telematics/subscriptions as a modelled option with a named data gap** (workspace has none — size externally and label, or say “not sized”). **Not** vehicle wholesale, manufacturing, or Isuzu Motors Ltd Japan P&L. |
| 3 | Time window | **CY2025 complete + FY2026 YTD** through last billing (**2026-06-30** if still current). Label partial years. Never annualise YTD into a fake full year. |
| 4 | Geography | **Full network.** ITUK is the **worked example**, not the only row. Never blend Israel. |
| 5 | SWOT entity | **ISZE aftersales** (European parts hub), not Isuzu Motors Ltd Japan. |
| 6 | Length | **16 pages ±4** (stay in 10–20 A4-equivalent). |
| 7 | Language | **English** only in the paper (shared). |
| 8 | Leakage € | **Do not quote unsigned leakage €** in the shared paper. List-to-pocket is unsigned (`DECISIONS.md` 2026-08-25). internal annex may name that the figure exists and is unsigned. |
| 9 | IAM unit share | **Do not invent.** Price evidence ≠ volume. `100% − PMS` is **not** independent-garage share. |
| 10 | Artefact | **Printable self-contained HTML** + sibling `OPEN_*.cmd`. Not PPTX unless the current message asks. |

If a later human message overrides a row, restate the ten-line contract before writing HTML.

---

## Modes (do not mix in one artefact)

| Surface | Mode | Allowed |
|---------|------|---------|
| Chat with Jerome while building | **B** | Nicknames, traps, two ITUK lanes, unsigned leakage, pipeline filenames. |
| HTML paper body, charts, captions, hover panels, print | **A** | Distributor in the room. **IML service schedule** (cite Apr 2026 PMS analysis / trip report / GIDSS / kick-off table). No **IML v7**, **Model B**, **PRISM lane**, personal names, sold-to codes as slide labels, export/blank-% jargon, internal filenames. |
| Speaker/source annex `.md` | **B** | Full lineage, lane names, integrity flags, what was left out. |

A bullet that needs a glossary to land **fails shared** — rewrite it.

---

## Forbidden words (never in shared paper, hover panels, or spoken/written labels to management)

Working labels Jerome banned. JSON/code field names may stay **in the pipeline**; they must not appear in the paper.

| Forbidden | Say instead |
|-----------|-------------|
| wallet / wallet € / parts wallet | **parts billed** vs **target spend per truck** (or max-spend ceiling) |
| street / street fills / street € | **OEM peer retail** / **dealer sell-out price** / **reference sell-out** |
| street index | **price index** (shop ÷ reference sell-out) |
| undercut street | **below our reference sell-out** |
| fill the street | **get OEM peer retail prices** / **complete peer price coverage** |
| Book B (bare) | **Book B (the price list we might change)** |
| `peer_street_eur`, `street_index`, `wallet_eur` as UI labels | keep as code keys only |

**Reference dealer sell-out €** = ISZE list × 1.40 to the dealer × 1.275 to the customer price we compare to shops (= ×**1.785**). First mention in the paper must use that English sentence; the factor may then appear in a footnote.

Kill criterion “forbidden pricing slang” means any of the left-column strings above in shared output (except a one-time filename footnote).

---

## Hard constraints (Grade D if broken)

### Numbers

1. Quote KPIs only from green `01_data/00_derived/_verification_report.json` → `metrics_snapshot.json` → `FACTS.md`. Last known green: **116 pass / 0 fail**, billing through **2026-06-30** (as of **2026-08-25**). If not green: **stop quoting headlines**; name the fail.
2. Never load `01_data/raw/sales/*.XLSX` or `01_data/12_raw/sales/*.XLSX` (or any line-level billing) into context. Derived parquet/CSV only.
3. Never invent KPIs. Decks, memory, and GPT lose to the verify spine.
4. Formulas when editing or explaining a metric: `03_analytics/Isuzu/prism/docs/metric_dictionary.md`.

### Capture, mix, IAM

5. PMS **headline = `line_type=total`**. Genuine is an extra quality lens. Sales is sales. Do not lead with genuine-only.
6. **BVP has no capture rate.** Mix ≠ capture. Show mix as quality of what was sold, not as “we captured BVP.”
7. **Never invent IAM capture %.** Independent-garage **unit volume is UNKNOWN**. Scrapes (Eucon / KS / Autodoc / Part Groups) are **price**, not volume. Coverage of billed book is often thin (Eucon UK 2023: ~38 priced PNs; DB coverage often ~1–17%).
8. **`100% − PMS` is not IAM share.** Residual = IAM + lost service + DIY + other-OEM + export + interval error + parc error. Call it “not sold through ISZE on this basket” if needed.
9. **PMS Best > 100%** — skip the series. Never plot “Best market” when best exceeds 100%.
10. Do **not reopen AIM 0–100 scoring** (closed). No new composite score on this paper.

### Entities (never blend)

11. **UTI sold-to 1799 ≠ UMI sold-to 1797.** Never average or label “Israel” as one IDS-linked number. **IDS Israel = UMI only.** UTI may appear as its **own** row.
12. **IUK customer 2574 ≠ ITUK customer 2575.** Ireland ≠ IUK ≠ IMIE.
13. **Two ITUK PMS lanes are both correct on different denominators** — never mix as “the” capture % (`00_docs/ITUK_PRISM_LANE_BRIDGE.md`):
    - **IML / service-schedule story (external):** oil-filter **35.1%**, gap **€2.04M**, UIO **22,389** (plus any other FACTS §1 figures still listed). Use this as the ITUK worked example in the shared paper (without internal nicknames). **Never** put both lanes in one hero tile.
    - **Network league (internal consistent denominator):** `pms_capture_by_db_year.csv`, bucketed UIO **23,068**. Use this **only** when ranking distributors against each other. shared: call it the **network-comparable capture**, not a pipeline codename.
14. **Shell `5500*` = Shell lubricants** (not bumper “SHELL;”, not Isuzu gear oil). If material, one shared callout; do not hide in UNCLASSIFIED without saying so.
15. GPS / ITUK: ITUK never on kickback or Other DBs tabs; dealer £ ≠ ISZE € target spend (`01_data/91_build/GPS_FILE_LINEAGE.md`).

### Leakage, tenders, closed topics

16. **Leakage € stays internal** until list-to-pocket is signed in writing (`DECISIONS.md` 2026-08-25). The shared paper may say realization is **not yet signed for external quote** — it may not print the unsigned euro as a hero.
17. **Nordics tender API keys are DONE.** Never ask Jerome to register, paste, or re-do Doffin/HILMA keys. If a scrape shows `AWAITING_KEY`, diagnose the loader silently. Coverage gap to discuss = **national portals** (8/29 footprint countries live; rest TED-only below threshold), not keys.
18. Do not re-propose anything in `00_docs/ISZE_ROADMAP.md` §5. Do not add this paper to §1 as new programme work.

### Ship / HTML (when a later session is actually allowed to write)

19. Edit HTML only under `02_dashboards/`. **Never** `07_deploy/`.
20. **No ship without OK.** HTML write only when the executing session’s **current** message says rebuild/ship.
21. Ship gate: **builder exit 0 ≠ done.** `file://` must paint (or sibling launcher). Chart.js **inline**, **no CDN**. Sibling `OPEN_*.cmd`. No `file://` markdown links in chat. Absolute paths in backticks.
22. Empty sections get an **amber banner** (e.g. no sell-out file) — never a blank Top N table.
23. Outlook / email: **draft only**, and only if the current message asks for mail. Never Send.

---

## Grade A bar (what “management would thank you” means)

This is **not** a data dump, not an MBA SWOT, not a dashboard gallery.

A managing director should, after **one scroll of page 1**, be able to say:

> We billed €X against a €Y target-spend ceiling (**and N% of that ceiling is a flat placeholder**). The largest **quotable** category gaps are clutch/brake (€…), not the filter worked example. Gross margin on the contested set is €… / UNKNOWN. Warranty is €… of the book. Here are the ready levers (Book B ambition, no-list PNs, sell-out coverage). Here are the decisions waiting. Here is what would change my mind.

If page 1 needs a glossary, it fails. If SWOT could apply to any OEM, it fails. If two ITUK capture percentages sit next to each other without saying which definition, it fails. If the hero narrative is oil filter while `pms_opportunity_matrix.csv` shows clutch/brake as ~46% of the component gap, it fails.

A Grade A paper also:

1. **Opens with a thesis** a director can repeat in one breath.
2. **Chart-first.** One glance = the story. Tables last, and few. **Chart titles are sentences**, not filenames.
3. Every exhibit has **one sentence** under it: claim + € or volume + source grain (CY vs YTD, which capture definition).
4. **UNKNOWNs are visible**, not smoothed. IAM unit share is a labelled hole, not a residual %. Colour: navy = us, terracotta = gap / ask, green = on plan, amber = unsigned / incomplete, red = integrity stop, grey = UNKNOWN.
5. SWOT cells are **decision tools** (see SWOT contract).
6. Page 14 is a **decision board** from roadmap §2 — asks, not agent nagging.
7. Page 15 lists **what would change our mind** (falsifiers), so the room can disagree productively.
8. Page 16 is a **verify stamp** a sceptic can audit.
9. Small-n: do not rank a distributor on a toy base. Suppress or footnote.

Tone: calm, specific, external-safe. No cheerleading. No “we crushed it.” No pipeline autobiography.

---

## Page architecture (~16 A4-equivalent pages)

Print CSS must treat these as pages (`@page` A4, `break-after: page` on `.paper-page`). Stay inside **10–20**. Cut decoration, not capture / GPS / mix / integrity.

| Page | Title (shared wording) | Must show | Must not |
|------|------------------------|-----------|----------|
| 1 | Cover — one-glance thesis + 4 hero KPIs | Thesis (≤40 words). Four heroes from **green verify** + **quotable opportunity**. At least one hero or callout must name the **top category gaps from `pms_opportunity_matrix.csv`** (clutch disc / brake pad / brake shoe — not oil filter as the opportunity lead). **Disclose** what share of the target-spend ceiling is a flat €250/UIO placeholder (or live equivalent from `wallet_waterfall.csv` `assumption_note`). Hover explainers on each hero. | Pipeline filenames; unsigned leakage as a hero; IAM %; blended Israel; oil-filter as the cover opportunity story while the matrix says otherwise. |
| 2 | How to read this paper | What the numbers **are** / **are not**: PMS total vs genuine; mix ≠ capture; two ITUK definitions exist and this paper uses which, where; Israel is two distributors; IAM volume unknown; YTD is YTD; **ceiling ≠ forecast**; **external GP rates never merge into internal KPI**. | Nicknames; “trust us.” |
| 3 | Parts billed vs target spend | €/truck league, traffic lights if defined, UIO as-of. Keep spend-per-truck separate from workshop cover. Caveats: UMI warranty gap, CR/RE exclusion, partial 2026. **Print the flat-placeholder share and a short sensitivity band** (e.g. non-flat median / Portugal / ITUK ceilings) next to the headline cover %. | ITUK on the wrong tab; blending dealer £ into ISZE €; one blended score; silent 51%-class headline with no placeholder disclose. |
| 4 | Capture — workshop basket + **component gap ranking** | **PMS total first.** Network-comparable table for ranking DBs. **One** ITUK worked example using the IML service-schedule figures (35.1% oil-filter, €2.04M gap, UIO 22,389) — as **method illustration**, demoted vs the **network category gap ranking** from `pms_opportunity_matrix.csv`. Print **gap-type split** from `capture_recovery_model.csv` (substitution / under-service / catalogue) with model vintage labelled. One sentence on IML **1.25 services/yr** vs network **0.5** on filters. | Mixing 35.1% next to 100%/116% as one fact; genuine-only headline; Best series >100%; oil filter as the euro-lead story. |
| 5 | Mix / quality of what was sold | Genuine vs BVP **mix**. Shell `5500*` lubricants callout if material. | “BVP capture %.” |
| 6 | Distributor league | Side-by-side GPS + PMS total + mix. **UTI and UMI as two rows.** IUK ≠ ITUK. State which UMI framing the room should prefer (incl. vs ex-warranty) — not only that both exist. | “Israel” as one IDS-linked average. |
| 7 | Dealer network (IDS) | Dealer score vs **country** average. **IDS Israel = UMI only.** Geo: do not ship country-centre blobs. English labels only. | UTI as the IDS Israel counterpart; Dutch leftovers; Weak-sector radar clutter. |
| 8 | Price vs aftermarket by PN + **margin where known** | On the scraped ∩ billed part set: reference dealer sell-out vs shop, and billed more/less. Name scrapes, vintage, undated share, UK/euro weight. **Gross margin layer** from Eucon (or say UNKNOWN). Surface **NO_LIST** euro / PN count from `pricing_history_findings.json` when present. | Forbidden pricing slang. Country coverage as the main price picture. Unsigned leakage hero. Merging external ATD GP % into verify KPIs. |
| 9 | Demand, replenishment, forecast honesty | Replenishment exceptions as operational fact — report **€ share of GPS billed book** covered by sell-out files, not only row counts. Forecast: median **WAPE** + series count **of denominator** (e.g. 548 of 636); note bias/FVA vs naive as missing if not computed; **G1 unsigned.** Do not over-apologise for ~50% WAPE on intermittent spares. | Presenting forecast as go-live; inventing realised € past billing horizon; “no exception” as network fact when files are missing. |
| 10 | Public tenders / volume | **Live** `tender_data.json` as-of (not a stale snapshot). Portal coverage. Size aftersales honestly: if addressable R&M uplift is tiny vs replenishment leakage, say **relationship/footprint play, not a parts-revenue play**. | Asking for Nordics keys; inventing award €; stale opportunity counts. |
| 11 | Data integrity & UNKNOWNs + warranty / telematics | Integrity flags; IAM **volume hole**; sell-out coverage as **% of billed €**; warranty billed € + claim expense YoY; telematics/subscriptions = modelled option **or** named data gap. Account-health: print `thresholds_calibrated: false` inline when true; defection = recoverable vs zero trailing revenue. | Blank tables; pretending the hole is a chart bug; dropping warranty after one traffic-light sentence. |
| 12–13 | SWOT (two pages) | Four quadrants, **SWOT contract** below. Entity = ISZE aftersales. Ready levers (Book B pack, no-list, sell-out files) ranked by return/effort — not buried. | MBA adjectives with no €; SWOT of Japan; SWOT of “Isuzu the brand” with no source. |
| 14 | What to do in 90 days | Decision board from `00_docs/ISZE_ROADMAP.md` **§2** **plus** ready commercial levers (Book B alloc ambition, no-list owner, DE/BE/PT sell-out). Consequence of no answer. Frame as **asks the room must make**. Do **not** re-ask Nordics keys. Lead with highest return-per-effort already built. | Fake Gantt; “we will fix leakage” without sign-off; ranking Book B fifth while it is the ready price lever. |
| 15 | What would change our mind | 5–8 falsifiers (e.g. IAM unit feed on one family; list-to-pocket sign-off; G1; IML air-factor confirmation; ITUK brake 0.4 vs 0.8; one DB independent sell-out; age-spend curve replacing flat €250). | Moving goalposts. |
| 16 | Sources / as-of / verify stamp | Verify pass/fail, billing max date, which capture definition on which page, file list (filenames **here** only). Label any external-sourced block (telematics, blended GP). | Chat `file://` links. |

Optional internal annex (separate file, only if HTML is authorised): lineage, two-lane math, unsigned leakage pointer, integrity IDs. Never merge into shared HTML.

**Cut order if over 20 pages:** tenders map detail, then dealer map extras, then mix as a full page (keep one mix footnote on capture). **Do not pad** if under 10 — deepen SWOT and the 90-day asks instead.

---

## SWOT contract (pages 12–13)

Not MBA fluff. **Every cell** must contain all four:

1. **One-line claim** (plain English, shared).
2. **Money or volume at stake** with source (file + grain + as-of). If the euro is unsigned (leakage) or missing, the cell says **UNKNOWN** and still states *what* is unknown.
3. **UNKNOWN** explicitly if the evidence is missing, thin, or the wrong grain — do not skip the word.
4. **What would change a decision** (the smallest fact that would rewrite the cell).

| Quadrant | Evidence allowed |
|----------|------------------|
| **Strengths** / **Weaknesses** | **Internal** ISZE evidence only (GPS, PMS total, mix, IDS, sell-out longs that exist, verify, replenishment). |
| **Opportunities** / **Threats** | **External** + competitive + parc + IAM **price** + tenders. Still sourced — or **UNKNOWN**. |

Examples of **fail:** “Strong brand” with no €; “IAM threat 40%” invented; “Opportunity: digital transformation”; blending UTI+UMI as a strength of “Israel.”

Examples of **pass:** “ITUK oil-filter cover on the IML service schedule is 35.1% (UIO 22,389; gap €2.04M; FACTS / Apr 2026 PMS analysis) — UNKNOWN = independent jobs not in the dealer; decision-changer = one family of IAM unit counts.”

Target **3–5 cells per quadrant**, not 12. Rank by € at stake.

---

## Visual system (shared HTML, when authorised)

Match the MD pack / IAM review visual language:

- Navy `#15233c`, terracotta `#c0552d`, paper `#f7f4ee`, ink `#222`. **Georgia** headings. Body a readable serif or clean sans on paper — **never white text on pale**.
- Self-contained HTML. Embed JSON (payload should stay ≲ ~2 MB). **Inline Chart.js (`chart.umd.js`)** — **never CDN**. `file://` first paint must show heroes + charts.
- Print: `@page { size: A4; margin: 14mm; }`. Each architecture page is a `.paper-page` with `break-after: page`. Design for print **and** screen.
- **Chart-first.** One glance = the story. Zero overlapping labels. Colour = meaning (navy = us, terracotta = gap / ask, green / amber / red / grey). Log axes only with forced ticks. **Chart titles are sentences**, not filenames.
- Hover KPI explainers: **CSS panel**, not `title=` only — formula, as-of, what is **not** included.
- Sibling `OPEN_*.cmd` that opens the HTML (`start "" "%~dp0ISZE_Exec_Aftersales_Paper.html"`). Run it in the same turn when building.
- No client changelog / agent build notes in the HTML. No Dutch. Country names in English.
- Sticky headers keep navy + paper contrast.

**Infographic density:** every content page except 2, 15, and 16 has **at least one** chart or visual league. Page 2 is a legend; 15 is falsifiers; 16 is sources.

---

## Source spine (read these; do not glob the repo)

Bootstrap: `INDEX.md` → `00_docs/ROUTING.yaml` (`exec_sales_paper`) → `AGENTS.md`. Then this file.

**Verify + headlines**

- `01_data/00_derived/_verification_report.json` (+ `.md` if needed)
- `01_data/00_derived/metrics_snapshot.json`
- `FACTS.md`
- `03_analytics/Isuzu/prism/docs/metric_dictionary.md`
- `03_analytics/Isuzu/prism/docs/DATA_INTEGRITY_FLAGS_2026-05-28.md`
- `01_data/00_derived/_data_integrity_open_issues.md` (if present)

**Capture / GPS / mix / opportunity**

- `00_docs/ITUK_PRISM_LANE_BRIDGE.md`
- `01_data/00_derived/pms_capture_by_db_year.csv`
- `01_data/00_derived/gps_spu_by_distributor.csv`
- `01_data/00_derived/mix_genuine_bvp_pms.csv`
- `01_data/00_derived/wallet_waterfall.csv` (**read `assumption_note`** — flat €250/UIO share)
- `01_data/00_derived/capture_trajectory.csv`
- `01_data/00_derived/pms_opportunity_matrix.csv` (**must drive category ranking / heroes**)
- `01_data/00_derived/pms_summary_by_db.csv`
- `01_data/00_derived/capture_recovery_model.csv` (substitution / under-service / catalogue)
- `01_data/00_derived/warranty_by_db_year.csv`

**Sell-out / IDS / pricing (price, not IAM volume)**

- Dealer sell-out longs **only where they exist** (ITUK, UTI, Ireland, IUK, Greece) — state **% of GPS billed €** covered
- `01_data/00_derived/eucon_uk_survey_2023_price_gap.meta.json` + `eucon_price_gap.csv` (GP at risk)
- `02_dashboards/pricing/pricing_history_findings.json` (**NO_LIST** euro / PN count)
- `01_data/00_derived/book_b_bucket_summary.csv` + `revision_book_b_pack.meta.json`
- `01_data/01_Pricing/DB_DLR_COMMERCIAL_STACK.md`
- IDS: template `02_dashboards/ids/` — do not score every country clone; Israel = UMI

**Demand / tenders / decisions / health**

- P5 forecast meta / WAPE as published (unsigned G1); prefer bias/FVA vs naive when computable
- `01_data/14_dashboards/tender_data.json` (**live as-of** at build time)
- `01_data/17_interactions/account_health.meta.json` (`thresholds_calibrated`)
- `01_data/00_derived/defection_alerts.csv` (recoverable vs zero trailing revenue)
- `00_docs/ISZE_ROADMAP.md` §2 and §5 (asks + do-not-reopen)
- `DECISIONS.md` (list-to-pocket, Nordics keys done, AIM scoring closed)
- `00_docs/REVIEW_EXEC_AFTERSALES_PAPER_20260915.md` (retro — do not re-ship the same failures)

**Never**

- `01_data/raw/sales/**`
- `07_deploy/**`
- `91_legacy/**` as evidence
- AIM 0–100 classifiers

Existing shared packs are **reference for visual craft**, not sources to copy jargon from: Aftermarket BI Command Center, pricing packs, MD pack capture (check freshness).

---

## Procedure (later session — HTML only if rebuild/ship)

1. Restate the ten locked defaults. Note any current-message override.
2. Green verify. If fail: stop headlines.
3. Pull the source spine. Do not open line-level XLSX.
4. Draft the **thesis + 4 heroes + SWOT claims** in internal chat first (numbers + sources). Do not write HTML yet unless the current message already said rebuild/ship.
5. If — and only if — the current message says **rebuild** or **ship**: write the self-contained HTML + `OPEN_*.cmd` under `02_dashboards/sales/`. internal annex separate.
6. Ship gate on the **rendered** file (not the builder): heroes have numbers; charts exist; no `NaN`; print pages ≈ 10–20; launcher exists; **run** `python 02_dashboards/_build/verify_exec_aftersales_paper.py` (must exit 0); paint check / receipt.
7. Chat reply: **What you should see** (≤3 bullets). Absolute paths in backticks. No `file://` markdown.

If the current message did **not** say rebuild/ship: stop after the internal outline (thesis, hero candidates, SWOT draft, UNKNOWNs). Do not write HTML.

---

## Kill criteria / Grade D examples

Any one of these = **do not claim done**; rewrite.

- Invented IAM % or `100% − PMS` sold as independent share
- Forbidden pricing slang (Forbidden words section) in the paper
- UTI+UMI blend, or UTI as IDS Israel
- Mixing the two ITUK capture lanes as one number
- White text on pale; CDN Chart.js; `fetch()` of sibling JSON as the only path
- Blank tables / empty Top N with no amber banner
- MBA SWOT with no euros and no UNKNOWN
- Pipeline jargon, nicknames, or personal names on shared pages
- Unsigned leakage € as a cover hero
- PMS Best series plotted when best &gt; 100%
- BVP “capture rate”
- Re-asking Nordics keys
- Reopening AIM 0–100
- Claiming done because the builder exited 0, without paint check / verify gate
- PPTX instead of HTML (unless explicitly asked)
- Writing HTML when the current message did not say rebuild/ship
- **Oil-filter (or any filter) as the opportunity hero** while `pms_opportunity_matrix.csv` shows clutch/brake categories as the euro lead
- **Headline cover % without disclosing** flat €250/UIO (or equivalent) placeholder share of the ceiling
- **Computed `pms_opportunity_matrix` / `capture_recovery_model` not shown** as ranking / gap-type split
- **No margin layer and no explicit UNKNOWN** when Eucon/GP files exist
- **Warranty dropped** after a traffic-light aside (must quantify billed share + claim expense YoY, or UNKNOWN)
- **Telematics/subscriptions silence** with no named data gap and no modelled option
- **Stale tender counts** vs live `tender_data.json` as-of at build
- **Sell-out coverage as row counts only** (must state % of billed €)
- **Account-health RED/AMBER without `thresholds_calibrated` flag**; defection “active alerts” without recoverable vs zero-base split
- **Book B pack buried** while unsigned alloc ambition is the highest return-per-effort ready lever
- **External ATD/NADA GP % merged** into an internal verify KPI

---

## Lessons from 2026-09-15 review (vs original brief)

| Topic | Original brief (pre-review) | What the first paper did | What Grade A now requires |
|---|---|---|---|
| Job | Diagnostic parts-hub paper + SWOT | Strong diagnostic | **Opportunity + commercialisation** paper (diagnostic is the annex, not the product) |
| Scope lock | GPS, PMS, mix, pricing, IDS, tenders, UIO | Hit that lock | + **margin**, **warranty**, **telematics sized or named UNKNOWN** |
| Opportunity matrix | Listed in source spine only | Computed €18.22M gap; not on a ranking page | **Must appear** as category ranking; hero follows euro, not the worked example |
| Oil filter | ITUK worked example (correct method) | Also became cover/90-day narrative | Worked example **only**; euro lead = clutch/brake |
| Ceiling | “Target spend / ceiling not forecast” | Hover/SWOT only | **Page 1 + page 3 disclose** flat-placeholder share + sensitivity |
| Gap type | Not required | One residual pool | Print substitution / under-service / catalogue |
| Ready levers | Roadmap §2 asks | Book B in SWOT / late ask | Rank Book B / no-list / sell-out by return-per-effort |
| Tenders | Portal coverage, keys done | Stale snapshot; no aftersales sizing | Live feed; say if channel is footprint not parts € |

Full evidence: `00_docs/REVIEW_EXEC_AFTERSALES_PAPER_20260915.md`.

---

## After the run

- Prompt-only sessions: commit is this markdown + maps. No HTML, no deploy sync.
- Build sessions: shared HTML + internal annex as **two files**. Ship gate on the HTML (`verify_exec_aftersales_paper.py` + paint). Draft-only mail if asked.
- Do not bump version labels without Jerome’s OK.
- Do not add this paper to `ISZE_ROADMAP.md` §1.

---

## Prompt — Grade A exec aftersales paper

```
You are in the ISZE repo (Isuzu Motors Europe, parts hub). Workspace root is
$ISZE_ROOT / the repo root (paths.yaml). Do not hardcode a laptop path.

Read INDEX.md → 00_docs/ROUTING.yaml (task key exec_sales_paper) → AGENTS.md.
Then read 00_docs/PROMPT_ISZE_EXEC_SALES_PAPER.md IN FULL and obey it.
Also read 00_docs/REVIEW_EXEC_AFTERSALES_PAPER_20260915.md and
00_docs/ITUK_PRISM_LANE_BRIDGE.md before any ITUK capture %.

THIS FILE IS THE BRIEF. Do not write HTML until THIS session's CURRENT
message says rebuild or ship. If it does not, deliver a internal outline only
(thesis, four hero candidates with sources, SWOT draft, UNKNOWN register).

Original ask (his words): so you did a lot of sales analysis, come up with a
10-20 page html with infographics, a paper where you analyze all the data of
Isuzu, and do a SWOT analysis; if you have questions ask them first; Grade A,
good enough that top management would thank you.

You already have the questions. Do NOT ask Jerome. Use the locked defaults
in PROMPT_ISZE_EXEC_SALES_PAPER.md Phase 0:

1. Audience = ISZE + IML top management (shared paper); chat + annex = internal.
2. Scope = aftersales commercialisation: GPS, PMS total, mix, pricing, IDS,
   tenders, UIO, gross margin where derived, warranty (billed + claims),
   telematics/subscriptions sized or named UNKNOWN — not vehicle manufacturing
   / Japan P&L.
3. Window = CY2025 complete + FY2026 YTD through last billing (2026-06-30
   if still current). Label partial years. Never fake a full year from YTD.
4. Geography = full network; ITUK = worked example, not the only row;
   never blend Israel (UTI 1799 ≠ UMI 1797; IDS Israel = UMI only).
5. SWOT entity = ISZE aftersales.
6. Length = 16 pages ±4 (stay in 10-20 A4).
7. Language = English.
8. Do not quote unsigned leakage € in the shared paper.
9. Do not invent IAM unit share. 100%−PMS is not IAM.
10. Artefact = printable self-contained HTML + OPEN_*.cmd, not PPTX.

Chat = internal. HTML body = shared (no IML v7 / Model B / PRISM lane /
personal names / pipeline filenames in the paper). Pricing labels =
OEM peer retail / dealer sell-out / reference sell-out / price index
(shop ÷ reference sell-out). Reference sell-out = PR00 × 1.40 × 1.275
(= ×1.785). Obey the Forbidden words section of the markdown.

Verify-green first: 01_data/00_derived/_verification_report.json →
metrics_snapshot.json → FACTS.md. Last known green (re-check): 116 pass /
0 fail, billing through 2026-06-30 as of 2026-08-25. If not green, stop
quoting headlines. Never load 01_data/raw/sales/*.XLSX.

PMS headline = line_type=total. Genuine = extra lens. BVP has no capture
rate. Mix ≠ capture. Skip PMS Best when best > 100%. Do not reopen AIM
0-100. Shell 5500* = lubricants. IUK 2574 ≠ ITUK 2575; Ireland ≠ IUK ≠ IMIE.

Two ITUK PMS lanes (both correct; never mix):
• IML service-schedule story: oil-filter 35.1%, gap €2.04M, UIO 22,389.
  Method illustration only — NOT the opportunity euro lead.
• Network-comparable league: pms_capture_by_db_year.csv, UIO 23,068.
  Use only to rank distributors on one denominator.

Opportunity euro lead = pms_opportunity_matrix.csv category ranking
(typically clutch disc / brake pad / brake shoe). Print gap-type split from
capture_recovery_model.csv. Disclose flat €250/UIO placeholder share of the
ceiling on pages 1 and 3. Margin from Eucon or UNKNOWN. Warranty quantified.
Telematics named gap or modelled+labelled. Live tender_data.json. Sell-out as
% of billed €. Book B alloc ambition ranked as a ready lever. External GP rates
never merge into internal KPIs.

Nordics tender keys are DONE. The gap is national portal coverage, not keys.
Never 07_deploy/. No Send mail. No ship without rebuild/ship in THIS message.

Page map (16): 1 cover thesis + opportunity heroes + ceiling disclose ·
2 how to read · 3 billed vs target + placeholder sensitivity ·
4 PMS total + category gap ranking + gap types + one ITUK method story ·
5 mix/BVP quality · 6 distributor league (UTI and UMI as two rows) ·
7 IDS (UMI for Israel) · 8 price + margin + NO_LIST ·
9 demand/replenishment (% of book) / forecast honesty ·
10 live tenders (footprint vs parts €) · 11 integrity + warranty + telematics
UNKNOWN · 12-13 SWOT · 14 90-day asks + ready levers · 15 falsifiers ·
16 sources/verify stamp.

SWOT: every cell = (1) one-line claim (2) € or volume + source (3) UNKNOWN
if missing (4) what would change a decision. S/W = internal ISZE evidence.
O/T = external/competitive/parc/IAM-price/tender, still sourced or UNKNOWN.

When HTML is authorised: 02_dashboards/sales/ISZE_Exec_Aftersales_Paper.html
+ OPEN_ISZE_Exec_Aftersales_Paper.cmd. Navy #15233c, terracotta #c0552d,
paper #f7f4ee, ink #222, Georgia headings. Inline Chart.js, no CDN.
Print CSS @page A4. file:// must paint. Hover = CSS panel. Chart-first.
Ship gate: exit 0 ≠ done; python 02_dashboards/_build/verify_exec_aftersales_paper.py;
paint check; no blank tables; no file:// chat links.

Grade D if: invented IAM %; forbidden pricing slang; Israel blend; mixed
ITUK lanes; CDN Chart.js; MBA SWOT with no euros; shared pipeline jargon;
unsigned leakage as a hero; oil-filter opportunity hero vs matrix; silent
ceiling placeholder; stale tenders; claimed done without verify + paint.

Output now (no rebuild/ship in this paste): internal outline first — verdict
thesis, four hero KPI candidates with file sources (matrix-led), SWOT 3-5
cells per quadrant in the four-part contract, UNKNOWN register, 90-day asks
from roadmap §2 plus ready levers. Stop. Wait for rebuild or ship.
```

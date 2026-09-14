# ISZE executive aftersales paper — paste-ready prompt

**Status:** brief only. Paste into a **new** Cursor/Claude session. **Do not start the HTML** until (1) Phase 0 answers are locked and (2) Jerome says **rebuild** or **ship**.  
**This file is Mode B** (agent + Jerome). The paper it later produces is **Mode A** (top management).  
**Siblings:** capture audit = `00_docs/DASHBOARD_CAPTURE_AUDIT_PROMPT.md`. IAM price/volume honesty = `00_docs/IAM_CAPTURE_PRICE_HUNT_REVIEW_PROMPT.md`. Do not duplicate those reviews; this paper **uses** their locked conclusions.  
**Outlook:** none. Draft-only if he later asks for a cover mail.

---

## What Jerome actually asked (do not dilute)

> So you did a lot of sales analysis, come up with a 10-20 page html with infographics, a paper where you analyze all the data of Isuzu, and do a SWOT analysis? if you have questions ask them first, I want the result as a grade a one analyst, but it should be so good, the top managment would pet you

**Job of this prompt:** force a board-grade **aftersales** paper, not a dashboard dump and not an MBA SWOT.  
**Job of the session that receives it:** **ask first. Do not start.**

---

## How to use

1. Open a **fresh** session with full ISZE repo access.
2. Paste the fenced block at the bottom.
3. The agent **stops after Phase 0 questions**. It does not write HTML, does not sync, does not bump versions.
4. Jerome answers (or says **lock defaults**).
5. Only a later message that says **rebuild** or **ship** is permission to write the Mode A HTML.

If this prompt is pasted into a session that is already mid-rebuild: **stop and say so**. Do not mix briefs.

---

## Why the rough ask would produce a C paper

| Rough phrase | What goes wrong | Grade-A rewrite |
|---|---|---|
| “all the data of Isuzu” | Vehicle, manufacturing, Japan HQ, IAM volume, and ISZE hub get blended into one mush | **ISZE aftersales parts hub** across the European distributor network. Vehicle wholesale and ISZJ factory are out unless a cited figure is needed as context. |
| “10–20 page html with infographics” | Chart junk, CDN, `file://` dead, 40 pages of screenshots | **16 ± 4 A4 pages**, print CSS, one story per page, Chart.js **inline**, paints on double-click. |
| “SWOT analysis” | Strengths = “strong brand”. No euros. Unfalsifiable. | Every SWOT cell = claim + € or volume + source + UNKNOWN + what would change a decision. |
| “grade a analyst / top management would pet you” | Adjectives, “insights”, agent slang, two ITUK capture % on one slide | One thesis a MD can repeat in 12 seconds. Honesty about holes. Decisions, not vocabulary. |
| “ask questions first” | Agent starts anyway with “sensible defaults” | **Hard stop.** No HTML until answers or an explicit **lock defaults**. |

---

## Phase 0 — questions the executing agent must ask first

Ask these **before any outline, HTML, or SWOT draft**. Number them. Wait. If Jerome says **lock defaults**, use the **Default** column and proceed only after he also says **rebuild** or **ship**.

| # | Question | Why it changes the paper | Default if he says lock |
|---|---|---|---|
| 1 | **Who is in the room?** ISZE management only, or IML / ITUK / a distributor also reading? | Mode A language, which capture lane, what can be shown. | **ISZE + IML top management.** Paper = Mode A. Private annex (sources, lane names) stays Mode B and is **not** in the HTML. |
| 2 | **What entity is the SWOT of?** ISZE aftersales hub, IML aftersales Europe, or “Isuzu” the OEM? | Strengths/threats invert if the subject is Japan vs the European parts hub. | **ISZE aftersales (European parts hub).** Not Isuzu Motors Ltd Japan. |
| 3 | **Time window?** CY2025 complete, FY2026 (Apr–Mar), or YTD through last billing? | Mixing CY and FY is how MDs lose trust. | **CY2025 complete** as the year of record + **YTD through last `sales_fact` billing date** as a clearly labelled extra (last green stamp: through **2026-06-30**). FY only if a figure is already FY in FACTS / PBI. |
| 4 | **Geography?** Full network, ITUK-only deep dive, or “ITUK + 4 peers”? | ITUK is the richest story and the easiest way to fake a network paper. | **Full network league** + **ITUK as the worked example** (IML service-schedule lane). Never blend UTI+UMI. |
| 5 | **May unsigned leakage / list-to-pocket € appear?** | DECISIONS 2026-08-25: leakage € stays Mode B until written sign-off. | **No** in the Mode A paper. Name the *existence* of a pocket gap if needed; **no unsigned €**. |
| 6 | **May we show a SWOT “IAM threat” with a %?** | IAM **price** exists. IAM **unit volume / share is UNKNOWN**. Inventing it is a fireable paper. | **Price evidence allowed. Unit share forbidden.** Write UNKNOWN. |
| 7 | **Print HTML only, or also PPTX / PDF?** | Scope. | **Self-contained HTML + `OPEN_*.cmd` only.** No PPTX unless he asks. Print-to-PDF is his step. |
| 8 | **Length?** 10, 16, or 20 pages? | Padding vs missing the decision page. | **16 pages** (hard floor 10, hard ceiling 20). Cut pages before adding annex charts. |
| 9 | **Language?** | Room. | **English.** |
| 10 | **What must this paper decide?** A 90-day ask list, a FY28 narrative, or a “where we are” briefing with no ask? | Tone of the last two pages. | **Where we are + 5 numbered asks** (from roadmap §2 / FACTS, not invented programmes). |

**If any answer is missing and he did not say lock defaults: stop.** Do not “start a draft so we have something.”

---

## Grade-A bar (what “pet you” actually means)

A managing director should, after **one scroll of page 1**, be able to say:

> “Our parts wallet is €X. We locate about half. The hole is not last-mile on the hero lines we measured; it is trucks that never enter the workshop, categories we under-serve, and an IAM fight we can **price** but cannot **count**. Here are five decisions. Here is what would change my mind.”

If page 1 needs a glossary, it fails. If SWOT could apply to any OEM, it fails. If two ITUK capture percentages sit next to each other without the lane name, it fails.

**Analyst craft (required):**

- Verdict in the **first sentence** of every page.
- Every chart title is a **sentence**, not a filename (`“Air and clutch still carry the ITUK gap €”`, not `pms_by_cat`).
- Colour = meaning (navy = us, terracotta = gap / ask, green = on plan, amber = unsigned / incomplete, red = integrity stop).
- **Unknowns are first-class.** A grey panel “what we cannot say” is worth more than a fake IAM %.
- Small-n: do not rank a distributor on a cell built on a toy base. Suppress or footnote.
- No new 0–100 score. AIM scoring is **closed**.

---

## Hard constraints (executing session)

### Numbers

1. Quote KPIs only after green `01_data/00_derived/_verification_report.json` (`ok`, fail = 0) → `metrics_snapshot.json` → `FACTS.md`.
2. If verify is red: **stop quoting headlines**. Name the fail. Do not paper over with old MD-pack tiles.
3. Never load `01_data/raw/sales/*.XLSX` or `01_data/12_raw/sales/*.XLSX` into context. Derived parquet/CSV only.
4. As-of date on page 1 must match the verify stamp, not “today”.
5. Metric formulas: `03_analytics/Isuzu/prism/docs/metric_dictionary.md`. Integrity: `03_analytics/Isuzu/prism/docs/DATA_INTEGRITY_FLAGS_2026-05-28.md`.

### Entities (never blend)

- **UTI** sold-to **1799** ≠ **UMI** sold-to **1797**. IDS Israel = **UMI dealers only**.
- **IUK** 2574 ≠ **ITUK** 2575. Ireland ≠ IUK ≠ IMIE.
- Two **ITUK PMS** numbers are both correct on **different denominators** (`00_docs/ITUK_PRISM_LANE_BRIDGE.md`):
  - **IML / service-schedule lane (Mode A story):** UIO **22,389**, oil-filter cover **35.1%**, 5-cat gap **€2.04M**, weighted cover **35.9%** — FACTS §1. Use this when the paper is “where we are with IML.”
  - **PRISM network league (internal ranking):** bucketed UIO **23,068**, `pms_capture_by_db_year.csv`. Use this when ranking DBs. **Never** put both in one hero tile.
- PMS headline = `line_type=total` (sales is sales). Genuine / BVP mix is an **extra quality lens**, never the capture that hides BVP.
- **BVP has no capture rate.** Mix ≠ capture.
- Do not plot “Best market” when best **> 100%**. Skip the series.
- **5500\*** = Shell lubricants, not bumper “SHELL;” and not unclassified filler.

### Language (Mode A paper)

- No **IML v7**, **Model B**, **PRISM lane**, sold-to, export, blank-%, loader, `_summary.json`, personal names.
- Say **IML service schedule** and cite the business source (Apr 2026 PMS analysis / FACTS).
- **Forbidden word:** street / street fills / street € / street index. Say **OEM peer retail** / **dealer sell-out** / **reference sell-out** / **price index**.
- Reference sell-out € = PR00 × 1.40 × 1.275 (**×1.785**). Footnote OK.
- JSON field names (`peer_street_eur`, `street_index`) may stay in pipeline footnotes only, never in body copy.

### Money that must not leak into Mode A

- Dealer-leakage / list-to-pocket € until written sign-off (DECISIONS 2026-08-25).
- Invented IAM unit volume or IAM share. Shop quotes are **prices**. Eucon 2023 is **2023 workshop GBP**, not live 2026 retail.
- **100% − PMS ≠ IAM.** Remainder includes deferred jobs and trucks that never enter the dealer.
- New 0–100 scores. Unsigned forecast G1 as a committed plan. P4 RED/AMBER as a call list (draft thresholds).

### Closed topics (do not reopen)

- Nordics tender API keys — **DONE**. Never ask to paste Doffin/HILMA keys.
- AIM 0–100 replacement score.
- “Please send SaTy / Nordics / IAM volume” as a human gate unless there is a **new evidenced** failure.

### Ship / files

- Edit HTML only under `02_dashboards/`. Never `07_deploy/`.
- No silent version overwrite. If a labelled pack already exists, **ask** before a new label.
- Mail: draft only. Never Send.
- Rebuild/ship **only** when the **current** message says rebuild or ship. This prompt file is **not** that permission.

---

## Paper architecture (16 pages ± 4)

Print CSS so each `.page` ≈ A4. One story per page. Hero KPIs only on page 1. Tables earn their place.

| P | Title (working) | Must answer | Infographic (one) | Fail if |
|---|---|---|---|---|
| 1 | **Cover / thesis** | The 12-second sentence + 4 hero KPIs with as-of | 4-tile strip + one thin rule in terracotta | Two theses. Mixed CY/FY in one tile. Lane-free ITUK %. |
| 2 | **How to read** | What the numbers **are** and **are not** (wallet vs capture vs mix vs price vs parc) | Simple stack diagram of layers (UIO → GPS → PMS total → mix) | Pipeline lecture. Mode B nicknames. |
| 3 | **Wallet & GPS** | Parts base €, GPS-facing €, € per truck where SPU is safe | Horizontal SPU bars, ITUK called out, no blend | Raw `sales_fact` total that includes freight/rebate as “sales”. |
| 4 | **Capture** | PMS **total** network + IML service-schedule story as **one** labelled lane | Category gap € (ITUK 5-cat) or network capture vs wallet | Genuine-only headline. Both ITUK lanes as “the” %. |
| 5 | **Mix / quality** | BVP mix as quality, € implication only if FACTS-safe | Mix stacked bars; genuine vs BVP as second lens | “BVP capture %”. Mix sold as the hole. |
| 6 | **Distributor league** | Who is carrying the book; outliers a MD already feels | Small-multiples or ranked table, UTI and UMI **two rows** | One row labelled Israel. IUK labelled ITUK. |
| 7 | **Network / dealers** | IDS / dealer score vs **country** average; Israel = UMI | One clean map **or** ranked dealers — not both cluttered | Country-centre pin blobs. Dutch labels. Weak-sector radar clutter. |
| 8 | **Price & competitiveness** | We can price IAM and OEM peer retail; we cannot count IAM | Price index vs reference sell-out for a **hero PN** with vintage labelled | “Street”. KS £125 hung on the wrong PN. Eucon 2023 as 2026 retail. |
| 9 | **Stock, replenishment, forecast** | What we can run on; honesty on WAPE / unsigned G1 | Exception count + € at stake from **signed** derived files | Forecast as a promise. Seed-€ invention. |
| 10 | **Public volume / tenders** | Where national portals exist; TED-only gap is the issue | Simple coverage map (have / TED-only) — 8/29 is the story | Asking for Nordics keys. Fake award €. |
| 11 | **Integrity & UNKNOWNs** | Flags still live (air factor provisional, brake 0.4 vs 0.8, Q1 SaTy hole, IAM units) | Grey UNKNOWN panel, 5–7 items max | Hiding holes. Integrity score 0–100 as a KPI. |
| 12–13 | **SWOT** | See SWOT contract below | 2×2 with **euros in the cell**, not icons | Generic OEM SWOT. No sources. |
| 14 | **90-day asks** | Five numbered decisions from roadmap §2 / DECISIONS — wording for a human, not an agent ticket | Decision table: ask / if yes / if no | Invented programmes. Nordics keys. “Fix if safe.” |
| 15 | **What would change our mind** | Falsifiers: IML air ratio, brake factor, IAM units, list-to-pocket sign-off, next SAP extract | Short list, one line each | Unfalsifiable strategy poetry. |
| 16 | **Sources** | Verify stamp, files, as-of. Grey, small, complete | Source table | Filenames in the body of pages 1–15. |

**Cut order if over 20:** page 10, then dealer map detail, then mix page (keep one mix footnote on capture).  
**Add order if under 10:** do not pad. Deepen SWOT and asks.

Visual system (Mode A):

- Navy `#15233c`, terracotta `#c0552d`, paper `#f7f4ee`, ink `#222`. Georgia headings, Segoe/system body.
- Chart.js **inline** (`chart.umd.js`) — **never CDN**.
- Self-contained if payload ≤ ~2 MB; else launcher. This paper should **embed**.
- Hover: CSS panel with formula + as-of + **not included** — not `title=` only.
- Zero overlapping labels. No white text on pale. Sticky headers stay navy-on-paper.
- `@media print` + `@page { size: A4; margin: 14mm; }`. Each `.page { break-after: page; }`.
- Proposed path **when rebuild is authorised:** `02_dashboards/sales/ISZE_Exec_Aftersales_Paper.html` + `OPEN_ISZE_Exec_Aftersales_Paper.cmd`. Do not write those files from this brief alone.

---

## SWOT contract (the part that usually embarrasses people)

**Subject:** ISZE aftersales (locked unless Phase 0 says otherwise).

Each of the 8–12 cells (2–3 per quadrant):

1. **Claim** in one sentence a parts director would recognise.
2. **Stake** — € or volume or coverage count, with source file (footnote, not body jargon).
3. **UNKNOWN** — what would make this cell stronger or kill it.
4. **Decision link** — which page-14 ask this supports.

| Quadrant | Must be grounded in | Forbidden |
|---|---|---|
| **S** Strengths | Measured GPS/PMS/sell-out/IDS/tender **haves** (e.g. ITUK pad last-mile closed where measured; green verify; DVLA ITUK parc lane; Nordics portals live) | “Strong brand”, “data-driven”, “AI”, “committed team” |
| **W** Weaknesses | Measured gaps (IML cover, air/clutch €, portal coverage 8/29, unsigned leakage, SaTy hole, forecast WAPE, air factor provisional) | Blaming SAP. Mixing lanes to make a gap look bigger. |
| **O** Opportunities | Addressable **with a denominator we have** (IML gap €, replenishment exceptions, tender coverage we can still wire, mix quality) | IAM “share we will take” without units. Vehicle sales recovery as if it were parts capture. |
| **T** Threats | IAM **price** war on billed hero PNs; parc / ICE window; unsigned price moves; distributor quiet (Early Warning, not draft P4 as gospel) | Invented independent-garage %. KS catalogue miss sold as volume proof. |

**TOWS (required, short):** four arrows only — SO / WO / ST / WT — each pointing at a page-14 ask. No extra framework (PESTLE, Porter, Ansoff) unless Jerome asked.

---

## Canonical inputs (read these, then stop)

Do not recursive-glob. Ignore `07_deploy/`. Prefer ISZE-root numbered folders.

| Need | Path |
|---|---|
| Bootstrap | `INDEX.md` → `00_docs/ROUTING.yaml` → `AGENTS.md` |
| Verify + headlines | `01_data/00_derived/_verification_report.json`, `metrics_snapshot.json`, `FACTS.md` |
| Formulas / flags | `03_analytics/Isuzu/prism/docs/metric_dictionary.md`, `DATA_INTEGRITY_FLAGS_2026-05-28.md` |
| ITUK two lanes | `00_docs/ITUK_PRISM_LANE_BRIDGE.md` |
| PMS league | `01_data/00_derived/pms_capture_by_db_year.csv` |
| GPS | `01_data/00_derived/gps_spu_by_distributor.csv` |
| Mix | `01_data/00_derived/mix_genuine_bvp_pms.csv` |
| OS have/need | `00_docs/ISZE_OS_DATA_MAP.yaml` |
| Queue + asks | `00_docs/ISZE_ROADMAP.md` §1–2, `DECISIONS.md` (newest first) |
| Capture audit (do not redo) | `00_docs/DASHBOARD_CAPTURE_AUDIT_PROMPT.md` |
| IAM honesty (do not redo) | `00_docs/IAM_CAPTURE_PRICE_HUNT_REVIEW_PROMPT.md` |
| Visual precedent | `02_dashboards/md_pack/ISZE_MD_Pack_Capture_FY27_FY28.html` |
| Presentation voice | `.cursor/skills/isze-db-sales-review/presentation.md` |
| Closed: Nordics keys | `.cursor/rules/isze-nordics-keys-closed.mdc` |
| Closed: no ship without OK | `.cursor/rules/isze-no-ship-without-ok.mdc` |

Optional if Phase 0 needs them: sell-out CSVs (ITUK, UTI, Ireland, IUK, Greece only), IDS compare template, tender `01_data/14_dashboards/tender_data.json`, action ledger **Mode B only**.

---

## Explicit DO NOT

- Start the paper in the same turn as Phase 0 questions.
- Invent capture %, IAM units, or a blended “Israel”.
- Use 100% − PMS as IAM share.
- Lead with genuine-only PMS.
- Say “street” in the paper or in conclusions.
- Quote unsigned leakage € in Mode A.
- Re-ask Nordics keys / paste-env sheets.
- Rebuild, `sync_to_deploys`, bump versions, or Send mail from this brief.
- New 0–100, AIM classifier, or “fix if safe”.
- Load line-level billing XLSX.
- Put Mode B nicknames in the HTML.
- Claim done because the builder exited 0. Ship gate + paint check when (later) authorised.

---

## Done line (for the later rebuild, not for this file)

When — and only when — rebuild/ship was explicit:

1. Verify green.
2. HTML paints on `file://` / launcher: hero KPIs numeric, SWOT cells have € or UNKNOWN, ≥1 chart with bars/SVG, sources table filled, no `NaN`.
3. `OPEN_*.cmd` exists next to the HTML; run it or state what is unverified.
4. Reply with **What you should see** (≤3 bullets) from the rendered file.
5. Chat links are dead — tell him to double-click the `.cmd`. Absolute paths in backticks.

Until then, the only acceptable output of a session running this prompt is: **Phase 0 questions**, then silence on files.

---

## Paste-ready prompt

Copy everything inside the fence into a **new** session.

```
You are in the ISZE repo (Isuzu Motors Europe, aftersales parts hub).

Read INDEX.md → 00_docs/ROUTING.yaml → AGENTS.md first. Follow them exactly.
Then read 00_docs/PROMPT_ISZE_EXEC_SALES_PAPER.md in full. That file is the
contract. If this message and that file conflict, the file wins except where
THIS message is more recent on rebuild/ship permission.

============================================================
HIS WORDS (do not dilute)
============================================================
So you did a lot of sales analysis, come up with a 10-20 page html with
infographics, a paper where you analyze all the data of Isuzu, and do a
SWOT analysis? if you have questions ask them first, I want the result as
a grade a one analyst, but it should be so good, the top managment would
pet you.

============================================================
YOU MUST STOP AFTER QUESTIONS. DO NOT START THE PAPER.
============================================================
This turn: output Phase 0 questions only (the table in
PROMPT_ISZE_EXEC_SALES_PAPER.md). Number them. Recommend the Default
column in one line each so Jerome can say "lock defaults" or change one.

Do not write HTML. Do not outline pages in a file. Do not SWOT-draft.
Do not sync_to_deploys. Do not bump versions. Do not send mail.
Do not "fix if safe". Do not load 01_data/raw/sales/*.XLSX.

Permission to write the Mode A HTML exists only if a LATER message in
this session says rebuild or ship AND Phase 0 is locked.

============================================================
WHEN (LATER) YOU ARE ALLOWED TO BUILD
============================================================
Produce a 10–20 page (target 16) self-contained HTML paper,
02_dashboards/sales/ISZE_Exec_Aftersales_Paper.html + OPEN_*.cmd,
print-CSS A4 pages, house colours (navy #15233c, terracotta #c0552d,
paper #f7f4ee), Georgia headings, Chart.js inline no CDN.

Audience: top management. Mode A in the HTML. Chat with Jerome = Mode B.

Thesis test: after page 1 a MD can repeat where the wallet is, what we
locate, what we cannot count, and five asks.

SWOT: ISZE aftersales unless Phase 0 changed the entity. Every cell =
claim + €/volume + source + UNKNOWN + decision link. No generic brand
SWOT. No invented IAM share. No "street" language.

Numbers: green _verification_report.json → metrics_snapshot.json →
FACTS.md. Two ITUK PMS lanes never mixed. PMS total first. UTI≠UMI.
IUK≠ITUK. Leakage € Mode B until signed. Nordics keys closed.
IAM prices ≠ IAM units. 100%−PMS is not IAM.

Follow the page map, SWOT contract, DO NOT list, and ship gate in
00_docs/PROMPT_ISZE_EXEC_SALES_PAPER.md.

============================================================
THIS TURN'S ONLY DELIVERABLE
============================================================
Phase 0 questions. Then wait.
```

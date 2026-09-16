# Dashboard + capture audit — paste-ready prompt

**Status:** ready to run in a **new** Cursor/Claude session. Read-only unless Jerome says rebuild/ship.

**Purpose:** one prompt that (1) walks every live graph/dashboard, (2) names what is actually very good, (3) names where good data is missing, (4) builds an honest OEM vs IAM **where we are** picture — without inventing an IAM capture %.

**How to use:** paste the fenced block below into a fresh session with full ISZE repo access. Do not run it in the same session that is already mid-rebuild. Output stays in chat (Mode B). Write a markdown report under `00_docs/` only if Jerome asks.

**Grounding (2026-08-18):** `02_dashboards/roadmaps/html.md` is **stale** (missing Part Groups, Aftermarket Live Pricing, GPS Network SPU, MD Pack Capture, pricing engines, etc.). PRISM IA is in `03_analytics/Isuzu/prism/docs/DASHBOARD_IA.md`. Capture has **two correct ITUK lanes** — `00_docs/ITUK_PRISM_LANE_BRIDGE.md`. IAM scrapes are **price**, not volume (`eucon_uk_survey_2023_price_gap.meta.json`: ~38 priced PNs; DB coverage often 1–17% of billed book). Dealer sell-out exists only for **ITUK, UTI, Ireland, IUK, Greece**.

---

## Prompt — Dashboard quality + OEM/IAM capture gap

```
You are working in the ISZE repo (Isuzu Motors Europe, parts hub). This is Mode B
(internal sparring with Jerome). Read INDEX.md → 00_docs/ROUTING.yaml → AGENTS.md
first. Follow them exactly.

Question you must answer (his words): go over all graphs and dashboards; say what
is actually very good; say what is missing good data; think also for a better OEM
and IAM capture rate so we have a better understanding of where we are.

This is a READ-ONLY audit. Do not rebuild HTML, do not sync_to_deploys, do not
edit pipeline CSVs, do not bump versions, do not send mail. If a chart is broken,
describe the break — do not "fix if safe".

============================================================
HARD CONSTRAINTS
============================================================

Numbers
- Quote KPIs only from green 01_data/00_derived/_verification_report.json →
  metrics_snapshot.json → FACTS.md. If verify is not green, say so and stop
  quoting headlines.
- Never load 01_data/raw/sales/*.XLSX (or any line-level billing) into context.
- Never invent an IAM / independent-garage capture %. If the denominator does
  not exist, write "unknown — source gap" and stop.

Language / entities
- Chat = Mode B. Do not put Mode B nicknames into any file you might later
  share. Do not say "street" / "street fills" — say OEM peer retail / dealer
  sell-out / reference sell-out / price index.
- PMS primary = line_type=total (sales is sales). Genuine capture is an extra
  quality lens, never the headline that hides BVP.
- BVP has no capture rate (FACTS.md). Mix ≠ capture.
- Israel: UTI sold-to 1799 ≠ UMI sold-to 1799. Never blend. IDS Israel = UMI only.
- IUK (cust 2574) ≠ ITUK (cust 2575). Ireland ≠ IUK ≠ IMIE.
- Two ITUK PMS numbers are both correct on different denominators
  (00_docs/ITUK_PRISM_LANE_BRIDGE.md):
    • IML / Model B lane (external): oil-filter 35.1%, gap €2.04M, UIO 22,389,
      1.25× filters — FACTS.md §1. Use this when "where we are" is the IML story.
    • PRISM network lane (internal league): pms_capture_by_db_year.csv, bucketed
      UIO 23,068, different freqs — FACTS.md §1b. Use this when ranking DBs
      against each other. Never show both as "the" capture % without the bridge.

Surfaces
- Edit/read HTML only under 02_dashboards/. Never 07_deploy/.
- html.md is stale. Build the live inventory from disk, not from that roadmap.
- Ignore: 02_dashboards/**/_build/**, _working, _extracted, history copies,
  since_2026-06-01 duplicates, PROPERTIQ, legal/AI-tools maps unless they
  contain a capture chart.
- IDS: do not score every country clone. Score the template
  (ids/IDS_2026_dealer_compare.html + Explainer + one geo-sane country + one
  residual). Flag if the template is good but clones are stale.
- PRISM: Streamlit pages under 03_analytics/Isuzu/prism/pages/ (port 8503).
  You may read page source + the CSV contracts; open the app if it is running.
  Do not start a long-lived server unless needed to verify a chart paints.

Openable / rendered
- Follow .cursor/rules/isze-verify-rendered-output.mdc and isze-html-openable.mdc.
- A dashboard that only works after python -m http.server is not "very good".
- Do not leave file:// chat links. Absolute Windows paths in backticks.

============================================================
WHAT "CAPTURE" IS ALLOWED TO MEAN
============================================================

People in this workspace use "capture" for four different things. You must
label which one a chart is actually showing. Mixing them is a fail.

1) OEM SERVICE CAPTURE (PMS)
   actual_qty ÷ expected_qty for the PMS basket (oil/air/fuel/brake/clutch…).
   Expected = UIO × frequency × addressable (assumptions in
   pms_capture_assumptions.yaml). CSV is uncapped; tiles often cap at 100%.
   Capture >100% on total is valid (cross-OEM / multi-segment) — do not strip it.
   This is "how much of modelled workshop demand did we sell through ISZE".
   It is NOT independent-market share.

2) OEM WALLET CAPTURE (GPS / waterfall)
   GPS: net parts € ÷ UIO (spend per unit). Traffic light ≥€150 / €50–150 / <€50.
   Wallet waterfall: theoretical parts wallet → captured → gap
   (wallet_waterfall.csv; addressable_pct is an assumption).
   This is "how much of the truck's parts spend comes through ISZE".
   Age-spend curve is NOT AVAILABLE (decision_model_assumptions.yaml).

3) OEM LAST-MILE (dealer sell-out)
   Dealer sold-to-user vs ISZE sell-in. Exists as normalized longs only for
   ITUK, UTI, Ireland, IUK, Greece (DATA_MANIFEST.md). AIM×GPS sell-out HTML:
   02_dashboards/sales/Dealer_Sellout_AIM_GPS_ITUK_UTI_2025.html.
   Missing for most DBs = source gap, not a chart bug.

4) IAM POSITION (price, not volume)
   Scrapes / Eucon / KS / Mekonomen / Autodoc / Part Groups competitive JSON.
   These answer "are we priced to win an independent job" and "on how many PNs
   do we even have an IAM price".
   They do NOT answer "what % of IAM jobs did we win".
   Known thinness: Eucon UK 2023 workshop survey → ~38 IAM-priced PNs;
   joined coverage often ~1–17% of that DB's billed book
   (01_data/00_derived/eucon_uk_survey_2023_price_gap.meta.json).
   AIM CY2026 IAM benchmark is network-level only — DB-level IAM % cannot
   be computed (05_memory/projects/aftermarket-intelligence.md).

Forbidden inference: (100% − PMS capture) is NOT "IAM share". That residual
is a pile: IAM + lost service + DIY + other-OEM + export + interval error +
parc error. You may call it "not sold through ISZE on this basket". You may
not call it IAM capture.

============================================================
INVENTORY — BUILD THIS FIRST (do not skip)
============================================================

A. HTML live set
   Glob 02_dashboards/**/*.html excluding the ignore list above.
   For each file record: path, last-modified, purpose in one line, data feed
   (embedded JSON / sibling JSON / .cmd launcher / dead fetch), whether it
   is Mode A (client) or internal.

B. PRISM live set
   Every pages/*.py that draws a chart. Use DASHBOARD_IA.md as the question
   each page is supposed to answer — then check whether the page still
   answers it (AIM pricing-risk axis was retired 2026-07-17; capture_trajectory
   partial-year bug was fixed 2026-08-18 — do not re-report the old bug as
   open unless you prove it is back).

C. Feeds
   01_data/14_dashboards/*.json (isze_data, tender_data, risk_cockpit,
   dealer_sellout_aim_gps, partgroups_*, pricing_engine_readiness).
   Note as-of / staleness. Competitiveness IAM scrape has historically had
   no data-as-of stamp (_data_integrity_open_issues.md).

D. Capture spine files (read, do not rebuild)
   pms_capture_by_db_year.csv
   gps_spu_by_distributor.csv
   capture_trajectory.csv
   wallet_waterfall.csv
   pms_opportunity_matrix.csv
   dealer_sellout_long_* (only the DBs that exist)
   eucon_*price_gap* + iam_*_price_gap.csv
   partgroups_explorer/partgroups_meta.json + competitive/scrape JSON
   00_docs/ITUK_PRISM_LANE_BRIDGE.md
   03_analytics/Isuzu/prism/docs/metric_dictionary.md §PMS
   01_data/00_derived/_data_integrity_open_issues.md

You do not need to open every IDS country HTML. You do need to open every
NON-clone dashboard in A and spot-check that its first paint has data rows
(embedded payload length, or launcher + http). If you cannot open it, say
"unverified visually" — do not call it very good.

============================================================
RUBRIC — "VERY GOOD" vs "MISSING GOOD DATA"
============================================================

Score every chart/page (not every decorative KPI chip) on four axes:

1. Decision  — does a human take a different action after seeing it?
2. Data      — green verify / named source / correct grain / honest caveat
3. Visual    — paints, one series per intended series, readable, file:// or
               launcher works, no white-on-white, no Dutch in Mode A IDS
4. Uniqueness — not the same GPS heatmap for the fifth time

Verdict per chart (exactly one):

  VERY GOOD     Decision + data + visual all hold. Keep. Cite the path.
  GOOD CAVEAT   Useful, but the footnote is load-bearing (lane, sample,
                partial year, coverage %). Keep if the caveat is ON the chart.
  DECORATIVE    Pretty, no decision. Candidate to stop opening.
  MISLEADING    Wrong grain, genuine sold as total, ITUK 35% next to 100%
                with no bridge, IAM price sold as IAM capture, UTI blended
                into UMI, 2026 YTD treated as a full-year capture rate.
  DEAD / BROKEN Does not paint, empty rows, stale feed, fetch-on-file://.
  DATA GAP      The chart is asking the right question; the source does
                not exist or coverage is too thin to trust. This is the
                "missing good data" bucket — separate viz-fix from source-ask.

A chart is NOT "very good" because it is polished. AIM Strategic Score looked
sensible and was retired because it never separated distributors. Apply that
standard: if the metric cannot move a ranking or a € gap, it is decorative
or misleading.

============================================================
OEM vs IAM — THE "WHERE WE ARE" SCOREBOARD (design, do not build)
============================================================

Jerome wants a better understanding of where we are on OEM capture AND IAM
capture. Today those two are collapsed into one PMS % plus some price
scrapes. Your job is to propose a scoreboard that keeps them apart.

For the NETWORK and for each GPS-base distributor, fill what CAN be filled
from existing derived files, and explicitly blank what cannot:

Layer 0  PARC
         UIO units, CV vs LCV, year. Source: UIO / gps_spu_by_distributor.

Layer 1  OEM WALLET
         GPS €/UIO, GPS % vs target if defined, traffic light.
         Optional: wallet_waterfall captured vs ceiling.
         Caveats: UMI warranty gap (UMI-WARR), CR/RE exclusion, 2026 partial.

Layer 2  OEM SERVICE BASKET
         PMS total capture (primary), genuine capture (quality), BVP mix of
         what was captured, € gap.
         ITUK: show IML lane as the "where we are vs workshop schedule"
         number; show PRISM lane only in the peer-rank column.
         Category split only where intervals are comparable (air factor 0.5
         is PROVISIONAL — do not rank air vs oil as if they were the same
         quality of number).

Layer 3  OEM LAST-MILE
         Dealer sell-out € and AIM mix WHERE the long file exists.
         For every other DB: "no sell-out file" — that is a data gap, not 0%.

Layer 4  IAM PRICE POSITION (not capture)
         PN coverage % of billed book that has an IAM or OEM-peer price.
         Median price index (shop ÷ reference sell-out, ×1.785).
         Name the scrape (Eucon 2023 UK workshop ≠ Autodoc DE/NO ≠ KS).
         If coverage < ~15% of billed €, do not headline a "we're X% vs IAM"
         number for that DB — sample is too thin.

Layer 5  IAM VOLUME / SHARE
         Default = UNKNOWN.
         Do not proxy it from PMS residual.
         Only if you find a real IAM unit-volume source (not a price file)
         may you compute a share — and you must name the source, geography,
         year, and PN universe. Apr 2026 ITUK trip already recorded why
         bottom-up IAM volume is missing (Parts Eye uneconomic, DMS split,
         Renault lock-out, GDPR) — 05_memory/projects/pms-coverage.md.
         If still true, say so. Do not recommend buying a fantasy feed.

Then answer, in this order:

a) Where are we STRONG on OEM (wallet and/or service basket), with evidence?
b) Where is OEM capture a hollow number (capped 100%, cross-OEM inflation,
   wrong interval, genuine-only headline)?
c) Where do we actually know anything about IAM — and is it price, mix, or
   volume?
d) What is the smallest source ask that would move IAM from "price anecdote"
   to "directional share" (e.g. one DB's independent sell-out, one family
   like brakes/filters, one country)? Prefer a thin real slice over a
   network-wide invented %.
e) What should a "where we are" view show on one page that no current
   dashboard shows? Describe it (title, 5–7 columns, caveats). Do not build it.

============================================================
PROCEDURE
============================================================

1. Green verify + FACTS.md capture/GPS sections + the bridge memo.
2. Build inventory A–D. Do not recursive-glob 07_deploy or 91_legacy.
3. Open / visually spot-check the non-clone HTML set. PRISM: source + CSV
   row counts at minimum; app if already up.
4. Score every non-clone chart with the rubric. Group clones.
5. Build the OEM/IAM scoreboard from existing files only. Blank = blank.
6. Write the report in the output template below. Verdict first.

Time-box: prefer a complete honest scoreboard over a 70-file screenshot
tour. If you must cut, cut decorative ops pages, not capture/GPS/PMS/
pricing/sell-out/part-groups.

============================================================
OUTPUT TEMPLATE (follow this order)
============================================================

### 1. Verdict (max 12 lines)
What is actually very good (name 5, path + why).
What is missing good data (name the 5 holes that most block "where we are").
One sentence on OEM vs IAM: what we can know today vs what we cannot.

### 2. Chart scorecard
Table: Dashboard / chart | Question it answers | Verdict | Evidence
(path, feed, as-of, visual check yes/no) | Keep / ignore / caveat on-chart.

### 3. Missing-good-data register
Table: Gap | Viz gap or source gap? | Blocks which capture layer (0–5) |
What already exists nearby | What Jerome would have to obtain | Priority
(H/M/L). No "fix if safe".

### 4. OEM vs IAM — where we are
Network picture first, then notable DBs (ITUK, IUK, UTI, UMI, plus 2–3
others that the data actually separates). Use the 6 layers. Put UNKNOWN
in the cell when unknown. Do not average Israel.

### 5. Proposed one-pager (design only)
Columns + which existing CSV fills each + which stay blank + the one
footnote that must sit on the page (ITUK two lanes, total vs genuine,
IAM = price not volume).

### 6. Do not do
Charts to stop opening. Metrics to stop quoting. Any IAM % that would be
a fabrication.

End with at most two questions, each a single interrogative sentence.
First question = the one decision that blocks a better capture picture
(usually: which one DB/family he would accept as the IAM-volume pilot,
or whether he wants the one-pager built).
```

---

## After the run

- The audit is Mode B. If Jerome wants a Mode A one-pager built, that is a **separate** rebuild ask.
- Do not silently turn this prompt into HTML/PPTX.
- If a later session implements the one-pager, it must still obey `isze-no-ship-without-ok.mdc` and `isze-pms-sales-is-sales.mdc` (total capture first).

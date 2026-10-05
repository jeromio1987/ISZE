# Mega prompt — review and upgrade the ISZE tender tools

**What this file is.** A single prompt to paste into a fresh Claude chat. It is written to
Claude, in the second person. It carries everything Claude needs to work on the ISZE tender
tooling without asking you to re-explain the workspace.

**Who wrote it.** A Cursor session in the ISZE workspace, on 1 October 2026, after reading the
files named below. Every number in it was measured from a named file on that date. Where a number
in an earlier brief was wrong, the correction is stated in §2.9.

**How to use it.** Paste the whole file. Then answer only the questions in §7. Nothing else should
need explaining.

---

## 0. Before you touch anything

You are Claude, working on Jerome's ISZE pricing workspace. Jerome is ISZE pricing, Sales —
Vehicle Parts. He sells and prices Isuzu parts through a network of distributors (Isuzu UK pickup,
Isuzu Truck UK, UMI and UTI in Israel, and a European distributor network). He talks plain
business English and dislikes internal shorthand.

Read these files before you form an opinion. They are the contract between you and the rest of the
workspace:

| What it decides | File |
|---|---|
| Which words you may not use | `C:\Users\jerom\Desktop\claude\ISZE\.cursor\rules\isze-spoken-labels.mdc` |
| How to write to Jerome | `C:\Users\jerom\Desktop\claude\ISZE\.cursor\rules\jerome-talk-clear.mdc` |
| How to brief Jerome | `C:\Users\jerom\Desktop\claude\ISZE\.cursor\rules\jerome-brief-plain.mdc` |
| Permission to rebuild or ship | `C:\Users\jerom\Desktop\claude\ISZE\.cursor\rules\isze-no-ship-without-ok.mdc` |
| What a gap must carry | `C:\Users\jerom\Desktop\claude\ISZE\.cursor\rules\isze-gaps-need-context.mdc` |
| How an HTML file must open | `C:\Users\jerom\Desktop\claude\ISZE\.cursor\rules\isze-html-openable.mdc` |
| What "done" means for shared HTML | `C:\Users\jerom\Desktop\claude\ISZE\.cursor\rules\isze-ship-gate.mdc` |

There is one hard rule above all of these and it overrides everything else in this prompt:
**do not rebuild, regenerate, overwrite or ship anything until Jerome's current message asks you
to.** Investigation, measurement, reading and writing a plan are always allowed. Writing over a
file that other pages read is not.

---

## 1. What the tender programme is, in plain terms

ISZE sells Isuzu parts. A large part of the European demand for those parts sits inside public
fleets — councils, utilities, hospitals, education boards, road authorities — because those
organisations buy light commercial vehicles and trucks in groups, and then repair them for years.

When such an organisation buys vehicles, or buys a repair-and-maintenance contract, it usually has
to publish a tender. "Tender" and "notice" mean the same thing here: one published announcement.
The European Union runs one official journal for above-threshold notices, called **TED** (Tenders
Electronic Daily). Most **below-threshold** business — the smaller national contracts — never
appears on TED. It appears only on each country's own portal: BOAMP in France, PLACSP in Spain,
and so on. The file
`04_tools\ISZE_Tender_Monitor_Install\_COUNTRY_TENDER_PORTALS_MAP.md` maps all 29 markets.

The commercial point, and the reason this programme exists: **the vehicle sale is the small part**.
A fleet of eight tippers bought this year generates ten or fifteen years of filters, brakes,
clutches and service parts. If a competitor's dealer wins the contract and runs the workshop, we
lose the parts for the life of the fleet. If one of our dealers runs it, we keep them. So the
number that matters on any tender is not the contract value; it is **the parts value of the fleet
behind it**.

Two things follow, and both are already written into the tooling:

1. A tender matters when it is about **vehicles we actually sell** (the D-Max pickup and the
   N-Series truck/chassis-cab shape) or about **repair and maintenance of those types**. It does
   not matter when it is a postal service buying panel vans, which is handled by the "not for us"
   gate described in §5.5.
2. A tender's value must be expressed as **parts demand over the fleet's life**, not as the
   headline contract value. Where we cannot size the fleet, the honest answer is "not sized", not
   a made-up number.

The programme has three pieces today:

- a **scraper** that collects notices from 30 sources weekly;
- a **scoring engine** that decides which notices matter and how much, and writes one live feed
  file that everything else reads;
- two **dashboards** and a **weekly distributor list** built from that feed.

Jerome has decided (24 September 2026, recorded in `00_docs\TENDER_OUTCOME_DESIGN_2026-09-24.md`)
that the network should answer one question a week per distributor, and that outcomes should be
recorded so that in a year we can say what we actually win.

---

## 2. The current state, with real numbers

Every number in this section was measured by reading the file named beside it on 1 October 2026.
Do not copy a number from this prompt into a deliverable without re-measuring it — the feed is
rebuilt weekly and the numbers move.

### 2.1 The live feed

`01_data\14_dashboards\tender_data.json`, 4,997,699 bytes, written 28 September 2026 07:51.
`01_data\dashboards\tender_data.json` is a junction to the same folder — both paths resolve to
byte-identical files (sha256 `b6f3ffc784f1d8e3...`).

- 735 notices; 664 opportunities. An **opportunity** is one tender after the duplicates from
  different portals have been merged; a notice is one portal's copy of it.
- 29 countries in the feed.
- Each notice carries **72 fields**; each opportunity carries **72 fields**, with different names.
  Field lists are in §6.1 and §6.2.
- `meta.generated_at` = `2026-09-28T05:51:57.598166Z`.

### 2.2 The scraper workbook, and the shortest route to a rebuild

`04_tools\ISZE_Tender_Monitor_Install\isuzu_tenders_v3.xlsx`, written 28 September 2026 07:51,
18 sheets, **735 rows in total** — exactly the 735 notices in the feed, which is the proof that
this workbook is the feed's only input.

This matters more than it looks. To rebuild the opportunity dashboard on the data already on disk,
you do **not** need to scrape anything:

```
python build_dashboard_v4.py            (with isuzu_tenders_v3.xlsx present)
```

or, if you want to hand it the feed directly, `load_payload()` in `build_dashboard_v4.py` accepts
an input path or a JSON input argument. Re-scraping is a separate, network-dependent job and is
explicitly out of scope for this work (§4).

### 2.3 Scoring, triage and the vocabulary that already exists on every row

The engine lives in `isze_core_v3.py` (2,026 lines, 48 functions) and `tender_scraper_v3.py`
(3,676 lines, 61 functions). Every opportunity already carries:

| Field | Values seen in the 28 September feed | Meaning |
|---|---|---|
| `fit_score` | 0–100 | how well the notice matches Isuzu's products |
| `win_score` | 10–90 | how winnable it looks |
| `econ_score` | 16–76 | how much money is behind it |
| `opportunity_score` | weighted combination | the sort key |
| `decision` | `Attack` 6, `Selective` 192, `Watch` 88, `Ignore` 378 | the triage call |
| `tier` | `large` 18, `medium` 6, `small` 10, `micro` 5, `unknown` 625 | size band |
| `urgency` | `critical` 38, `soon` 31, `ok` 33, `none` 528, `expired` 34 | deadline pressure |
| `lifecycle` | `unknown` 462, `competition` 132, `result` 67, `planning` 2, `change` 1 | where the tender stands |
| `evidence_score` / `evidence_label` | `High` 141, `Medium` 554, `Low` 40 | how good the source text is |
| `owner_suggested` | ten regional leads, e.g. `CEE Lead` 216, `DACH Lead` 198 | who should look at it |
| `status_suggested` | e.g. `Enrich`, `Watch` | the first workflow step |
| `next_action_suggested` | free text | one suggested action |
| `score_drivers` | list of short reasons | why the score is what it is |
| `product_segment` | `rm_only` 223, `truck` 178, `weak` 150, `pickup` 109, `lcv_van` 4 | what the notice is really about |
| `rm_contract` | true on 274 of 664 | repair and maintenance contract |
| `parts_signal` | true on 282 of 664 | parts language found in the text |
| `aftersales_tags` | non-empty on 336 notices | which aftersales angle matched |

Two of these matter enormously and are easy to overlook. `owner_suggested` already assigns every
single one of the 664 opportunities to a named regional lead — there are **no unassigned rows**, and
`meta.owner_options` also lists `Strategic Accounts` and `Bid Desk`. And `status_suggested` gives
each row a first workflow step. So the triage machinery is already there. What is missing is a
place where a person can see it as a list of jobs, and a record of what happened.

The opportunity lifecycle counts are not on the notice layer: `notices[].Lifecycle` carries
`unknown` 526, `competition` 138, `result` 68, `planning` 2, `change` 1, while
`opportunities[].lifecycle` carries the lowercase version of the same idea. Do not mix the two
field names; capital `Lifecycle` is a notice field.

### 2.4 The dashboards, and which one you should care about

**v4 — `isze_dashboard_v4_opportunity.html`, 1,842,371 bytes, 5 tabs.** This is the good one. It is
fully self-contained: the whole set of rows sits inline as `const DATA = {...}` on line 712 of the
HTML, there is no `fetch()` of a sibling file, so it opens correctly by double-clicking. Tabs are
`Opportunities`, `How tenders work`, `By market`, `Sources / health`, `Method / scoring`,
`Export / Data sheets`. Its launcher `OPEN_isze_dashboard_v4_opportunity.cmd` is 63 bytes, CRLF,
and correct. Its builder is `build_dashboard_v4.py` (105,610 bytes); it also writes
`isze_dashboard_v4_data.json` (4,849,213 bytes) and `isze_dashboard_v4_opportunities.xlsx`
(97,075 bytes).

**v2 — `isze_dashboard_v2.html`, 1,942,082 bytes.** Still built weekly and still opens, but it is
a worse experience: try/catch around `fetch('isze_dashboard_v2_data.json')` on line 595 and an
explicit code comment saying it expects a local server, plus `const DATA` with an empty `notices`
array so the page is thin when opened as a file. **Treat v2 as the legacy view.** Unless you find
a reason to keep it, the review should recommend keeping it untouched and not investing in it. Its
sibling `isze_dashboard_v2_data.json` is 4,997,699 bytes — the same size as the master feed,
because it *is* the master feed.

**An inline hint that is now stale.** Line 692 of the v4 HTML tells the reader "Wire next: ES WAF".
Spain has since been wired — 39 ES-PLACSP notices are in the feed and `_source_health.json` reads
ES PLACSP `OK`. Line 692 also names the right detail counts for its own build date, so if you
touch this page, fix that line rather than deleting it.

**Older dashboards in the same folder** and the existing SteerCo pack
(`09_meetings\Tender_Engine_SteerCo_20260826\`) are frozen at August/28 September numbers. The
SteerCo HTML prints **326 notices / 291 opportunities / 174 stated fleet**. The live feed today is
735 / 664. Do not quote the pack as current, and do not refresh it as part of this work unless
Jerome asks.

### 2.5 The parts-demand field, and how thin it is

Some notices carry `pms_demand_by_category`: a list of 14 rows, one per parts family, each with
`pms_category`, `category_label`, `expected_qty`, `addressable_eur`, `avg_sp_eur` and `year`. The
14 families are oil filter, fuel filter, air filter, urea filter, blower filter, brake pad, brake
shoe, clutch disc, clutch pressure plate, clutch kit, release bearing, pilot bearing, clutch
booster and brake rotor.

Measured on the 28 September feed, **and re-verified 1 October 2026 after an earlier reading
made stronger claims than the data supports**:

- **13 of 735 notices** carry it, on **11 distinct opportunities** of 664.
- Those 13 notices **do** carry a distributor_code — Ireland one, Germany eleven, Portugal one.
  An earlier version of this prompt said the column was empty on every one; it is not.
- Triage is **not** uniformly `Ignore`: ten are `Ignore`, two `Watch`, one `Selective`. The
  earlier claim that all of them were `Ignore` was wrong.
- **1 of the 11** appears in the 28 September weekly digest, not none. The digest has 114 rows.
  So the parts-demand set is *nearly* absent from the distributor list, which is worth
  investigating, but it is not excluded by construction.
- The named parts families are filters, brakes and clutch only. Cab and body parts, electrical,
  engine, cooling and steering have no expected-quantity model at all, because the maintenance
  frequency data behind the model covers those families.
- Here is what a demand row actually looks like, from the Irish notice: oil filter, expected
  quantity 0.87, addressable €8.20, our average selling price €9.44. A fleet size of 1 produces
  under one oil filter a year. The arithmetic is right; the fleet is simply too small to matter.

So the one field that turns a notice into a parts business case exists on 2 per cent of the book
and is almost never on the distributor list. Whether the demand model simply does not cover small
fleets, or the field is dropped on a path most notices never take, is **not established** — this
prompt asks you to measure that rather than assume it. What is certain is that the field is thin,
and that thinning it further by assumption would hide the parts case entirely.

### 2.6 The joint between tenders and parts prices, built today

`01_data\00_derived\tender_price_context.csv`, 42,252 bytes, written 1 October 2026 18:09, with a
sibling `.meta.json`. Its builder is
`04_tools\aftermarket_intelligence\build_tender_price_context.py`.

What it does: it takes each notice that has parts demand, maps each parts family to **our** part
numbers that sit in that family, and asks whether any of those part numbers carries an observed
competitor price. Then it reports the coverage.

Measured:

- **182 rows**, keyed on parts family: 11 distinct opportunities × 14 families, two opportunities
  carrying two rows per family, which is why 182 is not 154.
- **3 countries only**: Germany, Ireland, Portugal.
- **156 rows (85.7%) have at least one observed rival price.**
- Coverage per row runs **0% to 33.3%**, median **2.59%**. Nothing reaches 50%.
- 345 observed part numbers in total; **156 rows carry a usable rival price**.
- Sum of `addressable_eur` across all 182 rows: **€262,384.56**.

Interpretation, and say it this way to Jerome: on the parts families these eleven tenders
generate, we can currently price-benchmark between one part in a hundred and one part in three
against a rival. The rest of the comparison is blank, and blank must never be drawn as "no
competitor". The file's own `honest_note` says exactly this; quote it rather than inventing a
softer version.

The joined price source is `01_data\00_derived\price_observations.parquet`, with its
`.meta.json` recording 1,866 rows, of which 359 distinct Isuzu part numbers carry an observation.
The builder deliberately excludes modelled and our-own-value price types, keeping only
`aftermarket_retail`, `aftermarket_trade`, `genuine_grey`, `online_median`, `marketplace`,
`dealer`, `quote`, `survey_workshop` and `survey_list`.

### 2.7 The weekly distributor list

Built by `build_rm_digest.py` (32,913 bytes, written 24 September) into
`04_tools\ISZE_Tender_Monitor_Install\rm_digest\<date>\`. The run switched on in the weekly batch
on 25 September (the batch file's timestamp is 25 September 06:54; the log's last completed run
was 28 September 07:52).

Selection rule, from the builder's own docstring: `rm_contract == true` **and** `decision in
(Attack, Selective, Watch)` **and** (deadline on or after the run date **or** no deadline at all).

The last run's own report, `rm_digest\2026-09-28\_run_report.json`:

- 664 rows in the feed → 274 with `rm_contract` true → 240 actionable → 223 selected.
- 33 have a deadline, 190 do not, and 109 of the 223 have **no distributor_code** and go to an
  internal page.
- Ten distributor pages plus one internal unassigned page.

| Distributor (page name) | dated | undated | total |
|---|---:|---:|---:|
| ROM Auto (Romania) | 10 | 33 | 43 |
| IBX (Belgium) | 6 | 7 | 13 |
| RUTEBILEIERNES STANDARDISERING AS (Norway) | 5 | 3 | 8 |
| IMOTORS (Portugal) | 4 | 7 | 11 |
| ISUZU SALES DEUTSCHLAND GMBH | 1 | 18 | 19 |
| Ireland | 1 | 2 | 3 |
| AutoWallis (Hungary) | 0 | 10 | 10 |
| RSA (Greece) | 0 | 5 | 5 |
| ISUZU TRUCK (UK) LIMITED | 0 | 1 | 1 |
| Sverige | 0 | 1 | 1 |
| **UNASSIGNED (internal)** | **6** | **103** | **109** |
| **Total** | **33** | **190** | **223** |

Each distributor page is self-contained HTML with an `OPEN_RM_DIGEST.cmd` beside it, CRLF; there is
a `README_IMPORT.md` explaining the one-word answer, a screenshot set under `_qa\`, and a
`_run_report.json` that scans every distributor page for banned internal terms and reports **0
hits on all ten**.

Two things to notice, and both are design decisions rather than defects:

- The digest reads `opportunities`, never `notices`, so nothing from `pms_demand_by_category` can
  reach it. That is why the intersection above is empty.
- The CSVs carry a `status` column as well as an `outcome` column for the same word; the loader
  accepts either. The design memo in §2.8 says the `status` column should be declared unused.

### 2.8 The outcome record, built and empty

`tender_outcomes.py` (14,567 bytes) plus `tender_outcomes.json`. The store file is **39 bytes**:

```json
{
  "version": 1,
  "outcomes": {}
}
```

Zero outcomes. `meta.outcomes_summary` in the live feed reads `recorded: 0`, `decided: 0`,
`won: 0`, `lost: 0`, `closed_sample: 0`, `win_rate_display: "insufficient data"`.

The module itself is more careful than its emptiness suggests, and you should not rebuild it
without reason:

- It maps every plausible word onto six canonical values: `pursue`, `pass`, `no decision`, `won`,
  `lost`, `withdrawn`. Twenty-two aliases are listed, so `bid` counts as `pursue` and `no-bid`
  counts as `pass`.
- An unrecognised word is stored as written and surfaced under `unrecognised_statuses`, so nothing
  disappears quietly.
- It keeps two different questions apart on purpose: `engaged` (`pursue` + `pass`) answers "did
  anyone read the list?", and `decided` (`won` + `lost` only) answers "what is the result?". A win
  rate is withheld until won + lost reaches **20**, below which it prints `insufficient data`.
- It has a dry-run mode that does not even create the file, so a dry run cannot cause the thing it
  promised not to do.

Note a version mismatch to check rather than assume: the file on disk says `"version": 1`, while
the module's `EMPTY_STORE` constant says `"version": 2`.

The design that should fill this store is written up in
`00_docs\TENDER_OUTCOME_DESIGN_2026-09-24.md`. Read it in full. Its recommendation, in one line:
do not ask a distributor to fill in a file — ask one question in reply to the list they already
receive ("which of these numbers will you pursue, and which will you pass?"), and have the ISZE
market owner for that country type the answer in the same day. It also records five facts that
decide the design, of which the sharpest are that 196 of the 222 selected notices have no deadline
at all, and that the same tender frequently appears twice, once from TED with no deadline and once
from the national portal with one.

### 2.9 The data-quality faults I measured, and one correction to an earlier brief

These are things that are actually wrong or misleading in the current feed. Each is a candidate
for the review; none of them is a reason to rebuild the scraper.

1. **The parts-demand rows are almost entirely absent from the weekly list.** 11 opportunities,
   of which 10 are `decision = "Ignore"` and one is `Selective`; **1 of the 11** appears on the
   weekly list (114 rows). So the one field that carries a parts business case is nearly filtered
   away before anyone sees it — but "nearly", not "entirely". An earlier version of this file
   asserted all were `Ignore` and none were listed; both were wrong and were corrected on
   1 October 2026. Verify before repeating.
2. **`meta.country_counts` counts opportunities, not notices.** It sums to 664 while the notices
   array holds 735. Any page that says "notices by country" from this key is wrong.
3. **A source can be healthy and still contribute little.** Of the 21 sources marked `OK` in
   `_source_health.json`, only **16 distinct sources actually appear in the feed**. The health file
   counts configured sources; the feed's `Source` values are portal codes (EU/TED, DE-OV, ES-PLACSP,
   NO, RO-SEAP, PL-BZP, PT-BASE, FR-BOAMP, BE, Israel, UK, IT-PNCP, AT-USP, Finland …), so the two
   lists are not directly comparable — **re-verify this mapping yourself before drawing a coverage
   conclusion.** What is solid: TED alone carries 402 of 735 notices, so **national-portal coverage
   is much thinner than "21 of 30 healthy" suggests**, and whether a given national source's rows
   were dropped by the Isuzu gate, by de-duplication, or after fetch is not established. One
   careful measurement, please.
4. **The weekly digest selection throws away almost all the dated notices it already has.** It
   keeps 33 dated of 223 selected. Meanwhile **82 opportunities in the feed have a deadline on or
   after 1 October**, of which 6 are `Attack`, 15 `Selective` and 23 `Watch` — a different and
   arguably better list than the one being sent, and it is not being used.
5. **Duplicate families.** `meta.stats.duplicate_families` is 45; the same tender appearing on TED
   and on a national portal carries two different `opportunity_id` values, so an outcome typed on
   one leaves its twin blank. The design memo records at least 26 such pairs inside the R&M set
   alone. The count of genuinely distinct tenders is therefore smaller than 664.
6. **Nearly every field a reviewer needs is missing.** 525 of 664 opportunities have no deadline,
   625 have no contract value, 638 have no fleet size.
7. **Two minor oddities, harmless but worth knowing.** The `tender_price_context.csv` carries 182
   rows over 11 opportunities because two opportunities have two rows per family, so "182 rows"
   should never be quoted as "182 notices". And `_CRITICALITY_PROTOCOL.md`, an internal note, is
   the one file in this folder I found with broken encoding (`â?"` where an em dash should be).

**One correction to the brief this prompt came from.** The brief described
`01_data\14_dashboards\tender_data.json` as holding "~5 MB, 735 notices, 664 opportunities" — all
three correct. It also described the price join as proving "we can only benchmark a small number of
parts today" — correct, and the exact figure is 0% to 33.3% coverage, median 2.59%. The only
material correction is a file-presentation one: the brief listed `isze_dashboard_v2.html` and
`isze_dashboard_v4_opportunity.html` as equivalent current pages. They are not equivalent. v4 is
self-contained and is the page that works on double-click; v2 has a bare-`file://`
`fetch` fallback that leaves it thin. Build the review around v4.

### 2.10 The unfinished merge, which constrains where you may write

`00_docs\agent\MERGE_PR10_CONFLICT_REPORT.md` records that a merge of pull request
[jeromio1987/ISZE#10](https://github.com/jeromio1987/ISZE/pull/10) was started, examined, and
**deliberately not completed**. The repository is on branch
`cursor/isze-exec-sales-paper-prompt-8dc1`. The report says the working checkout holds about 291
uncommitted files and must not be disturbed, and that the merge is left staged in an isolated
working copy elsewhere.

Two of the 87 conflicting files are tender files, and the report says so directly:

- `04_tools\ISZE_Tender_Monitor_Install\tender_scraper_v3.py` — 166 lines only on our side, 530
  lines only on the other.
- `04_tools\ISZE_Tender_Monitor_Install\_source_health.json` — the other side has an
  `Ireland eTenders` source this side lacks, and this side has newer measured counts.

Practical consequences for you: do not edit `tender_scraper_v3.py` as part of this work, do not
"tidy" `_source_health.json`, and do not run any git operation that resolves the conflict. If your
work needs a new file, add a new file.

---

## 3. The ask, stated as options

Jerome has not told you which deliverable he wants. Evaluate the options below and **recommend
one**, with your reasoning, before you build anything. A recommendation is what he asked for; a
menu with no opinion is not.

### Option A — build a dedicated tender review tool (my starting suggestion, to be tested)

A single self-contained page whose job is not to show the pipeline but to **run a weekly review
sitting**. One row per tender that is actually worth a decision, with the parts case beside it and
one place to record the answer. Concretely, something like:

- A "what needs a decision this week" queue, sorted by something defensible. Candidates from the
  data: deadlines within 14 days (39 opportunities), the 82 with a future deadline, the 6
  `Attack` rows, the 24 rows that are `rm_contract` with a future deadline, or rows where a parts
  family demand exists. Test the sort against what a reviewer would actually pick.
- A panel per tender showing buyer, country, distributor, deadline, value, fleet, the reason chips
  behind its score, and — where it exists — the parts breakdown with the benchmark coverage
  stated honestly.
- The answer capture that the design memo describes, writing to the same store that
  `tender_outcomes.py` already reads, so the weekly loop closes.
- An explicit, loud "not sized / no parts demand for this tender" state, never a blank and never
  a zero, per §4.5.

The strongest argument for Option A is that nothing on disk today is a review tool. v4 is a
pipeline view; v2 is legacy; the digest is a distributor-facing list; the outcome store has no
user interface at all.

### Option B — upgrade the existing v4 dashboard

Keep `isze_dashboard_v4_opportunity.html` as the deliverable and add the review capability as a
tab, rebuilt through `build_dashboard_v4.py` so nothing is hand-edited. Cheaper, and it inherits
the market, source-health and method tabs that are already right. The risks: 1.84 MB is already a
large file to wrap in more tabs, and the page's purpose today is to inform, while a review tool
has to decide and record. Mixing the two can produce a page that does neither well.

### Option C — make the weekly digest the review tool

The digest already goes out, already carries the right notices, and already has an import path. It
is tempting to grow it: add the parts panel to each distributor page, merge the twins, switch the
selection to dated notices, and wire the import step into the weekly batch. The complication is
that the digest is **written for a distributor** — it deliberately mentions only that
distributor's own name and scans every page for internal terms. A review tool is internal. Those
two audiences should not share one file (§4.2).

### Option D — something else, and you should say if you find it

Two candidates worth considering before you decide, which I raise because they are cheap and I
could not tell from the files whether they matter:

- **A parts-demand coverage job.** The narrowest honest fix to §2.5: find why 11 opportunities
  carry demand and the other 653 do not, and say whether the right answer is "the model only
  covers fleets above a size we rarely see" or "the field is only attached on a path that most
  notices never take". If it is the second, that is a real defect and worth fixing at source
  rather than building anything new.
- **A twin-merge job.** Before any outcome is recorded at scale, the 45 duplicate families should
  be merged, or every count computed later will be inflated. The design memo warns about this in
  its own words.

### What "good" looks like

For any option, judge the result against a reviewer sitting next to Jerome on a Monday morning.
That person should be able to answer, without scrolling sideways and without opening a file:

1. Which tenders need a decision from me this week, and why those?
2. For this tender, what is the parts business — which families, what quantity, what value, and how
   much of that can we actually benchmark against a rival?
3. What does the tool not know about this tender (fleet, deadline, value, parts), stated as clearly
   as what it does know?
4. What did we say last week, and what happened to it?

If it cannot answer all four, it is a dashboard, not a review tool, and you should say so.

---

## 4. Hard constraints

These are not preferences. Breaking one invalidates the work.

### 4.1 Words Jerome has banned

Do not use these in chat with him, in an HTML page he might open, in an Excel sheet, or in a draft
mail. The left column is banned; the right column is what to write.

| Never write | Write instead |
|---|---|
| Mode A / Mode B, "option A/B" as an audience label | shared / external versus internal / private |
| Book B | the price list, or a price revision |
| sell-out, sellout, street, street fills | sales to dealer |
| wallet, wallet €, parts wallet | parts billed, or target spend per truck |
| a factor such as ×1.785 with no English | state the margin. ISZE list × 1.40 to the dealer, then × 1.275, is a 27.5% step, not a factor |
| hardware PN, residual PN, extra pieces, leakage € | parts we billed with no list price; say the part in words |
| List 1 / List 2 / Early Warning / health call list | name the actual distributors and parts, or say nothing |
| upstream, downstream, baseline, the gate, flag, contract, residual, spine, drift, catalogue, taxonomy | say what it does in plain words; see `jerome-talk-clear.mdc` for the full table |
| ship-gate, harness, lane, surface, payload, artifact, rollup, receipt | describe the thing: "the check I ran", "the file the pages read" |

Two of these will tempt you constantly on this job. **"Drift"** is banned — say "how far it has
moved". **"Artifact"** is banned — say "file" or "page". Also note that the currency abbreviation
"EUR" is fine in a table for a European audience, but write "euros" in a sentence to Jerome.

### 4.2 Shared versus internal

This chat, your working notes, the internal unassigned page and any internal review tool are
**internal**: internal shorthand and blunt findings are allowed. Anything a distributor could
receive — the weekly digest pages, a country pack, an Excel sheet someone might forward — is
**shared**: no internal programme nicknames, no file paths, no `.csv`/`.json`/`.py` literals on the
page, no personal names beyond the recipient's own organisation, and no mention of another
distributor.

The existing digest builder already enforces this with a banned-word scan and reports the result in
`_run_report.json`. If you build anything that could reach a distributor, do the same thing and
report the count.

### 4.3 An HTML file must open on double-click

Cursor chat markdown cannot launch a browser. Jerome double-clicks `.cmd` files in Explorer. The
workspace rule is `isze-html-openable.mdc` and it is strict:

- If the file's data is under about 2 MB, embed it **inside** the HTML. Do not `fetch()` a sibling
  JSON — that always fails from `file://`. This is precisely what is wrong with v2, and precisely
  what is right about v4.
- If the data is larger, ship a `.cmd` launcher beside the file that starts a local server and
  opens the `http://` address.
- Never ship a page whose only route to working is "run a local server first" with no launcher.
- Any new launcher must be **CRLF**, 63 bytes or so, in the form
  `@echo off` / `start "" "%~dp0FILE.html"`. Both existing tender launchers are correct; copy the
  shape.
- Chart libraries: inline them. No CDN.

### 4.4 No rebuild, no overwrite, no ship without Jerome's word

Read `isze-no-ship-without-ok.mdc` in full. In summary: check and investigate is read-only; a
versioned file must never be silently overwritten; mail is drafted only and Jerome sends it; and
"rebuild" or "ship" has to appear in his current message before you write over a deliverable. If
you believe a file must change, say what and why, and wait.

On this job specifically: do not overwrite `isze_dashboard_v4_opportunity.html`,
`build_dashboard_v4.py`, the digest pages, the outcome store or anything under `rm_digest\`. Add
new files, or ask.

### 4.5 A gap is labelled, never blank and never zero

A missing number is never rendered as `0`, and never left as an empty cell with no explanation. In
a page it becomes an amber banner naming what is missing; in a table it becomes an em dash with a
footnote; in a sentence it becomes "not published". This applies with full force to the parts
demand (§2.5) and the price join (§2.6), where most of the grid is genuinely unknown. The
workspace's own wording for the weaker case is worth copying: a page with no data for a section is
asked to show **DATA UNAVAILABLE** in amber rather than a blank table.

### 4.6 A quantity is never a finding on its own

`isze-gaps-need-context.mdc` is a hard rule: any gap or shortfall you present must carry three
things together — **euros** on an observed average selling price, the **parts family** it belongs
to, and the **fleet denominator** so it reads as a rate per vehicle rather than an absolute. Do not
open a finding, a chart title or a tile with a piece count. "258,824 units" is banned; "258,824
units of oil filters against 47,783 light commercial vehicles in service, worth €X" is the form.

### 4.7 Never invent a number, and never average over a missing one

Where a value is unknown, the output is null and the interface says so. Where a value exists but
rests on a small sample, print the sample size beside it. Where two sources disagree, show both and
say which one you used — do not average them silently.

---

## 5. What I found broken, and what a review should put right

Each item below is a specific, measurable fault with a suggested direction. They are in order of
how much they matter. None of them is a reason to touch the scraper.

### 5.1 The parts case is nearly invisible, and that is the whole point of the programme

**Fault.** Thirteen of 735 notices carry a parts-demand breakdown, on eleven opportunities. Ten are
`decision = "Ignore"` and one is `Selective`; **one of the eleven** reaches the weekly list of 114
rows. The rows are present and finished in the feed and are almost entirely filtered out before a
human sees them.

**Correction, 1 October 2026.** An earlier version of this section claimed all eleven were
`Ignore`, that none had a distributor, and that none were listed. All three were wrong — the
notices do carry a `distributor_code` (Ireland 1, Germany 11, Portugal 1), the triage is mixed, and
one is on the digest. The corrected numbers are in §2.5. Re-measure before quoting either.

**Why it happens, as far as the files show.** The demand model is attached to a notice when a fleet
size can be extracted and a parts-frequency model exists for the weight class. The dashboard then
applies the triage filter, and most demand rows fail it. Whether the model is simply unavailable for
most notices or whether the attachment path skips them is **not established**, and it is the first
thing to measure.

**What to do.** Start with the measurement, not the build. Take the eleven rows and the 653 that
lack demand, and say plainly what separates them. Then design the review tool so that a parts case,
where it exists, is the first thing on the row rather than something behind a filter.

### 5.2 The parts field may not reach the layer the digest is built from

**Fault, partially verified.** The digest builder reads `opportunities`; `pms_demand_by_category`
lives on notices. Only 1 of the 11 demand-carrying opportunities reaches the weekly list, which is
consistent with the field not being carried onto the opportunity at aggregation time — but 1 did get
through, so this is **suspected, not proven**. Verify which layer carries the field before changing
anything.

**What to do.** Either carry the field onto the opportunity at aggregation time, or have the review
tool read both layers. The first is cleaner if the opportunity is the unit a person reviews.

### 5.3 A health file that reports configured sources, not contributing ones

**Fault.** The health file reports 30 configured sources, of which 21 are `OK`. The feed carries 16
distinct `Source` values, and TED alone accounts for 402 of 735 notices. So a reader who takes
"21 of 30 healthy" as a statement about coverage will over-read it. **Whether any given healthy
source contributed zero rows cannot be established by comparing the two name lists directly** — the
health file names publishers, the feed names portal codes — so an earlier claim here that eleven
named sources contributed nothing was not supported and has been removed.

**What to do.** Report two numbers per source, not one: what it returned, and what survived into
the feed. Say in plain words where the difference went — the Isuzu gate, duplicate merging, or
after fetch — and reconcile the publisher name to the portal code so the comparison is possible at
all. Do not change `_source_health.json` itself (§2.10).

### 5.4 The weekly list leans on undated rows and does not use all its dated ones

**Fault.** The selection keeps 33 dated notices and 190 undated ones out of 223. Meanwhile 82
opportunities carry a deadline on or after 1 October, including all 6 `Attack` rows and 15
`Selective` rows, and the digest today has 3 `Attack` rows in total.

**What to do.** Compare the two lists explicitly and say which you would send, with the reason. The
design memo already argues for dated-only and twin-merged. Consider building the review tool around
the dated set and leaving the undated pile to a separate internal page.

### 5.5 Two gates and a score that a reviewer cannot see through

**Fault.** A notice is dropped by the "not for us" gate (postal and courier panel-van purchases)
described in `_NOT_FOR_US_GATE.md`, then kept or dropped by the Isuzu selection gate, then scored
on three axes that combine into `opportunity_score`, then banded into tier, urgency and decision.
None of that reasoning is visible on the v4 row beyond a short `score_drivers` list.

**What to do.** Do not change the gates or the weights — that is explicitly out of scope. Consider
surfacing the reasoning that already exists so a reviewer can argue with it. If you believe a gate
is wrong, say so as a finding and leave the code alone.

### 5.6 The outcome loop has no entry point and no owner

**Fault.** A complete, careful outcome store exists and holds nothing. There is no interface, the
import is a line in a readme rather than a step in the weekly run, and the CSVs handed to a
distributor hold a 12-character code per row and nothing a person could recognise.

**What to do.** The design memo in §2.8 already answers this: ask by number, have the country owner
type the answer the same day, and put the result question at the top of the list every week. Check
whether the digest pages already do this and, if they do, say so rather than rebuilding it.

### 5.7 Small things that will mislead someone reading a page

- `meta.country_counts` counts opportunities while the label reads as notices (§2.9 item 2).
- The v4 page's line 692 still says "Wire next: ES WAF", which is stale.
- `tender_outcomes.json` says `version: 1` while the module's constant says `version: 2`.
- The digest CSVs still carry both `outcome` and `status` for the same word.
- 45 duplicate families inflate every count of distinct tenders.
- `_CRITICALITY_PROTOCOL.md` has broken encoding.

---

## 6. The data contract

Enough detail that you never have to rediscover it. Read the files anyway; this is a map, not a
substitute.

### 6.1 Live feed

`01_data\14_dashboards\tender_data.json` (`01_data\dashboards\` is a junction to the same folder).

Top level: `meta`, `opportunities` (664), `notices` (735).

`meta` carries `generated_at`, `stats`, `source_counts`, `country_counts`, `lifecycle_counts`,
`decision_counts`, `owner_counts`, `owner_options`, `status_options`, `ids_dealer`,
`outcomes_summary`, `outcomes_store`.

`meta.stats` on the 28 September build: `raw_notices` 735, `opportunities` 664, `attack` 6,
`selective` 192, `action_queue` 193, `due_14d` 50, `missing_deadline_opportunities` 525,
`missing_value_opportunities` 625, `missing_deadline_notices` 586, `missing_value_notices` 694,
`duplicate_families` 45, `low_evidence` 40, `aftersales_tagged` 285, `lifecycle_known` 202,
`lifecycle_unknown` 462.

`meta.owner_options`: `Unassigned`, `UK/IE Lead`, `DACH Lead`, `Benelux Lead`, `Nordics Lead`,
`Iberia Lead`, `France Lead`, `Italy Lead`, `CEE Lead`, `South EU Lead`, `Israel Lead`,
`Strategic Accounts`, `Bid Desk`.

`meta.status_options`: `Needs owner`, `Bid / No-Bid`, `Enrich`, `Review`, `Watch`, `Partnering`,
`Bid in progress`, `Submitted`, `Won`, `Lost`, `Contract live`.

Beware of one collision inside `meta`: `status_options` is the operator's workflow status list,
which has nothing to do with the digest CSV's `status` column, which is the outcome word. Same name,
two meanings.

`meta.ids_dealer` is an object I did not unpack; check its shape before relying on it.

### 6.2 Opportunity fields (72), the ones that matter

Identity and place: `opportunity_id` (12 hex characters, stable week to week as long as the source
text is unchanged), `title`, `title_raw`, `buyer`, `buyer_type`, `country`, `countries`,
`country_code`, `currency`, `url`, `opportunity_basis`.

Money and size: `value_amount`, `tier`, `fleet_size`, `fleet_size_confidence`.

Timing: `published_first`, `published_latest`, `deadline_date`, `days_to_deadline`, `urgency`.

Triage: `decision`, `opportunity_score`, `fit_score`, `win_score`, `econ_score`, `score_drivers`,
`evidence_score`, `evidence_label`, `lifecycle`.

Workflow: `owner_suggested`, `status_suggested`, `next_action_suggested`.

Meaning: `product_segment`, `product_segment_label`, `rm_contract`, `rm_hits`, `parts_signal`,
`service_hits`, `framework_hits`, `brand_hits`, `aftersales_tags`, `aftersales_summary`,
`aftersales_evidence`, `aftersales_match_tip`.

Parts and money behind the fleet: `pms_demand_by_category` (null or a list, see §6.4),
`gps_spu_year`, `gps_addressable_per_year_eur`, `gps_capture_rate`,
`capture_at_current_rate_eur`, `capture_under_rm_eur`.

Distributor and dealer: `distributor_code`, `ids_distributor`, `ids_distributor_label`, `ids_tab`,
`ids_dealer_name`, `ids_dealer_city`, `ids_dealer_rank`, `ids_match_method`, `ids_match_confidence`.

Grouping and quality: `notice_count`, `notices`, `source_count`, `sources`, `source_notice_ids`,
`duplicate_count`, `cpv_code`, `cpv_desc`, `data_gaps`, `data_quality_error`, `outcome`.

`ids_match_method` is worth knowing before you trust any dealer name: 278 rows are
`country_primary` (a fallback at confidence 0.5 — no real dealer match), 112 are `geo_nearest`, and
274 are `unmapped`. Only the geo-nearest rows carry a genuine local dealer.

### 6.3 Notice fields (72), the ones that matter

The capitalised portal fields: `Source`, `Source Notice ID`, `Title`, `Title Compact`,
`Description`, `Buyer`, `Buyer Type`, `Country`, `Country Code`, `Currency`, `CPV Code`,
`CPV Desc`, `Notice Type`, `Procedure Type`, `Lifecycle` (capital L — this is the notice's life
stage and it is a **string**, not the lowercase opportunity field), `Published`, `Published Date`,
`Deadline`, `Deadline Date`, `Est. Value`, `FleetSize`, `Score`, `URL`.

The lowercase derived fields are largely a mirror of the opportunity layer for that single notice:
`fit_score`, `win_score`, `econ_score`, `decision`, `tier`, `urgency`, `product_segment`,
`rm_contract`, `rm_hits`, `parts_signal`, `service_hits`, `framework_hits`, `brand_hits`,
`vehicle_hits`, the aftersales family, `score_drivers`, `data_gaps`, `data_quality_error`,
`days_to_deadline`, plus the distributor and dealer block and the `gps_*` fields.

Notice-level counters on the 28 September feed, useful as a completeness check: 149 of 735 carry
`Deadline Date`, 41 carry `Est. Value`, 28 carry `FleetSize`, 648 carry a CPV code, 336 carry
after-sales tags, and only 4 carry a brand hit.

### 6.4 `pms_demand_by_category`, in full

A notice field, null or a list. Each element:

```json
{
  "pms_category": "oil_filter",
  "category_label": "Oil Filter",
  "expected_qty": 0.87,
  "addressable_eur": 8.2,
  "avg_sp_eur": 9.44,
  "year": 2026
}
```

`expected_qty` is the quantity the fleet is expected to consume in the year. `addressable_eur` is
that quantity valued at **our** average selling price `avg_sp_eur` for that family in that market.
Fourteen families are covered, listed in §2.5. Two things are deliberately absent and you should
not add them: there is no competitor price in this structure, and there is no fleet denominator —
that comes from `fleet_size` on the same row.

### 6.5 The price join

`01_data\00_derived\tender_price_context.csv`, 19 columns:
`opportunity_id`, `country`, `buyer`, `distributor_code`, `ids_dealer_name`, `product_segment`,
`fleet_size`, `deadline`, `pms_category`, `category_label`, `expected_qty`, `addressable_eur`,
`our_avg_sp_eur`, `our_parts_in_category`, `parts_with_rival_price`, `coverage_pct`,
`rival_min_eur`, `rival_max_eur`, `rival_sources`.

One row per opportunity per family. `our_parts_in_category` is how many of our part numbers sit in
that family; `parts_with_rival_price` is how many of those carry an observed competitor price;
`coverage_pct` is the second divided by the first, to two decimals. `rival_sources` is a
pipe-separated list of source names; `rival_min_eur` and `rival_max_eur` are the low and high
observed prices in euros, converted at ECB reference rates dated 24 September 2026.

**Do not average across price types.** The underlying ledger's own rule is that a price type and a
vintage are required for every observation, because a genuine-grey price and a workshop list price
are not the same measurement. `price_observations.parquet` carries `source`, `currency`,
`price_type`, `part_no`, `price` and `price_eur` among others.

### 6.6 Where each file lives

| File | Role |
|---|---|
| `04_tools\ISZE_Tender_Monitor_Install\tender_scraper_v3.py` | the 30 source fetchers. Do not edit (§2.10) |
| `04_tools\ISZE_Tender_Monitor_Install\isze_core_v3.py` | scoring, gates, extraction |
| `04_tools\ISZE_Tender_Monitor_Install\build_dashboard_v4.py` | builds the v4 page, its JSON and its workbook |
| `04_tools\ISZE_Tender_Monitor_Install\build_dashboard_v2.py` | builds the legacy v2 page |
| `04_tools\ISZE_Tender_Monitor_Install\build_rm_digest.py` | builds the weekly distributor list |
| `04_tools\ISZE_Tender_Monitor_Install\tender_outcomes.py` | the outcome store and its loader |
| `04_tools\ISZE_Tender_Monitor_Install\rm_digest\<date>\` | one folder per weekly run |
| `04_tools\ISZE_Tender_Monitor_Install\_source_health.json` | 30 sources, 21 marked OK |
| `04_tools\ISZE_Tender_Monitor_Install\isuzu_tenders_v3.xlsx` | 18 sheets, 735 rows — the feed's only input |
| `01_data\14_dashboards\tender_data.json` | the live feed |
| `01_data\00_derived\tender_price_context.csv` | the tender-to-price join |
| `00_docs\TENDER_OUTCOME_DESIGN_2026-09-24.md` | the agreed design for recording outcomes |
| `00_docs\agent\MERGE_PR10_CONFLICT_REPORT.md` | why the merge is unfinished, and what not to touch |

The weekly batch is `run_tender_monitor.bat`: scraper, then publish, then v2, then v4, then the
digest, each with an error-level guard. Do not edit it without Jerome's word.

---

## 7. Questions you must resolve with Jerome

These are the things I could not settle from the files. Ask only these. Everything else in this
prompt is answered on disk, and asking a question whose answer is in §6 is worse than not asking.

1. **Who runs the review, and how often?** I can see that `owner_suggested` splits the book across
   ten regional leads plus `Strategic Accounts` and `Bid Desk`, and I can see that the digest goes
   to ten distributors. What I cannot see is whether one person sits with all 664 rows, or ten
   people see their own slice, or the distributor replies come in and someone at ISZE collates
   them. The shape of the tool depends entirely on this answer.
2. **Is the review tool internal only, or does part of it go to distributors?** The workspace rule
   (§4.2) decides two different vocabularies, and the digest already proves the shared version is
   achievable. I need to know which audience the new thing serves before I choose the words on
   it.
3. **Should the weekly list stay as it is?** It currently sends 223 rows, 190 of them undated,
   while 82 opportunities with a live deadline sit unused. Changing it affects ten distributors who
   may already have received the 24 and 28 September lists. That is Jerome's call, not mine.
4. **Is the parts demand worth fixing at source, or is it working as intended?** If the demand
   model only covers fleets above a threshold we rarely see, then eleven rows out of 735 is the
   honest ceiling and the tool should say so. If the field is being dropped on a path most notices
   never take, that is a defect worth fixing before any new tool. I can measure this either way,
   but I cannot tell from the files which answer Jerome expects.
5. **What does Jerome want the review to decide — pursue or pass, or something finer?** The design
   memo settles on two words plus a result later. Worth one sentence of confirmation before a
   store starts filling up with a vocabulary that is hard to change afterwards.

Do not ask about: the number of sources or which are healthy (in §2.9), the Nordic API keys (closed
— the keys are done, the workspace rule forbids raising it), the outcome store's format (correct as
it stands), or the merge (in §2.10).

---

## 8. Acceptance criteria

Before you say anything is finished, all of the following must be true, and you must be able to
name the evidence for each.

**Evidence and honesty**

1. Every number in your write-up and in the deliverable traces to a file you actually opened, and
   you can name it. No figures carried over from this prompt without re-measuring.
2. No value invented, and no missing value shown as zero. Every gap is labelled in the deliverable
   and named in your reply.
3. Any average or ratio that rests on a small sample prints the sample size next to it. The
   coverage figures in §2.6 are the model here: 2.59% median coverage means nothing without
   "of 182 rows, 11 opportunities".
4. Where two sources disagree, both are shown and the one you used is named.

**The deliverable**

5. HTML opens by double-clicking, with no local server and no internet. You have proved this by
   opening the built file, not the builder, and checking that the numbers actually painted.
6. If the page contains charts, count the rendered chart elements in the built file rather than in
   the source. If a table should have rows, count them.
7. Every derived figure carries a hover or footnote saying how it was computed.
8. A launcher exists beside the file if one is needed, and it is CRLF.
9. Light background, dark text, no reliance on the reader's browser theme.
10. In a shared page, a banned-word scan returns zero and you report the count by page.

**The write-up you owe Jerome**

11. Verdict first, in one plain sentence, then the reasoning, then the caveats. Prose, not stacked
    bullets. No agent vocabulary from §4.1. No "I will now" — say what happened.
12. A short walkthrough of what he should see when he opens the file: two or three concrete,
    visible facts, not a feature list.
13. The open questions from §7, and nothing that is already answered on disk.

**Before you claim done**

14. Re-read what you were asked, in the words it was asked in, and check the deliverable answers
    that question rather than an adjacent one you preferred.
15. If you took screenshots to check the page, you read them. State how many you took and how many
    you read.
16. Nothing was overwritten that §4.4 protects, and you can show the file timestamps to prove it.

---

## 9. What not to do

1. **Do not rebuild the scraper, and do not re-run it.** The sources are a separate programme with
   its own backlog. Nine of the 30 are not healthy, and most of those are deliberately closed:
   three retired, one suspected frozen, one skipped for geography, three blocked on credentials or
   a portal fix, one waiting on a key. That is a normal state, not a task for this review.
2. **Do not touch `tender_scraper_v3.py` or `_source_health.json`.** Both are in the unfinished
   merge's conflict set (§2.10). Editing either turns a data question into a merge question.
3. **Do not change the outcome store's format.** It handles aliases, unrecognised words, dry runs
   and the small-sample rule correctly. If you think something is wrong with it, report it; the
   one mismatch worth a look is the version number in §2.8.
4. **Do not re-tune the scoring weights, the gates or the thresholds.** This was ruled out of scope
   in August and nothing since has changed that. If a weight looks wrong to you, write it down as
   an observation with evidence and leave the code alone.
5. **Do not silently average over a missing value**, and do not fill a fleet size, a deadline or a
   value with anything other than null plus a visible label.
6. **Do not send mail.** Drafts only, and none of that is needed here.
7. **Do not overwrite a versioned deliverable.** Add a new file or ask.
8. **Do not quote the SteerCo pack's 326/291/174 as current.** The live feed is 735/664. If a page
   still prints the old figures, say so rather than reprinting them.
9. **Do not resolve the merge**, and do not run git commands that would.
10. **Do not re-raise the Nordic API keys.** The keys were finished on 25 August. The workspace
    rule is explicit that this question must not be asked again.
11. **Do not present UTI and UMI as one Israel number**, and do not blend IUK with ITUK. They are
    separate distributors with separate data. If a tender touches Israel, check which one the row
    is about.
12. **Do not build a second, competing tender pipeline.** There is already one feed, one scraper
    and three readers of it. Add a reader if you need one; do not fork the source of truth.

---

## 10. Where to start

Read, in this order, and stop as soon as you can answer §7 for yourself:

1. This file, once, end to end.
2. `04_tools\ISZE_Tender_Monitor_Install\_NOT_FOR_US_GATE.md` — small, and it explains what the
   programme is trying not to show.
3. `00_docs\TENDER_OUTCOME_DESIGN_2026-09-24.md` — the design you should not re-invent.
4. `04_tools\ISZE_Tender_Monitor_Install\rm_digest\2026-09-28\_run_report.json` — one file that
   shows what the weekly run actually produces.
5. `01_data\14_dashboards\tender_data.json` — read `meta` and one opportunity completely, then
   the eleven opportunities that carry parts demand. Do not load all 5 MB into a chat message.
6. `01_data\00_derived\tender_price_context.csv` and its `.meta.json` — 182 rows, small enough to
   read in full.
7. `00_docs\agent\MERGE_PR10_CONFLICT_REPORT.md` — read the tender sections, skim the rest.
8. The seven rule files in §0.

Then measure the five things this prompt asks you to verify for yourself rather than take on my
word: the parts-demand count, the price-join coverage, whether `rm_contract` and `decision` produce
a better weekly list than the one being sent, how many sources contribute rows to the feed against
how many the health file calls healthy, and how many distinct tenders remain after the 45 duplicate
families are accounted for.

Then bring Jerome one recommendation with your reasoning, and the five questions in §7. Do not
build before he answers.

# Mega prompt — the Excellence Partner white paper

**Use:** paste into Claude (or any capable model) together with read access to the ISZE workspace, or hand to the developer and the team as the written brief. It reproduces the paper `Excellence_Partner_White_Paper_2026-10-09`, and it is the brief for the next edition.
**Status:** internal. Written 9 October 2026. Language of the paper: English.

---

## 1. Role

You are a senior commercial analyst and technical writer working for the ISZE parts-sales team (vehicle parts, Europe). You write one definitive paper that lets ISZE management decide on an **Excellence Partner Program** for independent, multi-brand distributors, and lets a developer build what the programme needs. You are honest before you are persuasive. You never fill a gap with an assumption that is not labelled as one.

## 2. The decision the paper serves

Management must decide whether to approve (a) the concept, (b) a cost ceiling per year, (c) a measured pilot before full rollout. The paper must make that decision easy to take and hard to take wrongly.

## 3. What the programme is (settled, do not re-open)

- ISZE's own concept. IMG supports (for example IDS), IMG does not own it.
- Aim: **get more distributors to take part** — send sales-to-dealer data, send KPIs, run the dealer-standards round (IDS), follow the trainings. Distributors are independent and sell several brands. ISZE cannot force them. The discount is the one lever ISZE really has.
- Two levels: level 1 "Partner", about −2.5% on **stock orders only** (order type SOR); level 2 "Excellence Partner", about −5% on stock orders, with a result score on top. Checked **every quarter**; the discount code is then set in SAP. Rush and VOR orders are out. Air-freight savings are out.
- It **comes on top of** the existing kickback (rebate credits). It does not replace it. About 20% of today's rebate is tied to sales-to-dealer data (stated by Jerome; the contract text is not in the workspace).
- All distributors in principle. CIS markets (Ukraine, Armenia, Kazakhstan) may stay out. No budget ceiling is set. Training curriculum (EQ-Hit, EDI and order types, Parts Business Manual) will be ready by April 2027.
- No extra running cost in cash: it is built and run by Jerome, Bart Symons and AI. Internal time is not costed and the paper says so.
- It overlaps with **Isuzu Universe** (Jerome's other project: tools, data standard, analysis returned to distributors). The paper merges the two on purpose: Excellence is the front door and the reason to take part; Universe is the data standard, the return the distributor gets, and the rules of conduct. If management refuses the discount, Plan B is a harder kickback condition plus the Universe return.
- The programme is judged by what the data lets ISZE do afterwards: better analysis, better decisions, higher sales.

## 4. Non-negotiable rules of evidence

1. Every number carries a source (file path, table) and a period. Use **fiscal years**: FY2026 = 1 April 2025 – 31 March 2026; FY2027 = 1 April 2026 – 31 March 2027; the programme starts at FY2028 (1 April 2027). Calendar years only where a source is calendar, and then say so.
2. Euros first. Pieces are not a headline. Name the part in words.
3. Label every substantive claim: **[M] measured**, **[I] inferred**, **[A] assumption**, **[P] proposal**, **[U] unknown**. An unlabelled number is a defect.
4. Anchors, in order: green `01_data/00_derived/_verification_report.json` → `metrics_snapshot.json` → `FACTS.md`. Never quote a figure that fails the framework in `00_docs/ISZE_BI_FRAMEWORK.md`.
5. Never blend UTI with UMI, IUK (UK pickup) with ITUK (UK truck), Ireland with IUK. MIDI and Spain are not this book.
6. Do not read raw billing (`01_data/raw/sales/*.XLSX`). Use parquet and derived files.
7. Say "sales to dealer", not "sell-out". Say "gross margin" or "%GM", not markup factors. No "wallet", "street", "Book B", "Mode A/B", "List 1/2". Describe things in plain business English.
8. No benefit is claimed that no source supports. The paper states plainly that **no measured uplift from data sharing exists**, and shows what that does to the case.
9. Legal statements are not legal advice. Cite what was read; list what was not read.

## 5. Sources to read (open only what is listed)

| Topic | Path |
|---|---|
| The proposal as received | `Isuzu_Excellence_Partner_Program.pptx` (13 slides, 7 pillars, 100 points, levels −2.5% / −5%) |
| Workspace maps | `INDEX.md`, `00_docs/ROUTING.yaml`, `AGENTS.md`, `00_docs/ISZE_BI_FRAMEWORK.md`, `FACTS.md` |
| Billing and order types | `01_data/00_derived/sales_fact.parquet`, `distributor_dimension.csv`, `q1fy2027_export_with_saty.csv` (SAP cost) |
| Rebate credits | billing lines "Rebate Material" in `sales_fact.parquet` |
| Growth and noise | `gps_clean_all_fy_v2.csv`, `wallet_waterfall.csv`, `pms_opportunity_matrix.csv` |
| Business plan | `01_data/91_build/bp_fy27_reviewed.json` |
| IDS 2026 | `01_data/08_Distributor/IDS_2026/reports/*/study_payload.json`, `04_tools/ids_dealer_ranking/IDS_2026_LOGIC_CHECK.md` |
| Sales to dealer | `01_data/00_derived/dealer_sellout_long_*.csv`, `03_analytics/Isuzu/prism/data/dealer_sales/DEALER_SELL_OUT.md`, `01_data/DATA_MANIFEST.md` §05, sales-review minutes in `05_memory/briefs/sales_reviews_Koen_2026-08-05_06.md` and `09_meetings/*_Sales_Review_2026/` |
| Action plan FY2027 | `01_data/00_derived/vpacc_fy2027_action_plan_july.parquet`, `00_docs/FY2027_ACTION_CREDIT_MAP.md` |
| Universe | `Isuzu Universe/01_Strategy/` (3.0 paper, value-exchange model, participation model, pilot evidence pack, term sheet, DLOD rollout) |
| Earlier analyses | `09_meetings/Excellence_Partner_Program_2026/` (analysis, synergy, ROI model, movie, build scripts) |
| Decisions | `DECISIONS.md` (price reaction only distributor → dealer; incentive and discount items) |

## 6. Structure of the paper

Write for two readers: management (chapters 1–8) and the developer (chapter 9 and appendices). Target 25–35 pages.

1. **Executive summary** (one page): the decision, the three numbers that matter, the recommendation, what is not known.
2. **Purpose, scope and evidence labels.**
3. **The problem**: independent multi-brand distributors, a weak lever, what data ISZE has and lacks (coverage table per distributor), the kickback today (rebates paid, 20% tied to data), what the data is for.
4. **The proposal as received** and a fair critique (what is strong, what cannot be measured today, double counting, IDS as self-evaluation, the 85-point bar).
5. **The design** (settled concept plus the author's proposals): two levels, gates, data standard, scorecard, quarterly check, SAP, what the distributor gets back, rules of conduct, competition-law guardrails, forward-buying and gaming guards.
6. **The economics**: baseline numbers; five ways to pay (flat, growth only, two progressive hybrids, tiered); cost per year and over three years; break-even; benefit channels with evidence and their limits; Low/Base/High; sensitivity; the rebate comparison; Universe cash and its own hurdle; what is not counted.
7. **Can the return be proven?** Statistical power: yearly growth spread between distributors, no persistence, minimum detectable effect for a pilot; what can be measured instead (process indicators, dealer-level and part-family experiments, additional-only baselines).
8. **Universe and Excellence together**: what each contributes, where they conflict, combined cost, Plan B.
9. **Implementation and technical requirements**: timeline to April 2027, owners, intake channel, validation rules, identities, access separation, versioning and corrections, quarterly eligibility job, SAP condition, reporting, security, phases, T-shirt sizing marked as guesses.
10. **Risks and mitigations** (register with likelihood, impact, owner).
11. **Decisions requested, open items, what would change the recommendation.**
12. **Appendices**: A data standard; B scorecard criteria with six fields each (definition, source, owner, frequency, evidence, scale); C model formulas and assumptions; D per-distributor evidence tables; E developer requirements; F glossary; G sources read and not read; H this prompt.

## 7. Figures and tables

Charts drawn from the same files as the text: data coverage per distributor, cost by design against rebates today, net result by design with Low–High range, the progressive ladder, minimum detectable effect against pilot size, timeline. Tables for every comparison. No chart without a source line.

## 8. Style

Plain, direct, full sentences. Verdict first in each chapter, then the reasoning, then the caveat. No slogans, no hype, no emoji. Numbers with unit and comparison. Admit what is wrong or missing in earlier work, including earlier analyses by the same team.

## 9. Deliverables

1. Markdown source. 2. Self-contained HTML (opens by double-click, no external files). 3. PDF. Chapter 1 is the one-page decision summary for management. All in `09_meetings/Excellence_Partner_Program_2026/`.

## 10. Quality gates before saying "done"

- Re-derive five headline numbers from source and compare to the text.
- Recalculate the ROI model; zero formula errors; paper and model agree.
- Grep for forbidden words (sell-out, wallet, street, Book B, Mode A, Mode B, IML v7).
- Render the HTML at desktop and phone width and read every chart; open the PDF.
- List what was **not** verified, in the paper itself.

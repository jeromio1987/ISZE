# A number to own — shortlist

**Prepared:** 2026-09-16 · **Purpose:** pick one figure that the company already reports, where the join behind it exists only in this workspace, and turn it into a named responsibility.
**Not in scope:** any new dashboard, page or HTML file. Every candidate below is a number that is re-cut from files that already exist.
**Numbers rule:** `ISZE/FACTS.md` wins over anything else. All figures below were re-derived on 2026-09-16 from the source files named in each block; CY2025 unless stated.

---

## Summary and recommendation

| # | Candidate | Reported today by | Scale | First move |
|---|-----------|-------------------|-------|-----------|
| 1 | **Share of the network where sales to dealer is visible** | nobody as a standing figure (printed once, 15 Sep 2026) | 54.4% of the 2025 billed book in the measured markets; 75.1% with two more files | one page a month |
| 2 | **Parts billed versus target spend per truck, by market and category** | tiles exist in the analysis tool and the exec paper; no owner | group bills 51.1% of a €60.2M modelled ceiling; 37.3% of that ceiling is one placeholder | own the assumption, not the chart |
| 3 | **Price index versus the independent aftermarket** | nobody at network level | median index 0.57, on 43 part numbers and 0.26% of the billed euro | print it with the coverage line |
| 4 | **Warranty share of parts billed, by market** | the cost side is reported as an expense; the share is not | €4.72M = 14.6% of 2025 parts billed | one line per month |
| 5 | **Share of parts billed that carries a usable list price** | nobody | was 15.08% of the billed book; now 0.59M left over 31 part numbers | quarterly, almost self-closing |

**Recommendation: take number 1.** Reasons, in order:

1. **It is already the company's own complaint.** The growth plan on the internal site says the business is missing dealer-level sales for the three biggest markets after the UK. A complaint becomes a responsibility the moment it gets a percentage and a monthly update.
2. **Every other candidate depends on it.** Parts billed against target spend is only comparable across markets where a sales-to-dealer file exists; the price index only becomes weight-bearing when it covers a material share of the billed book; the brake and clutch pilot cannot size its sample without per-dealer per-month data.
3. **The fix is three files, not a build.** Germany, Belgium and Portugal are a shared file format away (€6.36M of billed volume, 20.7 points). Portugal has already landed, so the pattern is proven.
4. **It fails the substitution test in the right direction.** Nobody else in the company can compute it, and no tool purchase produces it — it is a distributor relationship and a normalisation job, and the normalisation is already written down here.

The question that decides it is at the bottom of this file.

---

## 1. Share of the network where sales to dealer is visible

| | |
|---|---|
| **What it is, plainly** | Of everything ISZE billed in the measured markets, what share can be seen again at the next step down the chain — what the distributor actually sold on to its dealers, per part number, per dealer, per month. It is a visibility percentage, not a sales result. |
| **The figures** | 2025 billed volume in the eighteen measured markets: **€30,756,772**. Visible through a sales-to-dealer file: **five distributors, €16,735,739 = 54.4%**. Portugal has since landed, taking six distributors to **€18,445,533 = 60.0%**. Adding Germany (€2,535,932) and Belgium (€2,109,332) takes it to **€23,092,567 = 75.1%**. Adding the reviewed three files (Germany, Belgium, Portugal) on top of the original five gives **€21,370,292 = 69.5%**. Source: the per-market billed-versus-target table in `ISZE/01_data/00_derived/` (see footnote 1), cross-checked against `ISZE/01_data/00_derived/gps_spu_by_distributor.csv`. |
| **Who reports it today** | **Nobody.** It was printed once, on 15 Sep 2026, inside the executive aftersales paper, and it has no owner, no cadence and no place in a recurring report. Before that it appeared as a complaint in the growth plan, not as a figure. |
| **Why the join is only here** | The number does not exist in any single system. It is: a distributor's own per-dealer, per-part-number sales file (a different layout from each distributor) **joined to** ISZE's own billed book, **on top of** the truck-in-service list that defines the denominators. Six distributor layouts have been normalised into one shape here (`ISZE/01_data/90_INBOX/sales_to_dealer_mail_hunt_20260903/FINDINGS.md` documents what exists and what does not in the mailboxes). No reporting tool receives the dealer file, so no tool can produce the percentage. |
| **What it takes to become the named owner** | **Cadence:** monthly, on the existing refresh rhythm. **Where it is published:** one block in the monthly sales report, plus one line in the quarterly pack. **Who receives it:** the VP Sales, the IML aftersales contact, and the distributors who supply a file. **The ritual:** print the percentage, print the excluded euro beside it, and name which distributor file is missing — that single line is what makes the number move. |
| **Cost and risk** | Cost is small: chase three files, run the existing normalisation, publish one page. Risk sits in the denominator. €30.76M is the eighteen markets that have a target-spend basis, out of a **€112.09M parts base** in `FACTS.md` §4. On the full base the same five files would read about **14.9%**, not 54.4%. State which denominator is in use on every issue, or this number will be attacked the first time it is shown to someone who knows the billing total. Second risk: a distributor that stops sending a file silently shrinks the percentage. Never show it without the list of files behind it. |
| **What it replaces** | The line in the growth plan saying dealer-level data is missing for the largest markets. Right now that is a request. As a tracked percentage it is a managed gap with a named owner and a direction of travel. |

## 2. Parts billed versus target spend per truck, by market and by category

| | |
|---|---|
| **What it is, plainly** | What the network actually billed for parts, set against a modelled target spend per truck in service — in total, per market, and per part category. It answers "how much of a plausible parts spend per truck are we seeing". |
| **The figures** | 2025: billed **€30,756,772** against a modelled ceiling of **€60,217,570 = 51.1%**, leaving **€29,460,798**. Trucks in service: **163,198**. Ceiling per truck **€369**, billed per truck **€188.50**. Per-market range **€389 down to €88** per truck (`ISZE/01_data/00_derived/gps_spu_by_distributor.csv`). Category detail: the fourteen-category component gap sums to **€18,216,555** for 2025, led by clutch disc €3.14M, brake pad €2.78M, brake shoe €2.47M (`ISZE/01_data/00_derived/pms_opportunity_matrix.csv`). |
| **Who reports it today** | **Nobody owns it.** The spend-per-truck league exists as a tile in the internal analysis tool and as pages in the executive paper. The category gap exists as a derivation. No one is accountable for either, which is exactly why the ceiling assumption below has survived so long. |
| **Why the join is only here** | Three model outputs and one billing file have to be joined: expected part demand per category per market, the truck-in-service list, and the net parts billed per distributor. The join, the category definitions and the integrity flags on all three live here. An off-the-shelf business-intelligence deployment would reprint the numbers; it would not hold the definition. |
| **What it would take to become the named owner** | **Cadence:** quarterly, with the market league every month. **Where it is published:** the quarterly pack, with the assumption block attached. **Who receives it:** the VP Sales and the IML aftersales contact. **The ritual:** every publication carries the sentence about which part of the ceiling is a placeholder, and the sensitivity band below. |
| **Cost and risk** | The real cost is that owning this number means owning its weakest assumption, in public. **Nine markets — €22,491,239, or 37.3% of the ceiling — sit at one flat €250 per truck**, and the model treats target spend as flat across vehicle age. Re-cut on defensible alternatives, the same billed book reads **43.6%** (median of the other nine markets, €364.3), **40.6%** (Portugal's €423.4) or **29.4%** (the UK truck rate, €744.6). A 21.7-point swing on a placeholder is a presentational risk, and it is also the fastest route to a real per-market target: the moment you own the number, the age-spend curve becomes a data ask with a name on it. |
| **What it replaces** | The residual €29.46M and the €18.22M component gap as ownerless numbers that appear in decks and then get re-argued from scratch. It also makes the price index in candidate 3 interpretable, because a billed-versus-target figure tells you whether a market is a price problem or a coverage problem. |

## 3. Price index versus the independent aftermarket, network level

| | |
|---|---|
| **What it is, plainly** | The reference dealer price for a genuine part (the list price carried through the distributor and dealer margin to the counter, so it is comparable with what a workshop actually pays) divided by what independent suppliers charge for the same part number. Below 1 means the independent is cheaper. One number for the network, refreshed from the live scrape. |
| **The figures** | Median index **0.57** on `ISZE/01_data/00_derived/iam_ks_price_gap.csv` — that is 374 price points across **43 part numbers**, all scraped in August 2026. The 15 Sep 2026 executive paper also prints **0.42** on a deduplicated set of 130 part numbers. Both can be right on different sets; the difference is which set and which aggregation. |
| **Who reports it today** | **Nobody at network level.** There are dashboards with heatmaps and per-part-number views, and a monthly scraper run, but there is no published network figure with an owner. |
| **Why the join is only here** | Three joins that no tool performs on its own: scraped supplier prices to ISZE part numbers, the part numbers to the billed book (so the index can be weighted and its coverage stated), and the list price to the counter price through the margin chain. Two channel factors are needed as well, and they were corrected here in July 2026 after a wrong arithmetic form had inflated every index in one dashboard by about 22%. |
| **What it would take to become the named owner** | **Cadence:** monthly — the refresh job already runs on Monday mornings, so there is no new pipeline to build. **Where it is published:** one line in the monthly pricing note and one block in the quarterly pricing pack. **Who receives it:** the VP Sales, the pricing contact at IML, and the aftersales contact. **The ritual:** the coverage sentence travels with the number, always. |
| **Cost and risk** | The honest limit is severe and must be printed every time. **The measured set is 43 part numbers and €78,638 at reference dealer price — about 0.26% of the €30.76M billed book.** On the wider deduplicated set in the exec paper the euro weight is much better (€7.47M, 22.2% of the billed book), but that set mixes vintages from 2023 to 2026, roughly a quarter of its points come from an undated supplier file, and a fifth of the points are UK. The risk in owning this is that someone reads a **price** index as a **volume share**. A price index cannot tell you how many parts moved to the independent channel; there is no independent volume data in the workspace at all. |
| **What it replaces** | The competitiveness heatmap as a one-off dashboard read. It becomes a monitored number whose movement can be quoted in a pricing conversation without re-opening a dashboard — provided the coverage line is never dropped. |

## 4. Warranty share of parts billed, by market

| | |
|---|---|
| **What it is, plainly** | How much of what the company bills a market arrives through warranty claims rather than as customer-paid parts. It is a distortion measure: it flatters or punishes a market's spend-per-truck figure depending on how much of the book is warranty. |
| **The figures** | 2025 warranty parts **€4.72M = 14.6%** of parts billed, and **54%** of the Israeli light-commercial distributor's own billed book (that distributor's spend per truck reads €179 including warranty and €82 without). Warranty claim expense fell from **€4.22M in 2024 to €3.18M in 2025, down 25%**, while parts billing was flat. Source: `ISZE/01_data/00_derived/gps_spu_by_distributor.csv` and `ISZE/01_data/00_derived/warranty_by_db_year.csv`. |
| **Who reports it today** | **The cost is reported — as an expense by the aftersales function — and the share of parts billed is not reported at all.** The two live in different reports, which is why the −25% claim expense against flat parts billing went without commentary for a year. |
| **Why the join is only here** | Warranty claim expense arrives per distributor per year; parts billing arrives per part number; trucks in service arrive per market. Only this workspace holds all three joined at distributor grain, with the two Israeli entities kept apart and the Israeli light-commercial distributor's warranty distortion already isolated. |
| **What it would take to become the named owner** | **Cadence:** monthly, one line. **Where it is published:** the monthly sales report, next to the spend-per-truck line. **Who receives it:** the VP Sales, the aftersales function and the IML warranty contact. **The ritual:** report the share both including and excluding warranty, and report it as the restated spend per truck, because that is the version that changes a decision. |
| **Cost and risk** | Owning this drags you into an argument that the workspace currently dodges: whether a 25% fall in claim expense is improving quality or tightening authorisation, and whether either one pushed repair work into the customer-paid channel at lower parts visibility. That cannot be answered from the current extract. If you take this number, take the follow-up question with it, or it becomes a figure nobody trusts. Lower visibility than the first three; it is a supporting number rather than a headline. |
| **What it replaces** | The footnote that currently says a market's spend per truck is distorted by warranty. As a tracked share it stops being a footnote and becomes a reason to collect the claim-detail extract. |

## 5. Share of parts billed that carries a usable list price

| | |
|---|---|
| **What it is, plainly** | Of everything billed, how much sits on a part number that actually has a usable price on the list. Everything else cannot be reached by any price move at all, however good the pricing decision is. |
| **The figures** | CY2025: **251 part numbers, €4,955,737, or 15.08% of parts billed**, had no usable list price. A SAP pull on 11–12 August 2026 **closed 220 of those part numbers**; **31 remain, worth €591,916**, of which 7 part numbers (€524,734) are a lubricants line parked by decision and 24 (€67,182) are flagged as having no list entry in the system. Source: `ISZE/01_data/00_derived/no_pr00_gap_cy2025_ranked.meta.json`. |
| **Who reports it today** | **Nobody owns it.** It is the least glamorous candidate here and the only one where the work has already been demonstrated once, end to end. |
| **Why the join is only here** | It requires every billed part number in the year set against the list file for that same year, on matched vintages, with the difference classified by reason (absent from the list versus present with no usable price). The year-matched list history for 2023 to 2026 exists here and nowhere else. |
| **What it would take to become the named owner** | **Cadence:** quarterly. **Where it is published:** one block in the quarterly pack and one line in the pricing note. **Who receives it:** the VP Sales and the IML pricing contact, because closing the remainder needs a list-maintenance action from them. **The ritual:** report the remaining euro, not the percentage, and name the part numbers that need a list entry. |
| **Cost and risk** | Low cost, low glamour, and an uncomfortable truth: if you own this number, any part of the book outside the list is visibly your problem. The remaining €0.59M is small enough that a manager may ask why it is tracked at all — the answer is that it was €4.96M eighteen months earlier and that the same defect will reappear with every new model launch unless someone watches it. |
| **What it replaces** | A footnote in the price documentation. It also makes candidate 3 honest, because a price index is only as representative as the part numbers that carry a price at all. |

---

## The one question to answer before claiming any of them

**For candidate 1, the share of the network where sales to dealer is visible: is the denominator the €30.76M of the eighteen markets that have a target-spend basis, or the €112.09M full parts base?**

That single choice decides whether the headline is **54.4%** or about **14.9%**, and it decides what the number means to the person reading it. The eighteen-market basis is the honest denominator for a distribution question, because those are the markets where a per-truck target exists at all. The full parts base is the honest denominator for "how much of the company's billing can we see down the chain". Pick one, print it in the header of every issue, and never switch without saying so.

---

*Footnote — file names quoted once as permitted because they contain a word this document does not otherwise use: (1) `ISZE/01_data/00_derived/wallet_waterfall.csv`, the per-market billed-versus-target table behind candidate 1 and candidate 2; (2) `ISZE/01_data/00_derived/dealer_sellout_long_*.csv`, the normalised per-dealer sales-to-dealer files; (3) `ISZE/01_data/01_Pricing/BOOK_B_CONCLUSIONS_20260819.md`, the unsigned price-revision conclusions.*

*Integrity note for every figure above: all 2025 figures were re-derived on 2026-09-16 from the named files. The 2025 billed base derives from `ISZE/01_data/00_derived/gps_spu_by_distributor.csv` (2025 rows, 22 distributors including four with no truck-in-service data, total €32.38M) less the four markets with no truck-in-service basis (€1.62M) and less Palestine, giving the €30.76M used throughout; that exclusion matches the eighteen-market scope of the billed-versus-target table. The £/€ note is not used anywhere above; all figures are euro as they appear in the source files.*

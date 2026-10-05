# 02 — The sixteen Imotors dealers (2026 round)

**Source:** the sixteen per-dealer scorecards `01_data\08_Distributor\IDS_2026\Portugal\IDS Evaluation
2026 - PORTUGAL - FINAL\`, the national ranking `01_data\08_Distributor\IDS_2026\rankings\Portugal_dealer_ranking.xlsx`,
the section scores in `09_meetings\IDS_2026_DB_Feedback_Sheet_v0.4\Portugal\IDS_2026_DB_Rollup_Portugal_v0.4.xlsx`
sheet `Master data`, and coordinates from the IDS geo build.

**Read this first:** the score is the **dealer's own self-assessment**. The same sheet has an IMG/ISZE
column and it is **zero on all sixteen** — never filled in. The ISZE evaluator named on each sheet did
visit the site in April 2026 and recorded the address; the scoring itself is the dealer's.

---

## The table

Section columns are the five standards sections, each as a percentage of its own maximum. Maximum total
is 280 points.

| Rank | Dealer | Score % | Band | A Premises | B Organisation | C Service | D Parts | E Vehicle sales | City | Visited | Workshop vehicles/month |
|---:|---|---:|---|---:|---:|---:|---:|---:|---|---|---:|
| 1 | Amatoscar Évora | 99.29 | Good | 100.0 | 97.5 | 100.0 | 100.0 | 100.0 | Évora | 2026-04-27 | 44 |
| 2 | Auto Reno Minho Póvoa | 96.07 | Good | 95.7 | 97.5 | 92.5 | 97.9 | 100.0 | Póvoa de Varzim | 2026-04-13 | 6 |
| 2 | Auto Reno Paços de Ferreira | 96.07 | Good | 95.7 | 97.5 | 92.5 | 97.9 | 100.0 | Paços de Ferreira | 2026-04-07 | — |
| 2 | Auto Reno Minho Viana | 96.07 | Good | 95.7 | 97.5 | 92.5 | 97.9 | 100.0 | Viana do Castelo | 2026-04-13 | 15 |
| 5 | Auto Reno Penafiel | 94.29 | Good | 84.8 | 97.5 | 92.5 | 97.9 | 100.0 | Penafiel | 2026-04-07 | — |
| 6 | Amatoscar Portalegre | 92.50 | Good | 89.1 | 91.2 | 93.8 | 95.7 | 92.6 | Portalegre | 2026-04-15 | 25 |
| 7 | Auto Industrial Leiria | 90.71 | Good | 84.8 | 87.5 | 95.0 | 89.4 | 100.0 | Leiria | 2026-04-28 | 20 |
| 7 | Rolmax | 90.71 | Good | 87.0 | 95.0 | 85.0 | 93.6 | 96.3 | Vila Nova de Gaia | 2026-04-29 | 150 |
| 9 | Auto Imperial | 86.43 | Good | 84.8 | 88.8 | 88.8 | 85.1 | 77.8 | Bragança | 2026-04-13 | — |
| 10 | Socarros Caldas | 82.14 | Good | 78.3 | 83.8 | 87.5 | 78.7 | 74.1 | Caldas da Rainha | 2026-04-30 | 432 |
| 11 | Astara Retail Lisboa | 78.57 | Medium | 76.1 | 82.5 | 80.0 | 80.9 | 63.0 | Lisboa | 2026-04-24 | 8 |
| 12 | MCar | 77.86 | Medium | 71.7 | 76.2 | 83.8 | 85.1 | 63.0 | Almancil (Faro) | 2026-03-31 | 110 |
| 12 | Soter Máquinas | 77.86 | Medium | 78.3 | 76.2 | 80.0 | 83.0 | 66.7 | Angra do Heroísmo (Azores) | 2026-04-28 | 20 |
| 12 | Xanauto | 77.86 | Medium | 76.1 | 65.0 | 85.0 | 80.9 | 92.6 | Loures | — | — |
| 15 | Astara Retail Cascais | 76.43 | Medium | 69.6 | 81.2 | 78.8 | 78.7 | 63.0 | Cascais | 2026-04-24 | 12 |
| 16 | Amatoscar Beja | 74.64 | Medium | 54.3 | 72.5 | 81.2 | 74.5 | 96.3 | Beja | 2026-03-31 | — |

**Band counts:** 10 Good, 6 Medium, none Needs improvement.
**Section averages across the sixteen:** A 82.6 · B 86.7 · C 88.1 · **D 88.6** · E 86.6.
**Overall average 86.72%** on a maximum of 280 points, an average of 242.8 points scored.

**A small discrepancy between two official files, stated rather than smoothed.** The national ranking
file `Portugal_dealer_ranking.xlsx` prints 96.43% for the three Auto Reno Minho/Paços sites and 92.86%
for Amatoscar Portalegre, where the dealer rollup says 96.07% and 92.50%. The ranking order is identical;
the difference is under half a percentage point and comes from the two files dividing by a slightly
different maximum. The table above uses the rollup, because that is the file where the total and the five
sections come from the same table and can be added up by a reader. If anyone quotes a Portugal score from
the ranking file, expect it to be up to 0.4 points higher on those four dealers.

Addresses, coordinates and the other brands each site services are in the machine-readable version
(`09_dealer_dimension.csv`). Two are worth knowing: **Soter Máquinas is on Terceira in the Azores**, not
on the mainland, and several sites run three to ten other franchises alongside Isuzu.

---

## What the scores actually say

**Parts is the strongest section on average, and that is the opposite of what the market data says.**
Section D averages 88.6% — the highest of the five — while the same market captured 48.9% of its
target spend in 2025. A dealer scoring itself 90–100% on parts standards while the distributor is billed
at half its ceiling is the single most useful contradiction on the page. It has two possible causes and
the data does not separate them: the checklist may be measuring paperwork and facility rather than
throughput, or the self-assessment may be generous. The rollup says the same thing in its own words —
Bavo at Astara asked to use the tool partly to target "dealers suspected of inflating self-assessment
scores".

**Section A is the weakest, and one dealer drags it.** Average 82.6%, and **Amatoscar Beja scores 54.3%
on premises** while scoring 96.3% on vehicle sales. That is not a rounding difference; it is the lowest
single cell in the table by a wide margin, and it belongs in any page that claims to be honest.

**The weakest checklist items are the same items across the network.** Measured across all sixteen:
B.3 Education 78.1%, A.3 Uniforms 78.9%, A.2 Stationery/Publications 83.3%, B.5 Workshop 5S 84.6%.
The rollup picks out two shared blockers by name: **item C.4-20** (incoming vehicles and maintenances
documented to the dealer) is a top gap for **12 of 16** dealers, and **item A.1-22** (a 24/7
out-of-hours contact number) for **9 of 16**. Those are distributor-fixable, not dealer failures.

**Section E has the widest spread.** Xanauto scores 92.6% on vehicle sales; five dealers score 63.0–74.1%.
Every one of the five lowest is either an Astara Retail site or a site with several competing franchises.

**Eight of sixteen sit below the market average** — the rollup calls them the hit list: Amatoscar Beja,
Astara Retail Cascais, MCar, Soter Máquinas, Xanauto, Astara Retail Lisboa, Socarros Caldas, Auto
Imperial. Note that Auto Imperial at 86.4% is inside the Good band and still below the 86.7% average;
the band boundary and the average do not coincide, and a page should not imply they do.

**Every assessment in this round happened inside 30 days** — 31 March to 30 April 2026. One round, one
month, no history.

---

## What is not in this table, and why

| Missing | Why | What would close it |
|---|---|---|
| What each dealer buys | Imotors' sales-to-dealer file is one national row; no dealer column | A dealer-level extract in the same shape (part number, quantity, month, dealer) |
| Vehicles each dealer has in service | No per-dealer fleet exists anywhere in the workspace, for any market | Imotors' territory or registration split by dealer |
| The independent assessment | The IMG/ISZE block is zero on all 16 sheets | An ISZE-scored round, or the same round re-scored |
| What each dealer sells to truck owners | Nothing measures a dealer selling on; the layer stops at distributor-to-dealer | Dealer reporting, which does not exist in the network |
| Vehicles 4 of the 16 workshops see | Blank on their cover sheets | One column from Imotors |
| A previous round to compare against | This is the first scored round | Time |

# Price ambition — CLOSED, permanently

**Date closed:** 2026-09-22
**Closed by:** Jerome, in chat.
**His words, verbatim:**

> "delete price ambition I will come when it's done for now do a simulation on 5% increase and than never ask again."

## What this means

1. **The price-ambition question is closed.** It is not deferred, not parked, not awaiting an
   answer. It is closed. The last output of it is the +5% flat simulation dated 2026-09-22.
2. **Never ask again.** No agent, in any later session, asks Jerome what the price ambition should
   be, what the band should be, whether to go +4% or +5% or open on launch families only, or
   anything that reduces to that question. He will come back to it himself when it is done.
3. **Nothing was changed.** No price list, no price file, no entry in
   `03_analytics/isze_pricing/config.yaml`. The simulation is arithmetic on paper only.

## What was produced as the last output

| Item | Path |
|---|---|
| Simulation workbook | `01_data/01_Pricing/Price_Increase_5pct_Flat_SIMULATION_2026-09-22.xlsx` |
| Simulation page | `02_dashboards/pricing/ISZE_Price_Increase_5pct_Flat_SIMULATION_2026-09-22.html` |
| Launcher (double-click) | `02_dashboards/pricing/OPEN_ISZE_Price_Increase_5pct_Flat_SIMULATION_2026-09-22.cmd` |
| Numbers, machine-readable | `02_dashboards/pricing/_build/price_5pct_review_2026-09-22/price_increase_5pct_sim_summary_2026-09-22.json` |
| Builder | `02_dashboards/pricing/_build/price_5pct_review_2026-09-22/build_price_increase_5pct_sim_20260922.py` |
| Ship receipt | `02_dashboards/pricing/ISZE_Price_Increase_5pct_Flat_SIMULATION_2026-09-22.SHIP_RECEIPT.json` |

Headline: a flat +5% is **EUR 1,749,680.47** on the whole in-scope base and
**EUR 1,629,792.63** collectable on the 47,617 lines that can take a new price, against a filed
revision measured at **+5.9616%** / EUR 1,652,140.71 on the same lines. The two are separate
readings of one base and are never added.

## Where the question used to live

If a future agent finds one of these still calling it open, this file is the superseding record:

| Where | State after 2026-09-22 |
|---|---|
| `00_docs/ISZE_ROADMAP.md` §2 ref **B1** ("the price adjustment ambition") | **Closed 2026-09-22** — see the note under the waiting table |
| `00_docs/DECISION_RECONCILE_20260916.md` B1 / B8 | Historical. It records the position on 2026-09-16, which the 2026-09-22 closure supersedes |
| `01_data/01_Pricing/PLAN_FORECAST_WEIGHTED_AMBITION.md` | Untouched and left as it stands. It is a build plan; the ambition values in it are no longer a live question |
| `01_data/01_Pricing/BOOK_B_CONCLUSIONS_20260819.md` · `01_data/01_Pricing/DB_DLR_COMMERCIAL_STACK.md` · `00_docs/AFTERMARKET_BI_BUILD_MENU_20260819.md` | Their "blocked on ambition" wording is stale as a *question*. No rebuild was run and no file was rewritten |
| `DECISIONS.md` | Entry added 2026-09-22 at the top of the log |

## What is expressly NOT closed by this

- **The filed +5.9616% revision** stands as it is. Nothing here touches it.
- **The other pricing decisions** (industrial-engine discount rate, the 3% vs 5.96% reconciliation,
  override rows, competitor-evidence funding, class assignment — `roadmaps/pricing.md` §2.2–2.8)
  are separate items and remain exactly as they were. This closes the **ambition** question only.

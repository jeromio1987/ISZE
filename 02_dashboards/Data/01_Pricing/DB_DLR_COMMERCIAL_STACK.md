# DB→DLR commercial stack (internal)

**Builder:** `01_data/91_build/build_db_dlr_commercial_stack.py`  
**Rebuild:** `python 01_data/91_build/build_db_dlr_commercial_stack.py`  
**As of:** 2026-08-19 · **No +3% alloc run** — revision queue uses planned SP % from `pricing_sim_pr00_l12m` only.

## Scope

| DB | Sell-out | Billing join | Notes |
|----|----------|--------------|-------|
| ITUK | Dealer × PN × month + network rollup | ISZE→DB | Richest grain |
| UTI | Network PN × month (PartSales stack) | ISZE→DB | **UTI ≠ UMI** |
| IRELAND | Network PN × month (long CSV) | ISZE→DB | **≠ IUK ≠ IMIE** |
| IUK | Network PN × month | ISZE→DB | **LCV D-Max ≠ ITUK** |

## Outputs

| File | Build | Role |
|------|-------|------|
| `replenishment_bridge.parquet` | 1 | Network × PN × month: bill vs sell-out |
| `replenishment_bridge_ituk_dealer.parquet` | 1 | ITUK dealer × PN × month |
| `replenishment_summary_cy2025.parquet` | 1 | Annual pipeline class per PN |
| `replenishment_exceptions_cy2025.csv` | 1 | Top leakage / overstock rows |
| `revision_exception_queue.csv` | 2 | PN × DB guardrails before any list revision |
| `revision_book_b_review_pack.csv` | 2b | Book B PN × DB join — ambition seeds + revision actions |
| `revision_book_b_action_summary.csv` | 2b | Counts by `recommended_action` × `book_b_bucket` |
| `revision_book_b_top_review.csv` | 2b | Top 500 non-HOLD / non-RAISE rows for Jerome review |
| `price_elasticity_db_dlr_network.csv` | 3 | Proxy + blocked YoY for all four DBs |
| `price_elasticity_db_dlr_ituk_uti.csv` | 3 | Legacy subset (ITUK+UTI only) |
| `db_dlr_commercial_stack.meta.json` | — | Run stats |

## Revision actions (queue)

| Action | Meaning |
|--------|---------|
| `REVIEW_IAM_UNDERCUT` | Peer shop price more than 20% **below** our reference dealer price (index < 0.80) — the peer is cheaper, we look expensive, guardrail before any list move |
| `REVIEW_PROXY_ADVERSE` | Category cross-section proxy β < −0.5 (adequate n) |
| `REVIEW_LEAKAGE` | Sell-through high or sell-out without bill |
| `REVIEW_OVERSTOCK` | Bill without matching sell-out |
| `REVIEW_HIGH_LIST_EXPOSURE` | Planned sim list move > +8% on PN |
| `RAISE_OK_ROOM_VS_IAM` | Peer shop price more than 10% **above** our reference dealer price (index > 1.10) — we already hold the premium, a raise is defensible on this evidence |
| `HOLD_DEFAULT` | No rule fired |

**Direction of the index.** `ks_price_index` = peer shop price ÷ our reference dealer price. Below 1.0 the peer shop is cheaper than us; above 1.0 it is dearer. The band 0.80–1.10 is deliberately left unlabelled: inside it the two sides are too close to the measurement noise to act on. The index is built in `db_dlr_commercial_common.load_ks_pn_index` (shop price ÷ reference dealer price). Do not invert this reading — the two labels call for opposite commercial action and were previously swapped.

**Not in scope:** multiplying list deltas by β; running `isze_pricing.cli alloc`.

## Build 2b — Book B × revision pack

**Builder:** `01_data/91_build/build_revision_book_b_pack.py`  
**Rebuild:** `python 01_data/91_build/build_revision_book_b_pack.py` (after commercial stack + book_b provisional)  
**Inputs:** `book_b_provisional_weights.csv` + `revision_exception_queue.csv`  
**Book B conclusions:** `01_data/01_Pricing/BOOK_B_CONCLUSIONS_20260819.md`

| Grain | What |
|-------|------|
| Book B | Network APL seed — **one row per PN** (no DB) |
| Revision queue | **PN × DB** (ITUK, UTI, IRELAND, IUK) with CY2025 bill/sell-out |
| Review pack | Book B left-join revision — fans out to PN×DB where activity exists; else `book_b_pn_only` + `NO_REVISION_ACTIVITY` |

**Verified counts (2026-08-19):** 18,401 review rows · 4,918 Book B PNs with DB activity · 10,999 `NO_REVISION_ACTIVITY` · top review cap 500.

**Top review filter:** excludes `HOLD_DEFAULT` and `RAISE_OK_ROOM_VS_IAM`; sorted by `sellout_qty` then `forecast_weight_eur`.

**Jerome review first:** `revision_book_b_top_review.csv` — leakage-heavy; IUK rows are **IUK ≠ ITUK**.

**Still blocked without ambition % + alloc:** cannot rank DB-specific list moves, apply Book B target (+4%/+5%), or produce final revision targets — pack is guardrail overlay only.

## Director BI — command center (HTML)

**Open:** `02_dashboards/sales/OPEN_Aftermarket_BI_Command_Center.cmd`  
**Rebuild:** `python 02_dashboards/_build/build_aftermarket_bi_command_center.py --all`  
**Verify:** `python 02_dashboards/_build/verify_tier_a_html_json.py`

Chart-first view: € leakage by DB/AIM, ISZE Director vs DB Director tabs, Book B × guardrail overlay. Replenishment + Book B HTML aligned via same builder (`--all`).

## Honesty

- Elasticity rows remain **`measure_kind=proxy`** until a second full CY sell-out exists per DB.
- KS index uses GBP→EUR **1.17** diagnostic; shop = min(KS AM, GEN) where quoted.
- Reference sell-out = PR00 × **1.785** (not “street” in shared labels).

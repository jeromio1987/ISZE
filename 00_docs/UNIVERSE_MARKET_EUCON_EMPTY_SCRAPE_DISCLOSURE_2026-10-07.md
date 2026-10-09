# Market path — Eucon-only + empty scrape disclosure (7 Oct 2026)

This meets the **market** piece of the finished bar by the second allowed path: Eucon-only, with an honest empty scrape. It does **not** invent eligible competitor euros.

## What is real today

- **Eucon** approved survey prices remain the usable competitor price source for AIM market comparisons where they apply.
- UK focus scrape evidence (brake pad + oil filter cut): **79** rows on the hand-collect sheet; **0** of those 79 state delivery basis, so **eligible competitor offers from scrape = 0**.
- Four Tranzparts ledger rows elsewhere do state delivery, but that loader is retired and they are not in the coverage cut.

## What is not real / not claimed

- We do **not** claim scrape-fed eligible UK shop euros.
- We do **not** invent delivery or tax on silent pages.
- Portugal competitor scrape is out for finished (UK first; PT hosts unusable).

## Path to scrape euros later (optional, not required for finished)

Hand-collect sheet (fill only when the page states it):

`C:\Users\jerom\Desktop\claude\ISZE\01_data\90_INBOX\UNIVERSE_UK_DELIVERY_TAX_HAND_COLLECT_20261007.csv`

Start with priority 1 rows that have a live URL (8 of 14). Six priority-1 Eucon survey rows have no URL — skip unless a written survey delivery basis exists. Reload steps are in the sibling `.md`.

## Finished-bar status

Market piece: **met via Eucon-only + this disclosure** (7 Oct afternoon).

## Where the disclosure paints (7 Oct afternoon)

- **Universe board** (amber banner at top of page):  
  `C:\Users\jerom\Desktop\claude\ISZE\02_dashboards\hub\ISZE_UNIVERSE_BOARD.html`  
  Built by `02_dashboards/_build/build_universe_board.py` (`SHOW_MARKET_GAP_BANNER`).  
  State flags: `01_data/00_derived/universe_board_state.json` → `market_gap_banner`, `eligible_shop_offers_uk_focus: 0`, `market_path: eucon_only_empty_scrape_disclosed`.
- **INTERNAL AIM**: no separate one-line market-gap strip on the chrome (pack status is version / list / cost only). IDS on INTERNAL is Ferndown + Astara Lisboa dealer answers, not shop scrape. Case market panels already report empty eligible sets honestly when delivery basis is missing — no builder change; no invented eligible euros.


## Where the banner appears

- Universe board: amber strip on ISZE_UNIVERSE_BOARD.html — Market prices Eucon only; eligible shop offers = 0.
- Open: 02_dashboards/hub/OPEN_ISZE_UNIVERSE_BOARD.cmd

## Update same evening — UK eligible shop = 2 (still Eucon-primary)

After KS £10 carriage was wired into coverage, UK usable/eligible shop offers = **2** (1 oil-filter PN). Still far below the 50-row bar. TMC under-£150 delivery £ still unpublished; basket/checkout timed out (504). TMC PDPs state VAT included via schema.org but not the rate. See `UNIVERSE_UK_DELIVERY_FILL_RESULT_2026-10-07.md` follow-up hunt. Board banner already says eligible = 2. INTERNAL AIM `metadataLine` source now carries the same honest one-liner.

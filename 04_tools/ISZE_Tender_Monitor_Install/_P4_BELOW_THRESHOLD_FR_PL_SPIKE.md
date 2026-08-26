# P4 — Below-threshold portals FR → PL

**Date:** 2026-08-25  
**Status:** **DONE (spike + focused implement + main-feed merge)** — on weekly bat via `run_all`

## Verdict

| Market | Portal | Machine path | Spike result | Wired |
|---|---|---|---|---|
| **#1 FR** | BOAMP OpenDataSoft | Public ODS API — **no key** | **52** vehicle-ish notices in 30d lookback (API total≈9.7k matching objet filter) | `fetch_france_boamp` via `--only fr` |
| **#2 PL** | e-Zamówienia / BZP | `mo-board/api/v1/notice` — **no key**; needs NoticeType + date range + CpvCode | **38** unique CPV matches in lookback; many `isTenderAmountBelowEU=true` | `fetch_poland_bzp` via `--only pl` |

## Evidence

### France — BOAMP

- Dataset: `https://boamp-datadila.opendatasoft.com/…/boamp/records`
- Filter: `objet like '%vehicule%'|camion|utilitaire|fourgon|pickup|…`
- Sample live titles include utilitaire électrique, Pick-Up Nacelle, hydrocureur
- Side file: `isuzu_tenders_v3_fr_pl.xlsx` (France BOAMP sheet)

### Poland — BZP

- Endpoint: `https://ezamowienia.gov.pl/mo-board/api/v1/notice`
- Required: `NoticeType=ContractNotice`, `PublicationDateFrom/To`, `PageSize>0`
- CPV filter works (`CpvCode=34130000` returns goods-vehicle deliveries)
- Side file: same xlsx (Poland BZP sheet)

## Run (opt-in only)

```bat
cd C:\Users\jerom\Desktop\claude\ISZE\04_tools\ISZE_Tender_Monitor_Install
python tender_scraper_v3.py --only fr,pl
```

Does **not** overwrite main when focused — writes `isuzu_tenders_v3_fr_pl.xlsx`. Full weekly bat (`run_tender_monitor.bat`) now includes FR/PL on `run_all`.

## NEXT

1. ~~Run Isuzu product-fit gate on FR/PL side file; measure keep vs noise.~~ **DONE** — gate keep FR 20/52 · PL 23/38; merge drop 0.
2. ~~If keep-rate acceptable → merge into main scrape.~~ **DONE** — see `_phase1_fr_pl_merge.md` (main notices 254 / opps 228).
3. Weekly bat: **ON** (`run_all` includes FR/PL). Still supports `--only fr,pl`.
4. Then IT/ES from dark map (same pattern).
5. Do **not** invent GPS € for FR/PL — still no SPU in pack (P1). Floor remains **€1,488.22**.

## Not blocked

Free public APIs exist for both. No Jerome registration required (unlike Nordics).

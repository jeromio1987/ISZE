# PMS Capture - All Distributors (CY2025)

**Generated from PRISM canonical derived data** (`01_data/derived/`), pipeline green **103 pass / 0 fail (2026-06-13)**. Expected demand = UIO x svc/yr x 70% addressable (N75 0.5 / LCV 1.0; FACTS.md sec.2). € gap = sum over PMS categories of (expected-actual) x avg SP, floored at 0 = the cost of closing to **100% capture** (a theoretical ceiling, not a forecast). Capture is uncapped. Reconciles to FACTS.md sec.1 for ITUK.

**Confidence key:** HIGH = own external-registration UIO (ITUK/DVLA). MED = central v18 parc-model UIO (real, network-standard, but not own-registration). LOW = v18 UIO **and** a structural distortion making capture unreliable (BVP-only channel / genuine-data gap). No distributor uses a *proxied or missing* UIO - the split is own-registration (ITUK) vs the v18 model (all others).

| # | DB | Country | UIO | Total cap | Genuine cap | € gap (to 100%) | Conf | Top action |
|---:|---|---|---:|---:|---:|---:|:--:|---|
| 1 | **IUK** | United Kingdom | 47,783 | 25.3% | 22.8% | **€3,882,056** | MED | Largest € ceiling but LCV-scope & assumption-sensitive - validate LCV service rate with IML before treating as winnable; focus genuine clutch/brake. |
| 2 | **UMI** | Israel | 18,542 | 31.2% | 10.4% | **€1,177,826** | LOW | Fix the genuine/warranty DATA gap first (genuine 1.1%); € gap is directional only. BVP/aftermarket-dominant channel. |
| 3 | **ITUK** | United Kingdom | 22,389 | 94.7% | 79.9% | **€982,540** | HIGH | Filters saturated (oil 162%, fuel 206%) - drive genuine MIX + a brake-shoe/clutch wear-parts retention pilot (ISZJ). Not a capture-deficit story. |
| 4 | **GERMANY** | Germany | 13,780 | 34.7% | 30.5% | **€499,671** | MED | Genuine clutch range push (disc capture very low) |
| 5 | **UTI** | Israel | 10,336 | 179.6% | 74.2% | **€399,554** | LOW | BVP-only channel (genuine 2.2%, total 112%) - capture saturated on BVP; genuine upsell limited. Treat genuine gap as low-confidence. |
| 6 | **BELGIUM** | Belgium | 9,593 | 60.3% | 45.8% | **€374,120** | MED | Validate brake-shoe fitment first (~0% capture network-wide) before sizing |
| 7 | **SWEDEN** | Sweden | 8,443 | 62.7% | 60.7% | **€244,116** | MED | Genuine clutch range push (disc capture very low) |
| 8 | **PORTUGAL** | Portugal | 7,208 | 59.3% | 28.1% | **€231,975** | MED | Stock clutch boosters (near-zero capture) |
| 9 | **HUNGARY** | Hungary | 3,734 | 39.0% | 33.4% | **€145,466** | MED | Genuine clutch range push (disc capture very low) |
| 10 | **NORWAY** | Norway | 7,929 | 54.2% | 52.5% | **€139,580** | MED | Validate brake-shoe fitment first (~0% capture network-wide) before sizing |
| 11 | **GREECE** | Greece | 3,742 | 93.5% | 60.1% | **€91,647** | MED | Genuine clutch range push (disc capture very low) |
| 12 | **CYPRUS** | Cyprus | 2,308 | 118.7% | 70.1% | **€49,075** | MED | Genuine clutch range push (disc capture very low) |
| 13 | **MALTA** | Malta | 1,040 | 72.6% | 72.2% | **€39,386** | MED | Low priority - air-filter gap inflated by flat service interval (flag C) |
| 14 | **ROMANIA** | Romania | 1,071 | 70.8% | 62.0% | **€37,902** | MED | Genuine clutch range push (disc capture very low) |
| 15 | **FINLAND** | Finland | 1,204 | 71.3% | 68.7% | **€37,441** | MED | Genuine clutch range push (disc capture very low) |
| 16 | **DENMARK** | Denmark | 851 | 75.9% | 73.1% | **€35,267** | MED | Low priority - air-filter gap inflated by flat service interval (flag C) |
| 17 | **IRELAND** | Ireland | 2,161 | 212.5% | 164.3% | **€21,530** | MED | Range & stock genuine AdBlue/urea filters (capture near zero) |
| 18 | **ICELAND** | Iceland | 406 | 72.5% | 71.9% | **€12,172** | MED | Genuine clutch range push (disc capture very low) |
| | **NETWORK** | | | | | **€8,401,324** | | |

## Read-out

- **Newly sized vs ITUK:** ITUK was the only distributor with a standing capture write-up (the oil-filter dispute anchor). The other **17 distributors are newly given a per-DB € brief here**, off the existing green pipeline - same method, same source, now distributor-by-distributor.
- **Total addressable (to 100% capture, CY2025):** **€8,401,324** across 18 distributors, PMS categories only. This is a gross-SP ceiling, **not** the GPS wallet (€75.1M) and **not** a forecast.
- **Concentration:** the top 3 (IUK, ITUK, UMI) carry 72% of the € ceiling. IUK alone is 46% and rests on the LCV 1.0 svc/yr assumption.

## Honesty line - where the data is too thin to trust

- **UMI (LOW):** genuine capture 1.1% is a genuine/warranty **data gap**, not a real sell-out read. The €1.1M is directional.
- **UTI (LOW):** ~100% BVP channel; genuine capture (2.2%) is structurally meaningless. Total capture already >100%.
- **IUK (MED, but caveat):** the single biggest number (€3.9M) is LCV-scope and assumption-sensitive; treat as a ceiling pending IML LCV service-rate sign-off.
- **Air-filter gaps everywhere (flag C):** expected demand uses a flat service interval, so air-filter capture is artificially deflated and its € gap overstated. Not cross-category comparable.
- **Brake-shoe ~0% capture network-wide:** almost certainly a fitment/availability reality, not a winnable genuine gap - it inflates several DBs' totals (ITUK alone €535K).
- **BVP is not leakage:** genuine->BVP is in-tent retention. The winnable genuine slice is materially **smaller** than the €8.4M ceiling; sizing it needs IML interval data + PN->schedule (EQ-HIT) fitment validation (both open in pms-coverage.md).

_Source: `01_data/derived/pms_summary_by_db.csv`, `pms_capture_by_db_year.csv`, `pms_opportunity_matrix.csv`. Regenerate: `python 01_data/derived/pms_briefs/_build/gen_pms_briefs.py`._
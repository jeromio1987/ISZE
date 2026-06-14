# PMS Capture - All Distributors (CY2025)

**Generated from PRISM canonical derived data** (`01_data/derived/`), pipeline green **103 pass / 0 fail (2026-06-13)**. Expected demand = UIO x svc/yr x 70% addressable (N75 0.5 / LCV 1.0; FACTS.md sec.2). € gap = sum over PMS categories of (expected-actual) x avg SP, floored at 0 = the cost of closing to **100% capture** (a theoretical ceiling, not a forecast). Capture is uncapped. Reconciles to FACTS.md sec.1 for ITUK.

**Confidence key:** HIGH = own external-registration UIO (ITUK/DVLA). MED = central v18 parc-model UIO (real, network-standard, but not own-registration). LOW = v18 UIO **and** a structural distortion making capture unreliable (BVP-only channel / genuine-data gap). No distributor uses a *proxied or missing* UIO - the split is own-registration (ITUK) vs the v18 model (all others).

| # | DB | Country | UIO | Total cap | Genuine cap | € gap (to 100%) | Conf | Top action |
|---:|---|---|---:|---:|---:|---:|:--:|---|
| 1 | **IUK** | United Kingdom | 47,783 | 21.5% | 18.9% | **€3,928,046** | MED | Largest € ceiling but LCV-scope & assumption-sensitive - validate LCV service rate with IML before treating as winnable; focus genuine clutch/brake. |
| 2 | **ITUK** | United Kingdom | 22,389 | 78.0% | 62.6% | **€1,648,531** | HIGH | Filters saturated (oil 162%, fuel 206%) - drive genuine MIX + a brake-shoe/clutch wear-parts retention pilot (ISZJ). Not a capture-deficit story. |
| 3 | **UMI** | Israel | 18,542 | 22.7% | 1.1% | **€1,110,282** | LOW | Fix the genuine/warranty DATA gap first (genuine 1.1%); € gap is directional only. BVP/aftermarket-dominant channel. |
| 4 | **BELGIUM** | Belgium | 9,593 | 51.1% | 36.0% | **€570,513** | MED | Range & stock genuine AdBlue/urea filters (capture near zero) |
| 5 | **GERMANY** | Germany | 13,780 | 25.4% | 21.0% | **€534,683** | MED | Genuine clutch range push (pressure plate / kit) |
| 6 | **SWEDEN** | Sweden | 8,443 | 55.2% | 53.1% | **€192,953** | MED | Genuine brake retention pilot (pads) |
| 7 | **UTI** | Israel | 10,336 | 111.9% | 2.1% | **€185,321** | LOW | BVP-only channel (genuine 2.2%, total 112%) - capture saturated on BVP; genuine upsell limited. Treat genuine gap as low-confidence. |
| 8 | **NORWAY** | Norway | 7,929 | 43.1% | 41.3% | **€185,191** | MED | Genuine clutch range push (pressure plate / kit) |
| 9 | **PORTUGAL** | Portugal | 7,208 | 41.8% | 9.4% | **€165,679** | MED | Validate brake-shoe fitment first (~0% capture network-wide) before sizing |
| 10 | **GREECE** | Greece | 3,742 | 81.5% | 46.7% | **€115,304** | MED | Genuine clutch range push (pressure plate / kit) |
| 11 | **CYPRUS** | Cyprus | 2,308 | 106.5% | 55.9% | **€99,431** | MED | Range & stock genuine AdBlue/urea filters (capture near zero) |
| 12 | **HUNGARY** | Hungary | 3,734 | 31.4% | 25.6% | **€83,359** | MED | Genuine brake retention pilot (pads) |
| 13 | **IRELAND** | Ireland | 2,161 | 182.8% | 132.7% | **€51,680** | MED | Range & stock genuine AdBlue/urea filters (capture near zero) |
| 14 | **MALTA** | Malta | 1,040 | 63.1% | 62.7% | **€49,947** | MED | Genuine brake retention pilot (pads) |
| 15 | **ROMANIA** | Romania | 1,071 | 60.9% | 51.8% | **€41,282** | MED | Genuine brake retention pilot (pads) |
| 16 | **FINLAND** | Finland | 1,204 | 66.6% | 63.9% | **€29,803** | MED | Genuine brake retention pilot (pads) |
| 17 | **DENMARK** | Denmark | 851 | 52.9% | 50.1% | **€20,100** | MED | Low priority - air-filter gap inflated by flat service interval (flag C) |
| 18 | **ICELAND** | Iceland | 406 | 62.7% | 62.1% | **€7,475** | MED | Genuine brake retention pilot (pads) |
| | **NETWORK** | | | | | **€9,019,580** | | |

## Read-out

- **Newly sized vs ITUK:** ITUK was the only distributor with a standing capture write-up (the oil-filter dispute anchor). The other **17 distributors are newly given a per-DB € brief here**, off the existing green pipeline - same method, same source, now distributor-by-distributor.
- **Total addressable (to 100% capture, CY2025):** **€9,019,580** across 18 distributors, PMS categories only. This is a gross-SP ceiling, **not** the GPS wallet (€75.1M) and **not** a forecast.
- **Concentration:** the top 3 (IUK, ITUK, UMI) carry 74% of the € ceiling. IUK alone is 44% and rests on the LCV 1.0 svc/yr assumption.

## Honesty line - where the data is too thin to trust

- **UMI (LOW):** genuine capture 1.1% is a genuine/warranty **data gap**, not a real sell-out read. The €1.1M is directional.
- **UTI (LOW):** ~100% BVP channel; genuine capture (2.2%) is structurally meaningless. Total capture already >100%.
- **IUK (MED, but caveat):** the single biggest number (€3.9M) is LCV-scope and assumption-sensitive; treat as a ceiling pending IML LCV service-rate sign-off.
- **Air-filter gaps everywhere (flag C):** expected demand uses a flat service interval, so air-filter capture is artificially deflated and its € gap overstated. Not cross-category comparable.
- **Brake-shoe ~0% capture network-wide:** almost certainly a fitment/availability reality, not a winnable genuine gap - it inflates several DBs' totals (ITUK alone €535K).
- **BVP is not leakage:** genuine->BVP is in-tent retention. The winnable genuine slice is materially **smaller** than the €9.0M ceiling; sizing it needs IML interval data + PN->schedule (EQ-HIT) fitment validation (both open in pms-coverage.md).

_Source: `01_data/derived/pms_summary_by_db.csv`, `pms_capture_by_db_year.csv`, `pms_opportunity_matrix.csv`. Regenerate: `python 01_data/derived/pms_briefs/_build/gen_pms_briefs.py`._
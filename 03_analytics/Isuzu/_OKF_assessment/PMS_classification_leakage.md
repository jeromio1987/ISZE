# PMS Classification Leakage — Network Diagnostic (CY2025)

> **Historical / superseded (2026-06-15).** The in-scope leakage fix is **live** in `03_analytics/Isuzu/prism/data/pms_capture_supplement.csv` (339 PNs: 230 fig-key leakage + 109 brake_rotor; consumed by `build_bvp_p0_p1.py`). Do not re-open as an open item.
>
> **Superseded for the fix-list by [`PMS_figkey_completeness.md`](PMS_figkey_completeness.md)** — that uses the full parts-catalog `pms_category`/`fig_key` (authoritative) and puts in-scope missing at **€978K** (this keyword scan said €880K). This file remains the per-distributor leakage view.

**Validation:** the counted universe is reproduced with the pipeline's own `tag_pms_sales` — IUK brake_pad / ITUK oil_filter / UMI oil_filter / GERMANY clutch_disc all reproduce the capture file (all OK). IUK brake_pad leakage = €126,281 (matches the manual €126K finding).

**Leakage** = genuine PMS-described sales whose PN the pipeline left `is_pms=False` (not in the BVP catalog dimension, crossref, or registry) — **uncounted actual**, so each € means the matching € gap is overstated by ~that much. Description-matched and tight → **lower bound**. Filter **elements/element-kits** (the genuine service part, €4–20/u) are counted; filter **assemblies** (€50–208/u) and **DPD** are split out; blower *motors* and cap/sensor parts dropped.

## Headline

- **Actionable leakage CY2025: €879,521** — genuine PMS sales invisible to capture (**wear parts €631,584** + filter elements €247,937). That's ≈ **10% of the €9,019,579 gap ceiling is classification, not lost business.**
- Excluded as **not service parts**: €93,894 of filter **assemblies** (housings, €50–208/u) + **DPD** exhaust units ≈€707,846 (DPD ASM ≈€1,748/u) — major components, not routine PMS filters.
- **The €9.02M ceiling I reported is overstated by ≥ €879,521** (more once BVP-retention, flag-C air and realistic targets are applied). The biggest single cause is one genuine front brake-pad PN — see below.

## Leakage by distributor (corrected gap ≈ gap − actionable leakage)

| DB | € gap (reported) | Actionable leakage | Corrected gap ≈ | Leak qty |
|---|---:|---:|---:|---:|
| UTI | €185,321 | **€186,903** | €0 | 16,250 |
| IUK | €3,928,046 | **€180,638** | €3,747,408 | 3,604 |
| GERMANY | €534,683 | **€88,913** | €445,770 | 1,329 |
| ITUK | €1,648,531 | **€80,032** | €1,568,499 | 4,241 |
| BELGIUM | €570,513 | **€58,552** | €511,961 | 966 |
| PORTUGAL | €165,679 | **€57,768** | €107,911 | 2,198 |
| UMI | €1,110,282 | **€54,626** | €1,055,656 | 6,355 |
| SWEDEN | €192,953 | **€43,301** | €149,652 | 590 |
| NORWAY | €185,191 | **€35,640** | €149,552 | 570 |
| GREECE | €115,304 | **€22,326** | €92,978 | 434 |
| IRELAND | €51,680 | **€17,654** | €34,026 | 713 |
| HUNGARY | €83,359 | **€12,181** | €71,177 | 335 |
| CYPRUS | €99,431 | **€11,403** | €88,029 | 230 |
| ROMANIA | €41,282 | **€10,853** | €30,429 | 176 |
| MALTA | €49,947 | **€8,314** | €41,633 | 173 |
| FINLAND | €29,803 | **€4,904** | €24,899 | 66 |
| DENMARK | €20,100 | **€4,120** | €15,979 | 248 |
| ICELAND | €7,475 | **€1,392** | €6,082 | 35 |
| **NETWORK** | €9,019,579 | **€879,521** | €8,140,058 | 38,513 |

## Leakage by category (where the part-master is incomplete)

| Category | Actionable leakage € | Leak qty | Note |
|---|---:|---:|---|
| Brake pad | €425,673 | 6,187 | genuine wear part |
| Oil filter | €130,542 | 15,777 | genuine filter element |
| Fuel filter | €101,716 | 10,502 | genuine filter element |
| Clutch disc | €101,274 | 735 | genuine wear part |
| Brake shoe | €98,766 | 3,576 | genuine wear part |
| Blower/cabin filter | €14,085 | 1,383 | genuine filter element |
| Clutch kit | €4,245 | 17 | genuine wear part |
| Air filter | €1,594 | 130 | lower-confidence (AIR/ELEMENT keyword) |
| Pilot bearing | €1,500 | 199 | genuine wear part |
| Release bearing | €126 | 7 | genuine wear part |

## Top 20 missing PNs (the fix-list to add to the crossref / registry)

| PN | Category | Qty | € | Description |
|---|---|---:|---:|---|
| `8975056801` | Brake pad | 4,293 | €306,344 | PAD KIT; CALIPER,DISC BRK,FRT |
| `8982984040` | Oil filter | 7,849 | €97,810 | ELEMENT; OIL FILTER |
| `8976526220` | Brake pad | 1,558 | €93,919 | PAD KIT; CALIPER,DISC BRK,FRT |
| `8975425390` | Fuel filter | 5,251 | €51,596 | ELEMENT KIT; FUEL FILTER |
| `8983476230` | Clutch disc | 302 | €42,972 | DISC; CLUTCH |
| `8981475700` | Fuel filter | 4,770 | €40,202 | ELEMENT; FUEL FILTER |
| `8975435900` | Clutch disc | 240 | €37,264 | DISC; CLUTCH |
| `5876150531` | Oil filter | 7,861 | €32,352 | ELEMENT; OIL FILTER |
| `1471702670` | Brake shoe | 165 | €18,032 | SHOE; BRK,RR |
| `1471704851` | Brake shoe | 216 | €16,371 | SHOE; BRK,RR |
| `5878316930` | Brake shoe | 75 | €15,424 | SHOE KIT; BRAKE,RR |
| `8983753330` | Clutch disc | 124 | €14,018 | DISC; CLUTCH |
| `1471704830` | Brake shoe | 138 | €9,052 | SHOE; BRK,FRT |
| `8978279601` | Brake pad | 136 | €8,751 | PAD KIT; DISC BRK,W/O SHIM & C |
| `8980180360` | Brake shoe | 181 | €7,982 | SHOE KIT; BRK,RR |
| `8980250061` | Blower/cabin filter | 719 | €7,338 | FILTER; BLOWER UNIT |
| `8980791040` | Brake pad | 117 | €7,302 | PAD KIT; CALIPER,DISC BRK,FRT |
| `8973870961` | Blower/cabin filter | 634 | €6,450 | FILTER; BLOWER UNIT |
| `5876102341` | Clutch kit | 17 | €4,245 | CLUTCH KIT |
| `5872214840` | Brake pad | 6 | €3,606 | PAD KIT; CALIPER,DISC BRK,FRT |

## Read / honesty

- **Clutch gaps are mostly REAL.** Clutch leakage is small (€105,519) vs clutch's huge gaps — genuine clutches genuinely aren't sold much, so those gaps stand. The classification problem is concentrated in **brake pads** and **filter elements**, not clutch.
- **One PN dominates:** `8975056801` (`PAD KIT; CALIPER,DISC BRK,FRT`) — the single biggest genuine front brake pad — is sold network-wide but absent from the catalog/crossref/registry entirely.
- **ITUK is only partly shielded.** Its registry covers the pilot filter categories, but it still leaks genuine brake pads etc.; ITUK's gap is overstated too (see table).
- **Element vs assembly:** filter **elements/element-kits** (incl. fuel, €4–20/u) are genuine PMS service parts → counted; **filter assemblies** (€93,894, €50–208/u) are housings → excluded.
- **DPD is not a PMS filter.** `DPD ASM` (≈€1,748/u) + DPD sensors/gaskets ≈€707,846 are exhaust aftertreatment (major component), correctly outside PMS service-filter scope — confirmed by price.
- **Lower bound** — tight keywords; seat/bumper 'PAD', blower motors, caps & sensors excluded.
- **Fix** = add these genuine OE PNs to `genuine_bvp_crossref` / the registry with a `pms_category`, then re-run `run_pipeline_and_verify.ps1` (capture, briefs, dashboard and the FACTS anchor update together).

_Source: sales_fact via pipeline tagger + `pms_capture_by_db_year.csv`. Regenerate: `python _OKF_assessment/_build/pms_leakage_diagnostic.py`._
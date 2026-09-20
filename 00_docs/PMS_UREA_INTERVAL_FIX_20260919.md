# AdBlue (urea) filter interval — what the source row says, and what changed

**Raised by:** Jerome, 2026-09-19.
**Changed:** `03_analytics/Isuzu/prism/modules/pms_engine.py` and
`03_analytics/Isuzu/prism/data/pms_capture_assumptions.yaml`.
**Not changed:** any mileage assumption, any other service category, the IML v7 lane.

---

## 1. Does the row mean the filter cartridge, or the AdBlue tank?

It is the **filter**. Three things say so.

**a. The row's position beside the other replacement items.** On `GIDSS_maint_N_MY24.pdf`, the
N-series MY24 schedule (frame *16.07.2026*, producer *Microsoft: Print To PDF*), the NPR75 / 4HK1
table carries the row **"AdBlue filter"** at **200,000 km (124,000 miles), action R**, in the
*EXHAUST SYSTEM* block between the DPD items and the NOx sensor. The 80,000 km / 50,000-mile figures
in the earlier 2026-07-16 pull are the **NLR87 / RZ4E** page of the same PDF (its own note *2
confirms the page), not the 4HK1 table.

**b. The F-series sheet names the engine, and it is the same item.** `GIDSS_maint_F_MY24.pdf` page 1,
headed *"1. For Italy, Israel, Portugal, United Kingdom, Ireland (4HK1 Engine Model)"*, carries
**"AdBlue filter (4HK1-TCH engine model)"** at **80,000 km (50,000 miles)**, action R, Severe X. The
same sheet's text layer prints the parenthetical, so the row is a *part* qualified by engine, not a
tank qualified by market.

**c. The workspace already treats it as the cartridge, from the same source.** `01_data/03_PMS/PMS_Intervals_Authoritative_Sources.md` §1.2 B (line 106) and §1.4 A (line 202) carry both rows
verbatim; `02_dashboards/_build/leakage/README.md` line 149 records "Urea (AdBlue) filter —
200,000 km" and `00_docs/GPS_PMS_TRUTH_REPORT_20260917.md` line 119 confirms it a second time.
René's GIDSS row is also titled with the word *filter*, not *tank* or *module*.

**Method, stated because it is not obvious.** These PDFs are Microsoft Print-to-PDF output: each
table is an embedded JPEG with no text layer, so a grep finds nothing. The rows were read by
extracting the embedded image at native resolution, upscaling, and running the Windows OCR engine
plus a binarised pass. The label cell for the 200,000 km row reads **"Blues filter"** — the engine's
best rendering of *AdBlue filter* — on the row whose interval cell reads **"Every 200.000 km
(124.000 miles): R"**. Artefacts, if the read needs re-checking:

```
01_data/90_INBOX/_gidss_render/N24_p4_xref43.jpeg      native table image, N-series p4
01_data/90_INBOX/_gidss_render/ocr/N24_p4_xref43_x5.txt   OCR of that image
01_data/90_INBOX/_gidss_render/bin_lbl2_110.png          the binarised label crop that reads "Blues filter"
01_data/90_INBOX/_gidss_render/_ocr_binarise.py          the script that produced it
```

The F-series 80,000 km row is read the same way from `F24_tile_0_2.png`: the OCR of that tile
returns the label line **"AdBlue@ filter (4HK1-TCH engine model) …"** immediately above
**"Every 80,000 km (50.000 miles): R"**.

**Conclusion: it is the filter cartridge. The factor changes.**

---

## 2. What the factor was, and what it is now

The pipeline carried `urea_filter: 1.0`, i.e. one AdBlue filter per service visit — the same rate
an oil filter gets. Against the sourced interval that is wrong by about five times on the N-series.

The pipeline's own convention is one visit per **40,000 km** for N75
(`pms_capture_assumptions.yaml`, `n75_parc_assumptions.service_visit_interval_km: 40000`), so:

| Vehicle class | AdBlue interval | Visit interval | Share of a visit |
|---|---|---|---|
| N-series, NPR75 / 4HK1 | 200,000 km | 40,000 km | **0.20** |
| F-series, 4HK1-TCH | 80,000 km | 30,000 km (the provisional F-series figure already in `BUCKET_SERVICES_PER_YEAR`) | **0.375** |
| D-Max / LCV | not in the sources | 20,000 km | unchanged at 1.0 |

The two truck classes differ by 1.875x, so **one scalar cannot hold both**. That is why the change
is in `pms_engine.expected_by_category_bucketed()`, where the `cv_std` and `f_series` UIO buckets are
already separate, and not only in the YAML. `_DEFAULT_CONSUMABLE["urea_filter"]` is now `0.2` for the
legacy single-scope path and `UREA_FILTER_F_SERIES` carries the F-series rate.

Both files carry the source and the km figures in the code comment. Nothing else was touched.

---

## 3. What moved — before and after, per market

Controlled pair: the same build chain (`build_bvp_p0_p1.py`) run twice, once with the factor left at
1.0 and once at 0.20 / 0.375. Full table: `01_data/91_build/epc_batch2/_urea_before_after.txt`.

**AdBlue denominator, the markets that moved** (expected units a year, 2025):

| Market | before | after | ÷ | AdBlue capture before → after |
|---|---:|---:|---:|---|
| ITUK | 17,285.6 | 3,559.4 | 4.86 | 7.63% → **37.06%** |
| UTI | 12,920.0 | 2,584.0 | 5.00 | 0.63% → **3.17%** |
| PORTUGAL | 6,776.2 | 5,173.0 | 1.31 | 0.99% → 1.30% |
| IRELAND | 1,877.7 | 1,456.7 | 1.29 | 7.56% → 9.75% |
| MALTA | 963.3 | 830.3 | 1.16 | 0.42% → 0.48% |
| GERMANY | 13,494.5 | 13,137.3 | 1.03 | 0.01% → 0.02% |
| CYPRUS | 2,211.9 | 2,126.4 | 1.04 | 2.31% → 2.40% |
| BELGIUM | 9,584.9 | 9,501.0 | 1.01 | 0.72% → 0.73% |
| GREECE | 3,723.5 | 3,708.7 | 1.00 | 0.00% → 0.00% |
| DENMARK | 850.5 | 850.1 | 1.00 | 25.98% → 26.00% |

The last four move so little because their bucket is almost entirely LCV (where the rate is
unchanged). **Eight markets are untouched entirely** — Finland, Hungary, Iceland, IUK, Norway,
Romania, Sweden, UMI — because their truck bucket is zero and the LCV rate did not change.

**Effect on each market's published capture across all 14 families, 2025:**

| Market | before | after | delta |
|---|---:|---:|---:|
| ITUK | 44.68% | 50.95% | **+6.27 pp** |
| UTI | 49.55% | 56.33% | **+6.78 pp** |
| IRELAND | 96.64% | 100.05% | +3.41 pp |
| PORTUGAL | 28.77% | 29.84% | +1.07 pp |
| MALTA | 31.36% | 32.03% | +0.67 pp |
| CYPRUS | 49.96% | 50.26% | +0.30 pp |
| GERMANY | 13.86% | 13.92% | +0.06 pp |
| BELGIUM | 25.81% | 25.85% | +0.03 pp |
| GREECE | 40.28% | 40.30% | +0.02 pp |
| all others | — | — | 0.00 pp |

**Network:** urea expected 635,200 → 528,156; urea gap EUR 3,814,134 → **EUR 2,036,143**
(−EUR 1,778,000). All 14 categories: every category other than `urea_filter` is byte-identical
before and after — checked in `_urea_before_after.txt`, section *DID ANY OTHER CATEGORY MOVE?*.

### Published figures that move, and need a decision

- **ITUK AdBlue cover goes 7.63% → 37.06%.** This is a real rise in the *rate*, not in sales: the
  denominator shrank. The old denominator was too large by 4.86x.
- **ITUK all-family capture 44.68% → 50.95%.** ITUK is the IML v7 lane's market, and the IML v7
  deck itself (35.1% oil-filter cover, EUR 2,038,471 gap) is **not touched** — it lives in
  `iml_v7_ituk_cy2025.yaml` and is a separately agreed external basis.
- **UTI all-family capture 49.55% → 56.33%.**
- The leakage README's ITUK AdBlue figures (EUR 342,356 → EUR 20,022) were computed on the old
  denominator and are now stale.

---

## 4. Verification

`python scripts/verify_derived_pipeline.py` → **143 pass, 0 warn, 0 fail**, including the ITUK
oil-filter bands (2024 56.4% in 52–61%; 2025 78.7% in 74–84%), which are where a leak from this
change would have shown up first. Report: `01_data/00_derived/_verification_report.md`.

---

## 5. Not done, deliberately

- The D-Max / LCV AdBlue rate. No source gives a D-Max AdBlue interval, so it stays at 1.0 rather
  than being guessed. `03_analytics/Isuzu/prism/data/lcv_pms_genuine.yaml` has no urea entry.
- The mileage re-base. Out of scope and still open on its own decision.
- Stale downstream text naming the old AdBlue number (leakage README, PMS market briefs). Those are
  rebuilt files, not sources, and were left for a separate pass rather than edited by hand.

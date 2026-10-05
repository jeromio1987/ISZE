# GPS and PMS: what is actually true, and why the numbers kept moving

**Prepared:** 2026-09-17 · **internal (internal)** · Read-only investigation, nothing rebuilt
**Author:** agent, at Jerome's request after the leakage-tool review

---

## 1. Bottom line

There is not one GPS number and not one PMS number. There are **at least four published GPS
percentages and five published PMS denominators** for the same market and the same year, each
individually traceable to a file, and no two of them can appear on one page without
contradicting each other.

Neither of the two most consequential faults is a rounding error. Both are *structural*, both
were visible in the code for weeks, and at least one of them was already written down in July
and not acted on.

For ITUK CY2025, the same billing data produces:

| Metric | Figure | Where it is published |
|---|---:|---|
| GPS capture | **32.4%** | `wallet_waterfall.csv` — the ceiling leads with this |
| GPS capture | **47.0%** | `gps_spu_by_distributor.csv` — the GPS dashboard leads with this |
| GPS capture | **43.9%** | `fleet/ISZE_GPS_Dashboard.html` (ex-warranty variant) |
| Oil-filter capture | **100%** | `pms_capture_by_db_year.csv`, capped, as headline tiles show it |
| Oil-filter capture | **116.4%** | the same file, uncapped |
| Oil-filter capture | **35.1%** | the IML lane, shown to IML |
| All-PMS capture | **65.9%** | `pms_summary_by_db.csv` |
| All-PMS capture | **94.4%** | a review note already sitting in `90_INBOX` |

## 2. The GPS root cause — proven with exact arithmetic

Two independent ceilings exist for the same market-year.

**Ceiling A**, the one the GPS dashboard publishes, is built in `uio_v19_gps.json` from a real
weight-class split of the fleet:

```
ITUK 2025:  10,900 × €296  +  10,684 × €739  +  805 × €887  =  €11,835,911
```

**Ceiling B**, the one `wallet_waterfall.csv` publishes, is built from
`uio_by_model_bucket.csv`, whose only buckets are `cv_std`, `f_series` and `lcv`:

```
ITUK 2025:  22,191 × €739  +  877 × €887  =  €17,176,988
```

The difference is **€5,341,077**, and the preponderance of it is one thing:

```
10,900 light trucks × (€739 − €296) = €4,828,700
```

**`cv_std` has no N35/N75 split.** It lumps every light truck into one bucket, and that bucket
is then priced at the N75 rate of €739. The v19 file carries the split and prices the light
trucks at the N35 rate of €296. Everything else follows arithmetically.

On the same €5,564,544 of billing, ceiling A gives 47.0% and ceiling B gives 32.4%. Before the
corrected work today, the pack showed 32.4%.

**Which ceiling is right?** A. The independent check is the UK warranty VIN sample, which
measures 61% N35 / 33% N75 / 6% F-series. v19's split is 48.7% / 47.7% / 3.6%, close to that.
The bucket file's 96% `cv_std` is not a split at all, so it cannot be right by construction.

**Why this happened.** `pms_capture_config.py` carries the same fault and says so out loud:

> `"cv_std": 0.5,  # PROVISIONAL — LD+MD collapsed into one bucket, pending a real IML LD/MD
> interval split (Jerome 2026-07-15: "collapse LD+MD but flag it")`

The collapse was a deliberate, flagged decision. What did not happen is the split being
un-collapsed when `uio_v19_gps.json` produced a real split. So the two layers now disagree by
31% of the ceiling for the market that matters most.

## 3. The other GPS fault — the target figures contradict their own documentation

| Source | N35 | N75 | F-series | LCV |
|---|---:|---:|---:|---:|
| `gps_model_targets.csv` (**what the code loads**) | 296 | **739** | **887** | 250 |
| the CSV's own derivation | £400 × 0.66 × 1.12 | £1,000 × 0.66 × 1.12 | £1,200 × 0.66 × 1.12 | ISZE max |
| `gps_model_targets.py` **docstring** | — | **1,120** | **1,344** | 250 |
| `gps_engine.py` constant | flat **150** | flat 150 | flat 150 | flat 150 |

Three different target regimes live in the same package. The docstring is 1.52× the data, and
nothing reconciles them. A reader who trusts the comment gets a different answer from a reader
who trusts the CSV.

## 4. The PMS problem — five denominators, a 4.3× spread

The failure is the same shape as GPS: one number, several constructions, changed separately.

| Denominator construction | Expected units | Capture on 13,599 actual | Source |
|---|---:|---:|---|
| 22,389 × 0.5 svc × **70%** addressable | 7,836 | **173.5%** | `metric_dictionary.md` §PMS table |
| 22,389 × 0.5 svc × **100%** addressable | 11,194 | **121.5%** | the same dictionary, later in the same file |
| 22,389 × **1.25** svc × 100% | 27,986 | **48.6%** | IML v7 lane, for IML |
| 23,068 × 0.5 svc × 100% (bucket) | 11,534 | **117.9%** | PRISM lane, what ships today |
| 22,389 × **1.5** svc × 100% | 33,584 | **40.5%** | banned by the dictionary's own table |

Same part, same year, same billing file. The denominator spreads across **4.3×**, and the
answer moves from 40% to 174% purely on which line of which file you read.

Note rows 1 and 2: **the metric dictionary contradicts itself.** Its table says addressable is
70%; its narrative says 100% was set on 2026-07-03. `FACTS.md` says 100%. The YAML says 100%.
The dictionary's table was never updated.

## 5. What is actually true, as of today

Stated as a position, with the evidence behind it.

| Question | Answer | On what basis |
|---|---|---|
| ITUK GPS capture CY2025 | **47.0%** on total billing, **43.9%** ex-warranty | Ceiling A (v19 split, N35 priced at €296). Warranty must be stated either way, never silently dropped. |
| ITUK GPS target per truck | €296 N35 / €739 N75 / €887 F / €250 LCV | `gps_model_targets.csv`, derived from the £ study. The docstring's 1,120 / 1,344 has no source. |
| ITUK oil-filter capture | **116% uncapped** on the PRISM lane; **35.1%** on the IML lane | Different denominators by design, documented. They must never appear on the same slide unlabelled. |
| ITUK brake-pad capture | **not determinable** — somewhere between 15% and 88% | The units-per-brake-job question is unresolved. Four independent choices each move it by 2×. |
| Blower filter, CV markets | **should not be scored** | Zero units sold across all CV markets in four years. |
| AdBlue filter interval | **200,000 km** | GIDSS schedule, confirmed twice. The implied 39,500 km was wrong by 5×. |

## 6. Why it kept happening — the actual mechanism

Eight changes to the PMS denominator in ten weeks:

| Date | Change | Landed in |
|---|---|---|
| 2026-06-15 | rotor factor 0.25 added, unsourced | YAML comment |
| 2026-07-02 | air filter 1.0 → 0.5 | YAML comment |
| 2026-07-03 | addressable 70% → 100% | YAML comment |
| 2026-07-14 | ITUK brake factor 0.4, from an IML slide | YAML override |
| 2026-07-15 | bucket UIO split replaces a 2-market allowlist | FACTS.md, called a bug fix |
| 2026-07-16 | ITUK brake override flagged PROVISIONAL | YAML comments |
| 2026-07-26 | blower filter 0.25 → 1.0 | YAML comment |
| 2026-08-17 | brake units question raised to IML, unanswered | ask note |

Each change was individually justified and individually documented. **What never happened is a
single reconciliation that re-checks the headline after all of them.** The verification report
tests that files exist and that arithmetic is internally consistent — 116 checks, all green,
zero failures. It cannot catch this class of fault, because every variant is internally
consistent. That is why a green report and a wrong number coexist.

Four structural causes:

1. **No single owner of the definition.** The same concept is defined in a YAML, a CSV, a Python
   constant, a docstring, a markdown dictionary and FACTS.md — six places, no precedence rule.
2. **Reconciliation verifies consistency, not correctness.** It checks that A equals B, never
   that A is the right construction. Seven of its fourteen hard checks were also **skipped** on
   the last run (`--skip-raw`), so the raw-billing and waterfall checks did not run at all while
   the report still said PASS.
3. **Documentation is treated as description, not as data.** The docstring/CSV divergence and the
   addressable 70/100 divergence both went unnoticed because nothing tests prose against values.
4. **Placeholders are allowed to look like measurements.** A 0.25 rotor factor, a 20,000 km
   assumed mileage, a 96% `cv_std` bucket — each is a placeholder, none was marked as such on a
   dashboard, so each was read as a fact.

## 7. What was already known, and not acted on

This is the part that matters for trust, because it is not a data problem.

- `05_memory/projects/gps-reconciliation.md`, **2026-07-03**, states plainly that the v9 snapshot
  the GPS dashboards embed is **hardcoded to 12 June 2026**, before the Israel refresh, and that
  a raw rebuild runs 2–4.5% lower for most markets, UMI −20%, UTI −7.5%. It records this as a
  "soft WARN" pending "Jerome's decision". The GPS dashboard has been publishing the stale
  constants ever since.
- The same note documents **two GPS bases** that must never be cross-compared, and that the check
  mixing them "perma-failed" and was removed.
- `pms_capture_config.py` documents the LD+MD collapse as provisional and pending an IML split.
  That split arrived in `uio_v19_gps.json` and was never applied back.
- `ISZE_ITUK_Brake_Factor_IML_Ask_2026-07-23.md` asks the brake units question in writing. It is
  unanswered, and the pack I built still shows the unbanded number.
- A review note in `90_INBOX` already carries the **94.4%** figure, which no shipped artifact
  matches.

## 8. My own contribution to this

I should be direct about it, because Jerome is right that this is not normal.

1. **I shipped the leakage tool on ceiling B without reconciling it to ceiling A.** I read the
   waterfall, found a `gps_pct` column, and used it. I did not ask why a second GPS percentage
   existed with a different denominator three files away. That is how a 32.4% headline reached a
   pack that also cites a €60.22M ceiling built partly on the same figure.
2. **I presented 32.4% and 47.0% side by side in the same panel** and wrote a note calling them
   "two percentages, two questions" that are "never averaged together". That was wrong. They are
   one question with two answers, and the note made a contradiction sound like a feature.
3. **I ran the existing reconciliation and took PASS at face value** without noticing that half
   its hard checks were skipped.
4. **I rebuilt the PMS denominator on sourced intervals today without first reconciling it to the
   published 65.9%**, so there are now more denominators rather than fewer.
5. **I let the brake number ship unbanded** after reading the July ask that says it is unresolved.

The pattern is the same in all five: I verified that what I built was internally consistent, and
did not verify that it agreed with what was already published.

## 9. What needs a decision

Nothing below should be done by an agent alone.

1. **Which GPS construction is canonical.** My recommendation is ceiling A (v19 split), because
   it carries a real N35/N75 split and the independent VIN sample supports it. That requires
   `uio_by_model_bucket.csv` to gain the split, and `wallet_waterfall.csv` to be rebuilt — a
   PRISM engine change, not a reporting change.
2. **The addressable percentage.** 70% or 100%? The dictionary says both. `FACTS.md` and the YAML
   say 100%, set by you on 2026-07-03. The 70% was the older value and the dictionary's table was
   the last stale echo of it — I corrected that table on 2026-09-17 as documentation only; no
   number moved. **The mechanism, and I got this wrong twice yesterday before checking the code:**
   `addressable_pct` multiplies modelled expected demand and nothing else
   (`pms_engine.py:333` — `uio_units * svc * addressable_pct`). Actual sales are untouched. So the
   percentage scales every PMS capture figure by the inverse — at 70% instead of 100%, each one
   rises by about 43% relative (ITUK oil filter 65.9% → 94.2%). It does **not** touch GPS:
   `gps_engine.py` never reads the variable, because the ceiling is fleet count × rate per truck.
   The euro effect is separate but points the same way: of the €24.5M network gap, 100% treats all
   of it as claimable, and 70% declares about €7.35M structurally unreachable, leaving €17.1M.
   **The evidence actually argues against 70%:** three ITUK families already bill more than the
   model says can exist — oil filter 116.4%, fuel filter 157.0%, brake rotor 197.7% — while the
   basket as a whole reads 65.9%. A model reporting twice as many brake rotors sold as expected
   has its demand figure too low. At 70% addressable the basket rises to 94.2% and the brake rotor
   to 282%, which hides the error instead of exposing it. The knob worth turning is
   `services_per_year` for wear parts, not the share of the fleet.
3. **Whether the GPS dashboards get re-based off the June snapshot**, which is a 2–4.5% move with
   UMI at −20%.
4. **Whether the two lanes (IML v7 at 35.1%, PRISM at 116%) stay separate.** They can, but only
   if no artifact ever shows both without a label, and today two of them do.
5. **The brake units question.** Until IML answers, the brake figures should be published as a
   band or not at all.

## 10. What I recommend for the mechanism

Not more checks of the kind that already pass. Three things that would have caught every fault
above:

1. **One definition file, generated into everywhere else.** The target rates, the addressable
   percentage and the service intervals should exist in exactly one file, and the CSV, the
   docstring and the markdown should be generated from it or deleted.
2. **A cross-layer reconciliation that asserts equality between published figures**, not internal
   consistency: if the waterfall and the GPS feed disagree on the same market-year, fail. That is
   a five-line check and it would have caught the €5.34M gap on day one.
3. **Placeholders marked on the face.** Any figure resting on an assumed interval, an assumed
   mileage or a collapsed bucket should be rendered differently from a measured one. On the
   leakage tool I have now done this; the rest of the estate has not.

---

## Artefacts from this investigation

- `02_dashboards/_build/leakage/_forensic.py`, `_forensic2.py`, `_forensic3.py`, `_forensic4.py`
- `01_data/00_derived/gps_reconciliation_report.json` — 7 of 14 hard checks SKIPPED, verdict PASS
- `01_data/91_build/uio_v19_gps.json` — ceiling A, the split
- `03_analytics/Isuzu/prism/data/uio_by_model_bucket.csv` — ceiling B, no split
- `03_analytics/Isuzu/prism/data/gps_model_targets.csv` vs `modules/gps_model_targets.py`
- `03_analytics/Isuzu/prism/modules/gps_engine.py` line 33 — the flat €150 constant
- `03_analytics/Isuzu/prism/docs/metric_dictionary.md` — 70% table against 100% narrative
- `05_memory/projects/gps-reconciliation.md` — the July diagnosis, including the stale snapshot
- `03_analytics/Isuzu/prism/modules/pms_capture_config.py` — the flagged LD+MD collapse

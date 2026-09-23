# Project 3 — Aftersales ceiling & opportunity (multi-hour brief)

Live published network anchor (ceiling file, 2025): ~**55.7%** on **€55.25M**.
Retired: **51.1%** / **€60.22M**. Israel: UMI 1797 ≠ UTI 1799.
Block-3 checklist is in `00_ASK.md`. Recompute from CSV — do not trust this prose alone.

---

## A. Agent verdict (challenge every line)

1. Ceiling = target spend per truck × trucks in service; coverage = billed ÷ ceiling.
2. ITUK 32.4% vs ~47% was light trucks priced heavy; after split ~45.6% on ~€12.21M; only ITUK moved.
3. Opportunity heroes = clutch/brake euro gaps, not oil-filter method stories.
4. Eight markets on flat €250/truck hold ~40% of ceiling — disclose always.
5. Portugal parc light share 0.6364; shipment mix ~0.69 different; rebuild not authorised.
6. Primary lens = total capture; unit counts alone are not findings.
7. Mileage assumptions can inflate/deflate expected demand (UK light vs UTI heavy).
8. Addressable kept at 100%; clutch AT/MT not measurable from VIN.
9. Fleet-figure pack rebuild approved in principle, not run; new ceiling number separate.

---

## B. GPS / PMS alignment (full)

# GPS and PMS alignment — every surface, every figure, and why it drifted

**Prepared:** 2026-09-17 · **internal (internal)** · Read-only investigation
**Companion to:** `00_docs/GPS_PMS_TRUTH_REPORT_20260917.md` (the root-cause detail)
**Requested by Jerome:** *"align everything, check everything, and report. I just wonder how you could still make mistakes after months."*

---

## 1. The alignment matrix — ITUK CY2025

Every figure a reader can currently see, and what it rests on.

> **CORRECTION, added after two independent forensic audits returned.** An earlier version of this
> report named 47.0% as the correct GPS figure and recommended it as canonical. **That was wrong.**
> See §1a: the two ceilings are two aggregations of the same fleet, neither is a bug, and the
> choice between them is a decision rather than a fix.

## 1a. THE ROOT CAUSE, FOUND AND PROVEN

The two GPS ceilings are **not a bug**. They are two aggregations of the **same ITUK fleet**, and
the fleet has now been traced to its source.

The Make / Model / Variant register gives ITUK's carpark by family:

| Family | Units |
|---|---:|
| N35 | 10,900 |
| N75 | 9,359 |
| N50/55 | 651 |
| F135 | 442 |
| UNSPECIFIED | 417 |
| F110/120 | 358 |
| N62/65 | 257 |
| F150/180 | 5 |
| **Total** | **22,389** |

**v19 keeps that distinction** and prices it in three bands: N35 10,900 @ €296, N75/LD 10,684 @
€739, F/MD 805 @ €887 → **€11,835,911**.

**The UIO workbook has already merged it.** Sheet `1.UIO Overview` carries a single line,
`U KING CV LD 2025E = 22,190.9` — N35 and N75 together — plus `F-Series 877.0`, with no MD row.
So the cheap band is gone and every truck is priced at €739 → **€17,176,988**.

```
10,900 × (€739 − €296) = €4,828,700 of the €5,341,077 difference
```

**So neither figure is wrong, and there is no defect here to fix.** The rate card needs the
N35/N75 distinction (€296 vs €739); one route preserved it and the other had already lost it. That
is why the same billing reads 47.0% or 32.4%.

This was a **defect, and it is fixed** (2026-09-17). The workbook already carried the split in a
sheet nothing read: **`2. Vehicle Volume` section B** ("ITUK UK Car Par[k]"). `data_prep` now reads
it and emits explicit N35 / N75 rows before the rate mapper sees them.

**Result:** ITUK ceiling €17.18M → **€12.21M**, ITUK GPS **32.4% → 45.6%**, network **51.1% →
55.7%**. Only ITUK moved; the other 17 markets are byte-identical. The two ITUK GPS routes
converged from 14.6 points to 1.4, the residual being fleet vintage rather than method.

### GPS

| # | Surface | Figure | Ceiling used | Rests on |
|---|---|---:|---:|---|
| 1 | `wallet_waterfall.csv` | **32.4%** | €17.18M | bucket UIO, no N35 split, light trucks at €739 |
| 2 | `gps_spu_by_distributor.csv` | **47.0%** | €11.84M | v19 UIO, real N35 split, light trucks at €296 |
| 3 | `gps_spu_by_distributor.csv` (ex-warr) | **43.9%** | €11.84M | same as #2, warranty removed |
| 4 | `fleet/ISZE_GPS_Dashboard.html` | **43.9%** | €11.84M | embeds the v9 snapshot, hardcoded 12 Jun |
| 5 | `sales/ISZE_Leakage_Cockpit.html` | **32.4%** | €17.18M | reads #1 |
| 6 | `leakage_packs/..._ITUK.html` | **32.4%** | €17.18M | reads #1 |
| 7 | **`01_data/dashboards/isze_data.json`** | **47.0% / 43.9%** | €11.84M | `gps.ituk`, methodology "max-spend GPS v9" |
| 8 | `sales/ISZE_KPI_Dashboard.html` | 32.4% and 47.0% | both | carries both constructions |
| 9 | `sales/ISZE_Exec_Aftersales_Paper.html` | 32.4% | €17.18M | reads #1 |

**Nine GPS readings for one market-year, in four distinct constructions.** Surfaces 1, 5, 6 and 9
agree with each other. Surfaces 2, 3, 4 and 7 agree with each other. 1 and 2 are **14.6 points
apart on identical billing**. Surface 8 carries both, and surface 4 publishes a snapshot that
predates the Israel refresh.

**The decisive fact: which figure is canonical is genuinely contested inside the pipeline.**

Two instruments inside the same package claim different answers:

| Instrument | Anchors | Value |
|---|---|---|
| `metric_dictionary.md` line 13 | **`gps_spu_by_distributor.csv`** named canonical derived file | implies 47.0% |
| `facts_anchor.yaml` line 91, `tol_pct: 0.5` | **`waterfall.network.gps_pct_2025`** | **51.1** network |
| `metrics_snapshot.json` | same waterfall key | 51.1 |
| `FACTS.md` line 128 | "the 51.1% GPS anchor never moved" | locked |

So the **only drift-gated GPS anchor in the estate** is the waterfall construction — the one I
used — and the dictionary names a different file as canonical. That is not a distinction I can
settle by reading; it is a decision.

**And the deeper finding:** the two ceilings differ because `uio_by_model_bucket.csv` has no N35
bucket at all, while `uio_v19_gps.json` does. v19's split (48.7% N35 / 47.7% N75 / 3.6% F) matches
the measured UK warranty VIN mix (61 / 33 / 6) far better than the collapsed bucket does. So the
**precise defect is the missing split**, and the right answer is to fix the bucket file — not to
switch which of the two published figures we quote.

### PMS

| # | Surface | Figure | Expected units | Rests on |
|---|---|---:|---:|---|
| 1 | `pms_capture_by_db_year.csv` | **65.9%** | 75,337 | filed factors, 14 categories, all vehicles |
| 2 | `pms_summary_by_db.csv` | **65.9%** | 75,337 | same, weighted |
| 3 | `pms_capture_by_db_year.csv` genuine | **55.0%** | 75,337 | genuine lines only |
| 4 | `pms_opportunity_matrix.csv` gap | **€1.32M** | — | sum of 14 categories |
| 5 | IML v7 lane (`iml_v7_ituk_cy2025.yaml`) | **35.1%** oil filter | 27,986 | 22,389 DVLA × 1.25/yr, for IML |
| 6 | `leakage_packs/..._ITUK.html` | **83.0%** | 65,671 | sourced intervals, 5 of 12 families |
| 7 | Forecast weight scaffold | 131.3% oil filter | — | 2023 billing |
| 8 | `metrics_snapshot.json` | 154.4% oil filter 2023 | — | pinned anchor |
| 9 | `90_INBOX` review note | **94.4%** | — | a review, matching nothing shipped |

**Nine PMS readings for one market-year.** Surfaces 1 and 2 agree. Surface 6 is the corrected
figure from today. Surface 5 is a different lane by design. Surfaces 7, 8 and 9 agree with
nothing.

### Where the disagreement is legitimate, and where it is not

| Pair | Legitimate? |
|---|---|
| #2 vs #3 (total vs ex-warranty) | **Yes** — different question, but warranty must be stated |
| #1 vs #2 (two ceilings) | **No** — same question, two answers, 14.6 points apart |
| #1 vs #5/#6 (ceiling construction) | **No** — surfaces that read the file it feeds contradict it |
| IML 35.1% vs PRISM 65.9% | **Yes** — documented two-lane design |
| #7, #8, #9 | **No** — orphans; nothing reconciles them |

## 2. The single cause behind almost all of it

Almost every disagreement traces to **one missing split**: N35 versus N75 inside `cv_std`.

```
uio_by_model_bucket.csv   ->  cv_std 22,191  +  f_series 877        (no N35 split)
uio_v19_gps.json          ->  N35 10,900 + N75 10,684 + F 805      (has the split)
```

Because only one of the two files has the split, and only one of the two GPS target sets
distinguishes N35 (€296) from N75 (€739), the same fleet prices at two different ceilings. From
that, the same billing reads as two different GPS percentages, in two different dashboard
families, both of which are internally consistent and both of which pass every check.

The PMS side has the same shape: `pms_capture_config.py` carries
`"cv_std": 0.5, # PROVISIONAL — LD+MD collapsed... pending a real IML LD/MD interval split`.
The split arrived in v19 and was never applied back.

## 3. How this survived months — the honest account

Jerome's actual question. Answering it properly, because "it was a bug" is not the interesting part.

### 3.1 Every check I ran was a check of internal consistency

The 116-check verification report, the reconciliation harness, the pipeline tests — every one asks
*"does A equal B"*. None asks *"is A the right construction, and does everyone publish A?"*
A figure and its contradiction both pass. That is why a green report and six GPS percentages
coexist, and it is the single most important reason this lasted months.

### 3.2 The checks that would have caught it were skipped

`gps_reconciliation_report.json` says **PASS**, with 7 of 14 hard checks `SKIP` under `--skip-raw`:
raw-billing, transport sidecar, surcharge sidecar, unmapped payers, waterfall-vs-raw,
allcustomers-vs-raw. The waterfall check is exactly the one that compares the two ceilings. It
did not run, and the verdict still read PASS.

### 3.3 The definitions live in six places with no precedence rule

| Place | Says |
|---|---|
| `pms_capture_assumptions.yaml` | addressable 100% |
| `metric_dictionary.md` table | addressable **70%** |
| `metric_dictionary.md` narrative | addressable 100% |
| `FACTS.md` §2 | addressable 100% |
| `gps_model_targets.csv` | N75 €739 |
| `gps_model_targets.py` docstring | N75 **€1,120** |
| `gps_engine.py` | flat **€150** |

Nothing says which wins. A reader picking any one of them is being reasonable and getting a
different answer.

### 3.4 Prose was never tested against values

The addressable 70/100 contradiction and the 739/1,120 contradiction are both *prose versus data*.
No check compares a docstring or a markdown table to the value the code loads. They drifted
independently and both looked authoritative.

### 3.5 The one reconciliation that existed was written down and not acted on

`05_memory/projects/gps-reconciliation.md`, **2026-07-03**, states in plain text that the v9
snapshot the GPS dashboards embed is hardcoded to 12 June, runs 2–4.5% low, with UMI −20% and
UTI −7.5%, and logs it as a soft WARN *"pending Jerome's decision"*. That decision was never
asked for. The dashboard has published the stale constants for ten weeks.

### 3.6 Placeholders were never marked, so they read as measurements

A 0.25 rotor factor, a flat 20,000 km mileage, a 47% manual-transmission convention, a 96%
`cv_std` bucket. Each is an assumption. None was rendered differently from a measured figure, so
each was read as fact — including by me, in the pack I built.

### 3.7 My own contribution

I have to be specific, because three of the nine PMS readings and three of the GPS readings exist
because of me.

1. **I chose the wrong ceiling and did not ask why a second one existed.** I read
   `wallet_waterfall.csv`, found a `gps_pct` column, used it, and shipped a 32.4% headline. The
   correct figure — 47.0% — was already published in `isze_data.json`, the feed the dashboards
   themselves read. I did not look at it because I was building a new tool rather than reading
   what already existed.
2. **I put 32.4% and 47.0% in the same panel** and wrote a note calling them "two questions" that
   are "never averaged together". That is worse than the error: it made a contradiction sound
   deliberate. Those two lines are in the live file now.
3. **I took the reconciliation's PASS at face value** without opening it and seeing half the hard
   checks were skipped.
4. **I checked one source and called it the truth, twice.** I said the clutch family "has no
   replacement interval anywhere" after searching only the GIDSS schedules. The IML v7 lane
   carries one. I said the AdBlue interval was uncontested after checking one schedule. That one
   happened to be right.
5. **I added a ninth PMS denominator today** without reconciling it to the 65.9% already
   published, so the alignment problem got slightly wider before it got narrower.

Items 1 and 4 are the same mistake: **I searched for the answer to my question and treated the
first credible source as the whole answer.** I never asked "who else publishes this, and do we
agree?" That question would have cost one grep.

The pattern in all five is identical: **I verified my own work was internally consistent and never
verified it agreed with everyone else's.** For a workspace whose whole purpose is one number
everyone can trust, that is the wrong instinct, and it is why the mistakes recurred rather than
being caught once.

## 4. Alignment I would put in place

Not more of the checks that already pass.

| Fix | What it does | Effort |
|---|---|---|
| **One definitions file** | Target rates, addressable %, service intervals live in exactly one file. The CSV, the docstring, the markdown and the JSON are generated from it or deleted. Kills §3.3 and §3.4 permanently. | small |
| **Cross-surface equality check** | Assert that every surface publishing a metric for a market-year returns the same number. Fail the build on disagreement, not on inconsistency. Would have caught the €5.34M gap on day one. | small |
| **Stop skipping, or say so loudly** | A report with skipped hard checks must not print PASS. It should print `PARTIAL`. | trivial |
| **N35/N75 split into the bucket file** | Closes the root cause: one ceiling, one percentage. Requires a PRISM engine change. | medium |
| **Placeholders rendered as placeholders** | Any figure resting on an assumed interval, mileage or bucket renders differently from a measured one. Done on the leakage tool; nowhere else. | medium |
| **Orphan sweep** | Every published figure traced to the file it came from; anything untraceable deleted. Removes readings 7, 8 and 9. | small |

## 4a. What the two forensic audits added

Two independent read-only audits returned after this report was drafted. They found materially
more than I did, and three of their findings change the picture.

### GPS: eight percentages, not six, and five distinct denominators

| # | Denominator | ITUK | UTI |
|---|---|---:|---:|
| 1 | Per-model ceiling (296/739/887/250) — **the drift-gated anchor** | **32.4%** | 40.3% |
| 2 | v9 max-spend workbook, warranty in | **47.0%** | 40.3% |
| 3 | v9 max-spend, warranty out | 43.9% | 37.2% |
| 4 | v9 snapshot, a third vintage — **stale, flagged by its own memo** | 45.6% | 34.9% |
| 5 | Flat €150 per vehicle (`gps_engine.py` line 33) | **165.7%** | 214.9% |
| 6 | Flat €739.2 rate for ITUK and UTI alike (`gps_master.csv`) | **31.8%** | **31.8%** |
| 7 | Operating-dashboard FY spine | no % published | no % published |
| 8 | Network genuine-only | 49.3% vs 51.1% anchored | — |

New findings I had missed:

- **`gps_master.csv` gives ITUK and UTI the identical flat €739.2 rate.** UTI therefore reads 31.8%
  against a truck rate its fleet does not match. The Sales-Review blueprint already warns about
  exactly this, and the file is still live.
- **The GPS fleet dashboard publishes 48.7% and 45.6%** — a third vintage, on a sales column its
  own reconciliation memo flags as stale for ITUK by 3.6%.
- **The network figure is published twice, disagreeing:** `MASTER_DASHBOARD.html` and
  `ISZE_Risk_Cockpit.html` print **49.3%** (genuine only) while the anchor pins **51.1%**
  (genuine + BVP). Root cause: `build_risk_cockpit_viz.py` line 73 uses `genuine / wallet`.
- **Legacy units are still live:** 165.7% and 214.9% of a flat €150 target are computed by a helper
  in the same engine, and that is the *only* definition the metric dictionary documents.

### PMS: nine constructions, and the capping is worse than I knew

- **Capture is capped at 100% in eleven places**, including a hard `min(..., 1.0)` in a forked
  engine at `03_analytics/Isuzu/gps_dashboard/modules/pms_engine.py` line 386.
- **`metrics_snapshot.json` carries a wrong provenance note:** it pins 116.4% and 23,068 UIO while
  the note says "22389 x 0.5 svc/yr x **70%**". Wrong UIO *and* wrong addressable percentage.
- **`capture_recovery_model.csv` is built on Jan–Mar 2026 actuals against a full-year denominator**,
  and nothing on the file flags it. ITUK oil reads 0.2844 there versus 1.1643 for full CY2025.
- **`pms_briefs/*.md`** — 17 of 18 files predate the July re-base and publish the IML lane from
  inside `00_derived/`, next to the CSV that contradicts them.
- **An archived UTI deck publishes 194.8%** capture that reconciles with nothing. No live builder.
- **The ITUK operations ledger tells readers not to use `pms_summary_by_db.csv`** because it
  "contains 2026 only" — stale advice; the file is now 2025-only and is the correct league file.
- **A forked engine** with hardcoded parcs (8,515 N75 / 9,818 N35) produces a denominator ~2.7×
  smaller. No live page imports it, but it is not marked deprecated.

### The one thing both audits agree on, and it is the real answer

`uio_by_model_bucket.csv` has no N35 bucket. Every GPS discrepancy above traces to that, and the
same collapse is written into `pms_capture_config.py` as a flagged provisional. **Fix the split and
most of these eight GPS percentages collapse into one.** Everything else here is downstream.

## 5. Decisions only Jerome can take

1. **Which GPS construction is canonical.** I am no longer confident enough to recommend one. The
   drift gate anchors the waterfall (51.1% network, ITUK 32.4%); the dictionary names
   `gps_spu_by_distributor.csv` (ITUK 47.0%); and the v19 split better matches measured VIN data.
   My recommendation is now: **fix the N35/N75 split first, then re-decide**, because that is the
   only path where the two answers converge instead of one being chosen over the other.
2. **Addressable: 70% or 100%.** The percentage scales modelled expected demand and nothing else
   (`pms_engine.py:333`), so every PMS capture figure moves by the inverse — at 70%, ITUK oil
   filter goes from 65.9% to 94.2%. It does not touch GPS, and it does not touch actual sales. In
   euro terms, 100% treats the whole €24.5M network gap as claimable; 70% declares about €7.35M of
   it structurally unreachable. **The evidence argues for keeping 100%:** three ITUK families
   already bill more than the model says can exist (oil filter 116.4%, fuel filter 157.0%, brake
   rotor 197.7%) while the basket reads 65.9%. At 70% the brake rotor would read 282%, hiding
   rather than exposing the error. When the model says more was sold than exists, the demand
   figure is too low — the knob is `services_per_year` for wear parts, not the share of the fleet.
   Unless you tell me otherwise I will leave 100% in place and treat the dictionary table as the
   corrected one.
3. **Whether the GPS dashboards get rebuilt off the June snapshot**, and whether the 48.7/45.6
   vintage is retired.
4. **The manual-transmission split** — 10,549 or 23,068 clutch-capable vehicles, worth ~€250K of
   gap on ITUK alone.
5. **Retire or re-derive the orphaned UTI artifacts** (the 194.8% archive and the builder-less
   `uti_iml_v7_results_2026-07-06.json`).
6. **Retire `gps_master.csv`'s flat rate**, or label it so no deck can quote UTI at 31.8%.

Until 1 and 2 are answered, I would not put a GPS or PMS percentage on any page that leaves the
building. That is a real constraint, and it is the honest position.

---

## Artefacts

- Alignment extract: `02_dashboards/_build/leakage/_align.json` (30 surface readings)
- Rendered check of what each page shows for ITUK: `_align2.py`
- Root-cause detail: `00_docs/GPS_PMS_TRUTH_REPORT_20260917.md`
- Skipped-checks evidence: `01_data/00_derived/gps_reconciliation_report.json`
- The July diagnosis, not acted on: `05_memory/projects/gps-reconciliation.md`


---

## C. GPS truth report (full)

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


---

## D. LD / light-heavy correction note

# The "LD" weight label, and what it does to the parts wallet

**Written:** 2026-09-18 · read-only, no source file modified
**Question:** (1) is Israel's "CV LD" parc really 3.5-tonne trucks, as the label implies?
(2) can the mileage measured from warranty odometers be read as the total parc?

---

## 1. Verdict on the Israel question

**The "3.5-tonne" reading of Israel's light row is wrong, and the wallet happens to be right anyway — for
a reason nobody wrote down.**

Two independent sources say UTI's Israeli parc contains no 3.5-tonne Isuzu truck:

**Source A — the CV warranty VINs (2023-12 → 2026-03, 3,394 claims / 2,360 distinct VINs, all `UTI`):**

| Chassis code in VIN | Distinct VINs | Class |
|---|---:|---|
| `NPR75` | 895 | 7.5 t |
| `FRR90` | 817 | F-series |
| `FSR90` | 627 | F-series |
| `NPR85` | 13 | 7.5 t |
| `NPR88` | 8 | 7.5 t |
| any `NLR` / `NKR` / `NMR` (3.5 t) | **0** | — |

**Source B — the Israeli Ministry of Transport class table** (already in `06_uio/_CURRENT/V20_SPEC.md`
§Problem 4, from UTI's July presentation): at 30 June 2026 the smallest UTI class is **6.5–7.5 t with
8,610 trucks**, then 7.6–10 t 2,485, 10.1–12 t 2,697, 12.1–16 t 227, total **14,019**. There is no
3.5-tonne band.

Neither source alone is conclusive — A measures vehicles that *claimed* in a 28-month window, B is a
picture of the whole fleet. Together they leave no room for the "6,059 light-duty (3.5 t) units" reading.

### Why the wallet is right by accident

`prism/modules/gps_model_targets.py` maps a model literally named `"LD"` to **N75_N50_N62 = €739**, not
to the Grafter rate. Verified by calling the function:

```
"LD"     CV -> N75_N50_N62  €739
"MD"     CV -> F_Series_MD  €887
"N35"    CV -> N35_Grafter  €296
"NLR"    CV -> N35_Grafter  €296
```

So Israel's 6,059 units are being priced at €739 — which is the *correct* rate for a 7.5-tonne NPR75.
**The number is not wrong; the label is.** Anything that reads "LD" as light/3.5 t (V20_SPEC's §Problem 6
table, the `N35_Grafter` dead-configuration note, any future market split) will be wrong about Israel.

### What is actually wrong, and where it costs money

The `LD` row means a different physical vehicle in every market:

| Market | Share of the `LD` row that is really 3.5 t | Source |
|---|---:|---|
| ISRAEL | **0 %** | CV claims (2,360 VINs) + ministry table |
| ITALY | 92.8 % | CV claims |
| SWITZERLAND | 97.6 % | CV claims |
| FRANCE | 89.8 % | CV claims |
| PORTUGAL | 62.0 % | JP VIN register (2,111 shipments) |
| GERMANY | 44.3 % | JP VIN register (183 shipments) |
| MALTA | 36.9 % | JP VIN register (130 shipments) |
| BELGIUM | 91.8 % | JP VIN register (49 shipments) |
| UK / ITUK | 50.5 % | UIO workbook sheet `2. Vehicle Volume` §B (already wired) |

A label that means 0 % in one market and 98 % in another carries no information. The fix has to be per
market and has to come from VIN data — which is exactly the "older years need a source" gap V20_SPEC
§Problem 6 left open. **Two sources now close it for seven markets plus the UK**, and they agree with the
"shipped 2020–2026" proxy the spec already used (Portugal 62.0 % measured vs 68.5 % proxied).

**Correction to V20_SPEC §Problem 6:** its table shows Germany, Malta, Cyprus and Greece at "0 % 3.5 t,
no change". The JP VIN register shows **Germany 44.3 % (81 of 183)** and **Malta 36.9 % (48 of 130)**.
Germany's wallet is €3.81 m, so this is not a rounding item.

---

## 2. Measured wallet impact per market

Wallet = Σ(units × rate) on the UIO workbook 2025E rows; "now" prices every `LD` unit at €739.

| Market | `LD` 2025E | Wallet now | Wallet, measured mix | GPS % multiply by |
|---|---:|---:|---:|---:|
| PORTUGAL | 2,206 | €3,052,087 | €2,446,063 | **×1.248** |
| MALTA | 243 | €378,827 | €338,957 | **×1.118** |
| GERMANY | 697 | €3,808,128 | €3,671,241 | ×1.037 |
| IRELAND | 731 | €956,313 | €938,150 | ×1.019 |
| BELGIUM | 113 | €2,446,507 | €2,400,435 | ×1.019 |
| GREECE | 37 | €953,593 | €945,397 | ×1.009 |
| CYPRUS | 203 | €676,267 | €671,394 | ×1.007 |
| ISRAEL (UTI) | 6,059 | — | **unchanged** | ×1.000 |

Portugal reproduces the V20_SPEC headline (€3.05 m → €2.38 m on the 68.5 % proxy; €2.45 m on the measured
62.0 %), so the "Portugal's GPS % is understated by about a quarter" conclusion **holds** — the exact
multiplier moves from ×1.28 to ×1.25.

ITUK is the only market already handled: `data_prep._split_collapsed_ld_rows` divides its `LD` row using
the workbook's own section 2.B (N35 10,900 of 21,584 = 50.5 %).

---

## 3. Is the warranty odometer representative of the fleet?

**Partly. It is a real measurement on a biased sample, and the bias is disclosed rather than corrected.**

The estimator in `_cv_warranty_mileage_validation.md` is Method C: odometer at claim ÷ years since
`RETA6`. Its limits, stated plainly:

1. **A vehicle appears only if it claimed.** The file window is 28 months wide (Dec 2023 → Mar 2026), so
   no rate above ~2.5 years of age is reachable and the sample skews to vehicles young enough to have had
   a warranty repair.
2. **`RETA6` is not documented.** It behaves like a retail/first-registration month (0.3 % negative
   retail-to-repair gaps, reaches back to 2014-06 while every other date stops at 2023). If it is actually
   the *sale-to-dealer* date, every rate is understated by the dealer stock period.
3. **Honesty test on the derived rate.** For each VIN, first claim ÷ (first-claim date − `RETA6`). If a
   subset of the `RETA6` values were documented registration dates rather than true retail dates, that
   subset would show an implausibly low implied rate. It does not:

| Market | VINs | median implied km/yr | share implying <2,000 km/yr |
|---|---:|---:|---:|
| ISRAEL | 1,953 | 46,152 | 0.1 % |
| UK | 5,421 | 15,089 | 3.4 % |
| SPAIN | 1,076 | 17,903 | 4.0 % |
| ITALY | 5,385 | 10,637 | 5.8 % |
| PORTUGAL | 249 | 20,709 | 6.8 % |
| FRANCE | 1,243 | 8,738 | 7.7 % |

No market is hiding a block of false registrations, and this recomputation independently reproduces the
published Method C medians (Israel 51,680 vs 46,152 here; UK 16,688 vs 15,089) within the estimator-settings
band the reconciliation note already recorded (−2.8 % to −9.8 %).

4. **A second, estimator-free check agrees with it.** Median odometer *reading* at 2–3 years of vehicle
   age, no division at all:

| Market | all classes | N35 | N75 | F-series |
|---|---:|---:|---:|---:|
| ISRAEL | **132,098** | — | 115,301 | 136,015 |
| PORTUGAL | 51,165 | 31,208 | 86,580 | 44,531 |
| SPAIN | 41,334 | 39,950 | 119,485 | 41,953 |
| UK | 38,548 | 30,646 | 87,996 | 54,931 |
| ITALY | 24,932 | 24,592 | 32,207 | 29,535 |
| FRANCE | 21,578 | 21,068 | 36,708 | 45,200 |
| SWITZERLAND | 20,105 | 20,105 | — | — |

Israel's trucks read 132,000 km at two to three years; Switzerland's read 20,000. A 6.6× spread cannot be
produced by a defective date field.

### The one genuine representativeness problem

`milleage` is measured on **claiming** vehicles. The UK is the market where that matters most, because
ITUK is the only book whose 50,000 km/yr assumption the data contradicts (measured 16,688 across classes,
35,478 even for N75 alone). If the UK claim population is a young or urban subset of the parc, the median
is not the parc. Stated limit, and the single question that resolves it: ask ITUK for the average annual
mileage of the N-series parc, the same question UTI was asked.

**What the data *cannot* carry, at any sample size:** fleet age (claim age is not parc age — the real UK
number is 6.86 years for N75 from the DVLA/SMMT cohort table in
`ISUZU_UIO_Overview_2026_v19.xlsx!4. ITUK UIO Projection`), and the non-claiming tail of any market.

---

## 4. What was applied, and when

Applied 2026-09-18, on Jerome's approval, in three places.

### 4.1 UIO workbook — label only, no number touched

`06_uio/_CURRENT/ISUZU_UIO_Overview_2026.xlsx`. The `LD` label now says what it is, and Israel's row
carries the explanation. Every numeric cell, every formula, all three charts and all four images in
the file are byte-identical to the previous revision — verified by comparing the zip parts after the
edit. A full backup sits at
`06_uio/_Archive/ISUZU_UIO_Overview_2026_backup_before_ld_relabel_20260918.xlsx`.

Changelog rows V19-5 to V19-7 record it. The note was placed in **B92** of `1.UIO Overview`, not in
D7, because the PRISM loader reads column D as a machine field and a paragraph there becomes a model
name.

### 4.2 PRISM — the wallet split, per market

`03_analytics/Isuzu/prism/modules/data_prep.py` now splits the collapsed `LD` row for every market
with a measured share, not just the UK. Table: `03_analytics/Isuzu/prism/data/uio_ld_n35_share.csv`,
keyed on distributor code, with the basis named per row.

Measured effect on the 2025E target wallet: Portugal ×0.801, Malta ×0.895, Ireland ×0.979,
Belgium ×0.981, Germany ×0.982, Cyprus ×0.993. Israel and the UK unchanged. Full test suite green
(71 passed).

### 4.3 JP VIN register — the tonnage decode

`01_data/07_UIO/vin/build_vin_register.py` now takes GVW from the series, not from the number in the
chassis code. Rebuilt: the register reads **19,545 t over 3,238 trucks, 6.04 t average**, against
26,689 t / 8.24 t before. `gvw_t_source` is a new column so any fallback to the numeric code is
visible rather than silent. The old `gvw_t` by series was wrong: NLR 8.5–8.8 t (a 3.5 t truck),
NMR 8.5–8.8 t (5.5 t), FRR and FSR both 9.0 t (11–12 t and 13.5 t).

### 4.4 ITUK mileage question — drafted, not sent

`09_meetings/ITUK_MILEAGE_QUESTION_2026-09-18.md`. Addressed to Duncan Young, plain text, draft only.
It asks for the average annual mileage of the N-series parc with an N35/N75 split if available, and
explains why the VIN file he sent cannot answer it (no mileage column).

---


Sources read-only: `01_data/06_Warranty/*.xlsx` (5 claim sheets), `06_uio/_CURRENT/ISUZU_UIO_Overview_2026.xlsx`,
`01_data/07_UIO/vin/VIN_register.parquet`, `03_analytics/Isuzu/prism/modules/{gps_model_targets,data_prep}.py`,
`01_data/01_Pricing/_raw/Price_file_2026_full.xlsx`.


---

## E. Warranty — what else the claim files carry (limits)

# Warranty data — what else it carries

**Date:** 2026-09-18 · **Read-only.** No source file was modified. Numbers below are measured, not
modelled. Estimator and sample limits are stated where a figure could be misread.

> ## Correction — 2026-09-18 19:00, truck euro figures
>
> The **truck** euro figures in this note were computed by summing the claim file's amount column
> raw, and that column mixes three currencies. The CV file's `CRNCY` field carries two tokens:
> **`EUR GBP` means the amount is in POUNDS** (UK — 11,956 lines, the largest book in the file) and
> **`JPY EUR` means YEN** (Italy, Spain, France, Switzerland and others). Corrected figures:
>
> | In this note | Actually |
> |---|---|
> | Truck parts turnover "€2,826,045" | **€4,655,881** |
> | Emissions "€1,819,033 — 64% of CV parts value" | **€2,838,570 — 61%** |
> | Truck power steering gear "€800,191" | **~€1,150,000** |
>
> The **D-Max / LCV** figures are unaffected — that export is flagged per line and was normalised.
> The corrected, reproducible version of everything here is now a dataset folder:
> `01_data/00_derived/warranty_commercial/` (see its README), built by
> `01_data/91_build/build_warranty_commercial_datasets.py`. Shares and medians in this note stand;
> any absolute truck euro below should be read against the table above.

**Question asked:** what more can we get out of the warranty estate, with a commercial lens.

Sources: `01_data/00_derived/warranty_fy26_raw.csv` (LCV / D-Max claim export, AssessMonth
202504–202603, 20,383 lines) and the five claim-level sheets in `01_data/06_Warranty/*.xlsx`
(CV trucks, 33,416 lines after de-duplication, 22,732 distinct VINs, Dec 2023 → Mar 2026).

---

## 1. The hypothesis that died, and it is the one worth recording

**The warranty files carry no maintenance. Wear-part replacement intervals cannot be measured from
them, and the plan to replace the assumed 40,000 km service interval with a measured one is dead.**

| Part family | CV claim lines | LCV claim lines |
|---|---:|---:|
| Oil filter | **8** | 2 |
| Air cleaner element | **0** | 2 |
| Fuel filter | 10 | 19 |
| Brake pad | **0** | 33 |
| Brake rotor / disc | **0** | 48 |
| Clutch | 47 | 102 |
| Battery | 451 | 444 |

*Why this is the right answer and not a bug:* a consumable replaced at a scheduled service is not a
defect, so it is not a warranty claim. The files contain failures and defects only. A `SERVICE
PROGRAMMING SYSTEM - REPROGRAM` line at €0 or €1 is administrative.

**Consequence.** Measured service intervals and the `air_filter: 0.5` factor must come from the
dealer repair-order data or from an actual parts-sales basket by part number — not from warranty.
Do not spend more time looking in the claim files for them.

---

## 2. What the four unused fields actually contain

| Field | Verdict |
|---|---|
| **Dealer code** (`DLR`, 29 distinct, 100% populated) | **Usable and materially interesting.** The top code, `V19010`, carries **11,956 claim lines — 36% of the entire CV claim file** across all 21 markets. `V18840` 10,989 (33%), `V11110` 3,394 (Israel/UTI). One service point generating a third of a network's truck claims is either a very large fleet account or a process problem. Worth a look with the market. |
| **Second part line** (`PARTNBR2` / `QTY2` / `PARTAMT2`) | **Empty in CV** — 0 of 33,416 lines carry a second part number or amount, and the second amount column is present but always blank. **This settles the 33,416 vs 16,480 question explicitly:** the claim line has two part slots and only slot 1 is used, so the line count is the true claim count and the "16,480" figure — exactly half — was a double-count, not a halving. |
| **Labour** (`LBRAMT`) | **Not usable across markets.** Labour is 0.3% of cost in Italy against 29.5% in the UK, Portugal 9.2%, Germany 13.9%. That spread is a recording convention, not a cost difference. Usable for within-market comparison only, and even then with care. |
| **Failure code** (`TR_CD`, 76 distinct) | **Mostly administrative, with one real use.** Code `96` carries **22,179 lines — 66% of all claims — and only 1.2% of them have a part number**; its top operations are urea-sensor replacements, DPF work and reprogramming. Codes `50` (5,645 lines, 89% with a part number), `1`, `56`, `42` and `6` are genuine repair categories. **Use:** exclude code 96 to get a clean parts-defect view; its median odometer is 14,414 km against 39,363 for code 50. |

**A data-quality caveat that governs everything below.** The share of claim lines carrying **no real
part number** is wildly uneven by market: Czech 95%, Switzerland 90%, Italy 87%, France 83%, Spain
74%, UK 63% — against Israel 23%, Germany 23%, Portugal 17%, Ireland 8%. So any euro analysis on
this file is thinner in the German-owned markets (Italy, France, Spain, Switzerland, Czech) than in
the ISZE-owned ones. Any part-number ranking must say this on its face.

---

## 3. The commercial read — where warranty cost concentrates

### 3.1 On D-Max, it concentrates on running gear and electronics, not on the engine

Parts turnover by component family, LCV export, lines carrying a real parts charge:

| Family | Turnover | Share | Part numbers |
|---|---:|---:|---:|
| Steering | €821,331 | **23%** | 24 |
| Electrical & electronics | €595,948 | **17%** | 142 |
| Emissions aftertreatment | €289,524 | 8% | 38 |
| Powertrain (engine / turbo / injection) | €228,559 | 6% | 63 |
| Cooling | €151,019 | 4% | 26 |
| Transmission & driveline | €131,815 | 4% | 75 |
| Body, cab & interior | €90,805 | 3% | 198 |
| Cabin comfort & infotainment | €81,814 | 2% | 35 |
| Brakes | €24,685 | 1% | 54 |
| Filters & service items | €6,563 | 0% | 17 |

Steering and electrical are **40%** of the bill on 166 part numbers between them. That is a narrow,
actionable list.

### 3.2 One repair line dominates everything else

| Repair line | Lines | Turnover | Per truck | Median km | Median age | Markets |
|---|---:|---:|---:|---:|---:|---:|
| **Power steering gear — replace** | 329 | **€800,177** | **€2,432** | 44,181 | 2.7 yr | **22** |
| PM sensor — replace | 900 | €253,023 | €281 | 62,381 | 3.2 yr | 26 |
| Urea tank — replace | 112 | €135,081 | €1,206 | 45,836 | 3.2 yr | 15 |
| Emergency call unit — replace | 155 | €125,672 | €811 | 65,500 | 3.4 yr | 21 |
| Turbocharger — replace | 86 | €70,386 | €818 | 33,505 | 1.6 yr | 15 |

The steering gear is **one part number family, present in 22 of 30 markets on D-Max, and it fails at
2.7 years — inside the warranty**. At €2,432 a truck it is 23% of the entire D-Max parts bill on 1.6%
of the lines. **On trucks it is a minor line** — €29,671 across 35 claims in 7 markets — so do not
read the D-Max concentration onto the truck book. *(This replaces an earlier estimate of ~€1.15M for
the truck figure, which was wrong. See the correction in §3.5.)*

### 3.3 Warranty is a replacement programme, not a maintenance programme

Position of LCV repair lines against the stated limits:

| Position | Lines | Turnover | Share | Per line |
|---|---:|---:|---:|---:|
| Inside both limits (under 3 yr **and** under 100,000 km) | 8,232 | €2,029,883 | **58%** | €247 |
| Over 3 years | 3,727 | €1,328,328 | **38%** | €356 |
| Over 100,000 km | 480 | €157,809 | 4% | €329 |

**42% of parts turnover sits outside the limits** — overwhelmingly on age, not on distance. And the
per-line cost outside is **1.4×** the cost inside: a truck that has run out of years still gets the
expensive repair.

By market, as the share of that market's turnover sitting outside the limits:

| Market | Outside % | Market | Outside % |
|---|---:|---|---:|
| Norway (RSA) | **68%** | France | 54% |
| Malta | 64% | Ireland | 50% |
| Austria | 62% | UK | 37% |
| Switzerland | 58% | Romania | (small n) |
| Belgium | 46% | Sweden | **25%** |

That is a commercial question per market, not a technical one. A book where two thirds of warranty
turnover is outside the limits is buying loyalty; a book at 25% is applying the terms strictly.

### 3.4 The settlement rate varies by a factor of 3.7, and one market is an outlier

Parts claimed against parts admitted, LCV export, markets with 100+ lines:

| Market | Admitted ÷ claimed | Market | Admitted ÷ claimed |
|---|---:|---|---:|
| **Belgium (IBX)** | **47%** | Greece | 141% |
| Cyprus | 70% | Poland | **173%** |
| Finland | 86% | Portugal | 139% |
| Malta | 98% | Germany (ISD) | 138% |

Belgium recovers less than half of what it claims for parts. Poland's admitted parts value exceeds
its claim. Both are worth a question; neither is explained by the data here.

### 3.5 On trucks, the emissions hardware is the bill, and no single line dominates

**Correction, 2026-09-18 21:00 — the truck steering figure quoted earlier was wrong.** The paragraph
below used to say the power steering gear was "the largest line in the truck file at about €1.15M".
That was an estimate, and it is wrong. Now that the truck repair lines have actually been aggregated:

| Truck repair operation | Parts € | Claims | Markets | Median odometer |
|---|---:|---:|---:|---:|
| DPF filter — R&R | **821,661** | 575 | 8 | 125,707 km |
| Urea pump — replace | **780,371** | 589 | 15 | 20,900 km |
| Urea sensor — replace | 366,408 | 913 | 16 | 22,779 km |
| NOx sensor in — replace | 332,998 | 772 | 11 | 160,560 km |
| NOx sensor out — replace | 300,445 | 729 | 9 | 180,906 km |
| Meter board assembly — replace | 224,941 | 344 | 10 | 10 km |
| **Gear assembly, power steering — replace** | **29,671** | **35** | **7** | — |

The steering gear is the **largest single line on D-Max** (€800,177 on 329 claims) and a minor one on
trucks: €29,671 on 35 claims in 7 markets. **The two fleets have different bills and the D-Max story
must not be read onto the truck book.** Dataset added so this cannot recur:
`warranty_cv_top_repair_lines.csv`. The D-Max figure was always correct and is unaffected.

CV parts turnover by family: **DPF, urea pump and tank, dosing module, NOx and O2 sensors, SCR
catalyst and EGR filter total €2,838,570 of €4,655,881 — 61% of all CV parts value.** On D-Max the
same parts are €289,524, 8%. A truck's warranty bill is an aftertreatment bill; a pickup's is not.

---

## 4. The UK duty-cycle question — downgraded, not confirmed

**What raised it.** Every one of the 15 D-Max repair lines with enough volume in both samples shows
the UK repairing **earlier** than six mainland and Nordic markets combined. Median ratio across the
15 lines: **0.70**. Examples: steering gear UK 29,624 km vs peers 48,094; PM sensor 45,111 vs 62,323;
sub-radiator 27,949 vs 55,024. On trucks, where the UK is 64% 3.5 t against Italy's 93%, the UK
still shows a **higher** median odometer on every claim (22,820 vs Italy 13,200) — which argues the
UK gap is not explained by vehicle weight class.

**Why it is not a clean finding.** The per-market split shows the UK is not unique:

| Repair line | UK | France | Norway | Germany | Sweden | Portugal | Italy |
|---|---:|---:|---:|---:|---:|---:|---:|
| Power steering gear | 29,624 | 62,848 | 54,774 | 43,293 | **17,008** | 31,363 | — |
| Sub radiator | 27,949 | 37,178 | — | — | 71,908 | — | 43,369 |
| Sunshade left | 16,780 | 24,046 | 24,114 | 22,230 | 37,363 | 23,922 | 28,950 |

**Sweden replaces the steering gear sooner than the UK does.** And the near-zero odometer readings
that make the UK look early appear in other books too: the 25th percentile of all D-Max claim
odometers is **526 km in Sweden** and **12 km in Portugal** against 12,112 km in the UK. A claim
recorded at 12 km is a booking convention, not a measurement.

**Conclusion.** There is a real spread in odometer-at-repair across markets and the UK sits at the
low end of it, but the UK is not an outlier and part of the low end is a recording convention. **The
duty-cycle story does not survive on its own, and it should not be presented as one.** The clean
part of the UK question is still the one already recorded: the UK mileage assumption of 50,000 km/yr
against a measured 16,688, which is a different and much larger gap.

---

## 5. What this is worth commercially, ranked

1. **The steering gear is a campaign, not a line item.** One part family, €1.6M across both fleets,
   22 of 30 markets, failing at 2.7 years and 44,000 km — inside warranty. A supplier-quality
   conversation and a revised part number are the levers, and the size of the prize is now measured
   rather than felt.
2. **Warranty is a loyalty instrument in some books and not others.** 42% of D-Max parts turnover is
   outside the limits, and the market spread runs from 25% to 68%. The commercial question is
   whether that is deliberate. Nobody has asked it with a number attached.
3. **The parts-quality story is concentration, not breadth.** Steering and electrical are 40% of the
   D-Max bill on 166 part numbers; emissions is 64% of the truck bill. Two short lists, not a
   1,270-part-number problem.
4. **Belgium's 47% settlement rate and Poland's 173%** are the two clearest process anomalies in the
   file and cost nothing to ask about.
5. **The dealer code `V19010` generating 36% of all CV claims** is either a major account or an
   internal process issue, and nobody has looked.

---

## 6. Sample limits — carry these on any use of the above

- The CV file is **vehicles that made a warranty claim** over a 28-month window. It is not a fleet
  survey and it cannot give fleet age or fleet-wide failure rates.
- The two files cover **different fleets and periods**: CV trucks Dec 2023 → Mar 2026; D-Max
  Apr 2025 → Mar 2026 with the January–March 2026 export carrying 62% labour-only lines against 17%
  in the earlier export.
- Part-number coverage differs by market by an order of magnitude (Ireland 8% missing against Czech
  95%). Euro rankings by part number are weakest in the German-owned markets.
- **All currency conversions are indicative.** The D-Max export is an IMG European export, not one
  currency. Converting JPY at a flat 163.7 introduces a few percent of noise into any non-EUR
  market's absolute euros; shares and medians are safe, absolute euros are not.
- Medians are used throughout because every distribution here is right-skewed. Means are ~1.4× the
  medians and are not quoted.

## Repro

Scratch scripts used (left on disk under `01_data/90_INBOX/`, read-only against all sources):
`_tmp_probe_unused_fields.py`, `_tmp_probe_trouble_codes.py`, `_tmp_probe_lcv_maintenance.py`,
`_tmp_warranty_intervals.py`, `_tmp_warranty_commercial.py`, `_tmp_uk_duty_cycle_cv.py`,
`_tmp_uk_consistency_lcv.py`.


---

## F. Decisions register (open / decided — ceiling & packs)

# Decisions awaiting Jerome

**Register:** `DECISIONS_AWAITING_JEROME_2026-09-19.json` - the JSON is the single source. This page is a rendered twin and must not be hand-edited; re-render it from the JSON rather than editing here.
**Source of truth:** `01_data/90_INBOX/ISZE_ENVIRONMENT_FIX_APPROVAL_SHEET_2026-09-19.md`
**Source note:** Every decision below is extracted from Part 2 of the approval sheet plus its opening 'decision 0' block, or from a companion finding document named in the entry's own source_ref. Two pairs of numbered sheet items are the same question and are carried as one entry each (items 1 and 19, the price chain; items 5 and 13, the fleet-total rule), so 23 register entries cover all 23 numbered sheet items. The companion documents add three more entries (D24, D25, D26), each of which is the companion's own numbered decision rather than a sheet item, so the register now carries 26 entries.
**Generated:** 2026-09-19T22:03:55+02:00
**Status:** 18 open, 8 decided. Nothing in the source sheet has been executed.

**Chat answers are provisional until they are recorded here.** `status` is either `open` or `decided`. There is deliberately no third value: the hook that surfaces this register on Jerome's screen selects strictly on `status == "open"`, and it must not be edited, so any item whose question is still awaiting an answer has to carry `open` or it goes invisible.

**Open: 18.** Blocking 0 · high 2 · normal 16. Ready with no decision: 10 safe-tier repairs.

**How it reaches Jerome.** Hook `.cursor/hooks/decisions-awaiting-on-stop.mjs` (twin in `.codex/hooks/`) reads this file at the end of the first agent turn in a chat and prints the blocking items. Silent when nothing is open, and silent again for the rest of a chat once it has announced a given set of open items.

## Reopened - 2026-09-19

Three items were marked decided earlier today on chat remarks that do not support the closures. They are open again. The test applied is this register's own header rule: a chat remark is not a decision until it is recorded, and a decision recorded on insufficient evidence is worse than an open one.

### D01

**Was recorded as:** decided - label swap approved AND band widened
**Now:** open - the band half stands as a recorded sub-decision, the label swap is not authorised. It was then answered in full - band and label swap - and re-closed the same day; see the D01 entry below.

He said: *"I would say raise the bands so we can set a more competitive price, we should be dynamic in our pricing we have a lot of complaints for our brake parts."*

Why: He was asked two things and answered one. The sentence names the bands and the motive for widening them; it says nothing about which of the two action labels is the inverted one. The direction fix is a separate data-correctness claim whose evidence stands on its own, but it was never put to him as an answered question.

### D03

**Was recorded as:** decided - three-tier chain (1.40 to the distributor, 1.275 to the dealer)
**Now:** open - the three-tier reading is carried as a recommendation only. It was then answered, and answered differently from the earlier closure: the margins reading, not this chain. Re-closed the same day; see the D03 entry below.

He said: *"I provided that in the previous set of 11question."*

Why: That is a claim that he answered it earlier, not a confirmation of the specific reading. He was then asked to confirm the three-tier reading or correct it in one line and has not replied. The reading was an agent inference, recorded as his decision.

### D15

**Was recorded as:** decided - no change, discrepancy recorded as known and deliberate
**Now:** open - deferred for discussion, the 40 percent against 20 percent mismatch is unresolved. It was then answered, and answered against the deferred reading: the configuration is fixed to the 40% margin. Re-closed the same day; see the D15 entry below.

He said: *"This can be discussed keep the same price as it was."*

Why: The only operative instruction is 'keep the same price as it was' - do not change the live price list now. 'This can be discussed' defers the question that was actually asked, which was which of the two margins is correct. A deferral was recorded as a decision.

---

## Blocking — these stop work (0)

None.

---

## High — each holds up a published pack (2)

### D05 — The sales-review gate repair

Approve the staged repair of the sales-review gate, with Stage 0 first - rebuild one pack and diff it, to prove whether the staleness is shape or substance?

**View:** Yes, staged, Stage 0 first. The gate is what stops a bad review from shipping.
**Blocks:** Five checklist checks are absent from the executed path (sold-to population, coded-mix percentage, the above-100 control, the extended-target comparison and fiscal-year rollover). Separately, the gate refuses any profile whose sold-to is 1799, which blocks a legitimate UTI-only review - no UTI profile exists yet, so nothing is blocked today.

**Sheet:** Part 2 decision 3
**Asked on:** 2026-09-19
**Note:** Three corrections to what was said earlier: the freshness check is not broken - it is correctly flagging that sixteen summaries predate the 18 Sep loader change, so those packs really are stale; and the two silent skips are the coded-mix and exclusion checks, not the Power BI check. Added 2026-09-19 late: he directed that these questions stop (see question_flow_stopped). The register's own hook - the mechanism that puts open items on his screen - is outside this recording pass's write scope and was not changed, so this item will still surface until the question flow itself is dealt with as a separate piece of work.
**Question flow stopped:** Jerome, 2026-09-19, verbatim: "stop these questions". This is an instruction about the question flow, not an answer to the question. He asked for these questions to stop being put to him, and that direction is recorded here so it is not lost.
**No answer recorded:** No answer was given. He did not approve the staged repair, did not decline it, and did not pick any part of it. Marking this item decided would be false - no option was chosen and no direction on the gate itself was given. The sales-review gate is unchanged by this record and nothing in it is repaired.

### D24 — Portugal and Malta vehicle-class shares - two of the nine splits are flagged unmeasured

Accept the corrected N35/N75 shares including the two unmeasured ones (Portugal 0.690, Malta 0.369) and rebuild the ceiling on them, or hold the ceiling until the Portugal and Malta distributors can supply parc evidence?

**View:** Rebuild. The corrected split at least labels itself unmeasured, while the basis it replaced was an undocumented guess. Caveat to record with the answer: Portugal is three-quarters of the movement (EUR 674,246 of EUR 929,857) and is a market Jerome knows better than the file does - if he knows the Portuguese light/heavy mix to be different, that one number should be overridden by hand before the rebuild. If he chooses to hold instead, the seven shares with documentary evidence can be accepted now and only Portugal and Malta left pending - that split decision is his to make and this register does not read his answer as either.
**Blocks:** The entire ceiling rebuild chain. Nothing downstream of the ceiling (coverage %, uncaptured value, the flat-EUR-250-per-vehicle placeholder share, metrics snapshot, console tiles, hub, BPR deck, map snapshot, exec paper) can be rebuilt honestly until the corrected shares are either accepted or replaced. The headline movement, from the companion finding: the published EUR 55,253,312 2025 target-spend ceiling is stale because most markets' light trucks were priced at the heavy-truck rate; reproducing it with nothing else changed gives EUR 54,323,455, so coverage rises 55.7% to 56.6% and the uncaptured value falls EUR 24,496,540 to EUR 23,566,683. The fleet base did not change - 163,198 vehicles was already the base; what was wrong was how those vehicles were priced.

**Why the urgency moved:** Kept at high. The evidence half of the question is now answered by Jerome's own statement, so what remains is one commercial input and the rebuild decision behind it. It stays high rather than normal because the ceiling chain, and therefore every number D08 would publish, is still held on it.
**Answered half, stands:** Answered, and it stands: parc evidence for Portugal exists and it settles the light/heavy split. The register was wrong to record the market as having no parc-band source in the workspace, and the 'unmeasured' flag on Portugal is wrong for the same reason. The parc-derived share is 0.6364 on the 2025 basis, not the 0.690 the register assumes.
**Still open, not authorised:** Still open, not authorised. His sentence corrects the evidence question; it does NOT authorise the ceiling rebuild. Nothing in the ceiling chain is approved by this record: the corrected shares are not accepted, the Portuguese share is not replaced, no ceiling is re-based, no coverage figure is recomputed and no builder is run. The rebuild authority sits with D08, which is approved but not run, and D08 does not authorise a re-based ceiling either. The question that actually remains is which Portuguese light/heavy share replaces 0.690 - the parc-derived figure, or a number Jerome sets himself.
**What would close it:** One line from Jerome: accept the parc-derived Portuguese share (0.6364 on the 2025 basis) and with it the rest of the corrected share set, or hold the ceiling, or set the number himself. Writing it into uio_ld_n35_share.csv is a separate data change that needs its own explicit authorisation; this record does not perform it, and no ceiling is re-based here.
**Sheet:** Companion finding - read-only fleet-ceiling investigation, 2026-09-19
**Asked on:** 2026-09-19
**Note:** Folded in from a companion finding document, not from the approval sheet. The document's own limits, carried here unchanged: the exact pre-correction share values were not reconstructed for the markets whose rows were left whole; whether the ceiling file was ever actually rewritten on 18 September was not proven, since its mtime is 17 September 15:38, a day before the shares changed at 22:01 on 18 September; and no distributor parc document for Portugal or Malta was confirmed anywhere in the workspace. Two latent traps were found and neither was fixed - the stale verified anchor in 03_analytics/Isuzu/prism/data/facts_anchor.yaml lines 79-100, which pins coverage against the retired ceiling, and the V18 shadow copy at 03_analytics/Isuzu/prism/config.py lines 206-212, where the unversioned fallback UIO.xlsx is byte-identical to the archived V18 and the check meant to catch it only globs filenames containing v16, v17 or v18, so it is blind by construction.
**Fix site:** 03_analytics/Isuzu/prism/data/uio_ld_n35_share.csv (rows PORTUGAL and MALTA; basis column reads 'unmeasured')
**Source ref:** 01_data/90_INBOX/FLEET_CEILING_CORRECTION_FINDING_2026-09-19.md, section 2
**Evidence correction:** Jerome, 2026-09-19, verbatim: "We have parc evidence of Portugal". This corrects a statement carried in this register and in the share file it names. 03_analytics/Isuzu/prism/data/uio_ld_n35_share.csv holds Portugal with basis=jp_vin_shipments and the note that no Portuguese parc-band source exists in the workspace; this register's fix_site assumed the same. That is wrong - evidence exists, and it resolves the light/heavy split. On the 2025 basis the Portuguese N-series parc is N35 1,521.31 and N75/N50/N62 869.00 vehicles in service, so the light share is 1,521.31 / 2,390.31 = 0.6364 (63.6% light). The 2024 basis gives 0.6386 (1,534.63 / 2,403.02). The register currently carries 0.690, which is not a parc figure at all: it is a JP shipment mix (NLR 1,299 of 1,883 N-series in VIN_register.parquet, and that register covers 2020-2026 only). So the 'unmeasured' flag on Portugal is wrong, and 0.690 is not supported by the parc evidence. At 0.6364 the parc-derived share sits 5.4 points BELOW the 0.690 the register assumes, so adopting it would reduce the ceiling movement attributed to Portugal. The workbook also shows the commercial size of this: on the rebuilt split the Portuguese target spend is EUR 2,480,298 against EUR 3,052,087 on the current basis, and the GPS result moves from 53% net / 60% gross to 66% net / 73% gross. Those are the workbook's own figures, reported not re-derived.
**Evidence located:** Two Portuguese sources, and the second is the one that answers the question. (1) 01_data/07_UIO/Matriculas Isuzu SAP.xlsx - the I-Motors per-VIN registration register with explicit tonnage bands (3.5 Ton / 5 ton / 7,5 ton) on sheets '2005-2019' and '2019-2026' plus a 'SUM' sheet by band and year; registrations 2005 to June 2026; on disk since 14 July 2026, 2,010,557 bytes. (2) 01_data/08_Distributor/Imotors_Portugal_UIO_GPS_PMS_Study.xlsx, on disk since 14 July 2026, 36,179 bytes - this workbook applies the survival curve to that registration history. Sheet 'UIO_Rebuild' carries the cohort x age matrix in four blocks with a TOTAL STOCK row each; sheet 'UIO_Compare' pits the result against the current workbook; sheet 'GPS_Recalc' recomputes the target spend on the split. The survival curve is copied verbatim from UIO V19 'Assumptions & Mapping' rows 16-33, so it is the one already in use, not a new assumption.
**Evidence limit:** What the workbook does NOT settle: whether its rebuilt UIO numbers (CV LD 2,390 in 2025 against V19's 2,206) should replace the current fleet base. That is a fleet-base question and it is D09's territory, not this item's. The workbook's own README also flags a pre-existing inconsistency in the source GPS file - v5 reports a FY26 GPS% against a UIO of 8,444, not V19's 7,208 - which it flags but does not fix, and which does not affect the share itself.

---

## Normal — 16 items, one answer each

### D04 — Price index direction

Adopt the price-index proposal's framework so the bands decide, instead of choosing between the two reciprocal ratios?

**View:** Yes. The named measure currently has two definitions in live files - the glossary and register say shop price divided by our reference dealer price, the competitor document says the reverse - and both cannot be the same measure.
**Blocks:** Any index quoted in a shared pack can be read two ways until this is settled.

**Sheet:** Part 2 decision 2
**Asked on:** 2026-09-19

### D06 — Which ITUK figure the shared paper carries

Should the shared paper carry both ITUK lanes side by side, each with its denominator named?

**View:** Label both, reconcile neither. The 22,389 figure is a separate lane and is the basis of the externally published 35.1 percent, so it must not be folded into the other denominator.
**Blocks:** Which ITUK cover figure leads the next shared rebuild, and the wording around it.

**Sheet:** Part 2 decision 4
**Asked on:** 2026-09-19

### D07 — Fleet totals in documents - the standing rule

Approve the rule that no fleet total is printed in a document again - documents cite the worksheet and its version, and the count lives only in derived files with a read date beside it - plus the added drift check that fails when a new worksheet lands without the documents being re-pointed?

**View:** Yes to both. The drift check is currently blind to a worksheet swap, which is the one thing that actually happens.
**Blocks:** Whether the fleet figure and its version tag appear on the next shared rebuild. Sheet decision 5 also asks whether the number should be removed entirely or tagged to a version.

**Sheet:** Part 2 decisions 5 and 13
**Asked on:** 2026-09-19

### D09 — Which fleet base is canonical

Does the current worksheet loader become the canonical fleet base at 163,198, replacing the July extract at 163,459 that still feeds the spend-per-truck file?

**View:** The worksheet, which is what decision D08 assumes.
**Blocks:** Until answered the two bases keep disagreeing by 261 vehicles. The cause is a vehicle-class split, not two fleet collections: the five differing markets valued at the flat class rates give exactly the EUR 105,748 gap between the two files' ceilings.

**Sheet:** Part 2 decision 22
**Asked on:** 2026-09-19

### D10 — The retired ceiling is still printed

Replace the retired EUR 60.22M ceiling with the controlled EUR 55.253M in the review numbers file and the map page, or leave it as a dated historical value?

**View:** Replace it as part of the rebuild in D08.
**Blocks:** Two live files still print a ceiling the dashboard briefs call retired.

**Sheet:** Part 2 decision 23
**Asked on:** 2026-09-19

### D11 — The worksheet scope switch is set against its own read-me

Change the scope cell in the vehicle-population worksheet from Include to Exclude MIDI, as its own read-me says, or leave it and add a warning beside the top row?

**View:** Change it. A reader taking the top row today sees 258,594 vehicles, about 95,000 of which are MIDI markets that are not our customers, instead of the 163,198 base.
**Blocks:** The worksheet is inside the ask-first scope, so nothing there moves without approval.

**Sheet:** Safe tier S12 / Part 2 decision 14
**Asked on:** 2026-09-19
**Note:** Carried as a decision rather than a safe-tier repair because it is a change to a live workbook, not wording or a pointer.

### D12 — The nineteen mail files already in git history

Take option (a) - add the ignore rules so no more mail files get in, and leave history untouched?

**View:** (a) now. Decide separately whether to untrack them going forward or rewrite history if you care - nothing here is public, the repository is private.
**Blocks:** Nothing today. Nineteen Outlook mail files are tracked and reachable from the remote; one carries dealer packs sent to an external party and another a price-file email. One was already re-added once during a cleanup that thought it was deleting them.

**Sheet:** Part 2 decision 15
**Asked on:** 2026-09-19

### D14 — The sent-mail corpus inside the review pack

Delete the sent-mail corpus copy out of the review pack, or leave it?

**View:** Delete it from the pack. It is safe today only because one ignore pattern happens to cover its whole folder, so it is one exception away from being publishable.
**Blocks:** Nothing. The corpus contains sent-mail bodies, so it should not travel.

**Sheet:** Part 2 decision 17
**Asked on:** 2026-09-19

### D16 — Three shared pages with no builder

Treat the competitiveness dashboard, the quality-positioning overview and the pricing proposal as hand-maintained source going forward, or leave them as they are?

**View:** Declare them hand-maintained. They are generated pages with nothing that generates them, so under our own rules they cannot be lawfully fixed today - the page is read-only and there is no source to change.
**Blocks:** Those three pages cannot be corrected at all until it is decided which they are.

**Sheet:** Part 2 decision 20
**Asked on:** 2026-09-19

### D17 — What to do with the two review packs

Leave the nine-file and 133-file review packs frozen as the evidence trail, or regenerate them after the live fixes land?

**View:** Leave them frozen as evidence and say so on the pack. They embed the same defective paragraphs at different line numbers and will disagree with the live files the moment those are corrected.
**Blocks:** Nothing. It decides whether the packs are treated as an archive or as copies of the live files.

**Sheet:** Part 2 decision 21
**Asked on:** 2026-09-19

### D18 — What PMS and GPS stand for

Keep the data dictionary meaning of GPS (spend per unit) and treat 'Genuine Parts Share' as the internal programme name only, with PMS confirmed as 'periodic maintenance service'?

**View:** Yes - keep the dictionary meaning for the measure. The acronym currently carries an internal programme meaning that never appears in the glossary, and the whole spend-per-truck datamart is named after it.
**Blocks:** A shared-layer glossary and every caption that expands GPS.

**Sheet:** Part 2 decision 6
**Asked on:** 2026-09-19

### D19 — Which research context set is authoritative

Which of the two research context sets becomes authoritative, and where does the other live?

**View:** Could not determine a recommendation - both sets are live copies of the same documents, carrying the same defects at different line numbers. Nothing under the research tree has version history, so nothing there should be deleted.
**Blocks:** An agent reading the research context cannot tell which copy it should follow.

**Sheet:** Part 2 decision 7
**Asked on:** 2026-09-19

### D20 — Mail access - is the browser-only rule absolute

Is the browser-only rule absolute, or may mailbox access be authorised per task?

**View:** Keep it absolute - browser only, when you have opened the mailbox - and scope the exhausting-data-sources skill to a named task instead.
**Blocks:** A skill currently requires reading every mailbox store and archive, which the always-on rule forbids. The two cannot both be absolute.

**Sheet:** Part 2 decision 8
**Asked on:** 2026-09-19

### D21 — Rule consolidation - the worked merge example

Approve the worked merge example, holding the two rule filenames that machine checkers allowlist by name?

**View:** Approve the merge. Two rule files are allowlisted by filename in machine checkers, so they must never be renamed or folded - renaming them would silently disarm the check that polices banned words while every run still reports clean.
**Blocks:** The rule set stays as it is until this is answered.

**Sheet:** Part 2 decision 9
**Asked on:** 2026-09-19

### D22 — Is myPENS in scope

Is myPENS in scope for this workspace's rules, or a separate project?

**View:** Separate project. It has its own verify-and-ship skill and its own CI, and the ISZE rules are not written for it.
**Blocks:** Whether myPENS work is audited under this workspace's gates or its own.

**Sheet:** Part 2 decision 10
**Asked on:** 2026-09-19

### D23 — The state packet's superseded Excel line

Retire the superseded 'no Excel on this machine' line from the state packet, or keep it as history?

**View:** Retire it. Two passages of the same file now contradict each other - the earlier one says Excel and COM are missing, the later one says that report was wrong and Excel is installed and works.
**Blocks:** Nothing, but a contradicting state packet is what an agent reads first.

**Sheet:** Part 2 decision 11
**Asked on:** 2026-09-19

---

## Ready with no decision — 10 safe-tier repairs

Wording, pointers and factual corrections in files we own. None changes a number, a formula, a
fixture or a dashboard. None needs a rebuild.

| Ref | What | Where |
|---|---|---|
| **S1** | The ceiling rule quotes a retired numerator and a share computed from it | `.cursor/rules/isze-exec-aftersales-paper.mdc (line 23)` |
| **S2** | A checker tells the agent to write the stale 37.0% | `04_tools/workspace/check_spoken_labels.ps1 (lines 322-330)` |
| **S3** | The verification skill carries the stale ITUK half | `.cursor/skills/isze-verify-pipeline/SKILL.md (lines 60-64) and .agents/skills/isze-verify-pipeline/SKILL.md (same lines)` |
| **S4** | A rule delegates to a file that does not exist | `C:\Users\jerom\.cursor\rules\jerome-spar-default.mdc (line 18)` |
| **S5** | A rule points at a document that does not exist | `C:\Users\jerom\.cursor\rules\verify-before-done.mdc (line 39)` |
| **S6** | The email-style rule mixes two populations and contradicts its own table | `C:\Users\jerom\.cursor\rules\jerome-email-human-voice.mdc (lines 15, 23-25, 31, 40)` |
| **S7** | The modelled remainder is labelled as a buying decision | `01_data/90_INBOX/_kpi_graph_design_proposal.md (lines 73, 189, 223, 400)` |
| **S8** | The gaps rule's own worked example uses the same banned reading | `.cursor/rules/isze-gaps-need-context.mdc (line 51)` |
| **S9** | The facts sheet names a superseded verification run | `FACTS.md (lines 8 and 32)` |
| **S10** | The 'one snapshot only' price claim is false as an inventory statement | `the research context operations note, section 6.4, in both its live copy and the inbox copy` |

S1 and S2 must land in the same sitting - leaving S2 would undo S1 on the next checker run.
S3 is two near-identical twins that differ in three words; make the same substantive edit in both
and preserve the difference.

---

## Withdrawn (1)

| Ref | What | Why |
|---|---|---|
| **W01** | The annual revenue table does not bridge to the parts base | Superseded in this session. Sheet section 11 of the accompanying status register shows the printed series reconciles exactly once the Apr-Jun 2026 billing is added (103,993,893 + 8,095,414 = 112,089,307), which is the same bridge the facts sheet documents from the other direction. |

---

## Decided (8)

### D01 — Revision exception queue - the action labels read the price index backwards

Approve swapping the two action labels in the revision exception builder and regenerating the queue and its downstream pack, so the 'room to raise' rows are the ones where we are genuinely cheaper than the independent market?

**View:** Yes - fix it in the builder, not in the frozen CSV. Every one of the 84 rows labelled 'we look undercut' sits at index 1.06-5.79 (we are the dearer one) and every one of the 106 rows labelled 'room to raise' sits at 0.067-0.93 (we are the expensive one). No overlap, no contrary case, so it is a clean swap.
**Blocks:** Every downstream file that carries the label keeps telling us we have room to raise prices on the parts where we already ask two to four times the independent shop price: 106 rows carrying EUR 1.82M of CY2025 billed value, median index 0.63, 65 of them below 0.50. Live consumers are the Monday stand-up file, the GPS tab table, the open action ledger and the review workbook builder.

**Urgency when first raised:** blocking
**Urgency now:** high
**Why the urgency moved:** Lowered from blocking to high on reopening, to sit level with its partner D02, which is the same rebuild and was always high. The band half of this item is answered, so the item as a whole no longer stops everything - the label swap alone gates the queue regeneration, which is why it stays above normal.
**Answered half, stands:** Widen the raise / no-raise band to 0.80 and 1.10, and treat brakes as the first category to examine. Jerome, verbatim: "I would say raise the bands so we can set a more competitive price, we should be dynamic in our pricing we have a lot of complaints for our brake parts." This half stands and is not in question.
**Sheet:** READ FIRST / Part 2 decision 0
**Asked on:** 2026-09-19
**Note:** Both halves answered 2026-09-19. The band was confirmed earlier the same day; the label swap was confirmed as its own question. Neither half is executed - the queue regeneration is a separate piece of work and has not been run. Brakes remain the priority category named in his answer, and the register's own evidence for the swap (no overlap between the two labels' index ranges, no contrary case) is unchanged.
**Fix site:** 01_data/91_build/build_db_dlr_commercial_stack.py lines 170-181 (byte-identical twin at 01_data/_build/ carries the same defect)
**Supersedes:** The earlier record left this item open on the reading that the band sentence authorised the band only and not the label swap. That reading was correct at the time. The label swap was then put to Jerome as its own question and he answered yes, so the second half is now authorised as well and the item is closed.
**Decided on:** 2026-09-19
**Decision:** Yes to both halves. Swap the two action labels in the revision exception builder and regenerate the queue and its downstream pack, so the rows labelled 'room to raise' are the ones where we are genuinely cheaper than the independent market. The band half also stands: widen the raise and no-raise band to 0.80 and 1.10, and treat brakes as the first category to examine.
**Decision source:** Jerome, question-card selection, 2026-09-19. Card: "D01 - separately from the band, do you approve swapping the two action labels so 'room to raise' means the parts where we are genuinely cheaper than the independent market?" Selected: "Yes - swap the labels". The band half was already recorded from his earlier sentence. Asked as its own card because the earlier sentence did not cover the label swap.
**Evidence:** Closure rests on a STRUCTURED USER SELECTION, not on a conversational remark: the question was presented as a multiple-choice card (AskQuestion) and Jerome selected an option. A transcript-only audit will NOT see this - session transcript rows carry only assistant text and tool_use blocks. There is no tool_result block and no selection field in the JSONL, so the selection leaves no trace for a checker that reads the transcript. The selection is recorded here from the assistant's immediate in-session confirmation of the choice. Do not reopen on the ground that the transcript does not show it.

### D02 — Revision exception queue - the raise / no-raise band

Approve widening the raise and no-raise band to 0.80 and 1.10, leaving the middle inconclusive on this evidence?

**View:** Yes. The current 0.95 / 1.05 band is tighter than the measurement supports - roughly ninety percent of the index variation is which listing the scraper happened to match. On today's data the wider band moves 105 rows into no-raise and 42 into raise-defensible.
**Blocks:** Same rebuild as D01. Both answers are needed before the exception queue is regenerated.

**Partner item:** D01
**Sheet:** READ FIRST - threshold question
**Asked on:** 2026-09-19
**Note:** Carried as a decision in its own right rather than as a ride on D01: it was asked as the threshold question and answered as such. The wider band replaces the 0.95 / 1.05 band. Nothing is executed - the band change lands with the D01 rebuild, which is a separate piece of work.
**Decided on:** 2026-09-19
**Decision:** Widen the raise and no-raise band to 0.80 and 1.10 and leave the middle inconclusive on this evidence. Pairs with D01.
**Decision source:** Jerome, question-card selection, 2026-09-19. Card: "D02 - widen the raise / no-raise band on the revision exception queue to 0.80 and 1.10, leaving the middle inconclusive?" Selected: "Yes - widen it to 0.80 / 1.10".
**Evidence:** Closure rests on a STRUCTURED USER SELECTION, not on a conversational remark: the question was presented as a multiple-choice card (AskQuestion) and Jerome selected an option. A transcript-only audit will NOT see this - session transcript rows carry only assistant text and tool_use blocks. There is no tool_result block and no selection field in the JSONL, so the selection leaves no trace for a checker that reads the transcript. The selection is recorded here from the assistant's immediate in-session confirmation of the choice. Do not reopen on the ground that the transcript does not show it.

### D03 — Who buys at each step of the price chain

Is the approved basis the multiplier pair - ISZE list x 1.40 reaching the distributor, then x 1.275 reaching the dealer?

**View:** Keep the chain and fix the wording. Our own paper estimates the trade at 27-29 percent, and the alternative reading was already rejected once in July.
**Blocks:** Every shared pack that names a tier: the executive aftersales paper, the aftermarket pack, the leakage pack and the part-groups payload all say 1.40 already reaches the dealer with 1.275 reaching the customer, which skips a tier. Nothing in the pricing wording can be corrected until this is answered.

**Sheet:** READ FOURTH / Part 2 decisions 1 and 19
**Asked on:** 2026-09-19
**Note:** A deliberate, informed decision, recorded as such. He was told what it costs before he answered: the margins reading lifts the reference dealer price by 22.6%, about EUR 12.4M on the CY2025 billed base, none of which is ISZE revenue. Consequence, stated once: every shared pack that names a tier has to be rewritten to the margins reading, and any figure measured against the reference dealer price moves by the same 22.6%. Not executed, and not to be re-opened - he confirmed the reading after being shown the cost and the recommendation against it.
**Supersedes:** Supersedes the record made earlier on 2026-09-19, which carried the multiplier chain as a recommended reading and left the margins half open. That reading was rejected once before, in July, and the pricing paper and the analysis both recommend it again here. Jerome chose the margins reading after being told all of that.
**Decided on:** 2026-09-19
**Decision:** The margins reading, not the multiplier chain: a 37% margin at one step and 25-27.5% at the next, which needs a combined factor of about 2.15-2.19. Supersedes the earlier record in this register, which carried the multiplier chain as a recommended reading. That reading is not adopted.
**Decision source:** Jerome, question-card selection, 2026-09-19. Confirmation card shown deliberately because the answer reverses the earlier record: "D03 - confirming, because it reverses the earlier decision and lifts the reference dealer price 22.6% (~EUR 12.4M, none of it our revenue). Deliberate?" Selected: "Yes, deliberate - use the 37% / 25-27.5% margins reading". The other option on the same card was to switch back to the multiplier chain.
**Evidence:** Closure rests on a STRUCTURED USER SELECTION, not on a conversational remark: the question was presented as a multiple-choice card (AskQuestion) and Jerome selected an option. A transcript-only audit will NOT see this - session transcript rows carry only assistant text and tool_use blocks. There is no tool_result block and no selection field in the JSONL, so the selection leaves no trace for a checker that reads the transcript. The selection is recorded here from the assistant's immediate in-session confirmation of the choice. Do not reopen on the ground that the transcript does not show it.

### D08 — The fleet figure on shared dashboards and the presented deck

Approve rebuilding the five live dashboards, the AIM truck catalogue and the Business Performance Review deck from their builders, so the fleet reads 163,198 and the EUR 198 per truck slide is replaced by a matched rate?

**View:** Yes. EUR 198.10 is the only figure that divides a 22-entity euro total by an 18-market fleet. The two matched pairs are EUR 188.16 (18-market billed over the 18-market fleet of 163,459) and EUR 188.46 (same euro over the 163,198 target-spend fleet).
**Blocks:** Five live dashboards, the AIM truck catalogue and a presented deck print a fleet count the current worksheet does not support, and one slide prints the only scope-mixing rate.

**Sheet:** Part 2 decision 12
**Asked on:** 2026-09-19
**Note:** This is not a one-file edit. The current engine no longer reproduces the published ceiling - re-running it now yields EUR 54,323,455 against the published EUR 55,253,312 - so the rebuild re-bases the ceiling and every rate that divides by it. He was told this before he answered. His yes approves the rebuild; it does not approve the re-based ceiling as such, and the new ceiling value may need its own look once the rebuild lands. Not executed: no builder has been run.
**Decided on:** 2026-09-19
**Decision:** Yes. Rebuild the five live dashboards, the AIM truck catalogue and the Business Performance Review deck from their builders, so the fleet reads 163,198 and the EUR 198 per truck slide becomes a matched rate.
**Decision source:** Jerome, question-card selection, 2026-09-19. Card: "D08 - rebuild the five dashboards, the AIM truck catalogue and the BP Review deck so the fleet reads 163,198 and the EUR 198 per truck slide becomes a matched rate?" Selected: "Yes - rebuild all seven from their builders". He was told the re-based ceiling before answering.
**Evidence:** Closure rests on a STRUCTURED USER SELECTION, not on a conversational remark: the question was presented as a multiple-choice card (AskQuestion) and Jerome selected an option. A transcript-only audit will NOT see this - session transcript rows carry only assistant text and tool_use blocks. There is no tool_result block and no selection field in the JSONL, so the selection leaves no trace for a checker that reads the transcript. The selection is recorded here from the assistant's immediate in-session confirmation of the choice. Do not reopen on the ground that the transcript does not show it.

### D13 — Add the drafted ignore rules

Approve adding the drafted ignore rules so the 516 committable files stop being committable?

**View:** Yes. It is the cheapest item on the sheet: no rebuild, no rebuild authority, it does not touch history and it deletes nothing.
**Blocks:** 516 files are committable today that should not be - a live browser profile of 182 files (cookies, history, saved logins), 30 correspondence files, 173 backup copies at 436 MB, 123 root scratch files and 9 large binaries at 276 MB. The exposure arrives the moment someone runs a repository-wide add and push, which is exactly how the nineteen mail files got onto the remote.

**Sheet:** Part 2 decision 16
**Asked on:** 2026-09-19
**Note:** Two actions, both reversible. .gitignore was widened by one pattern and no rule was widened beyond the four loose files. The untracking touches the index only. Eight files under the parent outlook_extracts/ tree - outside the JEROME_ONLY marker - are still tracked and were deliberately left alone: five markdown files, a probe script and two small JSON captures. Each of the five markdown files is byte-identical to its untracked JEROME_ONLY/ copy, so identical content is now ignored in one folder and still tracked in the other. He has not decided on those, so nothing was done to them.
**Decided on:** 2026-09-19
**Decision:** Yes, in two named parts: add an ignore pattern for backup churn, and untrack the nine files under JEROME_ONLY/ with git rm --cached so they stop appearing in future commits. History is left as it is and no file is deleted from disk.
**Decision source:** Jerome, question-card selections, 2026-09-19, two cards in one sitting. Card D13a: "The four loose backup files (~100 KB, all regenerable copies). Add an ignore pattern so they can't be committed?" Selected: "Yes - add the .bak pattern, leave the already-tracked ones in history". Card D13b: "The nine files already committed under the JEROME_ONLY folder ..." Selected: "Untrack them going forward - stops future commits, leaves history as is".
**Evidence:** Closure rests on a STRUCTURED USER SELECTION, not on a conversational remark: the question was presented as a multiple-choice card (AskQuestion) and Jerome selected an option. A transcript-only audit will NOT see this - session transcript rows carry only assistant text and tool_use blocks. There is no tool_result block and no selection field in the JSONL, so the selection leaves no trace for a checker that reads the transcript. The selection is recorded here from the assistant's immediate in-session confirmation of the choice. Do not reopen on the ground that the transcript does not show it.

### D15 — Class T margin - 40 percent or 20 percent

Does class T keep the 40 percent margin its own price file charges (fix the configuration to a 0.60 divisor), or is 20 percent a deliberate booking rule and the price file the odd one out?

**View:** Fix the configuration to a 0.60 divisor, a 40 percent margin. The evidence is unanimous: 103 live class-T rows all price at 0.60, 100 derived rows all at 40 percent, and IML's own disc classes 99 of 101 rows as ST with no bare T code at all. The likely cause is a one-letter mapping error when IML's two-character codes were collapsed to one letter.
**Blocks:** Any calculation that reads a margin for those part numbers - an owned adjustment, a margin percentage in a launch book, a split table, any margin-based figure - currently assumes 20 percent where the line earns 40 percent. The affected book is small, around a hundred part numbers, but the fix is inside the locked pricing file, so it is a finding for you, not a fix.

**Sheet:** READ THIRD / Part 2 decision 18
**Asked on:** 2026-09-19
**Note:** Executed 2026-09-19: the single value changed, from 0.80 to 0.60, and nothing else in 03_analytics/isze_pricing/config.yaml was touched - its comments and the other class factors are exactly as they were. The live price list is not changed by this; the value is a configuration input, not a price. Consequence, stated once: any margin-based figure that touches those roughly one hundred class-T part numbers now assumes a 40% margin instead of 20%, and figures produced before this change assumed the lower margin. One honest limit carries over: no written IML class definition of ST was found, so the inference still rests on the 99-of-101 match between the code and the part numbers.
**Supersedes:** Supersedes the record made earlier on 2026-09-19, which said no change and kept the configuration at a 20% margin, treating the 40% against 20% question as deferred for discussion. That earlier record rested on the words 'keep the same price as it was', which were an instruction not to change the live price list now - an instruction that still stands. He has now answered the margin question itself, in favour of the 40% margin, so the deferred half is settled and the mismatch is closed.
**Decided on:** 2026-09-19
**Decision:** Fix the configuration to the 40% margin the price file actually charges - a 0.60 divisor - by changing class_factor.T in 03_analytics/isze_pricing/config.yaml from 0.80 to 0.60. The 20% reading is not adopted.
**Decision source:** Jerome, question-card selection, 2026-09-19. Card: "D15 (blocking) - class T is priced at a 40% margin in your price file but our config assumes 20%. Keep it as it is, or fix the config to 40%?" Selected: "Fix the config to the 40% margin the price file actually charges".
**Evidence:** Closure rests on a STRUCTURED USER SELECTION, not on a conversational remark: the question was presented as a multiple-choice card (AskQuestion) and Jerome selected an option. A transcript-only audit will NOT see this - session transcript rows carry only assistant text and tool_use blocks. There is no tool_result block and no selection field in the JSONL, so the selection leaves no trace for a checker that reads the transcript. The selection is recorded here from the assistant's immediate in-session confirmation of the choice. Do not reopen on the ground that the transcript does not show it.

### D25 — Price-index band - one threshold or two tiers

Should rows where the peer shop is up to 20% cheaper than us (index 0.60 to 0.95) be labelled as competitive-move candidates, or left unlabelled as the approved 0.80 threshold does?

**View:** Two tiers rather than one threshold: 0.60 to 0.95 as 'competitive move candidate', below 0.60 as 'genuinely exposed'. If a single threshold is mandatory, 0.90.
**Blocks:** The guardrail action list and any competitive price move on the affected families (intake/exhaust, air filter, suspension, and the five brake part numbers). The guardrail label is applied to quoted rows whose index falls below the lower bound, so widening the lower bound from 0.95 to 0.80 removes the flag from 44 rows where the peer shop is 7% to 18% below our reference dealer price - 44 rows carrying EUR 574,309 of billed business, of which the intake/exhaust block alone is EUR 369,882. Whether that is deliberate noise reduction or the opposite of the intent behind raising the bands is the question.

**Why the urgency moved:** Carried across as the companion document set it. Reviewed here and kept at high: it holds up a published action list and a live commercial choice rather than the whole rebuild, and its two readings of Jerome's 'raise the bands' sentence both remain consistent with his words, so the item itself is undecidable from the record and needs only his one-line answer. It does not sit at blocking because the guardrail ships and can be relabelled without re-deciding anything else.
**Partner item:** D02
**Sheet:** Companion finding - price-index band and the brake finding, 2026-09-19
**Asked on:** 2026-09-19
**Note:** Answered 2026-09-19 by instruction rather than by choosing an option. The question as written offered two tiers or one threshold; neither is adopted, because he has taken the mechanism out of pricing altogether. D01 and D02 remain recorded as decided - his instruction governs execution, not those records - so whether the label swap and the band widening are still to be applied, and when, is now his direct call and not this register's. The brake finding carried on this entry is a finding and is unaffected: it needs no pricing change to stand.
**Source ref:** 01_data/90_INBOX/BAND_AND_BRAKE_FINDING_2026-09-19.md, section 5
**Finding standalone:** The brake half of the companion document is a finding, not a decision. Brakes are barely affected by the band choice - only 5 brake rows worth EUR 60 in total sit in the released 0.80 to 0.95 zone. The brake problem is 38 rows below 0.80 worth EUR 722,257, which both bands flag. Five part numbers carry about EUR 696,000: 8983767550 brake rotor (GREECE, IRELAND, IUK; index 0.248; EUR 289,997), 8982447940 brake pad kit (GREECE, IRELAND, ITUK, UTI; index 0.224; EUR 252,073), 8981919560 brake rotor (IRELAND, ITUK; index 0.303; EUR 73,875), 8983767530 brake rotor (GREECE, IRELAND, IUK; index 0.248; EUR 62,332) and 8982488970 brake rotor (IRELAND, ITUK, UTI; index 0.779; EUR 17,924). Classified through 01_data/00_derived/aim_pn_classification.csv on aim_l2 = 'Brake parts', with the queue's own Brakes category as a cross-check. This contradicts the earlier hedge that the low indexes were mostly part-number match noise. One further item carried up unchanged: 8982447940 is the pad kit Jerome's own price-list conclusions recorded as HOLD_DEFAULT on ITUK, so it is simultaneously held and flagged as exposed, and that contradiction should be resolved with the brake review rather than left to sit. No decision is invented for the finding.
**Implementation record:** The agent implemented the approved 0.80 band as instructed. The companion document flags this as the one item in that workstream worth re-deciding, and the implementation is recorded here so the audit trail is not lost if the band changes.
**Decided on:** 2026-09-19
**Decision:** No change. Nothing in pricing is to be changed through this decision register. On the label question itself: no change - the pricing bands, the thresholds and the row labels stay exactly as they are, and the rows where the peer shop is up to 20% cheaper than us are not given a new label. The 0.80 threshold recorded under D02 stands as the last pricing change captured in this register.
**Decision source:** Jerome, chat, 2026-09-19, verbatim: "dont change anything from pricing via these questions". Recorded as a conversational remark on his own words, not as a question-card selection. The answer to the label question is read from that instruction: no change.
**Standing instruction:** This is a standing instruction, not only an answer to D25. Jerome has directed that pricing is not changed through this register's question mechanism. It reaches every pricing entry in the register, which is why it is also recorded at register level under standing_instruction_pricing.

### D26 — Retired Aftermarket BI Command Center - accept the retirement or restore the page

The Command Center was replaced by a 12 KB 'retired' suite-map stub in an uncommitted working-tree change, which broke the tier-A ship gate (verify_tier_a_html_json.py now fails on 'hero EUR leakage missing'). Does the retirement stand, or should the page be restored from HEAD (b88b9e8)?

**View:** Decide explicitly rather than leaving it uncommitted. If the retirement stands, update the verifier in the same change so the ship gate reads green again, and record that the repaired hero tile is now dead code. If it was accidental, restore the page and its builder from HEAD.
**Blocks:** The tier-A ship gate, which currently fails for the whole set of tier-A pages, not only for this page. The other two tier-A pages pass. Also undecided: whether the hero-tile repair in 02_dashboards/_build/aftermarket_bi_data.py is kept as dead code or removed - build_full_payload, the only place that writes iam_undercut_count and raise_defensible_count into the hero, has no caller, and build_network_aggregates is called only by the replenishment builder, which renders five different tiles and never this one.

**Why the urgency moved:** The companion document calls this medium. This register has no medium value and only three urgencies - blocking, high and normal - so it is carried as normal, deliberately not rounded up to high. The reason: the tier-A gate fails, but the retirement looks deliberate at the builder level (the builder itself was rewritten in the working tree and agrees with the page about the new suite map), so no published pack is printing something false and no reader is misled. What is wrong is the gate, and a gate that refuses a page is a safe failure, not a wrong number reaching Jerome. Rounding it to high would overstate it against D01, D08 and D13, which do hold up published packs.
**Sheet:** Companion finding - retired command center page breaks the ship gate, 2026-09-19
**Asked on:** 2026-09-19
**Note:** Folded in from a companion finding document. The size evidence, quoted because it is the whole basis for calling the change a retirement rather than a loss: the HEAD version is 460,678 bytes, the working tree version is 12,507 bytes, so 448,171 bytes are removed; git diff --stat reports 51 insertions and 449 deletions. The verifier's special case for this page demands the string 'Network € leakage' in the hero and at least 20 server-rendered bar-rows, neither of which can exist on a 12 KB suite index, so it is not a one-line string fix - the command-center entry has to be dropped or replaced outright if the retirement stands. Nothing was committed, so this is still a working-tree question and it can be answered in either direction without touching history.
**Fix site:** 02_dashboards/sales/ISZE_Aftermarket_BI_Command_Center.html, 02_dashboards/_build/build_aftermarket_bi_command_center.py and the command-center entry in 02_dashboards/_build/verify_tier_a_html_json.py lines 34-43
**Source ref:** 01_data/90_INBOX/RETIRED_PAGE_BREAKS_GATE_2026-09-19.md, section 5
**Decided on:** 2026-09-19
**Decision:** The retirement stands. The Aftermarket BI Command Center stays retired and is not restored from HEAD (b88b9e8). The page is a suite-map stub by design and the old command-center page is not coming back.
**Decision source:** Jerome, chat, 2026-09-19. He accepted the retirement. Recorded as a conversational remark on his own words, not as a question-card selection.
**Gate update outstanding:** OUTSTANDING, and deliberately not done in this pass. Accepting the retirement means the tier-A ship gate must stop expecting the retired page. The command-center entry in 02_dashboards/_build/verify_tier_a_html_json.py (lines 34-43) still demands a hero string and at least 20 server-rendered bar-rows, neither of which a 12 KB suite-map stub can carry, so the gate still fails for the whole tier-A set. It is not a one-line string fix: the entry has to be dropped or replaced outright. NO verifier and NO ship-gate script was modified while recording this decision - that change needs a deliberate pass of its own, and changing a gate on the back of a decision record is exactly what this register must not do. Also still open: whether the hero-tile repair in 02_dashboards/_build/aftermarket_bi_data.py is kept as dead code or removed.

---

## Register notes

**Still to correct:**
- DECISIONS.md and 00_docs/ISZE_ROADMAP.md were updated in the same pass on 2026-09-19 to carry the six answers recorded here, so all three now agree again for D01, D02, D03, D08, D13 and D15. For D03 and D15 the earlier wording is retained in both files and explicitly marked as superseded, so the correction is visible rather than silent.
- The readable twin is generated from this JSON by 04_tools/workspace/render_decisions_register.ps1. Re-run it after any edit here; do not hand-edit the .md.

**Closed again on:** 2026-09-19

**Closing note:** Six of the reopened and still-open items were answered by Jerome in the same chat session later on 2026-09-19 and are recorded as decided: D01, D02, D03, D08, D13 and D15. The reopened block below is kept as history - it explains why they were reopened and that reasoning has not been withdrawn. Two of the six were answered differently from the earlier closure: D03 moves from the multiplier chain to the margins reading, and D15 moves from leaving the configuration at a 20% margin to fixing it to the 40% margin the price file charges. Both are corrections, not confirmations, and both are marked as superseding the earlier wording. D05 was asked about and left open, with no decision recorded. D01, D03 and D15 now agree across this register, DECISIONS.md and 00_docs/ISZE_ROADMAP.md, which is what the three-place rule in 00_docs/DECISION_DISCIPLINE.md requires.

**Reopening audit note:** The 20:55 reopening of D01, D02, D03, D08, D13 and D15 was a FALSE NEGATIVE. It was triggered by a script that filtered on decision_source == 'Jerome, chat, 2026-09-19' and concluded the closures rested on an unverifiable chat remark. It never read the session. Each of the six was in fact put to Jerome as a structured multiple-choice card and he selected an option. The transcript cannot show that, because transcript rows contain only assistant text and tool_use blocks - there is no tool_result and no selection field - so a transcript-only check is structurally blind to question-card answers. The citations on the six now name the card and the selected option. D05 was asked about and NOT answered; it stays open.

**Standing instruction pricing:** STANDING INSTRUCTION - PRICING IS NOT CHANGED THROUGH THIS REGISTER. Jerome, 2026-09-19, verbatim: "dont change anything from pricing via these questions". No pricing value, band, threshold, label or price file may be changed on the strength of an answer to a question in this register. Pricing changes are Jerome's to initiate directly, as his own piece of work. The instruction reaches every pricing entry here, not only D25. It includes the D01 label swap and the D02 band widening - both remain recorded as decided, but neither is to be executed off the back of this mechanism - and it is the reason the class_factor.T change recorded under D15 must not be repeated in that way. Recorded at register level on purpose so it cannot be read as an answer to a single item.

**Recording pass 2026 09 19 late:** Late pass on 2026-09-19 recording four further directions from Jerome: D24 (factual correction only - parc evidence for Portugal exists; item stays OPEN and the ceiling rebuild stays unauthorised), D25 (decided - no pricing change through this register), D05 (OPEN, no answer given - he directed that the questions stop) and D26 (decided - the retired Aftermarket BI Command Center stays retired; its tier-A gate update is outstanding and was not made). No pricing value, verifier, ship-gate script, ceiling, coverage figure or dashboard was touched in this pass. Writes were limited to the three decision-record files.

---

## Travel proposal - NOT APPLIED

This section is a proposal. Nothing in it has been applied: `.gitignore` was not touched, no file was moved, and no hook was edited.

**Problem:** This register sits in 01_data/90_INBOX/, which the root .gitignore excludes at line 9 (01_data/90_INBOX/**). It is therefore untracked, it does not travel to a clone, and it is invisible on a second machine. A register whose whole purpose is to survive a chat dies with the machine it was written on.

**Recommendation:** Option B - move the register to 01_data/00_derived/, beside the data-gap register, and change the hook and the renderer default with it. This needs NO .gitignore change at all, which is the decisive point while another stream owns that file.

**Why this needs no .gitignore change:** VERIFIED 2026-09-19: git check-ignore on 01_data/00_derived/DECISIONS_AWAITING_JEROME_2026-09-19.json and the .md both exit 1, meaning NOT ignored. 00_derived is not blanket-excluded; it is a broadly trackable folder with individual large artefacts named one by one (parquet at lines 70-80, the three giant pricing CSVs at 87-89, insights/** at 94, the action-ledger transients at 274-275). The existing data-gap register 01_data/00_derived/_data_integrity_open_issues.md is tracked today, which is the proof.

**Why not the allowlist option:** Option A - leave it in 90_INBOX and add an allowlist entry - is workable but worse on three counts. It touches the one file another stream is editing right now. It needs a second entry to catch future dated registers, not just today's. And it leaves the register in the ingest drop folder that DATA_MANIFEST.md section 0 calls the place unsorted files land, which is not where a curated decision record belongs.

**The read-only lock question:** The lock on 01_data/00_derived/ is a policy lock, not a filesystem one - no read-only attribute is set on the directory, and the DECISIONS.md locked table files it under 'Locked | Note: derived spine'. So placing a writable register there does sit against that lock and needs Jerome's explicit exception: a decisions register is an index, not derived data, and moving it does not edit any of the locked artefacts. The data-gap register already sets this precedent - it lives there and is written by agents.

**Status:** PROPOSAL ONLY. Nothing in this proposal was applied: the register was not moved and no hook, hook config or test was edited. One correction as at 2026-09-19: .gitignore has since been changed once, by the separate D13 action, which added a bare *.bak rule. That change is unrelated to this proposal and does not touch the allowlist question it raises.

**The exact lines that would be needed (allowlist option):**

    !01_data/90_INBOX/DECISIONS_AWAITING_JEROME_*.json
    !01_data/90_INBOX/DECISIONS_AWAITING_JEROME_*.md

*Placement:* At the END of the file, after the scratch-probe block at lines 280-281. Placement is load-bearing: later negations win, so an entry placed near line 10 would be re-ignored by the blanket 01_data/90_INBOX/** at line 9. The ! line must also come after the exclusion it is undoing.

*Proof it works:* Same mechanism as the 08_gpt block at lines 130-133, where 08_gpt/** is followed by !08_gpt/*.md and 08_gpt/README.md is confirmed not ignored while a non-md file in that folder stays ignored.

*Caveat:* A negation re-includes a file only when its parent directory is not itself excluded by a separate recursive pattern. Verified safe here: line 9 excludes 01_data/90_INBOX/** but no rule excludes 01_data/ itself, and 08_gpt/ behaves the same way at line 130-133.

**Second-order effects if the register moves:**

  - The hook hardcodes the folder: .cursor/hooks/decisions-awaiting-on-stop.mjs line 40 sets INBOX = 01_data/90_INBOX, and findRegister() reads only that directory. Move the register without editing that line and the hook goes silent, permanently and without an error - its designed behaviour on a missing file. The .codex twin carries its own copy of the same constant.
  - The hook also prints two hardcoded paths to Jerome, built from the same INBOX constant at its lines 207 and 209, so the paths shown to him follow the folder automatically once the constant changes.
  - The hook's test 04_tools/workspace/_test_decisions_awaiting_hook.ps1 sets its own $inbox at line 27 and its live-register path at line 232, so both constants move with the register.
  - render_decisions_register.ps1 now defaults to 01_data/90_INBOX and would need the same one-line change, or a parameter passed.
  - The JSON's own 'source' field points at 01_data/90_INBOX/ISZE_ENVIRONMENT_FIX_APPROVAL_SHEET_2026-09-19.md, which stays in 90_INBOX - it is a different file and should not move.
  - DECISIONS.md and 00_docs/ISZE_ROADMAP.md both reference the register by its 90_INBOX path and would need re-pointing. Both are outside this task's write scope, so they were not touched.

---

## How this list reaches you

A hook runs at the end of the first agent turn in a chat and prints the **blocking** items in full
plus a count of the rest. It reads this register, so it cannot go out of date independently of it.
It stays quiet when nothing is open, and it does not repeat itself within a chat.

**To answer:** say the answer in chat, and it is recorded here, in `DECISIONS.md`, and in
`00_docs\ISZE_ROADMAP.md` in the same pass. Until all three agree the item stays open on this list.

_Rendered from `DECISIONS_AWAITING_JEROME_2026-09-19.json` by `04_tools\workspace\render_decisions_register.ps1`. Do not hand-edit this page._



---

## G. Claims to CONFIRM / REJECT / UNKNOWN

1. Network 2025 ceiling ≈ €55.253M, captured ≈ €30.76M → ~55.7%.
2. Flat-€250 markets = 8, share ≈ 40.3%.
3. ITUK GPS ≈ 45.6% on ≈ €12.21M.
4. Top gaps clutch disc / brake pad / brake shoe (verify from CSV).
5. Portugal n35_share live file = 0.6364 on imotors_parc_bands.
6. UTI ≠ UMI; IDS Israel = UMI only.
7. Warranty cannot prove maintenance intervals.
8. Rebuilding packs on a re-based ceiling while share-accept is open is wrong.

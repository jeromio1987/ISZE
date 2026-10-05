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

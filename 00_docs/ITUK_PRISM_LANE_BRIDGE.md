# ITUK PMS — bridging the two lanes (Model B/IML vs PRISM network)

**Read this before putting an ITUK PMS capture % or gap € in front of Jerome, IML, or ITUK.** There are
**two different, both-correct ITUK PMS numbers** in this workspace, built on different denominators for
different audiences. Quoting the wrong one in the wrong room — or both in the same slide without this
bridge — is the single easiest way to look inconsistent on ITUK.

---

## 1. The two lanes at a glance

| | **Model B / IML lane** (external) | **PRISM network lane** (internal) |
|---|---|---|
| Source | `data/iml_v7_ituk_cy2025.yaml` → `ITUK_PMS_Analysis_Apr2026_v7_reclassified.xlsx` | `pms_capture_by_db_year.csv` (built by `scripts/build_bvp_p0_p1.py` → `modules/pms_engine.py`) |
| FACTS.md section | **§1** | **§1b** |
| UIO denominator | **22,389** — full DVLA parc (flat, Mar 2026) | **23,068** — real cv_std/f_series UIO-bucket split (22,190.9 + 877.0), `data/uio_by_model_bucket.csv` |
| Service frequency | Oil/Fuel/Air **1.25×/yr**; Clutch/Brake **0.5×/yr** (IML 40,000km ÷ 50,000km/yr mileage) | Oil/Fuel/Air/wear categories at the global PRISM factors (`pms_capture_assumptions.yaml`), **ITUK brake override 0.4** as of 2026-07-21 |
| Addressable | 100% | 100% |
| Headline oil-filter cover | **35.1%** (ITUK→DLR 40.6%) | **116% uncapped / 100% capped** (CY2025) |
| PMS revenue gap | **€2,038,471** (5 categories) | Not the quoted external figure — see §3 below |
| Used for | IML business case, ITUK correspondence, external decks, dashboards, `isze_data.json` | PRISM network league table, cross-distributor benchmarking, capture-rate trend pages |

**Same real billing actuals feed both lanes.** The gap between 35.1% and 116%/100% is entirely the
denominator (UIO figure × service-frequency assumption), not a data discrepancy — see §4.

---

## 2. When to quote which

**Quote the Model B / IML lane (§1, 35.1% / €2.04M) when:**
- Talking to IML or ITUK directly (this is the standard they signed off, 2026-07-02 — see `DECISIONS.md`).
- In any business case, trip report, or external correspondence.
- Anywhere `isze_data.json` already publishes it (don't silently swap in the PRISM number).

**Quote the PRISM network lane (§1b) when:**
- Comparing ITUK against other distributors on the same league table / capture-rate page (`pages/3_PMS.py`,
  `network_percentile.csv`) — Model B's bespoke IML denominator doesn't exist for every distributor, so the
  network view has to use PRISM's own consistent denominator across all 18+ distributors.
- Looking at PRISM's own capture trend (2023→2024→2025) or the AIM×GPS quadrant, which is built entirely
  off the PRISM lane.
- Internal PRISM/dashboard work where the audience already knows this is the internal denominator.

**Never show both as "the" capture rate in the same meeting without this bridge.** If a deck needs both
(e.g. "here's what IML sees vs here's how ITUK ranks against peers internally"), say so explicitly and
show the UIO/denominator difference (22,389 flat DVLA vs 23,068 bucket-split), not just the two %s side by
side. A reader who sees 35% in one tab and 100%+ in the next, with no explanation, will assume one of them
is wrong — they're both right, on different questions.

---

## 3. The one thing NOT to cross-contaminate: revenue gap €

The Model B **€2,038,471** gap (5 categories, IML denominator) is the number IML/ITUK have seen and
signed off on. The PRISM lane's `revenue_gap_eur` column is **not currently safe to quote at all** as a
network total (see `DECISIONS.md` 2026-07-17 and 2026-07-21): any category where a distributor has zero
actual sales books a €0 gap (best-looking outcome for the worst real result), flagged via the
`revenue_gap_quotable` column added 2026-07-21 but not yet fixed at the value level. **Do not blend a
PRISM-lane € gap into an IML conversation, and do not quote the PRISM €17.09M-style network gap figure
externally until the quotable-KPI firewall is resolved past the flag stage.**

---

## 4. Why the two UIO denominators differ (root cause, not a bug)

- **Model B / IML (22,389):** the full DVLA-registered ITUK parc as of Mar 2026, no vehicle-class split,
  IML's own service-frequency assumptions (1.25×/yr filters, 0.5×/yr wear parts, both keyed to a
  confirmed 50,000km/yr ITUK average mileage).
- **PRISM (23,068):** re-based 2026-07-15 to split ITUK's N75 truck fleet into its real cv_std (22,190.9)
  + f_series (877.0) UIO buckets instead of one flat N75 number — see `modules/pms_engine.expected_by_category_bucketed()`
  and `scripts/build_uio_by_model_bucket.py`. This fixed a 2-market hardcoded allowlist that had
  mis-scoped 14 of 18 distributors network-wide; ITUK's own PRISM-lane numbers moved as a side effect,
  not because IML's number was wrong.

Both totals land within ~3% of each other (22,389 vs 23,068) — the **35% vs 100%+ gap is the
service-frequency assumption**, not the UIO count. Model B assumes filters get replaced 2.5× more often
per addressable unit (1.25×/yr vs PRISM's 0.5×/yr), which is why the same actual unit sales produce such
different cover percentages against each denominator.

---

## 5. Open items that touch both lanes

- **ITUK brake wear factor 0.4 vs 0.8** (PRISM lane only — Model B uses its own 0.5×/yr wear-part
  frequency, a different mechanism). See `00_docs/ISZE_ROADMAP.md` — unresolved, needs IML.
- **`revenue_gap_eur` quotable-KPI firewall** — flagged, not yet fixed at the value level (§3 above).

---

_Links: `FACTS.md` §1 (Model B) · `FACTS.md` §1b (PRISM lane) · `DECISIONS.md` 2026-07-02 (Model B adopted),
2026-07-16 (brake factor dead-config found), 2026-07-21 (dead-config fixed + revenue firewall) ·
`03_analytics/Isuzu/prism/docs/pms_service_intervals.md` (factor sourcing, all provisional) ·
`03_analytics/Isuzu/prism/modules/pms_engine.py` (`expected_by_category_bucketed`, `calculate_pms_capture`)._

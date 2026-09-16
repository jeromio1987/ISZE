# AIM scoring layer — what it is vs what it claims, and the 2026-08-18 backtest

**Verdict:** no fitted pricing-risk / opportunity candidate cleared a 2024→2025 holdout against GPS SPU or PMS **total** capture. Reproduce: `python scripts/backtest_aim_pricing_risk.py`. Classifier (`modules/aim_pn_classifier.py`) was not touched. No live page shipped.

Numbers from complete CY2023–2025 only (CY2026 excluded as 25% coverage). GPS tests drop the four no-UIO books (Armenia, Kazakhstan, Palestine, Ukraine). n = 18 UIO-ok distributors. Verification snapshot cited: `01_data/00_derived/_verification_report.json` green (106 pass / 0 fail, generated 2026-08-17).

---

## What the scoring layer claims vs what it is

AIM has two layers that later got conflated.

**Classification (works, out of scope here).** Category L1/L2/L3 plus Demand Type live on the Parts Master and, after the 2026-07-02 gap close, on `aim_pn_classification.csv`. Residual unclassified parts revenue is 1.6% (CY2024) / 1.8% (CY2025). That is a taxonomy. It is not a pricing-risk model.

**Scoring (this task).** The workbook advertises a 0–100 Strategic Score (sales, volume, criticality, competition, margin, growth → Strategic / Core / Standard / Long Tail) and a Pricing Risk Map (Must Review, class distortion, kit/component inversion, competitive overpricing, margin leakage). What actually reaches PRISM is thinner:

- `build_bvp_p4_p5.py` joins Parts Master **by normalised description**, then sets `aim_high_risk` if Pricing Risk is in `{must review, commercial review, class distortion, competitive overpricing, margin leakage}` or contains `"review"`.
- On the current Parts Master (`91_legacy/Isuzu/AIM_CY2025_Analysis.xlsx`): **2,557** rows are `"Below 2026 List"`, **1,916** are `"OK"`, and the real risk flags are a handful — Margin Leakage 12, Class Distortion 7, Competitive Overpricing 1, plus a few combined labels. Strategic Score exists (mean 46.1, max 97.9) and is **not** the GPS-matrix axis.
- Rolled to distributor-year, that flag is `aim_high_risk_pct` = high-risk € / AIM-matched €. CY2025 network exposure is ~1% (€316k). All-time max remains Norway 2023 at **0.0487**. The 0.12 gate used until 2026-07-17 never fired. The axis was a 1-D restatement of GPS.

So the scoring layer is a **face-valid, hand-labelled flag** with almost no positive rate, joined on description, never calibrated to an outcome. It claims to be a pricing-risk engine. It is a sparse tag. Classification is the part of AIM that does a real job.

A second, later rubric — `scripts/build_db_aftersales_risk.py` — repeats the same genus: min-max weights Eucon 0.35 / AIM scraper 0.25 / contested BVP 0.25 / VOR 0.15 into a 0–100 index, on `year.max()` (partial-year trap) and on `eucon_price_gap.csv` (PartsPool Autodoc DE/NO **2026-03-29**, not the 2023 UK survey; already flagged in `eucon_price_gap.meta.json`). It is not a fitted model and was not treated as a candidate.

---

## Outcomes and candidates (pre-registered)

**Outcomes (DB-year):** GPS `spend_per_unit_eur`; PMS **total** capture = Σ actual / Σ expected (`line_type=total`). Genuine capture is an extra lens only.

**Naive baselines:** last year’s own outcome (persistence); train-median; Δ = 0.

**Clears** iff 2024-lagged feature → 2025 outcome has Spearman |ρ| ≥ 0.47 (correct sign: higher feature → worse GPS/PMS), OLS MAE ≥10% better than the matching naive, **and** Spearman strictly better than lagged `aim_high_risk_pct` on the same rows. Predicting *change* (Δ) is the real test; level correlations are mostly who was already high/low.

| ID | Feature (always lagged one year) | Vintage honesty |
|----|----------------------------------|-----------------|
| C1 | Revenue-weighted IAM undercut on Eucon UK 2023 workshop PNs (`−delta_vs_proj_retail_pct`) | Valid 2023 vintage; 34 PNs |
| C1b | Share of € in those PNs where IAM < reference sell-out | Same |
| C2 | BVP capture of contested demand (`db_parts_mix_classification.csv`) | Fitted lag of an existing split; not a new taxonomy |
| C3 | Commodity-contested € share (BVP-catalog PNs excluding Maintenance / safety L1 + Demand Type) | Reuses AIM L1 + Demand Type + BVP dimension |
| AIM incumbent | Lagged `aim_high_risk_pct` | Control, not a new model |
| KS / PartsPool | 2026 scrapes | **Diagnostics only** — cannot forecast CY2025 |

Mekonomen: 7 PNs, **0** `filter_part_role` hits. Auto365: no OEM PN join (closed). KS is PN-indexed (43 PNs, scraped 2026-08-10) but the prices are a 2026 UK catalogue, not a leading indicator.

---

## Holdout results (2024 feature → 2025 outcome, n=18)

Persistence already separates the network: GPS ρ = **0.92**, PMS total ρ = **0.75**.

| Feature | GPS ρ | GPS p | PMS total ρ | PMS p | ΔGPS ρ | ΔPMS ρ | Clears? |
|---------|------:|------:|------------:|------:|-------:|-------:|---------|
| Persistence (yₜ₋₁) | 0.92 | 0.00 | 0.75 | 0.00 | — | — | baseline |
| AIM high-risk lag | −0.38 | 0.12 | **−0.57** | 0.014 | −0.35 | −0.24 | no (loses to persistence; Δ null) |
| C1 2023 IAM undercut | −0.44 | 0.069 | **−0.48** | 0.044 | −0.09 | −0.06 | no (does not beat AIM lag on PMS; Δ null; OLS vs median +5.9%) |
| C1b exposed € share | −0.41 | 0.095 | −0.13 | 0.61 | −0.03 | −0.27 | no |
| C2 BVP contested | +0.23 | 0.36 | +0.17 | 0.50 | +0.08 | −0.14 | no (wrong sign vs “risk”) |
| C3 commodity-contested share | +0.23 | 0.35 | **+0.63** | 0.005 | −0.23 | +0.04 | no (wrong sign: more contested mix → *higher* total capture) |

**Near-miss that must not be promoted:** C1 vs PMS total ρ = −0.48, p = 0.044 looks like a hit until (1) lagged AIM is stronger (−0.57), (2) C1 does not predict YoY change (Δ ρ ≈ 0), (3) last year’s capture is 0.75. Cross-section of *who already captures little* is not a pricing-risk forecast.

**C2 vs PMS genuine** (extra lens, not the primary): holdout ρ = −0.53, p = 0.022, OLS MAE vs median +22%. That is mix persistence — distributors that already down-trade to BVP still have lower genuine capture next year — not IAM price elasticity. Primary remains **total** capture; C2 vs total is +0.17 (null / wrong sign).

**2026 diagnostics (not forecasts):** KS undercut vs 2025 PMS ρ = −0.58 (contemporaneous). PartsPool 44-PN Autodoc DE/NO vs GPS/PMS ρ = −0.27, n=17.

---

## What to do instead (no page ship)

1. **Formally retire the AIM pricing-risk ambition** as a decision surface. Keep `aim_high_risk_pct` as the context column already decided on 2026-07-17. Do not re-gate page 16 or page 7 on a new 0–100.
2. **Keep the classification layer.** That is the working AIM product.
3. **Keep x = PMS total capture** on `pages/16_AIM_GPS_Matrix.py`. GPS × capture already separates; a fitted pricing-risk axis does not add a leading signal at DB-year grain with three clean years and PN-indexed competitor coverage this thin.
4. **Competitor prices stay at PN operating views** (Part-Groups / aftermarket dashboard), with vintages labelled: 2023 UK IAM survey ≠ 2026-03-29 PartsPool ≠ 2026-08 KS. Do not roll them into a network risk score.
5. **Redirect “who needs attention”** to GPS/PMS (live) and the P4 deterministic account-health spec (`00_docs/P4_DETERMINISTIC_SIGNALS.md`) — a different, already-specified approach, not a new rubric. Do not substitute `db_aftersales_risk.csv`.
6. Fitted price *response* remains the deferred DB→DLR elasticity path (`price_volume_elasticity.csv` is not quotable for ISZE→DB).

Panel: `docs/AIM_PRICING_RISK_BACKTEST_panel_2026-08-18.csv` · JSON: `docs/AIM_PRICING_RISK_BACKTEST_2026-08-18.json`.

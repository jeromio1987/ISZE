# IDS 2026 — cross-dataset correlation scan

**Mode B / internal. Read-only analysis — no rebuild, no mail, no commit.**
**Generated:** 2026-08-10 · IDS payload: 564 dealer rows, 521 after dropping the `Benelux` rollup (it double-counts BE+NL+LUX).

KPI anchor: `_verification_report.json` is **green** (106 pass / 0 fail, 2026-08-03).

## Verdict

**No. There is no defensible correlation between IDS 2026 dealer scores and any parts performance metric in this workspace.** Every candidate either dies when the join is done correctly, dies when single-dealer countries are removed, or dies under multiple-testing correction. Nothing survives Benjamini-Hochberg FDR at 10% — at either level.

That is not the same as "IDS is worthless". It means IDS is measuring something **orthogonal** to parts € — process and facility hygiene, self-reported — and it should be used the way Petros and Astara already use it (visit triage, coaching), not as a predictor of wallet.

**The one thing worth knowing:** the strongest *apparent* results in this scan were all artefacts, and I can show you exactly which artefact each one was. That is the useful output.

### The five relationships that looked real, and what each one actually was

| # | Relationship | Level | n | Raw strength | What it really was |
|---|---|---|--:|---|---|
| 1 | IDS total vs GPS capture-vs-max | DB | 12 | rho −0.71, p=0.010 (survives >=5-dealer cut at −0.81) | **Mostly denominator.** `capture vs max` divides by a per-DB € target that is 529 for ITUK, 427 Portugal, 364 Malta vs a flat 250 for everyone else. High-IDS markets are the ones graded against a harder target. Controlling for it: r=-0.45, p=0.15. |
| 2 | IDS total vs ITUK dealer parts € | dealer group | 31 | rho 0.20, p=0.27 | **Was rho 0.44 / p=0.019 until I fixed a name-matching bug** that collapsed 7 UK dealers (Elgin x2, Commercial Motors Wales, …) into one fake mega-group. Real answer: noise. |
| 3 | IDS total vs PMS leakage € per unit | dealer group | 31 | rho −0.37, p=0.040 | Right direction (better dealers leak less) and the only dealer-level survivor, but it fails FDR, and the leakage study itself only maps 7–39% of each dealer's lines to a PMS category. |
| 4 | IDS total vs genuine share, size-controlled | dealer group | 31 | partial r −0.37, p=0.039 | **Wrong direction** — higher-IDS UK dealers buy a *slightly lower* genuine share. Almost certainly a mix effect (bigger CV workshops do more contested/BVP-exposed work), not a standards effect. Fails FDR. |
| 5 | IDS total vs genuine EUR share of PMS mix | DB | 12 | rho 0.47, p=0.12 | The prior Kaizen pack's headline (+0.41 on Section D). **Collapses to rho 0.20 (p=0.58) once MALTA and CYPRUS are dropped** — two 'countries' whose IDS average is one dealer each. |

### What you probably expect that does NOT hold

- **Section D (Parts & Accessories) does not predict PMS capture.** rho −0.30 (n=11), and −0.28 on DBs with >=5 dealers. Flat. This reproduces the Jul-2026 Kaizen finding (it had −0.45) but with the honest caveat that n≈10 markets cannot support either number. Per the sales-is-sales rule this is measured on `line_type=total`; the genuine-only lens is no better (rho −0.10).
- **Section D does not predict KPI first fill rate or MOS.** rho −0.24 and −0.07. The Kaizen pack reported +0.41 fill / +0.33 MOS. That flip is what six extra months of KPI months and a different DB set does to an n=8 correlation — which tells you how much to trust either version.
- **IDS does not predict GPS €/UIO.** rho 0.11 all DBs, −0.07 on DBs with >=5 dealers. Nothing.
- **A good dealer is not a bigger dealer.** At UK dealer level IDS explains essentially none of parts spend (rho 0.20 group / 0.10 site). PR Fleet scores 38.8% and buys €70k; Warrington scores 97.9% and buys €345k — but Tanner scores 67.4% on €26k and JDS scores 68.1% on €335k. No line through it.
- **Country is not destiny, either.** Only ~20% of a dealer's IDS total is explained by which country he sits in (eta-squared 0.197, n=494). I expected the country-mix confound to be the whole story at dealer level; it is not. IDS genuinely discriminates *between dealers*. It just does not discriminate on anything that shows up in parts €.

### What IDS is actually measuring

Sections B, C, D and E inter-correlate at rho 0.66–0.78 and each correlates 0.81–0.91 with the total. That is a **single underlying factor**, not five independent capabilities — a dealer who scores well on Parts scores well on Service and Organisation. Practically: **Section D carries almost no information that the total score does not already carry**, so splitting Kaizen actions by section is over-reading the instrument.

### Where the mail/meeting record agrees

The qualitative corpus predicted this result and nobody in it ever claimed otherwise:

- Tomoe Baumann's own cross-checks found Hungary uploaded identical values for every dealer, Romania scoring blank cells as points, and Petros self-scoring above the allocated maximum. This is a **self-evaluation with known parser and submission defects**, not an audit.
- No distributor anywhere in the record claims high-IDS dealers buy more genuine parts. The only operational use is **"IDS dealer visits later; priority lower IDS scorers"** (Petros, 6 Aug) and Portugal treating it as a self-audit for coaching.
- IUK is the live counter-example: **IDS 81.7% (above network) while losing €243k of brakes to IAM** because dealers say OEM brakes and wipers are too dear. Standards high, wallet leaking. Price and range beat standards.
- Astara/Portugal scores 86.7% on IDS and simultaneously tells you GPS 63% is optimistic and ">50% of the parc is not regularly in the official network". High IDS, sceptical on capture.
- The Jul-2026 Kaizen pack already called this **"thesis half-confirmed … a clean Section D score is a process / stock / promo hygiene signal — it does not replace attach and capture work."** This scan says drop the "half" and keep the second sentence.

### Baumann exclude rule — effect on the numbers

Applied and tested both ways. **It changes nothing here**, for a structural reason worth knowing: the 18 red-marked/zero FR+ES dealers sit in MIDI markets that have **no PRISM PMS/GPS mapping at all**, so they never enter a correlation. They matter for MIDI country averages and rankings — not for this study. The zeros that do exist elsewhere (Switzerland 6, Italy 3) are per Tomoe's rule kept in.

### What is blocked, and what would unlock it

| Blocker | Consequence | What you would need |
|---|---|---|
| **No dealer-level parts sales outside ITUK** | The entire hypothesis is testable on 1 of 20 IDS countries. 476 scored dealers have an IDS score and no matching € line. | DB-to-dealer sell-out feeds from IUK, Petros, IBX, RSA, UMI — already on the `DATA_ASKS_IML_and_all_DBs` list. IUK (45 IDS dealers, LCV) is the highest-value single ask. |
| **ITUK IDS is `totals_only`** | The one market with dealer-level € has **no Section D score** — so the most interesting test (Parts standards vs parts purchases) cannot be run anywhere in the network today. | ITUK per-dealer section detail, or accept the total as proxy. |
| **No dealer ID** | Joins are fuzzy name matches. 44 IDS names vs 64 SAP legal names; a single normalisation bug moved the headline result from 'signal' to 'noise'. | A dealer code carried in both the IDS workbook and the sell-out extract. Cheapest high-value fix. |
| **KPI is DB-monthly, in Excel** | Fill rate and MOS can only ever be a country constant against 45 different dealer scores — zero within-country variance to correlate. | Dealer-level fill/backorder, or accept KPI is a DB story. |
| **MIDI (FR/IT/ES/CH) has no PRISM DB mapping** | 192 IDS dealers — the largest single block — are excluded from every business join. | A MIDI distributor mapping into `distributor_master_mapping.csv`. |
| **n=10–12 markets** | Every DB-level correlation is underpowered. To detect rho=0.5 at 80% power you need n≈29 markets. You have 12. | Nothing — this ceiling is structural. Stop quoting country-level r values as evidence. |

### If you want one number to carry into a meeting

> IDS 2026 and parts performance are statistically unrelated on every join we can currently make (dealer level n=31 UK groups; DB level n=10–12 markets; nothing survives multiple-testing correction). IDS is a self-reported process-hygiene score and should be used for visit triage, not wallet forecasting.

---

## L1 — What IDS actually measures (before joining anything)

- Dealers (excl. Benelux rollup): **521** across **19** countries
- Zero-score shells: **27** (France 14, Switzerland 6, Spain 4, Italy 3)
- Baumann-excluded (FR/ES red-marked + zeros): **18**
- `totals_only` (no section detail): **44** — all UK CV / ITUK

**Country-mix confound.** Between-country variance / total variance (eta-squared) = **0.197** on n=494 scored dealers.
So ~**20%** of a dealer's IDS total is explained by *which country he is in*, ~80% by the dealer himself.

**Section inter-correlation** (dealer level, n=447, Spearman):

| | A_pct | B_pct | C_pct | D_pct | E_pct | total_pct |
|---|---|---|---|---|---|---|
| **A_pct** | 1.0 | 0.58 | 0.47 | 0.58 | 0.52 | 0.71 |
| **B_pct** | 0.58 | 1.0 | 0.68 | 0.78 | 0.68 | 0.91 |
| **C_pct** | 0.47 | 0.68 | 1.0 | 0.72 | 0.59 | 0.82 |
| **D_pct** | 0.58 | 0.78 | 0.72 | 1.0 | 0.66 | 0.89 |
| **E_pct** | 0.52 | 0.68 | 0.59 | 0.66 | 1.0 | 0.81 |
| **total_pct** | 0.71 | 0.91 | 0.82 | 0.89 | 0.81 | 1.0 |

Section D (Parts) sd = 0.159, mean = 0.796; total sd = 0.135.

---

## L2 — Dealer level: IDS UK CV (ITUK) x ITUK dealer sell-out

IDS UK CV dealers: **44** · ITUK sell-out entities: **64** · matched **dealer groups: 31**

Unmatched IDS: PENTAGON
Sell-out with no IDS: ALK, ANDYPOWELL, CROSSSTREET, DITCHBURN, ERIKSOMMERA, GRAYCOLLTRAILER, LPMOBILEREPAIR, MOTU, SMV, TECHNI, TG, THOMPSON, WADE, WMS2007TAWM

**Caveat that kills half the value: UK CV IDS is `totals_only` — there is no Section D (Parts) score for ITUK. This dealer-level test can only use the TOTAL score.**

| X | Y | level | n | Pearson r | Spearman rho | p (rho) | verdict |
|---|---|---|--:|--:|--:|--:|---|
| IDS total % | log10 parts purchases EUR CY2025 | dealer group | 31 | 0.143 | 0.204 | 0.2715 | noise |
| IDS total % | parts purchases EUR CY2025 | dealer group | 31 | 0.214 | 0.204 | 0.2715 | noise |
| IDS total % | parts qty CY2025 | dealer group | 31 | 0.155 | 0.156 | 0.4015 | noise |
| IDS total % | genuine-only share of EUR | dealer group | 31 | -0.33 | -0.269 | 0.1431 | noise |
| IDS total % | BVP share of EUR | dealer group | 31 | 0.02 | 0.101 | 0.5892 | noise |
| IDS total % | contested-genuine share | dealer group | 31 | 0.253 | -0.008 | 0.9639 | noise |
| IDS total % | EUR per site (size-normalised) | dealer group | 31 | 0.275 | 0.197 | 0.2873 | noise |

**Partial correlation** IDS total % vs genuine-only share, controlling for dealer size (log EUR): r = **-0.372** (p=0.039, n=31).

**Is the size result an aggregation artefact?** Checks:

- IDS score vs number of sites in the group: rho = 0.045 (p=0.810) — multi-site groups do *not* score higher, so the € result is not just 'groups are bigger'.
- Partial correlation IDS vs log €, controlling for #sites: r = **0.128** (p=0.493).
- **Single-site dealer groups only: rho = 0.264 (p=0.2133, n=24)** — the cleanest cut, and it is stronger than the pooled one.
- Leave-one-out jackknife: rho stays in [0.129, 0.291] — no single dealer drives it.

**Site-level cross-check** (unambiguous 1:1 site pairs only, n=39):

| X | Y | level | n | Pearson r | Spearman rho | p (rho) | verdict |
|---|---|---|--:|--:|--:|--:|---|
| IDS total % | log10 parts EUR | dealer site | 39 | 0.067 | 0.095 | 0.5655 | noise |
| IDS total % | genuine-only share | dealer site | 39 | -0.164 | -0.201 | 0.2195 | noise |
| IDS total % | BVP share | dealer site | 39 | -0.018 | 0.04 | 0.808 | noise |

**PMS leakage vs IDS** (ITUK leakage study, n=31 groups):

| X | Y | level | n | Pearson r | Spearman rho | p (rho) | verdict |
|---|---|---|--:|--:|--:|--:|---|
| IDS total % | PMS leakage gap EUR | dealer group | 31 | -0.082 | -0.108 | 0.5625 | noise |
| IDS total % | leakage EUR per unit sold | dealer group | 31 | -0.369 | -0.371 | 0.04 | weak/marginal |

**Dealer-level multiple testing.** 10 tests run; 0 at p<0.05 vs 0.5 expected by chance; surviving Benjamini-Hochberg FDR 10%: **0**.

---

## L3 — DB / country level: IDS x PMS x GPS x KPI x UIO

DBs with IDS + at least one business metric: **13**

| DB | dealers | IDS total | IDS D | PMS total capt | PMS genuine capt | genuine share | GPS EUR/UIO | GPS vs max | KPI fill | KPI MOS | UIO |
|---|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|
| MALTA | 1 | 89.3 | 87.2 | 32.9 | 32.8 | 98.9 | 198.6 | 54.5 | 0.9 | 115.7 | 1040 |
| PORTUGAL | 16 | 86.7 | 88.6 | 32.4 | 12.8 | 41.9 | 209.1 | 48.9 | — | — | 8176 |
| HUNGARY | 19 | 86.4 | 89.5 | 19.1 | 14.1 | 70.7 | 88.4 | 35.4 | — | — | 3734 |
| POLAND | 23 | 84.8 | 87.5 | — | — | — | — | — | 0.8 | — | — |
| ITUK | 44 | 83.8 | — | 65.9 | 55.0 | 84.7 | 248.5 | 47.0 | 0.9 | 137.8 | 22389 |
| IUK | 45 | 81.5 | 81.7 | 17.3 | 15.6 | 77.0 | 128.3 | 51.3 | 0.9 | 74.8 | 47783 |
| DENMARK | 20 | 79.8 | 76.1 | 30.2 | 29.2 | 87.2 | 174.2 | 69.5 | — | — | 851 |
| ROMANIA | 15 | 79.5 | 80.1 | 36.6 | 28.1 | 82.6 | 163.6 | 65.4 | 0.9 | 119.8 | 1071 |
| NORWAY | 38 | 78.9 | 78.7 | 26.9 | 22.1 | 87.4 | 178.7 | 71.5 | 1.0 | 98.2 | 7929 |
| BELGIUM | 44 | 78.0 | 79.1 | 25.9 | 17.6 | 58.7 | 219.9 | 85.9 | 0.8 | 47.2 | 9594 |
| CYPRUS | 1 | 75.0 | 72.3 | 50.1 | 26.9 | 46.3 | 185.6 | 63.3 | — | — | 2308 |
| GREECE | 34 | 73.8 | 73.3 | 40.3 | 22.7 | 56.7 | 139.0 | 54.6 | 0.6 | 60.0 | 3742 |
| UMI | 29 | 62.6 | 61.6 | 21.3 | 7.1 | 18.4 | 179.0 | 71.6 | 1.0 | 147.0 | 18542 |

**All DB-level pairs** (Spearman is the one to read — n is small and distributions are skewed):

| X | Y | level | n | Pearson r | Spearman rho | p (rho) | verdict |
|---|---|---|--:|--:|--:|--:|---|
| IDS total % | PMS TOTAL capture (primary) | DB | 12 | 0.093 | -0.035 | 0.9141 | noise |
| IDS total % | PMS genuine capture (secondary lens) | DB | 12 | 0.354 | 0.21 | 0.5128 | noise |
| IDS total % | genuine EUR share of PMS mix | DB | 12 | 0.666 | 0.469 | 0.1245 | noise |
| IDS total % | GPS EUR/UIO | DB | 12 | 0.035 | 0.105 | 0.7456 | noise |
| IDS total % | GPS capture vs max | DB | 12 | -0.554 | -0.706 | 0.0102 | signal |
| IDS total % | KPI first fill rate | DB | 9 | 0.036 | -0.1 | 0.798 | noise |
| IDS total % | KPI months of stock (days) | DB | 8 | -0.112 | 0.143 | 0.7358 | noise |
| IDS total % | KPI parts sales per unit EUR | DB | 3 | 0.995 | 1.0 | 0.0 | n too small |
| IDS total % | log10 UIO (network size) | DB | 12 | -0.211 | -0.14 | 0.6646 | noise |
| IDS Section D % | PMS TOTAL capture (primary) | DB | 11 | -0.172 | -0.3 | 0.3701 | noise |
| IDS Section D % | PMS genuine capture (secondary lens) | DB | 11 | 0.164 | -0.1 | 0.7699 | noise |
| IDS Section D % | genuine EUR share of PMS mix | DB | 11 | 0.551 | 0.327 | 0.3259 | noise |
| IDS Section D % | GPS EUR/UIO | DB | 11 | -0.148 | -0.109 | 0.7495 | noise |
| IDS Section D % | GPS capture vs max | DB | 11 | -0.573 | -0.691 | 0.0186 | signal |
| IDS Section D % | KPI first fill rate | DB | 8 | -0.027 | -0.238 | 0.5702 | noise |
| IDS Section D % | KPI months of stock (days) | DB | 7 | -0.327 | -0.071 | 0.879 | n too small |
| IDS Section D % | KPI parts sales per unit EUR | DB | 3 | 0.983 | 1.0 | 0.0 | n too small |
| IDS Section D % | log10 UIO (network size) | DB | 11 | -0.17 | -0.045 | 0.8944 | noise |
| IDS Section C % | PMS TOTAL capture (primary) | DB | 11 | 0.126 | 0.109 | 0.7495 | noise |
| IDS Section C % | PMS genuine capture (secondary lens) | DB | 11 | 0.336 | 0.182 | 0.5926 | noise |
| IDS Section C % | genuine EUR share of PMS mix | DB | 11 | 0.427 | 0.191 | 0.5739 | noise |
| IDS Section C % | GPS EUR/UIO | DB | 11 | -0.004 | 0.264 | 0.4334 | noise |
| IDS Section C % | GPS capture vs max | DB | 11 | -0.347 | -0.491 | 0.1252 | noise |
| IDS Section C % | KPI first fill rate | DB | 8 | -0.048 | -0.405 | 0.3199 | noise |
| IDS Section C % | KPI months of stock (days) | DB | 7 | -0.307 | -0.179 | 0.7017 | n too small |
| IDS Section C % | KPI parts sales per unit EUR | DB | 3 | 0.369 | 0.5 | 0.6667 | n too small |
| IDS Section C % | log10 UIO (network size) | DB | 11 | -0.476 | -0.455 | 0.1601 | noise |
| IDS Section B % | PMS TOTAL capture (primary) | DB | 11 | -0.023 | -0.127 | 0.7092 | noise |
| IDS Section B % | PMS genuine capture (secondary lens) | DB | 11 | 0.351 | 0.109 | 0.7495 | noise |
| IDS Section B % | genuine EUR share of PMS mix | DB | 11 | 0.573 | 0.491 | 0.1252 | noise |
| IDS Section B % | GPS EUR/UIO | DB | 11 | 0.044 | -0.027 | 0.9366 | noise |
| IDS Section B % | GPS capture vs max | DB | 11 | -0.547 | -0.7 | 0.0165 | signal |
| IDS Section B % | KPI first fill rate | DB | 8 | 0.057 | -0.048 | 0.9108 | noise |
| IDS Section B % | KPI months of stock (days) | DB | 7 | 0.01 | -0.036 | 0.9394 | n too small |
| IDS Section B % | KPI parts sales per unit EUR | DB | 3 | 0.995 | 1.0 | 0.0 | n too small |
| IDS Section B % | log10 UIO (network size) | DB | 11 | -0.278 | -0.218 | 0.5192 | noise |

**Baumann sensitivity (zeros in vs out).** FR/ES have no PRISM DB mapping, so the red-marked zeros never enter the DB-level correlations at all:

- PMS total capture: rho with zeros IN = -0.035 (n=12) · zeros OUT = -0.035 (n=12)
- GPS EUR/UIO: rho with zeros IN = 0.105 (n=12) · zeros OUT = 0.105 (n=12)
- genuine share: rho with zeros IN = 0.469 (n=12) · zeros OUT = 0.469 (n=12)

**Top DB-level by |rho| (n>=8):**

| X | Y | level | n | Pearson r | Spearman rho | p (rho) | verdict |
|---|---|---|--:|--:|--:|--:|---|
| IDS total % | GPS capture vs max | DB | 12 | -0.554 | -0.706 | 0.0102 | signal |
| IDS Section B % | GPS capture vs max | DB | 11 | -0.547 | -0.7 | 0.0165 | signal |
| IDS Section D % | GPS capture vs max | DB | 11 | -0.573 | -0.691 | 0.0186 | signal |
| IDS Section C % | GPS capture vs max | DB | 11 | -0.347 | -0.491 | 0.1252 | noise |
| IDS Section B % | genuine EUR share of PMS mix | DB | 11 | 0.573 | 0.491 | 0.1252 | noise |
| IDS total % | genuine EUR share of PMS mix | DB | 12 | 0.666 | 0.469 | 0.1245 | noise |
| IDS Section C % | log10 UIO (network size) | DB | 11 | -0.476 | -0.455 | 0.1601 | noise |
| IDS Section C % | KPI first fill rate | DB | 8 | -0.048 | -0.405 | 0.3199 | noise |
| IDS Section D % | genuine EUR share of PMS mix | DB | 11 | 0.551 | 0.327 | 0.3259 | noise |
| IDS Section D % | PMS TOTAL capture (primary) | DB | 11 | -0.172 | -0.3 | 0.3701 | noise |

### DB-level robustness — three reasons to distrust the table above

**(1) Single-dealer 'countries'.** MALTA and CYPRUS have **1 IDS dealer each**; their 'country average' is one man's self-assessment carrying the same weight as ITUK's 44.

- IDS total % vs GPS capture vs max: all DBs rho=-0.706 (n=12) → **DBs with >=5 dealers rho=-0.806 (p=0.0049, n=10)**
- IDS total % vs genuine EUR share: all DBs rho=0.469 (n=12) → **DBs with >=5 dealers rho=0.200 (p=0.5796, n=10)**
- IDS total % vs PMS total capture: all DBs rho=-0.035 (n=12) → **DBs with >=5 dealers rho=0.018 (p=0.9602, n=10)**
- IDS Section D % vs GPS capture vs max: all DBs rho=-0.691 (n=11) → **DBs with >=5 dealers rho=-0.700 (p=0.0358, n=9)**
- IDS Section D % vs genuine EUR share: all DBs rho=0.327 (n=11) → **DBs with >=5 dealers rho=0.117 (p=0.7650, n=9)**
- IDS Section D % vs PMS total capture: all DBs rho=-0.300 (n=11) → **DBs with >=5 dealers rho=-0.283 (p=0.4600, n=9)**

**(2) `GPS capture vs max` is a target-relative ratio, and the target is not constant.** Back-solving `spend_per_unit / gps_capture_vs_max` recovers the per-DB € target:

| DB | GPS €/UIO | capture vs max | implied € target per vehicle |
|---|--:|--:|--:|
| ITUK | 248.5 | 47.0% | 529 |
| PORTUGAL | 209.1 | 48.9% | 427 |
| MALTA | 198.6 | 54.5% | 364 |
| CYPRUS | 185.6 | 63.3% | 293 |
| BELGIUM | 219.9 | 85.9% | 256 |
| GREECE | 139.0 | 54.6% | 255 |
| DENMARK | 174.2 | 69.5% | 251 |
| HUNGARY | 88.4 | 35.4% | 250 |
| IUK | 128.3 | 51.3% | 250 |
| NORWAY | 178.7 | 71.5% | 250 |
| ROMANIA | 163.6 | 65.4% | 250 |
| UMI | 179.0 | 71.6% | 250 |

- rho(IDS total, **implied target**) = **0.473** (p=0.1205, n=12)
- rho(IDS total, **raw GPS €/UIO**) = 0.105 (p=0.7456, n=12)

Most DBs sit on a flat €250 target; ITUK (528), Portugal (427), Malta (364) and Cyprus (293) carry heavier CV/segment-mix targets. Those same DBs score high on IDS. So the headline 'high IDS = low GPS capture' is **mostly the denominator**: high-IDS markets are the ones measured against a harder target. Against the raw €/UIO numerator the relationship evaporates.

**(3) Multiple testing.** 29 DB-level tests with n>=8; **3** came in at p<0.05 where 1.5 are expected by chance alone. Survivors under Benjamini-Hochberg FDR 10%: **0**. And the IDS sections inter-correlate at rho 0.66–0.91, so these are nowhere near independent tests — the effective number of questions asked is far smaller than 29, but so is the evidence.

Controlling for the target, the relationship halves and loses significance: partial r = **-0.446** (p=0.147, n=12). Inside the 8 DBs that share the flat €250 target — where capture-vs-max is just a rescaling of €/UIO — rho = **-0.690** (p=0.058). So a negative tilt does survive, but on n=8 with UMI (low IDS, high GPS) and Hungary (high IDS, low GPS) as the leverage points. Directionally interesting, not actionable.

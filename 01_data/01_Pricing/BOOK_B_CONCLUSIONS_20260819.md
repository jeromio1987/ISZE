# Book B — conclusions (internal · 2026-08-19)

> **2026-09-22 — the ambition question behind this file is CLOSED, permanently.** Jerome, verbatim:
> *"delete price ambition I will come when it's done for now do a simulation on 5% increase and
> than never ask again."* The "blocked on ambition" wording below is stale as a *question*: nothing
> was rebuilt and this file was not rewritten. **Do not ask him to choose an ambition value.** Last
> output: the +5% flat simulation of 2026-09-22 — record:
> [`00_docs/PRICE_AMBITION_CLOSED_2026-09-22.md`](../../00_docs/PRICE_AMBITION_CLOSED_2026-09-22.md).

**Status:** planning weight only — **not a publishable list revision.** No alloc run.  
**Review pack:** `01_data/00_derived/revision_book_b_top_review.csv` (Build 2b)  
**Full join:** `revision_book_b_review_pack.csv` · **Meta:** `revision_book_b_pack.meta.json`  
**Plan:** `PLAN_FORECAST_WEIGHTED_AMBITION.md`

---

## Verdict

Book B correctly says **put more of the next price rise on brakes, filters, and P700/UTI launch lines** — but until seed € lands and IAM/leakage guardrails are applied PN-by-PN, it stays a **planning weight**, not a list you can ship.

---

## What Book B says (provisional)

| | Book A | Book B |
|--|--------|--------|
| Weight | Past L12M € | L12M × growth factor |
| Target | +3% exact (when alloc runs) | **You choose** (+4% / +5% / launch-only) |

| Coverage | PN | L12M € | Forecast weight € |
|----------|-----|--------|-------------------|
| HAS_WEIGHT | 6,326 | €12.76M | **€14.52M** (+13.8% avg GF) |
| NEED_SEED / no L12M | 9,591 | — | cannot weight yet |

**~60% of forecast weight is launch-tagged** (RG21 + P700 + UTI ×1.25). Book B re-centres on **parc ramp**, not legacy bestsellers.

**Bucket share of forecast weight:** flat 1.0 **40%** · P700 carryover+UTI **31%** · RG21 first-fail **11%** · RG21 interval **6%**.

**Family share shift vs Book A:** brakes **+1.4 pp**, filters **+1.1 pp**.

---

## What it does not say yet

1. **Ambition % not chosen** — no +4% / +5% solve.  
2. **9,591 PNs without L12M** — 826 P700 new-only (ISIM, ADAS, LED…) need seed € from IML/IMIT/UTI.  
3. **Growth factors are midpoints** — not signed off.  
4. **θ_interval / SCR mix** still blocked for parc weighting.  
5. **internal only** — not an IML/IMIT narrative until you sign off.

---

## Build 2b overlay (revision × Book B)

| Metric | Count |
|--------|------:|
| Book B PNs with DB revision activity | 4,918 |
| Review pack rows | 18,401 |
| PNs flagged for review (excl HOLD / RAISE_OK / NO_ACTIVITY) | ~4,744 |
| Top-500 list mix | ~285 leakage · ~117 high-list-exposure · ~83 proxy-adverse |

**Which side the `RAISE_OK_ROOM_VS_IAM` exclusion drops.** `RAISE_OK_ROOM_VS_IAM` now means the peer shop is more than 10% **above** our reference dealer price (index > 1.10) — we already hold the premium and a raise is defensible. Excluding it from the "needs review" set therefore drops the rows we have least to worry about. It does **not** drop the rows where we look expensive: those are flagged `REVIEW_IAM_UNDERCUT` (index < 0.80) and stay in the review set.

**69% of Book B seeds (10,999 / 15,917) have no CY2025 DB→DLR activity** — mostly `other_gf_1_0` and `p700_new_only_seed`. Leakage dominates where activity exists; top sell-out rows skew **IUK** (separate from ITUK).

---

## Guardrails on weighted PNs (revision queue)

On the 6,326 weighted PNs, sell-out/revision flags dominate:

| Action | ~count |
|--------|--------|
| REVIEW_LEAKAGE | 3,222 |
| REVIEW_OVERSTOCK | 1,241 |
| REVIEW_HIGH_LIST_EXPOSURE | 1,157 |
| REVIEW_PROXY_ADVERSE | 593 |
| REVIEW_IAM_UNDERCUT | 26 |

**What the 26 `REVIEW_IAM_UNDERCUT` rows mean.** The label is the guardrail side: the peer shop is more than 20% below our reference dealer price (index < 0.80), so we look expensive on those part numbers. Before the direction fix these 26 rows were the peer-dearer ones, which was backwards. The direction of `ks_price_index` is peer shop ÷ our reference dealer price — below 1.0 is cheaper than us.

**Use Book B for family ambition; use revision pack for PN hold/review.**

Examples:

- `8982447940` (pad hero): Book B gainer but **HOLD_DEFAULT on ITUK** — do not blind-raise.  
- Top gainers often **IAM-undercut** or **leakage on one DB** while hot on another.

---

## Your decisions (before any Book B alloc)

1. Ambition target: **+4%? +5%? launch-only buckets?**  
2. Keep **UTI ×1.25** on P700 recommended? (drives ~34% of weight)  
3. Seed € for P700 new-only — wait for IML BOM or use UTI list placeholders?  
4. Guardrail rule: auto-**HOLD** on `REVIEW_IAM_UNDERCUT` + `REVIEW_PROXY_ADVERSE`?

---

## Next step (still no alloc until you say)

1. Pick ambition scope (one sentence).  
2. Seed pass → re-run `04_tools/forecast/build_book_b_provisional.py`.  
3. Then Book B alloc + merge `revision_book_b_top_review.csv` for sign-off sheet.  
4. Keep **Book A +3%** as baseline IML story until Book B is seeded and guardrails signed.

# ITUK PMS — SPA scope study: which parts belong in the Special Price Agreement

**Jerome-only working note, 2026-08-10.** Not vetted for IML/ITUK sharing — internal PN-level analysis on top of the existing SPA campaign, done to answer: *which PMS parts does ITUK actually need in the SPA to move the sales needle?*

**Method:** re-ran `02_dashboards/Data/90_INBOX/suzuki_pms_mail_pull/spa_ituk_fig_audit.py`'s logic against the current SPA campaign definition, cross-checked with `01_data/00_derived/{aim_pn_classification,ituk_pms_pn_audit,sales_by_db_fig_key_year}.csv` and `03_analytics/Isuzu/prism/data/fig_key_taxonomy.yaml`. Numbers below are **ITUK actual sales 2023–2026 (2026 partial)**, not the Model B/IML v7 demand model — this is a supply-side (what's priced) vs demand-side (what sells) reconciliation, not a new capture-rate claim.

---

## Bottom line

The current 55-PN SPA pack is **already brake-led in practice** (49% of pack revenue from 7 PNs) which matches the phase-one call, but **38% of its PNs (21/55) have never sold to ITUK**, and there's a specific, checkable mismatch in the rear-brake-shoe SKUs plus one real whitespace category (AdBlue/urea filter, €43.6K/yr ITUK revenue) sitting entirely outside SPA pricing. A v2 scope should keep the brake-pad core, swap or drop the dead rear-shoe SKUs, add urea filter, and force an explicit decision on clutch (12 PNs / 3.6% of revenue, contradicts the "clutch deferred" call).

The one thing I can't finish from this repo: the **actual SPA price/discount levels**. The source workbook (`01_data/03_PMS/PMS SPA study_ISZE (1).xlsx`) that defines what ITUK is charged per PN is **not committed to GitHub** — only a derived PN/category/fig-key audit survived into the repo. Any GP-impact sizing on a v2 scope needs that file (or a fresh export) landed in `01_data/90_INBOX/`.

---

## 1. What "SPA" is, and what's in scope today

SPA = **Special Price Agreement** — discounted net pricing on specific PNs (`05_memory/glossary.md`). Per `DECISIONS.md` (2026-06-15 entry): *"SPA campaign packs are price-only"* — the SPA file carries PN + price, not interval/demand data. That's a different lever from the Model B capture-gap work in `FACTS.md` §1: Model B tells you **which categories have unmet demand**; SPA is **how you make the priced part cheap enough for a dealer to fit genuine instead of aftermarket**.

Current campaign = 4 vehicle/engine packs, **55 unique PNs**:

| Pack | Vehicle / engine | PNs |
|---|---|---:|
| Main 7.5t | NPR75 / N75 / 4HK1 | 17 |
| Main 4JZ1 N75 | NPR88 / N75 / 4JZ1 | 20 |
| Main N35 | NLR87 / N35.125 / RZ4E | 18 |
| Secondary N35 | NLR88 / N35.150 / 4JZ1 | 14 |

---

## 2. How the current pack is actually performing (ITUK, 2023–2026 partial)

| Category | # PNs | # dead (0 sales) | ITUK qty | ITUK revenue € | % of pack revenue |
|---|---:|---:|---:|---:|---:|
| Brake | 7 | 4 | 12,724 | 1,058,502 | 49.0% |
| Fuel filter | 18 | 6 | 47,714 | 570,675 | 26.4% |
| Oil filter | 8 | 3 | 35,413 | 249,935 | 11.6% |
| Air filter | 10 | 4 | 6,752 | 203,775 | 9.4% |
| Clutch | 12 | 4 | 967 | 77,630 | 3.6% |
| **Total** | **55** | **21** | **103,570** | **2,160,517** | |

Notes:
- **One PN carries a third of the whole pack**: `8982447940` (Brake Pad Kit, fig 302-017) = €728,508, 34% of total pack revenue on its own. The pack's brake performance is really one SKU's performance.
- **21/55 PNs (38%) show zero ITUK sales** across four years — mostly BVP filter variants and, notably, the rear-drum brake shoe lines (see §4). "Zero" doesn't automatically mean "wrong part" — some may be genuinely low-fitment variants — but a pack this size shouldn't be carrying that much dead weight without someone checking why.
- Fuel filter's 26% share sits on 18 PNs — much of that is oil/fuel service-pack bundling working as intended (Model B has fuel at 65.1% cover already, the highest of the five categories).

---

## 3. Does this match the phase-one decision?

Per `05_memory/projects/pms-coverage.md` (Apr 2026 ITUK trip) and the 27 Jul 2026 IML meeting: **N75, Brake + Air = phase-one** (brake = offensive, recover IAM share; air = defensive, filtration "already competitive" on price). **Oil + fuel = service-pack support only. Clutch explicitly deferred** — genuine clutch barely sells and the manual/automatic addressable base is unresolved pending IML VIN/MT-AT data.

| Category | Strategic call | Pack reality | Read |
|---|---|---|---|
| Brake | Phase-one, offensive | 49% of pack revenue | **Aligned** — the pack already behaves like brake is the priority |
| Air filter | Phase-one, defensive | 9.4% of revenue, 4/10 PNs dead | **Underperforming its own priority** — biggest € gap in Model B (€736K) isn't showing up here |
| Oil / fuel | Support bundle | 38% combined revenue | **Aligned**, doing its bundling job |
| Clutch | **Deferred** | 12 PNs, real SPA price slots, 3.6% revenue | **Not aligned** — a deprioritized category still occupies a quarter of the pack's PN count |

The clutch line isn't a rounding error to ignore — it's 12 of 55 SPA slots (22% of the pack) tied up in a category IML/ITUK agreed not to push. Worth a explicit call: prune to the 2–3 clutch PNs that actually sell (`8982551391`, `8981649171`, `5876100771`, `5876100910` are the only ones with real volume) and free the rest, or leave it and stop calling clutch "deferred."

---

## 4. Two checkable gaps at fig-key level

### a) Likely SKU mismatch — rear brake shoe

The pack prices `305-124` (Rear Brake Shoe ASM) and `305-218` (Rear Brake Shoe Kit) — PNs `5878320440`, `8973319320`, plus the BVP variants — and **all of them show zero ITUK sales**. But fig-keys `305-001` (Shoe; BRK,RR) and `305-002` (Lining set; RR BRK, standard) are **not in the SPA pack at all**, and they carry real, current ITUK demand:

| Fig-key | Label | In SPA pack? | ITUK CY2025 | ITUK CY2026 (partial) |
|---|---|---|---:|---:|
| 305-124 / 305-218 | Rear Brake Shoe ASM/Kit | Yes — 0 sales | — | — |
| 305-001 | Shoe; BRK,RR | **No** | 164 units / €14,517 | 93 units / €9,063 |
| 305-002 | Lining set; RR BRK, standard | **No** | 16 units / €1,428 | 6 units / €508 |

Reads like ITUK's dealers are ordering a different rear-shoe SKU than the one the SPA pack discounts. Could be a genuine fitment split (different axle/trim), or the priced PNs are superseded/wrong. Either way it's a 10-minute EQ-HIT check, not a guess — see §6.

### b) Front shoe ASM (301-001) — real demand, not priced

Not in the SPA pack at all. ITUK CY2025: 79 units / €5,141; CY2026 (partial, already ahead of last year's pace): 116 units / €7,810.

### c) Whitespace — Urea (AdBlue) filter (873-042)

**Entirely outside both the SPA pack and the Model B 5-category model** (`FACTS.md` §1 only covers oil/fuel/air/clutch/brake). Real ITUK revenue: **1,319 units / €43,583 in CY2025 alone**, 5 distinct PNs, sold with zero SPA price support. This is a Euro6/AdBlue-generation consumable — the addressable parc only grows as the fleet ages into replacement cycles. It isn't in anyone's PMS category conversation right now.

---

## 5. Recommended SPA v2 scope (draft — needs sign-off, not a decision)

| Category | Action | Why |
|---|---|---|
| Brake pad (302-017 + kits) | **Keep as-is** | Core of the pack, proven revenue, matches phase-one |
| Rear brake shoe | **Investigate + likely swap** 305-124/218 → 305-001/002 | Priced SKUs sell zero; unpriced SKUs carry real demand (§4a) |
| Front shoe ASM (301-001) | **Add** | Real, growing ITUK demand with no price support |
| Air filter (130-001/130-006) | **Keep, but audit the 4 dead PNs** | Phase-one category underperforming its own € case |
| Urea/AdBlue filter (873-042) | **Add** | €43.6K/yr real ITUK revenue, zero price support, growing category |
| Oil / fuel filter | **Keep, bundle-only** | Already doing its job as service-pack support |
| Clutch | **Jerome call needed** | Either prune to the 3–4 PNs with real volume or drop — current state contradicts "deferred" |

This is a **scope** recommendation, not a priced one — I don't have the discount levels to know what any of this costs in GP. See §6.

---

## 6. Data needed beyond GitHub

Ranked by what actually blocks a decision:

1. **The SPA pricing workbook itself** (`01_data/03_PMS/PMS SPA study_ISZE (1).xlsx`) — referenced by the audit scripts at a local Windows path, **not in this repo**. Without it I can only reason about PN/fig-key inclusion, not discount %, net price, or GP impact of any v2 change. Drop the current version (or a fresh export) into `01_data/90_INBOX/` and it'll get sorted per `DATA_MANIFEST.md`.
2. **EQ-HIT / ITUK confirmation on rear brake shoe SKUs** — is 305-124/305-218 still valid and orderable, or superseded by 305-001/305-002? This is the one finding in §4a that changes the recommendation depending on the answer, and it's a catalog lookup ITUK or EQ-HIT access can settle directly.
3. **IML service-interval confirmation** — already an open ask (`01_data/03_PMS/ISZE_ITUK_Brake_Factor_IML_Ask_2026-07-23.md`, `mp/SHARE/DATA_ASKS_IML_and_all_DBs.md`): brake pad/shoe per-axle unit definition, rotor interval, authoritative km intervals. Unchanged by this study, still blocking.
4. **Urea/AdBlue filter replacement interval — no ask exists for this yet.** Needs adding to the next IML data ask if urea filter goes into SPA v2 or the Model B category set; there's currently no interval basis to size expected demand for this category at all.
5. **ITUK fleet trim mix (front disc vs rear drum vs any rear-disc variants)** — would explain the fig-key pattern in §4 directly instead of inferring it from sales presence/absence.
6. **VIN/MT-AT split** — already an open ask, needed before touching the clutch decision either way.
7. **Refreshed IAM competitor pricing** (KS International, JDS) — the only source is the Apr 2026 trip report; it's the commercial justification for discounting brake specifically (KS ~60–75% below ITUK wholesale) and it's four months old.

None of (2)–(7) exist in this GitHub repo in a form I can pull today — they're either open asks already in flight or new asks this study surfaces.

---

## Sources

- `02_dashboards/Data/90_INBOX/suzuki_pms_mail_pull/spa_ituk_fig_audit.py` + `.txt` (audit run, campaign pack definition, dead-PN list)
- `03_analytics/Isuzu/prism/data/fig_key_taxonomy.yaml` (fig-key → PMS category labels)
- `01_data/00_derived/sales_by_db_fig_key_year.csv` (ITUK fig-key revenue, 2025/2026)
- `FACTS.md` §1 (Model B category cover/gap), `05_memory/projects/pms-coverage.md` (phase-one decision, trip report pointer)
- `01_data/03_PMS/ISZE_ITUK_Brake_Factor_IML_Ask_2026-07-23.md`, `mp/SHARE/DATA_ASKS_IML_and_all_DBs.md` (existing open asks)

## Next steps

| # | Action | Owner | Timeline |
|---|---|---|---|
| 1 | Confirm 305-124/218 vs 305-001/002 SKU validity in EQ-HIT | Jerome / ITUK (James Marsh) | Before any SPA v2 pricing work |
| 2 | Land current SPA pricing workbook in `01_data/90_INBOX/` | Jerome | Next data pass |
| 3 | Decide clutch: prune to top 3–4 PNs or drop from SPA | Jerome | With v2 scope sign-off |
| 4 | Add urea/AdBlue filter interval to next IML data ask | Jerome | Next IML contact |
| 5 | Audit the 4 dead air-filter PNs (fitment check) | Jerome / ITUK | Before adding air filter spend |

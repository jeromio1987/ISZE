# Decision pack — 2026-09-14 (Mode B)

**For:** Jerome · **One sitting.** Tick a box per row. Until a row is ticked, **nothing gated in that row is applied in code.**

**This pack does not:** change P4 thresholds, run Book B alloc, mark forecast G1, quote leakage € in Mode A, or ship HTML.

**Related:** [`ISZE_ROADMAP.md`](ISZE_ROADMAP.md) §2 · [`AFTERMARKET_BI_BUILD_MENU_20260819.md`](AFTERMARKET_BI_BUILD_MENU_20260819.md) Tier B · [`P4_DETERMINISTIC_SIGNALS.md`](P4_DETERMINISTIC_SIGNALS.md) · [`LIST_TO_POCKET_VALIDATION_20260819.md`](../01_data/01_Pricing/LIST_TO_POCKET_VALIDATION_20260819.md)

**Agent run in the same pass (does not wait on these ticks):** Monday OS seed ≤5 REVIEW rows · tender diagnose · fig-key / EPC · scraper quality V2. See `DECISIONS.md` 2026-09-14.

---

## How to tick

Reply with the **Rec** letter per row, or write the override in one line. Blank = still waiting; gated productize (Step 5) does not start.

| Tick | Meaning |
|------|---------|
| **Rec** | Accept the recommended default in that row |
| **Override** | Your wording wins; agent records it in `DECISIONS.md` then acts |
| **Hold** | Leave the item exactly as it is |

---

## Pack

| Ref | Question | Recommended default | Why | Tick |
|-----|----------|---------------------|-----|------|
| **B5** | P4 amber/red — call list or not? | **Hold productize.** Keep the numeric draft in `P4_DETERMINISTIC_SIGNALS.md` §2. Do **not** treat 10 RED / 6 AMBER of 17 DBs as a call list. Next: you pick **tighten to ≤5 DBs** *or* **I accept this noisy set**. | Draft flags fire on almost the whole book. Early Warning stays the sales call list until 4.9. | |
| **L2P** | May leakage € leave the room (Mode A)? | **Keep Mode B.** Joins are already verified (2026-08-20) and year-matching is accepted. Remaining gate is **NO_LIST coverage**, not the join. Do not re-litigate year-match. | Coverage ~86–91%; 7 blank PR00 prices; 2026 uses the current list not a Jan snapshot. Quote only after EPC / residual NO_LIST (hub §1 item 9). | |
| **B6 / G1** | Forecast go-live on 98.2% catalogue? | **Do not G1.** Surface stays `pages/19_Forecast.py` **pre-G1**. | Catalogue bar is met. Median WAPE **49.4%** is the binding constraint, not coverage. | |
| **B7** | Who may override a forecast? | **Jerome only**, reason required. Alert if `sum(\|delta\|) / sum(forecast) > 15%` (already in the P5 spec). | Without this, G1 could not go live even after a later accuracy pass. | |
| **B1** | Book B alloc ambition? | **Launch-only.** No +4% / +5% solve. Book B stays a **review list**. | ~60% of forecast weight is already launch-tagged (RG21 + P700 + UTI ×1.25). Alloc without seed € and IAM guardrails is a fake list. | |
| **B2** | Seed € for 9,591 no-L12M PNs? | **Leave them out of every € ranking** until IML BOM / UTI placeholders exist. | Those PNs cannot be weighted. Inventing seed € would distort Book B. | |
| **B3** | Lock growth factors 1.24 / 1.25 / ×1.25 UTI? | **Keep as unsigned planning.** Do not lock. | Forecast and alloc inherit an unsigned assumption if we pretend they are signed. | |
| **B4** | Auto-HOLD on IAM-undercut + proxy-adverse? | **Manual HOLD.** Every exception stays a human row. | Auto-HOLD without a signed guardrail policy locks the revision queue. | |
| **B8** | Book A +3% alloc? | **Skip.** Explicit rebuild only — no default. | Same as the 2026-08-19 build menu. | |
| **B1b** | Approved LLM route for company text? | **Stay closed.** P2b / P3 / P6 remain zero code. Track A (P1 + P2a + P4 + P5) still runs. | No named route. Do not start Cowork/DPIA fiction. | |
| **B10** | Competitor vintage labels on Mode A HTML? | **Skip** until you ask a Mode A **rebuild**. Builder labels already exist. | Packs not rebuilt without the word rebuild. | |
| **A12** | Next sales-review deck? | **Skip** until you name the next DB. | A12 was skipped 2026-08-19 for this reason. | |
| **Sell-out** | Expand dealer sell-out (elasticity / UMI stack)? | **Cannot build without files.** `01_data/90_INBOX/` is **missing in this clone** (not a full of files — the folder is absent). Live CY2025 long files: **ITUK, UTI, IUK, Ireland, Greece**. Missing vs GPS network includes **UMI 1797** (never blend with UTI 1799) plus roughly the rest of the GPS book (Belgium, Portugal, Germany, Nordics, CEE, …). Drop extracts in `90_INBOX/` then say which DB. | Elasticity stays `measure_kind=proxy` until a second full CY per DB. | |

**Never on this pack:** Nordics Doffin / HILMA API keys (DONE 2026-08-25). Autodoc. Gross/SPA on billing. New 0–100 scores.

---

## What already ran without waiting

Recorded so this pack is not mistaken for “nothing happened.”

| Step | What | Status |
|------|------|--------|
| 1 | ≤5 Action Ledger rows seeded `REVIEW` (not ACTIONED); Monday PN → `opportunity_id` crosswalk | this run |
| 2 | Tender: IT/DE vs hub; ES PLACSP retry; next public national source | this run |
| 3 | Fig-key V2 remainder + EPC supersession validation | this run |
| 4 | Scraper quality V2 | this run |
| 5 | P4 widget / G1 / Mode A leakage / Book B alloc | **blocked on ticks above** |

---

## After you reply

Agent records ticks in `DECISIONS.md` (new dated entry). Then, and only then:

| If you tick | Then |
|-------------|------|
| B5 tighten or accept | P4 task 4.10 internal call list / PRISM widget. Still not Mode A until you say **ship**. |
| L2P Mode A | Command Center leakage labels — needs **rebuild** in a later message. |
| G1 | Forecast page caption goes live; override file is Jerome-only. |
| B1 launch-only | Book B stays a review list (already true). Alloc solver stays off. |
| A named next DB | A12 sales-review deck. |

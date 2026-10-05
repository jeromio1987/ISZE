# Decision reconciliation — 2026-09-16

**Purpose:** a draft for the weekly decision slot. Every item currently in
[`ISZE_ROADMAP.md`](ISZE_ROADMAP.md) §1 (open queue) and §2 (waiting on Jerome), read once against what the
workspace already says on paper.

**Hard rule used throughout:** an item is proposed as *record as decided* **only** where a written source proves
the decision was taken - a dated `DECISIONS.md` entry, a dated note in a workspace file, or an explicit
instruction. Chat history is not evidence. Where the paper trail was thin, the item is proposed as *must answer*.
No decision, date, euro figure or approval below is invented; every claim carries the file it came from.

**Outcomes used:** `record as decided` · `kill candidate` · `delegate candidate` · `must answer`.

**Companion rule:** [`DECISION_DISCIPLINE.md`](DECISION_DISCIPLINE.md) - three-place rule, weekly slot, and what a
delegation must contain.

---

## §1 — Open queue

| # | Item | How it reads in the roadmap today | Written evidence of a decision already taken | Proposed outcome |
|---|------|-----------------------------------|----------------------------------------------|------------------|
| 1 | P4 account-health calibration | "Builder live `p4-v1`; draft thresholds fire on 10 RED / 6 AMBER of 17 DBs — not yet a call list". Blocked on **Jerome** for amber/red thresholds | Build decision is recorded: `DECISIONS.md` 2026-08-18 — "Draft thresholds still fire on most of the book — that is why 4.9 (your calibration) is required". The thresholds themselves are unanswered | **must answer** |
| 2 | List-to-pocket sign-off | "Validation ran 2026-08-19 … leakage € stays **internal** until year-matched PR00/ZPR1→net joins are signed in writing". Blocked on **Jerome** — written sign-off | The gate is decided, the sign-off is not: `DECISIONS.md` 2026-08-25 — "Do not quote dealer-leakage / list-to-pocket leakage euros externally … until year-matched PR00/ZPR1 → net joins are validated and signed off in writing" | **must answer** |
| 3 | P5 forecast go-live (G1) | "P5.2 + P5.6 built — 548 series, median WAPE 49.4% …". Blocked on **Jerome** — sign G1 on 98.2% catalogue + override policy | Coverage bar is met but signing is open: `00_docs/roadmaps/ai_sales_intelligence.md` §6.0 — "G1 status: coverage bar **met** on catalogue parts. Still open before signing G1: task **1.4** (year-matched joins), **1.5** (verify rule), EPC validation of the supersession map" | **must answer** |
| 4 | National tender portal coverage | "Analysis done — only 8/29 footprint countries have a live national source; ~69% are TED-only below threshold". Blocked on **nothing** | No decision pending. The work is named in `00_docs/roadmaps/scrapers.md` P0: "Wire **ES PLACSP**, **IT PNCP/ANAC**, **DE oeffentlichevergabe** open data" | **delegate candidate** — name the owner and a date; no Jerome answer needed |
| 5 | Interval-aware air vs oil capture | "Shipped 2026-07-02 on a **provisional 0.5 air factor**". Blocked on IML ratio confirmation | The build decision is recorded: `DECISIONS.md` 2026-07-02 — "Set `air_filter` consumable_factor to **0.5** … Labelled PROVISIONAL". The same entry names the open piece: "**Open on Jerome/IML:** genuine service interval per category + avg annual km per distributor" | **delegate candidate** — chase IML for the interval and average annual km, with a date |
| 6 | ITUK brake wear factor — 0.4 or 0.8 | "0.4 in force and now actually applied (fix 2026-07-21). Do not quote ITUK brake capture as locked". Blocked on ITUK data | `DECISIONS.md` 2026-08-11 — "**ITUK brake 0.4 vs 0.8:** Keep pending — expect data from ITUK soon. Do not change factor." The units question ("does one `brake_pad` unit represent one axle set?") is genuinely unresolved | **delegate candidate** — chase ITUK/IML for the units basis, with a date. The 0.4-vs-0.8 question stays open until that answer lands |
| 7 | LCV generation-aware interval split | "Schedules on disk: RG21 RZ4F-TC **with SCR** = 15k km, without / older = 20k". Blocked on chassis + registration-year cutoffs | `DECISIONS.md` 2026-08-11 — "Still need chassis/reg-year cutoffs for SCR vs non-SCR parc weighting before changing `pms_capture_assumptions.yaml`" | **delegate candidate** — obtain the cutoffs, with a date |
| 8 | Fig-key V2 remainder | "`parts_catalog_dimension` live at 98.9% coverage". Blocked on **nothing** | No decision pending | **delegate candidate** — buildable today; name the owner and a date |
| 9 | Residual PR00 gaps | "24 PN / €67k ZPR1-path hardware + admin non-PN + parked UMI Shell. Supersession billed-on-old 925 PN / €2.48M (IE40 map, **not** EPC-validated)". Blocked on **nothing** | Supersession € is flagged unvalidated in `00_docs/roadmaps/ai_sales_intelligence.md` §6.0 — "Billed under superseded list number: **925 PN / €2.48M** (IE40 `newest_pn`; **not EPC-validated**)" | **delegate candidate** — EPC validation is the next slice; name the owner and a date |
| 10 | P2b / P3 / P6 (language model on mail text) | "Specced, zero code. P2a runs local and deterministic". Blocked on **B1b** then **G0b** | Nothing approved; the kill rule is on paper: `00_docs/roadmaps/ai_sales_intelligence.md` §0 — "**Kill rule:** if no approved LLM route (B1b), P2b/P3/P6 die" | **must answer** — same question as §2 B1b, listed once there |
| 11 | Supabase live Master KPIs (HTML V4) | "Not started". Blocked on schema + credentials | Standing rule points away from a second surface: `00_docs/UI_STACK.md` — "UI choice is presentation only. Do not rebuild the same KPI in HTML *and* Evidence unless HTML is the published export of that view" | **kill candidate** — no consumer has asked for it and the published surface is HTML. Confirm or keep on the queue |
| 12 | Dashboard filename renames | "Blocked by design — build scripts hardcode `vN`". Detail points at the rename plan in `CANONICAL.md` | `00_docs/CANONICAL.md` — "Pending renames (pipeline JSON — do not rename until builders + `gps_reconcile` updated together)". Open since 2026-06-12 with no owner | **delegate candidate** — name an owner and a date, or move it to §5 |
| 13 | Scraper quality V2 | "Tender relevance scoring, `scrape_error` column, RSS parse failures …". Blocked on **nothing** — "small items" | No decision pending | **delegate candidate** — small, unowned; name an owner and a date |
| 14 | Workspace cleanup decisions | **No longer a waiting item** — re-labelled 2026-09-16 to "Both halves already decided in writing … not waiting on Jerome", blocked on nothing | **Both halves are already decided on paper.** `00_docs/UI_STACK.md` — "**Decided:** 2026-06-13" (HTML / GitHub Pages is the external share surface); `00_docs/ISZE_Cleanup_Plan.md` Phase 3 — "**Closed 2026-07-26:** keep as **ops sandbox** indefinitely — no merge timeline" | **record as decided** — done in `ISZE_ROADMAP.md` on 2026-09-16. See the drift note below for the leftover `DECISIONS.md` entry |

### §1 drift note

`DECISIONS.md` still carries an entry titled "Open — ISZE_Dashboard merge timeline" with **Status: Open**, which
contradicts the later written close in `ISZE_Cleanup_Plan.md` (2026-07-26). Supersede that entry rather than
linking it again.

---

## §2 — Waiting on Jerome

| Ref | Item | How it reads in the roadmap today | Written evidence of a decision already taken | Proposed outcome |
|-----|------|-----------------------------------|----------------------------------------------|------------------|
| B1 | **the price adjustment ambition** — +4% / +5% / launch-only | "Revision book stays a review list, never a price move" | **CLOSED PERMANENTLY on 2026-09-22.** This row is historical: it records the position as it stood on 2026-09-16, when Jerome confirmed the item still open. On 2026-09-22 he closed it, verbatim: *"delete price ambition I will come when it's done for now do a simulation on 5% increase and than never ask again."* The +5% flat simulation is its last output. **Do not re-ask in any form.** Record: `00_docs/PRICE_AMBITION_CLOSED_2026-09-22.md` | **closed** — no memo, no signature needed |
| B2 | Seed € for 9,591 PNs with no last-12-month sales | "Those PNs stay out of every € ranking" | Unanswered, and stated as an input slot: `01_data/01_Pricing/PLAN_FORECAST_WEIGHTED_AMBITION.md` — "Fill **NEED_SEED** € for P700-new-only (from launch plan / PRD — not invented)" | **must answer** |
| B3 | Growth-factor sign-off | "Forecast and alloc inherit an unsigned assumption" | Unanswered: `01_data/01_Pricing/PLAN_FORECAST_WEIGHTED_AMBITION.md` — "Provisional growth_factor defaults (edit when you answer)" | **must answer** |
| B4 | Guardrail policy | "Every exception is manual" | Unanswered, framed as a decision: `01_data/01_Pricing/DB_DLR_COMMERCIAL_STACK.md` — "**Still blocked without ambition % + alloc:** cannot rank DB-specific list moves, … or produce final revision targets — pack is guardrail overlay only" | **must answer** |
| B5 | P4 calibration — amber/red thresholds | "Queue item 1 blocked" | Draft thresholds are on paper but uncalibrated: `DECISIONS.md` 2026-08-18 — "Draft thresholds still fire on most of the book". See §1 item 1 - the same question, listed once | **must answer** (same as §1 item 1) |
| B6 / D6 | G1 — sign 98.2% catalogue coverage | "Queue item 3 blocked" | Same evidence as §1 item 3: coverage bar met, signing open (`00_docs/roadmaps/ai_sales_intelligence.md` §6.0) | **must answer** (same as §1 item 3) |
| B7 / D4 | P5 override policy | "Forecast cannot go live even after G1" | Unanswered, and named as a gate: `00_docs/roadmaps/ai_sales_intelligence.md` §4 — "**G4** … override policy agreed" and §19 D4 — "Override policy: who may adjust the forecast, and does it require a reason string" | **must answer** |
| B8 | the base price revision +3% (past-year sales basis) | "Explicit rebuild only — no default" | The standing state is on paper twice: `01_data/01_Pricing/PLAN_FORECAST_WEIGHTED_AMBITION.md` — "stays **+3% on past L12M** — not overwritten; **no new official alloc run id**"; `01_data/01_Pricing/DB_DLR_COMMERCIAL_STACK.md` — "**No +3% alloc run**" | **Ambition half closed 2026-09-22, alloc half unchanged.** B8 was tied to B1 by the 2026-09-16 correction; with B1 closed permanently on 2026-09-22 there is no live ambition question left for it to block on. It is **not** converted into a decision: nothing about the +3% past-year basis or the alloc run has been rebuilt or signed, and no file was rewritten. If Jerome wants that basis to stand as a default it still needs his own dated line in `DECISIONS.md`. See `00_docs/PRICE_AMBITION_CLOSED_2026-09-22.md` |
| B9 | ITUK brake wear factor 0.4 vs 0.8 | "Queue item 6 blocked" | Same evidence as §1 item 6: `DECISIONS.md` 2026-08-11 — "Keep pending — expect data from ITUK soon. Do not change factor" | **delegate candidate** (same as §1 item 6). The 0.4-vs-0.8 question stays open |
| B10 | Competitor vintage labels (shared) | "shared keeps mixed-vintage files unlabelled in the UI" | Half recorded, half open: `DECISIONS.md` 2026-08-18 — "Builder labels for `eucon_price_gap.csv` now say PartsPool Autodoc DE/NO **2026-03-29**, not Eucon 2023 … Country packs / live HTML not rebuilt" | **must answer** — rebuild the packs with the corrected vintages, or declare those files internal-only |
| B1b | Approved route for company text | "P2b / P3 / P6 die; P1 + P2a + P4 + P5 still run" | Still open, dated: `00_docs/roadmaps/ai_sales_intelligence.md` §19 — "**D1b** Approved LLM route named, or P2b/P3/P6 shelved"; blocker table §18 B1b — "Open" | **must answer** — covers §1 item 10 |
| B1c | Shared Sales / Parts mailboxes — works-council step | "Mail corpus stays halved" | Still open: `00_docs/roadmaps/ai_sales_intelligence.md` §5 item 0.5 and §14 item 10 — "Works council / employee reps consulted — **required before shared `Sales`/`Parts` mailboxes enter scope**" | **must answer** |
| B4-gov | DPO for ISZE, or via IML legal | "P0 governance is 2 weeks or 8" | Still open: `00_docs/roadmaps/ai_sales_intelligence.md` §18 B4 — "DPO for ISZE, or via IML legal? … Owner: You … Status: Open" | **must answer** |

---

## Summary of the proposal

| Proposed outcome | Count | Items |
|---|---:|---|
| record as decided | 2 | §1 item 14 (workspace cleanup — applied to the roadmap 2026-09-16, label only); §2 B8 (base +3% revision stays as-is, no allocation without an explicit ask — **needs Jerome's line in `DECISIONS.md` first**) |
| kill candidate | 1 | §1 item 11 (Supabase live KPIs) |
| delegate candidate | 8 | §1 items 4, 5, 6, 7, 8, 9, 12, 13 - and §2 B9 is the same item as §1 item 6 |
| must answer | 11 distinct | §1 item 1 = §2 B5 · §1 item 2 · §1 item 3 = §2 B6/D6 · §1 item 10 = §2 B1b · §2 B1 · §2 B2 · §2 B3 · §2 B4 · §2 B7/D4 · §2 B10 · §2 B1c · §2 B4-gov |

Only two items in the whole list can be closed on paper today — and one of those still needs one signed line. That
is the finding: the list is not long because the analysis is missing, it is long because most of it has never been
through the three-place rule.

## Drift check on this month

`04_tools/workspace/check_decision_drift.ps1` compares §2 against `DECISIONS.md` entries dated after the
roadmap's own "Last updated" line (2026-09-16 at the time of writing). Run on 2026-09-16 it reports **no
drift**: the newest `DECISIONS.md` entry is dated 2026-08-25, so there is nothing newer to compare against.
The check will fire the first time a decision is logged after the roadmap's last update and the §2 row is left
untouched — which is exactly the situation the price adjustment ambition was in.

---

## Answers needed this week

One line each. Twelve answers, of which the first needs a signed memo rather than a one-liner.

1. **the price adjustment ambition** — **CLOSED PERMANENTLY on 2026-09-22** (it was still open on 2026-09-16; Jerome closed it on 2026-09-22 and asked never to be asked again). Do not re-open, and do not ask whether to go +4%, +5% or open on launch families only. The +5% flat simulation of 2026-09-22 is its last output: `00_docs/PRICE_AMBITION_CLOSED_2026-09-22.md`
   `Answer: ________________________________________`
2. Seed euro for the 9,591 PNs with no last-12-month sales: IML bill of materials, or UTI list placeholders?
   `Answer: ________________________________________`
3. Keep the provisional growth factors (1.24 filters, 1.25 first-failure) as they stand, or change them?
   `Answer: ________________________________________`
4. Adopt the guardrail rule - auto-HOLD on an IAM undercut and on an adverse proxy - or keep every exception manual?
   `Answer: ________________________________________`
5. Approve the draft account-health amber/red thresholds as they stand, or change them?
   `Answer: ________________________________________`
6. Sign G1 on the 98.2% price-list coverage now, or wait for the year-matched joins, the verify rule and EPC validation?
   `Answer: ________________________________________`
7. Who may change a forecast, and does every change need a written reason?
   `Answer: ________________________________________`
8. Correct the competitor vintages in the shared packs and rebuild, or keep those files internal only?
   `Answer: ________________________________________`
9. Name the approved route for company text, or shelve P2b / P3 / P6?
   `Answer: ________________________________________`
10. Pursue the shared Sales and Parts mailboxes with the works-council step, or stay on your own mailbox?
    `Answer: ________________________________________`
11. DPO for ISZE directly, or through IML legal?
    `Answer: ________________________________________`
12. Sign the year-matched list-to-pocket joins, so leakage euros can leave internal mode, or keep them internal?
    `Answer: ________________________________________`

---

**Footnote.** Two source filenames quoted above contain the pricing-track nickname the house labels do not use
in prose: `01_data/01_Pricing/BOOK_B_CONCLUSIONS_20260819.md` (the pricing review conclusions) and
`01_data/00_derived/revision_book_b_top_review.csv` (the review list). In every other line above that work is
called **the price list** / **a price adjustment**. Everything else is cited by its own path.

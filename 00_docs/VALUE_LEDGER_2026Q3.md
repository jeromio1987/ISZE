# Value ledger — 2026 Q3

**Prepared:** 2026-09-16 · **Audience:** manager and the next performance conversation. Not a working document.
**Rule for this page:** a euro appears only where a written, signed outcome exists in the workspace. Everything else is listed with a blank euro cell and the status `claimed, unsigned`. No figure on this page was invented, estimated or rounded up, and every cell carries a path.

---

| Item | Euro signed | Euro recovered | Hours freed | Evidence path | Status |
|------|------------:|---------------:|------------:|---------------|--------|
| UMI/Shell lubricants channel, FY2025 close-out — revenue, gross profit and net contribution after the distributor support payment | | | | `ISZE/05_memory/briefs/Lubricants_Closeout_FY2025_2026-05.md` · `ISZE/FACTS.md` §6 | `claimed, unsigned` — IML governance sign-off 8 May 2026 recorded; the euro rests on Jerome's own e-mails (revenue ~€442K, ~€57K gross profit, ~€20K support, ~€37K net) and none of it is a signed commercial document. `FACTS.md` §6 flags the whole section as not traced to a verified source file |
| Price-revision allocation — the unsigned ambition decision (+4% / +5% / launch-only) on 6,326 part numbers | | | | `ISZE/00_docs/ISZE_ROADMAP.md` §2 ref B1 · `ISZE/01_data/00_derived/revision_book_b_pack.meta.json` · `ISZE/01_data/01_Pricing/BOOK_B_CONCLUSIONS_20260819.md` | `claimed, unsigned` — built 2026-08-19, no allocation run, growth factors 1.24 / 1.25 themselves unsigned (`ISZE/00_docs/ISZE_ROADMAP.md` §2 ref B3). The modelled €383K–€726K per year on three ambition settings is an ask, not a signed number |
| Distributor replenishment leakage, CY2025 exceptions | | | | `ISZE/01_data/00_derived/replenishment_exceptions_cy2025.csv` · `ISZE/DECISIONS.md` 2026-08-25 | `claimed, unsigned` — leakage euro is Mode B only until the year-matched list-to-pocket joins are signed in writing. The €4.17M exceptions and €2.68M visible leakage are source-cell stakes, not recovery |
| Parts billed with no usable list price — coverage gap | | | | `ISZE/01_data/00_derived/no_pr00_gap_cy2025_ranked.meta.json` · `ISZE/00_docs/ISZE_ROADMAP.md` §4 (2026-08-11) | `claimed, unsigned` — a coverage measure, not a recovery claim: 251 part numbers / €4,955,737 in CY2025 closed to 31 / €591,916 by the August 2026 list pull. No signing is required for the measure; no euro may be called recovered from it |
| ITUK brake sales-promotion proposal (customer, received 2026-09-15) | | | | `ISZE/01_data/90_INBOX/_ituk_brake_spa_20260915/REVIEW_ITUK_Brake_SPA_20260915.md` | `claimed, unsigned` — the customer's volume figures reconcile exactly to our own per-dealer files and the diagnostic stands; the payment mechanism as designed would pay on 203 units worth €4,826 of gross profit. Internal recommendation is to reject the mechanism, so this is a declined claim, not value created |
| Tender R&M conversion on the live opportunity feed | | | | `ISZE/00_docs/REVIEW_EXEC_AFTERSALES_PAPER_20260915.md` §3.8 | `claimed, unsigned` — €55,786 per year addressable and €44,692 per year modelled uplift, both modelled from the live feed and not committed by anyone. The same review concludes the channel is a relationship play, not a parts-revenue play |
| Reporting and refresh effort removed by the live automations and pipelines | | | | `ISZE/00_docs/AUTOMATION_REGISTER.md` · `ISZE/00_docs/roadmaps/ai_sales_intelligence.md` §8.5 | `claimed, unsigned` — the hours column stays **blank**. The register shows the jobs that run (ten active skills, five live scheduled tasks, the derived pipeline and the action ledger) but no time measurement exists. The mail-and-action ROI model states plainly: "Do not populate this with illustrative numbers in any shared document" |
| Mail-scope governance for the local interaction layer | | | | `ISZE/00_docs/P2A_SESSION_MANIFEST.md` · `ISZE/DECISIONS.md` 2026-08-12 | Signed 2026-08-12 — own mailbox only, 24-month retention, no bodies stored. Enables the interaction layer. Carries no euro by design |
| Tender API key administration for the Nordic markets | | | | `ISZE/DECISIONS.md` 2026-08-25 · `ISZE/00_docs/AUTOMATION_REGISTER.md` | Signed off as done 2026-08-25 after repeated re-asks. Removes a recurring interruption; no euro attachable |
| Quarterly supply-versus-target measurement infrastructure | | | | `ISZE/01_data/00_derived/_verification_report.json` · `ISZE/01_data/00_derived/action_ledger.meta.json` · `ISZE/00_docs/AUTOMATION_REGISTER.md` §P8 | Pipeline green 116 pass / 0 fail (2026-08-25), billing through 2026-06-30; the action ledger carries 23,236 open items with a decision file that is still header-only, so it measures nothing yet |

**Rows deliberately left blank on the euro columns:** every row above. There is no signed euro outcome anywhere in this workspace as of 2026-09-16. That is the honest state of the page, and it is also the point of it: the amount of work waiting on a signature is large and the amount signed is zero.

---

## Figures that must not be added

These are all live, all correct in their own place, and all computed on different bases. Adding any two of them produces a number that means nothing:

| Figure | Basis | Source |
|--------|-------|--------|
| €22,110,563.54 of open opportunities | Summed source cells, explicitly mixed basis — the review states these source cells must not be read as a single pool | `ISZE/01_data/00_derived/ACTION_LEDGER_REVIEW_20260825.md` |
| €29,460,798 residual to a modelled ceiling | Ceiling minus billed; inherits a ceiling that is 37.3% placeholder | `ISZE/01_data/00_derived/wallet_waterfall.csv` (file name quoted once) |
| €18,216,555 component gap | Fourteen modelled categories, expected demand × observed price | `ISZE/01_data/00_derived/pms_opportunity_matrix.csv` |
| €12.76M / €14.52M price-revision base | Last-twelve-month billed base versus forecast-weighted base; a base, not a gain | `ISZE/01_data/00_derived/revision_book_b_pack.meta.json` |
| €4,955,737 no-list coverage gap | CY2025 billed value with no usable list price; a coverage measure | `ISZE/01_data/00_derived/no_pr00_gap_cy2025_ranked.meta.json` |
| €4,171,000 replenishment exceptions / €2.68M visible leakage | CY2025 exception rows; five distributors; leakage euro not quotable in writing | `ISZE/01_data/00_derived/replenishment_exceptions_cy2025.csv` · `ISZE/DECISIONS.md` 2026-08-25 |
| €4,826 gross profit on the ITUK brake proposal | Modelled at the payable increment, in euro after a flagged £/€ conversion, on a mechanism recommended for rejection | `ISZE/01_data/90_INBOX/_ituk_brake_spa_20260915/REVIEW_ITUK_Brake_SPA_20260915.md` |

Never sum across this table, and never present one of these rows as a saving. Each is a modelled or covered amount; none is a recovery.

## Where sources disagree — flagged, not resolved

`ISZE/FACTS.md` wins over every other file. Three points where the other files have moved and `FACTS.md` has not:

1. **Parts base.** `FACTS.md` §4 states a parts base of **€112.09M** billed through **2026-06-30**, as of 2026-08-25. The roadmap's shipped list records a further change on 2026-08-11 (a list-price pull closing part of the no-list gap, quoted as coverage rising to 98.2%). `FACTS.md` has not been updated with that. Until it is, quote €112.09M and treat the 98.2% figure as a list-coverage change, not a revenue restatement.
2. **Ceiling and cover.** The published 2025 cover is **51.1%** on a **€60,217,570** ceiling, which agrees with the `FACTS.md` change log of 2026-07-02. The alternatives (43.6% / 40.6% / 29.4% under different placeholder assumptions, and the 45.8% variant obtained when treating the flat-rate markets as the reviewed nine rather than the eight that are exactly at the placeholder) are **sensitivities on an assumption**, not corrections. Print them as a band under the published number; never replace it silently.
3. **Lubricants revenue.** The close-out note itself records ~€442K revenue against ~€582K gross in the system, attributed to net-versus-gross treatment, and `FACTS.md` §6 flags the section as unverified. Do not put either figure on this page until a source file is attached to it.

One further point of counting, not of disagreement: the visible-share candidate in the companion shortlist reads **54.4%** on the market basis used in the executive paper and **60.0%** once Portugal's file is included, which it now is. Same data, two moments. State the date.

---

## How to refresh this ledger each quarter

In this order, and do not skip step 2:

1. Run the pipeline and confirm the verification report has **0 fail** (`ISZE/03_analytics/Isuzu/prism/scripts/run_pipeline_and_verify.ps1` → `ISZE/01_data/00_derived/_verification_report.json`). If it is not green, stop — the ledger is not refreshed.
2. Read `ISZE/FACTS.md` head: the last-verified date, the parts base, and the change log. This file overrides everything else on this page. If it disagrees with any row, the row changes or gets flagged, never the other way round.
3. Read the newest entries of `ISZE/DECISIONS.md` for new sign-offs, new refusals and any euro that has moved from internal to signed.
4. Read `ISZE/01_data/00_derived/action_ledger.meta.json` for the billing horizon and the open-item counts, and note whether the decision file is still header-only.
5. Re-read the pricing pack meta, the no-list meta and the replenishment exception file for their own as-of stamps; these three drift at different speeds.
6. Sweep `ISZE/09_meetings/_MAIL_MINUTES_*/` and `ISZE/01_data/90_INBOX/` for anything a customer or IML actually confirmed in writing. This is where a row moves from `claimed, unsigned` to signed, and it is the step that gets skipped.
7. Move any newly signed row to the top, print the euro in the signed column, and cite the document that carries the signature — not a chat, not a deck, not this ledger.
8. Write a new file per quarter. Never overwrite a past quarter's ledger.

**The rule that does not bend:** in any version of this page that leaves your own machine, an item without a signed written outcome keeps a blank euro cell. A euro printed against an unsigned item is the fastest way to lose the argument this ledger exists to win.

---

*Footnote — file name quoted once as permitted because it contains a word this document does not otherwise use: `ISZE/01_data/00_derived/wallet_waterfall.csv`. Nine other sources are cited in full above; none of them was altered, and nothing under `ISZE/07_deploy/` was touched.*

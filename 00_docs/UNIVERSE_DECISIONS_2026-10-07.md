# Universe decisions locked 7 Oct 2026

From the approved U1–U26 assessment plan. Internal.

| # | Decision | Locked as | Evidence |
|---|---|---|---|
| 1 | Merge PR 70 (U28 stack) | **YES — MERGED** | https://github.com/jeromio1987/ISZE/pull/70 · merge `66a746a4` · 2026-10-07T11:20:42Z |
| 2 | Delivery / tax basis (U29-B) | **Verified; eligible still 0** | Field + mutation proven. PR 71 retargeted to `main` → now **MERGEABLE** but **631 files / ~635k lines** (U26 scrape cache). Do **not** smash-merge; follow code-only path in `UNIVERSE_PR71_FIX_LIST_2026-10-07.md`. Detail: `UNIVERSE_U29B_LEDGER_VERIFY_2026-10-07.md` |
| 3 | Portugal competitor scrape | **UK first; Portugal insufficient for now** | Two host sweeps; no usable PT shop pages; bar 50 rows, PT ~27. No third automated sweep. Hand collection only if you later ask |
| 4 | First real INTERNAL feeds | **Tender + PRISM + IDS (ITUK + Portugal I-Motors)** | PR 72 MERGED `41cddad1` (tender + PRISM). PR **77** MERGED `7d2c1630` — real IDS answers for Ferndown (ITUK) and Astara Lisboa (Portugal). Stock still optional later — needs a real stock observation file, not billed-vs-sales-to-dealer |
| 5 | ACCEPT-04 / 05 participants | **PARKED until finished bar** | Roster kept blank on purpose. Scripts on PR 73. See afternoon section below |
| 6 | Universe board scores | **Re-graded 7 Oct afternoon** | Sample restored: groundwork **48%** (29/60); AIM **60%** (6/10); accuracy condition 1 (47/50 L1). Note: `UNIVERSE_ACCURACY_SAMPLE_2026-10-07.md`. Launcher `OPEN_ISZE_UNIVERSE_BOARD.cmd`. |

## Landed after the assessment pack (7 Oct, small pieces)

- PR **73** MERGED (`3b28c340`) — acceptance scripts on main.
- PR **74** MERGED (`3af2f752`) — IT sign-in draft + module audit + roadmap cut proposal.
- PR **75** MERGED (`0a9d5b2d`) — delivery-basis schema/parsers only.
- PR **76** MERGED (`545f1a02`) — coverage CSVs; eligible still 0.
- PR **71** CLOSED (superseded by 75/76; fat scrape cache stayed out of main).
- PR **77** MERGED (`7d2c1630`) — real IDS for ITUK (Ferndown) + Portugal I-Motors (Astara Lisboa) on INTERNAL.

## Still open (your call)

- Hand a **real stock observation** file if you want CONNECT-06 filled on INTERNAL later (not inventable from billing). Not required for v1 finished.
- Accuracy sample **restored** (see decision #6) — finished bar piece met; verdicts are 24 Sep restore, not a fresh 7 Oct re-read.
- Market path: **met via Eucon-only + empty-scrape disclosure** (`UNIVERSE_MARKET_EUCON_EMPTY_SCRAPE_DISCLOSURE_2026-10-07.md`). UK hand-collect sheet ready for optional scrape euros later (`01_data/90_INBOX/UNIVERSE_UK_DELIVERY_TAX_HAND_COLLECT_20261007.csv`).

## Finished bar + ACCEPT parked (7 Oct afternoon)

Jerome will **not** review ACCEPT now. ACCEPT-04..08 are **parked** until the product meets the finished bar. Participant names do **not** block engineering.

**Finished bar (one page):** `UNIVERSE_FINISHED_BAR_2026-10-07.md`

| Topic | Locked this afternoon |
|---|---|
| What finished means | Real tender + PRISM + IDS (Ferndown ITUK + Astara Lisboa PT) already on INTERNAL; market = UK competitor euros **or** Eucon-only + empty-scrape disclosure; accuracy sample present and scored on the board |
| Stock | **Out** of v1 finished — see `UNIVERSE_STOCK_OUT_OF_SCOPE_2026-10-07.md` |
| Portugal competitor scrape | Not required for finished |
| ACCEPT-04..08 | Parked — people tests only after finished. Roster: `UNIVERSE_ACCEPT_PARTICIPANT_ROSTER_2026-10-07.md` |


## Finished bar status (7 Oct afternoon review)

| Piece | Status |
|---|---|
| Real feeds (tender + PRISM + IDS) | Met (PR 72 + 77) |
| Market | Met — Eucon-only + empty-scrape disclosure |
| Accuracy sample | Met — restored 24 Sep sample; board 47/50 L1 |
| Stock | Out of scope (parked) |
| ACCEPT-04..08 | Parked |

**INTERNAL finished bar: MET.** People tests only if/when Jerome asks.


## UK scrape wall (7 Oct evening)

- Eligible shop offers: **4** (PNs 8982705240, 8975546610).
- **54** KS category_only rows cannot be upgraded: cards say Isuzu PN not on them; no on-disk OE crosswalk (UNIVERSE_UK_OE_CROSSWALK_RESULT_2026-10-07.md).
- TMC: no under-£150 delivery £; VAT included without stated %.
- Growing past 4 needs new matched scrape sources or hand OE confirmation — not inventing on these 54.
- **22** pack-unknown rows: KS pages say pad set/filter kit only — no piece count (UNIVERSE_UK_PACK_HUNT_RESULT_2026-10-07.md).
- INTERNAL: cases ITUK-OIL-ELIG / ITUK-PAD-ELIG paint the 4 eligible KS offers (UNIVERSE_INTERNAL_ELIGIBLE_WIRE_2026-10-07.md). Open Isuzu Universe\05_AIM_Universe\OPEN_AIM_INTERNAL.cmd.
- Wider UK exact-OEM scan: **17** offers / **12** PNs vs focus **4** / 2 PNs (`UNIVERSE_UK_WIDER_ELIGIBLE_SCAN_2026-10-07.md`). Board shows both.
- INTERNAL now has **12** UK eligible PN case hooks / **17** shop offers painted (UNIVERSE_INTERNAL_ELIGIBLE_WIRE_2026-10-07.md).
- Next harvest plan ready; **8-PN KS OE-on-card pilot running** (UNIVERSE_UK_NEXT_HARVEST_2026-10-07.md, worklist in 90_INBOX).
- KS 8-PN Isuzu-PN search pilot: **0/8** (no results). Do not widen that query. Pivot to competitor-SKU search (UNIVERSE_UK_KS_PILOT_8PN_RESULT_2026-10-07.md).
- Competitor-SKU KS pivot: **0** accepted (30 empty / 2 wrong card). Eligible stays 17/12 (UNIVERSE_UK_KS_SKU_PILOT_RESULT_2026-10-07.md).
- KS £10 policy scope (live page): filter/clutch/exhaust only → wired 8983682091 PIPE; EXH. Wider **18**/13. Do not wire body/rotor/springs at £10.
- Omega UK Free Economy £0 (Store API cart) + VAT incl 20% (TOB) is an honest delivery wire for omegaspareparts exact_oem. TMC under-£150 still not inventable (504 / checkout-only).
- KS: search grid may omit Isuzu PN; PDP attribute **OE Equivalent Part Number** is valid exact_oem evidence when it prints the linked Isuzu number. Do not invent OE; only upgrade when that attribute (or clear OE field) shows it.
- KS PDP OE pass3: clutch/exhaust/filter SKUs also print OE Equivalent Part Number; £10 only when family matches live KS mainland classes (filter/clutch/exhaust). Non-class OE hits stay without £10.

# Universe U1–U26 — deep status assessment (7 Oct 2026)

Audience: Jerome. Internal. Assessment landed from the approved plan; scores and paths measured on disk / GitHub the same day.

**Verdict:** The pricing tool’s screens and wiring are largely proven on test data (90/96 on the U28 branch, now on `main` via PR 70); the commercial hole is still competitor prices on real UK/Portugal data (0 eligible offers); IDS has real Oct pilot pages the Sep board does not see; General surfaces and the Universe board content are still last month’s picture unless you open this file or the map.

---

## Three clocks — do not blend

| Clock | What it tells you | Danger if quoted alone |
|---|---|---|
| **U briefs** (`C:\Users\jerom\Desktop\claude\docs\cursor_briefs\`) | What waves ran 5–7 Oct | Not inside the ISZE search path |
| **Main `progress.json`** (after PR 70) | Should match the U28 record (~90 TV / ACCEPT-04..08 open) | Was 59/37 before the merge |
| **Board JSON content** (`built_at` body still Sep 24 scores) | “0 of 5 tools a distributor can open” | Ignores pilots, UK CV refresh, AIM v04 — **marked STALE** on 7 Oct |

Also: **P1–R8 ≠ U1–U8**. P/R are ITUK dealer folders from U1/U2 only. See `00_docs/agent/INCIDENT_UNIVERSE_U1_U8_MISS_2026-10-06.md`.

`Isuzu Universe/**` is cursorignored — status must use Shell / named paths, not workspace Grep.

**Locked decisions for the six follow-ups:** `00_docs/UNIVERSE_DECISIONS_2026-10-07.md`.

---

## 1. U1–U26 scoreboard

All briefs exist for U1–U26; U27–U29 also exist. Reports missing in `cursor_briefs` for **U25** and **U26** (U26 report: `_worktrees\ISZE_u26\01_data\91_build\_u26_E_REPORT.md`).

### Block A — Pilot pages

| Wave | What | Outcome |
|---|---|---|
| **U1** | ITUK Parts 2025 (8 dealers) | PARTLY — `07_Pilot_ITUK\pages\P1–R8`; 2 tooltip gaps |
| **U2** | Same dealers, Dealer Standards 2026 | LANDED |
| **U14** | Portugal Dealer Standards PT1–PT3 | PR #53 → `08_Pilot_Portugal` |

### Block B — AIM pricing tool (TASKS_96)

| Waves | Slice | Outcome |
|---|---|---|
| **U3–U5** | DATA/UX/CASE | LANDED |
| **U6–U7** | UX-03/04/07/08 + narrow shell | Landed |
| **U8–U9** | REVIEW | Merged |
| **U10–U12** | RANGE, ACCEPT gaps, C18 | Merged |
| **U13 + U15** | MARKET evidence | Logic/tests; **usable offers still empty** |
| **U16** | Independent verification | Merged |
| **U17–U18** | CONNECT-01..04 | Merged |
| **U19a/b** | RUN-01 + gap coverage | Coverage written; scrape not in U19b |
| **U20–U24** | CONNECT UI, SAFE, RUN, RANGE-07, ACCEPT-02 | On U28 stack → **merged to main as PR 70** on 7 Oct |

### Block C — Scrape × cross-reference

| Wave | What | Outcome |
|---|---|---|
| **U25** | ITUK+PT scrape | Superseded by U26; no report |
| **U26** | MEGA harvest + Spareto/Eucon grading | Worktree; ledger 6,597→6,690; UK focus 38→79; **eligible 0 / 0** |

**Why 0 eligible is not “scrape failed”:** every focus row dies on `DELIVERY_BASIS_NOT_STATED` until a page states delivery. U29-B added the ledger fields and proved the flip with a mutation; real UK focus pages still do not state a basis (4 Tranzparts rows state one, then drop as retired loader). Eligible stays **0**. See `00_docs/UNIVERSE_U29B_LEDGER_VERIFY_2026-10-07.md`.

This track is scrape × Eucon/open cross-ref for AIM pricing — **not** scrape × IDS.

### Beyond U26

| Wave | State |
|---|---|
| **U27** | Audit fixes on branch; incomplete report |
| **U28** | **PR 70 MERGED** 2026-10-07 (`66a746a4`) |
| **U29-A** | Same as PR 70 open-for-review → merged |
| **U29-B** | Piece A/B on main (PR 75/76); PR 71 closed; eligible still **0** |
| **U29-C** | **PR 72 MERGED** 2026-10-07 (`41cddad1`) — real tender + PRISM in INTERNAL |
| **U29-D/E/F** | PRs 73–74 MERGED; IDS real feed PR **77** MERGED |

---

## 2. General

| Surface | Vintage | Status |
|---|---|---|
| Universe 3.0 / INDEX planning block | 23 Sep | Planning edition |
| Universe **board** scores | 7 Oct rebuild | Live scores; groundwork 43% (26/60); accuracy sample still missing |
| Universe **map** | Rebuilt 7 Oct | Live; task list from progress |
| Action Centre / Opportunity / Atlases | Sep | Internal / snapshot; no Parts Universe v2.1 product |

---

## 3. UX

UX-01..08 technically verified. Narrow shell tested. Human ACCEPT-04..08 not run. Open: `Isuzu Universe\05_AIM_Universe\dist\OPEN_AIM_Pricing_Decisions_v04.cmd`. Tour: `docs\cursor_briefs\2026-10-07_UNIVERSE_GUIDED_TOUR.md` (synthetic + tender, PRISM, and IDS feeds in INTERNAL after PRs 72 and 77).

---

## 4. AIM

| Layer | After PR 70 on main |
|---|---|
| BASE / DATA / FIN / CASE / REVIEW / UX / MARKET / RANGE / SAFE / CONNECT / RUN | Technically verified (BASE-01 implemented) |
| ACCEPT-04..08 | Not started (need people) |
| MARKET-DATA-GAP | Still high — eligible competitor offers **0** |
| Distributor-open tool | Still no |

---

## 5. IDS

**Live Oct:** ITUK P1–R8 Parts + Standards; Portugal PT1–PT3 Standards; UK CV compare 6 Oct (44 dealers); CONNECT-01 identity gate; INTERNAL reads real IDS for Ferndown + Astara Lisboa (PR 77).

**Empty / stale:** milestone store `dealers_count=0`; Development Progress receipt 24 Sep; Studio not a shipped product. Scrape does not feed IDS.

---

## 6. Scrape × cross-reference

Worklist 680 rows / 123 OE. Eucon approved; no further Eucon ask. Spareto graded edges up. UK row coverage improved; Portugal hosts unusable. Delivery-basis schema on main via PR 75; coverage via PR 76. Eligible remains 0 until pages state delivery (do not invent).

---

## 7. Maturity by pillar

| Pillar | Engineering | Shared / distributor-ready | Biggest hole |
|---|---|---|---|
| General | Map live; board marked stale | No | Single current status = this file + map |
| UX | UX-01..08 TV | Internal only | Real participants |
| AIM | ~90/96 on main; v04 openable; tender + PRISM + IDS | No | Eligible prices = 0; ACCEPT people |
| IDS | Pilots + UK CV | Pilot pages yes | Empty milestone store |
| Scrape/xref | Harvest + grading ran | N/A | Pages silent on delivery; PT hosts |

---

## 8. Evidence anchors

- Briefs: `C:\Users\jerom\Desktop\claude\docs\cursor_briefs\`
- U26 report: `C:\Users\jerom\Desktop\claude\_worktrees\ISZE_u26\01_data\91_build\_u26_E_REPORT.md`
- Decisions: `C:\Users\jerom\Desktop\claude\ISZE\00_docs\UNIVERSE_DECISIONS_2026-10-07.md`
- Board: `C:\Users\jerom\Desktop\claude\ISZE\02_dashboards\hub\OPEN_ISZE_UNIVERSE_BOARD.cmd`
- PR 70: https://github.com/jeromio1987/ISZE/pull/70
- PR 72: https://github.com/jeromio1987/ISZE/pull/72

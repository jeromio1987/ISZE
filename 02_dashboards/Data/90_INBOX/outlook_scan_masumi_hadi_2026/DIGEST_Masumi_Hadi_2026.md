# Outlook scan — Masumi + Hadi (CY2026)

**Mode B · Jerome-only** · Scanned via local Outlook COM (Composio still unauthenticated).  
**Mailbox:** `jerome.van.der.pluym@isuzu-e.com` · Inbox + Sent + Archive  
**Scanned at:** 2026-08-09 11:08  
**Raw:** `hits.json` / `index.json` / `_analysis.json` in this folder

## Volume

| Lens | Count |
|------|------:|
| Hits involving Masumi or Hadi | 3,321 |
| **From Masumi** | **190** |
| **From Hadi** | **296** |
| Involving Masumi (from/to/cc) | 1,307 |
| Involving Hadi (from/to/cc) | 2,943 |

From-them by month is steady (~54–76/mo Jan–Jul; Aug partial ~33).

Theme tags on **mail from them** (subject+preview+attachments): Meeting 189 · Incentive 55 · Tender 40 · Lubricants 39 · UIO 37 · GPS 36 · PMS 32 · IDS 22.

---

## What matters now (lanes)

### Hadi’s own priority list (7 Aug — Action plan update July)

While on leave she asked the team to finish the action plan and focus on **MH requests**:

1. Genuine parts share (GPS)
2. PMS — ITUK, Portugal, Ireland (CV parts focus)
3. Lubricant project
4. KPI criteria — distributors’ parts sales target to network + fill rate
5. IDS result analysis + Kaizen proposals

That is the operating agenda. Everything below hangs off it.

### GPS

- **GPS // Sales to dealer way** (Jul): Masumi wants **DB sales targets toward dealers**, not only ISZE→DB. WIP OK; KPI 12-month file as base.
- **GPS and the target** (3 Jul): framework OK; **all DBs in list**; **equal stretch** (1% share like ITUK/Duncan).
- **KPI_targets.xlsx** (Jul): she chased with no feedback → sit-down.
- Price ladder already known from prior digest: FY27 +5%, FY28–31 +3%/yr; DB meetings → agreement **end August**.
- Portugal GPS ↔ UIO refresh asked 14 Jul (`Matriculas Isuzu SAP.xlsx`).

**Automation hypothesis:** treat GPS/KPI as a **state machine** (request → WIP file → stretch calc → DB meeting booked → agreed), fed by Masumi subject patterns + attachment names (`KPI_targets`, `GPS`, waterfall). Weekly open-loop skill should surface “stuck >N days without reply to Masumi”.

### PMS

- **IML/ITUK PMS Meeting Aug 2026** still live; Hadi on holiday same window — coverage risk.
- Masumi 7 Aug: **ITUK centralised purchasing** joint pack for Pete approval (pages 1–6 ISZE, 7–31 joint).
- Long thread history: IML PMS item promotion (Mar), conference parts slots, 3-party / Suzuki.

**Automation hypothesis:** calendar + mail watch for `PMS` + `ITUK` + `IML` → one **visit/agenda conflict board** (PMS day vs lubricants/GSCM/Ikeda CP) so PMS doesn’t get squeezed silently.

### UIO

- Recurring Masumi asks: Ireland UIO recombine (May), UTI MTBP volumes (Jun), Portugal UIO update for GPS (Jul), waterfall UIO factors (Jun IX study).
- Pattern: **Office / DB sends numbers in mail → Jerome must land them in `06_uio/_CURRENT`**. Today that is manual and easy to miss.

**Automation hypothesis:** when Masumi/Hadi mail has UIO-ish attachments (`UIO`, `保有台数`, `Matriculas`, volume tables), auto-drop a **staging note + file copy** into `01_data/90_INBOX/uio_from_mail/` and flag `isze-uio-staleness` / open loops. Do **not** auto-write `_CURRENT` formulas without Jerome OK.

### Tender / SPA / fleet

- **Poland PGE 173 units steel wheels** (Jul fw via Masumi/Hirai) — SPA path with IMIT; bid ~19 Aug.
- SPA waterfall discipline (Masumi 30 Jun): save-as with **YYYYMMDD** in filename under network BP folder.
- Autowallis Teams 11 Aug (Hadi booked Jerome).
- Georgia new dealer aftersales (ongoing Hadi/Masumi/IMIT).
- Incentive MOU question (4 Jun): how DBs use support money / anti front-load — strategic, not one-off.

**Automation hypothesis:** tender monitor already scrapes public tenders; **mail-side** needs a parallel watch for **SPA + fleet bid** subjects (Poland/PGE/SPA/waterfall) → risk cockpit / open loops. Naming convention check for waterfall files is a cheap hygiene job.

### IDS / Kaizen (adjacent, MH-driven)

- Prep IDS Feedback Mtg to DBs (Jul): overall + per-DB + Kaizen + schedule + target/result dates.
- PIC allocation draft to Tomoe (6 Aug) with `EU IDS Dealer Summary 20260724.xlsx`.
- Already partly covered by IDS tooling — mail should **trigger** pack refresh reminders, not replace ranking logic.

---

## Automation map (proposal — not built)

| Signal | Detect | Action (after your OK) |
|--------|--------|------------------------|
| From Masumi/Hadi | nightly COM or Composio | Tag GPS/PMS/UIO/Tender/IDS/Lubes; append to weekly open loops |
| GPS/KPI chase | subject + “no feedback” / meeting ask | Surface as P0 if >5 business days stale |
| UIO numbers in mail | attachment/keywords | Stage to INBOX only; never silent `_CURRENT` write |
| SPA / fleet bid | SPA, PGE, steel wheel, waterfall | Link to tender/risk view; deadline extract |
| PMS visit threads | IML/ITUK/PMS + dates | Agenda conflict digest before Japan week |
| Hadi “action plan” lists | bullet MH requests | Diff against last list → change log of priorities |

**Hard rules stay:** draft-only mail; no send; no silent version bumps; rebuild/ship only on explicit ask.

---

## Files

| File | Role |
|------|------|
| `_summary.json` | Counts |
| `index.json` | Light subject index |
| `hits.json` | Full records + body previews (large) |
| `_analysis.json` | Theme tags + lane threads |
| `_scan.py` | Re-runnable local scanner |

## Limits

- Composio Outlook **not** connected (auth did not complete) — used desktop Outlook.
- Archive barely contributed (1 from Hadi); most volume is Inbox.
- Involve-pass capped (~12k Inbox / ~6k Sent recent) — From-them Restrict is complete for Inbox SenderName match.
- Teams/chat “Hadewijch sent a message” noise counted in subjects.

Ready for your next instruction (deeper on one lane, automation skill draft, or add other people).

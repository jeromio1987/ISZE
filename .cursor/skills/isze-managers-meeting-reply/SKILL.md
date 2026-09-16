---
name: isze-managers-meeting-reply
description: >-
  Draft Jerome’s management/Japan replies in Dirk→Yoshimoto style: answer Dirk/YN
  question structure from Outlook + monthly sales xlsx + Margin/Rev BP + Power BI +
  MoMs, Masumi Sent voice, fact-gated. Use when Jerome asks for managers meeting
  reply, Dirk Yoshimoto reply way, Yoshimoto san draft, Japan management answer,
  or Aug recoverable / Sept-BP / lubricants-CP style replies.
---

# ISZE managers meeting reply (Dirk → Yoshimoto)

Jerome’s working way for answering Dirk / YN so he can forward to Yoshimoto san.
**Draft only — never Send.** Not an always-on rule; invoke by name or trigger phrases above.

## 1. Start from their questions

Answer **Dirk / YN structure**, not an agent taxonomy. Typical buckets:

- August recoverable / month result
- September vs BP (budget plan)
- Lubricants / centralised purchasing (CP)

Do not invent new section labels they did not ask for.

## 2. Tools (use the same stack Jerome uses)

Pull facts from these before drafting. Prefer live sources over memory.

| Source | How |
|--------|-----|
| Outlook | Agent browser only when Jerome has mailbox open: Aaron/John end-of-month results, Purchase situation, Shell/Faiza, daily sales from Peter |
| Daily / monthly sales xlsx | e.g. `01_data/90_INBOX/ISZE_MONTHLY_SALES_REPORT_09.2026.xlsx` (use the current month file in INBOX) |
| Margin / Rev BP | `01_data/Margin analysis report August.xlsx` (or current month’s Margin analysis / Rev BP 3+9) |
| Power BI | `SALES DATA VP NEW` / ISZE MONTHLY REPORT VP — only when he opens it in agent browser or provides screenshots |
| MoMs | On disk under `09_meetings/` + mailbox: Jul 14 CP, Aug 19 ITUK lubricants (and later MoMs when present) |
| Extra as needed | SPA, UMI minutes, Shelly |

Do **not** invent numbers from chat history when these files/tabs exist.

## 3. Draft shape

```
Dear Yoshimoto san,   (or Hello Yoshimoto san,)

[1 short intro — why this mail / which questions]

1. [Topic from Dirk/YN]
   - denser Outlook-style bullets (complete thoughts, not micro-fragments)
2. …
3. …

Kind regards,
```

- Numbered topics matching **their** ask.
- Bullets = full sentences / complete thoughts (Masumi-class density when the brief is a full picture).
- Stop after `Kind regards,` — no signature.
- **Draft only.** Never Send (no API, no script, no “he said send earlier”).

## 4. Voice

Match Jerome’s Masumi Sent style:

- Rule: `~/.cursor/rules/jerome-email-human-voice.mdc`
- Corpus: `01_data/90_INBOX/_jerome_masumi_PRIMARY_bodies.txt`

Default short; **longer OK** when he asks for a full picture / managers pack. Still plain English — no AI glue (“Hope you’re well”, “Separately”, “Happy to help”), no markdown bold in the body, no em-dashes as pauses.

Japan: `Dear … san,` / `Hello … san,` is correct.

## 5. Fact gate (before calling a draft “final”)

| Gate | Rule |
|------|------|
| Order receipt vs BP | Order receipt ≠ “ahead of monthly BP”. Do not equate backlog/orders with revenue vs budget. |
| Dealer vs target | Say “vs target” only if a target exists in the source. |
| CP / MoM | Centralised purchasing claims must be **MoM-true**. ME/Africa only if labelled as future EMEA from decks — not as Jul/Aug MoM fact. |
| Shell % | From `gps_pure_sales` (or the live GPS pure-sales source), not a guessed mix. |
| Israel | UTI ≠ UMI — never blend. |
| Spoken labels | No **sell-out** / **wallet** / **street** / **Book B**. Prefer: sales to dealer, parts billed vs target spend, OEM peer retail / reference dealer price, price list / price revision. |

If a gate fails → say UNKNOWN / source gap in the draft (or ask Jerome), do not paper over.

## 6. Separate tracks

Keep distinct; do not merge into one story:

1. **Shell → UMI** (Israel distributor track)
2. **Europe CP study** (centralised purchasing / lubricants Europe)

## 7. Customer attachments (HARD — Shelly / UMI / distributors)

Customer-facing Outlook drafts attach **only** what the customer can open and will use.

| OK | Forbidden |
|----|-----------|
| Meeting presentation `.pptx` / `.pdf` (Mode A) | `.cmd`, `.md`, `.csv`, `.zip` |
| `.xlsx` **only if they asked** for a workbook | Agent scripts, internal packs, IDS zips, SPA working CSVs |

If they asked only for the presentation → attach **that one file**. Keep zip/csv/scripts in an `_aside_do_not_attach/` subfolder so they are not sitting next to the draft body.

Scar (2026-09-15): Shelly asked for the 12 Aug presentation only; first draft wrongly attached IDS zip + PN decline CSV.

## Checklist before handoff

- [ ] Structure mirrors Dirk/YN questions
- [ ] Numbers traced to Outlook / xlsx / Margin / PBI / MoM (named in Mode B chat if needed; clean in draft)
- [ ] Fact gate passed
- [ ] Shell/UMI vs Europe CP not blended
- [ ] Customer attach = Mode A pptx/pdf only (no zip/csv/cmd/md/scripts) unless they asked for a workbook
- [ ] Draft only in chat (or Outlook draft if he asked) — never Sent

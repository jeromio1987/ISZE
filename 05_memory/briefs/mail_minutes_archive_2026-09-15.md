# Mail minutes archive — Jul–Sep 2026

**Built:** 2026-09-15 · **Trigger:** Jerome asked to save all meeting minutes created by him, Bart or Koen in the
last 3 months and hold them in memory.

## Where it lives

- **Archive:** `09_meetings/_MAIL_MINUTES_2026-09-15/`
- **Index (read this first):** `09_meetings/_MAIL_MINUTES_2026-09-15/README_MAIL_MINUTES_INDEX.md`
- **Provenance:** `_extracted/` (eml originals + full packs), `_zips/` (raw Outlook "Download all" archives)

## What was found (search window 2026-06-15 → 2026-09-15)

19 files, 14 distinct minutes, across three authors:

| Author | Minutes docs | What |
|---|---|---|
| **Jerome** | 11 | 5 business-review MoMs (260812_UMI, 260805_ISD, 260806_Harris, 260806_Petros, 260806_IUK, all sent 2026-08-12); Astara WE business review; Wallis aftersales minutes + AS BRM pack; PMS parts-sales-promotion draft MoM (v1–v4); ITUK PMS minutes 2026-08-18; Astara Portugal |
| **Bart Van Den Bosch** | **0** | Only operational reports in the window (BO lines / Fill Rate, Depreciations trading goods, Purchase Plan 8+4, Backorder Report, VP overstock) — no minutes |
| **Koen Matheussen** | **0** | Only operational files (Daily Sales Report, RG23 recommended parts list, Training matrix, D-Max charge cooler) — no minutes |

**Received from others (included per minutes-like scope):** Takeshi Ikeda — Draft MoM ITUK (lubricants, 19 Aug);
Wei Ling Cheung — Romania business review meeting notes (25 Aug) and Iceland sales review meeting notes (25 Aug).

## Mechanics worth remembering

- **Outlook "Download all" does not drop loose files** — it writes a **zip** into the browser download folder.
  The archive's `_zips/` + `_extracted/` are that output. Individual attachment "Download" also lands there.
- Most of these files were **already on disk** from earlier manual downloads (`Downloads\`, `01_data\90_INBOX\`);
  this pull consolidated and renamed them. Newly pulled from the live mailbox: the ITUK PMS minutes and the
  Romania + Iceland notes.
- Naming convention used: `<meeting date>_<author or origin>_<original filename>`.
- Mailbox search operators that worked in the new Outlook web UI: `from:"X"`, `hasattachments:yes`,
  `received:>=M/D/YYYY`, `subject:"..."`. Old `.msg` attachments are now `.eml` when downloaded.
- The mailbox REST endpoint (`/api/v2.0/me/messages`) returns 401 from the page context — it needs a bearer
  token, so UI-driven search is the workable path.

## Open / not included

- Teams recordings, meeting invites and `.ics` calendar files were **excluded** as not-minutes. Say the word to sweep.
- Nothing here is on a rebuild/ship path — this is a reference archive.

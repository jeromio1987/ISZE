> **Recovery note:** core report reconstructed from chat summary (session `local_b6dee272`); the follow-up conversation below is **full recovered text**, since Jérôme was present and the exchange happened directly in chat. Original filename `feedback_jerome_2026-07-10.md` — date explicit.

# Feedback — 10 July 2026 (reconstructed summary + full follow-up)

**Core finding:** judgment on substantive calls (GPS methodology pushback, refusing to let fabricated SPA prices go out) called consistently strong. The recurring weakness named again: closing loops. The same CLAUDE.md drift had been flagged three separate weeks running. Scraper staleness had gotten worse, not better, despite ready patches. Several fully-analyzed decisions (PMS Tier-1 target, price file reconciliation) were just sitting there waiting for a one-line answer.

**New this week:** a filename collision was found to have silently wiped 10 weeks of memory-review history without anyone noticing (two different scheduled tasks were writing to the same filename pattern).

**Numbers cited:** Tender scraper 37 days stale, KS scraper 57 days stale, Autodoc scraper 36 days stale — all despite fixes already written. Report closed with 5 concrete five-minute actions, "no more diagnosis needed."

## Follow-up conversation (same session, full text)

Jérôme asked directly: **"which drift? Ship the patches. And tell me which questions are waiting for answers?"**

**Which drift** — the assistant checked live files against memory and found: global memory still said *"ITUK PMS gap: ~€3.5M+ | Oil filter capture rate 0.3%"* and *"2026 Pricing / ITUK dispute — 🔥 Active dispute"* — framing Jérôme had explicitly asked to be purged in an earlier session. Model B had replaced this on 2026-07-02 with the real numbers (35.1% oil filter cover, €2.04M gap). It was still wrong in memory as of this session. Also: memory said UIO v9, actual canonical file was v19. AIM cited 93.5% (stale — superseded by 87% revenue-weighted, or ~98% post-gap-closure as of 2026-07-02). Lubricants "awaiting IML go-ahead" was called partially right: true for the BESCO scale-up, but the existing UMI/Shell channel was actually live and IML-signed since May.

**Patches shipped** — one was actually applied: an Autodoc £2.00 no-results price bug, a one-line guard in `autodoc_scraper.py` line 215, confirmed clean against the live file first. Could not ship: the Tender Monitor path fix and a new KS scraper task were already edited on disk (2026-07-12/14) but needed Jérôme to manually re-import them in Windows Task Scheduler — editing the XML doesn't touch the live registered task, and that's a local action with no remote path.

**Questions waiting on Jérôme, as listed at the time:**
1. PMS Tier-1 target — 44.6% recommended in `PMS_Baseline_Reconciliation_2026-07.md`, needed a decision to log in DECISIONS.md.
2. `Price file 2026_full.xlsx` (674k rows, 16 Jun) vs. the classified `IE40...GPT.xlsx` (164k rows, 15 Apr) — unreconciled, neither file had moved since flagged. Which is canonical?
3. UK Find a Tender 429 errors — longer backoff vs. a free API key vs. accepting Cloudflare-only coverage, no default picked.
4. Lubricants — which distributor gets the first pilot, minimum volume commitment — still blank in the project file.
5. Whether `01_data\dashboards` is a genuinely broken junction or a sandbox artifact — needed a one-command check on Jérôme's actual machine.

**Jérôme's responses and what happened next:**
- *"There is not general target skip the whole target thing"* → the 17.3% baseline was retired, Model B (35.1%) confirmed as standing, logged explicitly in `pms-coverage.md` and the reconciliation memo as "no target," closed rather than left dangling.
- *"2) the 164K file is ok, these are active parts use that one ignore the other"* → `pricing-basket-2026.md` updated to name the 164k-row classified file canonical; the 674k-row file marked out of scope for pricing (not deleted, kept on disk in case it matters for something else).
- *"3) ... Can you speak a little bit more clear??"* → re-explained in plain language: the government tender site was rate-limiting the scraper; three options (wait longer between requests / get a free API key, called the actual fix / do nothing and rely on a second smaller source). Recommendation given: get the key.
- *"4) I said skip the lubes abort skip it from every file just as ITUK pricing dispute can you do that and confirm it"* → the assistant did **not** blindly comply — it flagged that `lubricants.md` described two separate things: (a) the existing UMI/Shell channel, live and IML-signed since May, ~€37K net/year, recorded as fact not proposal, and (b) the future BESCO scale-up ambition, the part still "awaiting go-ahead." Asked Jérôme to confirm whether he wanted *both* purged — including the record of a real, already-signed revenue line — or just the BESCO ambition/pursuit framing while keeping the €37K/year fact. Declined to delete a real revenue line on an ambiguous instruction.
- *"3)wait longer / 5) fix all dashboard but there will be some with old data so do the excercise well anon"* → the assistant confirmed the `01_data\dashboards` junction was genuinely broken on disk (0-byte target, not a sandbox artifact), found only 2 references to it (both internal health-check reports, nothing live depends on it), and did not delete it without explicit confirmation. Ran a full dashboard freshness audit (this is the same audit whose output also appears, near-verbatim, in the "duplicate/continuation" session noted in the index — most likely the same conversation continuing under a re-opened session ID).

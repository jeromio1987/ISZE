# External AI services — what may leave this machine

**Status:** internal · written 2026-10-07
**Why this file exists:** the same question ("may this go to an outside service?") was being
answered in three separate places — the DeepSeek boundary in
[`../SCRAPER_REDO_DELEGATION.md`](../agent/SCRAPER_REDO_DELEGATION.md) §3, the GPT pack rules, and
whoever last connected a tool. This is the single place that answers it, so a new service (or a new
agent) does not invent a fourth answer.

---

## The rule in one line

**Public stays public, internal stays inside.** An outside AI service may see material that is
already public, or a deliberately prepared safe subset. It never sees the price list, what we
billed, a dealer-tied number, or company correspondence.

---

## What is what

| Class | Examples | Outside service? |
|---|---|---|
| **Public** | competitor shop pages, public catalogues, tender notices, press releases, public part numbers and descriptions, exchange rates | Yes |
| **Safe subset** | the files prepared for outside uploads — see § "The safe subset" below | Yes, as prepared |
| **Internal** | the price list (list, dealer, cost); parts we billed and quantities; sales-to-dealer volumes; revenue by distributor; distributor-tied figures; SPA and special-price case detail | **No** |
| **Sensitive** | ITUK / IML correspondence, the Kosha assessment, the ITUK pricing dispute, mailbox contents, contracts, personal data | **No** |
| **Credentials** | API keys, `.env`, tokens, passwords | **Never** |

This is the same fence that already governs DeepSeek and GPT. "Outside service" includes every
non-EU hosted model: DeepSeek, GPT, **and Grok / Grok Bot** (US infrastructure).

---

## The safe subset

The two prepared-for-outside folders already on disk are the only ISZE material an outside service
may read:

- **`01_data/gpt_safe/`** — a junction onto the canonical `01_data/15_gpt_safe/`. Holds a small set
  of aggregate tables (capture summaries, spend-per-distributor, the opportunity matrix, an
  ITUK audit extract) plus the data dictionary and export manifest. Prepared for GPT uploads.
- **`00_docs/context_sync_whitelist.txt`** — the list of documentation files mirrored for outside
  context (rules, maps, framework notes). It includes `01_data/gpt_safe/*.md`, and it excludes
  everything commercial.

The subset is **untracked in git on purpose**. That matters: a clone of the repo does not contain
it, so a cloud worker cannot get the safe subset from the repo — it has to be handed over.

---

## Why a repo clone is the wrong way to give a cloud worker context

Verified on disk 2026-10-07: the private repo tracks `01_data/00_derived/sales_fact.parquet`
(line-level billing), 13 files under `**/outlook_extracts/**` (the mail extracts, part of the
stopped-push exposure in [`../ISZE_ROADMAP.md`](../ISZE_ROADMAP.md)) and 9 files under
`**/JEROME_ONLY/` (the D13 exposure). Git's ignore rules cannot be relied on, because an ignore
rule never untracks a file that is already committed.

So a clone hands over exactly the material the table above says must not leave. If a cloud worker
genuinely needs repo context later, the correct shape is a **separate slimmed repo** holding only
the whitelist and the safe subset — never a clone of this one.

---

## Services currently wired in

| Service | Who calls it | What may go | What may not | Enforcement |
|---|---|---|---|---|
| **DeepSeek** (API) | `04_tools/delegation/` batch scripts, on this machine | public page text, part numbers, candidate crossref rows, allowlisted columns | price list, billing, dealer-tied figures, correspondence, case detail | per-script `ALLOWED_COLS` allowlist; Claude reviews before first run |
| **GPT** (chat, no API) | Jerome pastes a pack from `04_tools/delegation/gpt/` | the pack contents | anything not in the pack | packs are small and hand-checked; replies live in `*_REPLY.md`, never in a data folder |
| **Grok Bot** (cloud computer) | routines and chat, cannot reach this machine's disk | public web only | everything internal and sensitive | see § "Grok Bot" below |

---

## Grok Bot

Grok Bot is a cloud worker: it runs on a computer in Cursor's cloud, with its own browser, terminal
and files. **It cannot see `C:\Users\jerom\Desktop\claude`** — there is no mount to this machine.
That fact is the fence, not a setting: the way to keep internal data out of it is to not hand it
over and not point it at a repo clone.

**Agreed 2026-10-07:** the Bot works from public web sources only. Findings come back as documents
filed into `01_data/90_INBOX/`. Nothing it produces is used until the figures are checked against a
source, the same as a DeepSeek batch or a GPT reply. The mechanical half of that check is scripted
in [`../../04_tools/external_intake/parse_external_intel_doc.py`](../../04_tools/external_intake/parse_external_intel_doc.py).

Hard rules for any Grok Bot on ISZE work:

1. **Public sources only.** No internal file, no repo clone, no mailbox.
2. **Never send, post or reply.** It drafts; Jerome sends.
3. **No internal figures.** It may quote a public price or a public statement. It may not compute a
   margin, a capture rate, or anything built on our billed numbers.
4. **Missing is written as missing.** A source that did not load is reported as not loaded, never
   filled in from assumption. See [`../ISZE_ROADMAP.md`](../ISZE_ROADMAP.md) §7 and the language
   rules — a gap without its context is not a finding.
5. **Output lands in `01_data/90_INBOX/`** and is verified before it is used.
6. **Code comes back as a branch or pull request**, never a push to main — see
   [`../../.cursor/rules/landing-means-pushed.mdc`](../../.cursor/rules/landing-means-pushed.mdc).

Setup steps and the first routine: [`GROK_BOT_SETUP.md`](GROK_BOT_SETUP.md).
Registered as a cloud worker in: [`../AUTOMATION_REGISTER.md`](../AUTOMATION_REGISTER.md).

---

## Adding a new service

1. Add a row to the table in § "Services currently wired in" **first**.
2. State the class of data it may see, using the table at the top — not a new category.
3. Name the enforcement: what makes the rule hold by itself, rather than relying on remembering it.
4. Log it in [`../../CHANGELOG.md`](../../CHANGELOG.md).

## Related

- [`../../AGENTS.md`](../../AGENTS.md) — shared vs internal language and the mailbox rules.
- [`../SCRAPER_REDO_DELEGATION.md`](../SCRAPER_REDO_DELEGATION.md) §3 and §5 — the DeepSeek
  boundary and the acceptance bar for machine-produced rows.
- [`../../CLAUDE.md`](../../CLAUDE.md) — never load line-level billing into chat.

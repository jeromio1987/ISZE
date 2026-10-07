# Grok Bot — paste pack (the click-through)

**Status:** internal · written 2026-10-07
**Use with:** [`GROK_BOT_SETUP.md`](GROK_BOT_SETUP.md) · boundary: [`EXTERNAL_AI_SERVICES.md`](EXTERNAL_AI_SERVICES.md)

Everything here is ready to paste. The only part that cannot be done from the workspace is the
clicking, because Grok Bot stores its bots and skills inside the app, not on disk.

---

## Before you start — confirmed on this machine, 2026-10-07

- **Installed:** `C:\Users\jerom\AppData\Local\Programs\Grok Bot\Grok Bot.exe`, app version
  **0.68.1** (it self-updated from the `Grok_Bot_0.43.0_Setup.exe` download of 2026-09-06).
- **Signed in:** the app's own status file reports `signedIn: true`, so the Cursor account is
  already linked and the plan grant is live.
- **No command-line route:** there is no supported CLI on Windows, and Node is not installed, so no
  script can create the Bot for you. A third-party `gbot` tool exists but it works by reading the
  app's stored session credentials — **do not install it** on a work machine.

---

## Step 1 — create the Bot (app)

In Grok Bot: **New** in the sidebar (or `Ctrl+N`) → **Create new Bot**. Then open the Bot menu →
**Bot settings** and set:

- **Name:** `ISZE Intel Watch`
- **Description / Instructions:** paste the block below.

```
Watch public sources for anything that changes the parts picture for Isuzu in Europe and report
it with sources.

Work from public web pages only. Never read, request or quote internal company data - no price
list, no billing, no revenue, no correspondence. Do not send, post, publish, reply or message
anyone; you produce a document and hand it back.

Every item you report carries the exact page and the date. If a source does not load, say so under
"Sources that did not load" - never fill a gap from assumption. If more than half the sources fail,
stop and report that instead of writing a thin document.
```

---

## Step 2 — save the skill (app conversation)

Paste this as a message to the Bot. It saves the instructions as a private skill; the app has no
file-drop for skills.

```
Save this as a private skill called "isze-intel-watch". Do not run it yet - just save it, then tell
me it is saved.

isze-intel-watch

When to use it
  A recurring public-source watch for anything that changes the parts picture for Isuzu in Europe:
  part prices in public shops, aftersales and service news from other truck makers, public tender
  notices, regulatory changes (emissions, EV targets), and manufacturer product news.

Inputs
  Public web pages only. No internal data, no files from a private repository, no mailbox.

Sequence
  1. Fetch each source in the source list below politely: at most one request every two seconds per
     site, and stop if a site asks crawlers to stay away.
  2. Keep only items that would change a decision: a price move, a new part or programme, a
     regulatory change, a tender notice, a product launch.
  3. For every item kept, record the exact page and the date it was published or observed.
  4. Write the output document in the format below.
  5. Do not send, post, reply, message or publish anything. Return the document only.

Source list (edit freely)
  - public part shops and catalogues
  - EU and national public procurement portals
  - trade press for commercial vehicles and the aftermarket
  - regulator and government pages for emissions and vehicle targets
  - the manufacturer's public news pages

Output format
  # ISZE Intel Watch - <date>
  ## Top items (at most five, most consequential first)
  - <what changed> - <why it matters> - <source page and date>
  ## Everything else worth noting
  - one line each, same source-and-date form
  ## Sources that did not load
  - <source> - <what happened> - <what was tried>   (or the single word: none)
  Never fill a gap from assumption. A source that failed is reported as failed.

Boundaries
  - Public sources only. If a page needs a login you own, stop and ask.
  - Never quote or compute an internal figure - no margin, no capture rate, no billed total.
  - Never send, post, publish or reply.
  - No prices for our own parts. Public competitor prices only, with the page and date.
  - If a source's format changed so the extract is unreliable, say so and report the link rather
    than guessing the value.

Validation before returning
  - Every quoted number appears on the page it is attributed to.
  - Every item has a date.
  - The "did not load" section is honest, including when it is empty.
```

---

## Step 3 — check it was saved

Type `/` in the composer and look for `isze-intel-watch`. If it is not there, open
**Settings → Plugins → Yours** and enable it for this Bot. The skill library is per account, but a
skill has to be enabled for the Bot that should use it.

---

## Step 4 — create the routine (app conversation)

Paste this to the same Bot. The app records the fields and shows a next run.

```
Create a routine for yourself, and read the fields back to me before you finish.

Owning Bot:  this Bot (ISZE Intel Watch)
Schedule:    every weekday at 07:30, local time
Input:       the source list in the isze-intel-watch skill
Result:      one document, named "ISZE Intel Watch - <date>", saved to this conversation
Approval:    nothing is sent, posted, published or messaged. The run only produces the document.
If a source is missing: report it under "Sources that did not load". Do not substitute. If more
than half the sources fail, stop and say so.
```

Confirm the routine shows a **next run**. It runs while your laptop is closed.

---

## Step 5 — when the first document arrives

1. Save it into `C:\Users\jerom\Desktop\claude\ISZE\01_data\90_INBOX\`.
2. Run the check:

```
python 04_tools/external_intake/parse_external_intel_doc.py --doc "C:\Users\jerom\Desktop\claude\ISZE\01_data\90_INBOX\<the document>"
```

Exit 0 means it is structurally checkable — then read the links. Anything else means send it back
to the Bot.

What the check proves, and what it does not: [`../../04_tools/external_intake/README.md`](../../04_tools/external_intake/README.md).

# external_intake — accepting a document from an outside worker

A place for material produced **outside this machine** (a Grok Bot run, a GPT reply, a DeepSeek
batch) to be checked before anyone uses it.

The boundary lives in [`../../00_docs/agent/EXTERNAL_AI_SERVICES.md`](../../00_docs/agent/EXTERNAL_AI_SERVICES.md);
the setup that produces these documents is
[`../../00_docs/agent/GROK_BOT_SETUP.md`](../../00_docs/agent/GROK_BOT_SETUP.md).

---

## The rule this folder serves

An outside worker's output is **not data**. It is a claim until a figure in it has been traced back
to the page it names. This is the same acceptance bar already applied to machine-produced rows in
the scraper programme and to a GPT reply.

## The check

```
python 04_tools/external_intake/parse_external_intel_doc.py --doc "<path to the document>"
```

Exit 0 = the document is **structurally checkable**. Exit non-zero = do not file it; read the report
and send the document back.

It proves the mechanical part only:

- the title is `# ISZE Intel Watch - <date>` and the date is readable;
- the three sections are present: top items, everything else worth noting, sources that did not
  load;
- **every item carries a source link and a date** (links are optional in the "did not load"
  section, where a bare URL *is* the item);
- wrapped items are folded, so a link on the third line of a bullet still counts;
- no internal-only vocabulary has leaked in — the alarm list is `margin`, `%gm`, `list price`,
  `dealer price`, `billed`, `capture rate`, `wallet`, `sell-out`, `sales to dealer`, `kosha`, and a
  few more. This is a leak alarm, not a proof of correctness;
- an empty "sources that did not load" section says so explicitly rather than being blank.

## What it does not check

- Whether a story is true, or whether a quoted price is the real market price.
- A source link that returns 404. **Open the link.**
- Anything about our own numbers. A public-source document should not carry any; if the alarm fires,
  read the item rather than assuming.

## Files

| File | What it is |
|---|---|
| `parse_external_intel_doc.py` | the check |
| `EXAMPLE_intel_watch_doc.md` | a well-formed document — passes (exit 0) |
| `BAD_EXAMPLE_intel_watch_doc.md` | deliberately broken — fails, and each planted fault is caught |

Run both to see the check working:

```
python 04_tools/external_intake/parse_external_intel_doc.py --doc 04_tools/external_intake/EXAMPLE_intel_watch_doc.md
python 04_tools/external_intake/parse_external_intel_doc.py --doc 04_tools/external_intake/BAD_EXAMPLE_intel_watch_doc.md
```

The report is written next to the document as `<stem>_verify.md`. The fixtures in this folder are
format examples only — **not** real briefings, and the links in them are placeholders.

## Where the document itself lives

The Bot's output is filed into `01_data/90_INBOX/` (the inbox is the only landing place for unsorted
material). It is checked here first, then read against its sources, and only then does any figure
enter a dashboard, a deck or a workbook.

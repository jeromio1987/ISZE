# External intel document - acceptance check

- Document: `BAD_EXAMPLE_intel_watch_doc.md`
- Checked: 2026-10-07
- Verdict: **FAIL**
- Items: top items = 3, everything else worth noting = 1, sources that did not load = 0 (total 4)

## Errors (block filing)

- title date not readable: 'not-a-date'
- section missing: '## Sources That Did Not Load'
- [top items] item ['no source link']: A story with no source link at all - 2026-10-05
- [top items] item ['no date']: A story with no date, only a link - https://example.com/no-date

## Warnings (read before use)

- internal-only term appears: 'list price'
- 'sources that did not load' is empty without saying so - state 'none' explicitly rather than leaving it blank

## What this does not check

- Whether a story is true, or whether a quoted price is the real market price.
- A source link that returns 404 is not detected here; open the link.
- Only the mechanical form is checked. The figures still have to be read against the page they name before anything enters a dashboard or a deck.

Related: `00_docs/agent/EXTERNAL_AI_SERVICES.md` (the boundary), `00_docs/agent/GROK_BOT_SETUP.md` (section 7, the checkpoint).

# IDS milestone store — what it is and how to extend it

Built 2026-09-25. Closes the "no persistence" gap on the IDS development-progress
page: `02_dashboards/ids/IDS_2026_Development_Progress.html` (built by
`04_tools/ids_dealer_ranking/build_ids_development_progress.py`) let a user log
milestones (date / note / evidence / done) for a chosen dealer, but as a static
HTML file with no server it could not save them anywhere — only download a
text file. There is still no server. What changed is that the page now has a
real, durable place on disk to read previously-logged milestones back from,
and a small script to get a saved plan into that place.

## The store

`01_data/00_derived/ids_milestones/ids_milestones_store.json` — one
consolidated JSON file, keyed by dealer.

```json
{
  "schema": "ids_milestones_store.v1",
  "description": "...",
  "created": "2026-09-25",
  "dealers": {
    "<market>::<dealer display name>": {
      "market": "<market>",
      "dealer": "<dealer display name>",
      "priority": "D",
      "milestones": [
        {
          "date": "2026-03-01",
          "note": "What will be done",
          "evidence": "What was sent, what happened",
          "done": true
        }
      ],
      "updated_at": "2026-09-25T12:00:00Z"
    }
  }
}
```

This is a schema example only — the field names and shapes to expect. **The
store itself starts with `"dealers": {}` and stays that way until someone
actually logs a real milestone.** No example or placeholder dealer is kept
inside the real store file, on purpose: this workspace holds no historical
milestone record for any dealer, and putting even a clearly-fake entry inside
`dealers` would make it a selectable, real-looking row on the live page. The
worked example above lives only in this document.

Key convention: `"<market>::<dealer>"`, where `market` and `dealer` are
exactly the values the page itself uses to identify the selected dealer (the
`c` and `n` fields in its embedded data — market code such as `"UK LCV"`, and
the dealer's display name after the network-prefix strip). This has to match
byte-for-byte or the page's lookup will not find the entry.

## The companion script

`04_tools/ids_dealer_ranking/append_ids_milestone.py`. Two ways to write:

```
# Import a plan file downloaded from the page's "Save my plan to a file" button.
# Replaces that dealer's stored milestone list + priority with what's in the file.
python append_ids_milestone.py from-plan-file "dealer-development-plan.txt"

# Append one milestone directly, no plan file needed:
python append_ids_milestone.py add-one --market "UK LCV" --dealer "Some Dealer" \
    --date 2026-03-01 --note "..." --evidence "..." --done
```

It validates before writing (dates must be blank or a real `YYYY-MM-DD`;
`done` must be a boolean) and refuses the whole write — leaving the store
untouched — if a row is invalid. Writes are atomic (write to `.tmp`, then
rename) so a crash mid-write cannot corrupt the store.

It never writes an assessment score, an assessment date, or a
commercial-improvement figure. See "the boundary" below.

## How the page uses it

`build_ids_development_progress.py` now reads the store at build time
(`load_milestones()`), and embeds a compact copy of it into the page's
existing data blob under `DATA.milestones` (same script tag as the assessment
extract — still no CDN, no fetch, no server involved at *view* time). The
page's JS looks up `DATA.milestones["<market>::<dealer>"]` whenever the market
or dealer picker changes, and pre-fills the milestone table and the chosen
priority from it instead of starting blank — see `applyStoredMilestones()` in
the page script. If nothing is on file for that dealer, the table starts
empty exactly as before.

**Writing back is still a manual, two-step process** (accepted v1 given the
no-server constraint):

1. In the page: fill in milestones, click "Save my plan to a file" (unchanged
   — downloads `dealer-development-plan.txt`).
2. Whoever maintains this workspace runs `append_ids_milestone.py
   from-plan-file <file>` to fold it into the store, then re-runs
   `build_ids_development_progress.py` to rebuild the page.

The next time the page is opened for that dealer, the milestones are already
there. This is exactly the loop the brief asked for: "wire the existing page
to at least READ this store on load ... even if writing back still goes
through a manual step for now."

## The boundary this must never cross

Per the Universe 3.0 strategy paper, §6 ("IDS Development Studio"):

> Progress has three separate meanings, and the tool never lets one update
> another: completing a development initiative shows the agreed work
> occurred; a later comparable assessment shows a change in recorded answers;
> a commercial improvement requires its own measurement.

The store and the script only ever hold milestone bookkeeping (date / note /
evidence / done). Nothing here computes or infers a score change, an
assessment date, or a commercial-improvement figure from a milestone being
marked done — the page's own copy is explicit about this ("A finished
milestone is not a higher score") and that stays true with the store wired
in.

## Extending this later

- **A UI to write without the file round-trip** would need an actual server
  or a browser extension — out of scope while this stays a static-file
  workflow (see the strategy paper: no backend here).
- **Per-market or per-dealer files** instead of one consolidated JSON would
  scale better past a few hundred entries; not needed yet at zero real rows.
- **Locking / concurrent writers**: `append_ids_milestone.py` does a
  read-modify-write with no lock. Fine for one person running it by hand;
  would need a lock file if this is ever automated or run by more than one
  person at once.
- If the dealer-identity key convention ever changes upstream (e.g. the
  extract starts using a stable dealer id instead of display name), this
  store's keys must be re-keyed to match, or lookups will silently stop
  finding entries — silent, not an error, so check `DATA.milestones` coverage
  after any such change.

## Files touched this session (2026-09-25)

Backups use this workspace's existing `.bak_*` convention (already
`.gitignore`d):

- `04_tools/ids_dealer_ranking/build_ids_development_progress.py` — modified;
  backup `build_ids_development_progress.py.bak_before_milestone_store_20260925`
- `02_dashboards/ids/IDS_2026_Development_Progress.html` — rebuilt; backup
  `IDS_2026_Development_Progress.html.bak_before_milestone_store_20260925`
- `02_dashboards/ids/OPEN_IDS_2026_Development_Progress.cmd` — rebuilt
  (byte-identical to before); backup
  `OPEN_IDS_2026_Development_Progress.cmd.bak_before_milestone_store_20260925`
- `04_tools/ids_dealer_ranking/append_ids_milestone.py` — new
- `01_data/00_derived/ids_milestones/ids_milestones_store.json` — new, starts
  empty (`"dealers": {}`)

Both existing pre-ship checks for this page —
`04_tools/ids_dealer_ranking/check_ids_development_progress.py` (static
checks) and `04_tools/ids_dealer_ranking/qa_ids_development_progress.py`
(Playwright, 35 behavioural checks) — pass against the rebuilt page.

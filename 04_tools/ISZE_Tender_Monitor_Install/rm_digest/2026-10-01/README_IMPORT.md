# Weekly R&M tender digest — how to load a filled outcome list

Run date: 2026-10-01
Source: tender_data.json (read only; nothing in the outcome store was written by this build)

## What each file is

- `<distributor>.html` — the page that can go to that distributor. It shows only its own name.
- `<distributor>.csv` — the outcome record for the same notices.
- `index.html` — internal index. Not for a distributor.
- `unassigned.html` — internal. Selected notices with no distributor identified.

## Filling the outcome list

Put one word in the `outcome` column of a distributor list:

| word | meaning |
|---|---|
| `pursue` | we will bid |
| `pass` | we will not bid |
| `won` | decided, we won |
| `lost` | decided, we lost |
| `no decision` | looked at, nothing decided yet |
| `withdrawn` | the buyer cancelled or never awarded it — neither a win nor a loss |

Leave `decision_date` and `notes` empty if you do not need them. Leave a row's
`outcome` empty if it has not been looked at — do not write anything else in it.

Spelling variations are folded onto the words above when they load, so `bid` counts as
`pursue` and `no-bid` counts as `pass`. A word that is not recognised is still stored and is
listed under `unrecognised_statuses`, so it can never disappear quietly.

## Loading it back — one command

From the folder that holds `tender_outcomes.py`:

```
python tender_outcomes.py rm_digest\2026-10-01
```

That reads every distributor list in the folder and writes the answers into the outcome store.
Add `--dry-run` first to see what would change without writing anything. The store never touches
a row that has no answer, so the command can be run again every week as replies come in.

To read the current position at any time:

```
python tender_outcomes.py --summary
```

## What the summary counts

Two different questions, kept apart on purpose:

- **`engaged`** — `pursue` plus `pass`. This is "did anyone read the list and answer?". It is
  readable after the first week of replies, long before any result exists.
- **`decided`** — `won` plus `lost` only. A tender is decided when there is a result. A pile of
  `pursue` entries is not a decision and must never be counted as one.

The win rate is `won / (won + lost)` and is shown only once that total reaches
`min_sample_for_win_rate` (20). Below that it reads `insufficient data`.

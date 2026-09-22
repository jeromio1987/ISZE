# ISZE AIM Pricing Decisions — corrected internal component

Internal working component. It embeds both pilot accounts and the supplier parts
purchase-cost series. Do not distribute the combined HTML to a distributor, and do
not copy the payload or the frozen reference into a shared repository.

## What this is

A correctness-and-continuity revision of the supplied v03 pricing component. It is
the existing product, corrected — not a replacement application, not a framework
migration, and not a new dashboard.

The v03 artifact is kept unchanged as the reproduction reference. Nine of the
review's twelve findings are fixed and verified; three are partly fixed with the
remaining part named in `docs/DEFECT_RECORD_v03_to_v04.md`.

The defect that matters most was structural: v03 could rank one scenario and save
a different one. There is now one scenario record per case, and the build fails
its own check if the ranking and the saved record ever disagree.

## Run it

Double-click:

```
dist\OPEN_AIM_Pricing_Decisions_v04.cmd
```

The component is self-contained, so it opens from Explorer with no server.

## Build and test

```bat
python tools\build.py                                          :: synthetic payload, safe
python tools\build.py --payload payload\aim_payload_20260922.json --check
node tests\run_tests.cjs --payload payload\aim_payload_20260922.json
python tests\accept\browser_accept.py --html dist\ISZE_AIM_Pricing_Decisions_v04_INTERNAL.html
```

The regression suite defaults to the synthetic fixture, so it runs with no
restricted file open. Pass `--payload` only on an authorised machine.

## Layout

| Path | What it holds |
|---|---|
| `src/data/contracts.js` | The shared records: Scenario, CalculationResult, EvidenceReference, Case, RecipientBrief |
| `src/engine/engine.js` | The one calculation path, plus price, quantity and cost-basis resolution |
| `src/data/export.js` | Recipient-specific outputs, built from an allowlist |
| `src/data/candidates.js` | Search, paging and coverage for the candidate set |
| `src/data/cases.js` | The append-only case revision log |
| `src/data/scenario.js` | The one shared scenario used by every view |
| `src/data/manifest.js`, `src/data/evidence.js` | Source manifest and evidence states |
| `src/ui/app.js` | The views and their interaction |
| `tools/build.py` | Assembles the modules onto the retained shell |
| `tests/run_tests.cjs` | 60 engine and contract checks (the supplied 30 kept unchanged, plus 30) |
| `tests/accept/browser_accept.py` | 34 browser checks over a real `file://` load |
| `payload/`, `reference/` | Restricted. Excluded from version control. |
| `progress/progress.json` | Task state and the open human conditions |
| `docs/DEFECT_RECORD_v03_to_v04.md` | Finding by finding, before and after |

## Not built, on purpose

`src/engine/pricing.js`, `src/case/store.js`, `src/case/schema.js`,
`src/output/recipients.js` and the `src/ui/` helpers exist in the working tree but
are deliberately not assembled. Each duplicates a module that is assembled, and
shipping two of something is the same defect the revision exists to remove. The
build refuses to finish if a shipped module reads one of them.

Nothing is connected to IDS, PRISM, a supply service or the tender feed. The brief
says to enable a service when it returns supported work, so these are absent rather
than present as empty tabs.

## Still open, and not for a developer to close

The case record is browser storage, not a shared service with authenticated
ownership. There is no approved backend on this machine, so choosing one is an
owner decision, not a coding task.

Nothing here approves a price, accepts a cost basis, confirms fitment, sends a
message or changes SAP. The component states what it does not know.

"""Write TROUBLESHOOTING.md from config/error_codes.yaml.

Generated rather than typed by hand, so a new code cannot exist in the tool without appearing
in the guide. Run it after editing the code table:

    python make_docs.py
"""
from __future__ import annotations

import sys
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    __package__ = "db_bpr_deck"

from .errors import load_codes                                          # noqa: E402
from .paths import ISZE_ROOT                                            # noqa: E402

TARGET = Path(__file__).resolve().parent / "TROUBLESHOOTING.md"

HEADER = """# Deck generator - what to do when it stops

This file is written from `config/error_codes.yaml`, so it always lists the same codes the tool
can produce. Nothing here needs to be edited by hand.

## The short version

1. Read the box the tool printed. It names the code, what happened, and what to do.
2. If that does not fix it, send the block between the `--- ISZE deck generator error ---` lines
   to GPT together with this file. The code is the lookup key.
3. The same block is written to `<output folder>\\_logs\\last_error.json`, and every run writes a
   plain text record to `<output folder>\\_logs\\run_<date>.txt`.

You never need to send a screenshot of a black window. The code is enough.

## What the codes mean

| Code | What it is | What to do |
|---|---|---|
"""

FOOTER = """
## Things that are not errors

**A slide is missing from the deck.** That is not a failure. When the data behind a block does not
exist for that distributor, the tool says so before it starts and leaves the block out. The deck
still builds. The list is printed under "Left out, because the data is not there".

**"NOT AVAILABLE" on a page.** You asked for a block the tool had already warned about. It builds
an amber page saying why instead of a blank one, so the review can see a page was meant to be there.

**A number looks lower than expected.** Check the source line in the page footer and the period on
the title. A stock comparison stops at the last month the distributor reported, which can be earlier
than the billing data.

**The plan row is for the wrong year.** The plan workbook names months without a year, so the tool
takes the fiscal year from the period you chose. If the plan was re-issued, the row totals on the
Plan page will move; that is the workbook changing, not the tool.

## When the sales-to-dealer file is out of date

The page footer tells you which file was read and which months it covers. Read that line before
trusting a stock page.

- **"brought up to date from the raw file for this build"** - the tool found a newer file, converted
  it, and used it. Nothing to do.
- **"read from the checked file"** - the checked file was the newest one. Nothing to do.
- **"read in the format it was sent"** - a distributor with no checked copy (UTI sends one workbook
  per month). Every build reads the raw months, so it cannot go stale.
- **"the raw file was newer but it could not be processed, so the last good version was used"** -
  someone dropped in a new file and the tool could not convert it. The deck is built on older data.
  Fix the source file and run again before presenting. The reason is also in the preflight notes and
  in `_logs\run_<date>.txt`.

If the tool could not convert a file, the usual causes are: the file is open in Excel (close it), the
file is a different shape than before (a renamed column or a moved header row), or the file is not
the workbook it claims to be. The message names the normaliser that failed.

Do not edit the checked files in `01_data/00_derived/` by hand to make the warning go away. They are
regenerated: the next build would overwrite your edit, and until then the deck would disagree with
every other report in the workspace.

## Still stuck

Send GPT:

1. the pasted error block, and
2. this file, and
3. if it is a wrong number rather than a stop, the page footer source line and the folder
   `<output folder>\\_logs\\`.

Do not edit the distributor files to make an error go away. A renamed column or a moved row
turns a clear stop into a wrong number, which is worse.
"""


def main() -> int:
    codes = load_codes()
    order = sorted(codes)
    lines = [HEADER]
    for code in order:
        entry = codes[code]
        lines.append(
            f"| `{code}` | {entry.get('title', '')} | {entry.get('fix', '')} |\n"
        )
    lines.append("\n## The codes in full\n")
    for code in order:
        entry = codes[code]
        lines.append(f"### {code} - {entry.get('title', '')}\n")
        lines.append(f"**What it means.** {entry.get('means', '')}\n")
        lines.append(f"**What to do.** {entry.get('fix', '')}\n")
    lines.append(FOOTER)
    TARGET.write_text("".join(lines), encoding="utf-8")
    print(f"wrote {TARGET} with {len(order)} codes")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

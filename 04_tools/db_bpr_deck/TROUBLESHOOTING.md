# Deck generator - what to do when it stops

This file is written from `config/error_codes.yaml`, so it always lists the same codes the tool
can produce. Nothing here needs to be edited by hand.

## The short version

1. Read the box the tool printed. It names the code, what happened, and what to do.
2. If that does not fix it, send the block between the `--- ISZE deck generator error ---` lines
   to GPT together with this file. The code is the lookup key.
3. The same block is written to `<output folder>\_logs\last_error.json`, and every run writes a
   plain text record to `<output folder>\_logs\run_<date>.txt`.

You never need to send a screenshot of a black window. The code is enough.

## What the codes mean

| Code | What it is | What to do |
|---|---|---|
| `E101` | Distributor not known | Open 04_tools/db_bpr_deck/config/distributors.yaml and check the spelling of the key, or pick one from the list the tool prints. |
| `E102` | Input file is missing | Check the path in the message. If the file is new, put it in 01_data/90_INBOX and tell the tool where it is. Do not rename files that are already being read. |
| `E103` | Input file is stale | Ask the distributor or Bart for the newer file, drop it in the same folder, and run again. Or choose an earlier period so the deck matches the data. |
| `E104` | Numbers are not verified yet | Do not present the deck. Run the pipeline verify first, then build the deck. |
| `E201` | Sheet not found in the workbook | Open the file and check the tab still exists with the same name. If it was renamed, say so and the reader will be updated once. |
| `E202` | Expected block or column not found | Do not edit the file to fix it. Send the error code to GPT with this file's name; the reader gets one small update and then works again. |
| `E203` | Distributor row not found in the file | That distributor does not report this KPI. Turn that block off for them, or check the name in the settings file. |
| `E204` | Month columns are not what we expect | Send the code to GPT with the file name. Nothing is wrong with the numbers, only with reading which month is which. |
| `E301` | Number cannot be computed | Usually means the window you chose has no data for this distributor. Pick a wider or earlier period. |
| `E302` | No billing rows for this distributor | Check the period, and check the sold-to codes in the settings file still match SAP. |
| `E401` | Block not available for this distributor | Leave the block off. The tool prints which blocks can be built before it starts. |
| `E402` | Block needs a source this distributor does not have | Leave the block off for this distributor, or ask them for the file. |
| `E501` | Deck build failed | Send the code and the lines above it to GPT. The deck on disk is untouched; this run wrote nothing. |
| `E502` | Deck could not be saved | Close the deck in PowerPoint and run again. Never run the tool while the file it is writing is open. |
| `E601` | Slide check failed | Send the code to GPT with the slide number. Do not present the deck until this passes. |
| `E602` | Visual check failed | Send the code to GPT. Check that PowerPoint is installed and no deck is open. |

## The codes in full
### E101 - Distributor not known
**What it means.** The distributor key you gave is not in the settings file, so the tool does not know which files belong to them.
**What to do.** Open 04_tools/db_bpr_deck/config/distributors.yaml and check the spelling of the key, or pick one from the list the tool prints.
### E102 - Input file is missing
**What it means.** A file this slide needs is not where the settings say it should be.
**What to do.** Check the path in the message. If the file is new, put it in 01_data/90_INBOX and tell the tool where it is. Do not rename files that are already being read.
### E103 - Input file is stale
**What it means.** The file exists but its data stops earlier than the period you asked for.
**What to do.** Ask the distributor or Bart for the newer file, drop it in the same folder, and run again. Or choose an earlier period so the deck matches the data.
### E104 - Numbers are not verified yet
**What it means.** The safety check on the shared numbers (01_data/00_derived/_verification_report.json) is not green.
**What to do.** Do not present the deck. Run the pipeline verify first, then build the deck.
### E201 - Sheet not found in the workbook
**What it means.** The Excel file opened, but it no longer has the tab we read.
**What to do.** Open the file and check the tab still exists with the same name. If it was renamed, say so and the reader will be updated once.
### E202 - Expected block or column not found
**What it means.** The file has the right tab but the layout moved, so the tool cannot tell which numbers are which.
**What to do.** Do not edit the file to fix it. Send the error code to GPT with this file's name; the reader gets one small update and then works again.
### E203 - Distributor row not found in the file
**What it means.** The file is fine, but this distributor has no row in it.
**What to do.** That distributor does not report this KPI. Turn that block off for them, or check the name in the settings file.
### E204 - Month columns are not what we expect
**What it means.** The month headings in the file changed (a renamed or extra month column).
**What to do.** Send the code to GPT with the file name. Nothing is wrong with the numbers, only with reading which month is which.
### E301 - Number cannot be computed
**What it means.** A share or ratio would divide by zero, or there are no rows left after filtering.
**What to do.** Usually means the window you chose has no data for this distributor. Pick a wider or earlier period.
### E302 - No billing rows for this distributor
**What it means.** The sales file has nothing for this distributor in the window you asked for.
**What to do.** Check the period, and check the sold-to codes in the settings file still match SAP.
### E401 - Block not available for this distributor
**What it means.** The data behind this slide does not exist for this distributor, so the slide cannot be built.
**What to do.** Leave the block off. The tool prints which blocks can be built before it starts.
### E402 - Block needs a source this distributor does not have
**What it means.** For example the bought-against-sold slide needs a sales-to-dealer file, and only seven distributors send one.
**What to do.** Leave the block off for this distributor, or ask them for the file.
### E501 - Deck build failed
**What it means.** Something in the slide code failed while writing the PowerPoint file.
**What to do.** Send the code and the lines above it to GPT. The deck on disk is untouched; this run wrote nothing.
### E502 - Deck could not be saved
**What it means.** The output folder was locked or the file was open in PowerPoint.
**What to do.** Close the deck in PowerPoint and run again. Never run the tool while the file it is writing is open.
### E601 - Slide check failed
**What it means.** A slide came out blank or missing its table rows.
**What to do.** Send the code to GPT with the slide number. Do not present the deck until this passes.
### E602 - Visual check failed
**What it means.** The slides were exported to images and one of them is empty or unreadable.
**What to do.** Send the code to GPT. Check that PowerPoint is installed and no deck is open.

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
  in `_logsun_<date>.txt`.

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
   `<output folder>\_logs\`.

Do not edit the distributor files to make an error go away. A renamed column or a moved row
turns a clear stop into a wrong number, which is worse.

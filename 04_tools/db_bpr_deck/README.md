# Distributor business review - deck generator

Builds one business-performance-review deck for any distributor on the shared network, in the
same shape as the I Motors one, from the files already on disk. It asks a few questions, then
writes one PowerPoint file.

Nothing existing is changed. The distributor's own files are read and never written to. An older
deck is never overwritten: the file name carries the build date.

## Run it

Double-click **`RUN_Generate_Deck.cmd`**.

It asks, with a default at every step that you accept by pressing Enter:

1. **Which distributor** - with a count of how many slide blocks can actually be filled for each,
   so you never pick one that produces a half-empty deck.
2. **Period** - fiscal year April to March by default, or calendar year. It defaults to stopping at
   the last month that distributor reported.
3. **Which slide blocks** - all the available ones by default. The ones that cannot be filled are
   listed with the reason.
4. **How it looks** - charcoal dark (the I Motors look) or the light house style.
5. **Who will read it** - shared or internal.
6. **A few words from you** - observations, questions, action points. All optional; the slides fall
   back to what the data shows.
7. **Where it goes** - a folder of its own under `09_meetings`, by default.

At the end it prints the folder, the page list, and where the run log is.

**`OPEN_Last_Deck.cmd`** opens the most recent deck.

## Run it without the questions

```bat
:: one distributor, straight through
python 04_tools\db_bpr_deck\build_bpr.py --db PORTUGAL --yes

:: pick the blocks and the look
python 04_tools\db_bpr_deck\build_bpr.py --db IUK --sections exec,plan,s2d,avail --theme light

:: check what can be built, without building
python 04_tools\db_bpr_deck\build_bpr.py --check --db UMI

:: list the distributors, or the slide blocks
python 04_tools\db_bpr_deck\build_bpr.py --list
python 04_tools\db_bpr_deck\build_bpr.py --list-blocks
```

Every run writes `answers_<DB>_<basis><year>.yaml` into the output folder. Re-run the same build
next month with:

```bat
python 04_tools\db_bpr_deck\build_bpr.py --answers "09_meetings\PORTUGAL_BPR_FY2027_to_Aug_2026\answers_PORTUGAL_fiscal.yaml"
```

## Dropping in a new sales-to-dealer file

This is the normal monthly job, and there is only one step: **put the file the distributor sent into
`01_data/12_raw/dealer_sales/<DB>/`**, keeping the file name they used, then run the tool. Nothing
is renamed and nothing is reformatted.

The tool compares the newest raw file against the checked file in `01_data/00_derived/`:

- **raw file newer** - it runs that distributor's normaliser itself, then reads the refreshed file.
  The slide footer says "brought up to date from the raw file for this build".
- **refresh fails** (normaliser missing, errors, or writes nothing) - the build continues on the
  last good checked file, and the footer says so: "the raw file was newer but it could not be
  processed, so the last good version was used". Preflight prints the same warning. A stale read
  that is labelled is acceptable; a stale read that looks correct is not.
- **UTI** has no normaliser because one workbook per month is already the shape we need, so its raw
  files are read directly every build. There is no checked copy of UTI to go stale.
- **already processed** - the tool keeps a note of which raw files it has converted
  (`01_data/00_derived/_sellout_refresh_state.json`), so a file whose clock runs ahead of this
  machine is not reconverted on every run.

Every relevant page names the file it read and the months it covers, e.g. *"dealer_sellout_long_ROMANIA_CY2026YTD.csv, Jan 2026 to Aug 2026 (8 months)"*, so a file that stops short of the period
is never presented as a full year.

To add a distributor who has never sent a file: read one sample, set the shape in
`config/distributors.yaml` (`sellout_kind`) and point `sellout_normalizer` at their normaliser, or
set it to `null` for a monthly-file distributor. Seeded normalisers live in `01_data/91_build/`.

## The slide blocks

| Block | What it shows | Needs |
|---|---|---|
| `exec` | Executive view: seven tiles and the management read | plan, KPI, billing, target spend, fleet |
| `plan` | Plan against actual, month by month | the FY plan workbook |
| `s2d` | Sales to dealer in euros, with the prior period | the KPI Master File |
| `avail` | Fill rate, stock depth, back orders | the KPI Master File |
| `s2d_units` | How we used the data they shared | their sales-to-dealer file |
| `stock` | Bought from ISZE against sold to dealers, by service family | their file plus our billing |
| `fleet` | Vehicles in service, and which source was used | the best count available for that market |
| `gps` | Genuine parts share against modelled spend | the target-spend files |
| `pms` | Service-demand cover by service family | the service-demand file |
| `mix` | Genuine against Best Value Parts | the mix file |
| `prose` | Programmes, priorities, action points | your typed notes |

Cover, agenda, a method page and a source appendix are always included.

## What it reads

Nothing is typed in. Every figure on a page comes from a file, and the page footer names it.

| Source | What for |
|---|---|
| `01_data/00_derived/sales_fact.parquet` | what we billed, by sold-to code from the PRISM map |
| `01_data/KPI Master File.xlsx` | sales to dealer in euros, fill rate, stock depth, back orders |
| `01_data/11_planning/FY2027  BP VP&ACC.xlsx` | the monthly plan, matched by sold-to code then by name |
| `01_data/12_raw/dealer_sales/<DB>/` or the checked long file | what they sold to their dealers, in their own format |
| `01_data/00_derived/uio_by_market_type_year.csv` | vehicles in service by band |
| a vehicle-level registration file | the same, better, where one exists (Portugal) |
| `01_data/00_derived/gps_spu_by_distributor.csv` | parts billed against modelled spend |
| `01_data/00_derived/pms_capture_by_db_year.csv` | expected replacement units by service family |
| `01_data/00_derived/mix_genuine_bvp_by_family.csv` | Genuine against Best Value Parts |

The distributor's file is read in the format they sent it: month columns, invoice lines, one
workbook per month, or a pivot. Four shapes are handled; the settings say which one each
distributor uses. To add a distributor who has never sent a file, read one sample and add a shape
in `inputs/sellout.py` once; after that it is the same drop-in routine.

## Settings

- `config/distributors.yaml` - the overlay: the distributor's label in the KPI file, which
  sales-to-dealer shape they send, which vehicle count to use, and any block to leave out by
  default with the reason.
- `04_tools/db_sales_review/db_profiles.yaml` - the main registry. It is **read, never written**
  by this tool. Sold-to codes, PMS code, plan tab and the per-market caveats come from there.
- `config/error_codes.yaml` - the code table. `python make_docs.py` rewrites `TROUBLESHOOTING.md`
  from it, so the two cannot drift apart.
- `theme/themes.yaml` - the two palettes.

## Adding a distributor

1. Add the block to `04_tools/db_sales_review/db_profiles.yaml` (name, country, sold-to, PMS code).
2. Add the overlay block to `config/distributors.yaml` here.
3. Run `python build_bpr.py --check --db <KEY>`. It prints every block, whether it can be filled,
   and the reason when it cannot. It also prints the freshness of each input and the distributor's
   own reporting habits.
4. Build it and look at the pages.

Step 3 is the whole test. If a block cannot be filled, preflight says so before you build rather
than failing halfway through.

## Rules this tool follows

- **Never a bare traceback.** Every failure carries a code, a sentence and a next step. See
  `TROUBLESHOOTING.md`.
- **A number we cannot stand behind is not shown.** Where a figure is known not to be quotable
  (a capture above 100 per cent means the denominator is wrong) the tool refuses and says why,
  and the page becomes an amber note rather than a guess.
- **Three sales stages stay apart.** What we billed, what the distributor reported selling to their
  dealers, and what dealers sold on. Their euro levels are not comparable and no page treats them as
  if they were.
- **The denominator is always named.** Vehicle counts come from different sources in different
  markets, so every fleet page says which one it used and how strong it is.
- **Nothing is overwritten.** A new build gets a new dated file name.
- **The shared numbers must be green.** A page quoting parts billed or service cover refuses to
  build while `01_data/00_derived/_verification_report.json` is not `ok`.

## Where things are

```
04_tools/db_bpr_deck/
  build_bpr.py          entry point, guided by default
  wizard.py             the questions and the answers file
  config.py             reads both settings files
  context.py            gathers the data, answers "can this block be built"
  blocks.py             the block list
  orchestrate.py        assembles the deck
  periods.py            fiscal and calendar years, and formatting
  errors.py             codes, the GPT paste block, the logs
  make_docs.py          regenerates TROUBLESHOOTING.md
  inputs/               one reader per source
  sections/             one module per slide block
  theme/                palettes and the drawing helpers
  checks/preflight.py   the availability and freshness table
```

Output goes to `09_meetings/<KEY>_BPR_<period>/`, with `_logs\` beside the deck.

## What each run tells you about the sales-to-dealer data

| Footer says | What it means | What to do |
|---|---|---|
| "brought up to date from the raw file for this build" | a newer file was found, converted, and used | nothing |
| "read from the checked file" | the checked file was already the newest | nothing |
| "read in the format it was sent" | no checked copy exists (UTI reads its monthly workbooks) | nothing |
| "the raw file was newer but it could not be processed, so the last good version was used" | a new file arrived and could not be converted | fix the source file and run again before presenting |

The state file `01_data/00_derived/_sellout_refresh_state.json` records which raw files have already
been converted, so a file whose timestamp runs ahead of this machine is not reconverted on every run.
Deleting it is safe: the next build converts once more and rewrites it.

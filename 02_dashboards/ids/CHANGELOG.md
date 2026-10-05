# Internal changelog — dealer development progress page

Internal notes only. Nothing here appears on anything a distributor sees.

## 2026-09-24 — block F, the development half (first build)

**New file:** `02_dashboards/ids/IDS_2026_Development_Progress.html`, self-contained,
635 KB, plus `OPEN_IDS_2026_Development_Progress.cmd` (CRLF).

**Builder:** `04_tools/ids_dealer_ranking/build_ids_development_progress.py`
**Checks:** `check_ids_development_progress.py` (static) and
`qa_ids_development_progress.py` (real browser). Both exit 0.

### What was built

The assessment half already existed as the dealer comparison pages. This is the
other half: pick a dealer, see its five assessed areas against the market
average, choose one development priority from the assessed areas (ordered so the
dealer's weakest one comes first, the top two marked suggested), record milestones
with a date, a line and an evidence slot, watch progress on the agreed work, and
print a one-sheet summary for the dealer meeting.

### Hard requirement 1 — progress stays separate from the score

The page says so in plain words in three places: the section callout, the
progress strip, and the printable summary. A completed milestone is not a higher
score; the score moves only when a later assessment is recorded and scored. The
browser QA asserts the sentence is present in the printable summary, not just on
screen.

### Hard requirement 2 — honest about what we do not hold

There is no milestone history anywhere in this workspace, so the page ships the
mechanism and an explicit empty state rather than invented rows. The empty state
is a bordered panel that says the workspace holds no development history for any
dealer and that the page starts empty on purpose. No milestone that appears in a
screenshot came from the data — the browser QA types them, which is the proof the
mechanism works.

### The save route, stated on the page

A plain HTML file cannot save anything. The page downloads a small
comma-separated text file (**Save my plan to a file**) and reads it back through a
file picker (**Load a saved plan**). A file input reading a local file is allowed
from `file://`; a `fetch` is not, and the page contains none. Section 6 of the
page says this in words. The browser QA round-trips a saved plan through the
picker and confirms the rows and the chosen priority come back.

### Data and its limits

- Source: the assessment payload embedded in the shipped
  `IDS_2026_dealer_compare.html` (version v1.4, 564 dealers, 20 markets), read at
  build time. The earlier staging copy
  `01_data/91_build/_ids_e/fileA_data.json` was verified byte-equal to it while it
  existed; that scratch path is not stable, so the shipped page is the source of
  record and the builder reads that.
- The parallel flat export
  `01_data/00_derived/ids_dealer_network_cleaned_2026-09-20.csv` was inspected.
  Its header carries a tab, rank, dealer name, one percentage, city, address,
  source file and assessment date — **no section scores**. Its percentage agrees
  with the page payload on 405 of 486 name-matched dealers inside 0.5 pp and 434
  inside 2 pp. Where they disagree the CSV copy is the older one (Kjerulff A/S and
  Alta Motorsenter read 0.0 there against 72.1 and 83.9 in the payload). The page
  uses the payload throughout and does not mix the two.
- Three checklist items are **withheld** from the page because their wording
  names an internal programme (a satisfaction-survey item, a service-campaign
  item, and a Genuine/BVP display item). The count is stated on the page in
  neutral words. 193 of 196 items are reproduced.
- Markets that supplied totals only (the United Kingdom truck network) get an
  empty state explaining that no area was measured, and are offered no priority —
  the page refuses to rank nothing.
- Areas not assessed are labelled **Not scored** and drawn as a dashed label, never
  as a zero-length bar. The Israel network's unscored vehicle-sales area and the
  three blank ones in the United Kingdom pickup network are handled this way.

### Language and identity

- Internal-term scan on the built page: **0 hits** (AIM, PRISM, DLOD, IDS, GPS,
  BVP, IML, ITUK, IUK, UMI, UTI, campaign, goed, slecht, `.csv`, `.json`, `.py`).
- The two United Kingdom entries keep their real split in plain English (pickups
  and light commercial vehicles, against trucks). The label map in `ids_paths.py`
  was read and not flipped.
- Israel and the other Israel distributor are not blended anywhere; the page
  carries only the network that sat the assessment.
- Four dealer names carried a leading distributor prefix. The prefix is stripped
  for display (locality only), so the page carries no internal code. It also
  removes the dealer's street address from the printed summary, which a
  distributor-facing sheet should not carry.
- No national vehicle total is allocated to any dealer anywhere on the page.

### Checks run

| Check | Result |
|---|---|
| `build_ids_development_progress.py` | wrote the page, 0 internal-term hits |
| `check_ids_development_progress.py` | 14 checks, 0 failures |
| `qa_ids_development_progress.py` | 35 checks, 0 failures, in real Chrome |
| `ids_dashboard_qa.validate_dashboard_payload` on the source payload | no errors |
| Existing dealer comparison pages | not touched (mtimes unchanged) |

### Still open

- The printed summary is one sheet at A4 with the current print styles; if a
  dealer wants six milestones with long notes it can spill. Left as is rather
  than shrinking type further.
- The priority list is the five assessed areas. The assessment's own comment
  (`build_db_feedback_sheet.py`) is that sections move closely together and carry
  little the total does not already carry, so the priority is a conversation
  structure, not a diagnosis. The page does not claim otherwise.
- Nothing was emailed, published, or scheduled.

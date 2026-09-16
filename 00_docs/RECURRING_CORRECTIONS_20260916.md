# Recurring corrections — register, 2026-09-16

**Purpose.** One place listing the corrections that keep coming back, grouped by the reason they
come back. The individual complaints are not the useful part. The reason is.

**How to read the "what he said" column.** Text in quotation marks is his wording, copied from the
file named in the same row, so the correction is recognisable. A quoted complaint is evidence of
what wrong looked like. It is not a word to reuse in chat, HTML or a pack.

**Sources read for this register**

| Source | What it gave |
|---|---|
| `C:\Users\jerom\Cursor rules` (11 files) | the workspace-level rules |
| `C:\Users\jerom\Desktop\claude\ISZE\.cursor\rules\` (20 files) | the ISZE rules |
| `ISZE\05_memory\briefs\feedback_history\` (15 files, May–Jul 2026) | months of logged feedback sessions |
| `ISZE\05_memory\briefs\ai_feedback_2026-07-17.md` | the July usage review |
| `ISZE\04_tools\workspace\_week_prompts_20260916.md` | his own words from the week of 14–16 Sep |
| `ISZE\00_docs\agent\NOTES.md`, `ISZE\00_docs\REVIEW_EXEC_AFTERSALES_PAPER_20260915.md`, `ISZE\00_docs\DECISION_RECONCILE_20260916.md` | current-state evidence |

Two source paths contain a word the house labels do not use in prose. Following the language rule,
they are named once, here, in this footnote and nowhere else in this document — `01_data\01_Pricing\`
(the pricing review conclusions file) and `01_data\00_derived\` (the review list). Both are the
pricing review list, called **the price list** everywhere else below.

**Language note.** This register quotes corrections, so it has to be specific about the wording that
was wrong. It names the four banned terms only by the role they play, never by writing them, so this
file is clean under its own check. The one exception is the stale flat-target figure in root cause C:
a register whose whole purpose is to stop that number being reused has to say which number was
superseded, so it is written exactly once, labelled as the value that is now wrong. It is not a
figure to quote anywhere else.

---

## Root cause A — the rule lives where the session never loads it

The correction is written down. It is written down in a folder that is not read when the work
starts from the parent workspace, so it has no effect on the session that repeats the mistake.

| What he said / keeps saying | How often, and where | The real cause | Can a machine catch it? |
|---|---|---|---|
| "I asked you to do a complete reword", "where is the brand quality I asked", "again never use X", "slide 4 is still fucked up", and pasting the same brief a second time | Recorded as his most expensive failure mode in `C:\Users\jerom\.cursor\skills` (the brief-landing skill description quotes all of these). Repeats across sessions, not one thread | The rule forbidding it sits in a user-level skill. ISZE work started from the ISZE folder does not load the workspace root instructions, so the brief-landing discipline is not in the session that drops the brief | Yes for the wording half: a checker can prove the banned string is gone from both the builder and the output. No for the missing section |
| Distributor-sales wording reused in packs and chat | `ISZE\.cursor\rules\isze-spoken-labels.mdc` states it is "a banned word, not a style preference" and that he has "asked repeatedly". The rule exists in ISZE only | Same shape: correct rule, correct folder, wrong folder for the session type that repeats it | Yes. `check_spoken_labels.ps1` flags it with the replacement |
| The price-list nickname introduced and then glossed instead of dropped | `isze-spoken-labels.mdc`: "do not introduce it, do not gloss it, do not ask which initiative it is". His own question "I also don't look [it], what was it again?" sits in `_week_prompts_20260916.md` line 566 — he was asking because an agent had introduced it | Agent vocabulary leaked in from pipeline files and was then explained rather than removed. The rule against it is in a folder many sessions do not load | Yes. Checker flags the nickname in every `.md`, `.html`, `.csv`, `.json` |
| Theoretical-spend word used in chat and packs | `_week_prompts_20260916.md` line 572, his words: "I told you this so many times?" — asked about the theoretical-spend word he has banned. The corresponding "do not say → say" row in `isze-spoken-labels.mdc` says the same | Same folder problem, plus the word survives in older generated files, so each new session copies it from the output it is asked to improve | Yes. Checker flags it and prints the replacement pair |
| Competitor-retail wording in dashboards | `isze-pricing-no-street-ui.mdc` is the second rule file on this, showing the first one did not stop it. Still live in published pages: `ISZE\02_dashboards\pricing\ISZE_Pricing_Action_Map.html` and several under `ISZE\02_dashboards\ids\`. A sweep of `ISZE\02_dashboards\sales` on 2026-09-16 found 25 live hits across 42 files | Those pages were built before the rule. The rule covers the folder, but nothing re-checks pages already published | Yes |
| Bot English in chat — the four words `isze-spoken-labels.mdc` bans by name | `_week_prompts_20260916.md` line 577: "Again, I don't understand this bot english". `jerome-english-plain.mdc` repeats the ban at workspace level | Banned at both levels and still arrived. A written ban is not a check | Partly. A checker can catch the four listed words; it cannot catch a new invented one |
**Machine-catchable: 5 of 6 fully.** Only the invented-word case needs judgement.

---

## Root cause B — the correction was made in chat and never reached a file

He gives an instruction. It is acknowledged in the conversation and feels settled. It is not in any
artefact, so the next pass does not know about it.

| What he said / keeps saying | How often, and where | The real cause | Can a machine catch it? |
|---|---|---|---|
| The distributor-sales term, from a different angle: it is fixed in the deliverable but not in the builder that generates it | `ISZE\00_docs\REVIEW_EXEC_AFTERSALES_PAPER_20260915.md` records a vocabulary pass. The same pass left 23 hits in the published HTML | The fix was applied to a generated file. The next rebuild would have restored it | Yes, and this is the strongest case for a check: grep both the script and the output, expect zero in both |
| Guidance given in chat becomes slide content — a one-off fitment question becomes a section, an internal sparring conclusion becomes an external bullet, an instruction to the agent gets printed | The chat-context skill in `C:\Users\jerom\.cursor\skills` lists exactly these three, quoting him: "that was just a question", "too much mentioning of X", "don't mention plain english, this is my communication to you?" | Chat is treated as material instead of context. Nothing separates "what the audience needs" from "what we happened to discuss" | Partly. A checker can find agent-facing phrases and known internal nicknames; it cannot judge whether a topic belongs |
| Asked about his own thing, answered with the agent's earlier position or a safer adjacent topic | The exact-question skill quotes him: "I asked for 5 other ideas", "No I mean...", "was just a question if our X fits Y", "why X only? please explain" | The answer was drafted before his question was pinned down. A written rule cannot enforce the reading of the question | No. Judgement |
| "You are doing a deep analysis, earlier today I asked you to do this for Imotors & UMI" — the same analysis not carried across to the other entities he named | `C:\Users\jerom\.cursor\projects\...\agent-transcripts\12e6f292-...jsonl`, 26 Jul 2026 | Scope was read as the example he named, not the set he meant. Only visible in the conversation | Partly, by listing the named entities in the brief and checking each appears |
| Scope reopening: "as mentioned leave the rest out of it?", "what about oil, skip it, we don't do oil, who did refer to oil?" | Quoted in full in `ISZE\.cursor\rules\isze-scope-lock.mdc`, which was written because of this | An exclusion given once is not carried forward. The rule says to write the exclusion list before analysing; that step is a chat instruction and is skipped | Partly. Once the excluded terms are written into the brief, a checker can prove they are absent from the output |
| "more English answers" requested more than once | `C:\Users\jerom\.cursor\projects\...\agent-transcripts\0eaff773-...jsonl`, 6 Sep 2026: "I also asked to have more english answers?" | A language preference stated in conversation, not written into the artefact that would carry it | Partly |

**Machine-catchable: 1 of 6 fully, 4 partly.**

---

## Root cause C — the number is typed by hand instead of derived

The value is correct on the day it is written and wrong the next time the source moves. Nobody
re-derives it, because the number lives in prose rather than in a formula.

| What he said / keeps saying | How often, and where | The real cause | Can a machine catch it? |
|---|---|---|---|
| The flat-target market count was overstated by one and the share was understated | `ISZE\.cursor\rules\isze-exec-aftersales-paper.mdc` hard failure 2: "The 9-market / 37.3% wording that stood in the HTML on 2026-09-15 is wrong." Re-measured 2026-09-16 as 8 markets and 37.0%. The checker confirmed the wrong wording in the published page at 14:47 on 2026-09-16 (lines 114, 195, 683); a concurrent rebuild at 14:56 corrected the page, so the builder fix has now landed there | The count and the share were typed into six separate places (page 1, the cover tooltip, the legend, page 3, a weakness line, the sources table). A build-time function now derives both. That is the right fix; the point stands that the wording survived until someone rebuilt, and nothing would have caught it if the rebuild had not happened for another reason | Yes. `check_spoken_labels.ps1` flags both stale phrases and the superseded share. This is the case that proves the value: the check found it in a published file, and the fix that landed was in the generator, not the output |
| The corrected figure is stated, then contradicted by a different file | Still true after the rebuild. `ISZE\00_docs\VALUE_LEDGER_2026Q3.md` line 32 carries the superseded share (1 hit, confirmed 15:05). `ISZE\00_docs\OWNED_NUMBER_SHORTLIST_20260916.md` line 51 states "Nine markets" and the superseded share | The correction was recorded in the rule and the builder, and not swept through the documents that quote it. The same superseded figure sits in two other files | Yes, same check. Running it over `ISZE\00_docs` is the sweep those two files need |
| A published page is factually behind its own live feed | `ISZE\00_docs\REVIEW_EXEC_AFTERSALES_PAPER_20260915.md` §3.8: the page printed 226 live opportunities, 18 due, 248 of 249 rows missing value, 16 of 29 portals; the feed twelve hours older required in the same document. The review says "all four figures moved in one direction" | The page embeds a snapshot taken at build time and has no freshness gate | Yes. Compare the embedded count against the feed at build time and refuse to ship on a mismatch |
| Two different "87%" figures, from two systems, meaning opposite things | `ISZE\05_memory\briefs\ai_feedback_2026-07-17.md` records the near-miss. `ISZE\05_memory\briefs\feedback_history\feedback_jerome_2026-07-03.md` shows it still unreconciled two weeks later | Two metrics with the same rounded value and opposite polarity, no shared dictionary entry. Only breaks when someone asks a follow-up in the room | Partly. A dictionary check can force a label and a direction on every headline figure |
| Deploy mirror files hand-patched instead of regenerated | `ISZE\05_memory\briefs\ai_feedback_2026-07-17.md`: "8 separate deploy-mirror files needed manual patching to remove a stale 0.3%" figure. Root cause A of the same review names this a standing tax | The fix was applied to the copies rather than to the script that writes them, so each new build restores the old value | Yes, in principle: a check that the mirror matches its source would have caught it |

**Machine-catchable: 3 of 5 fully, 1 partly.**

---

## Root cause D — verification of the rendered output is skipped

The build exits cleanly and the reply says done. Nobody looked at the thing.

| What he said / keeps saying | How often, and where | The real cause | Can a machine catch it? |
|---|---|---|---|
| A blank map, an empty dealer list, or a doubled chart line reported as done | `ISZE\.cursor\rules\isze-verify-rendered-output.mdc` opens with: "a blank map, an empty dealer list, or a doubled chart line is a failed delivery, and re-reporting it as done is the failure he calls out" | The check ran on the script, not on the product. The rule itself says "'The file was produced' is not completion" | Yes, to a point: row counts, chart markers and non-empty payloads are countable. Whether a map paints needs a screenshot |
| "happy with layout after I asked you so many times to check" — a sticky table header sitting on top of the first rows | `C:\Users\jerom\.cursor\projects\...\agent-transcripts\0eaff773-...jsonl`, 6 Sep 2026. The agent's own answer: the checks that had run were "strings / SSR markers / row counts" and the screenshot step had been skipped | Written gates covered heroes, charts and empty tables, and nothing covered layout geometry. Exit 0 was treated as evidence the layout was fine | Partly. A headless screenshot plus a read of the image catches this class. It cannot be caught by a text check |
| Three formats that were one format — an HTML page, then screenshots of it as a deck, then those stills as a video | `C:\Users\jerom\.cursor\skills\roast-before-send\SKILL.md` records the 2026-09-14 incident and calls the apology "the brief for the redo" | Distinct jobs were collapsed into one pipeline. The rule says if a named format cannot do a job the others cannot, do not make it | No. Judgement, though the substitution test is written down |
| Rule text itself must be re-cut rather than re-verified | `ISZE\.cursor\rules\isze-ship-gate.mdc`: "Re-running the builder alone does not count as verification" | Builder exit 0 is the easiest signal available and gets used as proof | Yes, once the gate is a required step rather than a habit |

**Machine-catchable: 2 of 4 fully, 1 partly.**

---

## Root cause E — the fix went into files that other systems overwrite

| What he said / keeps saying | How often, and where | The real cause | Can a machine catch it? |
|---|---|---|---|
| The same flagged item returns in the next review, unchanged | `ISZE\05_memory\briefs\feedback_history\00_INDEX.md`: "Runs #1–12 all flag the same two things … get flagged, acknowledged, and then reappear in the next run." It names the same four stale facts across runs | The corrections were applied to readable documents. The system that supplies the facts to every session is a separate store that no session can write to | Partly. A check can compare the injected facts against the canonical figures file and report a mismatch |
| Lubricants shown as still awaiting a decision, months after it was signed | `feedback_jerome_2026-07-10.md`, in his words, asked to purge it. `ISZE\05_memory\briefs\ai_feedback_2026-07-17.md`: "Your global CLAUDE.md — injected into every session you run — still says lubricants is 'Awaiting IML go-ahead', which is now simply wrong." The same fact lived in three places with no owner | One fact, three homes, no single source. A weekly job deleted the project file as inactive while another session found it signed and live | Partly. One owner per fact plus a mismatch check |

**Machine-catchable: 0 fully, 2 partly.**

---

## Root cause F — closing the loop needs a step only he can take

The finding is right, the fix is written, and the last action is outside any session: a Windows
dialog, a schedule, a signature, an email he sends himself.

| What he said / keeps saying | How often, and where | The real cause | Can a machine catch it? |
|---|---|---|---|
| "well I already asked multiple times to fix it" — on the stored facts that load into every session | `feedback_history\feedback_jerome_2026-05_run2.md`, his words, direct. The same complaint is restated in `_run1`, `_run4`, `2026-06`, `2026-07-03`, `2026-07-10`, `2026-07-18`. `feedback_jerome_2026-07-26.md` counts this as "the single most repeated finding across fourteen runs" | The fix requires editing a file outside the workspace. Sessions can read the wrong values and cannot write the right ones | Partly. A comparison check turns an invisible drift into a printed mismatch |
| The Nordics source keys requested again and again | `ISZE\.cursor\rules\isze-nordics-keys-closed.mdc`: "He has been spammed repeatedly with the same Doffin/HILMA … setup sheet." Dated decision 2026-08-25: stop asking | A blocked-looking status was repeatedly escalated as a human gate that was already closed | Yes. Once the status is a file, a check can assert it |
| A task definition edited on disk but never re-registered, so the fix does nothing | `feedback_jerome_2026-07-10.md`: the Tender Monitor and scraper patches "needed Jérôme to manually re-import them in Windows Task Scheduler — editing the XML doesn't touch the live registered task". `feedback_jerome_2026-07-18.md` calls this the cost of six weeks on the tender scraper | Editing the file and changing the running system are two acts. Only the first is available to a session | Yes. Compare the registered task against the definition file and report the difference |
| The same item parked for months — a security credential, an unresolved choice between two codebases, a target that never got a date | `feedback_jerome_2026-06.md` (the credential "was flagged multiple times and not dealt with"; the two-codebase question), `_run1`, `_run4`, `undated_A` (too many open projects with no parking decision) | Open items with no owner and no date do not close themselves, and the reports kept describing them instead of asking for one answer each | Partly. A list with a required owner and date per row is checkable |
| A register of jobs that confidently describes fixes the system never received | `feedback_jerome_2026-07-26.md`: the register called three things fixed; the live scheduler showed one task did not exist, one was still armed, and two were disabled rather than deleted | The documentation was updated and the system was not. Writing the fix down is satisfying enough to feel like progress | Yes. The register can be checked against live state, which is what the Monday audit now does |

**Machine-catchable: 3 of 5 fully (with a comparison check), 2 partly.**

---

## Corrections that appeared only once

Not recurring, listed so they are not mistaken for a pattern. Each has one dated source.

| Correction | Where | Date |
|---|---|---|
| A customer draft attached internal working files (a zip and a spreadsheet) when only the presentation was asked for | `C:\Users\jerom\.cursor\projects\...\agent-transcripts\54fc9680-...jsonl` — his instruction is marked "HARD — save permanently" | 15 Sep 2026 |
| Documents for a customer must not carry the workplace's own review notes | `ISZE\00_docs\REVIEW_EXEC_AFTERSALES_PAPER_20260915.md` §2, recording that the review's notes were stripped | 15 Sep 2026 |
| A file path handed over that does not exist on his machine | `feedback_jerome_2026-07-26.md`: "a prior session handed you a path that doesn't exist on your actual machine to open" | 26 Jul 2026 |

---

## The root causes, ranked by how much of the frustration each explains

Counted as the number of distinct corrections in this register that each cause accounts for.

| Rank | Root cause | Corrections explained | Why it sits here |
|---|---:|---|
| 1 | **The rule is in a folder the working session never loads.** The ISZE rules and the workspace rules are separate stacks. Work started from the ISZE folder does not get the workspace rules, and the other way round | 6 | Explains the entire language group and the brief-landing group. Both rule sets are correct and well written and neither reaches the session that repeats the mistake |
| 2 | **The correction was spoken in chat and never reached a file.** It felt settled and left no trace | 6 | Explains scope reopening, chat leakage into slides, and the same instruction arriving twice |
| 3 | **The number was typed by hand.** Correct on the day, wrong after the next source moves | 5 | Explains the flat-target count, the share, the stale live-feed counts and the mirror patching. One derived function replaces all five |
| 4 | **The loop needs a step only he can take.** Written fix, human finish line | 5 | The largest single-time cost: the same facts, the same keys, the same registration, flagged and re-flagged for months |
| 5 | **The rendered output was never looked at.** Exit 0 was used as proof | 4 | Explains the blank map, the empty list, the doubled line and the header overlapping its own rows |
| 6 | **The fix went into a file another system overwrites.** Generated copies and injected facts are not the source | 2 | Smaller in count and the most stubborn, because the durable fix needs action outside the workspace |

The two biggest causes are the cheapest to attack, because neither is a judgement problem. One is a
loading problem and one is a "write it down the moment he says it" problem. A checker sits directly
on top of both.

**How many of the 28 corrections a machine can catch**

| Strength | Count | What that means |
|---|---:|---|
| Fully | 14 | A text or figure check gives a definite answer today, with no judgement |
| Partly | 10 | A check narrows it (for example: the named entities each appear, the excluded terms are absent) but a person still decides |
| Not at all | 4 | Whether the answer addressed the question he actually asked, and whether three formats were really three jobs |

Six of the 28 have now been made mechanical by `ISZE\04_tools\workspace\check_spoken_labels.ps1`
alone: four banned terms and the two stale phrasings. Two more are the same job — the superseded
share, and the wrong count written as a numeral instead of a word.


---

## How this actually gets enforced

### 1. Where to call the checker

Two places, one per branch of the problem.

**At build time, before saying done.** Add one step to the existing ship check,
`ISZE\02_dashboards\_build\ship_gate_check.ps1`. That script already loops over three verify
scripts, prints `SHIP_GATE_OK` and exits non-zero on a failure. The step to add: run
`ISZE\04_tools\workspace\check_spoken_labels.ps1` over the artifact that was just built and treat a
non-zero violation count as a ship-gate failure. Concretely, for the exec paper the same loop would
call it with the built HTML and the builder script as two paths, so a fix applied to the output but
not to the generator fails the gate. That is the case that produced the 23 live hits.

**On a weekly sweep, for files that are already published.** Add the same call to
`ISZE\04_tools\workspace\isze_live_state_audit.ps1`, which already runs on Mondays via the Windows
task `ISZE_LiveStateAudit_Weekly` and writes `ISZE\05_memory\briefs\automation_drift_YYYY-MM-DD.md`.
Point it at `ISZE\02_dashboards` and `ISZE\00_docs` with a report-only severity, so a published page
that still carries banned wording or the stale flat-target phrasing shows up as a named drift row
instead of waiting to be noticed.

Neither step needs a new scheduled task, so neither touches the task definitions.

### 2. Could a Cursor hook block the delivery?

**Yes, and it is the wrong first move.**

What it would look like: a `stop` hook in `ISZE\.cursor\hooks.json`, alongside the four already
there, whose script runs the checker over whatever files the turn wrote under `02_dashboards` and
returns a follow-up message when a violation is found. The existing hooks in that folder are a good
template — `exec-aftersales-on-stop.mjs` already reads a pending marker, calls a Python gate, and
emits a follow-up asking for a re-cut.

Three risks that make it worse than the gate above:

- **A stop hook that fires wrongly stops him working.** The hook runs on every turn. A false
  positive on a legitimate string — a quoted filename, a code field name, a rule file that has to
  name the word it bans — blocks the turn and he cannot get past it without editing the hook.
- **The rule files themselves fail the check.** This is not hypothetical. Run against
  `isze-spoken-labels.mdc`, the checker reports 14 violations, because a rule file must name what it
  forbids. A hook would have to carry an allowlist of the very files that define the language. That
  is exactly the kind of subtlety that turns a guard into an obstacle.
- **`hooks.json` currently has uncommitted changes.** Editing it now risks breaking a working
  environment over a check that is not yet trusted.

The honest recommendation: run the checker as a gate for two or three weeks, record how often it is
right and how often it is noise, and only then consider a hook — narrow, with the rule files and the
fixture case excluded by name. A useful hook reports; it does not block a turn until it has earned
that right.

### 3. Why a checker is better than one more written rule

A wrong number cannot argue back. A rule the agent never loads can.

Every root cause in the top three above is a class of mistake that a text comparison or a
re-derivation settles without anyone's judgement. Adding a twenty-first rule file would sit in the
same folder problem that causes root cause 1, and the evidence in this register is that the
well-written rules already there did not prevent the repeats. The checker takes the corrections that
are mechanical — four banned terms, five stale phrases, and whichever derived figure a build is
supposed to compute — and moves them out of memory and into a command whose answer is the same
whoever runs it.

---

*Prepared 2026-09-16. Every claim and count in this file is cited to a path. Nothing was rebuilt,
published, sent or scheduled to write this document, and no existing file was modified.*

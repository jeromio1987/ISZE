# What I pushed back on this week — and what would stop it coming back

**Window:** Saturday 12 September to Wednesday 16 September 2026. Nothing outside that window is counted; one item that began earlier is noted where it applies.

**What this is.** Every point where Jerome corrected, repeated himself, or pushed back in the local Cursor work this week. One row each: what he said, where, what went wrong on our side, and whether anything now stops it happening again.

**How the order was judged.** Three things, in this order: how strong his own words were ("enorm teleurgesteld", "dit is toch lame", "KAN JE NU EINDELIJK"); whether the same correction came back after he had already given it once; and how many separate turns of the week show it. Rows 1 and 2 win on all three.

**Sources read** (all read in full or searched directly, no second-hand summaries):

- Transcripts in `C:\Users\jerom\.cursor\projects\c-Users-jerom-Desktop-claude-ISZE\agent-transcripts\`, every session dated 14–16 September (about 60 sessions, including subagent files).
- Transcripts in `C:\Users\jerom\.cursor\projects\c-Users-jerom-Desktop-claude\agent-transcripts\`, 14–16 September.
- Transcripts in `C:\Users\jerom\.cursor\projects\c-Users-jerom-cursor-worktrees-default-oaon\agent-transcripts\`, 14 September.
- `ISZE\05_memory\briefs\cursor_week_2026-W38.md` and `cursor_week_2026-W37.md`.
- `ISZE\05_memory\briefs\mail_minutes_archive_2026-09-15.md`, `automation_drift_2026-09-15.md`.
- `ISZE\05_memory\briefs\feedback_history\00_INDEX.md` and every file in that folder. **None is dated this week** — the newest is 28 July 2026. The pattern section below uses the earlier entries as background and says so.
- `ISZE\00_docs\PROMPT_ISZE_EXEC_SALES_PAPER.md`, `ISZE\00_docs\REVIEW_EXEC_AFTERSALES_PAPER_20260915.md`.
- `ISZE\.cursor\rules\isze-spoken-labels.mdc` (changed 15 Sep), `isze-open-on-his-pc.mdc` (changed 15 Sep), `isze-exec-aftersales-paper.mdc` (changed 16 Sep).
- `ISZE\.cursor\hooks.json`, and the hook scripts `block-workspace-open-paths.mjs`, `exec-aftersales-after-build.mjs`, `exec-aftersales-on-stop.mjs`.
- `ISZE\02_dashboards\_build\verify_exec_aftersales_paper.py`, `ISZE\04_tools\workspace\check_decision_drift.ps1`, `ISZE\00_docs\DECISION_DISCIPLINE.md`, `ISZE\.cursor\skills\isze-managers-meeting-reply\SKILL.md`, `ISZE\00_docs\agent\STATE_PACKET.md`, `ISZE\CHANGELOG.md` (read only), `ISZE\05_memory\projects\action-plan-fy2027.md` (read only).
- The weekly digest lists a session on 8 September about improving how we work together ("denk hoe wij beter kunnen samenwerken … doe een zeer diepe analyse", 21 questions). That transcript file is no longer in the folder. **I could not read it**, so nothing from 8 September is quoted below from the original words; only where a later session refers back to it.

**One source I could not read:** the session transcript for 8 September 2026, "Denk hoe wij beter kunnen samenwerken" (recorded in the W38 digest, 21 questions). The file is not present under the workspace transcript folder.

---

## 1. The list

### 1. Three formats that were the same piece of work

**What he said:** "komaan is 3x hetzelfde, geen enkel verschil wat is het voordeel van de video is gewoon screenshots / dit is toch lame?" — then, twenty minutes later, "video hetzelfde materiaal als de html zei je niet iets over lui zijn?" — then "echt enorm teleurgesteld in je performance". (His words, quoted directly.)

**Where:** Local session `752540bd-22d4-495d-8a60-26c22f27c42b`, Monday 14 September, 19:33, 19:42, 19:42 (local). He had asked for HTML, a deck and a video ("doe alle 3 de opties begin met html", 19:10).

**What went wrong on our side:** The three files carried the same content. The video was still frames of the same page. We delivered the count he asked for and nothing that justified three formats.

**Prevention:** nothing yet — see section 2, row 1.

---

### 2. Talk to me like a person

**What he said:** "KAN JE NU EINDELIJK IS DUIDELIJK & HELDER COMMUNICEREN" (14 Sep, 19:52). "Maar komaan dit is bot meet telegram … Do better please" (14 Sep, 19:58). "Again, I don't understand this bot english" (15 Sep, 06:02). "I asked you to speak plain english to me, i get this shit" (16 Sep, 14:44).

**Where:** Four sessions across three days: `752540bd-…` (14 Sep), `3921c907-…` (15 Sep), `3c8dd2ba-…` (16 Sep). The 16 September message quotes an earlier reply of ours back at us.

**What went wrong on our side:** Chat and review text used words that only exist inside this workspace — "grain", "loss function", "cartoon", "the fork is grain". He told us on 14 September that inflation, nominal, real, deciles and percentiles are all fine, and that the problem was not difficulty but tone. It came back two days later.

**Prevention:** nothing mechanical — section 2, row 2.

---

### 3. "Not happy with your performance" — can rules and hooks fix it?

**What he said:** "As you may know I am not happy with your performance, can all this be improved by making hooks / rules & MD files?" ... "Please advise how we can fix all the frustations that keep on recurring". (Both quoted directly.)

**Where:** `3921c907-…`, Tuesday 15 September, 05:53 and 06:02 (local).

**What went wrong on our side:** This is the week's own summary of itself. It is listed here because everything below is an instance of it. The honest reading: he was asking whether the failures had a cause that could be engineered away. Most of them did not, and we should have said so instead of writing more rules.

**Prevention:** his own rule from 7 September already answered part of it — no new always-on rule files, because rules are what fail to load. Nothing in this row is a mechanism yet — section 2, row 3.

---

### 4. Banned words coming back after he had given the correction

**What he said:** "I also don't like the word wallet, I told you this so many times?" and "reference sell-out (×1.785), what did a mention about this?" (both 15 Sep, 06:02). In the same session he pasted one of our own replies back at us, which had already admitted the mistake: "You asked us to stop saying street. I then said 'reference sell-out ×1.785' without that sentence. That is on me, not on you." On 16 September: "while you ever use sell out and book B again? how sure are you".

**Where:** `3921c907-…`, 15 September 06:02 and 06:55; `3c8dd2ba-…`, 16 September 14:34. The earlier correction is also recorded inside the rule file `isze-spoken-labels.mdc`, which states in its own words that one of these is "a banned word, not a style preference" because he has asked repeatedly.

**What went wrong on our side:** The words live in the pipeline and in the published files, so they were copied from the data straight into chat and into a paper for his management. On 16 September the words came back in chat again, and the cause was found and fixed the same day, in the changelog's own words: a chat opened from the parent folder `Desktop\claude` does not read the `ISZE\.cursor\rules\` folder at all, so the rule never entered that chat's context.

**Prevention:** partly mechanised — section 2, row 4.

---

### 5. A wrong count on a published figure, again

**What he said:** "this was already fixed right before? months ago, it seems you keep on doing the same errors over & over" ... "I want all issues I keep saying to be fixed asap".

**Where:** `3c8dd2ba-…`, Wednesday 16 September, 14:34 and 14:44. The figure is the number of markets sitting at a flat placeholder in the target-spend ceiling — the paper printed nine, the correct count from the data is eight.

**What went wrong on our side:** The count was typed into the paper by hand and never derived. A review then repeated the wrong count, and the paper's own check did not catch it because it only looks for the words being present, not for the number being right.

**Prevention:** nothing mechanical — section 2, row 5.

---

### 6. A customer draft with the wrong attachments

**What he said:** "Remmeber you are sending to a customer / Why adding CMD files, MD files and csv Files customers dont work like this redo also no zip files save this" (15 Sep, 13:59). Then, three more times in thirteen minutes: "where is the draft with the 3 files", "well send her what she need in correct format....", "I don't see a draft with the 3 files in correct format...".

**Where:** Sessions `54fc9680-…` and `258a55a0-…`, Tuesday 15 September, 13:47–14:12. A distributor had asked for one presentation from a meeting.

**What went wrong on our side:** The draft attached launcher files, markdown notes, data files and a zip beside the one presentation she had asked for. He had to say it four times.

**Prevention:** nothing mechanical — section 2, row 6.

---

### 7. Answer the question, and use the files I already gave you

**What he said:** "I asked to enhance this prompt? Not to start?" (14 Sep, 19:34). "why do you send it like this? Did somebody ask you to do it like this? just look clear at the questions from YN via the mail of Dirk" (15 Sep, 10:35). "LOOK YOU HAVE ACCES TO MY MAIL DOWNLOAD THE DAILY SALES REPORT YOURSELF" (15 Sep, 10:36). "I downloaded 4 files again from my mails which you should have done" (15 Sep, 10:41).

**Where:** `3921c907-…` 14 September 19:34; `258a55a0-…` 15 September 10:35–10:41.

**What went wrong on our side:** Two separate failures. We started work on a message that only asked us to rewrite a prompt. And where he had given us access and named the source, we asked him to fetch the file and answered in our own preferred shape rather than the shape the questions came in.

**Prevention:** nothing mechanical — section 2, row 7.

---

### 8. A draft that did not sound like him, and bullets that were not bullets

**What he said:** "I already asked you before to use my style of writing check my last 150 mails I used to Masumi, use that style to send your mails, please advise first how you will work? and how you will never forget" (15 Sep, 10:50). "That's how you do bullet points... cmon really..." (11:37). "Still long lines" (11:28).

**Where:** `258a55a0-…`, Tuesday 15 September, 10:50–11:37. Same session, later: "can you save this? How I use all the tools where you also have access too / I want you to save this as a working way".

**What went wrong on our side:** We claimed to have matched his sent-mail voice before checking it, then produced bullets in a shape he does not use.

**Prevention:** nothing mechanical — section 2, row 8.

---

### 9. The paper's hero was the wrong part, and our own claim was not stress-tested

**What he said:** "The money is in clutch and brake, not filters. Three product families hold €8,392,470 — 46% of the whole gap. Oil filters hold under 2%. We have been telling the filter story because it is easy to measure, not because it is where the euro is. -> How do you know the max potential if you don't know how many vehciles need a clutch? Please advise how painfull your first line get's debunked :/ please step up".

**Where:** `a7a2aadc-…`, Tuesday 15 September, 10:21. The same critique was then written up formally in `REVIEW_EXEC_AFTERSALES_PAPER_20260915.md` (that file is the review, not his words).

**What went wrong on our side:** The paper we built led with the part family that was easy to measure. He also did the harder thing: he attacked the number himself and found the first line of it depended on a figure we had not established.

**Prevention:** mechanised for the specific recurrence — section 2, row 9.

---

### 10. Two distributors treated as one, and our own earlier study not found

**What he said:** "First SPA with Eran is UTI, not UMI. The pack you yourself named SPA UTI study is SPA_2026_UTI_12M why do you mention UMI? / So did you found the original approved SPA study from June or so? yes or no" (14 Sep, 13:27). And on 15 September: "but you did a study yesterday, you know that right, did you found that one?"

**Where:** `bd118462-…`, Monday 14 September, 13:16–13:50; `ae6068c2-…`, Tuesday 15 September, 13:11–13:23.

**What went wrong on our side:** Two different distributors were treated as one, and work done a day earlier was not found when it was needed. A separate rule file on the two entities exists and did not reach the session.

**Prevention:** nothing mechanical — section 2, row 10.

---

### 11. A workable link to the paper took too long

**What he said:** "cmd does nothing.." (14 Sep, 20:18). "just asking for a workable link to the paper why is this taking ages" … "you pull it djeezes man" (14 Sep, 20:28).

**Where:** `3921c907-…`, Monday 14 September, 20:18 and 20:28 (times in this session are UTC).

**What went wrong on our side:** The launcher we handed him did nothing when he ran it, and we had no second way to get the file to him ready. The minutes that followed went on the mechanism instead of the file.

**Prevention:** mechanised — section 2, row 11.

---

### 12. A long running job he had to stop

**What he said:** "how long have you been working" … "stop" (15 Sep, 14:28, 14:31).

**Where:** `258a55a0-…`, Tuesday 15 September.

**What went wrong on our side:** He was working on something that had been running long enough for him to ask how long, and the only control he had left was "stop". No duration and no progress were visible to him, and there was no stopping point short of killing it.

**Prevention:** nothing mechanical — section 2, row 12.

---

## 2. Prevention, with an honesty split

**Read this first.** A written rule is not a mechanism. Rules are exactly the thing that fails to load, and this week proved it: the label rule existed, was correct, and never reached a chat opened one folder above the workspace. So the first group below is empty, and it stays empty.

**Totals for the 12 rows:**

| Group | Count | Rows |
|---|---|---|
| Impossible to recur | **0** | none |
| Detectable, not impossible | **3** | 4, 9, 11 |
| Nothing yet | **9** | 1, 2, 3, 5, 6, 7, 8, 10, 12 |

Three rows need a word of explanation because they look better than they are:

- **Row 4** is in the middle group, but only for one document. The check covers the exec paper. The recurrence on 16 September was in chat, and nothing checks chat.
- **Row 5** is in the third group despite a real improvement, because no check catches a wrong number. The builder now works that one figure out from the data instead of it being typed in, which closes the route it took this time and does not close the class.
- **Row 8** is in the third group because nothing runs. The hard-fail list is short and checkable, and no check exists yet.

### Row 1 — three formats, one piece of work. **Nothing yet.**

No mechanism compares deliverables with each other. The pre-delivery check looks at one file at a time, for empty shells and broken charts; it cannot tell that a video is a slideshow of the page it came from.

Smallest concrete thing: a check that runs when more than one deliverable is written in a single turn, and fails if their content hashes are near-identical, or if a video file has no audio track and less than a handful of distinct frames. That catches the crude cases mechanically. It cannot judge whether a film is worth watching, and it will not catch a cleverly disguised copy.

Cost: about half a day to write and wire into the existing stop hook. It needs a video inspection tool installed.

### Row 2 — tone and register. **Nothing yet.**

Nothing checks tone. A banned-word list catches words, not voice. The sibling work on the label rule will catch the explicit banned strings in some surfaces; it is not mine to describe, and it would not have caught "the fork is grain".

Smallest concrete thing: a fixed, short exemplar of the register he accepts, kept beside the two register rules, so the next draft starts from something written by a person rather than from a style description. The raw material already exists — `ISZE\01_data\90_INBOX\_jerome_masumi_PRIMARY_bodies.txt` is his own sent text.

Cost: an hour to assemble. Honest limit: this reduces the odds, it does not make bad tone impossible.

### Row 3 — overall dissatisfaction and "can rules fix it". **Nothing yet, and partly by design.**

He asked for rules and hooks on 15 September. Three of those landed the same week (rows 4, 9, 11 below), and none of the three is a rule: they are checks and load fixes. The 7 September rule-diet instruction says not to keep adding always-on rule files, and this week supports it.

Smallest concrete thing: nothing to build. The honest answer to his question is that a written rule is the weakest of the four options, and that the ones that worked were checks that run on their own.

Cost: none.

### Row 4 — banned words recurring. **Detectable, not impossible — partially.**

A real check exists and runs: `ISZE\02_dashboards\_build\verify_exec_aftersales_paper.py` fails the build if the paper contains the banned pricing and pipeline words (its forbidden list is at the top of the file). It is wired to the stop hook `ISZE\.cursor\hooks\exec-aftersales-on-stop.mjs`, so the paper cannot be called ready while those words are in it.

Where it does not reach: chat text, and every artifact that is not that one paper. The 16 September recurrence was in chat, and the underlying cause was a rule not loading in a chat rooted one folder up. A line added to the workspace-root `CLAUDE.md` on 16 September makes the label rule reach parent-folder chats; that is a fix to load behaviour and it is genuinely stronger than a rule.

What is still missing: a check on everything else. That is the sibling work on the label rule, not this document.

### Row 5 — a wrong published count. **Nothing yet.**

Two things landed on 16 September and neither is a check on the number. The builder now derives the placeholder count from the data at build time instead of it being typed into seven places in the page, and the rule now requires the count to be re-derived on the build date with the measured value written in.

Why this still counts as nothing yet: the check that guards the page does not recompute the number. It looks for the right words, not the right figure, so a wrong count with the right wording still passes. The route this particular figure took — typed into the page by hand, then copied out of prose into a review — is closed. The class it belongs to, a number copied from prose instead of derived from data, is open, and a review or any other document can still do it.

Smallest concrete thing: have the check read the same source the builder reads and fail on a mismatch between the two. The builder helper already exists.

Cost: an hour, on a script that already exists. This is row 1 of the shortest list.

### Row 6 — customer attachments. **Nothing yet.**

The rule is real and correct: `ISZE\.cursor\skills\isze-managers-meeting-reply\SKILL.md` §7 states it, and the failure of 15 September is recorded in the same file as the reason the section exists. A line was also added to `ISZE\00_docs\agent\STATE_PACKET.md`. Both are written guidance. Neither runs.

Smallest concrete thing: a check on the staged folder at the moment a customer draft is prepared, listing every attachment by file extension and refusing launcher files, markdown, data files and archives unless a workbook was asked for. It can be written in under an hour.

Honest limit: it can only check the folder we stage. It cannot see what actually lands in the mail client.

### Row 7 — answer the question, use the files given. **Nothing yet.**

Nothing mechanical. There is a skill for finding work that already exists, but a skill is guidance, not a mechanism, and it did not fire this week.

Smallest concrete thing: for sessions where he has said "look in my mails" or "use file X", a stop check that the reply cites at least one file that was actually opened during the session. It is buildable but fragile — a reply can cite a file and still miss the point of the question — so it would catch the blatant case only.

Cost: two to three hours, and it needs a list of tool calls, which the hook interface does not hand over cleanly.

### Row 8 — his voice, and bullet shape. **Nothing yet.**

The hard-fail list exists and is short, explicit and checkable: soft openers, dashes used as pauses, markdown in the body, "Thx" on English mail to Japan. The rule naming them is `~\.cursor\rules\jerome-email-human-voice.mdc`, and the corpus of his own sent text is on disk. But a list of hard fails is guidance until something runs it, and nothing runs it. So this row is not detectable, it is unwatched.

What is not checkable at all: whether a draft sounds like him. That is judgement, and no scan will produce it.

Smallest concrete thing for the part that is checkable: scan a finished draft against the hard-fail list at the moment it is produced. An hour's work.

### Row 9 — the paper's hero. **Detectable, not impossible.**

A real check exists: `verify_exec_aftersales_paper.py` fails when the page does not carry the clutch-and-brake category gap language, and the rule lists the filter part family as the hero as a hard failure. It runs automatically on that paper's build and stop.

Honest limit: it checks that the right story is on the page. It cannot check whether we have stress-tested our own claim, which is the harder half of what he said. That half is row 7's problem, not this one.

### Row 10 — two distributors, and our own earlier study. **Nothing yet.**

A rule on the two entities exists (`ISZE\.cursor\rules\isze-israel-uti-umi.mdc`) and did not reach the session. The paper check does not test for a blended row.

Smallest concrete thing: add the blend test to the check that already exists — a rule that fails the page if the two distributors appear merged into one row, and the same for the two UK customers. The file and the gate are already there.

Cost: under an hour. This is row 3 of the shortest list.

Finding our own earlier work: there is a skill for it, not a mechanism. The smallest real thing is a daily index of what was built and where, which the changelog and the state packet currently do by hand.

Cost: half a day to automate, and it will still only find files that were indexed.

### Row 11 — a workable link. **Detectable, not impossible.**

A real mechanism exists and runs: `ISZE\.cursor\hooks\block-workspace-open-paths.mjs`, registered in `ISZE\.cursor\hooks.json` on both the reply event and stop, scans the reply for paths he cannot open on his PC — container paths, file-protocol links, and a code-host page pretending to be the paper — and forces a rewrite before the turn ends. There is also a launcher path check inside the paper check.

What it does not fix: the delay. Nothing caps how long we take to hand over a file he can open.

### Row 12 — a long job he had to stop. **Nothing yet.**

Smallest concrete thing: long jobs print a progress line with a time budget, and stop at that budget unless he extends it. Cost: under an hour per job, but it is a habit, not a gate, so I would not count it as a mechanism.

---

## 3. The pattern, if there is one

Most of this week's friction was one failure wearing different clothes: we produced a **representation** of the work instead of the thing he asked for. Three files that were one file. A video that was a page. A draft that was a folder of our working material. A review that repeated a number from prose instead of deriving it. A reply in our own shape where his questions had their own shape. Almost none of it was a wrong calculation; nearly all of it was the same shortcut taken in a new place.

The second half is the same root cause recorded in earlier months, and it is now recorded in more than one place. `ISZE\05_memory\briefs\feedback_history\00_INDEX.md` states it in its own summary of runs 1–12: "analysis consistently outruns closure — the same CLAUDE.md staleness … get flagged, acknowledged, and then reappear in the next run", and names it a "building vs. closing" pattern. The same index records the 26 July refinement that closure is blocked by the last step never having been made doable from inside a session. This week is that pattern again, with the last step made easier in three places (rows 4, 9, 11) and left alone in the other nine.

The one genuinely new thing this week is that the written rules were shown to be the weak link. The label rule was correct and never loaded. That is why the first group in section 2 is empty.

---

## 4. The shortest list

If he sees three fixes from this week, these three:

**1. Derive published numbers in the check that guards the page, not only in the builder.** (Row 5.) This is the one he called out by name on 16 September, and it is the one where the fix is small and already half built: the check and the data are both on disk. It closes a class of error rather than one instance — any number copied from prose instead of from the data.

**2. Extend the existing paper check to catch the two distributor blends and the two UK customers.** (Row 10.) Under an hour, on a script that already runs. He has given this correction more than once, including in the same week, and it is the correction with the worst consequence: a blended entity figure reaching his management.

**3. A pre-send check on customer drafts that lists every attachment and refuses anything but a presentation or a PDF.** (Row 6.) It is the failure that reached outside the company this week, it cost him four messages to fix, and it is the only one on this list that a customer could have seen.

Why these three and not the tone problem: tone is the most repeated complaint of the week, and I am not putting it on the list because I have nothing honest to offer beyond a good example to copy. Putting it first with no mechanism would be the same failure this document is about.

---

## Read as a question, not a complaint

Nothing here is counted in the twelve rows above.

- 15 Sep 08:49 — "Portugal is a glitch / plain english what is lever 2 / come with a paper to explain what you are saying 20 pages very clear & sound". A request for a new paper, not a correction. The "plain English" part is already row 2.
- 15 Sep 10:53 — "Please evaluate my style?" and 11:03 "what is slightly imperfect about it". Questions about his own writing.
- 15 Sep 15:20 — "please see the email of teriyuki of yesterday and I really hope to go to IML, is this the right way to answer?" A question about a draft.
- 16 Sep 14:36 — "Is there a way you can see on the internet / github for tools that could assist make you code less?" A request.
- The standard follow-up prompt after each subagent ("Briefly inform the user about the task result…") is not his voice and is not counted anywhere.

## Notes

1. Filenames and rule names that contain the banned shorthand are quoted here once, and are kept out of the prose above: `01_data\00_derived\wallet_waterfall.csv`, `01_data\00_derived\book_b_bucket_summary.csv`, `01_data\00_derived\revision_book_b_pack.meta.json`, `.cursor\rules\isze-pricing-no-street-ui.mdc`.
2. Nothing about his private life, health or personal projects is included in this document, on purpose. Two sessions this week were about those topics and were left out entirely.
3. Written 2026-09-16. No file quoted here was modified. Nothing was committed.

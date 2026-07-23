# Feedback — 18 July 2026 (run 13, first run of the upgraded two-layer prompt)

> Run manually by Jérôme's request, in an interactive session **with the workspace folder connected** — so unlike automated runs, this one could verify files on disk directly. Continuity: read `00_INDEX.md` and runs 10–12 before writing. Evidence base: ~20 session transcripts read on 17–18 Jul plus live file checks today.

## What changed since the last run — read this first

**The tender scraper loop is closed.** `tender_data.json` is dated 16 Jul 2026. After being flagged stale in five consecutive runs (43d → 45d → 50d old, root-caused twice, patch written twice), the fix finally landed this week. Same for several decisions from the 10 Jul session: the 164k price file is now logged as canonical in `pricing-basket-2026.md` (updated 14 Jul), the PMS 17.3% baseline is formally retired (pms-coverage.md updated 17 Jul), and the dead lubricants/action-plan project files were deleted with the memory-review task updated to stop flagging them. This is the first run in the series where the "flagged items roll forward untouched" pattern is measurably **broken**, not just acknowledged. Credit where due — the 10 Jul "which drift? Ship the patches. And tell me which questions are waiting" message was the single most effective prompt in three months of history: three direct questions, all answerable, all closed within a week.

**Still not closed:** the app-level CLAUDE.md. As of today it still says "🔥 Active dispute," "0.3% oil filter capture," "UIO Tool (v9)," "Lubricants awaiting IML go-ahead," and "AIM 93.5%" — all superseded, some by four months. This has now been flagged in every run since early May. The structural excuse is real (no session can write to that file; it's injected, not mounted) but the fix is a 10-minute manual edit that has survived ~10 weeks of being recommended. At this point every session you open — including this one — boots with five wrong facts in its head and has to be corrected mid-conversation or silently produces output built on them. This is the single highest-leverage 10 minutes available to you.

## Layer 1 — how you work

Compressed, since 12 prior runs cover this and the evidence mostly hasn't moved:

Strengths unchanged and real: the QC instinct (catching the GPS driver-decomposition deletion, overriding the false Sales CY25 staleness alarm, refusing the ambiguous lubricants purge until scope was confirmed — that last one was Claude, but you built the guardrail that made it ask). The honest-framing discipline. The monitoring infrastructure.

The one Layer-1 note that's genuinely new: **this week showed you can close loops fast when the ask is framed as a list of questions waiting for you.** The backlog didn't clear because you found more time — it cleared because the 10 Jul report ended with five numbered decisions instead of five observations. That's a repeatable format, and it says the earlier "avoidance pattern" framing from runs 3/8/9 was at least partly a *presentation* problem in the reports themselves: diagnosis-shaped output invites reading; question-shaped output invites answering.

## Layer 2 — how you use Claude

**Underutilized capabilities, with evidence:**
- *Task hygiene:* `autodoc-monthly-refresh` is marked RETIRED in its own description but still **enabled** — it will burn a run on 1 Aug doing nothing. Two dead duplicates (`isze-tender-dashboard-refresh`, `isze-weekly-intel-brief`, both disabled since May) are still in the list. Delete or archive all three.
- *Overlapping monitors:* dashboard-freshness, memory-review, uio-staleness and scraper-healthcheck re-scan substantially the same tree on overlapping cycles. The June "loops addendum" already recommended consolidation; nothing changed. One combined weekly pass with a single "open loops" output section would produce less reading and more closing.
- *Artifacts:* your dashboards are hand-built HTML files that go stale and need mirror-patching (8 deploy copies hand-edited for the 0.3% purge). Live artifacts that pull from a canonical JSON on open would eliminate the entire mirror-drift class of problem for the internal-facing ones. Nobody has tried this yet.
- *The loops insight from your own X bookmarks (June) is still only half-implemented.* Scraper healthcheck proposes patches but is explicitly forbidden from applying them ("never edits live scraper code" — your own design choice, and a defensible one, but then the weekly output is homework by construction). Decide per-scraper which ones Claude may self-patch; keep the read-only rule only where a bad patch has real cost.

**Prompt quality — three real prompts from this period, critiqued:**
1. *"which drift? Ship the patches. And tell me which questions are waiting for answers?"* (10 Jul) — your best prompt of the quarter. Specific, verifiable, closure-oriented. More of this.
2. *"I said skip the lubes abort skip it from every file just as ITUK pricing dispute can you do that and confirm it"* (10 Jul) — ambiguous scope over real money. "Skip the lubes" could have deleted the record of a signed €37K/year revenue channel. It only went right because Claude stopped to ask. When an instruction touches deletion or money, one extra clause ("keep the UMI/Shell record, kill the BESCO ambition") costs you five seconds and removes the coin-flip.
3. *"fix all dashboard but there will be some with old data so do the excercise well anon"* (12 Jul) — "do the exercise well" is a hope, not an instruction. It worked out because the session inferred the right standard, but the GPS v3b→v3c rebuild in June came from exactly this prompt shape: acceptance criteria arriving after the build ("this is key, it should be in method, why is it empty?"). The pattern is improving — the GPS incident hasn't repeated at that scale — but it's not gone.

**Workflow integration — the three seams that leak time, ranked:**
1. **Windows Task Scheduler.** Claude can edit the XML but not re-register the task; every scraper fix dies at "needs your re-import." This seam cost six weeks on the tender scraper. Cheapest fix: a single `register_tasks.ps1` in `04_tools/` that re-imports every task XML in one double-click, so the manual step is one action, always the same, instead of a bespoke instruction each time.
2. **The app-level CLAUDE.md.** Unreachable from any session, so memory corrections land everywhere except the one file injected into every conversation. Either edit it manually now, or slim it down to stable facts only (people, terms, preferences) and move all volatile project status into `ISZE/05_memory/` where sessions can actually maintain it. The second option removes the failure mode permanently and is the better fix.
3. **SAP exports.** Genuinely manual, nothing to automate from this side — but the monitors should stop counting closed-period files (Sales CY25) toward staleness, which was fixed for that file this week after your pushback. Done, just noting it as the third seam.

**Memory/context sync — better, worse, or unchanged?** Split verdict, and the split is the finding: the *workspace* memory layer (`05_memory/`) is now in its best state in the series — decisions logged, dead projects deleted, reconciliation memos filed, files dated this week. The *injected* layer (app CLAUDE.md) is unchanged since ~March and now actively contradicts the workspace layer on five facts. And the `isze-context` skill was found stale on 5 Jul (0.3% figure, dispute framing) with no evidence since that it's been corrected — check it. The system isn't drifting uniformly; it's split into one layer that heals and two that can't heal themselves.

**The recurring pitfall — supports, complicates, or contradicts?** Complicates, for the first time. The "analysis outruns closure" diagnosis held for runs 1–12 but this week's evidence shows closure happening at normal speed *once the asks were formatted as decisions*. The refined diagnosis: you don't avoid closing loops, you avoid *finding* them — they were buried in 2,000-word reports. Fix the format, and the behavior followed within days. Accordingly, future runs of this task should end with a numbered "waiting on you" list, nothing else in the final section.

## Bottom line

Best week in the series: the tender scraper, price-file canon, PMS baseline, and dead-project cleanup all closed. The upgrade request for this very task (adding the Claude-usage layer, done 18 Jul) is itself the right instinct — reviewing the tool usage, not just the work. Two things remain that no automated run can ever fix for you, both ~10 minutes, both flagged for ~10 weeks: edit or slim the app-level CLAUDE.md, and run the Task Scheduler re-import (partially done — verify KS/discount scrapers are registered, not just tender).

### Waiting on you (nothing else)
1. App CLAUDE.md: fix the five stale facts, or approve moving volatile status out of it entirely.
2. Verify KS + discount scraper tasks are registered in Task Scheduler (tender is confirmed working as of 16 Jul).
3. Delete/disable the three dead scheduled tasks (`autodoc-monthly-refresh` — still enabled, `isze-tender-dashboard-refresh`, `isze-weekly-intel-brief`).
4. Check `isze-context` skill for the stale 0.3%/dispute framing flagged 5 Jul — one read, one edit.
5. Decision: may the scraper healthcheck self-apply low-risk patches, per scraper? Yes/no per scraper is enough.

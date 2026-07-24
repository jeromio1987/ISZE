# X bookmarks brief — 24 Jul 2026

Source: 50 recent bookmarks via `Projects/twitter-mcp` (`_bookmarks_50.json`).  
Companion to June loops addendum (`feedback_jerome_2026-06_loops-addendum.md`) and run #13 (`feedback_jerome_2026-07-18.md`).

## Verdict

Same aspiration as June — **loops, graphs, unattended agents, cheaper execution** — but the stack has moved. You’re no longer “bookmarking without infrastructure”: Hydra, graph-engineering skill, scheduled monitors, and question-shaped feedback already exist. The gap is no longer *awareness*; it’s **verifiers + permission to close** (self-patch, Teach-a-Skill for recurring desktop work, one cost tier for routine jobs).

Noise filtered out: health/visceral-fat, ADHD, Naval sales podcast, Radiant infra, empty posts, pure hype trading clips.

---

## Theme clusters (what you actually save)

| Cluster | Signal posts | Relevance |
|---|---|---|
| **Loops → graphs / memory** | codila (Ng PDF, “skipping Graphs”), Buzzoni (6 patterns), Codez (Boris loops) | High — agent memory + workflow wiring |
| **Teach Claude a Skill** | Miles Deutscher + @claudeai (screen → reusable skill) | High — encode ISZE/desktop rituals |
| **Verifier before /loop** | Alpha Batcher quoting Karpathy | High — stops babysitting *and* runaway loops |
| **Stop babysitting** | rody / Sid Bidasaria; Miles `/goal` | High — same June theme |
| **Cost / compound models** | CJ Zafir tiering, Brick, OpenRouter Fusion, Kimi-in-Claude, Minimax loops | Medium — save frontier for plan/review |
| **CLAUDE.md as OS** | Karpathy CLAUDE.md leak posts | Medium — you have CLAUDE.md; quality/staleness still the issue |
| **Governance / permissions** | Chubby × Arcade (what agents may do + proof) | Medium — matches self-patch decision |
| **Second brain / Fable** | Miles Deutscher | Low–med — you already have `05_memory` |
| **Side-product / trading bots** | Boxmining directory, prediction-market bots | Low for ISZE; optional for investing/myPENS |

---

## Mapped to your buckets

### Already doing (don’t re-learn from Twitter)

- Scheduled estate indexed in `ISZE/00_docs/AUTOMATION_REGISTER.md`; job bodies under `Documents/Claude/Scheduled/<job>/SKILL.md`
- Scraper healthcheck **propose-only by design**: `…/isze-scraper-healthcheck-autofix/SKILL.md` → `proposed_patch.diff` / `manual_review_required.md` (never edits live scrapers)
- Hydra (tiered models) + Cursor `graph-engineering` + `/loop` skill; ISZE workflow `ISZE/.claude/workflows/dashboard-html-audit.js`
- Question-shaped “waiting on you” format (run #13 — this *did* unlock closure)
- Workspace memory layer `ISZE/05_memory/` is the healable store; feedback archive under `briefs/feedback_history/`

### Gaps the bookmarks point at (actionable)

| Bookmark idea | Where it lands | Concrete move |
|---|---|---|
| **Verifier before loop** | healthcheck, memory-review, any `/loop` | Write “done = …” *before* run (freshness, row counts, harness PASS). Reuse graph-engineering’s independent-verify pattern. |
| **Self-patch permission** | Same healthcheck skill + `ISZE/DECISIONS.md` | Allowlist 1–2 low-risk scrapers Claude may apply; keep tender/sales propose-only. Otherwise homework-by-design forever. |
| **Teach Claude a Skill** | Claude Desktop → Record a skill | Not operationalized yet (skills exist ad hoc). Record: scraper triage / GPS dashboard QA / myPENS release checklist. |
| **Graphs = memory** | Overlapping weekly monitors | Merge into one “open loops” digest (Jun/Jul feedback; still separate reports). |
| **Cheap model for execution** | Hydra already exists | Point *routine* scheduled jobs at the cheap tier; frontier only for plan/review. |
| **Karpathy CLAUDE.md** | Injected app CLAUDE.md still volatile/stale | Apply pending fixes (`ISZE_CLAUDE_memory_fixes_2026-07-21.md`); slim stable facts in CLAUDE.md, volatile status only in `05_memory/`. Also refresh stale `isze-context` skill. |
| **Agent permissions / proof** | Arcade-style + self-patch | Log what changed, by which task, with revert path when allowlist applies. |

### Projects-specific

- **ISZE** — self-patch decide + CLAUDE.md/`isze-context` refresh + merge monitors; delete dead scheduled dirs (`isze-weekly-intel-brief`, `isze-tender-dashboard-refresh` cleanup still open).
- **myPENS** — Phases 1–2 done; 3–6 partly open. Teach-a-Skill for release checklist; `/api-auth-audit` named in graph-engineering skill but no workflow under `Projects/mypens` yet (only ISZE has the workflow file).
- **investing / cockpit** — second-brain / indicator bookmarks optional; not this week.
- **Agent OS** — don’t add more loop frameworks; close the ones above.

---

## Top 5 (do these; ignore the rest of the feed)

1. **Decide scraper self-patch allowlist** (1–2 scrapers) — closes the June→July open loop.
2. **Add a verifier block** to healthcheck + memory-review outputs (“PASS if … / FAIL if …”) before any auto-apply.
3. **Slim/fix injected CLAUDE.md** + refresh `isze-context` (pending patch list already exists).
4. **Record one Teach Claude a Skill** for the ritual you re-explain most.
5. **Merge overlapping weekly monitors** into one “open loops” brief; delete/retire dead scheduled jobs.

---

## Waiting on you

**Decided / shipped 2026-07-24:** self-patch allowlist named (KS / Tranzparts / TMC / Mekonomen / Auto365 URL/selector only; Tender propose-only) in `DECISIONS.md`; package shipped — healthcheck allowlist gates, memory-review verifiers, `isze-weekly-open-loops`, teach-skills drafts under `ISZE/00_docs/teach-skills/`, dead scheduled dirs removed.

Still open (manual / Claude Desktop only):

1. **Record teach-skills** in Claude Desktop (drafts already under `ISZE/00_docs/teach-skills/`).
2. **Enable `isze-weekly-open-loops`** in Claude Desktop scheduled tasks UI (and confirm updated healthcheck / memory-review skills are picked up).
3. **Ship AppData CLAUDE.md** from `ISZE_CLAUDE_memory_fixes_2026-07-21.md` (path outside workspace).

# Efficiency eval — Multitask + close-the-loops package (24 Jul 2026)

Evidence: this Cursor chat transcript `143cfa9f-…` (timestamps UTC+2), bookmark brief, `00_INDEX.md` pattern, `DECISIONS.md` / `AUTOMATION_REGISTER.md` / Scheduled skills as of ~06:16.

**Not a sales pitch.** Numbers are inferred from message timestamps and file mtimes; treat ranges as order-of-magnitude.

---

## Session clock (what actually happened)

| Phase | Clock | His job | Agent job |
|-------|-------|---------|-----------|
| Explore options (API / scrape / MCP) | 05:33–05:44 | ~4 short turns | Serial answers |
| Install + wire twitter-mcp | 05:44–05:58 | Login in headed Chrome (~14 min hands-on) | Commands + configs |
| Pull 50 bookmarks + mapped brief | 06:01–06:03 | “yes please” | Pull + write; **scout subagent** in parallel for estate gaps |
| “What can you implement?” → full yes | 06:04–06:05 | One approval message (allowlist + package) | Plan → execute |
| Package implementation | 06:05–06:14 | Idle / elsewhere | Parent + **2 subagents** (open-loops skill, teach-skill drafts) |
| “Start multitasking” | 06:14 | Freed attention; immediately asked for this eval | Background finish: register, DECISIONS polish, brief wrap, logs |
| Docs settle | ~06:14–06:16 | Reading / other chat | File mtimes land |

**Wall to package mostly done:** ~41 min from first question (05:33→06:14).  
**His attention events:** ~12–13 turns; only ~2–3 were “babysit the build” — the rest were discovery + one decision batch.  
**His hands-on non-chat work:** ~14 min (X login). That would exist under any approach that needs a browser session.

---

## A. Multitask Mode / forked background agents

### What becomes parallel vs serial

| Serial (classic foreground) | Parallel (this session) |
|-----------------------------|-------------------------|
| Wait for each doc/skill rewrite before next | Teach-skill drafts ∥ open-loops skill ∥ parent healthcheck/memory edits |
| Stay in chat until register + DECISIONS + wrap done | Fork remaining docs; start a *different* ask (this eval) in the same minute |
| One scout-or-write path | Scout estate gaps while bookmarks pull finishes |

Still **serial by nature:** API-vs-MCP decisions, login, allowlist choice, anything that needs his judgment.

### Time saved for *him* vs tokens/cost

| Effect | Who benefits | This session |
|--------|--------------|--------------|
| Wall-clock while he does something else | **Him** | Multitask at 06:14: remaining docs finished in ~1–2 min of agent time; he spent that window on a new question instead of watching. Modest win *today* because leftovers were thin. |
| Parallel subagents during 06:05–06:14 | **Him + wall** | Larger win: open-loops (~4 min) + teach drafts (~2–3 min) overlapped parent work → package wall ~9 min instead of ~20–30 serial. |
| Token/cost | **Bill** | Multitask does **not** cut tokens; it can **raise** them (extra agent context, duplicate exploration). Savings here are attention and calendar, not API spend. Cheap-model routing (B) is the cost lever. |

### Overhead / risks (real in this chat)

1. **Coordination / incomplete handoff** — Parent said it would finish DECISIONS + register in background; those files *did* update (~06:15), but a thin fork transcript (`a566…`) shows only “continue executing” with no visible tool trail in that file. Trust the artifacts, not the ping narrative.
2. **Duplicate work** — Scout enriched the brief *after* a first write; harmless but double-touch. Parallel agents reading the same Scheduled folder can step on each other if both edit one SKILL.
3. **“Ping when done” latency** — He asked for efficiency eval *immediately* after enabling multitask; useful, but if the background job had been a 30-min build, notification lag + context switch cost would matter more than the ~2 min leftover here.
4. **Attention fragmentation** — Two background tracks (finish package + this eval) while Multitask is on: fine for independent docs; bad if both edit the same policy files.

### Rough compare: serial foreground vs multitask for the *implementation package*

Scope after approval (06:05): verifiers + allowlist healthcheck, memory-review gates, open-loops skill, teach-skill drafts, DECISIONS, AUTOMATION_REGISTER, dead-dir cleanup, `analyze_bookmarks.py`, myPENS `api-auth-audit.js`, brief wrap.

| Mode | His attention (estimate) | Agent wall (estimate) |
|------|--------------------------|------------------------|
| (1) Fully serial foreground, he waits each step | ~15–25 min watching / nudging | ~35–55 min |
| (2) Parallel subagents + short multitask finish (actual shape) | ~2–5 min (approve + “start multitasking”) | ~9–15 min |
| Delta | **~10–20 min of his time** | **~20–35 min wall** |

Caveat: discovery/setup (05:33–06:01) was mostly serial either way (~25 min wall, ~10 min of his Q&A + 14 min login). Multitask does not shrink “figure out MCP.”

---

## B. Close-the-loops package vs bookmark aspiration

June loops addendum: bookmarks = aspiration; healthcheck still homework-by-design. July 18 (#13): closure unlocked when asks became numbered decisions — but self-patch, merged monitors, dead jobs still open. **Today closed several of those in one approval.**

| Mechanism | Efficiency vs before | Maps to feedback pattern |
|-----------|----------------------|--------------------------|
| **Propose-only → allowlisted self-patch** (+ verifiers, `applied_patches_log.md`) | Each future allowlisted URL/selector fix: less “read diff → apply → re-run” homework (often ~5–15 min of his time when it fires). Tender still propose-only = correct risk trade. | Directly attacks “analysis outruns closure” / homework-by-design (June→#13→bookmarks Top 5 #1–2). |
| **CHEAP vs FRONTIER routing** | Cost lever on *recurring* jobs, not this chat. If scheduler honors tiers: routine runs avoid frontier burn (bookmark lore ~50%; treat as **aspiration until measured**). Hydra already existed — this is labeling the estate, not inventing tiering. | Cost/compound-models cluster; stops paying Opus for Sunday hygiene. |
| **Merged open-loops digest vs 4 reports** | Monday read: ~1 scannable brief vs health + freshness + memory + UIO. Rough: **~10–15 min → ~3–5 min** if he actually stops opening the four. | Index pattern: loops buried in long reports; #13 said format unlocks closure — one digest is the format fix for monitors. |
| **`analyze_bookmarks.py` vs manual paste** | Next pass: scripted pull + bucket stub vs session archaeology / Chrome MCP. Setup cost paid today; marginal cost drops hard. | Turns bookmark aspiration into a repeatable input to the same feedback archive. |

**Still not closed by this package:** injected AppData `CLAUDE.md` (outside workspace — still manual), Claude Desktop must actually *enable* `isze-weekly-open-loops`, Teach-a-Skill drafts still need a Desktop “Record” pass, first real auto-apply not proven yet (log empty).

Shipped vs pending snapshot (~06:16): allowlist DECISIONS ✅, healthcheck/memory skills ✅, open-loops skill ✅, dead dirs gone ✅, teach drafts ✅, register + CHEAP/FRONTIER ✅, analyzer + myPENS workflow ✅, brief “waiting on you” mostly struck ✅ — remaining: AppData CLAUDE.md + confirm Desktop schedule pickup.

---

## C. Honest bottom line

### When this way is clearly more efficient

- Multi-file **implementation packages** with independent slices (skills ∥ docs ∥ scripts) after **one** decision batch.
- Recurring estate work where **verifiers + allowlist** remove him from the loop.
- Bookmark / monitor **synthesis** he would otherwise re-read across four artifacts.
- Any stretch where his scarce resource is **attention**, not token budget.

### When it is NOT

- Small asks (“how do I get API access?”) — fork overhead > work.
- Decisions still on him (allowlist contents, money/deletion scope, AppData CLAUDE.md).
- MCP broken / red in Cursor (today: bookmarks via direct Playwright script, not live MCP tools) — parallel agents don’t fix a dead connector.
- Single-file policy edits two agents might both touch.
- Measuring “efficiency” as lower API spend — multitask often costs **more** tokens.

### Recommendations (maximize gain, limit chaos)

1. **Batch decisions once, then go dark** — Keep the #13 / today pattern: numbered “waiting on you,” one reply covering the batch, then Multitask for the rest. Don’t fork until the allowlist/scope is written down.
2. **Partition file ownership when parallel** — Parent owns `DECISIONS.md` + register; subagents own disjoint skill paths. No two agents edit the same SKILL.
3. **Prefer multitask for leftovers ≥ ~10 min** — Today’s 1–2 min doc polish barely paid the context switch; use fork when remaining work is clearly longer than a coffee.
4. **Measure CHEAP routing on one Sunday run** — Compare token/model on healthcheck before claiming the ~50% bookmark myth; label without measurement is theater.
5. **Close the two seams multitask cannot** — (a) edit injected CLAUDE.md once from the 21 Jul patch list; (b) confirm Desktop scheduled pickup for open-loops + updated healthcheck — otherwise the package is files on disk, not a loop.

---

## One-line verdict

**For this package:** ~2–3× faster agent wall and ~10–20 min less of his attention vs serial babysitting; **ongoing** win is self-patch + one Monday digest (hours/month if jobs fire), not Multitask itself. **Multitask is an attention shifter; the package is the efficiency product.**

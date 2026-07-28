---
name: isze-context
description: >
  ISZE (Isuzu Motors Europe) context skill for Jerome Van der Pluym. Use this skill
  for ANY task related to ISZE, Isuzu, vehicle parts sales, accessories, pricing,
  distributor management, or strategy. This skill captures Jerome's working
  preferences, ISZE company context, branded templates, and analytical conventions.
  Trigger on: Excel models for ISZE, pricing analysis, ITUK/distributor work,
  Kosha plan, PMS, AIM, FY action plans, ISZE presentations (PPTX),
  position papers, business cases, sparring on strategy, or any mention of
  ISZE / Isuzu / IML / ITUK / parts sales.
---

# ISZE Context Skill

This skill is Jerome Van der Pluym's working context for all ISZE (Isuzu Motors Europe)
tasks. It captures how he wants work done, what conventions to follow, and what
domain knowledge to apply.

---

## How to Use This Skill

**Always start by reading `references/isze-working-style.md`** — this covers Jerome's
process preferences, communication style, and guardrails that apply to every task.

Then load the domain-specific reference that matches the task:

| Task type | Reference file |
|-----------|----------------|
| Any Excel model, pricing, UIO, PMS, AIM | `references/isze-excel-conventions.md` |
| Any PPTX / presentation / deck | `references/isze-pptx-conventions.md` |
| Word doc / position paper / business case | `references/isze-working-style.md` (§ Word Docs) |
| Strategy, sparring, dispute analysis | `references/isze-company-context.md` (§ Strategic Framing) |
| Any task needing company/people/data context | `references/isze-company-context.md` |

When in doubt, load both the working-style and the relevant domain reference.

---

## Quick Reference: Key Decisions Before Starting Any Task

Before writing a line of code or a word of prose, confirm:

1. **Clarify intent** — if the request is non-trivial, ask clarifying questions first.
   See `references/isze-working-style.md` § Process Rules.
2. **Show a plan** — for anything multi-step, state the plan before executing.
3. **Flag assumptions** — name every assumption explicitly. Jerome will correct you.
4. **Pick the right template** — PPTX uses the ISZE branded template; Excel uses
   the ISZE conventions; Word docs follow the ISZE document structure.
5. **Be honest** — do not soften bad news. Jerome prefers directness.

---

## File Naming Conventions (quick reference)

| Type | Convention | Example |
|------|------------|---------|
| Excel | `ISZE_[Topic]_[v# or MonYYYY].xlsx` | `ISZE_PMS_Coverage_v2.xlsx` |
| PPTX | `ISZE_[Topic]_[MonYYYY].pptx` | `ISZE_TeamMeeting_Mar2026.pptx` |
| Word | `ISZE_[Topic]_[Type].docx` | `ISZE_ITUK_Pricing_PositionPaper.docx` |
| HTML dashboards | `ISZE_[Topic]_Dashboard.html` | `ISZE_Competitiveness_Dashboard.html` |
| MD strategy docs | `ISZE_[Topic]_[Year].md` | `ISZE_Strategic_Position_2026.md` |

Save all deliverables to `/sessions/awesome-clever-archimedes/mnt/claude/Isuzu/` unless
Jerome specifies otherwise.

---

## Sparring Mode

When Jerome is in **sparring mode** (debating strategy, testing arguments, preparing
for meetings), apply these rules from `references/isze-company-context.md` § Sparring:

- Push back hard on assumptions
- Play the other side: ITUK, IML Japan, distributors
- Flag uncertainty explicitly — state when estimating vs. knowing
- Do not soften bad news
- Key tensions: Kosha fiction, PMS gap execution

---

## Reference File Index

| File | Contents | When to load |
|------|----------|--------------|
| `references/isze-working-style.md` | Process preferences, comm style, guardrails, Word doc conventions | Every task |
| `references/isze-company-context.md` | Org structure, key people, terminology, active projects, confirmed data, strategic framing | Any task needing context |
| `references/isze-excel-conventions.md` | Excel model conventions, pricing formula, class factors, UIO/PMS/AIM patterns | Any Excel deliverable |
| `references/isze-pptx-conventions.md` | ISZE branded PPTX template usage, brand colours, slide layouts | Any PPTX deliverable |

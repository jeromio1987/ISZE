# AI stack — tier protocol & tool routing

**Agent sync:** 2026-06-13  
**Full memo:** [`AI_STACK_ARCHITECTURE_Apr2026.md`](AI_STACK_ARCHITECTURE_Apr2026.md) (Apr 2026 audit + workflow detail; paths updated Batch 3)

---

## Four-tier data architecture

```
TIER 0 — ISZE secure zone (NEVER touched by Claude or GPT)
  SAP, Power BI, ISZE network drive

TIER 1 — Local working folder ($env:ISZE_ROOT)
  Exports, dashboards, scripts, 05_memory/
  → Claude reads/writes here directly
  → GPT Enterprise cannot reach this

TIER 2 — GPT Enterprise Knowledge
  08_gpt/2_KNOWLEDGE_FILES/*.md (+ templates)
  → Manual upload; monthly refresh

TIER 3 — Published layer
  GitHub Pages HTML (deploy-side ../Data/ URLs), shareable URLs
```

**Design choice:** Context Pack (Tier 1 → Tier 2) is the **single synchronisation point**. Sync context, not raw data.

---

## Claude vs GPT — routing guide

| Task | Tool | Why |
|------|------|-----|
| Multi-file Excel, xlsx skill | **Claude** | Reads local files directly |
| HTML dashboards build/debug | **Claude** | Edits in place (`02_dashboards/`) |
| Python scripts / automation | **Claude** | Write, test, save locally |
| Long memos (3+ pages) | **Claude** | Long context, docx output |
| Strategic sparring offline | **GPT** | Context pack on phone |
| Quick SPA / single-PN check | **GPT** | Uploaded subset, fast |
| Meeting prep from scratch | **Claude** | `05_memory/` + briefs + projects |
| Sensitive (Kosha framing, personnel) | **Claude local only** | Never upload |

**Rule:** task needs >1 local file or produces a file → **Claude**. Self-contained chat, not at laptop → **GPT**.

---

## Context Pack sync protocol

**What:** `08_gpt/2_KNOWLEDGE_FILES/` + `3_TEMPLATES/`

**Cadence:**

- Monthly — first working Monday
- Ad-hoc — pricing change, project status, new confirmed data, Kosha revision
- FY boundary — full audit April + October

**Workflow:**

1. Claude diffs MD files from `05_memory/` + project files
2. Review + approve
3. Log in `08_gpt/CHANGELOG.md`
4. Re-upload to each Custom GPT Knowledge

---

## FACTS ↔ memory ↔ GPT

| Layer | Role |
|-------|------|
| `01_data/derived/metrics_snapshot.json` + green verify | Headline KPIs — wins always |
| `FACTS.md` | Human pins + pricing anchors |
| `05_memory/projects/*.md` | Programme status — never overrides KPIs |
| GPT knowledge files | Portable sparring — re-upload after FACTS changes |

See `00_docs/REFERENCE.md` for full reconciliation table.

---

## Governance (non-negotiable)

1. Nothing leaves Tier 1 without content review before GPT upload
2. Never upload: full PR00 list, line-level SPA, unreleased Kosha plans, personnel, active pricing correspondence
3. Tag sensitivity in MD front-matter where applicable
4. Audit trail: `08_gpt/CHANGELOG.md`, `05_memory/briefs/`, git commits via deploy scripts

---

## Briefs location

Weekly and analyst briefs: **`05_memory/briefs/`** (was scattered under `AI_Briefs/`, `Isuzu/AI_Briefs/`).

Scheduled skill `isze-weekly-intelligence-brief` writes here.

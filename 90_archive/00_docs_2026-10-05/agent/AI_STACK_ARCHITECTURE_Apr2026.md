# ISZE AI Stack — Architecture & Daily Workflow

> **Tier protocol (concise):** [`00_docs/agent/AI_STACK.md`](AI_STACK.md) · **Map registry:** [`00_docs/MAP_REGISTRY.yaml`](../MAP_REGISTRY.yaml)  
> **Path update (2026-06-13 Batch 3):** numbered folders + `$env:ISZE_ROOT`. Legacy names below in the Apr 2026 audit table are preserved for historical context — current paths: `05_memory/`, `02_dashboards/`, `04_tools/`, `08_gpt/`, `07_deploy/Master Dashboard/`.

**Author:** Jérôme Van der Pluym · **Date:** 21 April 2026 · **Scope:** Internal working reference (not for external distribution)

---

## TL;DR

1. **The framing "GPT Enterprise has folder access, Claude doesn't" is wrong in practice.** Neither has direct access to the ISZE shared network drive or SAP. Both are fed curated MD files. The real access split is: **Claude/Cowork can read your local `C:\Users\jerom\Desktop\claude` folder live; GPT Enterprise cannot — it only sees what you manually upload as Knowledge.**
2. **Use each tool for what it's actually good at.** Claude for multi-file local work, dashboards, Excel/Python automation, long memos, deploy scripts. GPT Enterprise for portable sparring, quick calcs against uploaded files, on-the-go email drafting, offline-from-laptop work.
3. **Stop trying to integrate them.** They are not integrable at the API level from your position. You are the bridge. That is fine — and it's the only compliant posture given that neither tool is officially sanctioned on ISZE's stack.
4. **The single file that makes this work is the Context Pack** (`08_gpt/2_KNOWLEDGE_FILES/*.md`). Keep it canonical, update monthly, re-upload to GPT in one batch. That's the sync protocol.
5. **Do not attempt a live Power BI ↔ GPT integration.** It requires admin rights you don't have, and it would expose distributor data to a non-sanctioned LLM. The manual "BVDB publishes PBI → you export → Claude analyses locally" path is slower but defensible.

---

## Reality check — what you've already built (audit, 21 Apr 2026)

| Layer | Artefact | Status |
|---|---|---|
| GPT knowledge | `08_gpt/2_KNOWLEDGE_FILES/` (6 MDs) | ✅ Built, Apr 2026 |
| GPT prompts | `08_gpt/1_CUSTOM_GPT_SKILLS/skill.md` + 4 `.skill` files | ✅ Built |
| GPT templates | `08_gpt/3_TEMPLATES/` (Email, Analysis Frameworks) | ✅ Built |
| Context briefing | `GPT_Enterprise_ContextBriefing_Apr2026.md` | ✅ Current |
| Data map | `GPT_Enterprise_DataMap_Apr2026.xlsx` | ✅ Current |
| Vector store (older) | `GPT_VectorStore/` — business_rules, pricing_rules, GPS spec | ⚠️ Drifted vs context pack |
| Local memory for Claude | `05_memory/` (projects, glossary, briefs) + CLAUDE.md | ✅ Active |
| Dashboards | 11 HTMLs under `02_dashboards/` incl. MASTER_DASHBOARD | ✅ Live |
| Deploy pipeline | `07_deploy/Master Dashboard/deploy.sh` → GitHub Pages | ✅ Set up |
| Tools | `04_tools/` — SPA Optimizer, Tender Monitor, discount-scanner, autodoc_scraper | ✅ Built |
| Python automation | `tender scraper/` — scraper + dashboard builder | ✅ Works |
| Weekly AI briefs | `05_memory/briefs/weekly_Wxx_2026.txt` | ✅ Running |

**Honest observation:** You already have 80% of the architecture. What's missing is not more tools — it's a **written protocol** for how Claude, GPT Enterprise, the local folder, Power BI, and the published dashboards relate. The rest of this memo is that protocol.

---

## The four-tier data architecture

```
┌─────────────────────────────────────────────────────────────┐
│ TIER 0 — ISZE secure zone (NEVER touched by Claude or GPT)  │
│  • SAP (SD, PR00 / ZPR1)                                    │
│  • Power BI workspace (BVDB)                                │
│  • ISZE shared network drive                                │
└─────────────────────────────────────────────────────────────┘
                          ↓  (you export — manual or scheduled)
┌─────────────────────────────────────────────────────────────┐
│ TIER 1 — Local working folder (C:\Users\jerom\Desktop\claude)│
│  • Exported Excel/CSV from SAP & Power BI                   │
│  • Dashboards, tools, Python scripts                        │
│  • memory/, GPT_Enterprise/, ISZE/, Isuzu/                  │
│  → Claude/Cowork reads & writes HERE directly               │
│  → GPT Enterprise cannot reach this                         │
└─────────────────────────────────────────────────────────────┘
                          ↓  (you upload — monthly + on change)
┌─────────────────────────────────────────────────────────────┐
│ TIER 2 — GPT Enterprise Knowledge                           │
│  • The 6 context-pack MDs + 2 templates                     │
│  • Small CSVs when useful (never the 164k-row price list)   │
│  → GPT reads as Knowledge files within Custom GPTs          │
└─────────────────────────────────────────────────────────────┘
                          ↓  (deploy.sh → git push)
┌─────────────────────────────────────────────────────────────┐
│ TIER 3 — Published layer (GitHub Pages, private repo)       │
│  • MASTER_DASHBOARD.html and other HTML views               │
│  • Reachable via URL, shareable with ITUK/IML when useful   │
└─────────────────────────────────────────────────────────────┘
```

**Key design choice:** the Context Pack (Tier 1 → Tier 2) is the **single synchronisation point**. You don't sync data, you sync *context*. Data stays local.

---

## Claude vs GPT Enterprise — what each is actually good for

This is the honest mapping. Use it as a routing guide.

| Task type | Tool | Why |
|---|---|---|
| Multi-file Excel work (xlsx skill, formulas, pivots) | **Claude** | Reads files directly from Desktop, uses xlsx skill, produces real .xlsx output |
| HTML dashboards (build, update, debug) | **Claude** | Can read 1,500+ line HTML files and edit in place |
| Python scripts / automation (tender scraper, etc.) | **Claude** | Can write, test in sandbox, save to local folder |
| Long memos (position papers, IML briefings, 3+ pages) | **Claude** | Longer context, xlsx/docx skills, file output |
| Strategic sparring, devil's advocate | **Either** — GPT preferred when offline / on phone | Context pack enables GPT to push back meaningfully; Claude has more local context |
| Pricing calculations (basket impact, FX decomposition) | **Claude for full list; GPT for single-PN quick check** | Claude handles 164k-row file; GPT handles uploaded subset |
| Email drafting in Jerome's style | **Either** — GPT slightly faster, both well-calibrated | Both have `Jerome_Working_Style.md` |
| Quick SPA anomaly flagging | **GPT (Data Analysis GPT) with uploaded file** | Works on phone, fast, contained scope |
| Meeting prep from scratch | **Claude** | Can pull from memory/, recent AI_Briefs, active project files in one pass |
| Code review / debugging dashboards | **Claude** | Sees the HTML/JS in full |
| Reading a new document (PDF, contract) you can paste | **Either** | No local access needed |
| Sensitive content (Kosha internal framing, personnel) | **Claude, local only — never uploaded** | GPT Enterprise is still external to ISZE |

**Rule of thumb:** if the task involves reading >1 local file or producing a file, use Claude. If the task is self-contained within a chat and you're not at your laptop, use GPT.

---

## Context Pack — the sync protocol

**What the Context Pack is:** the 6 MD files in `GPT_Enterprise/2_KNOWLEDGE_FILES/` + the 2 templates in `3_TEMPLATES/`. They are the shared source of truth between Claude (which reads them live) and GPT Enterprise (which gets them uploaded).

**Cadence:**
- **Monthly refresh** — first working Monday of each month. Claude regenerates the context pack from memory/ and current project files. You upload the delta to each Custom GPT.
- **Ad-hoc refresh triggers** — when any of these happen:
  - Pricing change (new FX, new BP_JPY, new class factor)
  - Project status change (Active Projects table)
  - New confirmed data point (UIO refresh, AIM percentage, pricing update)
  - Kosha plan revision
- **FY boundary refresh** — full audit of all 6 MDs in April + October.

**Concrete monthly workflow:**
1. Open Cowork. Say: "refresh context pack from latest memory/ and project files."
2. Claude diffs each MD file, proposes updates, writes new versions.
3. You review the diff, approve.
4. Claude writes a CHANGELOG entry in `GPT_Enterprise/CHANGELOG.md` (new file — recommended).
5. In ChatGPT Enterprise, for each of the 4 Custom GPTs: Configure → Knowledge → delete old versions → upload new.
6. (Optional) Claude can bundle the updated files into a new `GPT_Enterprise_Kit_YYYYMM.zip` so you always have a dated snapshot.

**Expected time per month:** 15–20 minutes. Most of it is the upload clicking in ChatGPT.

---

## Data flow for the key projects (routing table)

| Project | Primary data source | Who extracts | Where it lands | Who analyses |
|---|---|---|---|---|
| Pricing 2026 (ITUK) | SAP PR00, IE40 price list | You (manual SAP export) | `ISZE/Master Dashboard/` and `Isuzu/isuzu pricing engine/` | **Claude** (full price list) + **GPT Pricing Analyst** (quick checks) |
| Competitiveness Dashboard | Eucon + IE40 | You | `ISZE/Dashboards/ISZE_Competitiveness_Dashboard.html` | **Claude** (rebuild), GPT reads published HTML URL |
| UIO Tool | DVLA + distributor returns | You | `ISUZU_UIO_Overview_2026_v18.xlsx` | **Claude** (xlsx skill, heavy compute) |
| AIM | Sales classification + UIO | You + BVDB | `AIM_CY2025_Analysis.xlsx` | **Claude** (cross-joins), **GPT** for strategic interpretation |
| PMS Coverage | ITUK extracts | You | `ITUK_PMS_Analysis_Apr2026_v7_reclassified.xlsx` | **Claude** (capture rate maths) |
| Lubricants BC | Volume model | You | `ISZE_Lubricants_BC_Rebuilt_v2.xlsx` | **Claude** (xlsx), **GPT** for IML pitch language |
| Weekly AI Brief | Claude-generated from memory/ | **Claude** (scheduled or on-demand) | `ISZE/AI_Briefs/weekly_Wxx_2026.txt` | **Claude** writes, **GPT** reads during offline sparring |
| Tender scanning | `tender_scraper.py` | **Claude** runs the script | `tenders_output.xlsx`, `isze_dashboard.html` | **Claude** |

---

## Governance boundaries (non-negotiable)

Since neither tool is officially sanctioned by ISZE/IML on the company stack, the governance burden is on you. Hard rules:

1. **Nothing leaves Tier 1 (Desktop) without a content review.** Before you upload anything to GPT Enterprise knowledge, ask: is this fine if screenshotted externally?
2. **Never upload to external AI:**
   - The full 164k-row PR00 price list (commercially sensitive, and too large anyway)
   - Distributor-identifiable SPA details at line-item level
   - Unreleased IML Kosha plans or MTG minutes
   - Personnel data or salaries
   - Active legal/pricing correspondence with counterparties
3. **Sensitivity tag in MD files.** Add a YAML front-matter tag to each file:
   ```
   ---
   sensitivity: internal-only  # options: public | internal | confidential | restricted
   upload-to-gpt: false
   ---
   ```
   Claude should refuse to include `confidential` or `restricted` material in Context Pack updates. **Flagging this as an assumption** — you need to tell Claude this is the rule; the tag alone doesn't enforce anything.
4. **No trade actions.** Neither tool is used to send emails, execute price changes in SAP, publish to distributors without you clicking send yourself. This is already your pattern — make it explicit.
5. **Audit trail.** `GPT_Enterprise/CHANGELOG.md` logs every context-pack change. `ISZE/AI_Briefs/` retains weekly briefs. `deploy.sh` commits to git. This is your paper trail if anyone asks.
6. **Not sanctioned stack — say so if asked.** If IT or IML ever asks what tooling you use: honest answer. ChatGPT Enterprise licence (confirm: yours, your team's, or ISZE-wide?) + Anthropic Claude via Cowork, both running against MD files you maintain, no direct access to company systems. That's a defensible position.

---

## Power BI — the integration question, answered honestly

**You asked about integrating GPT Enterprise with Power BI. Honest answers:**

1. **Claude / Cowork ↔ Power BI: no direct integration possible in your setup.** Cowork has no MS Fabric / Power BI connector available to you right now. Workaround: export from Power BI to Excel, land in Desktop folder, Claude reads.
2. **GPT Enterprise ↔ Power BI: technically possible via GPT Actions + Power BI REST API, but requires:**
   - Azure AD app registration (you likely don't have admin rights)
   - Service principal with Power BI workspace access (BVDB would need to grant)
   - OpenAI Actions configuration in a Custom GPT
   - Explicit IML sign-off on data leaving ISZE's Microsoft tenant to OpenAI
   
   **Realistic verdict:** not worth pursuing from your position. It's a three-quarter-year project with IT and would still face the "is this sanctioned?" question.
3. **What IS worth doing:** ask BVDB to maintain a small set of **CSV exports** of key Power BI datasets (sales by distributor/month, UIO by model, AIM classification status), automatically refreshed to a folder Claude can read. That gets you 80% of the integration benefit with 5% of the effort.
4. **Real-time insights:** not achievable with either tool. Best you get is "24-hour-old PBI export that Claude regenerates the competitiveness dashboard from." Call it that, don't call it real-time.

---

## What to automate next (ranked by effort/value)

| # | Automation | Effort | Value | Notes |
|---|---|---|---|---|
| 1 | `CHANGELOG.md` for context pack + script to regenerate pack from memory/ | Low | High | Formalises the sync. Claude builds this in one session. |
| 2 | Sensitivity YAML front-matter on all Knowledge MDs | Low | Medium | Prevents accidental upload of restricted content. |
| 3 | Weekly brief scheduled task (already exists manually — formalise via `mcp__scheduled-tasks`) | Low | Medium | Claude runs every Monday morning, writes to `AI_Briefs/`. |
| 4 | BVDB-maintained CSV drop folder (Power BI → Desktop/ISZE/Data/latest/) | Medium | High | Requires BVDB buy-in. Biggest unlock for Claude. |
| 5 | Enhanced `deploy.sh` with pre-publish content review (strips sensitivity: restricted blocks) | Medium | Medium | Prevents confidential content hitting GitHub Pages. |
| 6 | Consolidate `GPT_VectorStore` (older) vs `GPT_Enterprise` (current) — one canonical source | Low | Medium | Currently drifted. Confusing. Pick one, archive the other. |
| 7 | Monthly context-pack refresh reminder (calendar + Claude prompt) | Low | Low | Routine discipline. |

**What to NOT automate (explicit non-goals):**
- Live PBI → GPT pipeline. Not worth it. See above.
- Auto-upload to GPT Enterprise knowledge. OpenAI doesn't expose this via API cleanly for Custom GPTs; manual upload is the only path.
- Claude → GPT handoff. They can't talk. You are the bridge.
- Sanctioning campaign. Don't pitch this internally as an official stack unless/until ISZE IT initiates it. Risk-reward is wrong for your role.

---

## Assumptions I'm flagging explicitly

These are things I stated above without verifying — confirm or correct:

1. **GPT Enterprise tier:** you said "deployed but no folder access." I'm assuming this means your ISZE team has a ChatGPT Enterprise licence (not Team, not Plus). If it's actually ChatGPT Team or personal Plus, the governance posture tightens further (Team has less data-retention protection).
2. **BVDB's willingness:** the "CSV drop folder" recommendation assumes BVDB will agree to publish scheduled Power BI exports. Not confirmed.
3. **GitHub Pages repo privacy:** I'm assuming your `isze-tools-github` GitHub repo is private. If it's public, the entire Tier 3 publishing layer has a much bigger governance issue.
4. **Sensitivity tag enforcement:** the YAML tag only works if Claude is instructed (via CLAUDE.md) to respect it. Tag alone is not a technical control. You'd need to add to CLAUDE.md: "Before adding content to GPT_Enterprise/2_KNOWLEDGE_FILES/*.md, verify sensitivity tag is `public` or `internal`. Never include content tagged `confidential` or `restricted`."
5. **"Not sanctioned stack":** your own words from the prompt. If ISZE IT has actually approved Claude via Cowork, that changes a lot. Confirm status.

---

## Open questions for you

1. Do you want me to **build the `CHANGELOG.md` + context-pack regeneration script** now as a follow-up?
2. Should I **consolidate `GPT_VectorStore` into `GPT_Enterprise`** (pick the current version, archive the rest)?
3. Do you want the **sensitivity tag instruction added to CLAUDE.md**?
4. Is BVDB someone you can ask about the **scheduled CSV export from Power BI**, or is that a non-starter politically?
5. Should the new MASTER_DASHBOARD section have a **"trigger Claude" link** that deep-links to Cowork with a pre-loaded prompt, or is that over-engineering?

---

*End of memo. Content is internal working reference only — not for IML, ITUK, or external sharing.*

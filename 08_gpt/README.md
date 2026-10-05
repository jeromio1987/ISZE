# GPT Enterprise Starter Kit â€” JÃ©rÃ´me Van der Pluym / ISZE
Last updated: April 2026

---

## What's in This Folder

This folder contains everything needed to set up effective Custom GPTs in ChatGPT Enterprise. There are three types of files:

| Folder | Contents | How to use |
|--------|----------|-----------|
| `1_CUSTOM_GPT_SKILLS/` | System prompt templates â€” one per GPT | Paste into the GPT's "Instructions" field |
| `2_KNOWLEDGE_FILES/` | Reference documents about ISZE, Jerome, and active projects | Upload as Knowledge files inside the GPT |
| `3_TEMPLATES/` | Email and analysis templates | Upload as Knowledge, or keep as personal reference |

---

## The Four Custom GPTs â€” Quick Summary

### GPT 1: ISZE Strategic Assistant
**File**: `1_CUSTOM_GPT_SKILLS/ISZE_Strategic_Assistant.md`
**For**: Strategic analysis, position papers, meeting prep, sparring, distributor correspondence, IML briefings. Your main all-purpose ISZE assistant.
**Knowledge files to upload**: All 5 files in `2_KNOWLEDGE_FILES/` + both files in `3_TEMPLATES/`

### GPT 2: ISZE Pricing Analyst
**File**: `1_CUSTOM_GPT_SKILLS/ISZE_Pricing_Analyst.md`
**For**: Price calculations, basket impact analysis, FX decomposition, ITUK pricing support.
**Knowledge files to upload**: `Pricing_Logic.md` + `Glossary_and_Terms.md`

### GPT 3: Productivity Assistant
**File**: `1_CUSTOM_GPT_SKILLS/Productivity_Assistant.md`
**For**: Email drafting, meeting prep, document structuring, task prioritisation. No ISZE data needed â€” general purpose.
**Knowledge files to upload**: `Jerome_Working_Style.md` + `Email_Templates.md`

### GPT 4: Data Analysis Assistant
**File**: `1_CUSTOM_GPT_SKILLS/Data_Analysis_Assistant.md`
**For**: Excel logic, Python scripts, KPI interpretation, Power BI support, AIM framework queries.
**Knowledge files to upload**: `Active_Projects_Apr2026.md` + `ISZE_Company_Context.md` + `Analysis_Frameworks.md`

---

## How to Create a Custom GPT in GPT Enterprise

1. Go to **ChatGPT** â†’ click your name â†’ **My GPTs** â†’ **Create a GPT**
2. Click **Configure** tab
3. **Name**: e.g. "ISZE Strategic Assistant"
4. **Instructions**: Paste the full contents of the relevant `.md` file from `1_CUSTOM_GPT_SKILLS/`
5. **Knowledge**: Upload the relevant files from `2_KNOWLEDGE_FILES/` and `3_TEMPLATES/`
6. Enable **Code Interpreter** if it's the Data Analysis GPT
7. Click **Save** â†’ set access to **Only me** or your team

---

## Recommended Upload Priority

If you're setting up just one GPT to start, use **GPT 1 (ISZE Strategic Assistant)** with all knowledge files. It covers 80% of use cases.

Knowledge files in priority order:
1. `ISZE_Company_Context.md` â€” org structure, key facts, UIO data
2. `Glossary_and_Terms.md` â€” all abbreviations decoded
3. `Active_Projects_Apr2026.md` â€” current project status and confirmed numbers
4. `Pricing_Logic.md` â€” pricing formula and FX history
5. `Jerome_Working_Style.md` â€” calibrates tone and behaviour
6. `Email_Templates.md` â€” ready-to-use drafts
7. `Analysis_Frameworks.md` â€” structured analysis methods

---

## What NOT to Upload

- Raw Excel/CSV files (164k-row price list, sales exports) â€” too large, GPT cannot parse these as knowledge
- `.xlsx` files â€” GPT Enterprise knowledge base cannot read them; convert key data to `.md` or `.csv` first
- Files with confidential salary or HR information

---

## Keeping This Up to Date

These files should be refreshed at the start of each fiscal year (April) and after major project milestones:
- FY change: update FX rate, UIO data, project status, Kosha targets
- ITUK pricing resolution: update `Active_Projects_Apr2026.md`
- New IML pricing: update `Pricing_Logic.md`
- New project starts: add to `Active_Projects_Apr2026.md`

---

## Relationship to GPT_VectorStore (archived)

`GPT_VectorStore/` was archived to `_archive/GPT_VectorStore/` in June 2026. Use **`GPT_Enterprise/2_KNOWLEDGE_FILES/`** for GPT uploads and **`ISZE/Projects/Isuzu/prism/docs/`** for GPS/PMS methodology. Recovery: copy from `_archive/` if needed.

---

## Current pack: `GPT6_CONTEXT/` (added 2026-09-19)

A **separate, self-contained five-file research set** for a general-purpose research model (Jerome has GPT6
at work but no Codex). It does not overwrite anything above. Written fresh from the live derived data and
`FACTS.md` on 2026-09-19.

| File | Contents |
|------|----------|
| `GPT6_CONTEXT/00_READ_ME_FIRST.md` | How to use the set, the seven rules, what is and is not attached |
| `GPT6_CONTEXT/01_ISUZU_AND_ISZE_BUSINESS.md` | Entity structure, vehicle ranges, markets, fiscal year, price chain, who does what |
| `GPT6_CONTEXT/02_NUMBERS_AND_HOW_THEY_ARE_BUILT.md` | Every live figure with as-of date, source file and quoting restriction |
| `GPT6_CONTEXT/03_OPERATIONS_OPEN_WORK_AND_CAVEATS.md` | What runs monthly, open work, decisions waiting, closed items, all known data defects |
| `GPT6_CONTEXT/04_GLOSSARY_AND_HOW_TO_WRITE.md` | Acronym decoder and the writing rules (plain English, margins not factors, units need context) |

**Why a second set:** the `2_KNOWLEDGE_FILES/` set above was last reconciled in April/July 2026 and still
carries superseded figures that must not be used - notably the ITUK oil-filter capture rate (9.8%/17.3%,
legacy denominator) and the pre-correction UIO totals. Loading both sets makes a model contradict itself.
The GPT6 pack supersedes the knowledge files for research use.

**Upload note:** the five files are plain markdown, roughly 66 KB total. No spreadsheets, no
line-level billing, no full price list. Optional four derived CSVs are named in `00_READ_ME_FIRST.md`.

# GPT Enterprise Starter Kit — Jérôme Van der Pluym / ISZE
Last updated: April 2026

---

## What's in This Folder

This folder contains everything needed to set up effective Custom GPTs in ChatGPT Enterprise. There are three types of files:

| Folder | Contents | How to use |
|--------|----------|-----------|
| `1_CUSTOM_GPT_SKILLS/` | System prompt templates — one per GPT | Paste into the GPT's "Instructions" field |
| `2_KNOWLEDGE_FILES/` | Reference documents about ISZE, Jerome, and active projects | Upload as Knowledge files inside the GPT |
| `3_TEMPLATES/` | Email and analysis templates | Upload as Knowledge, or keep as personal reference |

---

## The Four Custom GPTs — Quick Summary

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
**For**: Email drafting, meeting prep, document structuring, task prioritisation. No ISZE data needed — general purpose.
**Knowledge files to upload**: `Jerome_Working_Style.md` + `Email_Templates.md`

### GPT 4: Data Analysis Assistant
**File**: `1_CUSTOM_GPT_SKILLS/Data_Analysis_Assistant.md`
**For**: Excel logic, Python scripts, KPI interpretation, Power BI support, AIM framework queries.
**Knowledge files to upload**: `Active_Projects_Apr2026.md` + `ISZE_Company_Context.md` + `Analysis_Frameworks.md`

---

## How to Create a Custom GPT in GPT Enterprise

1. Go to **ChatGPT** → click your name → **My GPTs** → **Create a GPT**
2. Click **Configure** tab
3. **Name**: e.g. "ISZE Strategic Assistant"
4. **Instructions**: Paste the full contents of the relevant `.md` file from `1_CUSTOM_GPT_SKILLS/`
5. **Knowledge**: Upload the relevant files from `2_KNOWLEDGE_FILES/` and `3_TEMPLATES/`
6. Enable **Code Interpreter** if it's the Data Analysis GPT
7. Click **Save** → set access to **Only me** or your team

---

## Recommended Upload Priority

If you're setting up just one GPT to start, use **GPT 1 (ISZE Strategic Assistant)** with all knowledge files. It covers 80% of use cases.

Knowledge files in priority order:
1. `ISZE_Company_Context.md` — org structure, key facts, UIO data
2. `Glossary_and_Terms.md` — all abbreviations decoded
3. `Active_Projects_Apr2026.md` — current project status and confirmed numbers
4. `Pricing_Logic.md` — pricing formula and FX history
5. `Jerome_Working_Style.md` — calibrates tone and behaviour
6. `Email_Templates.md` — ready-to-use drafts
7. `Analysis_Frameworks.md` — structured analysis methods

---

## What NOT to Upload

- Raw Excel/CSV files (164k-row price list, sales exports) — too large, GPT cannot parse these as knowledge
- `.xlsx` files — GPT Enterprise knowledge base cannot read them; convert key data to `.md` or `.csv` first
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

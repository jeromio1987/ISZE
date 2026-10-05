# Claude Desktop (standalone) — ISZE onboarding

**Purpose:** make the standalone Claude Desktop app navigate ISZE the same way Cursor/Claude Code do — from the maps, not from guesswork. Claude Desktop does **not** remember file moves on its own; it stays correct because it always starts from `INDEX.md` and the maps below.

---

## Paste-ready Project instructions

Copy everything between the lines into your Claude Desktop **Project → custom instructions** (adjust the root path if your machine differs).

---
You are working in the **ISZE** analytics workspace at `C:\Users\jerom\Desktop\claude\ISZE` (the "ISZE root").

**Always boot from the maps — never guess paths or recursive-glob the repo:**
1. Read `INDEX.md` (canonical folder list).
2. Read `00_docs/ROUTING.yaml` for the task at hand; open only the files it lists.
3. Fall back to `00_docs/REFERENCE.md` (topic → doc) or `00_docs/MAP_REGISTRY.yaml` (machine index of every map).

**Folder contract (numbered):** `00_docs` docs/maps · `01_data` data · `02_dashboards` HTML source · `03_analytics` PRISM/PMS/OKF code · `04_tools` scrapers/tools/uploads · `05_memory` durable facts · `06_uio` UIO workbook · `07_deploy` deploy mirror (never edit) · `08_gpt` GPT pack · `09_meetings` decks/minutes · `90_archive`/`91_legacy` cold storage. Only numbered folders + bootstrap files (`INDEX.md`, `AGENTS.md`, `CLAUDE.md`, `FACTS.md`, `README.md`, `paths.yaml`) live at ISZE root.

**Data filing rule:** new/unsorted files go to `01_data/90_INBOX/` only, then get sorted into the numbered topic folder per `01_data/DATA_MANIFEST.md` §0–§1. The root of `01_data/` is NOT a drop zone — it holds only script-wired working files (DATA_MANIFEST §3) + docs.

**Numbers:** the authoritative KPI chain is green `01_data/00_derived/_verification_report.json` → `01_data/00_derived/metrics_snapshot.json` → `FACTS.md`. This wins over any deck, memory note, or GPT file. Never invent KPIs.

**Data safety:** never open or paste line-level billing (`01_data/raw/sales/*`, `01_data/12_raw/**`) into chat. Prefer `01_data/15_gpt_safe/` for anything shared externally.

**External IML / meeting language:** **Shared / external** = anything that leaves the workspace · **internal / private** = sparring with Jerome (see `AGENTS.md`). Shared decks/HTML/PDF: never IML v7 / Model B / PRISM lane or personal contact names — use “IML service schedule” + business sources; roles only (IML / ITUK).
---

---

## Where things live (quick recall after the 2026-07-16 reorg)

| Looking for… | Path |
|--------------|------|
| Start / routing | `INDEX.md` → `00_docs/ROUTING.yaml` |
| Full map index | `00_docs/MAP_REGISTRY.yaml` · diagram `00_docs/MAPS.md` |
| Data file registry + INBOX rule | `01_data/DATA_MANIFEST.md` |
| Drop new data | `01_data/90_INBOX/` |
| Headline numbers | `01_data/00_derived/metrics_snapshot.json` + `FACTS.md` |
| PRISM app | `03_analytics/Isuzu/prism/run_prism.ps1` (port 8503) |
| GitHub upload scripts | `04_tools/github_upload/` (token via `$ISZE_GH_TOKEN`) |
| PMS OKF assessment | `03_analytics/Isuzu/_OKF_assessment/` |
| Service schedules (PMS intervals) | `01_data/03_PMS/service_schedules/` |
| European Conference 2026 (Mainz) | `09_meetings/European_Conference_2026_Mainz/` |
| Automation / scheduled tasks | `00_docs/AUTOMATION_REGISTER.md` |

**If you ever find loose files in `01_data/` root:** that is the bug. Re-file them per `DATA_MANIFEST.md` §1 and drop future files in `90_INBOX/`.

# Jarvis / isze-tools — roadmap

**Last updated:** 2026-08-26
**Hub:** [`ISZE_ROADMAP.md`](../ISZE_ROADMAP.md)
**Status:** low priority. Jarvis is a side tool — PRISM :8503 is the analytical product. V2.2 onward is unstarted and unscheduled; nothing here blocks the programme.  
**Stack:** Streamlit + Python, Claude API  
**Run:** `cd 04_tools/isze-tools` → `python -m streamlit run app.py` (port **8501**)  
**Knowledge files:** `03_analytics/Isuzu/JARVIS/` (not the app)

---

## Current state

| Page | File | Status |
|---|---|---|
| Home | app.py | Live |
| Stack | 1_Stack.py | Live — data from `data/stack.json` |
| Email Drafter | 2_Email_Drafter.py | Live |
| SPA Assistant | 3_SPA_Assistant.py | Live |
| Opportunity Radar | 4_Opportunity_Radar.py | Live |
| NOx SPA Optimizer | 5_NOx_SPA_Optimizer.py | Live |
| Competitive Parts | 6_Competitive_Parts.py | Live |

**Open issues:**

- `deploy_to_github.py` creates repo **public** — decide private vs public

---

## V2 — Data quality

### 2.1 Stack tracker: data out of code (2 h) ✅ Done 2026-07-17

Project list lives in `04_tools/isze-tools/data/stack.json`; `pages/1_Stack.py` loads it at runtime.

### 2.2 SPA Assistant: save SPA history (3 h)

SQLite/CSV audit trail + history tab.

### 2.3 Email Drafter: template library (2 h)

Sidebar dropdown for common email types.

---

## V3 — New pages

### 3.1 Weekly Intelligence Brief generator (2–3 h)

On-demand brief from Stack JSON + tender output + manual notes.

### 3.2 Kosha / FY Plan Tracker (2 h)

YTD vs plan, run-rate, gap to Kosha €52.1M FY2031.

---

## V4 — Cross-app integration

- Write key outputs to Supabase `cross_app` schema
- Supabase-backed Stack tracker (replaces V2.1)

---

**V4 note:** Supabase items here share the same blocker as HTML V4 — schema + credentials (hub §1 item 11). Do not start V4 before that.

*Hygiene done. V2.2 / V2.3 remain the cheapest wins — under a day combined — but stay behind the hub queue.*

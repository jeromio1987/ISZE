# Phase 1 — IL + BE live source implementation

**Date:** 2026-08-25  
**Workspace:** `C:\Users\jerom\Desktop\claude\ISZE\04_tools\ISZE_Tender_Monitor_Install\`  
**Scope:** Wire discovery-verified Belgium SEA API + Israel mr.gov.il live fetchers into `tender_scraper_v3.py`.  
**Not touched:** Nordics key modules, `build_dashboard_v4.py`, GPS addressable formula (stays max_wallet/UIO × fleet — no €5,915 rebuild).  
**CPV:** No parent widening (skipped per brief).

---

## Before → after (notice counts)

| Source | Before (health / fetcher) | After (focused scrape 2026-08-25) |
|---|---|---|
| **Belgium** | RSS only → **0** notices; status **BROKEN** (SPA shell) | SEA API → **14** notices; status **OK** |
| **Belgium RSS** | BROKEN (count 0) | Still **BROKEN** — retired, no longer used for data |
| **Israel** | data.gov.il CKAN → **1** notice; status OK but frozen ~2021 | mr.gov.il live → **18** notices; status **OK** |
| **Israel data.gov.il** | Primary | **SUSPECT** / demoted secondary (not used this run) |
| **Israel RSS** | Dead (HTML) | Explicitly **BROKEN** |
| **TED CYP/MLT** | Already in `TED_TARGET_COUNTRIES` | Confirmed present — no change needed |

Focused command (no TED / Cloudflare hammer):

```bat
python tender_scraper_v3.py --only bel,isr
```

Side workbook (does not overwrite full weekly xlsx):  
`C:\Users\jerom\Desktop\claude\ISZE\04_tools\ISZE_Tender_Monitor_Install\isuzu_tenders_v3_bel_isr.xlsx`

Scrape log: `_phase1_il_be_scrape_log.txt`

---

## Code changes summary

### Belgium
- Replaced RSS fetcher with Keycloak `client_credentials` → `POST /api/sea/search/publications`
- Headers: `Authorization: Bearer …`, `BelGov-Trace-Id` (uuid4)
- Maps `dossier.titles`, `vaultSubmissionDeadline`, `publicationWorkspaceId`, `cpvMainCode`, organisation → notice schema (`Country Code=BEL`)
- Credentials: `ISZE_BE_CLIENT_ID` / `ISZE_BE_CLIENT_SECRET` from env / `isze_secrets.env`; fallback fetches public SPA `env.config.js` at runtime (**secret never hardcoded in git**)
- RSS candidates kept only for health probe → always BROKEN

### Israel
- Primary: autocomplete `…/search/autocomplete/SearchBox?term=…` (Hebrew vehicle terms)
- Secondary live: HTML `.result-container` scrape
- CKAN `data.gov.il` only if live returns 0
- Deadlines from `submittingDate` / `מועד אחרון להגשה`
- Schema: `Country Code=ISR`

### Ops
- `--only bel,isr` focused scrape path
- `_load_local_env()` reads `isze_secrets.env` / `.env.local` / `.env`
- `.gitignore` + `isze_secrets.env.example`
- `source_health` keys split honestly (live vs RSS vs CKAN)

---

## source_health (post-scrape)

| Key | Status | last_count | Notes |
|---|---|---|---|
| Belgium publicprocurement.be | **OK** | **14** | SEA API |
| Belgium RSS | **BROKEN** | 0 | SPA shell |
| Israel mr.gov.il | **OK** | **18** | autocomplete live |
| Israel data.gov.il | **SUSPECT** | 0 | demoted; frozen Feb 2021 |
| Israel RSS | **BROKEN** | 0 | retired |

---

## Credentials Jerome may still create

Optional but recommended (avoids depending on SPA config scrape):

1. Copy `isze_secrets.env.example` → `isze_secrets.env` in the Install folder  
2. Set:
   - `ISZE_BE_CLIENT_ID=frontend-public`
   - `ISZE_BE_CLIENT_SECRET=` *(value published in https://www.publicprocurement.be/env.config.js as `VITE_AUTH_CLIENTSECRET` — public SPA client)*
3. Path: `C:\Users\jerom\Desktop\claude\ISZE\04_tools\ISZE_Tender_Monitor_Install\isze_secrets.env`  
   **Do not commit.** Covered by `.gitignore`.

Longer-term: BOSA partner API onboarding for a dedicated client (helpdesk e-Procurement) if the frontend secret rotates.

No Israel API key required.

---

## Changed / added files (absolute paths)

- `C:\Users\jerom\Desktop\claude\ISZE\04_tools\ISZE_Tender_Monitor_Install\tender_scraper_v3.py`
- `C:\Users\jerom\Desktop\claude\ISZE\04_tools\ISZE_Tender_Monitor_Install\_source_health.json`
- `C:\Users\jerom\Desktop\claude\ISZE\04_tools\ISZE_Tender_Monitor_Install\.gitignore`
- `C:\Users\jerom\Desktop\claude\ISZE\04_tools\ISZE_Tender_Monitor_Install\isze_secrets.env.example`
- `C:\Users\jerom\Desktop\claude\ISZE\04_tools\ISZE_Tender_Monitor_Install\isuzu_tenders_v3_bel_isr.xlsx`
- `C:\Users\jerom\Desktop\claude\ISZE\04_tools\ISZE_Tender_Monitor_Install\_phase1_il_be_scrape_log.txt`
- `C:\Users\jerom\Desktop\claude\ISZE\04_tools\ISZE_Tender_Monitor_Install\_phase1_il_be_implementation.md` (this file)

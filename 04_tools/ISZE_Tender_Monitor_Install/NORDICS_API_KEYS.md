# Nordics API keys — Doffin (Norway) + HILMA (Finland)

> **CLOSED for Jerome (2026-08-25).** Keys are live. Agents must **not** re-send this setup sheet or ask him to register/paste keys again. See `_NORDICS_BLOCKED.md` (DONE) and Cursor rule `isze-nordics-keys-closed.mdc`. This doc is **reference only** if keys break and need re-issue.

Free subscription keys unlock Norway and Finland in the weekly tender scrape.
**Do not paste keys into Python source.** Put them only in `nordics_api_keys.env`
(gitignored). Process env vars `ISZE_DOFFIN_API_KEY` / `ISZE_HILMA_API_KEY` also work.

---

## One-time setup (about 10 minutes)

### 1. Norway — Doffin Public API

1. Open the developer portal:  
   https://dof-notices-prod-api.developer.azure-api.net/
2. **Sign up** / sign in.
3. Open **Products / APIs** and subscribe to the **Public API**  
   (search & download published notices).  
   Do **not** use the Notices / eSender **write** API — that is for publishing notices to Doffin, not reading them.
4. Open **Profile → Subscriptions**, show **Primary key**, copy it.

Gateway used by the scraper:

`https://dof-notices-prod-api.azure-api.net/public/v2/search`

(Same Public API as `api.doffin.no` / legacy `betaapi.doffin.no` host aliases.)

### 2. Finland — HILMA AVP-Read

1. Open:  
   https://hns-hilma-prod-apim.developer.azure-api.net/
2. **Sign up** / sign in.
3. Subscribe to product **AVP-Read** (free; active immediately).  
   Skip ETS-Write unless you need to *send* notices.
4. Copy the subscription **Primary key**.

Endpoint used by the scraper:

`https://api.hankintailmoitukset.fi/avp/eformnotices/docs/search` (POST, Azure Search body)

(Developer portal stays at `hns-hilma-prod-apim.developer.azure-api.net` — gateway host is `api.hankintailmoitukset.fi`.)

### 3. Local env file

In this folder (`ISZE_Tender_Monitor_Install`):

```bat
copy nordics_api_keys.env.example nordics_api_keys.env
notepad nordics_api_keys.env
```

Paste:

```
ISZE_DOFFIN_API_KEY=your-doffin-primary-key
ISZE_HILMA_API_KEY=your-hilma-primary-key
```

Save. Do not commit `nordics_api_keys.env`.

### 4. Verify

```bat
python verify_nordics_keys.py
```

Expect `OK` for each key that is present. The script never prints the key value.

Then the next `run_tender_monitor.bat` (or `python tender_scraper_v3.py`) will fetch Norway / Finland.

---

## How keys are loaded

Order (first non-empty wins):

1. Process environment (`ISZE_DOFFIN_API_KEY`, `ISZE_HILMA_API_KEY`)
2. Sibling file `nordics_api_keys.env`

`run_tender_monitor.bat` optionally loads the env file into the process before Python starts; the scraper also loads via `nordics_keys.py`.

---

## Troubleshooting

| Symptom | Likely cause |
|--------|----------------|
| Loud `MISSING API KEY` banner | Env file missing or empty — complete steps 1–3 |
| `verify` → FAIL 401 | Wrong key, or subscribed to write API instead of Public / AVP-Read |
| `verify` → FAIL 404 | Stale URL — update Install pack; Doffin path must be `/public/v2/search` |
| Keys work in verify but not in bat | Confirm `nordics_api_keys.env` sits next to `run_tender_monitor.bat` |

Contact: jerome.van.der.pluym@isuzu-e.com

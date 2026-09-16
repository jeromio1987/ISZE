# Phase 1 — Endpoint discovery (Israel · Belgium · TED CYP/MLT)

**Date probed:** 2026-08-25  
**Workspace:** `C:\Users\jerom\Desktop\claude\ISZE\04_tools\ISZE_Tender_Monitor_Install\`  
**Scope:** Find working machine-readable replacements for two DEAD sources. Production scrapers were **not** edited.  
**Probe artefacts:** `_phase1_probe_raw.json`, `_phase1_be_sample_publication.json`, throwaway `_phase1_*.py` scripts.

---

## Verdict (short)

| Source | Dead URL status | Working replacement? | Recommendation |
|---|---|---|---|
| **Israel** | RSS → 661 KB HTML, 0 `<item>` | **Yes** — live JSON autocomplete + HTML cards; OpenData CKAN exists but **frozen Feb 2021** | Prefer mr.gov.il autocomplete JSON (or HTML `.result-container`); treat data.gov.il as historical only |
| **Belgium** | `/en/rss` → 1196 B SPA shell | **Yes** — authenticated JSON `POST /api/sea/search/publications` | Use Keycloak client-credentials + `BelGov-Trace-Id`; no public keyless open-data feed found |
| **TED CYP/MLT** | N/A (missing from filter) | **Yes** — notices exist when `CY=CYP` / `CY=MLT` added | Add both to `TED_TARGET_COUNTRIES` |

---

## 1) Israel (`mr.gov.il`)

### Dead baseline (confirmed)

| URL | Method | Status | Content-Type | Bytes | `<item>` / JSON |
|---|---|---|---|---|---|
| `https://mr.gov.il/ilgstorefront/he/rss/Tenders.xml` | GET | 200 | `text/html;charset=UTF-8` | 661 445 | no / no |

All alternate RSS paths (`/en/rss/Tenders.xml`, `/he/rss`, etc.) also return HTML search shells. **RSS is retired.**

### Candidate A — data.gov.il OpenData (CKAN) — machine-readable but STALE

Official Government Procurement Administration datasets:

| Dataset | Package | Resource ID | Live probe |
|---|---|---|---|
| דוח מכרזים (tenders) | `tenders` | `7038b3e6-a74d-442e-b16b-466c8196124a` | HTTP 200 JSON, **14 205** records |
| דוח התקשרויות בפטור | `exemptions` | `65c8fced-c50c-400e-94fb-ef1a208c43e5` | HTTP 200 JSON, **165 705** records |

- **Endpoint:** `GET https://data.gov.il/api/3/action/datastore_search`
- **Params:** `resource_id`, optional `q`, `filters` (JSON), `limit`, `offset`, `sort`
- **Headers:** none required (UA recommended)
- **Freshness problem:** resource `last_modified` = **2021-02-16**; newest `_id` rows are dated **08.02.2021**. Package `metadata_modified` = 2023-03-21 but datastore content did not advance. **Do not rely on this alone for live monitoring.**

**Sample fields (tenders):**

| Field (Hebrew) | Meaning | Example |
|---|---|---|
| `שם הליך` | title | כלי רכב שטח (ג'יפ) … |
| `תאריך אחרון להגשת השגות` | deadline | 10.04.2016 |
| `מספר פרסום` | publication no. | 577346 |
| `סטטוס` | status | סגורה / פורסם / בעדכון |

**Minimal Python (CKAN — works, but stale):**

```python
import requests

RID = "7038b3e6-a74d-442e-b16b-466c8196124a"
r = requests.get(
    "https://data.gov.il/api/3/action/datastore_search",
    params={"resource_id": RID, "q": "רכב", "limit": 2, "sort": "_id desc"},
    timeout=60,
)
r.raise_for_status()
rec = r.json()["result"]["records"][0]
print(rec["שם הליך"], rec.get("תאריך אחרון להגשת השגות"), rec.get("מספר פרסום"))
```

### Candidate B — mr.gov.il autocomplete JSON (LIVE, preferred structured)

| URL | Method | Status | Content-Type | Bytes | Structured |
|---|---|---|---|---|---|
| `https://mr.gov.il/ilgstorefront/he/search/autocomplete/SearchBox?term=רכב` | GET | 200 | `application/json;charset=UTF-8` | ~8.5 KB | **yes** — `products[]` |

- **Params:** `term` (Hebrew keyword works best: `רכב`, `טנדר`, `תחזוקה`, …)
- **Headers:** none required
- **Notice fields present:**
  - title → `publishmentName`
  - link → `https://mr.gov.il/ilgstorefront/he` + `url` (e.g. `/p/4000621157`)
  - deadline → `submittingDate` (e.g. `08/10/2026 12:00`)
  - also: `status`, `officeName`, `processNumber`, `firstNewspaperPublicationDay`

**Sample (2026-08-25):**

- title: `מכרז ממוכן מהיר לרכש טאבלטים מוקשחים לרכבי כיבוי`
- link: `https://mr.gov.il/ilgstorefront/he/p/4000621157`
- deadline: `08/10/2026 12:00`

**Minimal Python:**

```python
import requests

r = requests.get(
    "https://mr.gov.il/ilgstorefront/he/search/autocomplete/SearchBox",
    params={"term": "רכב"},
    timeout=30,
)
r.raise_for_status()
p = r.json()["products"][0]
print(p["publishmentName"])
print("https://mr.gov.il/ilgstorefront/he" + p["url"])
print(p.get("submittingDate"))
```

**Caveat:** autocomplete returns a short suggestion set (not full pagination). Good for keyword sweeps; for exhaustive pages use Candidate C.

### Candidate C — HTML search-results scrape (LIVE last resort / full listing)

| URL | Method | Status | Bytes | Notes |
|---|---|---|---|---|
| `https://mr.gov.il/ilgstorefront/he/search/?s=TENDER` | GET | 200 | ~695 KB | title shows **21 963** tender results; server-rendered cards |

**Selectors (verified):**

| What | CSS / pattern |
|---|---|
| Result card | `.result-container` (20 per page) |
| Title + link | `.result-container a[href*='/p/']` → `h2.search-results-content-head` |
| Detail URL | `/ilgstorefront/he/p/{publicationCode}` |
| Deadline label | text `מועד אחרון להגשה:` then `DD/MM/YYYY` |
| Publisher | text after `שם המפרסם:` |
| Status | `span.status` |

No useful embedded JSON blob in page scripts beyond SAP Commerce `ACC.config`. Query param `q=` did **not** narrow the server-side result count in probes (same 21 963); facet/status filters in the UI may be needed for keyword narrowing, or combine with autocomplete.

**Minimal Python (HTML):**

```python
import re
import requests
from bs4 import BeautifulSoup

url = "https://mr.gov.il/ilgstorefront/he/search/?s=TENDER"
html = requests.get(url, timeout=60).text
soup = BeautifulSoup(html, "html.parser")
box = soup.select_one(".result-container")
a = box.select_one("a[href*='/p/']")
title = a.get_text(" ", strip=True)
link = "https://mr.gov.il" + a["href"]
m = re.search(r"מועד אחרון להגשה:\s*([0-9/]+(?:\s+[0-9:]+)?)", box.get_text(" ", strip=True))
deadline = m.group(1) if m else None
print(title, link, deadline)
```

**Sample:** title `מכרז 48-2026 - לאספקת שירותי הנגשת מסמכים…`, link `…/p/4000620545`, deadline `23/09/2026`.

### Israel recommendation for Phase 1 implementation

1. **Primary live:** autocomplete JSON (`SearchBox`) for vehicle/R&M Hebrew terms + HTML `.result-container` scrape for broader listing / pagination.  
2. **Do not** expect RSS revival.  
3. **data.gov.il** = optional historical backfill only until the resource is refreshed upstream.  
4. Deadline is available (`submittingDate` / `מועד אחרון להגשה`) — fix the empty hard-code in the old fetcher.

---

## 2) Belgium (`publicprocurement.be`)

### Dead baseline (confirmed)

| URL | Status | Bytes | Body |
|---|---|---|---|
| `https://www.publicprocurement.be/en/rss` | 200 | 1 196 | Vue SPA shell (“enable JavaScript”) |
| `https://www.publicprocurement.be/supplier/feed/rss` | 200 | 1 089 | same |
| `https://www.publicprocurement.be/nl/rss` | 200 | 1 196 | same |

No Atom/RSS, no keyless CKAN on data.gov.be / opendata.belgium.be for BDA notices (probes failed or 404).

### Working JSON API (documented via public SPA config + JS)

Config published at `https://www.publicprocurement.be/env.config.js` (no auth to read):

- `VITE_SEARCH_API_ENDPOINT` = `https://www.publicprocurement.be/api/sea/`
- `VITE_AUTH_URL` = `https://www.publicprocurement.be/auth`
- `VITE_AUTH_REALM` = `supplier`
- `VITE_AUTH_CLIENTID` = `frontend-public`
- `VITE_AUTH_CLIENTSECRET` = present in the same public file (SPA client)

SPA bundle calls: **`POST /search/publications`** on the search API base → full URL below.

#### Auth

| Step | URL | Method | Body |
|---|---|---|---|
| Token | `https://www.publicprocurement.be/auth/realms/supplier/protocol/openid-connect/token` | POST form | `grant_type=client_credentials` · `client_id=frontend-public` · `client_secret=<from env.config.js>` |

Returns Bearer `access_token` (HTTP 200).

#### Search notices

| | |
|---|---|
| **URL** | `https://www.publicprocurement.be/api/sea/search/publications` |
| **Method** | `POST` |
| **Headers** | `Authorization: Bearer <token>` · `BelGov-Trace-Id: <uuid-v4>` · `Content-Type: application/json` · `Accept: application/json` |
| **Body (JSON)** | see snippet — mirrors SPA `getPublications()` |

**Required / useful body fields (from SPA):**  
`terms`, `cpvCodes`, `withActiveSubmissionDeadline`, `publicationDateFrom/To`, `tenderSubmissionDeadlineFrom/To`, `nutsCodes`, `natures`, `page`, `pageSize`, `order`, …

**Live probe (2026-08-25):** `terms=voertuig` + ISZE CPVs + `withActiveSubmissionDeadline=true` → **HTTP 200**, `totalCount=13`, 5 publications in page.

**Sample notice fields:**

| Field | Example |
|---|---|
| title | `dossier.titles[0].text` → `Takelen van voertuigen op het grondgebied van Edegem en Aartselaar` |
| link | `https://www.publicprocurement.be/en/publication-workspaces/{publicationWorkspaceId}` (e.g. `…/5fa0e403-3ba7-4ed8-a646-01f8e084d6fd`) |
| deadline | `vaultSubmissionDeadline` → `2026-09-20T15:00:00` |
| also | `referenceNumber`, `publicationDate`, `cpvMainCode.code`, `organisation`, `tedPublished` |

**Minimal Python:**

```python
import os
import uuid
import requests

CLIENT_ID = "frontend-public"
# The portal publishes this value in its own front-end bundle
# (https://www.publicprocurement.be/env.config.js) -- read it from there once
# and export it as BE_BOSA_CLIENT_SECRET. Not stored in this repo.
CLIENT_SECRET = os.environ["BE_BOSA_CLIENT_SECRET"]

s = requests.Session()
tok = s.post(
    "https://www.publicprocurement.be/auth/realms/supplier/protocol/openid-connect/token",
    data={
        "grant_type": "client_credentials",
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
    },
    timeout=30,
)
tok.raise_for_status()
token = tok.json()["access_token"]

headers = {
    "Authorization": f"Bearer {token}",
    "BelGov-Trace-Id": str(uuid.uuid4()),
    "Accept": "application/json",
    "Content-Type": "application/json",
}
r = s.post(
    "https://www.publicprocurement.be/api/sea/search/publications",
    headers=headers,
    json={
        "terms": "voertuig",
        "cpvCodes": ["34131000", "50110000"],
        "withActiveSubmissionDeadline": True,
        "page": 1,
        "pageSize": 5,
    },
    timeout=45,
)
r.raise_for_status()
pub = r.json()["publications"][0]
title = pub["dossier"]["titles"][0]["text"]
link = (
    "https://www.publicprocurement.be/en/publication-workspaces/"
    + pub["publicationWorkspaceId"]
)
deadline = pub.get("vaultSubmissionDeadline")
print(title, link, deadline)
```

### Official onboarding path (documented, credentials required for partner API)

BOSA Helpdesk → Partners and Media → **Onboarding for the API** ([helpdesk e-Procurement](https://bosa.belgium.be/nl/services/helpdesk-e-procurement)). Third-party apps (e.g. proclogic) use OAuth against `enot.publicprocurement.be` / PubProc with issued client id/secret.  

For Phase 1, the **public SPA search API above already returns structured BDA notices** without waiting on a helpdesk ticket. Longer-term, a dedicated onboarded client is cleaner if BOSA rotates the frontend secret.

### Belgium recommendation

Replace RSS fetcher with: token → `POST …/api/sea/search/publications` filtered by ISZE CPV list (+ optional NL/FR/EN `terms`). TED remains the above-threshold path (`tedPublished` flag available on each hit).

---

## 3) TED — Cyprus (CYP) & Malta (MLT), last 30 days

**Endpoint:** `POST https://api.ted.europa.eu/v3/notices/search`  
**CPV block:** same surgical list as `tender_scraper_v3.py` (`34131000`, `34113000`, `34136000`, `34130000`, `34136200`, `50110000`, `50112000`, `50116000`, `50111000`)  
**Date gate:** `PD>=` (UTC today − 30 days)  
**No API key required.**

| Query countries | Iteration notices returned | `totalNoticeCount` (PAGE_NUMBER, limit=1) |
|---|---|---|
| `CY=CYP` only | **6** | **5** |
| `CY=MLT` only | **3** | **3** |
| `CYP OR MLT` | **9** | **8** |
| `CY=BEL` (control) | **16** | **15** |

(Small ITERATION vs PAGE_NUMBER deltas are version/pagination artefacts; order of magnitude is clear.)

**Sample CYP:** ND `527524-2026`, title eng *Road-sweeping vehicles / supply & maintenance of two sweepers…*, PD `2026-07-30`, DD present on some hits.  
**Sample MLT:** ND `522304-2026`, title eng *Utility vehicles – SPD8/2026/114 … one new utility electric vehicle…*, PD `2026-07-28`.

### Conclusion for coverage gap

CYP and MLT **do** publish matching vehicle/R&M notices on TED. Current zero count is because **`CYP` and `MLT` are absent from `TED_TARGET_COUNTRIES`**, not because of a CPV dead-end. Adding both codes should surface on the order of **~5 CYP + ~3 MLT** notices per rolling 30-day window (volume will vary).

---

## 4) Implementation notes (for later Phase 1 wiring — not done here)

- Israel fetcher: switch off RSS; wire autocomplete + HTML; populate Deadline from `submittingDate` / `מועד אחרון להגשה`.  
- Belgium fetcher: drop RSS URLs; implement token + search publications; store `vaultSubmissionDeadline` and workspace link.  
- TED: append `"CYP", "MLT"` to `TED_TARGET_COUNTRIES`.  
- Source health: treat HTTP 200 + HTML-without-items / SPA shell as **BROKEN**, not empty success.

---

## Probe log (high signal)

| Probe | Result |
|---|---|
| IL dead RSS | 200 HTML 661 KB, 0 item |
| IL CKAN `tenders` | 200 JSON, 14205 rows, max pub date ~2021-02 |
| IL autocomplete `term=רכב` | 200 JSON products with deadlines |
| IL HTML `.result-container` | 20 live 2026 cards + deadlines |
| BE `/en/rss` | 200 SPA 1196 B |
| BE `env.config.js` | exposes `/api/sea/` + Keycloak client |
| BE token + `POST /api/sea/search/publications` | **200 JSON**, publications + deadlines |
| TED CYP / MLT 30d | **~5–6 / 3** notices with surgical CPVs |

# Cursor task — restore tender coverage in the markets we cannot currently see

**Owner:** Jerome Van der Pluym · **Written:** 2026-08-25 · **Target:** `04_tools/ISZE_Tender_Monitor_Install/`

Diagnosis below is **evidence-based** — every endpoint in §1 was probed live on 2026-08-25 and the
observed response is recorded. Do not assume the historic code comments are still true; two of them
are wrong (see §1.1 and §1.2).

---

## 0. Why this matters (context for prioritisation)

Cross-referencing the live feed against the reviewed FY27 network budget
(`01_data/91_build/bp_fy27_reviewed.json`) shows coverage is close to *inversely* correlated with
revenue. Fix in revenue order, not in code-difficulty order.

| Market | FY27 BP revenue | Share | Notices today | Action-tier today |
|---|---:|---:|---:|---:|
| United Kingdom | €13.04M | 38.8% | 125 | **0** |
| Israel (UTI+UMI) | €6.07M | 18.1% | **0** | **0** |
| Germany | €2.91M | 8.7% | 66 | 6 |
| Belgium | €2.30M | 6.8% | 14 | 2 |
| Norway | €1.76M | 5.3% | 14 | 2 |
| Finland | €0.36M | 1.1% | 2 | 0 |
| Cyprus / Malta / Iceland | €0.88M | 2.6% | **0** | **0** |
| Kazakhstan (KTK) | €1.14M | 3.4% | **0** | **0** |

---

## 1. Root causes — verified, not assumed

### 1.1 Israel — the RSS endpoint no longer exists  ⚠️ CORRECTS AN EARLIER ASSUMPTION

`tender_scraper_v3.py :: fetch_israel()` (~line 727) requests:

```
https://mr.gov.il/ilgstorefront/he/rss/Tenders.xml
```

**Observed 2026-08-25:** `HTTP 200`, `Content-Type: text/html;charset=UTF-8`, 662,850 bytes.
The body is an HTML page (`<title>תוצאות חיפוש | ILG Site</title>`), not an RSS feed. There are
**zero `<item>` elements**. Confirmed by parsing with `lxml` in `recover=True` mode: 0 items.

The existing `except ET.ParseError` branch sanitises HTML entities and retries — that is treating a
symptom of the wrong disease. **A lenient parser will not help; there is no feed at this URL.**
The log line `[IL] Error: mismatched tag: line 53, column 2` is the HTML `</head>` tag, nothing more.

**Task:** find the current machine-readable source for Israeli government tenders and re-point the
function. Candidate routes, in order of preference:
1. An official API / OpenData endpoint on `mr.gov.il` or `data.gov.il` (search for a tenders dataset).
2. A current RSS/Atom path — the old `/rss/` prefix appears to have been retired in a site rebuild.
3. Last resort: HTML scraping of the search-results page, which *is* being served at the old URL.

**Acceptance:** `fetch_israel()` returns ≥1 structured notice on a normal run, with `Title`, `URL`,
`Published` and — critically — a **`Deadline`**, which the current implementation never populated
even when it worked (it hard-codes `"Deadline": ""`). Israel is 18.1% of network revenue and is the
single largest blind spot in the system.

### 1.2 Belgium — same failure mode  ⚠️ CORRECTS AN EARLIER ASSUMPTION

`tender_scraper_v3.py :: fetch_belgium()` (~line 1195) requests:

```
https://www.publicprocurement.be/en/rss
```

**Observed 2026-08-25:** `HTTP 200`, `Content-Type: text/html`, **1,196 bytes** — a JavaScript
single-page-app shell (`<html lang="en" translate="no">`), not a feed. The root domain returns the
identical 1,196-byte shell, confirming a site rebuild to an SPA.

The existing comment says *"TED covers above-threshold BE"* and treats 0 results as normal. It is
not normal — Belgium is the **fourth-largest market at €2.30M** and below-threshold municipal and
utility fleet work is exactly where an Isuzu-sized opportunity lives.

**Task:** identify the JSON/XHR API the SPA calls (browser devtools → Network tab on a search),
or use the Belgian federal e-Procurement open-data endpoint if one is published, and re-point the
function at it.

**Acceptance:** ≥1 Belgian below-threshold notice returned on a normal run.

### 1.3 Norway (Doffin) + Finland (HILMA) — free API keys never registered

`tender_scraper_v3.py` top of file:

```python
DOFFIN_API_KEY = ""     # Norway  — €1.76M market
HILMA_API_KEY  = ""     # Finland — €0.36M market
```

Both `fetch_doffin()` (~line 790) and `fetch_hilma()` (~line 873) early-return when the key is
blank. The code paths are already written and appear complete — this is registration, not engineering.

- Norway: https://docs.doffin.no — register, obtain `Ocp-Apim-Subscription-Key`
- Finland: https://www.hankintailmoitukset.fi/en/docs/api — register, obtain key

**Do not commit the keys to git.** Read them from environment variables
(`ISZE_DOFFIN_API_KEY`, `ISZE_HILMA_API_KEY`) with the existing module constant as a fallback,
so the scheduled task can supply them without the values landing in the repo.

**Acceptance:** both sources return >0 notices, and the run log stops printing `No API key set`.

### 1.4 Germany DTVP — below-threshold still uncovered

Carried as *"in progress"* since the March 2026 brief; still returns 0. TED covers German
above-threshold contracts only, so €2.91M of market sits half-seen. `fetch_germany()` ~line 1226.
Lower priority than §1.1–1.3 because partial coverage exists.

### 1.5 Cyprus, Malta, Iceland, Kazakhstan — no source configured at all

€2.02M combined and currently invisible rather than merely thin. Cyprus and Malta are EU members,
so above-threshold notices should already arrive via TED — **check whether the TED country filter is
excluding them before building anything new.** Iceland (EEA) and Kazakhstan (outside TED entirely)
need their own national sources.

---

## 2. The structural fix — make silent failure impossible

**This is the most important item in this document.** Every failure in §1.1–1.2 returns `HTTP 200`
with a valid-looking body. The scraper therefore cannot distinguish *"no tenders matched this week"*
from *"this endpoint has been dead for months"*, and the run log prints a reassuring summary either way:

```
  Israel:   0
  Belgium:  0
```

Add a **source health check** that fails loudly:

1. Declare an expected shape per source (content-type contains `xml`, and/or body contains `<item`
   or `<entry`, and/or minimum plausible byte size).
2. On mismatch, mark the source `BROKEN` — not `0 results` — and print it as a warning block at the
   **end** of the run, where a human reading the log will see it.
3. Track a rolling count of consecutive zero-result runs per source in a small JSON state file.
   Any source at **zero for 3 consecutive runs** is reported as `SUSPECT` even if it parses cleanly.
4. Surface both states in the dashboard header, so the health of the feed is visible to whoever
   reviews the weekly output rather than buried in a text log.

---

## 3. Two data-quality fixes (independent of the above)

### 3.1 Expire past-deadline notices

The action queue currently presents opportunities whose deadline has already passed at **Selective**
tier. Live examples from the 24 Aug 2026 run:

| Buyer | Country | Deadline | Days past |
|---|---|---|---|
| Командване на военноморските сили | Bulgaria | 2026-07-16 | 39 |
| Banca Naţională a României | Romania | 2026-07-18 | 37 |
| A.R.E.S. 118 | Italy | 2026-08-03 | 21 |
| R.A. ROMATSA | Romania | 2026-08-06 | 18 |

**Task:** in the scoring stage, route any notice with `deadline_date < today` to a terminal
`Expired` decision, and exclude `Expired` from the action queue and from the Attack/Selective counts.
Keep the rows in the dataset for history — just stop presenting them as actionable.

### 3.2 Multilingual fleet-size extraction

`isze_core_v3.py :: extract_fleet_size()` (~line 532) is **English-language and title-only**. Since
605 of 778 notices come from TED in national languages, it fires on **1 notice out of 778**.

A tested multilingual replacement (16 languages, matching both `<number> <noun>` and
`<noun> … <number> <counter-word>`, run against title **and** description) lifts this to **~22 of 778
at roughly 95% precision** on manual review. Real recoveries include an 83-vehicle Romanian postal
fleet (`C.N. POŞTA ROMÂNĂ`) and a 20-vehicle Stuttgart municipal order.

Required guards — these were added after false positives appeared in a first pass:
- reject any value in `1900–2100` (catches years, e.g. Hungarian ref `10/2026`)
- reject when `/` immediately precedes or follows the number (dates and reference numbers)
- cap plausible fleet size at ~3000
- take the **maximum** plausible match in the text, not the first

Reference implementation to port:
`C:\Users\jerom\AppData\Local\Temp\claude\C--Users-jerom-Desktop-claude-ISZE\a7507f41-dc59-42af-99ba-3f4b88a3e05a\scratchpad\fleet_extract_v2.py`

**Set expectations honestly:** only **168 of 778 notices (22%) carry any description text at all**,
and vehicle counts normally live in the tender documents behind the notice rather than in the notice
metadata. ~3% populated is the realistic ceiling for text extraction. This is worth doing because it
turns 1 usable figure into ~22 — it is *not* a route to a fully populated column.

---

## 4. Suggested order of work

| # | Task | Market value | Effort |
|---|---|---:|---|
| 1 | Source health check + loud failure (§2) | protects all | Low |
| 2 | Re-point Israel to a live endpoint (§1.1) | €6.07M | Medium |
| 3 | Doffin + HILMA keys via env vars (§1.3) | €2.12M | Trivial |
| 4 | Re-point Belgium to the SPA's API (§1.2) | €2.30M | Medium |
| 5 | Expire past-deadline notices (§3.1) | quality | Trivial |
| 6 | Multilingual fleet extractor (§3.2) | quality | Low |
| 7 | Germany DTVP below-threshold (§1.4) | €2.91M | High |
| 8 | Check TED filter for Cyprus/Malta; assess IS/KZ (§1.5) | €2.02M | Unknown |

---

## 5. Out of scope for this task

- **The UK zero.** The UK returns 125 notices and **0 at action tier** — that is a *scoring* question,
  not a source question, and is being handled separately by manual review of a notice sample.
  Do not re-tune the scoring model as part of this work.
- Any change to the Fit / Win / Econ weightings.
- The dashboard's visual design.

---

## 6. Verification before you call it done

Run `run_tender_monitor.bat` and confirm in `tender_monitor_log.txt`:

- [ ] Israel returns >0 notices, each carrying a deadline
- [ ] Belgium returns >0 notices
- [ ] Doffin and HILMA return >0 notices, and no `No API key set` line appears
- [ ] Any still-dead source is reported as **BROKEN**, not as `0`
- [ ] No notice with a past deadline appears at Attack or Selective tier
- [ ] Fleet size is populated on ~20+ notices, and spot-checking 10 shows no year-values (2026 etc.)
- [ ] No API key is present in any committed file

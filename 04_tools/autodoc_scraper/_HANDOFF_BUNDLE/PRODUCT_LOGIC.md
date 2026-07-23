# ISZE tools — product logic (why names look wrong today)

## The problem

The folder is called **`autodoc_scraper`**, but most of what you use is **not scraping**:

| What you actually do | What the folder name suggests |
|----------------------|------------------------------|
| PMS lost sales, UIO, PRISM capture | “Autodoc scraper” |
| IAM threat / quality lookup | “Autodoc scraper” |
| Optional competitor price CSVs | Only this part is truly “scraper” |

So titles like **“ISZE Competitive Intelligence”** mixed **PMS + IAM + scrapers** into one product. That is misleading.

**This document is the naming logic.** UI titles and `DASHBOARD_MAP.md` follow it.

---

## Four separate capabilities (do not merge)

```
┌─────────────────────────────────────────────────────────────────┐
│  A. ISZE SOURCE DATA (Excel / CSV) — truth for volumes & UIO      │
│     v3 PN matrix · v17 UIO · PMS Calc · PRISM derived · dealer   │
└───────────────────────────────┬─────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│  B. PMS ANALYTICS (engine.py) — AUTHORITATIVE for PMS claims     │
│     Lost GP · capture % · ITUK / multi-DB · by model              │
│     Streamlit: _HANDOFF_BUNDLE / run_bi.bat                      │
│     HTML: isze_executive_pms.html                                │
└───────────────────────────────┬─────────────────────────────────┘
                                │  (optional cross-check only)
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│  C. COMPETITOR PRICE SCRAPING (optional)                        │
│     autodoc / KS / Mekonomen scripts + CSVs                       │
│     Feeds: “Competitor prices” tab + brand list in PMS app       │
│     Does NOT set PMS actuals or PRISM capture                    │
└───────────────────────────────┬─────────────────────────────────┘
                                │  (input to scoring only)
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│  D. IAM SCORING (parent folder — lookup lab)                      │
│     iam_scoring.py · T/Q · substitution expected loss           │
│     Streamlit: autodoc_dashboard.py · HTML: isze_executive_iam  │
│     NOT validated for external PMS / ITUK letters                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## Correct product names (use these)

| Capability | Streamlit title | HTML title | Launcher |
|------------|-----------------|------------|----------|
| **PMS analytics** | ISZE PMS Intelligence | ISZE PMS Intelligence | `_HANDOFF_BUNDLE\run_bi.bat` |
| **IAM lookup** | ISZE IAM Lookup Lab | ISZE IAM Lookup Lab | `run_dashboard.bat` (parent) |
| **Competitor scrape** | (no standalone app in bundle) | — | `run_autodoc_scraper.bat` etc. (parent) |
| **Combined (legacy)** | — | ISZE Combined View (read banners) | `build_executive_dashboard.py --variant full` |

---

## What lives where (folder ≠ product)

| Path | Historical name | Actual role |
|------|-----------------|-------------|
| `04_tools/autodoc_scraper/` | “scraper repo” | **Monorepo**: PMS handoff + IAM dashboard + scrape scripts |
| `04_tools/autodoc_scraper/_HANDOFF_BUNDLE/` | handoff | **PMS product only** (engine + Streamlit) |
| `04_tools/autodoc_scraper/_html_previews/` | previews | Built **PMS** and **IAM** HTML (separate files) |
| `04_tools/autodoc_scraper/autodoc_scraper.py` | scraper | **Capability C** only |

Renaming the disk folder is optional and disruptive; **UI and docs now use product names above**, not the folder name.

---

## Streamlit tab logic (`bi_shell.py`)

| Tab | Layer | Purpose |
|-----|-------|---------|
| **ISZE source files** | A | Inspect v3 / v17 / PMS Calc inputs |
| **Competitor prices (optional)** | C | Scraper CSVs — not PMS actuals |
| **PMS results** | B | Engine output — only tab for PMS claims |

Inside **PMS results**, sub-tabs are all **layer B** except **Competitor brands**, which uses layer C data for context only.

---

## HTML file logic

| File | Layer | Open when |
|------|-------|-----------|
| `isze_executive_pms.html` | B only | Deck / email for PMS + PRISM |
| `isze_executive_iam.html` | D only | Internal IAM / threat discussion |
| `isze_executive_dashboard.html` | B + D | Avoid for external — mixed scopes |

Default launcher `run_executive_html.bat` opens **PMS HTML only**.

---

## Decision rules

1. **ITUK letter / capture % / lost GP** → **PMS analytics** (B), PRISM tab or PMS HTML.  
2. **“Who is cheaper on Autodoc?”** → **Competitor scrape** (C), optional.  
3. **Threat quadrant / P(sub) expected loss** → **IAM lookup** (D), disclaimed.  
4. **Never** cite IAM substitution loss as PMS leakage.  
5. **Never** cite scraper coverage as fleet UIO or dealer capture.

---

## Related docs

| Doc | Role |
|-----|------|
| `DASHBOARD_MAP.md` | Where to click (paths, launchers) |
| `SPEC.md` | PMS engine formulas and signed decisions |
| `AUDIT_MAP.md` | File index |
| `SCRAPE_OPTIONAL.md` | Why scrapers are optional for PMS |

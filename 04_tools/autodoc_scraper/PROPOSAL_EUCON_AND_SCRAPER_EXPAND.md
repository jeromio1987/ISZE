# Proposal — Eucon raw vs aftermarket table, then scraper expand

**Date:** 2026-08-14  
**Status:** PROPOSAL ONLY. No scrape run. No new crawler. No CSV expansion.  
**Dashboard code:** `render_dashboard.py` not touched.  
**Ask:** Jerome to approve before any live scrape (section 6).

Read-only sources: Eucon 2023 survey xlsx + PartsPool 2026-03-29 xlsx under `ISZE\01_data\01_Pricing\_raw\`; `eucon_price_gap.csv`; CY2025 `sales_fact.parquet` (18 DB books); `pricing_pr00_ie40.parquet`; scraper CSVs in this folder; `AUTO365_PN_JOIN.md`. Never opened `competitiveness_autodoc_risk.csv` or `01_data/raw/sales/*.XLSX`.

---

## Headline (read this first)

| Item | Number |
|---|---:|
| Aftermarket table today (`eucon_price_gap.csv`) | **44** Isuzu PNs |
| What that file actually is | PartsPool **2026-03-29** Autodoc DE/NO — **not** the 2023 UK survey |
| 2023 Price Survey, distinct Isuzu PNs | **152** valid (153 tokens, 1 garbage `"pleas"`) |
| Survey ∩ IE40 catalogue | **152 / 152** |
| Survey ∩ 18-DB CY2025 billed book | **136** PNs · **€5.51M** billed |
| Extra vs the 44-PN table, billed on the 18 | **+123 PNs · +€3.31M** |
| Of those extras, with a 2023 IAM **workshop/list** price | **+26 PNs · +€0.94M** (the rest is OEM map or unpriced IAM) |
| Dashboard example filters | `8981596930` fuel · `8974995480` air · `8982705240` oil — all three already in the 44 |

**Recommended next scrape (one sentence):** After two no-scrape joins (2023 survey → 18 books, labeled vintage; existing KS aftermarket hits → all 18 books, not only UMI/UTI), run KS International on the **48 oil/air/fuel PNs billed at UMI or GERMANY that are not in the current top-300 KS list** — do not scrape Auto365, Autodoc, TMC, or Tranzparts as if they were OEM-PN indexes.

---

## 1. What Eucon raw actually contains

Two different Eucon drops sit on disk. The operating-dashboard aftermarket table uses **only the second**, and the UI still says “Eucon 2023”.

### A. 2023–24 UK / ITUK Price Survey (the unused raw)

Filed 2026-08-10 from Downloads → `_raw/`. Grain = **one Isuzu PN × competitor brand × vehicle**, not a network price.

| File | Grain | Market | Pricing point | Distinct Isuzu PNs |
|---|---|---|---|---:|
| `Eucon_PriceSurvey_UK_2023_OEM_rawdata_20240109.xlsx` | OEM peer map (Ford / Toyota / DAF) | UK · Country=`UK` | **GBP list** (`CompetitorPrice`) · survey `ISZE price` ≈ IE40/PR00 list EUR, **not** street | **129** |
| `Eucon_PriceSurvey_ITUK_2023_OEM_rawdata.xlsx` | OEM peer map (DAF only) | ITUK CV | **GBP list** | **92** (all 92 already in the UK OEM file) |
| `Eucon_PriceSurvey_UK_2023_IAM_rawdata_20240109.xlsx` | IAM brand × PN (LCV 66 + HCV 170 rows) | UK | **List** + **workshop purchase** (median workshop÷list **0.65**) | **143** |

**Union of the three survey books: 152 valid Isuzu PNs.** Brands: OEM = DAF 138 / Ford 37 / Toyota 37 rows; IAM = Blue Print, Bosch, Hengst, Mahle, UFI, Donaldson, Fleetguard, Febi, … (32 named brands; most LCV/HCV rows are “not available at selected competitors”). Countries in the workbooks: **UK only**. Currency: **GBP**. Hard QA already on disk: `Eucon_PriceSurvey_2023_QA.md` — OEM crossrefs SAFE; survey prices NOT street-safe; no ×1.785 in the sheets; main-sheet `ISZE price` VLOOKUPs broken.

**PN coverage vs ISZE catalogue (IE40 PR00):** 152 / 152 survey PNs exist on IE40; 130 have a current priced PR00 row (`sp_eur > 0`, not superseded). 136 of 152 were billed somewhere on the 18-DB network in CY2025.

### B. PartsPool batch 2026-03-29 (what the aftermarket table actually is)

`eucon_pricing_partspool_20260329.xlsx` + `eucon_crossref_iam_20260329.csv`.

| Fact | Value |
|---|---|
| Date on the workbook | **2026-03-29** (source name `top 100_29032026_1507`) |
| Clean rows with an online price | 1,364 |
| Distinct Isuzu PNs with a price | **44** — identical to `eucon_price_gap.csv` |
| Countries in the cleaned file | **DE, NO only** |
| Webshops | Autodoc DE, Autodoc NO, KFZ Teile DE, PKW Teile DE, Skruvat NO |
| Competitor brands | **155** |
| Pricing point | Online IAM EUR vs **raw IE40 list** (metadata says so). Dashboard already restates Δ% vs PR00×1.785. |
| Original metadata claim | “97 unique Isuzu PNs” before dropping 297 null-price rows — **we only have the cleaned 44**. The 53 unpriced PNs are not recoverable from this file. |

This is a **top-revenue Autodoc DE/NO probe**, LCV-heavy. It is not a 2023 UK workshop survey.

### C. Why the dashboard feels “stuck on Eucon 2023”

`build_ledger.py` labels the 44 as “Eucon (DE/NO)” / “list/workshop mix (2023)”. That vintage tag is **wrong for this file**. The 44 are March 2026 Autodoc. The actual 2023 survey is sitting unused in `_raw/`. Both are outdated *as street 2026*, for different reasons: survey = 2023 GBP list/workshop; PartsPool = Autodoc online vs list, DE/NO only, 44 PNs.

---

## 2. Extra matches if we join raw Eucon more fully than `eucon_price_gap.csv`

**The gap file is not a subset of the 2023 survey.** Only **13 of 44** gap PNs appear in the survey. Re-joining raw Eucon is additive, not “unhiding rows from the same extract”.

PartsPool clean **=** the 44. Zero extra priced PNs there.

### 2a. PN presence (survey Isuzu PN ∩ billed book)

CY2025 complete, credits out, 18 GPS DBs.

| Book | Gap 44 already on the book | Extra survey PNs on the book | Extra billed € |
|---|---:|---:|---:|
| **Network (18)** | 42 / 44 · €3.95M (12.7% of €31.15M) | **+123** | **+€3.31M** |
| UMI | 25 · 9.2% of book | +23 | +€0.13M |
| GERMANY | 41 · 15.8% | +71 | +€0.13M |
| ITUK | **5 · 1.9%** | **+89** | **+€1.36M** |
| PORTUGAL | 30 · 6.9% | +74 | +€0.17M |
| UTI | **0 · 0%** | **+58** | **+€0.69M** |

The two gap PNs with **no** CY2025 18-DB bill: `8983320620` fuel pump, `8984865440` water pump (they still have network `rev_eur` on the gap file from an older/wider revenue pull).

**ITUK and UTI are the coverage hole.** Autodoc-top-100 barely touches the CV book. The 2023 HCV/ITUK survey does.

### 2b. Usable **priced** IAM from the 2023 survey (honest ceiling)

IAM survey competitor PN + list/workshop filled on **38** Isuzu PNs only (105 of 236 rows are “not available…”).

| | PNs | Of which billed CY2025 18-DB |
|---|---:|---:|
| IAM priced, not already in the 44 | **30** | **26 · €0.94M** |
| …on UMI / GERMANY / ITUK / PORTUGAL / UTI | 2 / 19 / 22 / 13 / 8 | (same 26, split) |

Those 26 are the only extra rows that could appear as a **price** on the aftermarket table, and only if labeled **2023 UK workshop/list GBP**, never mixed into KS 2026 trade or Mekonomen retail.

### 2c. OEM COMPARABLE maps (not a street price)

UK+ITUK OEM COMPARABLE: **105** distinct Isuzu PNs; **98** not in the 44; **84** billed (€2.52M). Peer brands = DAF / Hilux / Ranger only. Already used to fill `oem_peer_basket` (`peer_oe_pn`). **Do not** put OEM GBP list into the aftermarket € column.

**Practical extra for the aftermarket table = +26 priced IAM PNs, not +123.** The +123 is “this PN exists in a 2023 Eucon book and we billed it”; most of those rows have no competitor price until we scrape.

---

## 3. Filter PNs — dashboard examples and whether other scrapers hit

PMS cats on `parts_catalog_dimension.csv`. Network CY2025 oil+air+fuel = **203 PNs · €2.16M** (oil 72 / air 39 / fuel 92).

### 3a. The three dashboard examples

All three are **already in `eucon_price_gap.csv`** (PartsPool Autodoc DE/NO). None need Eucon re-join to “appear”.

| | `8981596930` fuel element kit | `8974995480` air (ACL) | `8982705240` oil element |
|---|---|---|---|
| Eucon gap | **Hit** — 88 offers, avg €10.06, DE+NO | **Hit** — 24 offers, avg €24.95 | **Hit** — 77 offers, avg €12.32 |
| Also in 2023 IAM survey? | Yes — workshop median **£10.65** / list £26.11 | Survey row **unpriced** (“not available”) | Yes — workshop **£9.20** / list £24.53 |
| CY2025 books | UMI, GERMANY, ITUK — not PT, not UTI | GERMANY, PORTUGAL — not UMI, not ITUK, not UTI | GERMANY, ITUK — not UMI, not PT, not UTI |
| **KS** (PN search, top 300) | **AM hit** £5 / £15 + genuine £25 | Scraped **ok but AM=0** — genuine £30 **OOS** only | **AM hit** £10 + genuine £15 |
| `iam_ks_price_gap.csv` | UMI only (file is UMI/UTI-only today) | Not joined (UMI does not bill it) | Not joined (UMI does not bill it) |
| **Mekonomen** (top 200) | In list · **`no_results`** | In list · **`no_results`** | In list · **`no_results`** |
| **TMC** | No OEM PN in file — product titles like “ELEMENT KIT; FUEL FILTER” are **category**, not this PN | No | No |
| **Tranzparts** | No OEM PN — Mann/Bosch SKUs (“WK 811/86”, “C 29 939”) | No | No |
| **Auto365** | No OEM PN column (see `AUTO365_PN_JOIN.md`) | No | No |

**Short:** oil and fuel **do** show up at KS as aftermarket; air only as genuine OOS. **None** of the three show up as a PN at Mekonomen, TMC, Tranzparts, or Auto365. Eucon (Autodoc DE/NO) is still the only dense IAM price cloud for these three.

### 3b. Other oil/air/fuel in the 2023 survey

12 survey PNs classified oil/air/fuel. **3** = the examples above (already in the 44). **8** extra billed on the 18; **1** (`8981059591` fuel) not billed CY2025.

| PN | Family | 2023 IAM workshop | On GER / ITUK / PT / UMI |
|---|---|---|---|
| `8982984040` oil | OEM comparable, **no IAM price** | — | GER, ITUK, PT |
| `8981772710` air | £40.22 workshop | GER, ITUK, PT |
| `8975425390` fuel | OEM comparable, no IAM price | GER, ITUK, PT |
| `8975425400` fuel | £12.35 | ITUK |
| `8983282070` oil | £12.91 | GER, ITUK |
| `8980714210` air | £38.61 | GER, ITUK |
| `8970622940` air | £39.10 | ITUK |
| `5876101170` oil (BVP) | £15.67 | ITUK |

Six of those eight have a 2023 UK workshop number we could show as **vintage**, not as 2026 street.

### 3c. Live scrapers vs filter lists (current files, not a new scrape)

| Source | What it is | Oil/air/fuel result |
|---|---|---|
| **KS** | PN-indexed Magento search. Current file = **top 300 network revenue**. 300 rows: 64 `ok`, **40** with aftermarket £>2 (hit rate **21.3%**). **The source is far bigger than our seed list:** its public sitemap carries **19,662 URLs, 6,453 containing "isuzu"**, against 300 part numbers we asked about. See the coverage note below. | 33 filters in that 300; **7 AM hits**; 2 genuine-only; 24 `no_results`. UMI 33 filter PNs → only **10** scraped, **1** AM. GERMANY 56 → 21 scraped, **5** AM. |
| **Mekonomen** | **CLOSED — does not carry Isuzu.** The earlier note here said "PN search, top 200. 7 `ok` rows, 0 filters. The 7 look like accessory/sensor false friends." They were not merely noisy, they were **search noise**: the site ignores the part-number query and its catalogue has three Isuzu entries in total, all radio adaptors. Verified 2026-09-18 by pulling all four product sitemaps (169,066 URLs). | Do not retry |
| **TMC** | Category crawl (search `?s=` times out). **Domain unreachable to a plain fetch 2026-09-18** (robots returned no response). | Titles collide with ISZE descriptions; **no OEM PN** — cannot say “this is 8982705240”. |
| **Tranzparts** | **CLOSED, verified 2026-09-18.** `mekonomen.co.uk` has **no A record at all**, only an SOA — the domain is dead, which explains the 7-rows-from-200 result. Separately `tranzparts.co.uk` carries **zero Isuzu in its first 250 products**; every 8-digit handle is Volvo, Iveco or DAF. | Do not retry |
| **Auto365** | **CLOSED — robots-disallowed and not an independent competitor.** Its robots.txt is `User-agent: * / Disallow: /` — everything is disallowed to every bot except Google's, and our scraper walks 21 product pages there. It is also **UMI's own shop** (`auto365@umi.co.il`), so it was never a third-party price. 208 Hebrew listings, internal מק"ט only. | `iam_israel_street.csv` only. Do not build `iam_israel_price_gap.csv`. |
| **KS coverage — the real constraint** | Verified 2026-09-18: `ks-international.com/sitemap.xml` is **12.6 MB and lists 19,662 URLs, 6,453 containing "isuzu"**, across NKR/NPR/NQR/NNR/NLR/Grafter N35/Forward/F110/FSR/FVR. Search by 10-digit number returns real hits and prices (spot-checked: `8983767550` → £36.00/£30.00, `8982705240` → £12.00/£10.00). **At our measured 21.3% hit rate, the full 15,872-part catalogue would yield roughly 3,380 part numbers with a price — about 7.9% of the priced book by value, against 16.5% today.** | The binding constraint was **never the source. It is the seed list** — 300 part numbers. |
| **Amayama** | **NEW, HIGH** | accepts any bare 10-digit Isuzu number in the URL and returns price, warehouse, stock and shipping server-side. Not a UK company but usable. |
| **Omega Spare Parts** | **NEW, HIGH** | publishes the OEM number as a structured field **and** prints a competitor `Dealer Price` on the same page. |
| **Cloudflare-blocked, unresolved** | eBay UK (403 on both hosts, tested twice with cookie jar), Amazon, Autodoc, Buycarparts, Partsouq, Euro Car Parts, **Bison Parts**. Bison is the one that matters: the best UK aftermarket N-Series range seen anywhere, with ex-VAT and inc-VAT prices, and **not one page could be read**. Unresolved, not dismissed. | Do not attempt to bypass |
| **Ireland** | **complete negative** | Harris Group, Colm Burns, D. Dennehy, H&I Parts, North Dublin Commercials are all phone-or-form businesses. None publishes a part number and a price. D. Dennehy's robots.txt explicitly blocks ClaudeBot and GPTBot. Ireland needs **asking**, not scraping. |

`iam_ks_price_gap.csv` is **UMI 7 + UTI 14** rows (21 PNs), of which **2** are filters. GERMANY already has **31** KS aftermarket hits in `ks_results.csv` that never reach the Germany dashboard because the join file was only built for Israel.

---

## 4. Recommended expansion order (do not execute)

### Step 0 — no scrape, do first (if approved as data work, still not a scrape)

1. **Re-join full Eucon raw to all 18 DB books**, as two labeled layers, not one blended €:
   - Layer A: PartsPool 44 (already wired) — keep, retag vintage **2026-03-29 Autodoc DE/NO**, drop the “2023” chip.
   - Layer B: 2023 survey IAM workshop/list on the **26 extra priced PNs** that hit a book — chip **UK 2023 workshop**, GBP→EUR with a stated rate, never into `Avg_Competitor_EUR` of the 44.
   - Layer C: OEM COMPARABLE maps stay on `oem_peer_basket`, not the aftermarket table.
2. **Rebuild `iam_ks_price_gap.csv` for all 18 DBs** from the existing `ks_results.csv` (same rule as today: `Status=ok`, AM £>2, skip genuine-only). Instant coverage: GERMANY 31 / ITUK 26 / PORTUGAL 28 / IRELAND 35 KS AM PNs already on disk; **31** of those 39 KS AM PNs are **not** in the Eucon 44. ITUK extra billed on those already-scraped KS AM rows ≈ **€0.59M**.

### Step 1 — first live scrape, if Jerome says go

**KS International, PN-indexed, not top-N.**

Current KS list is network top-300. That is why UMI is missing 23 of 33 filter PNs.

| Scope | PNs not in current `ks_results.csv` | Why this order |
|---|---:|---|
| **UMI ∪ GERMANY oil/air/fuel** | **48** (UMI 23, GER 35, overlap 18 on the union of 71) | Matches the “light list of ITUK / GERMANY / PORTUGAL / UMI” comment on the dashboard; KS is the only PN-indexed specialist that already hit 2 of 3 example filters. |
| Add ITUK filters | +36 more (union UMI\|GER\|ITUK = 84 missing) | ITUK is the Eucon-44 hole; do as pass 2. |
| Full 18-DB filter book | 203 − 33 already scraped ≈ **170** | Only if pass 1 hit-rate on the 48 is worth it. |

Pass 1 is a **filter-list scrape**, not `--top 300`. Seed from CY2025 billed PNs with `pms_category ∈ {oil_filter, air_filter, fuel_filter}` for UMI sold-to 1797 and GERMANY 2516+601.

**Mekonomen: CLOSED as a source — and the reason recorded here before was wrong.** The earlier note said the 200-PN run returned 0/22 filters and that "a Sweden-only retry on SWEDEN's 18 filter PNs is optional later". That retry would have been wasted effort. Verified 2026-09-18: **Mekonomen does not carry the Isuzu line at all.** All four product sitemaps were pulled — 169,066 product URLs — and they contain three Isuzu entries, all Connects2 radio-installation adaptors. The part-number search also does not work: `mekonomen.se/artiklar/search/?q=<PN>` returns byte-identical pages with the heading rendering `Sök ""`, so the query is echoed and ignored and the search is JavaScript/Algolia-driven. **The 7 `ok` rows in `mekonomen_results.csv` were search noise, not hits** — which is why they looked like accessory false friends (a bumper, a sensor). Do not retry with a filter list; the catalogue is empty of Isuzu. The Swedish route is the used-parts network instead: `bildelsbasen.se` and `laga.se` both support search by original number.

**Verified Nordic additions, 2026-09-18** (detail in `01_data/90_INBOX/scrape_targets/nordics.md`):

| Source | What it gives | Note |
|---|---|---|
| `mekster.no` | prints an `OE-nummer` block with real Isuzu 10-digit numbers and NOK prices | search returning 200 is NOT proof it works — mark probable, confirm on a product page |
| `geparden.no` | the product SKU **is** the Isuzu OEM number, e.g. `ISU5876150000`; genuine oil filter 379,05 NOK | the cleanest Norwegian bridge found |
| `tungen-bil.no` | an Isuzu dealer publishing a table explicitly searchable by part number, with price ex. mva | dealer prices, not IAM |
| `bildelsbasen.se`, `laga.se`, `autopurkaamot.com` | search by original number works | **used / trade tier — never mixed into new OEM peer retail** |
| `autoline.dk` | prints `P/NO` and `Referencenummer` with EUR prices | a pan-European marketplace with a Danish skin, not a Danish distributor book |

**Iceland and Finland:** official importers in all five Nordic countries sell by counter or phone, with no priced webshop. Iceland is a request-a-quote market — treat it as such rather than spending a scrape on it.

### What NOT to do

- **Auto365 without an OEM PN.** Already documented. Family catalogue only. No `iam_israel_price_gap.csv`.
- **£2 Autodoc poison.** Never read `competitiveness_autodoc_risk.csv`. All 298 rows `autodoc_min_eur ≤ 2.34` (median exactly 2.34) = GBP 2.00 “no results” placeholder. Autodoc DE is also Cloudflare-blocked on the OEM-peer pass.
- **TMC / Tranzparts as if they were PN.** Both are category crawls by design (TMC search times out; Tranzparts is not OEM-indexed). A title “ELEMENT; OIL FILTER” is not `8982705240`. Keep them as UK category street context, not aftermarket-table rows.
- **Do not dump 2023 OEM GBP list or IAM list into the same column as KS 2026 trade.**
- **Do not scrape peer Toyota/Ford/DAF OEs on KS** — already probed, 0 prices (KS is Isuzu-centric).
- **Do not write new crawlers** for this round.

---

## 5. Effort, FX, pricing-point honesty

### Effort (if approved)

| Work | Scrape? | Effort | Output |
|---|---|---|---|
| Retag Eucon 44 as PartsPool 2026-03-29; join 26 survey IAM prices as a separate probe | No | Half day | Aftermarket table gains ITUK/UTI rows that are **honestly 2023 UK workshop**, not fake 2026 street |
| Rebuild KS join for 18 DBs from existing CSV | No | 1–2 hours | GERMANY/ITUK/PT dashboards start showing KS AM that is already on disk |
| KS scrape 48 UMI∪GERMANY filters | **Yes** | ~2–4 min wall (delay 1–3 s) + 1 hour QA | New rows in `ks_results.csv`; then rebuild the join |
| KS scrape +ITUK filters (84 total missing) | Yes | ~5–8 min + QA | Fills the CV hole the Autodoc-44 never covered |
| Mekonomen / TMC-PN / Auto365-PN / Autodoc | — | **Skip** — Mekonomen and TMC closed 2026-09-18 as sources that cannot answer the question | — |

### FX (state the rate; do not invent a new official one)

| Source | Currency | Rate on disk | As-of |
|---|---|---|---|
| KS / TMC / Tranzparts scrapers | GBP ex-VAT | **1.17** GBP→EUR | `sources.yaml` 2026-05-01 |
| Mekonomen | SEK | **0.089** SEK→EUR | same |
| 2023 OEM helper sheet | GBP list → “Price in EUR” | Implied median **~1.163**; `EXCHG rate` cell **empty** | 2023–24 workbook |
| PartsPool | Already EUR | Do not apply NOK FX — metadata: NOK is a market label, implied ~1.15 is Norway premium vs DE | 2026-03-29 |
| Projected ISZE retail | — | PR00 × **1.40 × 1.275 = ×1.785** | `config.yaml` / enrich_street |

If we show 2023 workshop GBP next to 2026 KS GBP, convert both with a **labeled** rate and a vintage chip. Do not reuse the empty Eucon EXCHG cell as “official FX”.

### Pricing-point honesty (do not blend)

| Probe | Point | vs projected ISZE retail (PR00×1.785) |
|---|---|---|
| Eucon 44 (PartsPool) | Autodoc **online IAM**, DE/NO, Mar 2026 | Closest to “internet street”, still DE/NO not local |
| Eucon 2023 IAM | UK **workshop purchase** (~65% of list) and **list** | Trade, 3 years stale, UK |
| Eucon 2023 OEM | Peer **OEM list GBP** | Not aftermarket; not street |
| KS AM | UK specialist **trade**, ex-VAT | Trade vs projected retail — not like-for-like |
| KS genuine | Grey/parallel **genuine** | Parallel import, not IAM |
| Mekonomen | SE **retail** (and current hits look noisy) | Closer to retail, wrong shop, almost no filter hits |
| TMC / Tranzparts | UK category tickets | Context only |
| Auto365 | IL family tickets, ILS; scraper `ILS_EUR=0.25` is a placeholder | Local catalogue, not a PN delta |

A negative Δ% on Eucon-44 vs projected retail does **not** mean the same thing as a negative Δ% on KS trade. The dashboard already says probes are not added together. Keep it that way when the 26 survey rows land.

---

## 6. Approve before any scrape

Please tick one. Nothing below runs until you do.

- [ ] **A — no scrape.** Retag the 44 as PartsPool 2026-03-29. Join the 26 extra 2023 IAM workshop prices as a separate “UK 2023 workshop” probe on all 18 books. Rebuild KS join for all 18 from the CSV already on disk.
- [ ] **B — A, then KS 48.** Same as A, then scrape KS for UMI ∪ GERMANY oil/air/fuel PNs missing from `ks_results.csv` (48 PNs).
- [ ] **C — B, then KS +ITUK filters** (84 missing PNs across UMI\|GERMANY\|ITUK).
- [ ] **Hold.** Leave the aftermarket table as the 44 until a later call.

Default recommendation: **A immediately (no scrape), B only after you see the 18-DB KS join.** Do not start C, Mekonomen, Auto365, TMC-as-PN, or Autodoc.

---

## File map (canonical)

```
ISZE\01_data\01_Pricing\_raw\
  Eucon_PriceSurvey_UK_2023_OEM_rawdata_20240109.xlsx
  Eucon_PriceSurvey_ITUK_2023_OEM_rawdata.xlsx
  Eucon_PriceSurvey_UK_2023_IAM_rawdata_20240109.xlsx
  Eucon_PriceSurvey_2023_QA.md
  eucon_pricing_partspool_20260329.xlsx
  eucon_crossref_iam_20260329.csv
ISZE\01_data\00_derived\eucon_price_gap.csv          ← 44 PNs, dashboard table
ISZE\04_tools\autodoc_scraper\
  ks_results.csv                  ← 300 PNs, 39 AM usable
  mekonomen_results.csv           ← 200 PNs, 0 filters
  tmc_results.csv / tranzparts_results.csv  ← category only
  auto365_results.csv / AUTO365_PN_JOIN.md
  iam_ks_price_gap.csv            ← UMI+UTI only today (under 00_derived)
```

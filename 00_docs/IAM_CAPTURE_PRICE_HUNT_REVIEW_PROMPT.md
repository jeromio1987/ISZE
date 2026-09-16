# IAM capture + price hunt — killer review prompt (2026-08-19)

**Status:** paste into a **new** Cursor/Claude session. Read-only unless Jerome says **rebuild** or **ship**.  
**Sibling:** do not overwrite `00_docs/DASHBOARD_CAPTURE_AUDIT_PROMPT.md` — that audit is **chapter 1** of this story, not a duplicate home.  
**Outlook:** draft-only. Never Send. Paste file: `01_data/90_INBOX/DRAFT_outlook_iam_capture_review_20260819.md`.  
**Modes:** this file is **Mode B** (agent + Jerome). Anything that could be forwarded is labelled **Mode A** in the Outlook cover. Chat = B.

---

## Locked conclusions (do not reopen unless new evidence)

1. **OEM we can locate.** ITUK billed kits, dealer sell-out, PR00/IE40, PMS total capture, GPS wallet — those denominators exist. Quote them only after the verify-green gate.
2. **IAM we can price, not count.** Shop quotes and Eucon 2023 workshop GBP are **prices**. Independent-garage **unit volume** is UNKNOWN. Do not invent it.
3. **KS £125 / £35 is the successor line, not the hero.** KS N75.190 4HK1 pad SKU `0001187` lists OEM `8971686340` → IE40 successor **`8982169260`**. Treat KS genuine £125 / aftermarket £35 (ex VAT, OOS on 18 Aug) as that **low-volume successor line** until an application source proves interchange with volume PN **`8982447940`**.
4. **TecDoc shops already quote IAM on the volume PN.** Blue Print `ADZ94218` / Febi `16953` (and cousins) are listed against **`8982447940`** on Parts in Motion, CarParts247, GSF. That is **price evidence on the billed hero**, not KS catalogue proof of the same pad.
5. **PMS headline = total capture** (`line_type=total`). Genuine is an extra quality lens. Sales is sales.
6. **IUK ≠ ITUK.** IUK sold-to **2574** ≠ ITUK sold-to **2575**. Ireland ≠ IUK ≠ IMIE.
7. **UTI ≠ UMI.** UTI sold-to **1799** ≠ UMI sold-to **1797**. Never blend Israel. IDS Israel = UMI only.

**Hero money (locked as billed, not IAM):** ITUK CY2025 **`8982447940`** ≈ **2,282 kits / ~€198.8k**. Do not attach KS £125 to this PN.

---

## Question you must answer (his words)

> Please advise where all the work is done so it can be reviewed, write a killer review prompt + outlook to make all even much better in terms of jaw dropping conclusions, graphical blizzness and all together.

This session **already did the inventory + this prompt**. You (the reviewer) now **run the review**: judge Jerome’s frame, one narrative, jaw-dropping verdicts, graphical brilliance **specified below**. **Do not rebuild HTML/decks** unless the current message says rebuild/ship.

---

## Judge HIS frame — not yours

Jerome’s frame (sound until evidence breaks it):

> We know OEM location and volume on the franchise side. We can **price** IAM substitutes. We **cannot** count IAM units. KS catalog on N75.190 4HK1 is tagging the **old OE / successor line**, not the **€198k billed pad**. TecDoc shops already sell IAM against the volume PN. Until ITC C / GIDSS shows dual-current on the **same** N75.190 4HK1 11-2013-on **front-pad illustration**, leave `8982169260` and `8982447940` **unmatched**.

**Your job:** stress-test that frame. Say sound / flawed / conditional in the **first sentence**. Do not replace it with “here is my IAM capture %”. Do not “helpfully” fill the volume hole.

---

## Verify-green gate (before any KPI)

1. Open `C:\Users\jerom\Desktop\claude\ISZE\01_data\00_derived\_verification_report.json`.
2. Require `"ok": true` and fail = 0. Snapshot on disk 2026-08-18 15:12Z was **108 pass / 0 fail**.
3. Then `metrics_snapshot.json` → `FACTS.md` only as needed.
4. If not green: **stop quoting headlines**. Name the fail. Do not paper over with canvas numbers.

Never load `01_data/raw/sales/*.XLSX` or `01_data/12_raw/sales/*.XLSX` into context.

---

## One narrative (“all together”)

Tell **one** story in this order. Orphan files = fail.

1. **Capture audit** — what dashboards actually show; OEM wallet vs PMS total; two ITUK lanes (`00_docs/ITUK_PRISM_LANE_BRIDGE.md`); IAM % forbidden.
2. **ITUK pad volume** — billed 3,404 kits / hero 2,282; sell-out ~104% on pads (last-mile closed); IML brake cover **35.3% is not IAM share**; 100%−PMS is **not** independent-garage volume.
3. **Shop quotes** — TecDoc IAM on **`8982447940`** (GBP inc/ex VAT labelled); Autodoc is the wrong truck tool and Cloudflare-blocked.
4. **KS catalog miss** — 172 PDPs / 73 SKUs on N75.190 4HK1 brakes; **no `8982447940`** on those pad pages; `0001187` = `8971686340`.
5. **Interchange trap** — same GIDSS family fig **302-017** is a **family**, not one application. ITC C close-out: **dual-current on the same N75.190 4HK1 11-2013-on front-pad illustration, or leave unmatched.**

Parked (name, do not execute): dealer DMS/JDS, IAM volume at franchise shops, 0.4 vs 0.8 wear, network one-pager, ingest into `ks_results.csv` / `oem_peer_scrape_list.csv`.

---

## Jaw-dropping conclusions (required shape)

Every section ends with **one-line verdict** + **money at stake** + **UNKNOWN** + **what would change a decision**.

Minimum verdicts to write (improve wording, do not invent new €):

| Beat | Verdict pattern |
|------|-----------------|
| Capture | OEM we can locate; IAM share = UNKNOWN; two ITUK % must never be mixed. |
| Pad hero | ~€198k genuine billed on `8982447940` at 2575 CY2025 — last-mile is not the leak. |
| IML cover | 35.3% brake cover ≠ IAM. Remainder includes deferred jobs and trucks that never enter the dealer. |
| KS £125/£35 | Wrong PN for the hero until ITC C proves otherwise — successor `8982169260` (0 billed CY2025; 51 in 2024). |
| TecDoc | IAM already priced on the hero at workshop/retail shops — **price war exists; unit war unmeasured**. |
| Eucon 2023 | UK IAM **workshop purchase GBP 2023** on ~38 PNs; ITUK book coverage ~12.6% of billed € — **not** live 2026 genuine retail. Compare PR00 vs reference sell-out (PR00 × 1.40 × 1.275 = ×1.785) vs 2023 workshop GBP **as three different levels**. |
| DAF blanks | Eucon 2023 DAF **OEM list GBP** (e.g. DAF 1436901 vs `8982447940`) = **keep = NO**. Public 2026 hits are IAM/used, not DAF-boxed retail. |

**Graphical brilliance (if you produce a visual — only after rebuild/ship, or as canvas in-session):**

- Chart-first. One glance = the story. Tables last, one of them.
- Navy `#15233c`, terracotta `#c0552d`, paper `#f7f4ee`, ink `#222`. Georgia headings.
- **Never** white text on pale. Sticky headers must keep navy+paper.
- Hover KPI explainers (CSS panel, not `title=` only): formula, as-of date, what is **not** included.
- Self-contained HTML (inline Chart.js, **no CDN**) **or** Cursor canvas. `file://` must paint. Sibling `OPEN_*.cmd` + **run it**. Absolute paths in backticks — no `file://` markdown.
- Zero overlapping labels. Colour = meaning (green/amber/red/grey). Log axes only with forced ticks.
- **Forbidden word in UI and chat labels:** “street”. Say OEM peer retail / dealer sell-out / reference sell-out / price index.
- No pipeline filenames in the body; sources in a grey footnote.
- Do **not** claim a dashboard “done” without rendered verify (`.cursor/rules/isze-verify-rendered-output.mdc`).

This review pass: **prefer chat + canvas**. Do not ship new HTML unless Jerome says rebuild/ship.

---

## Explicit DO NOT

- Invent capture % or IAM unit volume / IAM share.
- Use **100% − PMS** as IAM share.
- Fill `peer_street_eur` / OEM-peer retail with Febi, Eucon IAM list, or 2023 DAF OEM list.
- Treat Eucon 2023 CompetitorPrice GBP as live 2026 genuine DAF/Isuzu retail.
- Attach KS `0001187` £125/£35 to `8982447940`.
- Blend UTI+UMI or label IUK numbers as ITUK.
- Lead with genuine-only PMS.
- Rebuild, sync_to_deploys, ingest hunt CSVs into `ks_results.csv` / `oem_peer_scrape_list.csv`, bump versions, or **Send** mail.
- “Fix if safe.” Load line-level billing XLSX.
- Say “street” in Mode A UI or in conclusions.

---

## File checklist (canonical = `01_data\`, not `02_dashboards\Data\` mirror)

Ignore `07_deploy/`. Prefer ISZE-root numbered folders.

### (1) Capture audit — Mode B

| What | Path | Notes |
|------|------|--------|
| Prior audit prompt | `C:\Users\jerom\Desktop\claude\ISZE\00_docs\DASHBOARD_CAPTURE_AUDIT_PROMPT.md` | 15.8 KB · 2026-08-18 |
| Canvas | `C:\Users\jerom\.cursor\projects\c-Users-jerom-Desktop-claude-ISZE\canvases\dashboard-capture-audit.canvas.tsx` | 9.0 KB · 2026-08-18 17:44 |
| ITUK two lanes | `C:\Users\jerom\Desktop\claude\ISZE\00_docs\ITUK_PRISM_LANE_BRIDGE.md` | |
| Verify | `C:\Users\jerom\Desktop\claude\ISZE\01_data\00_derived\_verification_report.json` | green 108/0/0 |
| Headlines | `C:\Users\jerom\Desktop\claude\ISZE\01_data\00_derived\metrics_snapshot.json` | |
| PMS by DB | `C:\Users\jerom\Desktop\claude\ISZE\01_data\00_derived\pms_capture_by_db_year.csv` | total first |
| MD pack capture HTML | `C:\Users\jerom\Desktop\claude\ISZE\02_dashboards\md_pack\ISZE_MD_Pack_Capture_FY27_FY28.html` | **Mode A**, stale 2026-07-16 — score freshness |
| Related canvas | `C:\Users\jerom\.cursor\projects\c-Users-jerom-Desktop-claude-ISZE\canvases\ks-pms-parts-route.canvas.tsx` | 2026-08-18 10:17 |

**OPEN_*.cmd:** none for the capture canvas. Part Groups (fat payload): `C:\Users\jerom\Desktop\claude\ISZE\02_dashboards\sales\OPEN_PartGroups_Explorer.cmd`.

### (2) ITUK brakes volume — Mode B (numbers); IML ask note may leave the building

| What | Path |
|------|------|
| Canvas | `C:\Users\jerom\.cursor\projects\c-Users-jerom-Desktop-claude-ISZE\canvases\ituk-brakes-iam-volume.canvas.tsx` |
| Sell-out by PN | `C:\Users\jerom\Desktop\claude\ISZE\01_data\00_derived\dealer_sellout_ituk_cy2025_by_pn.csv` |
| N75 by year | `C:\Users\jerom\Desktop\claude\ISZE\01_data\00_derived\ituk_n75_by_year.csv` |
| N75 VIN | `C:\Users\jerom\Desktop\claude\ISZE\01_data\00_derived\ituk_n75_vin_summary.csv` |
| Clutch 47% (adjacent, not pad) | `C:\Users\jerom\Desktop\claude\ISZE\01_data\00_derived\ituk_clutch_47pct.csv` |
| Brake factor note | `C:\Users\jerom\Desktop\claude\ISZE\01_data\03_PMS\ISZE_ITUK_Brake_Factor_IML_Ask_2026-07-23.md` |

No OPEN_*.cmd for the canvas.

### (3) KS / IAM price hunt — Mode B working files; Mode A engines already shipped (do not rebuild)

| What | Path |
|------|------|
| Canvas | `C:\Users\jerom\.cursor\projects\c-Users-jerom-Desktop-claude-ISZE\canvases\pricing-discovery-shops.canvas.tsx` |
| Live TecDoc quotes | `C:\Users\jerom\Desktop\claude\ISZE\01_data\01_Pricing\_raw\iam_sku_live_quotes_20260818.csv` |
| KS Magento hunt | `C:\Users\jerom\Desktop\claude\ISZE\01_data\01_Pricing\_raw\iam_sku_ks_hunt_20260818.csv` + `.json` + `_hunt_iam_sku_ks_20260818.py` |
| N75 OEM join (the trap) | `C:\Users\jerom\Desktop\claude\ISZE\01_data\01_Pricing\_raw\ks_catalog_n75_oem_join_20260818.json` |
| N75 brake hunt CSV/JSON | `C:\Users\jerom\Desktop\claude\ISZE\01_data\01_Pricing\_raw\ks_catalog_n75_brake_sku_hunt_20260818.csv` |
| 4HK1 hunt | `...\ks_catalog_n75_190_4hk1_brake_sku_hunt_20260818.csv` |
| 2013-on p2 | `...\ks_catalog_n75_190_2013on_brake_p2_20260818.csv` |
| Broader brake / Isuzu truck hunts | `ks_catalog_brake_sku_hunt_20260818.*` · `ks_catalog_isuzu_truck_brake_sku_hunt_20260818.*` · `ks_catalog_oem_join_20260818.json` |
| Browser crawlers | `_ks_browser_n75_190_4hk1_20260818.py` · `_ks_browser_n75_brakes_20260818.py` · `_ks_browser_n75_brake_html_20260818.py` · `_ks_browser_brake_crawl_20260818.py` · `_ks_browser_isuzu_truck_brakes_20260818.py` · `_ks_browser_n75_2013on_p2.py` |
| Hub/tree diag | `_ks_isuzu_truck_hub_diag_20260818.json` · `_ks_isuzu_truck_children_20260818.json` · `_ks_n75_brakes_diag_20260818.json` + `.png` + `.py` |
| Pipeline KS (do **not** ingest 18 Aug hunt into this) | `C:\Users\jerom\Desktop\claude\ISZE\04_tools\autodoc_scraper\ks_results.csv` (60.9 KB · 2026-08-17; gitignored) |
| Eucon 2023 IAM workshop join | `C:\Users\jerom\Desktop\claude\ISZE\01_data\00_derived\eucon_uk_survey_2023_price_gap.csv` + `.meta.json` |
| Eucon QA | `C:\Users\jerom\Desktop\claude\ISZE\01_data\01_Pricing\_raw\Eucon_PriceSurvey_2023_QA.md` |
| Aftermarket live HTML | `C:\Users\jerom\Desktop\claude\ISZE\02_dashboards\pricing\ISZE_Aftermarket_Live_Pricing_Dashboard.html` **Mode A** — **no OPEN_*.cmd found** (embed rule; do not rebuild) |
| IAM quality ITUK | `C:\Users\jerom\Desktop\claude\ISZE\02_dashboards\pricing\ISZE_IAM_Quality_Positioning_Engine_ITUK.html` **Mode A** |
| OPEN ITUK engine | `C:\Users\jerom\Desktop\claude\ISZE\02_dashboards\pricing\OPEN_ISZE_IAM_Quality_Positioning_Engine_ITUK.cmd` |
| OPEN overview | `C:\Users\jerom\Desktop\claude\ISZE\02_dashboards\pricing\OPEN_ISZE_IAM_Quality_Positioning_Overview.cmd` |

Also: `ISZE_IAM_Quality_Positioning_Engine.html` + `.cmd`; IMOTORS / ISD siblings + their OPEN_*.cmd. `_build` templates = not client.

### (4) OEM-peer DAF blanks — Mode B

| What | Path |
|------|------|
| Hunt CSV | `C:\Users\jerom\Desktop\claude\ISZE\01_data\01_Pricing\_raw\oem_peer_daf_hunt_20260818.csv` |
| Post-KS JSON | `...\oem_peer_daf_hunt_20260818.post_ks_browser.json` |
| Peer scrape list (pipeline, **do not fill**) | `C:\Users\jerom\Desktop\claude\ISZE\03_analytics\isze_pricing\oem_peer_scrape_list.csv` |
| Registry (internal; language still says old “street” in places — do not copy that word into conclusions) | `C:\Users\jerom\Desktop\claude\ISZE\03_analytics\isze_pricing\OEM_PEERS.md` |
| Seed | `C:\Users\jerom\Desktop\claude\ISZE\01_data\01_Pricing\_raw\oem_peer_basket_seed_20260810.csv` |

### (5) Interchange / GIDSS / ITC C — Mode B until a Mode A pack is authorised

| Fact | Evidence path |
|------|----------------|
| KS OEM on page = `8971686340` | `ks_catalog_n75_oem_join_20260818.json` |
| Successor `8982169260` vs volume `8982447940` | canvas `pricing-discovery-shops` table |
| Fig 302-017 = family | same canvas |
| ITC C close-out | **Not a file.** Close only if GIDSS/ITC C shows **both PNs current on the same N75.190 4HK1 11-2013-on front-pad illustration**. Else **unmatched**. |

Transcript (search, do not dump): `C:\Users\jerom\.cursor\projects\c-Users-jerom-Desktop-claude-ISZE\agent-transcripts\7e670733-16b8-4d1d-8427-5e8ddf17c4d9\7e670733-16b8-4d1d-8427-5e8ddf17c4d9.jsonl`

---

## Paste-ready prompt (Mode B)

```
You are in ISZE at C:\Users\jerom\Desktop\claude\ISZE. Mode B with Jerome.
Read INDEX.md → 00_docs/ROUTING.yaml (pricing + pms_programme) → AGENTS.md.
Read 00_docs/IAM_CAPTURE_PRICE_HUNT_REVIEW_PROMPT.md in full and obey it.
Read skills: answering-the-exact-question, locating-existing-artifacts, visueel-rapport
(visual quality rules only — do not rebuild HTML unless this message says rebuild/ship).

Question: review the capture-audit + ITUK pad + shop-quote + KS miss + interchange-trap
work as ONE story; judge Jerome’s frame; make conclusions jaw-dropping and specify
how graphics must look. Do not invent IAM units.

Locked: OEM locatable; IAM priceable not countable; KS £125/£35 = 8982169260 line until
ITC C dual-current on same N75.190 4HK1 11-2013-on front-pad illustration vs 8982447940;
TecDoc already quotes IAM on 8982447940; PMS total; IUK≠ITUK; UTI 1799 ≠ UMI 1797.
Hero billed ~€198.8k / 2,282 kits. Never 100%−PMS as IAM. Never fill OEM-peer retail
from Febi/Eucon list. Never Send mail. Never ingest into ks_results.csv.

Verify-green first. File checklist is in the markdown. Output: verdict first, then
the five-beat narrative, then UNKNOWN / decision-changers. Canvas OK. No ship.
```

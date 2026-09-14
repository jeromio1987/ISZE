# Country tender portals map — where every notice launches

**Date:** 2026-08-25 · **ES retry:** 2026-09-14 (`_ES_PLACSP_LIVE_20260914.md`)  
**Install:** `C:\Users\jerom\Desktop\claude\ISZE\04_tools\ISZE_Tender_Monitor_Install\`  
**Purpose:** Analysis first — map **official** publication channels vs what the engine actually scrapes. Not a UI pass.  
**Evidence:** `_source_health.json`, `_MARKET_COVERAGE_DARK_MAP.md`, `_SOURCE_HEALTH_FIX.md`, `_phase1_endpoint_discovery.md`, `_P4_BELOW_THRESHOLD_FR_PL_SPIKE.md`, `_OPEN_BACKLOG_ARRANGED.md`, `_ADDRESSABLE_VEHICLES.md`, plus official portal docs + probe `\_probe_country_portals_2026-08-25.json`.  
**Rule:** Ranges, not fake precision. No invented portals. **Notice coverage ≠ fleet extract ≠ GPS €.**

---

## Verdict (straight)

| Question | Answer |
|---|---|
| Are we scraping all sites where tenders launch? | **No.** TED covers **above-threshold** EU/EEA (and UK FaT for UK). Most **below-threshold** national buys never appear on TED. |
| Why does fleet / vehicle potential look tiny (~174 pickup/truck stated)? | **Consistent with current capture + extract.** Only a minority of gated opportunities publish an extractable fleet count; the hero KPI is `extract ∩ gate ∩ segment∈{pickup,truck}` — not “all CV notices.” Full portal wiring raises **notice volume**; it does **not** put a fleet number on every row. |
| Share of footprint countries with a **national LIVE** feed (beyond TED-only) | **~59% LIVE** (17/29) · **~3% CODE_READY** (LT) · rest DARK/BLOCKED national. |

**Footprint denominator:** 29 TED filter codes (`TED_TARGET_COUNTRIES`) = GBR, IRL, POL, PRT, GRC, ISR, DEU, FRA, ESP, ITA, NLD, BEL, DNK, SWE, NOR, FIN, ROU, HUN, CZE, SVK, BGR, HRV, AUT, LVA, LTU, EST, SVN, CYP, MLT.  
**Notes outside filter:** ISL, KAZ (see bottom). CH/SIMAP not in filter.

---

## Status legend

| Status | Meaning |
|---|---|
| **LIVE** | National (or UK) fetcher returning rows in `_source_health.json` |
| **CODE_READY** | Fetcher / API path known; blocked on key, registration, or WAF session — not inventing a portal |
| **PARTIAL** | Thin national supplement only; real below-threshold mass still missing |
| **DARK** | No national fetcher; **TED (or FaT) only** for that country |
| **BLOCKED** | Portal known but paid / geo / retired path — cannot wire free today |
| **RETIRED** | Old path deliberately demoted (SPA RSS, DTVP free path) |

**Scrape feasibility:** what a machine can use — `API` / `RSS` / `HTML` / `login` / `paid` (combinations allowed).

**Est. CV/LCV relevance lift:** expected **extra gate-passing Isuzu-relevant notices** in a rolling ~30d window if that national channel is wired well (order-of-magnitude vs today’s TED-only for that market). Anchored on FR/PL spike: FR BOAMP **52→20** gated · PL BZP **38→23** gated.

---

## Master table (every footprint country)

| Country | Where tenders are published (official portals) | Above TED threshold | Below threshold / national | Current engine source | Status | Scrape feasibility | Est. CV/LCV relevance lift if wired | Priority |
|---|---|---|---|---|---|---|---|---|
| **DE** | TED; **oeffentlichevergabe.de** (Bekanntmachungsservice / Datenservice Öffentlicher Einkauf); **service.bund.de** RSS (legacy feed into BKMS); state/regional eVergabe platforms; DTVP (procedure host, not free list) | TED DEU | oeffentlichevergabe + Länder platforms; service.bund subset | TED + **Germany OV** (OK 545→41 gated) + **service.bund** (OK 12) · DTVP **RETIRED** | **LIVE** (OV Open Data csv.zip) / bund crumb / **BLOCKED** DTVP free | Open Data **API** `notice-exports` (csv/eForms/OCDS); RSS (bund); DTVP **paid** Professional | Wired 2026-08-25 — residual lift if CPV tighten / Länder hosts | Maintain |
| **FR** | TED; **BOAMP** (boamp.fr / DILA OpenDataSoft); PLACE / regional profiles | TED FRA | BOAMP (national + many below) | TED + **France BOAMP** (OK 52) | **LIVE** | Public ODS **API** (no key) | Already wired — residual lift low (~+0–5); keep gate tight | Done / maintain |
| **PL** | TED; **e-Zamówienia / BZP** (ezamowienia.gov.pl) | TED POL | BZP (`isTenderAmountBelowEU` common) | TED + **Poland BZP** (OK 38) | **LIVE** | Public mo-board **API** (no key) | Already wired — residual low–med | Done / maintain |
| **IT** | TED; **PNCP** / ANAC **Pubblicità a valore legale** (pubblicitalegale.anticorruzione.it); MePA / Acquisti in Rete (execution); ANAC open data | TED ITA | PNCP is legal home for below-threshold (~majority by **count**) | TED + **Italy PNCP** (OK 32 raw → 2 gated) | **LIVE** | Public JSON `api/v0/avvisi` (no PDND); CKAN `dati.anticorruzione.it` still rejected | Wired 2026-08-25 — gate-tight; residual lift if search/CPV API params found | Maintain / tighten |
| **ES** | TED; **PLACSP / PLACE** (contrataciondelestado.es / contrataciondelsectorpublico.gob.es); CCAA aggregated platforms | TED ESP | PLACSP profiles + regional aggregation (excl. many contratos menores) | TED + **Spain PLACSP** Atom | **LIVE** (2026-09-14 Atom HTTP 200 this runner; 2 keyword / 0 gated in rolling window) | Official **Atom/XML** (WAF on some other egress — detector kept) | Rolling Atom is thin vs a 30d API dump; residual lift if ZIP/open-data pagination works | Maintain / thicken |
| **BE** | TED; **publicprocurement.be** (BOSA e-Notification / SEA) | TED BEL | SEA national | TED + **Belgium SEA** (OK 14) · RSS **RETIRED** | **LIVE** | Authenticated JSON **API** (SPA client credentials) | Already wired — residual low | Done / maintain |
| **NL** | TED; **TenderNed** (tenderned.nl) | TED NLD | TenderNed mandatory national | TED + **TenderNed RSS** (OK 25) | **LIVE** | **RSS** (+ HTML); registration free for bidding | Already wired — residual low | Done / maintain |
| **AT** | TED; **USP Ausschreibungssuche** (usp.gv.at / ausschreibungen.usp.gv.at) aggregating authority platforms | TED AUT | USP search (links out to procedure platforms) | TED + **Austria USP** (OK 23 → 4 gated) | **LIVE** | Public JSON `api/tenderlist` with `cpvList` + date window (text search ignored) | Wired 2026-08-25 overnight — residual if more CPV chips | Maintain |
| **CZ** | TED; **NEN / VVZ** (nen.nipez.cz, Věstník) | TED CZE | NEN + VVZ bulletin | TED + **Czechia VVZ** (OK 80→7 gated) | **LIVE** | Public `api.vvz.nipez.cz` · `createdAt[gte]` + order works; fulltext/CPV still ignored — client vehicle post-filter | Wired 2026-08-25 — residual if CPV/export auth | Maintain |
| **SK** | TED; **ÚVO / EVO / Vestník VO** (uvo.gov.sk) | TED SVK | Vestník / EVO | TED only | **BLOCKED** | HTML + **reCAPTCHA**; UVOstat paid | **Low–Med** (~+3–12) | **P2** (open data / paid) |
| **RO** | TED; **SEAP / e-licitatie.ro** | TED ROU | SEAP full national | TED + **Romania SEAP** (OK 147→13 gated) | **LIVE** | Public JSON `api-pub/NoticeCommon/GetCNoticeList` (POST; client-side CPV/keyword) | Wired 2026-08-25 overnight — residual if more pages / CPV API params | Maintain |
| **HU** | TED; **EKR** (ekr.gov.hu) | TED HUN | EKR mandatory | TED only | **BLOCKED** | **HTML** / login SPA; no free list API this pass | **Med** (~+5–18) if unlocked | **P2** (registration) |
| **PT** | TED; **Portal BASE** (base.gov.pt) + **dados.gov.pt** anúncios dumps | TED PRT | BASE centralises contracts / announcements | TED + **Portugal BASE** (OK 77→15 gated) | **LIVE** | dados.gov **JSON** (no IMPIC token); APIBase2 still optional token uplift | Wired 2026-08-25 — residual if APIBase2 | Maintain |
| **IE** | TED; **eTenders** (etenders.gov.ie) | TED IRL | eTenders national + lower-value | TED only | **BLOCKED** | **HTML** / portal search; RSS 500; brittle | **Low–Med** (~+2–10) | **P2** (OGP feed) |
| **UK** | **Find a Tender** (above + new PA regime); **Contracts Finder** (lower / legacy); Scotland portals for some below | FaT (UK post-Brexit; not TED) | CF + FaT below band | **UK FaT** (OK 22) + **CF** (OK 121 raw) | **LIVE** | Public **API**/search | Already strong; CF mostly fails Isuzu gate (passenger/route) — intentional | Maintain |
| **SE** | TED; **no single national portal** — registered commercial databases (Visma TendSign, Mercell, e-Avrop, Kommers Annons) per UHM/Konkurrensverket | TED SWE | Commercial annonsdatabaser (mandatory advertising below TED still not on TED) | TED only | **BLOCKED** | **login** per platform; often **paid** monitoring; no free unified API | **Med** lift but **Hard** feasibility (~+5–20 if multi-platform) | **P2** (budget) |
| **NO** | TED; **Doffin** (doffin.no) | TED NOR | Doffin national | TED + **Doffin** fetcher | **LIVE** (keys DONE 2026-08-25) | Free **API** (`nordics_api_keys.env`) | National NO live — do **not** re-ask Jerome for keys | Maintain |
| **FI** | TED; **HILMA** (hankintailmoitukset.fi) | TED FIN | HILMA statutory | TED + **HILMA** fetcher | **LIVE** (keys DONE 2026-08-25) | Free **API** (AVP-Read) | National FI live — do **not** re-ask Jerome for keys | Maintain |
| **DK** | TED; **udbud.dk** (Competition Authority / MitUdbud) | TED DNK | udbud.dk national (+ purchasing plans) | TED + **Denmark udbud** (OK 6 → 4 gated) | **LIVE** | Public JSON `POST /soegning/public/soegeresultat` (`fritekstQuery` + paginering ≥1) | Wired 2026-08-25 overnight — standalone `national_fetchers_dk.py` | Maintain |
| **HR** | TED; **EOJN** (eojn.nn.hr) | TED HRV | EOJN | TED only | **BLOCKED** | **HTML** SPA | **Low–Med** (~+2–10) | **P3** |
| **SI** | TED; **eNaročanje** (enarocanje.si) | TED SVN | eNaročanje | TED only | **BLOCKED** | **HTML** shell | **Low** (~+1–8) | **P3** |
| **LT** | TED; **CVP IS** (viesiejipirkimai.lt / CPP IS) | TED LTU | CVP IS mandatory | TED only | **CODE_READY** | Official export API needs **VPT apiKey** (401 bare) | **Low–Med** (~+2–10) | **P2** (key) |
| **LV** | TED; **IUB** notice DB + **EIS** (eis.gov.lv) | TED LVA | IUB / EIS | TED only | **BLOCKED** | **HTML** | **Low–Med** (~+2–10) | **P3** |
| **EE** | TED; **Riigihangete register** (riigihanked.riik.ee) | TED EST | State registry | TED only | **BLOCKED** | Official opendata API **HTTP 500** this runner | **Low–Med** (~+2–10) | **P3** (ministry fix) |
| **GR** | TED; **Promitheus / ESIDIS** (promitheus.gov.gr) | TED GRC | National e-procurement | TED only | **BLOCKED** | KIMDIS “opendata” URL = **login shell** | **Med** (~+4–15) | **P2** (credentials) |
| **CY** | TED; **eProcurement Cyprus** (eprocurement.gov.cy) | TED CYP | National portal | TED (CYP in filter) | **BLOCKED** national | **HTML** | **Low** (thin market; TED already ~5–6 /30d surgical) | **P3** |
| **MT** | TED; **eTenders Malta** (etenders.gov.mt) | TED MLT | National | TED (MLT in filter) | **BLOCKED** national | **HTML** | **Low** | **P3** |
| **IL** | **mr.gov.il** (Government Procurement Admin); IEC domestic (iec.co.il) + IEC global; data.gov.il CKAN **frozen ~2021** | N/A (not EU TED spine; ISR still in TED filter for some notices) | mr.gov.il + IEC | **mr.gov.il** LIVE · IEC global OK · IEC domestic **GEO_BLOCKED** · CKAN **SUSPECT** | **LIVE** (+ IEC partial) | Autocomplete **JSON** + **HTML**; IEC abroad HTML; domestic **geo** | Residual: fuller HTML pagination + domestic IEC from IL IP (~+3–12) | Maintain / P2 exhaust |
| **BG** | TED; **CAIS EOP** (app.eop.bg) | TED BGR | Central e-procurement | TED + **Bulgaria EOP** (OK 159→5 gated) | **LIVE** | Daily **OCDS JSON** on `storage.eop.bg/open-data-YYYY-MM-DD/` (no login) | Wired 2026-08-25 — residual if more lookback / CPV tighten | Maintain |

### Outside TED filter (brief notes)

| Country | Official portal(s) | Engine today | Status | Feasibility | Priority |
|---|---|---|---|---|---|
| **ISL** | **Útboðsvefur** / Ríkiskaup; above-EEA → TED | None (ISL not in `TED_TARGET_COUNTRIES`) | **DARK** | **HTML**; thin CV volume | **P3** only if network asks |
| **KZ** | **goszakup.gov.kz** (national) | None; KAZ has **no SPU** → GPS linkage stays null anyway | **DARK** | **HTML** / login; non-EU | **P3** / defer |

---

## Coverage vs fleet extract (do not conflate)

```
TED / national scrape  →  more NOTICES in the funnel
Isuzu gate             →  fewer keepers (passenger / SEND / tyres cut)
fleet_size extract     →  only when the notice text states a count (~7–8% today)
product_segment        →  pickup|truck for hero “vehicle potential”
GPS €                  →  extract ∩ pickup|truck ∩ distributor SPU map
```

| Metric (post FR/PL merge snapshot) | Value | Read |
|---|---:|---|
| Notices / opportunities | 254 / 228 | Lead coverage numerator |
| Rows with any fleet extract | ~15 | Source limitation |
| **Vehicle potential pickup/truck** | **18** (8 notices) | Hero KPI — **not** “all CV tenders” |
| Stated fleet all segments | 156 | Includes vans / weak |
| GPS-sized €/yr | €1,488.22 (3 rows) | Map + fleet + segment |

**Implication:** Wiring ES/IT/DE national can **double-ish** gated notice volume in those markets (order-of-magnitude from FR/PL) and still leave vehicle potential in the **tens**, not hundreds, until notices state fleets or TED detail/PDF extract improves.

---

## Current engine — what is actually LIVE

From `_source_health.json` (same day):

| Source | Status | last_count | Role |
|---|---|---:|---|
| TED Europa | OK | 605 | Above-threshold spine (29 countries) |
| UK Find a Tender | OK | 22 | UK above / new regime |
| UK Contracts Finder | OK | 121 | UK lower — most fail Isuzu gate |
| Netherlands TenderNed | OK | 25 | NL national |
| Belgium publicprocurement.be | OK | 14 | BE national |
| Israel mr.gov.il | OK | 18 | IL national |
| France BOAMP | OK | 52 | FR below/national |
| Poland BZP | OK | 38 | PL below/national |
| Italy PNCP | OK | 32 | IT below/national (2 gated) |
| Spain PLACSP | OK | 2 | ES national Atom — LIVE 2026-09-14 (0 gated this window) |
| Germany oeffentlichevergabe | OK | 545 | DE national BKMS Open Data (41 gated) |
| Germany service.bund | OK | 12 | DE RSS crumb |
| Romania SEAP | OK | 147 | RO national (13 gated) |
| IEC global-iec.com | OK | 7 | IL utility abroad list |
| Norway Doffin | **OK / LIVE** | 37 | 11 gated — keys DONE (do not re-ask) |
| Finland HILMA | **OK / LIVE** | 54 | 1 gated — keys DONE (do not re-ask) |
| Denmark udbud.dk | **OK / LIVE** | 6 | 4 gated — MitUdbud soegeresultat |
| Portugal BASE | **OK / LIVE** | 77 | 15 gated — dados.gov anúncios JSON |
| Bulgaria CAIS EOP | **OK / LIVE** | 159 | 5 gated — daily OCDS `storage.eop.bg` |
| Czechia VVZ | **OK / LIVE** | 80 | 7 gated — `createdAt[gte]` + client vehicle gate |
| Lithuania CVP IS | CODE_READY | 0 | needs VPT apiKey |
| Germany DTVP/NRW | RETIRED | 0 | Paid / no free feed |
| Belgium RSS / Israel RSS | RETIRED | 0 | SPA shells |
| Israel data.gov.il | SUSPECT | 0 | Frozen 2021 |
| IEC iec.co.il domestic | SKIPPED | 0 | GEO_BLOCKED |

**National LIVE countries (17/29 ≈ 59%):** UK, NL, BE, IL, FR, PL, IT, DE, RO, AT, NO, FI, DK, PT, BG, CZ, **ES**.  
**CODE_READY (1):** LT (CVP apiKey — do not ask Jerome).  
**DARK/BLOCKED national (~11/29 ≈ 38%):** HU, IE, SE, SK, EE, GR, HR, SI, LV, CY, MT.

Overall Isuzu-relevant **notice** coverage remains roughly **~35–55%** of the addressable public stream (`_MARKET_COVERAGE_DARK_MAP.md`) — TED-strong, below-threshold-weak.

---

## Top 10 portals to wire next (CV lift × feasibility)

Ranked for **expected gate-passing CV/LCV lead lift × machine feasibility**. Skip cosmetic UI.

| Rank | Portal | Country | Why | Feasibility | Est. gated lift /30d | Priority |
|---:|---|---|---|---|---|---|
| **1** | **PLACSP Atom / open data** | ES | Large below-threshold market; official syndication documented | Atom HTTP 200 this runner 2026-09-14 (2 keyword / 0 gated rolling window) | residual if ZIP/pagination | **Done (thin window)** |
| **2** | **PNCP / ANAC pubblicità + open data** | IT | Legal below-threshold home; huge notice count | Open data + HTML; PDND for full API | **+20–50** | **P0** |
| **3** | **oeffentlichevergabe.de Open Data** | DE | Replaces “TED-only honesty” for DE below-threshold mass | Official Open Data API (eForms/OCDS/CSV) | Wired 2026-08-25 (545→41 gated) | **Done** |
| **4** | **Doffin Public API** | NO | National NO | Free API + key | Wired 2026-08-25 (37→11 gated) | **Done** |
| **5** | **HILMA AVP-Read API** | FI | National FI | Free API + key | Keyed; gated CV still thin | **Maintain / tighten** |
| **6** | **Portal BASE APIBase2** | PT | Structured REST | Token + IMPIC auth | **+5–15** | **P1** |
| **7** | **SEAP / e-licitatie** | RO | High CEE public vehicle volume | Public JSON POST (client filter) | Wired 2026-08-25 (147→13 gated) | **Done** |
| **8** | **udbud.dk MitUdbud** | DK | Single national DK home | Public soegeresultat POST | Wired 2026-08-25 (6→4 gated) | **Done** |
| **9** | **USP Ausschreibungssuche** | AT | Aggregator for AT notices | Public JSON tenderlist | Wired 2026-08-25 (23→4 gated) | **Done** |
| **10** | **NEN / VVZ** | CZ | Mandatory CZ bulletin | Public API + `createdAt[gte]` + client vehicle gate | Wired 2026-08-25 (80→7 gated) | **Done** |

**Honorable / deferred:** IE eTenders (P2); GR Promitheus (P2); SE multi-platform (P2 — fragmented/paid); HU EKR (P2); Baltics/HR/SI/CY/MT (P3); ISL/KZ (P3); DTVP paid (BLOCKED unless budget). LT CVP apiKey (CODE_READY).

**Already done this wave (do not re-prioritize as “next”):** FR BOAMP, PL BZP, BE SEA, NL TenderNed, IL mr.gov.il, UK FaT/CF, TED CYP/MLT filter, DE OV, RO SEAP, AT USP, NO Doffin, **DK udbud**, **PT BASE**, **BG EOP**, **CZ VVZ**, **ES PLACSP Atom**.

---

## #1–#5 remaining (most real CV tender volume still dark)

1. **Hungary EKR** — national mandatory; login SPA; no free list API this pass.  
2. **Ireland eTenders** — RSS 404 on 2026-09-14; HTML portal.  
3. **Sweden** — no single gazette; commercial databases (paid / login).  
4. **Slovakia ÚVO** — recaptcha; no free list API.  
5. **Estonia RHR** — official opendata still HTTP 500 (ministry). **Not** Nordics keys.

Spain / Italy / Germany / Doffin / HILMA are **already LIVE**. Do not re-ask for Doffin or HILMA keys.

---

## Method notes / honesty limits

- TED **must** carry above-threshold notices for EU/EEA members in the filter; it **systematically misses** most below-threshold national advertising — that is why vehicle counts feel “too low.”  
- **Sweden** has **no** single state gazette equivalent to BOAMP/BZP; commercial databases are the official advertising channel — treat as hard.  
- **Germany** is federalised: BKMS/oeffentlichevergabe is the free **publication** hub; DTVP/state platforms host procedures — paid DTVP ≠ free BKMS.  
- ES Atom URLs returned **HTTP 200** from this runner on 2026-09-14 (`_probe_es_next_2026-09-14.json`); 2026-08-25 WAF deny was environment-specific. WAF detector stays.  
- Lift bands use FR/PL as calibration, not fake decimals.  
- **No scrapers implemented** in the 2026-08-25 analysis pass beyond optional probe JSON. ES Atom fetch is live 2026-09-14 (`scrape_es_side.py`).

---

## Evidence index

| Path | Role |
|---|---|
| `C:\Users\jerom\Desktop\claude\ISZE\04_tools\ISZE_Tender_Monitor_Install\_source_health.json` | Live statuses |
| `C:\Users\jerom\Desktop\claude\ISZE\04_tools\ISZE_Tender_Monitor_Install\_MARKET_COVERAGE_DARK_MAP.md` | 35–55% notice coverage bands |
| `C:\Users\jerom\Desktop\claude\ISZE\04_tools\ISZE_Tender_Monitor_Install\_P4_BELOW_THRESHOLD_FR_PL_SPIKE.md` | FR/PL lift calibration |
| `C:\Users\jerom\Desktop\claude\ISZE\04_tools\ISZE_Tender_Monitor_Install\_ADDRESSABLE_VEHICLES.md` | Why 18 vehicles |
| `C:\Users\jerom\Desktop\claude\ISZE\04_tools\ISZE_Tender_Monitor_Install\_probe_country_portals_2026-08-25.json` | Optional portal probes |
| `C:\Users\jerom\Desktop\claude\ISZE\04_tools\ISZE_Tender_Monitor_Install\_OPEN_BACKLOG_ARRANGED.md` | P0 = national portal coverage |

# Arranged backlog — ISZE Tender Monitor

**Written:** 2026-08-25 · **Updated:** 2026-09-14 (ES PLACSP LIVE this runner) · **Install:** `C:\Users\jerom\Desktop\claude\ISZE\04_tools\ISZE_Tender_Monitor_Install\`  
**Rule:** No item is DONE without evidence. Null ≠ 0. No invented SPU / keys / revenue.  
**Main priority (Jerome):** **National portal coverage** — analysis map shipped; wire next portals before cosmetic UI.

| Prio | Item | Status | Owner | Blocker / NEXT |
|------|------|--------|-------|----------------|
| **P0** | **National portal coverage** (map → wire ES/IT/DE + keys) | **ES/IT/DE WIRED 2026-09-22** | Implement | Probe `_probe_es_it_de_2026-09-22.json` · modules `national_fetchers_{es,it,de}.py` · Nordics keys already DONE · main 2026-09-14: Next DARK without a key: HU/IE/SE/SK/EE-500/GR (`_ES_PLACSP_LIVE_20260914.md`) |
| **P0** | Nordics Primary keys | **DONE** | Agent | verify ALL OK · health OK · NO/FI merged |
| **P1** | GPS maps FR/PL/IT/ES | **DONE (null)** | Market UX + arrange | 0 newly mapped; floor €1,488.22 |
| **P2** | Market table UX | **DONE** | Market UX sibling | Reason chips shipped — **below** portal coverage |
| **P3** | TED detail enrichment | **PARTIAL / NEXT** | Arrange agent | Cap code ON; detail GET needs TED auth |
| **P4** | Below-threshold FR→PL | **DONE (merged)** | Arrange agent | FR/PL on weekly bat + main feed |

---

## P0 — National portal coverage — **ES / IT / DE WIRED (2026-09-22)**

| Field | Value |
|---|---|
| **Status** | **WIRED** — additive modules + `tender_scraper_v3` wrappers + weekly bat + health OK |
| **Why P0** | Fleet/vehicle KPI looks “too low” mainly because many footprint countries were TED-only for below-threshold national buys — not a dashboard bug |
| **Probe 2026-09-22** | ES PLACSP Atom **216** raw → **10** gated · IT PNCP **22** → **2** · DE OV **590** → **163** |
| **Evidence** | `_probe_es_it_de_2026-09-22.json` · `national_fetchers_{es,it,de}.py` · `scrape_es_it_de_side.py` · `_source_health.json` |
| **LIVE national (ES/IT/DE)** | Spain **OK 216** (Atom `rel=next`, WAF cleared) · Italy **OK 22** · Germany OV **OK 590** (+ service.bund crumb) |
| **Do not** | Invent fleet / GPS € · **ask Jerome for Nordics API keys again** · treat TED as full national coverage |
| **Residual** | ES Atom window is recent updates (optional monthly ZIP for deeper history) · IT gate-tight · next dark portals from map (HU/IE/SE/…) |
| **Cosmetic / UX** | Explicitly **below** portal coverage |

---

## P0 — Nordics Primary keys — **DONE**

| Field | Value |
|---|---|
| **Status** | **DONE** |
| **DoD** | `nordics_api_keys.env` filled · `verify_nordics_keys.py` OK · health not AWAITING_KEY · NO/FI notices merged if API returns any |
| **Evidence** | Verify ALL OK · health Doffin/HILMA **OK** (37 / 54) · merge NO 11 + FI 1 · dashboard opps NO 10 / FI 1 |
| **Paths** | `nordics_api_keys.env` · `NORDICS_API_KEYS.md` · `_NORDICS_BLOCKED.md` · `verify_nordics_keys.py` |
| **Do not** | Commit keys · invent fleet / GPS € |

---

## P1 — GPS maps FR/PL/IT/ES — **DONE (null)**

| Field | Value |
|---|---|
| **Status** | **DONE (null)** |
| **DoD** | Audit csv+yaml; wire real only; null+label if no pack row; never invent SPU |
| **Audit** | No France / Poland / Italy / Spain SPU in `gps_spu_by_distributor.csv`. Yaml already `null`. |
| **Newly mapped** | **0** |
| **GPS floor** | Still **€1,488.22** / yr (unchanged after FR/PL notice merge — no invented maps) |
| **Label** | Chips + `gps_map.by_country[…].has_spu=false` |
| **Paths** | `gps_spu_by_distributor.csv` · `country_distributor_map.yaml` · `_WHY_MARKET_TABLE_EMPTY.md` |

---

## P2 — Market table UX — **DONE**

| Field | Value |
|---|---|
| **Status** | **DONE** · market UX shipped **Y** |
| **DoD** | Every market row shows reason chips (no fleet / no map / van-only / awaiting key) |
| **Shipped** | Why-blank chips · with-fleet · GPS-sized · segment mix; `_WHY_MARKET_TABLE_EMPTY.md`; v4 rebuilt |
| **Paths** | `build_dashboard_v4.py` · `isze_dashboard_v4_opportunity.html` · `OPEN_isze_dashboard_v4_opportunity.cmd` |
| **Preserved** | Product-fit · Hebrew ISR · source-health honesty · coverage chip · unsized wording · GPS = max wallet/UIO pickup/truck only · IDS dealer MAP |

---

## P3 — TED detail enrichment — **PARTIAL / NEXT**

| Field | Value |
|---|---|
| **Status** | **PARTIAL / NEXT** |
| **DoD** | Safe detail for gated IDs; before/after %; respect rate limits |
| **Landed** | Env-gated `ISZE_TED_FETCH_DETAIL` + `TED_DETAIL_CAP=40` + 0.5s delay; enrich after filter only |
| **Before %** (TED list, n=192) | deadline **12.5%** · value **0%** · fleet **7.8%** |
| **After %** | **n/a** — `GET /v3/notices/{id}` → **400 Missing Authorization** |
| **Blocker** | TED detail API requires Authorization; list search stays public |
| **Paths** | `tender_scraper_v3.py` · `_P3_TED_DETAIL_ENRICHMENT.md` |
| **NEXT** | Obtain TED API key → attach Authorization on detail only → re-measure % · keep bat default OFF |

---

## P4 — Below-threshold FR → PL — **DONE (merged)**

| Field | Value |
|---|---|
| **Status** | **DONE (spike + focused implement + main-feed merge)** |
| **DoD** | Implement or spike #1 FR then PL; gate; merge into main; wire weekly |
| **FR fetch** | BOAMP ODS → **52** notices (30d) via `fetch_france_boamp` |
| **PL fetch** | e-Zamówienia BZP → **38** unique CPV matches via `fetch_poland_bzp` |
| **After Isuzu gate** | FR **20** · PL **23** (side xlsx); re-gate on merge drop **0** |
| **Merged into main** | France BOAMP **20** + Poland BZP **23** sheets on `isuzu_tenders_v3.xlsx` |
| **Live feed** | notices **254** · opps **228** · GPS floor **€1,488.22** (3 sized) · vehicles pickup/truck **18** · stated all **156** |
| **Weekly bat** | **ON** — full scrape includes FR/PL (`run_fr`/`run_pl` on `run_all`); still supports `--only fr,pl` |
| **GPS** | FR/PL € still **null** (no SPU) — P1 unchanged |
| **IDS** | 519-dealer network preserved; FR/PL get IDS country_primary / geo_nearest |
| **Paths** | `_P4_BELOW_THRESHOLD_FR_PL_SPIKE.md` · `_phase1_fr_pl_merge.md` · `merge_fr_pl_into_main.py` · `tender_scraper_v3.py` |
| **NEXT** | IT/ES from dark map (same pattern). Do not invent GPS €. |

---

## Final report figures (this arrangement)

| Prio | Status | Figures |
|------|--------|---------|
| **P0 national portals** | **ANALYSIS DONE** | Map: `_COUNTRY_TENDER_PORTALS_MAP.md` · LIVE national **8/29** (NO/FI now OK) · top wire ES→IT→DE |
| P0 Nordics keys | **DONE** | verify ALL OK · health OK · scrape NO **37** / FI **54** · opps NO **10** / FI **1** |
| P1 | **DONE (null)** | Newly mapped GPS countries = **0**; GPS floor **€1,488.22** |
| P2 | **DONE** | Market UX shipped **Y** — subordinate to portal P0 |
| P3 | **PARTIAL / NEXT** | Before deadline 12.5% / value 0% / fleet 7.8%; after blocked on TED auth |
| P4 | **DONE (merged)** | Fetch FR **52** / PL **38** → gated **20** / **23** → main notices **254** / opps **228** |

---

## Parallel siblings

- **National portal coverage** → paper priority (`_COUNTRY_TENDER_PORTALS_MAP.md`) — do not deprioritize for cosmetic UI
- Nordics finish agent → **DONE** (`_NORDICS_BLOCKED.md` = DONE; keys in gitignored env)
- Market UX → P1/P2 **DONE**; IDS dealer MAP shipped (`_IDS_DEALER_MODULE.md`) — preserve on rebuilds; no new cosmetic ahead of portals
- Addressable-vehicles KPI → `vehicles_pickup_truck` / `vehicles_all_stated` in v4 sized_stats — preserved this rebuild

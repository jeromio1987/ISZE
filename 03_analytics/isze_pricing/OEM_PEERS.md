# OEM peer registry — Pricing Spec Layer 1 street / premium

**As of:** 2026-08-10  
**Rule:** talk in **%** only. FY27 list move = **+3% weighted** (separate).

Brand-quality IAM ceilings: `iam_quality_premium_pct.yaml`  
  tier4 +30% · tier3 +60% · tier2 +150% · tier1 +250%  
  Benchmark = **best** brand on the PN, not the cheapest.

Code registry: `premiums.py` → `OEM_PEERS`  
Basket scaffold: `oem_peer_basket.csv` (mirror: `01_data/01_Pricing/_raw/oem_peer_basket_seed_20260810.csv`)  
Re-seed: `python 03_analytics/isze_pricing/seed_oem_peer_basket.py`

---

## LCV — approved

| Peer OEM | Model |
|----------|--------|
| Toyota | Hilux |
| Ford | Ranger |
| Mitsubishi | L200 |

Status: **approved**. Prices blank until scrape/map → `basis: oem_benchmark`.  
Until then, LCV wear/PMS categories move on **`iam_derived`** (Eucon + brand tier %).

---

## CV — approved (IUK + Germany)

Jerome OK 2026-08-10 (incl. **DAF** add-on). Israel still pending.

### IUK (highest at-risk ~€5.4M on action map)
| Peer | Why |
|------|-----|
| **Ford Transit** | UK van/CV overlap; densest IAM substitute set |
| **Mercedes-Benz Sprinter** | Workshop habit / genuine peer street |
| **DAF (LF/CF class)** | UK truck competition; strong CV overlap |

### Germany (high defend)
| Peer | Why |
|------|-----|
| **Mercedes Sprinter / light truck** | DE OE street dense |
| **MAN TGL/TGM** | Light/medium truck peer |
| **VW Crafter** | Van segment overlap |
| **DAF (LF/CF class)** | DE truck competition |

### Israel — pending
- **UTI** and **UMI** separate passes — never blend  
- Peer set after local evidence; not approved yet

---

## Top competitors found (beyond approved OEM peers)

Evidence scan 2026-08-10 — subjects only; no price invention.

### From Outlook (local mailbox scan)
| Signal | Evidence |
|--------|----------|
| **IAM aftermarket leakage** (not OE model) | Sent *RE: Parts Campaign – Stock Reduction of Hitachi Branded Fuel Filters* (2026-06-10) — “non-genuine aftermarket” / SPA net vs volume drop |
| **Price file / GM context** | Sent *RE: April results - gross profit* (2026-05-20) — references 2026 price file / FX in GM discussion (not an OEM peer list) |
| **Iveco** (candidate only) | Sent *RE: IE30 – MOU for the FY2027 incentive agreements* (2026-04-22) — Iveco/CNH channel mentioned; **not** added to approved OEM peer set |

No Inbox/Sent hits for Transit / Sprinter / DAF / MAN / Crafter / Hilux / Ranger / L200 as named **parts street peers** in the scanned window. Composio Outlook OAuth was initiated but not required once local COM scan completed.

### From memory / weekly briefs (retail IAM, not OE peers)
UK Isuzu-parts e-commerce watchlist: **Tranzparts**, **Bison Parts**, **DPF Parts Direct**; newer names **Milner Off Road**, **T&M Commercials** (Isuzu & Maxus), **FridayParts**.  
These feed IAM street / Autodoc scrapers — they do **not** replace OEM peer OE-PN mapping.

### From action-map heat (data)
At-risk €: **IUK** ≫ UTI / Germany / UMI / ITUK. Hot categories: clutch_disc, brake_pad, brake_shoe, clutch_pressure_plate, brake_rotor, fuel_filter — same basket seed filters.

### Candidate not approved
| Candidate | Status |
|-----------|--------|
| **Iveco** (Daily / light CV) | Email mention only — ask before adding to peer set |
| **Maxus** | Retailer branding (T&M) — LCV-adjacent watch, not OE peer |

---

## Basket scaffold

| File | Role |
|------|------|
| `03_analytics/isze_pricing/oem_peer_basket.csv` | Working basket (PN × peer rows) |
| `01_data/01_Pricing/_raw/oem_peer_basket_seed_20260810.csv` | Seed snapshot |

Columns: `isze_pn`, `pms_category`, `description`, `peer_market` (IUK\|GERMANY\|LCV), `peer_oem`, `peer_model`, `peer_oe_pn` (**22 unique OEs / 39+ row fills**), `peer_street_eur` (**15 OEs filled → 22 priced rows**), `source`, `notes`, `status` (`needs_map` / `needs_scrape` / `priced`).

When `peer_street_eur` is filled (≥3 priced **rows**/cat), `premiums.load_oem_benchmark_from_basket()` (via `runlog.load_config` → `apply_ceilings_to_config_block`) upgrades category `basis` → `oem_benchmark`. **Live:** `air_filter`, `oil_filter`. Near gate (n=2): blower / brake_pad / brake_rotor / fuel_filter. Remainder: `iam_derived` / placeholder.

**Eucon map limit:** 2023 COMPARABLE survey only maps **DAF / Hilux / Ranger**. Approved peers L200 / Transit / Sprinter / MAN / Crafter stay `needs_map` until a real OE source arrives — do not invent. Diagnose: `python -m isze_pricing.cli diagnose`.

---

## Scraper / crossref assets (probe)

Under `04_tools/autodoc_scraper/` (on disk):

| Asset | Feeds OEM peer street? |
|-------|------------------------|
| `autodoc_results.csv`, `ks_results.csv`, `mekonomen_results.csv`, … | **IAM** street on **Isuzu PN** — useful for `iam_derived`, not peer OE street |
| `iam_brand_tiers.csv` | Brand-quality tiers for % ceilings |
| `vehicle_search_mapper.py` | Isuzu vehicle keyword search only (D-Max/N-series) |
| `crossref_search_runner.py` | Needs `autodoc_crossrefs.csv` — **missing** on disk |
| `autodoc_crossrefs.csv` / `crossref_results.csv` | **Missing** — OE cross-ref map not built |

**Blocker for scrape:** need **peer OE PN** (or TecDoc/Autodoc vehicle+category mapping) per basket row before peer street EUR can be filled. Do not invent OE PNs or prices.

---

## Eucon mail + crossref (2026-08-10 pull)

**Mailbox (local COM):** Eucon people hit — `Rene.Herrmann@eucon.com`, `partspool@eucon.com`, plus calendar trails with Isabel Weiß / Markus Hugenroth / Pascal Riddermann. Composio Outlook OAuth was offered but not completed; COM was enough for this pass.

| Found | What it is |
|-------|------------|
| `01_data/01_Pricing/_raw/Eucon_ISUZU_Europe_OEM_IAM_Benchmark_UK_IL_2021_V02_quotation.pdf` | 2021-07-23 quote OE-1196 (UK\|IL OEM+IAM PriceSurvey). **Not** the delivered results workbook. |
| Calendar 2023-09-19 kick-off → 2024-03-21 “Review results UK market” | Study ran; mailbox lacked attachments — **rawdata now filed** from Downloads → `_raw/Eucon_PriceSurvey_*` (2026-08-10). |
| 2026-03-29 PartsPool batch (top 100; DE/DK/PT/SE/NO) | Source of `eucon_pricing` / `eucon_price_gap.csv` |

**Crossref filed (IAM, not OEM OE peers):**

| File | Rows |
|------|------|
| `01_data/01_Pricing/_raw/eucon_crossref_iam_20260329.csv` | **822** rows (45 Isuzu PN × brand/PN/country; **469** unique Isuzu↔competitor PN pairs) |
| `01_data/01_Pricing/_raw/eucon_pricing_partspool_20260329.xlsx` | Clean + Summary_by_PN (44/45) |
| `01_data/00_derived/eucon_price_gap_street_qa.csv` | Same 44 PNs + street-corrected deltas |

`oem_peer_basket.csv` notes annotated where an IAM xref exists. **Do not** put Eucon IAM competitor PNs into `peer_oe_pn` — that column is OEM peer OE only. Crossref feeds **IAM scrape / `iam_derived`**. OEM peer OE map from 2023 survey COMPARABLE is loaded; street fills are separate (see `OEM_STREET_ARRANGE.md`).

### Pricing-point QA (Mode B) — verdict

**Yes — the Eucon probe’s headline deltas are on the wrong pricing point for street conclusions.**

- Stored `Avg_Delta_pct` / workbook `Delta_vs_ISZE_pct` = online IAM EUR vs **raw IE40/PR00 list** (metadata says so explicitly).
- Correct genuine street = PR00 × 1.40 × 1.275 = **×1.785**. Not ÷0.60÷0.725 (**×2.299**).
- `build_pricing_action_map.py` already rebuilds street as `IE40 × 1.785` — use **that**, not raw `Avg_Delta_pct`.
- 2021 quote scope collected OEM **list [A]** vs IAM **list [F]** + workshop purchase **[I]** — multi-level by design; if anyone read those as “street vs street” without restating, conclusions are unreliable the same way.

Examples (PR00 → street ×1.785 vs IAM avg; no billing dump):

| PN | PR00 | Street | IAM avg | Δ vs list | Δ vs street |
|----|------|--------|---------|-----------|-------------|
| 8983767550 rotor | 79.26 | 141.48 | 87.99 | +11% (looks OK) | **−38% undercut** |
| 8974995480 air filter | 21.18 | 37.81 | 24.95 | +18% | **−34%** |
| 8982705240 oil filter | 6.80 | 12.14 | 12.32 | +81% | **+1.5%** (near parity) |

Undercut count on 44 PNs: **25 at list** vs **40 at ×1.785** (×2.299 would say 42 — even worse, wrong math).

**Recovered 2026-08-10 (Downloads → `_raw/`):** the missing **2023–24 Eucon Price Survey rawdata** (OEM + IAM):

| File | Role |
|------|------|
| `01_data/01_Pricing/_raw/Eucon_PriceSurvey_UK_2023_OEM_rawdata_20240109.xlsx` | UK OEM: `CustomerPartNumber` ↔ `CompetitorPartNumber` + brand (Ford/Toyota/DAF); 212 rows, 179 COMPARABLE |
| `01_data/01_Pricing/_raw/Eucon_PriceSurvey_ITUK_2023_OEM_rawdata.xlsx` | ITUK OEM: same map vs DAF; 138 rows, 109 COMPARABLE |
| `01_data/01_Pricing/_raw/Eucon_PriceSurvey_UK_2023_IAM_rawdata_20240109.xlsx` | UK IAM LCV+HCV (list + workshop purchase) — IAM lens, not `peer_oe_pn` |

**Hard QA:** `01_data/01_Pricing/_raw/Eucon_PriceSurvey_2023_QA.md` — **crossrefs safe; prices not street-safe.**

**Basket wire (2026-08-10, pass 2 — “do all 3”):**  
- Rows **450 → 540** (+9 Isuzu PNs from Eucon OEM COMPARABLE WANT cats via `fill_oem_peer_basket_from_eucon.py`).  
- **`peer_oe_pn` filled: 39** rows (`status=needs_scrape`) — market-aligned only (LCV Toyota/Ford Ranger, IUK|GERMANY DAF). Still skip IUK Transit←Ranger.  
- **`peer_street_eur`: 0** — Autodoc Cloudflare; KS 0 hits on peer OEs. See `01_data/01_Pricing/_raw/Eucon_PriceSurvey_2023_street_scrape_note.md`.  
- Interim IAM workshop proxy (labeled `source=eucon_iam_workshop`): `01_data/00_derived/oem_peer_street_fill_20260810.csv` — Isuzu side PR00×1.785; **not** OEM peer street / **not** `oem_benchmark`.

**Re-run 2026-08-10 evening:** `fill_oem_peer_basket_from_eucon.py` again — **0 new OE fills** (COMPARABLE WANT ceiling reached; remaining clear maps are non-WANT cats or REJECT_SUB caliper/pipe/bearing). Street still **0**; `apply_oem_benchmark` stays gated. Scrape note refreshed.

---

## Street arrange package (Jerome 2026-08-10)

Live Autodoc/KS peer-OE scrape remains blocked. **Arrange path** (no invented prices):

| Artifact | Path |
|----------|------|
| Runbook | `OEM_STREET_ARRANGE.md` |
| Fill template (22 unique OEs) | `oem_peer_scrape_list.csv` (+ FX columns for GBP→EUR labeled) |
| Ingest | `ingest_oem_peer_street.py` → writes `peer_street_eur` on basket → next `alloc` runs `apply_oem_benchmark` |

DB→DLR invoice prices are **dropped as a near-term ask**; OEM street fill is the active Layer-1 unblock. ASP/list pass-through remains the lasting DB→DLR response price axis (see `PRICE_ELASTICITY_DB_DLR_ITUK_UTI.md`).

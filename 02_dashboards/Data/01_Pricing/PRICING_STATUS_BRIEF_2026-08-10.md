# Pricing programme — internal status brief (2026-08-10 evening)

**Audience:** Jerome only (internal). No shared ship.  
**Alloc baseline:** `20260810T171626Z__alloc__t3pct` — **+3.0000% exact**.

---

## Where we are

| Track | State |
|-------|--------|
| FY27 list target | **+3% weighted** held |
| `oem_benchmark` unlocked | **air_filter**, **oil_filter** (n=6 priced rows each) |
| Street filled | **15 / 22** unique mapped peer OEs |
| Near gate (n=2) | blower_filter, brake_pad, brake_rotor, fuel_filter |
| Below gate | brake_shoe (n=1), clutch_* (DAF blanks + Toyota cover only) |
| `iam_derived` | blower / brake_pad / brake_rotor / fuel_filter (Eucon n≥3) |
| Still `placeholder` | brake_shoe, clutch_disc/kit/pressure_plate, urea (no Eucon n≥3) |
| DB→DLR | Soft **proxy** on ITUK + UTI (ASP/list pass-through). Not in deltas. UTI≠UMI |
| ZPR1 vs PR00 | Basket diagnostic CSV live (UMI/UTI separate columns) |

---

## Blocked (do not invent)

1. **Paccar/DAF dealer quotes** — 6 of 7 scrape gaps are DAF (pad / discs / fuel housing / clutch). Public web = aftermarket, FEBI, or used only.
2. **Ford shoe 1713904** — Ford Online Shop has genuine Ranger shoes at **Product No 2138025** (£148.94) but that is **not** proven as supersession of Eucon OE **1713904**. Ford Oner lining kits use other finis. Leave blank.
3. **L200 / Transit / Sprinter / MAN / Crafter OE maps** — Eucon 2023 COMPARABLE only has **DAF + Toyota Hilux + Ford Ranger**. No survey maps for the other approved peers → cannot fill `peer_oe_pn` without a fake map.
4. **Live Autodoc scrape** — Cloudflare 403.

---

## What moved this pass (no new street → no new alloc)

- Eucon COMPARABLE gap scan → `01_data/00_derived/eucon_comparable_oem_gap_20260810.csv` (329 COMPARABLE rows; unused wear-cat hits are caliper/hose/release-bearing — correctly rejected).
- Readiness + PN street-vs-Isuze (PR00×1.785) diagnostics + `python -m isze_pricing.cli diagnose`.
- Unit tests for OEM gate + FX street resolve.
- Alloc summary now includes OEM readiness block (next run).
- Scrape-list hygiene note on Ford 1713904.

**No new alloc run id** — no new genuine OEM street to ingest; +3% baseline unchanged.

---

## Next (human / unlock)

| Priority | Ask |
|----------|-----|
| 1 | One genuine **new** Paccar/DAF street quote (disc **or** pad **or** clutch) → flips a near-gate brake/clutch cat to n≥3 with LCV fills |
| 2 | Confirm whether Ford **1713904** supersedes to **2138025** (dealer EPC) — if yes, can fill shoe street from Ford shop |
| 3 | Optional: TecDoc / PartsPool OEM crossref for L200 / Transit / Sprinter cabin or fuel filter on basket Isuzu PNs |
| 4 | Second CY sell-out → upgrade DB→DLR `proxy` → `elasticity` (not a gate on soft path) |

---

## Key paths

- Engine: `C:\Users\jerom\Desktop\claude\ISZE\03_analytics\isze_pricing\`
- Arrange: `...\OEM_STREET_ARRANGE.md`
- Scrape list: `...\oem_peer_scrape_list.csv`
- Last alloc: `...\runs\20260810T171626Z__alloc__t3pct\`
- Readiness: `C:\Users\jerom\Desktop\claude\ISZE\01_data\00_derived\oem_peer_readiness_20260810.json`
- **Dashboard (shared):** `C:\Users\jerom\Desktop\claude\ISZE\02_dashboards\pricing\ISZE_Pricing_Engine_Readiness_Dashboard.html`
- Dashboard JSON: `C:\Users\jerom\Desktop\claude\ISZE\01_data\14_dashboards\pricing_engine_readiness.json`
- internal comparison notes: `C:\Users\jerom\Desktop\claude\ISZE\01_data\01_Pricing\PRICING_ENGINE_VS_CLASS_NOTES_B.md`
- Rebuild dashboard: `python 02_dashboards/pricing/_build/build_pricing_engine_readiness_dashboard.py`

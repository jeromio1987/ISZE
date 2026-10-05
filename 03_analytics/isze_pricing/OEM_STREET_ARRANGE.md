# OEM peer street — arrange package (22 OEs)

**As of:** 2026-08-10 (evening pass 2)  
**Mode:** B (internal). No shared ship.  
**Goal:** Fill street EUR for mapped peer OEs → `oem_peer_basket.csv` → `apply_oem_benchmark` on next `alloc` (+3% target unchanged).  
**Status brief:** `C:\Users\jerom\Desktop\claude\ISZE\01_data\01_Pricing\PRICING_STATUS_BRIEF_2026-08-10.md`

---

## Status

| Item | State |
|------|--------|
| Mapped unique peer OE PNs | **22** in `oem_peer_scrape_list.csv` |
| Street filled (genuine OEM retail) | **15 / 22** |
| Still `not_found` | **7** (mostly DAF brakes/clutch + Ford shoe + DAF fuel housing) |
| Live Autodoc scrape | **Blocked** (Cloudflare 403) |
| KS / Mekonomen on peer OEs | **0 hits** |
| Eucon OEM survey prices | **List GBP — not street** (do not paste) |
| Eucon COMPARABLE brands | **DAF + Hilux + Ranger only** — no L200/Transit/Sprinter/MAN/Crafter maps |
| Basket priced rows | **22** (OE street propagated across IUK+GERMANY twins + sibling Isuzu PNs) |
| `oem_benchmark` unlocked | **air_filter**, **oil_filter** (n≥3 priced rows/cat) |
| Near gate (n=2) | blower_filter, brake_pad, brake_rotor, fuel_filter |
| Last alloc (no new street this pass) | `20260810T171626Z__alloc__t3pct` +3% exact |

Do **not** invent prices. Leave blank if not found.

---

## Files

| Path | Role |
|------|------|
| `C:\Users\jerom\Desktop\claude\ISZE\03_analytics\isze_pricing\oem_peer_scrape_list.csv` | Fill template (22 rows; 15 priced) |
| `C:\Users\jerom\Desktop\claude\ISZE\03_analytics\isze_pricing\oem_peer_scrape_list.md` | Cheat sheet |
| `C:\Users\jerom\Desktop\claude\ISZE\03_analytics\isze_pricing\oem_peer_basket.csv` | Working basket (ingest target) |
| `C:\Users\jerom\Desktop\claude\ISZE\03_analytics\isze_pricing\ingest_oem_peer_street.py` | Ingest filled list → basket (propagates by OE) |
| `C:\Users\jerom\Desktop\claude\ISZE\03_analytics\isze_pricing\_build_oem_peer_scrape_list.py` | Rebuild list from basket (blank-street only) |
| `C:\Users\jerom\Desktop\claude\ISZE\03_analytics\isze_pricing\diagnose_oem_peer_readiness.py` | Gate table + peer street vs Isuze (PR00×1.785) |
| `C:\Users\jerom\Desktop\claude\ISZE\03_analytics\isze_pricing\scan_eucon_comparable_oem_gap.py` | COMPARABLE OEs not yet in basket |
| `C:\Users\jerom\Desktop\claude\ISZE\01_data\01_Pricing\_raw\Eucon_PriceSurvey_2023_street_scrape_note.md` | Why live scrape failed |
| `C:\Users\jerom\Desktop\claude\ISZE\01_data\00_derived\oem_peer_readiness_20260810.json` | Machine-readable readiness snapshot |

---

## Columns to fill (scrape list)

| Column | Required? | Rule |
|--------|-----------|------|
| `peer_oe_pn` | (filled) | Search key — do not swap |
| `peer_street_eur` | preferred | Retail / workshop purchase **EUR** |
| `peer_street_native` | alt | Price in local currency if not EUR |
| `currency` | if native | e.g. `GBP`, `USD` |
| `fx_rate_to_eur` | if native | Multiply factor (native × rate = EUR). **Label** rate source |
| `fx_as_of` | if native | ISO date of FX |
| `source` | yes when priced | Dealer site / portal / phone quote |
| `notes` | helpful | URL, quote ref, FX label |

**Isuzu compare side (not the scrape target):** genuine street = **PR00 × 1.785**. Never compare peer street to raw PR00/IE40.

---

## Jerome / next-session steps

1. Open `oem_peer_scrape_list.csv` (Excel or Sheets).
2. For each remaining blank `peer_oe_pn`, look up **street/retail** (not list). Priority: genuine DAF disc / pad / clutch (unlocks brake_rotor, brake_pad, clutch).
3. Paste EUR into `peer_street_eur`, **or** native + `fx_rate_to_eur` + `fx_as_of` + `currency`.
4. Set `source` (where it came from). Leave blanks where not found.
5. Ingest:

```powershell
cd $env:ISZE_ROOT
python 03_analytics/isze_pricing/ingest_oem_peer_street.py --dry-run   # preview
python 03_analytics/isze_pricing/ingest_oem_peer_street.py             # write basket + bak
```

6. Re-run alloc (soft-applies `oem_benchmark` when ≥3 priced peers/category):

```powershell
cd $env:ISZE_ROOT\03_analytics
python -m isze_pricing.cli alloc --set allocation.target=0.03
```

7. Check run `summary.md` / resolved config: category `basis: oem_benchmark` where n≥3.

Rebuild empty list after more OE maps:

```powershell
python 03_analytics/isze_pricing/_build_oem_peer_scrape_list.py
```

---

## Alternates tried / allowed

| Path | Use? |
|------|------|
| Manual / browser fill of scrape list | **Yes** — primary arrange path |
| GBP/USD street × labeled FX → EUR | **Yes** — use native + `fx_rate_to_eur` + `fx_as_of` |
| Ford Oner (authorized Ford wholesale) exact finis | **Yes** — used for 2586463 / 2586105 |
| Local KS / Autodoc CSVs on **Isuzu PN** | IAM only — **not** OEM peer street |
| Eucon 2023 OEM `CompetitorPrice` GBP | **No** — list, not street |
| FEBI / aftermarket titled with DAF OE | **No** — not genuine OEM retail |
| Used / like-new housing assemblies | **No** — wrong condition / part form |
| Eucon IAM workshop proxy sidecar | **No** for `oem_benchmark` (labeled IAM only) |
| Invented / guessed EUR | **No** |
| Ford shop 2138025 as stand-in for Eucon OE 1713904 | **No** until EPC supersession proven |

---

## Gate for `oem_benchmark`

`premiums.apply_oem_benchmark_to_config_block` upgrades a PMS category when the basket has **≥3** rows with `peer_street_eur > 0` in that category (row count, not unique OE). Ingest propagates one OE street to all matching OE rows (IUK+GERMANY twins, sibling Isuzu PNs). Until then allocation stays on `iam_derived` / placeholder. FY27 list move remains **+3% weighted** (separate dial).

### Remaining blockers (7 OEs)

| OE | Peer | Cat | Blocker |
|----|------|-----|---------|
| 0001436901 | DAF | brake_pad | Aftermarket OE-crossref only |
| 0001408672 | DAF | brake_rotor | Aftermarket only |
| 0001703801 | DAF | brake_rotor | FEBI listing — rejected |
| 0001707215 | DAF | fuel_filter | Housing / used only — not new element |
| 0001713904 | Ford | brake_shoe | Ford shop genuine shoes = Product No **2138025** (£148.94) — **not** proven supersession of 1713904; leave blank |
| 0001714723 | DAF | clutch_pressure_plate | Used ads only |
| 0001722449 | DAF | clutch_disc | Aftermarket / used only |

**Human ask that unlocks most:** one genuine Paccar/DAF dealer quote (new) for a disc **or** pad **or** clutch OE above → flips the matching category to n≥3 when combined with LCV Toyota/Ford fills.

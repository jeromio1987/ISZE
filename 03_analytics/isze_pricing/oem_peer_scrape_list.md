# OEM peer street — manual scrape cheat sheet

**As of:** 2026-08-10 (15/22 street filled)  
**List:** `oem_peer_scrape_list.csv` (same folder)  
**Basket:** `oem_peer_basket.csv`  
**Arrange runbook:** `OEM_STREET_ARRANGE.md`  
**Ingest:** `ingest_oem_peer_street.py` (propagates by OE across markets/PNs)  
**Audience:** internal / internal fill only — not a dashboard ship.

---

## What to fill

| Column | Rule |
|--------|------|
| `peer_oe_pn` | Already mapped — search key (do not invent / swap) |
| `peer_street_eur` | **Retail / street EUR** (preferred) |
| `peer_street_native` | Alt: price in local currency |
| `currency` | `EUR` or e.g. `GBP` when using native |
| `fx_rate_to_eur` | If native: multiply factor (native × rate → EUR); label source |
| `fx_as_of` | FX date (ISO) when converting |
| `source` | Where you got it (dealer site, parts portal, phone quote, …) |
| `priority` | 1 = IUK/DE filters·brakes · 2 = LCV filters·brakes · 3–4 = clutch / other |

After fill, run `ingest_oem_peer_street.py` (do not hand-edit basket unless you must). Leave blanks if not found — **never invent**.

---

## Isuzu compare side (not the scrape target)

When you compare peer street to Isuzu:

- Isuzu genuine street = **PR00 × 1.785** (= 1.40 × 1.275).
- Do **not** compare peer street to raw PR00/IE40 list.

---

## Do not use as street

| Bad source | Why |
|------------|-----|
| Eucon 2023 OEM survey **list GBP / OEM list** | List price, not street — see `_raw/Eucon_PriceSurvey_2023_QA.md` |
| Eucon IAM competitor PN | IAM lens — not `peer_oe_pn` / not OEM peer street |
| Autodoc/KS on **Isuzu PN** | Feeds `iam_derived`, not peer OE street |
| Invented / guessed OE or EUR | Blocks `oem_benchmark` upgrade |

---

## Scope of this list

- Working file keeps **all 22** unique mapped OEs (filled + blank).
- **15 filled** (GBP/USD native × labeled FX, or prior EUR). **7 still not_found** — see `OEM_STREET_ARRANGE.md` blocker table.
- Prefer filters/brakes and approved peers: IUK/GERMANY DAF, LCV Toyota Hilux / Ford Ranger.
- New fill sources this pass: `fordoner.com` genuine Ford (2586463 pollen, 2586105 brake lining). Rejected: FEBI-titled DAF disc, used housings.

After fill (≥3 priced basket **rows**/category), engine upgrades `basis` → `oem_benchmark` via `premiums.load_oem_benchmark_from_basket()`. Currently unlocked: **air_filter**, **oil_filter**.

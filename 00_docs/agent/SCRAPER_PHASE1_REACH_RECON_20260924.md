# Phase 1 reach recon — six platforms, 2026-09-24

**Written by:** Cursor (this laptop) · **Authority:** Jerome's scrape go, 2026-09-24 (see `DECISIONS.md`
and `00_docs/agent/CURSOR_BRIEF_SCRAPER_REDO_20260924.md` task C7).
**Purpose:** the parsers in `04_tools/delegation/parsers/` were written from *research notes*, not from
pages. Five of the six sites had no page on disk, so their parsers were stubs that raise. This pass
turned every site into a **page on disk** plus a **reachable route**, so the parsers can be finished
against something real.

Every fetch below ran `check_scrape_consent.py` first (exit 0 required) and kept ≥ 2 s between
requests to the same host. Nothing bypassed a bot check or a login.

---

## 1. Consent gate — what it says today

`python 04_tools/autodoc_scraper/check_scrape_consent.py`

| Target | Verdict |
|---|---|
| ks-international.com | allowed |
| giltechparts.com | allowed |
| **mekster.no** | **allowed** |
| **geparden.no** | **allowed** |
| **amayama.com** | **allowed** |
| **omegaspareparts.com** | **allowed** |
| **tungen-bil.no** | **allowed** |
| auto365.co.il | **BLOCKED** (retired — third line of evidence for that decision) |
| mekonomen.se | **BLOCKED** (retired) |
| tmcshop.co.uk | UNKNOWN — robots unreachable (treat as blocked) |
| autodoc.co.uk | UNKNOWN — HTTP 403 on robots |
| m-savion.co.il | UNKNOWN — HTTP 403 on robots |

`autoline.dk` was **not** in the gate's target list. It was checked directly with
`--url https://autoline.dk --path <path>` and returned ALLOWED for every path used below. The gate's
`TARGETS` list should gain it.

**Consequence for the plan:** the "six platforms" ask is really **five reachable** (Amayama, Omega,
geparden.no, mekster.no, tungen-bil.no, autoline.dk — six) — all six are allowed. `tmcshop.co.uk` and
`autodoc.co.uk` are not part of Phase 1 and remain unknown/blocked.

---

## 2. Reachable route, per site — what was actually fetched

Everything below is saved under
`01_data/90_INBOX/scrape_targets/_probe/` (the folder the parsers already treat as their evidence
home). Sizes are the bytes on disk.

| Site | Route that works | Page saved | What it is |
|---|---|---|---|
| **Amayama** | `GET /en/part/isuzu/<pn>` | `v_amayama_live.html` (97,757 B) | Live re-fetch of the same page the parser was proven on. JSON-LD `Product` intact. |
| **Omega** | `GET /?s=<pn>&post_type=product` — **redirects straight to the product page** | `v_omega_search.html` (272,754 B) | WooCommerce. The redirect target was the real N35.120 air-filter page. |
| **geparden.no** | **sitemap route**: `sitemap.xml` → `sitemaps/products-{1..5}.xml` | `v_geparden_sitemap.xml`, `v_geparden_products{1..5}.xml` | 20,000 + 20,000 + 20,000 + 20,000 + 5,967 = **85,967 product URLs**. |
| **geparden.no** | a real product page from that sitemap | `v_geparden_product.html` (45,184 B) | AC compressor, brand Lucas. JSON-LD `Product` with `sku` + `offers.price` in NOK. |
| **mekster.no** | **product sitemap** `media/no_products_google_sitemap_{1..5}.xml` | `v_mekster_sitemap_{1..5}.xml` | 50k + 50k + 50k + 50k + 29,060 = **229,060 product URLs**. |
| **mekster.no** | one real product page | `v_mekster_product.html` (1.9 MB) | JSON-LD `Product`, `sku`, `offers.price` NOK, availability OutOfStock. |
| **tungen-bil.no** | category page (the research note's URL) | `v_tungen_list.html` (168,504 B) | WooCommerce/Kadence. **One** `<table>` with the four columns the note predicted. |
| **autoline.dk** | `GET /-/reservedele/Isuzu--c456tm2615` | `v_autoline_isuzu.html` (757,870 B) | The Isuzu parts list. JSON-LD `ItemList`, **578 offers**, DKK 220–41,000. |

### Two route corrections worth keeping

**geparden.no — `/search` is disallowed, and so is the guessed product URL.**
`check_scrape_consent.py --url https://geparden.no --path /search?q=...` returns BLOCKED. The
research note's assumption that a product URL looks like `/produkt/ISU<n>` is **wrong on the live
site**: product URLs are `/products/<slug>-p-isu<oem>` (lowercase `products`, and the OEM is a slug
suffix, not the whole path). Reach them by sitemap, exactly as the note anticipated.

**mekster.no — the search path is disallowed and the coverage is thin.**
robots.txt carries `Disallow: */catalogsearch/`, and `/sok?q=` returns **HTTP 404** (the sitepath is
not what the research note guessed). Sitemap route works. **But:** across all 229,060 product URLs,
only **15 contain "isuzu"** — 6 ClimAir wind deflectors, 2 Connect2 install kits, 1 oil-filter
socket, plus Chevrolet/Isuzu stereo adapters. **mekster.no is not an Isuzu parts source.** One of the
15 is a socket tool and several are not Isuzu parts at all. Decide honestly whether it stays in
Phase 1 at a token volume or is dropped; do not report 229,060 URLs as reach.

**autoline.dk — the obvious category code is the wrong category.**
`/-/reservedele--c6` 404s and `--c6` alone is *military vehicles*. The spare-parts category is
**`--c456`**, and Isuzu sits at **`/-/reservedele/Isuzu--c456tm2615`**. Robots disallows `/search/`
and `/search.php`, so the brand-category URL is the only compliant route.

---

## 3. What each parser will actually see — from the pages on disk

### Omega (`v_omega_search.html`, GBP)

A WooCommerce product page. Two independent price points on it, and they are **not the same thing**:

- JSON-LD `Product` → `offers[0].priceSpecification[0]` = **40.80 GBP** (unit price, ex VAT —
  the aftermarket price for the FilterCraft air filter).
- A description line → **`Dealer Price: 66.86 (GBP)`** — described on the page as *"Genuine brand new
  part supplied to us from the brand dealer network"*.
- A details table carries both numbers the note mentioned: `MPN 0011765K`,
  `Manufacturer Part Number 8-97062-294-0`, `Part Manufacturer Number 8970622940`,
  `Part Manufacturer FilterCraft`, `Brand Isuzu`, `Brand Type N35.120`.
- Also `Distributed by: K.S. International` — a mention, not a price.

**The trap:** 40.80 and 66.86 are two different price types on one page. Loading both as one row, or
loading 66.86 as "our competitor's price", would be exactly the `OE RRP` mistake recorded in
`MATCH_INDEX_REPORT.md` RULE 1. The dealer line is a **separate observation** (`price_type = dealer`),
the FilterCraft price is `aftermarket_retail`.

### geparden.no (`v_geparden_product.html`, NOK)

JSON-LD `Product` gives `sku` (**a manufacturer code, e.g. `LUCACP01114` — not an Isuzu OEM**),
`brand`, `offers.price`, `offers.priceCurrency = NOK`. The page renders **inclusive of MVA**
(`6645,25 NOK inkl. MVA`) with a struck-through `6995,00` — so `vat = "incl"`.

On the genuine Isuzu products the slug carries the OEM: `-p-isu8982705240`. Only **7** such URLs
exist across products-2..5 (and **0** in products-1). So geparden's Isuzu *genuine* coverage is a
handful of parts, not a catalogue. The other 28+ "isuzu" hits are D-Max **aftermarket** items from
Lucas / ABK / ClimAir — those are `aftermarket_retail`, genuine channel **not** implied.

### mekster.no (`v_mekster_product.html`, NOK)

JSON-LD `Product` with `sku`, `mpn`, `brand` (ClimAir), `offers.price = 859`, `priceCurrency NOK`,
`availability OutOfStock`, and a seller of `mekster.no`. Price renders as `859 Nok`. B2C-style
Magento with Algolia; page weight is ~1.9 MB, so parse the JSON-LD, never the DOM text.

### tungen-bil.no (`v_tungen_list.html`, NOK ex mva)

Exactly as the note predicted and **thin**: one table, four columns
`Varenummer / Beskrivelse / Antall / Pris (ex. mva)`, and **one data row**:
`8-98214687-0 | CAP. WEEL | 1 | 737`. The part number is in the **dashed 11-digit form**
(`8-98214687-0`), so `normalise_pn()` turns it into `8982146870`. No JSON-LD anywhere.

This is the Isuzu **dealer's** own older-original-stock list, so `price_type = dealer` and
`country = "NO"`. It is trustworthy but will only ever contribute a handful of rows.

### autoline.dk (`v_autoline_isuzu.html`, DKK/SEK/EUR)

A marketplace, and **used** parts, not new. JSON-LD `ItemList` with 578 offers in the aggregate
(DKK 220–41,000) and one `Product` per `ListItem`, each with its own `offers.price` and a
**currency that is not always DKK** — the first listing is `500 SEK`. The rendered list also shows
**Isuzu OEM numbers in the title**:

```
8973675060      bagaksel til Isuzu NQR lastbil          Pris efter forespørgsel
8-98204-942-0   katalysator til Isuzu NPR lastbil        Pris efter forespørgsel
8-97261-549-2   aksel til Isuzu NPR lastbil              Pris efter forespørgsel
```

`Pris efter forespørgsel` = "price on request", i.e. **no price**. So: the OEM numbers are a real
match source, but many rows carry no price at all and must be recorded as such rather than dropped
or defaulted. `itemCondition = UsedCondition` — this is `price_type = marketplace` and must never be
mixed with a new-part price. Rows with no price are still worth keeping as **match rows with no
price**, the convention already used for `OE RRP` in `MATCH_INDEX_REPORT.md`.

---

## 4. What this changes in the task list

- **C5/C7 are now unblocked, not blocked.** Every site has a page on disk. The five stubs can be
  replaced with real parsers written against those pages.
- **Only Amayama is live-proven.** The other five parsers must earn the same status: selector first,
  assert against the saved page in a `--selftest`, and raise rather than return `[]`.
- **mekster.no and tungen-bil.no are low-yield by nature.** Report them as such; do not present URL
  counts as coverage. `gaps-need-context` applies to coverage claims too.
- **autoline.dk is used parts on a marketplace.** Valuable for matching OEM numbers, weak for price
  comparison. Keep `price_type = marketplace` and keep it apart.
- **The consent gate needs `autoline.dk` added** to `TARGETS`, and should record that
  geparden's `/search` and mekster's `/sok` are disallowed even though the domains are allowed.

## 5. Files this recon produced

Probe scripts (read-only helpers, no parser logic):
`_probe_live_20260924.py`, `_probe_save_pages_20260924.py`, `_probe_shapes_20260924.py`,
`_probe_inspect_20260924.py`, `_probe_fragments_20260924.py`, `_probe_route{,2,3,4,5,6,7,8}_20260924.py`
— all under `04_tools/aftermarket_intelligence/`.

Pages and sitemaps: `01_data/90_INBOX/scrape_targets/_probe/` (listed in §2 above, plus
`v_geparden_products{2..5}.xml`, `v_mekster_sitemap_{1..5}.xml`, `v_autoline_spareparts.html`,
`v_mekster_home.html`, `v_mekster_robots.txt`, `v_autoline_robots.txt`, `v_ks_search.html`).

Shared fetch/consent layer: `04_tools/delegation/parsers/fetch_polite.py` — the single place a
Phase 1 request may open a connection (consent first, ≥ 2.2 s per host, cache to disk).

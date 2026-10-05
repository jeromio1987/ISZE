# Phase 1 parser build — work order for parallel agents (2026-09-24)

**For:** Cursor sub-agents working on Jerome's laptop · **Owner of the brief:** Cursor (main session)
**Authority:** Jerome's scrape go, 2026-09-24. Task **C7** in
`00_docs/agent/CURSOR_BRIEF_SCRAPER_REDO_20260924.md`; plan and data rules in
`00_docs/agent/SCRAPER_REDO_DELEGATION.md` §3, §5, §8.
**Read first:** `00_docs/agent/SCRAPER_PHASE1_REACH_RECON_20260924.md` — it names the page on disk for
every site and the exact fragments each parser must read.

---

## The job in one sentence

Replace the five stub parsers in `04_tools/delegation/parsers/price_parsers.py` with **real parsers,
each written and asserted against a page that is already saved on disk**, so that no fetch is needed
to prove the parser works, and a parser that finds nothing **fails loudly** instead of returning an
empty list.

**STATUS 2026-09-24, end of session: DONE.** Seven site modules exist and all seven pass
(`run_probe.py` → 7/7 sites OK; `price_parsers.py --selftest` → ALL SELFTESTS PASS). The FX blocker
below is closed. Outstanding is the ledger loader that reads these parsers and writes rows — the
parsers produce rows, nothing loads them yet.

---

## Module layout — do not all edit one file

`price_parsers.py` currently holds Amayama (working) plus four stubs that raise. Split it so six
agents can work without colliding:

```
04_tools/delegation/parsers/
  fetch_polite.py        # ALREADY WRITTEN — the only place a request opens a connection
  ledger_schema.py       # ALREADY WRITTEN — COLUMNS / PRICE_TYPES / MATCH_METHODS / normalise_pn
  _selftest_schema.py    # ALREADY WRITTEN — asserts the schema still matches the ledger
  site_amayama.py        # leave alone: already proven
  site_omega.py          # NEW
  site_geparden.py       # NEW
  site_mekster.py        # NEW
  site_tungen.py         # NEW
  site_autoline.py       # NEW
  site_ks.py             # NEW
  registry.py            # NEW — maps name -> parser, used by the runner
  run_probe.py           # NEW — parses every saved page and prints rows
  price_parsers.py       # keep as a thin shim re-exporting from the modules above
```

Every site module exposes exactly:

```python
SITE = "omega"
PROBE_PAGE = "v_omega_search.html"        # in 01_data/90_INBOX/scrape_targets/_probe/
COUNTRY = "UK"

def parse(html: str, *, source_url: str = "", observed_at: str = "") -> list[dict]: ...
def selftest() -> int: ...                # returns 0 on pass, non-zero on failure
```

## The rules — non-negotiable

1. **No parser may fetch.** Fetching goes through `fetch_polite.py` and only from a runner, never from
   `parse()`. `parse(html, ...)` takes HTML that is already in memory.
2. **A parser that returns `[]` must be a real answer, not a failure.** If the page's structure is
   missing, **raise** (a `ParseError` you define) so an empty result can never be mistaken for "site
   had no price". This is the Mekonomen lesson: seven false prices sat in a dashboard for six weeks
   because a scraper returned something instead of nothing.
3. **Selector-first.** Read the JSON-LD / CSS selector. Do **not** send anything to DeepSeek from a
   parser; DeepSeek is only a fallback the *runner* may call, and never with Eucon rows (below).
4. **`price_type` and `vintage` are mandatory.** Copy the allowed values from `ledger_schema.py`.
5. **Never mix price types.** Each row carries exactly one. In particular:
   - a genuine/Isuzu-dealer price is **not** the same observation as an aftermarket price on the same
     page (Omega has both — see below);
   - a used marketplace listing is not a new-part price (autoline).
6. **No invented numbers.** If a page shows no price, emit a row with `price=None` and say so in
   `stock`/`fx_note`, or omit the row — never default a price, never convert a currency by hand.
7. **The DeepSeek boundary holds.** Eucon-sourced match rows must never be sent to DeepSeek or any
   outside-EU service. Parsers here must not call DeepSeek at all; if the runner ever does, it uses
   public page text only.
8. **No deletes, no scheduled-task edits, no bat/ps1/yaml edits.** Those need Jerome's explicit yes.
9. **`check_scrape_consent.py` before every fetch**, exit 0 required. `fetch_polite.py` already does
   this — do not work around it.

---

## Per-site evidence — the exact fragments

Every page below is on disk at
`C:\Users\jerom\Desktop\claude\ISZE\01_data\90_INBOX\scrape_targets\_probe\`.

### Omega — `v_omega_search.html` (272,754 B) · `COUNTRY="UK"` · GBP

WooCommerce. Reach: `GET https://omegaspareparts.com/?s=<pn>&post_type=product` **redirects straight
to the product page.** Robots disallows `/wp-json/`, so HTML route only.

JSON-LD `Product` (one block, `@type=Product`):
- `name`: `0011765K Isuzu N35.120 EURO5b+ Air Filter Element 2008 onward`
- `sku`: `9294` (their internal code — **not** an Isuzu number)
- `brand.name`: `Isuzu`
- `offers[0].priceSpecification[0].price` = `"40.80"`, `priceCurrency` = `"GBP"` ← aftermarket price

The details table carries:
`MPN 0011765K` · `Manufacturer Part Number 8-97062-294-0` · `Part Manufacturer Number 8970622940` ·
`Part Manufacturer FilterCraft` · `Brand Isuzu` · `Brand Type N35.120` · `Condition New`

In the description:
`Dealer Price: 66.86 (GBP)` — the page says it is *"Genuine brand new part supplied to us from the
brand dealer network"*.

**Two rows, not one.** The 40.80 is `price_type="aftermarket_retail"`. The 66.86 is a separate
observation, `price_type="dealer"`. Both share `part_no="8970622940"` (from the 10-digit
manufacturer number), `match_method="exact_oem"`, `source="Omega"`, `source_url=<final url>`.
Loading both as one row, or loading 66.86 as "the aftermarket price", is the `OE RRP` mistake.

### geparden.no — `v_geparden_product.html` (45,184 B) · `COUNTRY="NO"` · NOK

JSON-LD `Product`: `sku="LUCACP01114"` (**a manufacturer code, not an Isuzu OEM**), `brand="Lucas"`,
`offers.price`, `offers.priceCurrency="NOK"`, and a nested `priceSpecification.price="6995"` — the
struck-through before-price. The visible price is `6645,25 NOK inkl. MVA`, so `vat="incl"`.

**Where the Isuzu number comes from:** not the JSON-LD. It is in the URL slug on genuine products:
`...-p-isu8982705240`. Use the slug; if there is no `-p-isu<digits>` suffix, there is **no Isuzu part
number** on that page — do not invent one, and do not use the manufacturer SKU as if it were one.

**Two channels on this site, and they are different rows:**
- slug has `-p-isu<oem>` and the title says *genuine Isuzu* → `price_type="genuine_grey"`
- title is a D-Max aftermarket part (Lucas, ABK, ClimAir, …) → `price_type="aftermarket_retail"`
  and `competitor_brand` is the real brand

Coverage reality to record in the selftest output, not to hide: across products-1..5 there are
**7** `-p-isu<digits>` URLs, **0** in products-1. Geparden's *genuine* Isuzu coverage is a handful.

### mekster.no — `v_mekster_product.html` (1.9 MB) · `COUNTRY="NO"` · NOK

JSON-LD `Product`: `name="Vindavviser, Foran - Isuzu D Max"`, `sku="TP2268CL3533"`,
`mpn="TP2268CL3533"`, `brand.name="ClimAir"`, `offers[0].price=859`, `priceCurrency="NOK"`,
`availability="…/OutOfStock"`, `seller.name="mekster.no"`. Page renders as `859 Nok`.

Page weight is ~1.9 MB with Algolia markup — **parse the JSON-LD only**, never the DOM text.

`map` the availability URL to `stock`: `InStock`→`"in"`, `OutOfStock`→`"out"`, other→`"unknown"`.

`price_type="aftermarket_retail"` (ClimAir is a real aftermarket brand). There is no Isuzu OEM number
on this page, so `part_no` will be `None` and the row should be emitted as a **category/match row with
no Isuzu number** — or skipped. Say which you chose in the docstring and the selftest output.

Reality to record: 229,060 product URLs, and only **15** mention Isuzu (6 ClimAir wind deflectors, 2
Connect2 kits, 1 oil-filter socket, stereo adapters). This site is **not** an Isuzu parts source.

### tungen-bil.no — `v_tungen_list.html` (168,504 B) · `COUNTRY="NO"` · NOK ex mva

WooCommerce/Kadence, **no JSON-LD**. One `<table>` with headers
`Varenummer / Beskrivelse / Antall / Pris (ex. mva)` and exactly **one** data row:

```
8-98214687-0 | CAP. WEEL | 1 | 737
```

`price_type="dealer"` — this is the Isuzu dealer's own older-original-stock list, and must never be
mixed with aftermarket. `vat="excl"` (the column says ex. mva). `normalise_pn("8-98214687-0")` →
`8982146870` (the dashed 11-digit form is the trap here).

A parser that finds zero data rows in a table whose header it *did* recognise must **raise**, not
return `[]`.

### autoline.dk — `v_autoline_isuzu.html` (757,870 B) · `COUNTRY="DK"` · DKK/SEK/EUR

Reach: `GET https://autoline.dk/-/reservedele/Isuzu--c456tm2615` (brand-category URL).
Robots disallows `/search/` and `/search.php`. `--c6` alone is **military vehicles** — the spare-parts
category is `--c456`.

Two shapes on the page, and they need different handling:

**1. JSON-LD `ItemList`** — `offers` is an `AggregateOffer` (`priceCurrency DKK`, `offerCount 578`,
`lowPrice 220`, `highPrice 41000`) and `itemListElement[]` is one `Product` each:
`name`, `url`, `brand.name`, `description`, and its own
`offers.price` + `offers.priceCurrency` + `offers.availability` + `offers.itemCondition`.
**The currency is per-listing and is not always DKK** — the first listing is `500 SEK`. Read it per
row; never assume the aggregate's currency.

**2. The rendered list** carries Isuzu OEM numbers in the title, e.g.
```
8973675060      bagaksel til Isuzu NQR lastbil      Pris efter forespørgsel
8-98204-942-0   katalysator til Isuzu NPR lastbil    Pris efter forespørgsel
8-97261-549-2   aksel til Isuzu NPR lastbil          Pris efter forespørgsel
```
`Pris efter forespørgsel` = "price on request" → **no price**. Emit those as match rows with
`price=None` and record that honestly (the `OE RRP` convention: a match row with no price). Do not
default a price, do not drop the OEM number.

`price_type="marketplace"` and `itemCondition=UsedCondition` — **used parts**. Never blend with a new
price. `match_method="exact_oem"` when the OEM number came from the title.

### KS International — `v_ks_search.html` (2.4 MB) · `COUNTRY="UK"` · GBP

Magento, server-side. Existing working scraper: `04_tools/autodoc_scraper/ks_scraper.py` — read it,
do not duplicate its logic. Page has `.product-item`, `.price-excluding-tax .price`,
`.price-including-tax .price`, `.product-sku`, `#genuine` badge, `.stock.unavailable`.
`sitemap.xml` is allowed (6,453 Isuzu URLs per the plan).

`price_type`: aftermarket items → `"aftermarket_retail"`; GENUINE-badged items → `"genuine_grey"`.
`vat="excl"` when using the excluding-tax price (that is what matches our list price basis).

---

## The FX blocker — RESOLVED 2026-09-24, and how

The ledger's FX table was `FX = {"EUR": 1.0, "GBP": 1.17, "SEK": 0.089}`, and `validate()` refuses any
row whose currency is not in it. **Every new site prices in NOK, DKK or USD**, so every new row would
have been refused before it could be stored.

That is now fixed centrally, in `04_tools/price_ledger/build_price_ledger.py`:
- `04_tools/price_ledger/build_fx_rates.py` writes `04_tools/price_ledger/fx_rates.json` from the
  **European Central Bank's daily euro reference rates** (public, dated, citable). One run.
- The ledger reads that file and adds any currency the working table lacked — **additively**. EUR,
  GBP and SEK keep the rates the existing 1,081 rows were built with, so **no stored euro value
  moves**. Verified: `python 04_tools/price_ledger/_check_fx_change_20260924.py` compares the ledger
  before and after the change and reports 0 rows with a moved `price_eur`.
- NO/NOK, DK/DKK and USD are now convertible. The ECB also publishes a slightly different GBP
  (1.1630 vs 1.17) and SEK (0.0888 vs 0.089); rebasing those is **Jerome's call and was not done**.

**What parsers should now do:** carry the native currency and price, and set
`price_eur = round(price * rate, 2)` using the rate for that currency from `fx_rates.json`, with
`fx_note` naming the source and reference date. If a parser already wrote a `fx_note` saying there is
no rate, that string is now stale — the orchestrator will normalise it.

---

## Acceptance — what "done" means per site

1. `python 04_tools/delegation/parsers/run_probe.py --site <name>` parses the saved page and prints the
   rows it found.
2. `python .../site_<name>.py --selftest` **asserts** the real values from that page (part number,
   price, currency, price_type, vat) and returns non-zero if any assertion fails. Assertions must be
   from the page, not from your expectation of what the page should say.
3. A deliberately-broken input (e.g. `parse("")` or a page with the structure removed) **raises** or
   returns a documented empty answer — never silently returns `[]` for a recognised-but-empty page.
4. The module docstring states the evidence status: which page, how many bytes, what was verified.
5. `python .../price_parsers.py --selftest` still passes (the Amayama assertion must not regress).

Report back in `04_tools/delegation/CURSOR_REPORT_20260924.md` (append a section) and one row on
`00_docs/agent/DELEGATOR_BOARD.md` per finished site.

# Auto 365 — no OEM part-number join key

**Date:** 2026-08-14  
**Verdict:** Auto 365 product pages do **not** carry a labeled Isuzu OEM part number. Do **not** write `iam_israel_price_gap.csv`. Family-level street stays in `ISZE\01_data\00_derived\iam_israel_street.csv`.

The listing scrape (`auto365_results.csv`, 208 rows) has no PN column. Identifiers on the site are:

| Field | What it is |
|---|---|
| URL `/product/{id}/` | Internal catalog id (e.g. 5108, 28585) |
| Hebrew `מק"ט` (SKU) | Same internal id, not an Isuzu 10-digit OEM |
| Hebrew title | Model + year range + part family (D-MAX / Sumo / Trooper / Rodeo) |
| Price | ILS is authority. `Price_EUR` uses scraper placeholder `ILS_EUR=0.25` — indicative only |

## Pages checked (curl_cffi chrome, HTTP 200)

Fetched 2026-08-14 from `auto365_oem` probe (`_probe_auto365_oem.py`). No JSON-LD `mpn` / `sku` / `partNumber`. No OEM label next to a 10-digit Isuzu PN.

| Product id | URL | Hebrew title (short) | Identifiers found |
|---|---|---|---|
| 5108 | https://www.auto365.co.il/product/5108/ | סומו פנס ראשי שמאל 2008–2018 | מק"ט 5108. WhatsApp `0506839743` (phone, not a PN). |
| 5128 | https://www.auto365.co.il/product/5128/ | D-MAX פנס ראשי שמאל 2007–2012 | מק"ט 5128. Same WhatsApp false-positive. |
| 5134 | https://www.auto365.co.il/product/5134/ | D-MAX מראה דלת שמאל 2004–2006 | מק"ט 5134. |
| 9444 | https://www.auto365.co.il/product/9444/ | רדיאטור מים טרופר דיזל 1993–2004 | מק"ט 9444. |
| 19740 | https://www.auto365.co.il/product/19740/ | D-MAX פנס ראשי ימין LED 2017–2019 | מק"ט 19740. |
| 27563 | https://www.auto365.co.il/product/27563/ | D-MAX מגן קדמי LS/LSE 2020–2022 | מק"ט 27563. |
| 28585 | https://www.auto365.co.il/product/28585/ | D-MAX פנס ראשי ימין+לד 2020–2024 | מק"ט 28585. See image-filename note below. |
| 29547 | https://www.auto365.co.il/product/29547/ | D-MAX מראה ימין 2020–2024 שחור | מק"ט 29547. |

**Site-wide false positive:** every page contains `0506839743` inside `https://api.whatsapp.com/send?phone=972506839743` (Israeli mobile 050-683-9743). Not a part number.

## Image filenames are not an OEM field

On product **28585** only, two 10-digit strings that look like Isuzu PNs appear as **image asset names**, not as product metadata:

- `og:image` → `/cache/w_600/8983287637.jpeg` — IE40 has `8983287637` = LAMP ASM; HEAD (€328.15). Same family as this listing, but the number is never labelled OEM / מק"ט מקורי.
- Related-product thumb → `/cache/.../8974882820.jpg` with alt text for a **rear** lamp. IE40 has `8974882820` = LAMP UNIT; RR COMB. That is a **different** part.

Using image filenames as a PN key would mix related-product thumbs into the join. 7 of 8 sampled pages have **no** such filename. This is not a catalog OEM index.

## What this means for the operating dashboard

- Keep `iam_israel_street.csv` (family min/avg/max, ILS median). Local Israel street context only.
- Do **not** fabricate a PN-shaped gap file from Hebrew titles or internal מק"ט.
- UMI/UTI PN-level street coverage must come from scrapers that already search by Isuzu PN (KS International first; Mekonomen has a real PN column and a handful of `ok` rows). See `build_iam_street_joins.py`.

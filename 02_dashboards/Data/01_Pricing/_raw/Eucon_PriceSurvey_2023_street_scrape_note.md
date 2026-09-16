# Eucon / OEM peer street scrape note (2026-08-10)

**Verdict (live Autodoc/KS):** Peer OE retail/street scrape **not usable** via Autodoc/KS. Autodoc DE = Cloudflare 403. KS International = HTTP 200 but **0 prices** on probed peer OE PNs (site is Isuzu-centric; peer Toyota/Ford/DAF OEs not stocked). Mekonomen probe also empty on sample Toyota OEs.

**Verdict (manual arrange, evening pass):** **15 / 22** unique peer OEs filled with **genuine OEM retail** (GBP/USD × labeled FX). Ingest propagates by OE → **22** priced basket rows. `oem_benchmark` unlocked for **air_filter** + **oil_filter**. See `03_analytics/isze_pricing/OEM_STREET_ARRANGE.md`.

## Probe summary (automated)
- Unique mapped peer OE PNs probed: **22**
- KS price hits: **0**
- Autodoc Cloudflare hits: **22**
- Basket rows with `peer_street_eur` from Autodoc/KS: **0**

## Manual street fills (genuine only)
- Sources used: cheapivecoparts / gfnparts / arnoldclark / jdmgarage / ehybrid / tpuk / roughtrax / toyotapartsdeal / cars245 / **fordoner.com** (authorized Ford wholesale).
- Rejected this pass: FEBI-titled DAF disc (1703801), used/like-new fuel housings (1707215), aftermarket OE-crossref pads/discs/clutch.
- FX: open.er-api.com GBP→EUR 1.167208 / USD→EUR 0.865507 as_of 2026-08-10.

## Interim (labeled only — not oem_benchmark)
- IAM survey **Workshop Purchase Price** → sidecar `01_data/00_derived/oem_peer_street_fill_20260810.csv` with `source=eucon_iam_workshop` for mapped Isuzu PNs.
- Isuzu compare side: **PR00 × 1.785** (genuine street).
- **OEM `CompetitorPrice` GBP list:** not used (not street).

## Do not
- Do not feed OEM list GBP or IAM list into `oem_benchmark`.
- Do not treat IAM workshop proxy as OEM peer street.
- Do not invent OE PNs or street EUR.

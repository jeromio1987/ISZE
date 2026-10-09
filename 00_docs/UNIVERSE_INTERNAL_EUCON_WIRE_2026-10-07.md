# INTERNAL Eucon survey wire — 2026-10-07

## Verdict

Eucon UK IAM survey prices (list + workshop) are wired into INTERNAL AIM market panels as a **separate observation stream**, labelled **Eucon survey** — not shop scrape. Delivery is missing on every survey ledger row, so the panel correctly keeps them **not shop-eligible** (`DELIVERY_BASIS_NOT_STATED`). ACCEPT / SYNTHETIC was not touched.

## Counts

| Stream | Offers | Shop-eligible on panel | Cases carrying them |
|---|---:|---:|---:|
| KS coverage-eligible shop (unchanged) | **17** | **17** | 12 |
| Eucon survey (new) | **6** | **0** | **3** |

Of the twelve UK coverage-eligible PNs, only **three** have UK `eucon_survey_2023` rows on disk. The other nine have no UK survey list/workshop price to attach (continental Eucon online/crossref exists for some, but that is not this survey stream).

## Cases with Eucon survey offers

| Case | Part | Eucon offers | Panel result |
|---|---|---:|---|
| `ITUK-AIR-062-ELIG` | 8970622940 air cleaner filter | **2** (list + workshop) | both ineligible — delivery not stated |
| `ITUK-FUEL-159-ELIG` | 8981596930 fuel filter element kit | **2** (list + workshop) | both ineligible — delivery not stated |
| `ITUK-OIL-ELIG` | 8982705240 oil filter | **2** (list + workshop) | both ineligible — delivery not stated |

Observation IDs:

- Air 8970622940: `91492ef0227bf731` (survey_workshop £39.10), `dbd73f8985084669` (survey_list £48.22)
- Fuel 8981596930: `0ce3a2e0349ff84c` (survey_workshop £10.65), `7155928f23692e84` (survey_list £26.11)
- Oil 8982705240: `7837a510623969b9` (survey_workshop £9.20), `7cf03d23a70202c4` (survey_list £24.53)

Seller on every row: **Eucon survey**. Kind: `Eucon survey list` / `Eucon survey workshop`. Freshness text states not a shop scrape and not shop-eligible without delivery.

## PNs in the twelve with no UK Eucon survey

8974995480, 8975546610, 8976739570, 8981394280, 8981402650, 8981941190, 8982399830, 8982831940, 8983214130 — KS shop rows only on those hooks.

## How they attach

1. `tools/connect_real_feeds.py` → `build_eucon_survey_offers()` reads `eucon_survey_2023` UK `survey_list` / `survey_workshop` rows for the twelve coverage PNs from `price_observations.parquet` (U29b ledger, same as the shop wire). Writes `eucon_survey_offers` / `eucon_survey_cases` into `payload/real_feeds.local.json`. Delivery fields are **omitted** (never invented).
2. `tools/attach_real_feeds_to_payload.py` puts those offers into `payload.offers` with IDs `EUCON-SURVEY-*`, and **appends** them to the existing ITUK-*-ELIG case `offers` lists beside the KS rows.
3. Rebuild: `python tools/build.py --payload payload/aim_payload_u29c_real_feeds.local.json` from the AIM root on `ISZE_u29c_ids_ituk_pt`.

Panel proof (Node run of `comparable.js`): KS eligible stays **17**; Eucon survey eligible **0** / ineligible **6**.

## Paths

- Worktree payload: `C:\Users\jerom\Desktop\claude\_worktrees\ISZE_u29c_ids_ituk_pt\Isuzu Universe\05_AIM_Universe\payload\aim_payload_u29c_real_feeds.local.json`
- Worktree feeds block: `C:\Users\jerom\Desktop\claude\_worktrees\ISZE_u29c_ids_ituk_pt\Isuzu Universe\05_AIM_Universe\payload\real_feeds.local.json`
- Worktree INTERNAL HTML: `C:\Users\jerom\Desktop\claude\_worktrees\ISZE_u29c_ids_ituk_pt\Isuzu Universe\05_AIM_Universe\dist\ISZE_AIM_Pricing_Decisions_v04_INTERNAL.html`
- Main clone copy: `C:\Users\jerom\Desktop\claude\ISZE\Isuzu Universe\05_AIM_Universe\dist\ISZE_AIM_Pricing_Decisions_v04_INTERNAL.html`
- Proof JSON: `C:\Users\jerom\Desktop\claude\_worktrees\ISZE_u29c_ids_ituk_pt\Isuzu Universe\05_AIM_Universe\dist\_eucon_wire_proof_20261007.json` (also copied under main `dist\`)

## Not done / still true

Eucon remains primary; UK shop eligible is still **17** (below the 50-row bar). Survey prices paint for honesty beside the three PNs that have them; they do not unlock a billing move or a price action. ACCEPT was not opened.

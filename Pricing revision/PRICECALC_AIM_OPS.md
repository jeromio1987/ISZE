# PriceCalc with AIM — operating rules

As of 2026-10-07.

## Two tools, two jobs

| Job | Open |
|---|---|
| Price one new or superseded part into SAP today | `01_data\01_Pricing\ISZE_PriceCalc_AIM_20261007.xlsx` (double-click `OPEN_PriceCalc_AIM.cmd` in this folder) |
| Portfolio view: base-price step, FX, stack, AIM by family | This folder’s pack via `OPEN_Pricing_revision.cmd` |

Do not retire PriceCalc because the revision HTML exists. The revision pack does not build SAP Fast Entry rows.

## Rate authority

Live dials live in `03_analytics\isze_pricing\config.yaml`. The AIM PriceCalc Config sheet was aligned to that file on 2026-10-07:

- FX **178.5** (was 163.7 on v3)
- Source J **0.673** (was 0.62)
- Source T **0.611** (unchanged)
- Class T factor **0.60** → **40% GM** (was 0.80 / 20% GM on v3)
- CIS flat **0.40** → **60% GM**

When rates move, refresh Config from `config.yaml`. Do not keep a second living rate book.

## Day-to-day on New Parts

1. Paste the IML website line.
2. Set Source (J/T) and Price List (PR00 / ISR…).
3. Pricing Class still comes from the IML class letter for SAP.
4. Paste the AIM level-1 family in column **AO**. Target %GM and CHECK mode fill from **AIM Margin Lookup**.
5. Copy the SAP zone into the matching SAP Output sheet / Fast Entry.

## Supersession

Old PN → newest PN: inherit the predecessor’s AIM category. Keep price continuity unless the yen base-price step forces a move. Newest Part No. drives Material. Do not re-open the category debate on every supersession.

## Truly new PN

Assign AIM level-1 first. Read **AIM Margin Lookup** for the target %GM. FOB is still yen BP ÷ FX × source discount. Only the margin step becomes AIM-led once Spec Q1 is answered yes.

## Until Spec Q1 is yes

SAP still follows the IML class letter. AIM target is a **CHECK** only: class implies X% GM; the AIM family wanted Y%. See `PRICECALC_AIM_VOICE_ASK.md`.

## Companion files

- Margin table (CSV): `01_data\01_Pricing\aim_category_target_gm_20261007.csv`
- Builder (re-run after config or AIM master changes): `01_data\91_build\build_pricecalc_aim_20261007.py`
- Legacy v3 (stale Config — do not use for new pricing): `91_legacy\Isuzu\Divers\ISZE_PriceCalc_2026_v3.xlsx`

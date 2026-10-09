# INTERNAL eligible UK shop wire — 2026-10-07

## Verdict

All **162** coverage-eligible UK `exact_oem` shop rows (wider cut, **41** PNs) now sit on INTERNAL AIM market panels as comparable offers, not only as a metadata count. Forty-one ITUK case hooks carry them (**152** KS + **10** Omega). ACCEPT / SYNTHETIC was not touched. Eucon survey remains a separate stream (6 offers / 3 PNs), labelled ineligible (no delivery).

Focus usable (oil filter + brake pad) is **58** of those 162. **Both** the focus and wider cuts now meet the 50-row sufficiency bar.

## Cases updated

| Case | Part | Eligible shop offers |
|---|---|---:|
| `ITUK-CLT-131-ELIG` | 1313100120 clutch kit | **6** |
| `ITUK-CLT-587-ELIG` | 5876101040 clutch kit | **2** |
| `ITUK-OIL-049-ELIG` | 8970497081 oil filter element | **2** |
| `ITUK-AIR-062-ELIG` | 8970622940 air cleaner filter | **22** |
| `ITUK-PAD-947-ELIG` | 8970947100 front brake-pad set | **2** |
| `ITUK-PAD-138-ELIG` | 8971138880 front brake-pad set | **2** |
| `ITUK-OIL-148-ELIG` | 8971482800 oil filter element | **2** |
| `ITUK-OIL-167-ELIG` | 8971679720 oil filter element | **1** |
| `ITUK-FUEL-172-ELIG` | 8971725491 fuel filter element kit | **8** |
| `ITUK-CLT-255-ELIG` | 8972553130 clutch kit | **4** |
| `ITUK-OIL-301-ELIG` | 8973017520 oil filter element | **3** |
| `ITUK-OIL-309-ELIG` | 8973099270 oil filter element | **1** |
| `ITUK-OIL-329-ELIG` | 8973299110 oil filter element | **6** |
| `ITUK-OIL-358-ELIG` | 8973587200 oil filter | **1** |
| `ITUK-AIR-499-ELIG` | 8974995480 air cleaner filter | **4** |
| `ITUK-OIL-543-ELIG` | 8975439050 oil filter element kit | **6** |
| `ITUK-PAD-ELIG` | 8975546610 brake pad kit | **8** |
| `ITUK-AIR-673-ELIG` | 8976739570 air cleaner filter | **6** |
| `ITUK-CLT-622-ELIG` | 8979466221 clutch-related | **1** |
| `ITUK-CLT-626-ELIG` | 8979466261 clutch-related | **1** |
| `ITUK-CLT-900-ELIG` | 8979490060 clutch-related | **1** |
| `ITUK-OIL-018-ELIG` | 8980188580 oil filter element | **12** |
| `ITUK-AIR-421-ELIG` | 8980714210 air cleaner filter | **12** |
| `ITUK-AIR-422-ELIG` | 8980714220 air cleaner filter | **10** |
| `ITUK-AXL-ELIG` | 8980806782 drive half axle shaft | **4** (Omega) |
| `ITUK-FUEL-095-ELIG` | 8980959830 fuel filter | **2** |
| `ITUK-OIL-124-ELIG` | 8981240801 oil filter gasket | **1** |
| `ITUK-BLW-ELIG` | 8981394280 blower unit filter | **1** |
| `ITUK-AIR-140-ELIG` | 8981402650 air cleaner filter | **1** |
| `ITUK-FUEL-159-ELIG` | 8981596930 fuel filter element kit | **4** |
| `ITUK-OIL-165-ELIG` | 8981650710 oil filter element | **3** |
| `ITUK-CLT-169-ELIG` | 8981698261 release bearing | **4** |
| `ITUK-FUEL-194-ELIG` | 8981941190 fuel filter element kit | **1** |
| `ITUK-FUEL-239-ELIG` | 8982399830 fuel filter assembly | **1** |
| `ITUK-EXH-247-ELIG` | 8982476961 exhaust | **1** |
| `ITUK-OIL-ELIG` | 8982705240 oil filter | **10** |
| `ITUK-CLT-ELIG` | 8982831940 clutch pressure plate | **3** |
| `ITUK-AIR-321-ELIG` | 8983214130 air cleaner filter | **3** |
| `ITUK-EXH-365-ELIG` | 8983656821 exhaust | **1** |
| `ITUK-EXH-ELIG` | 8983682091 exhaust pipe (`PIPE; EXH`) | **3** |
| `ITUK-CLT-375-ELIG` | 8983753330 clutch disc | **2** |

**Totals:** 41 cases · **162** eligible shop offers painted (KS 152 + Omega 10). Eucon survey on three of those hooks stays labelled ineligible.

Growth vs the prior INTERNAL wire (151 / 38): **+11** KS rows after focus-close Magento PDP **OE Equivalent Part Number** upgrades on leftover oil/pad SKUs (see `UNIVERSE_UK_KS_FOCUS_CLOSE_2026-10-07.md`). Three new focus case hooks (`ITUK-PAD-947-ELIG`, `ITUK-PAD-138-ELIG`, `ITUK-OIL-358-ELIG`) so every wider-eligible PN paints.

KS rows: VAT excl + KS £10 mainland carriage + `exact_oem` (including PDP-upgraded `loader=ks` rows). Omega rows: VAT incl 20% (Terms of Business) + UK Free Economy £0 from Store API (`delivery_included=yes`). Wider coverage evidence marks all 162 `eligible=true`. No prices invented.

## How they attach

1. `tools/connect_real_feeds.py` reads only U29b **wider** rows that coverage evidence marks eligible and whose PN is in `eligible_pns_detail` from `market_data_gap_coverage_uk_wider_exact_20261007.metrics.json`, and writes them into `payload/real_feeds.local.json`. Seller / tax / delivery text follows loader: KS vs Omega. `loader=ks` (PDP OE path) is treated as KS International.
2. `tools/attach_real_feeds_to_payload.py` puts those offers into `payload.offers`, creates the forty-one minimal ITUK case hooks, and points each case at its offer IDs with `observation_declarations` (`exact_part_number`, `per_piece`, delivery + FX from the U19 wider stage / ledger).
3. Rebuild: `python tools/build.py --payload payload/aim_payload_u29c_real_feeds.local.json` from the AIM root on `ISZE_u29c_ids_ituk_pt`.

Proof: `...\dist\_eligible_wire_proof_20261007.json` (shop unique **162**, cases **41**, Omega **10**, KS **152**, Eucon **6** separate).

## Paths

- Worktree payload: `C:\Users\jerom\Desktop\claude\_worktrees\ISZE_u29c_ids_ituk_pt\Isuzu Universe\05_AIM_Universe\payload\aim_payload_u29c_real_feeds.local.json`
- Worktree INTERNAL HTML: `C:\Users\jerom\Desktop\claude\_worktrees\ISZE_u29c_ids_ituk_pt\Isuzu Universe\05_AIM_Universe\dist\ISZE_AIM_Pricing_Decisions_v04_INTERNAL.html`
- Main clone copy: `C:\Users\jerom\Desktop\claude\ISZE\Isuzu Universe\05_AIM_Universe\dist\ISZE_AIM_Pricing_Decisions_v04_INTERNAL.html`
- Proof JSON: `...\dist\_eligible_wire_proof_20261007.json`
- Eligibility source (wider): `C:\Users\jerom\Desktop\claude\_worktrees\ISZE_u29b\01_data\00_derived\market_data_gap_coverage_uk_wider_exact_20261007.metrics.json`
- Wider evidence / stage: `...\91_build\_u19_evidence_results_uk_wider_exact_20261007.json`, `...\91_build\_u19_stage_offers_uk_wider_exact_20261007.json`
- Focus close: `00_docs/UNIVERSE_UK_KS_FOCUS_CLOSE_2026-10-07.md`
- PDP OE upgrade (Pass 3): `00_docs/UNIVERSE_UK_KS_PDP_OE_UPGRADE_PASS3_2026-10-07.md`
- Omega delivery hunt: `00_docs/UNIVERSE_UK_TMC_OMEGA_DELIVERY_HUNT_2026-10-07.md`

## Not done / still true

UK focus (**58**) and wider (**162**) both meet the 50-row sufficiency bar. Portugal eligible stays 0. These hooks do not lock a billing move or a price action. TMC under-£150 mainland £ still not inventable.

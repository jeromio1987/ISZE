# ISZE — corrected car park (UIO) for GPS recalculation

**Generated** 30 July 2026 · **Purpose** denominator input for recalculating GPS. Everything here is the *target-wallet side*. The sales numerator is NOT in this file — see section 6.

---

## 1. Seven things you must know before computing anything

1. **GPS = actual parts sales ÷ target wallet.** Target wallet = Σ (UIO per model group × € per vehicle per year). Sales are ISZE→distributor level, margin basis (not markup, not retail).
2. **CY2025 car park is UNCHANGED.** The scrap-rule defect only affects forecast years 2026+. 2025 is an actual anchor. **So the existing CY2025 network GPS lock of 51.1% ex-MIDI does not move because of this correction.** If you are restating CY2025 GPS, the car park is not your reason to.
3. **CY2026 is what changes**, and it is what FY27 GPS and the Extended Target need. Network target wallet falls **-4.9%** on the corrected car park.
4. **Only one UIO figure is exact: IUK LCV CY2026 = 44,926** (locked 30 July 2026). Every other corrected figure is a constant-hazard estimate (10.2% CV / 12.3% LCV) that sizes the error; the full V20 cohort rebuild will differ by a few per cent. Do not present these as V20 output.
5. **Israel CV (UTI) is NOT corrected and is still ~23% too low** vs the Ministry of Transport figure of 14,019 at 30 June 2026 (model: 10,760). Separate defect — missing weight classes, not scrap. Its wallet below is therefore understated. Do not apply a 1.25 multiplier.
6. **UK CV (ITUK) car park is deliberately unchanged** — it already uses a proper cohort survival model with an age floor.
7. **MIDI Europe is excluded from every total.** Not an ISZE distributor. Rows are in the CSV flagged `is_MIDI_exclude=True`. Note the live workbook's own MIDI filter is currently set to "Include", so its Grand Total is contaminated.

---

## 2. Target wallet rates and how the mapping works

Source: the GPS per-model target configuration. Derivation is `£ retail × (1 − GP 34%) × FX 1.12`, verified against the ITUK Parts Sales Target Study (April 2026).

| UIO `model_type` | GPS target group | € / vehicle / yr | Derivation |
|---|---|---:|---|
| LD (N-series) | N75_N50_N62 | **739** | £1,000 × 0.66 × 1.12 = 739.20 |
| MD | F_Series_MD | **887** | £1,200 × 0.66 × 1.12 = 887.04 |
| F-Series | F_Series_MD | **887** | £1,200 × 0.66 × 1.12 = 887.04 |
| LCV (D-Max) | LCV_D_Max | **250** | ISZE GPS maximum (LCV) |
| *(3.5t N35 Grafter)* | *N35_Grafter* | ***296*** | *£400 × 0.66 × 1.12 = 295.68 — **see section 5, this rate is currently unreachable*** |

---

## 3. Network target wallet, excluding MIDI

| Basis | Target wallet |
|---|---:|
| CY2025 (unchanged by the fix) | € 60,218,249 |
| CY2026 on the **V19** car park — do not use | € 63,924,216 |
| **CY2026 on the corrected car park** | **€ 60,785,306** |
| Effect of the car-park correction | **−4.9%** |

---

## 4. By distributor

| Distributor (DB) | UIO CY2025 | UIO CY2026 corrected | Wallet CY2025 € | Wallet CY2026 € |
|---|---:|---:|---:|---:|
| ITUK | 23,068 | 24,173 | 17,176,988 | 18,006,518 |
| IUK | 47,783 | 44,926 | 11,945,750 | 11,231,423 |
| UTI | 10,336 | 10,760 | 8,271,300 | 8,641,172 |
| UMI | 18,542 | 17,161 | 4,635,500 | 4,290,334 |
| ISD-Lang | 13,780 | 13,490 | 3,808,128 | 3,889,407 |
| Imotors | 7,208 | 7,825 | 3,052,087 | 3,363,062 |
| IBX | 9,593 | 9,290 | 2,453,507 | 2,389,344 |
| Isuzu Sverige | 8,443 | 8,304 | 2,110,750 | 2,076,128 |
| RSA | 7,929 | 7,374 | 1,982,250 | 1,843,433 |
| Isuzu Ireland | 2,161 | 2,594 | 956,313 | 1,150,801 |
| Petros Petropoulos | 3,742 | 3,938 | 953,593 | 1,013,590 |
| AutoWallis | 3,734 | 3,645 | 933,500 | 911,180 |
| Loutsios & Sons | 2,308 | 2,423 | 676,267 | 712,842 |
| GasanZammit | 1,040 | 1,016 | 378,827 | 372,488 |
| Nordic Auto. | 1,204 | 1,196 | 301,000 | 298,977 |
| Isuzu Rom Auto | 1,071 | 1,109 | 267,750 | 277,317 |
| Isuzu Denmark | 851 | 866 | 213,239 | 217,026 |
| BL | 406 | 401 | 101,500 | 100,266 |

---

## 5. The N35 Grafter problem — read this or your wallet will be too big

The UIO file has **no model split**: the model column reads `LD` for every N-series vehicle, 3.5-tonne and 7.5-tonne alike. The mapper sees `LD` and returns the 7.5t rate. **So every 3.5-tonne N35 Grafter is charged €739 of annual wallet instead of €296.** The €296 line exists in the config but no code path can return it, and the branch that looks for "N35" routes to €250 instead. Three values, none of them applied.

### ITUK — the split is known exactly, and it is worth €5.5m

The ITUK Parts Sales Target Study carries the real split, and it reconciles to the UIO row to within 0.1 units:

| ITUK CY2026 | Units | Rate | Wallet |
|---|---:|---:|---:|
| N35 (3.5t) | 12,345 | €296 | € 3,654,120 |
| N75 | 10,865 | €739 | € 8,029,235 |
| F-Series | 963 | €887 | € 854,181 |
| **Correct total** | **24,173** | | **€ 12,537,536** |
| Currently charged (all LD @ €739) | 24,173 | | € 18,006,371 |
| **Difference** | | | **−€ 5,468,835 (−30.4%)** |

> N35 12,345 + N75 10,865 = 23,210 = the UIO `LD` row exactly. This is not an estimate.
> **ITUK's GPS % is therefore understated by roughly a factor of 1.44 today.** Same effect on CY2025: wallet €17.18m → €12.11m (−29.5%).

### The seven ISZE markets — 3.5t share of N-series, from the shipment register 2020–2026

| Market | 3.5t share of N-series | Note |
|---|---:|---|
| Portugal | 68.5% | **Use ~64% instead** — a registration-based measurement from the distributor's own data is more precise and is already in use |
| Belgium | 85.7% | Immaterial — almost no trucks, wallet is nearly all pickups |
| Ireland | 6.3% | Immaterial |
| Germany, Malta, Cyprus, Greece | 0% | No effect |

> Caveat: these are shipment shares 2020–2026 applied to the whole fleet, and the register does not reach before 2020. Directional sizing, not a restatement. No split is available for IUK, UMI, UTI or the other markets.

---

## 6. What is NOT in this file — the sales numerator

You need actual ISZE→distributor parts sales to divide by these wallets. It is deliberately excluded because it cannot be joined to this table safely. Three traps:

1. **Distributor naming does not match.** The sales extract uses different names (`Sverige` vs `Isuzu Sverige`, `ISD` vs `ISD-Lang`, `BL Iceland` vs `BL`). Worse, **Greece is one row in sales but two distributors in the car park** (Petros Petropoulos and Loutsios & Sons) — that join is genuinely ambiguous and must be resolved by hand.
2. **Fiscal vs calendar year.** The sales columns are labelled FY (April–March). The car park is calendar year. These have been conflated before. Confirm which basis you are on before dividing.
3. **The existing GPS master file's own wallet is wrong** — it prices most distributors at a flat rate rather than the segmented rates above. Take the numerator from it if you like; do **not** take its `max_spend` or `gps_pct` columns.

Ask Jerome for the parts sales figures on a stated basis (ISZE→DB, credit notes and returns excluded, transport and rebates stripped).

---

## 7. How to compute

```
wallet_DB      = Σ over rows of (UIO_row × rate_for_model_type)
GPS_DB         = actual_parts_sales_DB ÷ wallet_DB
wallet_network = Σ wallet_DB   (exclude MIDI rows)
```

Apply the N35 split first where you have it (ITUK exactly; Portugal at ~64%). If any distributor comes out above 100%, stop — that means the wallet is wrong, not that the distributor over-performed. Do not present a capture rate above 100%.

---

*Row-level data: `UIO_carpark_for_GPS_recalc_2026-07-30.csv` — same folder, 84 rows, one per car-park line, with both the V19 and corrected CY2026 figures, the target group, the rate and the computed wallet.*
# ITUK PMS Pricing — Position Paper v1

**Prepared by:** ISZE Sales · J. Van der Pluym
**Source:** ISZE lifetime sales data, CY2023–2025, all 18 active distributors
**Status:** Internal — for the ITUK pricing conversation and Kosha PMS narrative

---

## Headline

**ITUK is paying 40% to 248% more per fleet vehicle than the network median on every PMS subgroup we measure — except one.** This is not a fleet-mix story. It is a price-per-PMS-unit story, measured on the same parts, on the same fleet basis (SPU = spend per unit-in-operation).

---

## The number that matters

| PMS subgroup | ITUK €/UIO/yr | Network median €/UIO/yr | **Premium ITUK pays** |
|---|---:|---:|---:|
| **Brake pads** | €13.51 | €3.88 | **+247.7%** |
| **Clutch pressure plate** | €1.13 | €0.33 | **+243.7%** |
| **Fuel filter** | €8.87 | €3.12 | **+184.1%** |
| Clutch disc | €0.65 | €0.33 | +99.5% |
| Air filter | €6.95 | €4.51 | +54.0% |
| Oil filter | €3.80 | €2.71 | +40.3% |
| Brake shoes | €0.10 | €0.78 | −86.9% |

**Read:** ITUK customers spend roughly **3.5× the network median** on brake pads, **3.4×** on clutch pressure plates, and **2.8×** on fuel filters — per truck in their fleet, per year, on Genuine + BVP combined. Only brake shoes are below median, and on negligible volume.

---

## Why this matters for the Kosha narrative

- The ISZE network is leaving **€5.07M / year** in PMS revenue on the table by under-capturing its fleet (sum of revenue gap, latest year across all distributors).
- ITUK is responsible for **€2.04M** of that gap — 9.0% of the network total, despite holding a much smaller share of the UIO.
- ITUK's capture-rate gap vs the network median is the symptom; **the SPU premium above is the cause.** Customers walking away from ITUK's PMS prices show up downstream as a low capture rate and as the IAM share of wallet that we lose entirely.

---

## What ITUK will counter and how the data answers

1. **"ITUK fleet is younger / different mix."** Mitigated — SPU is normalised by UIO. Mix-shift between PMS subgroups doesn't explain a uniform 40–248% premium across all of them.
2. **"ITUK Genuine ASP is set by IML."** Partly true on Genuine. But the BVP-equivalent ASP is also higher at ITUK than at peers selling the exact same paired PN — see `PricingGap_Pairs` sheet in the data pack.
3. **"ITUK costs more to serve."** Cost-to-serve does not justify a 248% retail premium on a competitive PMS part. R&M studies of the same N-series fleet across markets land within ±15% on fully-loaded service cost, not 3.5×.

---

## Recommended ask

1. **Re-baseline ITUK's PMS retail pricing to network median + a defensible UK premium (10–20% max).** Worst-case revenue impact is offset by the capture-rate recovery (model says ~30% on fuel filter alone).
2. **Make BVP the formal first-line offer at ITUK for the 8 zero-penetration subgroups** (wheel pin, brake lining, brake rotor, brake shoe friction, brake pad, clutch booster, engine foot rubber, hub oil seal — all have ITUK addressable Genuine sales but zero BVP sales).
3. **Land UREA-filter BVP push as Euro 6 PMS quick-win.** ITUK has £74k Genuine, £1.3k BVP — single biggest UREA opportunity in the network.

---

## Numerical appendix (selected high-stakes rows)

### A. The 8 ITUK BVP white-space subgroups

| Subgroup | Addressable BVP PNs | ITUK BVP sold today | White-space PNs |
|---|---:|---:|---:|
| Wheel pin | 19 | 0 | 19 |
| Clutch kit | 20 | 8 | 12 |
| Brake pad | 2 | 0 | 2 |
| Engine foot rubber | 2 | 0 | 2 |
| Brake lining | 1 | 0 | 1 |
| Brake rotor | 1 | 0 | 1 |
| Brake shoe | 1 | 0 | 1 |
| Clutch booster | 1 | 0 | 1 |
| Hub oil seal | 1 | 0 | 1 |

### B. UREA filter snapshot — Euro 6 PMS opportunity

| Distributor | UREA Genuine € | UREA BVP € | UIO | BVP € share |
|---|---:|---:|---:|---:|
| **ITUK** | **€74,269** | **€1,311** | 22,389 | **1.7%** |
| Ireland | €4,544 | €150 | 2,727 | 3.2% |
| Belgium | €152 | €0 | 9,311 | 0.0% |
| Cyprus | €76 | €0 | 2,072 | 0.0% |
| Malta | €70 | €0 | 1,054 | 0.0% |

---

## Source data

`C:\Users\jerom\Desktop\claude\ISZE\Projects\Isuzu\pms-pilot\ISZE_ITUK_DataPack_v1.xlsx`

- `ITUK_vs_Network_PMS` — premium table above
- `Kosha_Gap_OneNumber` — €5.07M network gap, top-15 distributor breakdown
- `WhiteSpace` — addressable vs sold per (distributor × subgroup)
- `PricingGap_Pairs` — pair-level ASP delta (genuine vs BVP)
- `UREA_QuickWin` — full UREA snapshot
- `Substitution_Momentum` — 4 flagged YoY substitution signals
- `AIM_BVP_CrossLink` — top 80 (distributor × family) where IAM is heavy and BVP is light

Underlying pipeline: `C:\Users\jerom\Desktop\claude\ISZE\Data\derived\` — built and verified via the prism contracts pipeline.

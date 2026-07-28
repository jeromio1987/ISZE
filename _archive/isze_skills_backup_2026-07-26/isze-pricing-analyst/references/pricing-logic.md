# ISZE Pricing Logic — Complete Reference
**Upload to GPT Enterprise knowledge base**
Last updated: April 2026

---

## Core Formula

### Step 1 — FOB Price (EUR)

```
FOB_EUR = BP_JPY ÷ FX_Rate × Source_Discount
```

| Variable | Source J (Japan/IML) | Source T (Thailand/IMIT) |
|----------|---------------------|------------------------|
| Source_Discount | 0.62 | 0.611 |
| FX Rate (FY2026) | 163.7 JPY/EUR | 163.7 JPY/EUR |

**D-Max parts are typically Source T; N-Series and F-Series are typically Source J.**

### Step 2 — Selling Price (PR00)

```
SP_EUR = FOB_EUR ÷ Class_Factor
```

Class factor determines the margin built into the selling price. Classes: C, D, F, J, M, P, V, T.

### Step 3 — Price Chain

```
ISZE → Distributor → Dealer/Fleet

ISZE SP (PR00) = base
DB (distributor) resale = ISZE_SP ÷ 0.60    → DB margin ~40%
DLR/Fleet = DB_price ÷ 0.75                  → DLR margin ~25%
```

---

## FX Rate History

| Pricing Period | FX Rate | Notes |
|---------------|---------|-------|
| FY2024 (Oct 2023) | 146.6 JPY/EUR | — |
| FY2025 (Apr 2024) | 153.3 JPY/EUR | — |
| FY2026 (Oct 2025) | 163.7 JPY/EUR | Current rate |

**Critical interpretation**: JPY weakening means a higher JPY/EUR number. This actually means EUR cost to ISZE is LOWER (more JPY buys the same EUR). The +5.3% price increase in FY2026 is NOT from FX — it is from IML raising Base Prices (BP_JPY) as part of the 2030 Vision strategy. FX, if applied purely, would have reduced EUR prices.

---

## Confirmed PR00 Prices (IE40, March 2026)

### D-Max (Source T — Thailand)

| Part | PN | ABC | Price (EUR) |
|------|----|-----|------------|
| Oil filter | 8982705240 | A | €6.80 |
| Fuel filter kit | 8981596930 | A | €13.85 |
| Thermostat | 8943703781 | A | €10.31 |
| Brake disc front | 8983767530 | A | €79.26 |
| Brake drum rear | 8979480380 | A | €72.49 |
| Clutch disc | 8982120690 | B | €157.24 |
| Glow plug | 8983320410 | A | €18.59 |
| EGR valve | 8983320160 | A | €235.55 |
| Water pump | 8984865440 | A | €175.21 |
| Shock front | 8976485560 | B | €35.20 |
| Shock rear | 8975595540 | A | €25.12 |

### N-Series (Source J — Japan)

| Part | PN | ABC | Price (EUR) |
|------|----|-----|------------|
| EGR (4HK1) | — | C | €151.32 |
| Clutch disc | 8972599400 | C | €84.47 |

---

## Price Lists

| Code | Description |
|------|-------------|
| PR00 | Standard European price list — all EU distributors |
| ZPR1 | Israel-specific (SAP condition type) |
| CIS | Armenia (GA) and Kazakhstan (CBC) |

---

## ABC Classification

| Code | Meaning |
|------|---------|
| A | Highest volume — most competitive risk |
| B | Significant volume |
| C–H | Decreasing volume |
| Blank | Not ranked / rare demand |

Focus competitive analysis on A/B parts. These are where IAM alternatives exist and capture rate matters most.

---

## ITUK Pricing Dispute — Key Numbers

| Metric | Value |
|--------|-------|
| Basket price increase 2025→2026 | +€298,911 |
| Basket % increase | +5.3% |
| Class 0 PNs (unclassified) | 10 (all Source J) |
| FX rate applied | 163.7 JPY/EUR |

**ISZE defence**: Formula is consistent, IML-directed, applied uniformly. FX symmetry: ISZE has never reduced prices when JPY weakened because IML has never instructed it to. Pricing is a pass-through — ISZE has no discretion.

---

## High-Risk Competitive Parts (IAM exposure)

Parts where independent aftermarket alternatives are well-established and priced significantly below genuine:

| Category | Risk Level | Notes |
|----------|-----------|-------|
| Oil filters | Very High | Bosch, Mann, Hengst — widely available |
| Fuel filters | High | Multiple IAM sources |
| Brake pads/discs | High | TMD, Brembo, etc. |
| Clutch sets | High | LuK, Valeo — direct fit |
| Glow plugs | Medium-High | Bosch, NGK |
| EGR valve | Medium | Pierburg — expensive but available |
| Water pump | Medium | Gates, Dayco |

**Note**: D-Max EGR at €235.55 (ABC:A) is particularly exposed. An IAM equivalent (Pierburg/BorgWarner) typically retails at €100–150 at dealer level.

# Data asks — IML (HQ) + all DBs (sales to dealers)

**Use:** paste-ready. No personal names. For Jerome’s IML meeting + follow-up to network.

---

## 1) Ask IML (HQ) — what only HQ can unlock

IML sits above markets. Prioritise what builds **GPS / PMS models** we cannot invent from billing alone.

### A — Confirm the service schedule (blocks % debates)
Please confirm the **authoritative IML service schedule** for N75 / N35 / F-series (and any other models in scope):

| Item | Needed |
|------|--------|
| Replacement interval (km) per PMS category / FIG-KEY | Oil, fuel, air, clutch, brake (and any other PMS FIG-KEYs) |
| Reference annual mileage by model family | Used to turn interval → times/year |
| Clutch addressable parc | Manual vs automatic rule (or % if VIN not available) |

*Why:* Kick-off materials showed oil at 20,000 km and a 20,000 km/yr example; the Apr 2026 ITUK study uses 50,000 km/yr and oil every 40,000 km. We need one HQ rule so every DB cover % is comparable.

### B — Parc / VIN (for clutch + model-bucket GPS)
| Item | Needed |
|------|--------|
| VIN-level or parc extract | Model code, model year, market/DB, **transmission (MT/AT)** where known |
| Or HQ standard MT share by model | If VIN cannot be released |

*Why:* Clutch PMS % is provisional until manual-only denominator is real.

### C — Model catalogue for “new models” (GPS + PMS)
For any model family we should add to GPS/PMS engines:

| Field | Example |
|-------|---------|
| Model / series name | e.g. next CV / LCV codes |
| FIG-KEY ↔ PMS category map | Same structure as current PMS SPA packs |
| GPS class / € or local-currency per UIO band | If HQ has a planning rate |
| Service interval pack | Same as A |

*Why:* New GPS/PMS models should start from HQ definitions, not guessed from one market.

### D — Nice to have (HQ)
- Cross-market PMS promotion playbook (what “item promotion activity” includes)
- Any HQ dashboard or cover % already computed (so we can reconcile, not compete)

### Paste — IML

```
Subject: PMS / GPS — HQ data to align models across DBs

Dear IML team,

To keep GPS and PMS models consistent across distributors, could you please help with:

1) Authoritative service schedule — replacement intervals (km) and reference
   annual mileage by model family (N75 / N35 / F and others in scope),
   including the clutch manual vs automatic rule.

2) Parc / VIN support — transmission (MT/AT) by model where available,
   or an HQ standard MT share if VIN cannot be shared.

3) Catalogue for any new model families to include in GPS/PMS
   (FIG-KEY map, intervals, planning €/UIO or local rate if defined).

We are standardising distributor → dealer (“sales to dealers”) extracts
from all DBs on one file shape; HQ schedule + parc rules will let us
compute comparable cover % everywhere.

Thank you
ISZE Parts Analytics
```

---

## 2) Ask every DB — sales to dealers (network advantage)

**Yes — do this.** Dealer grain unlocks leakage, GPS sell-out checks, and PMS cover below distributor. Today only ITUK (and UTI aggregate) are usable.

### Standard file shape (same for all DBs)

| Column | Required | Note |
|--------|----------|------|
| Period | Yes | Month or invoice date; state CY vs FY |
| Dealer code | Yes | Stable ID |
| Dealer name | Yes | |
| Part number | Yes | As sold |
| Description | Nice | |
| FIG-KEY | Nice | If DB has it |
| Qty | Yes | |
| Value | Yes | State currency + price level (wholesale to dealer) |
| Line type | Nice | Genuine / BVP / other if known |

**Minimum period now:** full **CY2025** (or last closed FY if that is their books).  
**Next refresh:** YTD through latest closed month (e.g. to **31/03/2026**).

### Paste — all DBs

```
Subject: Sales to dealers extract — CY2025 (+ YTD 2026 if available)

Dear Parts team,

To improve network PMS / GPS analytics (dealer-level), please send a
“sales to dealers” extract:

• Period: calendar 2025 (Jan–Dec), and if possible 2026 YTD to last closed month
• Columns: period, dealer code, dealer name, part number, qty, value (currency),
  description and FIG-KEY if available
• One row per dealer × part × period (or invoice line)

Same layout for every distributor lets us compare markets fairly.
Please send Excel or CSV to ISZE Parts Analytics.

Thank you
ISZE Parts Analytics
```

### Rollout tip
1. Send ITUK first (they already know the shape — March CY2025 file).  
2. Then UTI / UMI / IUK / EU DBs with the same template.  
3. Land files in `01_data/90_INBOX/` → sort per DATA_MANIFEST → rebuild sell-out derived.

---

## 3) Priority if IML only has bandwidth for 2 things

1. **Confirm intervals + mileage** (kills 35% vs 17% confusion).  
2. **MT/AT or VIN rule for clutch.**  

Sales-to-dealers stays on the **DB** track in parallel.

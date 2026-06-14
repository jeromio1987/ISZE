# Project: Competitiveness Dashboard

_Last validated: 2026-03-24_

## Status: Active — v1 complete, IE40-calibrated (Mar 2026)

## File
`Isuzu/Divers/ISZE_Competitiveness_Dashboard.html` — 70.7 KB, two-tab HTML

## What it does
Interactive heatmap comparing ISZE genuine parts (PR00) vs aftermarket (IAM and OEM-equivalent).
Segments: D-Max (LCV) / N-Series (MCV) / F-Series (HCV)
Markets: UK / DE / FR
Price levels: ASC (PR00) / DB (÷0.60) / DLR (÷0.75)
Compare modes: IAM retail / IAM trade (×0.65) / OEM-equiv retail / OEM-equiv trade (×0.72)

## Key findings (as of Mar 2026)
**D-Max (LCV):**
- PMS parts (filters/thermostat): ISZE competitive at ASC level (0.6–0.9×) ← GOOD
- Brakes: exposed at ASC level (disc 1.9×, pads 2.3×) ← BAD
- EGR valve: 1.27× vs IAM retail at ASC — worse at DB/DLR level
- Cabin filter: 1.17× — slightly exposed
- Ball joint: 1.0× — exactly at par with IAM

**N-Series (MCV):**
- Prices calibrated from IE40 JP price clusters
- EGR (4HK1): 1.16× vs IAM — moderate exposure
- Brake disc: 1.27× — exposed

**F-Series (HCV):**
- More competitive on brakes (fewer AM brands)
- Shock absorbers: extremely competitive

## Data confidence
- D-Max = HIGH (IE40 ABC:A confirmed)
- N-Series = MEDIUM (JP price clusters, not EQ-HIT mapped)
- F-Series = LOW (estimated, needs EQ-HIT validation)

## What would make it better
1. EQ-HIT access — would allow PN → model → service interval mapping
2. SAP export with customer invoice data — actual market pricing vs PR00
3. Real-time AM price scraping (AutoDoc, parts-market.de, etc.)
4. Distributor feedback on where they lose deals

## Connections
→ Supports ITUK pricing conversations (ISZE is competitive on many parts)
→ Feeds PMS coverage project narrative (genuine IS competitive on filters)
→ Supports Action Plan campaigns (target the exposed categories)

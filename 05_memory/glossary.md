# Full Glossary — ISZE Parts Sales

_Last validated: 2026-08-17 (content cross-checked against pricing-basket-2026.md and all in-scope
05_memory/projects/*.md files during this pass — no discrepancies found; missing field itself was
flagged in memory_review_W30_2026.txt through memory_review_W34_2026.txt)_

## Companies & Entities
| Term | Full Name | Notes |
|------|-----------|-------|
| ISZE | Isuzu Motors Europe | Jerome's company, parts distribution hub, Branch IE40 |
| IML / ISZJ | Isuzu Motors Limited | Japan HQ and parts source |
| IMIE | Isuzu Motors Intl Europe | Vehicle sales arm (separate from ISZE) |
| IMIT | Isuzu Motors Intl Thailand | Source T — Thailand parts |
| ITUK | Isuzu Truck UK Ltd | Primary UK distributor |
| IUK | Isuzu UK / DS/E International Motors Limited | UK pickup/LCV distributor (≠ ITUK truck) |
| ISD / IMG | Isuzu Motors Germany / ISZJ DE | German distributor (PRISM DB = ISD); also service/warranty |
| Petros | Petros / Loutsios Group (Greece) | Greek distributor; sellout / IDS packs under PETROS |
| Harris Group | Harris Group (Ireland) | Irish distributor (Isuzu Ireland) — contact John Cummins parts/logistics |
| IAS | Isuzu Accessories Supplier | Thailand-based, accessories |
| MIDI / AIOS | Regional Isuzu entities | Lubricants model reference |
| IIF | Isuzu training entity | Based in Dubai |

## People
| Abbreviation | Name | Role |
|-------------|------|------|
| JVDP / Jerome | Jérôme Van der Pluym | VP Sales, ISZE IE40 |
| KM / Koen | Koen Matheussen | ISZE Assistant Sales Manager — DB sales reviews / SPA / StD data |
| HT / Hadi | Hadewijch Tibos | ISZE Sales Manager — 3-party host with IMIE; DB sales reviews |
| DW | — | ISZE Accessories lead |
| SZ / Saida | — | ISZE Accessories backup |
| BVDB | — | ISZE Power BI reporting |
| Jimmy Meskens | Jimmy Meskens | ISZE — EDI / data-exchange setup (Petros thread) |
| James Marsh | James Marsh | Materials Expeditor, ITUK |
| John Lennon | John Lennon | General Manager Parts — IUK |
| Aaron Singh-Chutti | Aaron Singh-Chutti | Parts Inventory coordinator — IUK |
| Phil Evans | Phil Evans | IUK Technical — national R&M / extended-warranty options |
| Sebastian Müller | Sebastian Müller | Head of Aftersales — ISD (Germany) |
| Björn Groß | Björn Groß | ISD Aftersales — joining as Thomas Spenlein retires (2026) |
| Panagiotis Zoglopotitis | Panagiotis Zoglopotitis | Loutsios Group / Petros (Greece) — parts commercial contact |
| John Cummins | John Cummins | Parts & Logistics Manager — Harris Group (Ireland) |
| Keith Dempsey | Keith Dempsey | Ireland — fleet / vehicle-sales validation contact (with Carl) |
| Ryusuke Tanaka | Ryusuke Tanaka | Product Marketing, IML International Parts |
| Tomoaki Hiratsuka | Tomoaki Hiratsuka | IML International Parts Sales |
| Nikola Broecker | Nikola Broecker | IMIE Sales & Marketing — 3-party pickup decks / D-Max regs |
| Lucas Ganske | Lucas Ganske | IMIE — 3-party meeting circuit (with Nikola / Sonja) |
| Sonja Baranowski | Sonja Baranowski | IMIE — often distributes 3-party English PDFs |
| Łukasz Krzemiński | Łukasz Krzemiński | Poland aftersales — KPI/SPI monthly sheets (≠ Lucas IMIE) |

## Parts & Technical
| Term | Meaning |
|------|---------|
| VP | Vehicle Parts |
| ACC | Accessories |
| PMS | Periodic Maintenance Service — filters, clutch, brake |
| UIO | Units In Operation — vehicle fleet in service |
| IAM | Independent Aftermarket — non-genuine parts |
| OEM-equiv | OEM-equivalent brands (Bosch, Valeo, LuK, Pierburg, etc.) |
| EGR | Exhaust Gas Recirculation valve |
| DPD | Diesel Particulate Diffuser |
| 4JJ3 | D-Max current diesel engine (2.5D/3.0D) |
| 4HK1 | N-Series primary EU diesel engine |
| 6HK1 / 6UZ1 | F-Series engines |
| BESCO | Isuzu genuine lubricants brand |

## Commercial
| Term | Meaning |
|------|---------|
| DB | Distributor |
| IDS | Isuzu Dealer Standards (self-eval A–E) — visit triage, not wallet. OS: `05_memory/projects/ids-db-leverage-os.md` |
| DLR / ASC | Dealer / Authorised Service Centre |
| SPA | Special Price Agreement — discounted pricing for specific customer/model |
| DLOD | Don't Lose Deal — ITUK program for competitive quotes |
| VPACC | Vehicle Parts & Accessories (action plan label) |
| CR | Cost Reduction |
| SPLR | Supplier |
| KPI | Key Performance Indicator matrix |
| Genuine with BVP alternative | Display label for mix bucket `genuine_contested`: genuine PN that has a BVP catalogue pair. Use this in Mode A and all spoken/written comms — not “genuine contested” (sounds like AIM/street fight). Code/CSV field names may stay `genuine_contested_*`. |
| Genuine only | Genuine PN with no BVP catalogue alternative |
| BVP | Best Value Parts — ISZE value-tier SKU |

## Pricing
| Term | Meaning |
|------|---------|
| PR00 | Standard European selling price list (SAP) |
| ZPR1 | Israel price list condition type (SAP) |
| CIS | Price list for Armenia (GA) and Kazakhstan (CBC) |
| Source J | Japan/IML sourced — discount factor 0.62 |
| Source T | Thailand/IMIT sourced — discount factor 0.611 |
| BP | Base Price in JPY (from IML) |
| FOB | Free On Board price in EUR = BP_JPY / FX × source_discount |
| SP | Selling Price = FOB / class_factor |
| Class C/D/F/J/M/P/V/T | Parts classification — determines margin factor |
| ABC Code | Part ranking: A=highest volume → H=lowest; blank=unranked |

## Systems
| Term | Meaning |
|------|---------|
| EQ-HIT | Isuzu parts catalog lookup — maps PN to vehicle model/service interval |
| SAP | ERP system (pricing, orders, invoicing) |
| Power BI | Reporting tool (BVDB manages dashboards) |
| IE40 | ISZE's SAP branch/price list code |

## Financial
| Term | Meaning |
|------|---------|
| FY | Fiscal Year — April to March (Isuzu) |
| GP | Gross Profit |
| GP% | Gross Profit Margin % |
| Eucon | Price benchmarking study provider |
| R&M | Repair & Maintenance contracts |
| IGS | Isuzu Global Summit |

## Customer codes
| Code | Entity |
|------|--------|
| 1797 / UMI | Israel distributor 1 (Universal Motors Israel) |
| 1799 / UTI | Israel distributor 2 (Universal Trucks Israel) |
| GA | Green Armenia (CIS) |
| CBC | CBC Kazakhstan (CIS) |

## Aftermarket Intelligence Framework (AIM)
Terms from the GPT-built analytics framework (isuzu_aftermarket_full_build_v1.xlsx)

| Term | Meaning |
|------|---------|
| AIM | Aftermarket Intelligence Model — the full analytics system |
| Alias Master | Sheet normalizing raw distributor names (IUK, ITUK → Isuzu UK) |
| Category L1/L2/L3 | 3-level parts taxonomy (e.g. Engine → Cylinder Head → Cylinder Head) |
| Demand Type | Parts demand classification: Maintenance / Wear Repair / Breakdown Repair / Crash Body |
| Noise Flag | Parts excluded from growth analysis (freight, packaging, credits/debits, marketing) |
| Strategic Score | 0–100 score ranking parts on sales, volume, criticality, competition, margin, growth |
| Strategic Bucket | Score band: Strategic (80–100) / Core (60–79) / Standard (35–59) / Long Tail (0–34) |
| Traffic Driver | Strategic tag — part that drives workshop visits |
| Defensive Item | Strategic tag — part at high competitive risk; protect pricing |
| Safe Increase Candidate | Strategic tag — low competition, low visibility; can take price increase |
| Spend Index | Relative demand index = Parc × Age Factor × Category Factor |
| Age Factor | Demand multiplier by fleet age: 0–2yrs=0.4 / 3–5=0.8 / 6–10=1.2 / 10+=0.9 |
| Opportunity Gap | Distributor potential vs actual: types = service / repair / basket / structural |
| Pricing Risk Map | Framework detecting: price coherence, competitive overpricing, margin leakage, class distortion |
| Must Review | Highest-priority pricing risk bucket (high impact + high risk) |
| Class Distortion Risk | Class-based price increase that is commercially too aggressive |
| Kit/Component Inversion | Repair kit priced irrationally vs its component assembly |
| Disambiguation Rule | Context-sensitive keyword override (e.g. "hose" + "brake" → Brakes, not Engine) |
| Keyword Rules | 1,924-row engine mapping part description keywords → Category L1/L2/L3 |

---

## Corporate structure

```
IML (Isuzu Motors Limited — Japan HQ)
 └─ IMIE (Isuzu Motors Intl Europe — vehicle sales)
 └─ ISZE (Isuzu Motors Europe — parts hub, Branch IE40)
      └─ Distributors (DB): ITUK, IMG, FR, BE, NL, PL, Nordic, CIS, Israel…
           └─ Dealers (DLR): ASC / workshop level
 └─ IMIT (Isuzu Motors Intl Thailand — Source T parts)
 └─ IAS (Isuzu Accessories Supplier, Thailand)
```

## Pricing chain (summary)

ISZE (PR00) → DB (÷0.60, ~40% margin) → DLR/Fleet (÷0.75, ~25% margin)

Source J discount 0.62 · Source T discount 0.611 · SP = FOB / class_factor

## FY calendar

- **FY2026** = April 2025 – March 2026
- **FY2027** = April 2026 – March 2027
- **IGS** = Isuzu Global Summit (annual IML meeting)

# ISZE Company Context — Knowledge File
**Upload to GPT Enterprise knowledge base**
Last updated: April 2026

---

## Corporate Structure

```
IML — Isuzu Motors Limited (Japan HQ)
 ├── IMIE — Isuzu Motors International Europe (vehicle sales)
 ├── ISZE — Isuzu Motors Europe (parts hub — Jerome's company, Branch IE40)
 │    └── Distributors (DB):
 │         ├── ITUK — Isuzu Truck UK Ltd (primary UK distributor)
 │         ├── IMG — Isuzu Motors Germany
 │         ├── FR, BE, NL, PL, Nordic
 │         ├── CIS — Armenia (GA / Green Armenia), Kazakhstan (CBC)
 │         └── Israel — UMI (1797), UTI (1799)
 └── IMIT — Isuzu Motors International Thailand (Source T parts)
      └── IAS — Isuzu Accessories Supplier (Thailand)
```

**ISZE's role**: Parts distribution hub. Receives parts from IML (Japan) and IMIT (Thailand). Sets European selling prices (PR00). Sells to distributors, who sell to dealers and fleets.

---

## Vehicle Segments

| Vehicle | Engine | Source | Notes |
|---------|--------|--------|-------|
| D-Max | 4JJ3 (1.9D / 3.0D) | TH (Source T) | Main EU volume LCV pick-up |
| N-Series | 4HK1 (primary EU) | JP (Source J) | Medium truck — NKR/NHR/NLR/NMR/NPR |
| F-Series | 6HK1, 6UZ1 | JP (Source J) | Heavy truck — lower EU volume |

---

## Key People

| Name / Code | Role | Company |
|-------------|------|---------|
| Jérôme Van der Pluym (JVDP) | VP Vehicle Parts Sales | ISZE IE40 |
| KM | Sales colleague | ISZE |
| HT | Sales / Accessories colleague | ISZE |
| DW | Accessories lead | ISZE |
| SZ / Saida | Accessories backup | ISZE |
| BVDB | Power BI reporting | ISZE |
| James Marsh | Materials Expeditor | ITUK (james.marsh@isuzutruck.co.uk) |
| Ryusuke Tanaka | Product Marketing, International Parts | IML Japan |
| Tomoaki Hiratsuka | International Parts Sales | IML Japan |

---

## Fiscal Year

- **FY = April to March** (Isuzu convention)
- FY2026 = April 2025 – March 2026
- FY2027 = April 2026 – March 2027 (current year)

---

## Systems Used

| System | Purpose |
|--------|---------|
| SAP (IE40) | ERP — pricing, orders, invoicing |
| EQ-HIT | Parts catalogue — maps PN to vehicle/service |
| Power BI | KPI dashboards (managed by BVDB) |
| PR00 | Standard European price list condition (SAP) |
| ZPR1 | Israel-specific price list (SAP) |

---

## IE40 Price List (March 2026)

- **164,382 rows**, EUR, comma-decimal format
- Columns: P/N | Newest P/N | Description | Weight | L/W/H | Commodity Code | Country of Origin | ABC Code | Price (EUR) | Currency | Fig No. | Key No.
- ABC Code: A = highest volume → H = lowest; blank = unranked
- TH-sourced = D-Max signal | JP lower tier = N-Series | JP upper tier = F-Series

---

## ITUK Key Data (FY2026)

- **UIO total (DVLA, March 2026)**: 22,389 vehicles — N35: 10,900 | N75: 9,359 | N50/55: 651 | N62/65: 257 | F-series: 805 | D-Max: 417
- **FY26 target**: £13.13M
- **GPS benchmark**: £580.65/vehicle/year (True Sales average)
- **PMS oil filter capture rate**: 9.8% (CY2024) / 17.3% (CY2025) (5,815 units sold vs 33,584 expected)
- **Pricing basket impact 2025→2026**: +€298,911 / +5.3%

---

## Kosha Plan (IML commercial plan, Jan 2026)

| FY | VP Target |
|----|----------|
| FY2024 | €29.6M (actual) |
| FY2025 | €32.5M |
| FY2026 | €32.3M |
| FY2031 | €52.1M (+76%) |

GP compression: 37.4% (FY2025) → 26.1% (FY2028) per IML's own plan.

**Internal note**: The FY2031 target is structurally unreachable from current position. ISZE's real objective is to build a credible execution record through PMS, lubricants, AIM, and UIO-based modelling.

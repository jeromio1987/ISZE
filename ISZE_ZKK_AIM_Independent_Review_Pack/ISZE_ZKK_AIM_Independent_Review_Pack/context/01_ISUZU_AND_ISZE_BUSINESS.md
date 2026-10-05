# 01 - The Isuzu aftersales business

**As of:** 2026-09-19.

---

## 1. Where ISZE sits

```
Isuzu Motors Limited (IML) - Japan, the parent
 |
 +-- Isuzu Motors International Europe (IMIE)      vehicle sales into Europe (separate from ISZE)
 |
 +-- Isuzu Motors Europe (ISZE)                    parts hub - this is Jerome's company, SAP branch IE40
 |    |
 |    +-- National distributors (the "DB")        ITUK, IUK, ISD/Germany, Belgium, Netherlands, France,
 |         |                                      Poland, Nordics, Portugal, Spain, Italy, Greece, Hungary,
 |         |                                      Romania, Cyprus, Malta, Ireland, Israel, ...
 |         +-- Dealers and authorised service centres
 |              |
 |              +-- Fleets and end customers (trucks in service)
 |
 +-- Isuzu Motors International Thailand (IMIT)    the second parts source ("Source T")
```

ISZE does not sell trucks and does not deal with fleets directly. It buys parts from IML (Japan) and IMIT
(Thailand), sets the European selling price list (known as PR00), and sells to distributors. The distributor
sells to dealers. The dealer sells to the fleet that runs the truck.

That distance matters commercially: ISZE sees what the distributor orders, not what the dealer sold to the
end customer. Any statement about end-market price elasticity is therefore an inference, not a measurement,
unless a market has shared dealer-level sales data.

## 2. Vehicle ranges

| Range | What it is | Main engine | Parts source |
|---|---|---|---|
| D-Max | Pick-up, the European volume light commercial vehicle | 4JJ3 | Thailand (Source T) |
| N-Series | Light and medium truck. Model codes NKR/NHR/NLR/NMR/NPR; in the data they appear as tonnage bands: N35, N50/N55, N62/N65, N75 | 4HK1 | Japan (Source J) |
| F-Series | Heavy truck, lower European volume | 6HK1, 6UZ1 | Japan (Source J) |

The tonnage band is the single most important vehicle attribute in the data, because the parts that a
vehicle consumes per year depend on it. A 7.5-tonne N75 truck is a different parts consumer from a 3.5-tonne
N35 (in the UK known as the Grafter), and pricing them on one rate is a known and fixed error - see file 03.

## 3. Fiscal year

Isuzu's fiscal year runs **April to March**. The European aftersales business follows it for planning and
reporting.

- FY2026 = April 2025 to March 2026 (closed, complete)
- FY2027 = April 2026 to March 2027 (current)

Note that most of the data extract is on a **calendar year** basis (CY2023, CY2024, CY2025, CY2026 year to
date). When a question says "this year" it is worth asking whether it means the calendar year or the fiscal
year, because they are three months apart and the answer changes.

## 4. The price chain - and the one number to remember

```
Base Price in JPY (set by IML)
     divided by the FX rate (JPY per EUR)
     multiplied by the source discount (Source J 0.62, Source T 0.611)   ->  FOB in EUR
     divided by the class factor                                          ->  ISZE selling price (PR00)

then:
     ISZE list price   x 1.40   ->  what the distributor pays     (40% margin to the distributor)
     distributor price x 1.275  ->  what the dealer pays          (a further 27.5% margin to the dealer)

combined:  ISZE list x 1.785     =  the customer price we treat as the reference dealer price
```

Some older documents in this workspace express the same chain as divisions by 0.60 and 0.75, but that divisor
form does not reconcile with the multiples above, so the multiples are the form to use.

Two things to keep straight when discussing this:

- The **class factor** is a divisor, so the factor and the margin are two ways of saying the same thing:
  a factor of 0.47 is a 53% margin. Jerome works in margins. Always give the margin first.
- The **source discount** (0.62 for Japan, 0.611 for Thailand) is the discount ISZE receives against the
  base price. It is not a margin and it is not negotiable at ISZE level.

The class letters (C, D, F, J, M, P, V, T) are the parts classification that sets the factor. They carry no
meaning on their own and should never be written without the margin beside them.

**The current FX rate is 163.7 JPY/EUR (FY2026).** The history is 146.6 (October 2023), 153.3
(April 2024), 163.7 (October 2025). A higher number means a weaker yen, which means a *lower* euro cost to
ISZE. The FY2026 price increase of about 5% was therefore not caused by currency - it came from IML raising
the base prices. That distinction is the backbone of the ITUK price discussion (see file 03, section on
pricing).

## 5. The market entities

These are the codes that appear in the data. Where two codes belong to the same country they are still
**separate distributors with separate fleets, separate prices and separate performance**, and must never be
combined into one country figure.

**United Kingdom**

| Code | Entity | Fleet | Parts source mix |
|---|---|---|---|
| ITUK | Isuzu Truck UK - the truck distributor | 22,389 (DVLA, March 2026) | Japan |
| IUK | Isuzu UK - the pick-up / light commercial distributor | 47,783 (2025) | Thailand for D-Max, Japan for N-Series |

**Israel**

| Code | Entity | Sold-to code | Fleet | Note |
|---|---|---|---|---|
| UMI | Universal Motors Israel | 1797 | 18,542 (2025) | The distributor that participated in the 2026 dealer standards round |
| UTI | Universal Trucks Israel | 1799 | 10,336 (2025) | Did not participate in that round; separate fleet and separate parts behaviour |

In the billing data both appear under one payer name, so an analysis that filters on the payer name instead
of the sold-to code will blend them. That is a known trap.

**Continental Europe and other markets:** ISD (Germany), Belgium, Netherlands, France, Poland, Sweden,
Norway, Finland, Denmark, Iceland, Ireland, Portugal, Spain, Italy, Greece, Hungary, Romania, Cyprus, Malta.
The CIS markets are Armenia (GA, Green Armenia) and Kazakhstan (CBC). Turkey is deliberately not an ISZE
market - its absence from the data is by design, not a data gap.

**Billing entities with no fleet count:** Ukraine, Palestine, Armenia, Kazakhstan. These have real revenue
and appear in the sales data, but there is no vehicle-in-service register behind them, so any "per truck"
figure for them is not computable. Do not divide.

### The name mapping used across this pack

The plan workbook and the monthly report name a market after its distributor; the derived data files name it
after the country. This table is the single mapping used across the pack. The left column is the name the
plan workbook and the monthly report use, with the plan workbook's own SAP number for the line. The right
column is the country and the code that `01_data/00_derived/distributor_dimension.csv`,
`gps_spu_by_distributor.csv` and `wallet_waterfall.csv` carry.

| In the plan or the monthly report | Country | In the data files (code, SAP number) | Note |
|---|---|---|---|
| ITUK | United Kingdom | ITUK, 2194 | The truck distributor, one of the two UK entities. |
| IUK | United Kingdom | IUK, 89 | The light commercial distributor. Never add it to ITUK: separate fleets, prices and results. |
| UMI | Israel | UMI, sold-to 1797 | The light commercial distributor, and the one that took part in the 2026 dealer standards round. |
| UTI | Israel | UTI, sold-to 1799 | The truck distributor. Both Israeli entities bill under payer 1797, so filter on the sold-to code. |
| ISD | Germany | GERMANY, 93 and 2516 | Isuzu Sales Deutschland. Two sold-to numbers, so sum both. |
| IBX | Belgium | BELGIUM, 90 | Isuzu Benelux NV. The plan table in file 03 calls this line "Benelux and Poland", while the derived files carry payer 90 as Belgium only. Treat the Netherlands and Poland part of that line as unconfirmed. |
| Imotors | Portugal | PORTUGAL, 92 and 519 | Two sold-to numbers, so sum both. |
| RSA | Norway | NORWAY, 86 | Rutebileiernes Standardisering AS. Note that other data files use the letters RSA for the Greek distributor, so read the SAP number, not the letters. |
| Isuzu Sverige | Sweden | SWEDEN, 2181 | Isuzu Sverige AB. |
| Isuzu Ireland | Ireland | IRELAND, 76 | Isuzu Ireland. |
| KTK, Komtranskomplekt | Ukraine | UKRAINE, 2294 | File 01 section 5 lists Ukraine as a billing entity with no fleet count, so no per-truck figure exists for it. |
| Petros | Greece | GREECE, 66 | Petros Petropoulos. |
| Loutsios | Cyprus | CYPRUS, 393 | Loutsios A and Sons. Cyprus, not Greece. |
| MIDI | No single country | MIDI, 88 | Not an ISZE customer, and outside ISZE's own totals by convention. |
| BL. Ehf. | Iceland | ICELAND, 1576 | |
| GasanZammit | Malta | MALTA, 1759 | |
| Isuzu Danmark | Denmark | DENMARK, 2027 and 2751 | Two sold-to numbers, so sum both. |
| Isuzu Finland | Finland | FINLAND, 2679 | Nordic Automotive Trading oy. |
| WAE Kft | Hungary | HUNGARY, 537 | The plan workbook names the Hungarian line AW Distribution, SAP number 537. Both names are used for Hungary; whether they are the same company is not established in this pack. |
| Isuzu Rom Auto | Romania | ROMANIA, 396 | |
| KIMA | Palestine | PALESTINE, 2372 | File 01 section 5 lists Palestine as a billing entity with no fleet count. |
| Isuzu Armenia | Armenia | ARMENIA, sold-to 2733, SAP payer 2731 | Grand Avto LLC. The data code is GA; file 01 section 5 calls it Green Armenia. |
| Isuzu Kazakhstan | Kazakhstan | KAZAKHSTAN, sold-to 2734, SAP payer 2732 | CBC-Trans LLP. The data code is CBC. |

Country and code for each line come from `01_data/00_derived/distributor_dimension.csv` (sold-to, payer and
distributor code), `01_data/00_derived/gps_spu_by_distributor.csv` and `wallet_waterfall.csv` (distributor
code and country), `01_data/00_derived/warranty_by_db_year.csv` (RSA is Norway, WAE is Hungary, Petros is
Greece), and the SAP line numbers in `01_data/11_planning/FY2027  BP VP&ACC.xlsx`, sheet `VP FY27`.

The mapped lines cannot be added up to reproduce a plan total. On the sheet as it stands the rows sum to
more than the total it publishes (EUR 44,351,803 against EUR 35,284,444), because the smaller lines and the
residual OTHERS line run their own course rather than adding to the lines above them. Use the published
total, not a sum of the rows.

## 6. Concentration - why the network average misleads

From the 2025 calendar year data:

| Market | Parts billed, EUR | Share of network |
|---|---:|---:|
| IUK (UK light commercial) | 6,131,920 | 18.9% |
| ITUK (UK trucks) | 5,564,544 | 17.2% |
| UTI (Israel trucks) | 3,331,512 | 10.3% |
| UMI (Israel light commercial) | 3,319,344 | 10.3% |
| Germany | 2,535,932 | 7.8% |
| Belgium | 2,109,332 | 6.5% |
| Portugal | 1,709,794 | 5.3% |
| **Network** | **32,381,312** | **100%** |

The top five entities are 64.5% of the network. The two UK entities together are 36.1%. The two Israel
entities together are 20.5%. So a network-level percentage is roughly a statement about the UK and Israel,
weighted. Almost any decision-grade question needs the market cut, not the network cut.

## 7. The commercial model in one paragraph

Every truck in service consumes service parts every year: filters at the service interval, and wear parts
(brake, clutch) on a longer cycle. If you multiply the fleet by a defensible euro target per truck per year,
you get the total spend that fleet *should* generate - the ceiling. The share of that ceiling that arrives at
ISZE is the capture rate. The rest is either with an independent aftermarket supplier, or a service that
never happened, or a part that was bought elsewhere in the chain. The whole aftersales argument is about
closing that gap: which part families, in which markets, how much euro, and what action (price, availability,
technical campaign, dealer incentive) would move it.

The service-demand cover measure answers the same question from the other end: given the maintenance
schedule, how many of the expected units did we actually sell. Both views are needed because one is in euro
and the other is in units and part families.

## 8. Who does what

| Role | Entity |
|---|---|
| VP Vehicle Parts Sales | Isuzu Motors Europe (ISZE) - this role is Jerome's |
| Sales management | ISZE |
| Accessories | ISZE |
| Reporting and Power BI | ISZE |
| Materials expeditor | Isuzu Truck UK (ITUK) - the UK truck distributor |
| General manager, parts | Isuzu UK (IUK) - the UK light commercial distributor |
| Head of aftersales | Isuzu Sales Deutschland (ISD) - the German distributor |
| Parts and logistics | Harris Group Ireland - the Irish distributor |
| International parts, product marketing | Isuzu Motors Limited (IML) Japan |
| International parts, sales | Isuzu Motors Limited (IML) Japan |

Personal names are deliberately left out of this file, because it is uploaded to a research model and the
names add nothing to the reasoning. Use the role and the entity in any answer. Anything that leaves ISZE
uses roles as well, never personal names.

## 9. Restricted background

[This section was omitted from the handover because the source explicitly prohibits its reproduction. Other sections are unchanged.]

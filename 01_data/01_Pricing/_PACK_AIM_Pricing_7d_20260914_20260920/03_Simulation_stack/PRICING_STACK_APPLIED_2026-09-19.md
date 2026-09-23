# The weighted increase of all prices

*Built 2026-09-19T10:45:44+00:00 · window 1 Jul 2025 to 30 Jun 2026 · recipe in_scope and unpriced_reason null, 47,617 rows, index 5.961599%*

## The method

**weighted increase = SUM(quantity x change in yen base price) / SUM(quantity x previous yen base price) - 1.** It is read off the price comparison itself. Nothing is multiplied in.

This replaces a chain of three factors. Two of them were wrong, because both changes are already in force. The exchange rate of 178.5 is what we pay now, and the 67.3% purchase discount took effect on 5 January 2026. Multiplying by 163.7/178.5 treats a settled rate as a move to come, and multiplying by 0.673/0.620 adds a discount increase that is already inside today's prices.

## The headline

| | Rows | Share of weight | Weighted increase |
|---|---:|---:|---:|
| Japan (IML) | 22,731 | 47.71% | **+6.2081%** |
| Thailand (IMIT) | 23,085 | 43.08% | **+6.3088%** |
| no source label | 1,801 | 9.21% | **+3.0601%** |
| **All prices** | **47,617** | **100.00%** | **+5.9616%** |

The share of weight is the quantity-weighted share of the previous yen base price. The two source rows do not sum to 100% because 1,801 rows carry no source label in the price list.

## Figures replaced

| Measure | Earlier factor chain | Measured weighted increase |
|---|---:|---:|
| Whole priced book | +1.80% | **+5.9616%** |
| Japan (IML) | +5.74% | **+6.2081%** |
| Thailand (IMIT) | -2.45% | **+6.3088%** |

## Each market

The same measure, taken on the rows that belong to each market, so each market sheet carries a measured figure rather than a ratio of two constructed prices.

| Market | Rows | Part numbers | Billed EUR | Weighted increase | Japan | Thailand |
|---|---:|---:|---:|---:|---:|---:|
| PR00 | 32,434 | 10,968 | 12,831,246 | **+5.9211%** | +6.3925% | +6.4001% |
| UTI | 1,869 | 1,869 | 3,400,405 | **+5.5808%** | +5.6312% | +9.2395% |
| UMI | 2,428 | 2,428 | 2,429,160 | **+5.6370%** | +6.2140% | +6.2725% |
| CIS | 3,090 | 2,674 | 1,455,811 | **+4.8455%** | +4.6445% | +6.3769% |

UTI is sold-to 1799 and UMI is sold-to 1797. They are separate Israel distributors and are never combined.

## The exchange rate is applied, not decided

The rate is issued by ISZJ and applied. It is a corporate rate, not a commercial choice, and no part of it is handed to a distributor or held back as a decision. An earlier version of this analysis presented that as a dial with a five-point scale and a claim that one setting could not satisfy both sources. All of that was invented and has been removed.

## How the IML base price works - source documentation

**1. The Export Base Price is built up from IML's own costs, and our purchase price is a discount off it.**

*Source: Masumi Hayakawa (IML), 10 November 2025, "FW: ISZE 移転価格対応 10/30打ち合わせメモ・今後の対応事項につきまして"*

The factors are 62% on vehicle parts and 73.5% on industrial engines, applied to IML's Export Base Price. Worked example: an Export Base Price of 1,000 JPY gives a purchase price of 620 JPY on vehicle parts. The Export Base Price therefore sits above our purchase cost by construction, and it is not a restatement of any single cost line of ours.

**2. IML builds its offer price from supplier cost plus a target gross profit.**

*Source: Hideya Kondou (ISZJ), 24 November 2020, "ITUK向けMMU新規ハーネスの価格設定について"*

Normal at 25% gross profit, Best at 17%. So the Export Base Price is a supplier cost plus a stated margin - a build-up, not a rebilling of anyone else's cost.

**3. The discount change and the base-price revision happen at the same moment.**

*Source: Takayoshi Suzuki, 22 December 2025, "discount/whole sales ratio revisoin from Jan 5th 2026"*

Valid from 5 January 2026, and the mail states it is "the same timing with annual EBP revision". This is why the discount cannot be treated as a forward move: it was applied when the base price was last revised.

**4. The base price and the class letter arrive together from Japan.**

*Source: Peeraya Sawangsaensuk (IMIT), 29 April 2026, "RE: base price class"*

"Please find the B/P, Price Class, and remark as detailed below." The class letter is issued with the base price, so the class factor and the base price move on the same cycle.

## Two open items - flagged, not resolved

**Our configuration carries only the vehicle-parts rate**

03_analytics/isze_pricing/config.yaml holds J: 0.673, which is the vehicle-parts rate - 1 minus the 32.7% discount in Masumi Hayakawa's mail of 10 November 2025. The industrial-engine rate is different: 73.5% in 2025, moving to 79.7% in 2026 (1 minus 20.3%). Our configuration applies that rate to every Japan-sourced part, so an industrial-engine part is priced on the vehicle-parts rate.

*Next step: config.yaml is left alone, exactly as it stands. Question for IML: confirm the current industrial-engine rate and which part families it covers.*

**IML states a different revision size from ours**

Masumi Hayakawa's mail of 10 November 2025 says the CY2026 IML base price revision has an impact of "around 3% increase for ISZE (weighted average)". We measure 5.9616% on the published recipe. These are probably different revisions or different scopes - theirs may be a purchase-cost impact over a different window.

*Next step: Open reconciliation item, and it is left open rather than closed by choosing an explanation. Ask IML for the window, the scope and the weighting behind the 3%.*

## What could not be verified

- The weighted increase is measured on the price comparison itself. No exchange rate and no discount is multiplied into it.
- Rows with no source label carry no source split. Their weighted increase is reported separately rather than being assigned to Japan or Thailand.
- Volume and mix are held flat. This is the arithmetic of the price move, not a forecast.

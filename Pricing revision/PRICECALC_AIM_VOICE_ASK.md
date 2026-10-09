# One decision that unlocks AIM-led PriceCalc

As of 2026-10-07. Spec open question 1 / pricing roadmap §2.7.

## The question

Can ISZE set (or negotiate) the margin for **new part numbers** by **AIM category target %GM**, instead of accepting IML’s class letter as the only margin?

Answer in one line: **yes** / **no** / **yes for launch only (P700 / D-Max 2.2L)** / **ask IML first (name who)**.

## What each answer does

| Answer | What PriceCalc does |
|---|---|
| **yes** | AIM Margin Lookup becomes the margin driver for new PNs. Class letter stays only if SAP still needs it as a label. |
| **no** | Keep today’s path: class letter sets the SAP price. AIM target stays CHECK only (the mode the workbook ships in). |
| **yes for launch only** | Same as yes, but only for named new platforms; everything else stays class-led. |
| **ask IML first** | No change to PriceCalc until that conversation lands. |

## Why it matters

Class assignment is margin assignment for the life of the part. A new PN decision is worth more than several years of percentage list increases. The AIM skip is this decision — not a file swap.

## Already built (waiting on your answer)

- Config aligned to live rates (FX 178.5, J 0.673, class T at 40% GM)
- AIM category → proposed target %GM table in CHECK mode
- Ops rules: supersession inherits AIM; new PN assigns AIM then reads the table; SAP sheets stay in PriceCalc

Workbook: `01_data\01_Pricing\ISZE_PriceCalc_AIM_20261007.xlsx`

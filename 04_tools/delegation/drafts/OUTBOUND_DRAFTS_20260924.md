# Outbound drafts — scraper redo (cards 3.2 and 3.5)

**Status:** DRAFTS. Nothing sent. Jerome sends, edits or bins. Claude never sends.
**Written:** 2026-09-24
**Update 2026-09-25:** draft A (Eucon) is **HELD — do not send**; see the hold notice at the top of section A.

---

## A. Eucon — current status of the PartsPool account + a larger basket (card 3.2)

> **STATUS 2026-09-25: HELD — do not send as written.**
>
> The premise of this mail is wrong, so it must not go out. Per `00_docs/EUCON_LICENCE_BRIEF_2026-09-24.md`, the PartsPool contract has already ended: Jerome cancelled on 6 January 2026 and Eucon confirmed on 8 January 2026 that the service ends on **31 July 2026** (PartsPool is Eucon's online parts-price service, also called Market Data Engine). There is no live account to ask about, so "is the account still live?" is already answered and neither version of this mail should be sent.
>
> Two standing rules travel with this hold: nobody logs in to the Eucon portal (the contract has ended), and nobody asks Eucon what the `OE RRP` column means.
>
> Held by cursor (doc truth repairs), 2026-09-25. **Nothing was sent and nothing was deleted.** The original text is kept in full and unedited below, so nothing is lost.

**Context you should check before sending:**
- Your calendar has "Eucon annuleren" entries on 15 Jan, 4 Feb and 3 Mar 2026. Yet the PartsPool batch search still ran on **29 Mar 2026** (basket "top 100", countries DE, DK, PT, SE, NO). I don't know whether the cancellation went through. The answer decides whether this mail is a renewal or an upgrade question.
- If the account is still live, **you may not need Eucon's help at all.** You can upload a bigger basket yourself. A ready file with the **491 tier A parts** (part numbers only) is at
  `C:\Users\jerom\Desktop\claude\ISZE\04_tools\delegation\drafts\partspool_basket_tierA.csv`

**Subject:** PartsPool — account status and larger basket

Hello [Eucon contact],

Our PartsPool batch search of 29 March (top 100 parts; DE, DK, PT, SE, NO) worked well. Before we plan the next round, two questions:

1. What is the current status and end date of our PartsPool access?
2. We would like to run about 500 part numbers, adding UK, PL and IL to the countries. Is that covered by our current package? If not, what would it cost per run, and for a quarterly run?

A short answer is fine. We can send the basket file as soon as we know the limits.

Best regards,
Jérôme Van der Pluym

---

## B. TecAlliance — quote for OE-to-aftermarket data (card 3.2)

**Subject:** Quote request — TecDoc OE Parts Data and IAM prices, Isuzu commercial vehicles

Hello,

Isuzu Motors Europe (parts distribution) is looking at licensing TecDoc data for an internal price-positioning analysis. The scope we have in mind:

- **TecDoc OE Parts Data** for Isuzu: OE-number-to-aftermarket-number matching, covering N-Series, F-Series and D-Max.
- **The IAM Prices / OE Prices module**, if it is available for these makes and for these markets: UK, DE, PL, PT, the Nordics and Israel.
- Delivery by data package (SFTP) or web service, whichever suits a small internal team better.
- Internal use only: no resale and no publication.

Could you send a quote for a one-year licence, including any minimum term? Please also say whether a trial or sample extract of about 50 part numbers is possible.

Best regards,
Jérôme Van der Pluym
Isuzu Motors Europe

---

## C. Harris Group (Isuzu Ireland) — competitor price basket (card 3.5)

**Correction to the delegation file:** Harris Group is **our Irish distributor** (sold-to 76), not a competitor. So the Ireland basket works best as a request **to** Harris to collect competitor prices, not a request to them *as* a competitor. The other four names (Colm Burns, D. Dennehy, H&I Parts, North Dublin Commercials) are what Harris would be benchmarking against.

**Basket:** the 30 maintenance and wear parts with the highest billed value at Isuzu Ireland over the last 12 months. They cover **13.8%** of Ireland's billed €. The list below is part numbers and descriptions only, no prices:
`C:\Users\jerom\Desktop\claude\ISZE\04_tools\delegation\drafts\ireland_quote_basket_30.csv`

**Honest question before sending:** asking a distributor for competitor prices can come back as "then lower your price". Decide whether this is framed as a joint maintenance-parts exercise (the same framing as the ITUK maintenance-parts pilot) or kept light.

**To:** John Cummins, Parts & Logistics Manager, Harris Group
**Subject:** Maintenance parts — quick market price check, 30 parts

Hello John,

We are building a better picture of where Isuzu maintenance parts sit against the local market, country by country. Ireland is hard to read from outside: the independents there don't publish prices online.

Could you help with a light check? Attached are 30 filters, brake and clutch parts. For whichever you can, please give the price a workshop would pay locally for the nearest aftermarket equivalent, and the brand if you know it. Rough figures are fine. There is no need to cover every line.

If this is useful for you too, we can repeat it each quarter and share what we see from the other markets.

Best regards,
Jérôme

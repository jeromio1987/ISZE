# Coverage decision: keep building our own cross-reference, buy a licence, or stop

**24 September 2026 · internal · a recommendation only.** Nothing was bought, no vendor was contacted, nothing was subscribed to.

A cross-reference is the table that says "competitor brand X, part number Y, fits the same slot as our Isuzu part Z". Without it we cannot find a competitor's price for our part. OE means original equipment (our genuine part). IAM means the independent aftermarket (Bosch, Febi, Blue Print and so on). Tier A is the 491 highest-billed lines on the ranked list, worth EUR 21,312,526 of the EUR 34,612,569 billed over the last 12 months.

## The answer

**Stop growing our own cross-reference and spend the next step on testing a licence against the parts we cannot reach. That means a test, not a purchase.** The number that decides it is **EUR 13,543,552**: the Tier A billing that has no competitor number and no peer number, so our own methods can never reach it. Everything our own route can still add is **EUR 1,669,216** in total, and both pieces of it are already identified.

## Five things the brief had slightly wrong, or did not have

1. **The Eucon contract has ended.** Eucon is the German firm whose PartsPool service (a web tool that searches shops for competitor parts and prices) supplied our matches. On 8 January 2026 Eucon confirmed in writing "the termination of the contract as of 31. July 2026". The mail extracts were taken on 19 August 2026 and show no renewal after that.
2. **"Our own" cross-reference is entirely Eucon's.** All 6,455 competitor links in the graph come from Eucon products: 6,358 from Eucon extracts and 97 from the Eucon UK survey. None comes from our own scraping. So carrying on with our own build means working from a frozen extract that no longer receives new data.
3. **63.5% is a share of euro, not of parts.** 342 of the 491 Tier A lines is 70% by count. Their EUR 13,543,552 is 63.5% of Tier A billing. Three of the 342 are not parts.
4. **Only one of the three retired sources gave false matches.** Mekonomen's search ignored the part number, and seven of its false prices reached a pricing pack for UMI (one of our two Israel distributors). Auto365 carries no OE number and its robots rules bar all crawlers. Tranzparts carries no Isuzu. Autodoc and Oscaro block us completely with a bot check.
5. **Searching by our own number is not quite zero on the 342.** KS International (KS) is a UK parts shop and the only weekly source that searches by our part number. It searched 146 of the 342 lines and showed an aftermarket listing on 18 of them, worth EUR 757,300. A KS listing is a shop's own product. It is not a competitor number that anyone has confirmed fits.

The spot check says the matches we hold are sound: 0 wrong and 2 unverifiable out of 20, and 11 of 12 rows were confirmed by a second, independent shop. The problem is how far the matches reach, not whether they are right. That check was done by AI agents reading public pages. No person did it.

## What each route reaches, costs, and cannot do

| | Keep building our own | Buy a licence | Stop |
|---|---|---|---|
| **Reaches today** | 131 part numbers, EUR 5,639,298 (16.3% of billing). Tier A: 74 parts, EUR 5,172,315. Only 22 competitor numbers have two independent witnesses, and they cover 18 parts, EUR 1,256,258 | Unknown until tested. The one figure we have measured: the last PartsPool batch (29 March 2026), a basket named "top 100", came back with matches on 45 Isuzu numbers | The same 131 parts and EUR 5,639,298, frozen |
| **Can still add** | 43 competitor numbers with two or more sources and no price yet: 22 parts, EUR 911,916. Plus the 18 KS listings among the 342, worth EUR 757,300. **Total EUR 1,669,216** | Possibly some of the EUR 13,543,552. It is the only route that could reach those parts | Nothing |
| **Costs** | No cash. Little machine time: the weekly jobs are capped at 30 minutes each, and a full KS pass is estimated at 3.5 to 4 hours. **Staff and agent time was never logged per source, so I cannot give it a euro figure.** The measured cost so far is errors, not hours: see Mekonomen above | **No figure is recorded anywhere in the workspace.** Eucon invoices exist: a budget approval in August 2025, and two invoices for this financial year sent on in January 2026. No amount appears in the mail extracts, DECISIONS.md or the docs. The only outside figure is an integrator's own "orientative, not official" range for a TecDoc licence of EUR 7,000 to 25,000 a year (TecDoc is the European parts catalogue run by TecAlliance). It is a third-party claim recorded on 18 September, not a list price and not a quote. It is annual and priced on the buyer's revenue | No cash. The cost is that price revisions and UK defence decisions are made without a competitor view on 63.5% of Tier A billing |
| **Cannot do** | It can only search with a number we already hold, and **for the 342 there is none.** Searching by our own number works only on shops that list OE numbers. KS answered on 18 of 146 of these lines, and the rest of the market is blocked, retired or indexed by category (T&M Commercials, a UK Isuzu specialist, lists 91 products under four maintenance categories and no part numbers). It gets no new matches now that Eucon has ended. The price model does not fill the gap: it is typically 46% off, against 48% for one flat ratio | **It is unverified on Isuzu trucks.** TecDoc lists Isuzu N- and F-series vehicle types, but nobody has checked that one of our part numbers comes back with aftermarket equivalents. Use is restricted: copying the data into other systems is barred. Prices are a separate, optional module. Eucon was basket-based, and five years of it reached 131 of our 16,511 numbers | It adds nothing new. The prices we hold are dated 2023, March 2024 and March 2026, and they get older every month |

## Recommendation

**Freeze our own build and test a licence on the gap.** In practice:

1. Keep the two weekly fetches (KS and T&M Commercials) as they are. Build no new scrape source and do no more work on the price model.
2. Ask for two quotes, each with a sample run on the same fixed list of 50 of the 342 Tier A lines. One is TecAlliance's OE Parts Data, quoted by TecAlliance sales or an authorised TecDoc data partner. The other is re-opening Eucon PartsPool, quoted by Eucon's account management. Eucon's past price is held by our Finance accounts-payable team and in the signed August 2025 budget approval. Draft wording exists in `04_tools\delegation\drafts\OUTBOUND_DRAFTS_20260924.md`, but that draft predates the finding that the contract has ended and needs correcting before it is sent.
3. **Buy only if the sample finds competitor numbers for more than 12.3% of the sample's billed euro.** 12.3% is EUR 1,669,216 divided by EUR 13,543,552: what our own route can add for free, measured against what it can never reach. A licence that does no better than that is money for nothing.

## What would change the answer

**If the sample comes back under 12.3%, the answer becomes stop.** We keep what we hold, buy nothing and build nothing. The 342 would then be parts that nobody in the market cross-references by number, and more spending would not change that.

There is a second condition, which pushes the same way harder. If Eucon's terms forbid using the extracts after 31 July 2026 (the open question for the licence brief), our own route falls from 131 parts to zero. The choice then becomes licence or stop for the whole book, not only for the 342.

---
*Sources, all read on 24 September 2026:* `00_docs\agent\AFTERMARKET_INTELLIGENCE_STATE_20260924.md`; `04_tools\aftermarket_intelligence\state\` (CROSSREF_GRAPH_REPORT.md, RATIO_MODEL_REPORT.md, MATCH_INDEX_REPORT.md, crossref_edges.csv, seed_reach_tierA.csv); `04_tools\delegation\state\refresh_tiers_LOCAL.csv` (billed euro, tiers); `04_tools\autodoc_scraper\` (refresh_and_check_drift.py job list and retirement notes, ks_results.csv of 22 September, tmc_results.csv); `00_docs\roadmaps\scrapers.md`; `00_docs\agent\SCRAPER_REDO_DELEGATION.md` section 8; `01_data\90_INBOX\_aftermarket_spotcheck_20260924\` (result and independent-witness file); `01_data\90_INBOX\scrape_targets\crossref_databases.md` (TecDoc range, section 2.1); `02_dashboards\Data\90_INBOX\eucon_mail_extracts\` (termination confirmation of 8 January 2026, budget approval of August 2025, PartsPool batch of 29 March 2026; the password note was not opened). The EUR 1,669,216, the 12.3%, the 16.3% and the 18 KS listings among the 342 are my own calculations from those files, using read-only scripts that wrote nothing into the workspace.

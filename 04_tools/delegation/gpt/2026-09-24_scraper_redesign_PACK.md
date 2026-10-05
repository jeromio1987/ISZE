# GPT review pack — competitor price collection, redesign (card 0.5)

Paste everything below the line into GPT. Then paste its answer into
`C:\Users\jerom\Desktop\claude\ISZE\04_tools\delegation\gpt\2026-09-24_scraper_redesign_REPLY.md`

No price list, no sales lines and no dealer details are in this pack. Aggregates only.

---

You are a second reviewer. Challenge; do not agree by default.

**Context.** A European truck and pickup parts distributor (one brand, about 16,500 parts billed per year) wants competitor price observations to guide list pricing and maintenance-parts campaigns. Until now it scraped web shops by searching the brand's own 10-digit part numbers. Result: one usable UK specialist shop prices about 21% of the parts it is asked about. Four other shops were dropped: two don't carry the brand, one blocks crawlers, and one is the distributor's own shop.

**Proposed redesign.**
1. **Match numbers first, then price.** Build a table linking each brand part number to the aftermarket numbers that replace it (Bosch, Mann, Blue Print and so on). Sources: an existing licensed Eucon extract (45 part numbers, 432 aftermarket numbers), a paid TecDoc licence (quote pending), and shop product pages that print the OEM number. Then price the aftermarket numbers, which far more shops list.
2. **Only sites that allow it.** Respect robots.txt, logins and bot challenges; never bypass them. Blocked sites are replaced by licences, APIs or asking.
3. **Distributors as a source.** A one-line intake for every "competitor quoted lower" case from distributors: part, competitor brand, price, date, country.
4. **Refresh by value.** Tier A = 491 parts, 61.6% of billed €, refreshed weekly. Tier B = 1,809 parts, 28.3%, monthly. Tier C = 14,211 parts, 10.1%, estimated only, using a competitor-to-list ratio by category and price class.
5. **Automatic triggers.** A new or superseded part number, a price revision, or a new "competitor quoted lower" case queues a price check.
6. **One price-observation table.** Every row carries a price type (online retail, trade, grey genuine, survey, dealer, quote, estimate) and a vintage, and types are never averaged together.
7. **Division of labour.** A cheap LLM (DeepSeek) extracts fields from page text only when a normal parser fails. Every extracted price must appear word for word in the source, or the row is rejected. An expensive LLM orchestrates and checks samples.

**Question.** Is this the right design? What fails first?

**Answer format.** Verdict first. Then the 3 weakest points. Then what you would measure in the first month to know whether it works. Then anything important that is missing.

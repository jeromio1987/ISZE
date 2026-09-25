# Eucon licence brief

24 September 2026 · internal · prepared for Jerome · nothing sent to anyone, no Eucon file touched

**Verdict.** The first question already has a written answer. On 8 January 2026 Eucon confirmed that our PartsPool contract ends on 31 July 2026. PartsPool is Eucon's online parts-price service, also called Market Data Engine. So as of today the contract has ended. The question that decides the match rows is therefore not whether the contract is live. It is what Eucon's terms say about data we downloaded while it was live, and nobody has those terms in the workspace.

**What the files show.** The two new files were saved into the workspace today at 15:59 and 16:00. Their contents are dated 15 March 2024 and 28 July 2025, both inside the paid period. So they are older downloads, not a final extract and not a renewal. The "Eucon annuleren" (Dutch: "cancel Eucon") calendar entries from January to March 2026 line up with the cancellation mail of 6 January. One batch search still ran on 29 March 2026, inside the notice period, and it produced the March 2026 cross-reference we already use. The match index holds 7,701 rows, and 7,157 of them (93%) come from Eucon files. The other 544 map Isuzu genuine parts to BVP, our own value line, so they are not competitor matches. The work order's figure of about 4,600 was an estimate made before the index was built.

## The four questions, in order

| # | Question | Who can answer (role) | Status |
|---|---|---|---|
| 1 | Is any Eucon contract still live? Was the 31 July 2026 end ever reversed, is there any Eucon invoice dated after it, and were the 2021 benchmark and the 2023 price survey bought as separate projects with their own terms? | The contract owner in Sales – Vehicle Parts; Accounts Payable (Accounting, Finance & Corporate Planning) for invoices; the manager who signed the August 2025 budget approval | Mostly answered: ended 31 July 2026. The other parts are still open |
| 2 | Do the terms allow price monitoring, meaning comparing our prices with competitors' prices and using their part numbers to search web shops? | The signed order and the version of Eucon's general terms it refers to. The contract owner or Purchasing finds them. If we do not hold them, only Eucon's key account manager can supply them. In-house legal reads them | Open. No contract text on disk |
| 3 | Do the terms allow processing outside the EU (European Union), including sending rows to an AI (artificial intelligence) service hosted outside the EU? DeepSeek is the one the plan names | In-house legal for Eucon's terms. IT / information security for the company's own rule on sending company data to outside AI services | Open. Part numbers and prices are not personal data, so this is about the contract and confidentiality, not privacy law |
| 4 | Now that the contract has ended: may we keep using what we downloaded, must we delete or return it, and does that also cover files we built from it (the match index, price-gap tables, dashboards)? | In-house legal, reading the termination and confidentiality clauses | Open. Because the contract has ended, this is now the question that decides the rest |

## What each answer opens or closes

The three coverage routes: **(1)** carry on building our own competitor cross-reference, **(2)** buy a paid cross-reference licence, **(3)** stop.

- **Q1: ended, as confirmed.** No fresh Eucon data. Eucon can only come back as a new purchase under route 2, alongside other vendors. Route 1 can only run on what we already hold, and only if Q4 allows it.
- **Q2: allowed.** Route 1 keeps its starting list of Eucon competitor numbers. **Forbidden, or the terms say nothing:** that starting list is gone. Route 1 would restart from the 544 own-brand rows, which contain no competitor numbers. Route 2 becomes the only way to get a cross-reference, and route 3 becomes a real option.
- **Q3: allowed.** Route 1 may process Eucon rows with the outside-EU AI service. **Forbidden:** route 1 continues with processing inside the EU only. The outside-EU step stays closed for Eucon rows but not for other rows, subject to IT's rule.
- **Q4: continued use allowed.** Route 1 stays fully open on the rows we hold. But they will age: the newest are from March 2026, and nothing refreshes them without route 2. **Delete or return required:** route 1 loses 93% of its rows. The coverage figures built on them can no longer be quoted, and only routes 2 and 3 remain.

## Stop until a lawyer has read the terms

- Nothing that comes from Eucon goes to DeepSeek or any other service outside the EU.
- Eucon-derived rows are not shared with anyone new outside the company, such as distributors or shared packs.
- Nobody logs in to the Eucon portal. The contract ended on 31 July 2026, so a login now would use a service we no longer have.
- Do not ask Eucon what the `OE RRP` column means (step 4 of the state note). Asking tells Eucon we are still using the data after the contract ended. Legal should decide first whether to ask, and how.
- Do not delete, move or rename any Eucon file. If deletion turns out to be required, the lawyer should say what to delete and how. Deleting now would destroy the record of what we hold.

## Safe to do whatever the answers are

- Find the contract papers internally. That means the 2021 PartsPool order or order confirmation, the renewal from early 2023 (the calendar shows a renewal deadline of 1 February 2023), Eucon's general terms, and the orders for the 2021 and 2023 surveys. The 8 January 2026 termination confirmation is already on disk.
- Take the plain-text Eucon password out of the workspace. Jerome has to do this; any agent that reads the folder can read the password.
- List every place Eucon-derived data sits, so a delete or return request could be met the same day. Every row in the match index already names its source file, so the Eucon rows can be switched off in one step.
- Carry on with work that uses no Eucon rows: the classification join, the web searches by our own part number, and asking route 2 vendors for quotes.

<sub>Sources: mail extracts in `02_dashboards\Data\90_INBOX\eucon_mail_extracts\` (6 and 8 Jan 2026 cancellation thread, 29 Mar 2026 batch-search notice, Aug 2025 budget approval, Jan 2023 renewal calendar entry); row counts by source from `04_tools\aftermarket_intelligence\state\match_index.csv`; `00_docs\agent\AFTERMARKET_INTELLIGENCE_STATE_20260924.md` §3 and §7. The coverage decision file did not exist when this was written, so the three routes are as defined in the work order. `NOTE_Eucon.txt` was not opened.</sub>

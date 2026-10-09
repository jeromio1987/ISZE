# P06 — Monthly return per distributor

> Read `00_START_HERE.md` first. Needs P02, P04. Plan mode, then build.

## Goal
A self-contained HTML page per distributor per month that gives the distributor something worth having in return for its data: its own billing and sales to dealer, genuine and BVP mix in euros, maintenance-parts coverage, IDS position, and — once dealer detail exists — the same per dealer. Beside an **anonymous** network average. No rankings. Draft only.

## Why
Participation is kept only if it pays back in the same month. This page is the return. It is a **shared** document: careful business English, no internal nicknames, no personal names, no other distributor named.

## Read first
Spec §11. The existing one-pagers in `Isuzu Universe/02_Atlas/DISTRIBUTOR_ONE_PAGERS_2026-09/` (format, wording, source lines) and their build manifest. `.cursor/rules/isze-external-iml-language.mdc`, `isze-html-openable.mdc`, `isze-verify-rendered-output.mdc`, `isze-best-chart.mdc`. Universe rules: `Isuzu Universe/01_Strategy/Universe_Commercial_Participation_Model.md` ("Preventing Universe from feeling like ISZE surveillance").

## Build
`04_tools/partner_intake/returns.py`, CLI `returns build --distributor X --period 2027-05 --out <folder>`.
- Content blocks, each with a source line and a coverage note: billed (euros, FY months); billed vs sold on with warranty apart (from P04); genuine / BVP / genuine-with-a-BVP-alternative in euros; maintenance-parts coverage (total first; never plot best capture above 100%); IDS position (own dealers only, population and round stated, UTI ≠ UMI); per dealer purchasing spread **only** when named-dealer data exists, otherwise a plain sentence saying why it cannot be shown.
- Network average is an aggregate over at least five distributors, labelled anonymous; if fewer than five contribute, omit it.
- A "what you can correct" box: the distributor can flag a reading as wrong; no correction mechanism is built here, only the text and the contact role.
- Self-contained HTML (inline CSS, inline chart data, no CDN, no fetch). Looks right at desktop and phone width. Charts follow `isze-best-chart`.
- Output to the folder given on the command line; default `09_meetings/Excellence_Partner_Program_2026/returns/<DB>/<period>.html`. **Draft only; never sent.**

## Acceptance tests
1. Build for two synthetic distributors; each page names only its own distributor (grep the HTML for the other's name and code).
2. No ranking, no "best/worst", no league table anywhere (assert on words and structure).
3. With no named-dealer data the dealer block shows the explanatory sentence and **no** per-dealer figure derived from a national total.
4. Rendered check: open the HTML with Playwright at 1280 and 390 px; assert non-empty chart series, no horizontal scroll, and save screenshots; read them.
5. Forbidden-word grep passes (sell-out, wallet, street, Book B, Mode A/B, IML v7, any personal name list from config).
6. Numbers on the page equal the numbers from P04 for the same period.

## Return packet
Screenshots (paths), the grep result, the list of blocks that were omitted for lack of data and why.

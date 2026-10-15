# Pad kits outside "Brake Pad Kit" — proposal for the next AIM release

Five disc brake pad kits are filed as brake discs in the AIM release of 11 October, and I propose moving them to Brakes > Pads & Shoes > Brake Pad Kit in the next release. Together they billed EUR 260,016 in July 2025 to June 2026, the window the price revision tool uses (EUR 224,424 in FY2026). The wrong label comes from the AIM workbook itself and has been in every release since 20 September. Two other numbers of the same kit, 8978279580 and 8978279600, are already on Brake Pad Kit. Per part, on the tool's 12 months: 8978279610 EUR 145,942, 5876150640 EUR 71,974, 8978279590 EUR 23,593, 5876150650 EUR 9,919 and 8978279601 EUR 8,588. I also checked every other part whose description starts with "PAD KIT", on the release and on the PR00 price list. There are 25 more pad kits with no AIM label at all: 22 rear caliper kits and 3 kits that have no description in the release. Two of those three have been replaced by front pad kits that are already labelled Brake Pad Kit. None of the 25 has been billed since January 2023, so they do not change the price revision. However, 24 of them have a price on PR00, so I would label them now as well. Until a new release is cut, the price tool keeps the five billed kits at today's price through their own 0% on the Parts sheet, so your 30 September decision already holds. Nothing has been applied. When you say go, the next release is cut from the 11 October one with only these 30 parts changed, and the Power BI export is refreshed after it.

Proposal file, one row per part with the current and proposed labels and the euros:
C:\Users\jerom\Desktop\claude\ISZE\01_data\00_derived\_releases\next_release_proposal_pad_kits_2026-10-15.csv

Builder (it only writes the proposal and checks that nothing else would change):
C:\Users\jerom\Desktop\claude\ISZE\01_data\91_build\build_next_release_proposal_pad_kits_20261015.py

Sources: the AIM release of 11 Oct 2026, the price tool's billed base (price_bp_weighted_compare_pn.csv), sales_fact.parquet for FY2026, and the PR00 list of 13 Mar 2026 from pricing_pn_enquiry.parquet.

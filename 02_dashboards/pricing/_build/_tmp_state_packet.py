from pathlib import Path

p = Path(r"C:\Users\jerom\Desktop\claude\ISZE\00_docs\agent\STATE_PACKET.md")
t = p.read_text(encoding="utf-8")
marker = "## Price revision — AIM source analysis shipped (2026-09-17)"
insert = """## Price revision — customer-first drill (2026-09-17 evening)

Same AIM x source pack, extended. HTML now leads with sold-to customer -> L2 donut -> part-number table.
Excel DB x AIM L1 formula columns D-K are calculated and cached (COM save). Not held filter shows
the full EUR 2.23M pile; Parts billed chip is all-in-scope; single-DB league labels match the selection.

| Item | Path |
|------|------|
| HTML + OPEN | `02_dashboards\\pricing\\ISZE_Pricing_Revision_AIM_Source.html` · `OPEN_Pricing_Revision_AIM_Source.cmd` |
| Excel + OPEN | `01_data\\01_Pricing\\Pricing_Revision_AIM_Source_Analysis.xlsx` · `OPEN_Pricing_Revision_AIM_Source_Analysis.cmd` |
| Receipt | `02_dashboards\\pricing\\ISZE_Pricing_Revision_AIM_Source.SHIP_RECEIPT.json` |

"""
if "## Price revision — customer-first drill" in t:
    print("already updated")
else:
    if marker not in t:
        raise SystemExit("marker missing")
    t = t.replace(marker, insert + marker, 1)
    t = t.replace(
        "**Updated:** 2026-09-17 — price revision on the AIM spine shipped (Excel + HTML); air-filter handoff for the next agent",
        "**Updated:** 2026-09-17 — pricing customer drill + Excel L1 cache fix",
        1,
    )
    p.write_text(t, encoding="utf-8")
    print("STATE_PACKET updated")

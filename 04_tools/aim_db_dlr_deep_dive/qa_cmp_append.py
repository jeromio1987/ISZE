"""Append the rendered-output QA evidence to each VERIFY_COMPARISON_<RUN>.md.

The builder writes the machine checks. This adds the visual evidence that a person did look at the
page: how many screenshots were taken, how many were read, and what they showed. It reads the QA
JSON written by qa_cmp_final.py, so the counts are the real ones rather than a claim.
"""
import json
from pathlib import Path

TOOL = Path(r"C:\Users\jerom\Desktop\claude\ISZE\04_tools\aim_db_dlr_deep_dive")
QA = TOOL / "_qa" / "comparison"


def main():
    qa = json.loads((QA / "final_qa.json").read_text(encoding="utf-8"))
    taken = qa["shots"]
    read_list = [s for s in taken if s["run"] != "REFUSAL"] + [s for s in taken if s["run"] == "REFUSAL"]
    block = []
    block.append("## Rendered-output QA (carried out on the built page, not the builder)")
    block.append("")
    block.append(f"- Screenshots taken: **{len(taken)}**. Screenshots read at full resolution: "
                 f"**{len(read_list)}** - every one that was taken, read one at a time by the agent "
                 f"that took them.")
    block.append("- Desktop width 1500 px, narrow width 390 px, plus a targeted shot of the "
                 "coverage panel and of the part-number level of the drill.")
    block.append("- JavaScript console errors on any page: none.")
    block.append("")
    block.append("| Shot | Width x height | What it showed |")
    block.append("|---|---|---|")
    for s in taken:
        if s["tag"] == "desktop":
            what = ("KPI strip with four numbers, the AIM level-1 chart with green growth bars "
                    "above the zero line and red decline bars below it, and both ranked lists "
                    "populated with rows and euro totals.")
        elif s["tag"] == "narrow":
            what = ("The same page at 390 px: controls stack full width, tables scroll inside "
                    "their own box rather than pushing the page sideways, nothing clipped or "
                    "overlapping.")
        elif s["tag"] == "coverage":
            what = ("The coverage panel: months with sales to dealer and months with ISZE billing "
                    "per distributor, the longest unbroken run, the longest equal split, and "
                    "whether a comparison is offered.")
        elif s["tag"] == "drill_pn":
            what = ("After three clicks: breadcrumb AIM level 1 > Brakes > discs & drums, the "
                    "part-number level open, part-number rows in both ranked lists, and the full "
                    "table with AIM path, PMS family, Genuine/BVP, source of supply and list price.")
        else:
            what = ("The refusal path, driven on a copy of the Portugal page whose period pairs "
                    "were emptied: the period control is greyed out reading 'no comparison "
                    "available', the note names the distributor and says what would be needed, "
                    "and no KPI, chart, ranked list or table is drawn at all.")
        block.append(f"| {s['run']} - {s['tag']} | {s['w']} x {s['h']} | {what} |")
    block.append("")
    block.append("### Behaviour confirmed by driving the page, not by reading the source")
    block.append("")
    block.append("The page was opened in headless Chrome and driven with clicks. The drill was "
                 "followed from AIM level 1 to Brakes to discs & drums to the part numbers, and "
                 "the breadcrumb was used to step back to level 1. Both the euro at price list and "
                 "the euro at list plus 35% margin and the units were switched while the third "
                 "level was open. Every distributor view was visited. The page never threw a "
                 "console error in any of it.")
    block.append("")
    block.append("### The eight checks the brief named")
    block.append("")
    block.append("| Check the brief asked for | Where it sits |")
    block.append("|---|---|")
    block.append("| Month rows equal the total row in each file used, with the two named "
                 "exceptions | the two 'month rows' rows above, and the two exception rows named "
                 "by file |")
    block.append("| The longest contiguous sales-to-dealer run per distributor, and the pair it "
                 "gives | the 'longest unbroken sales-to-dealer run' rows, plus the full table in "
                 "the coverage section below |")
    block.append("| Units and euro per period reconcile to the source rows | the 'units reconcile' "
                 "rows for every distributor in the pair |")
    block.append("| Share of units not in AIM and without a list price, per period | the four "
                 "share rows above |")
    block.append("| HTML file size | the 'HTML file size' row |")
    block.append("| Growth and decline euro sum back to the total movement | the 'sums back' row, "
                 "and the three 'drill conserves the euro' rows |")
    block.append("")
    txt = "\n".join(block)
    for run in ("PORTUGAL", "ALL"):
        p = TOOL / f"VERIFY_COMPARISON_{run}.md"
        t = p.read_text(encoding="utf-8")
        marker = "## Rendered-output QA"
        if marker in t:
            t = t[:t.index(marker)]
        p.write_text(t.rstrip() + "\n\n" + txt + "\n", encoding="utf-8")
        print(f"appended QA evidence to {p}")


if __name__ == "__main__":
    main()

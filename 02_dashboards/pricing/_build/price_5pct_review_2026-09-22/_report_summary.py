"""Read-back of the 2026-09-22 +5% simulation summary. Prints the headline set for chat and QA."""
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
s = json.loads((HERE / "price_increase_5pct_sim_summary_2026-09-22.json").read_text(encoding="utf-8"))
h, mv, v = s["headline"], s["movability"], s["versus_filed_revision"]

print("billed", s["basis"]["billed_eur"], "lines", s["basis"]["lines"],
      "pns", s["basis"]["part_numbers"])
print("+5% all in-scope", h["step_5pct_on_all_in_scope_eur"],
      "| +5% movable", h["step_5pct_on_movable_eur"],
      "| filed step", v["step_filed_eur"])
print("index reproduced", v["index_reproduced_pct"], "| filed - flat(movable)",
      v["difference_filed_minus_flat_eur"])
print()
print("MARKET                     lines        billed  share%      movable billed    filed%     +5% step")
for r in s["by_market"]:
    print(r["market"].ljust(24), str(r["lines"]).rjust(7), str(round(r["billed_eur"])).rjust(13),
          str(r["share_of_billed_pct"]).rjust(7), str(round(r["movable_billed_eur"])).rjust(17),
          str(r["filed_weighted_pct"]).rjust(9), str(round(r["step_5pct_movable_eur"])).rjust(12))
print()
print("SOURCE             lines        billed  share%    filed%  no-move lines   no-move EUR     +5% step")
for r in s["by_source"]:
    print(r["source"].ljust(18), str(r["lines"]).rjust(7), str(round(r["billed_eur"])).rjust(13),
          str(r["share_of_billed_pct"]).rjust(7), str(r["filed_weighted_pct"]).rjust(9),
          str(r["immovable_lines"]).rjust(13), str(round(r["immovable_billed_eur"])).rjust(13),
          str(round(r["step_5pct_movable_eur"])).rjust(12))
print()
print("MARKET x SOURCE")
for r in s["by_market_source"]:
    print(r["market"].ljust(24), r["source"].ljust(18), str(r["movable_lines"]).rjust(7),
          str(round(r["billed_eur"])).rjust(13), str(r["filed_weighted_pct"]).rjust(9),
          str(round(r["step_5pct_eur"])).rjust(12))
print()
print("CANNOT MOVE", mv["immovable_lines"], "lines |", mv["immovable_billed_eur"], "EUR |",
      mv["immovable_share_pct"], "% | +5% it could not collect",
      mv["immovable_step_5pct_if_it_could_move_eur"])
for r in mv["immovable_composition"]:
    print("   reason:", r["reason"], r["lines"], r["billed_eur"], r["share_of_in_scope_billed_pct"])
for r in mv["immovable_sub_masks"]:
    print("   missing:", r["sub_reason"], r["lines"], r["billed_eur"])
print()
print("concentration", s["concentration_share_of_step_pct"])
print("deltas vs 17 Sep", [(f["field"], f["delta"]) for f in s["refresh_vs_2026_09_17"]["fields"]])
print("sum of market billed", round(sum(r["billed_eur"] for r in s["by_market"]), 2))
print("sum of source billed", round(sum(r["billed_eur"] for r in s["by_source"]), 2))

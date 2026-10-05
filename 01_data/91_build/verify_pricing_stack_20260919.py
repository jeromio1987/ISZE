# -*- coding: utf-8 -*-
"""
Verify the pricing stack on the MEASURED method.

Jerome, 2026-09-19, verbatim:
    "you need to look at the weighted increase of all prices not the formula"
    "0.673 was already active as of Jan 2026"
    "we apply the exchange rate just execute ... this is a corporate exchange rate"

WHAT THIS FILE USED TO ASSERT, AND WHY THAT WAS WRONG
  An earlier version asserted a chain of three factors:
      (1 + revision) x (FX_old / FX_new) x (discount_new / discount_old) - 1
  Two of those are already in force, so multiplying them in added moves that are not
  there. A later version replaced the chain with a "pass-through" dial: how much of the
  exchange-rate relief reaches the customer, with a five-point grid and a claim that one
  setting could not satisfy both sources. That was invented. The rate is issued by ISZJ
  and applied; there is nothing to pass on.

THE METHOD ASSERTED HERE
    weighted increase = SUM(qty x delta_jpy) / SUM(qty x bp_prior) - 1
  on the published recipe: in_scope == True AND unpriced_reason IS NULL -> 47,617 rows.
  It reproduces the published index of 5.9616% to six decimals.

  Asserted: no exchange rate and no discount is multiplied into the move, no
  pass-through dial or grid exists in any output, and the two open items (the
  industrial-engine rate, the 3% versus 5.96% revision gap) are present and marked as
  unresolved.

Run: python 01_data/91_build/verify_pricing_stack_20260919.py
"""
from __future__ import annotations

import io
import json
import sys
from pathlib import Path

import pandas as pd

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

ISZE = Path(r"C:\Users\jerom\Desktop\claude\ISZE")
DERIVED = ISZE / "01_data" / "00_derived"
INBOX = ISZE / "01_data" / "90_INBOX"
DASH = ISZE / "02_dashboards" / "pricing"
JSON_IN = DERIVED / "pricing_stack_applied_2026-09-19.json"
MD_IN = INBOX / "PRICING_STACK_APPLIED_2026-09-19.md"
CSV_IN = INBOX / "pricing_stack_applied_2026-09-19.csv"
HTML_IN = DASH / "PRICING_STACK_APPLIED_2026-09-19.html"
CMD_IN = DASH / "OPEN_PRICING_STACK_APPLIED.cmd"

RECIPE_INDEX = 0.059616
RECIPE_J, RECIPE_T = 0.062081, 0.063088
PR00_REGIONS = ("WEST", "SOUTH", "EAST", "NORDICS", "MIDDLE_EAST")
SRC_J, SRC_T = "J", "T"

# the pass-through vocabulary that must not appear anywhere
BANNED = ("pass-through", "pass through", "passthrough", "pass_through",
          "retain the relief", "retains the relief", "retain the rest",
          "hand on", "hand it on", "one dial cannot satisfy")

fails = []


def say(m: str = "") -> None:
    print(m)
    sys.stdout.flush()


def check(label: str, got, exp, tol: float) -> None:
    ok = abs(float(got) - float(exp)) <= tol
    say(f"  {'PASS' if ok else 'FAIL'}  {label:<64} got {float(got):>15,.6f}  "
        f"expected {float(exp):>15,.6f}")
    if not ok:
        fails.append(f"{label}: got {got}, expected {exp}")


def check_bool(label: str, ok: bool) -> None:
    say(f"  {'PASS' if ok else 'FAIL'}  {label}")
    if not ok:
        fails.append(label)


say("=" * 100)
say("1. THE MEASURE, RECOMPUTED FROM THE RAW FILES")
say("=" * 100)
cmp_ = pd.read_csv(DERIVED / "price_bp_weighted_compare_pn.csv",
                   dtype={"part_number": str, "customer_code": str})
rec = cmp_[(cmp_["in_scope"] == True) & cmp_["unpriced_reason"].isna()].copy()  # noqa: E712
rec["pn"] = rec["part_number"].astype(str).str.strip().str.zfill(10)
rec = rec[rec["billed_qty"].notna() & rec["bp_prior_revised"].notna()
          & rec["delta_jpy"].notna()].copy()
say(f"  recipe rows: {len(rec):,}   (expected 47,617)")
check_bool("the recipe row count is 47,617", len(rec) == 47617)
check_bool("delta_jpy is the difference of the two base prices",
           bool((rec["delta_jpy"] - (rec["bp_new_jpy"] - rec["bp_prior_revised"]))
                .abs().max() == 0))
rec["weight"] = rec["billed_qty"] * rec["bp_prior_revised"]
rec["step_yen"] = rec["billed_qty"] * rec["delta_jpy"]
idx = rec["step_yen"].sum() / rec["weight"].sum()
check("the published 5.9616% reproduces on the recipe", idx, RECIPE_INDEX, 1e-6)

pl = pd.read_parquet(DERIVED / "pricing_list_pn.parquet",
                     columns=["part_number", "source", "is_superseded_row"])
pl = pl[pl["is_superseded_row"] != True].drop_duplicates("part_number")       # noqa: E712
pl["pn"] = pl["part_number"].astype(str).str.strip().str.zfill(10)
rec = rec.merge(pl[["pn", "source"]], on="pn", how="left")
rec["srclab"] = rec["source"].where(rec["source"].isin([SRC_J, SRC_T]), "(none)")

BY_SRC = {}
for s in (SRC_J, SRC_T):
    g = rec[rec["srclab"] == s]
    BY_SRC[s] = {"rows": int(len(g)),
                 "billed": float(g["net_sales_value"].sum()),
                 "weight_share": float(g["weight"].sum() / rec["weight"].sum()),
                 "increase": float(g["step_yen"].sum() / g["weight"].sum())}
check("Japan, recomputed", BY_SRC[SRC_J]["increase"], RECIPE_J, 1e-5)
check("Thailand, recomputed", BY_SRC[SRC_T]["increase"], RECIPE_T, 1e-5)
say(f"  Japan    {BY_SRC[SRC_J]['rows']:,} rows   "
    f"{100*BY_SRC[SRC_J]['weight_share']:6.2f}% of weight   "
    f"{100*BY_SRC[SRC_J]['increase']:+.6f}%")
say(f"  Thailand {BY_SRC[SRC_T]['rows']:,} rows   "
    f"{100*BY_SRC[SRC_T]['weight_share']:6.2f}% of weight   "
    f"{100*BY_SRC[SRC_T]['increase']:+.6f}%")


def mask(code):
    if code == "PR00":
        return rec["region"].isin(PR00_REGIONS)
    if code == "UTI":
        return rec["customer_code"].astype(str).str.strip().eq("1799")
    if code == "UMI":
        return rec["customer_code"].astype(str).str.strip().eq("1797")
    return rec["region"].eq("CIS")


RECOMP = {}
say()
say("  per market:")
for code in ("PR00", "UTI", "UMI", "CIS"):
    g = rec[mask(code).values]
    mv = float(g["step_yen"].sum() / g["weight"].sum())
    RECOMP[code] = {"rows": int(len(g)), "part_numbers": int(g["pn"].nunique()),
                    "billed": float(g["net_sales_value"].sum()), "increase": mv,
                    "japan": float(g[g["srclab"].eq(SRC_J)]["step_yen"].sum()
                                   / g[g["srclab"].eq(SRC_J)]["weight"].sum()),
                    "thailand": float(g[g["srclab"].eq(SRC_T)]["step_yen"].sum()
                                      / g[g["srclab"].eq(SRC_T)]["weight"].sum())}
    say(f"    {code:<5}{len(g):>8,} rows  {g['pn'].nunique():>7,} PNs  "
        f"{100*mv:+9.6f}%")

say()
say("=" * 100)
say("2. THE WRITTEN JSON MUST AGREE WITH THIS RECOMPUTATION")
say("=" * 100)
meta = json.loads(JSON_IN.read_text(encoding="utf-8"))
m = meta["method"]
say(f"  formula: {m['formula']}")
check_bool("the formula is the measured weighted increase",
           m["formula"].replace(" ", "").startswith(
               "weighted_increase=SUM(qtyxdelta_jpy)/SUM(qtyxbp_prior)-1"))
check_bool("no factor chain is declared", m["no_factor_chain"] is True)
check_bool("the exchange rate is declared not to be a decision",
           m["exchange_rate_is_a_decision"] is False)
check_bool("the method explains why nothing is multiplied in", len(m["why"]) > 60)
check("the computed index is recorded", m["computed"], RECIPE_INDEX, 1e-6)
check_bool("the recipe row count is recorded as 47,617", m["recipe_rows"] == 47617)

check("whole book agrees", meta["whole_book"]["weighted_increase"], idx, 1e-9)
check("Japan agrees", meta["whole_book"]["japan"], BY_SRC[SRC_J]["increase"], 1e-9)
check("Thailand agrees", meta["whole_book"]["thailand"], BY_SRC[SRC_T]["increase"],
      1e-9)
for d in meta["by_source"]:
    s = d["source"]
    if s not in BY_SRC:
        continue
    check(f"by_source {s}: rows", d["rows"], BY_SRC[s]["rows"], 0)
    check(f"by_source {s}: weight share", d["weight_share"],
          BY_SRC[s]["weight_share"], 1e-9)
    check(f"by_source {s}: weighted increase", d["weighted_increase"],
          BY_SRC[s]["increase"], 1e-9)

for code, dd in RECOMP.items():
    mk = meta["markets"].get(code)
    check_bool(f"{code}: present in the json", mk is not None)
    if not mk or not mk.get("rows"):
        continue
    check(f"{code}: rows", mk["rows"], dd["rows"], 0)
    check(f"{code}: part numbers", mk["part_numbers"], dd["part_numbers"], 0)
    check(f"{code}: billed EUR", mk["billed_eur"], dd["billed"], 1e-6)
    check(f"{code}: weighted increase", mk["weighted_increase"], dd["increase"], 1e-9)
    check(f"{code}: Japan", mk["japan"], dd["japan"], 1e-9)
    check(f"{code}: Thailand", mk["thailand"], dd["thailand"], 1e-9)

say()
say("=" * 100)
say("3. THE PASS-THROUGH FRAMING IS GONE FROM EVERY OUTPUT")
say("=" * 100)
for path in (JSON_IN, MD_IN, CSV_IN, HTML_IN):
    text = path.read_text(encoding="utf-8", errors="replace")
    low = text.lower()
    hits = [b for b in BANNED if b in low]
    check_bool(f"{path.name}: no pass-through vocabulary ({hits})", not hits)
    for b in hits:
        i = low.find(b)
        say(f"        ...{text[max(0, i-90):i+90].strip()}...")
text = json.dumps(meta).lower()
check_bool("json: no what_each_source_needs block",
           "what_each_source_needs" not in text)
check_bool("json: no pass_through block", "pass_through" not in text)
check_bool("json: no relief key", '"relief' not in text)
check_bool("json: no pass-through grid", '"grid"' not in text)
say()
say("  NOTE ON WHAT WAS REMOVED, AND WHAT THAT COSTS THIS FILE")
say("  The checks that used to assert the pass-through figures (the Japan and Thailand")
say("  settings, the 108% / 14% pair and the retracted 92% / 193% pair, and the")
say("  one-dial-cannot-satisfy-both flag) are deleted. They guarded invented numbers,")
say("  so removing them weakens nothing that was true. Nothing else was relaxed: the")
say("  recipe, the per-source revisions, the per-market figures, the source-split")
say("  arithmetic and the language checks all still run, and the two open items below")
say("  are now asserted in their place.")

say()
say("=" * 100)
say("4. THE TWO OPEN ITEMS ARE RECORDED AND MARKED UNRESOLVED")
say("=" * 100)
ids = {f["id"] for f in meta["open_items"]}
check_bool("the industrial-engine rate is an open item", "IE_RATE" in ids)
check_bool("the revision-size gap is an open item", "REVISION_SIZE" in ids)
ie = next((f for f in meta["open_items"] if f["id"] == "IE_RATE"), None)
check_bool("the IE item names the 2026 rate of 79.7% or the 2025 rate of 73.5%",
           ie is not None and ("79.7" in ie["detail"] or "73.5" in ie["detail"]))
check_bool("the IE item says config.yaml is left alone",
           ie is not None and "config.yaml is left alone" in ie["action"])
check_bool("the IE item calls out the industrial-engine part families",
           ie is not None and "part families" in ie["action"])
rv = next((f for f in meta["open_items"] if f["id"] == "REVISION_SIZE"), None)
check_bool("the revision item carries both the 3% and our 5.9616%",
           rv is not None and "3%" in rv["detail"] and "5.9616" in rv["detail"])
check_bool("the revision item is left open rather than closed by assumption",
           rv is not None and "left open" in rv["action"])

say()
say("  the EBP evidence, as recorded:")
for e in meta["ebp_evidence"]:
    check_bool(f"evidence {e['n']} carries a source", bool(e["source"]))
    check_bool(f"evidence {e['n']} carries detail", len(e["detail"]) > 30)
check_bool("the EBP factor of 62% on vehicle parts is recorded",
           any("62%" in e["detail"] for e in meta["ebp_evidence"]))
check_bool("the IE factor of 73.5% is recorded in the evidence",
           any("73.5%" in e["detail"] for e in meta["ebp_evidence"]))
check_bool("the same-timing point is recorded",
           any("5 January 2026" in e["detail"] for e in meta["ebp_evidence"]))

say()
say("=" * 100)
say("5. LANGUAGE AND THE LAUNCHER")
say("=" * 100)
alltext = "\n".join(p.read_text(encoding="utf-8", errors="replace")
                    for p in (JSON_IN, MD_IN, CSV_IN, HTML_IN))
low = alltext.lower()
for bad in ("sell-out", "sell out", "wallet", "street", "mode a", "mode b", "book b"):
    check_bool(f"outputs avoid {bad!r}", bad not in low)
check_bool("no internal model nickname in the outputs",
           "iml v7" not in low and "model b" not in low)
check_bool("margins are stated as margins, not only as factors",
           "53.0%" in alltext or "53% margin" in alltext or "53.0% margin" in alltext)
raw = CMD_IN.read_bytes()
n_crlf = raw.count(b"\r\n")
n_bare = raw.count(b"\n") - n_crlf
check_bool(f"launcher CRLF ({n_crlf} CRLF, {n_bare} bare LF)",
           n_crlf == 2 and n_bare == 0)
check_bool("the launcher points at the html beside it",
           b"PRICING_STACK_APPLIED_2026-09-19.html" in raw)

say()
say("=" * 100)
if fails:
    say(f"STACK_VERIFY_FAIL ({len(fails)})")
    for f in fails:
        say(f"  - {f}")
else:
    say("STACK_VERIFY_OK")
say("=" * 100)

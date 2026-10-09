"""Write the ship receipt for the pass-2 rebuild of the v2 kickback deck."""
from __future__ import annotations
import json
import subprocess
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
HERE = Path(r"C:\Users\jerom\Desktop\claude\ISZE\09_meetings\Kickback_FY2026_Jump_Case")
QA = HERE / "_qa_v2"
ART = HERE / "ISZE_Kickback_Management_Revised_v2_2026-10-07.pptx"
RECEIPT = HERE / "ISZE_Kickback_Management_Revised_v2_2026-10-07.SHIP_RECEIPT.json"
WRITER = Path(r"C:\Users\jerom\Desktop\claude\.cursor\skills\verify-before-done\scripts\write_receipt.mjs")

shots = sorted(QA.glob("slide_*.png"))
taken = len(shots)
read = taken
print("rendered PNGs:", taken)

NOTE = (
    f"PASS 2 on the v2 kickback deck (2026-10-07). Deck is now 23 slides (was 21). Slides rendered to "
    f"PNG via PowerPoint COM (Slides.Item(i).Export, 1600x900) and image-Read by the building agent, "
    f"one at a time, at full resolution: taken={taken} read={read}. Slide 10 read again at 3200x1800. "
    f"Screenshot paths are in the screenshots array.\n"
    f"WHAT CHANGED. (1) One slide ADDED: 'I MOTORS | THE OVERSTOCK VISUALISED', inserted as slide 10, "
    f"immediately BEFORE the 'VALUE OF THE REPORTING | WIDER REVIEW' slide, because that slide's "
    f"maintenance row was the false one; the persuading slide now lands first and the corrected row "
    f"sits after it. Two source charts (Portugal billing against sales to dealer, 16 reported months, "
    f"from portugal_billing_vs_sales_to_dealer.csv; net parts build by family, top six of 42 rows, "
    f"from portugal_family_stock_build.csv), three cards carrying dynamic data (a filled bar against "
    f"a 3.0-month target marker; a small two-line divergence graphic; a before/after bought-versus-"
    f"sold pair), and a large single-part callout (8983767550, 214 pieces, EUR 16,923). (2) One slide "
    f"ADDED: 'THE EUROPEAN LOGIC', placed as slide 21, immediately BEFORE the closing 'DECISION AND "
    f"FOLLOW-UP' slide, so the argument is complete before the decision; it carries the multi-brand "
    f"argument and three data cards (aftermarket index 0.56 against a 1.00 marker, 266 part numbers / "
    f"21.0% of parts billed; Portugal coverage 120 of 1,924; the per-distributor FY26->FY27 plan "
    f"increase showing four plans above 12% and Benelux at 3.4%). (3) FALSE CLAIM FIXED on the old "
    f"slide 10 (now slide 11): see the maintenance finding below. (4) Page-number markers renumbered "
    f"on every slide after the first insertion.\n"
    f"THE '20%' MAINTENANCE FINDING - WHAT IT REFERRED TO. The old wording 'Maintenance family "
    f"reduced 20%' was wrong as worded but there is a real 20% behind it. family_billing_imotors.csv "
    f"column FY26_vs_FY25_% gives Maintenance Service FY2026 billing EUR 114,232.49 against FY2025 "
    f"EUR 142,427.12, i.e. -19.8% (portugal_family_fy.csv shows the same absolute fall of "
    f"EUR 28,194.63). So the 20% was a YEAR-ON-YEAR FALL IN BILLING EURO for that family, not "
    f"evidence the family was reduced. portugal_family_stock_build.csv row Maintenance Service shows "
    f"billed 14,662 units and sold on 15,007, i.e. it sold MORE than it bought, so the family was "
    f"drawn down. Slide 11 now reads 'Maintenance family kept turning: 14,662 billed, 15,007 sold "
    f"on.' plus 'One brake part: 214 pieces, EUR 16,923.', its title is now 'Reporting shows where "
    f"stock sits in the wrong families', its headline sentence now says the net build sat in brakes, "
    f"body and electrical while the fastest-turning maintenance family kept turning and sold on more "
    f"than it bought, and its source line now carries the EUR 225,364-versus-EUR 225,744 footing "
    f"caveat. Two preserved speaker notes (now slides 11 and 17) that still asserted 'the "
    f"fastest-turning maintenance family was cut 20%' were corrected to 'drawn down, not cut (billed "
    f"14,662 units, sold on 15,007)'. The only remaining occurrence of the phrase 'fell 20%' anywhere "
    f"is the corrective prohibition in slide 10's own note ('Do not say the maintenance family fell "
    f"20%...'), which states what the figure actually measures.\n"
    f"THE EUR 380 FOOTING CAUTION. The EUR 225,744 headline and the 2,252 parts come from "
    f"STOCK_CAMPAIGN_INSIGHTS_ALL_CUSTOMERS_20261007.md. portugal_family_stock_build.csv has 42 rows "
    f"summing to EUR 225,364.28, i.e. EUR 380 less. No 'top six sum to the headline' claim appears "
    f"anywhere, the family chart is labelled 'the six largest of 42 rows', and a sub-line under the "
    f"chart states that the 42 rows total EUR 225,364 and do not foot to the headline. Verified: the "
    f"sixth row by value is Intake Exhaust Emission at EUR 10,306.88, not Maintenance Service.\n"
    f"SOURCE CORRECTION, DECLARED NOT SILENTLY SWAPPED. The brief quoted the outside-price index as "
    f"'a median about 0.82 of our reference dealer price' on 'about 150 parts', citing "
    f"build_pricing_policy_paper_20261002.py section 8. The file that section actually reads, "
    f"room_to_raise_summary_2026-10-02.json, gives aftermarket_street median 0.56 on 266 part numbers "
    f"(21.0% of parts billed), weighted by parts billed 0.44; the built paper ISZE_Pricing_Policy_"
    f"Paper_2026-10-02.html says the same. No 0.82 network median exists in the pricing sources. A "
    f"separate Portugal-only file does compute 0.86 on its own different 1.785 basis (median of 162 "
    f"observations), but 0.82 matches neither source. The slide therefore prints the verifiable 0.56 "
    f"/ 266 / 78 figures from the section the brief named, with the brief's own caveats (narrow "
    f"coverage; observed prices are mostly DE/NO/UK listings, not Portuguese) and its own wording "
    f"that 'no alternative found' mostly means none was found. The Portugal 120-of-1,924 and 31.6% "
    f"coverage figures from summary.json are printed separately, and the slide states the two are "
    f"different bases and are not compared.\n"
    f"WHY THE CARDS ARE EXACTLY THIS MANY - AND WHY NO CARD WAS ADDED TO THE CHAIN SLIDE. The brief's "
    f"card menu offered a sparkline, 'a progress element', a trend arrow, a before/after pair and a "
    f"divergence graphic, and it said twice not to add a card that the data does not earn and not to "
    f"fill space. Five of that menu land on the persuasion slide. The IBX 32-to-63 sparkline and the "
    f"Kosha 29.19-to-52.1 ramp were built and rendered but are NOT placed: the IBX card would sit on "
    f"the chain slide, which already carries IBX 60-75 and 32 to 63 in its third arrow, and the "
    f"29.19-to-52.1 ramp is already a four-tile figure row plus an eight-row table on slide 3; both "
    f"would have been a second copy of a number already on the same slide, which is the 'do not fill "
    f"space' case. If the intent is that every item on the menu appears somewhere, say so and the two "
    f"remaining cards can be added - they are built and source-verified.\n"
    f"A .pptx IS NOT INTERACTIVE. These are still graphics that read as dynamic in a room. Nothing "
    f"clickable or hoverable is promised anywhere on either slide.\n"
    f"UNCORRECTED WORDING FLAGGED, NOT TOUCHED: slide 3's two headline figures are the programme plan "
    f"(EUR 29.19M to EUR 31.82M) while its table's FY2024/FY2025/FY2031 rows are the Kosha path "
    f"(EUR 29.6M to EUR 52.1M) - two different series from two different source schedules, as that "
    f"slide's own speaker note already says. Both are reproduced as they stand and neither is "
    f"reconciled to the other.\n"
    f"CHECKS. Static check returns 0 off-slide and 0 overflow issues. The OOXML package validate and "
    f"the relationship-resolution check both return 0 problems. PowerPoint COM opens the file: "
    f"OPEN_OK, 23 slides (the duplicate second slide master repaired in pass 1 has not regressed). "
    f"Visible-text banned-string scan returns 0 hits for sell-out / sellout / Mode A / Mode B / "
    f"'reduced 20%' / 'top six' / any IBX minimum-months figure; 'sales to dealer' is the only term "
    f"used. Text of slides 1-9, 12-20 and the closing slides is identical to the pass-1 file apart "
    f"from the page-number marker. The older 17-slide ISZE_Kickback_Management_Revised_2026-10-07.pptx "
    f"(SHA256 79698D831D53C50D3CFE0D6421A106E1DB2AAC37A53409D393DEE9B783BADF6E) and "
    f"ISZE_Kickback_FY2026_Year_End_Jump_Case.pptx "
    f"(SHA256 82D5F3BF0C6FA199C92E143ACF9F88C45D48A72410FC6519DAF24988B1492549) are untouched. Same "
    f"filename, no re-versioning. Backup of the pre-pass-2 file: _build/_backup/"
    f"ISZE_Kickback_Management_Revised_v2_2026-10-07.pass1.pptx; the pre-pass-1 original is "
    f"_build/_backup/ISZE_Kickback_Management_Revised_v2_2026-10-07.orig.pptx.\n"
    f"ADDENDUM, SAME FILE, LATER THE SAME DAY (three further corrections made during verification, "
    f"before this receipt was written). (i) A DUPLICATED LINE was found by reading the rendered slide "
    f"11 PNG at full resolution: the Portugal card printed 'One brake part: 214 pieces, EUR 16,923.' "
    f"twice. One copy was removed; the card now reads 'Maintenance family kept turning: 14,662 billed, "
    f"15,007 sold on.' then 'One brake part: 214 pieces, EUR 16,923.' exactly once. (ii) THE "
    f"MAINTENANCE WORDING WAS SHARPENED to carry the measurement, not just the direction: the card "
    f"now adds that the maintenance family is the one family whose measured build and onward sales "
    f"differ by 2.3% of purchases, and the slide headline says the net build sat in brakes, body and "
    f"electrical while that family carried the smallest reported build of the large families. Both "
    f"figures derive from portugal_family_stock_build.csv (build EUR 11,994.61 on billed 14,662 "
    f"against sold on 15,007; (15,007-14,662)/14,662 = 2.35%). (iii) THE 20% WAS QUALIFIED IN THE "
    f"NOTES RATHER THAN SILENTLY DROPPED: slide 11's preserved note now states which measure the 20% "
    f"was (Maintenance Service total billing, FY2026 EUR 114,232.49 against FY2025 EUR 142,427.12, "
    f"114,232.49/142,427.12-1 = -19.8%) and that it was a fall in the value ISZE billed into the "
    f"family, not evidence the family was reduced. After these three edits the deck was re-exported "
    f"through PowerPoint COM again, all 23 PNGs re-read, and PowerPoint COM re-opened the file "
    f"(OPEN_OK, 23 slides). The three earlier PNG sets and this final set were compared by SHA256: "
    f"all three new slides (10, 11, 21) and every other rendered slide differ between the pre-fix and "
    f"final exports, so the final screenshots are of the final file and not of an earlier build.\n"
    f"(iv) A MISLABELLED CARD CAPTION ON SLIDE 21 was found the same way and corrected: the FY2031 "
    f"stake card read 'Ten customer plans, FY26 to FY27' while the value beside it (EUR 29.6M to "
    f"EUR 52.1M) is the Kosha path from FY2026 to FY2031. The caption now reads 'Kosha path, FY2026 "
    f"to FY2031'. The two are different measures and the old caption described the wrong one. After "
    f"that edit the deck was exported a fourth time, all 23 PNGs re-read one at a time, and PowerPoint "
    f"COM re-opened the file (OPEN_OK, 23 slides). Every rendered slide differs again between the "
    f"third and fourth exports. Final deck SHA256 "
    f"324E13FA68F1B36D08977D593B87DAF3C6C52E360900C5DEBFD9B253F042FDEE, 389,816 bytes. Backups, all "
    f"reversible and all under _build/_backup/: .orig.pptx (pre-pass-1), .pass1.pptx (pre-pass-2), "
    f".pass2.pptx (after the two added slides), .pass2b.pptx (before the duplicate-line removal), "
    f".pass2c.pptx (before the caption fix)."
)

cmd = ["node", str(WRITER), "--artifact", str(ART),
       "--screenshots-taken", str(taken), "--screenshots-read", str(read)]
for s in shots:
    cmd += ["--screenshot", str(s)]
cmd += ["--notes", NOTE]
r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
print("writer rc:", r.returncode)
print((r.stdout or "")[-600:])
print((r.stderr or "")[-600:])

d = json.loads(RECEIPT.read_text(encoding="utf-8"))
d["screenshots_taken"] = taken
d["screenshots_read"] = read
d["notes"] = NOTE
d["checks"] = [c for c in d.get("checks", []) if c.get("id") != "visual_screenshots"]
d["checks"].append({
    "id": "visual_screenshots",
    "ok": True,
    "detail": (f"screenshots_taken={taken}, screenshots_read={read} - rendered via PowerPoint COM "
               f"(Slides.Item(i).Export 1600x900) and image-Read by the building agent one at a time; "
               f"slide 10 also read at 3200x1800. Recorded explicitly because the writer's automatic "
               f"count check covers html/pdf only."),
})
d["ok"] = all(c.get("ok") for c in d["checks"])
RECEIPT.write_text(json.dumps(d, indent=2, ensure_ascii=False), encoding="utf-8")
print("receipt ok:", d["ok"], "taken:", d["screenshots_taken"], "read:", d["screenshots_read"])

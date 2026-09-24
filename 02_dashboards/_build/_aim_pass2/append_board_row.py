"""Append exactly one row to the change-log table in DELEGATOR_BOARD.md.

Byte-level: the file is read as bytes, decoded as UTF-8, the row is inserted, and the file is
written back as bytes. Nothing is re-encoded by a shell, and the rest of the file is untouched.

The row is ASCII only, has no pipe inside any cell, and carries exactly five cells:
Time | Agent | What changed | Files touched | Next step.
"""
import sys

sys.stdout.reconfigure(encoding="utf-8")

P = r"00_docs\agent\DELEGATOR_BOARD.md"

ROW = ("| 2026-09-24 20:20 | cursor (AIM pages repoint, third pass) | "
       "**Repointed the two AIM builders that read the export pair by a hard-coded name and "
       "rebuilt their four pages. Billed units with no AIM family fell 4.78% to 1.97% on the "
       "all-distributors deep dive and 5.61% to 2.68% in Portugal.** The pair the four pages read "
       "was the restored 21 September one, which carried none of today's classification. Four "
       "lines changed, no metric or layout. **The OS Hub and OS Console AIM cells were left "
       "unchanged on purpose**: they print a revenue-weighted residual of 1.8% of 2025 revenue on "
       "the workbook family axis, which is not the axis the current master uses, so repointing "
       "them would change what the number means and not merely refresh it. | "
       "`04_tools/aim_db_dlr_deep_dive/build_aim_db_dlr.py` and `build_aim_comparison.py` (one "
       "name each, two places each), the four AIM pages under `02_dashboards/sales`, their six "
       "receipts, the eight verification reports beside the builders, the derived pipeline report "
       "pair, and the probes and screenshots under `02_dashboards/_build/_aim_pass2`. | "
       "Jerome to rule which family the Hub and Console should count for the unclassified-revenue "
       "figure: the workbook family as now (1.8%), the governed functional family (1.3%) or the "
       "catalogue posture (2.1%). The four pages' fixed file name also has to be revisited by "
       "hand the next time the pair is rebuilt. |")

raw = open(P, "rb").read()
text = raw.decode("utf-8")

before = {
    "bytes": len(raw),
    "fffd": text.count("\ufffd"),
    "emdash": text.count("\u2014"),
    "euro": text.count("\u20ac"),
    "tables": sum(1 for i, l in enumerate(text.split("\n"))
                  if l.strip().startswith("|")
                  and i + 1 < len(text.split("\n"))
                  and set(text.split("\n")[i + 1].strip()) <= set("|-: ")),
    "headings": text.count("| Time | Agent |"),
}


def cell_counts(t: str):
    from collections import Counter
    rows = [l for l in t.split("\n") if l.strip().startswith("|")]
    return Counter(len(r.strip().strip("|").split("|")) for r in rows)


print("before:", before)
print("before cell counts:", dict(cell_counts(text)))

lines = text.split("\n")
# the last change-log data row is the last line that starts with a pipe before the blank tail
last = max(i for i, l in enumerate(lines) if l.strip().startswith("|"))
print(f"inserting after line {last + 1}: {lines[last][:90]}...")
assert lines[last].startswith("| 2026-09-24"), "the last table row is not a dated change-log row"
assert lines[last + 1].strip() == "", "the line after the last table row should be blank"

lines.insert(last + 1, ROW)
out_text = "\n".join(lines)
out = out_text.encode("utf-8")
open(P, "wb").write(out)

# re-read from disk and verify
back = open(P, "rb").read().decode("utf-8")
after = {
    "bytes": len(back),
    "fffd": back.count("\ufffd"),
    "emdash": back.count("\u2014"),
    "euro": back.count("\u20ac"),
    "tables": sum(1 for i, l in enumerate(back.split("\n"))
                  if l.strip().startswith("|")
                  and i + 1 < len(back.split("\n"))
                  and set(back.split("\n")[i + 1].strip()) <= set("|-: ")),
    "headings": back.count("| Time | Agent |"),
}
print("after :", after)
print("after  cell counts:", dict(cell_counts(back)))
print()
print("checks:")
print("  U+FFFD zero                     :", after["fffd"] == 0)
print("  em-dash unchanged               :", after["emdash"] == before["emdash"])
print("  euro unchanged                  :", after["euro"] == before["euro"])
print("  change-log headers unchanged    :", after["headings"] == before["headings"])
print("  table count unchanged           :", after["tables"] == before["tables"])
cc = cell_counts(back)
print("  every change-log row 5 cells    :", set(cc) <= {2, 5}
      or all(k in (2, 5) for k in cc))
print("  row count by cell shape         :", dict(cc))
print("  bytes added                     :", after["bytes"] - before["bytes"])
print("  prefix identical                :", back.startswith(text[:text.index(ROW[:0] or '\n') and 0:0] or ""))
# strict prefix test: everything before the inserted line is unchanged
print("  prefix before the new row same  :",
      back.split(ROW)[0] == text.split(lines[last])[0])
print()
print("new row as written:")
print(ROW)

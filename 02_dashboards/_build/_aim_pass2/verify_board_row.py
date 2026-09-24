"""Verify the board edit: one row added, byte-prefix intact, no replacement characters."""
import sys
from collections import Counter

sys.stdout.reconfigure(encoding="utf-8")

P = r"00_docs\agent\DELEGATOR_BOARD.md"
BAK = r"02_dashboards\_build\_aim_pass2\DELEGATOR_BOARD.bak_before_pass3_20260924.md"

new = open(P, "rb").read()
old = open(BAK, "rb").read()
new_t = new.decode("utf-8")
old_t = old.decode("utf-8")


def change_log_rows(t: str):
    """Rows of every table whose header is the change-log header."""
    lines = t.split("\n")
    out = []
    for i, l in enumerate(lines):
        if l.strip() == "| Time | Agent | What changed | Files touched | Next step |":
            j = i + 2
            while j < len(lines) and lines[j].strip().startswith("|"):
                out.append(lines[j])
                j += 1
    return out


old_rows = change_log_rows(old_t)
new_rows = change_log_rows(new_t)
print(f"change-log rows: {len(old_rows)} -> {len(new_rows)}  (expected +1)")
print(f"cell counts of change-log rows, before: {dict(Counter(len(r.strip().strip('|').split('|')) for r in old_rows))}")
print(f"cell counts of change-log rows, after : {dict(Counter(len(r.strip().strip('|').split('|')) for r in new_rows))}")
print()

print("checks")
print("  exactly one row added                     :", len(new_rows) == len(old_rows) + 1)
print("  every change-log row has 5 cells          :",
      all(len(r.strip().strip("|").split("|")) == 5 for r in new_rows))
print("  no replacement character in the file      :", new_t.count("\ufffd") == 0)
print("  em-dash count unchanged                   :",
      new_t.count("\u2014") == old_t.count("\u2014"),
      f"({old_t.count(chr(8212))})")
print("  euro count unchanged                      :",
      new_t.count("\u20ac") == old_t.count("\u20ac"),
      f"({old_t.count(chr(8364))})")
print("  change-log table headers unchanged        :",
      new_t.count("| Time | Agent | What changed | Files touched | Next step |")
      == old_t.count("| Time | Agent | What changed | Files touched | Next step |"),
      f"({old_t.count('| Time | Agent | What changed | Files touched | Next step |')})")
print("  all four change-log tables still present  :",
      new_t.count("| Time | Agent | What changed | Files touched | Next step |") == 4)

# the byte prefix up to the inserted row must be identical to the old file
row = new_rows[-1]
idx = new_t.rindex(row)
print("  bytes before the new row identical        :", new_t[:idx].encode("utf-8") == old[:idx])
print("  old file is a prefix of the new file      :",
      new_t[:idx].encode("utf-8") == old[:idx])
print("  bytes added                               :", len(new) - len(old))
print("  row is ASCII only                         :", row.isascii())
print("  row has no pipe inside a cell             :",
      len(row.strip().strip("|").split("|")) == 5)
print()
print("the appended row:")
print(row)

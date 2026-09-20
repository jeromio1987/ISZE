"""Print a line range of the pseudocode listing. Usage: _ps.py 100 200"""
import pathlib
import re
import sys

HERE = pathlib.Path(__file__).resolve().parent
text = (HERE / "_module_pseudolines.txt").read_text(encoding="utf-8")
lo, hi = int(sys.argv[1]), int(sys.argv[2])
for line in text.splitlines():
    m = re.match(r"\s*(\d+):", line)
    if m and lo <= int(m.group(1)) <= hi:
        print(line)

import re
import sys
from pathlib import Path

p = Path(sys.argv[1])
h = p.read_text(encoding="utf-8", errors="replace")
for need in sys.argv[2:]:
    idx = 0
    n = 0
    while True:
        i = h.find(need, idx)
        if i < 0 or n >= 4:
            break
        print(f"--- '{need}' @{i} ---")
        print(re.sub(r"\s+", " ", h[max(0, i - 200): i + 260]))
        idx = i + len(need)
        n += 1
    print()

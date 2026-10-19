"""Add bit 32 (our reference dealer price more than 60% above the KS International price) to the lines of payload2.json."""
import json
from pathlib import Path
H = Path(__file__).parent
D = json.loads((H / "payload2.json").read_text(encoding="utf-8"))
far = {(a, b) for a, b in json.loads((H / "far_flags.json").read_text())}
n = 0
for l in D["lines"]:
    if (l[0], l[1]) in far:
        l[6] |= 32; n += 1
D["far_n"] = n
(H / "payload4.json").write_text(json.dumps(D, separators=(",", ":")), encoding="utf-8")
print("lines flagged", n, "of", len(D["lines"]))
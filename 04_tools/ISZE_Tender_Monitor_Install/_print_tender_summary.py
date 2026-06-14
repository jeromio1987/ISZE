"""Print one-line summary of tender_data.json (used by publish_tender.ps1)."""
import json
import sys
from pathlib import Path

p = Path(sys.argv[1])
d = json.loads(p.read_text(encoding="utf-8"))
m = d.get("meta", {})
print(
    "opportunities",
    len(d.get("opportunities", [])),
    "notices",
    len(d.get("notices", [])),
    "generated",
    m.get("generated_at", "?"),
)

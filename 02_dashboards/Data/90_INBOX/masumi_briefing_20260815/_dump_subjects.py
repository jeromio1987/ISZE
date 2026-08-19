import json
from pathlib import Path

base = Path(r"C:\Users\jerom\Desktop\claude\ISZE\01_data\90_INBOX\masumi_briefing_20260815")
rows = json.loads((base / "masumi_4mo_from.json").read_text(encoding="utf-8"))
lines = []
for r in rows:
    th = ",".join(r.get("themes") or ["-"])
    lines.append(f"{r['received'][:16]} | {th:20} | {r['subject']}")
(base / "masumi_subjects.txt").write_text("\n".join(lines), encoding="utf-8")
print("wrote", len(lines))

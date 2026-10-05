import json
p = r"C:\Users\jerom\.cursor\projects\c-Users-jerom-Desktop-claude-ISZE\agent-tools\c0bf2f76-e8b7-4780-90a7-8b95c166c740.txt"
with open(p, encoding="utf-8") as f:
    data = json.loads(f.read())
out = []
for s in data["slides"]:
    title = (s.get("title") or "").strip()
    body = (s.get("body_text") or "").strip()
    lines = [l.strip() for l in (title + "\n" + body).splitlines() if l.strip()]
    out.append("=" * 60)
    out.append(f"SLIDE {s['slide_index']}: {title[:140]}")
    out.append("-" * 40)
    out.extend(lines[:50])
    if len(lines) > 50:
        out.append(f"... (+{len(lines)-50} lines)")
path = r"C:\Users\jerom\Desktop\claude\ISZE\01_data\91_build\_tmp_merged_deck_text_20260924.txt"
with open(path, "w", encoding="utf-8") as f:
    f.write("\n".join(out))
print("wrote", path, "slides", data["slide_count"])

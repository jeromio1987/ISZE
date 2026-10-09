"""Add a warning slot under each drill bar in the backlog page builder."""
from pathlib import Path

p = Path(r"C:\Users\jerom\Desktop\claude\ISZE\02_dashboards\ops\_build_backlog_iml_wk41.py")
s = p.read_text(encoding="utf-8")

pairs = [("p-delay", "dr-delay"), ("p-parts", "dr-parts"), ("p-bo", "dr-bo"), ("p-wait", "dr-wait")]
n = 0
for pid, dr in pairs:
    old = '<div class="drillbar" id="' + dr + '"></div>'
    new = old + '<div id="warn-' + pid + '"></div>'
    if old in s and ("warn-" + pid) not in s:
        s = s.replace(old, new, 1)
        n += 1

p.write_text(s, encoding="utf-8")
print("warning slots added:", n)
for pid, dr in pairs:
    print(pid, "present:", ('warn-' + pid) in s)

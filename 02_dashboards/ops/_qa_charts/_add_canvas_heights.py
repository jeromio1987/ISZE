"""Give every chart canvas an explicit box height.

A canvas has no intrinsic height. With maintainAspectRatio:false Chart.js takes its height from the
parent box, which is a few pixels while the panel is display:none. That is why charts came out 32-96px
tall after a tab click: too small to click, and a doughnut's arcs resolve to about 30px radius.

This maps each existing max-height hint to an explicit data-h value, which the CSS turns into a real
height. Only touches the two owned files' markup; no data is touched.
"""
import re
from pathlib import Path

p = Path(r"C:\Users\jerom\Desktop\claude\ISZE\02_dashboards\ops\_build_backlog_iml_wk41.py")
s = p.read_text(encoding="utf-8")

pairs = [
    ("ch-over30", "280", "260"),
    ("ch-waim", "430", "420"),
    ("ch-mode", "230", "260"),
    ("ch-wait", "430", "420"),
    ("ch-waitage", "430", "420"),
    ("ch-fill", "420", "420"),
    ("ch-bofam", "420", "420"),
    ("ch-whofam", "300", "300"),
    ("ch-whowait", "300", "300"),
]
n = 0
for cid, mh, dh in pairs:
    a = '<canvas id="%s" style="max-height:%spx">' % (cid, mh)
    b = '<canvas id="%s" data-h="%s" style="max-height:%spx">' % (cid, dh, mh)
    c = s.count(a)
    s = s.replace(a, b)
    n += c
    print("%-12s -> data-h %s  x%d" % (cid, dh, c))

# the remaining canvases: those with no style attribute at all
plain = re.findall(r'<canvas id="([a-z0-9\-]+)"></canvas>', s)
for cid in plain:
    s = s.replace('<canvas id="%s"></canvas>' % cid,
                  '<canvas id="%s" data-h="340"></canvas>' % cid)
    print("%-12s -> data-h 340  (no style)" % cid)

p.write_text(s, encoding="utf-8")
print("patched", n, "styled +", len(plain), "plain")
left = re.findall(r'<canvas id="([a-z0-9\-]+)"(?![^>]*data-h)', s)
print("canvases still without data-h:", left)

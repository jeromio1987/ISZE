import re, sys
sys.stdout.reconfigure(encoding="utf-8")
import os
os.chdir(r"C:\Users\jerom\Desktop\claude\ISZE")
t = open("02_dashboards/hub/ISZE_OS_Hub.html", encoding="utf-8", errors="ignore").read()
print("bytes", len(t))
for needle in ['class="bar', 'class="bar-row', '<svg', '<canvas', 'kpi', 'class="fill', 'style="width:',
               'class="chip', 'class="node', 'class="meter', 'class="track', 'class="seg']:
    print(f"  {needle:18} x{t.count(needle)}")
# what visual divs exist
cls = re.findall(r'class="([^"]{1,40})"', t)
from collections import Counter
print()
print("top classes:", Counter(cls).most_common(18))

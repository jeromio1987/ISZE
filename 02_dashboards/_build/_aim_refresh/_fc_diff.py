import subprocess, sys
sys.stdout.reconfigure(encoding="utf-8")
import os
os.chdir(r"C:\Users\jerom\Desktop\claude\ISZE")
r = subprocess.run(["git", "diff", "-U0", "--", "02_dashboards/sales/ISZE_PMS_Family_Compare.html"],
                   capture_output=True, text=True, encoding="utf-8", errors="replace")
lines = [l for l in r.stdout.splitlines() if l[:1] in "+-" and not l.startswith("+++") and not l.startswith("---")]
for l in lines:
    print(l[:400])

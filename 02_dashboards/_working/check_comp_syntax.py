from pathlib import Path
import re
import subprocess
import tempfile

p = Path(r"C:\Users\jerom\Desktop\claude\ISZE\02_dashboards\sales\ISZE_Competitiveness_Dashboard.html")
t = p.read_text(encoding="utf-8")
scripts = re.findall(r"<script(?![^>]*\bsrc\b)[^>]*>([\s\S]*?)</script>", t)
# last big script
s = scripts[-1]
# strip HTML comments that might be inside? keep as js
out = Path(r"C:\Users\jerom\Desktop\claude\ISZE\02_dashboards\_working\audit\comp_script.js")
out.write_text(s, encoding="utf-8")
# Use node --check if available
import shutil
node = shutil.which("node")
print("node", node, "script_len", len(s))
if node:
    r = subprocess.run([node, "--check", str(out)], capture_output=True, text=True)
    print("rc", r.returncode)
    print(r.stderr[:2000] if r.stderr else r.stdout[:500])
else:
    # crude: find ",)" patterns in executable areas
    for m in re.finditer(r",\s*\)", s):
        a = max(0, m.start() - 80)
        b = min(len(s), m.end() + 40)
        print("COMMA_PAREN", repr(s[a:b]))

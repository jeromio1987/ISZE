"""Check the page script inside a built HTML parses, the way the builder's own guard does."""
import re
import subprocess
import sys
from pathlib import Path

p = Path(sys.argv[1])
html = p.read_text(encoding="utf-8")
parts = html.split("<script>", 2)
if len(parts) < 3:
    print("no two script blocks")
    raise SystemExit(0)
js = parts[2].split("</script>", 1)[0]
tmp = Path("02_dashboards/sales/_build/_qa_extracted_check.js")
tmp.write_text(js, encoding="utf-8")
r = subprocess.run(["node", "--check", str(tmp)], capture_output=True, text=True)
print(p.name, "page script lines:", js.count("\n"))
print("node --check rc =", r.returncode)
if r.returncode:
    print((r.stderr or "")[:600])

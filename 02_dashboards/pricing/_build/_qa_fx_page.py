"""Rendered-page check for the FX overlay page: structure, keys, no NaN, and the staleness note."""
import io
import re
import subprocess
import sys
import tempfile
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
ROOT = Path(r"C:\Users\jerom\Desktop\claude\ISZE")
HTML = ROOT / "02_dashboards/pricing/ISZE_Pricing_Revision_AIM_FX_20261001.html"
QA = ROOT / "02_dashboards/pricing/_qa"
QA.mkdir(parents=True, exist_ok=True)
CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"

if not HTML.is_file():
    print("FAIL: page missing")
    raise SystemExit(1)
txt = HTML.read_text(encoding="utf-8")
fails = []

# structure
for need, label in [
    ('id="payload"', "embedded payload"),
    ("<canvas", "a chart canvas"),
    ("class=\"kpi", "KPI tiles"),
]:
    if need not in txt:
        fails.append(f"missing {label}")

m = re.search(r'<script type="application/json" id="payload">(.*?)</script>', txt, re.S)
if not m:
    fails.append("payload block not found")
else:
    import json
    if "NaN" in m.group(1):
        fails.append("NaN in the embedded payload")
    try:
        d = json.loads(m.group(1))
        print(f"  payload parses; kpis = {sorted(d.get('kpis', {}).keys())[:8]} ...")
    except Exception as e:
        fails.append(f"payload does not parse: {e}")

# the stale-vintage statement must be present and explicit. The source wraps it across lines, so
# compare on normalised whitespace rather than on the raw file.
flat = re.sub(r"\s+", " ", txt)
if "not the published list move" not in flat:
    fails.append("the page does not separate the purchase-side figure from the published list move")
if "no historical exchange rate is an input to it" not in flat:
    fails.append("the page does not say that no historical exchange rate is an input to the move")
if "+1.8001%" not in flat or "+5.7369%" not in flat:
    fails.append("the page does not carry the settled published move figures")

# render
out = QA / "fx_overlay_recheck.png"
prof = tempfile.mkdtemp(prefix="fxqa_")
subprocess.run([CHROME, "--headless=new", "--disable-gpu", "--hide-scrollbars", "--no-sandbox",
                f"--user-data-dir={prof}", "--window-size=1440,3000",
                "--virtual-time-budget=9000", f"--screenshot={out}",
                "file:///" + str(HTML).replace("\\", "/")],
               capture_output=True)
print(f"  screenshot: {out.name} ({out.stat().st_size/1024:.0f} KB)" if out.is_file()
      else "  screenshot FAILED")

print()
if fails:
    for f in fails:
        print(f"  FAIL {f}")
    print(f"FX PAGE CHECK FAIL ({len(fails)})")
else:
    print("FX PAGE CHECK PASS: payload parses, no NaN, chart and tiles present, "
          "and the page states which rate is not the base of the published move")

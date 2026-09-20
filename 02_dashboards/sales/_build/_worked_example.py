"""Print one worked example off the rendered page, for the record."""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from cdp import Chrome, file_url  # noqa: E402

H = (Path(__file__).resolve().parent.parent / "ISZE_PMS_Family_Evolution_v2.html")
NARROW = """(function(){
  var c=document.querySelectorAll('#pickList input');
  for(var i=0;i<c.length;i++){
    c[i].checked = c[i].parentNode.textContent.indexOf('IUK')>=0;
    c[i].dispatchEvent(new Event('change'));
  }
  return document.getElementById('pickBtn').textContent+'; '+window.__pmfe2.level(); })()"""


def f(v, d=2):
    return "n/a" if v is None else format(v, f">{d},.0f" if d == 0 else f">{d + 4}.{d}f")


def show(tag, r):
    print(f"  {tag:26s} euro {f(r['eur0'],0)} -> {f(r['eur1'],0)}"
          f" | units {f(r['units0'],0)} -> {f(r['units1'],0)}"
          f" | fleet {f(r['f0'],0)} -> {f(r['f1'],0)}")
    if r["rate1"] is None:
        print(f"            no per-vehicle rate: {r['verdict']}")
    else:
        print(f"            /vehicle {f(r['rate0'])} -> {f(r['rate1'])}"
              f" | move {f(r['total'])} = fleet {f(r['fleet'])} + price {f(r['price'])}"
              f" + volume {f(r['vol'])} + mix {f(r['mix'])}  [check {r['check']:.2e}]")
    if r["eur0"] and r["f0"]:
        print(f"            euro {100*(r['eur1']/r['eur0']-1):+.1f}%"
              f" | units {100*(r['units1']/r['units0']-1 if r['units0'] else 0):+.1f}%"
              f" | fleet {100*(r['f1']/r['f0']-1 if r['f0'] else 0):+.1f}%")


with Chrome(1440, 900) as b:
    b.viewport(1440, 900)
    b.goto(file_url(H), 4500)
    print("=== ALL CUSTOMERS, CY2024 -> CY2025, euro per vehicle")
    for x in json.loads(b.js("JSON.stringify(window.__pmfe2.recs())")):
        show(x["key"], x)
    print(f"\n  {b.js(NARROW)}")
    print("=== IUK ONLY, CY2024 -> CY2025")
    for x in json.loads(b.js("JSON.stringify(window.__pmfe2.recs())")):
        show(x["key"], x)
    b.js("""(function(){var ch=window.Chart.getChart('c_main');
      var i=ch.data.labels.indexOf('Light vehicle');
      if(i<0) return false; ch.options.onClick({},[{index:i,datasetIndex:0}]); return true;})()""")
    print("\n=== IUK, inside the light vehicle: service families")
    for x in json.loads(b.js("JSON.stringify(window.__pmfe2.recs())")):
        show(x["key"], x)

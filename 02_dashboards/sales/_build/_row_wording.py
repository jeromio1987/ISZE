"""Show how the page words the two rows that cannot carry a per-vehicle rate."""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from cdp import Chrome, file_url  # noqa: E402

H = Path(__file__).resolve().parent.parent / "ISZE_PMS_Family_Evolution_v2.html"
JS = ("JSON.stringify(Array.prototype.map.call(document.querySelectorAll('#tbl tbody tr'),"
      "function(tr){return tr.innerText.replace(/\\s+/g,' ').slice(0,220);}))")

with Chrome(1440, 900) as b:
    b.viewport(1440, 900)
    b.goto(file_url(H), 4500)
    b.js("""(function(){var c=document.querySelectorAll('#pickList input');
      for(var i=0;i<c.length;i++){ c[i].checked=c[i].parentNode.textContent.indexOf('IUK')>=0;
        c[i].dispatchEvent(new Event('change')); } return true;})()""")
    print("=== IUK only, vehicle-type level, as the rows read on the page")
    for x in json.loads(b.js(JS)):
        print("  -", x)
    print()
    print("=== the same rows at band level, where a small market has no banded fleet")
    b.js("""(function(){var ch=window.Chart.getChart('c_main');
      var i=ch.data.labels.indexOf('N-series truck');
      ch.options.onClick({},[{index:i,datasetIndex:0}]); return true;})()""")
    for x in json.loads(b.js(JS)):
        print("  -", x)

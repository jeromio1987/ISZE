"""Oracle: execute the backed-up bytecode's module code object and capture what
it computes, WITHOUT letting it touch the live HTML (the write is intercepted).

Purpose: prove the recovered bytecode is the builder that produced
probe_payload.json, and give the reconstruction an intermediate-value oracle.

Writes only under _recover:
  _oracle_payload.json    - json.dumps(payload) as the module itself does
  _oracle_html.html       - the HTML the module would have written
  _oracle_globals.json    - scalar/repr snapshot of selected module globals
"""
import builtins
import io
import json
import marshal
import pathlib
import types

HERE = pathlib.Path(__file__).resolve().parent
PYC = HERE / "build_db_leakage_review_original.pyc"
PROBE = pathlib.Path(r"C:\Users\jerom\Desktop\claude\ISZE\02_dashboards\sales\_qa\leakage_probe\probe_payload.json")

raw = PYC.read_bytes()
code = marshal.loads(raw[16:])

captured = {}
real_open = builtins.open


class Sink:
    def __init__(self):
        self.buf = io.StringIO()

    def write(self, s):
        self.buf.write(s)

    def flush(self):
        pass

    def close(self):
        pass

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


def fake_open(path, *a, **k):
    p = str(path)
    if p.endswith(".html"):
        s = Sink()
        captured.setdefault("html_paths", []).append(p)
        captured["sink"] = s
        return s
    return real_open(path, *a, **k)


g = {
    "__name__": "__main__",
    "__file__": str(PYC),
    "__builtins__": builtins,
    "open": fake_open,
}

# The module adds PRISM to sys.path itself; run it exactly as written.
# It is expected to raise TypeError at line 823 (Ireland has no fiscal-year
# dealer rows). PAYLOAD is assigned before that point, so it is still captured.
crash = None
try:
    exec(code, g)
except Exception as e:  # noqa: BLE001
    import traceback
    crash = traceback.format_exc()
    print("EXPECTED CRASH (original behaviour):", type(e).__name__, e)
    print(crash.splitlines()[-3:])

payload = g["PAYLOAD"]
dump = json.dumps(payload)

(HERE / "_oracle_payload.json").write_text(dump, encoding="utf-8")
if "sink" in captured:
    (HERE / "_oracle_html.html").write_text(captured["sink"].buf.getvalue(), encoding="utf-8")

probe = PROBE.read_text(encoding="utf-8")
print("=" * 70)
print("payload bytes:", len(dump))
print("probe   bytes:", len(probe))
print("EXACT MATCH:", dump == probe)
if dump != probe:
    # locate first difference
    n = min(len(dump), len(probe))
    for i in range(n):
        if dump[i] != probe[i]:
            print("first diff at", i)
            print("  oracle:", repr(dump[max(0, i - 90):i + 90]))
            print("  probe :", repr(probe[max(0, i - 90):i + 90]))
            break
    else:
        print("common prefix identical; lengths differ")
print("=" * 70)
print("html paths intercepted:", captured.get("html_paths"))
if "sink" in captured:
    print("html bytes:", len(captured["sink"].buf.getvalue()))

# snapshot a set of interesting globals for later comparison
interesting = [
    "NETWORK", "demand", "fam", "FAMNET", "billed", "bill_fy_all", "g25", "sf", "ddim",
    "rep", "bridge", "signals", "mix", "m25", "aim", "a25", "npr", "NPR_TOTAL",
    "LUBE_EUR", "buckets", "NETDBS", "DEALER_FY_MONTHS", "dealer_eur_cy",
    "dealer_qty", "dealer_files", "dbs", "payload", "IUK_ADJ", "NPLIST", "npr_sorted",
]
snap = {}
for k in interesting:
    v = g.get(k)
    if v is None:
        continue
    try:
        if isinstance(v, __import__("pandas").DataFrame):
            snap[k] = {"__type__": "DataFrame", "shape": list(v.shape),
                       "columns": [str(c) for c in v.columns],
                       "head": v.head(6).to_dict("records")}
        elif isinstance(v, __import__("pandas").Series):
            snap[k] = {"__type__": "Series", "len": int(len(v)),
                       "name": str(v.name), "head": v.head(12).to_dict()}
        else:
            snap[k] = {"__type__": type(v).__name__, "repr": repr(v)[:4000]}
    except Exception as e:  # noqa: BLE001
        snap[k] = {"__type__": type(v).__name__, "error": str(e)}
(HERE / "_oracle_globals.json").write_text(json.dumps(snap, indent=1, default=repr), encoding="utf-8")
print("globals snapshotted:", sorted(snap))

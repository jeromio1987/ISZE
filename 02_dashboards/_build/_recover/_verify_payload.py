"""Acceptance test: run the reconstructed builder and compare its PAYLOAD with
the known-good probe_payload.json, byte for byte.

The HTML/CMD writes are intercepted so the live page is untouched until the
payload is proven identical.

Usage: python _verify_payload.py [--allow-cmd-write]
"""
import builtins
import io
import json
import pathlib
import sys
import traceback

HERE = pathlib.Path(__file__).resolve().parent
SRC = HERE / "build_db_leakage_review.reconstructed.py"
PROBE = pathlib.Path(r"C:\Users\jerom\Desktop\claude\ISZE\02_dashboards\sales\_qa\leakage_probe\probe_payload.json")

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
    if p.endswith(".html") or p.endswith(".cmd"):
        s = Sink()
        captured.setdefault("paths", []).append(p)
        captured.setdefault("buffers", {})[p] = s
        return s
    return real_open(path, *a, **k)


src = SRC.read_text(encoding="utf-8")
code = compile(src, str(SRC), "exec")
g = {"__name__": "__main__", "__file__": str(SRC), "__builtins__": builtins, "open": fake_open}

crash = None
try:
    exec(code, g)
except Exception:  # noqa: BLE001
    crash = traceback.format_exc()
    print("CRASH:", crash.splitlines()[-1])
    print(crash.splitlines()[-2])

payload = g.get("PAYLOAD")
if payload is None:
    print("NO PAYLOAD PRODUCED")
    sys.exit(2)

dump = json.dumps(payload)
probe = PROBE.read_text(encoding="utf-8")

print("=" * 70)
print("payload bytes:", len(dump))
print("probe   bytes:", len(probe))
print("EXACT MATCH:", dump == probe)
if dump != probe:
    n = min(len(dump), len(probe))
    for i in range(n):
        if dump[i] != probe[i]:
            print(f"first difference at byte {i}")
            print("  ours :", repr(dump[max(0, i - 120):i + 120]))
            print("  probe:", repr(probe[max(0, i - 120):i + 120]))
            break
    else:
        print("identical prefix; lengths differ")
    # also compare key-by-key for a readable report
    try:
        a, b = json.loads(dump), json.loads(probe)
        def diff(x, y, path=""):
            if type(x) is not type(y):
                print(f"  TYPE {path}: {type(x).__name__} vs {type(y).__name__}")
                return
            if isinstance(x, dict):
                for k in sorted(set(x) | set(y)):
                    if k not in x:
                        print(f"  MISSING ours {path}.{k}")
                    elif k not in y:
                        print(f"  EXTRA ours {path}.{k}")
                    else:
                        diff(x[k], y[k], f"{path}.{k}")
            elif isinstance(x, list):
                if len(x) != len(y):
                    print(f"  LEN {path}: {len(x)} vs {len(y)}")
                for i in range(min(len(x), len(y))):
                    diff(x[i], y[i], f"{path}[{i}]")
            elif x != y:
                print(f"  VALUE {path}: {x!r} vs {y!r}")
        diff(a, b)
    except Exception as e:  # noqa: BLE001
        print("structural compare failed:", e)
print("=" * 70)
print("intercepted writes:", captured.get("paths"))
for p, s in captured.get("buffers", {}).items():
    print("  ", p, len(s.buf.getvalue()), "chars")
sys.exit(0 if dump == probe else 1)

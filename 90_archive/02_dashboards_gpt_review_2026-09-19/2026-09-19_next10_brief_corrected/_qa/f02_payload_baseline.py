"""F02 baseline: locate the embedded payload and prove it parses as JSON before any edit. Read-only."""
import json

P = r"C:\Users\jerom\Desktop\claude\ISZE\02_dashboards\sales\_gpt_review\2026-09-19_next10_brief_corrected\02_ISZE_Leakage_Cockpit.html"
with open(P, encoding="utf-8", newline="") as f:
    t = f.read()

for marker in ("window.__LEAK__", "__LEAK__ =", "<script type=\"application/json\""):
    idx = t.find(marker)
    print(f"marker {marker!r}: idx={idx}")
    if idx >= 0:
        print("   ctx:", repr(t[idx:idx + 90]))


def extract_object(s, start):
    """start points at the first '{' of the object literal. Returns end index (exclusive)."""
    depth = 0
    i = start
    in_str = False
    esc = False
    while i < len(s):
        ch = s[i]
        if in_str:
            if esc:
                esc = False
            elif ch == "\\":
                esc = True
            elif ch == '"':
                in_str = False
        else:
            if ch == '"':
                in_str = True
            elif ch == "{":
                depth += 1
            elif ch == "}":
                depth -= 1
                if depth == 0:
                    return i + 1
        i += 1
    raise ValueError("unterminated")


anchor = t.find("window.__LEAK__")
brace = t.find("{", anchor)
end = extract_object(t, brace)
blob = t[brace:end]
print("\npayload chars:", len(blob))
try:
    d = json.loads(blob)
    print("PRE-EDIT payload parses as JSON: True; top keys:", list(d.keys())[:15])
    print("dbs:", len(d.get("dbs", {})), "meta keys:", list(d.get("meta", {}).keys())[:15])
    print("meta.verification:", d["meta"].get("verification"))
    print("has meta.source_methods:", "source_methods" in d.get("meta", {}))
    n_fw = sum(1 for v in d["dbs"].values() if isinstance(v, dict) and "forward" in v)
    print("dbs entries with 'forward':", n_fw)
    print("total 'forward' occurrences in parsed json:", blob.count('"forward"'))
except Exception as e:
    print("PRE-EDIT payload JSON.parse FAILED:", type(e).__name__, e)
    with open(r"C:\Users\jerom\Desktop\claude\ISZE\02_dashboards\sales\_gpt_review\2026-09-19_next10_brief_corrected\_qa\_f02_payload_baseline.txt", "w", encoding="utf-8") as o:
        o.write(blob)
    print("written baseline blob to _qa/_f02_payload_baseline.txt for inspection")

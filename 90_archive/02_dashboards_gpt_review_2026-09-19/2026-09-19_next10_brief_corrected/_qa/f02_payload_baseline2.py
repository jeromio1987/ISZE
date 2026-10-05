"""F02 baseline v2: extract the __LEAK__ object literal and validate it parses. Read-only."""
import json

P = r"C:\Users\jerom\Desktop\claude\ISZE\02_dashboards\sales\_gpt_review\2026-09-19_next10_brief_corrected\02_ISZE_Leakage_Cockpit.html"
with open(P, encoding="utf-8", newline="") as f:
    t = f.read()


def extract_object(s, start):
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


anchor = t.find("__LEAK__ = {")
brace = t.find("{", anchor)
end = extract_object(t, brace)
blob = t[brace:end]
print("payload chars:", len(blob))
print("assignment region:", repr(t[anchor - 40:brace + 20]))
try:
    d = json.loads(blob)
    print("PRE-EDIT payload parses as strict JSON: True")
    print("top keys:", list(d.keys()))
    print("dbs count:", len(d.get("dbs", {})))
    print("meta keys:", list(d.get("meta", {}).keys()))
    print("meta.verification:", d["meta"].get("verification"))
    print("meta.source_methods present:", "source_methods" in d.get("meta", {}))
    fw = [k for k, v in d["dbs"].items() if isinstance(v, dict) and "forward" in v]
    print("db keys with 'forward':", fw)
    print("count:", len(fw))
except Exception as e:
    print("PRE-EDIT strict-JSON parse FAILED:", type(e).__name__, e)
    with open(r"C:\Users\jerom\Desktop\claude\ISZE\02_dashboards\sales\_gpt_review\2026-09-19_next10_brief_corrected\_qa\_f02_payload_baseline.txt", "w", encoding="utf-8") as o:
        o.write(blob)

with open(r"C:\Users\jerom\Desktop\claude\ISZE\02_dashboards\sales\_gpt_review\2026-09-19_next10_brief_corrected\_qa\_f02_payload_extent.txt", "w", encoding="utf-8") as o:
    o.write(f"brace={brace}\nend={end}\nchars={end-brace}\n")
print("payload span chars", brace, end, end - brace)

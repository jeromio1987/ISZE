import json, re
P = r"C:\Users\jerom\Desktop\claude\ISZE\02_dashboards\sales\_gpt_review\2026-09-19_next10_brief_corrected\02_ISZE_Leakage_Cockpit.html"
t = open(P, encoding="utf-8", newline="").read()


def extract_object(s, start):
    depth = 0; i = start; in_str = False; esc = False
    while i < len(s):
        ch = s[i]
        if in_str:
            if esc: esc = False
            elif ch == "\\": esc = True
            elif ch == '"': in_str = False
        else:
            if ch == '"': in_str = True
            elif ch == "{": depth += 1
            elif ch == "}":
                depth -= 1
                if depth == 0: return i + 1
        i += 1
    raise ValueError


a = t.find("const __LEAK__ = {")
b = t.find("{", a)
e = extract_object(t, b)
blob = t[b:e]
print("blob chars", len(blob))
print("'</script' in blob:", blob.count("</script"))
print("blob first 120:", repr(blob[:120]))
print("blob last 120:", repr(blob[-120:]))
lines = blob.split("\n")
print("blob lines", len(lines))
for n in range(118, 130):
    print(f"blob L{n}: {lines[n-1]!r}")
# is it strict json?
try:
    json.loads(blob)
    print("strict JSON: YES")
except Exception as ex:
    print("strict JSON: NO ->", ex)
    # find the offset
    m = re.search(r"char (\d+)", str(ex))
# count trailing commas / unquoted keys
print("trailing-comma+brace pattern:", len(re.findall(r",\s*\n\s*[}\]]", blob)))
print("unquoted-ish key at line start:", len(re.findall(r"\n\s*[A-Za-z_][A-Za-z0-9_]*\s*:", blob)))

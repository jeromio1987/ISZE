"""Post-edit validation of the F02 payload and of every script block in the edited files.

1. Extract the `const __LEAK__ = {...}` object literal and evaluate it in node (not JSON.parse,
   because the literal legitimately contains arrow functions).
2. Confirm no 'forward' / 'ceiling_2030' remains and that the live ceiling survived.
3. node --check every <script> block of every edited file.
"""
import json, os, re, subprocess, tempfile, sys

BASE = r"C:\Users\jerom\Desktop\claude\ISZE\02_dashboards\sales\_gpt_review\2026-09-19_next10_brief_corrected"
QA = os.path.join(BASE, "_qa")
os.makedirs(QA, exist_ok=True)
F02 = os.path.join(BASE, "02_ISZE_Leakage_Cockpit.html")

t = open(F02, encoding="utf-8", newline="").read()
print("F02 'forward' occurrences :", t.count('"forward"'))
print("F02 ceiling_2030 occurrences:", t.count("ceiling_2030"))
print("F02 .forward dot-access    :", len(re.findall(r"\.forward\b", t)))
print("F02 live ceiling intact    :", '"ceiling_total_eur": 55253312' in t or "ceiling_total_eur" in t)
for m in re.finditer(r'"ceiling_total_eur":\s*([0-9]+)', t):
    print("   ceiling_total_eur =", m.group(1))
    break

a = t.find("const __LEAK__ = {")
b = t.find("{", a)
depth = 0; i = b; instr = False; esc = False
while i < len(t):
    ch = t[i]
    if instr:
        if esc: esc = False
        elif ch == "\\": esc = True
        elif ch == '"': instr = False
    else:
        if ch == '"': instr = True
        elif ch == "{": depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0: break
    i += 1
blob = t[b:i + 1]

eval_js = os.path.join(QA, "_f02_payload_eval.js")
with open(eval_js, "w", encoding="utf-8") as f:
    f.write("const __LEAK__ = " + blob + ";\n")
    f.write("const dbs = Object.keys(__LEAK__.dbs || {});\n")
    f.write("console.log('EVAL_OK dbs=' + dbs.length + ' meta_keys=' + Object.keys(__LEAK__.meta).length);\n")
    f.write("console.log('VERIF=' + JSON.stringify(__LEAK__.meta.verification));\n")
    f.write("console.log('HAS_FORWARD=' + JSON.stringify(dbs.filter(k => 'forward' in __LEAK__.dbs[k])));\n")
    f.write("console.log('CEILING=' + (__LEAK__.modules && JSON.stringify(Object.keys(__LEAK__.modules).filter(k=>/ceiling/i.test(k)))));\n")

r = subprocess.run(["node", eval_js], capture_output=True, text=True, encoding="utf-8")
print("\n--- node evaluate __LEAK__ ---")
print("rc:", r.returncode)
print(r.stdout.strip())
if r.stderr.strip():
    print("stderr:", r.stderr.strip()[:2000])

print("\n--- node --check on every script block of the edited files ---")
EDITED = [
    "01_ISZE_Exec_Aftersales_Paper.html",
    "02_ISZE_Leakage_Cockpit.html",
    "03_Warranty_Commercial_Review.html",
    "04_ISZE_AIM_Classification_Paper.html",
    "07_ISZE_Pricing_Revision_AIM_Source.html",
    "10_Dealer_Sellout_AIM_GPS_ITUK_UTI_2025.html",
]
scripts = re.compile(r"<script(?P<attrs>[^>]*)>(?P<body>.*?)</script>", re.S | re.I)
failures = 0
for fn in EDITED:
    p = os.path.join(BASE, fn)
    src = open(p, encoding="utf-8", newline="").read()
    blocks = list(scripts.finditer(src))
    if not blocks:
        print(f"{fn}: NO <script> blocks (nothing to parse)")
        continue
    ok = 0
    for n, m in enumerate(blocks, 1):
        attrs = m.group("attrs")
        if "application/json" in attrs:
            continue
        tmp = os.path.join(QA, f"_check_{fn[:2]}_{n}.js")
        with open(tmp, "w", encoding="utf-8") as f:
            f.write(m.group("body"))
        rr = subprocess.run(["node", "--check", tmp], capture_output=True, text=True, encoding="utf-8")
        if rr.returncode != 0:
            failures += 1
            print(f"  PARSE FAIL {fn} block {n}: {rr.stderr.strip()[:300]}")
        else:
            ok += 1
    print(f"{fn}: {len(blocks)} script blocks, {ok} parsed OK, {'0' if failures==0 else failures} failures")
print("\ntotal parse failures:", failures)

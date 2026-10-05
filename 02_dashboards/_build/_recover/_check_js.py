"""Syntax-check the inline JavaScript literal that the builder embeds.

Writes a small prelude so the script can be parsed standalone, then runs
`node --check`. Reports the first syntax error with the offending line, which is
how the empty league table and empty charts were traced.
"""
import pathlib
import subprocess
import sys

HERE = pathlib.Path(__file__).resolve().parent
const = (HERE / "_consts_all" / "c406.txt").read_text(encoding="utf-8")

PRELUDE = (
    'var DATA={meta:{snapshot:"",n_dbs:0,nw:{}},dbs:[],groups:[],noprice:[]};\n'
    "var IUK_ADJ={};\nvar KM={};\nvar FAMNET=[];\nvar NPLIST=[];\n"
    'var ST={period:"cy",dir:"db",warr:"inc"};\nvar LOADED=false;\n'
    "function g(x){return null;}\n"
    "function q(x){return null;}\n"
)

target = HERE / "_qa_c406_check.js"
target.write_text(PRELUDE + const, encoding="utf-8")

r = subprocess.run(["node", "--check", str(target)], capture_output=True, text=True)
print("js bytes:", len(const))
print("node --check exit:", r.returncode)
if r.returncode != 0:
    lines = [x for x in (r.stderr or "").splitlines() if x.strip()]
    for x in lines[:12]:
        print(" ", x)
    # print the failing source line
    for x in lines:
        if ":" in x and ".js:" in x:
            try:
                ln = int(x.rsplit(":", 1)[1])
            except ValueError:
                continue
            src = (PRELUDE + const).splitlines()
            for k in range(max(0, ln - 2), min(len(src), ln + 1)):
                print(f"  {k + 1:>4}: {src[k]!r}")
            break
sys.exit(r.returncode)

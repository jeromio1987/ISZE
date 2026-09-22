"""What global name does each source module actually publish?

The build's guard derived the name from the file name - src/case/store.js became
"root.AIMStore" - while the file publishes root.AIMCaseStore. So the guard
searched for a string that never occurs and reported "clean" while shipping a
facade whose dependency was not assembled. Found by the workflow developer.

This reports the real published name for every module, which is what the guard
needs instead of a guess.

Usage:  python tools/published_names.py
"""
import io
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)

PUBLISH_RE = re.compile(r'^\s*(?:root|globalThis)\.([A-Za-z_$][\w$]*)\s*=', re.M)
ASSIGN_RE = re.compile(r'root\.([A-Za-z_$][\w$]*)\s*=(?!=)')


def published(path):
    text = io.open(path, encoding="utf-8", errors="ignore").read()
    names = []
    for m in ASSIGN_RE.finditer(text):
        n = m.group(1)
        # Skip the read-only guards like `... : root.AIMContracts`.
        line_start = text.rfind("\n", 0, m.start()) + 1
        line_end = text.find("\n", m.start())
        line = text[line_start:line_end if line_end > 0 else len(text)]
        if re.search(r'\?\s*$|:\s*$|root\.' + re.escape(n) + r'\s*[;)]', line) and not re.search(r'\bvar\s|\bconst\s|\blet\s', line):
            continue
        if n not in names:
            names.append(n)
    return names


def main():
    mods = []
    for base, _d, files in os.walk(os.path.join(ROOT, "src")):
        for f in sorted(files):
            if f.endswith(".js"):
                rel = os.path.relpath(os.path.join(base, f), ROOT).replace("\\", "/")
                mods.append(rel)
    mods.sort()
    print("%-34s %s" % ("module", "publishes"))
    print("-" * 80)
    for m in mods:
        names = published(os.path.join(ROOT, m))
        guess = "root.AIM" + os.path.basename(m)[0].upper() + os.path.basename(m)[1:-3]
        real = names[-1] if names else "(nothing)"
        flag = "" if real == guess else "   <-- the build's guess %s is WRONG" % guess
        print("%-34s %s%s" % (m, real, flag))


if __name__ == "__main__":
    main()

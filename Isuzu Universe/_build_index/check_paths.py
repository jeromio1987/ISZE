# -*- coding: utf-8 -*-
r"""Does every path this index prints actually exist on disk?

Reads the index markdown, pulls out every backticked token that names a file or a folder, and
resolves it the way a reader would: a token carrying a folder is resolved against the Universe
folder; a bare file name is looked for anywhere in the folder, because the index names the folder
in the heading above the table. Read-only.
"""
import io
import os
import re
import sys

sys.stdout.reconfigure(encoding="utf-8")

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
MD = os.path.join(HERE, "UNIVERSE_FOLDER_INDEX_2026-09-23.md")

# a suffix shown as a description of a family of receipts, not a printed filename
SUFFIXES = ("SHIP_RECEIPT.json", ".VERIFICATION.md", ".cmd")
# family words, not one file
FAMILY = ("_probe", "figures")
# names the index prints inside a folder it has already named, so the reader resolves them there
NESTED = {
    "README.md": "05_AIM_Universe",
    "docs\\": "05_AIM_Universe",
    "progress\\progress.json": "05_AIM_Universe",
    "00_THE_MAP.md": "_MERGED_MASTER_2026-09-21",
}

# what the whole folder holds, by basename, for the bare-name lookups
BASENAMES = {}
for dirpath, dirnames, filenames in os.walk(ROOT):
    for n in list(dirnames) + list(filenames):
        BASENAMES.setdefault(n, []).append(os.path.join(dirpath, n))

src = io.open(MD, encoding="utf-8").read()
tokens = [t.strip() for t in re.findall(r"`([^`\n]+)`", src)]
tokens = [t for t in tokens if t and " " not in t]

seen, ordered = set(), []
for t in tokens:
    if t in seen:
        continue
    seen.add(t)
    ordered.append(t)

ok, bad, other = [], [], []
for t in ordered:
    if t in SUFFIXES:
        other.append(("suffix", t))
        continue
    if t in FAMILY:
        parent = os.path.dirname(t) or "."
        stem = os.path.basename(t)
        hits = [p for p in os.listdir(os.path.join(ROOT, parent))
                if p.startswith(stem)] if os.path.isdir(os.path.join(ROOT, parent)) else []
        hits += [p for p in os.listdir(os.path.join(ROOT, "_build_30")) if p.startswith(stem)]
        (ok if hits else bad).append((t, len(hits)))
        continue
    if t.endswith(".py") and "*" in t:
        stem = t.split("*")[0]
        hits = [n for n in BASENAMES if n.startswith(stem)]
        (ok if hits else bad).append((t, len(hits)))
        continue

    if t in NESTED:
        p = os.path.join(ROOT, NESTED[t].rstrip("\\"), t.rstrip("\\"))
    else:
        p = os.path.join(ROOT, t)
    if os.path.exists(p):
        ok.append((t, 1))
        continue
    hits = BASENAMES.get(os.path.basename(t.rstrip("\\")), [])
    if hits:
        ok.append((t, len(hits)))
    else:
        bad.append((t, 0))

print("distinct names printed: %d" % len(ordered))
print("files/folders resolved: %d" % len(ok))
print("suffixes (not a single file): %d  %s" % (len(other), [t for _k, t in other]))
print("FAILED: %d" % len(bad))
for t, n in bad:
    print("   MISSING %s" % t)
print()
for t, n in ok:
    print("   ok  %-58s  (%d on disk)" % (t, n))

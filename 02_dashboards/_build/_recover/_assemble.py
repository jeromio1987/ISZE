"""Assembler for the reconstructed builder.

Splices the large literals (inline CSS, inline JavaScript, HTML fragments) and
the multi-part f-strings back into the reconstruction, resolving markers
recursively, so the values are exact rather than retyped.

Writes build_db_leakage_review.reconstructed.py next to this file.

Usage: python _assemble.py
"""
import pathlib
import re

HERE = pathlib.Path(__file__).resolve().parent
CONSTS = HERE / "_consts_all"
FSTR = HERE / "_fstrings"
SRC = HERE / "build_db_leakage_review.reconstructed.in.py"
DST = HERE / "build_db_leakage_review.reconstructed.py"

text = SRC.read_text(encoding="utf-8")


def const(idx):
    return repr((CONSTS / f"c{idx:03d}.txt").read_text(encoding="utf-8"))


def fstr(idx):
    return (FSTR / f"fstr_{idx:03d}.txt").read_text(encoding="utf-8")


def resolve(t):
    for _ in range(12):
        before = t
        # source-level placeholders
        t = re.sub(r"__EXACT_C(\d{3})__", lambda m: const(int(m.group(1))), t)
        t = re.sub(r"__FSTR_(\d{3})__", lambda m: fstr(int(m.group(1))), t)
        # markers that arrived inside spliced fragments
        t = re.sub(r"@@C(\d{3})@@", lambda m: const(int(m.group(1))), t)
        t = re.sub(r"@@FSTR_(\d{3})@@", lambda m: fstr(int(m.group(1))), t)
        if t == before:
            break
    return t


new = resolve(text)
DST.write_text(new, encoding="utf-8")
print("bytes:", len(new))
left = re.findall(r"__[A-Z0-9_]+__|@@[A-Z0-9_]+@@", new)
print("remaining markers:", sorted(set(left)))

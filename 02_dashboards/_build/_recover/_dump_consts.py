"""Dump exact module-level string constants to individual files for faithful
reassembly. Writes _const_<index>.txt under _recover/_consts/."""
import json
import marshal
import pathlib
import re
import types

HERE = pathlib.Path(__file__).resolve().parent
OUT = HERE / "_consts"
OUT.mkdir(exist_ok=True)

raw = (HERE / "build_db_leakage_review_original.pyc").read_bytes()
code = marshal.loads(raw[16:])

# module consts in index order
manifest = []
for i, k in enumerate(code.co_consts):
    if isinstance(k, types.CodeType):
        manifest.append((i, "CODE", k.co_name, k.co_firstlineno))
        continue
    if isinstance(k, str) and len(k) > 200:
        p = OUT / f"_const_{i:03d}.txt"
        p.write_text(k, encoding="utf-8")
        manifest.append((i, "STRFILE", len(k), str(p.name)))
    else:
        manifest.append((i, type(k).__name__, repr(k)[:120], len(repr(k))))

(OUT / "_manifest.json").write_text(json.dumps(manifest, indent=1), encoding="utf-8")
for m in manifest:
    if m[1] in ("STRFILE", "CODE"):
        print(m)

"""Dump ALL module-level string constants (any length) to _consts_all/, so the
reconstruction can splice in exact literal values instead of hand-copied text.

Writes _consts_all/c<index>.txt plus a small manifest.
"""
import json
import marshal
import pathlib
import types

HERE = pathlib.Path(__file__).resolve().parent
OUT = HERE / "_consts_all"
OUT.mkdir(exist_ok=True)
for old in OUT.glob("*.txt"):
    old.unlink()

raw = (HERE / "build_db_leakage_review_original.pyc").read_bytes()
code = marshal.loads(raw[16:])

manifest = {}
for i, k in enumerate(code.co_consts):
    if isinstance(k, types.CodeType):
        continue
    if isinstance(k, str):
        (OUT / f"c{i:03d}.txt").write_text(k, encoding="utf-8")
        manifest[i] = {"len": len(k), "head": k[:60]}
    else:
        manifest[i] = {"type": type(k).__name__, "repr": repr(k)[:80]}

(HERE / "_consts_all" / "_manifest.json").write_text(json.dumps(manifest, indent=1), encoding="utf-8")
print("string constants dumped:", sum(1 for v in manifest.values() if "len" in v))
print("total consts:", len(manifest))

"""Print raw disassembly instructions for module source lines in a range.

Usage: _raw.py <lo> <hi> [object-path-substring]
"""
import dis
import marshal
import pathlib
import sys
import types

HERE = pathlib.Path(__file__).resolve().parent
raw = (HERE / "build_db_leakage_review_original.pyc").read_bytes()
code = marshal.loads(raw[16:])

lo, hi = int(sys.argv[1]), int(sys.argv[2])
want = sys.argv[3] if len(sys.argv) > 3 else "<module>"


def walk(c, path="<module>"):
    yield c, path
    for k in c.co_consts:
        if isinstance(k, types.CodeType):
            yield from walk(k, f"{path}/{k.co_name}@{k.co_firstlineno}")


target = None
for c, path in walk(code):
    if path == want:
        target = c
        break
if target is None:
    print("no object", want)
    sys.exit(1)

for ins in dis.get_instructions(target):
    ln = ins.positions.lineno if ins.positions else None
    if ln is not None and lo <= ln <= hi:
        print(f"{ln:>5}  {ins.offset:>6}  {ins.opname:<26} arg={ins.arg!r} {ins.argrepr!r}")

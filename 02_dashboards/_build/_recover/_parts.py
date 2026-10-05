"""Dump the ordered BUILD_STRING parts for module source lines in a range.

Each part is either a literal (from LOAD_CONST, shown exactly) or a replacement
field (shown as the raw decompiled expression). This is the ground truth for
reassembling a long f-string.

Usage: _parts.py <lo> <hi>
"""
import dis
import marshal
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
raw = (HERE / "build_db_leakage_review_original.pyc").read_bytes()
CODE = marshal.loads(raw[16:])

lo, hi = int(sys.argv[1]), int(sys.argv[2])

stack = []
cur = None
parts = []
collect = False
for ins in dis.get_instructions(CODE):
    ln = ins.positions.lineno if ins.positions else None
    op = ins.opname
    if op == "LOAD_CONST" and isinstance(ins.argval, str) and lo <= (ln or 0) <= hi:
        stack.append(("C", ins.argval))
        continue
    if op == "FORMAT_SIMPLE":
        v = stack.pop()
        parts.append(("F", v[1] if v[0] == "X" else v[1]))
        continue
    if op == "BUILD_STRING":
        if not collect:
            collect = True
        continue
    if collect and op in ("CALL", "POP_TOP"):
        collect = False
        if parts:
            print(f"--- BUILD_STRING with {len(parts)} parts ---")
            for i, (k, v) in enumerate(parts):
                if k == "C":
                    print(f"[{i:02d}] LITERAL len={len(v)}")
                    print(repr(v))
                else:
                    print(f"[{i:02d}] FIELD")
                    print(v)
            parts = []
        continue
    if ln is not None and not (lo <= ln <= hi):
        pass
    # mark expressions crudely: anything pushed while a FORMAT_SIMPLE eventually consumes
    continue

# second pass: capture expressions by simulating enough of the stack
print("\n(done)")

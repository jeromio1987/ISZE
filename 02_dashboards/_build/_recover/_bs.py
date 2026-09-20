"""Extract the exact ordered parts of the BUILD_STRING at a given source line.

Handles the small set of idioms present in this builder (including conditional
expressions whose branches are constants), so a long f-string can be rebuilt
exactly. Usage: _bs.py <line>
"""
import dis
import marshal
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
raw = (HERE / "build_db_leakage_review_original.pyc").read_bytes()
CODE = marshal.loads(raw[16:])
target_line = int(sys.argv[1])

stack = []
parts = []
pending_jumps = {}
collecting = False

instrs = list(dis.get_instructions(CODE))
for idx, ins in enumerate(instrs):
    ln = ins.positions.lineno if ins.positions else None
    op = ins.opname
    a = ins.argval

    if op == "LOAD_CONST":
        stack.append(("C", a))
    elif op == "LOAD_NAME" or op == "LOAD_FAST":
        stack.append(("N", a))
    elif op == "LOAD_ATTR":
        base = stack.pop() if stack else ("N", "?")
        stack.append(("X", f"{base[1]}.{a}"))
    elif op in ("BINARY_OP",):
        b = stack.pop() if stack else ("X", "?")
        x = stack.pop() if stack else ("X", "?")
        stack.append(("X", f"{x[1]}<op>{b[1]}"))
    elif op == "CALL":
        n = ins.arg or 0
        args = [stack.pop() for _ in range(n)][::-1] if n else []
        base = stack.pop() if stack else ("X", "?")
        if base[1] == "NULL" and stack:
            base = stack.pop()
        stack.append(("X", f"{base[1]}({', '.join(x[1] for x in args)})"))
    elif op == "CALL_KW":
        n = ins.arg or 0
        args = [stack.pop() for _ in range(n)][::-1] if n else []
        names = stack.pop() if stack else ("C", ())
        base = stack.pop() if stack else ("X", "?")
        if base[1] == "NULL" and stack:
            base = stack.pop()
        nm = names[1] if isinstance(names[1], tuple) else ()
        k = len(nm)
        pos = args[:n - k]
        kws = args[n - k:]
        rendered = [x[1] for x in pos] + [f"{p}={v[1]}" for p, v in zip(nm, kws)]
        stack.append(("X", f"{base[1]}({', '.join(rendered)})"))
    elif op == "PUSH_NULL":
        stack.append(("N", "NULL"))
    elif op == "FORMAT_SIMPLE":
        v = stack.pop() if stack else ("X", "?")
        parts.append(("FIELD", v[1]))
    elif op == "BUILD_STRING":
        collecting = True
    elif op == "BINARY_OP" or op == "TO_BOOL":
        pass

# simpler: walk again but print the raw sequence for the line
print("=== instructions on line", target_line, "===")
for ins in instrs:
    ln = ins.positions.lineno if ins.positions else None
    if ln == target_line:
        print(f"  {ins.offset:>6} {ins.opname:<20} {ins.argrepr!r}")

print("\n=== BUILD_STRING part sequence (stack bottom -> top) ===")
for i, p in enumerate(parts):
    print(f"[{i:02d}] {p[0]} {p[1]!r}")

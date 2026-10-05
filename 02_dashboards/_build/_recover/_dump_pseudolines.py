"""Recovery aid: print the module code object as a compact per-line pseudo-listing,
resolving LOAD_CONST to short forms. Makes the source logic readable without
reading 350 KB of raw disassembly.
"""
import dis
import marshal
import pathlib
import types

HERE = pathlib.Path(__file__).resolve().parent
raw = (HERE / "build_db_leakage_review_original.pyc").read_bytes()
code = marshal.loads(raw[16:])

out = []
w = out.append


def fmt(v, maxlen=88):
    if isinstance(v, types.CodeType):
        return f"<code {v.co_name}@{v.co_firstlineno}>"
    r = repr(v)
    if len(r) > maxlen:
        r = r[:maxlen] + f"...[{len(r)}]"
    return r


for lineno, off in dis.findlinestarts(code):
    pass

# group instructions by line
lines = {}
for instr in dis.get_instructions(code):
    lines.setdefault(instr.starts_line if instr.starts_line else None, [])


cur = 1
buf = []
for instr in dis.get_instructions(code):
    ln = instr.positions.lineno if instr.positions else None
    if ln is not None:
        if buf:
            w(f"{cur:>5}: " + " | ".join(buf))
            buf = []
        cur = ln
    op = instr.opname
    a = instr.argval
    if op in ("LOAD_CONST", "KW_NAMES"):
        buf.append(f"{op} {fmt(a)}")
    elif op in ("LOAD_NAME", "LOAD_GLOBAL", "STORE_NAME", "LOAD_ATTR", "STORE_ATTR",
                "LOAD_FAST", "STORE_FAST", "LOAD_METHOD", "IMPORT_NAME", "IMPORT_FROM",
                "STORE_SUBSCR", "BINARY_SUBSCR", "LOAD_FROM_DICT_OR_GLOBALS"):
        buf.append(f"{op} {a}")
    elif op in ("CALL", "CALL_KW", "CALL_FUNCTION_EX", "BINARY_OP", "COMPARE_OP",
                "BUILD_LIST", "BUILD_TUPLE", "BUILD_MAP", "BUILD_CONST_KEY_MAP",
                "BUILD_SLICE", "BUILD_STRING", "FORMAT_VALUE", "UNPACK_SEQUENCE",
                "CONTAINS_OP", "IS_OP", "UNARY_NEGATIVE", "UNARY_NOT", "GET_ITER",
                "MAKE_FUNCTION", "SET_FUNCTION_ATTRIBUTE", "COPY", "SWAP", "PUSH_NULL",
                "RETURN_VALUE", "JUMP_IF_FALSE", "JUMP_IF_TRUE", "GOTO", "GET_LEN",
                "LOAD_FROM_DICT_OR_DEREF", "MAKE_CELL", "SETUP_ANNOTATIONS"):
        buf.append(f"{op} {a}" if a is not None else op)
    else:
        buf.append(f"{op} {a}" if a is not None else op)
if buf:
    w(f"{cur:>5}: " + " | ".join(buf))

(HERE / "_module_pseudolines.txt").write_text("\n".join(out), encoding="utf-8")
print("lines written:", len(out))
print("first line no:", out[0][:6], "last:", out[-1][:6])

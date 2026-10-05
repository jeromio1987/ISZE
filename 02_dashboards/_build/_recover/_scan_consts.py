"""Recovery aid: list every code object in the backed-up bytecode and dump its
string constants, so a reconstruction can be checked against the original text.
Reads only the copy under _recover."""
import dis
import marshal
import pathlib
import types

PYC = pathlib.Path(r"C:\Users\jerom\Desktop\claude\ISZE\02_dashboards\_build\_recover\build_db_leakage_review_original.pyc")
raw = PYC.read_bytes()
print("header bytes:", raw[:16].hex())
print("source size recorded in header:", int.from_bytes(raw[12:16], "little"))
code = marshal.loads(raw[16:])
print("module co_name:", code.co_name, "| first line:", code.co_firstlineno)


def walk(c, depth=0, path="<module>"):
    yield c, depth, path
    for k in c.co_consts:
        if isinstance(k, types.CodeType):
            yield from walk(k, depth + 1, f"{path}/{k.co_name}")


total_consts = 0
objects = list(walk(code))
print("code objects:", len(objects))
for c, depth, path in objects:
    if depth > 1:
        continue
    names = [k for k in c.co_consts if isinstance(k, str) and len(k) > 2]
    total_consts += len(names)
    print(f"\n--- {path}  (line {c.co_firstlineno}, {len(names)} strings) ---")
    for s in names[:6]:
        print("     ", repr(s[:110]))
print("\ntotal long strings at depth<=1:", total_consts)

"""Recovery aid: dump the full structure of the backed-up bytecode in a form
that supports source reconstruction.

Writes (next to this file):
  _structure.txt  - one block per code object: name, args, lines, names, consts
  _disasm.txt     - full disassembly of every code object
  _consts.json    - all non-code constants per code object
  _names.json     - all names per code object

Reads only the copy under _recover. Writes only under _recover.
"""
import dis
import io
import json
import marshal
import pathlib
import types

HERE = pathlib.Path(__file__).resolve().parent
PYC = HERE / "build_db_leakage_review_original.pyc"

raw = PYC.read_bytes()
src_size = int.from_bytes(raw[12:16], "little")
code = marshal.loads(raw[16:])

objects = []


def walk(c, depth, path):
    objects.append((c, depth, path))
    for k in c.co_consts:
        if isinstance(k, types.CodeType):
            walk(k, depth + 1, f"{path}/{k.co_name}")


walk(code, 0, "<module>")

buf = io.StringIO()
w = buf.write
w(f"source size in header: {src_size}\n")
w(f"code objects: {len(objects)}\n\n")

consts_out = {}
names_out = {}

for c, depth, path in objects:
    w("=" * 100 + "\n")
    w(f"PATH {path}\n")
    w(f"  name={c.co_name!r} qualname={getattr(c, 'co_qualname', None)!r}\n")
    w(f"  firstline={c.co_firstlineno} nlines={len(list(dis.findlinestarts(c)))}\n")
    w(f"  argcount={c.co_argcount} posonly={c.co_posonlyargcount} kwonly={c.co_kwonlyargcount}\n")
    w(f"  flags={c.co_flags:#x} varnames={c.co_varnames!r}\n")
    w(f"  cellvars={c.co_cellvars!r} freevars={c.co_freevars!r}\n")
    w(f"  names={c.co_names!r}\n")
    kc = []
    for i, k in enumerate(c.co_consts):
        if isinstance(k, types.CodeType):
            kc.append((i, "CODE", k.co_name, k.co_firstlineno))
        else:
            kc.append((i, type(k).__name__, k))
        w(f"  const[{i}] = {k!r}\n" if not isinstance(k, types.CodeType)
          else f"  const[{i}] = <code {k.co_name} line {k.co_firstlineno}>\n")
    consts_out[path] = [
        {"i": e[0], "t": e[1], "v": (e[3] if len(e) > 3 and isinstance(e[3], (str, int, float, bool, bytes, tuple))
                                     else (None if len(e) <= 3 or e[-1] is None else repr(e[-1])))}
        for e in kc
    ]
    names_out[path] = list(c.co_names)
    w("\n")

(HERE / "_structure.txt").write_text(buf.getvalue(), encoding="utf-8")

dbuf = io.StringIO()
for c, depth, path in objects:
    dbuf.write("=" * 100 + "\n")
    dbuf.write(f"PATH {path}  name={c.co_name} firstline={c.co_firstlineno}\n")
    dbuf.write("=" * 100 + "\n")
    dis.dis(c, file=dbuf, depth=0)
    dbuf.write("\n\n")

(HERE / "_disasm.txt").write_text(dbuf.getvalue(), encoding="utf-8")

(HERE / "_consts.json").write_text(json.dumps(consts_out, indent=1, default=repr), encoding="utf-8")
(HERE / "_names.json").write_text(json.dumps(names_out, indent=1), encoding="utf-8")

print("source size:", src_size)
print("code objects:", len(objects))
print("structure bytes:", len(buf.getvalue()))
print("disasm bytes:", len(dbuf.getvalue()))
print("top-level objects:")
for c, depth, path in objects:
    if depth <= 1:
        print(f"  depth={depth} {path}  line={c.co_firstlineno} nconsts={len(c.co_consts)}")

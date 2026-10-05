"""Recovery aid: a small stack-simulating decompiler for the module code object.

Not a general decompiler: it handles the opcodes this builder actually uses and
emits Python-like pseudo-source, so the real source can be rewritten quickly and
accurately. Control flow is shown as explicit markers rather than reconstructed
blocks, because the goal is fidelity, not pretty output.

Writes _pseudosrc.txt next to this file.
"""
import dis
import marshal
import pathlib
import types

HERE = pathlib.Path(__file__).resolve().parent
raw = (HERE / "build_db_leakage_review_original.pyc").read_bytes()
CODE = marshal.loads(raw[16:])

# map long string constants back to their module-level index, so the pseudocode
# can reference the exact text dumped into _consts/ instead of a truncated repr.
CONST_INDEX = {}
for _i, _k in enumerate(CODE.co_consts):
    if isinstance(_k, str):
        CONST_INDEX.setdefault(repr(_k), _i)
def const_fmt(v):
    if isinstance(v, types.CodeType):
        return f"<func {v.co_name}@{v.co_firstlineno}>"
    if isinstance(v, str):
        idx = CONST_INDEX.get(repr(v))
        if idx is not None:
            return f"@@C{idx:03d}@@"
    r = repr(v)
    if len(r) > 100:
        r = r[:100] + f"...[{len(r)}]"
    return r

BIN = {v: k for k, v in dis._nb_ops} if hasattr(dis, "_nb_ops") else {}
CMP = {}
for i, ent in enumerate(dis.cmp_op):
    CMP[i] = ent[0] if isinstance(ent, tuple) else ent


FSTR_DIR = pathlib.Path(__file__).resolve().parent / "_fstrings"
FSTR_DIR.mkdir(exist_ok=True)
FSTR_INDEX = []


def fstring_exact(items):
    """Rebuild an f-string literal exactly (no truncation) and save it.

    Literal chunks come from LOAD_CONST; in the original source those braces were
    written doubled, so they are doubled again here to stay compilable.
    Convention: a part whose only braces are at the very ends is a replacement
    field; everything else is literal text.
    """
    out = ["f'"]
    for p in items:
        is_field = p.startswith("{") and p.endswith("}") and p.count("{") == 1
        if is_field:
            out.append(p)
        else:
            if p.startswith("<<genexpr@"):
                out.append(p)
                continue
            if p.startswith("@@C") and p.endswith("@@"):
                s = CODE.co_consts[int(p[3:-2])]
            else:
                s = p
                if (s.startswith("'") and s.endswith("'")) or (s.startswith('"') and s.endswith('"')):
                    try:
                        s = eval(s)
                    except Exception:  # noqa: BLE001
                        s = s[1:-1]
            s = s.replace("\\", "\\\\").replace("'", "\\'")
            s = s.replace("{", "{{").replace("}", "}}")
            s = s.replace("\n", "\\n").replace("\r", "\\r").replace("\t", "\\t")
            out.append(s)
    out.append("'")
    text = "".join(out)
    idx = len(FSTR_INDEX)
    (FSTR_DIR / f"fstr_{idx:03d}.txt").write_text(text, encoding="utf-8")
    FSTR_INDEX.append(text)
    return f"@@FSTR_{idx:03d}@@"


def fstring_source(items):
    return fstring_exact(items)


def binop(arg):
    try:
        return dis._nb_ops[arg][1]
    except Exception:  # noqa: BLE001
        return str(arg)


class D:
    def __init__(self, code):
        self.code = code
        self.out = []
        self.stack = []
        self.cur_line = code.co_firstlineno

    def p(self, indent, text):
        self.out.append("  " * indent + text)

    def resolve(self, target):
        import bisect
        k = bisect.bisect_left(self.offsets, target)
        return k if k < len(self.offsets) else None

    def resolve(self, target):
        import bisect
        k = bisect.bisect_left(self.offsets, target)
        return k if k < len(self.offsets) else None

    def run(self):
        raw = list(dis.get_instructions(self.code))
        skip_ops = {"EXTENDED_ARG", "NOT_TAKEN", "CACHE", "RESUME", "NOP"}
        instrs = [ins for ins in raw if ins.opname not in skip_ops]
        self.instrs = instrs
        # Jump targets can point at a filtered-out EXTENDED_ARG, so resolve to
        # the first instruction kept at or after the target offset.
        self.offsets = [ins.offset for ins in instrs]
        indent = 0
        i = 0
        while i < len(instrs):
            ins = instrs[i]
            ln = ins.positions.lineno if ins.positions else None
            if ln is not None and ln != self.cur_line:
                self.cur_line = ln
                self.p(indent, f"# line {ln}")
            skip = self.step_peek(i, indent)
            if skip:
                i += skip
            else:
                self.step(ins, indent)
                i += 1
        return "\n".join(self.out)

    def step_peek(self, i, indent):
        """Recognise idioms whose bytecode is not a plain stack sequence.

        1. `x or 0` compiles to COPY 1 / TO_BOOL / POP_JUMP_IF_TRUE / POP_TOP /
           LOAD_SMALL_INT 0.
        2. A conditional expression whose branches are constants compiles to
           POP_JUMP_IF_FALSE / LOAD_CONST A / JUMP_FORWARD / LOAD_CONST B.
           Inside an f-string that leaves BUILD_STRING with a wrong part count,
           so it is folded back into `(A if cond else B)`.
        """
        instrs = self.instrs
        if i + 4 >= len(instrs):
            return 0

        a, b, c, d, e = instrs[i:i + 5]
        if (a.opname == "COPY" and a.arg == 1
                and b.opname == "TO_BOOL"
                and c.opname == "POP_JUMP_IF_TRUE"
                and d.opname == "POP_TOP"
                and e.opname == "LOAD_SMALL_INT"):
            x = self.stack.pop() if self.stack else "?"
            self.stack.append(f"({x} or {e.argval})")
            return 5

        if a.opname == "POP_JUMP_IF_FALSE" and b.opname == "LOAD_CONST" and c.opname == "JUMP_FORWARD":
            else_idx = self.resolve(a.argval)
            if else_idx is not None and instrs[else_idx].opname == "LOAD_CONST":
                cond = self.stack.pop() if self.stack else "?"
                true_v = const_fmt(b.argval)
                false_v = const_fmt(instrs[else_idx].argval)
                self.stack.append(f"({true_v} if {cond} else {false_v})")
                return else_idx - i + 1
        return 0

    def step(self, ins, indent):
        op = ins.opname
        a = ins.argval
        S = self.stack
        try:
            if op in ("RESUME", "NOP", "CACHE", "EXTENDED_ARG", "MAKE_CELL", "SETUP_ANNOTATIONS",
                      "END_FOR", "NOT_TAKEN", "SET_FUNCTION_ATTRIBUTE"):
                pass
            elif op == "PUSH_NULL":
                S.append("NULL")
            elif op == "LOAD_CONST":
                if isinstance(a, types.CodeType) and a.co_name == "<genexpr>":
                    S.append(f"<<genexpr@{a.co_firstlineno}>>")
                else:
                    S.append(const_fmt(a))
            elif op == "LOAD_SMALL_INT":
                S.append(repr(a))
            elif op in ("LOAD_NAME", "LOAD_GLOBAL", "LOAD_FAST", "LOAD_FAST_CHECK",
                        "LOAD_FAST_BORROW", "LOAD_FAST_AND_CLEAR",
                        "LOAD_FROM_DICT_OR_GLOBALS", "LOAD_FROM_DICT_OR_DEREF"):
                S.append(str(a))
            elif op == "LOAD_FAST_BORROW_LOAD_FAST_BORROW":
                S.append(str(a[0]))
                S.append(str(a[1]))
            elif op == "LOAD_COMMON_CONSTANT":
                S.append(str(a))
            elif op == "LOAD_SPECIAL":
                S.append(f"<special {a}>")
            elif op == "CALL_INTRINSIC_1":
                x = S.pop() if S else "?"
                S.append(f"{a}({x})")
            elif op == "FORMAT_SIMPLE":
                x = S.pop() if S else "?"
                S.append(f"{{{x}}}")
            elif op == "FORMAT_WITH_SPEC":
                spec = S.pop() if S else "?"
                x = S.pop() if S else "?"
                S.append(f"{{{x}:{spec}}}")
            elif op == "DICT_UPDATE":
                v = S.pop() if S else "?"
                base = S.pop() if S else "{}"
                S.append(f"{{**{base}, **{v}}}")
            elif op in ("RETURN_GENERATOR", "YIELD_VALUE"):
                self.p(indent, f"# {op}")
            elif op == "LOAD_FAST_LOAD_FAST":
                S.append(str(a[0]))
                S.append(str(a[1]))
            elif op in ("LOAD_ATTR", "LOAD_METHOD"):
                base = S.pop() if S else "?"
                if base == "NULL" and S:
                    base = S.pop()
                S.append(f"{base}.{a}")
            elif op in ("STORE_NAME", "STORE_FAST"):
                v = S.pop() if S else "?"
                self.p(indent, f"{a} = {v}")
            elif op == "STORE_FAST_STORE_FAST":
                v1 = S.pop() if S else "?"
                v0 = S.pop() if S else "?"
                self.p(indent, f"{a[0]}, {a[1]} = {v0}, {v1}")
            elif op == "STORE_FAST_LOAD_FAST":
                v = S.pop() if S else "?"
                self.p(indent, f"{a[0]} = {v} ; load {a[1]}")
                S.append(str(a[1]))
            elif op == "STORE_ATTR":
                v = S.pop() if S else "?"
                o = S.pop() if S else "?"
                self.p(indent, f"{o}.{a} = {v}")
            elif op == "STORE_SUBSCR":
                k = S.pop() if S else "?"
                o = S.pop() if S else "?"
                v = S.pop() if S else "?"
                self.p(indent, f"{o}[{k}] = {v}")
            elif op == "BINARY_SUBSCR":
                k = S.pop() if S else "?"
                o = S.pop() if S else "?"
                S.append(f"{o}[{k}]")
            elif op == "BINARY_OP":
                b = S.pop() if S else "?"
                x = S.pop() if S else "?"
                nb = dis._nb_ops[ins.arg][0] if ins.arg < len(dis._nb_ops) else ""
                if nb == "NB_SUBSCR":
                    S.append(f"{x}[{b}]")
                elif nb.startswith("NB_INPLACE"):
                    sym = dis._nb_ops[ins.arg][1]
                    S.append(f"<aug {x} {sym}= {b}>")
                else:
                    S.append(f"({x} {binop(ins.arg)} {b})")
            elif op == "COMPARE_OP":
                b = S.pop() if S else "?"
                x = S.pop() if S else "?"
                S.append(f"({x} {CMP.get(ins.arg, ins.argrepr)} {b})")
            elif op == "UNARY_INVERT":
                x = S.pop() if S else "?"
                S.append(f"(~{x})")
            elif op == "UNARY_NEGATIVE":
                x = S.pop() if S else "?"
                S.append(f"(-{x})")
            elif op == "UNARY_NOT":
                x = S.pop() if S else "?"
                S.append(f"(not {x})")
            elif op == "TO_BOOL":
                x = S.pop() if S else "?"
                S.append(f"bool({x})")
            elif op == "CALL":
                n = ins.arg
                args = [S.pop() for _ in range(n)][::-1]
                base = S.pop() if S else "?"
                if base == "NULL" and S:
                    base = S.pop()
                S.append(f"{base}(" + ", ".join(args) + ")")
            elif op == "CALL_KW":
                n = ins.arg
                args = [S.pop() for _ in range(n)][::-1]
                names = S.pop() if S else "?"
                base = S.pop() if S else "?"
                if base == "NULL" and S:
                    base = S.pop()
                try:
                    realnames = eval(names)
                except Exception:  # noqa: BLE001
                    realnames = []
                if isinstance(realnames, tuple):
                    k = len(realnames)
                    pos = args[:n - k]
                    kws = args[n - k:]
                    rendered = list(pos) + [f"{nm}={v}" for nm, v in zip(realnames, kws)]
                    S.append(f"{base}(" + ", ".join(rendered) + ")")
                else:
                    S.append(f"{base}(*{args})")
            elif op == "CALL_FUNCTION_EX":
                kwargs = S.pop() if S else None
                args = S.pop() if S else "?"
                base = S.pop() if S else "?"
                if base == "NULL" and S:
                    base = S.pop()
                if kwargs and kwargs != "NULL":
                    S.append(f"{base}(*{args}, **{kwargs})")
                else:
                    S.append(f"{base}(*{args})")
            elif op == "BUILD_LIST":
                n = ins.arg
                items = [S.pop() for _ in range(n)][::-1]
                S.append("[" + ", ".join(items) + "]")
            elif op == "BUILD_TUPLE":
                n = ins.arg
                items = [S.pop() for _ in range(n)][::-1]
                S.append("(" + ", ".join(items) + ")")
            elif op == "BUILD_SET":
                n = ins.arg
                items = [S.pop() for _ in range(n)][::-1]
                S.append("{" + ", ".join(items) + "}")
            elif op == "BUILD_MAP":
                n = ins.arg
                items = [S.pop() for _ in range(2 * n)][::-1]
                pairs = [f"{items[j]}: {items[j + 1]}" for j in range(0, len(items), 2)]
                S.append("{" + ", ".join(pairs) + "}")
            elif op == "BUILD_CONST_KEY_MAP":
                n = ins.arg
                keys = S.pop()
                vals = [S.pop() for _ in range(n)][::-1]
                ks = eval(keys) if isinstance(keys, str) else keys
                S.append("{" + ", ".join(f"{k!r}: {v}" for k, v in zip(ks, vals)) + "}")
            elif op == "LIST_EXTEND":
                v = S.pop()
                base = S.pop() if S else "[]"
                if base in ("[]", "{", "{}"):
                    S.append(f"[*{v}]")
                else:
                    S.append(f"{base} + {v}")
            elif op == "SET_UPDATE":
                v = S.pop()
                base = S.pop() if S else "set()"
                S.append(f"{base} | {v}")
            elif op == "BUILD_SLICE":
                if ins.arg == 3:
                    c = S.pop() if S else "None"
                else:
                    c = "None"
                b = S.pop() if S else "None"
                x = S.pop() if S else "None"
                S.append(f"slice({x}, {b}, {c})")
            elif op == "FORMAT_VALUE":
                x = S.pop() if S else "?"
                S.append(f"{{{x}}}")
            elif op == "BUILD_STRING":
                n = ins.arg
                items = [S.pop() for _ in range(n)][::-1]
                S.append(fstring_source(items))
            elif op == "MAKE_FUNCTION":
                S.append(S.pop() if S else "?")
            elif op == "GET_ITER":
                x = S.pop() if S else "?"
                S.append(f"iter({x})")
            elif op == "GET_YIELD_FROM_ITER":
                x = S.pop() if S else "?"
                S.append(f"iter({x})")
            elif op == "FOR_ITER":
                it = S.pop() if S else "?"
                S.append(it)
                S.append(f"<next of {it}>")
                self.p(indent, f"# FOR_ITER -> {ins.argval}")
            elif op == "UNPACK_SEQUENCE":
                n = ins.arg
                x = S.pop() if S else "?"
                for k in range(n - 1, -1, -1):
                    S.append(f"({x})[{k}]")
            elif op == "POP_TOP":
                v = S.pop() if S else ""
                if v and v != "NULL":
                    self.p(indent, f"(discard) {v}")
            elif op == "COPY":
                S.append(S[-ins.arg] if len(S) >= ins.arg else "?")
            elif op == "SWAP":
                if len(S) >= ins.arg:
                    S[-1], S[-ins.arg] = S[-ins.arg], S[-1]
            elif op in ("JUMP_FORWARD", "JUMP_BACKWARD", "JUMP_BACKWARD_NO_INTERRUPT"):
                self.p(indent, f"# goto {ins.argval}")
            if op == "POP_JUMP_IF_FALSE":
                x = S.pop() if S else "?"
                self.p(indent, f"if not {x}: goto {ins.argval}")
            elif op == "POP_JUMP_IF_TRUE":
                x = S.pop() if S else "?"
                self.p(indent, f"if {x}: goto {ins.argval}")
            elif op == "POP_JUMP_IF_NONE":
                x = S.pop() if S else "?"
                self.p(indent, f"if {x} is None: goto {ins.argval}")
            elif op == "POP_JUMP_IF_NOT_NONE":
                x = S.pop() if S else "?"
                self.p(indent, f"if {x} is not None: goto {ins.argval}")
            elif op == "RETURN_VALUE":
                v = S.pop() if S else ""
                self.p(indent, f"return {v}")
            elif op == "RETURN_CONST":
                self.p(indent, f"return {const_fmt(a)}")
            elif op == "IMPORT_NAME":
                S.append(f"__import__({a!r})")
            elif op == "IMPORT_FROM":
                mod = S.pop() if S else "?"
                S.append(f"{mod}.{a}")
            elif op == "KW_NAMES":
                S.append(const_fmt(a))
            elif op == "CONTAINS_OP":
                b = S.pop() if S else "?"
                x = S.pop() if S else "?"
                needle = "in" if ins.arg == 0 else "not in"
                S.append(f"({x} {needle} {b})")
            elif op == "IS_OP":
                b = S.pop() if S else "?"
                x = S.pop() if S else "?"
                S.append(f"({x} is{'' if ins.arg == 0 else ' not'} {b})")
            elif op == "GET_LEN":
                x = S.pop() if S else "?"
                S.append(f"len({x})")
            elif op == "LIST_APPEND":
                v = S.pop() if S else "?"
                lst = S.pop() if S else "?"
                self.p(indent, f"{lst}.append({v})")
            elif op == "SET_ADD":
                v = S.pop() if S else "?"
                st = S.pop() if S else "?"
                self.p(indent, f"{st}.add({v})")
            elif op == "MAP_ADD":
                v = S.pop() if S else "?"
                k = S.pop() if S else "?"
                mp = S.pop() if S else "?"
                self.p(indent, f"{mp}[{k}] = {v}")
            elif op in ("RAISE_VARARGS", "RERAISE", "CHECK_EXC_MATCH", "PUSH_EXC_INFO",
                        "POP_EXCEPT", "BEGIN_TRY", "END_TRY", "SETUP_FINALLY", "CHECK_EG_MATCH",
                        "CLEANUP_THROW", "WITH_EXCEPT_START"):
                self.p(indent, f"# {op} {ins.argrepr}")
            else:
                self.p(indent, f"# UNHANDLED {op} {ins.argrepr}  stack_top={S[-3:]}")
        except Exception as e:  # noqa: BLE001
            self.p(indent, f"# ERR {op} {ins.argrepr}: {e}")

    def finish(self):
        pass


def walk(c, path="<module>"):
    yield c, path
    for k in c.co_consts:
        if isinstance(k, types.CodeType):
            yield from walk(k, f"{path}/{k.co_name}@{k.co_firstlineno}")


parts = []
for c, path in walk(CODE):
    d = D(c)
    body = d.run()
    parts.append("=" * 90 + f"\n# {path}   args={c.co_argcount} kwonly={c.co_kwonlyargcount} "
                 f"flags={c.co_flags:#x} line={c.co_firstlineno}\n" + "=" * 90 + "\n" + body + "\n")

(HERE / "_pseudosrc.txt").write_text("\n".join(parts), encoding="utf-8")
print("pseudosrc bytes:", len("\n".join(parts)))
print("objects:", len(parts))

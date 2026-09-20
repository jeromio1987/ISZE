"""Compare a candidate reconstruction against the original bytecode.

Compiles the candidate source and walks both code-object trees in parallel,
reporting structural and instruction-level differences. Used to drive the
reconstruction until it is equivalent, rather than eyeballing it.

Usage:
    python _compare.py <candidate.py> [--max-report N]
"""
import argparse
import dis
import marshal
import pathlib
import sys
import types

HERE = pathlib.Path(__file__).resolve().parent
PYC = HERE / "build_db_leakage_review_original.pyc"


def load_original():
    raw = PYC.read_bytes()
    return marshal.loads(raw[16:])


def walk(c, path="<module>"):
    yield c, path
    for k in c.co_consts:
        if isinstance(k, types.CodeType):
            yield from walk(k, f"{path}/{k.co_name}@{k.co_firstlineno}")


def const_key(k):
    if isinstance(k, types.CodeType):
        return ("code", k.co_name, k.co_firstlineno, len(list(dis.get_instructions(k))))
    if isinstance(k, float):
        return ("float", k)
    return (type(k).__name__, k)


def instr_list(c):
    out = []
    for i in dis.get_instructions(c):
        out.append((i.opname, const_key(i.argval) if isinstance(i.argval, types.CodeType) else i.argval))
    return out


def compare(orig, cand, max_report):
    oo = list(walk(orig))
    cc = list(walk(cand))
    problems = []
    print(f"original code objects: {len(oo)}   candidate: {len(cc)}")
    if len(oo) != len(cc):
        print("!! code object count differs")
    n = min(len(oo), len(cc))
    for idx in range(n):
        oc, op = oo[idx]
        cc_, cp = cc[idx]
        diffs = []
        if oc.co_name != cc_.co_name:
            diffs.append(f"co_name {oc.co_name!r} != {cc_.co_name!r}")
        if oc.co_argcount != cc_.co_argcount:
            diffs.append(f"argcount {oc.co_argcount} != {cc_.co_argcount}")
        if oc.co_posonlyargcount != cc_.co_posonlyargcount:
            diffs.append(f"posonly {oc.co_posonlyargcount} != {cc_.co_posonlyargcount}")
        if oc.co_kwonlyargcount != cc_.co_kwonlyargcount:
            diffs.append(f"kwonly {oc.co_kwonlyargcount} != {cc_.co_kwonlyargcount}")
        if oc.co_flags != cc_.co_flags:
            diffs.append(f"flags {oc.co_flags:#x} != {cc_.co_flags:#x}")
        if oc.co_varnames != cc_.co_varnames:
            diffs.append(f"varnames {oc.co_varnames!r} != {cc_.co_varnames!r}")
        if oc.co_names != cc_.co_names:
            on, cn = set(oc.co_names), set(cc_.co_names)
            diffs.append(f"names differ: extra_in_orig={sorted(on - cn)} extra_in_cand={sorted(cn - on)} "
                         f"order_same={oc.co_names == cc_.co_names}")
        ok = [const_key(k) for k in oc.co_consts if not isinstance(k, types.CodeType)]
        ck = [const_key(k) for k in cc_.co_consts if not isinstance(k, types.CodeType)]
        if ok != ck:
            # report first divergent constant
            for j in range(max(len(ok), len(ck))):
                a = ok[j] if j < len(ok) else None
                b = ck[j] if j < len(ck) else None
                if a != b:
                    diffs.append(f"const[{j}] {a!r} != {b!r}")
                    break
        oi = instr_list(oc)
        ci = instr_list(cc_)
        if oi != ci:
            for j in range(max(len(oi), len(ci))):
                a = oi[j] if j < len(oi) else None
                b = ci[j] if j < len(ci) else None
                if a != b:
                    diffs.append(f"instr[{j}] orig={a!r} cand={b!r} "
                                 f"(orig len {len(oi)}, cand len {len(ci)})")
                    break
        if diffs:
            problems.append((op, cp, diffs))
    if problems:
        print(f"\nDIFFERING CODE OBJECTS: {len(problems)} of {n}\n")
        for p in problems[:max_report]:
            print(f"--- orig {p[0]}\n    cand {p[1]}")
            for d in p[2][:4]:
                print(f"      {d}")
        if len(problems) > max_report:
            print(f"... and {len(problems) - max_report} more")
    else:
        print("\nALL CODE OBJECTS MATCH")
    return len(problems)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("candidate")
    ap.add_argument("--max-report", type=int, default=25)
    a = ap.parse_args()
    src = pathlib.Path(a.candidate).read_text(encoding="utf-8")
    cand = compile(src, a.candidate, "exec")
    orig = load_original()
    bad = compare(orig, cand, a.max_report)
    sys.exit(1 if bad else 0)

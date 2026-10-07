"""Which source modules does each test actually load?

Rationale: parallel developers each produced a module for the same concern, and
the assembled build ships one while retiring the other. If a test loads a retired
module, its green result guards code the product does not run - the F01 defect at
a higher level. This reports the misdirection explicitly instead of assuming the
test suite's green count means the shipped artifact is covered.

Usage:  python tools/module_audit.py
Writes: docs/MODULE_AUDIT.md
"""
import io
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)


def shipped_and_retired():
    src = io.open(os.path.join(ROOT, "tools", "build.py"), encoding="utf-8").read()
    # The shipped list is only the entries BEFORE UNWIRED_MODULES. Matching the
    # whole file reported every retired module as shipped too, which made the
    # "8 of 10 tests load a retired module" figure too high. Found by the
    # verification reviewer; corrected here and in the record.
    mods_region = src[:src.find("UNWIRED_MODULES")]
    shipped = re.findall(r'\("(src/[^"]+)",\s*"([^"]+)"\)', mods_region)
    # UNWIRED_MODULES entries are plain 2-tuples with a reason string.
    block = src[src.find("UNWIRED_MODULES"):src.find("AUDIT_ONLY_MODULES")]
    retired = re.findall(r'\("(src/[^"]+)",\s*"([^"]+)"\)', block)
    # The third class, so one report shows all three and a reader does not have to
    # read tools/build.py to find the audit-only modules (U29 task F).
    audit_block = src[src.find("AUDIT_ONLY_MODULES"):src.find("PUBLISHED_BY")]
    audit_only = re.findall(r'\("(src/[^"]+)",\s*"([^"]+)"\)', audit_block)
    return shipped, retired, audit_only


def test_files():
    out = []
    for base, _dirs, files in os.walk(os.path.join(ROOT, "tests")):
        if "_out" in base or "_profile" in base or "fixtures" in base:
            continue
        for f in files:
            if f.endswith((".mjs", ".cjs", ".js", ".py")):
                out.append(os.path.join(base, f))
    return sorted(out)


HARNESS = os.path.join(ROOT, "tests", "accept", "lib", "harness.cjs")


def harness_paths():
    """key -> src module, read from the acceptance harness's PATHS map.

    The acceptance checks load their modules through `H.requireModule(H.PATHS.x)`
    rather than by writing a path, so a scan of quoted paths alone misses every
    real load in tests/accept and reports a falling number that is really a
    shrinking detector. The map is parsed from the harness itself rather than
    typed here, so it cannot fall out of step with what the checks use.
    """
    out = {}
    try:
        text = io.open(HARNESS, encoding="utf-8", errors="ignore").read()
    except OSError:
        return out
    block = text[text.find("const PATHS = {"):text.find("};", text.find("const PATHS = {"))]
    for m in re.finditer(
            r"(\w+):\s*path\.join\(ROOT,\s*'src',\s*'([A-Za-z_]+)',\s*'([A-Za-z_]+\.js)'\)", block):
        out[m.group(1)] = "src/%s/%s" % (m.group(2), m.group(3))
    return out


def loaded_modules(path):
    """Which source modules a file loads, by text shape.

    This is a RAW TEXT SCAN and it cannot tell a load from a mention, so it
    matches the two shapes a load actually takes and nothing else:

      1. a quoted path            '../src/engine/engine.js'
      2. the acceptance harness   H.requireModule(H.PATHS.recipients)

    Matching only these two shapes is deliberate: a bare prose mention of a
    module name is not a load, and counting it made the summary report a
    re-pointed test as still loading what it had been moved off. Matching the
    harness form is equally deliberate: without it the scan reports a decreasing
    number for a growing blind spot.

    What it still cannot do, stated rather than hidden: a test that names a
    module in a STRING in order to assert it is not loaded (ux_flow.test.mjs
    lists the retired view layers exactly that way) is still counted as loading
    it. tests/accept/guard_09_module_scope.cjs reads the in-file declarations
    and is the authority on whether a load is deliberate.
    """
    try:
        text = io.open(path, encoding="utf-8", errors="ignore").read()
    except OSError:
        return set()
    found = set()
    # 1. a quoted path with an optional relative prefix:
    #    '../src/engine/engine.js'   'src/ui/views.js'   "src/case/store.js"
    for m in re.finditer(r"""['"](?:\.\.?/)*src[/\\]([A-Za-z_]+)[/\\]([A-Za-z_]+\.js)['"]""",
                         text):
        found.add("src/%s/%s" % (m.group(1), m.group(2)))
    # split-path form: path.join(ROOT, 'src', 'engine', 'engine.js')
    for m in re.finditer(r"'src'\s*,\s*'([A-Za-z_]+)'\s*,\s*'([A-Za-z_]+\.js)'", text):
        found.add("src/%s/%s" % (m.group(1), m.group(2)))
    for m in re.finditer(r'"src"\s*,\s*"([A-Za-z_]+)"\s*,\s*"([A-Za-z_]+\.js)"', text):
        found.add("src/%s/%s" % (m.group(1), m.group(2)))
    # 2. the acceptance harness: PATHS.<key>, wherever the key is used.
    for key, module in harness_paths().items():
        if re.search(r"PATHS\.%s\b" % re.escape(key), text) and key != "syntheticPayload":
            found.add(module)
    return found


def deleted_retired(retired):
    """Retired entries whose file has been deleted from the tree.

    A tombstone is not a live duplicate. tools/build.py keeps the entry so the
    guard that names it keeps working, and the file being absent is what makes
    that safe: nothing can load a file that does not exist.
    """
    out = {}
    for rel, why in retired:
        if not os.path.exists(os.path.join(ROOT, rel)):
            out[rel] = why
    return out


def main():
    shipped, retired, audit_only = shipped_and_retired()
    ship_names = {p for p, _ in shipped}
    retired_names = {p for p, _ in retired}
    audit_names = {p for p, _ in audit_only}
    reason = dict(retired)

    # A retired entry whose file has been deleted is a tombstone, not a live
    # duplicate: nothing can load it, so counting a mention of it as a retired
    # load makes the number wrong in the other direction. Kept separate so the
    # report can state both, rather than quietly lowering the count.
    gone = deleted_retired(retired)

    rows = []
    for t in test_files():
        mods = loaded_modules(t)
        if not mods:
            continue
        on_ship = sorted(m for m in mods if m in ship_names)
        on_retired = sorted(m for m in mods if m in retired_names)
        on_audit = sorted(m for m in mods if m in audit_names)
        on_gone = sorted(m for m in mods if m in gone)
        other = sorted(m for m in mods
                       if m not in ship_names and m not in retired_names
                       and m not in audit_names)
        rows.append({
            "test": os.path.relpath(t, ROOT).replace("\\", "/"),
            "shipped": on_ship, "retired": on_retired, "audit_only": on_audit,
            "deleted": on_gone, "other": other,
        })

    lines = ["# Which module each test loads", "",
             "Generated by `tools/module_audit.py`. A test that loads a retired module",
             "reports a real result about code the assembled artifact does not run.", "",
             "## Shipped by tools/build.py", ""]
    for p, label in shipped:
        lines.append("- `%s` - %s" % (p, label))
    lines += ["", "## Retired (present but not assembled)", ""]
    for p, why in retired:
        if p in gone:
            lines.append("- `%s` - %s; **DELETED from the tree, entry kept as a tombstone**"
                         % (p, why))
        else:
            lines.append("- `%s` - %s" % (p, why))

    lines += ["", "## Audit-only (assembled by no build; used by tools and tests only)", ""]
    if audit_only:
        for p, why in audit_only:
            lines.append("- `%s` - %s" % (p, why))
    else:
        lines.append("- none declared")

    lines += ["", "## Tests, by what they load", ""]
    bad = 0
    for r in rows:
        flag = "  <-- LOADS A RETIRED MODULE" if r["retired"] else ""
        if r["retired"]:
            bad += 1
        lines.append("- `%s`%s" % (r["test"], flag))
        if r["shipped"]:
            lines.append("    - shipped: %s" % ", ".join(r["shipped"]))
        if r["retired"]:
            lines.append("    - RETIRED: %s" % ", ".join(r["retired"]))
        if r["audit_only"]:
            lines.append("    - audit-only (not assembled): %s" % ", ".join(r["audit_only"]))
        if r["deleted"]:
            lines.append("    - names a DELETED module in a comment (not a load): %s"
                         % ", ".join(r["deleted"]))
        if r["other"]:
            lines.append("    - unlisted: %s" % ", ".join(r["other"]))

    lines += ["", "## Summary", "",
              "%d test files load a source module; %d of them load a retired one."
              % (len(rows), bad), "",
              "## Read this before acting on the number above", "",
              "This is a RAW TEXT SCAN. It cannot tell a misdirected load from a",
              "legitimate, in-file DECLARED comparison against a retired module - and",
              "a declared comparison is the right way to ask what the retired copy",
              "does, so some of the loads counted above are correct.",
              "",
              "`tests/accept/guard_09_module_scope.cjs` is the authority: it reads the",
              "declarations and fails only on an UNDECLARED retired load, which it",
              "reports as 3. Treat this file as the map, and that guard as the check.",
              ""]
    if gone:
        lines += ["## What this scan deliberately does not count", "",
                  "A retired entry whose file has been DELETED is a tombstone, not a live",
                  "duplicate, so it is listed separately rather than counted as a retired",
                  "load. The build keeps the entry on purpose so the guard that names it",
                  "keeps working, and nothing can load a file that is not on disk:",
                  ""]
        for p, why in gone.items():
            lines.append("- `%s` - %s" % (p, why))
        lines += ["",
                  "A module name that a test NAMES in order to assert it is not loaded is",
                  "still counted, because the scan cannot tell that from a load. A real",
                  "load is a require/import of a quoted path; the scan matches that shape",
                  "and not bare prose, so a re-pointed test's explanation of what it used",
                  "to load is no longer reported as a load.",
                  ""]

    out = os.path.join(ROOT, "docs", "MODULE_AUDIT.md")
    io.open(out, "w", encoding="utf-8").write("\n".join(lines) + "\n")

    print("%d test files load a source module" % len(rows))
    print("%d load a RETIRED module:" % bad)
    for r in rows:
        if r["retired"]:
            print("   %s" % r["test"])
            for m in r["retired"]:
                print("      <- %s  (%s)" % (m, reason.get(m, "")))
    print("wrote", out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

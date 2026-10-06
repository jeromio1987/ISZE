"""
Build the internal AIM pricing-decisions HTML (BASE-04, BASE-07).

The generated v03 file was both the source and the product, so a fix could only
be made by editing a six-megabyte file. This assembles the maintained modules in
src/ onto the retained visual shell and writes the internal artifact.

    python tools/build.py                              # synthetic payload (safe)
    python tools/build.py --payload <payload.json>     # authorised local payload
    python tools/build.py --payload <p> --check        # build, then run the checks

The shell is taken from the frozen v03 reference: this build never edits the
original artifact, and it never writes into the restricted payload.

The narrow-layout rules (UX-07) live in a maintained stylesheet, src/shell/
shell_narrow.css, which this build assembles into one <style id="shell-narrow">
block immediately before </head> and after the frozen styles. A file nobody may
edit cannot carry a rule that still has to change, so those rules are kept here
instead and a missing file stops the build rather than shipping without them.
"""
import argparse
import hashlib
from html import escape as html_escape
import io
import json
import os
import re
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
REFERENCE = os.path.join(ROOT, "reference",
                         "ISZE_AIM_Pricing_Decisions_v03_FROZEN.html")
# UX-07. The maintained small-screen stylesheet. It is assembled after the frozen
# styles so a rule of equal specificity in it wins; only the narrow layout lives
# there, and the frozen reference remains the visual starting point.
SHELL_NARROW = os.path.join(ROOT, "src", "shell", "shell_narrow.css")
DIST = os.path.join(ROOT, "dist")

# The version of THIS assembled component. The payload carries its own revision
# (0.3); the corrected component is 0.4. They are different clocks.
COMPONENT_VERSION = "0.4"

# Assembly order matters: the contracts, then the case service it reads, then the
# engine, then the data modules, then the view.
#
# Two notes for anyone editing the tables below:
#   - the `case` pair must stay before the case facade, because the facade reads
#     them and a browser has no require to fall back on;
#   - keep each entry on ONE line in the form  ("path", "label"),  because
#     _module_table and the test suites read the list line by line. A comment that
#     quotes a module path is fine; a comment inside the table that happens to look
#     like an entry is not. Measured 2026-09-22: a two-line comment in this list made
#     a naive scan report one module instead of twelve.
MODULES = [
    ("src/data/contracts.js", "shared records"),
    ("src/data/export.js", "recipient-specific exports, identity and permission"),
    ("src/case/schema.js", "case lifecycle and valid transitions"),
    ("src/case/store.js", "durable case repository, file and browser adapters"),
    ("src/engine/engine.js", "calculation (one entry point)"),
    ("src/data/manifest.js", "source manifest"),
    ("src/data/evidence.js", "evidence states"),
    ("src/data/market_observation.js", "competitor observation evidence record"),
    ("src/data/comparable.js", "comparable-price panel (computes, renders nothing)"),
    ("src/data/ids_evidence.js", "IDS evidence through validated identities"),
    ("src/data/ids_improvement_action.js", "IDS answer to separate improvement action"),
    ("src/data/prism_context.js", "read-only PRISM context at measured level"),
    ("src/data/vehicle_bands.js", "series_to_band.csv band_for (no second dictionary)"),
    ("src/data/service_demand_bounds.js", "service-demand and shared-applicability boundaries"),
    ("src/data/availability_question.js", "dated availability question and response"),
    ("src/data/tender_investigation.js", "tender feed to owned investigation"),
    ("src/data/candidates.js", "candidate workbench"),
    ("src/data/cases.js", "case facade over src/case/*"),
    ("src/data/scenario.js", "one shared scenario"),
    ("src/ui/app.js", "views and interaction"),
]

# Present in the working tree but deliberately NOT assembled into the artifact.
# Shipping a second case store, a second export builder or a second view model
# beside the ones the interface actually calls is the F01 defect at a higher
# level, so each of these is either retired or wired deliberately in a later
# increment. The build fails if a shipped module starts depending on one, so a
# dead module cannot become a silent runtime error.
UNWIRED_MODULES = [
    # DELETED 2026-09-22 - the file is gone from the tree. The entry is kept as a
    # tombstone on purpose: tests/accept/guard_09_module_scope.cjs G04 names this
    # path and asserts it classifies as RETIRED. Pruning it here without changing
    # that probe would fail a check this developer does not own, so the pruning is
    # left to the integration owner together with the guard. Nothing is assembled
    # from this entry and nothing reads it any more: tests/fin_math.test.mjs, the
    # last loader, now asks src/engine/engine.js.
    ("src/engine/pricing.js", "superseded by src/engine/engine.js; duplicate deleted 2026-09-22"),
    ("src/data/costbasis.js", "overlaps the engine's basis resolution"),
    ("src/output/recipients.js", "duplicate export builder"),
    ("src/ui/viewmodel.js", "duplicate view model"),
    ("src/ui/scenario.js", "duplicate scenario view helper"),
    ("src/ui/failure.js", "duplicate failure view"),
    ("src/ui/candidates.js", "duplicate candidate view"),
    ("src/ui/views.js", "retired second view layer; every view it held is ported into src/ui/app.js"),
    ("src/ui/render.js", "retired second shell; the F05 guard and routing live in src/ui/app.js"),
]

# The global each SHIPPED and each RETIRED module actually publishes, read from its
# own source. This used to be derived from the file name - src/case/store.js became
# "root.AIMStore" - and that derivation was wrong for EVERY module in the tree, so
# the guard below searched for strings that never occur and reported "clean" on
# every build. It therefore did not catch a facade assembled without its
# dependency, which is the exact defect it exists to prevent. Measured 2026-09-22
# with tools/published_names.py.
PUBLISHED_BY = {
    "src/data/contracts.js": "AIMContracts",
    "src/case/schema.js": "AIMCaseSchema",
    "src/case/store.js": "AIMCaseStore",
    "src/engine/engine.js": "PricingEngine",
    "src/engine/pricing.js": "PricingEngine",
    "src/data/manifest.js": "AIMManifest",
    "src/data/evidence.js": "AIMEvidence",
    "src/data/comparable.js": "AIMComparable",
    "src/data/ids_evidence.js": "AIMIdsEvidence",
    "src/data/ids_improvement_action.js": "AIMIdsImprovementAction",
    "src/data/prism_context.js": "AIMPrismContext",
    "src/data/vehicle_bands.js": "AIMVehicleBands",
    "src/data/service_demand_bounds.js": "AIMServiceDemandBounds",
    "src/data/availability_question.js": "AIMAvailabilityQuestion",
    "src/data/tender_investigation.js": "AIMTenderInvestigation",
    "src/data/export.js": "AIMExport",
    "src/data/candidates.js": "AIMCandidates",
    "src/data/cases.js": "AIMCases",
    "src/data/scenario.js": "AIMScenario",
    "src/data/costbasis.js": "AIMCostBasis",
    "src/output/recipients.js": "AIMOutput",
    "src/ui/viewmodel.js": "AIMViewModel",
    "src/ui/scenario.js": "AIMUI",
    "src/ui/failure.js": "AIMFailure",
    "src/ui/candidates.js": "AIMUI",
    "src/ui/views.js": "AIMUI",
    "src/ui/render.js": "AIMUI",
    "src/ui/app.js": None,   # mounts; it does not publish a global
}

BANNED_IN_OUTPUT = [
    ("mode a", "banned audience label"),
    ("mode b", "banned audience label"),
    ("sell-out", "banned commercial label"),
    ("sellout", "banned commercial label"),
    ("book b", "banned pricing label"),
]


def _module_table(text, start_marker, end_marker):
    """Read a (path, label) table out of this file.

    A regex over the whole region is too brittle: the comment above MODULES names
    modules in quotes, so a pattern matching "(src/...", "..." finds prose as
    well as entries and the count comes out wrong. Measured 2026-09-22 - a comment
    naming src/data/cases.js made a naive scan report one module instead of
    twelve, and two tests that read the list went red.

    This reads only lines that look like a table row: optional whitespace, an
    opening bracket, a quoted path, a comma, a quoted label, a closing bracket.
    Prose lines end in a full stop or a word, never in `),`.
    """
    body = text[text.index(start_marker):text.index(end_marker)]
    rows = []
    for line in body.split("\n"):
        s = line.strip()
        if not s.startswith("("):
            continue
        m = re.match(r'^\(\s*"([^"]+)"\s*,\s*"([^"]*)"\s*\)\s*,?\s*$', s)
        if m:
            rows.append((m.group(1), m.group(2)))
    return rows


def read_tables():
    """The two module tables, for any caller that wants them - a test, a report."""
    text = io.open(os.path.abspath(__file__), encoding="utf-8").read()
    return {
        "modules": _module_table(text, "MODULES = [", "UNWIRED_MODULES = ["),
        "unwired": _module_table(text, "UNWIRED_MODULES = [", "PUBLISHED_BY = {"),
    }


def read(path):
    with io.open(path, encoding="utf-8", errors="ignore") as fh:
        return fh.read()


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def extract_shell(html):
    """The retained visual direction: styles, header, sidebar, mount points.

    Everything after the case-data blob is replaced, because that is the whole
    application. The shell is what the operator sees around it.
    """
    data_match = re.search(
        r'<script id="case-data" type="application/json">(.*?)</script>', html, re.S)
    if not data_match:
        raise SystemExit("The frozen reference has no case-data block.")

    head_end = html.find("</head>")
    if head_end < 0:
        raise SystemExit("The frozen reference has no </head>.")
    head = html[:head_end]

    # The shell is everything from <body> up to the first <script>. Cutting at
    # the first </body> would truncate the shell, because the payload's own
    # export template contains that tag inside a string.
    body_start = html.find("<body")
    script_start = html.find("<script", body_start)
    if body_start < 0 or script_start < 0:
        raise SystemExit("Could not locate the shell boundary in the frozen reference.")
    body = html[body_start:script_start]

    # Everything the shell must expose, or the application cannot mount.
    for mount in ['id="case-list"', 'id="case-header"', 'id="scope-strip"',
                  'id="pack-status"', 'id="tabs"', 'id="content"', 'id="market"',
                  'id="sources-top"']:
        if mount not in body:
            raise SystemExit("The extracted shell is missing the mount point " + mount)
    return head, body


def build(payload_path):
    if not os.path.exists(REFERENCE):
        raise SystemExit(
            "The frozen v03 reference is missing:\n  " + REFERENCE
            + "\nCopy the original artifact there as "
              "ISZE_AIM_Pricing_Decisions_v03_FROZEN.html and run again.")

    shell_html = read(REFERENCE)
    head, body = extract_shell(shell_html)

    # UX-07. Refuse to build without the narrow stylesheet, the way a missing
    # module is refused: a build that silently ships the frozen narrow rules
    # again is the defect this file exists to remove.
    if not os.path.exists(SHELL_NARROW):
        raise SystemExit(
            "The maintained narrow-shell stylesheet is missing:\n  " + SHELL_NARROW
            + "\nIt holds the UX-07 small-screen rules; restore it and run again.")
    shell_narrow_css = read(SHELL_NARROW)

    # Hash the exact bytes opened, not a re-serialization that hides changes in
    # the source file. Preserve the legacy serialized digest under its old key.
    with open(payload_path, "rb") as fh:
        payload_raw = fh.read()

    def reject_constant(value):
        raise ValueError("Non-finite JSON constant refused: " + value)

    payload = json.loads(payload_raw.decode("utf-8-sig"), parse_constant=reject_constant)
    if not isinstance(payload, dict):
        raise SystemExit("The payload must be a JSON object.")
    payload_text = json.dumps(payload, separators=(",", ":"), allow_nan=False)
    # application/json does not stop an HTML parser recognising </script>.
    # JSON Unicode escapes preserve the data while keeping it inside its block.
    payload_html_text = (payload_text.replace("&", "\\u0026")
                         .replace("<", "\\u003c").replace(">", "\\u003e"))

    version = (payload.get("meta", {}) or {}).get("version", "AIM Pricing Decisions")

    # The stamp must name THIS component's version, not the payload's revision.
    # The payload is still the 0.3 pack; the artifact is the corrected 0.4 build.
    # Stamping the payload revision here would label the artifact 0.3 while its
    # own filename says v04 - the version-accuracy mistake this build exists to
    # remove. The payload revision is shown separately rather than dropped.
    version_stamp = '<span class="version">Decision component %s &middot; payload %s</span>' % (
        COMPONENT_VERSION, html_escape(str(version).replace("AIM Pricing Decisions ", ""), quote=True))
    # A callable replacement also keeps backslashes in source version text literal.
    body = re.sub(r'<span class="version">[^<]*</span>', lambda _match: version_stamp, body)
    body = body.replace("Decision component 0.2", "Decision component " + COMPONENT_VERSION)
    body = body.replace("Decision component 0.1", "Decision component " + COMPONENT_VERSION)

    # The narrow shell goes in AFTER the frozen styles, which `head` already
    # carries, and immediately before </head>.
    parts = [head,
             '<style id="shell-narrow">',
             shell_narrow_css,
             "</style>",
             "</head>",
             body]
    parts.append('<script id="case-data" type="application/json">')
    parts.append(payload_html_text)
    parts.append("</script>")
    for rel, _label in MODULES:
        path = os.path.join(ROOT, rel)
        if not os.path.exists(path):
            raise SystemExit("Missing module: " + path)
        source = read(path)
        # app.js ships its own <script> wrapper; the library modules do not.
        if source.lstrip().startswith("<script"):
            parts.append(source)
        else:
            parts.append("<script>")
            parts.append(source)
            parts.append("</script>")

    # A shipped module must not read a retired one, or the artifact loads with a
    # silent undefined global. The name is taken from PUBLISHED_BY, which records
    # what each file actually publishes, because deriving it from the file name
    # was wrong for every module in the tree and made this check search for a
    # string that never occurs.
    #
    # A tombstone entry is skipped: src/engine/pricing.js was deleted, and it
    # published the same name as the engine that replaced it, so treating it as a
    # live dependency would refuse a perfectly correct build.
    for rel, _label in MODULES:
        source = read(os.path.join(ROOT, rel))
        for unwired, why in UNWIRED_MODULES:
            if not os.path.exists(os.path.join(ROOT, unwired)):
                continue  # tombstone for a deleted file; nothing can be read from it
            name = PUBLISHED_BY.get(unwired)
            if not name:
                continue
            holder = "root." + name
            for match in re.finditer(re.escape(holder) + r"(?!\s*=)", source):
                line_no = source[:match.start()].count("\n") + 1
                raise SystemExit(
                    "%s line %d reads %s, which is not assembled into the artifact "
                    "(%s is %s). Wire it deliberately or retire it."
                    % (rel, line_no, holder, unwired, why))

    # A shipped module that publishes a name must not collide with another shipped
    # module's name: the second one would silently replace the first at runtime.
    seen = {}
    for rel, _label in MODULES:
        name = PUBLISHED_BY.get(rel)
        if name is None:
            continue
        if name in seen:
            raise SystemExit(
                "%s and %s both publish root.%s, so whichever is assembled second "
                "silently replaces the other." % (seen[name], rel, name))
        seen[name] = rel

    # A module named in neither list is invisible to the checks above. Report it
    # rather than let it ship unlinted; the caller decides, not the build.
    known = {rel for rel, _ in MODULES} | {rel for rel, _ in UNWIRED_MODULES}
    for rel in sorted(PUBLISHED_BY):
        if rel not in known:
            print("warning : %s publishes root.%s but is in neither MODULES nor "
                  "UNWIRED_MODULES" % (rel, PUBLISHED_BY[rel] or "(nothing)"))
    parts.append("</body></html>")
    html = "\n".join(parts)

    # A banned label must not reappear through a retained template string.
    findings = []
    lowered = html.lower()
    for term, why in BANNED_IN_OUTPUT:
        if term in lowered:
            findings.append("%s (%s)" % (term, why))

    if findings:
        raise SystemExit("Build refused before writing output: " + "; ".join(findings))

    os.makedirs(DIST, exist_ok=True)
    # The artifact name states which payload built it. One mutable file with a
    # fixed name meant any agent running the default build silently replaced the
    # real-payload artifact with a synthetic one, and a reader could not tell.
    # That is how a synthetic rebuild took out the browser journey at 13:42.
    is_synthetic = "synthetic" in os.path.basename(payload_path).lower()
    out_name = ("ISZE_AIM_Pricing_Decisions_v04_SYNTHETIC.html" if is_synthetic
                else "ISZE_AIM_Pricing_Decisions_v04_INTERNAL.html")
    out_html = os.path.join(DIST, out_name)
    with io.open(out_html, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(html)

    # A launcher per artifact, so the one a reader double-clicks matches the
    # build they were told about.
    launcher = os.path.join(DIST, out_name.replace(".html", "") + ".cmd")
    with io.open(launcher, "w", encoding="ascii", newline="\r\n") as fh:
        fh.write('@echo off\r\nstart "" "%~dp0' + out_name + '"\r\n')

    # Keep the house launcher name pointing at the real artifact when one is
    # built, so the documented double-click path keeps working.
    if not is_synthetic:
        house = os.path.join(DIST, "OPEN_AIM_Pricing_Decisions_v04.cmd")
        with io.open(house, "w", encoding="ascii", newline="\r\n") as fh:
            fh.write('@echo off\r\nstart "" "%~dp0' + out_name + '"\r\n')

    report = {
        "built_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "output": out_html,
        "output_bytes": os.path.getsize(out_html),
        "output_sha256": sha256(out_html),
        "payload_file": os.path.basename(payload_path),
        "payload_sha256": hashlib.sha256(payload_text.encode("utf-8")).hexdigest(),
        "payload_sha256_basis": "legacy compact JSON serialization, before HTML escaping",
        "payload_raw_sha256": hashlib.sha256(payload_raw).hexdigest(),
        "payload_canonical_sha256": hashlib.sha256(payload_text.encode("utf-8")).hexdigest(),
        "payload_canonical_basis": "Python compact JSON serialization; insertion order retained, not RFC canonical JSON",
        "payload_embedded_sha256": hashlib.sha256(payload_html_text.encode("utf-8")).hexdigest(),
        "payload_is_synthetic": is_synthetic,
        "shell_source": os.path.relpath(REFERENCE, ROOT),
        "shell_sha256": sha256(REFERENCE),
        "shell_narrow_sha256": sha256(SHELL_NARROW),
        "modules": [rel for rel, _ in MODULES],
        "banned_label_findings": findings,
    }
    with io.open(os.path.join(DIST, "_build_report.json"), "w", encoding="utf-8") as fh:
        fh.write(json.dumps(report, indent=2) + "\n")

    print("built   : %s" % out_html)
    print("bytes   : %d" % report["output_bytes"])
    print("sha256  : %s" % report["output_sha256"])
    print("payload : %s%s" % (
        report["payload_file"],
        "  (SYNTHETIC)" if report["payload_is_synthetic"] else "  (authorised local)"))
    print("labels  : %s" % ("WARNING " + "; ".join(findings) if findings else "clean"))
    if report["payload_is_synthetic"]:
        print("note    : written as a SYNTHETIC artifact. The real-payload artifact at "
              "dist/ISZE_AIM_Pricing_Decisions_v04_INTERNAL.html is untouched, so the "
              "browser journey keeps testing the real one.")
    return report


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--payload",
                    default=os.path.join(ROOT, "tests", "fixtures", "synthetic_payload.json"))
    ap.add_argument("--check", action="store_true",
                    help="run the regression suite against the same payload after building")
    args = ap.parse_args()

    build(args.payload)
    if args.check:
        import subprocess
        suite = os.path.join(ROOT, "tests", "run_tests.cjs")
        proc = subprocess.run(["node", suite, "--payload", args.payload],
                              cwd=ROOT, capture_output=True, text=True)
        print(proc.stdout.strip())
        return proc.returncode
    return 0


if __name__ == "__main__":
    sys.exit(main())

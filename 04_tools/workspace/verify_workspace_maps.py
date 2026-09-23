"""Verify the navigation maps agents boot from actually point at things that exist.

Agents start at INDEX.md -> ROUTING.yaml -> AGENTS.md and follow paths from there.
When one of those paths rots, the agent does not error — it quietly reads nothing,
or reads the wrong file. This script makes that failure loud.

Four checks:

  1. ROUTING paths   every path listed under a tasks.<name> entry resolves
  2. Registry paths  every path in MAP_REGISTRY.yaml resolves
  3. Markdown links  relative links in the bootstrap + roadmap docs resolve
  4. Ignore mirrors  every Tier 0 "never track" rule on 01_data/ has an
                     equivalent rule for the 02_dashboards/Data/ mirror, and
                     nothing tracked under a mirror path should have been ignored

Exits non-zero when a check fails, so it can gate CI.

Usage:
    python 04_tools/workspace/verify_workspace_maps.py [--quiet]
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path

try:
    import yaml
except ImportError:  # pragma: no cover
    print("FAIL: pyyaml not installed")
    raise SystemExit(2)

_TOOLS = Path(__file__).resolve().parent.parent
if str(_TOOLS) not in sys.path:
    sys.path.insert(0, str(_TOOLS))

from _shared.paths import ISZE_ROOT  # noqa: E402

# Docs whose relative links agents actually follow.
LINKED_DOCS = [
    "INDEX.md",
    "README.md",
    "AGENTS.md",
    "CLAUDE.md",
    "00_docs/ISZE_ROADMAP.md",
    "00_docs/MAPS.md",
    "00_docs/REFERENCE.md",
    "00_docs/README.md",
    "00_docs/roadmaps/gps.md",
    "00_docs/roadmaps/html.md",
    "00_docs/roadmaps/scrapers.md",
    "00_docs/roadmaps/tools.md",
    "00_docs/roadmaps/aim_prism_reinvention.md",
    "00_docs/roadmaps/ai_sales_intelligence.md",
]

# Links that intentionally leave this repo (parent workspace, private bridge).
LINK_ALLOWLIST = {"../../INDEX.md", "../../docs/BRIDGE_PRIVATE_ISZE.md"}

# Tier 0 directories that must never be tracked, on either side of the mirror.
TIER0_DIRS = [
    "12_raw",
    "raw",
    "90_INBOX",
    "_INBOX",
    "04_sales",
    "17_interactions",
]

LINK_RX = re.compile(r"\[[^\]]*\]\(([^)\s]+)\)")

# Keys whose values are paths. Free-text keys (description, rules) are prose and
# are never treated as paths. `never` lists exclusion patterns — those are meant
# to be absent, so checking them would invert the test.
PATH_KEYS = {
    "read", "optional", "data", "run", "rebuild", "open", "feed", "drop_zone",
    "verify", "workflow", "critique", "loop", "assets", "map",
}
SKIP_KEYS = {"description", "rules", "never", "note"}


def _path_scalars(node, in_path_context: bool = False):
    """Yield scalars that sit under a path-bearing key. Whole scalar, never split —
    ISZE has real paths with spaces (`09_meetings/Preparation Meetings/...`).

    Once inside a path-bearing key everything below it is a path, including the
    values of a keyword map such as `memory_topic.map`."""
    if isinstance(node, dict):
        for k, v in node.items():
            if k in SKIP_KEYS:
                continue
            yield from _path_scalars(v, in_path_context or k in PATH_KEYS)
    elif isinstance(node, list):
        for v in node:
            yield from _path_scalars(v, in_path_context)
    elif isinstance(node, str) and in_path_context:
        yield node


def _clean_candidate(text: str) -> str | None:
    """Normalise one scalar into a checkable path, or None if it is not one."""
    value = text.split("#")[0].strip().strip("`'\"")
    if not value:
        return None
    # Workflow steps read as prose: "Run 02_dashboards/sync_to_deploys.ps1".
    first, _, rest = value.partition(" ")
    if first in {"Run", "Edit", "Open", "Rebuild"} and rest:
        value = rest.strip()
    # Commands: take the argument that looks like a path.
    if value.split(" ", 1)[0] in {"python", "powershell", "pwsh", "node"}:
        parts = [p for p in value.split(" ")[1:] if "/" in p or p.endswith((".py", ".ps1"))]
        if not parts:
            return None
        value = parts[0]
    value = value.replace("/**", "").replace("/*", "").rstrip("/")
    if not re.search(r"[/.]", value) or value.startswith("http"):
        return None
    # Trailing prose like "(tender only)" or a sentence.
    if " " in value and not re.match(r"^[\w./\\ -]+$", value):
        return None
    return value


def _is_ignored(root: Path, rel: str) -> bool:
    """A gitignored path is expected to be absent in a fresh clone — not rot."""
    for probe in (rel, rel.rstrip("/") + "/"):
        try:
            if subprocess.run(
                ["git", "check-ignore", "-q", probe], cwd=root, capture_output=True
            ).returncode == 0:
                return True
        except Exception:
            return False
    return False


def check_routing(root: Path, problems: list[str], ignored: list[str]) -> int:
    data = yaml.safe_load((root / "00_docs/ROUTING.yaml").read_text(encoding="utf-8"))
    checked = 0
    for task, body in (data.get("tasks") or {}).items():
        for text in _path_scalars(body):
            candidate = _clean_candidate(text)
            if not candidate:
                continue
            checked += 1
            if (root / candidate).exists():
                continue
            where = f"ROUTING tasks.{task} -> {candidate}"
            (ignored if _is_ignored(root, candidate) else problems).append(where)
    return checked


def check_registry(root: Path, problems: list[str], ignored: list[str]) -> int:
    data = yaml.safe_load((root / "00_docs/MAP_REGISTRY.yaml").read_text(encoding="utf-8"))
    checked = 0
    for section in ("bootstrap", "reference", "roadmaps", "roadmap_specs", "memory",
                    "deploy", "data_spine", "code_spine", "scripts"):
        for text in _path_scalars(data.get(section) or {}, in_path_context=True):
            candidate = _clean_candidate(text)
            if not candidate or candidate.startswith(".."):  # parent-workspace pointer
                continue
            checked += 1
            if (root / candidate).exists():
                continue
            where = f"MAP_REGISTRY {section} -> {candidate}"
            (ignored if _is_ignored(root, candidate) else problems).append(where)
    return checked


def check_links(root: Path, problems: list[str]) -> int:
    checked = 0
    for rel in LINKED_DOCS:
        doc = root / rel
        if not doc.exists():
            problems.append(f"LINKED_DOCS: {rel} does not exist")
            continue
        for match in LINK_RX.finditer(doc.read_text(encoding="utf-8")):
            target = match.group(1).split("#")[0].strip()
            if not target or target.startswith(("http", "mailto:", "tel:")):
                continue
            if target in LINK_ALLOWLIST:
                continue
            checked += 1
            if not (doc.parent / target).exists():
                problems.append(f"{rel}: broken link -> {target}")
    return checked


def check_ignore_mirror(root: Path, problems: list[str]) -> int:
    """Tier 0 protection must cover 02_dashboards/Data/ as well as 01_data/."""
    gitignore = (root / ".gitignore").read_text(encoding="utf-8")
    checked = 0
    for name in TIER0_DIRS:
        canonical = f"01_data/{name}/**"
        if canonical not in gitignore:
            continue  # not a Tier 0 dir in this repo
        checked += 1
        mirror = f"02_dashboards/Data/{name}/**"
        if mirror not in gitignore:
            problems.append(
                f".gitignore: {canonical} is protected but {mirror} is not — "
                "the mirror path is an open back door"
            )
    return checked


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--quiet", action="store_true")
    args = parser.parse_args()

    root = ISZE_ROOT
    problems: list[str] = []
    ignored: list[str] = []
    counts = {
        "routing paths": check_routing(root, problems, ignored),
        "registry paths": check_registry(root, problems, ignored),
        "markdown links": check_links(root, problems),
        "tier0 mirror rules": check_ignore_mirror(root, problems),
    }

    if not args.quiet:
        print(f"workspace map check — root {root}")
        for label, n in counts.items():
            print(f"  {label:22} {n:>5} checked")

    if ignored and not args.quiet:
        # Expected in a fresh clone: the path is real on the workspace but gitignored.
        print(f"\nINFO — {len(ignored)} mapped path(s) absent because they are gitignored:")
        for item in sorted(ignored)[:12]:
            print(f"  - {item}")
        if len(ignored) > 12:
            print(f"  ... and {len(ignored) - 12} more")

    if problems:
        print(f"\nFAIL — {len(problems)} problem(s):")
        for p in problems:
            print(f"  - {p}")
        return 1

    print("\nOK — every mapped path, link and Tier 0 mirror rule resolves")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

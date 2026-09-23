"""Schema guard: has a derived file quietly stopped carrying a column it used to carry?

Added 2026-09-22, after the third instance in one day of the same class of defect — a file that
claims to carry information and quietly stops carrying it. On 2026-09-21 another workstream
regenerated `gps_spu_by_distributor.csv` and it **silently lost two annotation columns**
(`period_basis`, `coverage_note`) and one row. Nothing noticed for a day. It surfaced only because
`scripts/build_lost_sales_model.py` happened to name `period_basis` and crashed with
``KeyError: "['period_basis'] not in index"``.

Why the existing checks did not see it: the verifier reads *values*, so a missing column is caught
only if a check happens to name that column. Nothing compared the **shape** of a file against what
it is supposed to be. This module does that.

The expectations come from `verification_fixtures.yaml` -> `schema_required:`. A column declared
there and absent from the file is a **fail**, not a warn. That is deliberately different from the
freshness check (a warn, because some staleness is deliberate): a vanished column is never
deliberate, and something downstream may already depend on it.

Added columns are reported as detail only and never fail — a file is allowed to grow.

Where the file is committed to git, the expectation is additionally refreshed from
``git show HEAD:<path>`` and any column present in the committed version but absent from the working
copy is reported. That arm is best-effort: the declared list above is the primary mechanism and the
check works with no git at all.
"""
from __future__ import annotations

import csv
import io
import json
import shutil
import subprocess
from pathlib import Path
from typing import Any, Callable

CSV_SUFFIXES = {".csv", ".tsv"}


def _csv_columns(path: Path) -> list[str] | None:
    """Column names of a CSV on disk. Reads one line, so size is not a problem."""
    try:
        with path.open(encoding="utf-8-sig", newline="") as fh:
            header = next(csv.reader(fh), None)
    except OSError:
        return None
    return [c.strip() for c in header] if header else None


def _csv_columns_from_text(text: str) -> list[str] | None:
    header = next(csv.reader(io.StringIO(text)), None)
    return [c.strip() for c in header] if header else None


def _json_keys(path: Path, dotted: str | None) -> list[str] | None:
    """The keys of the JSON object at `dotted` (a dot path), or of the document root.

    `dotted` lets a fixture point at the object that actually holds the expected keys, e.g.
    `metrics` for metrics_snapshot.json, which is otherwise just {as_of, generator, metrics}.
    """
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    if not isinstance(payload, dict):
        return None
    if dotted:
        node: Any = payload
        for part in dotted.split("."):
            if not isinstance(node, dict) or part not in node:
                return None
            node = node[part]
        if not isinstance(node, dict):
            return None
        return list(node.keys())
    return list(payload.keys())


def _json_keys_from_text(text: str, dotted: str | None) -> list[str] | None:
    try:
        payload = json.loads(text)
    except ValueError:
        return None
    if not isinstance(payload, dict):
        return None
    node: Any = payload
    if dotted:
        for part in dotted.split("."):
            if not isinstance(node, dict) or part not in node:
                return None
            node = node[part]
        if not isinstance(node, dict):
            return None
    return list(node.keys())


def _current_columns(path: Path, kind: str, dotted: str | None) -> list[str] | None:
    if kind == "json":
        return _json_keys(path, dotted)
    return _csv_columns(path)


def _git_head_text(rel_path: str, repo_root: Path) -> str | None:
    """The committed version of a file, or None. Absence of git is never an error."""
    if shutil.which("git") is None:
        return None
    try:
        proc = subprocess.run(
            ["git", "show", f"HEAD:{rel_path}"],
            cwd=str(repo_root),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=60,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    return proc.stdout if proc.returncode == 0 else None


def evaluate(
    files: list[dict[str, Any]],
    derived_dir: Path,
    repo_root: Path | None = None,
) -> dict[str, Any]:
    """Compare each declared file's columns against the declaration. Pure — no report object."""
    per_file: list[dict[str, Any]] = []
    git_lost: list[str] = []

    for spec in files:
        name = str(spec.get("file") or "").strip()
        if not name:
            continue
        kind = str(spec.get("kind") or ("json" if name.endswith(".json") else "csv")).lower()
        dotted = spec.get("key_path")
        declared = [str(c) for c in (spec.get("required_columns") or [])]
        path = derived_dir / name

        entry: dict[str, Any] = {
            "file": name,
            "kind": kind,
            "declared": len(declared),
            "present": 0,
            "missing": [],
            "added": [],
            "status": "ok",
        }

        if not path.exists():
            entry["status"] = "missing_file"
            entry["missing"] = declared
            per_file.append(entry)
            continue

        actual = _current_columns(path, kind, dotted)
        if actual is None:
            entry["status"] = "unreadable"
            per_file.append(entry)
            continue

        absent = set(actual)
        missing = [c for c in declared if c not in absent]
        added = [c for c in actual if c not in set(declared)]
        entry["missing"] = missing
        entry["added"] = added
        entry["present"] = len(actual)
        entry["status"] = "column_lost" if missing else "ok"

        # Second, best-effort arm: what the committed version carries that the working copy
        # does not. Catches a column nobody thought to declare.
        if repo_root is not None:
            rel_dir = spec.get("git_dir")
            if rel_dir:
                head_text = _git_head_text(f"{rel_dir}/{name}".replace("\\", "/"), repo_root)
                if head_text:
                    if kind == "json":
                        head_cols = _json_keys_from_text(head_text, dotted)
                    else:
                        head_cols = _csv_columns_from_text(head_text)
                    if head_cols:
                        lost = [c for c in head_cols if c not in absent]
                        entry["lost_vs_git_head"] = lost
                        if lost:
                            git_lost.append(f"{name}: {', '.join(lost)}")

        per_file.append(entry)

    return {"files": per_file, "git_lost": git_lost}


def check(report: Any, fx: dict[str, Any], derived_dir: Path, chk: Callable[..., None]) -> None:
    spec = (fx or {}).get("schema_required") or {}
    files = spec.get("files") or []
    if not files:
        return

    # derived_dir is <repo>/01_data/00_derived, so its grandparent is the workspace root.
    # Only needed for the best-effort git arm; the declared list works with no repo at all.
    repo_root = Path(spec["repo_root"]) if spec.get("repo_root") else derived_dir.parents[1]
    if not (repo_root / ".git").exists():
        repo_root = None

    result = evaluate(files, derived_dir, repo_root)

    for entry in result["files"]:
        name = entry["file"]
        cid = f"schema.{name}"
        if entry["status"] == "missing_file":
            chk(
                report,
                cid,
                False,
                f"{name} is declared in schema_required but missing from {derived_dir.name}/",
                declared=entry["declared"],
            )
            continue
        if entry["status"] == "unreadable":
            chk(report, cid, False, f"{name} could not be read to test its columns")
            continue

        if entry["missing"]:
            chk(
                report,
                cid,
                False,
                f"{name} has LOST {len(entry['missing'])} declared column(s): "
                f"{', '.join(entry['missing'])}. Something downstream may read one of them — "
                f"the 2026-09-21 regeneration of gps_spu_by_distributor.csv dropped "
                f"period_basis/coverage_note this way and was found a day later by a KeyError.",
                missing=entry["missing"],
                declared=entry["declared"],
                present=entry["present"],
            )
        else:
            grew = f"; {len(entry['added'])} new column(s) reported, not a defect" if entry["added"] else ""
            chk(
                report,
                cid,
                True,
                f"{name}: all {entry['declared']} declared column(s) present"
                f" ({entry['present']} in the file){grew}",
                added=entry["added"],
            )

    # One aggregate check for the git arm, so the report stays readable.
    if repo_root is not None and any(e.get("lost_vs_git_head") is not None for e in result["files"]):
        if result["git_lost"]:
            chk(
                report,
                "schema.no_column_lost_vs_git_head",
                False,
                f"{len(result['git_lost'])} file(s) carry a column in their committed version "
                f"that the working copy no longer has: {'; '.join(result['git_lost'])}",
                lost=result["git_lost"],
            )
        else:
            chk(
                report,
                "schema.no_column_lost_vs_git_head",
                True,
                "no declared file has lost a column against its committed version",
            )

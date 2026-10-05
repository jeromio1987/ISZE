"""Typed failure with a code, a plain sentence, and a next step.

The rule for this tool: never a bare traceback. Every failure a person can cause
carries a code from config/error_codes.yaml, so it can be looked up in
TROUBLESHOOTING.md or pasted into GPT.

Usage:
    raise BprError("E102", "Sales-to-dealer file not found.",
                   path=..., expected="01_data/12_raw/dealer_sales/PORTUGAL/*.xlsx")
"""
from __future__ import annotations

import json
import platform
import sys
import traceback
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError:  # pragma: no cover
    yaml = None  # type: ignore

_CODES_PATH = Path(__file__).resolve().parent / "config" / "error_codes.yaml"


def load_codes() -> dict[str, dict[str, str]]:
    """The code table. Returns {} if the file cannot be read, so we never crash on our own error path."""
    if yaml is None or not _CODES_PATH.is_file():
        return {}
    try:
        with _CODES_PATH.open(encoding="utf-8") as fh:
            return yaml.safe_load(fh) or {}
    except Exception:
        return {}


def code_title(code: str) -> str:
    return (load_codes().get(code) or {}).get("title", "Unknown code")


def code_means(code: str) -> str:
    return (load_codes().get(code) or {}).get("means", "")


def code_fix(code: str) -> str:
    return (load_codes().get(code) or {}).get("fix", "")


class BprError(Exception):
    """A failure we can explain to a non-technical person."""

    def __init__(
        self,
        code: str,
        message: str,
        *,
        path: str | Path | None = None,
        expected: str | None = None,
        found: str | None = None,
        db: str | None = None,
        block: str | None = None,
        detail: str | None = None,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.path = str(path) if path is not None else None
        self.expected = expected
        self.found = found
        self.db = db
        self.block = block
        self.detail = detail

    # ---------------------------------------------------------------- reporting
    def as_dict(self) -> dict[str, Any]:
        return {
            "code": self.code,
            "title": code_title(self.code),
            "what_happened": self.message,
            "distributor": self.db,
            "slide_block": self.block,
            "file": self.path,
            "we_expected": self.expected,
            "we_found": self.found,
            "what_to_do": code_fix(self.code),
            "detail": self.detail,
            "when": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        }

    def gpt_block(self) -> str:
        """A short block someone can paste straight into GPT together with TROUBLESHOOTING.md."""
        d = self.as_dict()
        lines = [
            "--- ISZE deck generator error (paste this to GPT) ---",
            f"code: {d['code']}  ({d['title']})",
            f"what happened: {d['what_happened']}",
        ]
        for key, label in (
            ("distributor", "distributor"),
            ("slide_block", "slide block"),
            ("file", "file"),
            ("we_expected", "we expected"),
            ("we_found", "we found"),
            ("detail", "detail"),
        ):
            if d.get(key):
                lines.append(f"{label}: {d[key]}")
        lines += [
            f"what to do: {d['what_to_do']}",
            f"when: {d['when']}",
            "--- end ---",
        ]
        return "\n".join(lines)

    def pretty(self) -> str:
        d = self.as_dict()
        out = [
            "",
            "=" * 78,
            f"  STOPPED  [{d['code']}]  {d['title']}",
            "=" * 78,
            f"  {d['what_happened']}",
        ]
        if d.get("distributor"):
            out.append(f"  Distributor : {d['distributor']}")
        if d.get("slide_block"):
            out.append(f"  Slide block : {d['slide_block']}")
        if d.get("file"):
            out.append(f"  File        : {d['file']}")
        if d.get("we_expected"):
            out.append(f"  Expected    : {d['we_expected']}")
        if d.get("we_found"):
            out.append(f"  Found       : {d['we_found']}")
        if d.get("detail"):
            out.append(f"  Detail      : {d['detail']}")
        out += [
            "",
            f"  WHAT TO DO  : {d['what_to_do']}",
            "",
            "  If that does not fix it, send this whole block to GPT:",
            "",
        ]
        out += ["    " + ln for ln in self.gpt_block().splitlines()]
        out += ["", "=" * 78, ""]
        return "\n".join(out)


class BprWarn:
    """A non-fatal problem worth printing. Collected by the run log."""

    def __init__(self, message: str, *, path: str | Path | None = None, detail: str | None = None) -> None:
        self.message = message
        self.path = str(path) if path is not None else None
        self.detail = detail

    def pretty(self) -> str:
        tail = f"  [{self.path}]" if self.path else ""
        return f"  NOTE  {self.message}{tail}"

    def as_dict(self) -> dict[str, Any]:
        return {"message": self.message, "path": self.path, "detail": self.detail}


def write_error_log(err: BprError, log_dir: Path) -> Path | None:
    """Write _logs/last_error.json next to the output. Never raises."""
    try:
        log_dir.mkdir(parents=True, exist_ok=True)
        payload = err.as_dict()
        payload["environment"] = {
            "python": sys.version.split()[0],
            "platform": platform.platform(),
        }
        target = log_dir / "last_error.json"
        with target.open("w", encoding="utf-8") as fh:
            json.dump(payload, fh, indent=2, ensure_ascii=False)
        return target
    except Exception:
        return None


def write_run_log(
    log_dir: Path,
    *,
    argv: list[str],
    answers: dict[str, Any] | None,
    warnings: list[BprWarn] | None,
    result: str,
    error: BprError | None = None,
    outputs: list[Path] | None = None,
) -> Path | None:
    """One file per run under _logs/. Kept so a colleague can send it. Never raises."""
    try:
        log_dir.mkdir(parents=True, exist_ok=True)
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        target = log_dir / f"run_{stamp}.txt"
        lines = [
            f"ISZE BPR deck generator - run log",
            f"started/ended: {datetime.now().isoformat(timespec='seconds')}",
            f"result: {result}",
            f"command: {' '.join(argv)}",
            "",
            "answers used:",
        ]
        for k, v in (answers or {}).items():
            lines.append(f"  {k}: {v}")
        lines.append("")
        lines.append("notes:")
        for w in (warnings or []):
            lines.append(w.pretty())
        if not warnings:
            lines.append("  (none)")
        lines.append("")
        lines.append("written:")
        for p in (outputs or []):
            lines.append(f"  {p}")
        if error is not None:
            lines += ["", error.pretty()]
        with target.open("w", encoding="utf-8") as fh:
            fh.write("\n".join(lines))
        return target
    except Exception:
        return None


def install_traceback_guard(log_dir: Path, db: str | None = None, block: str | None = None) -> None:
    """Turn an unexpected Python error into a code E501 message instead of a raw traceback.

    Only unexpected errors go through here. A BprError is already explained.
    """
    def _hook(exc_type, exc_value, exc_tb):
        if isinstance(exc_value, BprError):
            err = exc_value
        else:
            last = traceback.extract_tb(exc_tb)[-1] if exc_tb else None
            where = f"{last.filename}:{last.lineno} in {last.name}" if last else "unknown place"
            err = BprError(
                "E501",
                f"The tool stopped on an unexpected problem: {exc_type.__name__}: {exc_value}",
                db=db,
                block=block,
                found=where,
                detail="".join(traceback.format_exception(exc_type, exc_value, exc_tb))[-1500:],
            )
        write_error_log(err, log_dir)
        print(err.pretty(), file=sys.stderr)
        raise SystemExit(1)

    sys.excepthook = _hook

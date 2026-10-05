"""Freshness check: is a derived file older than the input it is built from?

Added 2026-09-22, after a real miss. The main verifier reads a file's *contents*, so a file that is
internally consistent and two months behind its own input passes every check it has. That is what
happened to the tonnage layer: built on 19 Sep from a declared source, the source rewritten on
21 Sep, and a green pipeline said nothing while a page rebuilt on 21 Sep consumed the stale layer.

The pairs come from `verification_fixtures.yaml` -> `freshness:`. Each pair names one derived file
and the inputs it is built from. A derived file older than a declared input is a **warn**, not a
fail: some staleness is deliberate (the lost-sales cut-off is frozen on purpose), and a hard fail
would block the whole pipeline for a monthly refresh. What matters is that it is *visible*.

Nothing else in the pipeline sees this, so absence of a warn is the only signal it is current.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any, Callable

GRACE_SECONDS = 120  # a build that writes within the same couple of minutes is not stale


def _mtime(p: Path) -> float | None:
    try:
        return p.stat().st_mtime
    except OSError:
        return None


def evaluate(pairs: list[dict[str, Any]], derived_dir: Path) -> tuple[list[str], int]:
    """Return (stale descriptions, inputs checked). Pure - no report object, so it is testable."""
    stale: list[str] = []
    checked = 0
    for pair in pairs:
        out = derived_dir / pair["derived"]
        inputs = [derived_dir / i for i in pair.get("inputs", [])]
        inputs += [Path(p) for p in pair.get("inputs_abs", [])]
        out_m = _mtime(out)
        if out_m is None:
            continue
        for src in inputs:
            src_m = _mtime(src)
            if src_m is None:
                continue
            checked += 1
            if src_m > out_m + GRACE_SECONDS:
                days = (src_m - out_m) / 86400.0
                stale.append(
                    f"{pair['derived']} is {days:.1f} day(s) older than {src.name}"
                    f" (rebuild with {pair.get('built_by', '?')})"
                )
    return stale, checked


def check(report: Any, fx: dict[str, Any], derived_dir: Path, chk: Callable[..., None]) -> None:
    pairs = ((fx or {}).get("freshness") or {}).get("pairs") or []
    if not pairs:
        return
    stale, checked = evaluate(pairs, derived_dir)
    if not stale:
        chk(
            report,
            "freshness.no_stale_derived",
            True,
            f"{checked} declared input(s) checked; every derived file is at least as new as its input",
        )
    else:
        shown = "; ".join(stale[:6]) + (f" (+{len(stale) - 6} more)" if len(stale) > 6 else "")
        chk(
            report,
            "freshness.no_stale_derived",
            False,
            f"{len(stale)} derived file(s) sit behind their own input: {shown}",
            warn=True,
            stale=stale,
            inputs_checked=checked,
        )

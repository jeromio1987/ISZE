"""Unit tests for _shared.paths V3 workbook resolution (tmp dirs only)."""

from __future__ import annotations

import inspect
from pathlib import Path

import pytest

from _shared import paths as paths_module
from _shared.paths import (
    V3_FILENAME,
    _v3_workbook_candidates,
    resolve_first_existing,
    resolve_v3_workbook,
)


def _touch(path: Path, content: str = "stub") -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return path


@pytest.fixture
def isze_root(tmp_path: Path) -> Path:
    """Synthetic ISZE root using numbered folders from paths.yaml."""
    root = tmp_path / "isze"
    root.mkdir()
    return root


def test_v3_candidates_deterministic_order(isze_root: Path) -> None:
    candidates = _v3_workbook_candidates(isze_root)
    assert len(candidates) == 7
    assert candidates[0] == isze_root / "04_tools" / "autodoc_scraper" / V3_FILENAME
    assert candidates[1] == (
        isze_root / "04_tools" / "autodoc_scraper" / "_HANDOFF_BUNDLE" / V3_FILENAME
    )
    assert candidates[2] == isze_root / "01_data" / "models" / V3_FILENAME


def test_resolve_first_existing_picks_first_in_order(isze_root: Path) -> None:
    bundle = _touch(
        isze_root / "04_tools" / "autodoc_scraper" / "_HANDOFF_BUNDLE" / V3_FILENAME,
        "bundle",
    )
    models = _touch(isze_root / "01_data" / "models" / V3_FILENAME, "models")
    chosen = resolve_first_existing(_v3_workbook_candidates(isze_root))
    assert chosen == bundle.resolve()
    assert chosen != models.resolve()


def test_prefers_primary_scraper_over_handoff(isze_root: Path) -> None:
    primary = _touch(
        isze_root / "04_tools" / "autodoc_scraper" / V3_FILENAME,
        "primary",
    )
    _touch(
        isze_root / "04_tools" / "autodoc_scraper" / "_HANDOFF_BUNDLE" / V3_FILENAME,
        "bundle",
    )
    chosen = resolve_first_existing(_v3_workbook_candidates(isze_root))
    assert chosen == primary.resolve()


def test_falls_back_to_handoff_when_primary_missing(isze_root: Path) -> None:
    bundle = _touch(
        isze_root / "04_tools" / "autodoc_scraper" / "_HANDOFF_BUNDLE" / V3_FILENAME,
        "bundle",
    )
    chosen = resolve_first_existing(_v3_workbook_candidates(isze_root))
    assert chosen == bundle.resolve()


def test_falls_back_to_data_models_when_scraper_paths_missing(isze_root: Path) -> None:
    models = _touch(isze_root / "01_data" / "models" / V3_FILENAME, "models")
    chosen = resolve_first_existing(_v3_workbook_candidates(isze_root))
    assert chosen == models.resolve()


def test_returns_none_when_no_candidate_exists(isze_root: Path) -> None:
    assert resolve_first_existing(_v3_workbook_candidates(isze_root)) is None


def test_resolve_v3_workbook_via_monkeypatch(isze_root: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    primary = _touch(
        isze_root / "04_tools" / "autodoc_scraper" / V3_FILENAME,
        "primary",
    )

    def _candidates(root: Path | None = None) -> list[Path]:
        return _v3_workbook_candidates(isze_root if root is None else root)

    monkeypatch.setattr(paths_module, "_v3_workbook_candidates", _candidates)
    assert resolve_v3_workbook() == primary.resolve()


def test_no_os_walk_in_resolution_helpers() -> None:
    for fn in (resolve_v3_workbook, resolve_first_existing, _v3_workbook_candidates):
        source = inspect.getsource(fn)
        assert "os.walk" not in source
        assert "rglob" not in source
        assert "glob(" not in source

"""Theme colours, loaded from themes.yaml.

One place for the palette, so a slide never carries its own hex codes.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import yaml

from ..errors import BprError

_THEMES = Path(__file__).resolve().parent / "themes.yaml"
_CACHE: dict[str, "Palette"] = {}


@dataclass(frozen=True)
class Palette:
    name: str
    label: str
    note: str
    bg: str
    panel: str
    row2: str
    border: str
    rule: str
    ink: str
    muted: str
    faint: str
    grid: str
    header_fill: str
    on_header: str
    accent: str
    amber: str
    green: str
    grey: str
    on_accent: str
    logo: str
    font: str

    @property
    def is_dark(self) -> bool:
        return self.name == "charcoal"


def _load_all() -> dict[str, dict]:
    with _THEMES.open(encoding="utf-8") as fh:
        return yaml.safe_load(fh) or {}


def available() -> list[str]:
    return sorted(_load_all().keys())


def get(name: str) -> Palette:
    if name in _CACHE:
        return _CACHE[name]
    raw = _load_all()
    if name not in raw:
        raise BprError(
            "E101",
            f"Theme '{name}' is not defined.",
            expected=", ".join(sorted(raw.keys())),
            found=name,
        )
    data = dict(raw[name])
    data.setdefault("name", name)
    for key in ("label", "note", "bg", "panel", "row2", "border", "rule", "ink", "muted",
                "faint", "grid", "header_fill", "on_header", "accent", "amber", "green",
                "grey", "on_accent", "logo", "font"):
        data.setdefault(key, "")
    palette = Palette(**{k: data[k] for k in Palette.__dataclass_fields__})
    _CACHE[name] = palette
    return palette

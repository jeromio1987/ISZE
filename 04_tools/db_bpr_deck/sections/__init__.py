"""Slide blocks. Each module exposes render(deck, ctx) -> list of slides."""
from __future__ import annotations

from . import analysis, core, prose

MODULES = {
    "exec": core.render_exec,
    "plan": core.render_plan,
    "s2d": core.render_s2d,
    "avail": core.render_avail,
    "s2d_units": analysis.render_s2d_units,
    "stock": analysis.render_stock,
    "fleet": analysis.render_fleet,
    "gps": analysis.render_gps,
    "pms": analysis.render_pms,
    "mix": analysis.render_mix,
    "prose": prose.render_prose,
}

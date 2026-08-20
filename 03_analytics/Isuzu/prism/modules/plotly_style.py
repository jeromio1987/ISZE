"""Shared Plotly styling for the ISZE PRISM Streamlit app.

Single source of truth for the navy + orange house style. Cosmetic only — this
module never sets width / height / margin / use_container_width; those stay
owned by each page and by the layout/centering work, so styling can be applied
on top without fighting it.
"""

from __future__ import annotations

import plotly.graph_objects as go

# Brand colours
NAVY = "#1B3A6B"
ORANGE = "#E87722"
LIGHT_NEUTRAL = "#D6E4F0"

# Consistent navy -> orange -> blue -> amber sequence.
PALETTE = ["#1B3A6B", "#E87722", "#2C5AA0", "#F4A460", "#4A90D9"]

# Neutrals (gridlines, hover border)
_GRID = "#EEF0F4"

# Shared layout defaults applied by style(). Deliberately keeps only keys that
# never collide with per-figure arguments (a module spreading BASE_LAYOUT
# alongside its own `xaxis=`/`yaxis=`/`legend=` would otherwise raise a
# duplicate-keyword TypeError). Axis grid + legend chrome are applied by style()
# via separate calls instead. Also omits height / width / margin.
BASE_LAYOUT = dict(
    template="plotly_white",
    font=dict(family="Segoe UI, sans-serif", size=12, color="#222222"),
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="#FFFFFF",
    colorway=PALETTE,
    hoverlabel=dict(
        bgcolor="#FFFFFF",
        bordercolor=LIGHT_NEUTRAL,
        font=dict(family="Segoe UI, sans-serif", size=12, color=NAVY),
    ),
)


def style(
    fig: go.Figure,
    title: str | None = None,
    x: str | None = None,
    y: str | None = None,
    legend: bool = True,
) -> go.Figure:
    """Apply ISZE house styling to *fig* and return it.

    Cosmetic only: applies ``BASE_LAYOUT`` (font, backgrounds, colourway,
    hover chrome), a subtle grid on every axis, and unobtrusive legend chrome —
    without touching width / height / margin.

    - ``title`` — rendered left-aligned, bold, navy.
    - ``x`` / ``y`` — axis titles.
    - ``legend=False`` — hides the legend (single-series charts).
    """
    fig.update_layout(**BASE_LAYOUT)
    fig.update_xaxes(gridcolor=_GRID, zeroline=False)
    fig.update_yaxes(gridcolor=_GRID, zeroline=False)
    fig.update_layout(
        legend=dict(
            bgcolor="rgba(0,0,0,0)",
            bordercolor="rgba(0,0,0,0)",
            font=dict(size=11, color="#222222"),
        )
    )
    if title is not None:
        fig.update_layout(
            title=dict(
                text=title,
                x=0.0,
                xanchor="left",
                font=dict(family="Segoe UI, sans-serif", size=16, color=NAVY),
            )
        )
    if x is not None:
        fig.update_xaxes(title_text=x)
    if y is not None:
        fig.update_yaxes(title_text=y)
    if legend is False:
        fig.update_layout(showlegend=False)
    return fig

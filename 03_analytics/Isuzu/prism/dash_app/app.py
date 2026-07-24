#!/usr/bin/env python3
"""
PRISM Offset Insights — Dash app.

  python dash_app/app.py   ->  http://127.0.0.1:8050

Uses the same modules/advanced_visuals.py figures as Streamlit and Quarto.
"""
from __future__ import annotations

import sys
from pathlib import Path

PRISM_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PRISM_ROOT))

import pandas as pd
from dash import Dash, dcc, html, Input, Output

from config import DERIVED_DIR
from modules import advanced_visuals as av

DISTS = sorted(
    pd.read_csv(DERIVED_DIR / "gps_spu_by_distributor.csv")["distributor_code"]
    .dropna().unique().tolist()
)
DEFAULT = "ITUK" if "ITUK" in DISTS else DISTS[0]

app = Dash(__name__, title="PRISM Offset Insights")

app.layout = html.Div(style={"fontFamily": "Segoe UI, sans-serif", "background": "#F4F6F9"}, children=[
    html.Div(style={"background": "linear-gradient(120deg,#1B3A6B,#2C5AA0 60%,#E87722)",
                    "color": "#fff", "padding": "1.5rem 2rem"},
             children=[html.H1("PRISM — Offset Insights", style={"margin": 0}),
                       html.P("Six cross-data visuals · all figures from real sales_fact",
                              style={"margin": "0.3rem 0 0", "color": "#E8F0FA"})]),
    html.Div(style={"maxWidth": "1100px", "margin": "1rem auto", "padding": "0 1rem"}, children=[
        html.Label("Highlight distributor"),
        dcc.Dropdown(DISTS, DEFAULT, id="dist", clearable=False, style={"maxWidth": "320px"}),
        html.P("⚠️ Sankey 'Leakage' leg is an INFERENCE (under-service gap), not a measured "
               "competitor figure — internal use only.", style={"color": "#C62828", "fontSize": ".85rem"}),
        dcc.Graph(id="g1"), dcc.Graph(id="g2"), dcc.Graph(id="g3"),
        dcc.Graph(id="g4"), dcc.Graph(id="g5"), dcc.Graph(id="g6"),
        dcc.Graph(id="g7"),
        html.H2("Tender / R&M opportunity pipeline", style={"marginTop": "2rem"}),
        html.P("Qualified-pipeline view (counts + scores). Value present on only 12 of 520 "
               "opportunities — no € pipeline shown.", style={"color": "#555", "fontSize": ".85rem"}),
        dcc.Graph(id="g8"), dcc.Graph(id="g9"), dcc.Graph(id="g10"), dcc.Graph(id="g11"),
    ]),
])


@app.callback(
    Output("g1", "figure"), Output("g2", "figure"), Output("g3", "figure"),
    Output("g4", "figure"), Output("g5", "figure"), Output("g6", "figure"),
    Output("g7", "figure"), Output("g8", "figure"), Output("g9", "figure"),
    Output("g10", "figure"), Output("g11", "figure"),
    Input("dist", "value"),
)
def _update(hl):
    return (
        av.fig_trajectory_quiver(DERIVED_DIR, hl),
        av.fig_lumpiness_airfreight(DERIVED_DIR),
        av.fig_demand_flow_sankey(DERIVED_DIR),
        av.fig_vor_pricing_power(DERIVED_DIR, hl),
        av.fig_premium_defection(DERIVED_DIR, hl),
        av.fig_capture_ceiling(DERIVED_DIR, hl),
        av.fig_db_parts_mix(DERIVED_DIR, hl),
        av.fig_tender_funnel(DERIVED_DIR),
        av.fig_tender_country(DERIVED_DIR),
        av.fig_tender_owner(DERIVED_DIR),
        av.fig_tender_scatter(DERIVED_DIR),
    )


if __name__ == "__main__":
    app.run(debug=False, port=8050)

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import numpy as np
from io import StringIO

st.set_page_config(page_title="Opportunity Radar · ISZE", layout="wide", page_icon="🎯")

# ──────────────────────────────────────────────────────────────────────────────
# Constants
# ──────────────────────────────────────────────────────────────────────────────
COMP_TARGET = 20.0  # BP target for competitive parts share %

QUADRANT_COLORS = {
    "Stars":    "#00B050",
    "Priority": "#FF4444",
    "Growing":  "#5B9BD5",
    "Monitor":  "#A0A0A0",
}

# PLACEHOLDER DATA — replace by uploading real CSV export from Power BI
SAMPLE_DATA = [
    {"Customer": "Distributor A", "Revenue_L12": 800000, "Comp_Revenue_L12":  96000, "Revenue_PY": 700000},
    {"Customer": "Distributor B", "Revenue_L12": 500000, "Comp_Revenue_L12":  45000, "Revenue_PY": 430000},
    {"Customer": "Distributor C", "Revenue_L12": 270000, "Comp_Revenue_L12":  21600, "Revenue_PY": 260000},
    {"Customer": "Distributor D", "Revenue_L12": 210000, "Comp_Revenue_L12":  16800, "Revenue_PY": 280000},
    {"Customer": "Distributor E", "Revenue_L12": 195000, "Comp_Revenue_L12":  46800, "Revenue_PY": 160000},
    {"Customer": "Distributor F", "Revenue_L12": 130000, "Comp_Revenue_L12":  24700, "Revenue_PY": 110000},
    {"Customer": "Distributor G", "Revenue_L12": 125000, "Comp_Revenue_L12":  11250, "Revenue_PY": 165000},
    {"Customer": "Distributor H", "Revenue_L12":  95000, "Comp_Revenue_L12":  18050, "Revenue_PY":  70000},
    {"Customer": "Distributor I", "Revenue_L12":  85000, "Comp_Revenue_L12":   6800, "Revenue_PY": 110000},
    {"Customer": "Distributor J", "Revenue_L12":  40000, "Comp_Revenue_L12":   8800, "Revenue_PY":  34000},
]

# ──────────────────────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────────────────────
def fmt_eur(v: float) -> str:
    return f"€{v:,.0f}"


def compute_df(raw: pd.DataFrame) -> pd.DataFrame:
    df = raw.copy()
    df["Comp_Share_Pct"] = df["Comp_Revenue_L12"] / df["Revenue_L12"] * 100
    has_py = "Revenue_PY" in df.columns
    if has_py:
        df["YoY_Growth_Pct"] = np.where(
            df["Revenue_PY"] > 0,
            (df["Revenue_L12"] - df["Revenue_PY"]) / df["Revenue_PY"] * 100,
            np.nan,
        )
    else:
        df["YoY_Growth_Pct"] = np.nan
    return df


def assign_quadrant(row, avg_revenue: float) -> str:
    high_rev  = row["Revenue_L12"]   >= avg_revenue
    high_comp = row["Comp_Share_Pct"] >= COMP_TARGET
    if   high_rev and     high_comp: return "Stars"
    elif high_rev and not high_comp: return "Priority"
    elif not high_rev and high_comp: return "Growing"
    else:                            return "Monitor"


def bubble_size(yoy: float) -> float:
    if np.isnan(yoy):
        return 14
    return min(max(abs(yoy) * 0.8, 12), 40)


# ──────────────────────────────────────────────────────────────────────────────
# Sidebar
# ──────────────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.header("Controls")

    data_source = st.radio("Data source", ["Sample Data", "Upload CSV"], index=0)

    period_label = st.text_input("Period label", value="Rolling 12 Months")

    show_labels = st.toggle("Show customer labels", value=True)

    st.markdown("---")
    st.caption("CSV columns required: `Customer`, `Revenue_L12`, `Comp_Revenue_L12`  \nOptional: `Revenue_PY`")

# ──────────────────────────────────────────────────────────────────────────────
# Data loading
# ──────────────────────────────────────────────────────────────────────────────
df_raw = None

if data_source == "Sample Data":
    df_raw = pd.DataFrame(SAMPLE_DATA)
else:
    uploaded = st.file_uploader("Upload CSV", type=["csv"])
    if uploaded is not None:
        try:
            df_raw = pd.read_csv(uploaded)
            required = {"Customer", "Revenue_L12", "Comp_Revenue_L12"}
            missing = required - set(df_raw.columns)
            if missing:
                st.error(f"Missing columns: {', '.join(missing)}")
                df_raw = None
        except Exception as exc:
            st.error(f"Could not parse CSV: {exc}")
            df_raw = None
    else:
        st.info("Upload a CSV file, or switch to Sample Data in the sidebar.")

# ──────────────────────────────────────────────────────────────────────────────
# Main content
# ──────────────────────────────────────────────────────────────────────────────
st.title("Opportunity Radar — Competitive Parts")
st.caption(f"Period: {period_label}")

if df_raw is None:
    st.stop()

df = compute_df(df_raw)
avg_revenue = df["Revenue_L12"].mean()
df["Quadrant"] = df.apply(assign_quadrant, axis=1, avg_revenue=avg_revenue)
df["Bubble_Size"] = df["YoY_Growth_Pct"].apply(bubble_size)
df["Color"] = df["Quadrant"].map(QUADRANT_COLORS)

# ──────────────────────────────────────────────────────────────────────────────
# KPI row
# ──────────────────────────────────────────────────────────────────────────────
st.markdown("---")
k1, k2, k3, k4 = st.columns(4)

total_customers   = len(df)
avg_comp_share    = df["Comp_Share_Pct"].mean()
above_target      = (df["Comp_Share_Pct"] >= COMP_TARGET).sum()
total_revenue_l12 = df["Revenue_L12"].sum()

k1.metric("Customers",          total_customers)
k2.metric("Avg Comp Share",     f"{avg_comp_share:.1f}%")
k3.metric(f"Above {COMP_TARGET:.0f}% Target", f"{above_target} / {total_customers}")
k4.metric("Total Revenue L12",  fmt_eur(total_revenue_l12))

st.markdown("---")

# ──────────────────────────────────────────────────────────────────────────────
# Scatter chart
# ──────────────────────────────────────────────────────────────────────────────
fig = go.Figure()

# One trace per quadrant for clean legend
for quadrant, color in QUADRANT_COLORS.items():
    sub = df[df["Quadrant"] == quadrant]
    if sub.empty:
        continue

    hover_texts = []
    for _, row in sub.iterrows():
        yoy_str = f"{row['YoY_Growth_Pct']:+.1f}%" if not np.isnan(row["YoY_Growth_Pct"]) else "n/a"
        hover_texts.append(
            f"<b>{row['Customer']}</b><br>"
            f"Revenue L12: {fmt_eur(row['Revenue_L12'])}<br>"
            f"Comp Share: {row['Comp_Share_Pct']:.1f}%<br>"
            f"YoY Growth: {yoy_str}"
        )

    fig.add_trace(go.Scatter(
        x=sub["Revenue_L12"],
        y=sub["Comp_Share_Pct"],
        mode="markers+text" if show_labels else "markers",
        name=quadrant,
        text=sub["Customer"] if show_labels else None,
        textposition="top center",
        textfont=dict(color="white", size=11),
        hovertext=hover_texts,
        hoverinfo="text",
        marker=dict(
            size=sub["Bubble_Size"],
            color=color,
            line=dict(color="white", width=1),
            opacity=0.90,
        ),
    ))

# Reference lines
fig.add_hline(
    y=COMP_TARGET,
    line=dict(color="#FF6B6B", dash="dash", width=1.5),
    annotation_text=f"{COMP_TARGET:.0f}% BP Target",
    annotation_font_color="#FF6B6B",
    annotation_position="top right",
)
fig.add_vline(
    x=avg_revenue,
    line=dict(color="#888888", dash="dash", width=1.5),
    annotation_text="Avg Revenue",
    annotation_font_color="#888888",
    annotation_position="top left",
)

# Quadrant label annotations
x_min  = df["Revenue_L12"].min()
x_max  = df["Revenue_L12"].max()
x_pad  = (x_max - x_min) * 0.04
y_high = min(df["Comp_Share_Pct"].max() + 8, 95)
y_low  = max(df["Comp_Share_Pct"].min() - 8,  2)

quadrant_annotations = [
    dict(x=x_max - x_pad, y=y_high, text="Stars",    xanchor="right", yanchor="top",    font_color=QUADRANT_COLORS["Stars"]),
    dict(x=x_max - x_pad, y=y_low,  text="Priority", xanchor="right", yanchor="bottom", font_color=QUADRANT_COLORS["Priority"]),
    dict(x=x_min + x_pad, y=y_high, text="Growing",  xanchor="left",  yanchor="top",    font_color=QUADRANT_COLORS["Growing"]),
    dict(x=x_min + x_pad, y=y_low,  text="Monitor",  xanchor="left",  yanchor="bottom", font_color=QUADRANT_COLORS["Monitor"]),
]

for ann in quadrant_annotations:
    fig.add_annotation(
        x=ann["x"], y=ann["y"],
        text=f"<b>{ann['text']}</b>",
        showarrow=False,
        font=dict(size=13, color=ann["font_color"]),
        xanchor=ann["xanchor"],
        yanchor=ann["yanchor"],
        opacity=0.6,
    )

fig.update_layout(
    height=600,
    plot_bgcolor="#1a1a2e",
    paper_bgcolor="#16213e",
    font=dict(color="white"),
    xaxis=dict(
        title=f"Total Revenue L12 (EUR) — {period_label}",
        tickprefix="€",
        tickformat=",.0f",
        gridcolor="#2a2a4e",
        zerolinecolor="#2a2a4e",
    ),
    yaxis=dict(
        title="Competitive Parts Share %",
        ticksuffix="%",
        gridcolor="#2a2a4e",
        zerolinecolor="#2a2a4e",
        range=[0, max(df["Comp_Share_Pct"].max() + 10, COMP_TARGET + 10)],
    ),
    legend=dict(
        bgcolor="rgba(0,0,0,0.4)",
        bordercolor="#444",
        borderwidth=1,
        font=dict(color="white"),
    ),
    margin=dict(l=60, r=40, t=40, b=60),
    hovermode="closest",
)

st.plotly_chart(fig, use_container_width=True)

# ──────────────────────────────────────────────────────────────────────────────
# Summary table
# ──────────────────────────────────────────────────────────────────────────────
st.markdown("---")
st.markdown("### Customer Summary")

table_df = df[["Customer", "Revenue_L12", "Comp_Share_Pct", "YoY_Growth_Pct", "Quadrant"]].copy()
table_df = table_df.sort_values("Revenue_L12", ascending=False).reset_index(drop=True)

# Format display columns
table_df["Revenue L12"]  = table_df["Revenue_L12"].apply(fmt_eur)
table_df["Comp Share %"] = table_df["Comp_Share_Pct"].apply(lambda v: f"{v:.1f}%")
table_df["YoY"]          = table_df["YoY_Growth_Pct"].apply(
    lambda v: f"{v:+.1f}%" if not np.isnan(v) else "—"
)

display_df = table_df[["Customer", "Revenue L12", "Comp Share %", "YoY", "Quadrant"]].copy()

st.dataframe(display_df, use_container_width=True, hide_index=True)

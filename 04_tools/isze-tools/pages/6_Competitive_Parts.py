import datetime
import streamlit as st
import pandas as pd
import plotly.graph_objects as go

st.set_page_config(
    page_title="Competitive Parts Catalog · ISZE",
    layout="wide",
    page_icon="🔩",
)

# ──────────────────────────────────────────────────────────────────────────────
# Constants
# ──────────────────────────────────────────────────────────────────────────────
DATA_FILE  = r"C:\Users\jerom\Desktop\claude\ISZJ master data competitive parts.xlsx"
# Canonical sales source = the verified pipeline parquet (DI-9 fix, 2026-08-20).
# The legacy TSV (sales_detailed_for_claude_full_fixed.tsv) is stale/dead and
# predates the CR/RE exclusion + fig_key + more-complete CY2025 rebuild.
SALES_FILE = r"C:\Users\jerom\Desktop\claude\ISZE\01_data\00_derived\sales_fact.parquet"

PLOT_BG   = "#1a1a2e"
PAPER_BG  = "#16213e"
FONT_CLR  = "#ffffff"
BAR_CLR   = "#5B9BD5"


# ──────────────────────────────────────────────────────────────────────────────
# Data loading
# ──────────────────────────────────────────────────────────────────────────────
@st.cache_data
def load_data() -> pd.DataFrame:
    df = pd.read_excel(DATA_FILE, dtype={"Parts No": object, "New Pno": object})

    # Drop rows with null or @@@@ Part Names
    df = df[df["Parts Name"].notna()]
    df = df[~df["Parts Name"].astype(str).str.contains("@@@@", na=False)]

    # Normalise part number columns to clean integer strings (no .0, no sci notation)
    for col in ("Parts No", "New Pno"):
        if col in df.columns:
            def _to_str(v):
                if pd.isna(v):
                    return ""
                try:
                    return str(int(float(str(v))))
                except (ValueError, OverflowError):
                    return str(v).strip()
            df[col] = df[col].apply(_to_str)

    # Ensure numeric price column
    df["OSea Price"] = pd.to_numeric(df["OSea Price"], errors="coerce").fillna(0.0)

    return df


@st.cache_data
def load_sales() -> pd.DataFrame:
    df = pd.read_parquet(SALES_FILE)
    df["billing_date"] = pd.to_datetime(df["billing_date"], errors="coerce")

    # Normalise part_number to clean integer string — same logic as load_data
    def _norm_pno(v):
        if pd.isna(v):
            return ""
        try:
            return str(int(float(str(v))))
        except (ValueError, OverflowError):
            return str(v).strip()

    df["part_number"] = df["part_number"].apply(_norm_pno)
    # sold_to arrives stringified ('2194.0') in the parquet — clean for display/grouping
    df["sold_to"] = df["sold_to"].astype(str).str.replace(r"\.0$", "", regex=True)
    return df


@st.cache_data
def resolve_newest(df: pd.DataFrame) -> pd.DataFrame:
    """
    For each unique New Pno, keep ONE canonical row:
      - prefer the row where Parts No == New Pno (i.e. the part IS the newest version)
      - otherwise keep the row with the highest OSea Price
    Returns a deduplicated dataframe of current catalog parts.
    """
    result_rows = []

    for new_pno, group in df.groupby("New Pno"):
        exact = group[group["Parts No"] == new_pno]
        if not exact.empty:
            result_rows.append(exact.iloc[0])
        else:
            result_rows.append(group.loc[group["OSea Price"].idxmax()])

    return pd.DataFrame(result_rows).reset_index(drop=True)


@st.cache_data
def compute_comp_share(
    df_parts: pd.DataFrame, df_sales: pd.DataFrame
) -> pd.DataFrame:
    """
    For each distributor (sold_to), compute what share of their total sales
    comes from competitive part numbers.
    """
    # Build the full set of competitive part numbers
    comp_set = set(
        df_parts["Parts No"].dropna().astype(str).str.strip().tolist()
    ) | set(
        df_parts["New Pno"].dropna().astype(str).str.strip().tolist()
    )
    # Remove empty strings that may have crept in
    comp_set.discard("")

    df = df_sales.copy()
    df["is_competitive"] = df["part_number"].isin(comp_set)

    grouped = (
        df.groupby("sold_to")
        .apply(
            lambda g: pd.Series(
                {
                    "total_sales": g["net_sales_value"].sum(),
                    "comp_sales": g.loc[g["is_competitive"], "net_sales_value"].sum(),
                }
            ),
            include_groups=False,
        )
        .reset_index()
    )

    grouped["comp_share_pct"] = (
        grouped["comp_sales"] / grouped["total_sales"].replace(0, float("nan")) * 100
    ).fillna(0.0)

    return grouped.sort_values("total_sales", ascending=False).reset_index(drop=True)


# ──────────────────────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────────────────────
def fmt_jpy(v: float) -> str:
    if v <= 0:
        return "—"
    return f"¥{v:,.0f}"


def fmt_eur(v: float) -> str:
    if v <= 0:
        return "—"
    return f"€{v:,.0f}"


def is_active(row) -> bool:
    val = str(row.get("Activated in IE40", "")).strip()
    return val == "ISZ7"


def is_superseded(row) -> bool:
    return str(row["Parts No"]).strip() != str(row["New Pno"]).strip()


# ──────────────────────────────────────────────────────────────────────────────
# Load raw data
# ──────────────────────────────────────────────────────────────────────────────
try:
    df_raw = load_data()
except Exception as exc:
    st.error(f"Could not load data file: {exc}")
    st.stop()

# ──────────────────────────────────────────────────────────────────────────────
# Sidebar controls
# ──────────────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.header("Controls")

    fx_rate = st.number_input(
        "JPY / EUR rate",
        min_value=1.0,
        max_value=500.0,
        value=160.0,
        step=0.5,
        format="%.1f",
        help="Divide OSea Price (JPY) by this to get EUR price",
    )

    active_only = st.toggle("Active parts only (ISZ7)", value=True)
    priced_only = st.toggle("Priced parts only (OSea Price > 0)", value=True)
    show_superseded = st.toggle("Show superseded parts", value=False)

    st.markdown("---")

    period_range = st.date_input(
        "Sales period",
        value=(datetime.date(2025, 1, 1), datetime.date(2025, 12, 31)),
        format="DD/MM/YYYY",
    )

    st.markdown("---")

    name_search = st.text_input("Search Part Name", placeholder="e.g. filter, pump…")

    all_origins = sorted(df_raw["Origin"].dropna().unique().tolist())
    origin_filter = st.multiselect("Origin", options=all_origins, default=[])

    st.markdown("---")

    show_comp_share = st.toggle("Show Comp Share section", value=True)


# ──────────────────────────────────────────────────────────────────────────────
# Title
# ──────────────────────────────────────────────────────────────────────────────
st.title("Competitive Parts Catalog · ISZE")

# ──────────────────────────────────────────────────────────────────────────────
# NEW SECTION: Competitive Share by Distributor
# ──────────────────────────────────────────────────────────────────────────────
if show_comp_share:
    df_sales_raw = None
    sales_load_ok = False

    try:
        df_sales_raw = load_sales()
        sales_load_ok = True
    except Exception as exc:
        st.warning(f"Could not load sales file — Comp Share section skipped: {exc}")

    if sales_load_ok and df_sales_raw is not None:
        try:
            # Apply period filter before computing comp share
            df_sales_filtered = df_sales_raw.copy()
            if isinstance(period_range, (list, tuple)) and len(period_range) == 2:
                start, end = period_range
                df_sales_filtered = df_sales_filtered[
                    (df_sales_filtered["billing_date"] >= pd.Timestamp(start)) &
                    (df_sales_filtered["billing_date"] <= pd.Timestamp(end))
                ]

            df_comp_share = compute_comp_share(df_raw, df_sales_filtered)

            st.subheader("Competitive Share by Distributor")

            col_chart, col_table = st.columns([0.6, 0.4])

            with col_chart:
                # Assign bar color based on comp_share_pct thresholds
                bar_colors = []
                for pct in df_comp_share["comp_share_pct"]:
                    if pct >= 20:
                        bar_colors.append("#00B050")
                    elif pct >= 10:
                        bar_colors.append("#ED7D31")
                    else:
                        bar_colors.append("#FF4444")

                # Sort descending so highest share is at top of horizontal chart
                chart_df = df_comp_share.sort_values(
                    "comp_share_pct", ascending=True  # ascending=True → highest at top in horizontal bar
                )
                chart_colors = []
                for pct in chart_df["comp_share_pct"]:
                    if pct >= 20:
                        chart_colors.append("#00B050")
                    elif pct >= 10:
                        chart_colors.append("#ED7D31")
                    else:
                        chart_colors.append("#FF4444")

                x_max = chart_df["comp_share_pct"].max() + 5 if not chart_df.empty else 25

                fig_share = go.Figure()

                fig_share.add_trace(
                    go.Bar(
                        x=chart_df["comp_share_pct"].tolist(),
                        y=chart_df["sold_to"].tolist(),
                        orientation="h",
                        marker_color=chart_colors,
                        text=[f"{v:.1f}%" for v in chart_df["comp_share_pct"].tolist()],
                        textposition="outside",
                        textfont=dict(color=FONT_CLR, size=11),
                        cliponaxis=False,
                    )
                )

                # Vertical reference line at 20%
                fig_share.add_shape(
                    type="line",
                    x0=20,
                    x1=20,
                    y0=-0.5,
                    y1=len(chart_df) - 0.5,
                    line=dict(color="#FF4444", width=2, dash="dash"),
                )

                fig_share.add_annotation(
                    x=20,
                    y=len(chart_df) - 0.5,
                    text="20% BP Target",
                    showarrow=False,
                    xanchor="left",
                    font=dict(color="#FF4444", size=11),
                    yshift=8,
                )

                fig_share.update_layout(
                    plot_bgcolor=PLOT_BG,
                    paper_bgcolor=PAPER_BG,
                    font=dict(color=FONT_CLR),
                    xaxis=dict(
                        range=[0, x_max],
                        ticksuffix="%",
                        gridcolor="#2a2a4a",
                        title="Competitive Share",
                    ),
                    yaxis=dict(
                        tickfont=dict(size=11),
                        automargin=True,
                    ),
                    margin=dict(l=20, r=80, t=30, b=40),
                    height=400,
                    showlegend=False,
                )

                st.plotly_chart(fig_share, use_container_width=True)

            with col_table:
                table_df = df_comp_share[
                    ["sold_to", "total_sales", "comp_sales", "comp_share_pct"]
                ].copy()

                table_df["total_sales_fmt"] = table_df["total_sales"].apply(
                    lambda v: f"€{v:,.0f}" if v > 0 else "—"
                )
                table_df["comp_sales_fmt"] = table_df["comp_sales"].apply(
                    lambda v: f"€{v:,.0f}" if v > 0 else "—"
                )
                table_df["comp_share_fmt"] = table_df["comp_share_pct"].apply(
                    lambda v: f"{v:.1f}%"
                )

                table_display = table_df[
                    ["sold_to", "total_sales_fmt", "comp_sales_fmt", "comp_share_fmt"]
                ].rename(
                    columns={
                        "sold_to": "Distributor",
                        "total_sales_fmt": "Total Sales (EUR)",
                        "comp_sales_fmt": "Comp Sales (EUR)",
                        "comp_share_fmt": "Comp Share %",
                    }
                )

                st.dataframe(table_display, use_container_width=True, hide_index=True)

            period_str = (
                f"{period_range[0].strftime('%d/%m/%Y')} – {period_range[1].strftime('%d/%m/%Y')}"
                if isinstance(period_range, (list, tuple)) and len(period_range) == 2
                else "All dates"
            )
            st.caption(
                f"Period: {period_str} · Source: sales_fact.parquet (verified pipeline) × ISZJ competitive parts catalog"
            )

        except Exception as exc:
            st.warning(f"Could not compute competitive share: {exc}")

st.markdown("---")

# ──────────────────────────────────────────────────────────────────────────────
# Compute dataset-wide KPIs (before filters, on raw data)
# ──────────────────────────────────────────────────────────────────────────────
total_active_raw = (df_raw["Activated in IE40"].astype(str).str.strip() == "ISZ7").sum()
total_superseded_raw = (
    df_raw["Parts No"].astype(str).str.strip() != df_raw["New Pno"].astype(str).str.strip()
).sum()

# ──────────────────────────────────────────────────────────────────────────────
# Apply filters
# ──────────────────────────────────────────────────────────────────────────────
df_filtered = df_raw.copy()

if active_only:
    df_filtered = df_filtered[
        df_filtered["Activated in IE40"].astype(str).str.strip() == "ISZ7"
    ]

if priced_only:
    df_filtered = df_filtered[df_filtered["OSea Price"] > 0]

if not show_superseded:
    # Keep only rows where Parts No == New Pno (i.e. not superseded)
    df_filtered = df_filtered[
        df_filtered["Parts No"].astype(str).str.strip()
        == df_filtered["New Pno"].astype(str).str.strip()
    ]

if name_search.strip():
    df_filtered = df_filtered[
        df_filtered["Parts Name"].astype(str).str.contains(
            name_search.strip(), case=False, na=False
        )
    ]

if origin_filter:
    df_filtered = df_filtered[df_filtered["Origin"].isin(origin_filter)]

# ──────────────────────────────────────────────────────────────────────────────
# KPI row
# ──────────────────────────────────────────────────────────────────────────────
avg_price_eur = (
    (df_filtered["OSea Price"] / fx_rate).mean()
    if not df_filtered.empty and df_filtered["OSea Price"].sum() > 0
    else 0.0
)

k1, k2, k3, k4 = st.columns(4)
k1.metric("Parts shown",          f"{len(df_filtered):,}")
k2.metric("Active (ISZ7) in full dataset", f"{total_active_raw:,}")
k3.metric("Superseded in full dataset",    f"{total_superseded_raw:,}")
k4.metric("Avg price (EUR)",      fmt_eur(avg_price_eur))

st.markdown("---")

# ──────────────────────────────────────────────────────────────────────────────
# Build display dataframe
# ──────────────────────────────────────────────────────────────────────────────
if df_filtered.empty:
    st.info("No parts match the current filters.")
    st.stop()

display = df_filtered[
    ["Parts No", "New Pno", "Parts Name", "Origin", "OSea Price", "Activated in IE40"]
].copy()

# EUR price column
display["EUR Price"] = display["OSea Price"] / fx_rate

# Active flag
display["Active"] = display["Activated in IE40"].apply(
    lambda v: "✓" if str(v).strip() == "ISZ7" else ""
)

# Superseded flag + New Pno display
display["Superseded"] = display.apply(
    lambda r: "✓" if str(r["Parts No"]).strip() != str(r["New Pno"]).strip() else "",
    axis=1,
)
display["New Pno display"] = display.apply(
    lambda r: r["New Pno"] if str(r["Parts No"]).strip() != str(r["New Pno"]).strip() else "—",
    axis=1,
)

# Formatted price columns
display["OSea Price JPY"] = display["OSea Price"].apply(fmt_jpy)
display["EUR Price fmt"] = display["EUR Price"].apply(fmt_eur)

# Final column selection and rename
df_display = display[[
    "Parts No",
    "New Pno display",
    "Parts Name",
    "Origin",
    "OSea Price JPY",
    "EUR Price fmt",
    "Active",
    "Superseded",
]].rename(columns={
    "New Pno display": "New Pno",
    "OSea Price JPY":  "OSea Price (JPY)",
    "EUR Price fmt":   f"EUR Price (÷{fx_rate:.0f})",
})

st.dataframe(df_display, use_container_width=True, hide_index=True)

st.caption(f"{len(df_filtered):,} parts displayed · FX rate: ¥{fx_rate:.1f} = €1")

# ──────────────────────────────────────────────────────────────────────────────
# Top 20 most expensive parts — horizontal bar chart
# ──────────────────────────────────────────────────────────────────────────────
st.markdown("---")
st.subheader("Top 20 Most Expensive Parts (EUR)")

top20 = (
    display[display["EUR Price"] > 0]
    .nlargest(20, "EUR Price")
    .sort_values("EUR Price")           # ascending so longest bar is at top
)

if top20.empty:
    st.info("No priced parts available for chart.")
else:
    labels = top20.apply(
        lambda r: f"{r['Parts No']}  {str(r['Parts Name'])[:35]}", axis=1
    ).tolist()

    fig = go.Figure(
        go.Bar(
            x=top20["EUR Price"].tolist(),
            y=labels,
            orientation="h",
            marker_color=BAR_CLR,
            text=[f"€{v:,.0f}" for v in top20["EUR Price"].tolist()],
            textposition="outside",
            textfont=dict(color=FONT_CLR, size=11),
        )
    )

    fig.update_layout(
        plot_bgcolor=PLOT_BG,
        paper_bgcolor=PAPER_BG,
        font=dict(color=FONT_CLR),
        xaxis=dict(
            title="EUR Price",
            gridcolor="#2a2a4a",
            tickprefix="€",
            tickformat=",",
        ),
        yaxis=dict(
            tickfont=dict(size=11),
            automargin=True,
        ),
        margin=dict(l=20, r=80, t=30, b=40),
        height=540,
        showlegend=False,
    )

    st.plotly_chart(fig, use_container_width=True)

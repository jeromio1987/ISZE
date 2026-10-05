"""PRISM - Tender / R&M opportunity pipeline (reads the live tender feed)."""

from __future__ import annotations

import sys
from datetime import date
from pathlib import Path

import pandas as pd
import streamlit as st

APP_DIR = Path(__file__).parent.parent
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from config import DERIVED_DIR  # noqa: E402
from modules import advanced_visuals as av  # noqa: E402
from modules.plotly_style import style  # noqa: E402
from modules.tender_feed import (  # noqa: E402
    deadline_on_or_after,
    feed_date_label,
    feed_generated_at,
    feed_path,
    coverage,
    load_feed,
)

SRC = feed_path()


@st.cache_data(show_spinner="Loading tender feed...")
def load(_mtime_ns: int) -> tuple[pd.DataFrame, dict]:
    """Cached per file state, so a rewritten feed is picked up on rerun.

    ``_mtime_ns`` is the cache key: it is hashed by Streamlit, and the leading
    underscore only stops it being forwarded to the loader.
    """
    return load_feed()


st.title("Tender / R&M opportunity pipeline")
st.caption(
    "Scored public-tender opportunities — fleet R&M and parts contracts harvested "
    "from EU/UK notices. Read live from the weekly tender feed."
)

if not SRC.exists():
    st.error(
        f"Tender feed not found: {SRC}\n\n"
        "The PRISM tender page reads the weekly feed written by the ISZE Tender Monitor "
        "task. Restore the file, or run the monitor to write it again."
    )
    st.stop()

try:
    df, meta = load(SRC.stat().st_mtime_ns)
except Exception as exc:  # corrupt or half-written JSON
    st.error(f"Could not read {SRC.name}: {exc}")
    st.stop()

total = len(df)
cov = coverage(df)
feed_date = feed_date_label(meta)
feed_raw = feed_generated_at(meta)

# ── headline: what is in the feed, and how much of it is usable ──────────────
st.caption(f"Feed date: **{feed_date}**  ·  feed written {feed_raw}  ·  {SRC}")
c1, c2, c3, c4 = st.columns(4)
c1.metric("Opportunities", f"{total:,}")
c2.metric("Actionable", f"{int(df['actionable'].sum()):,}",
          help="Decision is Attack, Selective or Watch.")
c3.metric("Carry parts signal", f"{df['parts_signal'].mean():.0%}")
c4.metric("R&M contract", f"{df['rm_contract'].mean():.0%}")

if cov["value"] and cov["deadline"]:
    st.info(
        f"Coverage in this feed: a value is published on **{cov['value']} of {total}** "
        f"opportunities and a deadline on **{cov['deadline']} of {total}** "
        f"({cov['no_deadline']} have no deadline published), while a fleet size appears on "
        f"**{cov['fleet_size']}** and an outcome is recorded on **{cov['outcome']}**. "
        "So this page charts counts and scores, not a € pipeline and not award prices. "
        "A blank means the notice does not state the figure — never that it is zero.",
        icon="⚠️",
    )
if cov["outcome"] == 0:
    st.caption(
        "No outcome is recorded on any opportunity yet, so nothing here can show win/loss "
        "or a realised price."
    )

# ── filters ─────────────────────────────────────────────────────────────────
with st.container(border=True):
    f1, f2, f3 = st.columns([1.2, 1.2, 2.0])
    rm_only = f1.checkbox("R&M contracts only", value=False,
                          help="Keeps only opportunities whose notice covers fleet repair "
                               "and maintenance.")
    dated_only = f2.checkbox("Deadline on or after today", value=False,
                             help="Keeps only opportunities with a published deadline that "
                                  "has not passed. Undated rows are excluded, not assumed open.")
    decisions = f3.multiselect(
        "Decision", av.DECISION_ORDER, default=av.DECISION_ORDER,
    )

view = df[df["decision"].isin(decisions)] if decisions else df
if rm_only:
    view = view[view["rm_contract"]]
if dated_only:
    view = view[deadline_on_or_after(view, date.today())]

flt = []
if rm_only:
    flt.append("R&M contracts only")
if dated_only:
    flt.append("deadline on or after today")
label = " + ".join(flt) if flt else "no filter"
st.markdown(
    f"**{len(view):,} of {total:,} opportunities** shown ({label}). "
    f"Deadlines: {int(view['deadline_dt'].notna().sum()):,} published, "
    f"{int(view['deadline_dt'].isna().sum()):,} not published. "
    f"Values published on {int(view['value_amount'].notna().sum()):,}."
)
if len(view) == 0:
    st.warning(
        "No opportunity matches the filter. Undated notices are dropped by the deadline "
        "toggle, even when they may still be open — clear the toggle to see them."
    )

st.plotly_chart(style(av.fig_tender_funnel(DERIVED_DIR)), width="stretch")
col1, col2 = st.columns(2)
col1.plotly_chart(style(av.fig_tender_country(DERIVED_DIR)), width="stretch")
col2.plotly_chart(style(av.fig_tender_owner(DERIVED_DIR)), width="stretch")
st.plotly_chart(style(av.fig_tender_scatter(DERIVED_DIR)), width="stretch")

# ── action queue ────────────────────────────────────────────────────────────
st.subheader("Action queue — top Attack / Selective opportunities")
queue_cols = ["title", "country", "owner_suggested", "opportunity_score",
              "decision", "deadline_date", "value_amount", "url"]
queue = (
    view[view["decision"].isin(["Attack", "Selective"])]
    .sort_values("opportunity_score", ascending=False)
    .head(20)
)
if queue.empty:
    st.warning("No Attack or Selective opportunity matches the filter.")
else:
    queue = queue[[c for c in queue_cols if c in queue.columns]]
    st.dataframe(
        queue,
        width="stretch",
        hide_index=True,
        column_config={
            "url": st.column_config.LinkColumn("Notice", display_text="Open ↗"),
            "value_amount": st.column_config.NumberColumn("Value (notice)", format="%.0f"),
            "deadline_date": st.column_config.TextColumn("Deadline"),
        },
    )

# ── deadline view ───────────────────────────────────────────────────────────
st.subheader("Closing soonest (published deadlines)")
dated = view[view["deadline_dt"].notna()].sort_values("deadline_dt")
if dated.empty:
    st.warning(
        "No deadline is published on any opportunity in this selection. "
        "The notices do not state a date; they are not closed."
    )
else:
    show = dated.head(20)[["deadline_date", "days_to_deadline", "title", "country",
                           "owner_suggested", "decision", "url"]]
    show = show[[c for c in show.columns if c in dated.columns]]
    st.dataframe(
        show,
        width="stretch",
        hide_index=True,
        column_config={"url": st.column_config.LinkColumn("Notice", display_text="Open ↗")},
    )

with st.expander("Feed details and field coverage"):
    st.write(f"File: `{SRC}`")
    st.write(f"Feed generated at: `{feed_raw}` — shown above as {feed_date}")
    st.dataframe(
        pd.DataFrame(
            [
                {"field": "value_amount", "rows with a value": cov["value"], "of": total},
                {"field": "deadline_date", "rows with a value": cov["deadline"], "of": total},
                {"field": "fleet_size", "rows with a value": cov["fleet_size"], "of": total},
                {"field": "outcome", "rows with a value": cov["outcome"], "of": total},
            ]
        ),
        width="stretch",
        hide_index=True,
    )
    st.caption(
        "Counts above are counted from the file at load time. The superseded flattened "
        "table tender_pipeline.csv is no longer read by PRISM; it and its builder are kept "
        "on disk."
    )

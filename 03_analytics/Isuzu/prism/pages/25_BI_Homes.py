# PRISM — BI Homes shell (four homes; Monday Command killed)
"""
Live organiser for the ISZE BI portfolio.
Static HTML = share/deck layer. IDS and Tender stay outside BI.
Monday Command mega-home is killed — Monday = Pricing.
"""

from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

APP_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(APP_DIR))

from config import ISZE_ROOT  # noqa: E402

DASH = ISZE_ROOT / "02_dashboards"
SALES = DASH / "sales"
PRICING = DASH / "pricing"
HUB = DASH / "hub"
DOCS = ISZE_ROOT / "00_docs" / "agent"

HOMES = [
    {
        "id": "H1",
        "title": "Pricing (Monday)",
        "q": "Which PNs need a price / Book B action this week?",
        "html": PRICING / "ISZE_Pricing_Action_Map.html",
        "cmd": None,
        "note": "Or Command Center → Pricing tab (default). Conclusion checklist on page.",
        "also": SALES / "OPEN_Aftermarket_BI_Command_Center.cmd",
    },
    {
        "id": "H2",
        "title": "Sales to dealer — network",
        "q": "AIM / GPS picture for every distributor that has sales-to-dealer files?",
        "html": SALES / "Dealer_Sellout_AIM_GPS_Sales_to_Dealer_2025.html",
        "cmd": SALES / "OPEN_Dealer_Sellout_AIM_GPS.cmd",
        "note": "ITUK · UTI · IRELAND · IUK · GREECE · PORTUGAL. Meeting pack — not Monday.",
    },
    {
        "id": "H3",
        "title": "Sales to dealer — deep",
        "q": "For one DB, where does bill vs dealer sales break by layer?",
        "html": SALES / "Next_Analyses_Sales_to_Dealer_SixDB.html",
        "cmd": SALES / "OPEN_Next_Analyses_Sales_to_Dealer_SixDB.cmd",
        "note": "Also PartGroups + replenishment — one grain per meeting.",
    },
    {
        "id": "H4",
        "title": "GPS / PMS challenge",
        "q": "Under real mileage, which markets look weaker — oil or wear?",
        "html": SALES / "ISZE_Aftermarket_BI_Command_Center.html",
        "cmd": SALES / "OPEN_Aftermarket_BI_Command_Center.cmd",
        "note": "Open Command Center → tab GPS/PMS V2 LCV. Mode B · claim framework.",
    },
]


st.set_page_config(page_title="BI Homes · PRISM", layout="wide")
st.markdown(
    """
<style>
.main-header{background:linear-gradient(90deg,#1B3A6B,#2C5AA0);padding:1rem 1.5rem;border-radius:8px;margin-bottom:1rem}
.main-header h1{color:#fff!important;margin:0;font-size:1.5rem}
.main-header p{color:#D6E4F0;margin:.35rem 0 0;font-size:.9rem}
.card{border:1px solid #d9d3c8;border-left:4px solid #E87722;padding:1rem 1.1rem;margin:0 0 .8rem;border-radius:6px;background:#fff}
.card h3{margin:0 0 .35rem;color:#1B3A6B}
.card .q{font-weight:600;margin:.2rem 0}
.card .meta{font-size:.85rem;color:#666}
.out{opacity:.75;border-left-color:#999}
</style>
""",
    unsafe_allow_html=True,
)

st.markdown(
    """
<div class="main-header">
  <h1>BI Homes — PRISM shell</h1>
  <p>Four BI doors. Monday = <strong>Pricing</strong>. Monday Command mega-home is <strong>killed</strong>.
  IDS and tenders are not BI. Double-click OPEN_*.cmd for HTML packs.</p>
</div>
""",
    unsafe_allow_html=True,
)

spec = DOCS / "BI_FULL_AUDIT_AND_STRUCTURE_2026-09-06.md"
if spec.is_file():
    st.caption(f"Structure SSOT: `{spec}`")

for h in HOMES:
    path = h["html"]
    exists = path.is_file()
    st.markdown(
        f"""
<div class="card">
  <h3>{h['id']} · {h['title']}</h3>
  <p class="q">{h['q']}</p>
  <p class="meta">{h['note']}</p>
  <p class="meta"><code>{path}</code> · {"OK on disk" if exists else "MISSING — rebuild"}</p>
</div>
""",
        unsafe_allow_html=True,
    )
    c1, c2 = st.columns([1, 3])
    with c1:
        if h.get("cmd") and Path(h["cmd"]).is_file():
            st.code(Path(h["cmd"]).name, language=None)
        elif h.get("also") and Path(h["also"]).is_file():
            st.code(Path(h["also"]).name, language=None)
        elif path.is_file():
            st.code(path.name, language=None)
    with c2:
        st.write("Open via Explorer double-click on the `.cmd` (or HTML). PRISM does not auto-launch browsers.")

st.markdown("---")
st.markdown(
    """
<div class="card out">
  <h3>Out of BI / killed</h3>
  <p class="q">Monday Command mega-home — killed (do not rebuild as a door)</p>
  <p class="q">IDS country / dealer packs — separate project</p>
  <p class="q">Tender Monitor — outside BI (eyes-only)</p>
</div>
""",
    unsafe_allow_html=True,
)

st.page_link("pages/23_Dealer_Sellout.py", label="Related live page · Dealer Sell-out (23)")
st.page_link("pages/2_GPS.py", label="Related live page · GPS (2)")
st.page_link("pages/3_PMS.py", label="Related live page · PMS (3)")

index = HUB / "BI_PACKS.html"
if index.is_file():
    st.caption(f"Secondary static index: `{index}`")

import json
from pathlib import Path

import streamlit as st

st.set_page_config(page_title="Stack · Jarvis", page_icon="📋", layout="wide")

# ── Data ──────────────────────────────────────────────────────────────────────
_STACK_JSON = Path(__file__).resolve().parent.parent / "data" / "stack.json"


def _load_projects() -> list[dict]:
    with _STACK_JSON.open(encoding="utf-8") as f:
        return json.load(f)


PROJECTS = _load_projects()

STATUS_COLOR = {
    "🔥": "#dc2626",  # red
    "✅": "#16a34a",  # green
    "⏳": "#d97706",  # amber
}

# ── CSS ───────────────────────────────────────────────────────────────────────
st.markdown(
    """
<style>
.project-card {
    background: #1f2937;
    border-radius: 10px;
    padding: 18px 20px;
    margin-bottom: 14px;
    border-left: 4px solid #3b82f6;
}
.project-card.waiting { border-left-color: #d97706; }
.project-card.done    { border-left-color: #16a34a; }
.card-name  { font-size: 1.05rem; font-weight: 700; color: #f9fafb; margin-bottom: 4px; }
.card-sum   { font-size: 0.88rem; color: #d1d5db; margin-bottom: 6px; }
.card-risk  { font-size: 0.8rem;  color: #fca5a5; }
.badge {
    display: inline-block;
    font-size: 0.72rem;
    font-weight: 600;
    padding: 2px 8px;
    border-radius: 999px;
    margin-left: 8px;
    vertical-align: middle;
}
.badge-active  { background: #7f1d1d; color: #fecaca; }
.badge-waiting { background: #78350f; color: #fde68a; }
.badge-done    { background: #14532d; color: #bbf7d0; }
</style>
""",
    unsafe_allow_html=True,
)

# ── Header ────────────────────────────────────────────────────────────────────
st.markdown("# 📋 Stack")
st.caption("Jerome's active ISZE projects — loaded from data/stack.json")

active = sum(1 for p in PROJECTS if p["status"] == "🔥")
waiting = sum(1 for p in PROJECTS if p["status"] == "⏳")
done = sum(1 for p in PROJECTS if p["status"] == "✅")

m1, m2, m3 = st.columns(3)
m1.metric("🔥 Active", active)
m2.metric("⏳ Waiting", waiting)
m3.metric("✅ Done", done)

st.divider()

# ── Cards ─────────────────────────────────────────────────────────────────────
for p in PROJECTS:
    status = p["status"]
    css_class = {"🔥": "active", "⏳": "waiting", "✅": "done"}.get(status, "")
    badge_class = f"badge-{css_class}"

    st.markdown(
        f"""
<div class="project-card {css_class}">
  <div class="card-name">
    {status} {p['name']}
    <span class="badge {badge_class}">{p['status_label']}</span>
  </div>
  <div class="card-sum">{p['summary']}</div>
  <div class="card-risk">⚠ Risk: {p['risk']}</div>
</div>
""",
        unsafe_allow_html=True,
    )

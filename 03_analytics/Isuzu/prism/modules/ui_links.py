"""Sidebar page links that do not crash when a page is AppTested alone."""

from __future__ import annotations

import streamlit as st


def page_link(page: str, label: str, icon: str = "") -> None:
    try:
        st.page_link(page, label=label, icon=icon)
    except (KeyError, TypeError, AttributeError):
        st.caption(f"→ {label}")

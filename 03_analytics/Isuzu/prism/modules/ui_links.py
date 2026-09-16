"""Sidebar page links that do not crash when a page is AppTested alone."""

from __future__ import annotations

import streamlit as st

_CATCH: tuple[type[BaseException], ...] = (KeyError, TypeError, AttributeError)
try:
    from streamlit.errors import StreamlitPageNotFoundError

    _CATCH = (*_CATCH, StreamlitPageNotFoundError)
except ImportError:
    pass


def page_link(page: str, label: str, icon: str = "") -> None:
    try:
        st.page_link(page, label=label, icon=icon)
    except _CATCH:
        st.caption(f"→ {label}")

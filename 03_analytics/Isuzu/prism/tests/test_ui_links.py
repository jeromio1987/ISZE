"""page_link must not crash AppTest when sibling pages are not registered."""

from __future__ import annotations

from modules import ui_links as u


def test_page_link_swallows_page_not_found(monkeypatch) -> None:
    from streamlit.errors import StreamlitPageNotFoundError

    captions: list[str] = []

    def _boom(*_a, **_k):
        raise StreamlitPageNotFoundError("pages/3_PMS.py", ".", False)

    monkeypatch.setattr(u.st, "page_link", _boom)
    monkeypatch.setattr(u.st, "caption", lambda t: captions.append(t))
    u.page_link("pages/3_PMS.py", "PMS — Capture Rate", "🔧")
    assert captions == ["→ PMS — Capture Rate"]

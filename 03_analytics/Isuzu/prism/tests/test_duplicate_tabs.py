"""Duplicate-tab trim — §8 item 2. Tabs dropped, pages not merged."""

from __future__ import annotations

from pathlib import Path

PRISM_ROOT = Path(__file__).resolve().parent.parent
PAGES = PRISM_ROOT / "pages"


def test_bvp_dropped_home_page_duplicates():
    src = (PAGES / "4_BVP.py").read_text(encoding="utf-8")
    assert '"PMS capture"' not in src
    assert '"GPS / SPU"' not in src
    assert '"AIM risk"' not in src
    assert "pages/3_PMS.py" in src
    assert "pages/2_GPS.py" in src
    assert "pages/7_AIM_Review.py" in src


def test_insights_dropped_bvp_capture_tab():
    src = (PAGES / "5_Insights.py").read_text(encoding="utf-8")
    assert "BVP × Capture" not in src or "not repeated" in src
    assert "render_bvp_capture_quadrant" not in src
    assert "pages/16_AIM_GPS_Matrix.py" in src
    assert '"📐 BVP × Capture"' not in src


def test_strategic_dropped_exposed_and_basket():
    src = (PAGES / "5_Strategic.py").read_text(encoding="utf-8")
    assert "Most exposed (triple threat)" not in src
    assert "Basket correlation" not in src or "parked" in src
    assert "render_triple_threat" not in src
    assert "render_basket_correlation" not in src
    assert "pages/0_Early_Warning.py" in src
    assert src.count("st.tabs") == 1
    assert '"PMS opportunity (€)"' in src

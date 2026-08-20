"""INTERNAL_MODE tab lists — default is MD-safe."""

from __future__ import annotations

from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

from config import is_internal_mode
from modules.internal_gate import (
    customer_risk_tab_labels,
    decision_tab_labels,
    offset_tab_labels,
)

PRISM_ROOT = Path(__file__).resolve().parent.parent


def test_default_hides_internal_tabs():
    assert decision_tab_labels(internal=False) == ["€ Waterfall", "Revenue Runway"]
    assert "ITUK Leakage" not in decision_tab_labels(internal=False)
    assert "Attach" not in decision_tab_labels(internal=False)
    assert "Elasticity" not in decision_tab_labels(internal=False)
    assert "3 · Demand-Flow" not in offset_tab_labels(internal=False)
    assert "Aftermarket scrape" not in customer_risk_tab_labels(internal=False)
    assert customer_risk_tab_labels(internal=False)[-1] == "Export"


def test_internal_shows_hidden_tabs():
    assert decision_tab_labels(internal=True) == [
        "€ Waterfall", "Revenue Runway", "Attach", "ITUK Leakage", "Elasticity",
    ]
    assert "3 · Demand-Flow" in offset_tab_labels(internal=True)
    assert "Aftermarket scrape" in customer_risk_tab_labels(internal=True)


def test_is_internal_mode_reads_live_env(monkeypatch):
    monkeypatch.delenv("PRISM_INTERNAL", raising=False)
    assert is_internal_mode() is False
    monkeypatch.setenv("PRISM_INTERNAL", "true")
    assert is_internal_mode() is True
    monkeypatch.setenv("PRISM_INTERNAL", "false")
    assert is_internal_mode() is False


@pytest.mark.parametrize(
    "rel",
    [
        "pages/network_intelligence.py",
        "pages/internal_shelf.py",
        "pages/18_Decision_Models.py",
    ],
)
def test_gated_pages_render_with_internal_off(monkeypatch, rel):
    """Default env must not NameError on hidden tabs."""
    monkeypatch.setenv("PRISM_INTERNAL", "false")
    at = AppTest.from_file(str(PRISM_ROOT / rel), default_timeout=90.0)
    at.run(timeout=90.0)
    assert not at.exception, (
        f"{rel} raised with PRISM_INTERNAL=false:\n"
        + "\n".join(f"  {e.value!r}" for e in at.exception)
    )

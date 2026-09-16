"""Which Streamlit tabs are visible. Default = MD-safe (internal mode off).

Internal-only: ITUK attach / dealer leakage, price-volume elasticity,
demand-flow Sankey (inferred leakage €), aftermarket scrape.
Launch with PRISM_INTERNAL=true (run_prism_internal.ps1) to see them.
"""

from __future__ import annotations

from config import is_internal_mode

DECISION_MD = ["€ Waterfall", "Revenue Runway"]
DECISION_INTERNAL = ["Attach", "ITUK Leakage", "Elasticity"]

OFFSET_MD = [
    "1 · Movement",
    "2 · Lumpiness→Airfreight",
    "4 · VOR Pricing Power",
    "5 · Premium vs Defection",
    "6 · Capture Ceiling",
]
OFFSET_DEMAND_FLOW = "3 · Demand-Flow"

CUSTOMER_RISK_MD = ["Ranking", "Signal breakdown", "Threat map", "Export"]
CUSTOMER_RISK_SCRAPE = "Aftermarket scrape"


def decision_tab_labels(*, internal: bool | None = None) -> list[str]:
    if internal is None:
        internal = is_internal_mode()
    labels = list(DECISION_MD)
    if internal:
        labels.extend(DECISION_INTERNAL)
    return labels


def offset_tab_labels(*, internal: bool | None = None) -> list[str]:
    """Keep published labels; insert Demand-Flow only when internal."""
    if internal is None:
        internal = is_internal_mode()
    if not internal:
        return list(OFFSET_MD)
    return [
        OFFSET_MD[0],
        OFFSET_MD[1],
        OFFSET_DEMAND_FLOW,
        OFFSET_MD[2],
        OFFSET_MD[3],
        OFFSET_MD[4],
    ]


def customer_risk_tab_labels(*, internal: bool | None = None) -> list[str]:
    if internal is None:
        internal = is_internal_mode()
    labels = ["Ranking", "Signal breakdown", "Threat map"]
    if internal:
        labels.append(CUSTOMER_RISK_SCRAPE)
    labels.append("Export")
    return labels

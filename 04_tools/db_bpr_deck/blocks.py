"""Slide blocks: the units the deck is assembled from, in the order they appear."""
from __future__ import annotations

# key, label, needs, default_on
#   needs   a short plain-English sentence on what the block reads. Shown in the wizard
#           under the block name so a non-technical user can judge it.
#   default_on  whether the wizard pre-ticks it (availability still controls it)
BLOCKS: list[dict] = [
    {
        "key": "exec",
        "label": "Executive view",
        "needs": "Uses the plan, sales to dealer, availability and fleet tiles together.",
        "default_on": True,
    },
    {
        "key": "plan",
        "label": "Plan against actual",
        "needs": "Monthly budget and orders for this distributor from the FY plan workbook.",
        "default_on": True,
    },
    {
        "key": "s2d",
        "label": "Sales to dealer (euros)",
        "needs": "The distributor's own monthly reporting in the KPI Master File.",
        "default_on": True,
    },
    {
        "key": "avail",
        "label": "Availability: fill rate, stock, back orders",
        "needs": "Three KPI Master File blocks for this distributor.",
        "default_on": True,
    },
    {
        "key": "s2d_units",
        "label": "How we used the data they shared",
        "needs": "Their sales-to-dealer file, in their own format.",
        "default_on": True,
    },
    {
        "key": "stock",
        "label": "Bought from ISZE against sold to dealers",
        "needs": "Their sales-to-dealer file joined to what we billed them.",
        "default_on": True,
    },
    {
        "key": "fleet",
        "label": "Fleet and vehicles in service",
        "needs": "A vehicle count for this market, from the best source available.",
        "default_on": True,
    },
    {
        "key": "gps",
        "label": "Genuine parts share",
        "needs": "Parts billed against the modelled spend of the fleet.",
        "default_on": True,
    },
    {
        "key": "pms",
        "label": "Service-demand cover",
        "needs": "Expected replacement units by service family for this market.",
        "default_on": True,
    },
    {
        "key": "mix",
        "label": "Genuine and value parts mix",
        "needs": "Parts billed split between Genuine and Best Value Parts.",
        "default_on": True,
    },
    {
        "key": "prose",
        "label": "Programmes, priorities and actions",
        "needs": "No data. You type the points and the questions you want asked.",
        "default_on": True,
    },
]

BLOCK_KEYS = [b["key"] for b in BLOCKS]
BLOCK_LABEL = {b["key"]: b["label"] for b in BLOCKS}


def order_for(selected: list[str]) -> list[str]:
    """Return the selected blocks in their natural deck order."""
    return [k for k in BLOCK_KEYS if k in selected]

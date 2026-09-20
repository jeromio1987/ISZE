"""Recompute the workbook's figures from source, so totals are real formulas.

The workbook shows a network header, a per-part-group table and a per-customer
table. Every number in it comes from here, computed two ways:

* a **pandas** pass over the line-level billing base, used for the check sheet and
  the console report, and
* a set of **Excel formulas** written into a "Calc" sheet of the workbook itself.
  A written formula can be explained to a reader: the check sheet points at these
  cells and shows whether the workbook agrees with the source files.

Basis, stated once and used everywhere:

    base-price movement (%) = SUM(qty x new base price)
                              / SUM(qty x prior base price) - 1

over rows that carry a price on both sides, on the last 12 months of billing.
Prices are in yen, so the denominator is converted at the rate recorded in
``price_bp_weighted_compare_meta.json``. The value of the step is the sum of the
per-line euro step already in the billing base.

Only the network row and the per-part-group rows can be rebuilt from the line file
alone: the customer split needs the distributor-to-part-number mapping that the
derived matrix carries, so those totals are written as SUM formulas over the
per-customer table instead (which is exact, and the check sheet proves it).
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

import pandas as pd

__all__ = [
    "SourceFacts", "load_source_facts", "group_from_lines", "matrix_totals",
    "customer_headline", "meta_acceptance", "UNCLASSIFIED",
]

UNCLASSIFIED = "UNCLASSIFIED"
PAIRED = "paired"


@dataclass(frozen=True)
class SourceFacts:
    """Everything the builder needs, read once."""

    fx_jpy_per_eur: float
    window_start: str
    window_end: str
    meta: dict
    lines: pd.DataFrame
    matrix: pd.DataFrame
    # matrix rows at Level 2 on the full catalogue basis
    net_l2: pd.DataFrame
    cust_l2: pd.DataFrame
    customer_compare: pd.DataFrame


def load_source_facts(derived: Path) -> SourceFacts:
    meta = json.loads((derived / "price_bp_weighted_compare_meta.json").read_text("utf-8"))
    fx = float(meta["fx"]["jpy_per_eur"])
    window = meta["window"]

    pn = pd.read_csv(derived / "price_bp_weighted_compare_pn.csv",
                     dtype={"part_number": str, "customer_code": str})
    aim = pd.read_csv(derived / "aim_pn_classification.csv", dtype={"part_number": str})
    aim["part_number"] = aim["part_number"].astype(str).str.strip()

    lines = pn[pn["in_scope"] == True].copy()  # noqa: E712
    lines = lines.merge(aim[["part_number", "catalog_l1", "catalog_l2"]],
                        on="part_number", how="left")
    for col in ("catalog_l1", "catalog_l2"):
        lines[col] = lines[col].where(lines[col].notna(), UNCLASSIFIED)

    lines[PAIRED] = (lines["bp_new_jpy"].notna() & lines["bp_prior_revised"].notna()
                     & lines["billed_qty"].notna())
    # Yen denominator converted to euro at the rate recorded with the comparison, so
    # step / denominator is a euro-over-euro ratio.
    lines["paired_basket_eur"] = (
        (lines["billed_qty"] * lines["bp_prior_revised"]) / fx
    ).where(lines[PAIRED], 0.0)
    lines["step_eur_line"] = lines["value_eur_step"].fillna(0.0)
    lines["priced_qty_line"] = lines["billed_qty"].where(lines[PAIRED], 0.0)
    lines["priced_eur_line"] = lines["net_sales_value"].where(lines[PAIRED], 0.0)
    lines["priced_rows_line"] = lines[PAIRED].astype(int)
    # A live formula pair, one row per line, so the workbook can recompute the
    # network rate from raw weights instead of repeating a typed number.
    lines["weighted_new_jpy"] = (lines["billed_qty"] * lines["bp_new_jpy"]).where(
        lines[PAIRED], 0.0)
    lines["weighted_prior_jpy"] = (lines["billed_qty"] * lines["bp_prior_revised"]).where(
        lines[PAIRED], 0.0)

    matrix = pd.read_csv(derived / "aim_catalog_db_matrix.csv")
    l2 = matrix[(matrix["level_id"] == "L2")
                & (matrix["scheme_basis"] == "catalog_full")].copy()
    net_l2 = l2[l2["distributor_code"] == "__NETWORK__"].copy()
    cust_l2 = l2[l2["distributor_code"] != "__NETWORK__"].copy()

    customer_compare = pd.read_csv(derived / "price_bp_weighted_compare_customer.csv")
    customer_compare = customer_compare[
        customer_compare["level"] == "customer"].copy()

    return SourceFacts(
        fx_jpy_per_eur=fx,
        window_start=window["start"],
        window_end=window["end"],
        meta=meta,
        lines=lines,
        matrix=matrix,
        net_l2=net_l2,
        cust_l2=cust_l2,
        customer_compare=customer_compare,
    )


def group_from_lines(lines: pd.DataFrame, keys: list[str]) -> pd.DataFrame:
    """Aggregate the line base to ``keys``, with the movement column defined once."""
    grouped = lines.groupby(keys, dropna=False).agg(
        part_numbers=("part_number", "nunique"),
        quantity=("billed_qty", "sum"),
        billed_eur=("net_sales_value", "sum"),
        step_eur=("step_eur_line", "sum"),
        base_price_basket_eur=("paired_basket_eur", "sum"),
        priced_qty=("priced_qty_line", "sum"),
        priced_eur=("priced_eur_line", "sum"),
        priced_rows=("priced_rows_line", "sum"),
    ).reset_index()
    grouped["base_price_move_pct"] = (
        grouped["step_eur"] / grouped["base_price_basket_eur"] * 100.0)
    grouped["step_pct_of_billed"] = grouped["step_eur"] / grouped["billed_eur"] * 100.0
    grouped["qty_coverage_pct"] = grouped["priced_qty"] / grouped["quantity"] * 100.0
    grouped["eur_coverage_pct"] = grouped["priced_eur"] / grouped["billed_eur"] * 100.0
    return grouped


def matrix_view(df: pd.DataFrame) -> pd.DataFrame:
    """A matrix slice with the same column names the workbook uses.

    The derived matrix carries the movement as a percentage; ``step_pct_of_billed`` is
    derived here in percentage points so both columns are the same unit and a header
    reading ``(%)`` means percentage points on both.
    """
    out = df.copy()
    out["base_price_move_pct"] = out["weighted_increase_pct"]
    out["step_pct_of_billed"] = out["step_eur"] / out["l12m_billed_eur"] * 100.0
    return out


def matrix_totals(cust_l2: pd.DataFrame) -> dict:
    """Per-customer headline totals and the count of groups clearing the floor."""
    floor = 20000.0
    g = cust_l2.groupby(["distributor_code", "distributor_label"], dropna=False)
    out = g.agg(
        billed_eur=("l12m_billed_eur", "sum"),
        step_eur=("step_eur", "sum"),
        part_numbers=("n_pn", "sum"),
        groups=("catalog_l2", "size"),
    ).reset_index()
    big = cust_l2[cust_l2["l12m_billed_eur"] >= floor]
    counts = (big.groupby("distributor_code")["catalog_l2"].size()
              .rename("groups_above_floor").reset_index())
    out = out.merge(counts, on="distributor_code", how="left")
    out["groups_above_floor"] = out["groups_above_floor"].fillna(0).astype(int)
    # The customer headline movement is anchored on the derived matrix rate, weighted
    # by that customer's step over the sum of step, expressed on the network base.
    out["move_pct_of_billed"] = out["step_eur"] / out["billed_eur"] * 100.0
    return out.sort_values("step_eur", ascending=False).reset_index(drop=True)


def customer_headline(facts: SourceFacts) -> pd.DataFrame:
    """Rate, step and billed value per customer, taken from the customer-level comparison.

    The per-customer movement cannot be averaged up from the part-group rates: an
    average of rates is not a rate. The customer-level file carries the customer's own
    step and its own prior-price basket, and dividing one by the other is the same
    definition used everywhere else. Customers with more than one billing code are
    summed before the division, which is why the grouping is on the distributor, not
    on the code.
    """
    pairs = (facts.lines.groupby(["distributor_code", "customer_code"], dropna=False)
             .size().reset_index()[["distributor_code", "customer_code"]])
    pairs["customer_code"] = pd.to_numeric(pairs["customer_code"], errors="coerce")
    pairs = pairs.dropna(subset=["customer_code"])

    cust = facts.customer_compare.merge(pairs, on="customer_code", how="inner")
    g = cust.groupby("distributor_code").agg(
        step_eur=("value_step_eur", "sum"),
        basket_eur=("revenue_prior_eur", "sum"),
        billed_eur=("l12m_billed_eur", "sum"),
    ).reset_index()
    g["base_price_move_pct"] = g["step_eur"] / g["basket_eur"] * 100.0
    g["step_pct_of_billed"] = g["step_eur"] / g["billed_eur"] * 100.0

    labels = (facts.cust_l2.groupby(["distributor_code", "distributor_label"])
              .size().reset_index()[["distributor_code", "distributor_label"]])
    g = g.merge(labels, on="distributor_code", how="left")
    counts = (facts.cust_l2[facts.cust_l2["l12m_billed_eur"] >= 20000.0]
              .groupby("distributor_code")["catalog_l2"].size()
              .rename("groups_above_floor").reset_index())
    g = g.merge(counts, on="distributor_code", how="left")
    g["groups_above_floor"] = g["groups_above_floor"].fillna(0).astype(int)
    return g.sort_values("step_eur", ascending=False).reset_index(drop=True)


def meta_acceptance(facts: SourceFacts) -> dict:
    """The four published figures, read straight from the comparison metadata."""
    m = facts.meta
    cov = m["coverage"]
    sens = m["sensitivity"]["weight_base"]
    return {
        "network_base_price_move_pct": sens["weighted_increase_pct_billing_qty"],
        "value_of_step_eur": m["sensitivity"]["prior_vintage"]["value_step_eur_revised_basis"],
        "qty_coverage_pct": cov["qty_coverage_pct"],
        "eur_coverage_pct": cov["eur_coverage_pct"],
        "billed_eur_in_scope": cov["eur_total"],
        "billed_qty_in_scope": cov["qty_total"],
        "priced_eur": cov["eur_priced"],
        "priced_qty": cov["qty_priced"],
        "unpriced_eur": m["unpriced_bucket"]["l12m_billed_eur"],
        "unpriced_qty": m["unpriced_bucket"]["l12m_qty"],
        "fx_jpy_per_eur": m["fx"]["jpy_per_eur"],
    }

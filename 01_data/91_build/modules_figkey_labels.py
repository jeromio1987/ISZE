"""Figure-key label lookup for the AIM + fig-key export.

Keeps the export free of any PRISM import.

The rule is one line: **a row may never wear another figure key's label.**

parts_catalog_dimension.csv labels are looked up by part number. That is fine as
long as the part number sits on the same figure key in both files. Where the two
files disagree about a part number's key, the dimension label describes the other
key, and handing it over is how sixteen cabin blower filters came out as
"Urea (AdBlue) filter" (fixed 2026-09-21; 49 rows in total were affected).

So: keep the dimension label, except where this row's figure key differs from the
dimension's key for the same part number. There the label comes from the row's own
key — the label that key's other parts already carry in the dimension, or the
taxonomy label when the key has no parts in the dimension yet.
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd
import yaml

ROOT = Path(r"C:\Users\jerom\Desktop\claude\ISZE")
TAXONOMY = ROOT / "03_analytics" / "Isuzu" / "prism" / "data" / "fig_key_taxonomy.yaml"
DIMENSION = ROOT / "01_data" / "00_derived" / "parts_catalog_dimension.csv"


def _taxonomy_labels() -> dict[str, str]:
    if not TAXONOMY.is_file():
        return {}
    tax = yaml.safe_load(TAXONOMY.read_text(encoding="utf-8")) or {}
    out: dict[str, str] = {}
    for key, meta in (tax.get("pms_fig_keys") or {}).items():
        label = (meta or {}).get("label")
        if label:
            out[str(key).strip()] = str(label).strip()
    return out


def _dimension_tables() -> tuple[dict[str, str], dict[str, str]]:
    """(fig_key -> its most common label, part_number -> its fig key)."""
    if not DIMENSION.is_file():
        return {}, {}
    d = pd.read_csv(
        DIMENSION,
        usecols=["part_number", "fig_key", "fig_key_label"],
        dtype=str,
        low_memory=False,
    )
    for c in d.columns:
        d[c] = d[c].fillna("").astype(str).str.strip()

    labelled = d[(d["fig_key"] != "") & (d["fig_key_label"] != "")]
    if labelled.empty:
        by_key: dict[str, str] = {}
    else:
        most = (
            labelled.groupby(["fig_key", "fig_key_label"], as_index=False)
            .size()
            .sort_values("size", ascending=False)
            .drop_duplicates("fig_key", keep="first")
        )
        by_key = dict(zip(most["fig_key"], most["fig_key_label"]))

    keyed = d[d["fig_key"] != ""].drop_duplicates("part_number", keep="first")
    by_pn = dict(zip(keyed["part_number"], keyed["fig_key"]))
    return by_key, by_pn


def label_for_own_fig_key(
    part_number: pd.Series,
    fig_key: pd.Series,
    dim_label_by_pn: pd.Series,
) -> pd.Series:
    """Label per row. Keeps the part-number label unless this row's figure key is
    a curated taxonomy key that disagrees with the dimension's key for that part
    number — then the curated label for the row's own key wins.

    Deliberately narrow: only taxonomy keys can override, and only with a
    taxonomy label. Widening this to every key re-cuts thousands of labels from
    the coarse PR00 text and gets some of them wrong (e.g. air-cleaner elements
    on 130-026 would read "Other A/C").
    """
    pns = part_number.fillna("").astype(str).str.strip()
    keys = fig_key.fillna("").astype(str).str.strip()
    base = dim_label_by_pn.fillna("").astype(str).str.strip()

    _, by_pn = _dimension_tables()
    tax = _taxonomy_labels()

    own_label = keys.map(lambda k: tax.get(k, ""))
    disagree = pd.Series(
        [
            bool(k) and k in tax and bool(by_pn.get(p, "")) and k != by_pn.get(p, "")
            for p, k in zip(pns, keys)
        ],
        index=keys.index,
    )
    return base.where(~disagree, own_label)

"""Fig-key fill from IE40 parquet — existing PR00 rows only."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from modules.fig_key_catalog import (
    build_parts_catalog_dimension,
    fig_key_from_parts,
    fill_empty_fig_keys_in_pr00_csv,
    load_ie40_fig_key_lookup,
    lookup_ie40_fig_key,
)


def _write_pr00(path: Path, rows: list[tuple[str, str, str, str, str, str, str]]) -> None:
    path.write_text(
        "pn_norm,family,group,level3_type,fig_key,fig_no,key_no\n"
        + "\n".join(",".join(r) for r in rows)
        + "\n",
        encoding="utf-8",
    )


def _write_parquet(path: Path, rows: list[dict]) -> None:
    pd.DataFrame(rows).to_parquet(path, index=False)


def _write_bvp(path: Path) -> None:
    path.write_text(
        "part_number,pms_category,pms_flag,product_subgroup,in_bvp_catalog\n",
        encoding="utf-8",
    )


def test_fig_key_from_parts_digits_only() -> None:
    assert fig_key_from_parts(50, 2) == "050-002"
    assert fig_key_from_parts("1", "HAA") is None
    assert fig_key_from_parts("", "002") is None


def test_fill_empty_fig_key_from_parquet(tmp_path: Path) -> None:
    csv_path = tmp_path / "pr00_classification.csv"
    pq = tmp_path / "pricing_pr00_ie40.parquet"
    _write_pr00(
        csv_path,
        [
            ("1096251860", "Repair parts", "Gaskets / seals", "Oil seal", "", "", ""),
            ("8982705240", "Filters", "Oil filter", "Element", "050-002", "050", "002"),
        ],
    )
    _write_parquet(
        pq,
        [
            {
                "part_number": "1096251860",
                "newest_pn": "1096251860",
                "fig_no": "038",
                "key_no": "251",
            },
            {
                "part_number": "8982705240",
                "newest_pn": "8982705240",
                "fig_no": "999",
                "key_no": "999",
            },
            {
                "part_number": "9999999999",
                "newest_pn": "9999999999",
                "fig_no": "001",
                "key_no": "001",
            },
        ],
    )
    stats = fill_empty_fig_keys_in_pr00_csv(csv_path, pq)
    assert stats["filled"] == 1
    assert stats["added_pns"] == 0
    df = pd.read_csv(csv_path, dtype=str)
    assert len(df) == 2
    filled = df.loc[df["pn_norm"] == "1096251860"].iloc[0]
    assert filled["fig_key"] == "038-251"
    assert filled["family"] == "Repair parts"
    assert filled["group"] == "Gaskets / seals"
    kept = df.loc[df["pn_norm"] == "8982705240"].iloc[0]
    assert kept["fig_key"] == "050-002"
    assert "9999999999" not in set(df["pn_norm"])


def test_catalog_builder_fills_empty_without_rewriting_csv(tmp_path: Path) -> None:
    csv_path = tmp_path / "pr00_classification.csv"
    bvp = tmp_path / "bvp.csv"
    pq = tmp_path / "ie40.parquet"
    tax = tmp_path / "tax.yaml"
    ov = tmp_path / "overrides.csv"
    _write_pr00(
        csv_path,
        [("1096251860", "Repair parts", "Gaskets / seals", "Oil seal", "", "", "")],
    )
    _write_bvp(bvp)
    _write_parquet(
        pq,
        [
            {
                "part_number": "0001096251860",
                "newest_pn": "1096251860",
                "fig_no": 38,
                "key_no": 251,
            }
        ],
    )
    tax.write_text("pms_fig_keys: {}\ncategory_default_fig_key: {}\n", encoding="utf-8")
    ov.write_text("part_number,fig_key,source\n", encoding="utf-8")
    dim = build_parts_catalog_dimension(
        pr00_csv=csv_path,
        bvp_dimension_csv=bvp,
        taxonomy_path=tax,
        overrides_path=ov,
        ie40_parquet=pq,
    )
    hit = dim[dim["part_number"].astype(str).str.lstrip("0") == "1096251860"]
    assert not hit.empty
    assert hit.iloc[0]["fig_key"] == "038-251"
    csv_again = pd.read_csv(csv_path, dtype=str)
    assert (csv_again["fig_key"].fillna("") == "").all()


def test_lookup_prefers_part_number_row(tmp_path: Path) -> None:
    pq = tmp_path / "ie40.parquet"
    _write_parquet(
        pq,
        [
            {
                "part_number": "1111111111",
                "newest_pn": "2222222222",
                "fig_no": "010",
                "key_no": "001",
            },
            {
                "part_number": "2222222222",
                "newest_pn": "2222222222",
                "fig_no": "010",
                "key_no": "002",
            },
        ],
    )
    lookup = load_ie40_fig_key_lookup(pq)
    assert lookup_ie40_fig_key("1111111111", lookup)["fig_key"] == "010-001"
    assert lookup_ie40_fig_key("2222222222", lookup)["fig_key"] == "010-002"

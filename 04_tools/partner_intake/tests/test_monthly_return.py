"""Tests for the monthly return of one distributor.

Every euro in this file is made up. Nothing here is taken from a sales extract.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import monthly_return as mr  # noqa: E402

DISTRIBUTOR = "Harbour Parts"
DECOY = "ZEBRA_DECOY_MOTORS"
PERIOD = "2026-09"


def _own(**overrides: object) -> dict:
    own = {
        "billed_eur": 120_000,
        "warranty_eur": 15_000,
        "sales_to_dealer_eur": 70_000,
        "stock_eur": 35_000,
        "genuine_eur": 50_000,
        "bvp_eur": 20_000,
        "maintenance_eur": 18_000,
        "ids_note": "IDS file received for this month.",
    }
    own.update(overrides)
    return own


def _average(**overrides: object) -> dict:
    average = {
        "billed_eur": 80_000,
        "warranty_eur": 9_000,
        "sales_to_dealer_eur": 40_000,
        "stock_eur": 22_000,
        "genuine_eur": 30_000,
        "bvp_eur": 12_000,
        "maintenance_eur": 11_000,
        "ids_note": "QUILL_MOTORS average note",
        "distributor_name": "QUILL_MOTORS",
    }
    average.update(overrides)
    return average


def _text(**kwargs: object) -> str:
    args = {
        "distributor_name": DISTRIBUTOR,
        "period": PERIOD,
        "own": _own(),
        "network_average": _average(),
        "decoy_name": DECOY,
    }
    args.update(kwargs)
    return mr.build_return(**args)


def test_names_this_distributor_and_hides_the_decoy() -> None:
    text = _text()
    assert DISTRIBUTOR in text
    assert DECOY not in text
    assert "QUILL_MOTORS" not in text
    assert "Monthly return" in text
    assert "draft, for one distributor" in text
    assert "A person sends this." in text
    assert PERIOD in text


def test_warranty_unknown_leaves_stock_out() -> None:
    text = _text(
        own=_own(warranty_eur=None, stock_eur=424_242),
        network_average=_average(stock_eur=515_151, warranty_eur=9_000),
    )
    assert "warranty split unknown" in text
    assert "424242" not in text
    assert "424,242" not in text
    assert "515151" not in text
    assert "515,151" not in text
    assert "lost sales" not in text
    assert "EUR 120,000" in text
    assert "EUR 70,000" in text


def test_stock_line_says_stock_not_lost_sales() -> None:
    text = _text(network_average=None)
    assert "EUR 35,000" in text
    assert "This is stock, not lost sales." in text
    assert "anonymous network average" not in text.lower()


def test_stock_figure_is_the_one_passed_in() -> None:
    # 120000 - 15000 - 70000 would be 35000. Pass a different stock on purpose.
    text = _text(own=_own(stock_eur=13), network_average=None)
    assert "Stock: EUR 13. This is stock, not lost sales." in text
    assert "EUR 35,000" not in text


def test_network_average_has_no_count_unless_network_n_is_passed() -> None:
    quiet = _text()
    assert "anonymous network average" in quiet.lower()
    assert "EUR 120,000" in quiet
    assert "EUR 80,000" in quiet
    assert "17" not in quiet
    assert "distributors" not in quiet.lower()

    counted = _text(network_n=17)
    assert "Anonymous network average, across 17 distributors." in counted
    assert DECOY not in counted

    absent = _text(network_average=None, network_n=17)
    assert "17" not in absent
    assert "anonymous network average" not in absent.lower()
    assert "distributors" not in absent.lower()


def test_no_league_language() -> None:
    text = _text().lower()
    for banned in (
        "above average",
        "below average",
        "ranking",
        "ranked",
        "1st",
        "2nd",
        " place",
    ):
        assert banned not in text


def test_genuine_and_bvp_are_euro_lines() -> None:
    text = _text(network_average=None)
    assert "Genuine parts, in euros: EUR 50,000." in text
    assert "BVP, in euros: EUR 20,000." in text
    for word in ("piece", "pieces", "unit", "units", "qty"):
        assert word not in text.lower()


def test_ids_is_a_note() -> None:
    text = _text(network_average=None)
    assert "IDS note: IDS file received for this month." in text
    blank = _text(own=_own(ids_note=None), network_average=None)
    assert "IDS note: none supplied." in blank
    assert "score" not in blank.lower()


def test_html_file_is_self_contained(tmp_path: Path) -> None:
    path = tmp_path / "return.html"
    mr.write_html(
        path,
        DISTRIBUTOR,
        PERIOD,
        _own(),
        _average(),
        network_n=None,
        decoy_name=DECOY,
    )
    page = path.read_text(encoding="utf-8")
    assert DISTRIBUTOR in page
    assert DECOY not in page
    assert "QUILL_MOTORS" not in page
    assert "Monthly return" in page
    assert "draft, for one distributor" in page
    assert "A person sends this." in page
    assert "warranty" in page.lower()
    assert "#15233c" in page
    assert "#f7f4ee" in page
    assert "#c0552d" in page
    assert "#222" in page
    assert "Georgia" in page
    assert "<style>" in page
    assert "<link" not in page.lower()
    assert "<script" not in page.lower()
    assert "fetch(" not in page.lower()
    assert "cdn" not in page.lower()
    assert "color:#fff" not in page.replace(" ", "").lower()
    assert "color:#ffffff" not in page.replace(" ", "").lower()


def test_html_warranty_unknown_and_stock_wording(tmp_path: Path) -> None:
    unknown = tmp_path / "unknown.html"
    mr.write_html(
        unknown,
        DISTRIBUTOR,
        PERIOD,
        _own(warranty_eur=None, stock_eur=424_242),
        None,
        decoy_name=DECOY,
    )
    unknown_page = unknown.read_text(encoding="utf-8")
    assert "warranty split unknown" in unknown_page
    assert "424,242" not in unknown_page
    assert "lost sales" not in unknown_page
    assert DECOY not in unknown_page

    stocked = tmp_path / "stocked.html"
    mr.write_html(
        stocked,
        "Harbour & Co",
        PERIOD,
        _own(),
        None,
        decoy_name=DECOY,
    )
    stocked_page = stocked.read_text(encoding="utf-8")
    assert "This is stock, not lost sales." in stocked_page
    assert "Harbour &amp; Co" in stocked_page
    assert "Harbour & Co" not in stocked_page
    assert "<script>" not in stocked_page
    assert DECOY not in stocked_page


def test_html_escapes_a_name_that_looks_like_markup(tmp_path: Path) -> None:
    path = tmp_path / "mark.html"
    mr.write_html(
        path,
        "<script>alert(1)</script>",
        PERIOD,
        _own(),
        None,
    )
    page = path.read_text(encoding="utf-8")
    assert "<script>" not in page
    assert "&lt;script&gt;" in page


def test_decoy_must_be_text_or_absent() -> None:
    with pytest.raises(TypeError):
        mr.build_return(DISTRIBUTOR, PERIOD, _own(), None, decoy_name=3)  # type: ignore[arg-type]

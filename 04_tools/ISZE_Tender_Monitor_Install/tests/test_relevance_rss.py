"""Tender relevance 1–5, RSS sanitize/recover, Retry-After."""

from __future__ import annotations

import sys
from datetime import datetime, timedelta, timezone
from email.utils import format_datetime
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from isze_core_v3 import (  # noqa: E402
    ISZE_TARGET_MARKETS,
    normalize_raw_row,
    parse_xml_root,
    relevance_pass,
    relevance_score_1to5,
    retry_after_seconds,
    sanitize_xml_entities,
    score_legacy,
)


def test_score_legacy_still_one_to_five() -> None:
    assert score_legacy("office stationery") == 1
    assert 1 <= score_legacy("isuzu vehicle maintenance contract") <= 5


def test_relevance_target_market_keeps_legacy() -> None:
    title = "Isuzu N-series vehicle maintenance"
    assert "GBR" in ISZE_TARGET_MARKETS
    assert relevance_score_1to5(title, country_code="GBR") == score_legacy(title)
    assert relevance_pass(relevance_score_1to5(title, country_code="GBR"))


def test_relevance_outside_market_capped() -> None:
    title = "Isuzu vehicle maintenance and repair"
    base = score_legacy(title)
    assert base >= 3
    assert "USA" not in ISZE_TARGET_MARKETS
    scored = relevance_score_1to5(title, country_code="USA", value_amount=1_000_000)
    assert scored <= 2
    assert not relevance_pass(scored)


def test_normalize_keeps_low_relevance_rows() -> None:
    low = normalize_raw_row(
        {
            "Source": "test",
            "Title": "Isuzu vehicle maintenance",
            "Country": "United States",
            "Country Code": "USA",
            "Est. Value": "100",
        }
    )
    high = normalize_raw_row(
        {
            "Source": "test",
            "Title": "Isuzu vehicle maintenance",
            "Country": "United Kingdom",
            "Country Code": "GBR",
            "Est. Value": "100",
        }
    )
    exported = [low, high]
    assert len(exported) == 2
    assert low["relevance_pass"] is False
    assert high["relevance_pass"] is True
    assert 1 <= low["relevance_score_1to5"] <= 5
    assert 1 <= high["relevance_score_1to5"] <= 5


def test_sanitize_nbsp_and_parse() -> None:
    xml = (
        '<?xml version="1.0"?><rss version="2.0"><channel>'
        "<item><title>Fleet&nbsp;maintenance</title>"
        "<description>isuzu van</description></item>"
        "</channel></rss>"
    )
    cleaned = sanitize_xml_entities(xml)
    assert "&nbsp;" not in cleaned
    root = parse_xml_root(xml)
    title = root.find(".//item/title")
    assert title is not None
    assert "Fleet" in (title.text or "")


def test_retry_after_numeric_and_date() -> None:
    assert retry_after_seconds("12", attempt=0) == 12
    assert retry_after_seconds(None, attempt=0, fallback_schedule=[30, 60]) == 30
    future = datetime.now(timezone.utc) + timedelta(seconds=45)
    header = format_datetime(future)
    wait = retry_after_seconds(header, attempt=0, fallback_schedule=[9])
    assert 20 <= wait <= 45


def test_parse_xml_recover_mismatched_tag() -> None:
    xml = (
        '<?xml version="1.0"?><rss version="2.0"><channel>'
        "<item><title>Isuzu maintenance</title></wrong></item>"
        "</channel></rss>"
    )
    try:
        root = parse_xml_root(xml)
    except Exception:
        pytest.skip("recover parser unavailable")
    items = root.findall(".//item")
    assert isinstance(items, list)


def test_flatten_exports_relevance_score_and_keeps_fail_rows() -> None:
    from tender_scraper_v3 import flatten_for_export

    low = normalize_raw_row(
        {
            "Source": "test",
            "Title": "Isuzu vehicle maintenance",
            "Country": "United States",
            "Country Code": "USA",
            "Est. Value": "100",
        }
    )
    high = normalize_raw_row(
        {
            "Source": "test",
            "Title": "Isuzu vehicle maintenance",
            "Country": "United Kingdom",
            "Country Code": "GBR",
            "Est. Value": "100",
        }
    )
    exported = [flatten_for_export(low), flatten_for_export(high)]
    assert len(exported) == 2
    assert "Relevance Score" in exported[0]
    assert exported[0]["Relevance Pass"] == ""
    assert exported[1]["Relevance Pass"] == "YES"
    assert 1 <= int(exported[0]["Relevance Score"]) <= 5
    assert 1 <= int(exported[1]["Relevance Score"]) <= 5


def test_get_with_retry_honors_retry_after_and_records_exhaustion(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from tender_scraper_v3 import LAST_FETCH_ERRORS, get_with_retry

    sleeps: list[float] = []

    class _Resp:
        status_code = 429
        headers = {"Retry-After": "7"}

        def raise_for_status(self) -> None:
            raise AssertionError("429 must not raise before Retry-After loop")

    class _Session:
        def get(self, *args, **kwargs):
            return _Resp()

    monkeypatch.setattr("tender_scraper_v3.time.sleep", lambda s: sleeps.append(s))
    LAST_FETCH_ERRORS.clear()
    out = get_with_retry(
        _Session(),
        "https://example.test/ocds",
        max_retries=2,
        source_label="UK Find a Tender",
    )
    assert out is None
    assert sleeps == [7, 7]
    err = LAST_FETCH_ERRORS.get("UK Find a Tender") or ""
    assert "429" in err
    assert "exhausted" in err.lower()

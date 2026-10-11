"""Sample files and a few made-up rows. No distributor billing."""

from __future__ import annotations

import hashlib
import io
import json
import sys
from datetime import date
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import receipt  # noqa: E402
import rules  # noqa: E402
import validator  # noqa: E402

SAMPLES = ROOT / "samples"
V003_ACTION = "Remove it and send the file again as the next version."


def _declaration() -> dict:
    return validator.load_declaration(SAMPLES / "good_min_declaration.json")


def _good(**kwargs):
    defaults = dict(
        declaration=_declaration(),
        drop_distributor_id="SAMPLE",
        file_version=1,
        received=date(2027, 5, 10),
        previous_qty=None,
    )
    defaults.update(kwargs)
    return validator.validate_path(SAMPLES / "good_min.csv", **defaults)


def _row(**overrides) -> dict:
    row = {
        "distributor_id": "SAMPLE",
        "dealer_id": "DEALER1",
        "part_number": "001234",
        "quantity": "3",
        "period": "2027-04",
    }
    row.update(overrides)
    return row


def _run(rows, **kwargs):
    defaults = dict(
        declaration=_declaration(),
        drop_distributor_id="SAMPLE",
        file_version=1,
        received=date(2027, 5, 10),
        content_sha256="a" * 64,
        previous_qty=None,
    )
    defaults.update(kwargs)
    return validator.validate(rows, **defaults)


def _ids(result, rule_id):
    return [item for item in result.findings if item.rule_id == rule_id]


def test_good_min_is_accepted_and_keeps_text_and_returns():
    result = _good()
    assert result.accepted is True
    assert result.period == "2027-04"
    assert result.rows[0]["part_number"] == "001234"
    assert result.rows[1]["part_number"] == "000789"
    assert result.rows[1]["quantity"] == "-1"
    assert not any(item.stops for item in result.findings)
    assert _ids(result, "V012")[0].message == "no previous accepted month"
    assert _ids(result, "V012")[0].severity == "I"
    assert _ids(result, "V005")[0].message == (
        "catalogue match not run; no classification file is the authority"
    )
    assert _ids(result, "V005")[0].stops is False
    assert _ids(result, "V011") == []


def test_sha256_is_the_original_bytes():
    payload = (SAMPLES / "good_min.csv").read_bytes()
    result = _good()
    assert result.content_sha256 == hashlib.sha256(payload).hexdigest()


def test_bad_price_is_not_accepted_and_the_column_stays():
    result = validator.validate_path(
        SAMPLES / "bad_price.csv",
        _declaration(),
        "SAMPLE",
        1,
        date(2027, 5, 10),
    )
    assert result.accepted is False
    price = _ids(result, "V003")
    assert len(price) == 1
    assert price[0].stops is True
    assert price[0].severity == rules.RULE_BY_ID["V003"].severity
    assert price[0].action == V003_ACTION
    assert "unit_price" in result.rows[0]
    assert result.rows[0]["unit_price"] == "x"
    assert _ids(result, "V018")[0].stops is True


def test_hidden_currency_symbol_rejects_an_innocent_header():
    result = validator.validate_path(
        SAMPLES / "bad_hidden_price.csv",
        _declaration(),
        "SAMPLE",
        1,
        date(2027, 5, 10),
    )
    assert result.accepted is False
    hidden = _ids(result, "V018")
    assert len(hidden) == 1
    assert hidden[0].stops is True
    assert "£" in hidden[0].message
    assert _ids(result, "V003") == []


def test_receipt_text_for_a_price_column():
    result = validator.validate_path(
        SAMPLES / "bad_price.csv",
        _declaration(),
        "SAMPLE",
        1,
        date(2027, 5, 10),
    )
    text = receipt.as_text(result)
    body = receipt.as_dict(result)
    assert body["version"] == 1
    assert body["result"] == "NOT ACCEPTED"
    assert "Version 1" in text.splitlines()
    assert "NOT ACCEPTED" in text.splitlines()
    assert f"Rule V003: A price column was found (unit_price). {V003_ACTION}" in text
    assert "**" not in text
    assert "`" not in text
    assert "\n#" not in "\n" + text
    json.dumps(body)


def test_period_must_be_one_yyyy_mm():
    mixed = _run([_row(period="2027-04"), _row(period="2027-05")])
    assert _ids(mixed, "V004")[0].stops is True
    assert mixed.accepted is False
    assert mixed.period is None

    bare = _run([_row(period="2027-4")])
    assert _ids(bare, "V004")[0].stops is True
    assert bare.accepted is False


def test_blank_part_number_stops_without_a_catalogue_match():
    result = _run([_row(part_number=""), _row(part_number="00012")])
    assert result.accepted is False
    blank = [item for item in _ids(result, "V005") if item.stops]
    warn = [item for item in _ids(result, "V005") if not item.stops]
    assert len(blank) == 1
    assert len(warn) == 1
    assert result.rows[1]["part_number"] == "00012"
    assert "catalogue" not in blank[0].message


def test_blank_dealer_follows_stops_file():
    early = _run([_row(dealer_id="")])
    late_period = "2027-10"
    late = _run(
        [_row(dealer_id="", period=late_period)],
        received=date(2027, 11, 1),
    )
    early_hit = _ids(early, "V008")[0]
    late_hit = _ids(late, "V008")[0]
    severity = rules.RULE_BY_ID["V008"].severity
    assert early_hit.stops is rules.stops_file(severity, "2027-04")
    assert late_hit.stops is rules.stops_file(severity, late_period)
    assert early_hit.stops is False
    assert late_hit.stops is True
    assert early.accepted is True
    assert late.accepted is False
    assert early_hit.severity == rules.RULE_BY_ID["V008"].severity


def test_missing_declaration_field_stops():
    declaration = _declaration()
    declaration["date_from"] = "  "
    declaration.pop("returns_included")
    result = _run([_row()], declaration=declaration)
    hit = _ids(result, "V010")[0]
    assert hit.stops is True
    assert "date_from" in hit.message
    assert "returns_included" in hit.message
    assert result.accepted is False


def test_returns_included_false_keeps_a_negative_quantity():
    declaration = _declaration()
    declaration["returns_included"] = False
    result = _run([_row(quantity="-1")], declaration=declaration)
    assert _ids(result, "V010") == []
    assert result.rows[0]["quantity"] == "-1"
    assert result.accepted is True


def test_deadline_is_ten_weekdays_after_month_end():
    # 30 Apr 2027 is a Friday. The next ten weekdays end on 14 May 2027.
    assert date(2027, 4, 30).weekday() == 4
    assert validator.on_time_deadline("2027-04") == date(2027, 5, 14)
    # 31 Dec 2027 is a Friday. Ten weekdays later is 14 Jan 2028.
    assert validator.on_time_deadline("2027-12") == date(2028, 1, 14)

    on_time = _run([_row()], received=date(2027, 5, 14))
    late = _run([_row()], received=date(2027, 5, 15))
    assert _ids(on_time, "V011") == []
    assert on_time.accepted is True
    hit = _ids(late, "V011")[0]
    assert hit.stops is False
    assert hit.severity == rules.RULE_BY_ID["V011"].severity
    assert "no holiday calendar" in hit.message
    assert late.accepted is True


def test_volume_jump_does_not_invent_a_threshold():
    result = _run([_row(quantity="3"), _row(quantity="-1")], previous_qty=40)
    hit = _ids(result, "V012")[0]
    assert hit.message == "volume-jump threshold is not set"
    assert hit.severity == rules.RULE_BY_ID["V012"].severity
    assert hit.stops is False
    assert result.accepted is True
    assert "40" not in hit.message
    assert "%" not in hit.message


def test_no_previous_month_is_information():
    result = _run([_row()], previous_qty=None)
    hit = _ids(result, "V012")[0]
    assert hit.message == "no previous accepted month"
    assert hit.severity == "I"
    assert hit.stops is False


def test_distributor_must_match_the_drop_folder():
    result = _run([_row(), _row(distributor_id="OTHER")], drop_distributor_id="SAMPLE")
    hit = _ids(result, "V016")[0]
    assert hit.stops is True
    assert result.accepted is False
    assert "row 2" in hit.message


def test_currency_header_is_v018_and_not_a_price_word():
    result = _run([_row(gbp="x")])
    assert _ids(result, "V003") == []
    assert _ids(result, "V018")[0].stops is True
    assert result.accepted is False


def test_amount_and_customer_headers_are_not_rejected():
    result = _run([_row(amount="4", customer_name="EXAMPLE")])
    assert _ids(result, "V003") == []
    assert _ids(result, "V018") == []
    assert result.accepted is True


def test_quantity_must_be_a_number_and_a_negative_is_kept():
    bad = _run([_row(quantity="n/a")])
    assert bad.accepted is False
    hit = _ids(bad, validator.QUANTITY_RULE_ID)[0]
    assert hit.stops is True
    assert "number" in hit.message
    kept = _run([_row(quantity="-2")])
    assert kept.accepted is True
    assert kept.rows[0]["quantity"] == "-2"
    assert _ids(kept, validator.QUANTITY_RULE_ID) == []


def test_unstated_rules_are_listed_and_do_not_stop():
    result = _good()
    unstated = [rule.id for rule in rules.RULES if not rule.stated]
    stated = [rule.id for rule in rules.RULES if rule.stated]
    assert result.not_checked == unstated
    assert set(result.not_checked).isdisjoint(item.rule_id for item in result.findings)
    for rule_id in stated:
        assert rule_id not in result.not_checked
    text = receipt.as_text(result)
    assert "not checked, text not in the local spec:" in text
    assert "V001" in text
    assert result.accepted is True
    body = receipt.as_dict(result)
    assert body["result"] == "ACCEPTED"
    assert body["not_checked"][0]["note"] == "not checked, text not in the local spec"


def test_validate_does_not_write_a_ledger(tmp_path):
    before = {path.name for path in SAMPLES.iterdir()}
    result = _good()
    after = {path.name for path in SAMPLES.iterdir()}
    assert before == after
    receipt.write_text(tmp_path / "receipt.txt", result)
    written = (tmp_path / "receipt.txt").read_text(encoding="utf-8")
    assert written.startswith("Version 1\nACCEPTED\n")
    assert "File good_min.csv" in written


def test_utf8_bom_and_header_spelling(tmp_path):
    raw = (SAMPLES / "good_min.csv").read_bytes()
    path = tmp_path / "bom.csv"
    path.write_bytes(b"\xef\xbb\xbf" + raw)
    result = validator.validate_path(path, _declaration(), "SAMPLE", 1, date(2027, 5, 10))
    assert result.accepted is True
    assert result.rows[0]["part_number"] == "001234"

    titled = _run(
        [
            {
                "Distributor Id": "SAMPLE",
                "Dealer Id": "DEALER1",
                "Part Number": "00055",
                "Quantity": "1",
                "Period": "2027-04",
            }
        ]
    )
    assert titled.accepted is True
    assert titled.rows[0]["part_number"] == "00055"


def test_xlsx_keeps_a_text_part_number_and_a_currency_format():
    openpyxl = pytest.importorskip("openpyxl")
    workbook = openpyxl.Workbook()
    sheet = workbook.active
    sheet.append(["distributor_id", "dealer_id", "part_number", "quantity", "period", "comment"])
    sheet.append(["SAMPLE", "DEALER1", "00123", 3, "2027-04", 2])
    sheet.cell(2, 3).value = "00123"
    sheet.cell(2, 3).number_format = "@"
    sheet.cell(2, 6).number_format = '"£"#,##0'
    buffer = io.BytesIO()
    workbook.save(buffer)
    workbook.close()
    parsed = validator.parse_table_bytes(buffer.getvalue(), ".xlsx")
    assert parsed.rows[0]["part_number"] == "00123"
    assert "£" in parsed.rows[0]["comment"]
    result = validator.validate(
        parsed.rows,
        _declaration(),
        "SAMPLE",
        1,
        date(2027, 5, 10),
        "b" * 64,
        headers=parsed.headers,
        raw_headers=parsed.raw_headers,
    )
    assert result.rows[0]["part_number"] == "00123"
    assert result.accepted is False
    assert _ids(result, "V018")[0].stops is True


def test_xlsx_without_openpyxl_names_the_missing_library(monkeypatch):
    monkeypatch.setitem(sys.modules, "openpyxl", None)
    csv_rows = validator.parse_table_bytes(
        b"distributor_id,dealer_id,part_number,quantity,period\nSAMPLE,DEALER1,001,1,2027-04\n",
        ".csv",
    )
    assert csv_rows.rows[0]["part_number"] == "001"
    with pytest.raises(RuntimeError, match="openpyxl"):
        validator.parse_table_bytes(b"", ".xlsx")


def test_dollar_symbol_in_a_cell_stops():
    result = _run([_row(bin="box $ left")])
    assert result.accepted is False
    assert _ids(result, "V018")[0].stops is True
    assert _ids(result, "V003") == []

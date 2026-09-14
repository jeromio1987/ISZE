"""EPC supersession validator — never fake MATCH when export is missing."""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import pytest

from scripts import validate_supersession_epc as v


def test_discover_missing_is_none(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(v, "search_dirs", lambda: [tmp_path])
    path, searched = v.discover_epc_export(None)
    assert path is None
    assert searched
    assert all("MATCH" not in s for s in searched)


def test_blocked_meta_never_match(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(v, "OUT_META", tmp_path / "pn_supersession_epc_validation.meta.json")
    summary = v.write_blocked_meta(
        map_pn_count=925,
        searched=["/tmp/missing.xlsx"],
        ie40_check={"status": "INTERNAL_IE40_CHECK", "epc_validated": False},
    )
    assert summary["status"] == "BLOCKED_NO_EPC_EXPORT"
    assert summary["match"] == 0
    assert summary["epc_validated"] is False
    payload = json.loads((tmp_path / "pn_supersession_epc_validation.meta.json").read_text())
    assert payload["status"] == "BLOCKED_NO_EPC_EXPORT"
    assert payload["match"] == 0
    assert payload["internal_ie40_check"]["status"] == "INTERNAL_IE40_CHECK"
    assert payload["internal_ie40_check"]["epc_validated"] is False


def test_ie40_check_is_labelled_internal(tmp_path: Path) -> None:
    map_df = pd.DataFrame(
        {
            "old_pn": ["111", "222"],
            "current_pn": ["111N", "999"],
        }
    )
    pq = tmp_path / "ie40.parquet"
    pd.DataFrame(
        {
            "part_number": ["0000000111", "222"],
            "newest_pn": ["111N", "222N"],
        }
    ).to_parquet(pq, index=False)
    result = v.ie40_integrity_check(map_df, pq)
    assert result["status"] == "INTERNAL_IE40_CHECK"
    assert result["epc_validated"] is False
    assert result["newest_pn_agrees"] == 1
    assert result["newest_pn_differs"] == 1
    assert "not EPC-validated" in result["note"]


def test_epc_match_only_when_export_agrees(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(v, "OUT_CSV", tmp_path / "val.csv")
    monkeypatch.setattr(v, "OUT_META", tmp_path / "val.meta.json")
    map_df = pd.DataFrame(
        {
            "old_pn": ["AAA", "BBB"],
            "current_pn": ["AAA-NEW", "BBB-NEW"],
            "billed_on_old_pn_eur": ["1", "2"],
            "old_description": ["a", "b"],
        }
    )
    epc_path = tmp_path / "epc.csv"
    epc_path.write_text("old_pn,new_pn\nAAA,AAA-NEW\n", encoding="utf-8")
    epc_next = v._load_epc(epc_path, "old_pn", "new_pn")
    summary = v.validate_against_epc(map_df, epc_next, epc_path)
    assert summary["match"] == 1
    assert summary["not_found"] == 1
    out = pd.read_csv(tmp_path / "val.csv", dtype=str)
    assert set(out["verdict"]) == {"MATCH", "NOT_FOUND"}

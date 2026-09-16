from __future__ import annotations

import json

import pandas as pd
import pytest

from scripts import build_risk_cockpit_viz as risk


@pytest.mark.parametrize(
    ("percentile", "network_size", "expected"),
    [
        (100.0, 18, 1),
        (88.235294, 18, 3),
        (0.0, 18, 18),
        (50.0, 1, 1),
    ],
)
def test_league_rank_uses_network_size(percentile, network_size, expected):
    assert risk._league_rank(percentile, network_size) == expected


def test_network_bump_keeps_higher_is_better_percentiles(tmp_path, monkeypatch):
    rows = []
    for metric in ("gps_spu", "total_capture", "genuine_capture", "aim_risk"):
        for code, percentile in (("BEST", 100.0), ("MID", 50.0), ("WORST", 0.0)):
            rows.append(
                {
                    "distributor_code": code,
                    "year": 2025,
                    "metric": metric,
                    "percentile_rank": percentile,
                    "n_distributors": 3,
                }
            )
    source = tmp_path / "network_percentile.csv"
    pd.DataFrame(rows).to_csv(source, index=False)
    monkeypatch.setattr(risk, "NETWORK_PCT_CSV", source)

    payload = risk._network_bump(2025)

    for metric in payload["metrics"]:
        ranks = {
            line["distributor_code"]: line["points"][0]["rank"]
            for line in metric["lines"]
        }
        assert ranks == {"BEST": 1, "MID": 2, "WORST": 3}


def test_write_payload_keeps_json_and_embedded_data_in_sync(tmp_path, monkeypatch):
    out_json = tmp_path / "viz" / "risk_cockpit.json"
    out_js = tmp_path / "sales" / "risk_cockpit.data.js"
    monkeypatch.setattr(risk, "VIZ_DIR", out_json.parent)
    monkeypatch.setattr(risk, "OUT_JSON", out_json)
    monkeypatch.setattr(risk, "OUT_JS", out_js)
    payload = {"_meta": {"generated": "2026-07-26T00:00:00Z"}, "value": float("nan")}

    risk.write_payload(payload)

    json_payload = json.loads(out_json.read_text(encoding="utf-8"))
    embedded = out_js.read_text(encoding="utf-8")
    embedded_json = embedded.split("window.__RISK_COCKPIT_DATA__ = ", 1)[1].removesuffix(";\n")
    assert json.loads(embedded_json) == json_payload
    assert json_payload["value"] is None

from __future__ import annotations

import json

from scripts import build_risk_cockpit_viz as risk


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

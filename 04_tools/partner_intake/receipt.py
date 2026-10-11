"""Plain receipt for one checked file.

The dict is for a program. The text block is what a person can send.
No markdown and no bold.
"""

from __future__ import annotations

from pathlib import Path

try:
    from . import validator
except ImportError:
    import validator

NOT_CHECKED = "not checked, text not in the local spec"


def as_dict(result: validator.ValidationResult) -> dict:
    receipt = {
        "version": result.file_version,
        "result": "ACCEPTED" if result.accepted else "NOT ACCEPTED",
        "distributor_id": result.drop_distributor_id,
        "received": result.received.isoformat(),
        "sha256": result.content_sha256,
        "findings": [
            {
                "rule_id": item.rule_id,
                "severity": item.severity,
                "stops": item.stops,
                "message": item.message,
                "action": item.action,
            }
            for item in result.findings
        ],
        "not_checked": [
            {"rule_id": rule_id, "note": NOT_CHECKED} for rule_id in result.not_checked
        ],
    }
    if result.period:
        receipt["period"] = result.period
    if result.source_name:
        receipt["file"] = result.source_name
    return receipt


def as_text(result: validator.ValidationResult) -> str:
    receipt = as_dict(result)
    lines = [
        f"Version {receipt['version']}",
        receipt["result"],
    ]
    if receipt.get("file"):
        lines.append(f"File {receipt['file']}")
    lines.append(f"Distributor {receipt['distributor_id']}")
    if receipt.get("period"):
        lines.append(f"Period {receipt['period']}")
    lines.append(f"Received {receipt['received']}")
    lines.append(f"SHA256 {receipt['sha256']}")
    lines.append("")
    for item in result.findings:
        lines.append(f"Rule {item.rule_id}: {_pair(item.message, item.action)}")
    lines.append("")
    names = ", ".join(rule_id for rule_id in result.not_checked)
    lines.append(f"{NOT_CHECKED}: {names}.")
    lines.append("")
    return "\n".join(lines)


def write_text(path: Path | str, result: validator.ValidationResult) -> None:
    Path(path).write_text(as_text(result), encoding="utf-8", newline="\n")


def _pair(message: str, action: str) -> str:
    msg = message.strip()
    act = action.strip()
    if msg[-1:] not in ".!?":
        msg += "."
    if act[-1:] not in ".!?":
        act += "."
    return f"{msg} {act}"

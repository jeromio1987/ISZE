"""Run logging and tracking.

Every run writes a self-contained, timestamped folder:

    runs/<UTC stamp>__<kind>__<scenario>/
        config_resolved.yaml   exact config used, after overrides
        inputs.json            source files + their sha256, so a run is reproducible
        <outputs>.csv
        summary.md             human-readable

and appends one line to runs/REGISTRY.csv.

Point: any number this engine ever produces can be traced back to the exact
config and the exact input bytes that produced it.
"""
from __future__ import annotations

import csv
import hashlib
import json
import platform
import subprocess
from datetime import datetime, timezone
from pathlib import Path

import yaml

REGISTRY_COLS = [
    "run_id", "utc", "kind", "scenario", "config_sha", "input_sha",
    "rows", "headline", "git_rev", "note",
]


def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    h.update(Path(p).read_bytes())
    return h.hexdigest()[:16]


def sha256_obj(o) -> str:
    return hashlib.sha256(
        json.dumps(o, sort_keys=True, default=str).encode()
    ).hexdigest()[:16]


def _git_rev(root: Path) -> str:
    try:
        return subprocess.run(
            ["git", "-C", str(root), "rev-parse", "--short", "HEAD"],
            capture_output=True, text=True, timeout=5,
        ).stdout.strip() or "nogit"
    except Exception:
        return "nogit"


class Run:
    def __init__(self, root: Path, cfg: dict, kind: str, scenario: str = "default",
                 note: str = ""):
        self.root = Path(root)
        self.cfg = cfg
        self.kind = kind
        self.scenario = scenario
        self.note = note
        self.utc = datetime.now(timezone.utc)
        stamp = self.utc.strftime("%Y%m%dT%H%M%SZ")
        self.run_id = f"{stamp}__{kind}__{scenario}"

        self.dir = self.root / cfg["runlog"]["dir"] / self.run_id
        self.dir.mkdir(parents=True, exist_ok=True)

        self.config_sha = sha256_obj(cfg)
        (self.dir / "config_resolved.yaml").write_text(
            yaml.safe_dump(cfg, sort_keys=False), encoding="utf-8")

        self._inputs: dict[str, str] = {}
        self._tables: dict[str, object] = {}
        self._headline = ""

    def input(self, name: str, path: Path) -> Path:
        """Register an input file and hash it."""
        p = Path(path)
        self._inputs[name] = f"{p}::{sha256_file(p) if p.exists() else 'MISSING'}"
        return p

    def table(self, name: str, df) -> None:
        df.to_csv(self.dir / f"{name}.csv", index=False)
        self._tables[name] = len(df)

    def headline(self, text: str) -> None:
        self._headline = text

    def close(self, summary_md: str = "") -> Path:
        (self.dir / "inputs.json").write_text(
            json.dumps({"inputs": self._inputs, "tables": self._tables,
                        "python": platform.python_version()}, indent=2),
            encoding="utf-8")

        if self.cfg["runlog"].get("write_summary_md", True):
            head = (f"# {self.run_id}\n\n"
                    f"- **kind** {self.kind} · **scenario** {self.scenario}\n"
                    f"- **utc** {self.utc.isoformat()}\n"
                    f"- **config sha** `{self.config_sha}`\n"
                    f"- **headline** {self._headline}\n\n")
            (self.dir / "summary.md").write_text(head + summary_md, encoding="utf-8")

        reg = self.root / self.cfg["runlog"]["registry"]
        reg.parent.mkdir(parents=True, exist_ok=True)
        new = not reg.exists()
        with reg.open("a", newline="", encoding="utf-8") as fh:
            w = csv.DictWriter(fh, fieldnames=REGISTRY_COLS)
            if new:
                w.writeheader()
            w.writerow({
                "run_id": self.run_id, "utc": self.utc.isoformat(),
                "kind": self.kind, "scenario": self.scenario,
                "config_sha": self.config_sha,
                "input_sha": sha256_obj(self._inputs),
                "rows": sum(self._tables.values()) if self._tables else 0,
                "headline": self._headline,
                "git_rev": _git_rev(self.root), "note": self.note,
            })
        return self.dir


def load_config(path: Path, overrides: dict | None = None) -> dict:
    """Load config.yaml and apply dotted-key overrides, e.g.
    {"allocation.target": 0.02}. Overrides are what scenarios are built from.

    After overrides, merge Eucon brand-tier % ceilings into
    allocation.policy_premium.by_category (iam_derived where n>=3).
    """
    cfg = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    for dotted, val in (overrides or {}).items():
        node = cfg
        *parents, leaf = dotted.split(".")
        for k in parents:
            node = node.setdefault(k, {})
        node[leaf] = val

    # Brand-quality ceilings (Jerome % matrix) — soft-fail if feeds missing
    try:
        from .premiums import apply_ceilings_to_config_block, OEM_PEERS

        pp = cfg.setdefault("allocation", {}).setdefault("policy_premium", {})
        by_cat = pp.get("by_category", {})
        basket_rel = (cfg.get("paths") or {}).get("oem_peer_basket")
        basket_p = None
        if basket_rel:
            basket_p = Path(basket_rel)
            if not basket_p.is_absolute():
                # config.yaml lives in isze_pricing/ → parents[2] = workspace root
                basket_p = Path(path).resolve().parents[2] / basket_rel
        pp["by_category"] = apply_ceilings_to_config_block(
            by_cat, oem_basket_path=basket_p
        )
        cfg.setdefault("oem_peers", OEM_PEERS)
    except Exception as exc:  # noqa: BLE001 — run still valid, just flat premiums
        cfg.setdefault("_warnings", []).append(f"premiums_merge_skipped: {exc}")
    return cfg

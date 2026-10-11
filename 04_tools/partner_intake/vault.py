"""Original files for partner intake.

A file is fingerprinted with sha256. The original bytes are stored once and
never edited. A later call with the same fingerprint returns the stored record
and does not write a second copy. Checking is done on a copy.
"""

from __future__ import annotations

import hashlib
import json
import shutil
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

DEFAULT_ROOT = Path(__file__).resolve().parent / "_vault"


def fingerprint(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


@dataclass(frozen=True)
class StoredOriginal:
    distributor_id: str
    period: str
    version: int
    sha256: str
    byte_size: int
    received_at: str
    path: Path
    added: bool


class Vault:
    def __init__(self, root: Path | str | None = None) -> None:
        self.root = Path(root) if root is not None else DEFAULT_ROOT

    def store(
        self,
        distributor_id: str,
        period: str,
        version: int,
        data: bytes,
        received_at: str | None = None,
    ) -> StoredOriginal:
        distributor_id = _component(distributor_id, "distributor_id")
        period = _component(period, "period")
        version = _version(version)
        if not isinstance(data, (bytes, bytearray)):
            raise TypeError("data must be bytes")
        data = bytes(data)
        digest = fingerprint(data)
        when = received_at if received_at is not None else _now()
        if not isinstance(when, str) or not when:
            raise ValueError("received_at must be a non-empty string")

        existing = self._find(distributor_id, digest)
        if existing is not None:
            return existing

        folder = self._folder(distributor_id)
        folder.mkdir(parents=True, exist_ok=True)
        bin_path = folder / f"{period}_v{version}_{digest[:12]}.bin"
        side_path = bin_path.with_suffix(".json")
        if bin_path.exists():
            raise FileExistsError(f"refusing to overwrite stored original {bin_path}")
        if side_path.exists():
            raise FileExistsError(f"refusing to overwrite stored sidecar {side_path}")

        with bin_path.open("xb") as handle:
            handle.write(data)
        meta = {
            "received_at": when,
            "declared_version": version,
            "period": period,
            "sha256": digest,
            "byte_size": len(data),
        }
        try:
            with side_path.open("x", encoding="utf-8") as handle:
                json.dump(meta, handle, indent=2)
                handle.write("\n")
        except Exception:
            # The original bytes are already the stored file. Leave them.
            raise
        return self._load(distributor_id, side_path, added=True)

    def copy_for_check(self, record: StoredOriginal, dest: Path | str) -> Path:
        """Write a copy for checking. The stored original is not opened for write."""
        dest = Path(dest)
        if dest.resolve() == Path(record.path).resolve():
            raise ValueError("refusing to overwrite the stored original")
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(record.path, dest)
        return dest

    def _find(self, distributor_id: str, digest: str) -> StoredOriginal | None:
        folder = self._folder(distributor_id)
        if not folder.is_dir():
            return None
        for side_path in sorted(folder.glob("*.json")):
            try:
                meta = json.loads(side_path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                continue
            if meta.get("sha256") == digest:
                return self._load(distributor_id, side_path, added=False)
        for bin_path in sorted(folder.glob("*.bin")):
            try:
                on_disk = bin_path.read_bytes()
            except OSError:
                continue
            if fingerprint(on_disk) != digest:
                continue
            side_path = bin_path.with_suffix(".json")
            if side_path.is_file():
                return self._load(distributor_id, side_path, added=False)
            return StoredOriginal(
                distributor_id=distributor_id,
                period=_parse_bin_name(bin_path.name)[0],
                version=_parse_bin_name(bin_path.name)[1],
                sha256=digest,
                byte_size=len(on_disk),
                received_at="",
                path=bin_path,
                added=False,
            )
        return None

    def _load(self, distributor_id: str, side_path: Path, added: bool) -> StoredOriginal:
        meta = json.loads(side_path.read_text(encoding="utf-8"))
        bin_path = side_path.with_suffix(".bin")
        on_disk = bin_path.read_bytes()
        digest = fingerprint(on_disk)
        if digest != meta.get("sha256"):
            raise RuntimeError(f"stored original does not match its fingerprint: {bin_path}")
        return StoredOriginal(
            distributor_id=distributor_id,
            period=str(meta["period"]),
            version=int(meta["declared_version"]),
            sha256=digest,
            byte_size=int(meta["byte_size"]),
            received_at=str(meta["received_at"]),
            path=bin_path,
            added=added,
        )

    def _folder(self, distributor_id: str) -> Path:
        folder = (self.root / distributor_id / "originals").resolve()
        root = self.root.resolve()
        if root != folder and root not in folder.parents:
            raise ValueError("distributor path escapes the vault")
        return folder


def _component(value: str, label: str) -> str:
    if not isinstance(value, str) or not value or value in {".", ".."}:
        raise ValueError(f"{label} is empty")
    if any(ch in value for ch in ("/", "\\", "\x00", ":", "|")):
        raise ValueError(f"{label} must be a single path segment")
    return value


def _version(version: int) -> int:
    if isinstance(version, bool) or not isinstance(version, int) or version < 1:
        raise ValueError("version must be a positive integer")
    return version


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _parse_bin_name(name: str) -> tuple[str, int, str]:
    period, ver, prefix = Path(name).stem.rsplit("_", 2)
    if not ver.startswith("v"):
        raise ValueError(f"unrecognised original name: {name}")
    return period, int(ver[1:]), prefix

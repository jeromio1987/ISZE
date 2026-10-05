#!/usr/bin/env python3
"""
Classification Release Guard

Ensures Isuzu Universe builds use a frozen, approved parts-classification release.
Detects silent pipeline changes to the classification file.

Usage:
  python check_classification_release.py [file_path]

  If file_path is omitted, checks the approved release path from RELEASES.json.

  Exits 0 if the file hash matches the approved release.
  Exits 1 if hash does not match, status is not APPROVED, or file not found.

Importable:
  from check_classification_release import assert_release
  assert_release('/path/to/file.csv')  # raises AssertionError if not approved
"""

import json
import hashlib
import sys
import os
from pathlib import Path


def get_releases_path():
    """Get the path to RELEASES.json in the same directory as this script."""
    script_dir = Path(__file__).parent.absolute()
    return script_dir / "RELEASES.json"


def compute_file_hash(file_path):
    """Compute SHA-256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest().lower()


def load_releases():
    """Load RELEASES.json."""
    releases_path = get_releases_path()
    with open(releases_path, "r") as f:
        return json.load(f)


def find_approved_release(releases):
    """Find the approved release from the candidates list."""
    for candidate in releases.get("candidates", []):
        if candidate.get("status") == "APPROVED":
            return candidate
    return None


def resolve_release_path(candidate):
    """Resolve the candidate's path relative to the releases directory."""
    releases_dir = get_releases_path().parent
    candidate_path = candidate.get("path", "")

    if candidate_path.startswith("../"):
        # Relative path from releases dir
        return (releases_dir / candidate_path).resolve()
    else:
        # File in releases dir
        return (releases_dir / candidate_path).resolve()


def check_release(file_path=None):
    """
    Check if the given file matches the approved release.

    Args:
        file_path: Path to the file to check. If None, uses the approved release's path.

    Returns:
        tuple: (is_valid, message)
        is_valid: True if hash matches and status is APPROVED
        message: Human-readable status message
    """
    try:
        releases = load_releases()
    except FileNotFoundError:
        return False, f"RELEASES.json not found at {get_releases_path()}"
    except json.JSONDecodeError as e:
        return False, f"RELEASES.json is invalid JSON: {e}"

    approved = find_approved_release(releases)
    if not approved:
        return False, "No APPROVED release found in RELEASES.json. Status must be changed to APPROVED before use."

    # Resolve the file path to check
    if file_path:
        check_path = Path(file_path).resolve()
    else:
        check_path = resolve_release_path(approved)

    if not check_path.exists():
        return False, f"File not found: {check_path}"

    try:
        actual_hash = compute_file_hash(str(check_path))
    except Exception as e:
        return False, f"Failed to compute file hash: {e}"

    expected_hash = approved.get("sha256", "").lower()
    release_id = approved.get("release_id", "unknown")

    if actual_hash != expected_hash:
        return False, (
            f"Hash mismatch for {check_path.name}\n"
            f"  Expected (release {release_id}): {expected_hash}\n"
            f"  Actual:                        {actual_hash}\n"
            f"  This file does not match the approved classification release."
        )

    return True, f"OK: {check_path.name} matches approved release {release_id} ({expected_hash[:12]}...)"


def assert_release(file_path):
    """
    Assert that a file matches the approved classification release.

    Raises AssertionError if the file does not match.
    Useful for import into build scripts:

        from check_classification_release import assert_release
        assert_release('01_data/00_derived/aim_pn_classification_20260920.csv')

    Args:
        file_path: Path to the file to check

    Raises:
        AssertionError: If hash does not match or no APPROVED release exists
    """
    is_valid, message = check_release(file_path)
    if not is_valid:
        raise AssertionError(f"Classification release check failed:\n{message}")


def main():
    """Command-line interface."""
    file_path = sys.argv[1] if len(sys.argv) > 1 else None

    is_valid, message = check_release(file_path)
    print(message)

    sys.exit(0 if is_valid else 1)


if __name__ == "__main__":
    main()

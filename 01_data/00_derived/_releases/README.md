# Classification Release Guard

**Status (2026-10-02):** release `2026-10-02` APPROVED by Jerome on 2026-10-02 (sha256 `0ac91379...`); `2026-09-20` SUPERSEDED (hash and approval record kept); `2026-09-24-candidate` NOT_RELEASED. RELEASES.json is the source of truth; the sections below describe the 24 Sep setup.

**pr00 copy-integrity reference:** `pr00_classification_reference_20260920.csv` (+ `.meta.json`), the exact bytes of `pr00_classification.csv` at git c813330f (20 Sep), read-only, sha256 `98e64b5b...`. Jerome decided 2026-10-02 that the gate's `pr00_copy_integrity` measures against this pinned copy, not today's pr00, which carries the 21 Sep regression (1,660 rows). The gate re-hashes it and re-measures; a moved reference fails the check. Built by `01_data/91_build/pin_pr00_reference_20260920.py`.

## Overview

This folder contains the release guard infrastructure for the Isuzu Universe parts-classification file. It ensures that once a release is approved, the build pipeline cannot silently change the classification without an explicit update to RELEASES.json.

## Files

- **`aim_pn_classification_release_2026-09-20.csv`** — Frozen copy of the recommended release (read-only). SHA-256: `60111c104ddeb466e6c15f084039639d35172056b0fd2ea10225a3c50da610e0`. 164,908 rows.

- **`RELEASES.json`** — Manifest of release candidates with SHA-256 hashes, row counts, and status. Two candidates:
  - `2026-09-20`: PENDING_APPROVAL, recommended by Isuzu Universe memo
  - `2026-09-24-candidate`: NOT_RELEASED, contains EXPORT.XLSX classifications from 24 Sep; needs re-test

- **`check_classification_release.py`** — Guard script that verifies the approved release's hash. Exit 0 if valid, exit 1 if not approved, hash mismatch, or file not found. Importable as `assert_release(path)` for build scripts.

## Integration: Adding the Guard to Isuzu Universe Builds

Once Jerome approves a release, add this 2-line snippet to **Isuzu Universe\_build_final\build.py** at the top of the main build function:

```python
from isze_release_guard import assert_release
assert_release('../../01_data/00_derived/aim_pn_classification_<APPROVED_ID>.csv')
```

Replace `<APPROVED_ID>` with the approved release_id from RELEASES.json (e.g., `2026-09-20`).

The script will:
- Exit non-zero if the file's hash does not match RELEASES.json
- Exit non-zero if the status in RELEASES.json is not "APPROVED"
- Exit 0 and continue if the guard passes

This prevents accidental overwrites during pipeline re-runs.

## Decision Required

**Q:** Freeze the 2026-09-20 release (recommended, stable), or re-test and freeze the 2026-09-24-candidate (adds 1,197 EXPORT.XLSX classifications)?

See Isuzu Universe\01_Strategy\CLASSIFICATION_RELEASE_DECISION_2026-09.md for full decision context.

## Technical Details

The frozen release is stored read-only in this folder. Its path is recorded in RELEASES.json so the build pipeline can reference it by release_id rather than by changing paths in build.py. When a release is approved, only the status in RELEASES.json changes; no files move.

For the Python import path, use a relative reference:
```python
import sys
from pathlib import Path
releases_dir = Path(__file__).parent.parent / '01_data' / '00_derived' / '_releases'
sys.path.insert(0, str(releases_dir))
from check_classification_release import assert_release
```

Or, if a symlink to this folder exists in the build script's directory, the simpler form above works.

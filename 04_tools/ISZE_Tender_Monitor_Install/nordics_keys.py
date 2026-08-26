"""
Nordics API key loader for ISZE Tender Monitor (Norway Doffin + Finland HILMA).

Load order (first non-empty wins per key):
  1. Process environment (ISZE_DOFFIN_API_KEY / ISZE_HILMA_API_KEY)
  2. Sibling file nordics_api_keys.env (gitignored)

Never embed real keys in source. See NORDICS_API_KEYS.md.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Dict, Optional

_DIR = Path(__file__).resolve().parent
ENV_FILE = _DIR / "nordics_api_keys.env"
EXAMPLE_FILE = _DIR / "nordics_api_keys.env.example"

DOFFIN_ENV = "ISZE_DOFFIN_API_KEY"
HILMA_ENV = "ISZE_HILMA_API_KEY"

# Canonical Public API gateways (search/download — not eSender write APIs)
DOFFIN_SEARCH_URL = "https://dof-notices-prod-api.azure-api.net/public/v2/search"
DOFFIN_PORTAL = "https://dof-notices-prod-api.developer.azure-api.net/"
# Prod gateway host is api.hankintailmoitukset.fi (not *.azure-api.net).
# Search notices = Azure Cognitive Search over the eForms index.
HILMA_SEARCH_URL = "https://api.hankintailmoitukset.fi/avp/eformnotices/docs/search"
HILMA_NOTICES_URL = HILMA_SEARCH_URL  # alias kept for older imports / verify
HILMA_PORTAL = "https://hns-hilma-prod-apim.developer.azure-api.net/"

_file_cache: Optional[Dict[str, str]] = None


def _parse_env_file(path: Path) -> Dict[str, str]:
    out: Dict[str, str] = {}
    if not path.is_file():
        return out
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return out
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, val = line.partition("=")
        key = key.strip()
        val = val.strip().strip('"').strip("'")
        if key and val:
            out[key] = val
    return out


def _file_keys() -> Dict[str, str]:
    global _file_cache
    if _file_cache is None:
        _file_cache = _parse_env_file(ENV_FILE)
    return _file_cache


def reload() -> None:
    """Clear cached file parse (tests / after editing the env file)."""
    global _file_cache
    _file_cache = None


def _resolve(env_name: str) -> str:
    from_env = (os.environ.get(env_name) or "").strip()
    if from_env:
        return from_env
    return (_file_keys().get(env_name) or "").strip()


def get_doffin_key() -> str:
    return _resolve(DOFFIN_ENV)


def get_hilma_key() -> str:
    return _resolve(HILMA_ENV)


def status_report() -> Dict[str, object]:
    """Presence + source only — never includes key values."""
    def _one(env_name: str) -> Dict[str, object]:
        if (os.environ.get(env_name) or "").strip():
            return {"present": True, "source": "process_env"}
        if (_file_keys().get(env_name) or "").strip():
            return {"present": True, "source": "nordics_api_keys.env"}
        return {"present": False, "source": None}

    return {
        "env_file": str(ENV_FILE),
        "env_file_exists": ENV_FILE.is_file(),
        "doffin": _one(DOFFIN_ENV),
        "hilma": _one(HILMA_ENV),
        "doffin_search_url": DOFFIN_SEARCH_URL,
        "hilma_notices_url": HILMA_NOTICES_URL,
        "doffin_portal": DOFFIN_PORTAL,
        "hilma_portal": HILMA_PORTAL,
    }


def missing_key_banner(source: str) -> str:
    """Loud multi-line message when a Nordics key is absent."""
    if source == "doffin":
        return (
            "\n"
            + "=" * 72
            + "\n"
            "[Doffin] MISSING API KEY -- Norway will be SKIPPED\n"
            f"  1. Sign up / subscribe (Public API): {DOFFIN_PORTAL}\n"
            "  2. Copy Primary key into nordics_api_keys.env as ISZE_DOFFIN_API_KEY\n"
            "     (copy from nordics_api_keys.env.example -- see NORDICS_API_KEYS.md)\n"
            "  3. Verify:  python verify_nordics_keys.py\n"
            + "=" * 72
        )
    return (
        "\n"
        + "=" * 72
        + "\n"
        "[HILMA] MISSING API KEY -- Finland will be SKIPPED\n"
        f"  1. Sign up / subscribe AVP-Read (free): {HILMA_PORTAL}\n"
        "  2. Copy Primary key into nordics_api_keys.env as ISZE_HILMA_API_KEY\n"
        "     (copy from nordics_api_keys.env.example -- see NORDICS_API_KEYS.md)\n"
        "  3. Verify:  python verify_nordics_keys.py\n"
        + "=" * 72
    )


if __name__ == "__main__":
    import json

    print(json.dumps(status_report(), indent=2))

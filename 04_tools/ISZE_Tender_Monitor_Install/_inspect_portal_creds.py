"""Inspect Chrome Login Data / cookies for Nordics portals (no secret printing)."""
from __future__ import annotations

import base64
import json
import shutil
import sqlite3
import tempfile
from pathlib import Path

import win32crypt
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

USER = Path.home() / r"AppData\Local\Google\Chrome\User Data"
LOCAL_STATE = USER / "Local State"
LOGIN = USER / "Default" / "Login Data"
COOKIES = Path(tempfile.gettempdir()) / "isze-nordics-chrome-profile" / "Default" / "Network" / "Cookies"


def key() -> bytes:
    enc = base64.b64decode(json.loads(LOCAL_STATE.read_text(encoding="utf-8"))["os_crypt"]["encrypted_key"])
    return win32crypt.CryptUnprotectData(enc[5:], None, None, None, 0)[1]


def dec(k: bytes, blob: bytes) -> str:
    if not blob:
        return ""
    if blob[:3] in (b"v10", b"v20"):
        return AESGCM(k).decrypt(blob[3:15], blob[15:], None).decode("utf-8", "replace")
    try:
        return win32crypt.CryptUnprotectData(blob, None, None, None, 0)[1].decode("utf-8", "replace")
    except Exception:
        return ""


def main():
    k = key()
    print("=== cookies (names only) ===")
    if COOKIES.exists():
        con = sqlite3.connect(str(COOKIES))
        for host, name in con.execute("select host_key, name from cookies order by host_key, name"):
            if any(x in (host or "") for x in ("azure", "doffin", "hilma", "microsoft", "live.com", "login")):
                print(f"  {host} :: {name}")
        con.close()
    else:
        print("no cookie db")

    print("\n=== login data matches (username only, password len) ===")
    if not LOGIN.exists():
        print("no Login Data")
        return
    tmp = Path(tempfile.gettempdir()) / "isze-login-data"
    shutil.copy2(LOGIN, tmp)
    con = sqlite3.connect(str(tmp))
    rows = con.execute(
        "select origin_url, username_value, password_value from logins"
    ).fetchall()
    hits = 0
    for origin, user, pwblob in rows:
        o = (origin or "").lower()
        if any(x in o for x in ("dof-notices", "hilma", "azure-api.net", "doffin", "hankintailmoitukset")):
            pw = dec(k, pwblob or b"")
            print(f"  origin={origin} user={user!r} pw_len={len(pw)}")
            hits += 1
    if not hits:
        # broader: any isuzu email saved
        for origin, user, pwblob in rows:
            if user and "isuzu" in user.lower():
                pw = dec(k, pwblob or b"")
                print(f"  isuzu_saved origin={origin} user={user!r} pw_len={len(pw)}")
                hits += 1
    print("hits", hits)
    print("total_logins", len(rows))
    con.close()


if __name__ == "__main__":
    main()

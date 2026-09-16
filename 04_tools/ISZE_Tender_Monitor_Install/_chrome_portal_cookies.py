"""Pull Azure APIM developer-portal session cookies from Chrome and fetch subscription Primary keys."""
from __future__ import annotations

import base64
import json
import shutil
import sqlite3
import tempfile
from pathlib import Path

import requests
import win32crypt
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

CHROME_USER = Path.home() / r"AppData\Local\Google\Chrome\User Data"
LOCAL_STATE = CHROME_USER / "Local State"
COOKIES_CANDIDATES = [
    CHROME_USER / "Default" / "Network" / "Cookies",
    CHROME_USER / "Default" / "Cookies",
]
DOMAINS = [
    "dof-notices-prod-api.developer.azure-api.net",
    "hns-hilma-prod-apim.developer.azure-api.net",
]
ENV_PATH = Path(__file__).resolve().parent / "nordics_api_keys.env"
EXAMPLE = Path(__file__).resolve().parent / "nordics_api_keys.env.example"


def chrome_key() -> bytes:
    data = json.loads(LOCAL_STATE.read_text(encoding="utf-8"))
    enc = base64.b64decode(data["os_crypt"]["encrypted_key"])
    assert enc.startswith(b"DPAPI")
    return win32crypt.CryptUnprotectData(enc[5:], None, None, None, 0)[1]


def decrypt_value(key: bytes, encrypted: bytes) -> str:
    if not encrypted:
        return ""
    # Chrome v80+ : v10 / v20 prefix + nonce + ciphertext
    if encrypted[:3] in (b"v10", b"v20"):
        nonce = encrypted[3:15]
        cipher = encrypted[15:]
        return AESGCM(key).decrypt(nonce, cipher, None).decode("utf-8", errors="replace")
    # legacy DPAPI
    try:
        return win32crypt.CryptUnprotectData(encrypted, None, None, None, 0)[1].decode("utf-8", errors="replace")
    except Exception:
        return ""


def load_cookies(key: bytes) -> dict[str, dict[str, str]]:
    src = next((p for p in COOKIES_CANDIDATES if p.exists()), None)
    if not src:
        raise SystemExit("Chrome Cookies DB not found")
    tmp = Path(tempfile.mkdtemp()) / "Cookies"
    try:
        shutil.copy2(src, tmp)
    except Exception as exc:
        # locked — try again via powershell Copy-Item
        print("copy2 failed", exc)
        shutil.copyfile(src, tmp)

    out: dict[str, dict[str, str]] = {d: {} for d in DOMAINS}
    con = sqlite3.connect(str(tmp))
    cur = con.cursor()
    cur.execute(
        "SELECT host_key, name, encrypted_value, value FROM cookies"
    )
    for host, name, enc, val in cur.fetchall():
        host_n = (host or "").lstrip(".")
        matched = None
        for d in DOMAINS:
            if host_n == d or host_n.endswith("." + d) or d.endswith(host_n):
                matched = d
                break
        if not matched:
            # also catch parent azure-api.net auth cookies
            if "azure-api.net" in host_n or "microsoftonline" in host_n or "live.com" in host_n:
                matched = host_n
                out.setdefault(matched, {})
            else:
                continue
        plain = val or decrypt_value(key, enc or b"")
        if plain:
            out[matched][name] = plain
    con.close()
    return out


def session_for(domain: str, jar: dict[str, dict[str, str]]) -> requests.Session:
    s = requests.Session()
    s.headers.update(
        {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/151.0.0.0 Safari/537.36",
            "Accept": "application/json, text/plain, */*",
        }
    )
    # attach cookies for this domain and related hosts
    for host, cookies in jar.items():
        if domain in host or host in domain or "azure-api.net" in host:
            for name, value in cookies.items():
                s.cookies.set(name, value, domain=host if host.startswith(".") else host)
    return s


def try_endpoints(base: str, s: requests.Session) -> None:
    paths = [
        "/developer/subscriptions",
        "/developer/users/me",
        "/developer/products",
        "/mapi/subscriptions",
        "/mapi/users/me",
        "/api/subscriptions",
        "/profile",
        "/",
    ]
    for p in paths:
        url = base.rstrip("/") + p
        try:
            r = s.get(url, timeout=20, allow_redirects=True)
        except requests.RequestException as e:
            print(base, p, "ERR", e)
            continue
        ct = r.headers.get("Content-Type", "")
        snippet = (r.text or "")[:180].replace("\n", " ")
        print(f"{p} -> {r.status_code} {ct[:40]} len={len(r.content)} snip={snippet!r}")


def main():
    key = chrome_key()
    jar = load_cookies(key)
    print("Cookie hosts with values:")
    for host, cookies in sorted(jar.items()):
        print(f"  {host}: {len(cookies)} cookies names={list(cookies)[:12]}")

    for base in (
        "https://dof-notices-prod-api.developer.azure-api.net",
        "https://hns-hilma-prod-apim.developer.azure-api.net",
    ):
        domain = base.split("//", 1)[1]
        print("\n=== probing", base, "===")
        s = session_for(domain, jar)
        try_endpoints(base, s)


if __name__ == "__main__":
    main()

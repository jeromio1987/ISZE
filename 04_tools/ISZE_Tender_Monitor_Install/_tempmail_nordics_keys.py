"""Sign up Doffin+HILMA using Guerrilla Mail, verify email, capture Primary keys."""
from __future__ import annotations

import json
import os
import re
import time
import urllib.parse
import urllib.request
from pathlib import Path

import requests
import websocket

INSTALL = Path(__file__).resolve().parent
ENV_PATH = INSTALL / "nordics_api_keys.env"
EXAMPLE = INSTALL / "nordics_api_keys.env.example"
CREDS_PATH = INSTALL / "_nordics_portal_login.env"

GM = "https://api.guerrillamail.com/ajax.php"


def gm(params: dict) -> dict:
    r = requests.get(GM, params=params, timeout=30)
    r.raise_for_status()
    return r.json()


def new_mailbox() -> tuple[str, str]:
    data = gm({"f": "get_email_address", "lang": "en"})
    return data["email_addr"], data["sid_token"]


def poll_mail(sid: str, subject_re: str, timeout: int = 180) -> dict | None:
    end = time.time() + timeout
    while time.time() < end:
        inbox = gm({"f": "check_email", "sid_token": sid, "seq": 0})
        for item in inbox.get("list") or []:
            subj = item.get("mail_subject") or ""
            if re.search(subject_re, subj, re.I):
                detail = gm({"f": "fetch_email", "sid_token": sid, "email_id": item["mail_id"]})
                return detail
        print("mail wait...", time.strftime("%H:%M:%S"))
        time.sleep(8)
    return None


def extract_links(html: str) -> list[str]:
    return list(dict.fromkeys(re.findall(r"https?://[^\s\"'<>]+", html or "")))


def ensure_cdp() -> None:
    """Restart dedicated Chrome profile if CDP port is down."""
    import subprocess

    try:
        urllib.request.urlopen("http://127.0.0.1:9222/json/version", timeout=2).read()
        return
    except Exception:
        pass
    chrome = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
    dst = Path(os.environ.get("TEMP", ".")) / "isze-nordics-chrome-profile"
    subprocess.run(["taskkill", "/IM", "chrome.exe", "/F"], capture_output=True)
    time.sleep(2)
    subprocess.Popen(
        [
            chrome,
            "--remote-debugging-port=9222",
            "--remote-allow-origins=*",
            f"--user-data-dir={dst}",
            "--profile-directory=Default",
            "--no-first-run",
            "about:blank",
        ]
    )
    for _ in range(25):
        time.sleep(1)
        try:
            urllib.request.urlopen("http://127.0.0.1:9222/json/version", timeout=1).read()
            print("CDP restarted")
            return
        except Exception:
            continue
    raise RuntimeError("could not start CDP Chrome")


def tabs():
    ensure_cdp()
    return json.load(urllib.request.urlopen("http://127.0.0.1:9222/json", timeout=5))


class CDP:
    def __init__(self, ws_url: str):
        self.ws = websocket.create_connection(ws_url, timeout=60)
        self._id = 0

    def call(self, method: str, params: dict | None = None, timeout: float = 45.0):
        self._id += 1
        mid = self._id
        self.ws.send(json.dumps({"id": mid, "method": method, "params": params or {}}))
        end = time.time() + timeout
        while time.time() < end:
            self.ws.settimeout(max(0.5, end - time.time()))
            try:
                msg = json.loads(self.ws.recv())
            except Exception:
                continue
            if msg.get("id") == mid:
                if "error" in msg:
                    raise RuntimeError(msg["error"])
                return msg.get("result", {})
        raise TimeoutError(method)

    def evaluate(self, expression: str):
        return self.call(
            "Runtime.evaluate",
            {"expression": expression, "returnByValue": True},
        ).get("result", {})

    def navigate(self, url: str):
        self.call("Page.enable")
        self.call("Runtime.enable")
        self.call("Page.navigate", {"url": url})
        for _ in range(50):
            time.sleep(0.4)
            try:
                if self.evaluate("document.readyState").get("value") == "complete":
                    time.sleep(1.0)
                    return
            except Exception:
                time.sleep(0.4)

    def close(self):
        try:
            self.ws.close()
        except Exception:
            pass


def connect(url: str) -> CDP:
    pages = [t for t in tabs() if t.get("type") == "page"]
    cdp = CDP(pages[0]["webSocketDebuggerUrl"])
    cdp.navigate(url)
    cdp.close()
    time.sleep(0.7)
    host = urllib.parse.urlparse(url).netloc
    tab = pages[0]
    for t in tabs():
        if t.get("type") == "page" and host in (t.get("url") or ""):
            tab = t
            if url.rstrip("/") in (t.get("url") or ""):
                break
    return CDP(tab["webSocketDebuggerUrl"])


def signup(base: str, label: str, email: str, password: str) -> str:
    print(f"\n=== {label} SIGNUP {email} ===")
    cdp = connect(base + "/signup")
    cdp.evaluate(
        f"""
        (() => {{
          const set=(id,v)=>{{const el=document.getElementById(id); if(!el) return false;
            el.focus(); el.value=v; el.dispatchEvent(new Event('input',{{bubbles:true}}));
            el.dispatchEvent(new Event('change',{{bubbles:true}})); return true;}};
          set('email', {json.dumps(email)});
          set('password', {json.dumps(password)});
          set('confirmPassword', {json.dumps(password)});
          set('firstName', 'Jerome');
          set('lastName', 'ISZE');
          const box=document.querySelector('input[type=checkbox]');
          if(box){{
            const lab=box.id?document.querySelector('label[for=\"'+box.id+'\"]'):null;
            (lab||box.parentElement||box).click();
          }}
          return document.body.innerText.slice(0,200);
        }})()
        """
    )
    for i in range(25):
        time.sleep(1)
        if cdp.evaluate("document.querySelector('input[type=checkbox]')?.checked===true").get("value"):
            print(label, "POW ok", i)
            break
    cdp.evaluate(
        """
        (() => {
          const bs=[...document.querySelectorAll('button')].filter(b=>/sign up/i.test(b.innerText||''));
          if(bs.length) bs[bs.length-1].click();
          return bs.length;
        })()
        """
    )
    time.sleep(5)
    try:
        after = cdp.evaluate(
            "({url:location.href,body:document.body.innerText.slice(0,700)})"
        ).get("value")
    except Exception:
        cdp.close()
        cdp = connect(base + "/signup")
        after = cdp.evaluate(
            "({url:location.href,body:document.body.innerText.slice(0,700)})"
        ).get("value")
    print(label, "AFTER", after)
    cdp.close()
    return (after or {}).get("body", "")


def open_verify(link: str) -> str:
    print("VERIFY_LINK host", urllib.parse.urlparse(link).netloc)
    cdp = connect(link)
    time.sleep(3)
    try:
        info = cdp.evaluate(
            "({url:location.href,body:document.body.innerText.slice(0,700)})"
        ).get("value")
    except Exception as e:
        info = {"error": str(e)}
    print("VERIFY_AFTER", info)
    cdp.close()
    return (info or {}).get("url", "")


def signin(base: str, email: str, password: str) -> bool:
    cdp = connect(base + "/signin")
    cdp.evaluate(
        f"""
        (() => {{
          const set=(id,v)=>{{const el=document.getElementById(id); if(!el) return false;
            el.value=v; el.dispatchEvent(new Event('input',{{bubbles:true}})); return true;}};
          set('email', {json.dumps(email)});
          set('password', {json.dumps(password)});
          const bs=[...document.querySelectorAll('button')].filter(b=>/^sign in$/i.test((b.innerText||'').trim()));
          if(bs.length) bs[bs.length-1].click();
          return true;
        }})()
        """
    )
    time.sleep(5)
    try:
        body = cdp.evaluate("document.body.innerText").get("value") or ""
        url = cdp.evaluate("location.href").get("value") or ""
    except Exception:
        cdp.close()
        cdp = connect(base + "/profile")
        body = cdp.evaluate("document.body.innerText").get("value") or ""
        url = cdp.evaluate("location.href").get("value") or ""
    print("SIGNIN", url, body[:300].replace("\n", " | "))
    ok = "sign in" not in body.lower()[:120] or "subscription" in body.lower() or "/profile" in url
    cdp.close()
    return ok


def subscribe_and_key(base: str, label: str, product_needles: list[str]) -> str | None:
    cdp = connect(base + "/products")
    body = cdp.evaluate("document.body.innerText").get("value") or ""
    print(label, "products", body[:350].replace("\n", " | "))
    needles_js = json.dumps(product_needles)
    cdp.evaluate(
        f"""
        (() => {{
          const needles={needles_js}.map(s=>s.toLowerCase());
          for (const el of document.querySelectorAll('a,button,h1,h2,h3,div,span')) {{
            const t=(el.innerText||'').trim().toLowerCase();
            if (!t || t.length>80) continue;
            if (needles.some(n=>t.includes(n))) {{ el.click(); return t; }}
          }}
          return null;
        }})()
        """
    )
    time.sleep(2)
    cdp.evaluate(
        """
        (() => {
          const bs=[...document.querySelectorAll('button,a')].filter(b=>/subscribe/i.test(b.innerText||''));
          if (bs[0]) bs[0].click();
          return bs.map(b=>b.innerText.trim()).slice(0,8);
        })()
        """
    )
    time.sleep(3)
    cdp.close()

    cdp = connect(base + "/profile")
    cdp.evaluate(
        """
        (() => {
          for (const el of document.querySelectorAll('a,button,span')) {
            if (/subscriptions/i.test((el.innerText||'').trim())) { el.click(); return true; }
          }
          return false;
        })()
        """
    )
    time.sleep(2)
    for _ in range(10):
        cdp.evaluate(
            """
            (() => {
              let n=0;
              for (const el of document.querySelectorAll('button,a,span')) {
                const t=(el.innerText||'').trim().toLowerCase();
                if (t==='show' || t==='show key' || t==='copy') { el.click(); n++; }
              }
              return n;
            })()
            """
        )
        time.sleep(0.4)
    html = cdp.evaluate("document.documentElement.outerHTML").get("value") or ""
    text = cdp.evaluate("document.body.innerText").get("value") or ""
    cands = set()
    for pat in (
        r"\b[0-9a-fA-F]{32}\b",
        r"\b[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}\b",
        r"\b[A-Za-z0-9]{40,80}\b",
    ):
        cands.update(re.findall(pat, html + "\n" + text))
    blob = (html + "\n" + text).lower()
    best = None
    for c in sorted(cands, key=len, reverse=True):
        idx = blob.find(c.lower())
        window = blob[max(0, idx - 180) : idx + 180]
        if "primary" in window and len(c) >= 32:
            best = c
            break
    if not best:
        for c in sorted(cands, key=len, reverse=True):
            if len(c) >= 32 and re.fullmatch(r"[0-9a-fA-F-]+", c):
                best = c
                break
    print(label, "key_found", bool(best), "len", len(best or ""), "cands", len(cands))
    cdp.close()
    return best


def write_env(doffin: str | None, hilma: str | None):
    lines = []
    for line in EXAMPLE.read_text(encoding="utf-8").splitlines():
        if line.startswith("ISZE_DOFFIN_API_KEY="):
            lines.append(f"ISZE_DOFFIN_API_KEY={doffin or ''}")
        elif line.startswith("ISZE_HILMA_API_KEY="):
            lines.append(f"ISZE_HILMA_API_KEY={hilma or ''}")
        else:
            lines.append(line)
    ENV_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("WROTE_ENV", "doffin", len(doffin or ""), "hilma", len(hilma or ""))


def main():
    email, sid = new_mailbox()
    password = "IszeTemp!" + str(int(time.time()))[-6:] + "Aa1"
    CREDS_PATH.write_text(
        f"EMAIL={email}\nPASSWORD={password}\nSID={sid}\nSOURCE=guerrillamail\n",
        encoding="utf-8",
    )
    print("MAILBOX", email)

    doffin_body = signup(
        "https://dof-notices-prod-api.developer.azure-api.net", "DOFFIN", email, password
    )
    hilma_body = signup(
        "https://hns-hilma-prod-apim.developer.azure-api.net", "HILMA", email, password
    )

    # Verify emails
    for label, subj in (
        ("DOFFIN", r"confirm|verif|account|doffin|api management"),
        ("HILMA", r"confirm|verif|account|hilma|hankinta|api management"),
    ):
        mail = poll_mail(sid, subj, timeout=200)
        if not mail:
            print(label, "NO_VERIFY_MAIL")
            continue
        html = (mail.get("mail_body") or "") + "\n" + (mail.get("mail_excerpt") or "")
        print(label, "MAIL_SUBJ", mail.get("mail_subject"))
        links = [
            L
            for L in extract_links(html)
            if any(
                x in L.lower()
                for x in (
                    "confirm",
                    "verify",
                    "signup",
                    "azure-api.net",
                    "identity",
                    "account",
                )
            )
        ]
        if not links:
            links = extract_links(html)
        print(label, "links", len(links))
        for L in links[:5]:
            if "guerrillamail" in L:
                continue
            open_verify(L)
            break

    # Sign in + subscribe + capture
    signin("https://dof-notices-prod-api.developer.azure-api.net", email, password)
    signin("https://hns-hilma-prod-apim.developer.azure-api.net", email, password)
    doffin = subscribe_and_key(
        "https://dof-notices-prod-api.developer.azure-api.net",
        "DOFFIN",
        ["public api", "public"],
    )
    hilma = subscribe_and_key(
        "https://hns-hilma-prod-apim.developer.azure-api.net",
        "HILMA",
        ["avp-read", "avp"],
    )
    write_env(doffin, hilma)


if __name__ == "__main__":
    main()

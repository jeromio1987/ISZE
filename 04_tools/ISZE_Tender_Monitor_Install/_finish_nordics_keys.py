"""Finish Nordics keys: confirm Doffin email, signup HILMA, subscribe, write env."""
from __future__ import annotations

import json
import os
import re
import subprocess
import time
import urllib.parse
import urllib.request
from pathlib import Path

import requests
import websocket

INSTALL = Path(__file__).resolve().parent
ENV = INSTALL / "nordics_api_keys.env"
EXAMPLE = INSTALL / "nordics_api_keys.env.example"
CREDS = INSTALL / "_nordics_portal_login.env"
GM = "https://api.guerrillamail.com/ajax.php"

CONFIRM_DOFFIN = (
    "https://dof-notices-prod-api.developer.azure-api.net/confirm-v2/identities/basic/signup"
    "?userid=6a8dcd0bea8bbf0e5c432979"
    "&identity=xtdwnoxd%40guerrillamailblock.com"
    "&ticketid=6a8dcd0bea8bbf0e5c43297b"
    "&ticket=749bdf4125c848579695c9b6ed2cfbb2"
)


def load_creds():
    out = {}
    for line in CREDS.read_text(encoding="utf-8").splitlines():
        if "=" in line:
            k, _, v = line.partition("=")
            out[k.strip()] = v.strip()
    return out


def ensure_cdp():
    try:
        urllib.request.urlopen("http://127.0.0.1:9222/json/version", timeout=2).read()
        return
    except Exception:
        pass
    chrome = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
    dst = Path(os.environ["TEMP"]) / "isze-nordics-chrome-profile"
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
    for i in range(25):
        time.sleep(1)
        try:
            urllib.request.urlopen("http://127.0.0.1:9222/json/version", timeout=1).read()
            print("CDP up", i)
            return
        except Exception:
            pass
    raise RuntimeError("CDP failed")


def tabs():
    ensure_cdp()
    return json.load(urllib.request.urlopen("http://127.0.0.1:9222/json", timeout=5))


class CDP:
    def __init__(self, ws_url: str):
        self.ws = websocket.create_connection(ws_url, timeout=60)
        self._id = 0

    def call(self, method, params=None, timeout=45.0):
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
            "Runtime.evaluate", {"expression": expression, "returnByValue": True}
        ).get("result", {})

    def close(self):
        try:
            self.ws.close()
        except Exception:
            pass


def open_url(url: str) -> CDP:
    ensure_cdp()
    ver = json.load(urllib.request.urlopen("http://127.0.0.1:9222/json/version", timeout=5))
    b = CDP(ver["webSocketDebuggerUrl"])
    created = b.call("Target.createTarget", {"url": url})
    tid = created["targetId"]
    b.close()
    time.sleep(2)
    for _ in range(20):
        for t in tabs():
            if t.get("type") == "page" and t.get("id") == tid:
                cdp = CDP(t["webSocketDebuggerUrl"])
                for __ in range(30):
                    time.sleep(0.4)
                    try:
                        if cdp.evaluate("document.readyState").get("value") == "complete":
                            time.sleep(0.8)
                            return cdp
                    except Exception:
                        pass
                return cdp
        time.sleep(0.5)
    # fallback by URL host
    host = urllib.parse.urlparse(url).netloc
    for t in tabs():
        if t.get("type") == "page" and host in (t.get("url") or ""):
            return CDP(t["webSocketDebuggerUrl"])
    raise RuntimeError("no tab for " + url)


def page_info(cdp: CDP):
    return cdp.evaluate(
        "({url:location.href,title:document.title,body:(document.body&&document.body.innerText||'').slice(0,800)})"
    ).get("value")


def signup(base: str, label: str, email: str, password: str):
    print("\n=== SIGNUP", label, "===")
    cdp = open_url(base + "/signup")
    cdp.evaluate(
        f"""
        (() => {{
          const set=(id,v)=>{{const el=document.getElementById(id); if(!el) return false;
            el.value=v; el.dispatchEvent(new Event('input',{{bubbles:true}})); return true;}};
          set('email',{json.dumps(email)});
          set('password',{json.dumps(password)});
          set('confirmPassword',{json.dumps(password)});
          set('firstName','Jerome'); set('lastName','ISZE');
          const box=document.querySelector('input[type=checkbox]');
          if(box){{ const lab=box.id?document.querySelector('label[for=\"'+box.id+'\"]'):null;
            (lab||box.parentElement||box).click(); }}
          return true;
        }})()
        """
    )
    for i in range(20):
        time.sleep(1)
        if cdp.evaluate("!!document.querySelector('input[type=checkbox]')?.checked").get("value"):
            print(label, "POW", i)
            break
    cdp.evaluate(
        "([...document.querySelectorAll('button')].filter(b=>/sign up/i.test(b.innerText||'')).slice(-1)[0]||{{}}); "
        "([...document.querySelectorAll('button')].filter(b=>/sign up/i.test(b.innerText||'')).slice(-1)[0]||{{click(){{}}}}).click()"
    )
    time.sleep(5)
    try:
        info = page_info(cdp)
    except Exception:
        cdp.close()
        cdp = open_url(base + "/signup")
        info = page_info(cdp)
    print(label, info)
    cdp.close()
    return info


def signin(base: str, email: str, password: str):
    print("\n=== SIGNIN", base, "===")
    cdp = open_url(base + "/signin")
    cdp.evaluate(
        f"""
        (() => {{
          const set=(id,v)=>{{const el=document.getElementById(id); if(!el) return false;
            el.value=v; el.dispatchEvent(new Event('input',{{bubbles:true}})); return true;}};
          set('email',{json.dumps(email)}); set('password',{json.dumps(password)});
          const b=[...document.querySelectorAll('button')].find(x=>/^sign in$/i.test((x.innerText||'').trim()));
          if(b) b.click();
          return true;
        }})()
        """
    )
    time.sleep(5)
    try:
        info = page_info(cdp)
    except Exception:
        cdp.close()
        cdp = open_url(base + "/profile")
        info = page_info(cdp)
    print("SIGNIN_RESULT", info)
    cdp.close()
    return info


def capture_key(base: str, label: str, needles: list[str]) -> str | None:
    print("\n=== CAPTURE", label, "===")
    cdp = open_url(base + "/products")
    print("products", page_info(cdp))
    cdp.evaluate(
        f"""
        (() => {{
          const needles={json.dumps(needles)}.map(s=>s.toLowerCase());
          for (const el of document.querySelectorAll('a,button,h1,h2,h3,div,span')) {{
            const t=(el.innerText||'').trim().toLowerCase();
            if(t && t.length<90 && needles.some(n=>t.includes(n))) {{ el.click(); return t; }}
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
          if(bs[0]) bs[0].click();
          return bs.map(b=>b.innerText.trim()).slice(0,6);
        })()
        """
    )
    time.sleep(3)
    cdp.close()

    cdp = open_url(base + "/profile")
    cdp.evaluate(
        """
        (() => {
          for (const el of document.querySelectorAll('a,button,span')) {
            if(/subscriptions/i.test((el.innerText||'').trim())) { el.click(); return true; }
          }
          return false;
        })()
        """
    )
    time.sleep(2)
    for _ in range(12):
        cdp.evaluate(
            """
            (() => {
              let n=0;
              for (const el of document.querySelectorAll('button,a,span')) {
                const t=(el.innerText||'').trim().toLowerCase();
                if(t==='show'||t==='show key'||t==='copy'){ el.click(); n++; }
              }
              return n;
            })()
            """
        )
        time.sleep(0.35)
    html = cdp.evaluate("document.documentElement.outerHTML").get("value") or ""
    text = cdp.evaluate("document.body.innerText").get("value") or ""
    print(label, "profile_snip", text[:400].replace("\n", " | "))
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
        window = blob[max(0, idx - 200) : idx + 200]
        if "primary" in window and len(c) >= 32:
            best = c
            break
    if not best:
        for c in sorted(cands, key=len, reverse=True):
            if len(c) >= 32 and re.fullmatch(r"[0-9a-fA-F-]+", c):
                best = c
                break
    print(label, "picked", bool(best), "len", len(best or ""), "cands", len(cands))
    cdp.close()
    return best


def write_env(doffin, hilma):
    lines = []
    for line in EXAMPLE.read_text(encoding="utf-8").splitlines():
        if line.startswith("ISZE_DOFFIN_API_KEY="):
            lines.append(f"ISZE_DOFFIN_API_KEY={doffin or ''}")
        elif line.startswith("ISZE_HILMA_API_KEY="):
            lines.append(f"ISZE_HILMA_API_KEY={hilma or ''}")
        else:
            lines.append(line)
    ENV.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("WROTE_ENV", len(doffin or ""), len(hilma or ""))


def gm(params):
    return requests.get(GM, params=params, timeout=30).json()


def poll_hilma_confirm(sid: str, timeout=180):
    end = time.time() + timeout
    while time.time() < end:
        inbox = gm({"f": "check_email", "sid_token": sid, "seq": 0})
        for item in inbox.get("list") or []:
            frm = (item.get("mail_from") or "").lower()
            if "apimgmt" in frm or "azure" in frm:
                detail = gm({"f": "fetch_email", "sid_token": sid, "email_id": item["mail_id"]})
                body = detail.get("mail_body") or ""
                if "hilma" in body.lower() or "hns-hilma" in body.lower() or "hankinta" in body.lower():
                    links = re.findall(r'https?://[^\s"\'<>]+', body)
                    for L in links:
                        L = L.replace("&amp;", "&")
                        if "confirm" in L and "hns-hilma" in L:
                            return L
                    for L in links:
                        L = L.replace("&amp;", "&")
                        if "confirm" in L:
                            return L
        print("wait hilma mail...")
        time.sleep(8)
    return None


def main():
    creds = load_creds()
    email, password, sid = creds["EMAIL"], creds["PASSWORD"], creds["SID"]
    print("email", email)
    ensure_cdp()

    # Confirm Doffin
    print("\n=== CONFIRM DOFFIN ===")
    cdp = open_url(CONFIRM_DOFFIN)
    print(page_info(cdp))
    cdp.close()

    # HILMA signup
    signup("https://hns-hilma-prod-apim.developer.azure-api.net", "HILMA", email, password)
    link = poll_hilma_confirm(sid, timeout=200)
    print("HILMA confirm link", bool(link))
    if link:
        cdp = open_url(link)
        print(page_info(cdp))
        cdp.close()

    signin("https://dof-notices-prod-api.developer.azure-api.net", email, password)
    signin("https://hns-hilma-prod-apim.developer.azure-api.net", email, password)

    doffin = capture_key(
        "https://dof-notices-prod-api.developer.azure-api.net",
        "DOFFIN",
        ["public api", "public"],
    )
    hilma = capture_key(
        "https://hns-hilma-prod-apim.developer.azure-api.net",
        "HILMA",
        ["avp-read", "avp"],
    )
    write_env(doffin, hilma)


if __name__ == "__main__":
    main()

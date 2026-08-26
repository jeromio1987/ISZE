"""While Doffin session is live: subscribe Public API + capture real Primary key. Then HILMA."""
from __future__ import annotations

import json
import os
import re
import subprocess
import time
import urllib.request
from pathlib import Path

import requests
import websocket

INSTALL = Path(__file__).resolve().parent
ENV = INSTALL / "nordics_api_keys.env"
EXAMPLE = INSTALL / "nordics_api_keys.env.example"
CREDS = INSTALL / "_nordics_portal_login.env"
GM = "https://api.guerrillamail.com/ajax.php"


def creds():
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
            print("CDP", i)
            return
        except Exception:
            pass
    raise RuntimeError("no cdp")


def tabs():
    ensure_cdp()
    return json.load(urllib.request.urlopen("http://127.0.0.1:9222/json", timeout=5))


class CDP:
    def __init__(self, ws_url):
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
    tid = b.call("Target.createTarget", {"url": url})["targetId"]
    b.close()
    time.sleep(2)
    for _ in range(25):
        for t in tabs():
            if t.get("type") == "page" and t.get("id") == tid:
                cdp = CDP(t["webSocketDebuggerUrl"])
                for __ in range(40):
                    time.sleep(0.35)
                    try:
                        if cdp.evaluate("document.readyState").get("value") == "complete":
                            time.sleep(0.7)
                            return cdp
                    except Exception:
                        pass
                return cdp
        time.sleep(0.4)
    raise RuntimeError("tab missing " + url)


def info(cdp):
    return cdp.evaluate(
        "({url:location.href,body:(document.body&&document.body.innerText||'').slice(0,1200)})"
    ).get("value")


def signin(base, email, password):
    cdp = open_url(base + "/signin")
    cdp.evaluate(
        f"""
        (() => {{
          const set=(id,v)=>{{const el=document.getElementById(id); if(!el) return false;
            el.value=v; el.dispatchEvent(new Event('input',{{bubbles:true}})); return true;}};
          set('email',{json.dumps(email)}); set('password',{json.dumps(password)});
          const b=[...document.querySelectorAll('button')].find(x=>/^sign in$/i.test((x.innerText||'').trim()));
          if(b) b.click(); return true;
        }})()
        """
    )
    time.sleep(5)
    try:
        i = info(cdp)
    except Exception:
        cdp.close()
        cdp = open_url(base + "/")
        i = info(cdp)
    print("SIGNIN", i and i.get("url"), (i or {}).get("body", "")[:250].replace("\n", " | "))
    cdp.close()
    return i


def subscribe_public(base: str):
    # Open product page directly if possible
    candidates = [
        base + "/product#product=public-api",
        base + "/product#product=public",
        base + "/products/public-api",
        base + "/products",
    ]
    cdp = open_url(candidates[-1])
    print("PRODUCTS", info(cdp))
    # Click Public Api link/card
    clicked = cdp.evaluate(
        """
        (() => {
          const els=[...document.querySelectorAll('a,button,h1,h2,h3,td,div,span')];
          for (const el of els) {
            const t=(el.innerText||'').trim();
            if (/^public api$/i.test(t) || /^public api\\b/i.test(t)) { el.click(); return t; }
          }
          // softer
          for (const el of els) {
            const t=(el.innerText||'').trim().toLowerCase();
            if (t==='public api' || t.includes('public api used to search')) { el.click(); return t.slice(0,60); }
          }
          return null;
        })()
        """
    ).get("value")
    print("CLICKED_PRODUCT", clicked)
    time.sleep(3)
    print("AFTER_PRODUCT", info(cdp))
    # Subscribe button
    sub = cdp.evaluate(
        """
        (() => {
          const bs=[...document.querySelectorAll('button,a,input')];
          const hits=[];
          for (const b of bs) {
            const t=((b.innerText||b.value||'')+'').trim();
            if (/subscribe/i.test(t)) { hits.push(t); b.click(); }
          }
          return hits;
        })()
        """
    ).get("value")
    print("SUBSCRIBE_CLICKS", sub)
    time.sleep(3)
    # Confirm dialogs / name subscription
    cdp.evaluate(
        """
        (() => {
          // fill subscription name if present
          const name=document.querySelector('input[name=\"name\"],#name,input[placeholder*=\"name\" i]');
          if(name && !name.value) { name.value='ISZE Public'; name.dispatchEvent(new Event('input',{bubbles:true})); }
          for (const b of document.querySelectorAll('button,a')) {
            const t=(b.innerText||'').trim().toLowerCase();
            if (t==='subscribe' || t==='save' || t==='confirm' || t==='ok') b.click();
          }
          return true;
        })()
        """
    )
    time.sleep(4)
    print("AFTER_SUB", info(cdp))
    cdp.close()


def read_primary_from_profile(base: str) -> str | None:
    cdp = open_url(base + "/profile")
    print("PROFILE", info(cdp))
    cdp.evaluate(
        """
        (() => {
          for (const el of document.querySelectorAll('a,button,span')) {
            if (/^subscriptions$/i.test((el.innerText||'').trim()) || /subscriptions/i.test((el.innerText||'').trim())) {
              el.click(); return (el.innerText||'').trim();
            }
          }
          return null;
        })()
        """
    )
    time.sleep(2)
    # Expand / show keys — only click Show near Primary
    for _ in range(15):
        n = cdp.evaluate(
            """
            (() => {
              let n=0;
              const nodes=[...document.querySelectorAll('button,a,span')];
              for (const el of nodes) {
                const t=(el.innerText||'').trim().toLowerCase();
                if (t==='show') { el.click(); n++; }
              }
              return n;
            })()
            """
        ).get("value")
        time.sleep(0.4)
        if n == 0:
            break
    html = cdp.evaluate("document.documentElement.outerHTML").get("value") or ""
    text = cdp.evaluate("document.body.innerText").get("value") or ""
    print("SUBS_TEXT", text[:900].replace("\n", " | "))
    # Prefer values next to "Primary key"
    best = None
    # APIM often uses <code> or input with value
    for m in re.finditer(
        r"Primary(?:\s+key)?[^A-Za-z0-9]{0,80}([A-Za-z0-9]{32,80})",
        html + "\n" + text,
        flags=re.I,
    ):
        best = m.group(1)
        break
    if not best:
        # input values
        for m in re.finditer(r'value=\"([A-Za-z0-9]{32,80})\"', html):
            best = m.group(1)
            break
    print("PRIMARY", bool(best), "len", len(best or ""))
    cdp.close()
    return best


def write_env(doffin, hilma):
    # preserve existing non-empty if new missing
    existing = {}
    if ENV.exists():
        for line in ENV.read_text(encoding="utf-8").splitlines():
            if "=" in line and not line.strip().startswith("#"):
                k, _, v = line.partition("=")
                existing[k.strip()] = v.strip()
    d = doffin or existing.get("ISZE_DOFFIN_API_KEY") or ""
    h = hilma or existing.get("ISZE_HILMA_API_KEY") or ""
    # clear known-false 36-char GUID placeholders if verify would fail — caller overwrites
    lines = []
    for line in EXAMPLE.read_text(encoding="utf-8").splitlines():
        if line.startswith("ISZE_DOFFIN_API_KEY="):
            lines.append(f"ISZE_DOFFIN_API_KEY={d}")
        elif line.startswith("ISZE_HILMA_API_KEY="):
            lines.append(f"ISZE_HILMA_API_KEY={h}")
        else:
            lines.append(line)
    ENV.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("WROTE", len(d), len(h))


def signup_hilma(email, password):
    cdp = open_url("https://hns-hilma-prod-apim.developer.azure-api.net/signup")
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
            print("HILMA POW", i)
            break
    time.sleep(1)
    cdp.evaluate(
        "([...document.querySelectorAll('button')].filter(b=>/sign up/i.test(b.innerText||'')).slice(-1)[0]||{click(){}}).click()"
    )
    time.sleep(6)
    print("HILMA SIGNUP", info(cdp))
    cdp.close()


def poll_confirm(sid, host_hint, timeout=180):
    end = time.time() + timeout
    seen = set()
    while time.time() < end:
        inbox = requests.get(
            GM, params={"f": "check_email", "sid_token": sid, "seq": 0}, timeout=30
        ).json()
        for item in inbox.get("list") or []:
            mid = str(item.get("mail_id"))
            if mid in seen:
                continue
            frm = (item.get("mail_from") or "").lower()
            if "apimgmt" not in frm and "azure" not in frm:
                continue
            seen.add(mid)
            detail = requests.get(
                GM,
                params={"f": "fetch_email", "sid_token": sid, "email_id": mid},
                timeout=30,
            ).json()
            body = detail.get("mail_body") or ""
            for L in re.findall(r'https?://[^\s"\'<>]+', body):
                L = L.replace("&amp;", "&")
                if "confirm" in L and host_hint in L:
                    return L
        print("mail wait")
        time.sleep(8)
    return None


def main():
    c = creds()
    email, password, sid = c["EMAIL"], c["PASSWORD"], c["SID"]
    # wipe false keys
    write_env("", "")

    ensure_cdp()
    signin("https://dof-notices-prod-api.developer.azure-api.net", email, password)
    subscribe_public("https://dof-notices-prod-api.developer.azure-api.net")
    doffin = read_primary_from_profile("https://dof-notices-prod-api.developer.azure-api.net")

    signup_hilma(email, password)
    link = poll_confirm(sid, "hns-hilma", timeout=200)
    print("HILMA LINK", bool(link), (link or "")[:80])
    if link:
        cdp = open_url(link)
        print(info(cdp))
        cdp.close()
        signin("https://hns-hilma-prod-apim.developer.azure-api.net", email, password)
        # subscribe AVP-Read
        cdp = open_url("https://hns-hilma-prod-apim.developer.azure-api.net/products")
        print("HILMA PRODUCTS", info(cdp))
        cdp.evaluate(
            """
            (() => {
              for (const el of document.querySelectorAll('a,button,h1,h2,h3,td,div,span')) {
                const t=(el.innerText||'').trim();
                if (/avp-read/i.test(t) || /^avp/i.test(t)) { el.click(); return t; }
              }
              return null;
            })()
            """
        )
        time.sleep(2)
        cdp.evaluate(
            """
            (() => {
              for (const b of document.querySelectorAll('button,a')) {
                if (/subscribe/i.test(b.innerText||'')) b.click();
              }
              return true;
            })()
            """
        )
        time.sleep(3)
        cdp.close()
        hilma = read_primary_from_profile(
            "https://hns-hilma-prod-apim.developer.azure-api.net"
        )
    else:
        hilma = None

    write_env(doffin, hilma)


if __name__ == "__main__":
    main()

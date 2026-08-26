"""Sign up / sign in on Doffin + HILMA via Chrome CDP (port 9222). No key printing."""
from __future__ import annotations

import json
import time
import urllib.request
from pathlib import Path

import websocket  # websocket-client

CREDS = Path(__file__).resolve().parent / "_nordics_portal_login.env"
ENV_PATH = Path(__file__).resolve().parent / "nordics_api_keys.env"
EXAMPLE = Path(__file__).resolve().parent / "nordics_api_keys.env.example"


def load_creds() -> dict[str, str]:
    out: dict[str, str] = {}
    for line in CREDS.read_text(encoding="utf-8").splitlines():
        if "=" in line and not line.strip().startswith("#"):
            k, _, v = line.partition("=")
            out[k.strip()] = v.strip()
    return out


def tabs() -> list[dict]:
    return json.load(urllib.request.urlopen("http://127.0.0.1:9222/json", timeout=5))


def page_tab(prefer_substr: str | None = None) -> dict:
    pages = [t for t in tabs() if t.get("type") == "page"]
    if prefer_substr:
        for t in pages:
            if prefer_substr in (t.get("url") or ""):
                return t
    if not pages:
        raise RuntimeError("no page tabs")
    return pages[0]


class CDP:
    def __init__(self, ws_url: str):
        self.ws = websocket.create_connection(ws_url, timeout=30)
        self._id = 0

    def call(self, method: str, params: dict | None = None, timeout: float = 30.0):
        self._id += 1
        mid = self._id
        self.ws.send(json.dumps({"id": mid, "method": method, "params": params or {}}))
        end = time.time() + timeout
        while time.time() < end:
            self.ws.settimeout(max(0.5, end - time.time()))
            try:
                raw = self.ws.recv()
            except Exception:
                continue
            msg = json.loads(raw)
            if msg.get("id") == mid:
                if "error" in msg:
                    raise RuntimeError(msg["error"])
                return msg.get("result", {})
        raise TimeoutError(method)

    def evaluate(self, expression: str, await_promise: bool = False):
        res = self.call(
            "Runtime.evaluate",
            {
                "expression": expression,
                "returnByValue": True,
                "awaitPromise": await_promise,
            },
        )
        return res.get("result", {})

    def navigate(self, url: str):
        self.call("Page.enable")
        self.call("Runtime.enable")
        self.call("Page.navigate", {"url": url})
        # wait for ready
        for _ in range(40):
            time.sleep(0.5)
            st = self.evaluate("document.readyState").get("value")
            if st == "complete":
                # give SPA a beat
                time.sleep(1.0)
                return
        time.sleep(2)

    def close(self):
        try:
            self.ws.close()
        except Exception:
            pass


def connect_for(url: str) -> CDP:
    tab = page_tab()
    cdp = CDP(tab["webSocketDebuggerUrl"])
    cdp.navigate(url)
    # After navigation the target may change — reconnect to matching tab
    cdp.close()
    time.sleep(0.8)
    tab = page_tab(url.split("//", 1)[-1].split("/", 1)[0].split(".")[0])
    # prefer exact path match
    for t in tabs():
        if t.get("type") == "page" and url.rstrip("/") in (t.get("url") or ""):
            tab = t
            break
    else:
        # any page on same host
        host = url.split("//", 1)[-1].split("/", 1)[0]
        for t in tabs():
            if t.get("type") == "page" and host in (t.get("url") or ""):
                tab = t
                break
    return CDP(tab["webSocketDebuggerUrl"])


def signup(base: str, label: str, email: str, password: str) -> str:
    print(f"\n=== {label} SIGNUP ===")
    cdp = connect_for(base + "/signup")
    info = cdp.evaluate(
        "({url:location.href,title:document.title,body:document.body.innerText.slice(0,200)})"
    )
    print("AT", info.get("value"))

    fill = f"""
    (() => {{
      const set = (id, v) => {{
        const el = document.getElementById(id);
        if (!el) return false;
        el.focus();
        el.value = '';
        el.value = v;
        el.dispatchEvent(new Event('input', {{bubbles:true}}));
        el.dispatchEvent(new Event('change', {{bubbles:true}}));
        return true;
      }};
      return {{
        email: set('email', {json.dumps(email)}),
        password: set('password', {json.dumps(password)}),
        confirm: set('confirmPassword', {json.dumps(password)}),
        first: set('firstName', 'Jerome'),
        last: set('lastName', 'van der Pluym'),
      }};
    }})()
    """
    print("FILL", cdp.evaluate(fill).get("value"))

    # Click POW / robot checkbox via label
    cdp.evaluate(
        """
        (() => {
          const box = document.querySelector('input[type=checkbox]');
          if (!box) return 'no-box';
          const lab = box.id ? document.querySelector('label[for=\"'+box.id+'\"]') : null;
          const target = lab || box.closest('label') || box.parentElement || box;
          target.click();
          return {id: box.id, checked: box.checked};
        })()
        """
    )
    checked = False
    for i in range(30):
        time.sleep(1)
        val = cdp.evaluate(
            "document.querySelector('input[type=checkbox]')?.checked === true"
        ).get("value")
        print(label, "pow", i, val)
        if val:
            checked = True
            break
    if not checked:
        print(label, "POW not completed — trying submit anyway")

    cdp.evaluate(
        """
        (() => {
          const bs = [...document.querySelectorAll('button')]
            .filter(b => /sign up/i.test((b.innerText||'').trim()));
          if (!bs.length) return 0;
          bs[bs.length-1].click();
          return bs.length;
        })()
        """
    )
    time.sleep(6)
    # reconnect — navigation may have closed socket
    try:
        after = cdp.evaluate(
            "({url:location.href,title:document.title,body:document.body.innerText.slice(0,900)})"
        ).get("value")
    except Exception as exc:
        print(label, "reconnect after submit", exc)
        cdp.close()
        cdp = connect_for(base + "/profile")
        after = cdp.evaluate(
            "({url:location.href,title:document.title,body:document.body.innerText.slice(0,900)})"
        ).get("value")
    print(label, "AFTER", after)
    url = (after or {}).get("url", "")
    cdp.close()
    return url


def signin(base: str, label: str, email: str, password: str) -> str:
    print(f"\n=== {label} SIGNIN ===")
    cdp = connect_for(base + "/signin")
    cdp.evaluate(
        f"""
        (() => {{
          const set=(id,v)=>{{const el=document.getElementById(id); if(!el) return false; el.value=v;
            el.dispatchEvent(new Event('input',{{bubbles:true}})); return true;}};
          set('email', {json.dumps(email)});
          set('password', {json.dumps(password)});
          return true;
        }})()
        """
    )
    cdp.evaluate(
        """
        (() => {
          const bs=[...document.querySelectorAll('button')].filter(b=>/^sign in$/i.test((b.innerText||'').trim()));
          if(bs.length) bs[bs.length-1].click();
          return bs.length;
        })()
        """
    )
    time.sleep(5)
    try:
        after = cdp.evaluate(
            "({url:location.href,title:document.title,body:document.body.innerText.slice(0,900)})"
        ).get("value")
    except Exception:
        cdp.close()
        cdp = connect_for(base + "/profile")
        after = cdp.evaluate(
            "({url:location.href,title:document.title,body:document.body.innerText.slice(0,900)})"
        ).get("value")
    print(label, "AFTER", after)
    cdp.close()
    return (after or {}).get("url", "")


def reveal_and_capture(base: str, label: str, product_hint: str) -> str | None:
    print(f"\n=== {label} CAPTURE KEY ===")
    cdp = connect_for(base + "/profile")
    body = cdp.evaluate("document.body.innerText").get("value") or ""
    print(label, "profile_snip", body[:400].replace("\n", " | "))
    if "sign in" in body.lower()[:200] and "subscription" not in body.lower():
        print(label, "not signed in on profile")
        cdp.close()
        return None

    # click subscriptions / show
    cdp.evaluate(
        """
        (() => {
          const clickText = (re) => {
            const els=[...document.querySelectorAll('a,button,span,div')];
            for (const el of els) {
              if (re.test((el.innerText||'').trim())) { el.click(); return el.innerText.trim(); }
            }
            return null;
          };
          return {
            sub: clickText(/subscriptions/i),
          };
        })()
        """
    )
    time.sleep(2)
    # click Show repeatedly
    for _ in range(8):
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
        time.sleep(0.5)

    html = cdp.evaluate("document.documentElement.outerHTML").get("value") or ""
    text = cdp.evaluate("document.body.innerText").get("value") or ""
    import re

    cands = set()
    for pat in (
        r"\b[0-9a-fA-F]{32}\b",
        r"\b[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}\b",
        r"\b[A-Za-z0-9]{40,64}\b",
    ):
        cands.update(re.findall(pat, html + "\n" + text))

    # Prefer candidate near product hint + Primary
    blob = html + "\n" + text
    best = None
    for c in sorted(cands, key=len, reverse=True):
        idx = blob.find(c)
        if idx < 0:
            continue
        window = blob[max(0, idx - 200) : idx + 200].lower()
        if "primary" in window and (
            product_hint.lower() in window or "subscription" in window
        ):
            best = c
            break
    if not best:
        # any near primary
        for c in sorted(cands, key=len, reverse=True):
            idx = blob.find(c)
            window = blob[max(0, idx - 120) : idx + 120].lower()
            if "primary" in window and len(c) >= 32:
                best = c
                break
    print(label, "candidates", len(cands), "picked", bool(best), "len", len(best or ""))
    cdp.close()
    return best


def write_env(doffin: str | None, hilma: str | None):
    template = EXAMPLE.read_text(encoding="utf-8")
    lines = []
    for line in template.splitlines():
        if line.startswith("ISZE_DOFFIN_API_KEY="):
            lines.append(f"ISZE_DOFFIN_API_KEY={doffin or ''}")
        elif line.startswith("ISZE_HILMA_API_KEY="):
            lines.append(f"ISZE_HILMA_API_KEY={hilma or ''}")
        else:
            lines.append(line)
    ENV_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("WROTE_ENV doffin_len", len(doffin or ""), "hilma_len", len(hilma or ""))


def main():
    creds = load_creds()
    email, password = creds["EMAIL"], creds["PASSWORD"]
    bases = [
        ("https://dof-notices-prod-api.developer.azure-api.net", "DOFFIN", "public"),
        ("https://hns-hilma-prod-apim.developer.azure-api.net", "HILMA", "avp"),
    ]
    for base, label, _ in bases:
        url = signup(base, label, email, password)
        if "signin" in url or "signup" in url:
            signin(base, label, email, password)

    # Try subscribe products then capture
    for base, label, hint in bases:
        cdp = connect_for(base + "/products")
        body = cdp.evaluate("document.body.innerText").get("value") or ""
        print(label, "products_snip", body[:400].replace("\n", " | "))
        # click Subscribe where relevant
        cdp.evaluate(
            f"""
            (() => {{
              const want = {json.dumps(hint)};
              const cards=[...document.querySelectorAll('a,button,div,h1,h2,h3')];
              // click product link containing hint
              for (const el of cards) {{
                const t=(el.innerText||'').toLowerCase();
                if (t.includes(want) || t.includes('public api') || t.includes('avp-read')) {{
                  el.click(); return t.slice(0,80);
                }}
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
              return bs.map(b=>b.innerText.trim()).slice(0,5);
            })()
            """
        )
        time.sleep(2)
        cdp.close()

    doffin = reveal_and_capture(bases[0][0], "DOFFIN", "public")
    hilma = reveal_and_capture(bases[1][0], "HILMA", "avp")
    if doffin or hilma:
        write_env(doffin, hilma)
    else:
        print("NO_KEYS")


if __name__ == "__main__":
    main()

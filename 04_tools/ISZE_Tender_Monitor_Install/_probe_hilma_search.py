import json
import time
import urllib.request

import requests
import websocket

from nordics_keys import get_hilma_key, reload

reload()
k = get_hilma_key()
h = {
    "Ocp-Apim-Subscription-Key": k,
    "Accept": "application/json",
    "Content-Type": "application/json",
}

ver = json.load(urllib.request.urlopen("http://127.0.0.1:9222/json/version"))


class C:
    def __init__(self, u):
        self.ws = websocket.create_connection(u, timeout=60)
        self.i = 0

    def call(self, m, p=None, timeout=40):
        self.i += 1
        mid = self.i
        self.ws.send(json.dumps({"id": mid, "method": m, "params": p or {}}))
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
        raise TimeoutError(m)

    def ev(self, e):
        return self.call(
            "Runtime.evaluate", {"expression": e, "returnByValue": True}
        ).get("result", {})


b = C(ver["webSocketDebuggerUrl"])
tid = b.call(
    "Target.createTarget",
    {
        "url": "https://hns-hilma-prod-apim.developer.azure-api.net/api-details#api=avp-read-api"
    },
)["targetId"]
time.sleep(2.5)
tabs = json.load(urllib.request.urlopen("http://127.0.0.1:9222/json"))
c = C(next(t for t in tabs if t.get("id") == tid)["webSocketDebuggerUrl"])
time.sleep(1)
print(
    c.ev(
        """(() => {
  for (const el of document.querySelectorAll('a,button,div,span,li')) {
    const t=(el.innerText||'').trim();
    if (t==='Search notices') { el.click(); return t; }
  }
  return null;
})()"""
    )
)
time.sleep(2)
print((c.ev("document.body.innerText").get("value") or "")[:2200])
print(
    "URLS",
    c.ev(
        """(() => {
  const t=document.body.innerText;
  return (t.match(/https?:\\/\\/[^\\s]+/g)||[]).slice(0,20);
})()"""
    ).get("value"),
)

print("SEARCH PROBES")
body = {"search": "ajoneuvo", "top": 5, "count": True}
candidates = [
    ("POST", "https://api.hankintailmoitukset.fi/avp/notices/search"),
    ("POST", "https://api.hankintailmoitukset.fi/avp/Notices/search"),
    ("POST", "https://api.hankintailmoitukset.fi/avp/search/notices"),
    ("GET", "https://api.hankintailmoitukset.fi/avp/Notices?search=ajoneuvo"),
    ("POST", "https://api.hankintailmoitukset.fi/avp/Notices/docs/search"),
    ("POST", "https://api.hankintailmoitukset.fi/avp/indexes/notices/docs/search"),
    ("POST", "https://api.hankintailmoitukset.fi/avp/indexes/notice/docs/search"),
    ("GET", "https://api.hankintailmoitukset.fi/avp/indexes"),
    ("GET", "https://api.hankintailmoitukset.fi/avp/Notices"),
    ("POST", "https://api.hankintailmoitukset.fi/avp/docs/search.index/docs/search"),
]
for method, u in candidates:
    try:
        if method == "GET":
            r = requests.get(u, headers=h, timeout=25)
        else:
            r = requests.post(u, headers=h, json=body, timeout=25)
        print(
            method,
            r.status_code,
            u.split(".fi", 1)[-1],
            r.text[:110].replace("\n", " "),
        )
    except Exception as e:
        print(method, e)

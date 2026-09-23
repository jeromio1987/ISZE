"""Final functional check: the existing spine drill and the sold-to drill still
reach their part-number lists, with no JS errors.
"""
import base64, json, os, socket, struct, subprocess, time, urllib.request
from pathlib import Path

HTML = Path(r"C:\Users\jerom\Desktop\claude\ISZE\02_dashboards\pricing"
            r"\ISZE_Pricing_Revision_AIM_Source.html")
PORT = 9455 + (os.getpid() % 300)
exe = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
prof = Path(os.environ["TEMP"]) / f"isze_fin_{int(time.time())}"
p = subprocess.Popen([exe, "--headless=new", "--disable-gpu",
                      f"--remote-debugging-port={PORT}", f"--user-data-dir={prof}",
                      "--window-size=1600,1100", "--allow-file-access-from-files",
                      "--no-first-run", "--no-default-browser-check",
                      HTML.resolve().as_uri()],
                     stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
ws = None
for _ in range(50):
    time.sleep(0.5)
    try:
        t = [x for x in json.loads(urllib.request.urlopen(
            f"http://127.0.0.1:{PORT}/json/list", timeout=3).read().decode())
            if x.get("type") == "page" and x.get("webSocketDebuggerUrl")]
        if t:
            ws = t[0]["webSocketDebuggerUrl"]
            break
    except Exception:
        pass
h, po = "127.0.0.1", PORT
pa = ws.split(f"{h}:{po}", 1)[1]
s = socket.create_connection((h, po))
k = base64.b64encode(os.urandom(16)).decode()
s.sendall((f"GET {pa} HTTP/1.1\r\nHost: {h}:{po}\r\nUpgrade: websocket\r\n"
           f"Connection: Upgrade\r\nSec-WebSocket-Key: {k}\r\n"
           f"Sec-WebSocket-Version: 13\r\n\r\n").encode())
hd = b""
while b"\r\n\r\n" not in hd:
    hd += s.recv(4096)


def ev(e):
    d = json.dumps({"id": 5, "method": "Runtime.evaluate",
                    "params": {"expression": e, "returnByValue": True}}).encode()
    m = os.urandom(4)
    mm = bytes(b ^ m[j % 4] for j, b in enumerate(d))
    n = len(d)
    hh = bytes([0x81])
    hh += (bytes([0x80 | n]) if n < 126 else
           (bytes([0x80 | 126]) + struct.pack(">H", n) if n < 65536
            else bytes([0x80 | 127]) + struct.pack(">Q", n)))
    s.sendall(hh + m + mm)
    s.settimeout(60)
    while True:
        b1 = s.recv(2)
        ln = b1[1] & 0x7F
        if ln == 126:
            ln = struct.unpack(">H", s.recv(2))[0]
        elif ln == 127:
            ln = struct.unpack(">Q", s.recv(8))[0]
        buf = b""
        while len(buf) < ln:
            buf += s.recv(ln - len(buf))
        try:
            ms = json.loads(buf.decode())
        except Exception:
            continue
        if ms.get("id") == 5:
            r = ms.get("result", {})
            if "exceptionDetails" in r:
                return {"err": r["exceptionDetails"].get("text")}
            return r.get("result", {}).get("value")


time.sleep(7)
for _ in range(40):
    if ev("!!window.__qa"):
        break
    time.sleep(0.5)

print("spine drill (Not on AIM spine -> L2 -> L3 -> part numbers):")
print(json.dumps(ev("JSON.stringify(window.__qaDrillSpine())"), ensure_ascii=True)[:500])

print()
print("sold-to drill down to part numbers:")
print(json.dumps(ev("""(function(){
  document.getElementById('reset').click();
  var s=document.getElementById('cust'); s.value=String(s.options[1].value);
  s.dispatchEvent(new Event('change'));
  function clickRow(i){ var t=document.querySelectorAll('#cust-pn tbody tr');
    if(t.length>i) t[i].click(); return t.length; }
  var a=clickRow(0), b=clickRow(0), c=clickRow(0);
  var qa=window.__qa(); var tr=document.querySelector('#cust-pn tbody tr');
  return JSON.stringify({depths:[a,b,c], custL1:qa.custL1, custL2:qa.custL2, custL3:qa.custL3,
    pnRows:qa.custPn, custCrumb:qa.custCrumb,
    firstRow: tr? Array.prototype.map.call(tr.cells,function(td){
      return td.textContent.trim(); }).join(' | ') : null,
    errors:qa.errors}); })()"""), ensure_ascii=True)[:800])

print()
print("KPI chips follow the brake view when a distributor is chosen:")
print(json.dumps(ev("""(function(){
  document.getElementById('reset').click();
  var s=document.getElementById('db');
  var o=Array.prototype.filter.call(s.options,function(x){
    return x.text.trim()==='ITUK';})[0];
  s.value=String(o.value); s.dispatchEvent(new Event('change'));
  function clickRow(i){ var t=document.querySelectorAll('#brake-l2 tbody tr');
    if(t.length>i) t[i].click(); return t.length; }
  var n=clickRow(0);
  var qa=window.__qa();
  return JSON.stringify({l2Rows:n, kpi:qa.kpiVals, scopeNote:
    document.querySelector('#kpis .kpi .note')?document.querySelector('#kpis .kpi .note').textContent:null,
    brakeSel:qa.brakeL2, brakePn:qa.brakePn,
    figMove:qa.brakeFigs[0], errors:qa.errors}); })()"""), ensure_ascii=True)[:800])

s.close()
p.terminate()

# -*- coding: utf-8 -*-
"""Probe: can the original notice document be fetched for one German and one Norwegian result notice?
Prints status, content type, size and the first bytes. Writes nothing to disk. No keys are printed."""
import json, re, sys, urllib.request, urllib.error
sys.path.insert(0, r"C:\Users\jerom\Desktop\claude\ISZE\04_tools\ISZE_Tender_Monitor_Install")

d = json.load(open(r"C:\Users\jerom\Desktop\claude\ISZE\01_data\14_dashboards\tender_data.json", encoding="utf-8"))
res = [n for n in d["notices"] if re.search(r"RESULT|can-standard|can-modif|conclusion", str(n.get("Notice Type")), re.I)]
de = next(n for n in res if "DE-OV" in str(n.get("Source")))
no = next(n for n in res if "Norway" in str(n.get("Source")) and "CONCLUSION_OF_CONTRACT" in str(n.get("Notice Type")) and n.get("Est. Value"))


def get(url, headers=None, n=400):
    req = urllib.request.Request(url, headers=headers or {"User-Agent": "ISZE-tender-monitor/3 (internal research)"})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            b = r.read()
            print("  ", r.status, r.headers.get("Content-Type"), len(b), "bytes")
            print("  ", b[:n].decode("utf-8", "replace").replace("\n", " ")[:n])
            return b
    except urllib.error.HTTPError as e:
        print("  HTTP", e.code, e.reason)
    except Exception as e:
        print("  ERR", type(e).__name__, str(e)[:160])


nid = de["Source Notice ID"]
print("DE notice", nid)
for u in (f"https://oeffentlichevergabe.de/api/notices/{nid}", f"https://oeffentlichevergabe.de/api/notice-exports/{nid}",
          f"https://oeffentlichevergabe.de/api/notices/{nid}/xml", f"https://oeffentlichevergabe.de/ui/de/notice/{nid}"):
    print(u); get(u)

nid2 = no["Source Notice ID"]
print("NO notice", nid2)
try:
    from nordics_keys import get_doffin_key
    key = get_doffin_key()
    print("doffin key present:", bool(key))
except Exception as ex:
    key = ""; print("key loader error", type(ex).__name__)
for u in (f"https://dof-notices-prod-api.azure-api.net/public/v2/download/{nid2}", f"https://dof-notices-prod-api.azure-api.net/public/v2/notices/{nid2}"):
    print(u); get(u, {"Ocp-Apim-Subscription-Key": key, "User-Agent": "ISZE-tender-monitor/3"})

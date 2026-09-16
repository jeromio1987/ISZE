"""Continue Nordics key capture from existing Guerrilla Mail mailbox."""
from __future__ import annotations

import importlib.util
from pathlib import Path

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("tm", HERE / "_tempmail_nordics_keys.py")
tm = importlib.util.module_from_spec(spec)
assert spec.loader
spec.loader.exec_module(tm)

creds = {}
for line in (HERE / "_nordics_portal_login.env").read_text(encoding="utf-8").splitlines():
    if "=" in line:
        k, _, v = line.partition("=")
        creds[k.strip()] = v.strip()

email, password, sid = creds["EMAIL"], creds["PASSWORD"], creds["SID"]
print("CONTINUE", email)

tm.ensure_cdp()

# HILMA signup if needed
body = tm.signup(
    "https://hns-hilma-prod-apim.developer.azure-api.net", "HILMA", email, password
)
print("HILMA_SIGNUP_BODY", body[:200] if body else None)

# Poll verify mails
for label, subj in (
    ("DOFFIN", r"confirm|verif|account|doffin|api management|subscription"),
    ("HILMA", r"confirm|verif|account|hilma|hankinta|api management|subscription"),
):
    mail = tm.poll_mail(sid, subj, timeout=180)
    if not mail:
        print(label, "NO_VERIFY_MAIL")
        continue
    html = (mail.get("mail_body") or "") + "\n" + (mail.get("mail_excerpt") or "")
    print(label, "MAIL_SUBJ", mail.get("mail_subject"))
    links = [
        L
        for L in tm.extract_links(html)
        if any(
            x in L.lower()
            for x in ("confirm", "verify", "signup", "azure-api.net", "identity", "account", "activation")
        )
    ] or tm.extract_links(html)
    print(label, "links", links[:3])
    for L in links:
        if "guerrillamail" in L.lower():
            continue
        tm.open_verify(L)
        break

tm.ensure_cdp()
tm.signin("https://dof-notices-prod-api.developer.azure-api.net", email, password)
tm.signin("https://hns-hilma-prod-apim.developer.azure-api.net", email, password)
doffin = tm.subscribe_and_key(
    "https://dof-notices-prod-api.developer.azure-api.net",
    "DOFFIN",
    ["public api", "public"],
)
hilma = tm.subscribe_and_key(
    "https://hns-hilma-prod-apim.developer.azure-api.net",
    "HILMA",
    ["avp-read", "avp"],
)
tm.write_env(doffin, hilma)
print("DONE")

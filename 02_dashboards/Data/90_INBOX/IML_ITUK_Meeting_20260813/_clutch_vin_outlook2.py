"""Wider Outlook hunt: Natalie VIN reply + any VIN xlsx. VIN register model scan."""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

import pandas as pd
import win32com.client  # type: ignore

ROOT = Path(r"C:\Users\jerom\Desktop\claude\ISZE")
VIN_PQ = ROOT / r"01_data\07_UIO\vin\VIN_register.parquet"
OUT = ROOT / r"01_data\90_INBOX\IML_ITUK_Meeting_20260813\_clutch_vin_check2.json"
ATT_DIR = ROOT / r"01_data\90_INBOX\IML_ITUK_Meeting_20260813\vin_from_outlook"


def scan_vin() -> dict:
    df = pd.read_parquet(VIN_PQ)
    names = df["iszj_model_name"].astype(str)
    flags = {
        "amt": int(names.str.contains("AMT|SMOOTHER|ALLISON", case=False).sum()),
        "at_token": int(names.str.contains(r"\bAT\b|/AT|AT-", case=False).sum()),
        "mt_token": int(names.str.contains(r"\bMT\b|/MT|MT-|MYY", case=False).sum()),
        "auto": int(names.str.contains("AUTO", case=False).sum()),
        "manual": int(names.str.contains("MANUAL", case=False).sum()),
    }
    by_series = {str(k): int(v) for k, v in df["series"].value_counts().items()}
    by_db = {str(k): int(v) for k, v in df["db_code"].value_counts().items()}
    npr75 = int((df["series"].eq("NPR") & df["gvw_code"].astype(str).eq("75")).sum())
    return {
        "n": int(len(df)),
        "rolling_60m": int(df["in_pms_rolling_60m"].sum()) if "in_pms_rolling_60m" in df.columns else None,
        "transmission_unknown": int((df["transmission"].astype(str) == "unknown").sum()),
        "name_flags": flags,
        "by_series": by_series,
        "by_db": by_db,
        "npr75": npr75,
        "ituk_rows": int(df["db_code"].astype(str).str.contains("ITUK|UK|GB", case=False).sum()),
    }


def walk_folder(folder, depth=0, max_depth=3):
    yield folder
    if depth >= max_depth:
        return
    try:
        for i in range(1, folder.Folders.Count + 1):
            yield from walk_folder(folder.Folders.Item(i), depth + 1, max_depth)
    except Exception:
        return


def outlook_hunt() -> dict:
    outlook = win32com.client.Dispatch("Outlook.Application")
    ns = outlook.GetNamespace("MAPI")
    inbox = ns.GetDefaultFolder(6)
    sent = ns.GetDefaultFolder(5)
    hits = []
    saved = []
    ATT_DIR.mkdir(parents=True, exist_ok=True)

    def consider(it, label: str) -> None:
        try:
            subj = str(getattr(it, "Subject", "") or "")
            who = str(getattr(it, "SenderName", "") or "") + " " + str(getattr(it, "SenderEmailAddress", "") or "")
            to = str(getattr(it, "To", "") or "")
            blob = (subj + " " + who + " " + to).lower()
            natalie = "natalie" in blob
            vinish = "vin" in blob or "cbu" in blob or "clutch" in blob
            if not (natalie or (vinish and any(k in blob for k in ("pms", "2020", "transmission", "clutch", "cbu master")))):
                return
            rec = {
                "label": label,
                "when": str(it.ReceivedTime if label != "OUT" else it.SentOn),
                "who": str(getattr(it, "SenderName", "") or ""),
                "to": to[:180],
                "subj": subj,
                "n_att": int(it.Attachments.Count),
                "atts": [],
            }
            for i in range(1, it.Attachments.Count + 1):
                att = it.Attachments.Item(i)
                name = str(att.FileName)
                rec["atts"].append(name)
                low = name.lower()
                if natalie or any(x in low for x in ("vin", "cbu", "clutch", "uio")):
                    if low.endswith((".xlsx", ".xls", ".csv", ".zip", ".xlsm")):
                        dest = ATT_DIR / f"{label}_{name}"
                        if not dest.exists():
                            att.SaveAsFile(str(dest))
                        saved.append(str(dest))
            hits.append(rec)
        except Exception:
            return

    items = sent.Items
    items.Sort("[SentOn]", True)
    n = 0
    for it in items:
        n += 1
        if n > 800:
            break
        consider(it, "OUT")

    # inbox + one level of subfolders
    folders = [inbox]
    try:
        for i in range(1, min(inbox.Folders.Count, 20) + 1):
            folders.append(inbox.Folders.Item(i))
    except Exception:
        pass
    for folder in folders:
        try:
            name = str(folder.Name)
            items = folder.Items
            items.Sort("[ReceivedTime]", True)
            n = 0
            for it in items:
                n += 1
                if n > 500:
                    break
                consider(it, f"IN:{name}")
        except Exception:
            continue

    return {"hits": hits[:40], "n_hits": len(hits), "saved": saved}


def main() -> None:
    data = {"vin": scan_vin(), "mail": outlook_hunt(), "ran": datetime.now().isoformat(timespec="seconds")}
    OUT.write_text(json.dumps(data, indent=2), encoding="utf-8")
    print(json.dumps({"vin": data["vin"], "n_mail": data["mail"]["n_hits"], "saved": data["mail"]["saved"]}, indent=2))


if __name__ == "__main__":
    main()

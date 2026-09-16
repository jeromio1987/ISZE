"""Check VIN register for ITUK + transmission; search Outlook for Natalie VIN file."""
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import win32com.client  # type: ignore

ROOT = Path(r"C:\Users\jerom\Desktop\claude\ISZE")
VIN_PQ = ROOT / r"01_data\07_UIO\vin\VIN_register.parquet"
VIN_CSV = ROOT / r"01_data\07_UIO\vin\VIN_register.csv"
OUT = ROOT / r"01_data\90_INBOX\IML_ITUK_Meeting_20260813\_clutch_vin_check.json"
ATT_DIR = ROOT / r"01_data\90_INBOX\IML_ITUK_Meeting_20260813\vin_from_outlook"


def vin_summary() -> dict:
    path = VIN_PQ if VIN_PQ.is_file() else VIN_CSV
    df = pd.read_parquet(path) if path.suffix == ".parquet" else pd.read_csv(path, nrows=5)
    if path.suffix != ".parquet":
        df = pd.read_csv(path, low_memory=False)
    cols = list(df.columns)
    out: dict = {"path": str(path), "rows": int(len(df)), "cols": cols}
    for c in cols:
        if str(c).lower() in {"db", "market", "destination", "country", "distributor"}:
            vc = df[c].astype(str).value_counts().head(20)
            out[f"value_counts_{c}"] = {str(k): int(v) for k, v in vc.items()}
    tcol = [c for c in cols if "trans" in str(c).lower() or str(c).lower() in {"at", "mt", "gearbox"}]
    out["trans_cols"] = tcol
    for c in tcol:
        vc = df[c].astype(str).value_counts(dropna=False).head(15)
        out[f"vc_{c}"] = {str(k): int(v) for k, v in vc.items()}
    # ITUK-ish
    blob_cols = [c for c in cols if df[c].dtype == object][:12]
    hits = {}
    for key in ("ITUK", "2194", "GB", "UK", "UNITED KINGDOM"):
        n = 0
        for c in blob_cols:
            n += int(df[c].astype(str).str.contains(key, case=False, na=False).sum())
        hits[key] = n
    out["keyword_hits"] = hits
    return out


def outlook_natalie() -> dict:
    outlook = win32com.client.Dispatch("Outlook.Application")
    ns = outlook.GetNamespace("MAPI")
    inbox = ns.GetDefaultFolder(6)
    sent = ns.GetDefaultFolder(5)
    found = []
    saved = []
    ATT_DIR.mkdir(parents=True, exist_ok=True)
    for folder, label in ((inbox, "IN"), (sent, "OUT")):
        items = folder.Items
        items.Sort("[ReceivedTime]", True)
        n = 0
        for it in items:
            n += 1
            if n > 600:
                break
            try:
                subj = str(getattr(it, "Subject", "") or "")
                who = str(getattr(it, "SenderName", "") or "")
                sl = (subj + " " + who).lower()
                if "vin" not in sl:
                    continue
                if not any(k in sl for k in ("natalie", "cv 2020", "vin cv", "clutch", "pms")):
                    if "vin" in sl and ("2020" in sl or "pms" in sl or "ituk" in sl):
                        pass
                    else:
                        continue
                rec = {
                    "label": label,
                    "when": str(it.ReceivedTime if label == "IN" else it.SentOn),
                    "who": who,
                    "subj": subj,
                    "n_att": int(it.Attachments.Count),
                    "atts": [],
                }
                for i in range(1, it.Attachments.Count + 1):
                    att = it.Attachments.Item(i)
                    name = str(att.FileName)
                    rec["atts"].append(name)
                    if name.lower().endswith((".xlsx", ".xls", ".csv", ".zip")):
                        dest = ATT_DIR / f"{label}_{name}"
                        if not dest.exists():
                            att.SaveAsFile(str(dest))
                            saved.append(str(dest))
                found.append(rec)
                if len(found) >= 25:
                    break
            except Exception:
                continue
    return {"found": found, "saved": saved}


def main() -> None:
    data = {"vin": vin_summary(), "mail": outlook_natalie()}
    OUT.write_text(json.dumps(data, indent=2), encoding="utf-8")
    print("wrote", OUT)
    print("rows", data["vin"]["rows"], "trans", data["vin"].get("trans_cols"), "hits", data["vin"].get("keyword_hits"))
    print("mail hits", len(data["mail"]["found"]), "saved", data["mail"]["saved"])


if __name__ == "__main__":
    main()

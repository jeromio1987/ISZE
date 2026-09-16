"""Probe oeffentlichevergabe notice-exports formats (throwaway)."""
from __future__ import annotations

import csv
import io
import json
import sys
import zipfile
from pathlib import Path

import requests

if sys.stdout.encoding and sys.stdout.encoding.lower() not in ("utf-8", "utf8"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

HERE = Path(__file__).resolve().parent
OUT = HERE / "_probe_de_ov_formats.json"

s = requests.Session()
s.headers.update(
    {
        "User-Agent": "Mozilla/5.0 (compatible; ISZE-TenderMonitor/3.0)",
        "Accept": "*/*",
    }
)

url = "https://oeffentlichevergabe.de/api/notice-exports"
results = []

for params in [
    {"pubDay": "2026-08-20", "format": "csv.zip"},
    {"pubDay": "2026-08-20", "format": "eforms.zip"},
    {"pubDay": "2026-08-20", "format": "ocds.zip"},
    {"pubDay": "2026-08-24", "format": "csv.zip"},
    {"pubMonth": "2026-08", "format": "csv.zip"},
]:
    row = {"params": params}
    try:
        r = s.get(url, params=params, timeout=120)
        row["status"] = r.status_code
        row["ctype"] = r.headers.get("Content-Type")
        row["cd"] = r.headers.get("Content-Disposition")
        body = r.content or b""
        row["bytes"] = len(body)
        row["magic"] = body[:4].hex()
        if r.status_code == 200 and body[:2] == b"PK":
            with zipfile.ZipFile(io.BytesIO(body)) as zf:
                names = zf.namelist()
                row["zip_n"] = len(names)
                row["zip_sample"] = names[:15]
                if "notice.csv" in names:
                    raw = zf.read("notice.csv")
                    text = raw.decode("utf-8-sig", errors="replace")
                    reader = csv.DictReader(io.StringIO(text))
                    headers = reader.fieldnames or []
                    row["notice_headers"] = headers[:40]
                    sample = []
                    for i, rec in enumerate(reader):
                        if i >= 3:
                            break
                        sample.append({k: (rec.get(k) or "")[:120] for k in headers[:12]})
                    row["notice_sample"] = sample
                if "classification.csv" in names:
                    raw = zf.read("classification.csv")
                    text = raw.decode("utf-8-sig", errors="replace")
                    reader = csv.DictReader(io.StringIO(text))
                    headers = reader.fieldnames or []
                    row["class_headers"] = headers
                    # Count vehicle-ish CPV
                    veh = 0
                    samples = []
                    for rec in reader:
                        code = (rec.get("classificationCode") or rec.get("code") or "")
                        if code.startswith(("341", "5011", "501")):
                            veh += 1
                            if len(samples) < 5:
                                samples.append(dict(rec))
                    row["vehicle_class_rows"] = veh
                    row["vehicle_class_samples"] = samples
        elif r.status_code != 200:
            row["body"] = body[:300].decode("utf-8", errors="replace")
    except Exception as exc:
        row["error"] = str(exc)
    results.append(row)
    print(
        f"{params} -> {row.get('status')} bytes={row.get('bytes')} "
        f"zip_n={row.get('zip_n')} veh={row.get('vehicle_class_rows')} err={row.get('error')}"
    )

OUT.write_text(json.dumps(results, indent=2, ensure_ascii=False), encoding="utf-8")
print(f"Wrote {OUT}")

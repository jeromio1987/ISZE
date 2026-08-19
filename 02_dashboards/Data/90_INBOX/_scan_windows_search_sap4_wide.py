"""Dump Windows Search sap4 / UTIPartSales / uti.co.il from-addresses to JSON only."""
from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

import win32com.client

META = Path(r"C:\Users\jerom\Desktop\claude\ISZE\01_data\90_INBOX\outlook_uti_sap4_windows_search_wide_20260813.json")


def run_query(conn, sql: str) -> list[dict]:
    rs = win32com.client.Dispatch("ADODB.Recordset")
    try:
        rs.Open(sql, conn)
    except Exception as e:
        return [{"_error": str(e)}]
    rows = []
    if rs.EOF:
        rs.Close()
        return rows
    while not rs.EOF:
        row = {}
        for i in range(rs.Fields.Count):
            f = rs.Fields.Item(i)
            try:
                val = f.Value
            except Exception:
                val = None
            row[str(f.Name)] = str(val) if val is not None else None
        rows.append(row)
        rs.MoveNext()
    rs.Close()
    return rows


def main() -> None:
    conn = win32com.client.Dispatch("ADODB.Connection")
    conn.Open(
        'Provider=Search.CollatorDSO;Extended Properties="Application=Windows"'
    )
    queries = {
        "utipartsales_all": """SELECT TOP 200 System.Subject, System.Message.FromAddress, System.Message.DateReceived, System.ItemPathDisplay, System.Size
           FROM SystemIndex WHERE CONTAINS(System.Subject, '"UTIPartSales"')""",
        "uti_from": """SELECT TOP 500 System.Subject, System.Message.FromAddress, System.Message.DateReceived, System.ItemPathDisplay
           FROM SystemIndex WHERE CONTAINS(System.Message.FromAddress, '"uti.co.il"')""",
        "sap4_star": """SELECT TOP 50 System.Subject, System.Message.FromAddress, System.ItemPathDisplay, System.ItemUrl, System.DateModified
           FROM SystemIndex WHERE CONTAINS(*, '"sap4@uti"')""",
        "sap4_from_like": """SELECT TOP 50 System.Subject, System.Message.FromAddress, System.Message.DateReceived, System.ItemPathDisplay
           FROM SystemIndex WHERE System.Message.FromAddress LIKE '%sap4%'""",
        "noreply2": """SELECT TOP 50 System.Subject, System.Message.FromAddress, System.Message.DateReceived, System.ItemPathDisplay
           FROM SystemIndex WHERE CONTAINS(System.Message.FromAddress, '"noreply2@uti.co.il"')""",
    }
    out = {}
    for name, sql in queries.items():
        rows = run_query(conn, sql)
        out[name] = {"n": len(rows), "rows": rows}
        print(name, len(rows), flush=True)
    conn.Close()

    froms = Counter()
    years = Counter()
    for r in out["utipartsales_all"]["rows"]:
        froms[r.get("SYSTEM.MESSAGE.FROMADDRESS") or ""] += 1
        years[(r.get("SYSTEM.MESSAGE.DATERECEIVED") or "")[:4]] += 1
    uti_froms = Counter()
    for r in out["uti_from"]["rows"]:
        uti_froms[r.get("SYSTEM.MESSAGE.FROMADDRESS") or ""] += 1
    out["summary"] = {
        "utipartsales_from": dict(froms),
        "utipartsales_years": dict(years),
        "uti_from_addresses": dict(uti_froms),
        "sap4_star_n": out["sap4_star"]["n"],
        "sap4_from_like_n": out["sap4_from_like"]["n"],
    }
    print("SUMMARY", json.dumps(out["summary"], indent=2), flush=True)
    META.write_text(json.dumps(out, indent=2, default=str), encoding="utf-8")
    print("WROTE", META, flush=True)


if __name__ == "__main__":
    main()

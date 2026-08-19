"""Windows Search index hunt for sap4@uti.co.il Outlook items. Never Send."""
from __future__ import annotations

import json
from pathlib import Path

import win32com.client

ISZE = Path(r"C:\Users\jerom\Desktop\claude\ISZE")
META = ISZE / r"01_data\90_INBOX\outlook_uti_sap4_windows_search_20260813.json"

QUERIES = [
    """SELECT TOP 200 System.Subject, System.Message.FromAddress, System.Message.DateReceived, System.ItemUrl, System.ItemPathDisplay, System.ItemName, System.Size, System.Kind, System.Search.Store
       FROM SystemIndex
       WHERE CONTAINS(System.Message.FromAddress, '"sap4"')""",
    """SELECT TOP 200 System.Subject, System.Message.FromAddress, System.Message.DateReceived, System.ItemUrl, System.ItemPathDisplay, System.ItemName, System.Size
       FROM SystemIndex
       WHERE System.Message.FromAddress LIKE '%sap4%'""",
    """SELECT TOP 200 System.Subject, System.Message.FromAddress, System.Message.DateReceived, System.ItemUrl, System.ItemPathDisplay, System.ItemName
       FROM SystemIndex
       WHERE CONTAINS(System.Search.Contents, '"UTIPartSales"') AND System.Message.DateReceived < '2023-01-01'""",
    """SELECT TOP 50 System.Subject, System.Message.FromAddress, System.Message.DateReceived, System.ItemPathDisplay
       FROM SystemIndex
       WHERE CONTAINS(System.Subject, '"UTIPartSales"')""",
]


def run_query(conn, sql: str) -> list[dict]:
    rs = win32com.client.Dispatch("ADODB.Recordset")
    try:
        rs.Open(sql, conn)
    except Exception as e:
        return [{"_error": str(e), "_sql": sql[:180]}]
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
    out = []
    for sql in QUERIES:
        print("QUERY", sql[:80], flush=True)
        rows = run_query(conn, sql)
        print("  rows", len(rows), flush=True)
        if rows:
            print("  first", rows[0], flush=True)
        out.append({"sql": sql, "n": len(rows), "rows": rows})
    conn.Close()
    META.write_text(json.dumps(out, indent=2, default=str), encoding="utf-8")
    print("DONE", META, flush=True)


if __name__ == "__main__":
    main()

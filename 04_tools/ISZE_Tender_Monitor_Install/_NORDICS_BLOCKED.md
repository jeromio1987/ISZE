# Nordics keys — DONE

**Status:** `nordics_api_keys.env` filled (gitignored) · `verify_nordics_keys.py` **ALL OK** · source health **OK** for Norway Doffin + Finland HILMA.

| Check | Result |
|---|---|
| Verify | ALL OK (Doffin GET search 200 · HILMA POST eformnotices search 200) |
| Focused scrape | Doffin **37** · HILMA **54** keyword matches |
| Merge (gated) | NO **11** · FI **1** into `isuzu_tenders_v3.xlsx` |
| Dashboard opps | Norway **10** · Finland **1** (after Isuzu / not-for-us / product-fit) |
| Health | Doffin **OK** · HILMA **OK** |

**Env:** `C:\Users\jerom\Desktop\claude\ISZE\04_tools\ISZE_Tender_Monitor_Install\nordics_api_keys.env`  
**HILMA gateway:** `https://api.hankintailmoitukset.fi/avp/eformnotices/docs/search` (not `*.azure-api.net/avp/Notices`)

Product-fit, coverage chip, unsized KPI, IDS — preserved on v4 rebuild.

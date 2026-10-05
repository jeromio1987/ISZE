# Reuse map (C05)

inspected_at: 2026-09-21T06:43:45Z

| Candidate | Recommendation | Cite | Notes |
|---|---|---|---|
| PRISM Streamlit app | keep separate / reuse metrics & loaders after approval | `03_analytics/Isuzu/prism/` ; pack docs `10_PRISM_OVERVIEW.md`–`17_...` | Full customer auth/separation not established in this inspection. Do not treat PRISM as Universe production host without access model. |
| PRISM GPS/PMS/BVP engines | adapt after approval | pack `14_PRISM_SOURCE_ENGINES.py` banners → live modules under `prism/modules/` | Reuse calculations; do not duplicate engines. |
| ITUK dealer sell-out derived CSVs | reuse directly for commercial pilot panels | `01_data/00_derived/dealer_sellout_long_ITUK_CY2025.csv` (pack copy `01_...`) | Quantity grain dealer×PN×month CY2025. |
| AIM classification dated export | reuse directly as pinned release | `01_data/00_derived/AIM_Master_PN_Categories_Figkey_20260921.csv` | Pin filename+date in any Universe label. |
| Network Atlas HTML | adapt after approval | `01_data/ISUZU_Network_Atlas_v0_2.html` + review note | Prototype; known join/identity gaps. |
| AIM Parts Atlas HTML | adapt after approval | `02_dashboards/AIM_Parts_Atlas_v2.0.html` | Portfolio view candidate. |
| IDS dealer compare | reuse as IDS module surface | `02_dashboards/ids/IDS_2026_dealer_compare.html` | Assessment evidence; not commercial performance. |
| Tender data JSON | adapt after approval for panel | `01_data/14_dashboards/tender_data.json` | Exists; not integrated into Universe product. |
| New unified Universe framework | unresolved / not proposed | (absent app) | No replacement architecture proposed in R0. |

No automatic PRISM→Universe merge is authorized by this inspection.

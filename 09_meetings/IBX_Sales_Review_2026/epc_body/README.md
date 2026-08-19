# IBX Body → Snap-on EPC model scrape

## Blocker (agent)

Cursor's agent browser has **no tab / cannot attach** to your Chrome session.
Your login at Snap-on EPC is only visible in **your** browser.

## Exact steps (you)

1. Open (or focus) **https://isuzu.snaponepc.com/epc/#/** — stay logged in on the EPC part-search UI.
2. Press **F12** → **Console**.
3. Open `PASTE_IN_SNAPON_CONSOLE.js` in an editor, copy **all**, paste into the console, Enter.
4. Run:
   ```js
   window.__bgRun(window.__IBX_BODY_PNS, 12000)
   ```
   Top 100 PNs ≈ 20.0 min at 12s spacing (~74% of H1'26 Body EUR).
5. Watch `window.__bgState` until `running: false`.
6. Run:
   ```js
   window.__downloadResults("IBX_body_epc_results.json")
   ```
7. Move the downloaded JSON into this folder:
   `C:\Users\jerom\Desktop\claude\ISZE\09_meetings\IBX_Sales_Review_2026\epc_body`
8. Tell the agent (or run):
   ```
   python build_body_models_and_dashboard.py --from-results
   ```

## Notes

- Never invent models. Blank = not found / not scraped yet.
- Snap-on may throttle; if many `poll timeout`, stop and resume later with remaining PNs.
- Autodoc scrapers do **not** provide OEM vehicle application for these PNs.

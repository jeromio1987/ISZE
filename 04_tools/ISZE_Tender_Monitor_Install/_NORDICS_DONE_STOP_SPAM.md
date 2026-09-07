# Nordics DONE — STOP SPAM

**Status: DONE.** Agents must not reopen Doffin / HILMA / Hankintailmoitukset developer portals or re-ask Jerome for API keys.

## Facts (do not re-verify by opening portals)
- Keys are already in env (`nordics_api_keys.env` / loader path as documented in `_NORDICS_BLOCKED.md` and workspace rules).
- Verify OK; NO/FI merged into tender monitor.
- Workspace rule: `ISZE/.cursor/rules/isze-nordics-keys-closed.mdc` — closed as of 2026-08-25. Not in `~\.cursor\rules`.

## Hard stop for agents
1. Do **not** open:
   - `dof-notices-prod-api.developer.azure-api.net`
   - `hns-hilma-prod-apim.developer.azure-api.net`
   - hankintailmoitukset.fi developer / APIM pages
2. Do **not** spawn Cursor browser or Chrome to those URLs.
3. Do **not** add Nordics key registration to waiting-on-Jerome lists, morning briefs, or audits.
4. If scrape health says `AWAITING_KEY`: fix env/loader yourself; escalate only with a **new** evidenced API failure — not setup instructions again.

## Related
- `_NORDICS_BLOCKED.md`
- `ISZE/.cursor/rules/isze-nordics-keys-closed.mdc`
- DECISIONS 2026-08-25

Written: 2026-08-25 — stop spam marker for all agents.

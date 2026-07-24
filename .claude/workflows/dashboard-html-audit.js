export const meta = {
  name: 'dashboard-html-audit',
  description:
    'Audit ISZE 02_dashboards HTML for data-path / safety / deploy-mirror violations; independent verifier per finding',
  phases: [
    { title: 'Discover', detail: 'List HTML files under 02_dashboards' },
    { title: 'Audit', detail: 'One agent per file checks frozen rules' },
    { title: 'Verify', detail: 'Fresh-context verifier confirms each finding' },
    { title: 'Synthesize', detail: 'One ranked report' },
  ],
}

/**
 * Optional args:
 *   /dashboard-html-audit with maxFiles 20 under 02_dashboards/sales
 *   args.maxFiles -- default 20
 *   args.under    -- subdirectory (default 02_dashboards)
 */
const maxFiles =
  typeof args !== 'undefined' && args && Number(args.maxFiles) > 0
    ? Math.min(80, Math.floor(Number(args.maxFiles)))
    : 20
const under =
  typeof args !== 'undefined' && args && typeof args.under === 'string' && args.under.trim()
    ? args.under.trim().replace(/^\/+/, '').replace(/\\/g, '/')
    : '02_dashboards'

const RULES = `
ISZE frozen rules for HTML dashboards (read-only -- do not edit files, do not open raw billing XLSX):

Flag when the file:
1. Fetches or embeds line-level billing / raw sales XLSX paths (01_data/raw/sales, Data/raw/sales, *.XLSX billing dumps)
2. Points editors at 07_deploy/ as a source of truth, or documents editing the deploy mirror / Master Dashboard/context
3. Hardcodes machine-specific absolute paths (C:\\Users\\...) instead of relative ../Data or workspace-relative URLs
4. Invents or hardcodes KPI capture%/GPS/BVP numbers that should come from derived JSON (note as medium if clearly stale literals)
5. Loads secrets, tokens, or connection strings in client-side JS

Do NOT flag:
- Relative fetches to Data/dashboards/*.json or 01_data/dashboards (deploy URL pattern)
- Archive / _archive prototypes clearly marked as non-production
- Comments that warn against raw billing
`

phase('Discover')
const discovered = await agent(
  `List HTML files under ${under}/ (recursive). Return repo-relative paths. ` +
    `Prefer live dashboards under sales/, gps/, fleet/, ops/, hub/, pricing/, side/ before _archive. ` +
    `Cap at ${maxFiles}. Do not read contents yet.`,
  {
    label: 'discover-html',
    phase: 'Discover',
    schema: {
      type: 'object',
      required: ['files'],
      properties: {
        files: { type: 'array', items: { type: 'string' } },
        truncated: { type: 'boolean' },
      },
    },
  },
)

const files = (discovered.files || []).slice(0, maxFiles)
log(`Auditing ${files.length} HTML files under ${under}`)

phase('Audit')
const audits = await pipeline(files, (file) =>
  agent(
    `Read ${file}.\n${RULES}\n` +
      `Return findings only for real rule breaks. Empty findings if clean.`,
    {
      label: `audit:${file}`,
      phase: 'Audit',
      schema: {
        type: 'object',
        required: ['file', 'findings'],
        properties: {
          file: { type: 'string' },
          findings: {
            type: 'array',
            items: {
              type: 'object',
              required: ['rule', 'severity', 'reason', 'evidence'],
              properties: {
                rule: { type: 'string' },
                severity: { type: 'string', enum: ['high', 'medium', 'low'] },
                reason: { type: 'string' },
                evidence: { type: 'string' },
              },
            },
          },
        },
      },
    },
  ),
)

const candidates = (audits || [])
  .filter(Boolean)
  .flatMap((a) =>
    (a.findings || []).map((f) => ({
      file: a.file,
      rule: f.rule,
      severity: f.severity,
      reason: f.reason,
      evidence: f.evidence,
    })),
  )

log(`Audit produced ${candidates.length} candidate findings`)

phase('Verify')
const verified = await pipeline(candidates, (finding) =>
  agent(
    `Independent verifier -- no prior audit context.\n` +
      `Re-read ${finding.file}. Claim:\n${JSON.stringify(finding, null, 2)}\n\n${RULES}\n` +
      `Confirm only on clear evidence. Reject vibes and archive false positives.`,
    {
      label: `verify:${finding.file}:${finding.rule}`,
      phase: 'Verify',
      schema: {
        type: 'object',
        required: ['confirmed', 'file', 'rule', 'severity', 'rationale'],
        properties: {
          confirmed: { type: 'boolean' },
          file: { type: 'string' },
          rule: { type: 'string' },
          severity: { type: 'string', enum: ['high', 'medium', 'low'] },
          rationale: { type: 'string' },
        },
      },
    },
  ),
)

const confirmed = (verified || []).filter(Boolean).filter((v) => v.confirmed === true)
log(`${confirmed.length} findings confirmed`)

phase('Synthesize')
const report = await agent(
  `Write a short ISZE dashboard HTML audit report.\n` +
    `Scope: ${files.length} files under ${under}.\n` +
    `Confirmed:\n${JSON.stringify(confirmed, null, 2)}\n` +
    `Only confirmed items. Group by severity. Remind: edit 02_dashboards then sync_to_deploys.ps1 -- never 07_deploy.`,
  { label: 'synthesize-report', phase: 'Synthesize' },
)

return {
  scope: { under, maxFiles, filesAudited: files.length },
  candidates: candidates.length,
  confirmedCount: confirmed.length,
  confirmed,
  report,
}

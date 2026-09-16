#!/usr/bin/env node
/**
 * stop hook: if exec aftersales build left a pending QA marker, run verify and follow up.
 */
import fs from 'node:fs'
import path from 'node:path'
import { fileURLToPath } from 'node:url'
import { spawnSync } from 'node:child_process'

const __dirname = path.dirname(fileURLToPath(import.meta.url))
const MARKER = path.join(__dirname, '.exec-aftersales-pending-qa.json')

function readStdin() {
  try {
    return fs.readFileSync(0, 'utf8')
  } catch {
    return '{}'
  }
}

function emit(obj) {
  process.stdout.write(JSON.stringify(obj))
}

readStdin()

if (!fs.existsSync(MARKER)) {
  emit({})
  process.exit(0)
}

let meta = {}
try {
  meta = JSON.parse(fs.readFileSync(MARKER, 'utf8'))
} catch {
  meta = {}
}

const root = path.resolve(__dirname, '..', '..')
const gate = path.join(root, '02_dashboards', '_build', 'verify_exec_aftersales_paper.py')

if (!fs.existsSync(gate)) {
  emit({
    followup_message:
      'STOP: Exec aftersales build was detected but verify_exec_aftersales_paper.py is missing. Do not claim the paper done.',
  })
  process.exit(0)
}

const r = spawnSync('python', [gate], {
  encoding: 'utf8',
  cwd: root,
  shell: process.platform === 'win32',
  timeout: 120_000,
})
const out = ((r.stdout || '') + (r.stderr || '')).trim().slice(0, 2500)

if ((r.status ?? 1) !== 0) {
  emit({
    followup_message:
      'STOP: Exec aftersales VERIFY FAIL. Do not claim the paper ready.\n' +
      out +
      '\nRe-cut per 00_docs/REVIEW_EXEC_AFTERSALES_PAPER_20260915.md and .cursor/rules/isze-exec-aftersales-paper.mdc, then re-run verify + paint.',
  })
  process.exit(0)
}

try {
  fs.unlinkSync(MARKER)
} catch {
  /* ignore */
}

const note = meta.verify_ran
  ? 'Verify already ran this session; stop re-check PASS.'
  : 'Verify PASS on stop.'

emit({
  followup_message:
    `Exec aftersales stop check: ${note}\n${out}\n` +
    'Still required before done: paint screenshots + SHIP_RECEIPT; matrix-led heroes; ceiling placeholder on p1/p3; live tenders.',
})
process.exit(0)

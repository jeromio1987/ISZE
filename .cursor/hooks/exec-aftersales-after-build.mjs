#!/usr/bin/env node
/**
 * afterShellExecution: when build_exec_aftersales_paper runs, mark pending QA.
 */
import fs from 'node:fs'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

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

const raw = readStdin()
let payload = {}
try {
  payload = JSON.parse(raw || '{}')
} catch {
  payload = {}
}

const cmd = String(payload.command || payload.cmd || '')
const hit = /build_exec_aftersales_paper\.py|verify_exec_aftersales_paper\.py/i.test(cmd)

if (!hit) {
  emit({})
  process.exit(0)
}

const isVerify = /verify_exec_aftersales_paper\.py/i.test(cmd)

try {
  fs.writeFileSync(
    MARKER,
    JSON.stringify(
      {
        at: new Date().toISOString(),
        command: cmd.slice(0, 500),
        needs_qa: !isVerify,
        verify_ran: isVerify,
      },
      null,
      2,
    ),
    'utf8',
  )
} catch {
  /* ignore */
}

if (isVerify) {
  emit({
    followup_message:
      'Exec aftersales verify ran. Before claiming done: paint check + SHIP_RECEIPT; hero must follow pms_opportunity_matrix (not oil-filter); ceiling placeholder disclosed. See REVIEW_EXEC_AFTERSALES_PAPER_20260915.md.',
  })
  process.exit(0)
}

emit({
  followup_message:
    'Exec aftersales paper build detected. You MUST run ' +
    '`python 02_dashboards/_build/verify_exec_aftersales_paper.py` before claiming done. ' +
    'Hard fails from 2026-09-15 retro: oil-filter opportunity hero, silent €250 ceiling placeholder, unused opportunity matrix, no margin/warranty/telematics treatment, stale tenders. Rule: .cursor/rules/isze-exec-aftersales-paper.mdc.',
})
process.exit(0)

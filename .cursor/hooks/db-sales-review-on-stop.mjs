#!/usr/bin/env node
/**
 * stop hook: if a db_sales_review build left a pending QA marker, follow up loudly.
 */
import fs from 'node:fs'
import path from 'node:path'
import { fileURLToPath } from 'node:url'
import { spawnSync } from 'node:child_process'

const __dirname = path.dirname(fileURLToPath(import.meta.url))
const MARKER = path.join(__dirname, '.db-sales-review-pending-qa.json')

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

readStdin() // consume

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

const db = meta.db
const root = path.resolve(__dirname, '..', '..')
const gate = path.join(
  root,
  '.cursor',
  'skills',
  'isze-db-sales-review',
  'scripts',
  'qa_deck_gate.py',
)

let gateLine = 'qa_deck_gate.py not run this turn'
if (db && fs.existsSync(gate)) {
  const r = spawnSync('python', [gate, '--db', db], {
    encoding: 'utf8',
    cwd: root,
    shell: process.platform === 'win32',
    timeout: 120_000,
  })
  const out = ((r.stdout || '') + (r.stderr || '')).trim().slice(0, 1500)
  if ((r.status ?? 1) !== 0) {
    emit({
      followup_message:
        `STOP: DB Sales Review QA GATE FAIL for ${db}. Do not claim the deck is ready.\n${out}\n` +
        'Fix loader/profile, re-run build_parts_analysis, then gate, then deck. See RETRO_2026-08-12.',
    })
    process.exit(0)
  }
  gateLine = out || `QA GATE PASS — ${db}`
  try {
    fs.unlinkSync(MARKER)
  } catch {
    /* ignore */
  }
  emit({
    followup_message:
      `DB Sales Review stop check: ${gateLine}. Still verify Mode A: PBI lead, SaTy no jargon, PMS Best skipped if >100%, no UTI blend.`,
  })
  process.exit(0)
}

emit({
  followup_message:
    'DB Sales Review build was detected earlier this session but QA marker has no --db. ' +
    'Run qa_deck_gate.py before telling Jerome the pack is done. See isze-db-sales-review skill.',
})
process.exit(0)

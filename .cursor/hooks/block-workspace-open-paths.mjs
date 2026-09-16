#!/usr/bin/env node
/**
 * Warn when a reply tells Jerome to open /workspace/, file://, or a GitHub blob HTML.
 * afterAgentResponse: record hits. stop: one follow-up rewrite (loop_limit 1).
 */
import fs from 'node:fs'
import os from 'node:os'
import path from 'node:path'

const FLAG = path.join(os.tmpdir(), 'isze-open-path-warn.json')

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

function scan(text) {
  if (!text || typeof text !== 'string') return []
  const hits = []
  if (/[/\\]workspace[/\\]/i.test(text)) hits.push('a /workspace/ or \\workspace\\ path')
  if (/file:\/\//i.test(text)) hits.push('a file:// link')
  if (/github\.com\/\S+\/blob\//i.test(text)) hits.push('a GitHub blob URL as the open path')
  return hits
}

function followup(hits) {
  return (
    'STOP: that reply used a path Jerome cannot open on this Windows PC (' +
    hits.join('; ') +
    '). Rewrite with a quoted path under C:\\Users\\jerom\\Desktop\\claude\\ISZE\\ only if that file exists here. No file-protocol markdown. No GitHub blob HTML. Sibling OPEN_*.cmd, CRLF, double-click in Explorer.'
  )
}

function eventName(input) {
  const named = String(input.hook_event_name || '')
  if (named) return named
  if (input.status) return 'stop'
  if (typeof input.text === 'string') return 'afterAgentResponse'
  return ''
}

const input = JSON.parse(readStdin() || '{}')
const event = eventName(input)

try {
  if (event === 'afterAgentResponse') {
    const hits = scan(input.text || '')
    if (hits.length) {
      fs.writeFileSync(FLAG, JSON.stringify({ hits, at: Date.now() }), 'utf8')
    } else if (fs.existsSync(FLAG)) {
      fs.unlinkSync(FLAG)
    }
    emit({})
    process.exit(0)
  }

  if (event === 'stop') {
    const loopCount = Number(input.loop_count || 0)
    if (input.status && input.status !== 'completed') {
      emit({})
      process.exit(0)
    }
    if (loopCount >= 1) {
      if (fs.existsSync(FLAG)) fs.unlinkSync(FLAG)
      emit({})
      process.exit(0)
    }
    if (fs.existsSync(FLAG)) {
      let hits = ['a blocked open path']
      try {
        const parsed = JSON.parse(fs.readFileSync(FLAG, 'utf8'))
        if (Array.isArray(parsed.hits) && parsed.hits.length) hits = parsed.hits
      } catch {
        /* keep default */
      }
      try {
        fs.unlinkSync(FLAG)
      } catch {
        /* ignore */
      }
      emit({ followup_message: followup(hits) })
      process.exit(0)
    }
    emit({})
    process.exit(0)
  }
} catch {
  emit({})
  process.exit(0)
}

emit({})
process.exit(0)

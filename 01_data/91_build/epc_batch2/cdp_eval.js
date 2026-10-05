// Minimal CDP client: evaluate one expression in a given browser view and print the result.
// usage: node cdp_eval.js <viewId> <expression> <awaitPromise 0|1> [timeoutSeconds]
//
// The browser exposes a DevTools HTTP endpoint on a loopback port (found under ~/.cursor).
// This script discovers it, attaches to the target view, evaluates, and exits.
const fs = require('fs');
const os = require('os');
const path = require('path');
const net = require('net');
const crypto = require('crypto');

const viewId = process.argv[2];
const expression = process.argv[3];
const awaitPromise = process.argv[4] === '1';
const timeoutS = parseInt(process.argv[5] || '180', 10);

function findEndpoint() {
  const roots = [
    path.join(os.homedir(), '.cursor'),
    path.join(process.env.LOCALAPPDATA || '', 'Cursor'),
  ];
  const found = [];
  const walk = (dir, depth) => {
    if (depth > 5) return;
    let entries;
    try {
      entries = fs.readdirSync(dir, { withFileTypes: true });
    } catch (e) {
      return;
    }
    for (const e of entries) {
      const p = path.join(dir, e.name);
      if (e.isDirectory()) {
        walk(p, depth + 1);
      } else if (e.name === 'DevToolsActivePort' || /DevToolsActivePort/.test(e.name)) {
        found.push(p);
      }
    }
  };
  for (const r of roots) walk(r, 0);
  for (const p of found) {
    try {
      const lines = fs.readFileSync(p, 'utf8').split(/\r?\n/);
      const port = parseInt(lines[0], 10);
      if (port > 0) return { file: p, port };
    } catch (e) { /* keep looking */ }
  }
  return null;
}

function httpGetJson(port, urlPath) {
  return new Promise((resolve, reject) => {
    const req = require('http').request(
      { host: '127.0.0.1', port, path: urlPath, method: 'GET' },
      (res) => {
        let body = '';
        res.on('data', (c) => { body += c; });
        res.on('end', () => {
          try { resolve(JSON.parse(body)); } catch (e) { reject(new Error(body.slice(0, 200))); }
        });
      }
    );
    req.on('error', reject);
    req.end();
  });
}

function wsUrlFromHttp(port, pathName) {
  return new Promise((resolve, reject) => {
    const req = require('http').request(
      { host: '127.0.0.1', port, path: pathName, method: 'GET' },
      (res) => {
        let body = '';
        res.on('data', (c) => { body += c; });
        res.on('end', () => {
          const m = body.match(/ws:\/\/[^\s"']+/);
          if (m) resolve(m[0]); else reject(new Error('no ws url in ' + body.slice(0, 200)));
        });
      }
    );
    req.on('error', reject);
    req.end();
  });
}

class Ws {
  constructor(url) {
    const u = new URL(url);
    this.sock = net.connect(parseInt(u.port, 10), u.hostname);
    this.buf = Buffer.alloc(0);
    this.handlers = [];
    this.ready = new Promise((resolve, reject) => {
      this.sock.on('connect', () => {
        const key = crypto.randomBytes(16).toString('base64');
        this.sock.write(
          `GET ${u.pathname}${u.search} HTTP/1.1\r\n` +
          `Host: ${u.host}\r\n` +
          'Upgrade: websocket\r\nConnection: Upgrade\r\n' +
          `Sec-WebSocket-Key: ${key}\r\nSec-WebSocket-Version: 13\r\n\r\n`
        );
      });
      this.sock.on('data', (chunk) => {
        this.buf = Buffer.concat([this.buf, chunk]);
        if (!this.upgraded && this.buf.includes(Buffer.from('\r\n\r\n'))) {
          const idx = this.buf.indexOf(Buffer.from('\r\n\r\n')) + 4;
          this.buf = this.buf.slice(idx);
          this.upgraded = true;
          resolve();
        }
        if (this.upgraded) this.drain();
      });
      this.sock.on('error', reject);
    });
  }

  drain() {
    while (this.buf.length >= 2) {
      const b0 = this.buf[0];
      const b1 = this.buf[1];
      let len = b1 & 0x7f;
      let off = 2;
      if (len === 126) {
        if (this.buf.length < 4) return;
        len = this.buf.readUInt16BE(2);
        off = 4;
      } else if (len === 127) {
        if (this.buf.length < 10) return;
        len = Number(this.buf.readBigUInt64BE(2));
        off = 10;
      }
      if (this.buf.length < off + len) return;
      const payload = this.buf.slice(off, off + len);
      this.buf = this.buf.slice(off + len);
      if ((b0 & 0x0f) === 1) {
        const h = this.handlers.shift();
        if (h) h(payload.toString('utf8'));
      }
    }
  }

  send(text) {
    const data = Buffer.from(text, 'utf8');
    const mask = crypto.randomBytes(4);
    let header;
    if (data.length < 126) {
      header = Buffer.alloc(2);
      header[1] = 0x80 | data.length;
    } else if (data.length < 65536) {
      header = Buffer.alloc(4);
      header[1] = 0x80 | 126;
      header.writeUInt16BE(data.length, 2);
    } else {
      header = Buffer.alloc(10);
      header[1] = 0x80 | 127;
      header.writeBigUInt64BE(BigInt(data.length), 2);
    }
    header[0] = 0x81;
    const masked = Buffer.alloc(data.length);
    for (let i = 0; i < data.length; i++) masked[i] = data[i] ^ mask[i % 4];
    return new Promise((resolve) => {
      this.handlers.push(resolve);
      this.sock.write(Buffer.concat([header, mask, masked]));
    });
  }

  close() { try { this.sock.destroy(); } catch (e) { /* ignore */ } }
}

(async () => {
  const ep = findEndpoint();
  if (!ep) { console.error('no DevToolsActivePort found'); process.exit(2); }

  let targets;
  try {
    targets = await httpGetJson(ep.port, '/json/list');
  } catch (e) {
    console.error('cannot list targets: ' + e.message);
    process.exit(3);
  }
  const target = (targets || []).find((t) => t.id === viewId || t.webSocketDebuggerUrl === viewId);
  let wsUrl = target ? target.webSocketDebuggerUrl : null;

  if (!wsUrl) {
    // the EPC is a chrome-extension-hosted webview; its targets may sit off /json/list
    try {
      wsUrl = await wsUrlFromHttp(ep.port, '/json/version');
      console.error('view not in /json/list; version endpoint only');
    } catch (e) { /* ignore */ }
  }
  if (!wsUrl) { console.error('target not found for view ' + viewId); process.exit(4); }

  const ws = new Ws(wsUrl);
  await ws.ready;

  const id = 1;
  const msg = JSON.stringify({
    id,
    method: 'Runtime.evaluate',
    params: { expression, returnByValue: true, awaitPromise, userGesture: true },
  });
  const reply = await Promise.race([
    ws.send(msg),
    new Promise((_, rej) => setTimeout(() => rej(new Error('cdp timeout')), timeoutS * 1000)),
  ]);
  ws.close();
  const parsed = JSON.parse(reply);
  if (parsed.result && parsed.result.exceptionDetails) {
    console.error('JS exception: ' + JSON.stringify(parsed.result.exceptionDetails).slice(0, 300));
    process.exit(5);
  }
  const val = parsed.result && parsed.result.result ? parsed.result.result.value : undefined;
  process.stdout.write(typeof val === 'string' ? val : JSON.stringify(val));
})();

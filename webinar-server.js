/**
 * 🎓 Webinar Server — Claude for Everyone
 *
 * Instructor runs this once. All students open the link. No API key needed.
 *
 * Usage:
 *   node webinar-server.js YOUR_API_KEY
 *
 * Students open:
 *   http://YOUR_LOCAL_IP:7824    (same WiFi)
 *   or share the ngrok link:  npx ngrok http 7824
 */

const http  = require('http');
const https = require('https');
const fs    = require('fs');
const path  = require('path');
const os    = require('os');

const PORT = 7824;
const DIR  = __dirname;

// ── API key: command-line arg or env var ──────────────────────────
const API_KEY = process.argv[2] || process.env.CLAUDE_API_KEY || '';
if (!API_KEY || !API_KEY.startsWith('sk-')) {
  console.error('');
  console.error('  ❌  API key missing or invalid.');
  console.error('');
  console.error('  Run:  node webinar-server.js YOUR_API_KEY');
  console.error('  e.g.  node webinar-server.js sk-ant-api03-...');
  console.error('');
  process.exit(1);
}

// ── Stats tracker ─────────────────────────────────────────────────
const stats = { builds: 0, modifies: 0, students: new Set() };

// ── CORS headers ──────────────────────────────────────────────────
const CORS = {
  'Access-Control-Allow-Origin':  '*',
  'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
  'Access-Control-Allow-Headers': 'Content-Type',
};

// ── Get local IP for display ──────────────────────────────────────
function getLocalIP() {
  for (const ifaces of Object.values(os.networkInterfaces())) {
    for (const iface of ifaces) {
      if (iface.family === 'IPv4' && !iface.internal) return iface.address;
    }
  }
  return 'localhost';
}

// ── Proxy a request to Claude API ────────────────────────────────
function proxyToClaude(body, res) {
  const options = {
    hostname: 'api.anthropic.com',
    path:     '/v1/messages',
    method:   'POST',
    headers: {
      'Content-Type':      'application/json',
      'x-api-key':         API_KEY,
      'anthropic-version': '2023-06-01',
      'Content-Length':    Buffer.byteLength(body),
    },
  };

  const proxyReq = https.request(options, (proxyRes) => {
    res.writeHead(proxyRes.statusCode, { ...CORS, 'Content-Type': 'application/json' });
    proxyRes.pipe(res);
  });

  proxyReq.on('error', (err) => {
    console.error('  Claude API error:', err.message);
    res.writeHead(500, CORS);
    res.end(JSON.stringify({ error: { message: 'Proxy error: ' + err.message } }));
  });

  proxyReq.write(body);
  proxyReq.end();
}

// ── Main server ───────────────────────────────────────────────────
const server = http.createServer((req, res) => {
  const ip  = req.socket.remoteAddress || 'unknown';
  const url = (req.url || '/').split('?')[0];

  // CORS preflight
  if (req.method === 'OPTIONS') {
    res.writeHead(204, CORS);
    res.end();
    return;
  }

  // ── Serve workshop tool — inject webinar mode flag ─────────────
  if (req.method === 'GET' && (url === '/' || url === '/workshop-tool.html')) {
    const filePath = path.join(DIR, 'workshop-tool.html');
    fs.readFile(filePath, 'utf8', (err, html) => {
      if (err) {
        res.writeHead(404, CORS);
        res.end('workshop-tool.html not found — make sure this server.js is in the same folder.');
        return;
      }
      // Inject webinar mode — banner directly in HTML + JS flag + hide server box
      const banner = '<div style="background:linear-gradient(135deg,#6c3aed,#a855f7);color:#fff;text-align:center;padding:11px 16px;font-size:14px;font-weight:800;position:sticky;top:0;z-index:99999;letter-spacing:0.3px;">🎓 Webinar Mode &nbsp;—&nbsp; Claude powered by your instructor &nbsp;|&nbsp; No API key needed</div>';
      const flag   = '<script>window._WEBINAR_MODE=true;window._WEBINAR_PORT=' + PORT + ';</script>';
      const hideServerBox = '<style>#serverSetupBox,#serverPill{display:none!important;}</style>';
      let patched = html
        .replace('<head>', '<head>\n' + flag + hideServerBox)
        .replace('<body>', '<body>\n' + banner);
      res.writeHead(200, { ...CORS, 'Content-Type': 'text/html; charset=utf-8' });
      res.end(patched);
      stats.students.add(ip);
    });
    return;
  }

  // ── POST /api/claude — proxy to Anthropic ──────────────────────
  if (req.method === 'POST' && url === '/api/claude') {
    let body = '';
    req.on('data', chunk => { body += chunk.toString(); });
    req.on('end', () => {
      try {
        const parsed = JSON.parse(body);
        // Remove thinking param — not supported without special beta headers
        delete parsed.thinking;
        // Count builds vs modifies
        const isModify = parsed.messages && parsed.messages.some(m =>
          typeof m.content === 'string' && m.content.includes('existing code')
        );
        if (isModify) stats.modifies++; else stats.builds++;
        stats.students.add(ip);
        console.log(`  📨 ${isModify ? 'Modify' : 'Build '} from ${ip} | Builds: ${stats.builds} | Modifies: ${stats.modifies} | Students: ${stats.students.size}`);
        body = JSON.stringify(parsed);
      } catch(e) { console.log('  ⚠️  Parse error:', e.message); }
      proxyToClaude(body, res);
    });
    return;
  }

  // ── POST /save-preview — save generated app ────────────────────
  if (req.method === 'POST' && url === '/save-preview') {
    let body = '';
    req.on('data', chunk => { body += chunk.toString(); });
    req.on('end', () => {
      try {
        fs.writeFileSync(path.join(DIR, 'preview-app.html'), body, 'utf8');
        const previewUrl = `http://localhost:${PORT}/preview-app.html`;
        res.writeHead(200, { ...CORS, 'Content-Type': 'application/json' });
        res.end(JSON.stringify({ ok: true, url: previewUrl }));
      } catch (err) {
        res.writeHead(500, CORS);
        res.end(JSON.stringify({ ok: false, error: err.message }));
      }
    });
    return;
  }

  // ── GET — serve static files ───────────────────────────────────
  if (req.method === 'GET') {
    const filePath = path.join(DIR, url);
    const resolved = path.resolve(filePath);
    if (!resolved.startsWith(path.resolve(DIR))) {
      res.writeHead(403, CORS); res.end('Forbidden'); return;
    }
    fs.readFile(resolved, (err, data) => {
      if (err) { res.writeHead(404, CORS); res.end('Not Found'); return; }
      const ext  = path.extname(url).toLowerCase();
      const mime = { '.html': 'text/html', '.js': 'text/javascript', '.css': 'text/css', '.png': 'image/png' }[ext] || 'application/octet-stream';
      res.writeHead(200, { ...CORS, 'Content-Type': mime });
      res.end(data);
    });
    return;
  }

  res.writeHead(404, CORS);
  res.end('Not found');
});

// ── Start ─────────────────────────────────────────────────────────
server.listen(PORT, '0.0.0.0', () => {
  const localIP = getLocalIP();
  const masked  = API_KEY.slice(0, 16) + '...' + API_KEY.slice(-4);

  console.log('');
  console.log('  ╔══════════════════════════════════════════════════════╗');
  console.log('  ║  🎓  WEBINAR MODE — Claude for Everyone             ║');
  console.log('  ╠══════════════════════════════════════════════════════╣');
  console.log('  ║                                                      ║');
  console.log(`  ║  🔑 API Key : ${masked.padEnd(38)}║`);
  console.log('  ║                                                      ║');
  console.log('  ║  Share this link with your students:                ║');
  console.log(`  ║  👉 http://${localIP}:${PORT}${''.padEnd(27 - localIP.length)}║`);
  console.log('  ║                                                      ║');
  console.log('  ║  For students outside your WiFi, also run:          ║');
  console.log('  ║    npx ngrok http ' + PORT + '                              ║');
  console.log('  ║                                                      ║');
  console.log('  ║  Keep this window open during the webinar.          ║');
  console.log('  ║  Press Ctrl+C to stop.                              ║');
  console.log('  ╚══════════════════════════════════════════════════════╝');
  console.log('');
  console.log('  Waiting for students...');
  console.log('');
});

server.on('error', (err) => {
  if (err.code === 'EADDRINUSE') {
    console.error(`\n  ❌  Port ${PORT} is in use. Stop the other server first.\n`);
  } else {
    console.error('  Server error:', err);
  }
  process.exit(1);
});

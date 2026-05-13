/**
 * Build My App — Local Dev Server
 *
 * Serves the workshop tool AND accepts generated apps via POST.
 * When the tool POSTs an app's HTML to /save-preview, this server saves
 * it as preview-app.html and returns the localhost URL.
 *
 * This means generated apps open as real HTTP pages — zero hacks needed,
 * Firebase works 100%, all buttons work, everything is perfect.
 *
 * Run:  node server.js
 * Tool: http://localhost:7823/workshop-tool.html
 */

const http  = require('http');
const fs    = require('fs');
const path  = require('path');

const PORT = 7823;
const DIR  = __dirname;

const MIME = {
  '.html': 'text/html; charset=utf-8',
  '.js':   'text/javascript',
  '.css':  'text/css',
  '.png':  'image/png',
  '.jpg':  'image/jpeg',
  '.jpeg': 'image/jpeg',
  '.svg':  'image/svg+xml',
  '.ico':  'image/x-icon',
  '.json': 'application/json',
  '.mp4':  'video/mp4',
};

const CORS = {
  'Access-Control-Allow-Origin':  '*',
  'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
  'Access-Control-Allow-Headers': 'Content-Type',
};

const server = http.createServer((req, res) => {
  // --- CORS preflight ---
  if (req.method === 'OPTIONS') {
    res.writeHead(204, CORS);
    res.end();
    return;
  }

  // ------------------------------------------------------------------
  // POST /save-preview  — workshop tool sends generated HTML here
  // We save it as preview-app.html and return the URL to open.
  // ------------------------------------------------------------------
  if (req.method === 'POST' && req.url === '/save-preview') {
    let body = '';
    req.on('data', chunk => { body += chunk.toString(); });
    req.on('end', () => {
      try {
        const savePath = path.join(DIR, 'preview-app.html');
        fs.writeFileSync(savePath, body, 'utf8');
        const previewUrl = `http://localhost:${PORT}/preview-app.html`;
        res.writeHead(200, { ...CORS, 'Content-Type': 'application/json' });
        res.end(JSON.stringify({ ok: true, url: previewUrl }));
        console.log(`\n✅ App saved → ${previewUrl}`);
      } catch (err) {
        res.writeHead(500, { ...CORS, 'Content-Type': 'application/json' });
        res.end(JSON.stringify({ ok: false, error: err.message }));
      }
    });
    return;
  }

  // ------------------------------------------------------------------
  // GET — serve static files from this directory
  // ------------------------------------------------------------------
  if (req.method === 'GET') {
    // Use built-in URL parsing (no deprecated url.parse)
    const reqUrl  = new URL(req.url, `http://localhost:${PORT}`);
    const pathname = reqUrl.pathname;
    let filePath = path.join(DIR, pathname);

    // Directory → serve workshop-tool.html
    if (pathname === '/' || pathname === '') {
      filePath = path.join(DIR, 'workshop-tool.html');
    }

    // Security: prevent path traversal outside DIR
    const resolved = path.resolve(filePath);
    if (!resolved.startsWith(path.resolve(DIR))) {
      res.writeHead(403, CORS);
      res.end('Forbidden');
      return;
    }

    fs.readFile(resolved, (err, data) => {
      if (err) {
        res.writeHead(404, { ...CORS, 'Content-Type': 'text/plain' });
        res.end('404 Not Found: ' + pathname);
        return;
      }
      const ext  = path.extname(filePath).toLowerCase();
      const mime = MIME[ext] || 'application/octet-stream';
      res.writeHead(200, { ...CORS, 'Content-Type': mime });
      res.end(data);
    });
    return;
  }

  res.writeHead(405, CORS);
  res.end('Method Not Allowed');
});

server.listen(PORT, () => {
  console.log('');
  console.log('╔════════════════════════════════════════════════════╗');
  console.log('║  ⚡ Build My App — Local Server Running            ║');
  console.log('╠════════════════════════════════════════════════════╣');
  console.log(`║  Workshop Tool  →  http://localhost:${PORT}/         ║`);
  console.log(`║  Generated App  →  http://localhost:${PORT}/preview  ║`);
  console.log('╚════════════════════════════════════════════════════╝');
  console.log('');
});

server.on('error', (err) => {
  if (err.code === 'EADDRINUSE') {
    console.error(`\n❌ Port ${PORT} is already in use. Stop the other server first.\n`);
  } else {
    console.error('Server error:', err);
  }
  process.exit(1);
});

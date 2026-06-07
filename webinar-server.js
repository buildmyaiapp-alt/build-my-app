// ============================================================
// BUILD MY APP — Workshop Proxy Server
// Runs on Railway — forwards Claude API calls from students
// Students don't need their own API key
// ============================================================

const http  = require('http');
const https = require('https');
const PORT  = process.env.PORT || 7824;
const API_KEY = process.env.ANTHROPIC_API_KEY || '';

const ALLOWED_ORIGIN = '*';

function handleCORS(res) {
  res.setHeader('Access-Control-Allow-Origin', ALLOWED_ORIGIN);
  res.setHeader('Access-Control-Allow-Methods', 'POST, GET, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type, x-api-key, anthropic-version');
}

http.createServer((req, res) => {
  handleCORS(res);

  // CORS preflight
  if (req.method === 'OPTIONS') {
    res.writeHead(204);
    res.end();
    return;
  }

  // Health check
  if (req.method === 'GET' || req.url === '/health') {
    res.writeHead(200, { 'Content-Type': 'application/json' });
    res.end(JSON.stringify({ status: 'ok', workshop: 'Build My App', keySet: !!API_KEY }));
    return;
  }

  // Proxy Claude API calls
  if (req.method === 'POST') {
    let body = '';
    req.on('data', chunk => body += chunk);
    req.on('end', () => {
      try {
        const payload = JSON.parse(body);

        const options = {
          hostname: 'api.anthropic.com',
          path:     '/v1/messages',
          method:   'POST',
          headers:  {
            'Content-Type':      'application/json',
            'x-api-key':         API_KEY,
            'anthropic-version': '2023-06-01',
          }
        };

        const proxyReq = https.request(options, proxyRes => {
          handleCORS(res);
          res.writeHead(proxyRes.statusCode, { 'Content-Type': 'application/json' });
          proxyRes.pipe(res);
        });

        proxyReq.on('error', err => {
          res.writeHead(500, { 'Content-Type': 'application/json' });
          res.end(JSON.stringify({ error: err.message }));
        });

        proxyReq.write(JSON.stringify(payload));
        proxyReq.end();

      } catch (err) {
        res.writeHead(400, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({ error: 'Invalid JSON: ' + err.message }));
      }
    });
    return;
  }

  res.writeHead(404);
  res.end('Not found');

}).listen(PORT, () => {
  console.log(`✅ Workshop proxy server running on port ${PORT}`);
  console.log(`   API key set: ${!!API_KEY}`);
});

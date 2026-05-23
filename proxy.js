// Little Jimmy — Capital.com account-switch proxy
// Runs on http://localhost:3001
// Needed because PUT /api/v1/session/account/{id} is blocked by CORS from GitHub Pages.
// Usage: node proxy.js  (or double-click start-proxy.bat)

const http  = require('http');
const https = require('https');

const PORT = 3001;

const server = http.createServer((req, res) => {
  const origin = req.headers.origin || '*';

  // CORS — allow any origin; this proxy only listens on 127.0.0.1
  res.setHeader('Access-Control-Allow-Origin',  origin);
  res.setHeader('Access-Control-Allow-Methods', 'POST, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type');
  res.setHeader('Access-Control-Max-Age',       '86400');
  res.setHeader('Vary', 'Origin');

  // Preflight
  if (req.method === 'OPTIONS') {
    res.writeHead(204);
    res.end();
    return;
  }

  // ── POST /switch-account ──────────────────────────────────────────
  if (req.method === 'POST' && req.url === '/switch-account') {
    let raw = '';
    req.on('data', chunk => { raw += chunk; });
    req.on('end', () => {
      // Parse body
      let body;
      try { body = JSON.parse(raw); }
      catch (e) {
        res.writeHead(400, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({ error: 'Invalid JSON body' }));
        return;
      }

      const { accountId, CST, SEC, apiKey, base } = body;
      if (!accountId || !CST || !apiKey || !base) {
        res.writeHead(400, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({ error: 'Missing required fields: accountId, CST, apiKey, base' }));
        return;
      }

      // Build the Capital.com target URL
      let targetUrl;
      try { targetUrl = new URL(`/api/v1/session/account/${accountId}`, base); }
      catch (e) {
        res.writeHead(400, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({ error: 'Invalid base URL' }));
        return;
      }

      console.log(`[Proxy] PUT ${targetUrl.href}`);

      const options = {
        hostname: targetUrl.hostname,
        port:     443,
        path:     targetUrl.pathname + targetUrl.search,
        method:   'PUT',
        headers:  {
          'Content-Type':      'application/json',
          'Content-Length':    '0',
          'CST':               CST,
          'X-SECURITY-TOKEN':  SEC || '',
          'X-CAP-API-KEY':     apiKey,
        },
      };

      const upstream = https.request(options, upstreamRes => {
        console.log(`[Proxy] Capital.com → ${upstreamRes.statusCode}`);

        // Forward Capital.com's session tokens to the browser
        const reply = {
          'Content-Type':              'application/json',
          'Access-Control-Allow-Origin': origin,
        };
        const newCST = upstreamRes.headers['cst'];
        const newSEC = upstreamRes.headers['x-security-token'];
        if (newCST) reply['CST']               = newCST;
        if (newSEC) reply['X-SECURITY-TOKEN']  = newSEC;

        res.writeHead(upstreamRes.statusCode, reply);

        let responseBody = '';
        upstreamRes.on('data',  chunk => { responseBody += chunk; });
        upstreamRes.on('end',   ()    => { res.end(responseBody); });
      });

      upstream.on('error', err => {
        console.error('[Proxy] Upstream error:', err.message);
        res.writeHead(502, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({ error: 'Upstream error: ' + err.message }));
      });

      upstream.end();
    });
    return;
  }

  // ── Everything else → 404 ────────────────────────────────────────
  res.writeHead(404, { 'Content-Type': 'application/json' });
  res.end(JSON.stringify({ error: 'Not found. POST to /switch-account' }));
});

server.listen(PORT, '127.0.0.1', () => {
  console.log('');
  console.log('  Little Jimmy — account-switch proxy');
  console.log(`  Listening on http://localhost:${PORT}/switch-account`);
  console.log('  Press Ctrl+C to stop.');
  console.log('');
});

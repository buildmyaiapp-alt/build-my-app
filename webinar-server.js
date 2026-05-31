const http = require('http');
const PORT = process.env.PORT || 7824;

http.createServer((req, res) => {
  res.writeHead(200, {'Content-Type': 'text/html'});
  res.end(`<!DOCTYPE html><html><head><meta charset="UTF-8"/><meta name="viewport" content="width=device-width,initial-scale=1.0"/><title>Workshop Closed</title><style>*{margin:0;padding:0;box-sizing:border-box;}body{background:#0d0d1a;font-family:Inter,sans-serif;display:flex;align-items:center;justify-content:center;min-height:100vh;padding:24px;}div{text-align:center;color:#fff;}div p:first-child{font-size:64px;margin-bottom:16px;}h1{font-size:28px;font-weight:900;margin-bottom:12px;}p{font-size:16px;color:rgba(255,255,255,0.6);line-height:1.6;}</style></head><body><div><p>🎓</p><h1>Workshop has ended!</h1><p>Thank you for attending.<br/>See you in the next batch!</p></div></body></html>`);
}).listen(PORT, () => console.log(`Closed server running on port ${PORT}`));

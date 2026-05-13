#!/usr/bin/env python3
"""
Build My App — Preview Server
==============================

Mac / Linux:
    python3 start-server.py

Windows:
    Double-click  start-server.bat
    (or open Terminal/CMD and run:  python start-server.py)

Then open the tool at:  http://localhost:7823/workshop-tool.html
Or access from GitHub:  https://buildmyaiapp-alt.github.io/build-my-app/workshop-tool.html

When you build an app in the tool, it will open as:
    http://localhost:7823/preview-app.html   ← real HTTP, everything works
"""

import http.server
import json
import os
import webbrowser
import sys

PORT  = 7823
DIR   = os.path.dirname(os.path.abspath(__file__))

class PreviewHandler(http.server.SimpleHTTPRequestHandler):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DIR, **kwargs)

    # ── CORS preflight ──────────────────────────────────────────────────────────
    def do_OPTIONS(self):
        self.send_response(204)
        self._add_cors()
        self.end_headers()

    # ── POST /save-preview  — tool sends generated HTML here ───────────────────
    def do_POST(self):
        if self.path == '/save-preview':
            length = int(self.headers.get('Content-Length', 0))
            html   = self.rfile.read(length)
            dest   = os.path.join(DIR, 'preview-app.html')
            with open(dest, 'wb') as f:
                f.write(html)
            preview_url = f'http://localhost:{PORT}/preview-app.html'
            self.send_response(200)
            self._add_cors()
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({'ok': True, 'url': preview_url}).encode())
            print(f'\n✅  App saved  →  {preview_url}')
        else:
            self.send_response(404)
            self.end_headers()

    # ── Inject CORS headers on every response ──────────────────────────────────
    def _add_cors(self):
        self.send_header('Access-Control-Allow-Origin',  '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')

    def end_headers(self):
        self._add_cors()
        super().end_headers()

    # ── Clean log output ────────────────────────────────────────────────────────
    def log_message(self, fmt, *args):
        pass   # suppress default Apache-style logs — we print our own


def main():
    try:
        httpd = http.server.HTTPServer(('', PORT), PreviewHandler)
    except OSError:
        print(f'\n❌  Port {PORT} is already in use.')
        print(f'    Stop the other server (or close the terminal running it) and try again.\n')
        sys.exit(1)

    tool_url    = f'http://localhost:{PORT}/workshop-tool.html'
    preview_url = f'http://localhost:{PORT}/preview-app.html'

    print('')
    print('╔══════════════════════════════════════════════════════╗')
    print('║  ⚡  Build My App — Preview Server Running          ║')
    print('╠══════════════════════════════════════════════════════╣')
    print(f'║  Workshop Tool  →  {tool_url:<33}║')
    print(f'║  Your App       →  {preview_url:<33}║')
    print('╠══════════════════════════════════════════════════════╣')
    print('║  Keep this window open while using the tool.        ║')
    print('║  Press  Ctrl + C  to stop.                          ║')
    print('╚══════════════════════════════════════════════════════╝')
    print('')

    # Open the tool in the browser automatically
    webbrowser.open(tool_url)

    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print('\n\nServer stopped. Goodbye! 👋\n')


if __name__ == '__main__':
    main()

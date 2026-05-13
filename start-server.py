#!/usr/bin/env python3
"""
Build My App -- Preview Server
===============================

NO DOWNLOAD NEEDED. Paste one line in Terminal / Command Prompt:

  Mac:
    curl -fsSL https://raw.githubusercontent.com/buildmyaiapp-alt/build-my-app/main/start-server.py | python3

  Windows (Command Prompt):
    curl -s https://raw.githubusercontent.com/buildmyaiapp-alt/build-my-app/main/start-server.py -o %TEMP%\bma.py && python %TEMP%\bma.py

  Windows (PowerShell):
    python -c "import urllib.request; exec(urllib.request.urlopen('https://raw.githubusercontent.com/buildmyaiapp-alt/build-my-app/main/start-server.py').read().decode())"

OR if you already downloaded this file:
  Mac:      python3 start-server.py
  Windows:  double-click start-server.bat
"""

import http.server
import json
import os
import sys
import webbrowser

PORT = 7823

# ── Work out where to save preview-app.html ──────────────────────────────────
# When run as a file:   use the script's own directory
# When piped from URL:  __file__ is missing → use Desktop, else Home
try:
    _here = os.path.dirname(os.path.abspath(__file__))
    # If the script lives in a real directory (not stdin), use it
    DIR = _here if os.path.isdir(_here) else None
except NameError:
    DIR = None

if not DIR:
    # Piped from URL — save to Desktop if it exists, otherwise Home
    _desktop = os.path.join(os.path.expanduser('~'), 'Desktop')
    DIR = _desktop if os.path.isdir(_desktop) else os.path.expanduser('~')


class PreviewHandler(http.server.SimpleHTTPRequestHandler):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DIR, **kwargs)

    # ── CORS preflight ────────────────────────────────────────────────────────
    def do_OPTIONS(self):
        self.send_response(204)
        self._cors()
        self.end_headers()

    # ── POST /save-preview  — workshop tool sends generated HTML here ─────────
    def do_POST(self):
        if self.path == '/save-preview':
            length = int(self.headers.get('Content-Length', 0))
            html   = self.rfile.read(length)
            dest   = os.path.join(DIR, 'preview-app.html')
            with open(dest, 'wb') as f:
                f.write(html)
            preview_url = 'http://localhost:{}/preview-app.html'.format(PORT)
            self.send_response(200)
            self._cors()
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({'ok': True, 'url': preview_url}).encode())
            print('\n  App saved  ->  {}\n'.format(preview_url))
        else:
            self.send_response(404)
            self.end_headers()

    # ── Inject CORS on every response ─────────────────────────────────────────
    def _cors(self):
        self.send_header('Access-Control-Allow-Origin',  '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')

    def end_headers(self):
        self._cors()
        super().end_headers()

    def log_message(self, fmt, *args):
        pass  # silence default access log


def main():
    try:
        httpd = http.server.HTTPServer(('', PORT), PreviewHandler)
    except OSError:
        print('\n  ERROR: Port {} is already in use.'.format(PORT))
        print('  Close the other terminal window running the server and try again.\n')
        sys.exit(1)

    # If workshop-tool.html is in the same folder, open it locally.
    # Otherwise open the GitHub Pages version.
    local_tool = os.path.join(DIR, 'workshop-tool.html')
    if os.path.exists(local_tool):
        open_url = 'http://localhost:{}/workshop-tool.html'.format(PORT)
    else:
        open_url = 'https://buildmyaiapp-alt.github.io/build-my-app/workshop-tool.html'

    preview_url = 'http://localhost:{}/preview-app.html'.format(PORT)

    print('')
    print('  +--------------------------------------------------+')
    print('  |   Build My App  --  Preview Server Running      |')
    print('  +--------------------------------------------------+')
    print('  |  Tool    ->  {}  |'.format(open_url.ljust(38)))
    print('  |  App     ->  {}  |'.format(preview_url.ljust(38)))
    print('  +--------------------------------------------------+')
    print('  |  Keep this window OPEN while using the tool.    |')
    print('  |  Press  Ctrl + C  to stop the server.           |')
    print('  +--------------------------------------------------+')
    print('')

    webbrowser.open(open_url)

    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print('\n  Server stopped.\n')


if __name__ == '__main__':
    main()
else:
    # Script was exec()'d (e.g. piped via python -c "exec(...)") — run main()
    main()

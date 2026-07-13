#!/usr/bin/env python3
"""Avvia il server HTTP per Brain-Move Web.

Utilizzo:
  python serve.py              # porta 8080
  python serve.py --port 3000  # porta personalizzata
  python serve.py --open       # apre il browser automaticamente
"""

import http.server
import os
import subprocess
import sys
import webbrowser
from pathlib import Path

DIR = Path(__file__).parent
DIST = DIR / "dist"
PORT = 8080
OPEN_BROWSER = False


def build():
    print("Build in corso...")
    npm = "npm.cmd" if os.name == "nt" else "npm"
    result = subprocess.run([npm, "run", "build"], cwd=str(DIR), capture_output=True, text=True)
    if result.returncode != 0:
        print("ERRORE build:", result.stderr)
        sys.exit(1)
    print("Build completata.")


def main():
    global PORT, OPEN_BROWSER

    args = sys.argv[1:]
    i = 0
    while i < len(args):
        if args[i] == "--port" and i + 1 < len(args):
            PORT = int(args[i + 1])
            i += 2
        elif args[i] == "--open":
            OPEN_BROWSER = True
            i += 1
        else:
            print(f"Ignorato argomento sconosciuto: {args[i]}")
            i += 1

    if not DIST.is_dir():
        print("Cartella dist/ non trovata.")
        build()
    else:
        # Controlla se i file sorgente sono più recenti del build
        src_files = list((DIR / "src").rglob("*")) + [DIR / "index.html"]
        dist_files = list(DIST.rglob("*"))
        if src_files and dist_files:
            latest_src = max(f.stat().st_mtime for f in src_files)
            earliest_dist = min(f.stat().st_mtime for f in dist_files)
            if latest_src > earliest_dist:
                print("I sorgenti sono stati modificati dopo l'ultimo build.")
                build()

    os.chdir(str(DIST))

    handler = http.server.SimpleHTTPRequestHandler

    class NoCacheHandler(handler):
        def end_headers(self):
            self.send_header("Cache-Control", "no-cache, no-store, must-revalidate")
            self.send_header("Pragma", "no-cache")
            self.send_header("Expires", "0")
            super().end_headers()

    server = http.server.HTTPServer(("0.0.0.0", PORT), NoCacheHandler)

    url = f"http://localhost:{PORT}"
    print(f"\n  Brain-Move Web avviato su {url}")
    print("  Premi Ctrl+C per fermare.\n")

    if OPEN_BROWSER:
        webbrowser.open(url)

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nServer fermato.")
        server.server_close()


if __name__ == "__main__":
    main()

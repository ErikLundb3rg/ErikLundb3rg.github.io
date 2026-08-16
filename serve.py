#!/usr/bin/env python3
"""Dev server with hot reload. Run: python serve.py"""

try:
    from livereload import Server, shell
except ImportError:
    raise SystemExit("Run: pip install livereload")

import subprocess, sys
from pathlib import Path

ROOT = Path(__file__).parent
REBUILD = shell(f"{sys.executable} build.py")

subprocess.run([sys.executable, "build.py"], check=True)

server = Server()

# Watch build script
server.watch("build.py", REBUILD)

# Watch all .md files in root and every subdirectory (collections, posts, etc.)
for md in ROOT.rglob("*.md"):
    if "public" in md.parts:
        continue
    server.watch(str(md), REBUILD)

# Also watch for new files added to any directory
for d in ROOT.iterdir():
    if d.is_dir() and d.name not in ("public", ".git") and not d.name.startswith("."):
        server.watch(str(d), REBUILD)

server.serve(root="public", port=8000, open_url_delay=1)

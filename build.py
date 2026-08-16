#!/usr/bin/env python3
"""Build static HTML from Markdown posts."""

import shutil
from datetime import datetime
from pathlib import Path

try:
    import markdown
except ImportError:
    raise SystemExit("Run: pip install markdown")

ROOT   = Path(__file__).parent
POSTS  = ROOT / "posts"
PUBLIC = ROOT / "public"

RESERVED_DIRS = {"public", "posts"}

CSS = """
* { box-sizing: border-box; margin: 0; padding: 0; }
body {
    background: #f5f0e8;
    color: #2a2018;
    font-family: Georgia, 'Times New Roman', serif;
    font-size: 18px;
    line-height: 1.7;
    max-width: 640px;
    margin: 0 auto;
    padding: 2rem 1.5rem 4rem;
}
a { color: #1a4a8a; }
a:visited { color: #6b3a8a; }
header { margin-bottom: 2.5rem; border-bottom: 1px solid #c8bfaf; padding-bottom: 1rem; }
header h1 { font-size: 1.2rem; font-weight: normal; letter-spacing: 0.02em; }
header nav { margin-top: 0.4rem; font-size: 0.9rem; }
header nav a { margin-right: 1rem; text-decoration: none; }
header nav a:hover { text-decoration: underline; }
h1, h2, h3 { font-weight: normal; margin: 1.5rem 0 0.5rem; }
h1 { font-size: 1.6rem; }
h2 { font-size: 1.25rem; }
p { margin: 0.9rem 0; }
ul, ol { margin: 0.9rem 0 0.9rem 1.5rem; }
li { margin: 0.3rem 0; }
blockquote {
    border-left: 3px solid #c8bfaf;
    margin: 1rem 0;
    padding: 0.2rem 1rem;
    color: #5a4f42;
}
code {
    font-family: 'Courier New', monospace;
    font-size: 0.85em;
    background: #ebe5d9;
    padding: 0.1em 0.3em;
    border-radius: 2px;
}
pre { background: #ebe5d9; padding: 1rem; overflow-x: auto; margin: 1rem 0; }
pre code { background: none; padding: 0; }
.post-meta { font-size: 0.85rem; color: #7a6e61; margin-bottom: 1.5rem; }
.post-list { list-style: none; padding: 0; margin: 0; }
.post-list li { margin: 0.8rem 0; }
.post-list li a { display: block; }
.post-list .date { font-size: 0.85rem; color: #7a6e61; white-space: nowrap; flex-shrink: 0; }
.writing-list { list-style: none; padding: 0; margin: 0; }
.writing-list li { margin: 0.8rem 0; display: flex; gap: 1.5rem; align-items: baseline; }
.writing-list .date { font-size: 0.85rem; color: #7a6e61; white-space: nowrap; flex-shrink: 0; }
hr { border: none; border-top: 1px solid #c8bfaf; margin: 2rem 0; }
footer { margin-top: 3rem; padding-top: 1rem; border-top: 1px solid #c8bfaf; font-size: 0.85rem; color: #7a6e61; }
"""

SITE_TITLE = "Erik Lundberg"


def parse_md(path: Path) -> dict:
    text = path.read_text(encoding="utf-8")
    meta, body = {}, text
    if text.startswith("---"):
        end = text.index("---", 3)
        for line in text[3:end].strip().splitlines():
            if ":" in line:
                k, v = line.split(":", 1)
                meta[k.strip()] = v.strip()
        body = text[end + 3:].strip()
    return {
        "title":     meta.get("title", path.stem.replace("-", " ").title()),
        "date":      meta.get("date", ""),
        "nav_order": int(meta.get("nav_order", 50)),
        "slug":      path.stem,
        "body":      body,
    }


def render_date(d: str) -> str:
    try:
        return datetime.strptime(d, "%Y-%m-%d").strftime("%B %-d, %Y")
    except Exception:
        return d


def find_collections() -> list:
    """Any subdirectory (not reserved) with .md files becomes a collection."""
    cols = []
    for d in sorted(ROOT.iterdir()):
        if not d.is_dir() or d.name in RESERVED_DIRS or d.name.startswith("."):
            continue
        items = sorted([f for f in d.glob("*.md") if f.name != "_index.md"])
        if not items:
            continue
        index_file = d / "_index.md"
        meta = parse_md(index_file) if index_file.exists() else {
            "title": d.name.title(), "nav_order": 50, "date": "", "body": "", "slug": d.name,
        }
        meta["slug"] = d.name
        meta["items"] = [parse_md(f) for f in items]
        cols.append(meta)
    return cols


def build_nav(pages: list, collections: list) -> list:
    """Merge standalone pages and collections into a sorted nav list."""
    nav = []
    for p in pages:
        nav.append({"title": p["title"], "href": f'/{p["slug"]}/', "slug": p["slug"], "nav_order": p["nav_order"]})
    for c in collections:
        nav.append({"title": c["title"], "href": f'/{c["slug"]}/', "slug": c["slug"], "nav_order": c["nav_order"]})
    return sorted(nav, key=lambda n: (n["nav_order"], n["title"]))


def page(title: str, content: str, nav: list, active: str = "") -> str:
    def nav_link(href, label, slug):
        style = ' style="font-weight:bold;"' if active == slug else ""
        return f'<a href="{href}"{style}>{label}</a>'

    nav_html = '<a href="/">Writing</a>' + ("&nbsp;" if nav else "")
    nav_html = '<a href="/"' + (' style="font-weight:bold;"' if active == "writing" else "") + '>Writing</a>'
    for n in nav:
        nav_html += nav_link(n["href"], n["title"], n["slug"])

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{title} — {SITE_TITLE}</title>
  <link rel="stylesheet" href="/style.css">
</head>
<body>
<header>
  <h1><a href="/" style="text-decoration:none; color:inherit;">{SITE_TITLE}</a></h1>
  <nav>{nav_html}</nav>
</header>
{content}
<footer>&#169; {SITE_TITLE}</footer>
</body>
</html>
"""


def build():
    if PUBLIC.exists():
        shutil.rmtree(PUBLIC)
    PUBLIC.mkdir()

    (PUBLIC / "style.css").write_text(CSS, encoding="utf-8")

    pages      = sorted([parse_md(p) for p in ROOT.glob("*.md")], key=lambda p: (p["nav_order"], p["title"]))
    collections = find_collections()
    nav        = build_nav(pages, collections)

    md = markdown.Markdown(extensions=["fenced_code", "tables"])

    # Index (Writing)
    posts = sorted([parse_md(p) for p in POSTS.glob("*.md")], key=lambda p: p["date"], reverse=True)
    items = "\n".join(
        f'<li><span class="date">{render_date(p["date"])}</span>'
        f'<a href="/posts/{p["slug"]}/">{p["title"]}</a></li>'
        for p in posts
    )
    index_html = f'<ul class="writing-list">{items}</ul>' if posts else "<p>No posts yet.</p>"
    (PUBLIC / "index.html").write_text(page(SITE_TITLE, index_html, nav, "writing"), encoding="utf-8")

    # Post pages
    (PUBLIC / "posts").mkdir()
    for post in posts:
        md.reset()
        body_html = md.convert(post["body"])
        date_line = f'<p class="post-meta">{render_date(post["date"])}</p>' if post["date"] else ""
        content = f'<h1>{post["title"]}</h1>{date_line}<hr>{body_html}'
        dest = PUBLIC / "posts" / post["slug"]
        dest.mkdir()
        (dest / "index.html").write_text(page(post["title"], content, nav), encoding="utf-8")

    # Standalone pages (root *.md)
    for p in pages:
        md.reset()
        body_html = md.convert(p["body"])
        content = f'<h1>{p["title"]}</h1><hr>{body_html}'
        dest = PUBLIC / p["slug"]
        dest.mkdir()
        (dest / "index.html").write_text(page(p["title"], content, nav, p["slug"]), encoding="utf-8")

    # Collections (e.g. lists/)
    for col in collections:
        col_dir = PUBLIC / col["slug"]
        col_dir.mkdir()

        # Collection index
        items_html = "\n".join(
            f'<li><a href="/{col["slug"]}/{item["slug"]}/">{item["title"]}</a></li>'
            for item in col["items"]
        )
        content = f'<h1>{col["title"]}</h1><hr><ul class="post-list">{items_html}</ul>'
        (col_dir / "index.html").write_text(page(col["title"], content, nav, col["slug"]), encoding="utf-8")

        # Individual collection items
        for item in col["items"]:
            md.reset()
            body_html = md.convert(item["body"])
            content = f'<h1>{item["title"]}</h1><hr>{body_html}'
            dest = col_dir / item["slug"]
            dest.mkdir()
            (dest / "index.html").write_text(page(item["title"], content, nav, col["slug"]), encoding="utf-8")

    total_items = sum(len(c["items"]) for c in collections)
    print(f"Built {len(posts)} post(s), {len(pages)} page(s), {len(collections)} collection(s) ({total_items} items) → public/")


if __name__ == "__main__":
    build()

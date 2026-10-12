# ponytail: stdlib link-graph check for the rewritten snapshot
# Run from the site root:  python -I _tools/verify_links.py
# Reports unique internal URLs that resolve to no file on disk (with count and
# one example file). Exit code 1 when any are found.
import re
import sys
from pathlib import Path
from urllib.parse import urlsplit, unquote

ROOT = Path(__file__).resolve().parents[1]
ATTR_RE = re.compile(
    r'''(?:\b(?:href|src|action|poster|data-src|data-background-image|data-bg|formaction)\s*=\s*["'])([^"']+)''')
CSS_URL_RE = re.compile(r"""url\(\s*['"]?([^'")\s]+)""")
HOST_RE = re.compile(r"^(?:(?:https?:)?//)?(?:www\.)?saawe\.org\.za")
ASSET_EXT = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg", ".ico", ".css", ".js",
             ".pdf", ".zip", ".doc", ".docx", ".xls", ".xlsx", ".mp4", ".mp3",
             ".woff", ".woff2", ".ttf", ".eot", ".otf", ".avif"}

def resolve(url):
    """Root-relative URL -> the file that should serve it (dir -> index.html)."""
    p = urlsplit(unquote(url))
    parts = [s for s in p.path.strip("/").split("/") if s]
    if not parts:
        return ROOT / "index.html"
    if not Path(parts[-1]).suffix:
        parts += ["index.html"]
    qname = parts[-1] + "~" + p.query
    if p.query and ROOT.joinpath(*parts[:-1], qname).exists():
        parts[-1] = qname
    return ROOT.joinpath(*(
        "".join(c if c not in '<>:"|?*' else "_" for c in seg)
        for seg in parts[:-1] + [parts[-1]]))

misses = {}                                          # url -> [count, example file]
leftovers = 0
for f in sorted(ROOT.rglob("*")):
    if not f.is_file() or "_tools" in f.relative_to(ROOT).parts:
        continue
    ext = f.suffix.lower()
    if ext not in (".html", ".css", ".xml", ".js", ".json", ".svg", ".txt"):
        continue
    try:
        s = f.read_bytes().decode("utf-8")
    except UnicodeDecodeError:
        continue
    rel = f.relative_to(ROOT).as_posix()
    refs = ATTR_RE.findall(s) if ext == ".html" else []
    refs += [m.group(1) for m in CSS_URL_RE.finditer(s)]
    for ref in refs:
        ref = ref.strip()
        if not ref or ref.startswith(("#", "mailto:", "tel:", "javascript:", "data:")):
            continue
        if HOST_RE.match(ref):
            leftovers += 1
            print(f"LEFT   {rel}: {ref[:110]}")
            continue
        if ref.startswith("\\"):                     # JSON-escaped path ref
            ref = ref.replace("\\/", "/").lstrip("\\")
        if ref.startswith("//") or "://" in ref:
            continue                                 # external
        if ref.startswith("/"):
            if not resolve(ref).exists():
                e = misses.setdefault(ref.split("?")[0][:110], [0, rel])
                e[0] += 1
        else:                                        # page/css-relative link
            p = urlsplit(ref)
            if Path(p.path).suffix.lower() in ASSET_EXT and not (f.parent / unquote(p.path)).exists():
                e = misses.setdefault(ref.split("?")[0][:110], [0, rel])
                e[0] += 1

for url, (n, rel) in sorted(misses.items()):
    print(f"MISS x{n:<5} e.g. {rel}: {url}")
print(f"\nunique misses={len(misses)}  total={sum(v[0] for v in misses.values())}  leftover-domain-refs={leftovers}")
sys.exit(1 if (misses or leftovers) else 0)
# ponytail: fetches every internal URL the link check reports as missing.
# Usage:  python -I _tools/verify_links.py | python -I _tools/fetch_missing.py
# Reads "MISS ... : /url" lines on stdin, fetches from saawe.org.za, saves at the
# plain crawler path when content validates (magic bytes for binaries, non-HTML
# otherwise). Dead links on the live site are reported and left missing.
import re
import sys
from pathlib import Path
from urllib.parse import urlsplit, unquote
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
MAGIC = {
    b"\xff\xd8\xff": ".jpg", b"\x89PNG": ".png", b"GIF8": ".gif", b"%PDF": ".pdf",
    b"\xd0\xcf\x11\xe0": ".doc", b"wOFF": ".woff", b"OTTO": ".otf", b"\x00\x01\x00\x00": ".ttf",
}
UA = {"User-Agent": "Mozilla/5.0 (site-backup)"}

urls = sorted({line.rsplit(":", 1)[-1].strip()
               for line in sys.stdin.read().splitlines() if line.startswith("MISS")})
saved = failed = 0
for url in urls:
    path = url.split("?")[0].split("#")[0]
    dest = ROOT.joinpath(*(c for c in unquote(path).strip("/").split("/") if c))
    if not Path(dest.name).suffix:
        dest = dest / "index.html"
    if dest.exists() or not path:
        continue
    try:
        req = Request(f"https://saawe.org.za{path}", headers=UA)
        with urlopen(req, timeout=30) as r:
            data = r.read()
    except Exception as e:
        print(f"FAIL {getattr(e, 'code', type(e).__name__):>4} {url}")
        failed += 1
        continue
    ext = dest.suffix.lower()
    if ext not in (".eot", ".svg", ".html", ".txt"):
        if not any(data.startswith(m) for m in MAGIC):
            print(f"SKIP {len(data):>7}B {url} (no binary magic)")
            continue
    if len(data) < 100:
        print(f"SKIP {len(data):>7}B {url} (too small)")
        continue
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_bytes(data)
    print(f"SAVE {len(data):>7}B {path}")
    saved += 1
print(f"\nsaved={saved} failed={failed}")
# ponytail: fetches missing assets from the Wayback Machine instead of the (now
# bot-blocked / replaced) live site.
# Usage:  python -I _tools/verify_links.py | python -I _tools/fetch_wayback.py
# Reads "MISS ... : /url" lines on stdin; for each, grabs the raw capture
# (web/2026id_), saves at the plain crawler path when the content validates.
import sys
from pathlib import Path
from urllib.parse import unquote
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
WB = "https://web.archive.org/web/2026id_/https://saawe.org.za"
MAGIC = {
    b"\xff\xd8\xff": ".jpg", b"\x96j\xf1\x1e": ".eot", b"\x89PNG": ".png", b"GIF8": ".gif",
    b"\x50\x4b": ".docx", b"\xd0\xcf\x11\xe0": ".doc", b"wOFF": ".woff", b"OTTO": ".otf",
    b"\x00\x01\x00\x00": ".ttf", b"<?xml": ".svg", b"%PDF": ".pdf",
}
NO_MAGIC = {".svg", ".eot", ".txt"}

urls = sorted({line.rsplit(":", 1)[-1].strip()
               for line in sys.stdin.read().splitlines() if line.startswith("MISS")})
saved = failed = 0
for url in urls:
    path = url.split("?")[0].split("#")[0]
    if not path.startswith("/wp-content/"):
        print(f"SKIP {url} (not a static asset)")
        continue
    dest = ROOT.joinpath(*(c for c in unquote(path).strip("/").split("/") if c))
    if dest.exists():
        continue
    try:
        req = Request(f"{WB}{path}")
        with urlopen(req, timeout=60) as r:
            data = r.read()
        date = r.geturl().split("/web/")[1].split("id_")[0]
    except Exception as e:
        print(f"FAIL {getattr(e, 'code', type(e).__name__):>4} {url}")
        failed += 1
        continue
    ext = dest.suffix.lower()
    if data.lstrip()[:9] == b"<!doctype " or data.lstrip()[:5] == b"<html":
        print(f"SKIP {url} (html masquerading as asset)")
        continue
    if ext not in NO_MAGIC and not any(data.startswith(m) for m in MAGIC):
        print(f"SKIP {len(data):>7}B {url} (bad magic for .{ext})")
        continue
    if len(data) < 100:
        print(f"SKIP tiny {url}")
        continue
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_bytes(data)
    print(f"SAVE {len(data):>7}B [{date}] {path}")
    saved += 1
print(f"\nsaved={saved} failed={failed}")
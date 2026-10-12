# ponytail: stdlib rewriter for the crawled saawe.org.za snapshot; see _tools/README.md
# Run from the site root:  python -I _tools/fix_urls.py
# Pass 1 (HTML only): same-host attribute URLs of the form .../<path>?<query> are
#         rewritten to the on-disk crawler filename <path>~<query> when it exists.
# Pass 2 (all text): https://saawe.org.za (http / protocol-relative / JSON-escaped
#         variants) is stripped, making every internal URL root-relative.
import html
import re
from pathlib import Path
from urllib.parse import urlsplit, unquote

HOST = "saawe.org.za"
ROOT = Path(__file__).resolve().parents[1]
TEXT_EXT = {".html", ".css", ".js", ".xml", ".json", ".txt", ".svg"}
ATTR_RE = re.compile(
    r'''(?P<pre>\b(?:href|src|action|poster|data-src|data-background-image|data-bg|formaction)\s*=\s*["'])(?P<url>[^"']+)(?P<post>["'])'''
    r"|(?P<srcsetpre>\bsrcset\s*=\s*[\"'])(?P<srcset>[^\"']+)")

def disk_for(url):
    """Mirror of crawl.py:path_for() — root-relative -> file paths that may exist."""
    p = urlsplit(html.unescape(url))
    parts = [unquote(s) for s in p.path.strip("/").split("/") if s] or ["index.html"]
    if not Path(parts[-1]).suffix:                 # path-like URL -> dir/index.html
        parts += ["index.html"]
    out = []
    for name in ((parts[-1] + "~" + p.query) if p.query else "", parts[-1]):
        out.append(ROOT.joinpath(*(
            "".join(c if c not in '<>:"|?*' else "_" for c in s) for s in parts[:-1] + [name])))
    return out

def fix_attr(url):
    """Map a same-host URL with query to its saved filename; strip //, keep misses."""
    if HOST + "/" not in url or "?" not in url:
        return url
    if url.startswith("//"):
        url = "https:" + url
    for cand in disk_for(url):
        if cand.exists():
            return "/" + cand.relative_to(ROOT).as_posix()
    return url

def fix_srcset(v):
    return ", ".join(" ".join(fix_attr(p) if i == 0 else p
                              for i, p in enumerate(entry.split())) if HOST in entry else entry
                     for entry in v.split(","))

def main():
    n_changed = 0
    for f in sorted(ROOT.rglob("*")):
        if not f.is_file() or f.suffix.lower() not in TEXT_EXT:
            continue
        if "_tools" in f.relative_to(ROOT).parts:
            continue
        try:
            s = f.read_bytes().decode("utf-8")
        except UnicodeDecodeError:
            continue
        orig = s
        if f.suffix.lower() == ".html":
            # dead WP plumbing never saved (405 / oEmbed discovery): drop the tags
            s = re.sub(r"\s*<link rel=\"pingback\"[^>]*>", "", s)
            s = re.sub(r"\s*<link rel=\"alternate\" type=\"[^\"]*oembed\"[^>]*>", "", s)
            s = re.sub(r"\s*<link rel=\"alternate\" type=\"application/json\" href=\"/(?:af/)?wp-json/wp/v2/users/[^\"]*\"[^>]*>", "", s)
            def sub(m):
                if m.group("url") is not None:
                    fixed = fix_attr(m.group("url")).replace("&", "&amp;")
                    return m.group("pre") + fixed + m.group("post")
                return m.group("srcsetpre") + fix_srcset(m.group("srcset"))
            s = ATTR_RE.sub(sub, s)
        # domain strips: plain, protocol-relative, JSON-escaped (https:\/\/ host \/path)
        s = re.sub(r"https?://(?:www\.)?" + HOST.replace(".", r"\."), "", s)
        s = s.replace("//" + HOST + "/", "/")
        s = re.sub(r"https?:\\/\\/(?:www\.)?saawe\.org\.za", "", s)
        s = s.replace("\\/\\/saawe.org.za", "")
        if s != orig:
            f.write_bytes(s.encode("utf-8"))
            n_changed += 1
    print(f"rewrote {n_changed} files")

if __name__ == "__main__":
    main()
# _tools

Maintenance scripts for the static mirror. All stdlib Python; run from the repo
root (`python -I _tools/<script>.py`) so relative paths resolve to the site tree.

## fix_urls.py

One-time converter that turned the raw crawl (absolute `https://saawe.org.za/…`
links verbatim) into a self-contained mirror:

1. Same-host attribute URLs with a query string (`…?p=825`, `…?ver=4.25.0`) are
   rewritten to the crawler's on-disk filenames (`…~p=825`, `…~ver=4.25.0`) when
   that file exists — mirroring `backup/_tools/crawl.py:path_for`.
2. Every remaining `https://saawe.org.za` (http / protocol-relative / JSON
   `\/`-escaped variants) is stripped, making internal URLs root-relative; this
   also fixes canonical, srcset, inline `<style>` and sitemap/RSS content.
3. Dead WordPress metadata tags that were never crawable (`pingback`,
   oEmbed discovery, `wp-json/wp/v2/users` REST links) are removed.

Files are already converted; re-running is idempotent but pointless. Keep it as
documentation of what changed, in case the mirror is ever re-crawled and needs
the same pass applied.

## verify_links.py

The runnable check. Re-extracts every same-origin reference the way the crawler
does (href/src/action/poster/data-*/srcset in HTML, `url()` in CSS and inline
styles), resolves it to a file the way a static server would (directory URLs →
`index.html`, query URLs → `…~query` names), and reports every reference with no
file on disk plus any surviving absolute-domain links. Exits 1 when anything is
found, so it can gate a re-crawl or deployment.

Current known-dead set (documented in the root README) is expected output.

## fetch_missing.py / fetch_wayback.py

Both read `verify_links.py`'s MISS lines on stdin and refetch what they can:

```
python -I _tools/verify_links.py | python -I _tools/fetch_wayback.py
```

- `fetch_missing.py` fetches from the live site — blocked since 2026-10 by the
  Vercel security checkpoint now fronting www.saawe.org.za; kept for when (if)
  the checkpoint is lifted.
- `fetch_wayback.py` fetches from the Wayback Machine (`web/2026id_` raw
  captures) and validates content (magic bytes / html-page rejection) before
  writing. This is what recovered the Divi icon fonts and the larger upload
  images on 2026-10-12.

After fetching assets, re-run `fix_urls.py` only if URLs changed (plain-path
saves normally don't need it) and re-run `verify_links.py` to confirm.
# saawe.org.za — old WordPress site, static mirror

Snapshot of the old WordPress/Divi site at https://saawe.org.za ( crawled 2026-10-09, refreshed 2026-10-12 with assets recovered from the Wayback Machine). The WordPress install itself no longer exists — the live domain now serves the new site on Vercel — so this tree is the only surviving copy, served as plain static files. It is intended for Vercel: no build step, static output, served from the repo root.

## What works / what doesn't

- All 164 pages (English + Afrikaans) browse normally; internal links, images, stylesheets, fonts, and document downloads are rewritten to relative paths and verified by `_tools/verify_links.py`.
- Anything needing a server is dead, as on any static mirror: site search, comments (`wp-comments-post.php`), cart/checkout/my-account, `wp-json`, and the two stale `index.php/en/...` menu links that were already broken on the live site.
- Known-dead files (inherited from the live site at crawl time, unrecoverable — host and Wayback both lack them): the "What Can I Do" section backdrops `uploads/2021/06/{bible,church-missionaries,field,go,peace,pray,tv}.jpg`, `2018/04/Discover-the-Bible-1.png`, `2018/04/Go-1.png`, `2018/04/pexels-photo-257092.jpeg`, the two PRAYER-COUPONS FEB/MAR-2024 .doc files, and `2019/02/Short-Term-Outreaches-2019.pdf`. Pages show those sections without their backdrop photo. IE9/pre-2013 fallback font formats (`modules.eot`, `modules.svg`) for the Divi icon font are likewise absent (modern browsers load `modules.woff`/`.ttf`, which are present).

## Tools (`_tools/`)

Run from the repo root with `python -I`.

- `fix_urls.py` — one-time converter that rewrote the absolute `https://saawe.org.za/…` links in the crawl to root-relative paths and mapped query-string URLs (`?p=825`, `?ver=…`) to the crawler's `…~p=825`/`…~ver=…` filenames. Keep for reference; do not re-run (files are already converted).
- `verify_links.py` — link audit; exits non-zero if an internal reference resolves to no file. Output (one MISS line per unique URL) feeds both fetchers.
- `fetch_wayback.py` — refetches missing assets from the Wayback Machine (`verify_links.py | fetch_wayback.py`).
- `fetch_missing.py` — older variant that fetches from the live site (now bot-protected by a Vercel security checkpoint; kept in case the checkpoint is lifted).

## Serving locally

`python -m http.server 8000` from this folder, then open http://localhost:8000/ — the directory layout mirrors the old site's URL paths.
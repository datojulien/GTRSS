# Personal Podcast RSS Feeds

This repository publishes personal RSS feeds for two separate podcasts:

- **France Culture / Le Cours de l'histoire**: a fresh-feed bridge built from Radio France episode pages.
- **RTL / Les Grosses Têtes**: a splitter that turns the official Audiomeans feed into three smaller themed feeds.

The generated XML files live at the repository root on purpose so existing feed URLs stay stable.

## Feeds

| Podcast | Feed file | Generator | Browser style |
| --- | --- | --- | --- |
| Le Cours de l'histoire | `feed.xml` | `build_feed.py` | `feed-style.xsl` |
| Les Grosses Têtes, intégrales | `only_integrale_feed.xml` | `keep_integrale.py` | `grosses-tetes-style.xsl` |
| Les Grosses Têtes, extras / best-of | `only_best_feed.xml` | `keep_integrale.py` | `grosses-tetes-style.xsl` |
| Les Grosses Têtes, other episodes | `only_remaining_feed.xml` | `keep_integrale.py` | `grosses-tetes-style.xsl` |

## Repository Layout

```text
.
├── build_feed.py                 # France Culture feed builder
├── feed.xml                      # Generated France Culture feed
├── feed-style.xsl                # Browser view for feed.xml
├── episodes.json                 # France Culture archive/state
├── keep_integrale.py             # Grosses Têtes feed splitter
├── only_integrale_feed.xml       # Generated Grosses Têtes intégrale feed
├── only_best_feed.xml            # Generated Grosses Têtes extras/best-of feed
├── only_remaining_feed.xml       # Generated Grosses Têtes remaining episodes feed
├── grosses-tetes-style.xsl       # Browser view for the Grosses Têtes feeds
├── Integrales.jpg                # Grosses Têtes intégrale cover
├── Extras.jpg                    # Grosses Têtes extras cover
├── Autres.jpg                    # Grosses Têtes remaining episodes cover
├── debug_episode.py              # France Culture scraping helper
├── test_links.py                 # France Culture link discovery helper
├── test_mp3.py                   # France Culture audio discovery helper
├── update-feed.yml.backup        # GitHub Actions workflow template
└── requirements.txt
```

## Setup

Use Python 3.12 or newer.

```bash
python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
```

## Build The Feeds

Build only the France Culture feed:

```bash
python3 build_feed.py
```

This fetches recent episode pages from Radio France, merges new entries into `episodes.json`, regenerates `feed.xml`, and rewrites `feed-style.xsl`.

Build only the Grosses Têtes feeds:

```bash
python3 keep_integrale.py
```

This fetches the official Audiomeans source feed and regenerates:

- `only_integrale_feed.xml`: titles starting with `L'INTÉGRALE` or `DÉBRIEF`, except items classified as best-of.
- `only_best_feed.xml`: best-of style titles that are at least 20 minutes long.
- `only_remaining_feed.xml`: every remaining item.

By default `keep_integrale.py` only writes files. To also commit and push its generated outputs:

```bash
GTRSS_AUTO_COMMIT=1 python3 keep_integrale.py
```

## Automation

`update-feed.yml.backup` is a GitHub Actions workflow template. To enable it, copy or move it to `.github/workflows/update-feed.yml`.

The workflow is set up to:

1. Install dependencies from `requirements.txt`.
2. Run `build_feed.py`.
3. Run `keep_integrale.py`.
4. Commit all generated feed, style, and archive files if anything changed.

## Validation

Useful local checks after editing scripts or styles:

```bash
python3 -m py_compile build_feed.py keep_integrale.py
python3 - <<'PY'
import xml.etree.ElementTree as ET
for path in [
    "feed.xml",
    "only_integrale_feed.xml",
    "only_best_feed.xml",
    "only_remaining_feed.xml",
    "feed-style.xsl",
    "grosses-tetes-style.xsl",
]:
    ET.parse(path)
    print(f"{path}: ok")
PY
xsltproc feed-style.xsl feed.xml >/tmp/cours-histoire.html
xsltproc grosses-tetes-style.xsl only_integrale_feed.xml >/tmp/grosses-tetes-integrale.html
xsltproc grosses-tetes-style.xsl only_best_feed.xml >/tmp/grosses-tetes-best.html
xsltproc grosses-tetes-style.xsl only_remaining_feed.xml >/tmp/grosses-tetes-remaining.html
```

## Notes

- Keep the generated XML filenames stable unless you are ready to update podcast subscriptions.
- `episodes.json` belongs to the France Culture feed only.
- The three cover images belong to the Grosses Têtes split feeds only.
- The debug/test helper scripts are for Radio France scraping experiments and are not part of the regular build path.

## License

MIT. See `LICENSE`.

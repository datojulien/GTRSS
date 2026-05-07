#!/usr/bin/env python3
import json
import re
import html
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from datetime import datetime, timezone
from feedgen.feed import FeedGenerator
from dateutil.parser import isoparse


SHOW_URL = "https://www.radiofrance.fr/franceculture/podcasts/le-cours-de-l-histoire"
BASE_URL = "https://www.radiofrance.fr"

OUTPUT_FILE = "feed.xml"
STYLE_FILE = "feed-style.xsl"
ARCHIVE_FILE = "episodes.json"

MAX_LINKS_TO_CHECK = 30

FEED_TITLE = "Le Cours de l'histoire — Flux frais"
FEED_SUBTITLE = "Flux personnel généré depuis le site Radio France"
FEED_DESCRIPTION = (
    "Un flux RSS personnel qui récupère les épisodes depuis le site web de "
    "France Culture lorsque le flux officiel n’est pas encore à jour."
)

FEED_IMAGE = "https://www.radiofrance.fr/pikapi/images/d1d9dd6a-bb4b-4811-bfc0-e846eaeb317f/300x300"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Personal Radio France RSS generator)"
}


def fetch_html(url):
    response = requests.get(url, headers=HEADERS, timeout=25)
    response.raise_for_status()
    response.encoding = "utf-8"
    return response.text


def clean_text(value):
    if not value:
        return ""

    value = BeautifulSoup(value, "html.parser").get_text(" ", strip=True)
    value = html.unescape(value)
    value = re.sub(r"\s+", " ", value)
    return value.strip()


def parse_iso_date(value):
    if not value:
        return datetime.now(timezone.utc)

    try:
        dt = isoparse(value)
        if not dt.tzinfo:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except Exception:
        return datetime.now(timezone.utc)


def date_to_archive(dt):
    if isinstance(dt, datetime):
        return dt.isoformat()
    return str(dt)


def archive_to_date(value):
    return parse_iso_date(value)


def parse_duration_to_seconds(duration):
    if not duration:
        return None

    match = re.search(
        r"P(?:(\d+)Y)?(?:(\d+)M)?(?:(\d+)D)?T?"
        r"(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?",
        duration
    )

    if not match:
        return None

    years, months, days, hours, minutes, seconds = [
        int(x) if x else 0 for x in match.groups()
    ]

    return (
        years * 365 * 24 * 3600
        + months * 30 * 24 * 3600
        + days * 24 * 3600
        + hours * 3600
        + minutes * 60
        + seconds
    )


def seconds_to_itunes_duration(seconds):
    if not seconds:
        return None

    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    secs = seconds % 60

    if hours:
        return f"{hours}:{minutes:02d}:{secs:02d}"

    return f"{minutes}:{secs:02d}"


def normalize_audio_type(audio_type, audio_url):
    if audio_type:
        return audio_type

    lower = audio_url.lower()

    if ".mp3" in lower:
        return "audio/mpeg"

    if ".m4a" in lower or ".mp4" in lower:
        return "audio/mp4"

    return "audio/mp4"


def is_itunes_safe_image(url):
    if not url:
        return False

    clean_url = url.split("?")[0].lower()

    return (
        clean_url.endswith(".jpg")
        or clean_url.endswith(".jpeg")
        or clean_url.endswith(".png")
    )


def get_episode_links():
    html_page = fetch_html(SHOW_URL)
    soup = BeautifulSoup(html_page, "html.parser")

    links = []

    for a in soup.find_all("a", href=True):
        href = a["href"]

        if "/franceculture/podcasts/le-cours-de-l-histoire/" not in href:
            continue

        full_url = urljoin(BASE_URL, href)

        if full_url == SHOW_URL:
            continue

        if full_url not in links:
            links.append(full_url)

    return links[:MAX_LINKS_TO_CHECK]


def find_radio_episode_from_jsonld(soup):
    scripts = soup.find_all("script", type="application/ld+json")

    for script in scripts:
        if not script.string:
            continue

        try:
            data = json.loads(script.string)
        except Exception:
            continue

        graph = data.get("@graph", [])

        for item in graph:
            if item.get("@type") == "RadioEpisode":
                return item

    return None


def extract_article_metadata(soup):
    def meta_content(selector):
        tag = soup.select_one(selector)
        return tag.get("content") if tag and tag.get("content") else None

    return {
        "og_title": meta_content('meta[property="og:title"]'),
        "og_description": meta_content('meta[property="og:description"]'),
        "og_image": meta_content('meta[property="og:image"]'),
        "published": meta_content('meta[property="article:published_time"]'),
        "modified": meta_content('meta[property="article:modified_time"]'),
    }


def extract_episode_data(url):
    html_page = fetch_html(url)
    soup = BeautifulSoup(html_page, "html.parser")

    episode = find_radio_episode_from_jsonld(soup)
    metadata = extract_article_metadata(soup)

    if not episode:
        return None

    audio = episode.get("mainEntity", {}) or {}
    image = episode.get("image", {}) or {}

    audio_url = audio.get("contentUrl")

    if not audio_url:
        return None

    duration_seconds = parse_duration_to_seconds(audio.get("duration"))

    title = (
        episode.get("headline")
        or episode.get("name")
        or metadata.get("og_title")
        or "Épisode sans titre"
    )

    description = (
        episode.get("description")
        or metadata.get("og_description")
        or ""
    )

    image_url = (
        image.get("url")
        or metadata.get("og_image")
        or None
    )

    published = (
        episode.get("dateCreated")
        or metadata.get("published")
        or metadata.get("modified")
    )

    audio_type = normalize_audio_type(
        audio.get("encodingFormat"),
        audio_url
    )

    published_dt = parse_iso_date(published)

    return {
        "title": clean_text(title),
        "description": clean_text(description),
        "audio_url": audio_url,
        "audio_type": audio_type,
        "duration_seconds": duration_seconds,
        "duration_itunes": seconds_to_itunes_duration(duration_seconds),
        "published": date_to_archive(published_dt),
        "image": image_url,
        "url": url,
    }


def load_archive():
    try:
        with open(ARCHIVE_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)

        if isinstance(data, list):
            return data

        return []

    except FileNotFoundError:
        return []

    except Exception:
        return []


def save_archive(episodes):
    with open(ARCHIVE_FILE, "w", encoding="utf-8") as f:
        json.dump(episodes, f, ensure_ascii=False, indent=2)


def merge_episodes(old_episodes, new_episodes):
    merged = {}

    for episode in old_episodes:
        if episode.get("url"):
            merged[episode["url"]] = episode

    for episode in new_episodes:
        if episode.get("url"):
            merged[episode["url"]] = episode

    episodes = list(merged.values())

    episodes.sort(
        key=lambda item: archive_to_date(item.get("published")),
        reverse=True
    )

    return episodes


def write_stylesheet():
    xsl = """<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet version="1.0"
  xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
  xmlns:itunes="http://www.itunes.com/dtds/podcast-1.0.dtd">

<xsl:output method="html" encoding="UTF-8" indent="yes"/>

<xsl:template match="/">
<html>
<head>
  <meta charset="UTF-8"/>
  <title><xsl:value-of select="/rss/channel/title"/></title>
  <style>
    body {
      margin: 0;
      font-family: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      background: #111;
      color: #f5f5f5;
      line-height: 1.5;
    }

    .hero {
      padding: 56px 24px;
      background: linear-gradient(135deg, #351057, #7b1fa2, #111);
      border-bottom: 1px solid rgba(255,255,255,0.15);
    }

    .wrap {
      max-width: 950px;
      margin: 0 auto;
    }

    h1 {
      margin: 0 0 12px;
      font-size: 42px;
      letter-spacing: -0.04em;
    }

    .subtitle {
      max-width: 720px;
      font-size: 18px;
      opacity: 0.9;
    }

    .badge {
      display: inline-block;
      margin-bottom: 18px;
      padding: 6px 12px;
      border-radius: 999px;
      background: rgba(255,255,255,0.14);
      font-size: 13px;
      text-transform: uppercase;
      letter-spacing: 0.08em;
    }

    .content {
      padding: 32px 24px 64px;
    }

    .episode {
      display: grid;
      grid-template-columns: 120px 1fr;
      gap: 20px;
      padding: 22px;
      margin-bottom: 18px;
      border-radius: 24px;
      background: #1b1b1f;
      border: 1px solid rgba(255,255,255,0.08);
      box-shadow: 0 10px 35px rgba(0,0,0,0.25);
    }

    .episode img {
      width: 120px;
      height: 120px;
      object-fit: cover;
      border-radius: 18px;
      background: #333;
    }

    .episode h2 {
      margin: 0 0 8px;
      font-size: 22px;
      line-height: 1.2;
    }

    .episode h2 a {
      color: #fff;
      text-decoration: none;
    }

    .date {
      color: #c9a8ff;
      font-size: 14px;
      margin-bottom: 10px;
    }

    .desc {
      color: #ddd;
      margin-bottom: 14px;
    }

    audio {
      width: 100%;
      margin-top: 8px;
    }

    .rss-note {
      margin-top: 24px;
      padding: 16px 18px;
      border-radius: 16px;
      background: rgba(255,255,255,0.08);
      color: #ddd;
      font-size: 14px;
    }

    @media (max-width: 650px) {
      .episode {
        grid-template-columns: 1fr;
      }

      .episode img {
        width: 100%;
        height: auto;
        max-height: 280px;
      }

      h1 {
        font-size: 32px;
      }
    }
  </style>
</head>

<body>
  <section class="hero">
    <div class="wrap">
      <div class="badge">RSS personnel</div>
      <h1><xsl:value-of select="/rss/channel/title"/></h1>
      <div class="subtitle">
        <xsl:value-of select="/rss/channel/description"/>
      </div>
      <div class="rss-note">
        This is a podcast RSS feed. Copy this URL into a podcast app to subscribe.
      </div>
    </div>
  </section>

  <main class="content">
    <div class="wrap">
      <xsl:for-each select="/rss/channel/item">
        <article class="episode">
          <div>
            <xsl:choose>
              <xsl:when test="itunes:image/@href">
                <img>
                  <xsl:attribute name="src">
                    <xsl:value-of select="itunes:image/@href"/>
                  </xsl:attribute>
                </img>
              </xsl:when>
            </xsl:choose>
          </div>

          <div>
            <h2>
              <a>
                <xsl:attribute name="href">
                  <xsl:value-of select="link"/>
                </xsl:attribute>
                <xsl:value-of select="title"/>
              </a>
            </h2>

            <div class="date">
              <xsl:value-of select="pubDate"/>
            </div>

            <div class="desc">
              <xsl:value-of select="description"/>
            </div>

            <audio controls="controls">
              <source>
                <xsl:attribute name="src">
                  <xsl:value-of select="enclosure/@url"/>
                </xsl:attribute>
                <xsl:attribute name="type">
                  <xsl:value-of select="enclosure/@type"/>
                </xsl:attribute>
              </source>
            </audio>
          </div>
        </article>
      </xsl:for-each>
    </div>
  </main>
</body>
</html>
</xsl:template>
</xsl:stylesheet>
"""

    with open(STYLE_FILE, "w", encoding="utf-8") as f:
        f.write(xsl)


def build_rss(episodes):
    fg = FeedGenerator()
    fg.load_extension("podcast")

    fg.id(SHOW_URL)
    fg.title(FEED_TITLE)
    fg.subtitle(FEED_SUBTITLE)
    fg.description(FEED_DESCRIPTION)
    fg.language("fr")
    fg.link(href=SHOW_URL, rel="alternate")
    fg.link(href=OUTPUT_FILE, rel="self")
    fg.author({"name": "Radio France / France Culture"})
    fg.logo(FEED_IMAGE)
    fg.updated(datetime.now(timezone.utc))

    fg.podcast.itunes_author("France Culture")
    fg.podcast.itunes_summary(FEED_DESCRIPTION)
    fg.podcast.itunes_subtitle(FEED_SUBTITLE)
    fg.podcast.itunes_owner(
        name="Personal RSS Bridge",
        email="no-reply@example.com"
    )
    fg.podcast.itunes_explicit("no")
    fg.podcast.itunes_category("History")

    if is_itunes_safe_image(FEED_IMAGE):
        fg.podcast.itunes_image(FEED_IMAGE)

    for episode in episodes:
        published_dt = archive_to_date(episode.get("published"))

        fe = fg.add_entry()

        fe.id(episode["url"])
        fe.title(episode["title"])
        fe.link(href=episode["url"])
        fe.guid(episode["url"], permalink=True)
        fe.published(published_dt)
        fe.updated(published_dt)

        rich_description = f"""
        <p>{html.escape(episode.get("description", ""))}</p>
        <p><strong>Source:</strong> <a href="{episode["url"]}">France Culture</a></p>
        """

        if episode.get("image"):
            rich_description += f"""
            <p>
              <img src="{episode["image"]}" alt="{html.escape(episode["title"])}" />
            </p>
            """

        fe.description(episode.get("description", ""))
        fe.content(rich_description, type="CDATA")

        fe.enclosure(
            episode["audio_url"],
            str(episode.get("duration_seconds") or 0),
            episode.get("audio_type") or "audio/mp4"
        )

        fe.podcast.itunes_author("France Culture")
        fe.podcast.itunes_summary(episode.get("description", ""))
        fe.podcast.itunes_subtitle(episode.get("description", "")[:255])

        if episode.get("duration_itunes"):
            fe.podcast.itunes_duration(episode["duration_itunes"])

        if is_itunes_safe_image(episode.get("image")):
            fe.podcast.itunes_image(episode["image"])

    rss = fg.rss_str(pretty=True)

    stylesheet = f'<?xml-stylesheet type="text/xsl" href="{STYLE_FILE}"?>\n'.encode("utf-8")

    if rss.startswith(b"<?xml"):
        first_line_end = rss.find(b"\n") + 1
        rss = rss[:first_line_end] + stylesheet + rss[first_line_end:]

    with open(OUTPUT_FILE, "wb") as f:
        f.write(rss)


def build_feed():
    print("Loading archive...")
    archive = load_archive()
    known_urls = {episode.get("url") for episode in archive}

    print(f"Archive contains {len(archive)} episodes")

    print("Fetching website episode links...")
    links = get_episode_links()
    print(f"Found {len(links)} episode links on website")

    new_episodes = []

    for link in links:
        if link in known_urls:
            print(f"Already archived: {link}")
            continue

        print(f"Checking: {link}")

        try:
            data = extract_episode_data(link)

            if not data:
                print("  -> skipped, no valid episode data")
                continue

            new_episodes.append(data)
            print(f"  -> added: {data['title']}")

        except Exception as error:
            print(f"  -> error: {error}")

    all_episodes = merge_episodes(archive, new_episodes)

    save_archive(all_episodes)
    write_stylesheet()
    build_rss(all_episodes)

    print()
    print(f"New episodes added: {len(new_episodes)}")
    print(f"Total archived episodes: {len(all_episodes)}")
    print(f"Created {OUTPUT_FILE}")
    print(f"Created {STYLE_FILE}")
    print(f"Updated {ARCHIVE_FILE}")


if __name__ == "__main__":
    build_feed()

#!/usr/bin/env python3
"""Build Radio France personal podcast RSS feeds."""

from __future__ import annotations

import html
import json
import os
import re
import tempfile
from dataclasses import dataclass
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path
from typing import Iterable
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup
from dateutil.parser import isoparse
from feedgen.feed import FeedGenerator
from lxml import etree
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


BASE_URL = "https://www.radiofrance.fr"
DEFAULT_PUBLIC_BASE_URL = "https://datojulien.github.io/GTRSS/"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Personal Radio France RSS generator)"
}


@dataclass(frozen=True)
class RadioFranceFeedConfig:
    show_url: str
    show_path: str
    output_file: str
    style_file: str
    archive_file: str
    feed_title: str
    feed_subtitle: str
    feed_description: str
    feed_image: str
    feed_author_name: str
    itunes_author: str
    itunes_category: str
    source_label: str
    max_links_to_check: int = 30
    follow_pagination: bool = False
    max_pages_to_check: int = 1
    min_published_date: str | None = None
    stop_when_before_min_published_date: bool = False


FRANCE_CULTURE_CONFIG = RadioFranceFeedConfig(
    show_url="https://www.radiofrance.fr/franceculture/podcasts/le-cours-de-l-histoire",
    show_path="/franceculture/podcasts/le-cours-de-l-histoire/",
    output_file="feed.xml",
    style_file="feed-style.xsl",
    archive_file="episodes.json",
    feed_title="Le Cours de l'histoire — Flux frais",
    feed_subtitle="Flux personnel généré depuis le site Radio France",
    feed_description=(
        "Un flux RSS personnel qui récupère les épisodes depuis le site web de "
        "France Culture lorsque le flux officiel n’est pas encore à jour."
    ),
    feed_image=(
        "https://www.radiofrance.fr/pikapi/images/"
        "d1d9dd6a-bb4b-4811-bfc0-e846eaeb317f/300x300"
    ),
    feed_author_name="Radio France / France Culture",
    itunes_author="France Culture",
    itunes_category="History",
    source_label="France Culture",
)


ARCHIVE_REQUIRED_TEXT_FIELDS = ("title", "url", "audio_url", "audio_type", "published")
ARCHIVE_OPTIONAL_FIELDS = (
    "description",
    "duration_seconds",
    "duration_itunes",
    "image",
    "audio_length",
)


def public_base_url() -> str:
    base_url = os.environ.get("GTRSS_PUBLIC_BASE_URL", DEFAULT_PUBLIC_BASE_URL).strip()
    if not base_url:
        base_url = DEFAULT_PUBLIC_BASE_URL
    return base_url.rstrip("/") + "/"


def public_file_url(filename: str) -> str:
    return urljoin(public_base_url(), filename)


def create_session() -> requests.Session:
    retry = Retry(
        total=3,
        connect=3,
        read=3,
        status=3,
        backoff_factor=0.75,
        status_forcelist=(429, 500, 502, 503, 504),
        allowed_methods=("GET", "HEAD"),
        raise_on_status=False,
    )
    adapter = HTTPAdapter(max_retries=retry)
    session = requests.Session()
    session.headers.update(HEADERS)
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    return session


def fetch_html(session: requests.Session, url: str) -> str:
    response = session.get(url, timeout=25)
    response.raise_for_status()
    response.encoding = "utf-8"
    return response.text


def fetch_content_length(session: requests.Session, url: str) -> int:
    try:
        response = session.head(url, allow_redirects=True, timeout=20)
        response.raise_for_status()
        content_length = response.headers.get("Content-Length")
        if content_length and content_length.isdigit():
            return int(content_length)
    except requests.RequestException:
        pass
    return 0


def atomic_write_bytes(path: str | Path, data: bytes) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        "wb",
        delete=False,
        dir=str(target.parent or Path(".")),
        prefix=f".{target.name}.",
    ) as tmp:
        tmp.write(data)
        tmp_name = tmp.name
    os.replace(tmp_name, target)


def atomic_write_text(path: str | Path, text: str) -> None:
    atomic_write_bytes(path, text.encode("utf-8"))


def clean_text(value: str | None) -> str:
    if not value:
        return ""

    value = BeautifulSoup(value, "html.parser").get_text(" ", strip=True)
    value = html.unescape(value)
    value = re.sub(r"\s+", " ", value)
    return value.strip()


def parse_iso_date(value: str | None) -> datetime:
    if not value:
        raise ValueError("missing date")

    dt = isoparse(value)
    if not dt.tzinfo:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt


def date_to_archive(dt: datetime) -> str:
    return dt.isoformat()


def archive_to_date(value: str | None) -> datetime:
    return parse_iso_date(value)


def parse_duration_to_seconds(duration: str | None) -> int | None:
    if not duration:
        return None

    match = re.fullmatch(
        r"P(?:(\d+)Y)?(?:(\d+)M)?(?:(\d+)D)?T?"
        r"(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?",
        duration,
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


def seconds_to_itunes_duration(seconds: int | None) -> str | None:
    if not seconds:
        return None

    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    secs = seconds % 60

    if hours:
        return f"{hours}:{minutes:02d}:{secs:02d}"

    return f"{minutes}:{secs:02d}"


def normalize_audio_type(audio_type: str | None, audio_url: str) -> str:
    if audio_type:
        return audio_type

    lower = audio_url.lower()

    if ".mp3" in lower:
        return "audio/mpeg"

    if ".m4a" in lower or ".mp4" in lower:
        return "audio/mp4"

    return "audio/mp4"


def is_itunes_safe_image(url: str | None) -> bool:
    if not url:
        return False

    clean_url = url.split("?")[0].lower()

    return (
        clean_url.endswith(".jpg")
        or clean_url.endswith(".jpeg")
        or clean_url.endswith(".png")
    )


def is_http_url(value: str) -> bool:
    parsed = urlparse(value)
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)


def extract_episode_links_from_soup(
    soup: BeautifulSoup,
    config: RadioFranceFeedConfig,
) -> list[str]:
    links = []

    for anchor in soup.find_all("a", href=True):
        href = anchor["href"]

        if config.show_path not in href:
            continue

        full_url = urljoin(BASE_URL, href)

        if full_url == config.show_url:
            continue

        if full_url not in links:
            links.append(full_url)

    return links


def find_next_page_url(soup: BeautifulSoup, current_url: str) -> str | None:
    next_tag = soup.find("link", rel=lambda value: value and "next" in value)

    if not next_tag or not next_tag.get("href"):
        return None

    return urljoin(current_url, next_tag["href"])


def get_episode_links_from_page(
    session: requests.Session,
    page_url: str,
    config: RadioFranceFeedConfig,
) -> tuple[list[str], str | None]:
    html_page = fetch_html(session, page_url)
    soup = BeautifulSoup(html_page, "html.parser")

    return (
        extract_episode_links_from_soup(soup, config),
        find_next_page_url(soup, page_url),
    )


def get_episode_links(
    session: requests.Session,
    config: RadioFranceFeedConfig,
) -> list[str]:
    links = []
    seen_links = set()
    seen_pages = set()
    page_url = config.show_url

    for _ in range(config.max_pages_to_check):
        if not page_url or page_url in seen_pages:
            break

        seen_pages.add(page_url)
        page_links, next_page_url = get_episode_links_from_page(session, page_url, config)

        for link in page_links:
            if link in seen_links:
                continue

            seen_links.add(link)
            links.append(link)

            if len(links) >= config.max_links_to_check:
                return links

        if not config.follow_pagination:
            break

        page_url = next_page_url

    if not links:
        raise RuntimeError(f"No episode links found for {config.show_url}")

    return links


def find_radio_episode_from_jsonld(soup: BeautifulSoup) -> dict | None:
    scripts = soup.find_all("script", type="application/ld+json")

    for script in scripts:
        if not script.string:
            continue

        try:
            data = json.loads(script.string)
        except json.JSONDecodeError:
            continue

        graph = data.get("@graph", [])

        for item in graph:
            if item.get("@type") == "RadioEpisode":
                return item

    return None


def extract_article_metadata(soup: BeautifulSoup) -> dict[str, str | None]:
    def meta_content(selector: str) -> str | None:
        tag = soup.select_one(selector)
        return tag.get("content") if tag and tag.get("content") else None

    return {
        "og_title": meta_content('meta[property="og:title"]'),
        "og_description": meta_content('meta[property="og:description"]'),
        "og_image": meta_content('meta[property="og:image"]'),
        "published": meta_content('meta[property="article:published_time"]'),
        "modified": meta_content('meta[property="article:modified_time"]'),
    }


def extract_episode_data(
    session: requests.Session,
    url: str,
) -> dict | None:
    html_page = fetch_html(session, url)
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

    image_url = image.get("url") or metadata.get("og_image") or None
    published = (
        episode.get("dateCreated")
        or metadata.get("published")
        or metadata.get("modified")
    )
    published_dt = parse_iso_date(published)
    audio_type = normalize_audio_type(audio.get("encodingFormat"), audio_url)

    data = {
        "title": clean_text(title),
        "description": clean_text(description),
        "audio_url": audio_url,
        "audio_type": audio_type,
        "duration_seconds": duration_seconds,
        "duration_itunes": seconds_to_itunes_duration(duration_seconds),
        "published": date_to_archive(published_dt),
        "image": image_url,
        "url": url,
        "audio_length": fetch_content_length(session, audio_url),
    }
    validate_episode(data)
    return data


def normalize_archive_episode(episode: dict, index: int) -> dict:
    if not isinstance(episode, dict):
        raise ValueError(f"Archive item {index} is not an object")

    normalized = dict(episode)
    for key in ARCHIVE_OPTIONAL_FIELDS:
        normalized.setdefault(key, None)
    normalized["audio_length"] = int(normalized.get("audio_length") or 0)
    validate_episode(normalized, index=index)
    return normalized


def validate_episode(episode: dict, index: int | None = None) -> None:
    label = f"Archive item {index}" if index is not None else "Episode"

    for key in ARCHIVE_REQUIRED_TEXT_FIELDS:
        if not isinstance(episode.get(key), str) or not episode[key].strip():
            raise ValueError(f"{label} has missing or invalid {key}")

    if not is_http_url(episode["url"]):
        raise ValueError(f"{label} has invalid url: {episode['url']}")

    if not is_http_url(episode["audio_url"]):
        raise ValueError(f"{label} has invalid audio_url: {episode['audio_url']}")

    archive_to_date(episode.get("published"))

    duration_seconds = episode.get("duration_seconds")
    if duration_seconds is not None and (
        not isinstance(duration_seconds, int) or duration_seconds < 0
    ):
        raise ValueError(f"{label} has invalid duration_seconds")

    audio_length = episode.get("audio_length")
    if audio_length is not None and (
        not isinstance(audio_length, int) or audio_length < 0
    ):
        raise ValueError(f"{label} has invalid audio_length")


def validate_archive(episodes: Iterable[dict]) -> list[dict]:
    normalized = []
    seen_urls = set()

    for index, episode in enumerate(episodes, 1):
        item = normalize_archive_episode(episode, index)
        if item["url"] in seen_urls:
            raise ValueError(f"Duplicate archive URL: {item['url']}")
        seen_urls.add(item["url"])
        normalized.append(item)

    return normalized


def load_archive(config: RadioFranceFeedConfig) -> list[dict]:
    path = Path(config.archive_file)
    if not path.exists():
        return []

    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)

    if not isinstance(data, list):
        raise ValueError(f"{config.archive_file} must contain a JSON list")

    return validate_archive(data)


def save_archive(config: RadioFranceFeedConfig, episodes: list[dict]) -> None:
    episodes = validate_archive(episodes)
    text = json.dumps(episodes, ensure_ascii=False, indent=2) + "\n"
    atomic_write_text(config.archive_file, text)


def hydrate_audio_lengths(
    session: requests.Session,
    episodes: Iterable[dict],
) -> list[dict]:
    hydrated = []

    for episode in episodes:
        item = dict(episode)
        if not item.get("audio_length"):
            item["audio_length"] = fetch_content_length(session, item["audio_url"])
        validate_episode(item)
        hydrated.append(item)

    return hydrated


def merge_episodes(old_episodes: Iterable[dict], new_episodes: Iterable[dict]) -> list[dict]:
    merged = {}

    for episode in old_episodes:
        merged[episode["url"]] = episode

    for episode in new_episodes:
        merged[episode["url"]] = episode

    return sort_episodes_newest_first(merged.values())


def filter_episodes_by_min_date(
    config: RadioFranceFeedConfig,
    episodes: Iterable[dict],
) -> list[dict]:
    if not config.min_published_date:
        return list(episodes)

    min_date = parse_iso_date(config.min_published_date)

    return [
        episode for episode in episodes
        if archive_to_date(episode.get("published")) >= min_date
    ]


def sort_episodes_newest_first(episodes: Iterable[dict]) -> list[dict]:
    return sorted(
        episodes,
        key=lambda item: archive_to_date(item.get("published")),
        reverse=True,
    )


def sort_rss_items_newest_first(rss: bytes) -> bytes:
    parser = etree.XMLParser(strip_cdata=False)
    root = etree.fromstring(rss, parser)
    channel = root.find("channel")

    if channel is None:
        return rss

    items = channel.findall("item")

    if not items:
        return rss

    def item_date(item):
        try:
            return parsedate_to_datetime(item.findtext("pubDate") or "")
        except (TypeError, ValueError):
            return datetime.min.replace(tzinfo=timezone.utc)

    for item in items:
        channel.remove(item)

    sorted_items = sorted(items, key=item_date, reverse=True)

    for index, item in enumerate(sorted_items):
        item.tail = "\n  " if index == len(sorted_items) - 1 else "\n    "
        channel.append(item)

    return etree.tostring(
        root,
        encoding="UTF-8",
        xml_declaration=True,
        pretty_print=True,
    )


def episode_description_for_feed(episode: dict) -> str:
    description = clean_text(episode.get("description", ""))

    if not description or description == ".":
        return episode.get("title", "")

    return description


def add_stylesheet_instruction(rss: bytes, style_file: str) -> bytes:
    stylesheet = f'<?xml-stylesheet type="text/xsl" href="{style_file}"?>\n'.encode(
        "utf-8"
    )

    if b"<?xml-stylesheet" in rss[:300]:
        return rss

    if rss.startswith(b"<?xml"):
        first_line_end = rss.find(b"\n") + 1
        return rss[:first_line_end] + stylesheet + rss[first_line_end:]

    return stylesheet + rss


def build_rss(config: RadioFranceFeedConfig, episodes: list[dict]) -> bytes:
    episodes = sort_episodes_newest_first(validate_archive(episodes))
    feed_url = public_file_url(config.output_file)

    fg = FeedGenerator()
    fg.load_extension("podcast")

    fg.id(feed_url)
    fg.title(config.feed_title)
    fg.subtitle(config.feed_subtitle)
    fg.description(config.feed_description)
    fg.language("fr")
    fg.link(href=feed_url, rel="alternate")
    fg.link(href=feed_url, rel="self")
    fg.author({"name": config.feed_author_name})
    fg.logo(config.feed_image)
    fg.updated(datetime.now(timezone.utc))

    fg.podcast.itunes_author(config.itunes_author)
    fg.podcast.itunes_summary(config.feed_description)
    fg.podcast.itunes_subtitle(config.feed_subtitle)
    fg.podcast.itunes_owner(
        name="Personal RSS Bridge",
        email="no-reply@example.com",
    )
    fg.podcast.itunes_explicit("no")
    fg.podcast.itunes_category(config.itunes_category)

    if is_itunes_safe_image(config.feed_image):
        fg.podcast.itunes_image(config.feed_image)

    for episode in episodes:
        published_dt = archive_to_date(episode.get("published"))
        description = episode_description_for_feed(episode)

        fe = fg.add_entry()

        fe.id(episode["url"])
        fe.title(episode["title"])
        fe.link(href=episode["url"])
        fe.guid(episode["url"], permalink=True)
        fe.published(published_dt)
        fe.updated(published_dt)

        rich_description = f"""
        <p>{html.escape(description)}</p>
        <p><strong>Source:</strong> <a href="{episode["url"]}">{config.source_label}</a></p>
        """

        if episode.get("image"):
            rich_description += f"""
            <p>
              <img src="{episode["image"]}" alt="{html.escape(episode["title"])}" />
            </p>
            """

        fe.description(description)
        fe.content(rich_description, type="CDATA")
        fe.enclosure(
            episode["audio_url"],
            str(episode.get("audio_length") or 0),
            episode.get("audio_type") or "audio/mp4",
        )

        fe.podcast.itunes_author(config.itunes_author)
        fe.podcast.itunes_summary(description)
        fe.podcast.itunes_subtitle(description[:255])

        if episode.get("duration_itunes"):
            fe.podcast.itunes_duration(episode["duration_itunes"])

        if is_itunes_safe_image(episode.get("image")):
            fe.podcast.itunes_image(episode["image"])

    rss = sort_rss_items_newest_first(fg.rss_str(pretty=True))
    return add_stylesheet_instruction(rss, config.style_file)


def write_rss(config: RadioFranceFeedConfig, episodes: list[dict]) -> None:
    atomic_write_bytes(config.output_file, build_rss(config, episodes))


def build_feed(config: RadioFranceFeedConfig = FRANCE_CULTURE_CONFIG) -> None:
    session = create_session()

    print("Loading archive...")
    archive = load_archive(config)
    known_urls = {episode["url"] for episode in archive}
    print(f"Archive contains {len(archive)} episodes")

    print("Fetching website episode links...")
    links = get_episode_links(session, config)
    print(f"Found {len(links)} episode links on website")

    new_episodes = []

    for link in links:
        if link in known_urls:
            print(f"Already archived: {link}")
            continue

        print(f"Checking: {link}")
        data = extract_episode_data(session, link)

        if not data:
            raise RuntimeError(f"No valid episode data found at {link}")

        if config.min_published_date:
            published_dt = archive_to_date(data.get("published"))
            min_dt = parse_iso_date(config.min_published_date)

            if published_dt < min_dt:
                print(f"  -> skipped, before {config.min_published_date}")
                if config.stop_when_before_min_published_date:
                    print("  -> stopping, remaining links are older")
                    break
                continue

        new_episodes.append(data)
        print(f"  -> added: {data['title']}")

    hydrated_archive = hydrate_audio_lengths(session, archive)
    all_episodes = filter_episodes_by_min_date(
        config,
        merge_episodes(hydrated_archive, new_episodes),
    )

    if not all_episodes:
        raise RuntimeError(f"No episodes available for {config.feed_title}")

    save_archive(config, all_episodes)
    write_rss(config, all_episodes)

    print()
    print(f"New episodes added: {len(new_episodes)}")
    print(f"Total archived episodes: {len(all_episodes)}")
    print(f"Created {config.output_file}")
    print(f"Updated {config.archive_file}")


if __name__ == "__main__":
    build_feed()

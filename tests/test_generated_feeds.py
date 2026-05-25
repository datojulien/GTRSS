import json
import os
import xml.etree.ElementTree as ET
from email.utils import parsedate_to_datetime
from pathlib import Path

import pytest
import requests

from build_feed import DEFAULT_PUBLIC_BASE_URL
from keep_integrale import is_best_episode, is_integrale_title, is_remaining_item, safe_text


ROOT = Path(__file__).resolve().parents[1]
FEED_FILES = [
    "feed.xml",
    "francois-rollin-feed.xml",
    "roselyne-bachelot-feed.xml",
    "only_integrale_feed.xml",
    "only_best_feed.xml",
    "only_remaining_feed.xml",
]
XSL_FILES = [
    "feed-style.xsl",
    "francois-rollin-style.xsl",
    "roselyne-bachelot-style.xsl",
    "grosses-tetes-style.xsl",
]
NS = {
    "atom": "http://www.w3.org/2005/Atom",
}


def parse_xml(path):
    return ET.parse(ROOT / path).getroot()


def channel(path):
    root = parse_xml(path)
    channel_node = root.find("channel")
    assert channel_node is not None
    return channel_node


def test_xml_and_xsl_parse():
    for path in FEED_FILES + XSL_FILES:
        ET.parse(ROOT / path)


def test_feed_items_have_required_fields_and_unique_guids():
    for path in FEED_FILES:
        items = channel(path).findall("item")
        assert items, f"{path} has no items"
        guids = []
        dates = []

        for item in items:
            assert (item.findtext("title") or "").strip()
            assert (item.findtext("guid") or "").strip()
            assert (item.findtext("pubDate") or "").strip()
            enclosure = item.find("enclosure")
            assert enclosure is not None
            assert enclosure.get("url")
            assert enclosure.get("type")
            assert enclosure.get("length") is not None

            guids.append(item.findtext("guid"))
            dates.append(parsedate_to_datetime(item.findtext("pubDate")))

        assert len(guids) == len(set(guids)), f"{path} has duplicate GUIDs"
        assert all(dates[i] >= dates[i + 1] for i in range(len(dates) - 1))


def test_radiofrance_archives_match_generated_feeds():
    pairs = [
        ("episodes.json", "feed.xml"),
        ("francois-rollin-episodes.json", "francois-rollin-feed.xml"),
        ("roselyne-bachelot-episodes.json", "roselyne-bachelot-feed.xml"),
    ]

    for archive_path, feed_path in pairs:
        archive = json.loads((ROOT / archive_path).read_text(encoding="utf-8"))
        items = channel(feed_path).findall("item")
        archive_urls = {episode["url"] for episode in archive}
        feed_guids = {item.findtext("guid") for item in items}
        assert archive_urls == feed_guids
        assert all("audio_length" in episode for episode in archive)


def test_grosses_tetes_split_feeds_are_non_overlapping_and_classified():
    seen_guids = set()

    for item in channel("only_integrale_feed.xml").findall("item"):
        title = safe_text(item, "title")
        assert is_integrale_title(title)
        assert not is_best_episode(item)
        seen_guids.add(item.findtext("guid"))

    for item in channel("only_best_feed.xml").findall("item"):
        assert is_best_episode(item)
        guid = item.findtext("guid")
        assert guid not in seen_guids
        seen_guids.add(guid)

    for item in channel("only_remaining_feed.xml").findall("item"):
        assert is_remaining_item(item)
        guid = item.findtext("guid")
        assert guid not in seen_guids
        seen_guids.add(guid)


def test_feed_links_use_canonical_github_pages_base():
    for path in FEED_FILES:
        feed_url = DEFAULT_PUBLIC_BASE_URL + path
        feed_channel = channel(path)
        assert feed_channel.findtext("link") == feed_url

        atom_links = feed_channel.findall("atom:link", NS)
        self_links = [link for link in atom_links if link.get("rel") == "self"]
        assert self_links, f"{path} has no atom self link"
        assert self_links[0].get("href") == feed_url


@pytest.mark.skipif(
    os.environ.get("GTRSS_RUN_NETWORK_TESTS") != "1",
    reason="network smoke tests are opt-in",
)
def test_public_feed_urls_are_reachable():
    for path in FEED_FILES:
        response = requests.get(DEFAULT_PUBLIC_BASE_URL + path, timeout=20)
        assert response.status_code < 500

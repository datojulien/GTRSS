#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Build the RTL / Les Grosses Têtes split RSS feeds."""

from __future__ import annotations

import io
import os
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from email.utils import formatdate
from typing import Callable

from build_feed import atomic_write_bytes, create_session, public_file_url


ITUNES_NS = "http://www.itunes.com/dtds/podcast-1.0.dtd"
GPOD_NS = "http://www.google.com/schemas/play-podcasts/1.0"
ATOM_NS = "http://www.w3.org/2005/Atom"
ET.register_namespace("itunes", ITUNES_NS)
ET.register_namespace("atom", ATOM_NS)


@dataclass(frozen=True)
class GrossesTetesConfig:
    feed_url: str = "https://feeds.audiomeans.fr/feed/d7c6111b-04c1-46bc-b74c-d941a90d37fb.xml"
    output_integrale: str = "only_integrale_feed.xml"
    output_best: str = "only_best_feed.xml"
    output_remaining: str = "only_remaining_feed.xml"
    style_file: str = "grosses-tetes-style.xsl"
    min_best_duration_min: int = 20
    integrale_image_file: str = "Integrales.jpg"
    best_image_file: str = "Extras.jpg"
    autres_image_file: str = "Autres.jpg"
    integrale_summary: str = (
        "Tous les épisodes de L'Intégrale de 'Les Grosses Têtes', regroupant "
        "la diffusion complète sans coupures ni extras."
    )
    best_summary: str = (
        "Le Best Of : une sélection des moments les plus drôles et "
        "emblématiques de la saison, incluant bonus et moments cultes "
        "(≥ 20 min)."
    )
    remaining_summary: str = (
        "Les autres épisodes : tout le reste du flux officiel, hors Intégrale "
        "et Best Of, pour ne rien manquer."
    )

    @property
    def min_best_duration_sec(self) -> int:
        return self.min_best_duration_min * 60


CONFIG = GrossesTetesConfig()

INTEGRALE_PREFIXES = ("L'INTÉGRALE", "DÉBRIEF")
BEST_PREFIXES = (
    "MEILLEUR DE LA SAISON",
    "BEST OF",
    "MOMENT CULTE",
    "L'INTÉGRALE - Le Best of",
)


def safe_text(elem: ET.Element, tag: str, ns: str | None = None) -> str:
    if ns:
        tag = f"{{{ns}}}{tag}"
    node = elem.find(tag)
    return (node.text or "").strip() if node is not None and node.text else ""


def parse_itunes_duration_to_seconds(text: str | None) -> int:
    """Parse SS, MM:SS, or HH:MM:SS to seconds. Invalid values return -1."""
    if not text:
        return -1
    value = text.strip()
    try:
        if value.isdigit():
            return int(value)
        parts = value.split(":")
        if len(parts) == 2:
            minutes, seconds = parts
            return int(minutes) * 60 + int(seconds)
        if len(parts) == 3:
            hours, minutes, seconds = parts
            return int(hours) * 3600 + int(minutes) * 60 + int(seconds)
    except ValueError:
        pass
    return -1


def get_item_duration_seconds(item: ET.Element) -> int:
    return parse_itunes_duration_to_seconds(safe_text(item, "duration", ITUNES_NS))


def is_best_title(title: str) -> bool:
    return title.startswith(BEST_PREFIXES)


def is_integrale_title(title: str) -> bool:
    return title.startswith(INTEGRALE_PREFIXES) and not is_best_title(title)


def is_best_episode(item: ET.Element, config: GrossesTetesConfig = CONFIG) -> bool:
    title = safe_text(item, "title")
    return is_best_title(title) and get_item_duration_seconds(item) >= config.min_best_duration_sec


def is_remaining_item(item: ET.Element, config: GrossesTetesConfig = CONFIG) -> bool:
    title = safe_text(item, "title")
    return not is_integrale_title(title) and not is_best_episode(item, config)


def source_channel(root: ET.Element) -> ET.Element:
    channel = root.find("channel")
    if channel is None:
        raise ValueError("Source RSS has no channel")
    return channel


def new_root_with_filtered_items(
    raw: bytes,
    predicate_item: Callable[[ET.Element], bool],
) -> tuple[ET.Element, ET.Element]:
    root = ET.fromstring(raw)
    channel = source_channel(root)
    for item in list(channel.findall("item")):
        if not predicate_item(item):
            channel.remove(item)
    return root, channel


def remove_children(channel: ET.Element, *tags: str) -> None:
    for tag in tags:
        for old in channel.findall(tag):
            channel.remove(old)


def apply_cover(channel: ET.Element, image_url: str, title: str, link: str) -> None:
    remove_children(
        channel,
        "image",
        f"{{{GPOD_NS}}}image",
        f"{{{ITUNES_NS}}}image",
    )

    itunes_image = ET.Element(f"{{{ITUNES_NS}}}image")
    itunes_image.set("href", image_url)

    image = ET.Element("image")
    ET.SubElement(image, "url").text = image_url
    ET.SubElement(image, "title").text = title
    ET.SubElement(image, "link").text = link

    title_elem = channel.find("title")
    idx = list(channel).index(title_elem) if title_elem is not None else 0
    channel.insert(idx + 1, image)
    channel.insert(idx + 1, itunes_image)


def ensure_atom_self_link(channel: ET.Element, feed_url: str) -> None:
    for old in list(channel.findall(f"{{{ATOM_NS}}}link")):
        if old.get("rel") == "self":
            channel.remove(old)

    atom_link = ET.Element(f"{{{ATOM_NS}}}link")
    atom_link.set("href", feed_url)
    atom_link.set("rel", "self")
    atom_link.set("type", "application/rss+xml")

    description = channel.find("description")
    idx = list(channel).index(description) if description is not None else 0
    channel.insert(idx + 1, atom_link)


def finalize_channel(
    channel: ET.Element,
    src_title: str,
    cover_url: str,
    output_file: str,
    title_suffix: str,
    summary_text: str,
    now: str,
) -> None:
    feed_url = public_file_url(output_file)
    title_text = f"{src_title} ({title_suffix})"

    title_node = channel.find("title")
    if title_node is None:
        title_node = ET.SubElement(channel, "title")
    title_node.text = title_text

    link_node = channel.find("link")
    if link_node is None:
        link_node = ET.SubElement(channel, "link")
    link_node.text = feed_url

    desc = channel.find("description")
    if desc is None:
        desc = ET.SubElement(channel, "description")
    desc.text = summary_text

    summary_tag = f"{{{ITUNES_NS}}}summary"
    node = channel.find(summary_tag)
    if node is None:
        node = ET.SubElement(channel, summary_tag)
    node.text = summary_text

    apply_cover(channel, cover_url, title_text, feed_url)
    ensure_atom_self_link(channel, feed_url)

    for tag in ("pubDate", "lastBuildDate"):
        node = channel.find(tag)
        if node is None:
            ET.SubElement(channel, tag).text = now
        else:
            node.text = now


def add_stylesheet_instruction(xml_bytes: bytes, style_file: str) -> bytes:
    stylesheet = f'<?xml-stylesheet type="text/xsl" href="{style_file}"?>\n'.encode(
        "utf-8"
    )

    if b"<?xml-stylesheet" in xml_bytes[:300]:
        return xml_bytes

    if xml_bytes.startswith(b"<?xml"):
        first_line_end = xml_bytes.find(b"\n")
        if first_line_end != -1:
            return xml_bytes[: first_line_end + 1] + stylesheet + xml_bytes[first_line_end + 1 :]

        declaration_end = xml_bytes.find(b"?>")
        if declaration_end != -1:
            insert_at = declaration_end + 2
            return xml_bytes[:insert_at] + b"\n" + stylesheet + xml_bytes[insert_at:]

    return stylesheet + xml_bytes


def clean_text_value(value: str) -> str:
    lines = value.replace("\r\n", "\n").replace("\r", "\n").split("\n")
    return "\n".join(line.strip() for line in lines).strip()


def strip_text_edges(root: ET.Element) -> None:
    for elem in root.iter():
        if elem.text:
            elem.text = clean_text_value(elem.text)
        if elem.tail:
            elem.tail = elem.tail.rstrip()


def item_count(channel: ET.Element) -> int:
    return len(channel.findall("item"))


def render_xml(root: ET.Element, style_file: str) -> bytes:
    strip_text_edges(root)
    ET.indent(root, space="  ")
    buffer = io.BytesIO()
    ET.ElementTree(root).write(buffer, encoding="utf-8", xml_declaration=True)
    return add_stylesheet_instruction(buffer.getvalue(), style_file)


def write_xml(root: ET.Element, out_path: str, style_file: str) -> None:
    atomic_write_bytes(out_path, render_xml(root, style_file))


def fetch_source_feed(config: GrossesTetesConfig = CONFIG) -> bytes:
    session = create_session()
    response = session.get(config.feed_url, timeout=60)
    response.raise_for_status()
    return response.content


def build_split_feeds(
    raw: bytes,
    config: GrossesTetesConfig = CONFIG,
    now: str | None = None,
) -> dict[str, ET.Element]:
    now = now or formatdate(usegmt=True)
    src_root = ET.fromstring(raw)
    src_title = safe_text(source_channel(src_root), "title")
    if not src_title:
        raise ValueError("Source RSS channel has no title")

    root_i, ch_i = new_root_with_filtered_items(
        raw,
        lambda item: is_integrale_title(safe_text(item, "title")),
    )
    finalize_channel(
        ch_i,
        src_title,
        public_file_url(config.integrale_image_file),
        config.output_integrale,
        "L’intégrale",
        config.integrale_summary,
        now,
    )

    root_b, ch_b = new_root_with_filtered_items(
        raw,
        lambda item: is_best_episode(item, config),
    )
    finalize_channel(
        ch_b,
        src_title,
        public_file_url(config.best_image_file),
        config.output_best,
        "Extras",
        config.best_summary,
        now,
    )

    root_r, ch_r = new_root_with_filtered_items(
        raw,
        lambda item: is_remaining_item(item, config),
    )
    finalize_channel(
        ch_r,
        src_title,
        public_file_url(config.autres_image_file),
        config.output_remaining,
        "Other Episodes",
        config.remaining_summary,
        now,
    )

    outputs = {
        config.output_integrale: root_i,
        config.output_best: root_b,
        config.output_remaining: root_r,
    }

    empty = [
        path
        for path, root in outputs.items()
        if item_count(source_channel(root)) == 0
    ]
    if empty:
        raise RuntimeError(f"Refusing to write empty split feed(s): {', '.join(empty)}")

    return outputs


def write_split_feeds(
    roots: dict[str, ET.Element],
    config: GrossesTetesConfig = CONFIG,
) -> None:
    for output_file, root in roots.items():
        write_xml(root, output_file, config.style_file)


def main(config: GrossesTetesConfig = CONFIG) -> None:
    if os.environ.get("GTRSS_AUTO_COMMIT") == "1":
        print(
            "GTRSS_AUTO_COMMIT is deprecated; generation no longer runs git "
            "commands. GitHub Actions handles commits."
        )

    raw = fetch_source_feed(config)
    roots = build_split_feeds(raw, config)
    write_split_feeds(roots, config)

    print(f"rebuilt {config.output_integrale}")
    print(f"rebuilt {config.output_best} (only items ≥ {config.min_best_duration_min} min)")
    print(f"rebuilt {config.output_remaining}")


if __name__ == "__main__":
    main()

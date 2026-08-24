import xml.etree.ElementTree as ET

import pytest

from keep_integrale import (
    GrossesTetesConfig,
    ITUNES_NS,
    build_split_feeds,
    clean_text_value,
    get_item_duration_seconds,
    is_best_episode,
    is_best_title,
    is_integrale_title,
    item_count,
    is_remaining_item,
    parse_itunes_duration_to_seconds,
    source_channel,
    write_split_feeds,
)


def make_item(title, duration="00:30:00"):
    item = ET.Element("item")
    ET.SubElement(item, "title").text = title
    ET.SubElement(item, f"{{{ITUNES_NS}}}duration").text = duration
    return item


def make_feed(*items):
    root = ET.Element("rss", version="2.0")
    channel = ET.SubElement(root, "channel")
    ET.SubElement(channel, "title").text = "Les Grosses Têtes"
    for item in items:
        channel.append(item)
    return ET.tostring(root, encoding="utf-8", xml_declaration=True)


@pytest.mark.parametrize(
    ("text", "seconds"),
    [
        ("90", 90),
        ("04:20", 260),
        ("01:40:30", 6030),
        ("bad", -1),
        ("", -1),
    ],
)
def test_parse_itunes_duration_to_seconds(text, seconds):
    assert parse_itunes_duration_to_seconds(text) == seconds


def test_grosses_tetes_classification_rules():
    integrale = make_item("L'INTÉGRALE - Émission du mercredi 13 mai 2026")
    best = make_item("L'INTÉGRALE - Le Best of du dimanche 17 mai 2026")
    short_best = make_item("BEST OF - Trop court", "00:10:00")
    remaining = make_item("LE MEILLEUR DE RUQUIER - Une histoire drôle")

    assert is_integrale_title(integrale.findtext("title"))
    assert is_best_title(best.findtext("title"))
    assert is_best_episode(best)
    assert not is_best_episode(short_best)
    assert is_remaining_item(short_best)
    assert is_remaining_item(remaining)
    assert get_item_duration_seconds(best) == 1800


@pytest.mark.parametrize(
    "title",
    [
        "L'INTÉGRALE - Le Best of du dimanche 17 mai 2026",
        "L'INTÉGRALE - Le Best Of du dimanche 17 mai 2026",
        "L'INTÉGRALE - LE BEST OF du dimanche 17 mai 2026",
    ],
)
def test_best_title_matching_is_case_insensitive(title):
    item = make_item(title)

    assert is_best_title(title)
    assert is_best_episode(item)
    assert not is_integrale_title(title)


def test_clean_text_value_normalizes_edge_whitespace():
    value = " first line \r\n second line \n third line "
    assert clean_text_value(value) == "first line\nsecond line\nthird line"


def test_build_split_feeds_allows_empty_categories():
    raw = make_feed(
        make_item("BEST OF - Une sélection", "00:30:00"),
        make_item("Une autre émission", "00:05:00"),
    )

    roots = build_split_feeds(raw)

    assert item_count(source_channel(roots["only_integrale_feed.xml"])) == 0
    assert item_count(source_channel(roots["only_best_feed.xml"])) == 1
    assert item_count(source_channel(roots["only_remaining_feed.xml"])) == 1


def test_write_split_feeds_preserves_existing_file_when_category_is_empty(tmp_path):
    config = GrossesTetesConfig(
        output_integrale=str(tmp_path / "only_integrale_feed.xml"),
        output_best=str(tmp_path / "only_best_feed.xml"),
        output_remaining=str(tmp_path / "only_remaining_feed.xml"),
    )
    raw = make_feed(
        make_item("BEST OF - Une sélection", "00:30:00"),
        make_item("Une autre émission", "00:05:00"),
    )
    roots = build_split_feeds(raw, config)

    existing = tmp_path / "only_integrale_feed.xml"
    existing.write_text("keep me", encoding="utf-8")

    results = write_split_feeds(roots, config)

    assert existing.read_text(encoding="utf-8") == "keep me"
    assert results[str(existing)] == "preserved"
    assert results[str(tmp_path / "only_best_feed.xml")] == "rebuilt"
    assert results[str(tmp_path / "only_remaining_feed.xml")] == "rebuilt"
    ET.parse(tmp_path / "only_best_feed.xml")
    ET.parse(tmp_path / "only_remaining_feed.xml")

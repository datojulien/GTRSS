import xml.etree.ElementTree as ET

import pytest

from keep_integrale import (
    ITUNES_NS,
    clean_text_value,
    get_item_duration_seconds,
    is_best_episode,
    is_best_title,
    is_integrale_title,
    is_remaining_item,
    parse_itunes_duration_to_seconds,
)


def make_item(title, duration="00:30:00"):
    item = ET.Element("item")
    ET.SubElement(item, "title").text = title
    ET.SubElement(item, f"{{{ITUNES_NS}}}duration").text = duration
    return item


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


def test_clean_text_value_normalizes_edge_whitespace():
    value = " first line \r\n second line \n third line "
    assert clean_text_value(value) == "first line\nsecond line\nthird line"

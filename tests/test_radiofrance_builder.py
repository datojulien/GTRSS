import pytest

from build_feed import (
    FRANCE_CULTURE_CONFIG,
    RadioFranceFeedConfig,
    extract_episode_links_from_soup,
    parse_duration_to_seconds,
    parse_iso_date,
    public_file_url,
    seconds_to_itunes_duration,
    validate_archive,
)
from build_bachelot_feed import BACHELOT_CONFIG
from build_rollin_feed import ROLLIN_CONFIG
from bs4 import BeautifulSoup


def test_duration_helpers():
    assert parse_duration_to_seconds("PT58M56S") == 3536
    assert parse_duration_to_seconds("PT1H02M03S") == 3723
    assert parse_duration_to_seconds("not-a-duration") is None
    assert seconds_to_itunes_duration(260) == "4:20"
    assert seconds_to_itunes_duration(3723) == "1:02:03"
    assert seconds_to_itunes_duration(None) is None


def test_parse_iso_date_is_strict():
    assert parse_iso_date("2026-05-18T10:05:02+00:00").tzinfo is not None
    with pytest.raises(ValueError):
        parse_iso_date(None)
    with pytest.raises(ValueError):
        parse_iso_date("not-a-date")


def test_archive_validation_requires_unique_urls_and_valid_audio():
    episode = {
        "title": "A title",
        "description": "",
        "audio_url": "https://example.com/audio.mp3",
        "audio_type": "audio/mpeg",
        "duration_seconds": 60,
        "duration_itunes": "1:00",
        "published": "2026-05-18T10:05:02+00:00",
        "image": None,
        "url": "https://example.com/episode",
        "audio_length": 1234,
    }
    assert validate_archive([episode]) == [episode]

    duplicate = dict(episode)
    with pytest.raises(ValueError, match="Duplicate archive URL"):
        validate_archive([episode, duplicate])

    invalid = dict(episode, audio_url="not-a-url")
    with pytest.raises(ValueError, match="invalid audio_url"):
        validate_archive([invalid])


def test_feed_configs_are_explicit():
    assert isinstance(FRANCE_CULTURE_CONFIG, RadioFranceFeedConfig)
    assert FRANCE_CULTURE_CONFIG.output_file == "feed.xml"
    assert ROLLIN_CONFIG.output_file == "francois-rollin-feed.xml"
    assert ROLLIN_CONFIG.follow_pagination is True
    assert ROLLIN_CONFIG.min_published_date == "2025-08-01T00:00:00+00:00"
    assert BACHELOT_CONFIG.output_file == "roselyne-bachelot-feed.xml"
    assert BACHELOT_CONFIG.follow_pagination is True
    assert BACHELOT_CONFIG.itunes_author == "France Musique"


def test_radiofrance_link_extraction_accepts_legacy_episode_slugs():
    soup = BeautifulSoup(
        """
        <a href="/francemusique/podcasts/la-chronique-de-roselyne-bachelot">show</a>
        <a href="/francemusique/podcasts/la-chronique-de-roselyne-bachelot?p=2">page 2</a>
        <a href="/francemusique/podcasts/la-chronique-de-roselyne-bachelot/champagne-ardent-3491601">new slug</a>
        <a href="/francemusique/podcasts/la-chronique-de-roselyne-bachelot-cheikha-remitti-reine-du-rai-1064980">legacy slug</a>
        """,
        "html.parser",
    )

    assert extract_episode_links_from_soup(soup, BACHELOT_CONFIG) == [
        (
            "https://www.radiofrance.fr/francemusique/podcasts/"
            "la-chronique-de-roselyne-bachelot/champagne-ardent-3491601"
        ),
        (
            "https://www.radiofrance.fr/francemusique/podcasts/"
            "la-chronique-de-roselyne-bachelot-cheikha-remitti-reine-du-rai-1064980"
        ),
    ]


def test_public_file_url_defaults_to_github_pages(monkeypatch):
    monkeypatch.delenv("GTRSS_PUBLIC_BASE_URL", raising=False)
    assert public_file_url("feed.xml") == "https://datojulien.github.io/GTRSS/feed.xml"

    monkeypatch.setenv("GTRSS_PUBLIC_BASE_URL", "https://example.com/custom")
    assert public_file_url("feed.xml") == "https://example.com/custom/feed.xml"

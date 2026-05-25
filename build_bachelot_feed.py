#!/usr/bin/env python3
"""Build the France Musique / Roselyne Bachelot personal RSS feed."""

from build_feed import RadioFranceFeedConfig, build_feed


BACHELOT_CONFIG = RadioFranceFeedConfig(
    show_url=(
        "https://www.radiofrance.fr/francemusique/podcasts/"
        "la-chronique-de-roselyne-bachelot"
    ),
    show_path="/francemusique/podcasts/la-chronique-de-roselyne-bachelot",
    output_file="roselyne-bachelot-feed.xml",
    style_file="roselyne-bachelot-style.xsl",
    archive_file="roselyne-bachelot-episodes.json",
    max_links_to_check=100,
    follow_pagination=True,
    max_pages_to_check=5,
    min_published_date="2025-08-01T00:00:00+00:00",
    stop_when_before_min_published_date=True,
    feed_title="La chronique de Roselyne Bachelot — Flux frais",
    feed_subtitle="Flux personnel généré depuis le site Radio France",
    feed_description=(
        "Un flux RSS personnel qui récupère les épisodes depuis le site web de "
        "France Musique lorsque le flux officiel n’est pas encore à jour."
    ),
    feed_image=(
        "https://www.radiofrance.fr/pikapi/images/"
        "951b7b95-d363-43f8-9fda-e162b17396fc/1200x680"
    ),
    feed_author_name="Radio France / France Musique",
    itunes_author="France Musique",
    itunes_category="Music",
    source_label="France Musique",
)


if __name__ == "__main__":
    build_feed(BACHELOT_CONFIG)

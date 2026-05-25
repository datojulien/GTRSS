#!/usr/bin/env python3
"""Build the France Inter / Le billet de François Rollin personal RSS feed."""

from build_feed import RadioFranceFeedConfig, build_feed


ROLLIN_CONFIG = RadioFranceFeedConfig(
    show_url=(
        "https://www.radiofrance.fr/franceinter/podcasts/"
        "le-billet-de-francois-rollin"
    ),
    show_path="/franceinter/podcasts/le-billet-de-francois-rollin/",
    output_file="francois-rollin-feed.xml",
    style_file="francois-rollin-style.xsl",
    archive_file="francois-rollin-episodes.json",
    max_links_to_check=120,
    follow_pagination=True,
    max_pages_to_check=8,
    min_published_date="2025-08-01T00:00:00+00:00",
    stop_when_before_min_published_date=True,
    feed_title="Le billet de François Rollin — Flux frais",
    feed_subtitle="Flux personnel généré depuis le site Radio France",
    feed_description=(
        "Un flux RSS personnel qui récupère les épisodes depuis le site web de "
        "France Inter lorsque le flux officiel n’est pas encore à jour."
    ),
    feed_image=(
        "https://www.radiofrance.fr/pikapi/images/"
        "b66e4080-2221-4df9-9205-35e13f450bdd/300x300"
    ),
    feed_author_name="Radio France / France Inter",
    itunes_author="France Inter",
    itunes_category="Comedy",
    source_label="France Inter",
)


if __name__ == "__main__":
    build_feed(ROLLIN_CONFIG)

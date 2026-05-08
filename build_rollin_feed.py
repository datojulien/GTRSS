#!/usr/bin/env python3
"""Build the France Inter / Le billet de François Rollin personal RSS feed."""

import build_feed as radiofrance_feed


radiofrance_feed.SHOW_URL = (
    "https://www.radiofrance.fr/franceinter/podcasts/"
    "le-billet-de-francois-rollin"
)
radiofrance_feed.SHOW_PATH = (
    "/franceinter/podcasts/le-billet-de-francois-rollin/"
)
radiofrance_feed.OUTPUT_FILE = "francois-rollin-feed.xml"
radiofrance_feed.STYLE_FILE = "francois-rollin-style.xsl"
radiofrance_feed.ARCHIVE_FILE = "francois-rollin-episodes.json"

radiofrance_feed.FEED_TITLE = "Le billet de François Rollin — Flux frais"
radiofrance_feed.FEED_SUBTITLE = (
    "Flux personnel généré depuis le site Radio France"
)
radiofrance_feed.FEED_DESCRIPTION = (
    "Un flux RSS personnel qui récupère les épisodes depuis le site web de "
    "France Inter lorsque le flux officiel n’est pas encore à jour."
)
radiofrance_feed.FEED_IMAGE = (
    "https://www.radiofrance.fr/pikapi/images/"
    "b66e4080-2221-4df9-9205-35e13f450bdd/1200x680"
)
radiofrance_feed.FEED_AUTHOR_NAME = "Radio France / France Inter"
radiofrance_feed.ITUNES_AUTHOR = "France Inter"
radiofrance_feed.ITUNES_CATEGORY = "Comedy"
radiofrance_feed.SOURCE_LABEL = "France Inter"


if __name__ == "__main__":
    radiofrance_feed.build_feed()

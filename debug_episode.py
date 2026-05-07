import requests
import re

EPISODE_URL = "https://www.radiofrance.fr/franceculture/podcasts/le-cours-de-l-histoire/sevigne-et-les-nouvelles-une-observatrice-des-intrigues-de-la-cour-2773570"

headers = {
    "User-Agent": "Mozilla/5.0"
}

html = requests.get(EPISODE_URL, headers=headers, timeout=20).text

print("Page length:", len(html))

keywords = [
    "mp3",
    "audio",
    "media",
    "manifest",
    "podcast",
    "episode",
    "player",
    "sounds",
    "url"
]

for keyword in keywords:
    count = html.lower().count(keyword)
    print(f"{keyword}: {count}")

print("\n--- Lines containing audio/mp3/media ---\n")

for line in html.splitlines():
    lower = line.lower()
    if "mp3" in lower or "audio" in lower or "media" in lower or "player" in lower:
        print(line[:1000])
        print()

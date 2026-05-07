import re
import requests

EPISODE_URL = "https://www.radiofrance.fr/franceculture/podcasts/le-cours-de-l-histoire/sevigne-et-les-nouvelles-une-observatrice-des-intrigues-de-la-cour-2773570"

headers = {
    "User-Agent": "Mozilla/5.0"
}

html = requests.get(EPISODE_URL, headers=headers, timeout=20).text

patterns = [
    r'https://[^"\']+?\.mp3[^"\']*',
    r'https:\\/\\/[^"\']+?\.mp3[^"\']*'
]

found = None

for pattern in patterns:
    match = re.search(pattern, html)
    if match:
        found = match.group(0).replace("\\/", "/")
        break

if found:
    print("MP3 found:")
    print(found)
else:
    print("No MP3 found")

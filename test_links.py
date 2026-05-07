import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

SHOW_URL = "https://www.radiofrance.fr/franceculture/podcasts/le-cours-de-l-histoire"
BASE_URL = "https://www.radiofrance.fr"

headers = {
    "User-Agent": "Mozilla/5.0"
}

html = requests.get(SHOW_URL, headers=headers, timeout=20).text
soup = BeautifulSoup(html, "html.parser")

links = []

for a in soup.find_all("a", href=True):
    href = a["href"]

    if "/franceculture/podcasts/le-cours-de-l-histoire/" in href:
        full_url = urljoin(BASE_URL, href)

        if full_url not in links:
            links.append(full_url)

for link in links[:20]:
    print(link)

print(f"\nFound {len(links)} episode links")

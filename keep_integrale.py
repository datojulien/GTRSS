#!/usr/bin/env python3
import xml.etree.ElementTree as ET
import requests
from email.utils import formatdate
import subprocess
import os

# ─── CONFIG ───────────────────────────────────────────────────
feed_url    = "https://feeds.audiomeans.fr/feed/d7c6111b-04c1-46bc-b74c-d941a90d37fb.xml"
output_file = "only_integrale_feed.xml"
include_pref = "L'INTÉGRALE"
repo_path   = "."
# ───────────────────────────────────────────────────────────────

# ensure <itunes:duration> etc keep their prefix
ET.register_namespace('itunes','http://www.itunes.com/dtds/podcast-1.0.dtd')

# 1) FETCH source feed
resp = requests.get(feed_url)
resp.raise_for_status()
src_root    = ET.fromstring(resp.content)
src_channel = src_root.find("channel")

# 2) LOAD existing feed (if any) and collect GUIDs
existing_guids = set()
if os.path.exists(output_file):
    existing_tree    = ET.parse(output_file)
    existing_root    = existing_tree.getroot()
    existing_channel = existing_root.find("channel")
    for item in existing_channel.findall("item"):
        existing_guids.add(item.find("guid").text.strip())
else:
    existing_root    = None
    existing_channel = None

# 3) PICK UP new integrale items
new_items = []
for item in src_channel.findall("item"):
    title = item.find("title").text.strip()
    guid  = item.find("guid").text.strip()
    if title.startswith(include_pref) and guid not in existing_guids:
        new_items.append(item)

# if no new items and feed exists, exit
if new_items and existing_channel is None:
    # no existing, but there *are* new items → will build from scratch below
    pass
elif not new_items and existing_channel is not None:
    print("No new items, exiting")
    exit(0)

# 4) BUILD or MERGE the feed
if existing_channel is None:
    # first run: take source channel, strip non-integrale, then update title & timestamps
    root    = src_root
    channel = src_channel
    # remove non-integrale
    for item in list(channel.findall("item")):
        if not item.find("title").text.strip().startswith(include_pref):
            channel.remove(item)
else:
    # merge into existing
    root    = existing_root
    channel = existing_channel
    # prepend new items so newest first
    first_item = channel.find("item")
    for item in reversed(new_items):
        channel.insert(list(channel).index(first_item), item)

# 5) UPDATE CHANNEL TITLE (always based on source feed)
src_title = src_channel.find("title").text or ""
channel.find("title").text = f"{src_title} (L’intégrale)"

# 6) UPDATE TIMESTAMPS
now = formatdate(usegmt=True)
for tag in ("lastBuildDate","pubDate"):
    node = channel.find(tag)
    if node is not None:
        node.text = now
    else:
        ET.SubElement(channel, tag).text = now

# 7) WRITE OUT
ET.indent(root, space="  ")
ET.ElementTree(root).write(
    output_file,
    encoding="utf-8",
    xml_declaration=True
)
print(f"✔️ wrote {len(new_items)} new item(s) to {output_file}")

# 8) COMMIT & PUSH if we added anything
if new_items:
    os.chdir(repo_path)
    subprocess.run(["git","add", os.path.basename(output_file)])
    msg = f"Add {len(new_items)} new L’INTÉGRALE item(s) at {now}"
    subprocess.run(["git","commit","-m", msg], check=False)
    subprocess.run(["git","push","origin","main"], check=False)

#!/usr/bin/env python3
import xml.etree.ElementTree as ET
import requests
from email.utils import formatdate
import subprocess
import os

# ─── CONFIG ───────────────────────────────────────────────────
feed_url          = "https://feeds.audiomeans.fr/feed/d7c6111b-04c1-46bc-b74c-d941a90d37fb.xml"
output_integrale  = "only_integrale_feed.xml"
output_best       = "only_best_feed.xml"
integrale_pref    = "L'INTÉGRALE"
best_prefs        = ("MEILLEUR DE LA SAISON", "BEST OF", "MOMENT CULTE")
repo_path         = "."
# ───────────────────────────────────────────────────────────────

# preserve itunes: namespace
ET.register_namespace('itunes', 'http://www.itunes.com/dtds/podcast-1.0.dtd')

# 1) FETCH source feed
resp         = requests.get(feed_url)
resp.raise_for_status()
src_root     = ET.fromstring(resp.content)
src_channel  = src_root.find("channel")

# 2) LOAD existing feeds and collect GUIDs
existing_guids_i = set()
existing_root_i = existing_channel_i = None
if os.path.exists(output_integrale):
    existing_tree_i    = ET.parse(output_integrale)
    existing_root_i    = existing_tree_i.getroot()
    existing_channel_i = existing_root_i.find("channel")
    for item in existing_channel_i.findall("item"):
        existing_guids_i.add(item.find("guid").text.strip())

existing_guids_b = set()
existing_root_b = existing_channel_b = None
if os.path.exists(output_best):
    existing_tree_b    = ET.parse(output_best)
    existing_root_b    = existing_tree_b.getroot()
    existing_channel_b = existing_root_b.find("channel")
    for item in existing_channel_b.findall("item"):
        existing_guids_b.add(item.find("guid").text.strip())

# 3) PICK UP new items
new_i = []
new_b = []
for item in src_channel.findall("item"):
    title = item.find("title").text.strip()
    guid  = item.find("guid").text.strip()
    if title.startswith(integrale_pref) and guid not in existing_guids_i:
        new_i.append(item)
    if any(title.startswith(p) for p in best_prefs) and guid not in existing_guids_b:
        new_b.append(item)

# if nothing new for a feed and it exists, skip writing it
if not new_i and existing_channel_i is not None:
    print("No new integrale items, skipping integrale feed")
else:
    # 4a) BUILD or MERGE the integrale feed
    if existing_channel_i is None:
        root_i    = src_root
        channel_i = src_channel
        # strip out everything not L'INTÉGRALE
        for it in list(channel_i.findall("item")):
            if not it.find("title").text.strip().startswith(integrale_pref):
                channel_i.remove(it)
    else:
        root_i    = existing_root_i
        channel_i = existing_channel_i
        first = channel_i.find("item")
        for it in reversed(new_i):
            channel_i.insert(list(channel_i).index(first), it)

    # 5a) UPDATE integrale TITLE & DATES
    channel_i.find("title").text = f"{src_channel.find('title').text} (L’intégrale)"
    now = formatdate(usegmt=True)
    for tag in ("lastBuildDate","pubDate"):
        node = channel_i.find(tag)
        if node is not None:
            node.text = now
        else:
            ET.SubElement(channel_i, tag).text = now

    # 6a) WRITE integrale
    ET.indent(root_i, space="  ")
    ET.ElementTree(root_i).write(output_integrale, encoding="utf-8", xml_declaration=True)
    print(f"✔️ wrote {len(new_i)} new integrale item(s) to {output_integrale}")

    # 7a) COMMIT & PUSH integrale
    if new_i:
        os.chdir(repo_path)
        subprocess.run(["git","add", os.path.basename(output_integrale)])
        msg = f"Add {len(new_i)} new L’INTÉGRALE item(s) at {now}"
        subprocess.run(["git","commit","-m", msg], check=False)
        subprocess.run(["git","push","origin","main"], check=False)

if not new_b and existing_channel_b is not None:
    print("No new best-of items, skipping best-of feed")
else:
    # 4b) BUILD or MERGE the best-of feed
    if existing_channel_b is None:
        root_b    = src_root
        channel_b = src_channel
        # strip out everything not in best_prefs
        for it in list(channel_b.findall("item")):
            if not any(it.find("title").text.strip().startswith(p) for p in best_prefs):
                channel_b.remove(it)
    else:
        root_b    = existing_root_b
        channel_b = existing_channel_b
        first = channel_b.find("item")
        for it in reversed(new_b):
            channel_b.insert(list(channel_b).index(first), it)

    # 5b) UPDATE best-of TITLE & DATES
    channel_b.find("title").text = f"{src_channel.find('title').text} (Best Episodes)"
    # reuse `now`
    for tag in ("lastBuildDate","pubDate"):
        node = channel_b.find(tag)
        if node is not None:
            node.text = now
        else:
            ET.SubElement(channel_b, tag).text = now

    # 6b) WRITE best-of
    ET.indent(root_b, space="  ")
    ET.ElementTree(root_b).write(output_best, encoding="utf-8", xml_declaration=True)
    print(f"✔️ wrote {len(new_b)} new best-of item(s) to {output_best}")

    # 7b) COMMIT & PUSH best-of
    if new_b:
        os.chdir(repo_path)
        subprocess.run(["git","add", os.path.basename(output_best)])
        msg = f"Add {len(new_b)} new best-of item(s) at {now}"
        subprocess.run(["git","commit","-m", msg], check=False)
        subprocess.run(["git","push","origin","main"], check=False)

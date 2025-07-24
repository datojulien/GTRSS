#!/usr/bin/env python3
import xml.etree.ElementTree as ET
import requests
from email.utils import formatdate
import subprocess
import os

# ─── CONFIG ───────────────────────────────────────────────────
feed_url            = "https://feeds.audiomeans.fr/feed/d7c6111b-04c1-46bc-b74c-d941a90d37fb.xml"
output_integrale    = "only_integrale_feed.xml"
output_best         = "only_best_feed.xml"
output_remaining    = "only_remaining_feed.xml"
integrale_pref      = "L'INTÉGRALE"
best_prefs          = ("MEILLEUR DE LA SAISON", "BEST OF", "MOMENT CULTE")
repo_path           = "."
# Cover art URLs (raw GitHub links)
# Using the datojulien/GTRSS repository
integrale_image_url = "https://raw.githubusercontent.com/datojulien/GTRSS/main/Integrales.jpg"
best_image_url      = "https://raw.githubusercontent.com/datojulien/GTRSS/main/Extras.jpg"
# ───────────────────────────────────────────────────────────────

# Register iTunes namespace to preserve prefixes
ITUNES_NS = 'http://www.itunes.com/dtds/podcast-1.0.dtd'
ET.register_namespace('itunes', ITUNES_NS)

# 1) FETCH source feed
resp = requests.get(feed_url)
resp.raise_for_status()
raw = resp.content
# parse once for detection
src_root = ET.fromstring(raw)
src_channel = src_root.find('channel')

# 2) LOAD existing feeds and collect GUIDs
# Integrale feed\existing_guids_i = set()
existing_root_i = existing_channel_i = None
if os.path.exists(output_integrale):
    tree_i = ET.parse(output_integrale)
    existing_root_i = tree_i.getroot()
    existing_channel_i = existing_root_i.find('channel')
    for item in existing_channel_i.findall('item'):
        existing_guids_i.add(item.find('guid').text.strip())

# Best-of feed
existing_guids_b = set()
existing_root_b = existing_channel_b = None
if os.path.exists(output_best):
    tree_b = ET.parse(output_best)
    existing_root_b = tree_b.getroot()
    existing_channel_b = existing_root_b.find('channel')
    for item in existing_channel_b.findall('item'):
        existing_guids_b.add(item.find('guid').text.strip())

# Remaining feed
existing_guids_r = set()
existing_root_r = existing_channel_r = None
if os.path.exists(output_remaining):
    tree_r = ET.parse(output_remaining)
    existing_root_r = tree_r.getroot()
    existing_channel_r = existing_root_r.find('channel')
    for item in existing_channel_r.findall('item'): 
        existing_guids_r.add(item.find('guid').text.strip())

# 3) PICK UP new items
new_i = []  # integrale
new_b = []  # best-of
new_r = []  # remaining
for item in src_channel.findall('item'):
    title = item.find('title').text.strip()
    guid  = item.find('guid').text.strip()
    is_integrale = title.startswith(integrale_pref)
    is_best      = any(title.startswith(pref) for pref in best_prefs)
    if is_integrale and guid not in existing_guids_i:
        new_i.append(item)
    if is_best and guid not in existing_guids_b:
        new_b.append(item)
    if not is_integrale and not is_best and guid not in existing_guids_r:
        new_r.append(item)

# timestamp
now = formatdate(usegmt=True)

# helper: apply cover
def apply_cover(channel, image_url):
    tag = f"{{{ITUNES_NS}}}image"
    for old in channel.findall(tag):
        channel.remove(old)
    img = ET.Element(tag)
    img.set('href', image_url)
    title_elem = channel.find('title')
    if title_elem is not None:
        idx = list(channel).index(title_elem)
        channel.insert(idx + 1, img)
    else:
        channel.insert(0, img)

# --- Process Integrale Feed ---
if new_i or existing_channel_i is None:
    if existing_channel_i is None:
        root_i = ET.fromstring(raw)
        channel_i = root_i.find('channel')
        for it in list(channel_i.findall('item')):
            if not it.find('title').text.strip().startswith(integrale_pref):
                channel_i.remove(it)
    else:
        root_i = existing_root_i
        channel_i = existing_channel_i
        first = channel_i.find('item')
        for it in reversed(new_i):
            channel_i.insert(list(channel_i).index(first), it)
    apply_cover(channel_i, integrale_image_url)
    src_title = src_channel.find('title').text or ''
    channel_i.find('title').text = f"{src_title} (L’intégrale)"
    for tag in ('lastBuildDate', 'pubDate'):
        node = channel_i.find(tag)
        if node is not None:
            node.text = now
        else:
            ET.SubElement(channel_i, tag).text = now
    ET.indent(root_i, space='  ')
    ET.ElementTree(root_i).write(output_integrale, encoding='utf-8', xml_declaration=True)
    print(f"✔️ wrote {len(new_i)} new integrale item(s) to {output_integrale}")
    if new_i:
        os.chdir(repo_path)
        subprocess.run(['git', 'add', output_integrale])
        msg = f"Add {len(new_i)} new L’INTÉGRALE item(s) at {now}"
        subprocess.run(['git', 'commit', '-m', msg], check=False)
        subprocess.run(['git', 'push', 'origin', 'main'], check=False)
else:
    print('No new integrale items, skipping integrale feed')

# --- Process Best-of (Extras) Feed ---
if new_b or existing_channel_b is None:
    if existing_channel_b is None:
        root_b = ET.fromstring(raw)
        channel_b = root_b.find('channel')
        for it in list(channel_b.findall('item')):
            if not any(it.find('title').text.strip().startswith(pref) for pref in best_prefs):
                channel_b.remove(it)
    else:
        root_b = existing_root_b
        channel_b = existing_channel_b
        first = channel_b.find('item')
        for it in reversed(new_b):
            channel_b.insert(list(channel_b).index(first), it)
    apply_cover(channel_b, best_image_url)
    src_title = src_channel.find('title').text or ''
    channel_b.find('title').text = f"{src_title} (Extras)"
    for tag in ('lastBuildDate', 'pubDate'):
        node = channel_b.find(tag)
        if node is not None:
            node.text = now
        else:
            ET.SubElement(channel_b, tag).text = now
    ET.indent(root_b, space='  ')
    ET.ElementTree(root_b).write(output_best, encoding='utf-8', xml_declaration=True)
    print(f"✔️ wrote {len(new_b)} new extras item(s) to {output_best}")
    if new_b:
        os.chdir(repo_path)
        subprocess.run(['git', 'add', output_best])
        msg = f"Add {len(new_b)} new Extras item(s) at {now}"
        subprocess.run(['git', 'commit', '-m', msg], check=False)
        subprocess.run(['git', 'push', 'origin', 'main'], check=False)
else:
    print('No new extras items, skipping extras feed')

# --- Process Remaining Feed ---
if new_r or existing_channel_r is None:
    if existing_channel_r is None:
        root_r = ET.fromstring(raw)
        channel_r = root_r.find('channel')
        for it in list(channel_r.findall('item')):
            t = it.find('title').text.strip()
            if t.startswith(integrale_pref) or any(t.startswith(pref) for pref in best_prefs):
                channel_r.remove(it)
    else:
        root_r = existing_root_r
        channel_r = existing_channel_r
        first = channel_r.find('item')
        for it in reversed(new_r):
            channel_r.insert(list(channel_r).index(first), it)
    src_title = src_channel.find('title').text or ''
    channel_r.find('title').text = f"{src_title} (Other Episodes)"
    for tag in ('lastBuildDate', 'pubDate'):
        node = channel_r.find(tag)
        if node is not None:
            node.text = now
        else:
            ET.SubElement(channel_r, tag).text = now
    ET.indent(root_r, space='  ')
    ET.ElementTree(root_r).write(output_remaining, encoding='utf-8', xml_declaration=True)
    print(f"✔️ wrote {len(new_r)} new remaining item(s) to {output_remaining}")
    if new_r:
        os.chdir(repo_path)
        subprocess.run(['git', 'add', output_remaining])
        msg = f"Add {len(new_r)} new remaining item(s) at {now}"
        subprocess.run(['git', 'commit', '-m', msg], check=False)
        subprocess.run(['git', 'push', 'origin', 'main'], check=False)
else:
    print('No new remaining items, skipping remaining feed')

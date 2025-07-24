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
integrale_image_url = "https://raw.githubusercontent.com/datojulien/GTRSS/main/Integrales.jpg"
best_image_url      = "https://raw.githubusercontent.com/datojulien/GTRSS/main/Extras.jpg"
# Custom channel summaries
integrale_summary   = "Tous les épisodes de L'Intégrale de 'Les Grosses Têtes', regroupant la diffusion complète sans coupures ni extras."
best_summary        = "Le Best Of : une sélection des moments les plus drôles et emblématiques de la saison, incluant bonus et moments cultes."
remaining_summary   = "Les autres épisodes : tout le reste du flux officiel, hors Intégrale et Best Of, pour ne rien manquer."
# ───────────────────────────────────────────────────────────────

# Register namespaces
ITUNES_NS = 'http://www.itunes.com/dtds/podcast-1.0.dtd'
NS2 = 'http://www.google.com/schemas/play-podcasts/1.0'
ET.register_namespace('itunes', ITUNES_NS)
ET.register_namespace('ns2', NS2)

# 1) FETCH source feed
resp = requests.get(feed_url)
resp.raise_for_status()
raw = resp.content
src_root = ET.fromstring(raw)
src_channel = src_root.find('channel')

# 2) LOAD existing feeds and collect GUIDs
existing_guids_i = set()
existing_root_i = existing_channel_i = None
if os.path.exists(output_integrale):
    tree_i = ET.parse(output_integrale)
    existing_root_i = tree_i.getroot()
    existing_channel_i = existing_root_i.find('channel')
    for item in existing_channel_i.findall('item'):
        existing_guids_i.add(item.find('guid').text.strip())

existing_guids_b = set()
existing_root_b = existing_channel_b = None
if os.path.exists(output_best):
    tree_b = ET.parse(output_best)
    existing_root_b = tree_b.getroot()
    existing_channel_b = existing_root_b.find('channel')
    for item in existing_channel_b.findall('item'):
        existing_guids_b.add(item.find('guid').text.strip())

existing_guids_r = set()
existing_root_r = existing_channel_r = None
if os.path.exists(output_remaining):
    tree_r = ET.parse(output_remaining)
    existing_root_r = tree_r.getroot()
    existing_channel_r = existing_root_r.find('channel')
    for item in existing_channel_r.findall('item'):
        existing_guids_r.add(item.find('guid').text.strip())

# 3) PICK UP new items
new_i, new_b, new_r = [], [], []
for item in src_channel.findall('item'):
    title = item.find('title').text.strip()
    guid = item.find('guid').text.strip()
    is_integrale = title.startswith(integrale_pref)
    is_best = any(title.startswith(pref) for pref in best_prefs)
    if is_integrale and guid not in existing_guids_i:
        new_i.append(item)
    if is_best and guid not in existing_guids_b:
        new_b.append(item)
    if not is_integrale and not is_best and guid not in existing_guids_r:
        new_r.append(item)

# 4) Helper to apply cover art and strip old images
def apply_cover(channel, image_url):
    for old in channel.findall('image') + channel.findall(f"{{{NS2}}}image") + channel.findall(f"{{{ITUNES_NS}}}image"):
        channel.remove(old)
    img = ET.Element(f"{{{ITUNES_NS}}}image")
    img.set('href', image_url)
    title_elem = channel.find('title')
    idx = list(channel).index(title_elem) if title_elem is not None else 0
    channel.insert(idx+1, img)

# Timestamp
now = formatdate(usegmt=True)

# Function to update common channel tags
def finalize_channel(channel, cover_url, title_suffix, summary_text):
    apply_cover(channel, cover_url)
    src_title = src_channel.find('title').text or ''
    channel.find('title').text = f"{src_title} ({title_suffix})"
    # itunes:summary
    sum_tag = f"{{{ITUNES_NS}}}summary"
    node = channel.find(sum_tag)
    if node is None:
        node = ET.SubElement(channel, sum_tag)
    node.text = summary_text
    # pubDate and lastBuildDate
    for tag in ('pubDate','lastBuildDate'):
        n = channel.find(tag)
        if n is None:
            ET.SubElement(channel, tag).text = now
        else:
            n.text = now

# --- Generate Integrale Feed ---
if new_i or existing_channel_i is None:
    if existing_channel_i is None:
        root_i = ET.fromstring(raw)
        channel_i = root_i.find('channel')
        for it in list(channel_i.findall('item')):
            if not it.find('title').text.strip().startswith(integrale_pref):
                channel_i.remove(it)
    else:
        root_i, channel_i = existing_root_i, existing_channel_i
        first = channel_i.find('item')
        for it in reversed(new_i): channel_i.insert(list(channel_i).index(first), it)
    finalize_channel(channel_i, integrale_image_url, "L’intégrale", integrale_summary)
    ET.indent(root_i, space='  ')
    ET.ElementTree(root_i).write(output_integrale, encoding='utf-8', xml_declaration=True)
    print(f"✔️ wrote {len(new_i)} integrale items to {output_integrale}")

# --- Generate Best-of (Extras) Feed ---
if new_b or existing_channel_b is None:
    if existing_channel_b is None:
        root_b = ET.fromstring(raw)
        channel_b = root_b.find('channel')
        for it in list(channel_b.findall('item')):
            if not any(it.find('title').text.strip().startswith(pref) for pref in best_prefs):
                channel_b.remove(it)
    else:
        root_b, channel_b = existing_root_b, existing_channel_b
        first = channel_b.find('item')
        for it in reversed(new_b): channel_b.insert(list(channel_b).index(first), it)
    finalize_channel(channel_b, best_image_url, "Extras", best_summary)
    ET.indent(root_b, space='  ')
    ET.ElementTree(root_b).write(output_best, encoding='utf-8', xml_declaration=True)
    print(f"✔️ wrote {len(new_b)} best-of items to {output_best}")

# --- Generate Remaining Feed ---
if new_r or existing_channel_r is None:
    if existing_channel_r is None:
        root_r = ET.fromstring(raw)
        channel_r = root_r.find('channel')
        for it in list(channel_r.findall('item')):
            t = it.find('title').text.strip()
            if t.startswith(integrale_pref) or any(t.startswith(pref) for pref in best_prefs):
                channel_r.remove(it)
    else:
        root_r, channel_r = existing_root_r, existing_channel_r
        first = channel_r.find('item')
        for it in reversed(new_r): channel_r.insert(list(channel_r).index(first), it)
    finalize_channel(channel_r, integrale_image_url, "Other Episodes", remaining_summary)
    ET.indent(root_r, space='  ')
    ET.ElementTree(root_r).write(output_remaining, encoding='utf-8', xml_declaration=True)
    print(f"✔️ wrote {len(new_r)} remaining items to {output_remaining}")

# Git commit/push steps can follow if needed

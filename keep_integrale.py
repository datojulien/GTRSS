#!/usr/bin/env python3
# -*- coding: utf-8 -*-

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

# Titles (prefix checks use .startswith on tuples)
integrale_pref      = ("L'INTÉGRALE", "DÉBRIEF")
best_prefs          = (
    "MEILLEUR DE LA SAISON",
    "BEST OF",
    "MOMENT CULTE",
    "L'INTÉGRALE - Le Best of",   # important: treat as Best-of, not Intégrale
)

# Best-of minimum duration (minutes)
MIN_BEST_DURATION_MIN = 20
MIN_BEST_DURATION_SEC = MIN_BEST_DURATION_MIN * 60

repo_path           = "."

# Cover art
integrale_image_url = "https://raw.githubusercontent.com/datojulien/GTRSS/main/Integrales.jpg"
best_image_url      = "https://raw.githubusercontent.com/datojulien/GTRSS/main/Extras.jpg"
autres_image_url    = "https://raw.githubusercontent.com/datojulien/GTRSS/main/Autres.jpg"

# Channel summaries
integrale_summary   = "Tous les épisodes de L'Intégrale de 'Les Grosses Têtes', regroupant la diffusion complète sans coupures ni extras."
best_summary        = "Le Best Of : une sélection des moments les plus drôles et emblématiques de la saison, incluant bonus et moments cultes (≥ 20 min)."
remaining_summary   = "Les autres épisodes : tout le reste du flux officiel, hors Intégrale et Best Of, pour ne rien manquer."
# ───────────────────────────────────────────────────────────────

# Namespaces
ITUNES_NS = "http://www.itunes.com/dtds/podcast-1.0.dtd"
GPOD_NS   = "http://www.google.com/schemas/play-podcasts/1.0"
ET.register_namespace('itunes', ITUNES_NS)

# 1) FETCH source feed
resp = requests.get(feed_url, timeout=60)
resp.raise_for_status()
raw = resp.content
src_root = ET.fromstring(raw)
src_channel = src_root.find('channel')

# 2) LOAD existing feeds and collect GUIDs
def load_existing(path):
    guids = set()
    root = channel = None
    if os.path.exists(path):
        tree = ET.parse(path)
        root = tree.getroot()
        channel = root.find('channel')
        for item in channel.findall('item'):
            g = item.find('guid')
            if g is not None and g.text:
                guids.add(g.text.strip())
    return root, channel, guids

existing_root_i, existing_channel_i, existing_guids_i = load_existing(output_integrale)
existing_root_b, existing_channel_b, existing_guids_b = load_existing(output_best)
existing_root_r, existing_channel_r, existing_guids_r = load_existing(output_remaining)

# 3) HELPERS
def safe_text(elem, tag, ns=None):
    if ns:
        tag = f"{{{ns}}}{tag}"
    node = elem.find(tag)
    return (node.text or "").strip() if node is not None and node.text else ""

def parse_itunes_duration_to_seconds(text: str) -> int:
    """
    Parse itunes:duration value to seconds.
    Accepts "SS", "MM:SS", "HH:MM:SS". Returns -1 if invalid/missing.
    """
    if not text:
        return -1
    s = text.strip()
    try:
        # pure seconds
        if s.isdigit():
            return int(s)
        parts = s.split(":")
        if len(parts) == 2:  # MM:SS
            mm, ss = parts
            return int(mm) * 60 + int(ss)
        if len(parts) == 3:  # HH:MM:SS
            hh, mm, ss = parts
            return int(hh) * 3600 + int(mm) * 60 + int(ss)
    except Exception:
        pass
    return -1

def get_item_duration_seconds(item) -> int:
    dur_text = safe_text(item, 'duration', ITUNES_NS)
    return parse_itunes_duration_to_seconds(dur_text)

def is_best_title(title: str) -> bool:
    return any(title.startswith(pref) for pref in best_prefs)

def is_integrale_title(title: str) -> bool:
    # Intégrale only if it starts with integrale_pref AND is NOT best-of
    return title.startswith(integrale_pref) and not is_best_title(title)

def is_best_episode(item) -> bool:
    """
    Best-of classification that ALSO enforces the duration threshold.
    Missing/invalid duration -> exclude from Best-of.
    """
    title = safe_text(item, 'title')
    if not is_best_title(title):
        return False
    dur = get_item_duration_seconds(item)
    return dur >= MIN_BEST_DURATION_SEC

def is_remaining_title(t: str) -> bool:
    return (not is_integrale_title(t)) and (not is_best_title(t))

# 4) COLLECT new items (incremental pass)
new_i, new_b, new_r = [], [], []

for item in src_channel.findall('item'):
    title = safe_text(item, 'title')
    guid  = safe_text(item, 'guid')

    if not guid:
        continue

    if is_integrale_title(title):
        if guid not in existing_guids_i:
            new_i.append(item)
    elif is_best_episode(item):
        if guid not in existing_guids_b:
            new_b.append(item)
    else:
        if guid not in existing_guids_r:
            new_r.append(item)

# 5) COVER handling
def apply_cover(channel, image_url):
    # Remove any existing <image>, <itunes:image>, <gpod:image>
    for old in channel.findall('image') + channel.findall(f"{{{GPOD_NS}}}image") + channel.findall(f"{{{ITUNES_NS}}}image"):
        channel.remove(old)
    img = ET.Element(f"{{{ITUNES_NS}}}image")
    img.set('href', image_url)
    title_elem = channel.find('title')
    idx = list(channel).index(title_elem) if title_elem is not None else 0
    channel.insert(idx + 1, img)

# Timestamp
now = formatdate(usegmt=True)

# 6) Channel finalization
def finalize_channel(channel, cover_url, title_suffix, summary_text):
    apply_cover(channel, cover_url)
    src_title = safe_text(src_channel, 'title')
    title_node = channel.find('title')
    if title_node is None:
        title_node = ET.SubElement(channel, 'title')
    title_node.text = f"{src_title} ({title_suffix})"

    # <description>
    desc = channel.find('description')
    if desc is None:
        desc = ET.SubElement(channel, 'description')
    desc.text = summary_text

    # <itunes:summary>
    sum_tag = f"{{{ITUNES_NS}}}summary"
    node = channel.find(sum_tag)
    if node is None:
        node = ET.SubElement(channel, sum_tag)
    node.text = summary_text

    # timestamps
    for tag in ('pubDate', 'lastBuildDate'):
        n = channel.find(tag)
        if n is None:
            ET.SubElement(channel, tag).text = now
        else:
            n.text = now

# 7) Utilities
def clone_and_filter(predicate_item):
    """
    Clone the original feed root and keep only items for which predicate_item(item) is True.
    """
    root = ET.fromstring(raw)
    ch   = root.find('channel')
    for it in list(ch.findall('item')):
        if not predicate_item(it):
            ch.remove(it)
    return root, ch

def insert_new_items_at_top(channel, new_items):
    """
    Insert in reverse to keep original order at top.
    """
    if not new_items:
        return
    first = channel.find('item')
    for it in reversed(new_items):
        if first is not None:
            channel.insert(list(channel).index(first), it)
        else:
            channel.append(it)

def prune_best_short_items(channel_b):
    """
    Remove any items in existing Best-of channel whose duration is below threshold,
    or which no longer match Best-of title (safety net).
    """
    changed = False
    for it in list(channel_b.findall('item')):
        title = safe_text(it, 'title')
        if (not is_best_title(title)) or (get_item_duration_seconds(it) < MIN_BEST_DURATION_SEC):
            channel_b.remove(it)
            changed = True
    return changed

# --- Generate Intégrale Feed ---
if new_i or existing_channel_i is None:
    if existing_channel_i is None:
        # Keep items that are integrale (but not best-of)
        root_i, channel_i = clone_and_filter(lambda it: is_integrale_title(safe_text(it, 'title')))
    else:
        root_i, channel_i = existing_root_i, existing_channel_i
        insert_new_items_at_top(channel_i, new_i)

    finalize_channel(channel_i, integrale_image_url, "L’intégrale", integrale_summary)
    try:
        ET.indent(root_i, space='  ')
    except AttributeError:
        pass
    ET.ElementTree(root_i).write(output_integrale, encoding='utf-8', xml_declaration=True)
    print(f"✔️ wrote {len(new_i)} integrale items to {output_integrale}")

    if new_i:
        try:
            os.chdir(repo_path)
            subprocess.run(["git", "add", output_integrale], check=False)
            subprocess.run(["git", "commit", "-m", f"Add {len(new_i)} new integrale item(s) at {now}"], check=False)
            subprocess.run(["git", "push", "origin", "main"], check=False)
        finally:
            pass

# --- Generate Best-of (Extras) Feed (≥ 20 min) ---
if new_b or existing_channel_b is None:
    if existing_channel_b is None:
        # Keep items that are best-of AND satisfy duration threshold
        root_b, channel_b = clone_and_filter(is_best_episode)
    else:
        root_b, channel_b = existing_root_b, existing_channel_b
        # Insert new qualifying items
        insert_new_items_at_top(channel_b, new_b)
        # Prune any too-short or no longer best-of items already present
        if prune_best_short_items(channel_b):
            print("⛏️  pruned short/non-best items from existing Best-of feed")

    finalize_channel(channel_b, best_image_url, "Extras", best_summary)
    try:
        ET.indent(root_b, space='  ')
    except AttributeError:
        pass
    ET.ElementTree(root_b).write(output_best, encoding='utf-8', xml_declaration=True)
    print(f"✔️ wrote {len(new_b)} best-of items (≥ {MIN_BEST_DURATION_MIN} min) to {output_best}")

    if new_b:
        try:
            os.chdir(repo_path)
            subprocess.run(["git", "add", output_best], check=False)
            subprocess.run(["git", "commit", "-m", f"Add {len(new_b)} new best-of item(s) ≥ {MIN_BEST_DURATION_MIN} min at {now}"], check=False)
            subprocess.run(["git", "push", "origin", "main"], check=False)
        finally:
            pass

# --- Generate Remaining Feed ---
if new_r or existing_channel_r is None:
    if existing_channel_r is None:
        # Keep items that are neither integrale nor best-of (no duration rule here)
        root_r, channel_r = clone_and_filter(
            lambda it: (not is_integrale_title(safe_text(it, 'title'))) and (not is_best_episode(it))
        )
    else:
        root_r, channel_r = existing_root_r, existing_channel_r
        insert_new_items_at_top(channel_r, new_r)

    finalize_channel(channel_r, autres_image_url, "Other Episodes", remaining_summary)
    try:
        ET.indent(root_r, space='  ')
    except AttributeError:
        pass
    ET.ElementTree(root_r).write(output_remaining, encoding='utf-8', xml_declaration=True)
    print(f"✔️ wrote {len(new_r)} remaining items to {output_remaining}")

    if new_r:
        try:
            os.chdir(repo_path)
            subprocess.run(["git", "add", output_remaining], check=False)
            subprocess.run(["git", "commit", "-m", f"Add {len(new_r)} new remaining item(s) at {now}"], check=False)
            subprocess.run(["git", "push", "origin", "main"], check=False)
        finally:
            pass

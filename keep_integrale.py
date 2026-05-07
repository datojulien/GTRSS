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

# Title prefix checks use .startswith on tuples
integrale_pref      = ("L'INTÉGRALE", "DÉBRIEF")
best_prefs          = (
    "MEILLEUR DE LA SAISON",
    "BEST OF",
    "MOMENT CULTE",
    "L'INTÉGRALE - Le Best of",   # ensure these go to Best-of, not Intégrale
)

# Best-of minimum duration (minutes)
MIN_BEST_DURATION_MIN = 20
MIN_BEST_DURATION_SEC = MIN_BEST_DURATION_MIN * 60

# Git repo root (optional; leave "." to use current dir)
repo_path           = "."

# Cover art URLs
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

# Timestamp
now = formatdate(usegmt=True)

# ─── FETCH SOURCE FEED ────────────────────────────────────────
resp = requests.get(feed_url, timeout=60)
resp.raise_for_status()
raw = resp.content
src_root = ET.fromstring(raw)
src_channel = src_root.find('channel')

# ─── HELPERS ──────────────────────────────────────────────────
def safe_text(elem, tag, ns=None):
    if ns:
        tag = f"{{{ns}}}{tag}"
    node = elem.find(tag)
    return (node.text or "").strip() if node is not None and node.text else ""

def parse_itunes_duration_to_seconds(text: str) -> int:
    """
    Parse itunes:duration to seconds.
    Accepts "SS", "MM:SS", "HH:MM:SS". Returns -1 if invalid/missing.
    """
    if not text:
        return -1
    s = text.strip()
    try:
        if s.isdigit():
            return int(s)
        parts = s.split(":")
        if len(parts) == 2:
            mm, ss = parts
            return int(mm) * 60 + int(ss)
        if len(parts) == 3:
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
    # Intégrale only if starts with integrale_pref AND is NOT best-of
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

def is_remaining_item(item) -> bool:
    t = safe_text(item, 'title')
    return (not is_integrale_title(t)) and (not is_best_episode(item))

def new_root_with_filtered_items(predicate_item):
    """
    Create a fresh copy of the source feed, keeping only items that satisfy predicate_item(item).
    """
    root = ET.fromstring(raw)
    ch   = root.find('channel')
    for it in list(ch.findall('item')):
        if not predicate_item(it):
            ch.remove(it)
    return root, ch

def apply_cover(channel, image_url):
    # Remove any existing <image>, <itunes:image>, <gpod:image>
    for old in channel.findall('image') + channel.findall(f"{{{GPOD_NS}}}image") + channel.findall(f"{{{ITUNES_NS}}}image"):
        channel.remove(old)
    img = ET.Element(f"{{{ITUNES_NS}}}image")
    img.set('href', image_url)
    title_elem = channel.find('title')
    idx = list(channel).index(title_elem) if title_elem is not None else 0
    channel.insert(idx + 1, img)

def finalize_channel(channel, cover_url, title_suffix, summary_text):
    apply_cover(channel, cover_url)
    src_title = safe_text(src_channel, 'title')

    # <title>
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

def write_xml(root, out_path):
    try:
        ET.indent(root, space='  ')
    except AttributeError:
        pass
    ET.ElementTree(root).write(out_path, encoding='utf-8', xml_declaration=True)

def git_commit(paths, message):
    try:
        cwd = os.getcwd()
        os.chdir(repo_path)
        subprocess.run(["git", "add"] + paths, check=False)
        subprocess.run(["git", "commit", "-m", message], check=False)
        subprocess.run(["git", "push", "origin", "main"], check=False)
    finally:
        try:
            os.chdir(cwd)
        except Exception:
            pass

# ─── BUILD ALL FEEDS FRESH (always overwrite) ─────────────────
# Intégrale (not best-of)
root_i, ch_i = new_root_with_filtered_items(lambda it: is_integrale_title(safe_text(it, 'title')))
finalize_channel(ch_i, integrale_image_url, "L’intégrale", integrale_summary)
write_xml(root_i, output_integrale)
print(f"✔️ rebuilt {output_integrale}")

# Best-of (≥ 20 min)
root_b, ch_b = new_root_with_filtered_items(is_best_episode)
finalize_channel(ch_b, best_image_url, "Extras", best_summary)
write_xml(root_b, output_best)
print(f"✔️ rebuilt {output_best} (only items ≥ {MIN_BEST_DURATION_MIN} min)")

# Remaining (everything else that isn't Intégrale or Best-of ≥ 20)
root_r, ch_r = new_root_with_filtered_items(is_remaining_item)
finalize_channel(ch_r, autres_image_url, "Other Episodes", remaining_summary)
write_xml(root_r, output_remaining)
print(f"✔️ rebuilt {output_remaining}")

# Optional: single commit covering all three (comment out if undesired)
git_commit(
    [output_integrale, output_best, output_remaining],
    f"Rebuild feeds at {now}: enforce Best-of ≥ {MIN_BEST_DURATION_MIN} min and proper categorization"
)

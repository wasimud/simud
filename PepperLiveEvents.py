#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
pepperlive_m3u8_events_only.py
==============================
- SOLO canali con evento reale (homepage match-card)
- Nome evento + (nome canale leggibile) tra parentesi
- MPD puliti (senza ?ck=)
- Chiave via #KODIPROP
- group-title = data giornata
Aggiornato Marzo 2026
"""

import re
import sys
import json
import time
import base64
import urllib.parse
from datetime import datetime
from pathlib import Path
import cloudscraper

# =============================================
# CONFIG
# =============================================

BASE = "https://pepperlive.info"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36",
    "Referer": BASE + "/",
    "Accept-Language": "it-IT,it;q=0.9",
}

TIMEOUT = 20
OUTPUT = "PepperLive_Events.m3u8"

CANALI_RINOMINA = {
    "SPORTUNO": "Sky Sport Uno",
    "SPORTCALCIO": "Sky Sport Calcio",
    "SportTV1": "Sport TV 1 PT",
    "SportTV5": "Sport TV 5 PT",
    "Dazn1_PT": "DAZN 1 PT",
    "Dazn2_PT": "DAZN 2 PT",
    "Dazn3_PT": "DAZN 3 PT",
    "live7": "Extra 1080p",
    "Canale65": "720p A",
}

JSON_PATHS = [
    "links.json", "mpd.json", "mpd_links.json", "canali.json",
    "api/links.json", "api/mpd.json", "data/links.json",
    "update/links_v2.json", "player/links.json",
    "links_new.json", "canali_mpd.json", "streams.json",
]

# =============================================

def extract_kid_key(ck: str) -> tuple:
    if not ck:
        return None, None
    ck = ck.strip()
    for pad in ['', '=', '==', '===', '====']:
        try:
            dec = base64.b64decode(ck + pad).decode('utf-8', errors='ignore').strip()
            if ':' in dec and not dec.startswith('{'):
                parts = [x.strip().lower() for x in dec.split(':', 1)]
                if len(parts) == 2:
                    kid, key = parts
            else:
                data = json.loads(dec)
                if isinstance(data, dict):
                    if "kid" in data and "key" in data:
                        kid, key = data["kid"].lower(), data["key"].lower()
                    else:
                        k, v = next(iter(data.items()))
                        kid, key = k.lower(), v.lower()

            kid = re.sub(r'[^0-9a-f]', '', kid)
            key = re.sub(r'[^0-9a-f]', '', key)
            if len(kid) == 32 and len(key) == 32:
                return kid, key
        except:
            continue
    return None, None


def find_global_json(scraper):
    ts = int(time.time())
    for path in JSON_PATHS:
        for prefix in ["", "api/", "data/", "assets/", "update/", "player/"]:
            for query in ["", f"?v={ts}", f"?t={ts}", f"?_{ts}"]:
                url = f"{BASE}/{prefix}{path}{query}"
                try:
                    r = scraper.get(url, timeout=12, headers=HEADERS)
                    if r.status_code == 200 and 'json' in r.headers.get('content-type', '').lower():
                        data = r.json()
                        if isinstance(data, dict) and len(data) > 3:
                            print(f"JSON trovato! {url} ({len(data)} canali)")
                            return data
                except:
                    pass
    print("Nessun JSON MPD trovato.")
    return None


def clean_mpd_url(full_url: str) -> str:
    parsed = urllib.parse.urlparse(full_url)
    if not parsed.query:
        return full_url
    qs = urllib.parse.parse_qs(parsed.query)
    qs.pop('ck', None)
    new_query = urllib.parse.urlencode(qs, doseq=True)
    return parsed._replace(query=new_query).geturl().rstrip('?')


def parse_homepage_for_events(html: str):
    events = []
    lines = html.splitlines()
    i = 0
    current_date = "Sconosciuta"
    current_cat = "Sconosciuta"

    while i < len(lines):
        line = lines[i].strip()

        m = re.search(r'<div class="date-header[^"]*">([^<]+)</div>', line, re.I)
        if m:
            current_date = m.group(1).strip().upper()
            i += 1
            continue

        m = re.search(r'<span class="category-label[^"]*">([^<]+)</span>', line, re.I)
        if m:
            current_cat = re.sub(r'\s+', ' ', m.group(1)).strip().rstrip('- ')
            i += 1
            continue

        if '<div class="match-card' in line:
            card = line
            depth = 1
            i += 1
            while i < len(lines) and depth > 0:
                card += "\n" + lines[i]
                depth += lines[i].count('<div') - lines[i].count('</div>')
                i += 1

            m_time = re.search(r'<span class="ora-txt[^"]*">(.*?)</span>', card, re.DOTALL | re.I)
            orario = m_time.group(1).strip() if m_time else "??:??"

            m_teams = re.search(r'<div class="teams-box[^"]*">(.*?)</div>', card, re.DOTALL | re.I)
            squadre = ""
            if m_teams:
                txt = re.sub(r'<[^>]+>', '', m_teams.group(1))
                txt = re.sub(r'\s+', ' ', txt).strip()
                squadre = txt.replace("VS", " - ").replace("vs", " - ").strip()

            mpd_links = re.findall(r'href="live\.php\?ch=([^"]+)"[^>]*class="[^"]*btn-premium[^"]*"[^>]*>MPD</a>', card, re.I)
            for ch in mpd_links:
                ch = ch.strip()
                if not ch: continue

                parti = []
                if squadre: parti.append(squadre)
                if orario != "??:??": parti.append(orario)
                if current_cat != "Sconosciuta": parti.append(current_cat)

                titolo = " • ".join(parti).strip()
                if not titolo: titolo = f"Evento {ch}"

                events.append({
                    "ch": ch,
                    "title": titolo,
                    "date": current_date,
                    "orario": orario,
                    "squadre": squadre,
                    "cat": current_cat,
                })

        else:
            i += 1

    return events


def main():
    print("=== PepperLive M3U8 - SOLO Eventi Reali + MPD Puliti ===\n")

    scraper = cloudscraper.create_scraper(
        browser={'browser': 'chrome', 'platform': 'windows'},
        delay=5,
    )

    print("→ Scarico homepage per eventi...")
    try:
        r = scraper.get(BASE, headers=HEADERS, timeout=TIMEOUT)
        html = r.text
    except Exception as e:
        print(f"Errore homepage: {e}")
        sys.exit(1)

    events_from_home = parse_homepage_for_events(html)
    print(f"Eventi reali trovati: {len(events_from_home)}")

    print("\n→ Ricerca JSON MPD globale...")
    json_data = find_global_json(scraper)

    if not json_data:
        print("Nessun JSON trovato → impossibile recuperare flussi")
        sys.exit(1)

    m3u = [
        "#EXTM3U",
        f"#PLAYLIST:PepperLive MPD Eventi - {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        "#EXT-X-VERSION:3",
        "#EXT-X-ALLOW-CACHE:YES",
        ""
    ]

    count_success = 0

    for ev in events_from_home:
        ch = ev["ch"]
        nome_can = CANALI_RINOMINA.get(ch, ch)
        titolo_base = ev["title"]
        titolo = f"{titolo_base} ({nome_can})"
        group = ev["date"]

        if ch not in json_data:
            print(f"  {ch:14} → {titolo} (evento ok ma MPD mancante nel JSON)")
            continue

        full_url = json_data[ch]
        clean_url = clean_mpd_url(full_url)

        parsed = urllib.parse.urlparse(full_url)
        qs = urllib.parse.parse_qs(parsed.query)
        ck = qs.get("ck", [None])[0]

        kid, key = extract_kid_key(ck)

        m3u.append(f'#EXTINF:-1 tvg-id="{ch}" tvg-name="{nome_can}" group-title="{group}", {titolo}')
        if kid and key:
            m3u.append("#KODIPROP:inputstream.adaptive.license_type=clearkey")
            m3u.append(f"#KODIPROP:inputstream.adaptive.license_key={kid}:{key}")
        m3u.append("#KODIPROP:inputstream.adaptive.stream_headers=User-Agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
        m3u.append(clean_url)
        m3u.append("")

        count_success += 1
        print(f"  {ch:14} → {titolo}")

    Path(OUTPUT).write_text("\n".join(m3u), encoding="utf-8")
    print(f"\nCreato: {OUTPUT}  ({count_success} canali con evento + MPD valido)")
    print("Solo canali con match reale inclusi (no canali generici senza evento)")
    print("Provalo in Kodi / Tivimate")


if __name__ == "__main__":
    main()

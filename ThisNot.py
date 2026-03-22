#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
ThisNot M3U Generator – Solo MPD (DASH) – Marzo 2026
- Eventi da /api/eventi.json
- Cerca **SOLO** MPD (.mpd), con o senza token in query
- Supporta ClearKey dal pattern chrome-extension o altri ck=...
- Niente HLS / m3u8 – scartati esplicitamente
"""

import cloudscraper
import re
import base64
import json
from urllib.parse import urljoin, quote
import ssl
import urllib3
import time
import sys

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# ---------------- CONFIG ----------------
DOMAINS = ["https://thisnot.business"]
PASSWORD = "2025"
M3U_OUTPUT = "thisnot.m3u8"

# ---------------- SETUP ----------------
unverified_ctx = ssl._create_unverified_context()

scraper = cloudscraper.create_scraper(
    browser={'browser': 'chrome', 'platform': 'windows', 'mobile': False},
    delay=10,
    ssl_context=unverified_ctx,
    interpreter='js2py',
)
scraper.verify = False

scraper.headers.update({
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
    "Accept": "application/json, text/plain, */*",
    "Referer": "https://thisnot.business/",
})

USER_AGENT_QUOTED = quote(scraper.headers["User-Agent"])

# ---------------- HELPER ----------------
def remove_emoji(text):
    if not text:
        return ""
    emoji_pattern = re.compile(
        "["
        u"\U0001F600-\U0001F64F" u"\U0001F300-\U0001F5FF" u"\U0001F680-\U0001F6FF" 
        u"\U0001F1E0-\U0001F1FF" u"\U00002702-\U000027B0" u"\U000024C2-\U0001F251"
        "]+", flags=re.UNICODE)
    return emoji_pattern.sub(r'', text).strip()


def decode_clear_key(b64_str):
    if not b64_str:
        return None
    try:
        b64_str += "=" * ((4 - len(b64_str) % 4) % 4)
        decoded = base64.b64decode(b64_str).decode('utf-8', errors='ignore').strip()
        if decoded.startswith('{'):
            d = json.loads(decoded)
            if d:
                kid, key = next(iter(d.items()))
                return f"{kid.lower()}:{key.lower()}"
        if ':' in decoded:
            parts = decoded.split(':', 1)
            return f"{parts[0].lower()}:{parts[1].lower()}"
        return None
    except:
        return None


def request_url(url, method="GET", data=None, timeout=15):
    try:
        if method.upper() == "GET":
            r = scraper.get(url, timeout=timeout, allow_redirects=True)
        else:
            r = scraper.post(url, data=data, timeout=timeout, allow_redirects=True)
        print(f"  → {method} {url:<65} → {r.status_code} ({len(r.text or ''):,} byte)")
        return r
    except Exception as e:
        print(f"  Errore {url}: {str(e)[:100]}...")
        return None


def attempt_login(base_url):
    login_url = urljoin(base_url, "/index.php")
    print(f"\nProvo dominio → {base_url}")
    
    resp = request_url(login_url)
    if not resp or resp.status_code >= 400:
        return False, None
    
    post_resp = request_url(login_url, "POST", {"password": PASSWORD})
    
    if post_resp and post_resp.status_code < 400 and "INSERIRE PASSWORD" not in post_resp.text.upper():
        print("  LOGIN OK ✓")
        return True, base_url
    
    print("  Login fallito")
    return False, None


# ---------------- ESTRAI SOLO MPD ----------------
def extract_mpd(player_html, titolo):
    # PRIORITÀ 1: Pattern chrome-extension ...#https...mpd...ck=...
    pattern_chrome = r'chrome-extension://opmeopcambhfimffbomjgemehjkbbmji/pages/player\.html#(https?://[^#]+)'
    m = re.search(pattern_chrome, player_html, re.IGNORECASE | re.DOTALL)
    
    if m:
        fragment = m.group(1).strip()
        
        # Ricostruisci URL fermandoci prima di ck=
        parts = re.split(r'([?&])', fragment)
        mpd_parts = []
        ck_value = None
        
        i = 0
        while i < len(parts):
            part = parts[i]
            lower_part = part.lower()
            if 'ck=' in lower_part:
                # Estrai valore ck
                ck_match = re.search(r'ck=([^&#]*)', part + (parts[i+1] if i+1 < len(parts) else ''))
                if ck_match:
                    ck_value = ck_match.group(1).strip()
                break
            mpd_parts.append(part)
            i += 1
        
        candidate_url = ''.join(mpd_parts).rstrip('?& \t\n\r')
        
        # Accetta SOLO se sembra un vero MPD
        lower_url = candidate_url.lower()
        if not (lower_url.endswith('.mpd') or 'manifest.mpd' in lower_url or 'index.mpd' in lower_url):
            print(f"  → chrome-pattern scartato: non termina con .mpd → {candidate_url[:80]}...")
            candidate_url = None
        
        if candidate_url:
            clear_key = decode_clear_key(ck_value) if ck_value else None
            
            print(f"  → MPD chrome-pattern valido → {candidate_url}")
            if clear_key:
                print(f"      └─ ClearKey: {clear_key}")
            
            lines = [
                f"#EXTINF:-1 tvg-id=\"{titolo.lower().replace(' ', '_')}\" group-title=\"ThisNot 2026\",{titolo}",
                f"#KODIPROP:inputstream.adaptive.stream_headers=User-Agent%3D{USER_AGENT_QUOTED}",
            ]
            if clear_key:
                lines.extend([
                    "#KODIPROP:inputstream.adaptive.license_type=clearkey",
                    f"#KODIPROP:inputstream.adaptive.license_key={clear_key}",
                ])
            lines.append(candidate_url)
            return "\n".join(lines), "MPD chrome-pattern"
    
    # PRIORITÀ 2: Cerca esplicitamente solo URL MPD nell'HTML
    mpd_patterns = [
        r'(https?://[^\s"\'<>\]\[\\]+?\.mpd(?:\?[^\s"\'<>\]\[\\]*)?)',
        r'(https?://[^\s"\'<>\]\[\\]+?/Manifest\.mpd(?:\?[^\s"\'<>\]\[\\]*)?)',
        r'(https?://[^\s"\'<>\]\[\\]+?/index\.mpd(?:\?[^\s"\'<>\]\[\\]*)?)',
    ]
    
    for pat in mpd_patterns:
        matches = re.findall(pat, player_html, re.IGNORECASE)
        if matches:
            full_mpd = matches[0].strip()
            
            # Cerchiamo ClearKey (ck=, clearkey=, key=)
            ck_match = re.search(r'(?:ck|clearkey|key)=([A-Za-z0-9+/=_-]+)', player_html, re.IGNORECASE)
            clear_key = decode_clear_key(ck_match.group(1)) if ck_match else None
            
            lines = [
                f"#EXTINF:-1 tvg-id=\"{titolo.lower().replace(' ', '_')}\" group-title=\"ThisNot 2026\",{titolo}",
                f"#KODIPROP:inputstream.adaptive.stream_headers=User-Agent%3D{USER_AGENT_QUOTED}",
            ]
            if clear_key:
                lines.extend([
                    "#KODIPROP:inputstream.adaptive.license_type=clearkey",
                    f"#KODIPROP:inputstream.adaptive.license_key={clear_key}",
                ])
            lines.append(full_mpd)
            
            msg = "MPD generico trovato"
            if clear_key:
                msg += " + ClearKey"
            print(f"  → {msg} → {full_mpd}")
            if clear_key:
                print(f"      └─ ClearKey: {clear_key}")
            
            return "\n".join(lines), msg
    
    print("  Nessun MPD valido trovato nell'HTML – scartato (probabile solo HLS o altro)")
    return None, None


# ---------------- MAIN ----------------
print("=== ThisNot – Solo MPD (no HLS/m3u8) ===\n")

active_domain = None
for dom in DOMAINS:
    ok, url = attempt_login(dom)
    if ok:
        active_domain = url
        break
    time.sleep(3)

if not active_domain:
    print("Login fallito su tutti i domini")
    sys.exit(1)

print(f"Dominio funzionante → {active_domain}\n")

json_url = urljoin(active_domain, "/api/eventi.json")
print("→ Carico eventi da API...")
json_resp = request_url(json_url)

if not json_resp or json_resp.status_code != 200:
    print("Errore su api/eventi.json")
    sys.exit(1)

data = json_resp.json()
eventi = data.get("eventi", [])

print(f"Trovati {len(eventi)} eventi\n")

m3u_lines = [
    "#EXTM3U",
    f"# Generato {time.strftime('%Y-%m-%d %H:%M:%S')} – ThisNot solo MPD",
    "# Nota: contiene **solo** flussi DASH (.mpd) – HLS esclusi",
]

success = 0

for ev in eventi:
    competizione = remove_emoji(ev.get("competizione", "Evento"))
    evento_nome  = remove_emoji(ev.get("evento", ""))
    orario       = remove_emoji(ev.get("orario", ""))
    canale       = remove_emoji(ev.get("canale", ""))
    link         = ev.get("link", "")

    id_match = re.search(r'id=([^&]+)', link)
    if not id_match:
        continue
    chan_id = id_match.group(1)

    titolo_parts = [evento_nome] if evento_nome else []
    if orario:
        titolo_parts.append(f"Ora: {orario}")
    if canale:
        titolo_parts.append(f"({canale})")
    titolo = " ".join(titolo_parts).strip() or f"Evento {chan_id}"

    print(f"Evento: {titolo} | ID: {chan_id}")

    player_url = urljoin(active_domain, f"/player.php?id={chan_id}")
    p_resp = request_url(player_url)
    if not p_resp or p_resp.status_code >= 400:
        print("  Player non raggiungibile\n")
        continue

    entry, typ = extract_mpd(p_resp.text, titolo)

    if entry:
        entry = entry.replace('group-title="ThisNot 2026"', f'group-title="{competizione}"')
        m3u_lines.append(entry)
        m3u_lines.append("")
        success += 1
        print(f"  OK → {typ}\n")
    else:
        print("  Salto – nessun MPD\n")

    time.sleep(1.1)

with open(M3U_OUTPUT, "w", encoding="utf-8") as f:
    f.write("\n".join(m3u_lines))

print(f"\nFile salvato → {M3U_OUTPUT}")
print(f"Canali MPD aggiunti: {success} / {len(eventi)}")
print("Script configurato per ignorare completamente gli stream HLS (.m3u8).\n")

#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
ThisNot M3U Generator – Solo MPD (DASH) – Marzo 2026
- Solo MPD (.mpd)
- Estrae ck= per ClearKey MA NON lo mette nell'URL MPD
- Fix automatico per flussi Vodafone
- Cerca fino a trovare il ClearKey
"""

import cloudscraper
import re
import base64
import json
from urllib.parse import urljoin, quote, urlparse, urlunparse, parse_qs, urlencode
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
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36",
    "Accept": "application/json, text/plain, */*",
    "Referer": "https://thisnot.business/",
})

USER_AGENT_QUOTED = quote(scraper.headers["User-Agent"])

# ---------------- HELPER FUNCTIONS ----------------
def remove_emoji(text):
    if not text:
        return ""
    emoji_pattern = re.compile(
        "[" u"\U0001F600-\U0001F64F" u"\U0001F300-\U0001F5FF" u"\U0001F680-\U0001F6FF" 
        u"\U0001F1E0-\U0001F1FF" u"\U00002702-\U000027B0" u"\U000024C2-\U0001F251" "]+", 
        flags=re.UNICODE)
    return emoji_pattern.sub(r'', text).strip()


def decode_clear_key(b64_str):
    if not b64_str:
        return None
    try:
        b64_str = b64_str + "=" * ((4 - len(b64_str) % 4) % 4)
        decoded_bytes = base64.b64decode(b64_str, validate=False)
        decoded = decoded_bytes.decode('utf-8', errors='ignore').strip()

        if decoded.startswith('{'):
            d = json.loads(decoded)
            if isinstance(d, dict) and d:
                kid, key = next(iter(d.items()))
                return f"{kid.lower()}:{key.lower()}"

        if ':' in decoded:
            parts = decoded.split(':', 1)
            return f"{parts[0].lower()}:{parts[1].lower()}"

        return None
    except Exception as e:
        print(f"  Errore decode ClearKey: {str(e)}")
        return None


def clean_mpd_url(url):
    if not url:
        return None
    url = re.sub(r'</?iframe.*$', '', url, flags=re.IGNORECASE | re.DOTALL)
    url = url.strip('"\' \t\n\r')
    
    parsed = urlparse(url)
    query_params = parse_qs(parsed.query)
    query_params.pop('ck', None)
    query_params.pop('CK', None)
    
    new_query = urlencode(query_params, doseq=True)
    cleaned_url = urlunparse((
        parsed.scheme, parsed.netloc, parsed.path,
        parsed.params, new_query, parsed.fragment
    ))
    return cleaned_url.rstrip('?&')


def fix_vodafone_mpd(url):
    """Fix automatico per flussi Vodafone - aggiunge .mpd dopo Manifest quando necessario"""
    if not url or "rr.cdn.vodafone.pt" not in url.lower():
        return url

    # Se contiene già /Manifest.mpd → lascia invariato
    if "/Manifest.mpd" in url:
        return url

    # Caso principale: /index.mpd/Manifest?parametri  → diventa /index.mpd/Manifest.mpd?parametri
    if "/Manifest?" in url or url.rstrip("/").endswith("/Manifest"):
        fixed = re.sub(r'/Manifest(\?|$)', r'/Manifest.mpd\1', url, flags=re.IGNORECASE)
        if fixed != url:
            print(f"  → Fix Vodafone applicato (.mpd aggiunto) → {fixed}")
        return fixed

    # Caso fallback che avevi già (per sicurezza)
    if url.rstrip("/").endswith("/index.mpd"):
        fixed = url.rstrip("/") + "/Manifest.mpd?start=LIVE&end=END&device=DASH_AVC_HD"
        print(f"  → Fix Vodafone applicato (Manifest.mpd completo) → {fixed}")
        return fixed

    return url


def build_m3u_entry(mpd_url, clear_key, titolo, competizione):
    lines = [
        f"#EXTINF:-1 tvg-id=\"{titolo.lower().replace(' ', '_')}\" group-title=\"{competizione}\",{titolo}",
        f"#KODIPROP:inputstream.adaptive.stream_headers=User-Agent%3D{USER_AGENT_QUOTED}",
    ]
    if clear_key:
        lines.extend([
            "#KODIPROP:inputstream.adaptive.license_type=clearkey",
            f"#KODIPROP:inputstream.adaptive.license_key={clear_key}",
        ])
    lines.append(mpd_url)
    return "\n".join(lines)


def request_url(url, method="GET", data=None, timeout=15):
    try:
        if method.upper() == "GET":
            r = scraper.get(url, timeout=timeout, allow_redirects=True)
        else:
            r = scraper.post(url, data=data, timeout=timeout, allow_redirects=True)
        print(f"  → {method} {url:<70} → {r.status_code}")
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


# ---------------- ESTRAI MPD (VERSIONE FINALE) ----------------
def extract_mpd(player_html, titolo):
    # PRIORITÀ 1: chrome-extension
    pattern_chrome = r'chrome-extension://opmeopcambhfimffbomjgemehjkbbmji/pages/player\.html#([^#]+)'
    m = re.search(pattern_chrome, player_html, re.IGNORECASE)
    
    if m:
        fragment = m.group(1).strip()
        mpd_match = re.search(r'(https?://[^\s#"]+?\.mpd(?:\?[^\s#"]*)?)', fragment, re.IGNORECASE)
        ck_match = re.search(r'[?&]ck=([A-Za-z0-9+/=_-]+)', fragment, re.IGNORECASE)
        
        if mpd_match:
            raw_url = mpd_match.group(1)
            clean_url = clean_mpd_url(raw_url)
            clean_url = fix_vodafone_mpd(clean_url)
            
            ck_value = ck_match.group(1) if ck_match else None
            clear_key = decode_clear_key(ck_value) if ck_value else None
            
            print(f"  → MPD chrome-extension → {clean_url[:130]}...")
            if clear_key:
                print(f"      └─ ClearKey: {clear_key}")
            
            return build_m3u_entry(clean_url, clear_key, titolo, "ThisNot 2026"), "MPD chrome-extension"
    
    # PRIORITÀ 2: Ricerca generica (continua fino a trovare ck)
    mpd_patterns = [r'(https?://[^\s"\'<>\]]+?\.mpd(?:\?[^\s"\'<>\]]*)?)']
    
    for pat in mpd_patterns:
        matches = re.findall(pat, player_html, re.IGNORECASE)
        for raw_url in matches:
            clean_url = clean_mpd_url(raw_url)
            clean_url = fix_vodafone_mpd(clean_url)
            
            ck_match = re.search(r'(?:ck|clearkey|key)=([A-Za-z0-9+/=_-]+)', player_html, re.IGNORECASE)
            clear_key = decode_clear_key(ck_match.group(1)) if ck_match else None
            
            if clean_url:
                print(f"  → MPD generico trovato → {clean_url[:120]}...")
                if clear_key:
                    print(f"      └─ ClearKey trovato: {clear_key}")
                    return build_m3u_entry(clean_url, clear_key, titolo, "ThisNot 2026"), "MPD generico + ClearKey"
                else:
                    print("      └─ Nessun ClearKey, continuo la ricerca...")
    
    print("  Nessun MPD valido con ClearKey trovato")
    return None, None


# ---------------- MAIN ----------------
print("=== ThisNot – Solo MPD (ck rimosso dall'URL) ===\n")

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
    "# ck= rimosso dall'URL MPD | ClearKey separato | Fix Vodafone automatico",
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

    print(f"\nEvento: {titolo} | ID: {chan_id}")

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
        print("  Salto – nessun MPD con ClearKey\n")

    time.sleep(1.2)

with open(M3U_OUTPUT, "w", encoding="utf-8") as f:
    f.write("\n".join(m3u_lines))

print(f"\nFile salvato → {M3U_OUTPUT}")
print(f"Canali MPD aggiunti: {success} / {len(eventi)}")
print("Script terminato correttamente.\n")

#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
ThisNot M3U Generator da API JSON + MPD con token/ck migliorato – Marzo 2026
- Eventi da /api/eventi.json
- Gestione MPD: priorità al pattern chrome-extension#mpd+ck (con token/key)
- Fallback MPD semplice se non trovato
- HLS con headers come ultima opzione
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
    if not text: return ""
    emoji_pattern = re.compile(
        "["
        u"\U0001F600-\U0001F64F" u"\U0001F300-\U0001F5FF" u"\U0001F680-\U0001F6FF" 
        u"\U0001F1E0-\U0001F1FF" u"\U00002702-\U000027B0" u"\U000024C2-\U0001F251"
        "]+", flags=re.UNICODE)
    return emoji_pattern.sub(r'', text).strip()


def decode_clear_key(b64_str):
    if not b64_str: return None
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


def decode_headers_b64(b64: str) -> dict:
    if not b64: return {}
    try:
        b64 += "==" * ((4 - len(b64) % 4) % 4)
        return json.loads(base64.b64decode(b64).decode("utf-8", errors="ignore"))
    except:
        return {}


def clean_stream_url(url: str) -> str:
    if not url: return ""
    return url.split("&headers=", 1)[0] if "&headers=" in url else url


def build_vlc_opts(hd: dict) -> list:
    opts = []
    ua = hd.get("user-agent") or hd.get("User-Agent")
    if ua: opts.append(f"#EXTVLCOPT:http-user-agent={ua}")
    ref = hd.get("referer") or hd.get("Referer")
    if ref: opts.append(f"#EXTVLCOPT:http-referrer={ref}")
    origin = hd.get("origin") or hd.get("Origin")
    if origin:
        opts.append(f"#EXTVLCOPT:http-origin={origin}")
        opts.append(f"#EXTVLCOPT:http-header=Origin: {origin}")
    return opts


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


# ---------------- ESTRAI STREAM (con gestione token/ck migliorata) ----------------
def extract_stream(player_html, titolo):
    # PRIORITÀ 1: Pattern chrome-extension con MPD + ck= (dal tuo script vecchio)
    pattern_chrome = r'chrome-extension://opmeopcambhfimffbomjgemehjkbbmji/pages/player\.html#(https?://[^#]+)'
    m = re.search(pattern_chrome, player_html, re.IGNORECASE | re.DOTALL)
    
    if m:
        fragment = m.group(1)
        
        # MPD + eventuali query (token, etc.)
        mpd_re = re.search(r'(https?://[^\s&#?]+\.mpd(?:/[^&#?]*)*)', fragment)
        ck_re  = re.search(r'ck=([A-Za-z0-9+/=_-]+)', fragment)
        
        if mpd_re:
            mpd_url = mpd_re.group(1).split('?')[0].rstrip('/')   # base URL
            # Mantieni eventuali ?token=... se presenti (molti MPD usano query per auth)
            full_mpd = mpd_re.group(1)
            
            clear_key = None
            if ck_re:
                clear_key = decode_clear_key(ck_re.group(1))
                print(f"  → ClearKey trovata nel fragment → {clear_key}")
            
            lines = [
                f"#EXTINF:-1 tvg-id=\"{titolo.lower().replace(' ', '_')}\" group-title=\"ThisNot 2026\",{titolo}",
                f"#KODIPROP:inputstream.adaptive.stream_headers=User-Agent%3D{USER_AGENT_QUOTED}",
            ]
            if clear_key:
                lines.extend([
                    "#KODIPROP:inputstream.adaptive.license_type=clearkey",
                    f"#KODIPROP:inputstream.adaptive.license_key={clear_key}",
                ])
            lines.append(full_mpd)  # con token se c'era
            print(f"  → MPD con possibile token → {full_mpd}")
            return "\n".join(lines), "MPD (chrome-pattern)"
    
    # PRIORITÀ 2: MPD semplice ovunque nell'HTML
    mpd_matches = re.findall(r'(https?://[^\s"\'<>?&]+\.mpd(?:/[^\s"\'<>?&]*)?(?:\?[^\s"\'<>]+)?)', player_html)
    if mpd_matches:
        full_mpd = mpd_matches[0]  # prende anche ?token=... se presente
        mpd_base = full_mpd.split('?')[0].rstrip('/')
        
        # Cerca ck= separatamente (a volte è fuori dal #fragment)
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
        lines.append(full_mpd)  # con token/query se c'è
        print(f"  → MPD trovato (con/senza token) → {full_mpd}")
        if clear_key:
            print(f"  → ClearKey associata → {clear_key}")
        return "\n".join(lines), "MPD"
    
    # PRIORITÀ 3: HLS con headers
    hls_pattern = r'(?:chrome-extension://[^#"]+[#"]|player\.html[#"]|src=["\'])(https?://[^"&\s]+?\.m3u8[^"&\s]*)(?:&headers=([A-Za-z0-9+/=]+))?'
    m = re.search(hls_pattern, player_html, re.IGNORECASE | re.DOTALL)
    if m:
        raw = m.group(1)
        b64 = m.group(2)
        url_clean = clean_stream_url(raw)
        hd = decode_headers_b64(b64) if b64 else {}
        opts = build_vlc_opts(hd)
        lines = [f"#EXTINF:-1 tvg-id=\"{titolo.lower().replace(' ', '_')}\" group-title=\"ThisNot 2026\",{titolo} (HLS)"]
        lines.extend(opts)
        lines.append(url_clean)
        return "\n".join(lines), "HLS"
    
    return None, None


# ---------------- MAIN ----------------
print("=== ThisNot Eventi da JSON + MPD token/ck migliorato ===\n")

active_domain = None
for dom in DOMAINS:
    ok, url = attempt_login(dom)
    if ok:
        active_domain = url
        break
    time.sleep(3)

if not active_domain:
    print("Login fallito")
    sys.exit(1)

print(f"Dominio OK → {active_domain}\n")

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
    f"# Generato {time.strftime('%Y-%m-%d %H:%M:%S')} – ThisNot con MPD token/ck",
]

success = 0

for ev in eventi:
    competizione = remove_emoji(ev.get("competizione", "Evento"))
    evento_nome = remove_emoji(ev.get("evento", ""))
    orario = remove_emoji(ev.get("orario", ""))
    canale = remove_emoji(ev.get("canale", ""))
    link = ev.get("link", "")

    id_match = re.search(r'id=([^&]+)', link)
    if not id_match: continue
    chan_id = id_match.group(1)

    titolo_parts = [evento_nome] if evento_nome else []
    if orario: titolo_parts.append(f"Ora: {orario}")
    if canale: titolo_parts.append(f"({canale})")
    titolo = " ".join(titolo_parts).strip() or f"Evento {chan_id}"

    print(f"Evento: {titolo} | ID: {chan_id}")

    player_url = urljoin(active_domain, f"/player.php?id={chan_id}")
    p_resp = request_url(player_url)
    if not p_resp or p_resp.status_code >= 400:
        print("  Player fallito\n")
        continue

    entry, typ = extract_stream(p_resp.text, titolo)

    if entry:
        entry = entry.replace('group-title="ThisNot 2026"', f'group-title="{competizione}"')
        m3u_lines.append(entry)
        m3u_lines.append("")
        success += 1
        print(f"  OK ({typ})\n")
    else:
        print("  Nessun flusso\n")

    time.sleep(1.2)

with open(M3U_OUTPUT, "w", encoding="utf-8") as f:
    f.write("\n".join(m3u_lines))

print(f"\nFile → {M3U_OUTPUT}")
print(f"Aggiunti: {success}/{len(eventi)}")
print("Nota: MPD con token/ck dovrebbe essere gestito meglio ora")

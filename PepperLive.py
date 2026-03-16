# pepperlive_full_m3u8_generator_clean.py
# Genera PepperLive.m3u8 SENZA token ck= nel link MPD
# Chiave solo via #KODIPROP - aggiornato Marzo 2026

import requests
import json
import time
import base64
import urllib.parse
from pathlib import Path
import sys

# =============================================
# CONFIGURAZIONE
# =============================================

BASE_URLS = [
    "https://pepperlive.info",
    "https://www.pepperlive.info",
]

TIMEOUT = 12

POSSIBILI_NOMI = [
    "links.json", "mpd.json", "canali.json", "channels.json",
    "mpd_links.json", "streams.json", "data.json", "config.json",
    "api/links.json", "api/channels.json", "api/mpd.json",
    "assets/links.json", "json/links.json", "player/links.json",
    "live/links.json", "update/links.json", "cdn/links.json",
    "links_v2.json", "links_new.json", "canali_mpd.json",
]

VARIANTI_PATH = ["", "api/", "data/", "assets/", "json/", "cdn/", "update/", "player/", "live/"]

# Rinominazione canali - modifica qui i nomi che preferisci
CANALI_RINOMINA = {
    "SPORTUNO":        "Sky Sport Uno ",
    "SPORTCALCIO":     "Sky Sport Calcio ",
    "SPORTF1":         "Sky Sport F1 ",
    "SPORTTENNIS":     "Sky Sport Tennis ",
    "SPORT251":        "Sky Sport 251 ",
    "Sport_DAZN":      "DAZN Eventi",
    "Dazn1_WARP":      "DAZN Warp (Funzionante Su Determinate Connessioni)",
    "Canale5":         "Canale 5 ",
    "Italia1":         "Italia 1 ",
    "SportTV1":        "Sport TV 1 PT",
    "SportTV2":        "Sport TV 2 PT",
    "SportTV3":        "Sport TV 3 PT",
    "SportTV4":        "Sport TV 4 PT",
    "SportTV5":        "Sport TV 5 PT",
    "Dazn1_PT":        "DAZN 1 PT",
    "Dazn2_PT":        "DAZN 2 PT",
    "Dazn3_PT":        "DAZN 3 PT",
    "Dazn4_PT":        "DAZN 4 PT",
    "TNTSP1":          "TNT Sports 1",
    "TNTSP2":          "TNT Sports 2",
    "NovaSP1":         "Nova Sports 1",
    "NovaSP2":         "Nova Sports 2",
    "BBC1":            "BBC One",
    "ELEVEN1":         "Eleven Sports 1",
    "ELEVEN2":         "Eleven Sports 2",
    "ELEVEN3":         "Eleven Sports 3",
    "ELEVEN4":         "Eleven Sports 4",
    "PRIME":           "Prime Video Sport",
    "LAB1":            "LAB1",
    # Aggiungi altri canali se compaiono
}

OUTPUT_M3U8 = "PepperLive.m3u8"

# =============================================

def extract_kid_key(ck_value: str) -> tuple[str | None, str | None]:
    """ Gestisce entrambi i formati ck= che hai mostrato """
    if not ck_value:
        return None, None

    ck_value = ck_value.strip()

    # Aggiungi padding se necessario
    padded = ck_value
    for extra in ['', '=', '==', '===', '====']:
        try:
            decoded = base64.b64decode(padded + extra)
            break
        except:
            decoded = None

    if decoded is None:
        return None, None

    try:
        decoded_str = decoded.decode('utf-8', errors='ignore').strip()

        # Caso 1: semplice "kid:key"
        if ':' in decoded_str and not decoded_str.startswith('{'):
            parts = decoded_str.split(':', 1)
            kid = parts[0].strip().lower()
            key = parts[1].strip().lower()

        # Caso 2: JSON {"kid":"...","key":"..."} o {"longkid":"longkey"}
        else:
            try:
                data = json.loads(decoded_str)
                if isinstance(data, dict):
                    if "kid" in data and "key" in data:
                        kid = data["kid"].lower().replace('-','').replace('_','')
                        key = data["key"].lower().replace('-','').replace('_','')
                    else:
                        # Singleton dict → primo pair
                        k, v = next(iter(data.items()))
                        kid = k.lower().replace('-','').replace('_','')
                        key = v.lower().replace('-','').replace('_','')
                else:
                    return None, None
            except json.JSONDecodeError:
                return None, None

        # Pulizia finale: solo hex, lunghezza 32
        kid = ''.join(c for c in kid if c in '0123456789abcdef')
        key = ''.join(c for c in key if c in '0123456789abcdef')

        if len(kid) == 32 and len(key) == 32:
            return kid, key
        else:
            return None, None

    except:
        return None, None


def fetch_json(url: str) -> dict | None:
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124.0.0.0",
        "Cache-Control": "no-cache",
        "Pragma": "no-cache",
    }
    try:
        r = requests.get(url, headers=headers, timeout=TIMEOUT, allow_redirects=True)
        if r.status_code == 200 and "json" in r.headers.get("content-type", "").lower():
            return r.json()
        return None
    except:
        return None


def clean_mpd_url(full_url: str) -> str:
    """ Rimuove completamente ?ck=... dal link MPD """
    parsed = urllib.parse.urlparse(full_url)
    if not parsed.query:
        return full_url

    qs = urllib.parse.parse_qs(parsed.query)
    if 'ck' in qs:
        del qs['ck']

    new_query = urllib.parse.urlencode(qs, doseq=True)
    new_url = parsed._replace(query=new_query).geturl()
    return new_url.rstrip('?')


def main():
    print("=== PepperLive M3U8 Generator - LINK PULITI (no ck=) ===\n")

    json_data = None
    found_url = ""

    ts = int(time.time())

    for base in BASE_URLS:
        print(f"Testing base: {base}")
        for nome in POSSIBILI_NOMI:
            for pref in VARIANTI_PATH:
                path = pref + nome
                for q in ["", f"?v={ts}", f"?_={ts}", f"?nocache={ts}"]:
                    url = f"{base.rstrip('/')}/{path.lstrip('/')}{q}"
                    print(f"  → {url}", end=" ... ", flush=True)
                    data = fetch_json(url)
                    if data and isinstance(data, dict) and len(data) > 0:
                        print("TROVATO!")
                        json_data = data
                        found_url = url
                        break
                    print("no")
                if json_data: break
            if json_data: break
        if json_data: break

    if not json_data:
        print("\nNESSUN JSON MPD trovato.")
        print("Controlla manualmente Network tab (F12) e copia URL .json")
        sys.exit(1)

    print(f"\nJSON trovato! ({len(json_data)} canali) da: {found_url}\n")

    # Genera M3U8
    m3u_lines = [
        "#EXTM3U",
        "#EXT-X-VERSION:3",
        "#EXT-X-ALLOW-CACHE:YES",
        "#PLAYLIST:PepperLive MPD - Sky/DAZN/Altri",
        ""
    ]

    count_with_key = 0

    for orig_name, full_url in json_data.items():
        display_name = CANALI_RINOMINA.get(orig_name, orig_name)

        # Link MPD PULITO senza ?ck=
        clean_url = clean_mpd_url(full_url)

        # Estrai chiave dal ck= originale
        parsed = urllib.parse.urlparse(full_url)
        qs = urllib.parse.parse_qs(parsed.query)
        ck = qs.get("ck", [None])[0]

        kid, key = extract_kid_key(ck)

        m3u_lines.append(f'#EXTINF:-1 tvg-id="{orig_name}" group-title="PepperLive MPD", {display_name}')

        if kid and key:
            m3u_lines.append("#KODIPROP:inputstream.adaptive.license_type=clearkey")
            m3u_lines.append(f"#KODIPROP:inputstream.adaptive.license_key={kid}:{key}")
            count_with_key += 1

        m3u_lines.append("#KODIPROP:inputstream.adaptive.stream_headers=User-Agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64)")
        m3u_lines.append(clean_url)
        m3u_lines.append("")

    try:
        with open(OUTPUT_M3U8, "w", encoding="utf-8") as f:
            f.write("\n".join(m3u_lines))
        print(f"\nSUCCESSO! Creato {OUTPUT_M3U8}")
        print(f"  Canali totali: {len(json_data)}")
        print(f"  Con ClearKey valida: {count_with_key}")
        print("  → Link MPD tutti puliti (senza ?ck=)")
        print("Importa in Kodi / Tivimate / IPTV Smarters / GSE IPTV")
    except Exception as e:
        print(f"Errore salvataggio: {e}")

if __name__ == "__main__":
    main()

import base64
import json
import re
import requests
import urllib.parse

# ==============================
# CONFIG
# ==============================

DEFAULT_LOGO = "https://skygo.sky.it/etc/designs/skygo/img/sky-logo@2x.png"
OUTPUT_M3U = "sky.m3u8"

AMSTAFF_URL = "https://test34344.herokuapp.com/filter.php"

PASSWORD = "MandraKodi3"
DEVICE_ID = "2K1WPN"
VERSION = "2.0.0"

USER_AGENT = f"MandraKodi2@@{VERSION}@@{PASSWORD}@@{DEVICE_ID}"

# ==============================
# DATABASE CANALI (invariato - lo lascio per completezza)
# ==============================

CHANNELS_DB = {
    "cinemaaction": {"nome": "Sky Cinema Action", "logo": "https://pixel.disco.nowtv.it/logo/skychb_206_lightnow/LOGO_CHANNEL_DARK/4000?language=it-IT&proposition=NOWOTT", "group": "Sky Cinema"},
    "cinemastories": {"nome": "Sky Cinema Stories", "logo": "https://static.skyassets.com/contentstack/assets/blt4b099fa9cc3801a6/bltc18b20583b1e4d5c/69298d9f7d013486e53a81ee/logo_sky_cinema_stories.png?downsize=640:*&output-format=jpg", "group": "Sky Cinema"},
    "cinemacomedy": {"nome": "Sky Cinema Comedy", "logo": "https://pixel.disco.nowtv.it/logo/skychb_30_lightnow/LOGO_CHANNEL_DARK/4000?language=it-IT&proposition=NOWOTT", "group": "Sky Cinema"},
    "cinemadrama": {"nome": "Sky Cinema Drama", "logo": "https://pixel.disco.nowtv.it/logo/skychb_769_lightnow/LOGO_CHANNEL_DARK/4000?language=it-IT&proposition=NOWOTT", "group": "Sky Cinema"},
    "cinemadue": {"nome": "Sky Cinema Due", "logo": "https://pixel.disco.nowtv.it/logo/skychb_564_lightnow/LOGO_CHANNEL_DARK/4000?language=it-IT&proposition=NOWOTT", "group": "Sky Cinema"},
    "cinemauno": {"nome": "Sky Cinema Uno", "logo": "https://pixel.disco.nowtv.it/logo/skychb_202_lightnow/LOGO_CHANNEL_DARK/4000?language=it-IT&proposition=NOWOTT", "group": "Sky Cinema"},
    "cinemafamily": {"nome": "Sky Cinema Family", "logo": "https://pixel.disco.nowtv.it/logo/skychb_255_lightnow/LOGO_CHANNEL_DARK/4000?language=it-IT&proposition=NOWOTT", "group": "Sky Cinema"},
    "cinemasuspense": {"nome": "Sky Cinema Suspense", "logo": "https://pixel.disco.nowtv.it/logo/skychb_47_lightnow/LOGO_CHANNEL_DARK/4000?language=it-IT&proposition=NOWOTT", "group": "Sky Cinema"},
    "cinemaromance": {"nome": "Sky Cinema Romance", "logo": "https://upload.wikimedia.org/wikipedia/en/thumb/9/91/Sky_Cinema_Romance_-_2021_logo.svg/960px-Sky_Cinema_Romance_-_2021_logo.svg.png", "group": "Sky Cinema"},
    "cinemacollection": {"nome": "Sky Cinema Collection", "logo": "https://pixel.disco.nowtv.it/logo/skychb_204_lightnow/LOGO_CHANNEL_DARK/4000?language=it-IT&proposition=NOWOTT", "group": "Sky Cinema"},


    "sportf1": {"nome": "Sky Sport F1", "logo": "https://pixel.disco.nowtv.it/logo/skychb_478_lightnow/LOGO_CHANNEL_DARK/4000?language=it-IT&proposition=NOWOTT", "group": "Sky Sport"},
    "sport24": {"nome": "Sky Sport 24", "logo": "https://pixel.disco.nowtv.it/logo/skychb_35_lightnow/LOGO_CHANNEL_DARK/4000?language=it-IT&proposition=NOWOTT", "group": "Sky Sport"},
    "sportuno": {"nome": "Sky Sport Uno", "logo": "https://pixel.disco.nowtv.it/logo/skychb_23_lightnow/LOGO_CHANNEL_DARK/4000?language=it-IT&proposition=NOWOTT", "group": "Sky Sport"},
    "sportmotogp": {"nome": "Sky Sport MotoGP", "logo": "https://pixel.disco.nowtv.it/logo/skychb_483_lightnow/LOGO_CHANNEL_DARK/4000?language=it-IT&proposition=NOWOTT", "group": "Sky Sport"},
    "sportcalcio": {"nome": "Sky Sport Calcio", "logo": "https://pixel.disco.nowtv.it/logo/skychb_209_lightnow/LOGO_CHANNEL_DARK/4000?language=it-IT&proposition=NOWOTT", "group": "Sky Sport"},
    "sportbasket": {"nome": "Sky Sport Basket", "logo": "https://pixel.disco.nowtv.it/logo/skychb_764_lightnow/LOGO_CHANNEL_DARK/4000?language=it-IT&proposition=NOWOTT", "group": "Sky Sport"},
    "sportmax": {"nome": "Sky Sport Max", "logo": "https://pixel.disco.nowtv.it/logo/skychb_248_lightnow/LOGO_CHANNEL_DARK/4000?language=it-IT&proposition=NOWOTT", "group": "Sky Sport"},
    "sportmix": {"nome": "Sky Sport Mix", "logo": "https://pixel.disco.nowtv.it/logo/skychb_579_lightnow/LOGO_CHANNEL_DARK/4000?language=it-IT&proposition=NOWOTT", "group": "Sky Sport"},
    "sportarena": {"nome": "Sky Sport Arena", "logo": "https://pixel.disco.nowtv.it/logo/skychb_24_lightnow/LOGO_CHANNEL_DARK/4000?language=it-IT&proposition=NOWOTT", "group": "Sky Sport"},
    "sporttennis": {"nome": "Sky Sport Tennis", "logo": "https://pixel.disco.nowtv.it/logo/skychb_559_lightnow/LOGO_CHANNEL_DARK/4000?language=it-IT&proposition=NOWOTT", "group": "Sky Sport"},
    "sportlegend": {"nome": "Sky Sport Legend", "logo": "https://pixel.disco.nowtv.it/logo/skychb_578_lightnow/LOGO_CHANNEL_DARK/4000?language=it-IT&proposition=NOWOTT", "group": "Sky Sport"},
    "sportgolf": {"nome": "Sky Sport Golf", "logo": "https://pixel.disco.nowtv.it/logo/skychb_768_lightnow/LOGO_CHANNEL_DARK/4000?language=it-IT&proposition=NOWOTT", "group": "Sky Sport"},
    "sport251": {"nome": "Sky Sport 251", "logo": "https://pixel.disco.nowtv.it/logo/skychb_917_lightnow/LOGO_CHANNEL_DARK/4000?language=it-IT&proposition=NOWOTT", "group": "Sky Sport"},
    "sport252": {"nome": "Sky Sport 252", "logo": "https://pixel.disco.nowtv.it/logo/skychb_951_lightnow/LOGO_CHANNEL_DARK/4000?language=it-IT&proposition=NOWOTT", "group": "Sky Sport"},
    "sport253": {"nome": "Sky Sport 253", "logo": "https://pixel.disco.nowtv.it/logo/skychb_233_lightnow/LOGO_CHANNEL_DARK/4000?language=it-IT&proposition=NOWOTT", "group": "Sky Sport"},
    "sport254": {"nome": "Sky Sport 254", "logo": "https://pixel.disco.nowtv.it/logo/skychb_234_lightnow/LOGO_CHANNEL_DARK/4000?language=it-IT&proposition=NOWOTT", "group": "Sky Sport"},
    "sport255": {"nome": "Sky Sport 255", "logo": "https://pixel.disco.nowtv.it/logo/skychb_910_lightnow/LOGO_CHANNEL_DARK/4000?language=it-IT&proposition=NOWOTT", "group": "Sky Sport"},
    "sport256": {"nome": "Sky Sport 256", "logo": "https://pixel.disco.nowtv.it/logo/skychb_912_lightnow/LOGO_CHANNEL_DARK/4000?language=it-IT&proposition=NOWOTT", "group": "Sky Sport"},
    "sport257": {"nome": "Sky Sport 257", "logo": "https://pixel.disco.nowtv.it/logo/skychb_775_lightnow/LOGO_CHANNEL_DARK/4000?language=it-IT&proposition=NOWOTT", "group": "Sky Sport"},
    "sport258": {"nome": "Sky Sport 258", "logo": "https://pixel.disco.nowtv.it/logo/skychb_912_lightnow/LOGO_CHANNEL_DARK/4000?language=it-IT&proposition=NOWOTT", "group": "Sky Sport"},
    "sport259": {"nome": "Sky Sport 259", "logo": "https://pixel.disco.nowtv.it/logo/skychb_613_lightnow/LOGO_CHANNEL_DARK/4000?language=it-IT&proposition=NOWOTT", "group": "Sky Sport"},
    "dazn": {"nome": "Dazn 1", "logo": "https://upload.wikimedia.org/wikipedia/commons/e/e3/Tv-channel-%E2%94%82-dazn-1.png", "group": "Sky Sport"},
    


    "uno": {"nome": "Sky Uno", "logo": "https://pixel.disco.nowtv.it/logo/skychb_477_lightnow/LOGO_CHANNEL_DARK/4000?language=it-IT&proposition=NOWOTT", "group": "Sky Intrattenimento"},
    "unoplus": {"nome": "Sky Uno", "logo": "https://pixel.disco.nowtv.it/logo/skychb_477_lightnow/LOGO_CHANNEL_DARK/4000?language=it-IT&proposition=NOWOTT", "group": "Sky Intrattenimento"},
    "atlantic": {"nome": "Sky Atlantic", "logo": "https://pixel.disco.nowtv.it/logo/skychb_226_lightnow/LOGO_CHANNEL_DARK/4000?language=it-IT&proposition=NOWOTT", "group": "Sky Intrattenimento"},
    "serie": {"nome": "Sky Serie", "logo": "https://pixel.disco.nowtv.it/logo/skychb_684_lightnow/LOGO_CHANNEL_DARK/4000?language=it-IT&proposition=NOWOTT", "group": "Sky Intrattenimento"},
    "crime": {"nome": "Sky Crime", "logo": "https://pixel.disco.nowtv.it/logo/skychb_249_lightnow/LOGO_CHANNEL_DARK/4000?language=it-IT&proposition=NOWOTT", "group": "Sky Intrattenimento"},
    "investigation": {"nome": "Sky Investigation", "logo": "https://pixel.disco.nowtv.it/logo/skychb_686_lightnow/LOGO_CHANNEL_DARK/4000?language=it-IT&proposition=NOWOTT", "group": "Sky Intrattenimento"},
    "nature": {"nome": "Sky Nature", "logo": "https://pixel.disco.nowtv.it/logo/skychb_695_lightnow/LOGO_CHANNEL_DARK/4000?language=it-IT&proposition=NOWOTT", "group": "Sky Intrattenimento"},
    "documentaries": {"nome": "Sky Documentaries", "logo": "https://pixel.disco.nowtv.it/logo/skychb_697_lightnow/LOGO_CHANNEL_DARK/4000?language=it-IT&proposition=NOWOTT", "group": "Sky Intrattenimento"},
    "adventure": {"nome": "Sky Adventure", "logo": "https://pixel.disco.nowtv.it/logo/skychb_961_lightnow/LOGO_CHANNEL_DARK/4000?language=it-IT&proposition=NOWOTT", "group": "Sky Intrattenimento"},
    "collection": {"nome": "Sky Collection", "logo": "https://images.contentstack.io/v3/assets/blt4b099fa9cc3801a6/blt6210e5c9e5633b2c/69088303a15f04806ab5deed/logo_sky_collection.png", "group": "Sky Intrattenimento"},
    "comedycentral": {"nome": "Comedy Central", "logo": "https://pixel.disco.nowtv.it/logo/skychb_404_lightnow/LOGO_CHANNEL_DARK/4000?language=it-IT&proposition=NOWOTT", "group": "Sky Intrattenimento"},
    "history": {"nome": "History Channel", "logo": "https://pixel.disco.nowtv.it/logo/skychb_513_lightnow/LOGO_CHANNEL_DARK/4000?language=it-IT&proposition=NOWOTT", "group": "Sky Intrattenimento"},
    "arte": {"nome": "Sky Arte", "logo": "https://pixel.disco.nowtv.it/logo/skychb_74_lightnow/LOGO_CHANNEL_DARK/4000?language=it-IT&proposition=NOWOTT", "group": "Sky Intrattenimento"},
    "mtv": {"nome": "MTV", "logo": "https://pixel.disco.nowtv.it/logo/skychb_763_lightnow/LOGO_CHANNEL_DARK/4000?language=it-IT&proposition=NOWOTT", "group": "Sky Intrattenimento"},
    "tg24": {"nome": "Sky TG24", "logo": "https://pixel.disco.nowtv.it/logo/skychb_519_lightnow/LOGO_CHANNEL_DARK/4000?language=it-IT&proposition=NOWOTT", "group": "Sky Intrattenimento"},


    "cartoonnetwork": {"nome": "Cartoon Network", "logo": "https://raw.githubusercontent.com/tv-logo/tv-logos/main/countries/italy/cartoon-network-it.png", "group": "Sky Bambini"},
    "nickjr": {"nome": "Nick Junior", "logo": "https://raw.githubusercontent.com/tv-logo/tv-logos/main/countries/italy/nick-jr-it.png", "group": "Sky Bambini"},
    "boomerang": {"nome": "Boomerang", "logo": "https://raw.githubusercontent.com/tv-logo/tv-logos/main/countries/italy/boomerang-it.png", "group": "Sky Bambini"},
    "nickelodeon": {"nome": "Nickelodeon", "logo": "https://raw.githubusercontent.com/tv-logo/tv-logos/main/countries/italy/nickelodeon-it.png", "group": "Sky Bambini"},
    "mrbean": {"nome": "Mr Bean Channel", "logo": "https://i.postimg.cc/rmwVGQNn/Mr-Bean-29-logo-svg.png", "group": "Sky Bambini"},
    "deakids": {"nome": "Deakids", "logo": "https://raw.githubusercontent.com/tv-logo/tv-logos/main/countries/italy/dea-kids-it.png", "group": "Sky Bambini"}

}

# ==============================
# UTILS
# ==============================

def clean_m3u_text(text):
    if not text: return ""
    text = re.sub(r"\[/?COLOR[^\]]*\]", "", text, flags=re.IGNORECASE)
    return re.sub(r"\s+", " ", text).strip()

def normalize(text):
    if not text: return ""
    return re.sub(r"[^a-z0-9]", "", text.lower())

def match_channel(title):
    key = normalize(title)
    for k, v in CHANNELS_DB.items():
        if k in key or normalize(v["nome"]) in key:
            return v
    return None

# ==============================
# DECODE AMSTAFF - VERSIONE ADATTATA AL TUO SERVER ATTUALE
# ==============================

def decode_amstaff(myresolve):
    if not myresolve or not myresolve.strip():
        return None, None, None

    raw = myresolve.strip()
    # print(f"  [RAW] {raw[:140]}{'...' if len(raw)>140 else ''}")

    # Rimuovi prefisso amstaff@@ se presente
    if raw.lower().startswith("amstaff@@"):
        content = raw[9:].strip()
    else:
        content = raw

    # Decodifica URL encoding (per sicurezza, anche se nel tuo caso non sembra encoded)
    content = urllib.parse.unquote(content)

    # Caso 1: è base64 valido → decodifica e split |kid:key
    try:
        padded = content + "=" * (-len(content) % 4)
        decoded_bytes = base64.b64decode(padded, validate=True)
        try:
            text = decoded_bytes.decode('utf-8')
        except UnicodeDecodeError:
            text = decoded_bytes.hex()

        if "|" in text:
            url, rest = text.split("|", 1)
            url = url.strip()
            if ":" in rest:
                kid, key = rest.rsplit(":", 1)
                return url, kid.strip(), key.strip()
            return url, None, None
        # se no | → forse solo url base64-encoded
        if text.startswith("http"):
            return text, None, None

    except Exception:
        # NON è base64 → probabilmente è direttamente URL|kid:key o solo URL
        pass

    # Caso 2: formato "rotto" attuale del server: direttamente URL (a volte con |kid:key attaccato)
    if "|" in content:
        parts = content.split("|", 1)
        url = parts[0].strip()
        if len(parts) > 1:
            rest = parts[1].split("&")[0].split("?")[0].strip()  # pulisci sporcizia finale
            if ":" in rest:
                try:
                    kid, key = rest.split(":", 1)
                    return url, kid.strip(), key.strip()
                except:
                    pass
        return url, None, None

    # Caso 3: sembra solo URL MPD / m3u8
    if content.startswith("http") and (".mpd" in content or ".m3u8" in content):
        return content, None, None

    # Fallimento
    # print("  [FALLITO]", content[:80])
    return None, None, None

# ==============================
# FETCH + WALK (invariato)
# ==============================

def fetch_amstaff_channels():
    print(f"\n=== Tentativo connessione ===\nURL: {AMSTAFF_URL}")
    try:
        r = requests.get(
            AMSTAFF_URL,
            headers={"User-Agent": USER_AGENT},
            params={"numTest": "A1A260"},
            timeout=15
        )
        print(f"Status code: {r.status_code} | Lunghezza: {len(r.text)}")

        if r.status_code != 200:
            return []

        text = r.text.strip()
        try:
            data = json.loads(text)
        except:
            print("JSON non valido")
            return []

        found = []
        def walk(o):
            if isinstance(o, dict):
                if "title" in o and "myresolve" in o:
                    found.append((o["title"].strip(), o["myresolve"].strip()))
                for v in o.values():
                    walk(v)
            elif isinstance(o, list):
                for i in o:
                    walk(i)
        walk(data)
        print(f"Trovati {len(found)} canali nel JSON\n")
        return found

    except Exception as e:
        print(f"Errore richiesta: {e}")
        return []

# ==============================
# M3U
# ==============================

def generate_m3u(channels):
    if not channels:
        print("NESSUN CANALE TROVATO")
        return

    print(f"=== INIZIO GENERAZIONE M3U ({len(channels)} canali) ===\n")
    m3u = "#EXTM3U x-tvg-url=\"\"\n\n"
    count = 0

    for i, (title, myresolve) in enumerate(channels, 1):
        title_clean = clean_m3u_text(title)
        print(f"{i:2d}) {title_clean}")

        url, kid, key = decode_amstaff(myresolve)

        if not url or not url.startswith("http"):
            print("   → FALLITO: nessun URL valido estratto\n")
            continue

        meta = match_channel(title_clean)
        name = meta["nome"] if meta else title_clean or "Unknown"
        logo = meta["logo"] if meta else DEFAULT_LOGO
        group = meta["group"] if meta else "Sky / Altro"

        tvg_id = normalize(name)

        m3u += f'#EXTINF:-1 tvg-id="{tvg_id}" tvg-logo="{logo}" group-title="{group}",{name}\n'

        if kid and key and len(key) > 20:  # filtro anti-0000
            m3u += '#KODIPROP:inputstream.adaptive.license_type=clearkey\n'
            m3u += f'#KODIPROP:inputstream.adaptive.license_key={kid}:{key}\n'
            print(f"   → CLEARK EY: {kid[:8]}...:{key[:8]}...")
        else:
            print("   → Nessuna chiave valida (canale forse in chiaro o kid/key vuoti)")

        m3u += f"{url}\n\n"
        print(f"   URL: {url[:100]}{'...' if len(url)>100 else ''}\n")
        count += 1

    with open(OUTPUT_M3U, "w", encoding="utf-8") as f:
        f.write(m3u)

    print(f"=== COMPLETATO ===\nCanali scritti: {count}/{len(channels)}\nFile: {OUTPUT_M3U} ✓")

# ==============================
# MAIN
# ==============================

if __name__ == "__main__":
    print("=== MANDRAKODI SKY IPTV - FIX FORMATO SERVER ATTUALE ===\n")
    channels = fetch_amstaff_channels()
    generate_m3u(channels)
    print("\n=== FINE ===\n")

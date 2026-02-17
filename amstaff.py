import base64
import json
import re
import requests

# ==============================
# CONFIG
# ==============================

DEBUG = True
DEFAULT_LOGO = "https://viverediturismofestival.it/wp-content/uploads/2025/10/Sponsor-piccolopartner-2025-10-24T180159.016.png"
OUTPUT_M3U = "sport_lastminute.m3u8"
HOME_URL = "https://test34344.herokuapp.com/filter.php"
PASSWORD = "MandraKodi3"
DEVICE_ID = "2K1WPN"
VERSION = "2.0.0"
USER_AGENT = f"MandraKodi2@@{VERSION}@@{PASSWORD}@@{DEVICE_ID}"

# ==============================
# LOGGER
# ==============================

def log(msg, level="INFO"):
    if DEBUG:
        print(f"[{level}] {msg}")

# ==============================
# UTILITY
# ==============================

def clean_title(t):
    return re.sub(r"\[/?[A-Z]+[^\]]*\]", "", t, flags=re.IGNORECASE).strip()

# =====================================================
# DECODER AMSTAFF RAW - versione permissiva
# =====================================================

def decode_amstaff_raw(encoded):
    log("Tentativo decode AMSTAFF", "AMSTAFF")
    
    prefixes = [
        "amstaff@@", "amstaffd@@", "amstaf@@", "mstf@@",
        "https://amstaff@@", "http://amstaff@@",
        "amstaff:https://", "amstaffd:https://"
    ]
    
    original = encoded
    for p in prefixes:
        if encoded.lower().startswith(p):
            encoded = encoded[len(p):].lstrip()
            log(f"Rimosso prefisso: {p}", "STRIP")
            break

    encoded = encoded.replace("\n", "").replace("\r", "").strip()
    
    # Caso pipe: url|kid:key   (accetta anche 0000)
    if "|" in encoded:
        try:
            url_part, key_part = encoded.rsplit("|", 1)
            url = url_part.strip()
            key_part = key_part.strip()
            
            if url.startswith(("http://", "https://")):
                if ":" in key_part:
                    key_id, key = key_part.split(":", 1)
                    key_id = key_id.strip()
                    key = key.strip()
                else:
                    key_id = ""
                    key = key_part.strip()
                
                log(f"AMSTAFF OK (pipe) → {url}  key={key[:12]}{'...' if len(key)>12 else ''}", "OK")
                return {
                    "type": "amstaff",
                    "url": url,
                    "key_id": key_id,
                    "key": key
                }
        except Exception as e:
            log(f"Errore parsing pipe: {e}", "ERROR")

    # Fallback base64
    attempts = []

    def try_decode(s):
        try:
            s_clean = re.sub(r"[^A-Za-z0-9+/=]", "", s)
            missing = len(s_clean) % 4
            if missing:
                s_clean += "=" * (4 - missing)
            d = base64.b64decode(s_clean).decode("utf-8", "ignore").strip()
            if d:
                attempts.append(d)
        except:
            pass

    try_decode(encoded)
    try_decode(original)

    if attempts:
        decoded = attempts[0]
        if "##" in decoded:
            decoded = decoded.split("##")[0].strip()

        if "|" in decoded:
            try:
                url, rest = decoded.split("|", 1)
                if ":" in rest:
                    kid, key = rest.split(":", 1)
                    log(f"AMSTAFF base64+pipe OK → {url}", "OK")
                    return {
                        "type": "amstaff",
                        "url": url.strip(),
                        "key_id": kid.strip(),
                        "key": key.strip()
                    }
            except:
                pass

    log("Formato AMSTAFF non riconosciuto", "DROP")
    return None

# =====================================================
# UNIVERSAL STREAM DECODER
# =====================================================

def decode_stream(value):
    if not value:
        log("Resolve vuoto", "DROP")
        return None
    
    value = value.strip()
    log(f"Decodifica → {value[:120]}{'...' if len(value)>120 else ''}", "DECODE")

    if value.lower().startswith("freeshot@@"):
        log("Freeshot ignorato", "DROP")
        return None

    # Prova AMSTAFF per primo
    amstaff = decode_amstaff_raw(value)
    if amstaff:
        return amstaff

    # URL diretto semplice
    if value.startswith(("http://", "https://")):
        key_id = re.search(r"key_id=([A-Za-z0-9-_]+)", value)
        key = re.search(r"key=([A-Za-z0-9-_/=]+)", value)
        return {
            "type": "direct",
            "url": value,
            "key_id": key_id.group(1) if key_id else "",
            "key": key.group(1) if key else ""
        }

    log("Nessun decoder applicabile", "DROP")
    return None

# =====================================================
# KODI PROPERTIES
# =====================================================

def build_kodi_props(stream):
    props = []
    url = stream.get("url", "").lower()

    if ".mpd" in url:
        props.append("#KODIPROP:inputstream.adaptive.manifest_type=mpd")
    elif ".m3u8" in url:
        props.append("#KODIPROP:inputstream.adaptive.manifest_type=hls")

    key_id = stream.get("key_id", "").strip()
    key = stream.get("key", "").strip()

    if key_id and key:
        props.append("#KODIPROP:inputstream.adaptive.license_type=clearkey")
        props.append(f"#KODIPROP:inputstream.adaptive.license_key={key_id}:{key}")

    return props

# =====================================================
# JSON PARSER
# =====================================================

def extract_channels(obj, out):
    if isinstance(obj, dict):
        if "title" in obj and "myresolve" in obj:
            title = clean_title(obj["title"])
            resolve = obj["myresolve"]
            log(f"Canale → {title}", "FOUND")
            out.append({"title": title, "resolve": resolve})
        for v in obj.values():
            extract_channels(v, out)
    elif isinstance(obj, list):
        for item in obj:
            extract_channels(item, out)
    return out

def find_category_link(data, name):
    name = name.upper()
    found = None
    def search(x):
        nonlocal found
        if found: return
        if isinstance(x, dict):
            if name in x.get("title", "").upper() and "externallink" in x:
                found = x["externallink"]
                return
            for v in x.values():
                search(v)
        elif isinstance(x, list):
            for i in x:
                search(i)
    search(data)
    return found

# =====================================================
# FETCH CHANNELS
# =====================================================

def fetch_amstaff_channels():
    headers = {"User-Agent": USER_AGENT}
    try:
        home = requests.get(HOME_URL, headers=headers, timeout=15).json()
        sport = find_category_link(home, "SPORT")
        if not sport: return []
        sport_json = requests.get(sport, headers=headers, timeout=15).json()
        last = find_category_link(sport_json, "LAST MINUTE")
        if not last: return []
        last_json = requests.get(last, headers=headers, timeout=15).json()
    except Exception as e:
        log(f"Errore fetch: {e}", "ERROR")
        return []

    raw_channels = extract_channels(last_json, [])
    log(f"Trovati {len(raw_channels)} canali grezzi", "STATS")

    final = []
    for ch in raw_channels:
        decoded = decode_stream(ch["resolve"])
        if decoded:
            decoded["title"] = ch["title"]
            final.append(decoded)
    
    log(f"Decodificati con successo: {len(final)}", "STATS")
    return final

# =====================================================
# PULIZIA - NESSUNA DEDUPLICA (tutti i canali vengono tenuti)
# =====================================================

def clean_and_dedup_channels(channels):
    log(f"Nessuna deduplica applicata → mantenuti tutti i {len(channels)} canali (anche duplicati)", "INFO")
    return channels

# =====================================================
# GENERA M3U - forza 0000 quando placeholder
# =====================================================

def generate_m3u(channels):
    m3u = "#EXTM3U\n\n"

    for ch in channels:
        title = ch["title"]
        url = ch.get("url", "")
        key_id = ch.get("key_id", "").strip()
        key = ch.get("key", "").strip()

        tvg_id = re.sub(r"[^A-Za-z0-9]", "", title).lower()

        # Placeholder → forziamo 0000
        if not key or key in ("0000", "0", "") or len(key) <= 8:
            key = "0000"
            if not key_id:
                key_id = "00000000000000000000000000000000"

        props = build_kodi_props(ch)

        # Override per 0000
        if key == "0000":
            props = [p for p in props if "license_key" not in p and "license_type" not in p]
            props.append("#KODIPROP:inputstream.adaptive.license_type=clearkey")
            props.append("#KODIPROP:inputstream.adaptive.license_key=0000")

        m3u += f'#EXTINF:-1 tvg-id="{tvg_id}" tvg-logo="{DEFAULT_LOGO}" group-title="LAST MINUTE",{title}\n'
        for p in props:
            m3u += p + "\n"
        m3u += url + "\n\n"

    with open(OUTPUT_M3U, "w", encoding="utf-8") as f:
        f.write(m3u)

    log(f"Playlist generata: {OUTPUT_M3U}  ({len(channels)} canali)", "DONE")

# =====================================================
# MAIN
# =====================================================

if __name__ == "__main__":
    channels = fetch_amstaff_channels()
    if channels:
        cleaned = clean_and_dedup_channels(channels)  # ora ritorna tutti
        generate_m3u(cleaned)
    else:
        log("Nessun canale recuperato", "FAIL")

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
# DECODER AMSTAFF RAW - SUPER PERMISSIVO
# =====================================================

def decode_amstaff_raw(encoded):
    log("Tentativo decode AMSTAFF", "AMSTAFF")

    prefixes = ["amstaff@@", "amstaffd@@", "amstaf@@", "mstf@@"]
    
    encoded = encoded.replace("\n", "").replace("\r", "").strip()
    
    prefix_found = None
    for p in prefixes:
        if encoded.lower().startswith(p):
            prefix_found = p
            encoded = encoded[len(p):].strip()
            break

    if not prefix_found:
        log("Non inizia con prefisso AMSTAFF", "SKIP")
        return None

    url = ""
    key_id = ""
    key = ""

    if "|" in encoded:
        url_part, key_part = encoded.split("|", 1)
        url = url_part.strip()
        key_part = key_part.strip()

        url = re.sub(r'^https?://+', 'https://', url)
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url.lstrip('/')

        if ":" in key_part:
            try:
                key_id, key = key_part.split(":", 1)
                key_id = key_id.strip()
                key = key.strip()
            except:
                key_id = key_part.strip()
        else:
            key_id = key_part.strip() if key_part else ""
    else:
        url = encoded.strip()
        url = re.sub(r'^https?://+', 'https://', url)
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url.lstrip('/')

    if url and url.startswith("http"):
        log(f"AMSTAFF ACCEPTATO → {url}  kid={key_id} key={key}", "OK")
        return {
            "type": "amstaff",
            "url": url,
            "key_id": key_id,
            "key": key
        }

    log("AMSTAFF fallito", "DROP")
    return None

# =====================================================
# UNIVERSAL STREAM DECODER
# =====================================================

def decode_stream(value):
    if not value:
        log("Resolve vuoto", "DROP")
        return None

    value = value.strip()
    log(f"Decodifica → {value}", "DECODE")

    # AMSTAFF
    if any(value.lower().startswith(p) for p in ["amstaff@@", "amstaffd@@", "amstaf@@", "mstf@@"]):
        amstaff = decode_amstaff_raw(value)
        if amstaff:
            return amstaff

    # DAZN
    if value.lower().startswith("dazntoken@@"):
        log("Tipo DAZN", "TYPE")
        try:
            b64 = value.split("@@")[1]
            missing = len(b64) % 4
            if missing:
                b64 += "=" * (4 - missing)
            decoded = base64.b64decode(b64).decode("utf-8", "ignore")
            parts = decoded.split("|")
            if len(parts) >= 2:
                url = parts[0]
                token = parts[-1]
                key_id, key = ("", "")
                if len(parts) == 3 and ":" in parts[1]:
                    key_id, key = parts[1].split(":", 1)
                log(f"DAZN OK → {url}", "OK")
                return {
                    "type": "dazn",
                    "url": url,
                    "key_id": key_id,
                    "key": key,
                    "token": token
                }
        except:
            log("DAZN decode fallito", "DROP")
            return None

    # URL diretto
    if value.startswith("http"):
        log(f"URL diretto → {value}", "OK")
        return extract_from_url(value)

    if ".mpd" in value or ".m3u8" in value:
        url = value if value.startswith("http") else "https://" + value
        log(f"Manifest diretto → {url}", "OK")
        return extract_from_url(url)

    log("Nessun decoder valido", "DROP")
    return None

def extract_from_url(url):
    key_id = ""
    key = ""
    m1 = re.search(r"key_id=([A-Za-z0-9-_]+)", url)
    m2 = re.search(r"key=([A-Za-z0-9-_/=]+)", url)
    if m1: key_id = m1.group(1)
    if m2: key = m2.group(1)
    return {"type": "direct", "url": url, "key_id": key_id, "key": key}

# =====================================================
# KODI PROPERTY BUILDER
# =====================================================

def build_kodi_props(stream):
    props = []
    url_lower = stream["url"].lower()

    if ".mpd" in url_lower:
        props.append("#KODIPROP:inputstream.adaptive.manifest_type=mpd")
    elif ".m3u8" in url_lower:
        props.append("#KODIPROP:inputstream.adaptive.manifest_type=hls")

    if stream.get("key_id") and stream.get("key"):
        props.append("#KODIPROP:inputstream.adaptive.license_type=clearkey")
        props.append(f"#KODIPROP:inputstream.adaptive.license_key={stream['key_id']}:{stream['key']}")

    if stream.get("type") == "dazn" and stream.get("token"):
        header = (
            f"dazn-token={stream['token']}"
            "&user-agent=Mozilla/5.0"
            "&referer=https://www.dazn.com/"
            "&origin=https://www.dazn.com"
        )
        props.append(f"#KODIPROP:inputstream.adaptive.stream_headers={header}")

    return props

# =====================================================
# JSON PARSER
# =====================================================

def extract_channels(obj, out):
    if isinstance(obj, dict):
        if "title" in obj and "myresolve" in obj:
            title = clean_title(obj["title"])
            resolve = obj["myresolve"]
            log(f"Canale trovato → {title}", "FOUND")
            out.append({"title": title, "resolve": resolve})
        for v in obj.values():
            extract_channels(v, out)
    elif isinstance(obj, list):
        for i in obj:
            extract_channels(i, out)
    return out

def find_category_link(data, name):
    name = name.upper()
    found = None

    def search(x):
        nonlocal found
        if found:
            return
        if isinstance(x, dict):
            if name in x.get("title", "").upper() and "externallink" in x:
                found = x["externallink"]
                log(f"Categoria '{name}' → {found}", "OK")
                return
            for v in x.values():
                search(v)
        elif isinstance(x, list):
            for i in x:
                search(i)

    log(f"Cerco categoria {name}", "SEARCH")
    search(data)
    return found

# =====================================================
# FETCH
# =====================================================

def fetch_amstaff_channels():
    headers = {"User-Agent": USER_AGENT}

    try:
        home = requests.get(HOME_URL, headers=headers, timeout=15).json()
    except Exception as e:
        log(f"Errore fetch home: {e}", "ERROR")
        return []

    sport = find_category_link(home, "SPORT")
    if not sport:
        log("Categoria SPORT non trovata", "DROP")
        return []

    try:
        sport_json = requests.get(sport, headers=headers, timeout=15).json()
    except:
        log("Errore fetch SPORT", "ERROR")
        return []

    last = find_category_link(sport_json, "LAST MINUTE")
    if not last:
        log("Categoria LAST MINUTE non trovata", "DROP")
        return []

    try:
        last_json = requests.get(last, headers=headers, timeout=15).json()
    except:
        log("Errore fetch LAST MINUTE", "ERROR")
        return []

    raw = extract_channels(last_json, [])
    log(f"Canali grezzi trovati: {len(raw)}", "STATS")

    final = []
    for ch in raw:
        decoded = decode_stream(ch["resolve"])
        if not decoded:
            log(f"SCARTATO → {ch['title']}", "DROP")
            continue
        decoded["title"] = ch["title"]
        final.append(decoded)
        log(f"ACCETTATO → {ch['title']} ({decoded.get('type', 'unknown')})", "OK")

    log(f"Canali validi finali: {len(final)}", "STATS")
    return final

# =====================================================
# M3U GENERATOR + PULIZIA SELETTIVA
# =====================================================

def generate_m3u(channels):
    m3u_lines = ["#EXTM3U\n"]

    for ch in channels:
        props = build_kodi_props(ch)
        tvg_id = re.sub(r"[^A-Za-z0-9]", "", ch["title"]).lower()
        m3u_lines.append(f'#EXTINF:-1 tvg-id="{tvg_id}" tvg-logo="{DEFAULT_LOGO}" group-title="LAST MINUTE",{ch["title"]}\n')
        for p in props:
            m3u_lines.append(p + "\n")
        m3u_lines.append(ch["url"] + "\n\n")

    with open(OUTPUT_M3U, "w", encoding="utf-8") as f:
        f.writelines(m3u_lines)

    log(f"Playlist generata → {OUTPUT_M3U} ({len(channels)} canali)", "DONE")

    # Pulizia selettiva SOLO su linee con prefissi residui
    try:
        with open(OUTPUT_M3U, "r", encoding="utf-8") as f:
            lines = f.readlines()

        cleaned_lines = []
        cleaned = 0

        for line in lines:
            stripped = line.strip()
            if stripped.startswith("http") and re.search(r'(amstaff@@|amstaffd@@|amstaf@@|mstf@@)', stripped, re.IGNORECASE):
                cleaned_url = re.sub(r'(https?://)?(?:amstaff@@|amstaffd@@|amstaf@@|mstf@@)', '', stripped, flags=re.IGNORECASE)
                cleaned_url = re.sub(r'(https?://)+', 'https://', cleaned_url)
                if not cleaned_url.startswith(('http://', 'https://')):
                    cleaned_url = 'https://' + cleaned_url.lstrip('/')
                log(f"Pulito residuo → {stripped[:100]}... → {cleaned_url[:100]}...", "CLEAN")
                cleaned_lines.append(cleaned_url + "\n")
                cleaned += 1
            else:
                cleaned_lines.append(line)

        with open(OUTPUT_M3U, "w", encoding="utf-8") as f:
            f.writelines(cleaned_lines)

        log(f"Ripulizia selettiva: {cleaned} flussi corretti", "DONE")
    except Exception as e:
        log(f"Errore pulizia: {e}", "ERROR")

# =====================================================
# MAIN
# =====================================================

if __name__ == "__main__":
    channels = fetch_amstaff_channels()
    if channels:
        generate_m3u(channels)
    else:
        log("Nessun canale trovato o errore durante il recupero", "FAIL")

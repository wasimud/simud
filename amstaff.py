import base64
import json
import re
import requests

# ==============================
# CONFIG
# ==============================

DEBUG = True

DEFAULT_LOGO = "https://toppng.com/uploads/preview/3790038-logo-vetrina-dazn-sport-dazn-a-11563364038i3yzrattgk.png"
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
# DECODER AMSTAFF RAW
# =====================================================

def decode_amstaff_raw(encoded):
    log("Tentativo decode AMSTAFF", "AMSTAFF")

    prefixes = ["amstaff@@", "amstaffd@@", "amstaf@@", "mstf@@"]
    for p in prefixes:
        if encoded.lower().startswith(p):
            encoded = encoded[len(p):]

    encoded = encoded.replace("\n", "").replace("\r", "")
    attempts = []

    def try_decode(s):
        try:
            missing = len(s) % 4
            if missing:
                s += "=" * (4 - missing)
            d = base64.b64decode(s).decode("utf-8", "ignore")
            if d:
                attempts.append(d)
        except:
            pass

    try_decode(encoded)
    try_decode(re.sub(r"[^A-Za-z0-9+/=]", "", encoded))

    if not attempts:
        log("Decode AMSTAFF fallito", "DROP")
        return None

    decoded = attempts[0]

    if "##" in decoded:
        decoded = decoded.split("##")[0]

    if "|" in decoded and ":" in decoded:
        url, rest = decoded.split("|", 1)
        key_id, key = rest.split(":", 1)
        log(f"AMSTAFF OK → {url}", "OK")
        return {"type": "amstaff", "url": url, "key_id": key_id, "key": key}

    if "key_id=" in decoded and "key=" in decoded:
        url = decoded.split("|")[0]
        kid = re.search(r"key_id=([A-Za-z0-9-_]+)", decoded).group(1)
        key = re.search(r"key=([A-Za-z0-9-_/=]+)", decoded).group(1)
        log(f"AMSTAFF OK (query) → {url}", "OK")
        return {"type": "amstaff", "url": url, "key_id": kid, "key": key}

    log("AMSTAFF decodificato ma non valido", "DROP")
    return None


# =====================================================
# URL PARSER
# =====================================================

def extract_from_url(url):
    log(f"URL diretta → {url}", "URL")

    key_id = ""
    key = ""

    m1 = re.search(r"key_id=([A-Za-z0-9-_]+)", url)
    m2 = re.search(r"key=([A-Za-z0-9-_/=]+)", url)

    if m1:
        key_id = m1.group(1)
    if m2:
        key = m2.group(1)

    return {"type": "direct", "url": url, "key_id": key_id, "key": key}


def extract_from_url_fallback(value):
    m = re.search(r"(https?://[^\s\"']+)", value)
    if not m:
        log("Fallback URL fallito", "DROP")
        return None
    return extract_from_url(m.group(1))


# =====================================================
# UNIVERSAL STREAM DECODER
# =====================================================

def decode_stream(value):
    if not value:
        log("Resolve vuoto", "DROP")
        return None

    value = value.strip()
    log(f"Decodifica → {value}", "DECODE")

    if value.lower().startswith("dazntoken@@"):
        log("Tipo DAZN", "TYPE")
        try:
            b64 = value.split("@@")[1]
            missing = len(b64) % 4
            if missing:
                b64 += "=" * (4 - missing)
            decoded = base64.b64decode(b64).decode("utf-8", "ignore")
        except:
            log("DAZN decode fallito", "DROP")
            return None

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

    if value.lower().startswith("freeshot@@"):
        log("Freeshot ignorato", "DROP")
        return None

    if value.startswith("http"):
        return extract_from_url(value)

    if ".mpd" in value or ".m3u8" in value:
        return extract_from_url(value if value.startswith("http") else "https://" + value)

    if value.startswith("{") and value.endswith("}"):
        try:
            obj = json.loads(value)
            log("JSON inline OK", "OK")
            return {
                "type": "json",
                "url": obj.get("url"),
                "key_id": obj.get("key_id", ""),
                "key": obj.get("key", "")
            }
        except:
            log("JSON non valido", "DROP")

    amstaff = decode_amstaff_raw(value)
    if amstaff:
        return amstaff

    log("Nessun decoder valido", "DROP")
    return None


# =====================================================
# KODI PROPERTY BUILDER
# =====================================================

def build_kodi_props(stream):
    props = []

    if ".mpd" in stream["url"]:
        props.append("#KODIPROP:inputstream.adaptive.manifest_type=mpd")

    if stream.get("type") == "dazn":
        if stream["key_id"] and stream["key"]:
            props.append("#KODIPROP:inputstream.adaptive.license_type=clearkey")
            props.append(
                f"#KODIPROP:inputstream.adaptive.license_key={stream['key_id']}:{stream['key']}"
            )

        header = (
            f"dazn-token={stream['token']}"
            "&user-agent=Mozilla/5.0"
            "&referer=https://www.dazn.com/"
            "&origin=https://www.dazn.com"
        )

        props.append(f"#KODIPROP:inputstream.adaptive.stream_headers={header}")
        return props

    if stream["key_id"] and stream["key"]:
        props.append("#KODIPROP:inputstream.adaptive.license_type=clearkey")
        props.append(
            f"#KODIPROP:inputstream.adaptive.license_key={stream['key_id']}:{stream['key']}"
        )

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
            log(f"Resolve → {resolve}", "RAW")

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
    if not found:
        log(f"Categoria {name} NON trovata", "DROP")
    return found


# =====================================================
# FETCH
# =====================================================

def fetch_amstaff_channels():
    headers = {"User-Agent": USER_AGENT}

    home = requests.get(HOME_URL, headers=headers, timeout=15).json()

    sport = find_category_link(home, "SPORT")
    if not sport:
        return []

    sport_json = requests.get(sport, headers=headers, timeout=15).json()
    last = find_category_link(sport_json, "LAST MINUTE")
    if not last:
        return []

    last_json = requests.get(last, headers=headers, timeout=15).json()

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
        log(f"ACCETTATO → {ch['title']} ({decoded['type']})", "OK")

    log(f"Canali validi finali: {len(final)}", "STATS")
    return final


# =====================================================
# M3U
# =====================================================

def generate_m3u(channels):
    m3u = "#EXTM3U\n\n"

    for ch in channels:
        props = build_kodi_props(ch)
        tvg_id = re.sub(r"[^A-Za-z0-9]", "", ch["title"]).lower()

        m3u += f'#EXTINF:-1 tvg-id="{tvg_id}" tvg-logo="{DEFAULT_LOGO}" group-title="LAST MINUTE",{ch["title"]}\n'
        for p in props:
            m3u += p + "\n"
        m3u += ch["url"] + "\n\n"

    with open(OUTPUT_M3U, "w", encoding="utf-8") as f:
        f.write(m3u)

    log(f"Playlist generata → {OUTPUT_M3U}", "DONE")


# =====================================================
# MAIN
# =====================================================

if __name__ == "__main__":
    channels = fetch_amstaff_channels()
    if channels:
        generate_m3u(channels)
    else:
        log("Nessun canale trovato", "FAIL")

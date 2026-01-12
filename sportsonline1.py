import cloudscraper
import json
import re

URL_SOURCE = "https://sportsonline.st/prog.txt"
OUTPUT_FILE = "W3U/EventiS.w3u"   # <-- SALVA NELLA CARTELLA W3U

# HEADER DEL FILE W3U
HEADER = {
    "name": "Eventi Sportsonline",
    "author": "Only Mobile",
    "info": "Aggiornata",
    "image": "https://static.wikia.nocookie.net/logopedia/images/0/0c/DAZN_PPV_print.svg/revision/latest/scale-to-width-down/250?cb=20240911135312",
    "url": "https://raw.githubusercontent.com/warsimud/simud/refs/heads/main/W3U/EventiS.w3u",
    "stations": []
}

# REGEX robusta per estrarre gli eventi
EVENT_REGEX = re.compile(
    r'^(\d{1,2}:\d{2})\s+(.*?)\s*\|\s*(https?://\S+)$'
)

def main():
    scraper = cloudscraper.create_scraper()

    print("Scarico lista da sportsonline.cx ...")
    try:
        content = scraper.get(URL_SOURCE).text
    except Exception as e:
        print("Errore nel download:", e)
        return

    stations = []

    for line in content.splitlines():
        line = line.strip()

        # prova match della regex
        match = EVENT_REGEX.match(line)
        if not match:
            continue

        time_part, title, url = match.groups()

        station = {
            "name": title.strip(),
            "info": time_part.strip(),
            "online": "true",
            "image": "https://www.chefstudio.it/img/blog/logo-serie-a/nuovo-logo-serie-a.jpg",
            "userAgent": "Mozilla/5.0 (iPhone; CPU iPhone OS 17_5_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0.1 Mobile/15E148 Safari/605.1.15/Clipbox+/2.2.8",
            "url": url.strip(),
            "embed": "true",
            "isHost": ""
        }

        stations.append(station)

    HEADER["stations"] = stations

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(HEADER, f, indent=4, ensure_ascii=False)

    print(f"✔ GENERATE {len(stations)} CANALI")
    print(f"✔ File creato: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()

import cloudscraper
import re

URL_SOURCE = "https://sportsonline.st/prog.txt"
OUTPUT_TXT = "sportsonline.txt"

# Immagine base (quella che vuoi te)
IMAGE_DEFAULT = "https://11contro11.it/wp-content/uploads/2024/10/serie-a-11-2024-696x392.png"

# Regex: parte canali e parte eventi
CHANNEL_REGEX = re.compile(r'^(HD|BR)(\d+)\s+(.*)$')
EVENT_REGEX = re.compile(r'^(\d{1,2}:\d{2})\s+(.*?)\s*\|\s*(https?://\S+)$')


def main():
    scraper = cloudscraper.create_scraper()

    print("Scarico prog.txt ...")
    try:
        content = scraper.get(URL_SOURCE).text
    except Exception as e:
        print("Errore:", e)
        return

    italian_channels = set()
    lines = content.splitlines()

    # 1️⃣ TROVA I CANALI ITALIANI
    for line in lines:
        m = CHANNEL_REGEX.match(line.strip())
        if not m:
            continue

        prefix, num, lang = m.groups()
        lang = lang.strip().upper()

        if "ITALIAN" in lang:
            italian_channels.add(f"{prefix}{num}")

    print("Canali italiani trovati:", italian_channels)

    # 2️⃣ FILTRA SOLO GLI EVENTI ITALIANI
    txt_output = []

    for line in lines:
        m = EVENT_REGEX.match(line.strip())
        if not m:
            continue

        time_part, title, url = m.groups()

        # Estrai il canale dall'URL
        channel_match = re.search(r'/(\w+?)(\d+)\.php$', url)
        if not channel_match:
            continue

        prefix = channel_match.group(1).upper()  # hd → HD
        num = channel_match.group(2)
        channel_id = f"{prefix}{num}"

        # Se il canale non è italiano → skip
        if channel_id not in italian_channels:
            continue

        # Salva nel TXT con immagine
        txt_output.append(f"{title} | {time_part} | {url} | {IMAGE_DEFAULT}")

    # 3️⃣ SALVA FILE TXT
    with open(OUTPUT_TXT, "w", encoding="utf-8") as f:
        f.write("\n".join(txt_output))

    print("✔ Eventi italiani trovati:", len(txt_output))
    print("✔ File salvato:", OUTPUT_TXT)


if __name__ == "__main__":
    main()

import cloudscraper
import re

URL_SOURCE = "https://sportsonline.st/prog.txt"
OUTPUT_TXT = "sportsonlinecompleto.txt"

# Immagine base (quella che vuoi te)
IMAGE_DEFAULT = "https://i.postimg.cc/hPwWVN4r/Chat-GPT-Image-8-feb-2026-12-11-19.png"

# Regex eventi
EVENT_REGEX = re.compile(r'^(\d{1,2}:\d{2})\s+(.*?)\s*\|\s*(https?://\S+)$')


def main():
    scraper = cloudscraper.create_scraper()

    print("Scarico prog.txt ...")
    try:
        content = scraper.get(URL_SOURCE).text
    except Exception as e:
        print("Errore:", e)
        return

    lines = content.splitlines()
    txt_output = []

    # 1️⃣ PRENDI TUTTI GLI EVENTI (niente filtri)
    for line in lines:
        m = EVENT_REGEX.match(line.strip())
        if not m:
            continue

        time_part, title, url = m.groups()

        # Salva tutto, zero filtraggio
        txt_output.append(f"{title} | {time_part} | {url} | {IMAGE_DEFAULT}")

    # 2️⃣ SALVA FILE TXT
    with open(OUTPUT_TXT, "w", encoding="utf-8") as f:
        f.write("\n".join(txt_output))

    print("✔ Eventi trovati:", len(txt_output))
    print("✔ File salvato:", OUTPUT_TXT)


if __name__ == "__main__":
    main()

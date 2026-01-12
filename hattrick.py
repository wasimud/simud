import cloudscraper
from bs4 import BeautifulSoup
import json
import os


URL = "https://hattrick.ws/"

OUTPUT_FILE = "W3U/EventiH.w3u"
RAW_URL = "https://raw.githubusercontent.com/warsimud/simud/refs/heads/main/W3U/EventiH.w3u"


def estrai_eventi():
    scraper = cloudscraper.create_scraper()
    html = scraper.get(URL).text

    soup = BeautifulSoup(html, "html.parser")

    eventi = []

    blocchi = soup.find_all("div", class_="row")

    for row in blocchi:

        # immagine
        img_tag = row.find("img", class_="mascot")
        img_evento = img_tag["src"] if img_tag else ""

        # titolo evento
        titolo_tag = row.find("a", class_="game-name")
        if not titolo_tag:
            continue

        titolo = titolo_tag.text.strip()

        # ❌ ESCLUDI "Canali On Line" o simili
        if titolo.lower() in ["canali on line", "canali online", "canali on-line"]:
            continue

        # categoria
        categoria_tag = row.find("p", class_="date")
        categoria = categoria_tag.text.strip() if categoria_tag else ""

        # link canali .htm
        links = []
        for btn in row.find_all("a", href=True):
            href = btn["href"]
            if href.endswith(".htm"):
                nome_canale = btn.text.strip()
                links.append((nome_canale, href))

        if not links:
            continue

        eventi.append({
            "titolo": titolo,
            "categoria": categoria,
            "immagine": img_evento,
            "canali": links
        })

    return eventi


def crea_w3u(eventi):
    struttura = {
        "name": "Eventi Hattrick",
        "author": "Only Mobile",
        "info": "Aggiornata 20/11/25",
        "image": "https://static.wikia.nocookie.net/logopedia/images/0/0c/DAZN_PPV_print.svg/revision/latest/scale-to-width-down/250?cb=20240911135312",
        "url": RAW_URL,
        "stations": []
    }

    for ev in eventi:
        titolo = ev["titolo"]
        categoria = ev["categoria"]
        img = ev["immagine"] or "https://i.postimg.cc/K818HSJd/46373132-world-of-sports-vector-illustration-of-sports-icons-basketball-soccer-tennis-boxing-wrestli.png"

        for nome_canale, link in ev["canali"]:
            struttura["stations"].append({
                "name": f"{titolo} - {nome_canale}",
                "info": categoria,
                "online": "true",
                "image": img,
                "userAgent": "Mozilla/5.0 (iPhone; CPU iPhone OS 17_5_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0.1 Mobile/15E148 Safari/605.1.15/Clipbox+/2.2.8",
                "url": link,
                "embed": "true",
                "isHost": ""
            })

    return struttura


def salva_file_w3u(dati):

    # crea la cartella se manca
    os.makedirs("W3U", exist_ok=True)

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(dati, f, indent=4, ensure_ascii=False)

    print(f"✅ File generato: {OUTPUT_FILE}")
    print(f"📌 URL previsto nei client: {RAW_URL}")


# ---- MAIN ----
eventi = estrai_eventi()
w3u = crea_w3u(eventi)
salva_file_w3u(w3u)

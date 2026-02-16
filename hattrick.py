import cloudscraper
from bs4 import BeautifulSoup
import json
import os
from urllib.parse import urljoin

URL = "https://htsport.cc/"

OUTPUT_FILE = "W3U/EventiH.w3u"
RAW_URL = "https://raw.githubusercontent.com/wasimud/simud/refs/heads/main/W3U/EventiH.w3u"


def make_absolute_url(base_url: str, href: str) -> str:
    """
    Converte link relativi in assoluti usando base_url.
    Esempi:
      - "eurosport1.htm"  -> "https://htsport.cc/eurosport1.htm"
      - "/eurosport1.htm" -> "https://htsport.cc/eurosport1.htm"
      - "https://..."     -> resta invariato
    """
    if not href:
        return ""
    return urljoin(base_url, href.strip())


def estrai_eventi():
    scraper = cloudscraper.create_scraper()
    html = scraper.get(URL).text

    soup = BeautifulSoup(html, "html.parser")

    eventi = []
    blocchi = soup.find_all("div", class_="row")

    for row in blocchi:

        # immagine evento (se relativa -> assoluta)
        img_tag = row.find("img", class_="mascot")
        img_evento = ""
        if img_tag and img_tag.get("src"):
            img_evento = make_absolute_url(URL, img_tag["src"])

        # titolo evento
        titolo_tag = row.find("a", class_="game-name")
        if not titolo_tag:
            continue

        titolo = titolo_tag.text.strip()

        # ❌ ESCLUDI "Canali On Line" o simili
        if titolo.lower() in ["canali on line", "canali online", "canali on-line"]:
            continue

        # categoria (orario/descrizione)
        categoria_tag = row.find("p", class_="date")
        categoria = categoria_tag.text.strip() if categoria_tag else ""

        # link canali .htm (forza assoluti)
        links = []
        for btn in row.find_all("a", href=True):
            href = btn["href"].strip()
            if href.endswith(".htm"):
                nome_canale = btn.text.strip()
                href_assoluto = make_absolute_url(URL, href)  # ✅ QUI
                links.append((nome_canale, href_assoluto))

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

    fallback_img = "https://i.postimg.cc/K818HSJd/46373132-world-of-sports-vector-illustration-of-sports-icons-basketball-soccer-tennis-boxing-wrestli.png"

    for ev in eventi:
        titolo = ev["titolo"]
        categoria = ev["categoria"]
        img = ev["immagine"] or fallback_img

        for nome_canale, link_assoluto in ev["canali"]:
            struttura["stations"].append({
                "name": f"{titolo} - {nome_canale}",
                "info": categoria,
                "online": "true",
                "image": img,
                "userAgent": "Mozilla/5.0 (iPhone; CPU iPhone OS 17_5_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0.1 Mobile/15E148 Safari/605.1.15/Clipbox+/2.2.8",
                "url": link_assoluto,  # ✅ sempre https://htsport.cc/xxx.htm
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

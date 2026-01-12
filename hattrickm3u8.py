import asyncio
import cloudscraper
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright

URL_PRINCIPALE = "https://hattrick.ws/"
LOGO = "https://resource-m.calcionapoli24.it/www/thumbs/1200x/1590651555_987.jpg"

# -----------------------------------------------------------
# 🎯 RINOMINA CANALI
# -----------------------------------------------------------

RENAME_RULES = [
    (["1", "uno"], "Sky Sport Uno"),
    (["calcio"], "Sky Sport Calcio"),
    (["mix"], "Sky Sport Mix"),
    (["max"], "Sky Sport Max"),
    (["arena"], "Sky Sport Arena"),
    (["24"], "Sky Sport 24"),
    (["tennis"], "Sky Sport Tennis"),
    (["motogp"], "Sky Sport MotoGP"),
    (["f1", "formula"], "Sky Sport Formula 1"),
    (["dazn"], "DAZN 1"),
]

def normalizza_nome(nome):
    nome_l = nome.lower()
    for keys, nuovo in RENAME_RULES:
        for k in keys:
            if k in nome_l:
                return nuovo
    return nome.strip()

# -----------------------------------------------------------
# 1️⃣ ESTRAI CANALI
# -----------------------------------------------------------

def estrai_canali():
    scraper = cloudscraper.create_scraper(
        browser={"browser": "chrome", "platform": "windows", "desktop": True}
    )

    try:
        r = scraper.get(URL_PRINCIPALE, timeout=15)
        r.raise_for_status()
    except Exception as e:
        print("❌ Sito non raggiungibile:", e)
        return []

    soup = BeautifulSoup(r.text, "html.parser")
    canali = []

    for btn in soup.find_all("button"):
        a = btn.find("a")
        if a and a.get("href", "").endswith(".htm"):
            canali.append({
                "nome": normalizza_nome(a.text),
                "url": a["href"]
            })

    return canali

# -----------------------------------------------------------
# 2️⃣ PLAYWRIGHT → SNIFF M3U8 REALI
# -----------------------------------------------------------

async def estrai_m3u8(url):

    async with async_playwright() as p:
        browser = await p.webkit.launch(headless=True)

        context = await browser.new_context(
            user_agent=(
                "Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) "
                "AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Mobile Safari/604.1"
            )
        )

        stream = None

        def on_request(req):
            nonlocal stream
            if req.url.endswith("index.m3u8") and "tracks" not in req.url:
                print("✔️ STREAM:", req.url)
                stream = req.url

        context.on("request", on_request)

        page = await context.new_page()

        try:
            await page.goto(url, timeout=60000)
            await asyncio.sleep(6)
        except:
            pass

        await browser.close()
        return stream

# -----------------------------------------------------------
# 3️⃣ SCRIVI FILE M3U8
# -----------------------------------------------------------

def scrivi_m3u8(nome_file, canali):
    with open(nome_file, "w", encoding="utf-8") as f:
        f.write("#EXTM3U\n\n")

        for i, c in enumerate(canali, 1):
            f.write(
                f'#EXTINF:-1 tvg-id="{i}" '
                f'group-title="Sky Sport IPTV" '
                f'tvg-logo="{LOGO}", {c["nome"]}\n'
            )
            f.write(c["url"] + "\n\n")

# -----------------------------------------------------------
# 4️⃣ MAIN
# -----------------------------------------------------------

async def main():

    print("📥 Raccolgo canali...")
    canali = estrai_canali()

    if not canali:
        print("🚫 Nessun canale trovato")
        return

    finali = []
    visti = set()

    print("🎬 Analisi stream...\n")

    for c in canali:
        print("➡", c["nome"])
        m3u8 = await estrai_m3u8(c["url"])

        if not m3u8 or m3u8 in visti:
            continue

        visti.add(m3u8)
        finali.append({
            "nome": c["nome"],
            "url": m3u8
        })

    scrivi_m3u8("hattrick.m3u8", finali)

    print("\n🎉 COMPLETATO")
    print("📺 Canali salvati:", len(finali))
    print("📁 File: hattrick.m3u8")

# -----------------------------------------------------------
# AVVIO
# -----------------------------------------------------------

asyncio.run(main())

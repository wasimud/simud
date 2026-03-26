import cloudscraper
from bs4 import BeautifulSoup
import time
import re

# ==================== CONFIGURAZIONE ====================
MAIN_URL = "https://htsport.cc/"
OUTPUT_FILE = "hattrick.m3u8"

# Immagine logo (cambiala con la tua)
IMAGE_URL = "https://i.postimg.cc/Kvwg9t3F/3790038-logo-vetrina-dazn-sport-dazn-a-11563364038i3yzrattgk-removebg-preview.png"

# Headers
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36"
REFERRER = "https://mediahosting.space/"
ORIGIN = "https://mediahosting.space"
# =======================================================

scraper = cloudscraper.create_scraper(
    browser={
        'browser': 'chrome',
        'platform': 'windows',
        'mobile': False
    }
)
scraper.headers.update({
    'User-Agent': USER_AGENT,
    'Referer': REFERRER,
    'Origin': ORIGIN
})

print("🚀 Avvio scraping da https://htsport.cc/ ...")

# 1. Scarica la pagina principale
response = scraper.get(MAIN_URL)
if response.status_code != 200:
    print(f"❌ Errore nel caricamento della pagina principale: {response.status_code}")
    exit()

soup = BeautifulSoup(response.text, 'html.parser')

# 2. Trova tutti i blocchi evento (.row dentro .events)
rows = soup.select('.events .row')
print(f"✅ Trovati {len(rows)} blocchi evento")

event_list = []  # lista di (nome_evento, url_pagina_stream)

for row in rows:
    # Nome evento
    game_name_tag = row.select_one('.details .game-name')
    if not game_name_tag:
        continue
    nome_evento = game_name_tag.get_text(strip=True)
    if not nome_evento:
        continue

    # === FILTRO PER ESCLUDERE "Canali On Line" ===
    if "canali on line" in nome_evento.lower() or "canale on line" in nome_evento.lower():
        print(f"⏭️  Saltato sezione Canali On Line: {nome_evento}")
        continue

    # Tutti i link .htm interni (i canali live degli eventi)
    links = row.select('a[href$=".htm"]')
    for link in links:
        href = link.get('href')
        if href and not href.startswith(('http://', 'https://')):
            event_url = f"https://htsport.cc/{href.lstrip('/')}"
            event_list.append((nome_evento, event_url))

# Rimuovi duplicati mantenendo l'ordine
event_list = list(dict.fromkeys(event_list))
print(f"✅ Estratti {len(event_list)} link evento (dopo aver escluso Canali On Line)")

# 3. Crea il file M3U
with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
    f.write("#EXTM3U\n\n")

    processed = 0
    for nome, pagina_url in event_list:
        print(f"📡 Processando {nome} → {pagina_url}")
        
        try:
            resp = scraper.get(pagina_url, timeout=15)
            if resp.status_code != 200:
                print(f"   ⚠️  Errore {resp.status_code} su {pagina_url}")
                time.sleep(1)
                continue

            event_soup = BeautifulSoup(resp.text, 'html.parser')
            
            # Trova l'iframe con il player
            iframe = event_soup.find('iframe', id='iframe')
            if not iframe or not iframe.get('src'):
                iframe = event_soup.find('iframe', attrs={'class': lambda x: x and 'iframe' in str(x).lower()})
            
            if iframe and iframe.get('src'):
                src = iframe['src']
                if '#' in src:
                    m3u8_url = src.split('#', 1)[1].strip()
                    if m3u8_url.startswith('http'):
                        # Scrivi nel M3U
                        f.write(f'#EXTINF:-1 tvg-id="" tvg-logo="{IMAGE_URL}" group-title="Eventi IPTV",{nome}\n')
                        f.write(f'#EXTVLCOPT:http-user-agent={USER_AGENT}\n')
                        f.write(f'#EXTVLCOPT:http-referrer={REFERRER}\n')
                        f.write(f'#EXTVLCOPT:http-origin={ORIGIN}\n')
                        f.write(f'#EXTVLCOPT:http-header=Origin: {ORIGIN}\n')
                        f.write(f'{m3u8_url}\n\n')
                        
                        print(f"   ✅ Stream trovato: {m3u8_url[:100]}...")
                        processed += 1
                    else:
                        print("   ⚠️  URL dopo # non è un link HTTP")
                else:
                    print("   ⚠️  Nessun # trovato nell'iframe src")
            else:
                print("   ⚠️  Nessun iframe trovato nella pagina evento")
                
        except Exception as e:
            print(f"   ❌ Errore: {str(e)[:120]}")
        
        time.sleep(1.5)  # Anti-ban leggero

print(f"\n🎉 FINITO! Playlist creata: {OUTPUT_FILE}")
print(f"   📊 {processed} stream aggiunti (solo eventi live)")
print(f"   🖼️  Immagine usata: {IMAGE_URL}")
print("\n💡 Usa la playlist in VLC, Kodi, IPTV Smarters o simili.")

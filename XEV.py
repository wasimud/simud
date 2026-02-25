from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from webdriver_manager.chrome import ChromeDriverManager
import time
import pyperclip
import re

# ────────────────────────────────────────────────
EMAIL    = "pinpinoinfin@gmail.com"
PASSWORD = "Simone04238."

DISCOVER_URL = "https://web.stremio.com/#/discover/https%3A%2F%2Fstreamvix.hayd.uk%2FeyJtZWRpYWZsb3dNYXN0ZXIiOmZhbHNlLCJkdnJFbmFibGVkIjpmYWxzZSwiZGlzYWJsZUxpdmVUdiI6ZmFsc2UsInZhdm9vTm9NZnBFbmFibGVkIjp0cnVlLCJ0cmFpbGVyRW5hYmxlZCI6dHJ1ZSwiZGlzYWJsZVZpeHNyYyI6ZmFsc2UsInZpeERpcmVjdCI6ZmFsc2UsInZpeERpcmVjdEZoZCI6ZmFsc2UsImNiMDFFbmFibGVkIjpmYWxzZSwiZ3VhcmRhaGRFbmFibGVkIjp0cnVlLCJndWFyZGFzZXJpZUVuYWJsZWQiOnRydWUsImd1YXJkb3NlcmllRW5hYmxlZCI6dHJ1ZSwiZ3VhcmRhZmxpeEVuYWJsZWQiOnRydWUsImV1cm9zdHJlYW1pbmdFbmFibGVkIjpmYWxzZSwibG9vbmV4RW5hYmxlZCI6ZmFsc2UsInRvb25pdGFsaWFFbmFibGVkIjpmYWxzZSwibG9vbmV4RW5hYmxlZCI6ZmFsc2UsImFuaW1lc2F0dXJuRW5hYmxlZCI6dHJ1ZSwiYW5pbWV3b3JsZEVuYWJsZWQiOnRydWUsImFuaW1ldW5pdHlFbmFibGVkIjp0cnVlLCJhbmltZXVuaXR5QXV0byI6ZmFsc2UsImFuaW1ldW5pdHlGaGQiOmZhbHNlLCJ2aXhQcm94eSI6ZmFsc2UsInZpeFByb3h5RmhkIjp0cnVlfQ%3D%3D%2Fmanifest.json/tv/streamvix_live?genre=X-Eventi"

SQUADRE_SERIE_A = {
    "atalanta", "bologna", "cagliari", "como", "cremonese", "fiorentina", "genoa", "hellas verona", "inter", "juventus", "lazio", "lecce", "milan", "napoli", "parma", "pisa", "roma", "sassuolo", "torino", "udinese", "dazn"
}

LOGO_URL = "https://i.postimg.cc/BvQ3kS1S/Sky-Sport-Serie-A.png"

options = Options()
options.add_argument("--window-size=1280,900")
options.add_argument("--disable-notifications")
options.add_argument("--log-level=3")
options.add_experimental_option("excludeSwitches", ["enable-logging"])
# options.add_argument("--headless=new")  # decommenta se vuoi esecuzione silenziosa

driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
wait = WebDriverWait(driver, 9)
actions = ActionChains(driver)

m3u_lines = ["#EXTM3U"]
added_count = 0

def parse_stream_for_kodi(url, title):
    key_id = None
    key = None

    key_id_match = re.search(r'key_id=([a-f0-9]{32})', url, re.IGNORECASE)
    key_match = re.search(r'key=([a-f0-9]{32})', url, re.IGNORECASE)

    if key_id_match:
        key_id = key_id_match.group(1)
    if key_match:
        key = key_match.group(1)

    base_url = re.sub(r'(&key_id=[a-f0-9]{32})|(&key=[a-f0-9]{32})', '', url).rstrip('&? ')

    channel_match = re.search(r'channel\(([^)]+)\)', base_url, re.IGNORECASE)
    tvg_id = channel_match.group(1) if channel_match else "unknown_channel"

    if key_id and key:
        lines = [
            f'#EXTINF:-1 tvg-id="{tvg_id}" tvg-logo="{LOGO_URL}" group-title="Serie A X-Eventi",{title}',
            '#KODIPROP:inputstream.adaptive.license_type=clearkey',
            f'#KODIPROP:inputstream.adaptive.license_key={key_id}:{key}',
            base_url
        ]
        return '\n'.join(lines)
    else:
        return f'#EXTINF:-1 tvg-logo="{LOGO_URL}" group-title="Serie A X-Eventi",{title}\n{url}'

try:
    print("Login...")
    driver.get("https://web.stremio.com/#/intro?form=login")
    time.sleep(1.8)

    email_field = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='email']")))
    email_field.send_keys(EMAIL)

    pwd_field = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='password']")))
    pwd_field.send_keys(PASSWORD + Keys.ENTER)
    time.sleep(7)

    print("→ X-Eventi...")
    driver.get(DISCOVER_URL)
    time.sleep(4)

    driver.execute_script("window.scrollBy(0, 3000);")
    time.sleep(1.0)
    driver.execute_script("window.scrollBy(0, 3000);")
    time.sleep(0.8)

    event_links = driver.find_elements(By.CSS_SELECTOR, 'a[href^="#/detail/tv/"]')
    print(f"Trovati {len(event_links)} eventi totali")

    for idx, link in enumerate(event_links, 1):
        try:
            title_raw = link.text.strip()
            title = ' '.join(title_raw.split())

            title_lower = title.lower()
            if not any(s in title_lower for s in SQUADRE_SERIE_A):
                continue

            print(f"[{idx:02d}] PROCESSO: {title}")

            detail_path = link.get_attribute("href").split("#")[-1]
            driver.get("https://web.stremio.com/#" + detail_path)
            time.sleep(2.0)

            stream_url = None

            player_selectors = [
                'a[href^="#/player/"]',
                'a.label-container-XOyzm[href^="#/player/"]',
                'svg.icon-rAZvO',
                '[class*="play"], [class*="watch"]'
            ]

            player_elem = None
            for sel in player_selectors:
                try:
                    player_elem = driver.find_element(By.CSS_SELECTOR, sel)
                    if player_elem.is_displayed():
                        break
                except:
                    continue

            if player_elem:
                driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", player_elem)
                time.sleep(0.4)

                actions.context_click(player_elem).perform()
                time.sleep(1.8)

                copy_item = None
                try:
                    copy_item = wait.until(EC.element_to_be_clickable((
                        By.XPATH,
                        '//div[contains(@class, "context-menu-option-container") and (contains(., "Copy stream link") or contains(@title, "Copy stream link"))]'
                    )))
                except:
                    menu_items = driver.find_elements(By.CSS_SELECTOR, '.context-menu-option-container-BZGla, .context-menu-option-container')
                    for item in menu_items:
                        txt = (item.text or item.get_attribute("title") or "").lower()
                        if "copy stream link" in txt:
                            copy_item = item
                            break

                if copy_item:
                    actions.move_to_element(copy_item).pause(0.3).click().perform()
                    time.sleep(1.2)

                    raw_clip = pyperclip.paste().strip()
                    if raw_clip.startswith(('http://', 'https://')) and len(raw_clip) > 40:
                        stream_url = raw_clip
                        print(f"  → Copiato: {stream_url[:85]}...")
                    else:
                        print(f"  → Clipboard non valida: {raw_clip[:60]}")
                else:
                    print("  → 'Copy stream link' non trovato")
            else:
                print("  → Elemento play non trovato")

            if stream_url:
                extinf_block = parse_stream_for_kodi(stream_url, title)
                m3u_lines.append(extinf_block)
                m3u_lines.append("")  # riga vuota tra canali
                added_count += 1
                print("  → Aggiunto\n")
            else:
                print("  → FALLITO\n")

            driver.back()
            time.sleep(1.0)

        except Exception as e:
            print(f"  Errore: {str(e)[:90]}...\n")
            try: driver.back()
            except: pass
            time.sleep(1.5)

    # Salva con il nome richiesto
    with open("XEV.m3u8", "w", encoding="utf-8") as f:
        f.write("\n".join(m3u_lines).strip() + "\n")

    print(f"\nCOMPLETATO!")
    print(f"Eventi aggiunti (Serie A filtrate): {added_count}")
    print("File salvato come: XEV.m3u8")

except Exception as e:
    print("CRASH:", str(e))

finally:
    driver.quit()

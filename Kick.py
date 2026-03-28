#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import streamlink
import sys
from datetime import datetime

# ====================== CONFIGURAZIONE ======================
# Aggiungi qui tutti i canali che vuoi!
# Formato: "nome_canale": "url_kick"

CHANNELS = {
    "anidomgotv": "https://kick.com/anidomgotv",
    # Aggiungi altri canali qui sotto (esempio):
    # "nome2": "https://kick.com/nome2",
    # "nome3": "https://kick.com/nome3",
    # "paul": "https://kick.com/paul",
}

# Logo di default (puoi cambiarlo per ogni canale se vuoi)
DEFAULT_LOGO = "https://i.imgur.com/tuo-logo-qui.png"

# Header comuni
USER_AGENT = "Mozilla/5.0 (iPhone; CPU iPhone OS 17_7 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.0 Mobile/15E148 Safari/604.1"
REFERER = "https://kick.com/"
ORIGIN = "https://kick.com/"

QUALITY = "best"          # "best", "720p", "480p", ecc.
OUTPUT_FILE = "Kick.m3u8"
# ===========================================================

def get_stream_url(url):
    """Estrae l'URL dello stream m3u8 usando streamlink"""
    session = streamlink.Streamlink()
    session.set_option("http-headers", {
        "User-Agent": USER_AGENT,
        "Referer": REFERER,
        "Origin": ORIGIN
    })

    try:
        streams = session.streams(url)
        if not streams:
            return None
        
        # Prova la qualità richiesta, altrimenti usa "best"
        if QUALITY in streams:
            return streams[QUALITY].to_url()
        elif "best" in streams:
            return streams["best"].to_url()
        else:
            # Prende la prima qualità disponibile
            return next(iter(streams.values())).to_url()
            
    except Exception as e:
        print(f"    Errore durante l'estrazione: {e}")
        return None


def main():
    print(f"[{datetime.now().strftime('%H:%M:%S')}] Inizio estrazione stream Kick...\n")

    m3u_content = ["#EXTM3U"]

    success_count = 0

    for name, url in CHANNELS.items():
        print(f"➤ Elaborazione: {name} ... ", end="")
        
        stream_url = get_stream_url(url)
        
        if stream_url:
            # Aggiunge al file m3u8
            m3u_content.append(f'#EXTINF:-1 tvg-logo="{DEFAULT_LOGO}" group-title="Kick", {name}')
            m3u_content.append("#EXTVLCOPT:http-referrer=https://kick.com/")
            m3u_content.append("#EXTVLCOPT:http-origin=https://kick.com/")
            m3u_content.append(f"#EXTVLCOPT:http-user-agent={USER_AGENT}")
            m3u_content.append(f"{stream_url}\n")
            
            print("✅ OK")
            success_count += 1
        else:
            print("❌ Offline o non raggiungibile")

    # Scrive il file finale
    if success_count > 0:
        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            f.write("\n".join(m3u_content))
        
        print(f"\n🎉 Completato! {success_count}/{len(CHANNELS)} canali aggiunti")
        print(f"   File creato: {OUTPUT_FILE}")
    else:
        print("\n❌ Nessun canale attivo è stato trovato.")

    print("\nPuoi aprire Kick.m3u8 direttamente con VLC o caricarlo nella tua app IPTV.")


if __name__ == "__main__":
    main()

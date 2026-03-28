import yt_dlp
import json
from datetime import datetime
import time

# ================== CONFIGURAZIONE ==================
channels = [
    {
        "name": "Sky",
        "url": "https://www.youtube.com/@skysport/videos"
    },
    # Aggiungi altri canali qui
    # {"name": "Nome Canale", "url": "https://www.youtube.com/@AltroCanale/videos"},
]

MAX_VIDEOS_PER_CHANNEL = 50
OUTPUT_TXT = "highlights.txt"
# ====================================================

def get_latest_videos_yt_dlp(channel_url, limit=30):
    ydl_opts = {
        'quiet': True,
        'no_warnings': True,
        'extract_flat': True,
        'ignoreerrors': True,
        'playlist_items': f'1-{limit}',
        
        # === OPZIONI ANTI-LIMITAZIONE GITHUB ACTIONS ===
        'sleep_interval_requests': 4,      # pausa tra richieste (molto importante)
        'sleep_interval': 3,
        'retries': 10,
        'extractor_retries': 10,
        'fragment_retries': 10,
        
        # Prova diversi client YouTube (aiuta molto)
        'extractor_args': {
            'youtube': {
                'player_client': ['android', 'ios', 'web'],   # android spesso bypassa meglio
                'skip': ['webpage'],                          # opzionale
            }
        },
        
        # Altre opzioni utili
        'http_headers': {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36',
        },
    }

    print(f"   Estrazione da: {channel_url}")
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(channel_url, download=False)
            
            if not info or 'entries' not in info:
                print("   Nessun 'entries' trovato nella risposta.")
                return []
                
            entries = [e for e in info.get('entries', []) if e and isinstance(e, dict)]
            print(f"   Trovati {len(entries)} video validi (prima del limite)")
            return entries[:limit]
            
    except Exception as e:
        print(f"   Errore durante l'estrazione: {e}")
        return []


def save_to_txt(videos, filename=OUTPUT_TXT):
    with open(filename, "w", encoding="utf-8") as f:
        f.write("DAZN HIGHLIGHTS - LISTA VIDEO\n")
        f.write(f"Generato il: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n")
        f.write(f"Totale video: {len(videos)}\n")
        f.write("=" * 100 + "\n\n")

        for i, v in enumerate(videos, 1):
            title = v.get('title', 'Titolo non disponibile')
            video_id = v.get('id')
            channel_name = v.get('channel', 'DAZN IT')

            if not video_id:
                continue

            thumb = f"https://i.ytimg.com/vi/{video_id}/maxresdefault.jpg"
            link = f"https://www.youtube.com/watch?v={video_id}"
            embed = f"https://www.youtube.com/embed/{video_id}?autoplay=1&rel=0"

            f.write(f"{i:3d}. {title}\n")
            f.write(f"   Canale     : {channel_name}\n")
            f.write(f"   Thumb      : {thumb}\n")
            f.write(f"   Link       : {link}\n")
            f.write(f"   Embed      : {embed}\n")
            f.write("-" * 100 + "\n\n")


# ================== MAIN ==================
if __name__ == "__main__":
    print("🚀 Inizio estrazione video...\n")

    all_videos = []

    for ch in channels:
        print(f"→ Elaboro: {ch['name']} ...")
        
        videos = get_latest_videos_yt_dlp(ch['url'], MAX_VIDEOS_PER_CHANNEL)
        
        added = 0
        for video in videos:
            if video and isinstance(video, dict) and video.get('id'):
                all_videos.append({
                    "id": video['id'],
                    "title": video.get('title', 'Titolo non disponibile'),
                    "channel": ch['name']
                })
                added += 1
        
        print(f"   Aggiunti {added} video da {ch['name']}\n")
        
        # Pausa tra un canale e l'altro (se ne hai più di uno)
        if len(channels) > 1:
            time.sleep(5)

    if not all_videos:
        print("❌ Nessun video trovato.")
        exit(1)

    save_to_txt(all_videos)

    print(f"✅ File salvato con successo!")
    print(f"   Totale video: {len(all_videos)}")
    print(f"   File: {OUTPUT_TXT}")
    print("\n💡 Puoi ora usare questo file insieme al tuo HTML fullscreen player.")

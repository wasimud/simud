import yt_dlp
import json
from datetime import datetime

# ================== CONFIGURAZIONE ==================
channels = [
    {
        "name": "Giampy",
        "url": "https://www.youtube.com/@zGiampyTek/videos"
    },
    {
        "name": "iNoob",
        "url": "https://www.youtube.com/@iNoobChannel/videos"
    },
    {
        "name": "Murry",
        "url": "https://www.youtube.com/@xMurryPwNz/videos"
    },
    {
        "name": "Favij",
        "url": "https://www.youtube.com/@FavijTV/videos"
    },
    {
        "name": "The Show",
        "url": "https://www.youtube.com/@theshowisyou/videos"
    },
    # Aggiungi altri canali qui
    # {"name": "Nome Canale", "url": "https://www.youtube.com/@AltroCanale/videos"},
]

MAX_VIDEOS_PER_CHANNEL = 100
OUTPUT_TXT = "youtube.txt"
# ====================================================

def get_latest_videos_yt_dlp(channel_url, limit=30):
    ydl_opts = {
        'quiet': True,
        'no_warnings': True,
        'extract_flat': True,
        'ignoreerrors': True,
        'playlist_items': f'1-{limit}',
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(channel_url, download=False)
        if not info or 'entries' not in info:
            return []
        return info['entries'][:limit]


def save_to_txt(videos, filename=OUTPUT_TXT):
    with open(filename, "w", encoding="utf-8") as f:
        f.write("DAZN HIGHLIGHTS - LISTA VIDEO\n")
        f.write(f"Generato il: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n")
        f.write(f"Totale video: {len(videos)}\n")
        f.write("=" * 100 + "\n\n")

        for i, v in enumerate(videos, 1):
            title = v.get('title', 'Titolo non disponibile')
            video_id = v['id']
            thumb = f"https://i.ytimg.com/vi/{video_id}/maxresdefault.jpg"
            link = f"https://www.youtube.com/watch?v={video_id}"
            embed = f"https://www.youtube.com/embed/{video_id}?autoplay=1&rel=0"

            f.write(f"{i:3d}. {title}\n")
            f.write(f"   Canale     : {v.get('channel', 'DAZN IT')}\n")
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
            if video and isinstance(video, dict) and 'id' in video:
                all_videos.append({
                    "id": video['id'],
                    "title": video.get('title', 'Titolo non disponibile'),
                    "channel": ch['name']
                })
                added += 1
        
        print(f"   Trovati e aggiunti {added} video\n")

    if not all_videos:
        print("❌ Nessun video trovato.")
        exit(1)

    save_to_txt(all_videos)

    print(f"✅ File salvato con successo!")
    print(f"   Totale video: {len(all_videos)}")
    print(f"   File: {OUTPUT_TXT}")
    print("\n💡 Puoi ora usare questo file insieme al tuo HTML fullscreen player.")

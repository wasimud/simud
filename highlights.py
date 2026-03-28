import yt_dlp
from datetime import datetime

# ================== CONFIGURAZIONE ==================
channels = [
    {
        "name": "DAZN IT",
        "url": "https://www.youtube.com/@DAZNIT/videos"
    },
    # Aggiungi altri canali qui
]

MAX_VIDEOS_PER_CHANNEL = 30
OUTPUT_TXT = "videos_list.txt"
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
        f.write(f"Generato il: {datetime.now().strftime('%d/%m/%Y %H:%M')}\n")
        f.write(f"Totale video: {len(videos)}\n")
        f.write("=" * 90 + "\n\n")

        for i, v in enumerate(videos, 1):
            title = v['title']
            thumb = f"https://i.ytimg.com/vi/{v['id']}/maxresdefault.jpg"
            link = f"https://www.youtube.com/watch?v={v['id']}"

            f.write(f"{i:2d}. {title}\n")
            f.write(f"   Thumb : {thumb}\n")
            f.write(f"   Link  : {link}\n")
            f.write("-" * 90 + "\n\n")


# ================== MAIN ==================
if __name__ == "__main__":
    print("🚀 Estrazione video in corso...\n")

    all_videos = []

    for ch in channels:
        print(f"→ Elaboro: {ch['name']}")
        videos = get_latest_videos_yt_dlp(ch['url'], MAX_VIDEOS_PER_CHANNEL)

        for video in videos:
            if video and 'id' in video:
                all_videos.append({
                    "id": video['id'],
                    "title": video.get('title', 'Titolo non disponibile'),
                    "channel": ch['name']
                })

        print(f"   Trovati {len(videos)} video\n")

    if not all_videos:
        print("❌ Nessun video trovato.")
        exit(1)

    save_to_txt(all_videos)

    print(f"✅ Fatto! File salvato: {OUTPUT_TXT}")
    print(f"   Totale video: {len(all_videos)}")

import yt_dlp
from datetime import datetime
import time

# ================== CONFIGURAZIONE ==================
channels = [
    {
        "name": "DAZN IT",
        "url": "https://www.youtube.com/@DAZNIT/videos"
    },
]

MAX_VIDEOS_PER_CHANNEL = 25          # Ridotto un po' per evitare blocchi
OUTPUT_TXT = "highlights.txt"
# ====================================================

def is_video_embeddable(video):
    """Controllo embeddabilità"""
    if not video or not isinstance(video, dict):
        return False

    if video.get('playable_in_embed') is False:
        return False

    playability = video.get('playability_status') or {}
    status = playability.get('status', '').upper()
    if status in ('UNPLAYABLE', 'LOGIN_REQUIRED', 'ERROR', 'AGE_VERIFICATION_REQUIRED'):
        return False

    reason = str(playability.get('reason', '')).lower()
    blocked_keywords = ['embed', 'disabled', 'restricted', 'owner', 'copyright', 'private']
    if any(kw in reason for kw in blocked_keywords):
        return False

    if video.get('is_live') or video.get('was_live'):
        return False

    return True


def get_latest_videos_yt_dlp(channel_url, limit=25):
    # Prima estrazione veloce (flat)
    ydl_opts_flat = {
        'quiet': True,
        'no_warnings': True,
        'ignoreerrors': True,
        'extract_flat': True,
        'playlist_items': f'1-{limit * 2}',
    }

    print("   Estrazione veloce lista video...")

    with yt_dlp.YoutubeDL(ydl_opts_flat) as ydl:
        info = ydl.extract_info(channel_url, download=False)
        if not info or 'entries' not in info:
            return []

        entries = [e for e in info['entries'] if e and isinstance(e, dict) and 'id' in e]
        print(f"   Trovati {len(entries)} video totali (estrazione veloce)")

    # Ora controlliamo embeddabilità solo sui primi video (più lenti ma mirati)
    embeddable = []
    ydl_opts_full = {
        'quiet': True,
        'no_warnings': True,
        'ignoreerrors': True,
        'extract_flat': False,
        'socket_timeout': 20,
    }

    print("   Verifica embeddabilità (può richiedere tempo)...")

    with yt_dlp.YoutubeDL(ydl_opts_full) as ydl:
        for i, entry in enumerate(entries[:limit * 2]):
            try:
                if len(embeddable) >= limit:
                    break

                print(f"     Controllo {i+1}/{len(entries)}: {entry.get('title', 'N/D')[:60]}...")

                full_info = ydl.extract_info(f"https://www.youtube.com/watch?v={entry['id']}", 
                                           download=False, 
                                           ie_key='Youtube')

                if is_video_embeddable(full_info):
                    embeddable.append(full_info)
                    print(f"       → OK (embeddabile)")
                else:
                    print(f"       → Bloccato per embed")

                time.sleep(0.8)  # Piccola pausa per non sovraccaricare YouTube

            except Exception as e:
                print(f"       → Errore: {str(e)[:80]}")
                continue

    return embeddable[:limit]


def save_to_txt(videos, filename=OUTPUT_TXT):
    with open(filename, "w", encoding="utf-8") as f:
        f.write("DAZN HIGHLIGHTS - VIDEO EMBEDDABILI\n")
        f.write(f"Generato il: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n")
        f.write(f"Totale video embeddabili trovati: {len(videos)}\n")
        f.write("=" * 100 + "\n\n")

        for i, v in enumerate(videos, 1):
            title = v.get('title', 'Titolo non disponibile')
            video_id = v.get('id')
            channel = v.get('channel', 'DAZN IT')

            thumb = f"https://i.ytimg.com/vi/{video_id}/maxresdefault.jpg"
            link = f"https://www.youtube.com/watch?v={video_id}"
            embed = f"https://www.youtube.com/embed/{video_id}?autoplay=1&rel=0"

            f.write(f"{i:3d}. {title}\n")
            f.write(f"   Canale     : {channel}\n")
            f.write(f"   Thumb      : {thumb}\n")
            f.write(f"   Link       : {link}\n")
            f.write(f"   Embed      : {embed}\n")
            f.write("-" * 100 + "\n\n")


# ================== MAIN ==================
if __name__ == "__main__":
    print("🚀 Inizio estrazione video embeddabili...\n")

    all_videos = []

    for ch in channels:
        print(f"→ Elaboro: {ch['name']} ...")
        videos = get_latest_videos_yt_dlp(ch['url'], MAX_VIDEOS_PER_CHANNEL)
        
        for video in videos:
            if video and 'id' in video:
                all_videos.append({
                    "id": video['id'],
                    "title": video.get('title', 'Titolo non disponibile'),
                    "channel": ch['name']
                })

        print(f"   Aggiunti {len(videos)} video embeddabili da {ch['name']}\n")

    if not all_videos:
        print("❌ Nessun video embeddabile trovato.")
        exit(1)

    save_to_txt(all_videos)

    print(f"✅ File salvato con successo!")
    print(f"   Totale video embeddabili: {len(all_videos)}")
    print(f"   File: {OUTPUT_TXT}")

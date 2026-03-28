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
        "name": "iNoob Gaming",
        "url": "https://www.youtube.com/@iNoobGaming/videos"
    },
    {
        "name": "Fabrizio Corona",
        "url": "https://www.youtube.com/@officialfabriziocorona/videos"
    },
    {
        "name": "Favij",
        "url": "https://www.youtube.com/@FavijTV/videos"
    },
    {
        "name": "Meme Official",
        "url": "https://www.youtube.com/@MEMEofficialITA/videos"
    },
    {
        "name": "Stockdroid",
        "url": "https://www.youtube.com/@stockdroid/videos"
    },
    {
        "name": "X2Marco",
        "url": "https://www.youtube.com/@X2Marco/videos"
    },
    {
        "name": "Leo",
        "url": "https://www.youtube.com/@leo/videos"
    },
    {
        "name": "Sedia",
        "url": "https://www.youtube.com/@LaSediaa2Gambe/videos"
    },
    {
        "name": "La Sedia Da Gaming",
        "url": "https://www.youtube.com/@lasediadagaming/videos"
    },
    {
        "name": "Poldo",
        "url": "https://www.youtube.com/@poldo/videos"
    },
    {
        "name": "Poldo Extra",
        "url": "https://www.youtube.com/@PoldoExtra/videos"
    },
    {
        "name": "Michele Molteni",
        "url": "https://www.youtube.com/@MolteniMichele/videos"
    },
    {
        "name": "Gabriele Vagnato",
        "url": "https://www.youtube.com/@gabrielevagnato/videos"
    },
    {
        "name": "Jakidale",
        "url": "https://www.youtube.com/@jakidale/videos"
    },
    {
        "name": "Techdale",
        "url": "https://www.youtube.com/@TechDale/videos"
    },
    {
        "name": "YungestMoonstar",
        "url": "https://www.youtube.com/@ymoonstar/videos"
    },
    {
        "name": "Thasup",
        "url": "https://www.youtube.com/@thasup/videos"
    },
    {
        "name": "Cicciogamer89",
        "url": "https://www.youtube.com/@CiccioGamer89/videos"
    },
    {
        "name": "Cicciogamer89 GamePlay",
        "url": "https://www.youtube.com/@CiccioGameplay89/videos"
    },
    {
        "name": "Grax",
        "url": "https://www.youtube.com/@Grax/videos"
    },
    {
        "name": "ControCalcio",
        "url": "https://www.youtube.com/@Controcalcio/videos"
    },
    {
        "name": "Riccardo Dose",
        "url": "https://www.youtube.com/@RiccardoDose94/videos"
    },
    {
        "name": "Nicolo Cumerlato",
        "url": "https://www.youtube.com/@nico.lato/videos"
    },
    {
        "name": "Giovanni Fois",
        "url": "https://www.youtube.com/@GiovanniFois/videos"
    },
    {
        "name": "Lollo Lacustre",
        "url": "https://www.youtube.com/@lollolacustre/videos"
    },
    {
        "name": "Aledellagiusta",
        "url": "https://www.youtube.com/@aledellagiusta/videos"
    },
    {
        "name": "Kappa Freneh",
        "url": "https://www.youtube.com/@Frenezy/videos"
    },
    {
        "name": "Il Ridoppiatore",
        "url": "https://www.youtube.com/@ILRidoppiatore/videos"
    },
    {
        "name": "Dado",
        "url": "https://www.youtube.com/@dadontheroad/videos"
    },
    {
        "name": "Andrea Galeazzi",
        "url": "https://www.youtube.com/@AndreaGaleazziVERIFICATO/videos"
    },
    {
        "name": "MikeShowSha",
        "url": "https://www.youtube.com/@MikeShowSha/videos"
    },
    {
        "name": "Blur Freebooter",
        "url": "https://www.youtube.com/@stalla_freebooter/videos"
    },
    {
        "name": "Surry",
        "url": "https://www.youtube.com/@surrealpower/videos"
    },
    {
        "name": "Surry And Chills",
        "url": "https://www.youtube.com/@SurryAndChill/videos"
    },
    {
        "name": "Dario Moccia Archives",
        "url": "https://www.youtube.com/@DarioMocciaArchives/videos"
    },
    {
        "name": "NerdMovieProductions",
        "url": "https://www.youtube.com/@NerdMovieProducti0ns/videos"
    },
    {
        "name": "Otto Climan",
        "url": "https://www.youtube.com/@OttoCliman/videos"
    },
    {
        "name": "ZW Jackson",
        "url": "https://www.youtube.com/@ZWJACKSON/videos"
    },
    {
        "name": "Fc Zeta Milano",
        "url": "https://www.youtube.com/@FCZetaMilano/videos"
    },
    {
        "name": "St3pNy",
        "url": "https://www.youtube.com/@MoD3rNSt3pNy/videos"
    },
    {
        "name": "St3pNy²",
        "url": "https://www.youtube.com/@St3pNy/videos"
    },
    {
        "name": "Techdale",
        "url": "https://www.youtube.com/@TechDale/videos"
    },
    {
        "name": "Stallions TV Blur",
        "url": "https://www.youtube.com/@StallionsTV/videos"
    },
    {
        "name": "Blur",
        "url": "https://www.youtube.com/@blurindietro/videos"
    },
    {
        "name": "Marza",
        "url": "https://www.youtube.com/@marzatv/videos"
    },
    {
        "name": "The Real Marza",
        "url": "https://www.youtube.com/@TheRealMarzaa/videos"
    },
    {
        "name": "Stormy",
        "url": "https://www.youtube.com/@S7ORMyyy/videos"
    },
    {
        "name": "The Show",
        "url": "https://www.youtube.com/@theshowisyou/videos"
    },
    # Aggiungi altri canali qui
    # {"name": "Nome Canale", "url": "https://www.youtube.com/@AltroCanale/videos"},
]

MAX_VIDEOS_PER_CHANNEL = 200
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

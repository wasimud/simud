import yt_dlp
import json

# ================== CONFIGURAZIONE ==================
channels = [
    {
        "name": "DAZN IT",
        "url": "https://www.youtube.com/@DAZNIT/videos"
    },
    # Aggiungi altri canali qui
    # {"name": "Nome Canale", "url": "https://www.youtube.com/@AltroCanale/videos"},
]

MAX_VIDEOS_PER_CHANNEL = 30
OUTPUT_FILE = "highlights.html"
# ====================================================

IFRAME_TEMPLATE = '''
<div style="position: fixed; top: 0; left: 0; width: 100vw; height: 100vh; background: #000; margin: 0; padding: 0; overflow: hidden; z-index: 999;">
    <iframe 
        style="position: absolute; top: 0; left: 0; width: 100%; height: 100%; border: none;"
        src="https://www.youtube.com/embed/{video_id}?autoplay=1&rel=0&playsinline=1" 
        title="{title}"
        frameborder="0" 
        allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share; fullscreen" 
        referrerpolicy="strict-origin-when-cross-origin" 
        allowfullscreen>
    </iframe>
</div>
'''

HTML_TEMPLATE = '''<!doctype html>
<html lang="it">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="referrer" content="strict-origin-when-cross-origin">
<title>YouTube Fullscreen Player</title>
<style>
:root{--a1:59,130,246;--a2:124,58,237;}
html,body{margin:0;min-height:100vh;background:#000 url('https://wallpapercave.com/wp/wp3202262.jpg') center/cover fixed;font-family:system-ui;color:#fff;}
.topbar{display:flex;align-items:center;gap:14px;padding:14px 18px;position:sticky;top:0;z-index:50;backdrop-filter:blur(10px);background:rgba(0,0,0,.7);}
h1{margin:0;font-size:28px;background:linear-gradient(90deg,rgb(var(--a1)),rgb(var(--a2)));-webkit-background-clip:text;color:transparent;}
.wrap{max-width:1700px;margin:0 auto;padding:20px;}
.cards{display:grid;grid-template-columns:repeat(auto-fill,minmax(280px,1fr));gap:24px;}
.card{aspect-ratio:16/9;border-radius:18px;overflow:hidden;position:relative;cursor:pointer;background:#111;border:2px solid rgba(255,255,255,.15);transition:all .25s;}
.card:hover{transform:scale(1.05);border-color:rgb(var(--a1));box-shadow:0 0 30px rgba(59,130,246,.6);}
.card:focus{outline:none;transform:translateY(-6px) scale(1.04);border:3px solid rgb(var(--a1));box-shadow:0 0 30px rgba(59,130,246,.8);}
.thumb{position:absolute;inset:0;background-size:cover;background-position:center;}
.meta{position:absolute;bottom:0;left:0;right:0;padding:14px;background:linear-gradient(180deg,transparent,rgba(0,0,0,.9));font-size:15px;font-weight:600;line-height:1.3;}
.channel-name{font-size:13px;opacity:0.8;margin-top:4px;}

/* ===== PLAYER ===== */
.player-overlay{
  position:fixed;inset:0;background:#000;z-index:9999;
  visibility:hidden;opacity:0;transition:.25s;
}
.player-overlay.active{visibility:visible;opacity:1}
.player-back{
  position:absolute;top:15px;left:15px;padding:12px 24px;border-radius:12px;
  background:rgba(0,0,0,.7);border:1px solid #fff;color:#fff;font-size:16px;
  z-index:10;cursor:pointer;
}
.player-back:focus{
  outline:none;border:2px solid rgb(var(--a1));box-shadow:0 0 18px rgba(59,130,246,.9);
}
</style>
</head>
<body>

<header class="topbar">
  <h1>Dazn HighLights</h1>
</header>

<main class="wrap">
  <div class="cards" id="cards"></div>
</main>

<div class="player-overlay" id="overlay">
  <button class="player-back" id="backBtn" tabindex="0">← Indietro (Esc o Freccia ↓)</button>
  <div id="player"></div>
</div>

<script>
const allVideos = {videos_json};

let currentIndex = 0;
let lastCardIndex = 0;
const overlay = document.getElementById('overlay');
const playerDiv = document.getElementById('player');
const backBtn = document.getElementById('backBtn');

function openVideo(index) {
  currentIndex = index;
  lastCardIndex = index;
  const v = allVideos[index];
  
  const html = `{iframe_template}`
    .replace(/{video_id}/g, v.id)
    .replace(/{title}/g, v.title.replace(/"/g, '&quot;'));
  
  playerDiv.innerHTML = html;
  overlay.classList.add('active');
  backBtn.focus();
}

function closeVideo() {
  overlay.classList.remove('active');
  playerDiv.innerHTML = '';
  setTimeout(() => {
    const cards = document.querySelectorAll('.card');
    if (cards[lastCardIndex]) cards[lastCardIndex].focus();
  }, 10);
}

backBtn.onclick = closeVideo;
backBtn.onkeydown = e => {
  if (['Enter', ' ', 'Escape', 'Backspace', 'ArrowDown'].includes(e.key)) {
    e.preventDefault();
    closeVideo();
  }
};

// ===== NAVIGAZIONE TASTIERA NEL PLAYER (come nell'IPTV) =====
document.addEventListener('keydown', e => {
  if (!overlay.classList.contains('active')) return;

  switch (e.key) {
    case 'ArrowRight':
      e.preventDefault();
      currentIndex = (currentIndex + 1) % allVideos.length;
      openVideo(currentIndex);
      break;

    case 'ArrowLeft':
      e.preventDefault();
      currentIndex = (currentIndex - 1 + allVideos.length) % allVideos.length;
      openVideo(currentIndex);
      break;

    case 'ArrowDown':
    case 'Escape':
    case 'Backspace':
      e.preventDefault();
      closeVideo();
      break;
  }
});

// ===== GENERAZIONE CARD =====
allVideos.forEach((v, i) => {
  const card = document.createElement('div');
  card.className = 'card';
  card.tabIndex = 0;
  card.innerHTML = `
    <div class="thumb" style="background-image:url('https://i.ytimg.com/vi/${v.id}/maxresdefault.jpg')"></div>
    <div class="meta">
      ${v.title}
      <div class="channel-name">${v.channel}</div>
    </div>
  `;
  
  card.onclick = () => openVideo(i);
  card.onkeydown = e => {
    if (e.key === 'Enter' || e.key === ' ') {
      e.preventDefault();
      openVideo(i);
    }
  };
  card.onfocus = () => lastCardIndex = i;
  
  document.getElementById('cards').appendChild(card);
});

// Focus iniziale sulla prima card
setTimeout(() => {
  document.querySelector('.card')?.focus();
}, 100);
</script>
</body>
</html>
'''

def get_latest_videos_yt_dlp(channel_url, limit=15):
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

# ================== MAIN ==================
if __name__ == "__main__":
    print("🚀 Inizio estrazione video...\n")

    all_videos = []
    for ch in channels:
        print(f"→ Elaboro: {ch['name']} ...")
        videos = get_latest_videos_yt_dlp(ch['url'], MAX_VIDEOS_PER_CHANNEL)
        
        for video in videos:
            if not video or 'id' not in video:
                continue
            all_videos.append({
                "id": video['id'],
                "title": video.get('title', 'Titolo non disponibile'),
                "channel": ch['name']
            })
        
        print(f"   Trovati {len(videos)} video\n")

    if not all_videos:
        print("❌ Nessun video trovato.")
        exit(1)

    videos_json = json.dumps(all_videos, ensure_ascii=False, indent=2)

    final_html = HTML_TEMPLATE.replace("{videos_json}", videos_json)\
                              .replace("{iframe_template}", IFRAME_TEMPLATE)

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write(final_html)

    print(f"✅ HTML creato con successo!")
    print(f"   Totale video: {len(all_videos)}")
    print(f"   File: {OUTPUT_FILE}")
    print("\n💡 Consigli:")
    print("   1. Apri con Live Server (VS Code)")
    print("   2. Usa la tastiera: frecce destra/sinistra per cambiare video")
    print("   3. Freccia giù / Esc / Backspace per tornare alla griglia")

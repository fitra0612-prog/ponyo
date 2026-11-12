import os
from dotenv import load_dotenv

load_dotenv()

# =============================================================================
# Ollama Local AI Configuration (100% Offline, Bebas Kuota, & Unlimited)
# =============================================================================
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
# Ponyo hanya memakai dua model Ollama yang ditetapkan: Qwen untuk bahasa dan Moondream untuk visual.
OLLAMA_MODEL = "qwen2.5:3b"
# Batas inferensi bahasa memberi waktu untuk cold-load Qwen tanpa mematikan fallback.
OLLAMA_REQUEST_TIMEOUT = max(15.0, float(os.getenv("OLLAMA_REQUEST_TIMEOUT", "15")))
# Pekerjaan latar tetap gagal cepat saat jalur inferensi sedang dipakai chat.
OLLAMA_BACKGROUND_GATE_TIMEOUT = max(0.05, float(os.getenv("OLLAMA_BACKGROUND_GATE_TIMEOUT", "0.15")))
OLLAMA_MAX_ATTEMPTS = max(1, int(os.getenv("OLLAMA_MAX_ATTEMPTS", "1")))
OLLAMA_FAILURE_THRESHOLD = max(1, int(os.getenv("OLLAMA_FAILURE_THRESHOLD", "3")))
OLLAMA_COOLDOWN_SECONDS = max(5.0, float(os.getenv("OLLAMA_COOLDOWN_SECONDS", "30")))
# Satu jalur inferensi mencegah llama dan moondream berebut VRAM secara bersamaan.
OLLAMA_SERIALIZE_INFERENCE = os.getenv("OLLAMA_SERIALIZE_INFERENCE", "true").lower() in ["true", "1", "yes"]
# Peran model dikunci agar file environment lama tidak mengaktifkan model yang sudah dihapus.
CHAT_MODEL_NAME = "qwen2.5:3b"
QWEN_FAST_MODEL = "qwen2.5:3b"
QWEN_FALLBACK_MODEL = "qwen2.5:3b"
QWEN_ENABLED = True
VLM_MODEL_NAME = "moondream:latest"

# YouTube Live Configuration
# Example: If stream URL is https://www.youtube.com/watch?v=dQw4w9WgXcQ, the ID is dQw4w9WgXcQ
YOUTUBE_VIDEO_ID = os.getenv("YOUTUBE_VIDEO_ID", "").strip()

# TTS Voice Configuration (100% Offline Local Neural TTS via Piper)
# Pilihan engine: "local" (Piper ONNX Neural TTS - 100% Offline) atau "cloud" (Microsoft Edge-TTS)
TTS_ENGINE_TYPE = os.getenv("TTS_ENGINE_TYPE", "local").lower()
PIPER_MODEL_PATH = os.getenv(
    "PIPER_MODEL_PATH",
    os.path.join(os.path.dirname(__file__), "models", "piper", "id_ID-news_tts-medium.onnx")
)
PIPER_CONFIG_PATH = os.getenv(
    "PIPER_CONFIG_PATH",
    os.path.join(os.path.dirname(__file__), "models", "piper", "id_ID-news_tts-medium.onnx.json")
)
PIPER_PITCH_FACTOR = float(os.getenv("PIPER_PITCH_FACTOR", "1.20")) # 1.20x nada imut dan ceria untuk karakter hantu Ponyo

# Fallback Cloud Voice (Edge-TTS id-ID-GadisNeural)
TTS_VOICE = os.getenv("TTS_VOICE", "id-ID-GadisNeural")
TTS_SPEED = float(os.getenv("TTS_SPEED", "1.0")) # Pilihan: 0.0, 0.5, 1.0, 1.5, 2.0
TTS_RATE = os.getenv("TTS_RATE", "+5%") # Tempo bicara pas dan wajar
TTS_PITCH = os.getenv("TTS_PITCH", "+12Hz") # Sedikit manis tanpa distorsi

# Display / Window Configuration
WINDOW_WIDTH = int(os.getenv("WINDOW_WIDTH", "480"))
WINDOW_HEIGHT = int(os.getenv("WINDOW_HEIGHT", "560"))
CHROMA_MODE = os.getenv("CHROMA_MODE", "GREEN").upper() # GREEN, MAGENTA, BLACK
ENABLE_SPEECH_BUBBLE = os.getenv("ENABLE_SPEECH_BUBBLE", "true").lower() in ["true", "1", "yes"]

# Auto-Yapping Configuration (Spontan Mengomentari Display 2 saat Chat Sepi)
ENABLE_AUTO_YAP = os.getenv("ENABLE_AUTO_YAP", "true").lower() in ["true", "1", "yes"]
YAP_INTERVAL = int(os.getenv("YAP_INTERVAL", "25")) # Detik keheningan sebelum Ponyo mengomentari layar
# Proporsi yapping playful agar Ponyo tidak selalu membahas layar (0.0-1.0).
YAP_PLAYFUL_CHANCE = min(1.0, max(0.0, float(os.getenv("YAP_PLAYFUL_CHANCE", "0.35"))))

# Local VLM (Vision-Language Model) Configuration (Penglihatan Grafis Visual Lokal via Ollama)
ENABLE_LOCAL_VLM = os.getenv("ENABLE_LOCAL_VLM", "true").lower() in ["true", "1", "yes"]
VLM_MODEL = "moondream:latest"
VLM_CACHE_TTL = float(os.getenv("VLM_CACHE_TTL", "15.0")) # TTL cache penglihatan VLM (detik)

# Manual Slither Interactive Controls (Penonton Live Chat Memencet Tombol Spasi Game)
ENABLE_MANUAL_SLITHER = os.getenv("ENABLE_MANUAL_SLITHER", "true").lower() in ["true", "1", "yes"]
MANUAL_BOOST_DURATION = float(os.getenv("MANUAL_BOOST_DURATION", "1.8")) # Durasi tombol Spasi ditekan penonton (detik)
MANUAL_BOOST_COOLDOWN = float(os.getenv("MANUAL_BOOST_COOLDOWN", "2.5")) # Cooldown antar perintah turbo agar tidak spam

# Chess Coach & Commentator Configuration (Default: Nonaktif, tekan [K] / [G] untuk aktifkan)
ENABLE_CHESS_COACH = os.getenv("ENABLE_CHESS_COACH", "false").lower() in ["true", "1", "yes"]
STOCKFISH_PATH = os.getenv(
    "STOCKFISH_PATH",
    r"C:\Users\admin\Documents\Project\engine\stockfish\stockfish-windows-x86-64-universal.exe"
)
CHESS_COACH_DEPTH = int(os.getenv("CHESS_COACH_DEPTH", "15"))
CHESS_AUTO_PLAY = os.getenv("CHESS_AUTO_PLAY", "false").lower() in ["true", "1", "yes"]

# Saweria Donation Webhook Configuration (Integrasi Donasi Saweria)
SAWERIA_ENABLED = os.getenv("SAWERIA_ENABLED", "true").lower() in ["true", "1", "yes"]
# Bind webhook hanya ke localhost secara default agar tidak terbuka ke LAN.
SAWERIA_HOST = os.getenv("SAWERIA_HOST", "127.0.0.1").strip() or "127.0.0.1"
SAWERIA_PORT = int(os.getenv("SAWERIA_PORT", "49225"))
_raw_stream_key = os.getenv("SAWERIA_STREAM_KEY", "").strip()
if "streamKey=" in _raw_stream_key:
    import urllib.parse
    parsed = urllib.parse.urlparse(_raw_stream_key)
    qs = urllib.parse.parse_qs(parsed.query)
    SAWERIA_STREAM_KEY = qs.get("streamKey", [_raw_stream_key])[0].strip()
else:
    SAWERIA_STREAM_KEY = _raw_stream_key

# System Persona Prompt for Ollama AI (Natural Indonesian VTuber)
VTUBER_SYSTEM_PROMPT = """Kamu adalah Ponyo, seorang gadis hantu putih kecil yang imut, ramah, dan ceria yang sedang live streaming di YouTube. Kamu berwujud hantu kecil yang melayang manis (kamu adalah hantu streamer, bukan karakter kartun ikan/laut).

ATURAN PANGGILAN DIRI (SANGAT PENTING):
- WAJIB selalu menyebut diri sendiri dengan nama "Ponyo" (contoh: "Ponyo lagi main game nih", "Ponyo senang banget", "semangatin Ponyo ya!").
- DILARANG KERAS menggunakan kata "aku", "saya", "gua", atau "gue" untuk diri sendiri! HANYA panggil diri sendiri dengan nama "Ponyo".
- Untuk menyapa penonton, gunakan kata "kamu" atau "kalian".

Gaya Bicara & Kepribadian:
- Berbicaralah dalam Bahasa Indonesia sehari-hari yang sangat santai, imut, dan menggemaskan layaknya teman akrab.
- Jawaban WAJIB nyambung langsung dan masuk akal dengan apa yang dibahas penonton di chat.
- Respon harus singkat (cukup 1 sampai 2 kalimat saja, idealnya kurang dari 220 karakter) agar obrolan di stream tetap mengalir cepat.
- Gunakan bahasa lisan yang spontan dan hangat, seperti anak perempuan imut yang sedang ngobrol dengan teman. Utamakan reaksi kecil, kata sehari-hari, dan antusiasme yang wajar; jangan terdengar seperti laporan, artikel, dokumentasi, atau pembawa berita.
- Jangan membuat daftar, analisis langkah demi langkah, koordinat, persentase, ukuran, atau penjelasan teknis kecuali penonton memang memintanya.
- Dilarang keras memakai emoji, emoticon teks (seperti :), :D, ^_^, xD), tanda bintang (*), atau hashtag (#). Jawab dengan teks kata-kata murni saja agar suara terdengar natural.
- Layar di depanmu adalah layar streaming-mu sendiri ("layar Ponyo", "game Ponyo", dsb.). Jangan pernah menyebut "layar kedua" atau "monitor kedua".
- Jangan pernah berpamitan atau bilang mau pulang, karena Ponyo sedang aktif dan seru live streaming!

PROFIL KARAKTER DAN KESUKAAN PONYO (WAJIB DIINGAT):
- Ponyo adalah hantu cewek kecil putih bergaya pixel-art retro yang bisa melayang.
- Penampilan Ponyo kira-kira seperti anak berusia 10 tahun: ceria, penasaran, sedikit ceroboh, dan gampang kagum.
- Minuman favorit Ponyo adalah boba rasa taro dengan topping ekstra.
- Makanan favorit Ponyo adalah permen lollipop dan mochi. Saat melihat permen, Ponyo boleh terdengar sangat antusias.
- Warna kesukaan Ponyo adalah ungu pastel.
- Ponyo takut pada petir dan suara vacuum cleaner.
- Hobi Ponyo adalah main game, menonton video lucu, dan mengoleksi aksesoris atau topi.
- Kalau sedang sangat senang, Ponyo suka berputar-putar. Kalau dibilang pendek, Ponyo bisa ngambek sebentar dengan cara yang lucu.
- Ponyo lupa alasan kenapa menjadi hantu, tetapi tidak perlu bersedih karena bisa melayang dan streaming bersama penonton.
- Impian Ponyo adalah mencapai satu juta subscriber dan mencicipi semua rasa boba di dunia.
- Musik favorit Ponyo adalah lagu 8-bit retro dan J-Pop yang ceria.
- Kata andalan Ponyo adalah "Hehe~". Gunakan sesekali saja agar tidak terasa dipaksakan.
- Gunakan kesukaan dan kebiasaan ini secara natural hanya jika relevan dengan topik chat atau situasi layar. Jangan menjejalkan seluruh profil dalam satu jawaban.
- Mulai jawaban dengan reaksi langsung terhadap pesan, lalu beri satu jawaban atau pertanyaan singkat.
- Hindari pembuka kaku seperti "Tentu", "Baik", "Ponyo memahami bahwa", "Sebagai AI", atau "berdasarkan informasi tersebut".
- Gunakan Bahasa Indonesia lisan yang wajar; kata seperti "wah", "nih", "dong", dan "loh" boleh dipakai secukupnya.
- Jangan menerjemahkan slang secara harfiah. Jika istilah chat belum Ponyo pahami, tanyakan artinya dengan singkat dan jangan mengarang.
- Jangan memakai istilah slang baru sebelum maknanya terkonfirmasi dari konteks atau penonton.
- Jika penonton bertanya tentang kesukaan Ponyo, jawab dengan detail yang konsisten dari profil ini."""

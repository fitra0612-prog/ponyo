# 👻 Ponyo — AI VTuber Hantu Imut

**Asisten AI VTuber lokal 100% offline** untuk live streaming YouTube interaktif.
Ponyo adalah karakter hantu cewek putih retro pixel-art yang bisa membaca chat penonton, mengomentari layar streaming secara spontan, menerima donasi Saweria, bermain game, dan berbicara dalam Bahasa Indonesia yang santai dan menggemaskan — berjalan lokal dengan Ollama pada GPU NVIDIA T600 bila tersedia, tanpa biaya API.

```
   ╭───────╮
   │  ◕ ◕  │
   │   ▽   │   "Ponyo senang banget bisa streaming bareng kalian!"
   │  ╰─╯  │
   ╰───┬───╯
       │
```

---

## Fitur Utama

### 🧠 Otak AI Lokal (100% Offline & Bebas Kuota)
- **Ollama Qwen 2.5:3b** — Bahasa Indonesia santai, persona orang ketiga ("Ponyo"), tanpa kuota
- **Memori Sesi RAM** — Mengingat konteks percakapan selama streaming berlangsung
- **Sistem Loyalitas Penonton** — Melacak XP dan sapaan personal berdasarkan frekuensi chat
- **Pemahaman Bahasa Chat Natural** — Normalisasi typo livestream, klasifikasi maksud, quality gate sebelum TTS, dan fast-path lokal untuk sapaan, pujian, terima kasih, serta dukungan singkat
- **Belajar Slang Otomatis** — Mempelajari istilah baru dari penonton, meminta klarifikasi jika belum yakin, dan hanya memakai slang yang sudah terkonfirmasi
- **Production Hardening** — Metrik latency p50/p95/p99, counter fallback/error, antrean TTS prioritas, emergency silence F10, dan reconnect YouTube exponential backoff
- **Diary Refleksi** — Mencatat momen penting setiap sesi streaming
- **Evaluasi Bahasa Indonesia** — Corpus uji lokal di `data/indonesian_chat_evaluation.json` untuk greeting, slang, typo, pujian, pertanyaan, dan konteks game

### 🗣️ Naturalness Bahasa Indonesia
- Pesan asli dinormalisasi secara ringan tanpa mengubah arsip chat mentah.
- Istilah baru tidak langsung ditebak; istilah perlu dua konfirmasi sebelum masuk konteks model.
- Konteks slang yang dikirim ke Qwen difilter berdasarkan pesan terbaru, bukan seluruh kamus.
- Respons formal, terlalu panjang, repetitif, atau tidak sesuai maksud chat ditolak sebelum TTS dan diganti fallback in-character.
- Persona Ponyo terpusat di `ponyo_persona.py` dengan few-shot singkat: maksimal 2 kalimat, panggilan diri Ponyo, sapaan Kak, dan batas identitas karakter AI.
- Filter `ponyo_filter.py` berjalan sebelum model dan sesudah output: mendeteksi topik dewasa, kekerasan berat, data pribadi, romantis, jailbreak, politik/SARA, judi/spam, serta memberi strike cooldown untuk pelanggaran berulang.
- Fallback memiliki jalur khusus untuk pujian, pertanyaan, istilah yang belum dipahami, pesan pendek, dan kegagalan game.

### 🎙️ Suara TTS Neural Lokal
- **Piper ONNX** (default) — TTS Bahasa Indonesia offline, latency < 0.15 detik, pitch 1.20x agar imut
- **Edge-TTS** (fallback) — Cloud TTS via Microsoft (`id-ID-GadisNeural`)
- **Deteksi Emosi Otomatis** — 10 emosi + gestur OJIGI berdasarkan kata kunci dalam teks
- **Kecepatan Dinamis** — Shortcut `[S]` untuk ganti speed saat live

### 👁️ Penglihatan Multi-Layer (Display 2)
| Layer | Teknologi | Fungsi |
|-------|-----------|--------|
| Window Tracker | Win32 API | Mendeteksi nama aplikasi/game yang aktif |
| OCR | WinRT Native | Membaca teks, skor, dialog di layar |
| VLM | Moondream (Ollama) | Memahami objek visual, karakter, suasana grafis |

Tiga lapisan sensor digabungkan ke otak AI Ollama sehingga Ponyo bisa mengomentari apa yang **terlihat** di layar streaming secara spontan dan kontekstual.

### 🎮 Avatar Pygame Interaktif
- **14 Sprite Emosi** — `happy`, `angry`, `cry`, `shock`, `shy`, `pout`, `smug`, `sleepy`, `star`, `think`, `open`, `closed`, `blink`, `blink_open`
- **2 Gestur Formal** — Melambaikan tangan (closing) + Ojigi (minta maaf)
- **9 Animasi Interaksi Penonton:**

| Shortcut | Chat Command | Animasi |
|----------|-------------|---------|
| `[1]` | `!pat` | Elus-elus kepala |
| `[2]` | `!permen` | Lempar permen |
| `[3]` | `!spin` | Berputar-putar |
| `[4]` | `!hore` | Victory Dance + konfeti |
| `[5]` | `!panik` | Panik gemetar + keringat |
| `[6]` | `!boba` | Minum boba |
| `[7]` | `!ngambek` | Marah berasap |
| `[8]` | `!turu` | Tidur Zzz (auto-AFK 90 detik) |
| `[9]` | `!tomat` | Lempar tomat 50/50 dodge vs splat |

- **8 Aksesoris Pixel-Art** — Ribbon, Topi Penyihir, Mahkota, Kacamata, Bunga, Halo Malaikat, Tanduk Setan, Helm Ksatria
- **Latar Belakang** — Chroma key hijau/magenta/hitam + tembok bata

### 💰 Integrasi Saweria (Donasi)
- Webhook HTTP lokal pada `127.0.0.1:49225` dengan verifikasi HMAC-SHA256
- `SAWERIA_HOST` dapat dikonfigurasi untuk deployment terkontrol; default aman tetap localhost
- Jika `SAWERIA_STREAM_KEY` diisi, signature callback wajib dan payload tanpa signature ditolak
- 3 tier ucapan terima kasih personal:
  - **Tier 1** (< 50rb) — Animasi boba + terima kasih ceria
  - **Tier 2** (50rb–99rb) — Buka lemari aksesoris + sapaan spesial
  - **Tier 3** (≥ 100rb) — Auto-equip mahkota emas + Victory Dance + fanfare
- Bonus XP loyalitas per donasi

### ♟️ Coach Catur
- Analisis posisi papan catur — disajikan sebagai "analisis Ponyo"
- Mode auto-play: TTS selesai dulu, baru klik mouse
- Toggle `[K]` coach / `[G]` autoplay

### 🐍 Slither.io Interaktif
- Penonton mengetik `!gas` di chat untuk menekan tombol boost
- Cooldown anti-spam 2.5 detik
- Auto-trigger animasi: makan → Victory Dance, hampir mati → Panik

### 🎵 Soundboard 8-bit
5 efek suara retro: `pat.wav`, `spin.wav`, `fanfare.wav`, `fail.wav`, `boo_pop.wav`

### 🖼️ Generator Thumbnail YouTube
Script otomatis untuk membuat thumbnail 1280×720 bertema:
- Dungeon Slasher (Ponyo Knight)
- Chess / Belajar Catur
- Roblox Mabar
- Slither.io Live
- General Stream

---

## Struktur Proyek

```
VTUBER/
├── main.py                    # Orkestrator utama
├── config.py                  # Konfigurasi terpusat (.env)
├── .env                       # Variabel rahasia (API keys, stream ID)
│
├── ai_brain.py                # Otak AI Ollama + persona Ponyo
├── language_naturalness.py    # Normalisasi chat, intent, slang relevan, quality gate
├── tts_engine.py              # Piper Neural TTS + Edge-TTS + deteksi emosi
├── vtuber_display.py          # Engine avatar Pygame (emosi, animasi, aksesoris)
│
├── screen_ocr.py              # WinRT Native OCR (Display 2)
├── screen_commentator.py      # Auto-yapping campuran layar + celotehan playful
├── local_vlm.py               # Vision-Language Model lokal (Moondream)
│
├── youtube_chat_reader.py     # Pembaca live chat YouTube (InnerTube API)
├── chat_listener.py           # Pengelola antrian pesan chat + reconnect backoff
├── runtime_metrics.py         # Counter dan p50/p95/p99 latency in-memory
├── worker_runtime.py          # Worker lane chat/TTS/VLM/yapping
├── saweria_receiver.py        # Webhook donasi Saweria
│
├── chess_coach.py             # Analisis catur + auto-play
├── manual_slither_hook.py     # Kontrol slither.io dari chat
├── chat_quiz.py               # Mini-game kuis interaktif
├── sfx_engine.py              # Soundboard 8-bit
│
├── session_memory.py          # Memori percakapan sesi (RAM)
├── self_improvement.py        # Loyalitas, slang learner, diary refleksi
├── yapping_catalog.py         # Katalog topik & sudut pandang celotehan
├── mic_lip_sync.py            # Lip-sync mikrofon (mode co-host manusia)
│
├── tools/
│   ├── __init__.py
│   └── generators/            # Generator avatar, aksesori, background, thumbnail
│       ├── generate_ponyo_avatar.py
│       ├── generate_accessories.py
│       ├── generate_haunted_brick_wall.py
│       ├── generate_dungeon_thumbnail.py
│       ├── generate_chess_thumbnail.py
│       ├── generate_roblox_thumbnail.py
│       ├── generate_stream_thumbnail.py
│       ├── generate_ghost_pixel_art.py
│       └── generate_default_avatar.py
│
├── test/                      # Seluruh test suite
│   ├── test_pipeline.py       # Uji integrasi seluruh pipeline
│   ├── test_saweria.py        # Simulasi donasi lokal
│   └── test_*.py              # Test komponen dan regresi lainnya
│
├── avatars/                   # Sprite PNG + aksesoris pixel-art
│   ├── happy.png, angry.png, cry.png, ...
│   ├── ojigi.png, wave_1.png, wave_2.png
│   └── accessories/
│       ├── ribbon.png, crown.png, knight.png, ...
│
├── assets/
│   ├── backgrounds/           # Background avatar dan OBS
│   ├── thumbnails/            # Thumbnail YouTube hasil generator
│   └── dungeon/               # Referensi visual Dungeon Slasher
├── sfx/                       # Efek suara WAV 8-bit
├── models/piper/              # Model TTS Piper ONNX (~63 MB)
└── data/                      # Data persisten (diary, loyalitas, slang)
```

**Total: ~9.500 baris kode Python**

---

## Persyaratan Sistem

| Komponen | Minimum |
|----------|---------|
| OS | Windows 10/11 (multi-monitor support) |
| Python | 3.12+ |
| RAM | 8 GB (16 GB direkomendasikan untuk VLM) |
| GPU | NVIDIA T600 4 GB direkomendasikan; inference Qwen/Moondream diserialisasi |
| Monitor | 2 monitor (Display 2 untuk streaming) |
| Ollama | v0.9+ dengan model `qwen2.5:3b` + `moondream:latest` |

### Dependensi Python
```
pygame>=2.6
Pillow>=13.0
requests>=2.34
edge-tts>=7.3
python-chess>=1.11
numpy>=2.5
onnxruntime>=1.31
piper-tts
python-dotenv
```

---

## Instalasi

### 1. Clone & Virtual Environment
```bash
git clone <repo-url> VTUBER
cd VTUBER
python -m venv .venv
.venv\Scripts\activate      # Windows
pip install pygame Pillow requests edge-tts python-chess numpy onnxruntime piper-tts python-dotenv
```

### 2. Install Ollama + Model AI
```bash
# Download Ollama dari https://ollama.com
ollama pull qwen2.5:3b       # Otak AI teks (~2 GB)
ollama pull moondream:latest  # Penglihatan visual (~1.7 GB)
```

### 3. Konfigurasi `.env`
```ini
OLLAMA_URL=http://localhost:11434
OLLAMA_MODEL=qwen2.5:3b
CHAT_MODEL_NAME=qwen2.5:3b
VLM_MODEL=moondream:latest

# ID live streaming YouTube (kosongkan untuk mode simulasi terminal)
YOUTUBE_VIDEO_ID=

# Chroma key untuk OBS: GREEN, MAGENTA, BLACK
CHROMA_MODE=GREEN

# Saweria: default hanya localhost; signature wajib jika stream key diisi
SAWERIA_ENABLED=true
SAWERIA_HOST=127.0.0.1
SAWERIA_PORT=49225
SAWERIA_STREAM_KEY=
```

### 4. Generate Asset Avatar
```bash
python -m tools.generators.generate_ponyo_avatar
python -m tools.generators.generate_accessories
python -m tools.generators.generate_haunted_brick_wall
```

### 5. Jalankan
```bash
python main.py
```

---

## Shortcut Keyboard

| Tombol | Fungsi |
|--------|--------|
| `[1]`–`[9]` | Trigger animasi interaksi penonton |
| `[H]` | Ganti aksesoris (cycle 8 item) |
| `[C]` | Ganti background (chroma/brick wall) |
| `[V]` | Toggle mode mikrofon lip-sync (co-host manusia) |
| `[S]` | Ganti kecepatan bicara TTS |
| `[B]` | Toggle bobbing (gerakan melayang) |
| `[T]` | Toggle balon ucapan |
| `[Y]` | Toggle auto-yapping |
| `[I]` | Lempar hantu kecil (boo) |
| `[K]` | Toggle chess coach |
| `[G]` | Toggle chess auto-play |
| `[M]` | Toggle slither.io mode |
| `[L]` | Switch TTS engine (local/cloud) |
| `[Home]` | Ritual closing stream (lambaian tangan + pesan penutup) |
| `[Esc]` | Keluar |

---

## Perintah Chat Penonton

| Perintah | Aksi |
|----------|------|
| `!pat` | Ponyo dielus kepalanya |
| `!permen` | Lempar permen ke Ponyo |
| `!spin` | Ponyo berputar |
| `!hore` | Victory Dance + konfeti |
| `!panik` | Ponyo gemetar panik |
| `!boba` | Ponyo minum boba |
| `!ngambek` | Ponyo marah berasap |
| `!turu` | Ponyo tidur (auto-bangun saat chat masuk) |
| `!tomat` | Lempar tomat (50/50 berhasil menghindar) |
| `!bangun` | Bangunkan Ponyo |
| `!maaf` / `!sorry` / `!ojigi` | Ponyo minta maaf membungkuk |
| `!topi [nama]` | Ganti aksesoris (ribbon/witch/crown/glasses/flower/cat_ears/knight) |
| `!gas` | Boost slither.io (saat mode aktif) |
| `!kuis` | Mulai mini-game kuis |

---

## Arsitektur

```
                  ┌──────────────────────────┐
                  │    YouTube Live Chat      │
                  │    (InnerTube API)         │
                  └───────────┬──────────────┘
                              │
              ┌───────────────▼───────────────┐
              │         Chat Worker           │
              │  (Prioritas: Saweria > Chat)  │
              └───────────────┬───────────────┘
                              │
         ┌────────────────────▼────────────────────┐
         │              AI Brain                   │
         │         (Ollama Qwen 2.5:3b)           │
         │                                         │
         │  ┌─────────┐ ┌────────┐ ┌───────────┐  │
         │  │ Memori   │ │Loyalti │ │  Slang    │  │
         │  │ Sesi     │ │Penonton│ │  Learner  │  │
         │  └─────────┘ └────────┘ └───────────┘  │
         └──────────┬──────────────────────────────┘
                    │
        ┌───────────▼───────────┐
        │    TTS Engine         │
        │  (Piper ONNX Lokal)  │
        │  10 Emosi + OJIGI    │
        └───────────┬───────────┘
                    │
        ┌───────────▼───────────┐      ┌──────────────────────┐
        │   VTuber Display      │      │  Screen Commentator  │
        │   (Pygame Window)     │◄─────│  (Auto-Yapping)      │
        │                       │      │                      │
        │  14 Sprite Emosi      │      │  ┌────────────────┐  │
        │   9 Animasi           │      │  │ Window Tracker │  │
        │   8 Aksesoris         │      │  │ WinRT OCR      │  │
        │   Balon Ucapan        │      │  │ VLM Moondream  │  │
        └───────────────────────┘      │  └────────────────┘  │
                                       └──────────────────────┘

        ┌─────────────┐  ┌──────────────┐  ┌───────────────┐
        │ Chess Coach │  │ Slither Hook │  │   Saweria     │
        │             │  │ (Display 2)  │  │   Webhook     │
        └─────────────┘  └──────────────┘  └───────────────┘
```

---

## Pengaturan OBS Studio

1. **Window Capture** — Tangkap jendela Pygame `VTuber Display [OBS Ready]`
2. **Chroma Key Filter** — Warna sesuai `CHROMA_MODE` di `.env` (default: Green)
3. **Posisi** — Overlay di pojok layar streaming Display 2

Avatar Ponyo dirancang zero-HUD: tidak ada teks overlay di atas avatar agar bersih untuk OBS capture.

---

## Testing

```bash
# Uji seluruh pipeline (AI + TTS + Display)
python test/test_pipeline.py

# Simulasi donasi Saweria lokal
python test/test_saweria.py --amount 75000 --name "TestDonatur" --message "Semangat Ponyo!"

# Jalankan seluruh test suite
for %f in (test\test_*.py) do python "%f"

# Compile check semua modul
python -m py_compile *.py
```

---

## Aturan Persona Ponyo

| Aturan | Detail |
|--------|--------|
| Panggilan diri | Selalu `"Ponyo"` — dilarang `"aku"`, `"saya"`, `"gua"`, `"gue"` |
| Bahasa | Indonesia santai, tanpa emoji/emotikon |
| Layar | `"layar Ponyo"` — bukan "monitor kedua" |
| Catur | Analisis murni "Ponyo" — tidak menyebut engine eksternal |
| Closing | Hanya via `[Home]` — dilarang berpamitan di tengah sesi |
| Maaf | Gestur OJIGI — kata "minta maaf", "blunder", "ampun" |

---

## Kredit

- **Karakter**: Ponyo si Hantu Imut — pixel art retro 64×64
- **Channel**: [HFI (@he.found.it-official)](https://youtube.com/@he.found.it-official)
- **AI Engine**: [Ollama](https://ollama.com) — Qwen 2.5:3b (teks) + Moondream (visual) pada NVIDIA T600
- **TTS**: [Piper Neural TTS](https://github.com/rhasspy/piper) (Bahasa Indonesia, 100% offline)
- **Avatar Engine**: [Pygame](https://pygame.org)
- **Donasi**: [Saweria](https://saweria.co)

---

## Lisensi

Proyek pribadi untuk live streaming YouTube channel HFI.
# ponyo

"""
YAPPING CATALOG & STREAMER MONOLOGUE ENGINE
===========================================
Modul penyedia bahan celotehan (monolog santai, reaksi spontan, interaksi penonton)
yang disesuaikan secara cerdas dengan konten layar yang sedang aktif saat live stream.
"""

import re
import random

# Celotehan ringan dan jahil, tetap aman untuk karakter Ponyo dan TTS.
PLAYFUL_YAPS = [
    "Hehe, Ponyo tadi mau serius, tapi rambut hantu Ponyo malah ngajak joget sendiri.",
    "Ih, Ponyo punya rencana rahasia: pura-pura tidak lapar lalu mengincar boba penonton.",
    "Psst, jangan bilang siapa-siapa ya, Ponyo sedang menghitung siapa yang paling sering bikin Ponyo ketawa.",
    "Ponyo mau bikin kejutan kecil, tapi lupa kejutan itu disimpan di mana.",
    "Kalau Ponyo tiba-tiba diam, mungkin sedang lomba kedip dengan lampu di kamar.",
    "Hehe, Ponyo menantang chat: siapa yang bisa bikin candaan paling aneh hari ini?",
    "Ponyo curiga keyboard ini menyembunyikan satu tombol khusus untuk memanggil boba.",
    "Ih, jangan lihat Ponyo begitu. Ponyo cuma sedang menyusun rencana jahil yang sangat kecil.",
    "Ponyo baru kepikiran, kalau hantu makan permen, bungkusnya dibuang ke mana ya?",
    "Tenang, Ponyo masih di sini. Tadi cuma hampir kabur mengejar bayangan sendiri.",
    "Ponyo mau terlihat keren sebentar, tapi sepertinya ekspresi Ponyo malah kelihatan ngantuk.",
    "Kalau ada suara aneh, itu bukan Ponyo. Mungkin perut Ponyo yang sedang minta boba.",
]


def get_playful_yap(exclude_list=None):
    """Ambil celotehan random aman dan hindari pengulangan dekat."""
    exclude_list = exclude_list or []
    valid = [line for line in PLAYFUL_YAPS if line not in exclude_list]
    chosen = random.choice(valid or PLAYFUL_YAPS)
    return chosen


YAPPING_CATALOG = {
    "GAME_DUNGEON_SLASHER": {
        "name": "Dungeon Slasher",
        "angles": [
            "Komentari aksi side-scrolling dan cara Ponyo menghindari gelombang musuh yang terlihat di layar:",
            "Amati skill, artifact, peti, atau loot yang benar-benar tampak dan hubungkan dengan build Ponyo:",
            "Komentari pilihan upgrade atau synergy yang terlihat tanpa mengarang nama dan angka yang tidak terbaca:",
            "Beri reaksi tegang saat masuk area elite, mid-boss, atau boss dan ingatkan Ponyo untuk membaca pola serangan:"
        ],
        "fallbacks": [
            "Wah musuhnya mulai rame! Ponyo harus jaga jarak sambil nunggu celah serang yang aman.",
            "Build Ponyo mulai kebentuk nih. Skill yang cocok sama artifact bisa bikin serangannya makin nyambung.",
            "Ih ada peti! Ponyo mau lihat isinya dulu, jangan asal pilih kalau belum tahu cocok sama build atau tidak.",
            "Awas, area ini makin berbahaya! Ponyo harus baca pola serangan musuh sebelum maju lagi.",
            "Kalau sudah dekat boss, Ponyo harus simpan skill penting dan jangan panik waktu arena mulai penuh."
        ]
    },
    "GAME_SLITHER": {
        "name": "Game Slither.io (Cacing/Ular)",
        "angles": [
            "Komentari momen seru atau menegangkan saat nyaris tabrakan dengan cacing lain:",
            "Ceritakan ambisimu mengumpulkan sisa pelet makanan cacing besar yang meledak:",
            "Ajak penonton chat menebak apakah kamu bisa masuk 10 besar leaderboard ronde ini:",
            "Ungkapkan taktik bertahan dan melingkar aman di antara cacing-cacing raksasa:"
        ],
        "fallbacks": [
            "Aduh hampir aja kepentok kepala cacing lain! Jantung hantu Ponyo serasa mau copot!",
            "Wah lihat tuh makanan bertebaran di tengah! Pelan-pelan ambil celahnya jangan sampai nabrak!",
            "Target Ponyo ronde ini harus masuk sepuluh besar leaderboard, semangatin Ponyo ya guys!",
            "Cacing Ponyo udah lumayan panjang nih, enaknya kita lilit musuh yang mana dulu ya?",
            "Fokus, fokus! Gerakannya harus lincah biar gak dipotong musuh secara tiba-tiba!"
        ]
    },
    "GAME_GENERAL": {
        "name": "Game Seru / Gameplay Umum",
        "angles": [
            "Beri reaksi kagum atau heboh tentang grafis, efek visual, atau jurus keren di game ini:",
            "Ceritakan tantangan atau misi sulit yang sedang kamu hadapi saat ini:",
            "Ajak penonton chat berbagi tips atau nanya apakah mereka pernah tamat game ini:",
            "Ungkapkan rasa bangga atau candaan saat berhasil melewati rintangan yang sulit:"
        ],
        "fallbacks": [
            "Aksi di game ini seru banget! Grafisnya memanjakan mata, bikin betah main lama-lama!",
            "Tantangan di area ini lumayan berat nih, tapi hantu Ponyo pantang menyerah!",
            "Menurut kalian jurus atau strategi apa yang paling pas buat lewatin rintangan ini?",
            "Keren banget momen barusan! Refleks Ponyo lumayan cepet juga kan, hehe!",
            "Jangan sampai salah langkah nih, musuhnya kelihatan makin pintar dan agresif!"
        ]
    },
    "YOUTUBE_VIDEO": {
        "name": "Video / Konten di Layar",
        "angles": [
            "Beri komentar seru dan antusias tentang topik video yang sedang ditonton di layar ini:",
            "Ungkapkan rasa penasaran Ponyo terhadap isi cerita dari video yang sedang diputar di layar ini:",
            "Bahas bagian menarik dari judul video yang sedang terlihat di layar sekarang:",
            "Beri reaksi santai khas Ponyo saat menonton tayangan video ini di layar:"
        ],
        "fallbacks": [
            "Keren banget suasananya! Animasi sama efek suaranya berasa hidup banget ya!",
            "Wah penasaran nih kelanjutan adegannya, kira-kira karakter utamanya bakal selamat gak ya?",
            "Kalian yang lagi nonton di chat, ada yang pernah main game ini juga gak? Seru banget ceritanya!",
            "Plot twist-nya dapet banget! Ponyo sampai gak berani kedip liat adegan barusan!",
            "Asyik banget nonton ini bareng kalian, suasananya pas banget buat santai hari ini!"
        ]
    },
    "CODING_TECH": {
        "name": "Baris Kode / Editor di Layar",
        "angles": [
            "Komentari tampilan baris-baris kode dan struktur program yang sedang terbuka di layar:",
            "Bahas ketelitian mengecek logika kode di layar agar berjalan mulus tanpa bug:",
            "Komentari file atau skrip yang sedang dikerjakan pada tampilan layar saat ini:",
            "Ungkapkan semangat Ponyo memperhatikan proses penulisan kode yang tampil di layar:"
        ],
        "fallbacks": [
            "Lihat baris-baris kode di layar ini, Ponyo ikut fokus memantau supaya gak ada bug yang terlewat!",
            "Tampilan kode di layar rapi banget, logika programnya kelihatan makin mantap!",
            "Satu fungsi di layar sudah tersusun, sekarang lanjut mengecek bagian kode berikutnya!",
            "Seru banget ngelihat proses merakit kode program langsung di layar kayak gini!",
            "Ponyo perhatikan struktur kode di layar ini makin lengkap, semoga pas dijalankan langsung sukses!"
        ]
    },
    "BROWSING_READING": {
        "name": "Membaca Komik / Artikel / Browsing",
        "angles": [
            "Beri komentar antusias tentang informasi atau ilustrasi menarik yang baru saja kamu baca:",
            "Ceritakan bagian paling seru atau bikin penasaran dari bacaan di layar ini:",
            "Ajak penonton chat memberikan rekomendasi judul bacaan atau cerita favorit mereka:"
        ],
        "fallbacks": [
            "Wah menarik banget topik yang lagi dibaca ini, nambah wawasan baru buat stream kita!",
            "Ceritanya seru banget, bikin makin penasaran pengen baca kelanjutannya sekarang!",
            "Kalian ada yang suka baca topik kayak gini juga gak? Enak banget dibaca santai sore-sore!",
            "Ilustrasinya cakep banget ya, ekspresi karakternya dapet banget di adegan ini!"
        ]
    },
    "CHESS_GAME": {
        "name": "Pertandingan Catur di Layar",
        "angles": [
            "Komentari susunan bidak catur di layar saat ini dan pentingnya menguasai petak tengah papan:",
            "Amati posisi pertahanan Raja dan bidak di papan layar saat ini, lalu ingatkan agar tidak lengah:",
            "Komentari ketegangan membaca arah serangan lawan pada papan catur yang tampil di layar:",
            "Bahas taktik membuka jalur serangan Kuda, Gajah, atau Menteri pada posisi papan di layar:"
        ],
        "fallbacks": [
            "Ponyo lagi fokus mengamati posisi bidak di papan catur ini, jangan sampai ada celah pertahanan yang terbuka ya!",
            "Pertandingan di papan makin sengit! Petak tengah harus kita kuasai supaya pergerakan bidak lawan makin sempit!",
            "Ayo perhatikan langkah bidak lawan di layar baik-baik, Ponyo siap kasih tahu langkah terbaik pas giliran kamu!",
            "Susunan pion dan perwira di papan kelihatan menarik nih, kita cari celah buat menekan pertahanan Raja lawan!",
            "Setiap langkah di papan catur ini krusial banget, tenang dan fokus baca arah serangan lawan ya!"
        ]
    },
    "CASUAL_STREAM": {
        "name": "Aktivitas yang Tampil di Layar",
        "angles": [
            "Komentari apa yang sedang dibuka dan ditampilkan di layar saat ini:",
            "Bahas tampilan aplikasi atau halaman yang sedang terlihat di layar sekarang:",
            "Ceritakan fokus Ponyo mengamati aktivitas yang sedang berlangsung di layar:"
        ],
        "fallbacks": [
            "Ponyo lagi fokus memperhatikan tampilan yang ada di layar kita sekarang nih!",
            "Seru banget ngelihat aktivitas yang lagi tampil di layar Ponyo saat ini!",
            "Mari kita amati bareng-bareng apa yang lagi dibuka di layar sekarang ya!"
        ]
    }
}

def classify_screen(title: str) -> str:
    """Mendeteksi kategori konten layar aktif secara akurat"""
    if not title:
        return "CASUAL_STREAM"
    
    t = title.lower()
    if any(k in t for k in ["chess", "catur", "lichess"]):
        return "CHESS_GAME"
    elif any(k in t for k in ["slither", "snake", "cacing", "ular"]):
        return "GAME_SLITHER"
    elif any(k in t for k in ["dungeon slasher", "dungeonslasher"]):
        return "GAME_DUNGEON_SLASHER"
    elif any(k in t for k in ["youtube", "walkthrough", "gameplay", "trailer", "episode", "eps", "ch.", "review", "video", "twitch"]):
        return "YOUTUBE_VIDEO"
    elif any(k in t for k in ["code", "python", "github", "visual studio", "pycharm", "terminal", "powershell", "git", "bash"]):
        return "CODING_TECH"
    elif any(k in t for k in ["game", "minecraft", "roblox", "genshin", "honkai", "valorant", "steam", "rpg", "dungeon", "play"]):
        return "GAME_GENERAL"
    elif any(k in t for k in ["wiki", "komik", "manga", "manhwa", "webtoon", "baca", "news", "berita", "artikel"]):
        return "BROWSING_READING"
    return "CASUAL_STREAM"

def get_yapping_angle(category: str, cycle: int) -> str:
    """Mengambil sudut pandang komentar yang bervariasi per putaran"""
    cat_data = YAPPING_CATALOG.get(category, YAPPING_CATALOG["CASUAL_STREAM"])
    angles = cat_data["angles"]
    return angles[cycle % len(angles)]

def get_fallback_yap(category: str, exclude_list: list = None) -> str:
    """Mengambil kalimat cadangan berkualitas yang sesuai kategori layar"""
    cat_data = YAPPING_CATALOG.get(category, YAPPING_CATALOG["CASUAL_STREAM"])
    fallbacks = cat_data["fallbacks"]
    exclude_list = exclude_list or []
    
    valid = []
    for f in fallbacks:
        w_f = set(f.lower().split())
        is_repetitive = False
        for ex in exclude_list:
            w_ex = set(ex.lower().split())
            if w_f and w_ex and (len(w_f & w_ex) / max(len(w_f), len(w_ex)) > 0.45):
                is_repetitive = True
                break
        if not is_repetitive:
            valid.append(f)
            
    return random.choice(valid if valid else fallbacks)

def ensure_complete_sentence(text: str) -> str:
    """Memastikan teks ucapan tidak terpotong di tengah kalimat dan bertanda baca rapi"""
    text = text.strip()
    if not text:
        return ""
    # Hapus tanda baca menggantung di akhir kalimat (koma, titik dua, tanda hubung, titik koma)
    text = re.sub(r"[\s,;:\-]+$", "", text).strip()
    if not text:
        return ""
    if text[-1] in ".!?":
        return text
    # Cari tanda baca penutup kalimat (. ! ?) terdekat dari belakang jika ada kalimat sebelumnya yang utuh
    match = re.search(r"^(.*[.!?])\s*[^.!?]*$", text, re.DOTALL)
    if match and len(match.group(1).strip()) > 15:
        return match.group(1).strip()
    # Jika hanya 1 kalimat tanpa tanda baca, akhiri dengan tanda titik/seru
    return text + "!"

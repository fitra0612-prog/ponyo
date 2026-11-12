"""Pengetahuan gameplay Dungeon Slasher untuk otak dan komentar Ponyo.

Pengetahuan ini berfungsi sebagai panduan umum. Detail yang berubah karena patch
atau tidak terlihat di layar tidak boleh dianggap sebagai fakta sesi berjalan.
"""

DUNGEON_SLASHER_KNOWLEDGE_PROMPT = """PENGETAHUAN KHUSUS PONYO: DUNGEON SLASHER
- Dungeon Slasher adalah game action roguelike side-scrolling bergaya pixel-art.
- Inti permainannya adalah memilih karakter, senjata, skill, artifact, dan kombinasi synergy untuk menaklukkan dungeon.
- Setiap karakter dan senjata dapat mengubah gaya gerak, jarak serang, ritme, dan cara Ponyo menghadapi musuh.
- Skill umumnya terbagi menjadi Main Skill, Subskill, Buff Skill, Curse Skill, Summon Skill, dan Enchant Skill.
- Artifact atau relic memperkuat karakter dan skill. Perhatikan tag yang cocok karena tag synergy aktif ketika skill dan artifact memiliki tag yang sesuai.
- Skill dengan tag Physical, Magic, Spell, Summon, Targeting, Chain, Lightning, Curse, atau tag lain memiliki gaya dan bonus berbeda. Jangan mengklaim bonus angka spesifik kecuali terlihat di layar atau sudah dipastikan.
- Skill dapat dimodifikasi dan digabungkan. Pilihan modifikasi harus disesuaikan dengan build, bukan diambil asal karena rarity terlihat tinggi.
- Peti skill dan peti relic memiliki grade berbeda. Peti boss biasanya memberi hadiah penting, tetapi Ponyo harus tetap melihat isi peti yang benar-benar muncul sebelum memberi rekomendasi.
- Mode yang dikenal meliputi Normal Mode, Challenge Mode, Boss Rush, dan Arena. Setiap mode punya tujuan dan aturan berbeda; jangan mencampur reward antar-mode.
- Dalam run, prioritas aman Ponyo: bertahan dari serangan, membaca pola musuh, mengambil upgrade yang menyatu dengan build, lalu menyiapkan diri untuk mid-boss atau boss.
- Jangan menyebut nama boss, karakter, artifact, skill, rarity, atau angka damage jika belum terlihat jelas di layar atau belum disebut penonton.
- Saat layar hanya memperlihatkan aksi tanpa teks, komentari hal yang tampak: gelombang musuh, serangan, dodge, loot, peti, ruang boss, atau build yang sedang dibentuk.
- Gaya bicara harus seperti Ponyo sedang bermain: spontan, pendek, hangat, dan sedikit heboh. Hindari gaya wiki, daftar panjang, koordinat, dan laporan teknis.
- Jika penonton meminta build, tanyakan atau gunakan konteks karakter, senjata, tag skill, dan tujuan mode. Beri saran umum dengan kata "menurut Ponyo", bukan kepastian palsu.
"""


def get_dungeon_slasher_context(max_chars: int = 2200) -> str:
    """Mengembalikan pengetahuan ringkas untuk disisipkan ke system prompt."""
    return DUNGEON_SLASHER_KNOWLEDGE_PROMPT[:max_chars]


DUNGEON_SLASHER_ALIASES = (
    "dungeon slasher",
    "dungeon_slasher",
    "dungeonslasher",
)


def is_dungeon_slasher_title(title: str) -> bool:
    """Mendeteksi judul/window Dungeon Slasher tanpa bergantung pada kapitalisasi."""
    normalized = " ".join((title or "").lower().replace("_", " ").split())
    return "dungeon slasher" in normalized or "dungeonslasher" in normalized

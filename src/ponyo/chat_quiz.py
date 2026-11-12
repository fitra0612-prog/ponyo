"""
CHAT QUIZ & TEBAK-TEBAKAN INTERAKTIF UNTUK PONYO VTUBER (SARAN NOMOR 4)
=======================================================================
Mengelola mini-game tebak-tebakan kata, teka-teki hantu, dan kuis lucu
secara real-time dengan penonton live stream YouTube.
Pemenang yang berhasil menjawab benar akan mendapatkan bonus +50 XP
pada sistem Viewer Loyalty dan memicu soundboard fanfare!
"""

import time
import random
import re
from typing import Optional, Dict

QUIZ_DATABASE = [
    {
        "id": 1,
        "question": "Pintu apa yang didorong sepuluh orang pun tidak bakal bisa terbuka?",
        "answers": ["pintu geser", "geser", "sliding door"],
        "punchline": "Karena dibukanya harus digeser, bukan didorong!",
        "hint": "Cara membukanya bukan didorong, tapi diseret ke samping..."
    },
    {
        "id": 2,
        "question": "Gajah naik becak yang kelihatan apanya hayo?",
        "answers": ["bohong", "bohongnya", "kelihatan bohong", "boong"],
        "punchline": "Kelihatan bohongnya dong, mana muat gajah naik becak!",
        "hint": "Coba pikir masuk akal gak kalau ada gajah naik becak?"
    },
    {
        "id": 3,
        "question": "Hewan apa yang paling bersaudara?",
        "answers": ["katak", "katak beradik", "kodok beradik"],
        "punchline": "Katak beradik! Seperti kakak beradik!",
        "hint": "Hewan amfibi yang suka lompat-lompat dan bersuara kwek-kwek..."
    },
    {
        "id": 4,
        "question": "Ikan apa yang matanya paling banyak?",
        "answers": ["teri", "ikan teri", "teri sekilo", "teri 1 kilo", "ikan teri sekilo"],
        "punchline": "Ikan teri satu kilo! Matanya ada ribuan!",
        "hint": "Ikan kecil-kecil asin kalau dibeli dalam jumlah satu kilo..."
    },
    {
        "id": 5,
        "question": "Rambut putih namanya uban, rambut merah namanya pirang, kalau rambut hijau namanya apa?",
        "answers": ["rambutan", "rambutan belum matang", "rambutan mentah", "rambutan hijau"],
        "punchline": "Rambutan yang belum matang!",
        "hint": "Bukan rambut kepala manusia, tapi nama buah manis berambut..."
    },
    {
        "id": 6,
        "question": "Benda apa yang kalau dipotong malah semakin tinggi?",
        "answers": ["celana", "celana panjang"],
        "punchline": "Celana panjang kalau dipotong bawahnya jadi celana tinggi alias pendek!",
        "hint": "Pakaian yang dipakai di kaki..."
    },
    {
        "id": 7,
        "question": "Lemari apa yang bisa dimasukkan ke dalam kantong saku?",
        "answers": ["limaribu", "lima ribu", "5 ribu", "5000", "lemari-buan", "lemaribuan"],
        "punchline": "Lemari-buan rupiah! Lembaran uang lima ribuan!",
        "hint": "Pelesetan dari pecahan uang kertas..."
    },
    {
        "id": 8,
        "question": "Kenapa dokter kalau mau operasi mulutnya ditutup masker?",
        "answers": ["gak kelihatan", "tidak kelihatan", "mata", "ketutup matanya", "buta"],
        "punchline": "Kalau matanya yang ditutup masker, dokternya gak bisa lihat dong!",
        "hint": "Coba bayangkan kalau masker dipasang di mata dokter..."
    },
    {
        "id": 9,
        "question": "Kutu apa yang paling menyeramkan bagi manusia?",
        "answers": ["kutukan", "kutu kan"],
        "punchline": "Kutu-kan penyihir atau kutukan kuno!",
        "hint": "Bukan serangga kepala, tapi mantra sihir gelap..."
    },
    {
        "id": 10,
        "question": "Belut apa yang paling berbahaya dan bikin pusing?",
        "answers": ["belutang", "belut-ang", "hutang", "utang"],
        "punchline": "Belut-ang banyak ke teman alias terlilit utang!",
        "hint": "Pelesetan dari kewajiban pinjam uang yang belum dibayar..."
    },
    {
        "id": 11,
        "question": "Sayur apa yang jago nyanyi lagu internasional?",
        "answers": ["coldplay", "kol", "sayur kol", "koldplay"],
        "punchline": "Kol-dplay! Band terkenal dari Inggris!",
        "hint": "Sayur lalapan kubis putih yang mirip nama band konser Chris Martin..."
    },
    {
        "id": 12,
        "question": "Daun apa yang sama sekali tidak boleh disentuh?",
        "answers": ["dont touch me", "daun touch me", "don't touch me"],
        "punchline": "Daun touch me! Bahasa Inggrisnya jangan sentuh aku!",
        "hint": "Pelesetan bahasa Inggris: Don't touch me..."
    },
    {
        "id": 13,
        "question": "Burung apa yang suka menolak ajakan?",
        "answers": ["gagak", "burung gagak", "gak", "nggak"],
        "punchline": "Burung Ga-gak! Bunyinya gak gak gak!",
        "hint": "Burung hitam misterius yang suka bilang 'Gak! Gak! Gak!'..."
    },
    {
        "id": 14,
        "question": "Benda apa yang selalu berjalan tapi tidak punya kaki?",
        "answers": ["jam", "jam dinding", "arloji", "jam tangan", "waktu"],
        "punchline": "Jam dinding! Jarumnya muter jalan terus tanpa kaki!",
        "hint": "Penunjuk waktu yang berdetik tik-tok di dinding..."
    },
    {
        "id": 15,
        "question": "Benda apa yang punya mata tapi tidak bisa melihat?",
        "answers": ["jarum", "jarum jahit"],
        "punchline": "Jarum jahit! Lubang benangnya disebut mata jarum!",
        "hint": "Alat jahit runcing tempat memasukkan benang..."
    },
    {
        "id": 16,
        "question": "Apa yang selalu datang tapi tidak pernah tiba hari ini?",
        "answers": ["besok", "hari esok", "tomorrow"],
        "punchline": "Hari esok! Pas sampai di hari itu, namanya berubah jadi hari ini!",
        "hint": "Hari setelah hari ini..."
    },
    {
        "id": 17,
        "question": "Benda apa yang makin diisi malah semakin ringan dan melayang?",
        "answers": ["balon", "balon gas", "balon helium", "balon udara"],
        "punchline": "Balon gas helium! Makin diisi gas makin melayang ke langit!",
        "hint": "Benda karet warna-warni pesta ulang tahun..."
    },
    {
        "id": 18,
        "question": "Siapakah orang yang memotong rambut tiap hari tapi tidak pernah botak?",
        "answers": ["tukang cukur", "barber", "barbershop", "tukang potong rambut"],
        "punchline": "Tukang cukur rambut! Yang dipotong kan rambut pelanggannya!",
        "hint": "Profesi pemotong rambut di salon atau barbershop..."
    },
    {
        "id": 19,
        "question": "Siapakah yang selalu tidur memakai sepatu?",
        "answers": ["kuda"],
        "punchline": "Kuda! Tapal sepatunya nempel terus bahkan saat tidur!",
        "hint": "Hewan pelari kencang berkaki empat yang punya tapal besi..."
    },
    {
        "id": 20,
        "question": "Bebek apa yang jalannya selalu belok ke kiri?",
        "answers": ["dikunci stang", "kunci stang", "stang"],
        "punchline": "Bebek motor yang dikunci stang ke kiri!",
        "hint": "Bukan unggas hidup, tapi jenis motor jadul yang diparkir..."
    },
    {
        "id": 21,
        "question": "Buah apa yang paling pemberani dan pantang mundur?",
        "answers": ["semangka", "buah semangka"],
        "punchline": "Semang-ka! Semangat terus, pantang mundur!",
        "hint": "Buah besar berbiji hijau dalamnya merah manis..."
    },
    {
        "id": 22,
        "question": "Hantu apa yang suka jajan makanan di kantin?",
        "answers": ["hantu lapar", "lapar", "hantu jajan"],
        "punchline": "Hantu yang lagi lapar banget kayak Ponyo!",
        "hint": "Perasaan perut keroncongan minta makan..."
    }
]


class ChatQuizEngine:
    def __init__(self):
        self.active_quiz: Optional[Dict] = None
        self.start_time: float = 0.0
        self.timeout_s: float = 65.0
        self.used_ids = set()

    def is_active(self) -> bool:
        if self.active_quiz is None:
            return False
        # Cek apakah waktu kuis sudah kedaluwarsa
        if time.time() - self.start_time > self.timeout_s:
            return False
        return True

    def start_new_quiz(self, author: str = "") -> str:
        """Memulai satu ronde kuis baru dan mengembalikan kalimat ucapan pembuka Ponyo"""
        # Pilih soal yang belum baru saja dipakai
        available = [q for q in QUIZ_DATABASE if q["id"] not in self.used_ids]
        if not available:
            self.used_ids.clear()
            available = QUIZ_DATABASE

        quiz = random.choice(available)
        self.used_ids.add(quiz["id"])
        self.active_quiz = quiz
        self.start_time = time.time()

        challenger = f"dari {author}" if author else ""
        text = (
            f"Kuis Tebak-tebakan Ponyo dimulai {challenger}! "
            f"Pertanyaannya: {quiz['question']} "
            f"Ayo yang tahu jawabannya langsung ketik di chat! Yang benar dapat 50 poin pengalaman!"
        )
        return text

    def get_hint(self) -> str:
        if not self.is_active():
            return "Saat ini belum ada kuis yang aktif nih. Ketik !kuis atau !tebak buat mulai tebak-tebakan ya!"
        return f"Petunjuk dari Ponyo: {self.active_quiz['hint']}"

    def forfeit(self) -> str:
        """Menyerah dan mengungkapkan jawaban"""
        if not self.is_active():
            return "Belum ada kuis yang berjalan nih. Ketik !kuis buat mulai tebak-tebakan bareng Ponyo!"
        ans = self.active_quiz["answers"][0].title()
        punch = self.active_quiz["punchline"]
        self.active_quiz = None
        return f"Yah pada menyerah nih! Jawabannya adalah: {ans}! {punch} Jangan sedih ya, ketik !kuis lagi nanti!"

    def check_timeout(self) -> Optional[str]:
        """Dipanggil dari loop utama jika kuis berjalan lebih dari timeout"""
        if self.active_quiz and (time.time() - self.start_time > self.timeout_s):
            ans = self.active_quiz["answers"][0].title()
            punch = self.active_quiz["punchline"]
            self.active_quiz = None
            return f"Waktu habis! Jawabannya adalah {ans}! {punch} Yuk ketik !kuis lagi kalau mau tebak-tebakan!"
        return None

    def check_answer(self, author: str, message: str) -> Optional[Dict]:
        """
        Memeriksa apakah pesan penonton memuat jawaban yang tepat.
        Mengembalikan dict hasil jika benar, atau None jika bukan jawaban.
        """
        if not self.is_active():
            return None

        msg_clean = message.strip().lower()
        # Normalisasi tanda baca
        msg_normalized = re.sub(r"[^\w\s]", " ", msg_clean)
        words = set(msg_normalized.split())

        matched = False
        matched_answer = self.active_quiz["answers"][0]

        for ans in self.active_quiz["answers"]:
            ans_clean = ans.lower().strip()
            # Cek kecocokan frasa utuh atau kata kunci
            if ans_clean in msg_clean:
                matched = True
                matched_answer = ans
                break
            # Cek jika jawaban 1 kata dan kata itu ada di dalam kata-kata chat
            if " " not in ans_clean and ans_clean in words:
                matched = True
                matched_answer = ans
                break

        if matched:
            punch = self.active_quiz["punchline"]
            quiz_copy = dict(self.active_quiz)
            self.active_quiz = None
            reply = (
                f"Yaaay pintar banget {author}! Jawabannya tepat sekali: {matched_answer.title()}! "
                f"{punch} Selamat ya, {author} berhasil dapat bonus 50 poin pengalaman!"
            )
            return {
                "correct": True,
                "winner": author,
                "answer": matched_answer,
                "punchline": punch,
                "reply": reply,
                "quiz": quiz_copy
            }

        return None


# Global instance siap pakai
chat_quiz = ChatQuizEngine()

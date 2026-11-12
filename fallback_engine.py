"""Context-aware offline fallback responses with anti-repetition rotation."""


class FallbackResponseEngine:
    def __init__(self):
        self._cursor = {}

    BANKS = {
        "greeting": [
            "Halo {author}, Ponyo senang kamu mampir ke live hari ini!",
            "Hai {author}, yuk ngobrol santai bareng Ponyo!",
            "Boo, selamat datang {author}! Pas banget datang saat stream lagi seru.",
            "Halo {author}, Ponyo baru saja menunggumu nih."
        ],
        "support": [
            "Makasih semangatnya, {author}. Dukungan kamu bikin Ponyo makin ceria!",
            "Ponyo jadi tambah berani lanjut berkat semangat dari {author}.",
            "Dukungan kecil dari {author} rasanya besar banget buat Ponyo!",
            "Hehe, semangatnya Ponyo terima baik-baik. Yuk lanjut seru-seruan!"
        ],
        "game": [
            "Ponyo masih fokus di {game}, tapi obrolan {author} bikin suasananya makin rame.",
            "Momen di {game} ini lumayan menegangkan, {author}. Ponyo cari celah aman dulu.",
            "Ponyo lanjut pelan-pelan di {game}; yang penting jangan terburu-buru.",
            "Seru juga bahas {game} bareng {author}. Ponyo tetap fokus sambil baca chat ya."
        ],
        "general": [
            "Hehe, Ponyo dengar kok, {author}. Yuk lanjut ngobrol santai!",
            "Wah menarik juga, {author}. Ponyo tampung dulu idenya.",
            "Ponyo suka obrolan begini, {author}. Bikin live terasa lebih dekat.",
            "Makasih sudah ikut nimbrung, {author}. Ponyo tetap temani sampai suasananya makin seru."
        ],
        "compliment": [
            "Makasih {author}, Ponyo jadi makin semangat nih!",
            "Hehe, pujiannya bikin Ponyo senang, {author}."
        ],
        "confused_slang": [
            "Ponyo belum terlalu paham istilah itu, {author}. Artinya apa ya?",
            "Istilahnya baru buat Ponyo nih, {author}. Boleh jelasin artinya?"
        ],
        "question": [
            "Hmm, pertanyaan bagus, {author}. Ponyo jawab sebisanya ya.",
            "Ponyo coba jelasin singkat ya, {author}."
        ],
        "short_message": [
            "Hehe, Ponyo dengar kok, {author}.",
            "Ponyo tetap temani di sini ya, {author}."
        ],
        "game_failure": [
            "Yah, hampir banget, {author}. Ponyo coba lagi pelan-pelan.",
            "Aduh gagal sedikit, tapi belum selesai kok, {author}."
        ],
    }

    def generate(self, author, message, recent=None, game="game Ponyo", intent=None):
        text = (message or "").lower()
        if intent in self.BANKS:
            bank = self.BANKS[intent]
        elif any(word in text for word in ("halo", "hai", "hello", "hi", "boo")):
            bank = self.BANKS["greeting"]
        elif any(word in text for word in ("semangat", "sukses", "support", "jago")):
            bank = self.BANKS["support"]
        elif game and game.lower() not in ("umum", ""):
            bank = self.BANKS["game"]
        else:
            bank = self.BANKS["general"]
        recent = recent or []
        candidates = [item for item in bank if item.format(author=author, game=game) not in recent]
        if not candidates:
            candidates = bank
        key = ("greeting" if bank is self.BANKS["greeting"] else "support" if bank is self.BANKS["support"] else "game" if bank is self.BANKS["game"] else "general")
        index = self._cursor.get(key, 0) % len(candidates)
        self._cursor[key] = index + 1
        return candidates[index].format(author=author or "teman", game=game or "game Ponyo")

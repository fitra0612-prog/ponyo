import os
import math
import time
import random
import threading
import pygame
from .config import WINDOW_WIDTH, WINDOW_HEIGHT, CHROMA_MODE, ENABLE_SPEECH_BUBBLE
from .sfx_engine import sfx_player
from .mic_lip_sync import mic_lip_sync

CHROMA_PALETTE = {
    "GREEN": (0, 255, 0),
    "MAGENTA": (255, 0, 255),
    "BLUE": (0, 0, 255),
    "BLACK": (0, 0, 0)
}

class VTuberDisplay:
    def __init__(self, tts_engine, avatar_dir="avatars", commentator=None, manual_hook=None, chess_coach=None, ai_brain=None):
        self.tts = tts_engine
        self.avatar_dir = avatar_dir
        self.commentator = commentator
        self.manual_hook = manual_hook
        self.chess_coach = chess_coach
        self.ai_brain = ai_brain
        self.width = WINDOW_WIDTH
        self.height = WINDOW_HEIGHT
        self.is_closing = False
        self.active_closing = False
        
        # Inisialisasi display
        pygame.init()
        self.screen = pygame.display.set_mode((self.width, self.height), pygame.RESIZABLE)
        pygame.display.set_caption("Ponyo Ghost Display [OBS Ready]")
        
        # Background Chroma Key & Rumah Hantu
        self.color_keys = ["GREEN", "MAGENTA", "BLUE", "BLACK", "BRICK_WALL"]
        self.current_color_idx = 0
        if CHROMA_MODE in self.color_keys:
            self.current_color_idx = self.color_keys.index(CHROMA_MODE)

        # Efek pernapasan / bobbing melayang
        self.enable_bobbing = True
        self.clock = pygame.time.Clock()
        self.running = True

        # Animasi kedip mata otomatis (Natural Auto-Blink)
        self.is_blinking = False
        self.blink_start_time = 0.0
        self.blink_duration = 0.16
        self.next_blink_time = time.time() + random.uniform(2.0, 4.0)
        self.is_double_blink = False

        # Balon Teks Ucapan (Live Speech Bubble Overlay)
        self.show_speech_bubble = ENABLE_SPEECH_BUBBLE
        self.bubble_font = pygame.font.SysFont("consolas", 15, bold=True)
        self.tag_font = pygame.font.SysFont("consolas", 12, bold=True)
        self.boo_font = pygame.font.SysFont("consolas", 46, bold=True)

        # Animasi Idle Spesial: Menghilang & Muncul Tiba-tiba dari Bawah (Ghost Peek-a-boo)
        self.idle_trick_enabled = True
        self.idle_state = "NORMAL" # NORMAL, VANISH, HIDDEN, PEEK_RISE, PEEK_HOLD, FLOAT_HOME
        self.idle_timer = time.time()
        self.next_idle_trick_time = time.time() + random.uniform(20.0, 35.0)
        self.peek_x = self.width // 2
        self.hidden_duration = 1.6
        self.hold_duration = 1.1
        self.particles = []
        self.target_size = 360

        # Mini-Game & Interaksi Visual Penonton (PAT, TREAT, SPIN, DANCE, PANIC, BOBA, RAGE, SLEEP, TOMATO)
        self.active_interaction = None
        self.interaction_timer = 0.0
        self.interaction_duration = 0.0
        self.interaction_author = ""
        self.tomato_outcome = "DODGE"
        self.is_sleeping = False
        self.zzz_font = pygame.font.SysFont("consolas", 16, bold=True)
        self.confetti_particles = []

        # Sistem Aksesoris & Kostum Pixel-Art (Saran Nomor 2: Wardrobe / Hats System)
        self.current_accessory = None # None, ribbon, witch, crown, glasses, flower, angel_halo, devil_horns, knight
        self.accessories_orig = {}
        self.accessories = {}
        self.accessory_keys = ["ribbon", "witch", "crown", "glasses", "flower", "angel_halo", "devil_horns", "knight"]
        self.accessory_names_id = {
            "ribbon": "Pita Merah Muda",
            "witch": "Topi Penyihir",
            "crown": "Mahkota Emas",
            "glasses": "Kacamata Hitam",
            "flower": "Bunga Melati",
            "angel_halo": "Halo Malaikat Kuning",
            "devil_horns": "Tanduk Setan Merah",
            "knight": "Helm Ksatria"
        }

        # Mode Manual Mikrofon Streamer (Shortcut [V] - Human VTuber)
        self.manual_mic_mode = False
        self.mic_lip_sync = mic_lip_sync

        # Load avatar images
        self._load_sprites()

    def _load_sprites(self):
        closed_path = os.path.join(self.avatar_dir, "closed.png")
        open_path = os.path.join(self.avatar_dir, "open.png")
        blink_path = os.path.join(self.avatar_dir, "blink.png")
        blink_open_path = os.path.join(self.avatar_dir, "blink_open.png")
        happy_path = os.path.join(self.avatar_dir, "happy.png")
        shock_path = os.path.join(self.avatar_dir, "shock.png")
        pout_path = os.path.join(self.avatar_dir, "pout.png")
        think_path = os.path.join(self.avatar_dir, "think.png")
        cry_path = os.path.join(self.avatar_dir, "cry.png")
        smug_path = os.path.join(self.avatar_dir, "smug.png")
        shy_path = os.path.join(self.avatar_dir, "shy.png")
        sleepy_path = os.path.join(self.avatar_dir, "sleepy.png")
        angry_path = os.path.join(self.avatar_dir, "angry.png")
        star_path = os.path.join(self.avatar_dir, "star.png")
        ojigi_path = os.path.join(self.avatar_dir, "ojigi.png")

        if not os.path.exists(closed_path) or not os.path.exists(star_path) or not os.path.exists(ojigi_path):
            from tools.generators.generate_ponyo_avatar import generate_ponyo_ghost_avatars
            generate_ponyo_ghost_avatars(self.avatar_dir)

        self.img_closed_orig = pygame.image.load(closed_path).convert_alpha()
        self.img_open_orig = pygame.image.load(open_path).convert_alpha()
        
        # Load blinking sprites with fallbacks
        self.img_blink_orig = pygame.image.load(blink_path).convert_alpha() if os.path.exists(blink_path) else self.img_closed_orig
        self.img_blink_open_orig = pygame.image.load(blink_open_path).convert_alpha() if os.path.exists(blink_open_path) else self.img_open_orig

        # Load dynamic emotion sprites (10 Emosi + Ojigi)
        self.img_happy_orig = pygame.image.load(happy_path).convert_alpha() if os.path.exists(happy_path) else self.img_open_orig
        self.img_shock_orig = pygame.image.load(shock_path).convert_alpha() if os.path.exists(shock_path) else self.img_open_orig
        self.img_pout_orig = pygame.image.load(pout_path).convert_alpha() if os.path.exists(pout_path) else self.img_closed_orig
        self.img_think_orig = pygame.image.load(think_path).convert_alpha() if os.path.exists(think_path) else self.img_closed_orig
        self.img_cry_orig = pygame.image.load(cry_path).convert_alpha() if os.path.exists(cry_path) else self.img_open_orig
        self.img_smug_orig = pygame.image.load(smug_path).convert_alpha() if os.path.exists(smug_path) else self.img_closed_orig
        self.img_shy_orig = pygame.image.load(shy_path).convert_alpha() if os.path.exists(shy_path) else self.img_closed_orig
        self.img_sleepy_orig = pygame.image.load(sleepy_path).convert_alpha() if os.path.exists(sleepy_path) else self.img_closed_orig
        self.img_angry_orig = pygame.image.load(angry_path).convert_alpha() if os.path.exists(angry_path) else self.img_closed_orig
        self.img_star_orig = pygame.image.load(star_path).convert_alpha() if os.path.exists(star_path) else self.img_open_orig
        self.img_ojigi_orig = pygame.image.load(ojigi_path).convert_alpha() if os.path.exists(ojigi_path) else self.img_closed_orig

        # Load frame animasi melambaikan tangan ceria (HAPPY wave_1 & wave_2) untuk closing stream
        wave1_path = os.path.join(self.avatar_dir, "wave_1.png")
        wave2_path = os.path.join(self.avatar_dir, "wave_2.png")
        self.img_wave1_orig = pygame.image.load(wave1_path).convert_alpha() if os.path.exists(wave1_path) else self.img_happy_orig
        self.img_wave2_orig = pygame.image.load(wave2_path).convert_alpha() if os.path.exists(wave2_path) else self.img_happy_orig

        # Load large human hand pixel art for petting (!pat)
        pat_down_path = os.path.join(self.avatar_dir, "pat_hand_down.png")
        pat_up_path = os.path.join(self.avatar_dir, "pat_hand_up.png")
        if not os.path.exists(pat_down_path) or not os.path.exists(pat_up_path):
            from tools.generators.generate_ponyo_avatar import generate_pat_hand_sprites
            generate_pat_hand_sprites(self.avatar_dir)

        self.img_hand_down_orig = pygame.image.load(pat_down_path).convert_alpha()
        self.img_hand_up_orig = pygame.image.load(pat_up_path).convert_alpha()

        # Load aksesoris pixel-art (Saran Nomor 2)
        acc_dir = os.path.join(self.avatar_dir, "accessories")
        required_accessories = [f"{key}.png" for key in self.accessory_keys]
        if not os.path.exists(acc_dir) or any(
            not os.path.exists(os.path.join(acc_dir, filename)) for filename in required_accessories
        ):
            from tools.generators.generate_accessories import generate_all_accessories
            generate_all_accessories(acc_dir)

        for k in self.accessory_keys:
            p = os.path.join(acc_dir, f"{k}.png")
            if os.path.exists(p):
                self.accessories_orig[k] = pygame.image.load(p).convert_alpha()

        # Load background brick wall rumah hantu
        bg_wall_path = os.path.join(os.path.dirname(__file__), "assets", "backgrounds", "background_brick_wall_avatar.png")
        if os.path.exists(bg_wall_path):
            self.bg_brick_wall_orig = pygame.image.load(bg_wall_path).convert()
            self.bg_brick_wall = pygame.transform.scale(self.bg_brick_wall_orig, (self.width, self.height))
        else:
            self.bg_brick_wall_orig = None
            self.bg_brick_wall = None

        self._scale_sprites()

    def _scale_sprites(self):
        # Skala proporsional agar balon ucapan di atas kepala muat dengan elegan
        self.target_size = min(int(self.width * 0.78), int(self.height * 0.65))
        sz = (self.target_size, self.target_size)
        self.img_closed = pygame.transform.smoothscale(self.img_closed_orig, sz)
        self.img_open = pygame.transform.smoothscale(self.img_open_orig, sz)
        self.img_blink = pygame.transform.smoothscale(self.img_blink_orig, sz)
        self.img_blink_open = pygame.transform.smoothscale(self.img_blink_open_orig, sz)
        self.img_happy = pygame.transform.smoothscale(self.img_happy_orig, sz)
        self.img_shock = pygame.transform.smoothscale(self.img_shock_orig, sz)
        self.img_pout = pygame.transform.smoothscale(self.img_pout_orig, sz)
        self.img_think = pygame.transform.smoothscale(self.img_think_orig, sz)
        self.img_cry = pygame.transform.smoothscale(self.img_cry_orig, sz)
        self.img_smug = pygame.transform.smoothscale(self.img_smug_orig, sz)
        self.img_shy = pygame.transform.smoothscale(self.img_shy_orig, sz)
        self.img_sleepy = pygame.transform.smoothscale(self.img_sleepy_orig, sz)
        self.img_angry = pygame.transform.smoothscale(self.img_angry_orig, sz)
        self.img_star = pygame.transform.smoothscale(self.img_star_orig, sz)
        self.img_ojigi = pygame.transform.smoothscale(self.img_ojigi_orig, sz)
        self.img_wave1 = pygame.transform.smoothscale(self.img_wave1_orig, sz)
        self.img_wave2 = pygame.transform.smoothscale(self.img_wave2_orig, sz)

        # Skala semua aksesoris agar presisi 1:1 pas di atas kepala Ponyo
        for k, orig in self.accessories_orig.items():
            self.accessories[k] = pygame.transform.smoothscale(orig, sz)

        # Ukuran tangan manusia pixel-art sebesar ukuran Ponyo (Life-sized hand pat)
        self.hand_size = int(self.target_size * 1.02)
        h_sz = (self.hand_size, self.hand_size)
        self.img_hand_down = pygame.transform.smoothscale(self.img_hand_down_orig, h_sz)
        self.img_hand_up = pygame.transform.smoothscale(self.img_hand_up_orig, h_sz)

    def set_accessory(self, name: str) -> bool:
        """Memasang aksesoris tertentu ke kepala Ponyo"""
        if not name:
            self.current_accessory = None
            return True
        key = name.strip().lower()
        alias_map = {
            "witch": "witch", "penyihir": "witch", "topi": "witch", "sihir": "witch",
            "ribbon": "ribbon", "pita": "ribbon", "pink": "ribbon",
            "crown": "crown", "mahkota": "crown", "raja": "crown", "queen": "crown", "king": "crown",
            "glasses": "glasses", "kacamata": "glasses", "sunglasses": "glasses", "thug": "glasses",
            "flower": "flower", "bunga": "flower", "melati": "flower", "mawar": "flower",
            "angel_halo": "angel_halo", "halo": "angel_halo", "malaikat": "angel_halo", "angel": "angel_halo",
            "devil_horns": "devil_horns", "tanduk": "devil_horns", "setan": "devil_horns", "iblis": "devil_horns", "devil": "devil_horns",
            "knight": "knight", "helm": "knight", "helmet": "knight", "ksatria": "knight", "slasher": "knight", "armor": "knight"
        }
        target = alias_map.get(key, key)
        if target in self.accessories:
            self.current_accessory = target
            print(f"[WARDROBE] Ponyo memakai aksesoris: {self.accessory_names_id.get(target, target)}")
            return True
        elif target in ("none", "lepas", "copot", "buka", "off"):
            self.current_accessory = None
            print("[WARDROBE] Ponyo melepas aksesoris kepala.")
            return True
        return False

    def remove_accessory(self):
        self.current_accessory = None
        print("[WARDROBE] Ponyo melepas aksesoris kepala.")

    def cycle_accessory(self) -> str:
        """Mengganti aksesoris berikutnya secara bergiliran (Tombol [H])"""
        cycle_list = [None] + self.accessory_keys
        idx = 0
        if self.current_accessory in cycle_list:
            idx = (cycle_list.index(self.current_accessory) + 1) % len(cycle_list)
        self.current_accessory = cycle_list[idx]
        name = self.accessory_names_id.get(self.current_accessory, "Tanpa Aksesoris")
        print(f"[DISPLAY] Aksesoris kepala diganti ke: {name}")
        return name

    def toggle_manual_mic(self) -> bool:
        """Toggle antara mode Bot AI Otomatis dan Mode Manual Microphone Streamer (Tombol [V])"""
        self.manual_mic_mode = not self.manual_mic_mode
        if self.manual_mic_mode:
            # Hentikan & mute TTS bot
            self.tts.interrupt()
            self.tts.is_muted = True
            self.tts.current_text = ""
            self.mic_lip_sync.start()
            sfx_player.play("pat")
            dev_name = self.mic_lip_sync.active_device_name or "Mikrofon Utama"
            print("\n" + "=" * 62)
            print("[VTUBER MODE] >>> MODE MANUAL MIC (HUMAN VTUBER) AKTIF! <<<")
            print(f"* Kendali suara Ponyo 100% dari mikrofon: {dev_name}")
            print("* Bot AI & Auto-Yapping dinonaktifkan (Mulut avatar bergerak sesuai suaramu)")
            print("=" * 62 + "\n")
        else:
            self.mic_lip_sync.stop()
            self.tts.is_muted = False
            sfx_player.play("boo_pop")
            print("\n" + "=" * 62)
            print("[VTUBER MODE] >>> MODE BOT AI OTOMATIS AKTIF! <<<")
            print("* Ponyo kembali berbicara mandiri menggunakan kecerdasan buatan.")
            print("=" * 62 + "\n")
        return self.manual_mic_mode

    def trigger_stream_closing(self):
        """Menjalankan ritual closing livestream (Ponyo tersenyum bahagia HAPPY, melambaikan tangan, dan auto-exit)"""
        if getattr(self, "is_closing", False):
            return
        self.is_closing = True
        self.active_closing = True
        print("\n" + "=" * 62)
        print("[CLOSING] >>> RITUAL CLOSING LIVESTREAM DIMULAI [Home] <<<")
        print("* Ponyo tersenyum bahagia (HAPPY) dan melambaikan tangan berpamitan.")
        print("=" * 62 + "\n")

        # Matikan auto-yapping agar tidak memotong closing
        if self.commentator:
            self.commentator.is_enabled = False

        # Unmute TTS jika sedang di mode manual mic
        if getattr(self, "manual_mic_mode", False):
            self.toggle_manual_mic()

        if self.tts:
            self.tts.interrupt()

        # Bunyikan fanfare penutup
        sfx_player.play("fanfare")

        # Susun kalimat penutup personal dengan menyebut penonton paling aktif
        top_viewers = []
        if hasattr(self, "ai_brain") and self.ai_brain and hasattr(self.ai_brain, "memory"):
            mem_viewers = getattr(self.ai_brain.memory, "viewers", {})
            sorted_v = sorted(mem_viewers.values(), key=lambda v: v.get("chat_count", 0), reverse=True)
            top_viewers = [v["display_name"] for v in sorted_v if v.get("display_name", "").lower() not in ["streamer", "system", "audience"]]

        if top_viewers:
            viewer_names = ", ".join(top_viewers[:3])
            closing_text = (
                f"Wah seru banget live stream hari ini! Makasih banyak ya buat teman-teman yang udah nemenin dan seru-seruan bareng Ponyo, "
                f"terutama {viewer_names} dan semua teman-teman di live chat! "
                f"Ponyo pamit undur diri dulu ya. Jangan lupa like dan subscribe! Sampai jumpa di live stream Ponyo berikutnya! Boo! Bye-bye semuanya!"
            )
        else:
            closing_text = (
                "Wah seru banget live stream hari ini! Makasih banyak buat semua teman-teman yang udah mampir dan nonton Ponyo hari ini! "
                "Ponyo pamit undur diri dulu ya, jangan lupa like dan subscribe! Sampai jumpa di live stream Ponyo berikutnya! Boo! Bye-bye semuanya!"
            )

        def closing_worker():
            time.sleep(0.3)
            print(f"\n[VTUBER CLOSING SPEECH]: {closing_text}")
            self.tts.speak_text(closing_text, interruptible=False)
            time.sleep(1.8)
            print("[CLOSING] Ucapan penutup tuntas. Mengakhiri live stream...")
            self.running = False

        threading.Thread(target=closing_worker, daemon=True).start()

    @staticmethod
    def ease_out_back(x: float) -> float:
        """Easing lentur memantul untuk efek muncul mengejutkan dari bawah"""
        c1 = 1.70158
        c3 = c1 + 1
        return 1 + c3 * math.pow(x - 1, 3) + c1 * math.pow(x - 1, 2)

    @staticmethod
    def ease_in_out(x: float) -> float:
        """Easing halus untuk kembali ke posisi awal"""
        return 0.5 * (1 - math.cos(math.pi * x))

    def trigger_idle_trick(self):
        """Memicu aksi hantu menghilang dan muncul mengejutkan dari bawah secara manual"""
        if not self.tts.is_speaking and self.idle_state == "NORMAL":
            self.idle_state = "VANISH"
            self.idle_timer = time.time()
            print("[DISPLAY] Trik hantu diaktifkan: Ponyo menghilang!")

    def trigger_headpat(self, author: str = ""):
        """Nomor 4: Memicu animasi elus kepala Ponyo (!pat / !elus)"""
        self.active_interaction = "PAT"
        self.interaction_timer = time.time()
        self.interaction_duration = 2.8
        self.interaction_author = author
        sfx_player.play("pat")
        cx = self.width // 2
        cy = int(self.height * 0.45)
        for _ in range(8):
            self.particles.append({
                'x': cx + random.randint(-70, 70),
                'y': cy + random.randint(-30, 30),
                'vx': random.uniform(-1.2, 1.2),
                'vy': random.uniform(-2.6, -1.0),
                'life': 1.0,
                'radius': random.randint(5, 8),
                'color': (255, 130, 175)
            })

    def trigger_treat(self, author: str = ""):
        """Nomor 4: Memicu animasi lempar permen manis ke Ponyo (!permen / !kasihmakan)"""
        self.active_interaction = "TREAT"
        self.interaction_timer = time.time()
        self.interaction_duration = 2.4
        self.interaction_author = author
        sfx_player.play("pat")

    def trigger_spin(self, author: str = ""):
        """Nomor 4: Memicu animasi Ponyo berputar 360 derajat (!spin)"""
        self.wake_up()
        self.active_interaction = "SPIN"
        self.interaction_timer = time.time()
        self.interaction_duration = 1.5
        self.interaction_author = author
        sfx_player.play("spin")
        cx = self.width // 2
        cy = int(self.height * 0.60)
        for _ in range(10):
            self.particles.append({
                'x': cx + random.randint(-80, 80),
                'y': cy + random.randint(-60, 60),
                'vx': random.uniform(-2.0, 2.0),
                'vy': random.uniform(-2.5, 0.5),
                'life': 1.0,
                'radius': random.randint(4, 8),
                'color': (255, 220, 80)
            })

    def trigger_dance(self, author: str = ""):
        """Saran 1: Animasi Loncat Kegirangan / Joget Hore (!hore / !dance)"""
        self.wake_up()
        self.active_interaction = "DANCE"
        self.interaction_timer = time.time()
        self.interaction_duration = 3.0
        self.interaction_author = author
        sfx_player.play("fanfare")
        print(f"[DISPLAY] Animasi DANCE (Loncat Kegirangan) aktif: {author}")

    def trigger_panic(self, author: str = ""):
        """Saran 2: Animasi Menggigil Panik / Shiver (!panik / !kaget)"""
        self.wake_up()
        self.active_interaction = "PANIC"
        self.interaction_timer = time.time()
        self.interaction_duration = 2.5
        self.interaction_author = author
        sfx_player.play("fail")
        print(f"[DISPLAY] Animasi PANIC (Menggigil Panik) aktif: {author}")

    def trigger_boba(self, author: str = ""):
        """Saran 3: Animasi Menyeruput Boba / Kopi (!boba / !kopi / !minum)"""
        self.wake_up()
        self.active_interaction = "BOBA"
        self.interaction_timer = time.time()
        self.interaction_duration = 3.2
        self.interaction_author = author
        sfx_player.play("pat")
        print(f"[DISPLAY] Animasi BOBA (Menyeruput Boba) aktif: {author}")

    def trigger_rage(self, author: str = ""):
        """Saran 4: Animasi Mengambek & Kepala Mengepul Asap (!ngambek / !marah)"""
        self.wake_up()
        self.active_interaction = "RAGE"
        self.interaction_timer = time.time()
        self.interaction_duration = 2.8
        self.interaction_author = author
        sfx_player.play("fail")
        print(f"[DISPLAY] Animasi RAGE (Mengambek Asap) aktif: {author}")

    def trigger_sleep(self, author: str = ""):
        """Saran 5: Animasi Tidur Mendengkur Zzz (!turu / !tidur / !ngantuk)"""
        self.is_sleeping = not self.is_sleeping
        if self.is_sleeping:
            self.active_interaction = "SLEEP"
            self.interaction_timer = time.time()
            self.interaction_duration = 999999.0
            self.interaction_author = author
            print(f"[DISPLAY] Animasi SLEEP (Tidur Mendengkur Zzz) aktif: {author}")
        else:
            self.wake_up()

    def wake_up(self):
        """Membangunkan Ponyo seketika dari tidur saat ada interaksi baru"""
        if self.is_sleeping or self.active_interaction == "SLEEP":
            self.is_sleeping = False
            if self.active_interaction == "SLEEP":
                self.active_interaction = None
            print("[DISPLAY] Ponyo terbangun dari tidur!")

    def trigger_tomato(self, author: str = ""):
        """Saran 6: Reaksi Interaktif Lempar Tomat (50% Dodge / 50% Splat) (!tomat / !lempar)"""
        self.wake_up()
        self.active_interaction = "TOMATO"
        self.interaction_timer = time.time()
        self.interaction_duration = 2.8
        self.interaction_author = author
        self.tomato_outcome = random.choice(["DODGE", "SPLAT"])
        sfx_player.play("boo_pop")
        print(f"[DISPLAY] Animasi TOMATO ({self.tomato_outcome}) aktif: {author}")

    def _draw_headpat_hand(self, center_x: int, head_top_y: int, elapsed: float):
        """Menggambar tangan manusia pixel-art seukuran tubuh Ponyo yang mengelus lembut kepala Ponyo"""
        # Siklus ritme mengelus (~2.5 elusan per detik)
        cycle = (elapsed * 2.8) % 1.0
        is_down = cycle < 0.50

        # Gerakan horizontal meluncur maju-mundur mengelus kepala
        pat_dx = int(math.sin(elapsed * 5.6) * 16)
        # Gerakan vertikal menekan lembut saat down dan terangkat saat up
        if is_down:
            p = cycle / 0.50
            pat_dy = int(math.sin(p * math.pi) * 10)
            hand_surf = self.img_hand_down
        else:
            p = (cycle - 0.50) / 0.50
            pat_dy = int(-math.sin(p * math.pi) * 8)
            hand_surf = self.img_hand_up

        # Posisikan tangan tepat menangkup di atas kepala kubah Ponyo
        hx = center_x - int(self.hand_size * 0.38) + pat_dx
        hy = head_top_y - int(self.hand_size * 0.44) + pat_dy
        self.screen.blit(hand_surf, (hx, hy))

    def _draw_candy_treat(self, center_x: int, center_y: int, prog: float):
        """Menggambar permen manis yang melambung ke arah Ponyo lalu pecah jadi partikel bahagia"""
        if prog < 0.60:
            t = prog / 0.60
            start_x = 40
            start_y = self.height - 80
            curr_x = int(start_x + (center_x - start_x) * t)
            arc_y = int(-120 * math.sin(math.pi * t))
            curr_y = int(start_y + (center_y - start_y) * t) + arc_y

            # Bungkus permen kiri & kanan
            pygame.draw.polygon(self.screen, (255, 110, 165), [
                (curr_x - 22, curr_y - 10), (curr_x - 22, curr_y + 10), (curr_x - 8, curr_y)
            ])
            pygame.draw.polygon(self.screen, (255, 110, 165), [
                (curr_x + 22, curr_y - 10), (curr_x + 22, curr_y + 10), (curr_x + 8, curr_y)
            ])
            # Bola permen tengah
            pygame.draw.circle(self.screen, (255, 85, 145), (curr_x, curr_y), 13)
            pygame.draw.circle(self.screen, (255, 210, 230), (curr_x - 4, curr_y - 4), 4)
            pygame.draw.circle(self.screen, (30, 32, 45), (curr_x, curr_y), 13, width=3)

    def _draw_confetti(self, now: float):
        """Saran 1: Menggambar partikel konfeti warna-warni berjatuhan saat loncat kegirangan"""
        if random.random() < 0.40:
            self.confetti_particles.append({
                'x': random.randint(20, self.width - 20),
                'y': -10,
                'vx': random.uniform(-1.2, 1.2),
                'vy': random.uniform(2.5, 5.0),
                'w': random.randint(5, 8),
                'h': random.randint(7, 11),
                'color': random.choice([
                    (255, 65, 85), (255, 215, 30), (50, 225, 110),
                    (45, 185, 255), (255, 120, 220), (255, 160, 40)
                ]),
                'angle': random.uniform(0, math.pi * 2)
            })
        new_confetti = []
        for c in self.confetti_particles:
            c['x'] += c['vx']
            c['y'] += c['vy']
            c['angle'] += 0.16
            if c['y'] < self.height + 15:
                w = max(2, int(abs(math.cos(c['angle'])) * c['w']))
                pygame.draw.rect(self.screen, c['color'], (int(c['x']), int(c['y']), w, c['h']))
                new_confetti.append(c)
        self.confetti_particles = new_confetti[-35:]

    def _draw_panic_sweat(self, cx: int, top_y: int, now: float):
        """Saran 2: Menggambar tetesan keringat dingin berkedip di samping dahi saat panik"""
        drop_y = top_y + 16 + int(math.sin(now * 12.0) * 4)
        # Keringat kiri
        lx = cx - int(self.target_size * 0.32)
        pygame.draw.circle(self.screen, (90, 210, 255), (lx, drop_y), 6)
        pygame.draw.polygon(self.screen, (90, 210, 255), [(lx - 4, drop_y), (lx + 4, drop_y), (lx, drop_y - 8)])
        pygame.draw.circle(self.screen, (255, 255, 255), (lx - 1, drop_y - 1), 2)
        # Keringat kanan
        rx = cx + int(self.target_size * 0.32)
        pygame.draw.circle(self.screen, (90, 210, 255), (rx, drop_y + 4), 6)
        pygame.draw.polygon(self.screen, (90, 210, 255), [(rx - 5, drop_y + 4), (rx + 5, drop_y + 4), (rx, drop_y - 6)])
        pygame.draw.circle(self.screen, (255, 255, 255), (rx - 1, drop_y + 3), 2)

    def _draw_boba_cup(self, cx: int, cy: int, prog: float):
        """Saran 3: Menggambar cup boba milk tea pixel art dengan sedotan dan mutiara tapioka"""
        cup_x = cx
        cup_y = cy + int(self.target_size * 0.20)
        cup_surf = pygame.Surface((70, 90), pygame.SRCALPHA)
        # Gelas plastik bening
        pygame.draw.polygon(cup_surf, (230, 240, 255, 180), [(12, 18), (58, 18), (50, 78), (20, 78)])
        pygame.draw.polygon(cup_surf, (35, 40, 60, 240), [(12, 18), (58, 18), (50, 78), (20, 78)], width=2)
        # Teh susu manis
        pygame.draw.polygon(cup_surf, (205, 150, 105, 235), [(14, 26), (56, 26), (49, 76), (21, 76)])
        # Boba tapioka hitam
        pearls = [(26, 68), (34, 70), (42, 67), (29, 61), (39, 62), (34, 56)]
        for px, py in pearls:
            pygame.draw.circle(cup_surf, (30, 20, 25), (px, py), 4)
            pygame.draw.circle(cup_surf, (90, 70, 75), (px - 1, py - 1), 1)
        # Tutup seal cup merah muda
        pygame.draw.rect(cup_surf, (255, 95, 150), (8, 14, 54, 7), border_radius=3)
        # Sedotan boba
        pygame.draw.line(cup_surf, (70, 220, 255), (35, 50), (46, 0), 5)
        pygame.draw.line(cup_surf, (25, 30, 45), (35, 50), (46, 0), 1)
        self.screen.blit(cup_surf, (cup_x - 35, cup_y - 45))

        # Tangan hantu imut Ponyo memegang erat cup boba di kiri dan kanan
        pygame.draw.circle(self.screen, (255, 255, 255), (cup_x - 26, cup_y + 10), 8)
        pygame.draw.circle(self.screen, (35, 40, 60), (cup_x - 26, cup_y + 10), 8, width=2)
        pygame.draw.circle(self.screen, (255, 255, 255), (cup_x + 26, cup_y + 10), 8)
        pygame.draw.circle(self.screen, (35, 40, 60), (cup_x + 26, cup_y + 10), 8, width=2)

    def _draw_steam_puffs(self, cx: int, top_y: int, now: float):
        """Saran 4: Menggambar kepulan uap asap kartun dari kepala saat Ponyo mengambek"""
        for side, dir_x in [(-1, -1), (1, 1)]:
            base_x = cx + dir_x * int(self.target_size * 0.22)
            base_y = top_y + 18
            for i in range(3):
                p = ((now * 2.5 + i * 0.33) % 1.0)
                sx = int(base_x + dir_x * (p * 35))
                sy = int(base_y - p * 38)
                r = int(5 + p * 9)
                alpha = int((1.0 - p) * 220)
                steam_surf = pygame.Surface((r * 2 + 4, r * 2 + 4), pygame.SRCALPHA)
                pygame.draw.circle(steam_surf, (255, 255, 255, alpha), (r + 2, r + 2), r)
                pygame.draw.circle(steam_surf, (220, 225, 240, alpha), (r + 2, r + 2), r, width=2)
                self.screen.blit(steam_surf, (sx - r - 2, sy - r - 2))

    def _draw_zzz_bubble(self, cx: int, top_y: int, now: float):
        """Saran 5: Menggambar gelembung tidur dan huruf Zzz... saat Ponyo tertidur"""
        cycle = (now * 0.42) % 1.0
        grow = math.sin(cycle * math.pi)
        r = int(7 + grow * 15)
        bx = cx + int(self.target_size * 0.18) + int(math.sin(now * 2.0) * 6)
        by = top_y + 35 - int(cycle * 30)

        bubble_surf = pygame.Surface((r * 2 + 6, r * 2 + 6), pygame.SRCALPHA)
        pygame.draw.circle(bubble_surf, (180, 225, 255, 170), (r + 3, r + 3), r)
        pygame.draw.circle(bubble_surf, (255, 255, 255, 220), (r + 1, r + 1), max(2, r // 3))
        pygame.draw.circle(bubble_surf, (90, 140, 200, 200), (r + 3, r + 3), r, width=2)
        self.screen.blit(bubble_surf, (bx - r - 3, by - r - 3))

        phase = int((now * 1.5) % 3) + 1
        txt = "Z" * phase
        z_surf = self.zzz_font.render(txt, True, (80, 120, 220))
        self.screen.blit(z_surf, (bx + r + 4, by - 8))

    def _draw_single_tomato(self, x: int, y: int, angle: float = 0.0):
        """Menggambar buah tomat merah pixel art bulat dengan tangkai hijau"""
        pygame.draw.circle(self.screen, (235, 35, 40), (x, y), 12)
        pygame.draw.circle(self.screen, (255, 120, 130), (x - 3, y - 4), 3)
        pygame.draw.polygon(self.screen, (50, 180, 60), [(x, y - 15), (x - 5, y - 11), (x + 5, y - 11)])
        pygame.draw.polygon(self.screen, (50, 180, 60), [(x - 6, y - 10), (x + 6, y - 10), (x, y - 8)])

    def _draw_tomato_splat(self, x: int, y: int):
        """Menggambar cipratan saus tomat merah cerah saat tomat mengenai badan Ponyo"""
        pygame.draw.circle(self.screen, (220, 35, 40), (x, y), 22)
        splats = [
            (-16, -10, 8), (18, -8, 9), (-10, 16, 7), (12, 14, 10),
            (0, -18, 7), (-22, 6, 6), (22, 8, 7), (0, 24, 6)
        ]
        for dx, dy, r in splats:
            pygame.draw.circle(self.screen, (220, 35, 40), (x + dx, y + dy), r)
        # Highlight saus
        pygame.draw.circle(self.screen, (255, 120, 130), (x - 6, y - 6), 5)
        # Tetesan saus meleleh ke bawah
        pygame.draw.line(self.screen, (200, 25, 30), (x - 4, y + 10), (x - 4, y + 34), 4)
        pygame.draw.line(self.screen, (200, 25, 30), (x + 8, y + 8), (x + 8, y + 28), 3)

    def _draw_tomato_interaction(self, cx: int, cy: int, prog: float):
        """Saran 6: Menggambar lemparan tomat (Dodge vs Splat)"""
        outcome = getattr(self, "tomato_outcome", "DODGE")
        if outcome == "DODGE":
            tom_x = int(-30 + prog * (self.width + 70))
            tom_y = cy - int(self.target_size * 0.15)
            self._draw_single_tomato(tom_x, tom_y, angle=prog * 12.0)
        else:
            splat_y = cy + 28
            if prog < 0.25:
                p = prog / 0.25
                tom_x = int(-30 + p * (cx + 30))
                tom_y = int((cy - 10) + p * 38)
                self._draw_single_tomato(tom_x, tom_y, angle=p * 8.0)
            else:
                self._draw_tomato_splat(cx, splat_y)

    def draw_speech_bubble(self, text: str, head_top_y: int):
        """Menggambar balon teks ucapan retro pixel art di atas kepala Ponyo"""
        if not text:
            return

        bw = min(self.width - 36, 430)
        # Word wrapping otomatis
        words = text.split()
        lines = []
        curr = ""
        for w in words:
            test = curr + (" " if curr else "") + w
            if self.bubble_font.size(test)[0] < bw - 32:
                curr = test
            else:
                lines.append(curr)
                curr = w
        if curr:
            lines.append(curr)

        lines = lines[:3] # Maksimal 3 baris
        bh = max(65, 34 + len(lines) * 22)
        bx = (self.width - bw) // 2
        by = max(16, head_top_y - bh - 14)

        # 1. Kotak Balon Putih
        pygame.draw.rect(self.screen, (255, 255, 255), (bx, by, bw, bh), border_radius=10)
        # 2. Outline Gelap Retro
        pygame.draw.rect(self.screen, (30, 32, 45), (bx, by, bw, bh), width=3, border_radius=10)

        # 3. Ekor Penunjuk ke Kepala Ponyo
        tail_x = self.width // 2
        tail_pts = [
            (tail_x - 10, by + bh - 2),
            (tail_x + 10, by + bh - 2),
            (tail_x, min(head_top_y - 2, by + bh + 13))
        ]
        pygame.draw.polygon(self.screen, (255, 255, 255), tail_pts)
        pygame.draw.polygon(self.screen, (30, 32, 45), tail_pts, width=3)
        # Tutup garis sambungan
        pygame.draw.line(self.screen, (255, 255, 255), (tail_x - 8, by + bh - 2), (tail_x + 8, by + bh - 2), 4)

        # 4. Badge Nama PONYO di pojok kiri atas balon
        tag_surf = self.tag_font.render("PONYO", True, (255, 255, 255))
        tag_w = tag_surf.get_width() + 14
        tag_h = tag_surf.get_height() + 6
        pygame.draw.rect(self.screen, (60, 70, 110), (bx + 14, by - 9, tag_w, tag_h), border_radius=5)
        pygame.draw.rect(self.screen, (30, 32, 45), (bx + 14, by - 9, tag_w, tag_h), width=2, border_radius=5)
        self.screen.blit(tag_surf, (bx + 21, by - 6))

        # 5. Render Teks Ucapan
        ty = by + 18
        for line in lines:
            txt_surf = self.bubble_font.render(line, True, (25, 28, 40))
            self.screen.blit(txt_surf, (bx + 16, ty))
            ty += 22

    def draw_boo_bubble(self, center_x: int, head_top_y: int):
        """Menggambar teks kejutan 'Boo!' berukuran besar tepat di atas kepala Ponyo saat animasi mengejutkan"""
        text = "Boo!"
        shake_x = int(math.sin(time.time() * 28.0) * 3)
        shake_y = int(math.cos(time.time() * 24.0) * 2)

        txt_surf = self.boo_font.render(text, True, (30, 32, 45))
        bw = txt_surf.get_width() + 44
        bh = txt_surf.get_height() + 24

        bx = max(12, min(self.width - bw - 12, center_x - bw // 2 + shake_x))
        by = max(16, head_top_y - bh - 14 + shake_y)

        # 1. Kotak Balon Kejutan Putih Terang + Outline Tebal
        pygame.draw.rect(self.screen, (255, 255, 255), (bx, by, bw, bh), border_radius=14)
        pygame.draw.rect(self.screen, (30, 32, 45), (bx, by, bw, bh), width=4, border_radius=14)

        # 2. Ekor Penunjuk ke Kepala Ponyo
        tail_x = max(bx + 18, min(bx + bw - 18, center_x + shake_x))
        tail_pts = [
            (tail_x - 11, by + bh - 3),
            (tail_x + 11, by + bh - 3),
            (tail_x, min(head_top_y - 2, by + bh + 14))
        ]
        pygame.draw.polygon(self.screen, (255, 255, 255), tail_pts)
        pygame.draw.polygon(self.screen, (30, 32, 45), tail_pts, width=3)
        pygame.draw.line(self.screen, (255, 255, 255), (tail_x - 9, by + bh - 3), (tail_x + 9, by + bh - 3), 4)

        # 3. Render Teks Boo! di Tengah Balon
        tx = bx + (bw - txt_surf.get_width()) // 2
        ty = by + (bh - txt_surf.get_height()) // 2
        self.screen.blit(txt_surf, (tx, ty))

    def handle_resize(self, new_width, new_height):
        self.width = max(200, new_width)
        self.height = max(200, new_height)
        self.screen = pygame.display.set_mode((self.width, self.height), pygame.RESIZABLE)
        if getattr(self, "bg_brick_wall_orig", None):
            self.bg_brick_wall = pygame.transform.scale(self.bg_brick_wall_orig, (self.width, self.height))
        self._scale_sprites()

    def cycle_chroma_color(self):
        self.current_color_idx = (self.current_color_idx + 1) % len(self.color_keys)
        name = self.color_keys[self.current_color_idx]
        print(f"[DISPLAY] Warna background Chroma Key diubah ke: {name}")

    def run_frame(self):
        """Memproses satu frame event dan gambar. Mengembalikan False jika window ditutup."""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
                return False
            elif event.type == pygame.VIDEORESIZE:
                self.handle_resize(event.w, event.h)
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.running = False
                    return False
                elif event.key == pygame.K_F10:
                    enabled = self.tts_engine.set_emergency_silence(
                        not getattr(self.tts_engine, "emergency_silence", False)
                    )
                    print(f"[DISPLAY] Emergency silence: {'Aktif' if enabled else 'Nonaktif'}")
                elif event.key == pygame.K_c:
                    self.cycle_chroma_color()
                elif event.key == pygame.K_b:
                    self.enable_bobbing = not self.enable_bobbing
                    status = "Aktif" if self.enable_bobbing else "Nonaktif"
                    print(f"[DISPLAY] Animasi bobbing: {status}")
                elif event.key == pygame.K_t:
                    self.show_speech_bubble = not self.show_speech_bubble
                    status = "Aktif" if self.show_speech_bubble else "Nonaktif"
                    print(f"[DISPLAY] Balon teks ucapan: {status}")
                elif event.key == pygame.K_y:
                    if self.commentator:
                        self.commentator.is_enabled = not self.commentator.is_enabled
                        status = "Aktif" if self.commentator.is_enabled else "Nonaktif"
                        print(f"[DISPLAY] Auto-Yapping Display 2: {status}")
                elif event.key == pygame.K_i:
                    self.trigger_idle_trick()
                elif event.key == pygame.K_m:
                    if self.manual_hook:
                        self.manual_hook.toggle()
                elif event.key == pygame.K_k:
                    if self.chess_coach:
                        self.chess_coach.toggle_coach()
                elif event.key == pygame.K_g:
                    if self.chess_coach:
                        self.chess_coach.toggle_auto_play()
                elif event.key == pygame.K_1:
                    self.trigger_headpat("Streamer")
                elif event.key == pygame.K_2:
                    self.trigger_treat("Streamer")
                elif event.key == pygame.K_3:
                    self.trigger_spin("Streamer")
                elif event.key == pygame.K_4:
                    self.trigger_dance("Streamer")
                elif event.key == pygame.K_5:
                    self.trigger_panic("Streamer")
                elif event.key == pygame.K_6:
                    self.trigger_boba("Streamer")
                elif event.key == pygame.K_7:
                    self.trigger_rage("Streamer")
                elif event.key == pygame.K_8:
                    self.trigger_sleep("Streamer")
                elif event.key == pygame.K_9:
                    self.trigger_tomato("Streamer")
                elif event.key == pygame.K_h:
                    self.cycle_accessory()
                elif event.key == pygame.K_v:
                    self.toggle_manual_mic()
                elif event.key == pygame.K_s:
                    if hasattr(self, "tts") and self.tts:
                        self.tts.cycle_speed()
                elif event.key == pygame.K_l:
                    if hasattr(self, "tts") and self.tts:
                        self.tts.toggle_engine()
                elif event.key == pygame.K_HOME:
                    self.trigger_stream_closing()

        # Gambar background chroma atau brick wall rumah hantu
        bg_name = self.color_keys[self.current_color_idx]
        if bg_name == "BRICK_WALL" and getattr(self, "bg_brick_wall", None):
            self.screen.blit(self.bg_brick_wall, (0, 0))
        else:
            bg_rgb = CHROMA_PALETTE.get(bg_name, (0, 255, 0))
            self.screen.fill(bg_rgb)

        now = time.time()

        # Hitung animasi bobbing
        offset_y = 0
        if self.enable_bobbing:
            is_talking = self.mic_lip_sync.is_speaking() if self.manual_mic_mode else self.tts.is_speaking
            speed = 8.0 if is_talking else 3.0
            amplitude = 4.0 if is_talking else 2.0
            offset_y = int(math.sin(now * speed) * amplitude)

        # Hitung animasi kedip mata alami (Auto-Blink)
        if not self.is_blinking:
            if now >= self.next_blink_time:
                self.is_blinking = True
                self.blink_start_time = now
                self.is_double_blink = random.random() < 0.18
        else:
            if now - self.blink_start_time >= self.blink_duration:
                self.is_blinking = False
                if getattr(self, "is_double_blink", False):
                    self.next_blink_time = now + 0.10
                    self.is_double_blink = False
                else:
                    self.next_blink_time = now + random.uniform(2.5, 4.5)

        # Posisi dasar karakter di tengah layar
        base_cx = self.width // 2
        base_cy = int(self.height * 0.64)
        center_x = base_cx
        center_y = base_cy + offset_y

        # Modifikasi gerak & posisi khusus interaksi animasi
        if self.active_interaction == "DANCE":
            jump_p = (now * 4.6) % 1.0
            jump_y = -int(math.sin(jump_p * math.pi) * 32)
            center_y += jump_y
        elif self.active_interaction == "PANIC":
            center_x += random.randint(-5, 5)
            center_y += random.randint(-2, 2)
        elif self.active_interaction == "RAGE":
            center_x += random.randint(-2, 2)
        elif self.is_sleeping or self.active_interaction == "SLEEP":
            center_y += 18
        elif self.active_interaction == "TOMATO":
            if getattr(self, "tomato_outcome", "DODGE") == "DODGE":
                inter_prog = (now - self.interaction_timer) / max(0.01, self.interaction_duration)
                if 0.22 <= inter_prog <= 0.65:
                    duck_p = (inter_prog - 0.22) / 0.43
                    center_y += int(math.sin(duck_p * math.pi) * 44)

        alpha = 255
        custom_sprite = None

        # Evaluasi Animasi Idle Trik Hantu (Menghilang & Muncul Tiba-tiba dari Bawah)
        if self.idle_trick_enabled:
            # Jika sedang bicara atau ada balon ucapan aktif, batalkan trik dan kembali normal seketika
            if self.tts.is_speaking or (self.show_speech_bubble and self.tts.get_active_text()):
                if self.idle_state != "NORMAL":
                    self.idle_state = "NORMAL"
                    self.next_idle_trick_time = now + random.uniform(20.0, 35.0)
            else:
                if self.idle_state == "NORMAL":
                    if now >= self.next_idle_trick_time:
                        self.idle_state = "VANISH"
                        self.idle_timer = now
                        # Munculkan partikel kabut halus saat menghilang
                        for _ in range(6):
                            self.particles.append({
                                'x': base_cx + random.randint(-self.target_size // 4, self.target_size // 4),
                                'y': base_cy + random.randint(-self.target_size // 4, self.target_size // 4),
                                'vx': random.uniform(-1.0, 1.0),
                                'vy': random.uniform(-2.2, -0.6),
                                'life': 1.0,
                                'radius': random.randint(4, 9)
                            })

                elif self.idle_state == "VANISH":
                    p = min(1.0, (now - self.idle_timer) / 0.8)
                    alpha = max(0, min(255, int(255 * (1.0 - p))))
                    center_y = base_cy - int(p * 20) + offset_y
                    if p >= 1.0:
                        self.idle_state = "HIDDEN"
                        self.idle_timer = now
                        self.hidden_duration = random.uniform(1.2, 2.2)

                elif self.idle_state == "HIDDEN":
                    alpha = 0
                    if now - self.idle_timer >= self.hidden_duration:
                        # Pilih posisi muncul dari bawah: kiri, tengah, atau kanan
                        self.peek_x = random.choice([
                            int(self.width * 0.32),
                            self.width // 2,
                            int(self.width * 0.68)
                        ])
                        self.idle_state = "PEEK_RISE"
                        self.idle_timer = now
                        sfx_player.play("boo_pop")
                        # Partikel efek pop-up muncul dari bawah
                        for _ in range(5):
                            self.particles.append({
                                'x': self.peek_x + random.randint(-40, 40),
                                'y': self.height - 20,
                                'vx': random.uniform(-1.5, 1.5),
                                'vy': random.uniform(-3.0, -1.0),
                                'life': 0.8,
                                'radius': random.randint(3, 7)
                            })

                elif self.idle_state == "PEEK_RISE":
                    p = min(1.0, (now - self.idle_timer) / 0.45)
                    e = self.ease_out_back(p)
                    start_y = self.height + self.target_size // 2
                    target_peek_y = self.height - int(self.target_size * 0.38)
                    center_x = self.peek_x
                    center_y = int(start_y + (target_peek_y - start_y) * e)
                    alpha = 255
                    custom_sprite = self.img_open # Tangan terangkat menggemaskan saat nongol
                    if p >= 1.0:
                        self.idle_state = "PEEK_HOLD"
                        self.idle_timer = now
                        self.hold_duration = random.uniform(0.9, 1.5)

                elif self.idle_state == "PEEK_HOLD":
                    center_x = self.peek_x + int(math.sin((now - self.idle_timer) * 10) * 3)
                    center_y = self.height - int(self.target_size * 0.38)
                    alpha = 255
                    custom_sprite = self.img_blink_open if self.is_blinking else self.img_open
                    if now - self.idle_timer >= self.hold_duration:
                        self.idle_state = "FLOAT_HOME"
                        self.idle_timer = now

                elif self.idle_state == "FLOAT_HOME":
                    p = min(1.0, (now - self.idle_timer) / 1.0)
                    e = self.ease_in_out(p)
                    start_peek_y = self.height - int(self.target_size * 0.38)
                    center_x = int(self.peek_x + (base_cx - self.peek_x) * e)
                    center_y = int(start_peek_y + (base_cy - start_peek_y) * e) + offset_y
                    alpha = 255
                    if p >= 1.0:
                        self.idle_state = "NORMAL"
                        self.next_idle_trick_time = now + random.uniform(22.0, 38.0)

        # Update dan render partikel debu kabut hantu / hati / bintang (Maksimal 25 partikel)
        new_particles = []
        if len(self.particles) > 25:
            self.particles = self.particles[-25:]
        for pt in self.particles:
            pt['x'] += pt['vx']
            pt['y'] += pt['vy']
            pt['life'] -= 0.025
            if pt['life'] > 0:
                p_alpha = max(0, min(255, int(255 * pt['life'])))
                p_col = pt.get('color', (240, 245, 255))
                p_surf = pygame.Surface((pt['radius'] * 2, pt['radius'] * 2), pygame.SRCALPHA)
                pygame.draw.circle(p_surf, (*p_col, p_alpha), (pt['radius'], pt['radius']), pt['radius'])
                self.screen.blit(p_surf, (int(pt['x'] - pt['radius']), int(pt['y'] - pt['radius'])))
                new_particles.append(pt)
        self.particles = new_particles

        # Cek status interaksi visual penonton (PAT, TREAT, SPIN, DANCE, PANIC, BOBA, RAGE, SLEEP, TOMATO)
        inter_prog = 0.0
        if self.active_interaction:
            inter_elapsed = now - self.interaction_timer
            if inter_elapsed >= self.interaction_duration:
                if self.active_interaction != "SLEEP":
                    self.active_interaction = None
            else:
                inter_prog = inter_elapsed / max(0.01, self.interaction_duration)
                if self.active_interaction in ("PAT", "TREAT"):
                    custom_sprite = self.img_happy
                elif self.active_interaction == "DANCE":
                    custom_sprite = self.img_star
                elif self.active_interaction == "PANIC":
                    custom_sprite = self.img_shock
                elif self.active_interaction == "BOBA":
                    custom_sprite = self.img_shy
                elif self.active_interaction == "RAGE":
                    custom_sprite = self.img_angry
                elif self.active_interaction == "SLEEP" or self.is_sleeping:
                    custom_sprite = self.img_sleepy
                elif self.active_interaction == "TOMATO":
                    if getattr(self, "tomato_outcome", "DODGE") == "DODGE":
                        if inter_prog > 0.65:
                            custom_sprite = self.img_smug
                    else:
                        if inter_prog > 0.25:
                            custom_sprite = self.img_shock

        # Pilih sprite berdasarkan emosi dinamis (Nomor 1)
        active_emotion = self.tts.get_active_emotion() if hasattr(self.tts, "get_active_emotion") else "NORMAL"

        # Render avatar jika tampak
        rect = None
        if alpha > 0:
            if custom_sprite is not None:
                sprite = custom_sprite
            elif getattr(self, "active_closing", False):
                # Animasi melambaikan tangan ceria dengan ekspresi HAPPY saat closing stream
                wave_frame = self.img_wave1 if int(now * 3.5) % 2 == 0 else self.img_wave2
                sprite = wave_frame
            elif self.manual_mic_mode:
                # Mode Manual Microphone: Mulut avatar digerakkan oleh suara fisik streamer
                if self.mic_lip_sync.is_speaking():
                    sprite = self.img_blink_open if self.is_blinking else self.img_open
                else:
                    sprite = self.img_blink if self.is_blinking else self.img_closed
            elif active_emotion == "OJIGI":
                # Animasi membungkuk Ojigi ketika Ponyo meminta maaf atau melakukan kesalahan
                sprite = self.img_ojigi
            elif active_emotion == "HAPPY":
                sprite = self.img_blink_open if self.is_blinking else self.img_happy
            elif active_emotion == "SHOCK":
                sprite = self.img_shock
            elif active_emotion == "POUT":
                sprite = self.img_pout
            elif active_emotion == "THINK":
                sprite = self.img_think
            elif active_emotion == "CRY":
                sprite = self.img_cry
            elif active_emotion == "SMUG":
                sprite = self.img_smug
            elif active_emotion == "SHY":
                sprite = self.img_shy
            elif active_emotion == "SLEEPY":
                sprite = self.img_sleepy
            elif active_emotion == "ANGRY":
                sprite = self.img_angry
            elif active_emotion == "STAR":
                sprite = self.img_blink_open if self.is_blinking else self.img_star
            elif self.tts.is_speaking:
                sprite = self.img_blink_open if self.is_blinking else self.img_open
            else:
                sprite = self.img_blink if self.is_blinking else self.img_closed

            # Efek rotasi 360 derajat jika interaksi !spin sedang berlangsung
            if self.active_interaction == "SPIN":
                angle = -inter_prog * 720.0
                sprite = pygame.transform.rotate(sprite, angle)

            rect = sprite.get_rect(center=(center_x, center_y))
            if alpha < 255:
                s_copy = sprite.copy()
                s_copy.set_alpha(alpha)
                self.screen.blit(s_copy, rect)
            else:
                self.screen.blit(sprite, rect)

            # Render aksesoris pixel-art jika sedang dipakai / otomatis saat smug/star (Saran Nomor 2)
            acc_name = self.current_accessory
            if not acc_name and active_emotion == "SMUG":
                acc_name = "glasses"
            elif not acc_name and active_emotion == "STAR":
                acc_name = "crown"

            if acc_name and acc_name in self.accessories:
                acc_surf = self.accessories[acc_name]
                if self.active_interaction == "SPIN":
                    acc_surf = pygame.transform.rotate(acc_surf, angle)
                if alpha < 255:
                    a_copy = acc_surf.copy()
                    a_copy.set_alpha(alpha)
                    self.screen.blit(a_copy, rect)
                else:
                    self.screen.blit(acc_surf, rect)

            # Render efek overlay interaksi penonton (PAT, TREAT, DANCE, PANIC, BOBA, RAGE, SLEEP, TOMATO)
            if self.active_interaction == "PAT":
                self._draw_headpat_hand(center_x, rect.top + int(self.target_size * 0.14), now - self.interaction_timer)
            elif self.active_interaction == "TREAT":
                self._draw_candy_treat(center_x, center_y - 10, inter_prog)
            elif self.active_interaction == "DANCE":
                self._draw_confetti(now)
            elif self.active_interaction == "PANIC":
                self._draw_panic_sweat(center_x, rect.top, now)
            elif self.active_interaction == "BOBA":
                self._draw_boba_cup(center_x, center_y, inter_prog)
            elif self.active_interaction == "RAGE":
                self._draw_steam_puffs(center_x, rect.top, now)
            elif self.active_interaction == "SLEEP" or self.is_sleeping:
                self._draw_zzz_bubble(center_x, rect.top, now)
            elif self.active_interaction == "TOMATO":
                self._draw_tomato_interaction(center_x, center_y, inter_prog)

        # Gambar Balon Teks Ucapan (Speech Bubble) atau Teks Kejutan BOOO
        if rect:
            active_text = self.tts.get_active_text() if self.show_speech_bubble else ""
            if active_text:
                self.draw_speech_bubble(active_text, rect.top)
            elif self.idle_state in ("PEEK_RISE", "PEEK_HOLD"):
                self.draw_boo_bubble(center_x, rect.top)

        pygame.display.flip()
        self.clock.tick(60)
        return True

    def close(self):
        self.running = False
        if hasattr(self, "mic_lip_sync") and self.mic_lip_sync:
            self.mic_lip_sync.stop()
        pygame.quit()

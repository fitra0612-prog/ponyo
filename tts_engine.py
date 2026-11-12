import asyncio
import os
import time
import tempfile
import threading
import socket
import subprocess
import aiohttp
from aiohttp.abc import AbstractResolver
import pygame
from config import (
    TTS_VOICE, TTS_RATE, TTS_PITCH, TTS_SPEED,
    TTS_ENGINE_TYPE, PIPER_MODEL_PATH, PIPER_CONFIG_PATH, PIPER_PITCH_FACTOR
)

# Resolver cerdas anti-gagal untuk menangani DNS blip / getaddrinfo failed
class ResilientResolver(AbstractResolver):
    KNOWN_BING_IPS = ['150.171.27.10', '150.171.28.10']

    async def resolve(self, host, port=443, family=socket.AF_INET):
        try:
            # 1. Coba resolusi DNS standar (IPv4)
            infos = socket.getaddrinfo(host, port, socket.AF_INET, socket.SOCK_STREAM)
            hosts = []
            for info in infos:
                ip = info[4][0]
                hosts.append({
                    'hostname': host,
                    'host': ip,
                    'port': port,
                    'family': socket.AF_INET,
                    'proto': 0,
                    'flags': socket.AI_NUMERICHOST
                })
            if hosts:
                return hosts
        except Exception:
            pass

        # 2. Fallback otomatis ke IP redundan Microsoft jika DNS gagal resolve
        hosts = []
        for ip in self.KNOWN_BING_IPS:
            hosts.append({
                'hostname': host,
                'host': ip,
                'port': port,
                'family': socket.AF_INET,
                'proto': 0,
                'flags': socket.AI_NUMERICHOST
            })
        return hosts

    async def close(self):
        pass

class TTSEngine:
    def __init__(self, voice: str = TTS_VOICE):
        self.voice = voice
        self.is_speaking = False
        self.is_interruptible = False
        self.is_muted = False  # True saat mode manual mic VTuber aktif
        self.emergency_silence = False
        self._mute_before_emergency = False
        self._lock = threading.Lock()

        # Kecepatan bicara TTS (Pilihan: 0.0, 0.5, 1.0, 1.5, 2.0)
        self.speed = float(TTS_SPEED)
        self.speed_levels = [0.0, 0.5, 1.0, 1.5, 2.0]

        # Mode Engine: "local" (Piper 100% Offline) atau "cloud" (Edge-TTS)
        self.engine_type = TTS_ENGINE_TYPE
        self.pitch_factor = float(PIPER_PITCH_FACTOR)
        self.piper_voice = None
        self._init_piper()
        
        # Teks ucapan saat ini & timer balon ucapan
        self.current_text = ""
        self.current_emotion = "NORMAL"
        self.last_speech_time = 0.0
        self.speech_bubble_linger = 2.2  # Tahan balon 2.2 detik setelah audio selesai agar penonton sempat membaca
        
        # Inisialisasi mixer pygame jika belum
        if not pygame.mixer.get_init():
            pygame.mixer.init()

    @staticmethod
    def detect_emotion(text: str) -> str:
        """Mendeteksi ekspresi emosi wajah Ponyo dari kalimat yang diucapkan (10 Emosi)"""
        if not text:
            return "NORMAL"
        t = text.lower()
        # Ekspresi OJIGI khusus saat Ponyo meminta maaf / melakukan kesalahan (Zarei Bow)
        if any(w in t for w in [
            "minta maaf", "maaf ya", "maafkan", "mohon maaf", "sorry", "salah langkah",
            "blunder", "kesalahan", "ampun", "gomen", "sumimasen", "khilaf", "ojigi"
        ]):
            return "OJIGI"
        if any(w in t for w in [
            "sedih", "nangis", "yah kalah", "kalah lagi", "hiks", "mati lagi", "kecewa", "sayang sekali", "gagal"
        ]):
            return "CRY"
        if any(w in t for w in [
            "balas dendam", "marah", "awas ya", "jangan motong", "geram", "kesal", "sebel"
        ]):
            return "ANGRY"
        if any(w in t for w in [
            "aduh", "waduh", "kaget", "hampir", "nyaris", "disekak", "awas",
            "bahaya", "copot", "tabrak", "kepentok", "astaga", "ya ampun"
        ]):
            return "SHOCK"
        if any(w in t for w in [
            "kan ponyo bilang", "jago kan", "jenius", "jago banget", "ez", "easy", "udah dibilang", "santai aja"
        ]):
            return "SMUG"
        if any(w in t for w in [
            "banyak makanan", "rejeki nomplok", "makanan gratis", "berkilau", "wahhh", "wahh", "bintang", "emas"
        ]):
            return "STAR"
        if any(w in t for w in [
            "malu", "tersipu", "salting", "makasih pujiannya", "bisa aja", "jadi malu", "manis banget"
        ]):
            return "SHY"
        if any(w in t for w in [
            "turu", "ngantuk", "tidur", "hoaam", "hoam", "lelah", "istirahat dulu"
        ]):
            return "SLEEPY"
        if any(w in t for w in [
            "jahat", "curang", "usil", "iseng", "ngambek", "jangan gitu", "masa ponyo", "kok gitu"
        ]):
            return "POUT"
        if any(w in t for w in [
            "kira-kira", "hmm", "gimana ya", "strategi", "mikir",
            "bingung", "kenapa ya", "analisis", "penasaran"
        ]):
            return "THINK"
        if any(w in t for w in [
            "makasih", "terima kasih", "senang", "hore", "menang", "skakmat",
            "mantap", "hebat", "gg", "sayang", "permen", "elus", "asik",
            "asyik", "seru banget", "halo", "selamat datang", "rejeki", "nyam"
        ]):
            return "HAPPY"
        return "NORMAL"

    def get_active_emotion(self) -> str:
        if self.is_speaking:
            return self.current_emotion
        if self.current_text and (time.time() - self.last_speech_time < self.speech_bubble_linger):
            return self.current_emotion
        return "NORMAL"

    def interrupt(self):
        """Menghentikan audio yang sedang diputar jika bersifat interruptible."""
        try:
            if pygame.mixer.get_init() and pygame.mixer.music.get_busy():
                pygame.mixer.music.stop()
        except Exception:
            pass
        self.is_speaking = False
        self.current_text = ""

    def can_speak(self) -> bool:
        return not self.is_muted and not self.emergency_silence

    def set_emergency_silence(self, enabled: bool = True) -> bool:
        """Host kill-switch: hentikan audio dan blokir speech sampai dibuka lagi."""
        self.emergency_silence = bool(enabled)
        if self.emergency_silence:
            self._mute_before_emergency = bool(self.is_muted)
            self.is_muted = True
            self.interrupt()
            self.current_text = ""
            self.current_emotion = "NORMAL"
            print("[TTS SAFETY] Emergency silence aktif.")
        else:
            self.is_muted = bool(self._mute_before_emergency)
            print("[TTS SAFETY] Emergency silence nonaktif.")
        return self.emergency_silence

    def get_edge_rate(self) -> str:
        """Mengubah float speed (0.0, 0.5, 1.0, 1.5, 2.0) ke format persentase Edge-TTS"""
        if self.speed <= 0.0:
            return "-100%"
        elif abs(self.speed - 0.5) < 0.01:
            return "-50%"
        elif abs(self.speed - 1.0) < 0.01:
            return "+5%"
        elif abs(self.speed - 1.5) < 0.01:
            return "+50%"
        elif self.speed >= 2.0:
            return "+100%"
        else:
            pct = int((self.speed - 1.0) * 100)
            sign = "+" if pct >= 0 else ""
            return f"{sign}{pct}%"

    def get_sapi_rate(self) -> int:
        """Mengubah float speed ke rentang integer SAPI Windows (-10 s.d 10)"""
        if self.speed <= 0.0:
            return -10
        elif abs(self.speed - 0.5) < 0.01:
            return -5
        elif abs(self.speed - 1.0) < 0.01:
            return 1
        elif abs(self.speed - 1.5) < 0.01:
            return 5
        elif self.speed >= 2.0:
            return 10
        else:
            return int(max(-10, min(10, (self.speed - 1.0) * 10)))

    def set_speed(self, speed: float) -> float:
        """Mengatur kecepatan TTS ke salah satu level: 0.0, 0.5, 1.0, 1.5, 2.0"""
        closest = min(self.speed_levels, key=lambda x: abs(x - float(speed)))
        self.speed = closest
        label = f"{self.speed}x"
        if self.speed == 0.0:
            desc = "Hening / Mute (Hanya Balon Teks)"
        elif self.speed == 0.5:
            desc = "Lambat (0.5x)"
        elif self.speed == 1.0:
            desc = "Normal (1.0x)"
        elif self.speed == 1.5:
            desc = "Cepat (1.5x)"
        else:
            desc = "Sangat Cepat (2.0x)"
        print(f"[TTS SPEED] Kecepatan bicara Ponyo diatur ke: {label} ({desc})")
        return self.speed

    def cycle_speed(self) -> float:
        """Berganti ke level kecepatan berikutnya: 0.0 -> 0.5 -> 1.0 -> 1.5 -> 2.0 -> 0.0"""
        idx = 0
        for i, lvl in enumerate(self.speed_levels):
            if abs(self.speed - lvl) < 0.01:
                idx = (i + 1) % len(self.speed_levels)
                break
        self.speed = self.speed_levels[idx]
        return self.set_speed(self.speed)

    def _init_piper(self):
        """Inisialisasi Piper Local Neural TTS jika file model tersedia"""
        self.piper_voice = None
        if os.path.exists(PIPER_MODEL_PATH) and os.path.exists(PIPER_CONFIG_PATH):
            try:
                from piper import PiperVoice
                self.piper_voice = PiperVoice.load(PIPER_MODEL_PATH, config_path=PIPER_CONFIG_PATH)
                print(f"[TTS LOKAL] Model Piper Neural TTS (100% Offline) siap: {os.path.basename(PIPER_MODEL_PATH)}")
            except Exception as e:
                print(f"[TTS LOKAL] Gagal memuat model Piper: {e}")
        else:
            print("[TTS LOKAL] File model Piper belum ditemukan di folder models/piper.")

    def set_engine(self, engine_name: str) -> str:
        """Mengatur engine TTS: 'local' (Piper Offline) atau 'cloud' (Edge-TTS)"""
        engine_clean = engine_name.strip().lower()
        if engine_clean in ["local", "lokal", "offline", "piper"]:
            if not self.piper_voice:
                self._init_piper()
            if self.piper_voice:
                self.engine_type = "local"
                msg = "LOKAL (Piper Neural TTS - 100% Offline & Instan)"
            else:
                msg = "Model lokal belum siap, tetap menggunakan Cloud."
        else:
            self.engine_type = "cloud"
            msg = "CLOUD (Microsoft Edge-TTS id-ID-GadisNeural)"
        print(f"[TTS ENGINE] Mode Text-to-Speech aktif: {msg}")
        return self.engine_type

    def toggle_engine(self) -> str:
        """Toggle antara engine Lokal Piper dan Cloud Edge-TTS (Tombol [L])"""
        new_eng = "cloud" if self.engine_type == "local" else "local"
        self.set_engine(new_eng)
        return self.engine_type

    def _synthesize_piper(self, text: str, output_wav: str) -> bool:
        """Sintesis suara Bahasa Indonesia menggunakan model Piper Neural TTS 100% lokal (In-Memory Streaming)"""
        if not self.piper_voice:
            return False
        try:
            import io
            import wave
            from piper.config import SynthesisConfig

            # Kalkulasi pitch dan speed
            pitch_f = max(0.5, float(getattr(self, "pitch_factor", 1.20)))
            current_spd = max(0.2, float(self.speed))
            eff_length = pitch_f / current_spd
            cfg = SynthesisConfig(length_scale=eff_length)
            target_framerate = int(22050 * pitch_f)

            # Sintesis langsung ke in-memory BytesIO (Bebas I/O disk)
            mem_raw = io.BytesIO()
            with wave.open(mem_raw, "wb") as wf:
                self.piper_voice.synthesize_wav(text, wf, syn_config=cfg)

            mem_raw.seek(0)
            with wave.open(mem_raw, "rb") as rf:
                raw_bytes = rf.readframes(rf.getnframes())

            with wave.open(output_wav, "wb") as wf:
                wf.setnchannels(1)
                wf.setsampwidth(2)
                wf.setframerate(target_framerate)
                wf.writeframes(raw_bytes)

            return os.path.exists(output_wav) and os.path.getsize(output_wav) > 0
        except Exception as e:
            print(f"[TTS LOKAL] Error saat sintesis Piper: {e}")
            return False

    def get_active_text(self) -> str:
        """Mengembalikan teks yang sedang/baru saja diucapkan untuk ditampilkan di Speech Bubble"""
        if self.is_speaking:
            return self.current_text
        if self.current_text and (time.time() - self.last_speech_time < self.speech_bubble_linger):
            return self.current_text
        return ""

    async def _synthesize_edge_tts(self, text: str, output_path: str):
        import edge_tts
        resolver = ResilientResolver()
        conn = aiohttp.TCPConnector(resolver=resolver, family=socket.AF_INET)
        communicate = edge_tts.Communicate(
            text=text,
            voice=self.voice,
            rate=self.get_edge_rate(),
            pitch=TTS_PITCH,
            connector=conn
        )
        await communicate.save(output_path)

    def _synthesize_offline_sapi(self, text: str, wav_path: str) -> bool:
        """Fallback darurat menggunakan Windows Speech Synthesizer bawaan (100% Offline)"""
        clean_text = text.replace('"', ' ').replace("'", " ")
        ps_cmd = (
            f"Add-Type -AssemblyName System.Speech; "
            f"$s = New-Object System.Speech.Synthesis.SpeechSynthesizer; "
            f"$idVoice = $s.GetInstalledVoices() | Where-Object {{ $_.VoiceInfo.Culture.Name -like 'id*' -and $_.Enabled }}; "
            f"if ($idVoice) {{ $s.SelectVoice($idVoice[0].VoiceInfo.Name); }} "
            f"else {{ $fem = $s.GetInstalledVoices() | Where-Object {{ $_.VoiceInfo.Gender -eq 'Female' -and $_.Enabled }}; if ($fem) {{ $s.SelectVoice($fem[0].VoiceInfo.Name); }} }} "
            f"$s.Rate = {self.get_sapi_rate()}; "
            f"$s.SetOutputToWaveFile('{wav_path}'); "
            f"$s.Speak('{clean_text}'); "
            f"$s.Dispose();"
        )
        try:
            subprocess.run(
                ["powershell", "-NoProfile", "-Command", ps_cmd],
                timeout=6,
                check=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            return os.path.exists(wav_path) and os.path.getsize(wav_path) > 0
        except Exception:
            return False

    def speak_text(self, text: str, interruptible: bool = False):
        """Menyintesis suara dan memutarnya secara sinkron di worker thread"""
        if not self.can_speak():
            return
        if not text or not text.strip():
            return

        with self._lock:
            self.is_interruptible = interruptible
            # Reset teks aktif agar balon ucapan lama tidak muncul selama proses sintesis audio
            self.current_text = ""
            self.last_speech_time = 0.0

            # Jika kecepatan 0.0 (Mode Hening / Silent), tampilkan balon teks tanpa memutar audio
            if self.speed <= 0.0:
                clean_text = text.strip()
                self.current_text = clean_text
                self.current_emotion = self.detect_emotion(clean_text)
                self.is_speaking = True
                self.last_speech_time = time.time()
                display_dur = min(3.5, max(1.2, len(clean_text) * 0.05))
                time.sleep(display_dur)
                self.is_speaking = False
                self.last_speech_time = time.time()
                return

            # Buat temporary file untuk audio
            with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as tf:
                temp_mp3 = tf.name
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tf:
                temp_wav = tf.name

            audio_to_play = None
            try:
                # 1. Jika mode "local" aktif: Utamakan Piper Neural TTS (100% Offline & Cepat)
                if self.engine_type == "local" and self.piper_voice:
                    if self._synthesize_piper(text, temp_wav):
                        audio_to_play = temp_wav

                # 2. Jika mode "cloud" atau Piper belum berhasil: Coba Edge-TTS Cloud
                if not audio_to_play:
                    for attempt in range(2):
                        try:
                            asyncio.run(self._synthesize_edge_tts(text, temp_mp3))
                            if os.path.exists(temp_mp3) and os.path.getsize(temp_mp3) > 0:
                                audio_to_play = temp_mp3
                                break
                        except Exception as err:
                            if attempt == 0:
                                time.sleep(0.4)
                            else:
                                print(f"[TTS] Edge-TTS koneksi terganggu ({err}).")

                # 3. Jika Edge-TTS gagal dan belum coba Piper: Coba Piper sebagai fallback
                if not audio_to_play and self.piper_voice:
                    if self._synthesize_piper(text, temp_wav):
                        audio_to_play = temp_wav

                # 4. Fallback darurat terakhir: Windows SAPI bawaan
                if not audio_to_play:
                    if self._synthesize_offline_sapi(text, temp_wav):
                        audio_to_play = temp_wav

                # 5. Mainkan audio yang berhasil disintesis:
                #    BALON TEKS DAN EMOSI HANYA MUNCUL DI SINI SETELAH AUDIO SELESAI DISIAPKAN!
                if audio_to_play and os.path.exists(audio_to_play) and os.path.getsize(audio_to_play) > 0:
                    pygame.mixer.music.load(audio_to_play)

                    # Update teks, emosi, dan status bicara tepat saat pemutaran audio dimulai
                    clean_text = text.strip()
                    self.current_text = clean_text
                    self.current_emotion = self.detect_emotion(clean_text)
                    self.is_speaking = True
                    self.last_speech_time = time.time()

                    pygame.mixer.music.play()

                    while pygame.mixer.music.get_busy():
                        time.sleep(0.04)

            except Exception as e:
                print(f"[TTS] Error saat memainkan audio: {e}")
            finally:
                self.is_speaking = False
                self.last_speech_time = time.time()
                try:
                    pygame.mixer.music.unload()
                    if os.path.exists(temp_mp3):
                        os.remove(temp_mp3)
                    if os.path.exists(temp_wav):
                        os.remove(temp_wav)
                except Exception:
                    pass

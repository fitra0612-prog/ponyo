"""
RETRO 8-BIT SOUNDBOARD & SFX ENGINE FOR PONYO VTUBER (NOMOR 3)
==============================================================
Menghasilkan dan memutar efek suara retro imut (8-bit/chime) secara otomatis:
- boo_pop : Saat Ponyo muncul mengejutkan dari bawah layar ("Boo!")
- fanfare : Saat makan banyak di Slither.io / menang catur / naik level penonton
- fail    : Saat cacing menabrak / kalah
- pat     : Saat penonton mengelus kepala (!pat / !elus) atau memberi permen (!permen)
- spin    : Saat penonton memutar tubuh Ponyo (!spin)
"""

import os
import math
import wave
import struct
import pygame

SFX_DIR = os.path.join(os.path.dirname(__file__), "sfx")


def _generate_tone_sequence(filepath: str, notes: list, sample_rate: int = 44100):
    """
    notes: list of (freq_start, freq_end, duration_s, volume)
    Menghasilkan file WAV 16-bit mono dengan envelope halus.
    """
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    samples = []
    for f_start, f_end, dur, vol in notes:
        n_samples = int(sample_rate * dur)
        for i in range(n_samples):
            t = i / sample_rate
            prog = i / max(1, n_samples)
            freq = f_start + (f_end - f_start) * prog
            # Envelope fade-in & fade-out lembut agar tidak klik
            env = 1.0
            if prog < 0.08:
                env = prog / 0.08
            elif prog > 0.75:
                env = (1.0 - prog) / 0.25
            # Campuran sine + sedikit triangle harmonic agar terdengar chiptune retro imut
            val = (
                0.75 * math.sin(2.0 * math.pi * freq * t) +
                0.25 * math.sin(2.0 * math.pi * (freq * 2.0) * t)
            )
            sample_int = int(max(-32767, min(32767, val * vol * env * 32767)))
            samples.append(sample_int)

    with wave.open(filepath, "w") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes(struct.pack(f"<{len(samples)}h", *samples))


def ensure_sfx_files(sfx_dir: str = SFX_DIR):
    os.makedirs(sfx_dir, exist_ok=True)

    # 1. boo_pop.wav: Suara Pop/Chime kejutan imut saat muncul "Boo!"
    boo_path = os.path.join(sfx_dir, "boo_pop.wav")
    if not os.path.exists(boo_path):
        _generate_tone_sequence(boo_path, [
            (440.0, 660.0, 0.07, 0.35),
            (660.0, 987.7, 0.09, 0.40),
            (987.7, 1318.5, 0.14, 0.38),
        ])

    # 2. fanfare.wav: Suara kemenangan / makan banyak / naik level (C5 - E5 - G5 - C6)
    fanfare_path = os.path.join(sfx_dir, "fanfare.wav")
    if not os.path.exists(fanfare_path):
        _generate_tone_sequence(fanfare_path, [
            (523.25, 523.25, 0.09, 0.35),
            (659.25, 659.25, 0.09, 0.35),
            (783.99, 783.99, 0.10, 0.38),
            (1046.50, 1046.50, 0.22, 0.42),
        ])

    # 3. fail.wav: Suara gagal / nabrak lucu (turun nada)
    fail_path = os.path.join(sfx_dir, "fail.wav")
    if not os.path.exists(fail_path):
        _generate_tone_sequence(fail_path, [
            (392.00, 370.00, 0.11, 0.35),
            (349.23, 329.63, 0.11, 0.35),
            (311.13, 261.63, 0.24, 0.38),
        ])

    # 4. pat.wav: Suara sparkle manis saat dielus (!pat) atau dikasih permen (!permen)
    pat_path = os.path.join(sfx_dir, "pat.wav")
    if not os.path.exists(pat_path):
        _generate_tone_sequence(pat_path, [
            (659.25, 783.99, 0.07, 0.32),
            (880.00, 1046.50, 0.08, 0.35),
            (1174.66, 1318.51, 0.14, 0.35),
        ])

    # 5. spin.wav: Suara berputar 360 derajat (!spin)
    spin_path = os.path.join(sfx_dir, "spin.wav")
    if not os.path.exists(spin_path):
        _generate_tone_sequence(spin_path, [
            (350.0, 880.0, 0.16, 0.32),
            (880.0, 440.0, 0.14, 0.30),
            (440.0, 1046.5, 0.18, 0.35),
        ])


class SFXEngine:
    def __init__(self, sfx_dir: str = SFX_DIR):
        self.sfx_dir = sfx_dir
        self.is_enabled = True
        self.sounds = {}
        ensure_sfx_files(self.sfx_dir)
        self._load_sounds()

    def _load_sounds(self):
        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init()
            for name in ["boo_pop", "fanfare", "fail", "pat", "spin"]:
                p = os.path.join(self.sfx_dir, f"{name}.wav")
                if os.path.exists(p):
                    snd = pygame.mixer.Sound(p)
                    snd.set_volume(0.45)
                    self.sounds[name] = snd
        except Exception as e:
            print(f"[SFX] Gagal memuat sound effects: {e}")

    def play(self, name: str):
        if not self.is_enabled:
            return
        try:
            if not self.sounds:
                self._load_sounds()
            snd = self.sounds.get(name)
            if snd:
                snd.play()
        except Exception:
            pass


sfx_player = SFXEngine()

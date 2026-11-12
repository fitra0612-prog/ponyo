import sys
import os
import time
import random
import queue
import threading

from config import (
    YOUTUBE_VIDEO_ID,
    ENABLE_AUTO_YAP,
    YAP_INTERVAL,
    YAP_PLAYFUL_CHANCE,
    ENABLE_MANUAL_SLITHER,
    MANUAL_BOOST_DURATION,
    MANUAL_BOOST_COOLDOWN,
    ENABLE_CHESS_COACH,
    CHESS_COACH_DEPTH,
    CHESS_AUTO_PLAY,
    SAWERIA_ENABLED,
    SAWERIA_HOST,
    SAWERIA_PORT,
    SAWERIA_STREAM_KEY
)
from ai_brain import AIBrain
from tts_engine import TTSEngine
from chat_listener import ChatListener
from vtuber_display import VTuberDisplay
from screen_commentator import ScreenCommentator
from manual_slither_hook import ManualSlitherHook
from chess_coach import ChessCoach
from self_improvement import stream_reflector
from sfx_engine import sfx_player
from chat_quiz import chat_quiz
from saweria_receiver import SaweriaReceiver
from worker_runtime import WorkerRuntime
from ollama_runtime import ollama_health
from local_vlm import local_vlm
from content_policy import sanitize_output
from runtime_metrics import runtime_metrics

# Jalur kerja terpisah: chat tetap memprioritaskan pesan terbaru, sedangkan TTS
# memiliki antrean sendiri agar sintesis tidak memblokir ingestion dan VLM.
STREAM_WORKERS = None


def _speak_tts(tts_engine, text, interruptible=False, wait=False, priority=False):
    # Pesan prioritas membuang yapping/audio lama yang masih menunggu, tetapi
    # tidak memotong ucapan penting kecuali ucapan itu memang interruptible.
    if priority and STREAM_WORKERS is not None:
        dropped = STREAM_WORKERS.clear_lane("tts")
        if dropped:
            print(f"[TTS QUEUE] Membuang {dropped} audio lama demi pesan prioritas.")
        if tts_engine.is_speaking and tts_engine.is_interruptible:
            tts_engine.interrupt()
    # Pertahanan terakhir: tidak ada teks yang boleh mencapai Piper tanpa gate.
    text = sanitize_output(text)
    if STREAM_WORKERS is not None:
        if wait:
            done = threading.Event()
            accepted = STREAM_WORKERS.submit_result(
                "tts", tts_engine.speak_text, lambda _result: done.set(),
                text, interruptible=interruptible,
            )
            if accepted:
                done.wait()
                return
        else:
            accepted = STREAM_WORKERS.submit("tts", tts_engine.speak_text, text, interruptible=interruptible)
            if accepted:
                return
    TTSEngine.speak_text(tts_engine, text, interruptible=interruptible)

# Import Game Bridge untuk reaksi game real-time
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
try:
    from game_bridge import bridge
except Exception:
    bridge = None

def print_banner():
    banner = """
=============================================================
      AI VTUBER PONYO (THE CUTE GHOST) - LIVE STREAM BOT     
=============================================================
* Karakter: Ponyo si Hantu Imut (Retro Pixel Art)
* Mulut Avatar: Terbuka saat berbicara, tertutup saat diam
* Background: Green Screen Chroma Key (Siap untuk OBS Studio)
* Kontrol Display:
  - [C] : Ganti warna background (Hijau / Magenta / Biru / Hitam)
  - [B] : Nyalakan/Matikan animasi bobbing (melayang)
  - [T] : Nyalakan/Matikan balon teks ucapan (Speech Bubble)
  - [Y] : Nyalakan/Matikan Auto-Yapping (Komentar Layar)
  - [I] : Trik hantu (Menghilang & Muncul tiba-tiba dari bawah)
  - [M] : Nyalakan/Matikan Chat Usil Menekan Spasi (Manual Slither)
  - [K] : Nyalakan/Matikan Coach & Komentator Catur Ponyo (Default: Nonaktif)
  - [G] : Nyalakan/Matikan Auto-Play Bidak Catur oleh Ponyo (Default: Nonaktif)
  - [1] / [2] / [3] : Interaksi Elus (!pat) / Permen (!permen) / Putar (!spin)
  - [4] / [5] / [6] : Joget Hore (!hore) / Panik Shiver (!panik) / Minum Boba (!boba)
  - [7] / [8] / [9] : Mengambek Asap (!ngambek) / Tidur Zzz (!turu) / Lempar Tomat (!tomat)
  - [H] : Ganti Aksesoris/Topi Kepala (Pita / Penyihir / Mahkota / Kacamata / Bunga / Halo / Tanduk / Helm Ksatria)
  - [F10] : Emergency Silence (Hentikan dan blokir seluruh suara Ponyo)
  - [V] : Toggle Mode Suara (Bot AI Otomatis <-> Manual Microphone VTuber)
  - [S] : Ganti Kecepatan Bicara TTS (0.0x / 0.5x / 1.0x / 1.5x / 2.0x)
  - [L] : Ganti Mesin TTS (Lokal Piper 100% Offline <-> Cloud Edge-TTS)
  - [Home] : Closing Livestream (Ritual Pamit Penutup, Lambaian Tangan HAPPY & Auto-Exit)
  - [Esc] atau Tutup Window : Berhenti
* Integrasi Saweria: Webhook Receiver aktif di port 49225 (Auto-Dance, Konfeti, & TTS Terima Kasih)
=============================================================
"""
    print(banner)

GAME_REACTIONS = {
    "DEATH": [
        "Aduh maaf ya teman-teman, Ponyo salah langkah dan bikin kesalahan! Ponyo minta maaf, yuk coba lagi!",
        "Aduh, nabrak ular lain! Padahal Ponyo kan hantu, kok bisa nabrak ya? Yuk kita coba lagi!",
        "Yah kepentok musuh! Tenang guys, ronde baru dimulai, saatnya Ponyo balas dendam!",
        "Waduh musuhnya motong jalan Ponyo! Ayo gas lagi!"
    ],
    "FEAST": [
        "Wah, ada ular meledak di depan! Ayo sikat semua makanannya nyam nyam!",
        "Nyam nyam, banyak makanan gratis! Ular Ponyo makin gendut nih!",
        "Rejeki nomplok guys, sikat makanannya biar ular Ponyo makin panjang!"
    ],
    "NEAR_MISS": [
        "Waduh hampir aja kepentok! Jantung hantu Ponyo mau copot, untung selamat!",
        "Awas awas, nyaris banget! Huft, untung refleks Ponyo lincah!"
    ],
    "DEFENSIVE_COIL": [
        "Waduh dikepung musuh! Waktunya jurus melingkar bertahan!",
        "Ponyo melingkar dulu ya guys, jangan sampai ketabrak musuh!"
    ],
    "SPAWN": [
        "Boo! Ular hantu Ponyo kembali beraksi di arena! Semangat!"
    ]
}

def chat_worker(
    chat_queue: queue.Queue,
    ai_brain: AIBrain,
    tts_engine: TTSEngine,
    stop_event: threading.Event,
    commentator: ScreenCommentator = None,
    manual_hook: ManualSlitherHook = None,
    chess_coach: ChessCoach = None,
    display_ref: list = None,
    saweria_receiver: SaweriaReceiver = None
):
    """Worker background untuk memproses donasi Saweria, instruksi Coach Catur, antrean chat, komentar game, & auto-yapping"""
    last_activity_time = time.time()
    last_metrics_report = 0.0

    while not stop_event.is_set():
        # 0A. PRIORITAS UTAMA: Cek Donasi Saweria Real-Time (Auto-Dance, Konfeti, & TTS Terima Kasih)
        if saweria_receiver:
            donation = saweria_receiver.get_next_donation()
            if donation:
                donator = donation["donator"]
                amount = donation["amount"]
                message = donation["message"]

                disp_obj = display_ref[0] if display_ref and display_ref[0] else None
                if disp_obj:
                    disp_obj.wake_up()
                    disp_obj.trigger_dance(f"Saweria: {donator}")
                    # Jika donasi Sultan (>= 100.000), otomatis kenakan Mahkota Emas!
                    if amount >= 100000:
                        disp_obj.set_accessory("crown")

                sfx_player.play("fanfare")
                speech_text, tier = SaweriaReceiver.format_speech_response(donator, amount, message)
                print(f"\n[VTUBER SAWERIA RESPONSE - {tier}]: {speech_text}")

                if hasattr(ai_brain, "loyalty_system") and ai_brain.loyalty_system:
                    bonus_xp = max(50, amount // 100) # Rp 10.000 = 100 XP, Rp 50.000 = 500 XP
                    lvl_info = ai_brain.loyalty_system.add_xp(donator, bonus_xp)
                    if lvl_info.get("leveled_up"):
                        print(f"[SAWERIA LEVEL UP!] {donator} naik ke Level {lvl_info['level']} ({lvl_info['badge']})!")

                _speak_tts(tts_engine, speech_text, interruptible=False, priority=True)
                runtime_metrics.increment("donation_speech")
                last_activity_time = time.time()
                time.sleep(0.3)
                continue

        # 0B. PRIORITAS KILAT: Instruksi Langkah Terbaik Catur saat Giliran Pemain Tiba
        if chess_coach and chess_coach.is_enabled and not tts_engine.is_muted and not chess_coach.coach_queue.empty():
            if tts_engine.is_speaking and tts_engine.is_interruptible:
                tts_engine.interrupt()
                time.sleep(0.05)
            if not tts_engine.is_speaking:
                coach_res = chess_coach.get_coach_message()
                if isinstance(coach_res, tuple):
                    coach_msg, auto_move = coach_res
                else:
                    coach_msg, auto_move = coach_res, None

                if coach_msg:
                    # 1. Ponyo berbicara instruksi langkah sampai selesai
                    _speak_tts(tts_engine, coach_msg, interruptible=False, wait=True)
                    last_activity_time = time.time()

                    # 2. SETELAH SELESAI BICARA: Jika Auto-Play aktif, baru mainkan bidak di layar!
                    if auto_move and chess_coach.auto_play:
                        print(f"[PONYO AUTO-PLAY] TTS selesai diucapkan! Ponyo mulai menggerakkan bidak di layar: {auto_move}")
                        time.sleep(0.25)
                        chess_coach.execute_auto_move(auto_move)
                    continue

        # 1. Cek chat dari penonton (Prioritas Utama Interaksi)
        try:
            item = chat_queue.get(timeout=0.10)
            chat_queue.task_done()

            # Mode Real-Time: Jika ada pesan menumpuk selama Ponyo bicara,
            # lewati pesan lama dan langsung ambil pesan yang paling baru (terbaru).
            skipped_count = 0
            while not chat_queue.empty():
                try:
                    old_author, old_message = item
                    # Catat pesan lama yang dilewati ke memori sementara agar Ponyo tetap tahu penonton tersebut sempat chat
                    if hasattr(ai_brain, "memory") and ai_brain.memory:
                        ai_brain.memory.record_chat(old_author, old_message)

                    item = chat_queue.get_nowait()
                    chat_queue.task_done()
                    skipped_count += 1
                except queue.Empty:
                    break

            if skipped_count > 0:
                print(f"[CHAT QUEUE] Melewati {skipped_count} pesan lama, langsung merespons pesan terbaru!")

            author, message = item
            print(f"\n[AI DIPROSES] Merespons chat terbaru dari {author}: \"{message}\"")

            msg_clean = message.strip().lower()

            # Trigger animasi mini-game visual di layar avatar (Nomor 4: !pat, !permen, !spin, !topi)
            disp_obj = display_ref[0] if display_ref and display_ref[0] else None
            if disp_obj:
                disp_obj.wake_up()

            if disp_obj and msg_clean.startswith("!"):
                if any(k in msg_clean for k in ["!pat", "!elus", "!headpat", "!sayang"]):
                    disp_obj.trigger_headpat(author)
                elif any(k in msg_clean for k in ["!permen", "!kasihmakan", "!treat", "!makan"]):
                    disp_obj.trigger_treat(author)
                elif any(k in msg_clean for k in ["!spin", "!putarbadan"]):
                    disp_obj.trigger_spin(author)
                elif any(k in msg_clean for k in ["!hore", "!dance", "!menang", "!joget"]):
                    disp_obj.trigger_dance(author)
                elif any(k in msg_clean for k in ["!panik", "!kaget", "!shiver", "!takut"]):
                    disp_obj.trigger_panic(author)
                elif any(k in msg_clean for k in ["!boba", "!kopi", "!minum", "!teh", "!ngopi"]):
                    disp_obj.trigger_boba(author)
                elif any(k in msg_clean for k in ["!ngambek", "!marah", "!kesal", "!rage"]):
                    disp_obj.trigger_rage(author)
                elif any(k in msg_clean for k in ["!turu", "!tidur", "!ngantuk", "!sleep"]):
                    disp_obj.trigger_sleep(author)
                elif any(k in msg_clean for k in ["!bangun", "!wake"]):
                    disp_obj.wake_up()
                elif any(k in msg_clean for k in ["!tomat", "!lempar", "!sandal"]):
                    disp_obj.trigger_tomato(author)
                elif any(k in msg_clean for k in ["!topi", "!aksesoris", "!pakai", "!kostum", "!wardrobe"]):
                    # Cari kata aksesoris spesifik dalam perintah
                    for word in msg_clean.split():
                        cleaned_word = word.strip("!.,?")
                        if cleaned_word in [
                            "witch", "penyihir", "sihir", "ribbon", "pita", "pink",
                            "crown", "mahkota", "raja", "queen", "glasses", "kacamata",
                            "sunglasses", "flower", "bunga", "melati", "halo", "malaikat", "angel",
                            "tanduk", "setan", "iblis", "devil", "knight", "helm", "helmet", "ksatria",
                            "lepas", "copot", "buka", "none", "off"
                        ]:
                            disp_obj.set_accessory(cleaned_word)
                            break
                elif any(k in msg_clean for k in ["!lepas", "!copot"]):
                    disp_obj.remove_accessory()

            # Perintah khusus Coach Catur via Chat (!saran / !langkah / !coach / !bantu)
            if chess_coach and msg_clean.startswith("!"):
                if any(k in msg_clean for k in ["!saran", "!langkah", "!catur", "!coach", "!bestmove"]):
                    advice = chess_coach.get_on_demand_advice()
                    print(f"[VTUBER CHESS ADVICE]: {advice}")
                    _speak_tts(tts_engine, advice, interruptible=False)
                    last_activity_time = time.time()
                    continue
                elif any(k in msg_clean for k in ["!bantu", "!jalan"]):
                    if chess_coach.last_best_move and chess_coach.board_found:
                        assist_msg = f"Siap {author}! Ponyo bantu jalankan langkah terbaik {chess_coach.last_best_move} di papan!"
                        print(f"[VTUBER CHESS ASSIST]: {assist_msg}")
                        _speak_tts(tts_engine, assist_msg, interruptible=False)
                        time.sleep(0.25)
                        chess_coach.execute_auto_move(chess_coach.last_best_move)
                    else:
                        assist_msg = chess_coach.get_on_demand_advice()
                        print(f"[VTUBER CHESS ASSIST]: {assist_msg}")
                        _speak_tts(tts_engine, assist_msg, interruptible=False)
                    last_activity_time = time.time()
                    continue

            # Perintah khusus Pengaturan Kecepatan TTS via Chat (!speed / !kecepatan / !tempo)
            if msg_clean.startswith("!") and any(k in msg_clean.lower() for k in ["!speed", "!kecepatan", "!tempo"]):
                cmd_parts = msg_clean.lower().split()
                target_spd = None
                for part in cmd_parts:
                    p_clean = part.replace(",", ".").strip("!xX")
                    try:
                        v = float(p_clean)
                        if v in [0.0, 0.5, 1.0, 1.5, 2.0] or 0.0 <= v <= 2.5:
                            target_spd = v
                            break
                    except ValueError:
                        continue
                if target_spd is not None:
                    actual_spd = tts_engine.set_speed(target_spd)
                    if actual_spd == 0.0:
                        spd_reply = f"Mode hening aktif atas permintaan {author}! Ponyo sekarang berbicara tanpa suara ya!"
                    else:
                        spd_reply = f"Siap {author}! Kecepatan suara Ponyo diubah ke {actual_spd}x!"
                else:
                    spd_reply = f"Pilihan kecepatan suara Ponyo: 0.0x (hening), 0.5x (lambat), 1.0x (normal), 1.5x (cepat), dan 2.0x (sangat cepat)! Ketik '!speed <angka>' ya, {author}!"
                print(f"[VTUBER SPEED]: {spd_reply}")
                _speak_tts(tts_engine, spd_reply, interruptible=False)
                last_activity_time = time.time()
                continue

            # Perintah khusus Ganti Engine TTS via Chat (!tts / !engine)
            if msg_clean.startswith("!") and any(k in msg_clean.lower() for k in ["!tts", "!engine"]):
                cmd_low = msg_clean.lower()
                if any(w in cmd_low for w in ["local", "lokal", "offline", "piper"]):
                    tts_engine.set_engine("local")
                    eng_reply = f"Siap {author}! Ponyo sekarang menggunakan Text to Speech LOKAL 100% offline via Piper Neural TTS!"
                elif any(w in cmd_low for w in ["cloud", "edge", "online"]):
                    tts_engine.set_engine("cloud")
                    eng_reply = f"Siap {author}! Ponyo beralih ke suara Cloud Edge-TTS!"
                else:
                    curr = "LOKAL (100% Offline Piper)" if tts_engine.engine_type == "local" else "CLOUD (Edge-TTS)"
                    eng_reply = f"Saat ini Ponyo menggunakan Text to Speech {curr}. Ketik '!tts lokal' atau '!tts cloud' untuk mengganti ya, {author}!"
                print(f"[VTUBER ENGINE]: {eng_reply}")
                _speak_tts(tts_engine, eng_reply, interruptible=False)
                last_activity_time = time.time()
                continue

            # Eksekusi aksi fisik keyboard jika mode manual Slither aktif (chat usil menekan Spasi game)
            if manual_hook and message.strip().startswith("!"):
                manual_hook.handle_command(author, message)

            try:
                if tts_engine.is_muted:
                    # Di mode manual microphone (Human VTuber), bot tidak berbicara otomatis agar suara streamer bebas.
                    print(f"\n[LIVE CHAT (STREAMER READS)]: {author}: {message}")
                    last_activity_time = time.time()
                else:
                    reply = ai_brain.generate_reply(author, message)
                    print(f"[VTUBER RESPONS]: {reply}")
                    _speak_tts(tts_engine, reply, interruptible=False, priority=True)
                    runtime_metrics.increment("chat_speech")
                    last_activity_time = time.time()
                    time.sleep(0.3)
            except Exception as e:
                print(f"[WORKER ERROR] Gagal memproses chat: {e}")
            continue
        except queue.Empty:
            pass

        # 2. Cek event game dari Slither.io / Chess Bridge jika tidak ada chat penonton yang menunggu
        if bridge and not tts_engine.is_speaking and not tts_engine.is_muted:
            event = bridge.get_game_event(timeout=0.03)
            if event:
                ev_type = event.get("type")
                if ev_type == "CHESS_COACH":
                    c_msg = event.get("details", {}).get("message", "")
                    if c_msg:
                        print(f"\n[VTUBER CHESS COACH]: {c_msg}")
                        _speak_tts(tts_engine, c_msg, interruptible=False)
                        last_activity_time = time.time()
                        continue
                elif ev_type in GAME_REACTIONS:
                    if hasattr(ai_brain, "memory"):
                        ai_brain.memory.set_active_game("Slither.io")
                        ai_brain.memory.record_game_event(ev_type)
                    disp_obj = display_ref[0] if display_ref and display_ref[0] else None
                    if ev_type == "DEATH":
                        sfx_player.play("fail")
                    elif ev_type == "FEAST":
                        sfx_player.play("fanfare")
                        if disp_obj:
                            disp_obj.trigger_dance("Game FEAST")
                    elif ev_type in ("NEAR_MISS", "DEFENSIVE_COIL"):
                        if disp_obj:
                            disp_obj.trigger_panic("Game Panic")
                    reaction = random.choice(GAME_REACTIONS[ev_type])
                    print(f"\n[VTUBER GAME REAKSI - {ev_type}]: {reaction}")
                    _speak_tts(tts_engine, reaction, interruptible=True)
                    last_activity_time = time.time()
                    time.sleep(0.3)
                    continue

        # 3. Kuis Timeout: Jika kuis tebak-tebakan sudah berjalan terlalu lama tanpa jawaban
        if chat_quiz.is_active() and not tts_engine.is_speaking and not tts_engine.is_muted:
            quiz_timeout_msg = chat_quiz.check_timeout()
            if quiz_timeout_msg:
                print(f"\n[QUIZ TIMEOUT]: {quiz_timeout_msg}")
                _speak_tts(tts_engine, quiz_timeout_msg, interruptible=False)
                last_activity_time = time.time()
                continue

        # 4. AUTO-YAPPING dijalankan melalui lane khusus agar tidak memblokir chat.
        if commentator and commentator.is_enabled and not tts_engine.is_speaking and not tts_engine.is_muted and chat_queue.empty():
            silence_duration = time.time() - last_activity_time
            if silence_duration >= commentator.yap_interval:
                def deliver_yap(yap):
                    if yap:
                        print(f"\n[PONYO AUTO-YAPPING (Display 2)]: {yap}")
                        _speak_tts(tts_engine, yap, interruptible=True)
                if STREAM_WORKERS and STREAM_WORKERS.submit_result("yapping", commentator.generate_yap, deliver_yap):
                    last_activity_time = time.time()
                else:
                    deliver_yap(commentator.generate_yap())
                    last_activity_time = time.time()

        # 5. Pantau kesehatan Ollama dan metrik secara periodik tanpa mengirim payload chat.
        now = time.time()
        if int(now) % 30 == 0:
            ollama_health.check()
        if now - last_metrics_report >= 60.0:
            print(f"[RUNTIME METRICS] {runtime_metrics.snapshot()}")
            last_metrics_report = now

def main():
    global STREAM_WORKERS
    print_banner()

    # Worker terisolasi: chat, TTS, VLM, dan auto-yapping tidak berbagi antrean.
    STREAM_WORKERS = WorkerRuntime(maxsize=32, start=True)
    local_vlm.set_worker_runtime(STREAM_WORKERS)
    ollama_health.start(interval=30.0)

    # 1. Inisialisasi komponen
    ai_brain = AIBrain()
    tts_engine = TTSEngine()
    chat_queue = queue.Queue()
    stop_event = threading.Event()

    # Inisialisasi Chess Coach & Commentator
    chess_coach = ChessCoach(depth=CHESS_COACH_DEPTH, auto_play=CHESS_AUTO_PLAY)
    chess_coach.is_enabled = ENABLE_CHESS_COACH
    chess_coach.start()
    if chess_coach.is_enabled:
        print("[CHESS COACH] Aktif: Ponyo memantau papan catur & langsung memberi langkah terbaik saat giliranmu!")

    # Inisialisasi Screen Commentator (Auto-Yapping fokus pada layar yang sedang ditampilkan)
    commentator = ScreenCommentator(ai_brain, yap_interval=YAP_INTERVAL, chess_coach=chess_coach)
    commentator.is_enabled = ENABLE_AUTO_YAP
    if commentator.is_enabled:
        print(f"[YAP] Auto-Yapping Aktif: campuran komentar layar dan celotehan playful (peluang playful {YAP_PLAYFUL_CHANCE:.0%}) setiap {YAP_INTERVAL} detik keheningan.")

    # Inisialisasi Manual Slither Interactive Hook (Penonton chat memencet tombol Spasi game)
    manual_hook = ManualSlitherHook(boost_duration=MANUAL_BOOST_DURATION, cooldown=MANUAL_BOOST_COOLDOWN)
    manual_hook.is_enabled = ENABLE_MANUAL_SLITHER
    if manual_hook.is_enabled:
        print(f"[INTERAKTIF MANUAL] Aktif: Chat penonton (!boost) akan memencet tombol Spasi game selama {MANUAL_BOOST_DURATION}s.")

    # Inisialisasi Saweria Donation Webhook Receiver (Port 49225)
    saweria_receiver = None
    if SAWERIA_ENABLED:
        saweria_receiver = SaweriaReceiver(
            port=SAWERIA_PORT,
            stream_key=SAWERIA_STREAM_KEY,
            host=SAWERIA_HOST,
        )
        saweria_receiver.start()

    # 2. Inisialisasi listener chat YouTube / Terminal
    chat_listener = ChatListener(chat_queue, video_id=YOUTUBE_VIDEO_ID)
    chat_listener.start()

    # Referensi objek display untuk dipicu dari worker thread
    display_ref = [None]

    # 3. Jalankan worker chat pada lane khusus; TTS/VLM/yapping tetap terisolasi.
    STREAM_WORKERS.submit(
        "chat",
        chat_worker,
        chat_queue, ai_brain, tts_engine, stop_event,
        commentator, manual_hook, chess_coach, display_ref, saweria_receiver,
    )

    # Pemeriksaan awal Ollama memberi status nyata sebelum salam pembuka.
    print(f"[OLLAMA HEALTH] {ollama_health.check()}")

    # Ucapan salam pembuka
    def welcome_greeting():
        time.sleep(1.0)
        greeting = "Boo! Halo semuanya! Ponyo si hantu imut, selamat datang di live stream Ponyo hari ini!"
        print(f"[VTUBER GREETING]: {greeting}")
        _speak_tts(tts_engine, greeting)

    threading.Thread(target=welcome_greeting, daemon=True).start()

    # 4. Inisialisasi window display VTuber (Wajib berjalan di Main Thread)
    display = VTuberDisplay(
        tts_engine,
        commentator=commentator,
        manual_hook=manual_hook,
        chess_coach=chess_coach,
        ai_brain=ai_brain
    )
    display_ref[0] = display

    try:
        # Loop rendering visual avatar
        while display.running:
            if not display.run_frame():
                break
    except KeyboardInterrupt:
        print("\n[INFO] Menutup program via keyboard interrupt...")
    finally:
        print("[INFO] Membersihkan resource dan mematikan sistem...")
        stop_event.set()
        if STREAM_WORKERS:
            STREAM_WORKERS.stop()
            STREAM_WORKERS = None
        ollama_health.stop()
        if saweria_receiver:
            saweria_receiver.stop()
        chess_coach.stop()
        chat_listener.stop()
        display.close()

        # Eksekusi Evaluasi Pasca-Streaming (Modul A: Post-Stream Reflection)
        try:
            session_summary = ai_brain.memory.get_session_summary_data()
            stream_reflector.generate_post_stream_reflection(session_summary)
        except Exception as err:
            print(f"[REFLEKSI ERROR] Gagal membuat refleksi pasca-streaming: {err}")

        ai_brain.reset_memory()
        print("[INFO] Memori sementara sesi di-reset total.")
        print("[INFO] Bot VTuber berhasil dimatikan. Sampai jumpa!")
        sys.exit(0)

if __name__ == "__main__":
    main()

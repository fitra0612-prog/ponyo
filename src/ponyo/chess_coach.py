"""
PONYO CHESS COACH & COMMENTATOR (POWERED BY STOCKFISH 19)
=========================================================
Memantau papan catur di layar secara real-time, mendeteksi giliran pemain,
menghitung langkah terbaik menggunakan Stockfish 19, dan langsung memberikan
instruksi langkah terbaik serta komentar posisi dalam Bahasa Indonesia khas Ponyo.
"""

import os
import time
import random
import queue
import threading
import subprocess
import ctypes
from ctypes import wintypes
from PIL import ImageGrab
import chess

from .config import (
    ENABLE_CHESS_COACH,
    STOCKFISH_PATH,
    CHESS_COACH_DEPTH,
    CHESS_AUTO_PLAY
)

try:
    ctypes.windll.shcore.SetProcessDpiAwareness(2)
except Exception:
    pass

user32 = ctypes.windll.user32

# Geometri layar streaming (Display 2)
DISP2_BBOX = (1920, -1036, 3840, 44)
DISP2_OFFSET_X = 1920
DISP2_OFFSET_Y = -1036

PIECE_NAMES_ID = {
    chess.PAWN: "Pion",
    chess.KNIGHT: "Kuda",
    chess.BISHOP: "Gajah",
    chess.ROOK: "Benteng",
    chess.QUEEN: "Menteri",
    chess.KING: "Raja"
}


def is_background_pixel(r, g, b):
    # Dark square: green ~ (115, 149, 82)
    if abs(r - 115) < 25 and abs(g - 149) < 25 and abs(b - 82) < 25:
        return True
    # Light square: buff ~ (235, 236, 208)
    if abs(r - 235) < 20 and abs(g - 236) < 20 and abs(b - 208) < 20:
        return True
    # Dark square yellow highlight ~ (186, 202, 68)
    if abs(r - 186) < 25 and abs(g - 202) < 25 and abs(b - 68) < 25:
        return True
    # Light square yellow highlight ~ (245, 246, 130)
    if abs(r - 245) < 20 and abs(g - 246) < 20 and abs(b - 130) < 25:
        return True
    return False


def classify_piece_square(sq_img):
    w, h = sq_img.size
    pts = []
    white_pts = 0
    for y in range(h):
        for x in range(w):
            p = sq_img.getpixel((x, y))[:3]
            if not is_background_pixel(*p):
                pts.append((x, y))
                if p[0] > 220 and p[1] > 220 and p[2] > 220:
                    white_pts += 1

    area = len(pts)
    if area < 500:
        return '.'

    is_white = (white_pts > 500)

    if area < 3000:
        p_char = 'P'
    elif area >= 4600:
        cx = w // 2
        center_stem = sum(
            1 for y in range(10, min(25, h))
            if not is_background_pixel(*sq_img.getpixel((cx, y))[:3])
        )
        p_char = 'K' if center_stem >= 6 else 'Q'
    elif area >= 4200:
        p_char = 'N'
    else:
        y_probe = min(25, h - 1)
        pts_y25 = [
            x for x in range(w)
            if not is_background_pixel(*sq_img.getpixel((x, y_probe))[:3])
        ]
        width_y25 = max(pts_y25) - min(pts_y25) if pts_y25 else 0
        if width_y25 >= 38:
            p_char = 'R'
        else:
            p_char = 'B'

    return p_char if is_white else p_char.lower()


class ChessCoach:
    def __init__(self, stockfish_path=STOCKFISH_PATH, depth=CHESS_COACH_DEPTH, auto_play=CHESS_AUTO_PLAY):
        self.stockfish_path = stockfish_path
        self.depth = depth
        self.is_enabled = ENABLE_CHESS_COACH
        self.auto_play = auto_play

        # Geometri papan di dalam tangkapan layar
        self.board_x = 368
        self.board_y = 148
        self.board_w = 860
        self.board_h = 860
        self.sq_size = self.board_w / 8.0
        self.board_found = False

        # State permainan catur
        self.player_color = 'white'
        self.board = chess.Board()
        self.game_in_progress = False
        self.last_highlights = set()
        self.last_coached_piece_fen = ""
        self.last_best_move = None
        self.last_eval_score = "0.00"
        self.last_opponent_move_desc = ""
        self.last_game_over_announced = False

        # Antrean instruksi suara prioritas tinggi untuk Ponyo
        self.coach_queue = queue.Queue(maxsize=10)
        self._stop_event = threading.Event()
        self._thread = None
        self._sf_lock = threading.Lock()

    def start(self):
        if self._thread is None or not self._thread.is_alive():
            self._stop_event.clear()
            self._thread = threading.Thread(target=self._monitor_loop, daemon=True)
            self._thread.start()

    def stop(self):
        self._stop_event.set()

    def toggle_coach(self) -> bool:
        self.is_enabled = not self.is_enabled
        status = "AKTIF" if self.is_enabled else "NONAKTIF"
        print(f"[CHESS COACH] Mode Coach & Komentator Catur: {status}")
        if self.is_enabled:
            # Paksa evaluasi ulang posisi saat ini jika papan sedang terbuka
            self.last_coached_piece_fen = ""
        else:
            self.board_found = False
            self.game_in_progress = False
            while not self.coach_queue.empty():
                try:
                    self.coach_queue.get_nowait()
                except Exception:
                    break
        return self.is_enabled

    def is_chess_window_on_screen(self) -> bool:
        """Memastikan jendela paling depan (topmost) di layar streaming benar-benar menampilkan Catur"""
        top_titles = []

        def enum_proc(hwnd, lparam):
            if user32.IsWindowVisible(hwnd) and not user32.IsIconic(hwnd):
                rect = wintypes.RECT()
                user32.GetWindowRect(hwnd, ctypes.byref(rect))
                if rect.right > 1920 and rect.left < 3840 and rect.bottom > -1036 and rect.top < 44:
                    length = user32.GetWindowTextLengthW(hwnd)
                    if length > 0:
                        buf = ctypes.create_unicode_buffer(length + 1)
                        user32.GetWindowTextW(hwnd, buf, length + 1)
                        title = buf.value.strip()
                        ignored = [
                            'Program Manager', 'Windows Shell', 'Settings', 'Cua.',
                            'Taskbar', 'Tray', 'Default IME', 'MSCTFIME',
                            'Hermes', 'Ponyo Ghost Display', 'OBS', 'OBS Studio',
                            'Command Prompt', 'Windows PowerShell', 'cmd.exe'
                        ]
                        if title and not any(title.startswith(ig) or title == ig for ig in ignored):
                            w = rect.right - rect.left
                            h = rect.bottom - rect.top
                            if w > 400 and h > 300:
                                top_titles.append(title)
            return True

        WNDENUMPROC = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
        user32.EnumWindows(WNDENUMPROC(enum_proc), 0)
        if not top_titles:
            return False
        front_title = top_titles[0].lower()
        return any(k in front_title for k in ["chess", "catur", "lichess"])

    def toggle_auto_play(self) -> bool:
        self.auto_play = not self.auto_play
        status = "AKTIF (Ponyo Ikut Menggerakkan Bidak)" if self.auto_play else "NONAKTIF (Hanya Suara Coach)"
        print(f"[CHESS COACH] Auto-Play Bidak: {status}")
        return self.auto_play

    def get_coach_message(self):
        """Mengambil pesan instruksi langkah terbaik dan langkah auto-play jika ada.
        Mengembalikan tuple (coach_text, auto_move) atau (None, None).
        """
        try:
            item = None
            # Ambil instruksi paling baru jika ada beberapa yang menumpuk
            while not self.coach_queue.empty():
                item = self.coach_queue.get_nowait()
            if isinstance(item, tuple):
                return item
            elif isinstance(item, str):
                return (item, None)
            return (None, None)
        except Exception:
            return (None, None)

    def execute_auto_move(self, uci_move: str) -> bool:
        """Mengeksekusi langkah di layar setelah Ponyo selesai mengucapkan TTS sampai tuntas"""
        if not uci_move:
            return False
        if not self.is_chess_window_on_screen():
            print("[PONYO AUTO-PLAY] Jendela catur tidak aktif di depan layar, langkah dibatalkan.")
            return False

        print(f"[PONYO AUTO-PLAY] TTS tuntas! Memainkan langkah di layar: {uci_move}")
        if self.execute_move_on_screen(uci_move):
            try:
                self.board.push_uci(uci_move)
                self.last_coached_piece_fen = f"{self.board.fen().split()[0]}_{self.board.turn}"
                return True
            except Exception as e:
                print(f"[PONYO AUTO-PLAY] Error push board state: {e}")
        return False

    def capture_screen(self):
        try:
            return ImageGrab.grab(bbox=DISP2_BBOX, all_screens=True)
        except Exception:
            return None

    def find_board(self, img=None) -> bool:
        if img is None:
            img = self.capture_screen()
        if img is None:
            return False

        w, h = img.size
        dark_squares = []
        for y in range(0, h, 6):
            for x in range(0, w, 6):
                r, g, b = img.getpixel((x, y))[:3]
                if abs(r - 115) <= 6 and abs(g - 149) <= 6 and abs(b - 82) <= 6:
                    dark_squares.append((x, y))

        # Pastikan ukuran papan catur wajar (minimal 350x350 piksel)
        if len(dark_squares) < 120:
            self.board_found = False
            return False

        min_x = min(p[0] for p in dark_squares)
        max_x = max(p[0] for p in dark_squares)
        min_y = min(p[1] for p in dark_squares)
        max_y = max(p[1] for p in dark_squares)

        bw = max_x - min_x
        bh = max_y - min_y
        if bw < 350 or bh < 350 or abs(bw - bh) > 80:
            self.board_found = False
            return False

        self.board_x = min_x
        self.board_y = min_y
        self.board_w = bw
        self.board_h = bh
        self.sq_size = self.board_w / 8.0
        self.board_found = True
        return True

    def is_board_active(self, img) -> bool:
        if img is None or not self.board_found:
            return False
        cx_light = int(self.board_x + 4.5 * self.sq_size)
        cy_light = int(self.board_y + 4.5 * self.sq_size)
        if not (0 <= cx_light < img.width and 0 <= cy_light < img.height):
            return False
        p = img.getpixel((cx_light, cy_light))[:3]
        # Pastikan masih ada warna petak catur hijau di petak tetangga
        cx_dark = int(self.board_x + 3.5 * self.sq_size)
        cy_dark = int(self.board_y + 4.5 * self.sq_size)
        pd = img.getpixel((cx_dark, cy_dark))[:3]
        is_green_or_hl = (
            (abs(pd[0] - 115) < 30 and abs(pd[1] - 149) < 30 and abs(pd[2] - 82) < 30) or
            (abs(pd[0] - 186) < 30 and abs(pd[1] - 202) < 30 and abs(pd[2] - 68) < 30) or
            (pd[0] > 200 or pd[1] > 200 or pd[0] < 100)
        )
        return (p[0] > 180 and p[1] > 180) and is_green_or_hl

    def is_square_occupied(self, img, col, row) -> str:
        cx = int(self.board_x + (col + 0.5) * self.sq_size)
        cy = int(self.board_y + (row + 0.5) * self.sq_size)
        white_px = 0
        black_px = 0
        for dy in range(-15, 16, 3):
            for dx in range(-15, 16, 3):
                px = cx + dx
                py = cy + dy
                if 0 <= px < img.width and 0 <= py < img.height:
                    p = img.getpixel((px, py))[:3]
                    if p[0] > 245 and p[1] > 245 and p[2] > 245:
                        white_px += 1
                    elif p[0] < 115 and p[1] < 115 and p[2] < 115 and max(p) - min(p) < 15:
                        black_px += 1
        if white_px > 15:
            return 'W'
        elif black_px > 15:
            return 'B'
        return '.'

    def square_name_to_col_row(self, sq_name: str):
        f = sq_name[0]
        r = sq_name[1]
        if self.player_color == 'white':
            col = ord(f) - ord('a')
            row = 8 - int(r)
        else:
            col = ord('h') - ord(f)
            row = int(r) - 1
        return col, row

    def is_square_name_occupied(self, img, sq_name: str) -> str:
        col, row = self.square_name_to_col_row(sq_name)
        return self.is_square_occupied(img, col, row)

    def detect_color_from_board(self, img) -> str:
        bot_w = sum(
            1 for col in range(8)
            if self.is_square_occupied(img, col, 7) == 'W' or self.is_square_occupied(img, col, 6) == 'W'
        )
        bot_b = sum(
            1 for col in range(8)
            if self.is_square_occupied(img, col, 7) == 'B' or self.is_square_occupied(img, col, 6) == 'B'
        )
        top_w = sum(
            1 for col in range(8)
            if self.is_square_occupied(img, col, 0) == 'W' or self.is_square_occupied(img, col, 1) == 'W'
        )
        top_b = sum(
            1 for col in range(8)
            if self.is_square_occupied(img, col, 0) == 'B' or self.is_square_occupied(img, col, 1) == 'B'
        )
        if bot_b > bot_w or top_w > top_b:
            return 'black'
        return 'white'

    def is_starting_position(self, img) -> bool:
        if not self.is_board_active(img):
            return False
        for row in [2, 3, 4, 5]:
            for col in range(8):
                if self.is_square_occupied(img, col, row) != '.':
                    return False
        row0_pieces = sum(1 for col in range(8) if self.is_square_occupied(img, col, 0) != '.')
        row7_pieces = sum(1 for col in range(8) if self.is_square_occupied(img, col, 7) != '.')
        return row0_pieces >= 7 and row7_pieces >= 7

    def detect_highlights(self, img) -> set:
        highlights = set()
        for row in range(8):
            for col in range(8):
                if self.player_color == 'white':
                    f = chr(ord('a') + col)
                    r = str(8 - row)
                else:
                    f = chr(ord('h') - col)
                    r = str(row + 1)

                cx1 = int(self.board_x + (col + 0.82) * self.sq_size)
                cy1 = int(self.board_y + (row + 0.18) * self.sq_size)
                cx2 = int(self.board_x + (col + 0.18) * self.sq_size)
                cy2 = int(self.board_y + (row + 0.18) * self.sq_size)

                for cx, cy in [(cx1, cy1), (cx2, cy2)]:
                    if 0 <= cx < img.width and 0 <= cy < img.height:
                        rgb = img.getpixel((cx, cy))[:3]
                        if (rgb[0] > 215 and rgb[1] > 215 and 90 < rgb[2] < 160) or \
                           (160 < rgb[0] < 215 and 170 < rgb[1] < 235 and 45 < rgb[2] < 95):
                            highlights.add(f + r)
                            break
        return highlights

    def scan_board_from_vision(self, img):
        """Memindai 64 petak catur secara langsung dari gambar layar dan merekonstruksi objek chess.Board"""
        t0 = time.time()
        board_chars = []
        for row in range(8):
            row_chars = []
            for col in range(8):
                x1 = int(self.board_x + col * self.sq_size)
                y1 = int(self.board_y + row * self.sq_size)
                x2 = int(self.board_x + (col + 1) * self.sq_size)
                y2 = int(self.board_y + (row + 1) * self.sq_size)
                sq_im = img.crop((x1, y1, x2, y2))
                row_chars.append(classify_piece_square(sq_im))
            board_chars.append(row_chars)

        fen_ranks = []
        if self.player_color == 'white':
            for row in board_chars:
                empty = 0
                rank_str = ""
                for ch in row:
                    if ch == '.':
                        empty += 1
                    else:
                        if empty > 0:
                            rank_str += str(empty)
                            empty = 0
                        rank_str += ch
                if empty > 0:
                    rank_str += str(empty)
                fen_ranks.append(rank_str)
        else:
            for r_idx in range(7, -1, -1):
                row = board_chars[r_idx][::-1]
                empty = 0
                rank_str = ""
                for ch in row:
                    if ch == '.':
                        empty += 1
                    else:
                        if empty > 0:
                            rank_str += str(empty)
                            empty = 0
                        rank_str += ch
                if empty > 0:
                    rank_str += str(empty)
                fen_ranks.append(rank_str)

        board_fen = "/".join(fen_ranks)
        hl = self.detect_highlights(img)
        self.last_highlights = hl

        dummy_w = chess.Board(f"{board_fen} w - - 0 1")
        castling_rights = ""
        if dummy_w.piece_at(chess.E1) == chess.Piece(chess.KING, chess.WHITE):
            if dummy_w.piece_at(chess.H1) == chess.Piece(chess.ROOK, chess.WHITE):
                castling_rights += "K"
            if dummy_w.piece_at(chess.A1) == chess.Piece(chess.ROOK, chess.WHITE):
                castling_rights += "Q"
        if dummy_w.piece_at(chess.E8) == chess.Piece(chess.KING, chess.BLACK):
            if dummy_w.piece_at(chess.H8) == chess.Piece(chess.ROOK, chess.BLACK):
                castling_rights += "k"
            if dummy_w.piece_at(chess.A8) == chess.Piece(chess.ROOK, chess.BLACK):
                castling_rights += "q"
        if not castling_rights:
            castling_rights = "-"

        # Tentukan giliran siapa dari bidak yang berdiri di atas petak highlight terakhir
        active_turn = 'w'
        turn_reason = "Giliran Putih (Awal)"
        for sq_name in hl:
            sq_idx = chess.parse_square(sq_name)
            p = dummy_w.piece_at(sq_idx)
            if p is not None:
                if p.color == chess.WHITE:
                    active_turn = 'b'
                    piece_id = PIECE_NAMES_ID.get(p.piece_type, "bidak")
                    turn_reason = f"Putih baru saja menggerakkan {piece_id} ke {sq_name}"
                else:
                    active_turn = 'w'
                    piece_id = PIECE_NAMES_ID.get(p.piece_type, "bidak")
                    turn_reason = f"Hitam baru saja menggerakkan {piece_id} ke {sq_name}"
                break

        full_fen = f"{board_fen} {active_turn} {castling_rights} - 0 10"
        try:
            parsed_board = chess.Board(full_fen)
        except Exception:
            parsed_board = chess.Board(f"{board_fen} {active_turn} - - 0 10")

        elapsed = time.time() - t0
        return parsed_board, elapsed, turn_reason

    def describe_move_short(self, board: chess.Board, move: chess.Move) -> str:
        """Deskripsi singkat langkah lawan (contoh: 'Kuda ke f6' atau 'Pion makan d4')"""
        piece = board.piece_at(move.from_square)
        piece_name = PIECE_NAMES_ID.get(piece.piece_type, "bidak") if piece else "bidak"
        dst = chess.square_name(move.to_square)

        if board.is_castling(move):
            return "rokade"
        if board.is_capture(move):
            if board.is_en_passant(move):
                cap_name = "Pion"
            else:
                cap_p = board.piece_at(move.to_square)
                cap_name = PIECE_NAMES_ID.get(cap_p.piece_type, "bidak") if cap_p else "bidak"
            return f"{piece_name} makan {cap_name} di {dst}"
        return f"{piece_name} ke {dst}"

    def format_coach_instruction(self, board: chess.Board, uci_move: str, eval_score: str, prefix_context: str = "") -> str:
        """Mengubah langkah UCI Stockfish menjadi kalimat instruksi Coach Ponyo dalam Bahasa Indonesia"""
        if not uci_move:
            return ""
        try:
            move = chess.Move.from_uci(uci_move)
        except Exception:
            return f"Langkah terbaik menurut Ponyo adalah {uci_move}!"

        piece = board.piece_at(move.from_square)
        piece_name = PIECE_NAMES_ID.get(piece.piece_type, "bidak") if piece else "bidak"
        src = chess.square_name(move.from_square)
        dst = chess.square_name(move.to_square)

        # 1. Susun instruksi inti langkah
        if board.is_castling(move):
            if board.is_kingside_castling(move):
                action = f"lakukan rokade pendek, geser Raja dari {src} ke {dst}"
            else:
                action = f"lakukan rokade panjang, geser Raja dari {src} ke {dst}"
        elif board.is_capture(move):
            if board.is_en_passant(move):
                cap_name = "Pion"
            else:
                cap_p = board.piece_at(move.to_square)
                cap_name = PIECE_NAMES_ID.get(cap_p.piece_type, "bidak lawan") if cap_p else "bidak lawan"
            action = f"gerakkan {piece_name} dari {src} makan {cap_name} di {dst}"
        else:
            verb = "majukan" if piece and piece.piece_type == chess.PAWN else "gerakkan"
            action = f"{verb} {piece_name} dari {src} ke {dst}"

        if move.promotion:
            promo_name = PIECE_NAMES_ID.get(move.promotion, "Menteri")
            action += f" lalu promosi jadi {promo_name}"

        # Cek apakah langkah ini menghasilkan skak atau skakmat
        b_copy = board.copy()
        try:
            b_copy.push(move)
            if b_copy.is_checkmate():
                action += ", langsung skakmat"
            elif b_copy.is_check():
                action += ", skak"
        except Exception:
            pass

        # 2. Susun konteks pembuka
        in_check = board.is_check()
        if in_check:
            intro = "Awas Raja kamu sedang disekak! "
        elif prefix_context:
            intro = f"{prefix_context} "
        else:
            intro = "Giliran kamu! "

        # 3. Tambahan komentar evaluasi singkat
        eval_suffix = ""
        if eval_score.startswith("M"):
            mate_val = eval_score[1:]
            if not mate_val.startswith("-") and mate_val != "1":
                eval_suffix = f" Ada skakmat dalam {mate_val} langkah!"
        else:
            try:
                val = float(eval_score)
                if val >= 3.0:
                    eval_suffix = " Posisi kamu unggul telak!"
                elif val >= 1.2:
                    eval_suffix = " Posisi kamu lagi unggul nih!"
                elif val <= -2.5 and not in_check:
                    eval_suffix = " Tetap fokus bertahan ya!"
            except Exception:
                pass

        return f"{intro}Langkah terbaik menurut Ponyo, {action}!{eval_suffix}"

    def get_stockfish_move(self, fen: str = None, depth: int = None):
        """Menjalankan kalkulasi langkah terbaik dengan Stockfish 19"""
        if not os.path.exists(self.stockfish_path):
            print(f"[CHESS COACH ERROR] File Stockfish tidak ditemukan di {self.stockfish_path}")
            return None, "0.00"

        target_fen = fen or self.board.fen()
        target_depth = depth or self.depth

        with self._sf_lock:
            try:
                p = subprocess.Popen(
                    [self.stockfish_path],
                    stdin=subprocess.PIPE,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    encoding="utf-8",
                    errors="ignore",
                    creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
                )
                p.stdin.write("uci\n")
                p.stdin.write("isready\n")
                p.stdin.write(f"position fen {target_fen}\n")
                p.stdin.write(f"go depth {target_depth}\n")
                p.stdin.flush()

                best_move = None
                eval_score = "0.00"
                t_start = time.time()
                while time.time() - t_start < 6.0:
                    line = p.stdout.readline()
                    if not line:
                        break
                    line_str = line.strip()
                    if "score cp" in line_str:
                        parts = line_str.split()
                        if "cp" in parts:
                            cp = int(parts[parts.index("cp") + 1])
                            eval_score = f"{cp / 100.0:+.2f}"
                    elif "score mate" in line_str:
                        parts = line_str.split()
                        if "mate" in parts:
                            mate = parts[parts.index("mate") + 1]
                            eval_score = f"M{mate}"
                    if line_str.startswith("bestmove"):
                        best_move = line_str.split()[1]
                        break

                try:
                    p.stdin.write("quit\n")
                    p.stdin.flush()
                    p.terminate()
                except Exception:
                    pass

                if best_move == "(none)":
                    best_move = None
                return best_move, eval_score
            except Exception as e:
                print(f"[CHESS COACH ERROR] Gagal memanggil Stockfish: {e}")
                return None, "0.00"

    def try_detect_board_move(self, img) -> tuple:
        """
        Mendeteksi langkah yang baru saja terjadi di papan (baik langkah pemain maupun lawan).
        Mengembalikan (detected: bool, move_obj_or_None, move_desc: str)
        """
        hl = self.detect_highlights(img)
        if len(hl) < 2 or hl == self.last_highlights:
            return False, None, ""

        # Tunggu sejenak (90ms) untuk memastikan animasi geser bidak selesai di layar
        time.sleep(0.09)
        img = self.capture_screen()
        if img is None:
            return False, None, ""
        hl = self.detect_highlights(img)
        if len(hl) < 2:
            return False, None, ""

        moving_color_code = 'W' if self.board.turn == chess.WHITE else 'B'

        # 1. Coba cocokkan 1 langkah legal pada giliran saat ini
        for m in self.board.legal_moves:
            src = chess.square_name(m.from_square)
            dst = chess.square_name(m.to_square)
            if {src, dst}.issubset(hl):
                # Verifikasi visual: petak asal sekarang kosong dan petak tujuan berisi bidak warna yang jalan
                if self.is_square_name_occupied(img, src) == '.' and self.is_square_name_occupied(img, dst) == moving_color_code:
                    picked = m
                    for alt in self.board.legal_moves:
                        if {chess.square_name(alt.from_square), chess.square_name(alt.to_square)}.issubset(hl) and alt.promotion == chess.QUEEN:
                            picked = alt
                    desc = self.describe_move_short(self.board, picked)
                    mover_side = "WHITE" if self.board.turn == chess.WHITE else "BLACK"
                    print(f"[CHESS COACH] Langkah terdeteksi ({mover_side}): {picked.uci()} ({desc})")
                    self.board.push(picked)
                    self.last_highlights = hl
                    return True, picked, desc

        # 2. Coba cocokkan skenario 2-ply cepat (Pemain melangkah lalu Lawan langsung premove/membalas cepat)
        opp_color_code = 'B' if moving_color_code == 'W' else 'W'
        for m1 in self.board.legal_moves:
            src1 = chess.square_name(m1.from_square)
            if self.is_square_name_occupied(img, src1) == '.':
                b_copy = self.board.copy()
                b_copy.push(m1)
                for m2 in b_copy.legal_moves:
                    src2 = chess.square_name(m2.from_square)
                    dst2 = chess.square_name(m2.to_square)
                    if {src2, dst2}.issubset(hl):
                        if self.is_square_name_occupied(img, src2) == '.' and self.is_square_name_occupied(img, dst2) == opp_color_code:
                            desc2 = self.describe_move_short(b_copy, m2)
                            print(f"[CHESS COACH] 2 Langkah cepat terdeteksi: {m1.uci()} lalu dibalas {m2.uci()} ({desc2})")
                            self.board.push(m1)
                            self.board.push(m2)
                            self.last_highlights = hl
                            return True, m2, desc2

        return False, None, ""

    def get_square_coords(self, square_str):
        col, row = self.square_name_to_col_row(square_str)
        img_x = self.board_x + (col + 0.5) * self.sq_size + random.randint(-5, 5)
        img_y = self.board_y + (row + 0.5) * self.sq_size + random.randint(-5, 5)
        return int(DISP2_OFFSET_X + img_x), int(DISP2_OFFSET_Y + img_y)

    def execute_move_on_screen(self, uci_move: str) -> bool:
        """Menggerakkan bidak secara fisik di layar jika Auto-Play atau perintah !bantu diaktifkan"""
        if not uci_move or not self.board_found:
            return False
        src = uci_move[:2]
        dst = uci_move[2:4]
        sx1, sy1 = self.get_square_coords(src)
        sx2, sy2 = self.get_square_coords(dst)

        # Fokus ke jendela browser catur
        pt = wintypes.POINT(int(DISP2_OFFSET_X + self.board_x + 200), int(DISP2_OFFSET_Y + self.board_y + 200))
        hwnd = user32.WindowFromPoint(pt)
        root = user32.GetAncestor(hwnd, 2)
        if root and user32.GetForegroundWindow() != root:
            user32.SetForegroundWindow(root)
            time.sleep(0.05)

        user32.SetCursorPos(sx1, sy1)
        time.sleep(0.04)
        user32.mouse_event(0x0002, 0, 0, 0, 0)
        time.sleep(0.04)
        user32.mouse_event(0x0004, 0, 0, 0, 0)
        time.sleep(0.06)

        user32.SetCursorPos(sx2, sy2)
        time.sleep(0.04)
        user32.mouse_event(0x0002, 0, 0, 0, 0)
        time.sleep(0.04)
        user32.mouse_event(0x0004, 0, 0, 0, 0)
        time.sleep(0.10)

        if len(uci_move) > 4 and uci_move[4] == 'q':
            time.sleep(0.10)
            user32.SetCursorPos(sx2, sy2)
            user32.mouse_event(0x0002, 0, 0, 0, 0)
            time.sleep(0.03)
            user32.mouse_event(0x0004, 0, 0, 0, 0)

        return True

    def get_on_demand_advice(self) -> str:
        """Dipanggil saat pemain/penonton mengetik !saran, !langkah, atau bertanya langkah catur"""
        img = self.capture_screen()
        if img is None:
            return "Ponyo belum melihat papan catur di layar Ponyo nih. Buka dulu papan caturnya ya!"

        if not self.board_found or not self.is_board_active(img):
            if not self.find_board(img):
                return "Ponyo belum menemukan papan catur yang aktif di layar Ponyo. Pastikan papan caturnya terlihat jelas ya!"

        self.player_color = self.detect_color_from_board(img)
        if self.is_starting_position(img):
            self.board = chess.Board()
        else:
            scanned, _, _ = self.scan_board_from_vision(img)
            self.board = scanned

        my_color = chess.WHITE if self.player_color == 'white' else chess.BLACK
        warna_id = "Putih" if my_color == chess.WHITE else "Hitam"

        if self.board.is_game_over():
            return "Pertandingan catur di papan saat ini sudah selesai! Yuk mulai pertandingan baru bareng Ponyo!"

        if self.board.turn != my_color:
            best_opp, score = self.get_stockfish_move(depth=12)
            return f"Sekarang sedang giliran lawan melangkah! Kamu pegang bidak {warna_id}, tunggu lawan jalan dulu nanti Ponyo langsung kasih tahu langkah terbaiknya ya!"

        best_move, score = self.get_stockfish_move(depth=self.depth)
        if not best_move:
            return "Ponyo sedang mengamati posisi papan, ayo fokus!"
        self.last_best_move = best_move
        self.last_eval_score = score
        return self.format_coach_instruction(self.board, best_move, score)

    def get_live_board_summary(self) -> str:
        """Mengambil ringkasan posisi nyata papan catur di layar saat ini untuk bahan komentar layar (yapping)"""
        img = self.capture_screen()
        if img is None:
            return ""
        if not self.board_found or not self.is_board_active(img):
            if not self.find_board(img) or not self.is_board_active(img):
                return ""
            self.player_color = self.detect_color_from_board(img)
            if self.is_starting_position(img):
                self.board = chess.Board()
                reason = "Posisi awal pertandingan"
            else:
                self.board, _, reason = self.scan_board_from_vision(img)
        else:
            if self.is_starting_position(img):
                reason = "Posisi awal pertandingan"
            else:
                _, _, reason = self.scan_board_from_vision(img)

        warna_id = "Putih" if self.player_color == 'white' else "Hitam"
        my_color = chess.WHITE if self.player_color == 'white' else chess.BLACK
        turn_str = "giliran kita melangkah" if self.board.turn == my_color else "sedang menunggu lawan melangkah"
        return f"Kita memegang bidak {warna_id}. Status di papan: {reason}, saat ini {turn_str}."

    def generate_accurate_board_yap(self, cycle: int = 0) -> str:
        """
        Menghasilkan komentar yapping Bahasa Indonesia yang 100% akurat sesuai posisi nyata
        bidak di papan catur layar saat ini (tanpa halusinasi petak atau menyebut engine).
        """
        img = self.capture_screen()
        if img is None:
            return ""
        if not self.board_found or not self.is_board_active(img):
            if not self.find_board(img) or not self.is_board_active(img):
                return ""

        self.player_color = self.detect_color_from_board(img)
        if self.is_starting_position(img):
            b = chess.Board()
            reason = "Posisi awal pertandingan"
        else:
            b, _, reason = self.scan_board_from_vision(img)
            self.board = b

        my_color = chess.WHITE if self.player_color == 'white' else chess.BLACK
        opp_color = not my_color
        warna_id = "Putih" if my_color == chess.WHITE else "Hitam"

        # Hitung perwira aktif kita yang sudah keluar dari baris awal
        active_pieces = []
        home_rank = 0 if my_color == chess.WHITE else 7
        for sq in chess.SQUARES:
            p = b.piece_at(sq)
            if p and p.color == my_color and p.piece_type in [chess.KNIGHT, chess.BISHOP, chess.QUEEN]:
                if chess.square_rank(sq) != home_rank:
                    p_name = PIECE_NAMES_ID.get(p.piece_type, "Bidak")
                    active_pieces.append(f"{p_name} di {chess.square_name(sq)}")

        # Hitung selisih materi di papan
        vals = {chess.PAWN: 1, chess.KNIGHT: 3, chess.BISHOP: 3, chess.ROOK: 5, chess.QUEEN: 9}
        my_mat = sum(len(b.pieces(pt, my_color)) * val for pt, val in vals.items())
        opp_mat = sum(len(b.pieces(pt, opp_color)) * val for pt, val in vals.items())
        mat_diff = my_mat - opp_mat

        mode = cycle % 4
        if mode == 0:
            # Sudut pandang 1: Status giliran & langkah terakhir di papan
            if b.turn == my_color:
                best_m, sc = self.get_stockfish_move(fen=b.fen(), depth=12)
                if best_m:
                    return self.format_coach_instruction(b, best_m, sc, prefix_context=f"Di papan sekarang giliran {warna_id} jalan!")
            return f"Di papan catur sekarang kita pegang bidak {warna_id}. {reason}, sekarang Ponyo lagi fokus tunggu langkah balasan lawan nih!"

        elif mode == 1:
            # Sudut pandang 2: Perwira yang aktif di papan nyata
            if len(active_pieces) >= 2:
                return f"Lihat posisi di papan, {active_pieces[0]} dan {active_pieces[1]} kita sudah aktif mengawal area tengah. Susunan bidak Ponyo kelihatan solid banget!"
            elif len(active_pieces) == 1:
                return f"Di papan saat ini {active_pieces[0]} kita sudah maju membuka jalan. Yuk keluarkan perwira lainnya supaya serangan kita makin kuat!"
            else:
                return "Pertandingan baru dimulai di papan! Yuk kita kuasai petak tengah pakai Pion dan keluarkan Kuda serta Gajah kita!"

        elif mode == 2:
            # Sudut pandang 3: Keseimbangan materi bidak di papan
            if mat_diff >= 2:
                return f"Mantap banget, kalau dilihat di papan sekarang jumlah bidak {warna_id} kita lagi unggul atas lawan! Pertahankan posisi ini sampai skakmat ya!"
            elif mat_diff <= -2:
                return "Walaupun kita sempat kehilangan bidak di papan, jangan panik ya! Ponyo bantu cari celah taktik buat membalikkan keadaan!"
            else:
                return "Pertarungan di papan catur masih sengit dan imbang nih! Belum ada yang blunder, jadi perhatikan setiap langkah lawan baik-baik ya!"

        else:
            # Sudut pandang 4: Keamanan Raja di papan
            king_sq = b.king(my_color)
            if king_sq is not None:
                k_name = chess.square_name(king_sq)
                if k_name in ["g1", "c1", "g8", "c8"]:
                    return f"Raja {warna_id} kita di petak {k_name} sudah aman setelah rokade. Sekarang Ponyo bisa fokus bantu kamu menyusun serangan ke pertahanan lawan!"
                else:
                    return f"Raja {warna_id} kita masih berada di petak {k_name} nih. Nanti kalau jalur sudah terbuka, jangan lupa amankan Raja dengan rokade ya!"
            return "Ponyo terus pantau setiap pergerakan bidak di papan catur ini, ayo kita mainkan langkah paling akurat!"

    def _emit_coach_speech(self, text: str, auto_move: str = None):
        if not text:
            return
        try:
            while not self.coach_queue.empty():
                self.coach_queue.get_nowait()
            self.coach_queue.put_nowait((text, auto_move))
        except Exception:
            pass

    def _monitor_loop(self):
        """Loop pemantau papan catur secara real-time di background"""
        last_find_attempt = 0.0
        last_resync_check = time.time()

        while not self._stop_event.is_set():
            if not self.is_enabled:
                time.sleep(0.5)
                continue

            # Pastikan layar benar-benar sedang menampilkan jendela Catur di posisi paling depan
            if not self.is_chess_window_on_screen():
                if self.board_found or self.game_in_progress:
                    self.board_found = False
                    self.game_in_progress = False
                    while not self.coach_queue.empty():
                        try:
                            self.coach_queue.get_nowait()
                        except Exception:
                            break
                time.sleep(0.8)
                continue

            img = self.capture_screen()
            if img is None:
                time.sleep(0.5)
                continue

            # 1. Jika papan belum terkunci, cari papan catur setiap 2 detik
            if not self.board_found or not self.is_board_active(img):
                if time.time() - last_find_attempt >= 2.0:
                    last_find_attempt = time.time()
                    if self.find_board(img) and self.is_board_active(img):
                        self.player_color = self.detect_color_from_board(img)
                        warna_id = "Putih" if self.player_color == 'white' else "Hitam"
                        print(f"\n[CHESS COACH] Papan catur terdeteksi! Kamu bermain sebagai: {warna_id.upper()}")

                        if self.is_starting_position(img):
                            self.board = chess.Board()
                            self.last_highlights = set()
                            self.game_in_progress = True
                            self.last_coached_piece_fen = ""
                            self.last_opponent_move_desc = ""
                        else:
                            scanned_b, scan_t, reason = self.scan_board_from_vision(img)
                            self.board = scanned_b
                            self.game_in_progress = True
                            self.last_coached_piece_fen = ""
                            self.last_opponent_move_desc = ""
                            print(f"[CHESS COACH] Sinkronisasi posisi tengah permainan ({scan_t:.2f}s): {reason}")
                else:
                    time.sleep(0.4)
                    continue

            # 2. Cek apakah pertandingan baru saja dimulai ulang (Starting Position)
            if self.is_starting_position(img):
                if not self.game_in_progress or len(self.board.move_stack) > 1 or self.board.fen().split()[0] != chess.STARTING_BOARD_FEN:
                    self.player_color = self.detect_color_from_board(img)
                    self.board = chess.Board()
                    self.last_highlights = set()
                    self.game_in_progress = True
                    self.last_coached_piece_fen = ""
                    self.last_opponent_move_desc = ""
                    self.last_game_over_announced = False
                    warna_id = "Putih" if self.player_color == 'white' else "Hitam"
                    print(f"\n[CHESS COACH] Pertandingan baru dimulai! Kamu memegang bidak {warna_id.upper()}.")
                    if self.player_color == 'black':
                        self._emit_coach_speech(
                            "Pertandingan catur baru dimulai, kamu memegang bidak Hitam! Kita tunggu langkah pertama lawan dulu ya!"
                        )

            if not self.game_in_progress:
                time.sleep(0.25)
                continue

            my_color = chess.WHITE if self.player_color == 'white' else chess.BLACK

            # 3. Deteksi langkah baru di papan dari perubahan highlight kuning
            moved, move_obj, move_desc = self.try_detect_board_move(img)
            if moved:
                last_resync_check = time.time()
                # Jika yang baru saja melangkah adalah lawan, maka sekarang giliran pemain!
                if self.board.turn == my_color:
                    self.last_opponent_move_desc = f"Lawan jalan {move_desc}."
                else:
                    self.last_opponent_move_desc = ""
            else:
                # Cek apakah ada perubahan highlight yang tidak cocok dengan langkah legal (misal lompatan posisi/resync)
                current_hl = self.detect_highlights(img)
                hl_unmatched = (len(current_hl) >= 2 and current_hl != self.last_highlights)
                periodic_resync = (time.time() - last_resync_check > 1.8)

                if hl_unmatched or periodic_resync:
                    last_resync_check = time.time()
                    scanned_b, _, reason = self.scan_board_from_vision(img)
                    old_piece_fen = self.board.fen().split()[0]
                    new_piece_fen = scanned_b.fen().split()[0]
                    if new_piece_fen != old_piece_fen or scanned_b.turn != self.board.turn:
                        print(f"[CHESS COACH] Sinkronisasi otomatis papan: {reason}")
                        self.board = scanned_b
                        if reason.startswith("Putih baru") or reason.startswith("Hitam baru"):
                            self.last_opponent_move_desc = ""

            # 4. Cek apakah permainan sudah berakhir (Checkmate / Stalemate)
            if self.board.is_game_over():
                if not self.last_game_over_announced:
                    self.last_game_over_announced = True
                    if self.board.is_checkmate():
                        winner = "Hitam" if self.board.turn == chess.WHITE else "Putih"
                        my_warna = "Putih" if my_color == chess.WHITE else "Hitam"
                        if winner == my_warna:
                            self._emit_coach_speech("Skakmat! Wah hebat banget, kita menang pertandingan catur ini! GG banget!")
                        else:
                            self._emit_coach_speech("Yah skakmat! Tidak apa-apa, pertandingan tadi seru banget. Yuk kita balas di ronde berikutnya!")
                    else:
                        self._emit_coach_speech("Pertandingan berakhir remis! Permainan yang sangat sengit!")
                time.sleep(0.3)
                continue

            # 5. SAAT GILIRAN PEMAIN BERMAIN -> LANGSUNG BERIKAN LANGKAH TERBAIK!
            current_piece_fen = f"{self.board.fen().split()[0]}_{self.board.turn}"
            if self.board.turn == my_color and current_piece_fen != self.last_coached_piece_fen:
                self.last_coached_piece_fen = current_piece_fen
                best_move, eval_score = self.get_stockfish_move(depth=self.depth)
                if best_move:
                    self.last_best_move = best_move
                    self.last_eval_score = eval_score

                    prefix = self.last_opponent_move_desc
                    if len(self.board.move_stack) == 0 and self.board.fen().split()[0] == chess.STARTING_BOARD_FEN:
                        prefix = "Pertandingan dimulai, kamu pegang Putih!"

                    coach_text = self.format_coach_instruction(
                        self.board,
                        best_move,
                        eval_score,
                        prefix_context=prefix
                    )
                    print(f"\n[PONYO CHESS COACH] ({best_move} | Eval {eval_score}): {coach_text}")
                    # Kirim instruksi suara ke antrean berserta target langkah.
                    # Langkah fisik di layar akan dieksekusi di main.py SETELAH Ponyo tuntas mengucapkan TTS!
                    auto_move_target = best_move if self.auto_play else None
                    self._emit_coach_speech(coach_text, auto_move=auto_move_target)

            time.sleep(0.12)

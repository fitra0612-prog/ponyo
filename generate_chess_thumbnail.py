"""
YOUTUBE THUMBNAIL GENERATOR: BELAJAR CHESS BERSAMA PONYO
=========================================================
Menghasilkan thumbnail YouTube berkualitas tinggi 1280x720 (16:9)
dengan komposisi visual ala streamer catur profesional & VTuber anime:
- Karakter Ponyo si Hantu Imut mengenakan Mahkota Emas Kerajaan (Queen/King of Chess)
- Papan catur 3D bersudut dramatis dengan panah analisis taktik (Chess.com style)
- Bidak Catur Pixel Art (Kuda Knight, Benteng Rook, Raja King, Pion)
- Tipografi bold YouTube berdampak tinggi (Impact / Arial Black)
- Badge LIVE STREAM, ELO RATING, dan HOOK BANNER "DARI PEMULA JADI PRO!"
"""

import os
import math
import random
from PIL import Image, ImageDraw, ImageFont, ImageFilter

OUTPUT_DIR = os.path.abspath("C:/Users/admin/Documents/Project/VTUBER")
OUTPUT_PATH = os.path.join(OUTPUT_DIR, "thumbnail_belajar_chess_ponyo.png")
AVATARS_DIR = os.path.join(OUTPUT_DIR, "avatars")

W, H = 1280, 720


def draw_pixel_pawn_icon(draw, x, y, size=18, color=(255, 255, 255, 255)):
    """Menggambar ikon Pion Catur pixel art kecil untuk pill"""
    draw.ellipse([x + 5, y, x + 13, y + 8], fill=color)
    draw.rectangle([x + 6, y + 8, x + 12, y + 10], fill=color)
    draw.polygon([(x + 9, y + 10), (x + 3, y + 15), (x + 15, y + 15)], fill=color)
    draw.rectangle([x + 2, y + 15, x + 16, y + 18], fill=color)


def draw_pixel_lightning_icon(draw, x, y, size=18, color=(255, 255, 255, 255)):
    """Menggambar ikon Petir kilat pixel art kecil"""
    pts = [
        (x + 10, y),
        (x + 2, y + 10),
        (x + 9, y + 10),
        (x + 7, y + 18),
        (x + 16, y + 7),
        (x + 10, y + 7)
    ]
    draw.polygon(pts, fill=color)


def draw_pixel_trophy_icon(draw, x, y, size=18, color=(255, 255, 255, 255)):
    """Menggambar ikon Piala kemenangan pixel art kecil"""
    draw.polygon([(x + 3, y), (x + 15, y), (x + 12, y + 10), (x + 6, y + 10)], fill=color)
    draw.rectangle([x + 8, y + 10, x + 10, y + 14], fill=color)
    draw.rectangle([x + 4, y + 14, x + 14, y + 17], fill=color)


def draw_pixel_crown_icon(draw, x, y, size=20, color=(255, 220, 60, 255)):
    """Menggambar ikon Mahkota Emas catur kecil"""
    pts = [
        (x + 2, y + 5),
        (x + 6, y + 11),
        (x + 10, y + 2),
        (x + 14, y + 11),
        (x + 18, y + 5),
        (x + 17, y + 16),
        (x + 3, y + 16)
    ]
    draw.polygon(pts, fill=color)
    draw.rectangle([x + 3, y + 16, x + 17, y + 18], fill=color)


def draw_pixel_knight(draw, x, y, size=64, is_white=True):
    """Menggambar bidak Kuda (Knight) pixel art"""
    scale = size // 16
    grid = [
        "....######......",
        "...########.....",
        "..###..#####....",
        "..##....####....",
        "..##########....",
        ".############...",
        ".###..#######...",
        "######.######...",
        "######.######...",
        ".############...",
        "..###########...",
        "...##########...",
        "...#########....",
        "...#########....",
        "..###########...",
        ".#############.."
    ]
    c_main = (245, 248, 255) if is_white else (45, 42, 60)
    c_shade = (190, 200, 225) if is_white else (25, 22, 38)
    c_out = (25, 30, 48) if is_white else (15, 12, 25)
    
    for r, row in enumerate(grid):
        for c, ch in enumerate(row):
            if ch == '#':
                px = x + c * scale
                py = y + r * scale
                col = c_main if c < 10 else c_shade
                draw.rectangle([px, py, px + scale - 1, py + scale - 1], fill=col)
                # Outline
                if c == 0 or r == 0 or (c > 0 and grid[r][c-1] == '.') or (c < 15 and grid[r][c+1] == '.'):
                    draw.rectangle([px, py, px + scale - 1, py + scale - 1], fill=c_out)


def draw_pixel_king(draw, x, y, size=64, is_white=True):
    """Menggambar bidak Raja (King) pixel art dengan salib mahkota"""
    scale = size // 16
    grid = [
        ".......##.......",
        ".....######.....",
        ".......##.......",
        "....########....",
        "...##########...",
        "..###..##..###..",
        "..############..",
        "...##########...",
        "....########....",
        "....########....",
        "...##########...",
        "...##########...",
        "..############..",
        "..############..",
        ".##############.",
        "################"
    ]
    c_main = (255, 220, 60) if is_white else (50, 48, 65)
    c_shade = (210, 160, 30) if is_white else (30, 28, 42)
    c_out = (35, 25, 10) if is_white else (15, 12, 22)
    
    for r, row in enumerate(grid):
        for c, ch in enumerate(row):
            if ch == '#':
                px = x + c * scale
                py = y + r * scale
                col = c_main if c < 8 else c_shade
                draw.rectangle([px, py, px + scale - 1, py + scale - 1], fill=col)


def generate_chess_thumbnail():
    print("[THUMBNAIL] Memulai pembuatan thumbnail YouTube Chess...")

    # 1. Base Canvas & Background Atmosfer Ruang Catur Gelap Mewah
    base = Image.new("RGBA", (W, H), (14, 16, 28, 255))
    draw_base = ImageDraw.Draw(base)

    # Gradient radial atmosferik (Navy Purple -> Deep Midnight)
    cx, cy = int(W * 0.45), int(H * 0.5)
    max_dist = math.hypot(W, H) / 1.5
    for r in range(int(max_dist), 0, -12):
        t = r / max_dist
        cr = int(14 * t + 32 * (1 - t))
        cg = int(16 * t + 28 * (1 - t))
        cb = int(28 * t + 65 * (1 - t))
        draw_base.ellipse([cx - r, cy - r * 0.8, cx + r, cy + r * 0.8], fill=(cr, cg, cb, 255))

    # Grid pola papan catur halus di latar belakang
    grid_size = 64
    for gx in range(0, W, grid_size):
        for gy in range(0, H, grid_size):
            if (gx // grid_size + gy // grid_size) % 2 == 0:
                draw_base.rectangle([gx, gy, gx + grid_size, gy + grid_size], fill=(255, 255, 255, 6))

    # 2. Papan Catur 3D Perspektif Dramatis di Sisi Kiri-Tengah
    board_layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    b_draw = ImageDraw.Draw(board_layer)

    # Gambar papan catur isometrik / berperspektif miring di bagian bawah
    board_origin_x = 80
    board_origin_y = 440
    tile_w = 64
    tile_h = 32

    # Petak catur kayu berperspektif (Cream & Dark Walnut Wood)
    C_LIGHT_SQ = (235, 218, 185, 255)
    C_DARK_SQ = (120, 85, 65, 255)
    C_GLOW_SQ = (80, 220, 120, 230) # Petak analisis langkah terbaik (Hijau Chess.com)

    for row in range(6):
        for col in range(6):
            # Transformasi koordinat isometrik
            iso_x = board_origin_x + (col - row) * (tile_w * 0.72) + 260
            iso_y = board_origin_y + (col + row) * (tile_h * 0.62)
            
            p1 = (iso_x, iso_y - tile_h // 2)
            p2 = (iso_x + tile_w // 2, iso_y)
            p3 = (iso_x, iso_y + tile_h // 2)
            p4 = (iso_x - tile_w // 2, iso_y)

            # Warna petak
            if (row, col) in [(2, 3), (3, 3)]:
                fill_color = C_GLOW_SQ # Highlight taktik catur
            elif (row + col) % 2 == 0:
                fill_color = C_LIGHT_SQ
            else:
                fill_color = C_DARK_SQ

            b_draw.polygon([p1, p2, p3, p4], fill=fill_color, outline=(25, 20, 30, 220))

    # Gambar Panah Taktik Catur Hijau Neon (Analisis Langkah Terbaik / Best Move Arrow)
    arrow_start = (board_origin_x + 260, board_origin_y + 40)
    arrow_end = (board_origin_x + 360, board_origin_y - 20)
    b_draw.line([arrow_start, arrow_end], fill=(50, 255, 120, 240), width=14)
    # Kepala panah
    b_draw.polygon([
        (arrow_end[0] + 18, arrow_end[1] - 8),
        (arrow_end[0] - 14, arrow_end[1] - 22),
        (arrow_end[0] - 8, arrow_end[1] + 16)
    ], fill=(50, 255, 120, 255))

    # Gambar Bidak-Bidak Catur Pixel Art di Papan
    draw_pixel_knight(b_draw, board_origin_x + 310, board_origin_y - 10, size=90, is_white=True)
    draw_pixel_king(b_draw, board_origin_x + 190, board_origin_y + 20, size=95, is_white=True)
    draw_pixel_knight(b_draw, board_origin_x + 120, board_origin_y + 80, size=75, is_white=False)

    base.alpha_composite(board_layer)

    # 3. Karakter Ponyo VTuber dengan Mahkota Emas (Queen of Chess) di Sisi Kanan
    ponyo_img_path = os.path.join(AVATARS_DIR, "star.png") # Ekspresi kagum / berkilau bintang!
    if not os.path.exists(ponyo_img_path):
        ponyo_img_path = os.path.join(AVATARS_DIR, "happy.png")

    crown_img_path = os.path.join(AVATARS_DIR, "accessories", "crown.png")

    if os.path.exists(ponyo_img_path):
        ponyo_base = Image.open(ponyo_img_path).convert("RGBA")
        if os.path.exists(crown_img_path):
            crown_base = Image.open(crown_img_path).convert("RGBA")
            # Pasang mahkota emas di atas kepala Ponyo
            ponyo_composite = Image.alpha_composite(ponyo_base, crown_base)
        else:
            ponyo_composite = ponyo_base

        # Perbesar ukuran Ponyo agar megah dan mendominasi sisi kanan thumbnail (510x510)
        ponyo_size = 530
        ponyo_scaled = ponyo_composite.resize((ponyo_size, ponyo_size), Image.Resampling.NEAREST)

        # Buat Outline / Glow Putih & Cyan di Sekeliling Ponyo (Sticker Effect ala YouTube)
        glow_mask = Image.new("RGBA", (ponyo_size + 40, ponyo_size + 40), (0, 0, 0, 0))
        gm_draw = ImageDraw.Draw(glow_mask)
        p_alpha = ponyo_scaled.split()[3]

        # Outer thick border sticker
        border_thickness = 10
        for dx in range(-border_thickness, border_thickness + 1):
            for dy in range(-border_thickness, border_thickness + 1):
                if dx*dx + dy*dy <= border_thickness*border_thickness:
                    glow_mask.paste((0, 240, 255, 255), (dx + 20, dy + 20), p_alpha)

        # Inner white sticker line
        for dx in range(-4, 5):
            for dy in range(-4, 5):
                if dx*dx + dy*dy <= 16:
                    glow_mask.paste((255, 255, 255, 255), (dx + 20, dy + 20), p_alpha)

        # Paste Ponyo ke atas glow sticker
        glow_mask.paste(ponyo_scaled, (20, 20), ponyo_scaled)

        # Posisi Ponyo di sisi kanan thumbnail
        ponyo_pos_x = W - ponyo_size - 10
        ponyo_pos_y = H - ponyo_size + 15
        base.paste(glow_mask, (ponyo_pos_x - 20, ponyo_pos_y - 20), glow_mask)

    # 4. Balon Percakapan Komik Ponyo: "SKAKMAT DALAM 3 LANGKAH?!"
    bubble_img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    bu_draw = ImageDraw.Draw(bubble_img)

    font_impact = "C:/Windows/Fonts/impact.ttf"
    font_arial = "C:/Windows/Fonts/ariblk.ttf"

    font_bubble = ImageFont.truetype(font_arial, 22) if os.path.exists(font_arial) else ImageFont.load_default()

    # Balon kata di atas kepala Ponyo
    bx1, by1, bx2, by2 = W - 410, 80, W - 40, 160
    # Bayangan balon
    bu_draw.rounded_rectangle([bx1 + 6, by1 + 6, bx2 + 6, by2 + 6], radius=18, fill=(10, 12, 22, 180))
    # Bodi balon putih bersih
    bu_draw.rounded_rectangle([bx1, by1, bx2, by2], radius=18, fill=(255, 255, 255, 255), outline=(20, 24, 45, 255), width=4)
    # Ekor balon menunjuk ke kepala Ponyo
    bu_draw.polygon([
        (W - 200, by2 - 2),
        (W - 170, by2 - 2),
        (W - 160, by2 + 28)
    ], fill=(255, 255, 255, 255))
    bu_draw.line([(W - 200, by2 - 2), (W - 160, by2 + 28)], fill=(20, 24, 45, 255), width=4)
    bu_draw.line([(W - 170, by2 - 2), (W - 160, by2 + 28)], fill=(20, 24, 45, 255), width=4)

    bu_draw.text((bx1 + 22, by1 + 18), "TRIK SKAKMAT CEPAT!", fill=(225, 25, 50), font=font_bubble)
    bu_draw.text((bx1 + 22, by1 + 46), "Ponyo ajari sampai jago!", fill=(20, 28, 48), font=font_bubble)

    base.alpha_composite(bubble_img)

    # 5. TIPOGRAFI JUDUL UTAMA YOUTUBE (Sisi Kiri)
    txt_layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(txt_layer)

    font_title = ImageFont.truetype(font_impact, 104) if os.path.exists(font_impact) else ImageFont.load_default()
    font_ponyo = ImageFont.truetype(font_impact, 112) if os.path.exists(font_impact) else ImageFont.load_default()
    font_sub = ImageFont.truetype(font_impact, 36) if os.path.exists(font_impact) else ImageFont.load_default()
    font_badge = ImageFont.truetype(font_arial, 18) if os.path.exists(font_arial) else ImageFont.load_default()
    font_pills = ImageFont.truetype(font_arial, 15) if os.path.exists(font_arial) else ImageFont.load_default()

    # --- TOP BADGE: 🔴 LIVE STREAM + 👑 COACH VTUBER PONYO ---
    # Pill LIVE Merah Menyala
    d.rounded_rectangle([48, 38, 165, 76], radius=19, fill=(235, 25, 55, 255), outline=(255, 255, 255, 240), width=3)
    d.ellipse([60, 49, 74, 63], fill=(255, 255, 255, 255))
    d.text((84, 46), "LIVE", fill=(255, 255, 255), font=font_badge)

    # Pill COACH PONYO Emas (Diberi Ikon Mahkota Pixel Art Asli & Ukuran Proporsional)
    d.rounded_rectangle([180, 38, 515, 76], radius=19, fill=(35, 30, 55, 245), outline=(255, 215, 60, 240), width=3)
    draw_pixel_crown_icon(d, 196, 48, size=20, color=(255, 220, 80, 255))
    d.text((226, 46), "COACH VTUBER PONYO", fill=(255, 220, 80), font=font_badge)

    # --- BARIS JUDUL 1: "BELAJAR CHESS" ---
    title1 = "BELAJAR CHESS"
    t1_x, t1_y = 48, 92

    # 3D Deep Shadow & Outline Tebal
    for off in range(12, 0, -1):
        d.text((t1_x + off, t1_y + off), title1, fill=(8, 10, 20, 255), font=font_title)

    stroke_w = 7
    for sx in range(-stroke_w, stroke_w + 1):
        for sy in range(-stroke_w, stroke_w + 1):
            if sx*sx + sy*sy <= stroke_w*stroke_w:
                d.text((t1_x + sx, t1_y + sy), title1, fill=(15, 18, 30), font=font_title)

    # Warna Putih Bersih dengan Highlight Cyan Lembut
    d.text((t1_x, t1_y), title1, fill=(245, 252, 255), font=font_title)
    d.text((t1_x, t1_y - 3), title1, fill=(255, 255, 255), font=font_title)

    # --- BARIS JUDUL 2: "BERSAMA PONYO!" ---
    title2 = "BERSAMA PONYO!"
    t2_x, t2_y = 48, 200

    for off in range(14, 0, -1):
        d.text((t2_x + off, t2_y + off), title2, fill=(8, 10, 20, 255), font=font_ponyo)

    for sx in range(-stroke_w, stroke_w + 1):
        for sy in range(-stroke_w, stroke_w + 1):
            if sx*sx + sy*sy <= stroke_w*stroke_w:
                d.text((t2_x + sx, t2_y + sy), title2, fill=(15, 18, 30), font=font_ponyo)

    # Gradien Kuning-Emas Menyilaukan
    d.text((t2_x, t2_y), title2, fill=(255, 215, 30), font=font_ponyo)
    d.text((t2_x, t2_y - 3), title2, fill=(255, 245, 140), font=font_ponyo)

    # --- SUB-BANNER HOOK: "DARI PEMULA JADI PRO & MASTER!" ---
    hb_x1, hb_y1, hb_x2, hb_y2 = 48, 328, 725, 396
    d.rounded_rectangle([hb_x1 + 6, hb_y1 + 6, hb_x2 + 6, hb_y2 + 6], radius=14, fill=(8, 10, 20, 200))
    d.rounded_rectangle([hb_x1, hb_y1, hb_x2, hb_y2], radius=14, fill=(235, 35, 55, 255), outline=(255, 255, 255, 240), width=3)
    d.text((hb_x1 + 24, hb_y1 + 16), "DARI PEMULA JADI JAGO & PRO!", fill=(255, 255, 255), font=font_sub)

    # --- 3 BADGE FITUR DENGAN IKON PIXEL ART ASLI (Bebas Tofu Box & Luas) ---
    pills_data = [
        ("TRIK PEMBUKAAN", (35, 125, 245), (255, 255, 255), "PAWN", 222),
        ("BEDAH STRATEGI", (245, 150, 15), (20, 20, 25), "LIGHTNING", 216),
        ("NAIK +500 ELO!", (45, 205, 90), (15, 30, 20), "TROPHY", 200)
    ]
    px_start = 48
    py_pos = 416
    pill_h = 44

    cur_x = px_start
    for p_text, p_bg, p_fg, icon_type, p_w in pills_data:
        d.rounded_rectangle([cur_x + 3, py_pos + 3, cur_x + p_w + 3, py_pos + pill_h + 3], radius=12, fill=(10, 12, 22, 180))
        d.rounded_rectangle([cur_x, py_pos, cur_x + p_w, py_pos + pill_h], radius=12, fill=p_bg, outline=(255, 255, 255, 220), width=2)
        
        # Gambar ikon pixel art asli
        if icon_type == "PAWN":
            draw_pixel_pawn_icon(d, cur_x + 12, py_pos + 12, size=18, color=p_fg)
        elif icon_type == "LIGHTNING":
            draw_pixel_lightning_icon(d, cur_x + 12, py_pos + 12, size=18, color=p_fg)
        elif icon_type == "TROPHY":
            draw_pixel_trophy_icon(d, cur_x + 12, py_pos + 12, size=18, color=p_fg)

        d.text((cur_x + 38, py_pos + 12), p_text, fill=p_fg, font=font_pills)
        cur_x += p_w + 14

    # --- BADGE ELO / RATING DI POJOK KIRI BAWAH ---
    elo_x1, elo_y1, elo_x2, elo_y2 = 48, 622, 410, 680
    d.rounded_rectangle([elo_x1 + 4, elo_y1 + 4, elo_x2 + 4, elo_y2 + 4], radius=12, fill=(10, 12, 22, 180))
    d.rounded_rectangle([elo_x1, elo_y1, elo_x2, elo_y2], radius=12, fill=(24, 28, 52, 245), outline=(0, 240, 255, 220), width=2)
    d.text((elo_x1 + 20, elo_y1 + 16), "GRATIS! BISA TANYA DI CHAT", fill=(0, 240, 255), font=font_badge)

    base.alpha_composite(txt_layer)

    # 6. Border Luar Thumbnail Gaya YouTube Gamer Retro
    draw_final = ImageDraw.Draw(base)
    draw_final.rectangle([0, 0, W - 1, H - 1], outline=(255, 215, 60, 255), width=6)
    draw_final.rectangle([6, 6, W - 7, H - 7], outline=(20, 24, 40, 255), width=3)

    # Simpan hasil akhir
    base.save(OUTPUT_PATH, "PNG")
    print(f"[THUMBNAIL] Sukses dibuat: {OUTPUT_PATH} ({W}x{H})")
    return OUTPUT_PATH


if __name__ == "__main__":
    generate_chess_thumbnail()

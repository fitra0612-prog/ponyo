"""
YOUTUBE LIVE STREAM THUMBNAIL GENERATOR: MAIN SANTAI ROBLOX BARENG PONYO
========================================================================
Menghasilkan thumbnail YouTube profesional 1280x720 (16:9 Standard YouTube)
untuk live streaming Roblox santai & mabar bersama VTuber Ponyo.

Fitur visual:
- Karakter Ponyo si Hantu Imut mengenakan Telinga Kucing (Cat Ears) & Mata Bintang (Star Eyes)
- Karakter Classic Roblox Noob pixel art melompat di rintangan Obby pelangi
- Blok-blok rintangan Roblox Obby 3D dengan stud di atasnya
- Logo Roblox ikonik berputar miring
- Balon teks komik ajakan mabar: "OBBY SERU BANGET! Yuk mabar & join Ponyo!"
- Tipografi bold YouTube (Impact & Arial Black) dengan bayangan 3D tebal
- Badge status LIVE, MABAR SERVER, dan REQUEST MAP (Bebas missing glyphs)
"""

import os
import math
from PIL import Image, ImageDraw, ImageFont

PROJECT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
OUTPUT_DIR = os.path.join(PROJECT_DIR, "assets", "thumbnails")
os.makedirs(OUTPUT_DIR, exist_ok=True)
OUTPUT_PATH = os.path.join(OUTPUT_DIR, "thumbnail_roblox_mabar_ponyo.png")
AVATARS_DIR = os.path.join(PROJECT_DIR, "avatars")

W, H = 1280, 720


def draw_roblox_logo(draw, cx, cy, size=38, color=(235, 35, 50, 255)):
    """Menggambar logo miring ikonik Roblox dengan lubang persegi di tengahnya"""
    angle = math.radians(-14)
    half = size / 2.0
    hole_half = size * 0.24

    def rotate_pt(px, py):
        rx = px * math.cos(angle) - py * math.sin(angle)
        ry = px * math.sin(angle) + py * math.cos(angle)
        return (cx + rx, cy + ry)

    outer_pts = [
        rotate_pt(-half, -half),
        rotate_pt(half, -half),
        rotate_pt(half, half),
        rotate_pt(-half, half)
    ]
    # Bayangan logo
    shadow_pts = [(x + 4, y + 4) for x, y in outer_pts]
    draw.polygon(shadow_pts, fill=(10, 12, 25, 200))
    draw.polygon(outer_pts, fill=color)

    hole_pts = [
        rotate_pt(-hole_half, -hole_half),
        rotate_pt(hole_half, -hole_half),
        rotate_pt(hole_half, hole_half),
        rotate_pt(-hole_half, hole_half)
    ]
    draw.polygon(hole_pts, fill=(20, 24, 45, 255))


def draw_pixel_gamepad_icon(draw, x, y, size=18, color=(255, 255, 255, 255)):
    """Menggambar ikon stick controller gamepad pixel art"""
    # Body
    draw.rounded_rectangle([x + 1, y + 3, x + 19, y + 15], radius=4, fill=color)
    # D-pad cross & buttons
    c_cut = (20, 25, 45, 255)
    draw.rectangle([x + 4, y + 6, x + 8, y + 8], fill=c_cut)
    draw.rectangle([x + 5, y + 5, x + 7, y + 9], fill=c_cut)
    # Buttons
    draw.rectangle([x + 13, y + 6, x + 15, y + 8], fill=c_cut)
    draw.rectangle([x + 15, y + 8, x + 17, y + 10], fill=c_cut)


def draw_pixel_rainbow_block_icon(draw, x, y, size=18, color=(255, 255, 255, 255)):
    """Menggambar ikon blok kubus Roblox berundak"""
    draw.rectangle([x + 2, y + 4, x + 18, y + 16], fill=color)
    # 2 studs on top
    draw.rectangle([x + 4, y + 1, x + 8, y + 4], fill=color)
    draw.rectangle([x + 12, y + 1, x + 16, y + 4], fill=color)


def draw_pixel_chat_icon(draw, x, y, size=18, color=(255, 255, 255, 255)):
    """Menggambar ikon balon chat penonton"""
    draw.rounded_rectangle([x + 2, y + 2, x + 18, y + 14], radius=3, fill=color)
    draw.polygon([(x + 5, y + 14), (x + 9, y + 14), (x + 5, y + 18)], fill=color)
    c_dots = (20, 25, 45, 255)
    draw.rectangle([x + 5, y + 7, x + 7, y + 9], fill=c_dots)
    draw.rectangle([x + 9, y + 7, x + 11, y + 9], fill=c_dots)
    draw.rectangle([x + 13, y + 7, x + 15, y + 9], fill=c_dots)


def draw_pixel_noob(draw, x, y, scale=4):
    """Menggambar karakter ikonik Roblox Classic Noob pixel art"""
    C_YELLOW = (255, 222, 40, 255)
    C_BLUE = (0, 135, 235, 255)
    C_GREEN = (90, 210, 50, 255)
    C_FACE = (20, 22, 35, 255)
    C_OUTLINE = (18, 22, 36, 255)

    # Bayangan di bawah kaki
    draw.ellipse([x, y + 25 * scale, x + 16 * scale, y + 28 * scale], fill=(10, 15, 30, 160))

    # Kepala (8x8)
    draw.rectangle([x + 4 * scale, y, x + 12 * scale - 1, y + 8 * scale - 1], fill=C_YELLOW, outline=C_OUTLINE)
    # Mata & Senyum ramah Noob
    draw.rectangle([x + 6 * scale, y + 3 * scale, x + 7 * scale - 1, y + 4 * scale - 1], fill=C_FACE)
    draw.rectangle([x + 9 * scale, y + 3 * scale, x + 10 * scale - 1, y + 4 * scale - 1], fill=C_FACE)
    draw.rectangle([x + 6 * scale, y + 6 * scale, x + 10 * scale - 1, y + 7 * scale - 1], fill=C_FACE)

    # Badan / Baju Biru (8x9)
    draw.rectangle([x + 4 * scale, y + 8 * scale, x + 12 * scale - 1, y + 17 * scale - 1], fill=C_BLUE, outline=C_OUTLINE)

    # Lengan Kiri (Turun santai)
    draw.rectangle([x, y + 8 * scale, x + 4 * scale - 1, y + 16 * scale - 1], fill=C_YELLOW, outline=C_OUTLINE)

    # Lengan Kanan (Melambai menyapa penonton ke atas)
    draw.rectangle([x + 12 * scale, y + 3 * scale, x + 16 * scale - 1, y + 11 * scale - 1], fill=C_YELLOW, outline=C_OUTLINE)

    # Kaki / Celana Hijau (4x9 each)
    draw.rectangle([x + 4 * scale, y + 17 * scale, x + 8 * scale - 1, y + 26 * scale - 1], fill=C_GREEN, outline=C_OUTLINE)
    draw.rectangle([x + 8 * scale, y + 17 * scale, x + 12 * scale - 1, y + 26 * scale - 1], fill=C_GREEN, outline=C_OUTLINE)


def draw_3d_obby_block(draw, x, y, width=120, height=50, depth=25, top_color=(255, 60, 80), side_color=(190, 30, 50)):
    """Menggambar balok rintangan Roblox Obby 3D lengkap dengan studs bulat di atasnya"""
    # Sisi samping / bawah 3D
    draw.rectangle([x, y + depth, x + width, y + height + depth], fill=side_color, outline=(20, 24, 40, 255), width=2)
    # Sisi atas
    draw.rectangle([x, y, x + width, y + depth], fill=top_color, outline=(20, 24, 40, 255), width=2)

    # Studs bulat khas Roblox di permukaan atas blok
    stud_r = 7
    num_studs = max(2, width // 35)
    step = width / (num_studs + 1)
    for i in range(1, num_studs + 1):
        sx = int(x + i * step)
        sy = int(y + depth / 2)
        # Bayangan stud
        draw.ellipse([sx - stud_r, sy - stud_r // 2 + 1, sx + stud_r, sy + stud_r // 2 + 1], fill=(*side_color[:3], 240))
        # Kepala stud
        draw.ellipse([sx - stud_r, sy - stud_r // 2, sx + stud_r, sy + stud_r // 2], fill=top_color, outline=(20, 24, 40, 200))


def generate_roblox_thumbnail():
    print("[THUMBNAIL] Memulai pembuatan thumbnail YouTube Roblox Mabar...")

    # 1. Base Canvas & Background Langit Senja Ceria Roblox (Sunset Purple / Cyan Dreamy Sky)
    base = Image.new("RGBA", (W, H), (18, 20, 42, 255))
    draw_base = ImageDraw.Draw(base)

    # Gradien langit bertingkat (Deep Midnight Violet -> Vibrant Purple -> Warm Magenta-Orange)
    for y in range(H):
        t = y / float(H)
        # Langit atas biru malam, tengah ungu ceria, bawah semburat hangat
        if t < 0.5:
            p = t / 0.5
            r = int(22 * (1 - p) + 75 * p)
            g = int(26 * (1 - p) + 40 * p)
            b = int(60 * (1 - p) + 125 * p)
        else:
            p = (t - 0.5) / 0.5
            r = int(75 * (1 - p) + 140 * p)
            g = int(40 * (1 - p) + 60 * p)
            b = int(125 * (1 - p) + 85 * p)
        draw_base.line([(0, y), (W, y)], fill=(r, g, b, 255))

    # Awan lembut di langit (Ditempatkan di area tengah-kanan agar langit kiri bersih untuk teks judul)
    def draw_pixel_cloud(d, cx, cy, w, h):
        c_cloud = (255, 255, 255, 22)
        d.rounded_rectangle([cx - w // 2, cy - h // 2, cx + w // 2, cy + h // 2], radius=h // 2, fill=c_cloud)
        d.rounded_rectangle([cx - w // 3, cy - h, cx + w // 3, cy], radius=h // 2, fill=c_cloud)

    draw_pixel_cloud(draw_base, 760, 85, 300, 50)
    draw_pixel_cloud(draw_base, 1140, 140, 180, 36)

    # 2. Gambar Rintangan Balok Obby Pelangi 3D Mengambang (Rainbow Obby)
    # Diposisikan rapi di area bawah-tengah (y=500..590) sehingga terpisah dari teks & karakter
    obby_blocks = [
        (48, 540, 110, 38, 20, (255, 55, 75), (180, 25, 45)),    # Merah
        (175, 510, 110, 38, 20, (255, 140, 20), (185, 95, 10)),  # Oranye
        (305, 535, 115, 38, 20, (255, 220, 30), (190, 160, 15)), # Kuning (Tempat Noob berdiri)
        (440, 495, 115, 38, 20, (60, 215, 90), (35, 150, 60)),   # Hijau
        (575, 525, 115, 38, 20, (30, 185, 255), (15, 125, 190)), # Cyan
    ]

    for bx, by, bw, bh, bd, top_c, side_c in obby_blocks:
        draw_3d_obby_block(draw_base, bx, by, width=bw, height=bh, depth=bd, top_color=top_c, side_color=side_c)

    # Karakter Classic Roblox Noob berdiri bebas & tampak utuh 100% di atas blok kuning!
    # Berada tepat di antara baris pills (y=405) dan bottom CTA (y=622), bebas tumpang tindih
    draw_pixel_noob(draw_base, 335, 435, scale=4)

    # Logo Roblox Tilted Cube di latar belakang melayang
    draw_roblox_logo(draw_base, 735, 205, size=60, color=(245, 45, 60, 255))

    # 3. Karakter Ponyo VTuber dengan Halo Malaikat Kuning di Sisi Kanan
    ponyo_img_path = os.path.join(AVATARS_DIR, "star.png") # Ekspresi ceria dengan mata bintang
    if not os.path.exists(ponyo_img_path):
        ponyo_img_path = os.path.join(AVATARS_DIR, "happy.png")

    angel_halo_path = os.path.join(AVATARS_DIR, "accessories", "angel_halo.png")

    if os.path.exists(ponyo_img_path):
        ponyo_base = Image.open(ponyo_img_path).convert("RGBA")
        if os.path.exists(angel_halo_path):
            halo_img = Image.open(angel_halo_path).convert("RGBA")
            ponyo_composite = Image.alpha_composite(ponyo_base, halo_img)
        else:
            ponyo_composite = ponyo_base

        ponyo_size = 540
        ponyo_scaled = ponyo_composite.resize((ponyo_size, ponyo_size), Image.Resampling.NEAREST)

        # Efek stiker garis tepi ganda (Cyan neon + Putih bersih)
        glow_mask = Image.new("RGBA", (ponyo_size + 40, ponyo_size + 40), (0, 0, 0, 0))
        p_alpha = ponyo_scaled.split()[3]

        border_thickness = 11
        for dx in range(-border_thickness, border_thickness + 1):
            for dy in range(-border_thickness, border_thickness + 1):
                if dx * dx + dy * dy <= border_thickness * border_thickness:
                    glow_mask.paste((255, 60, 160, 255), (dx + 20, dy + 20), p_alpha) # Glow Pink/Magenta ceria

        for dx in range(-4, 5):
            for dy in range(-4, 5):
                if dx * dx + dy * dy <= 16:
                    glow_mask.paste((255, 255, 255, 255), (dx + 20, dy + 20), p_alpha)

        glow_mask.paste(ponyo_scaled, (20, 20), ponyo_scaled)

        # Letakkan Ponyo di sisi kanan thumbnail
        ponyo_pos_x = W - ponyo_size - 10
        ponyo_pos_y = H - ponyo_size + 20
        base.paste(glow_mask, (ponyo_pos_x - 20, ponyo_pos_y - 20), glow_mask)

    # 4. Balon Percakapan Komik Ponyo (Speech Bubble di Kanan Atas)
    bubble_img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    bu_draw = ImageDraw.Draw(bubble_img)

    font_impact = "C:/Windows/Fonts/impact.ttf"
    font_arial = "C:/Windows/Fonts/ariblk.ttf"

    font_bubble_title = ImageFont.truetype(font_impact, 26) if os.path.exists(font_impact) else ImageFont.load_default()
    font_bubble_sub = ImageFont.truetype(font_arial, 18) if os.path.exists(font_arial) else ImageFont.load_default()

    bx1, by1, bx2, by2 = W - 410, 75, W - 40, 162
    bu_draw.rounded_rectangle([bx1 + 6, by1 + 6, bx2 + 6, by2 + 6], radius=18, fill=(10, 12, 22, 180))
    bu_draw.rounded_rectangle([bx1, by1, bx2, by2], radius=18, fill=(255, 255, 255, 255), outline=(20, 24, 45, 255), width=4)

    # Ekor balon menunjuk ke kepala Ponyo
    bu_draw.polygon([
        (W - 200, by2 - 2),
        (W - 170, by2 - 2),
        (W - 160, by2 + 28)
    ], fill=(255, 255, 255, 255))
    bu_draw.line([(W - 200, by2 - 2), (W - 160, by2 + 28)], fill=(20, 24, 45, 255), width=4)
    bu_draw.line([(W - 170, by2 - 2), (W - 160, by2 + 28)], fill=(20, 24, 45, 255), width=4)

    bu_draw.text((bx1 + 24, by1 + 16), "OBBY SERU BANGET!", fill=(235, 35, 50), font=font_bubble_title)
    bu_draw.text((bx1 + 24, by1 + 48), "Yuk mabar & join Ponyo!", fill=(20, 28, 48), font=font_bubble_sub)

    base.alpha_composite(bubble_img)

    # 5. TIPOGRAFI JUDUL BESAR YOUTUBE (Sisi Kiri)
    txt_layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(txt_layer)

    font_title1 = ImageFont.truetype(font_impact, 96) if os.path.exists(font_impact) else ImageFont.load_default()
    font_roblox = ImageFont.truetype(font_impact, 114) if os.path.exists(font_impact) else ImageFont.load_default()
    font_sub = ImageFont.truetype(font_impact, 36) if os.path.exists(font_impact) else ImageFont.load_default()
    font_badge = ImageFont.truetype(font_arial, 18) if os.path.exists(font_arial) else ImageFont.load_default()
    font_pills = ImageFont.truetype(font_arial, 15) if os.path.exists(font_arial) else ImageFont.load_default()

    # --- TOP STATUS PILLS: 🔴 LIVE STREAM + 🎮 ROBLOX CHILL & PLAY ---
    # Pill LIVE Merah Menyala
    d.rounded_rectangle([48, 38, 165, 76], radius=19, fill=(235, 25, 55, 255), outline=(255, 255, 255, 240), width=3)
    d.ellipse([60, 49, 74, 63], fill=(255, 255, 255, 255))
    d.text((84, 46), "LIVE", fill=(255, 255, 255), font=font_badge)

    # Pill ROBLOX CHILL & PLAY
    d.rounded_rectangle([180, 38, 510, 76], radius=19, fill=(35, 28, 60, 245), outline=(255, 215, 60, 240), width=3)
    draw_roblox_logo(d, 204, 57, size=24, color=(255, 220, 80, 255))
    d.text((226, 46), "ROBLOX CHILL & PLAY", fill=(255, 220, 80), font=font_badge)

    # --- BARIS JUDUL 1: "MAIN SANTAI" ---
    title1 = "MAIN SANTAI"
    t1_x, t1_y = 48, 88

    # 3D Shadow Tebal
    for off in range(12, 0, -1):
        d.text((t1_x + off, t1_y + off), title1, fill=(10, 12, 25, 255), font=font_title1)

    stroke_w = 7
    for sx in range(-stroke_w, stroke_w + 1):
        for sy in range(-stroke_w, stroke_w + 1):
            if sx * sx + sy * sy <= stroke_w * stroke_w:
                d.text((t1_x + sx, t1_y + sy), title1, fill=(18, 22, 36), font=font_title1)

    d.text((t1_x, t1_y), title1, fill=(250, 252, 255), font=font_title1)
    d.text((t1_x, t1_y - 3), title1, fill=(255, 255, 255), font=font_title1)

    # --- BARIS JUDUL 2: "ROBLOX PONYO!" ---
    title2 = "ROBLOX PONYO!"
    t2_x, t2_y = 48, 192

    for off in range(14, 0, -1):
        d.text((t2_x + off, t2_y + off), title2, fill=(10, 12, 25, 255), font=font_roblox)

    for sx in range(-stroke_w, stroke_w + 1):
        for sy in range(-stroke_w, stroke_w + 1):
            if sx * sx + sy * sy <= stroke_w * stroke_w:
                d.text((t2_x + sx, t2_y + sy), title2, fill=(18, 22, 36), font=font_roblox)

    # Gradien Kuning-Merah cerah khas gaming
    d.text((t2_x, t2_y), title2, fill=(255, 215, 35), font=font_roblox)
    d.text((t2_x, t2_y - 3), title2, fill=(255, 245, 140), font=font_roblox)

    # --- SUB-BANNER HOOK: "OBBY, PARKOUR & SERU-SERUAN!" ---
    hb_x1, hb_y1, hb_x2, hb_y2 = 48, 320, 720, 388
    d.rounded_rectangle([hb_x1 + 6, hb_y1 + 6, hb_x2 + 6, hb_y2 + 6], radius=14, fill=(10, 12, 25, 200))
    d.rounded_rectangle([hb_x1, hb_y1, hb_x2, hb_y2], radius=14, fill=(235, 45, 75, 255), outline=(255, 255, 255, 240), width=3)
    d.text((hb_x1 + 24, hb_y1 + 16), "OBBY, PARKOUR & SERU-SERUAN!", fill=(255, 255, 255), font=font_sub)

    # --- 3 FEATURE PILLS (Bebas Missing Glyphs & Pas) ---
    pills_data = [
        ("MABAR VIEWERS", (35, 125, 245), (255, 255, 255), "GAMEPAD", 205),
        ("OBBY & CHILL", (245, 145, 15), (20, 20, 25), "BLOCK", 195),
        ("REQUEST MAP", (45, 205, 90), (15, 30, 20), "CHAT", 190)
    ]
    px_start = 48
    py_pos = 408
    pill_h = 44

    cur_x = px_start
    for p_text, p_bg, p_fg, icon_type, p_w in pills_data:
        d.rounded_rectangle([cur_x + 3, py_pos + 3, cur_x + p_w + 3, py_pos + pill_h + 3], radius=12, fill=(10, 12, 22, 180))
        d.rounded_rectangle([cur_x, py_pos, cur_x + p_w, py_pos + pill_h], radius=12, fill=p_bg, outline=(255, 255, 255, 220), width=2)

        if icon_type == "GAMEPAD":
            draw_pixel_gamepad_icon(d, cur_x + 12, py_pos + 12, size=18, color=p_fg)
        elif icon_type == "BLOCK":
            draw_pixel_rainbow_block_icon(d, cur_x + 12, py_pos + 12, size=18, color=p_fg)
        elif icon_type == "CHAT":
            draw_pixel_chat_icon(d, cur_x + 12, py_pos + 12, size=18, color=p_fg)

        d.text((cur_x + 38, py_pos + 12), p_text, fill=p_fg, font=font_pills)
        cur_x += p_w + 14

    # --- CALL TO ACTION BADGE (Pojok Kiri Bawah) ---
    cta_x1, cta_y1, cta_x2, cta_y2 = 48, 622, 435, 680
    d.rounded_rectangle([cta_x1 + 4, cta_y1 + 4, cta_x2 + 4, cta_y2 + 4], radius=12, fill=(10, 12, 22, 180))
    d.rounded_rectangle([cta_x1, cta_y1, cta_x2, cta_y2], radius=12, fill=(25, 28, 55, 245), outline=(0, 240, 255, 220), width=2)
    d.text((cta_x1 + 20, cta_y1 + 16), "GRATIS! SEMUA BISA JOIN MABAR", fill=(0, 240, 255), font=font_badge)

    base.alpha_composite(txt_layer)

    # 6. Border Luar Thumbnail Gaya YouTube Gamer Retro
    draw_final = ImageDraw.Draw(base)
    draw_final.rectangle([0, 0, W - 1, H - 1], outline=(255, 215, 60, 255), width=6)
    draw_final.rectangle([6, 6, W - 7, H - 7], outline=(20, 24, 40, 255), width=3)

    base.save(OUTPUT_PATH, "PNG")
    print(f"[THUMBNAIL] Sukses dibuat: {OUTPUT_PATH} ({W}x{H})")
    return OUTPUT_PATH


if __name__ == "__main__":
    generate_roblox_thumbnail()

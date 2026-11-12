"""
HAUNTED HOUSE BRICK WALL PIXEL ART GENERATOR
============================================
Menghasilkan latar belakang dinding bata rumah hantu (haunted house brick wall)
bergaya retro pixel art atmosferik.

Menghasilkan 2 ukuran:
1. background_haunted_brick_wall.png (1920x1080 - 16:9 HD untuk OBS Stream Background / Wallpaper)
2. background_brick_wall_avatar.png (480x560 - Proporsional untuk jendela display avatar Ponyo)
"""

import os
import math
import random
from PIL import Image, ImageDraw

def create_haunted_brick_wall(width=1920, height=1080, scale=6):
    # Dimensi kanvas pixel art murni
    gw = width // scale
    gh = height // scale
    
    img = Image.new("RGBA", (gw, gh), (16, 14, 26, 255))
    px = img.load()
    
    # Palet Warna Rumah Hantu
    # Bata Gelap & Lembap
    PAL_MORTAR = (20, 18, 30)
    PAL_BRICK_BASE = (38, 34, 54)
    PAL_BRICK_DARK = (28, 25, 40)
    PAL_BRICK_MID = (46, 42, 66)
    PAL_BRICK_LIGHT = (64, 58, 88)
    PAL_BRICK_HIGHLIGHT = (82, 75, 112)
    
    # Lumut & Kelembapan Berhantu
    PAL_MOSS_DARK = (24, 46, 38)
    PAL_MOSS_MID = (38, 74, 58)
    PAL_MOSS_LIGHT = (62, 118, 92)
    
    # Obor Mistis / Cahaya Api Hantu (Cyan/Eerie Teal-Blue Flame)
    TORCH_X = int(gw * 0.22)
    TORCH_Y = int(gh * 0.42)
    
    TORCH_X2 = int(gw * 0.78)
    TORCH_Y2 = int(gh * 0.42)
    
    # 1. Gambar Susunan Bata (Staggered Brickwork)
    brick_h = 10
    brick_w = 24
    
    random.seed(1337) # Deterministik agar detail konsisten
    
    # Peta variasi warna tiap bata
    for row_idx, y in enumerate(range(0, gh, brick_h)):
        is_odd = (row_idx % 2 == 1)
        x_offset = - (brick_w // 2) if is_odd else 0
        
        for x in range(x_offset, gw + brick_w, brick_w):
            # Variasi warna bata acak alami
            v = random.choice([-6, -3, 0, 3, 6])
            b_base = (
                max(15, min(255, PAL_BRICK_MID[0] + v)),
                max(15, min(255, PAL_BRICK_MID[1] + v)),
                max(20, min(255, PAL_BRICK_MID[2] + v))
            )
            
            # Beberapa bata rusak / pecah / bolong
            is_broken = (random.random() < 0.08)
            is_mossy = (random.random() < 0.25)
            
            for by in range(brick_h):
                py = y + by
                if py >= gh:
                    break
                for bx in range(brick_w):
                    px_pos = x + bx
                    if 0 <= px_pos < gw:
                        # Garis semen / mortar di sekeliling bata
                        if by == brick_h - 1 or bx == brick_w - 1:
                            px[px_pos, py] = PAL_MORTAR + (255,)
                        elif by == 0 or bx == 0:
                            # Highlight sisi atas & kiri bata
                            px[px_pos, py] = PAL_BRICK_LIGHT + (255,)
                        elif by == 1 or bx == 1:
                            px[px_pos, py] = PAL_BRICK_MID + (255,)
                        elif by == brick_h - 2 or bx == brick_w - 2:
                            # Shadow sisi bawah & kanan bata
                            px[px_pos, py] = PAL_BRICK_DARK + (255,)
                        else:
                            # Bodi bata bertekstur
                            tex = random.choice([-2, 0, 2])
                            c = (
                                max(10, min(255, b_base[0] + tex)),
                                max(10, min(255, b_base[1] + tex)),
                                max(15, min(255, b_base[2] + tex)),
                                255
                            )
                            px[px_pos, py] = c
                            
            # Jika bata rusak / berlubang
            if is_broken and x > 10 and x < gw - 30 and y > 20 and y < gh - 40:
                hole_w = random.randint(4, 10)
                hole_h = random.randint(3, 6)
                hx = x + random.randint(2, brick_w - hole_w - 2)
                hy = y + random.randint(1, brick_h - hole_h - 1)
                for dhy in range(hole_h):
                    for dhx in range(hole_w):
                        cur_x = hx + dhx
                        cur_y = hy + dhy
                        if 0 <= cur_x < gw and 0 <= cur_y < gh:
                            px[cur_x, cur_y] = (12, 10, 18, 255) # Lubang gelap dalam
                # Retakan keluar dari lubang
                for step in range(random.randint(4, 9)):
                    rx = hx + hole_w + step
                    ry = hy + (step % 2)
                    if 0 <= rx < gw and 0 <= ry < gh:
                        px[rx, ry] = (14, 12, 22, 255)

    # 2. Tambahkan Lumut Menjalar (Creeping Moss & Vines)
    for _ in range(35):
        vx = random.randint(0, gw - 1)
        vy = random.randint(0, gh - 1)
        v_len = random.randint(5, 22)
        cur_vx, cur_vy = vx, vy
        for _ in range(v_len):
            if 0 <= cur_vx < gw and 0 <= cur_vy < gh:
                c_moss = random.choice([PAL_MOSS_DARK, PAL_MOSS_MID, PAL_MOSS_LIGHT])
                px[cur_vx, cur_vy] = c_moss + (255,)
                # Lebarkan sedikit
                if random.random() < 0.5 and cur_vx + 1 < gw:
                    px[cur_vx + 1, cur_vy] = PAL_MOSS_DARK + (255,)
            cur_vy += 1
            if random.random() < 0.4:
                cur_vx += random.choice([-1, 1])

    # 3. Mata Mengintai di Lubang Dinding Gelap (Spooky Peeking Eyes)
    peeking_spots = [
        (int(gw * 0.12), int(gh * 0.65)),
        (int(gw * 0.88), int(gh * 0.28)),
        (int(gw * 0.48), int(gh * 0.82))
    ]
    for ex, ey in peeking_spots:
        # Lubang batu gelap di belakang
        for dy in range(-2, 3):
            for dx in range(-4, 5):
                if 0 <= ex + dx < gw and 0 <= ey + dy < gh:
                    px[ex + dx, ey + dy] = (8, 6, 14, 255)
        # Sepasang mata bercahaya kuning/oranye hantu
        if 0 <= ex < gw and 0 <= ey < gh:
            # Mata kiri
            px[ex - 2, ey] = (255, 215, 60, 255)
            px[ex - 2, ey - 1] = (255, 240, 150, 255)
            # Mata kanan
            px[ex + 2, ey] = (255, 215, 60, 255)
            px[ex + 2, ey - 1] = (255, 240, 150, 255)

    # 4. Sarang Laba-laba di Sudut-sudut (Corner Cobwebs)
    def draw_web(corner_x, corner_y, dir_x, dir_y, size=32):
        C_WEB = (130, 135, 165, 140)
        C_WEB_LIGHT = (180, 185, 215, 180)
        # Garis jari-jari
        for i in range(1, size):
            # Garis diagonal utama
            wx = corner_x + dir_x * i
            wy = corner_y + dir_y * int(i * 0.75)
            if 0 <= wx < gw and 0 <= wy < gh:
                px[wx, wy] = C_WEB
            # Garis kedua
            wx2 = corner_x + dir_x * int(i * 0.75)
            wy2 = corner_y + dir_y * i
            if 0 <= wx2 < gw and 0 <= wy2 < gh:
                px[wx2, wy2] = C_WEB
            # Lengkungan benang penghubung
            if i % 6 == 0:
                for step in range(i):
                    lx = corner_x + dir_x * step
                    ly = corner_y + dir_y * int(math.sqrt(max(0, i*i - step*step)) * 0.85)
                    if 0 <= lx < gw and 0 <= ly < gh:
                        px[lx, ly] = C_WEB_LIGHT

    # Pasang sarang laba-laba di pojok kiri atas & kanan atas
    draw_web(0, 0, 1, 1, size=28)
    draw_web(gw - 1, 0, -1, 1, size=32)
    draw_web(0, gh - 1, 1, -1, size=22)

    # 5. Balok Kayu Tua & Rantai Menggantung di Langit-langit (Gothic Wooden Beams & Chains)
    # Rantai besi menggantung
    for chain_x in [int(gw * 0.38), int(gw * 0.62)]:
        chain_len = random.randint(24, 45)
        for cy in range(0, chain_len):
            if cy % 3 == 0:
                px[chain_x, cy] = (45, 45, 60, 255)
                px[chain_x - 1, cy] = (25, 25, 35, 255)
                px[chain_x + 1, cy] = (65, 65, 85, 255)
            else:
                px[chain_x, cy] = (30, 30, 42, 255)
        # Cincin / Belenggu besi di ujung rantai
        end_y = chain_len
        for dy in range(4):
            px[chain_x - 2, end_y + dy] = (70, 70, 95, 255)
            px[chain_x + 2, end_y + dy] = (70, 70, 95, 255)
        px[chain_x - 1, end_y + 4] = (70, 70, 95, 255)
        px[chain_x, end_y + 4] = (70, 70, 95, 255)
        px[chain_x + 1, end_y + 4] = (70, 70, 95, 255)

    # 6. Efek Pencahayaan Obor Berhantu (Eerie Torch Light Overlay)
    # Obor 1 (Kiri) dan Obor 2 (Kanan)
    torches = [(TORCH_X, TORCH_Y), (TORCH_X2, TORCH_Y2)]
    
    # Hitung radial lighting mistis (Cyan-Violet Spooky Glow)
    for y in range(gh):
        for x in range(gw):
            orig_r, orig_g, orig_b, orig_a = px[x, y]
            
            # Hitung pengaruh cahaya dari kedua obor
            total_glow = 0.0
            for tx, ty in torches:
                dist = math.hypot(x - tx, (y - ty) * 1.25)
                # Radius cahaya obor
                if dist < 85:
                    intensity = math.pow(max(0.0, 1.0 - (dist / 85.0)), 1.6)
                    total_glow += intensity
            
            # Ambience gelap rumah hantu (Vignette di pinggiran)
            cx, cy = gw / 2.0, gh / 2.0
            dist_center = math.hypot((x - cx) / cx, (y - cy) / cy)
            vignette = max(0.45, 1.05 - (dist_center * 0.45))
            
            # Warnai dengan cahaya api biru/ungu berhantu (Ghost Flame)
            glow_r = int(total_glow * 35)
            glow_g = int(total_glow * 115)
            glow_b = int(total_glow * 140)
            
            nr = int(min(255, (orig_r * vignette) + glow_r))
            ng = int(min(255, (orig_g * vignette) + glow_g))
            nb = int(min(255, (orig_b * vignette) + glow_b))
            
            px[x, y] = (nr, ng, nb, 255)

    # 7. Gambar Braket Besi & Api Obor Pixel Art
    for tx, ty in torches:
        # Braket besi hitam di dinding
        # Plat besi
        for dy in range(-2, 8):
            for dx in range(-2, 3):
                px[tx + dx, ty + dy] = (25, 26, 38, 255)
        # Lengan penyangga miring
        px[tx, ty + 8] = (35, 38, 52, 255)
        px[tx - 1, ty + 9] = (35, 38, 52, 255)
        px[tx - 2, ty + 10] = (20, 22, 32, 255)
        # Wadah mangkuk obor
        for dx in range(-4, 5):
            px[tx + dx, ty - 2] = (50, 52, 70, 255)
            px[tx + dx, ty - 1] = (38, 40, 56, 255)
        for dx in range(-3, 4):
            px[tx + dx, ty] = (28, 30, 42, 255)
        
        # Nyala Api Biru Kehantuan (Ghost Fire)
        # Inti api (putih-cyan sangat terang)
        flame_core = (235, 255, 255, 255)
        flame_cyan = (90, 240, 255, 255)
        flame_blue = (40, 140, 250, 255)
        flame_deep = (25, 60, 180, 255)
        
        # Bentuk lidah api
        for dy in range(-12, -2):
            w = int((12 + dy) * 0.55) + 1
            for dx in range(-w, w + 1):
                if abs(dx) <= 1 and dy > -9:
                    px[tx + dx, ty + dy] = flame_core
                elif abs(dx) <= w - 1 and dy > -11:
                    px[tx + dx, ty + dy] = flame_cyan
                elif abs(dx) <= w:
                    px[tx + dx, ty + dy] = flame_blue
                else:
                    px[tx + dx, ty + dy] = flame_deep
        # Ujung jilatan api melengkung ke atas
        px[tx, ty - 13] = flame_cyan
        px[tx - 1, ty - 14] = flame_blue
        px[tx, ty - 15] = flame_blue
        
        # Percikan partikel api melayang
        px[tx + 3, ty - 16] = flame_cyan
        px[tx - 2, ty - 18] = flame_cyan

    # 8. Skala ke resolusi target menggunakan NEAREST Neighbor (Gaya Pixel Art Murni)
    scaled_img = img.resize((width, height), Image.Resampling.NEAREST)
    return scaled_img


def generate_all_backgrounds():
    output_dir = os.path.join(os.path.dirname(__file__), "assets", "backgrounds")
    os.makedirs(output_dir, exist_ok=True)

    # 1. Background Lebar untuk OBS / YouTube Live (1920x1080 Full HD)
    bg_1080p = create_haunted_brick_wall(width=1920, height=1080, scale=6)
    path_1080p = os.path.join(output_dir, "background_haunted_brick_wall.png")
    bg_1080p.save(path_1080p, "PNG")
    print(f"[BACKGROUND] Berhasil dibuat: {path_1080p} (1920x1080)")

    # 2. Background Vertikal untuk Display Avatar Ponyo (480x560)
    bg_avatar = create_haunted_brick_wall(width=480, height=560, scale=4)
    path_avatar = os.path.join(output_dir, "background_brick_wall_avatar.png")
    bg_avatar.save(path_avatar, "PNG")
    print(f"[BACKGROUND] Berhasil dibuat: {path_avatar} (480x560)")


if __name__ == "__main__":
    generate_all_backgrounds()

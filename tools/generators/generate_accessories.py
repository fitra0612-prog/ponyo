"""
PIXEL ART ACCESSORIES GENERATOR FOR PONYO VTUBER (SARAN NOMOR 2)
================================================================
Menghasilkan aksesoris pixel art retro pada grid 64x64 (skala 576x576):
- ribbon   : Pita merah muda manis di samping kepala Ponyo
- witch    : Topi kerucut penyihir ungu tua dengan gesper emas
- crown    : Mahkota emas raja dengan permata ruby & safir
- glasses  : Kacamata hitam pixel art keren (Thug Life)
- flower   : Bunga melati putih & kuning lembut dengan daun hijau
- angel_halo  : Halo malaikat emas kuning
- devil_horns : Tanduk setan merah
- knight   : Helm ksatria
"""

import os
from PIL import Image

PROJECT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
ACCESSORIES_DIR = os.path.join(PROJECT_DIR, "avatars", "accessories")


def generate_all_accessories(output_dir: str = ACCESSORIES_DIR):
    os.makedirs(output_dir, exist_ok=True)
    # Remove the retired accessory so old installations cannot keep loading it.
    retired_cat_ears = os.path.join(output_dir, "cat_ears.png")
    if os.path.exists(retired_cat_ears):
        os.remove(retired_cat_ears)
    GW, GH = 64, 64
    SCALE = 9

    C_TRANS = (0, 0, 0, 0)
    C_OUTLINE = (28, 30, 42, 255)
    cx = 31

    def make_canvas():
        return Image.new("RGBA", (GW, GH), C_TRANS)

    def outline_and_scale(img, outline_color=C_OUTLINE):
        px = img.load()
        outlined = Image.new("RGBA", (GW, GH), C_TRANS)
        out_pix = outlined.load()
        for x in range(GW):
            for y in range(GH):
                if px[x, y][3] > 0:
                    out_pix[x, y] = px[x, y]
        for x in range(GW):
            for y in range(GH):
                if px[x, y][3] == 0:
                    for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                        nx, ny = x + dx, y + dy
                        if 0 <= nx < GW and 0 <= ny < GH and px[nx, ny][3] > 0:
                            out_pix[x, y] = outline_color
                            break
        return outlined.resize((GW * SCALE, GH * SCALE), Image.Resampling.NEAREST)

    # 1. RIBBON (Pita merah muda di samping kepala)
    def gen_ribbon():
        img = make_canvas()
        px = img.load()
        C_PINK = (255, 120, 160, 255)
        C_DARK_PINK = (215, 75, 120, 255)
        C_LIGHT_PINK = (255, 190, 215, 255)
        rx, ry = cx - 11, 13
        # Left loop
        for x in range(rx - 6, rx - 1):
            for y in range(ry - 4, ry + 3):
                px[x, y] = C_PINK
        px[rx - 5, ry - 3] = C_LIGHT_PINK
        px[rx - 6, ry + 2] = C_DARK_PINK
        # Right loop
        for x in range(rx + 2, rx + 7):
            for y in range(ry - 4, ry + 3):
                px[x, y] = C_PINK
        px[rx + 5, ry - 3] = C_LIGHT_PINK
        px[rx + 6, ry + 2] = C_DARK_PINK
        # Center knot
        for x in range(rx - 1, rx + 2):
            for y in range(ry - 2, ry + 2):
                px[x, y] = C_DARK_PINK
        px[rx, ry - 1] = C_LIGHT_PINK
        # Ribbon tails
        for y in range(ry + 2, ry + 8):
            px[rx - 3, y] = C_PINK
            px[rx - 2, y] = C_DARK_PINK
            px[rx + 1, y] = C_PINK
            px[rx + 2, y] = C_DARK_PINK
        return outline_and_scale(img)

    # 2. WITCH HAT (Topi penyihir kerucut)
    def gen_witch():
        img = make_canvas()
        px = img.load()
        C_PURPLE = (75, 50, 115, 255)
        C_DARK_PURPLE = (50, 32, 85, 255)
        C_LIGHT_PURPLE = (110, 80, 160, 255)
        C_GOLD = (255, 210, 60, 255)
        C_DARK_GOLD = (200, 150, 30, 255)
        # Wide brim
        for y in range(12, 16):
            w = 17 - (y - 12) * 2
            for x in range(cx - w, cx + w + 1):
                px[x, y] = C_PURPLE if x < cx + 4 else C_DARK_PURPLE
        # Gold belt
        for y in range(10, 12):
            for x in range(cx - 9, cx + 10):
                px[x, y] = C_GOLD if abs(x - cx) <= 2 else C_DARK_GOLD
        # Conical crown tapering up and tilting left
        widths = [9, 8, 7, 6, 5, 4, 3, 2, 2, 1]
        for idx, w in enumerate(widths):
            y = 9 - idx
            shift = int(idx * 0.45)
            for x in range(cx - w - shift, cx + w - shift + 1):
                px[x, y] = C_LIGHT_PURPLE if x == cx - w - shift else (C_PURPLE if x < cx - shift else C_DARK_PURPLE)
        px[cx - 5, 0] = C_PURPLE
        return outline_and_scale(img)

    # 3. CROWN (Mahkota emas raja)
    def gen_crown():
        img = make_canvas()
        px = img.load()
        C_GOLD = (255, 215, 65, 255)
        C_DARK_GOLD = (205, 155, 30, 255)
        C_LIGHT_GOLD = (255, 245, 140, 255)
        C_RUBY = (245, 45, 65, 255)
        C_SAPPHIRE = (45, 135, 255, 255)
        # Base band
        for y in range(6, 9):
            for x in range(cx - 9, cx + 10):
                px[x, y] = C_GOLD
                if y == 6:
                    px[x, y] = C_LIGHT_GOLD
                elif y == 8:
                    px[x, y] = C_DARK_GOLD
        # Jewels on band
        px[cx, 7] = C_RUBY
        px[cx - 5, 7] = C_SAPPHIRE
        px[cx + 5, 7] = C_SAPPHIRE
        # Peaks
        for y in range(2, 6):
            w = 5 - y
            for x in range(cx - 8 - w, cx - 8 + w + 1):
                px[x, y] = C_GOLD
            for x in range(cx + 8 - w, cx + 8 + w + 1):
                px[x, y] = C_GOLD
        px[cx - 8, 1] = C_RUBY
        px[cx + 8, 1] = C_RUBY
        # Center peak
        for y in range(1, 6):
            w = 5 - y
            for x in range(cx - w, cx + w + 1):
                px[x, y] = C_LIGHT_GOLD if x < cx else C_GOLD
        px[cx, 0] = C_RUBY
        return outline_and_scale(img)

    # 4. GLASSES (Kacamata hitam keren / Thug Life)
    def gen_glasses():
        img = make_canvas()
        px = img.load()
        C_BLACK = (20, 20, 28, 255)
        C_GRAY = (65, 65, 80, 255)
        C_WHITE = (255, 255, 255, 255)
        # Bridge
        for x in range(cx - 2, cx + 3):
            for y in range(21, 23):
                px[x, y] = C_BLACK
        # Left frame & lens
        for x in range(cx - 12, cx - 2):
            for y in range(20, 27):
                px[x, y] = C_BLACK
        for x in range(cx - 11, cx - 3):
            for y in range(21, 26):
                px[x, y] = C_GRAY
        px[cx - 10, 22] = C_WHITE
        px[cx - 9, 23] = C_WHITE
        px[cx - 8, 24] = C_WHITE

        # Right frame & lens
        for x in range(cx + 3, cx + 13):
            for y in range(20, 27):
                px[x, y] = C_BLACK
        for x in range(cx + 4, cx + 12):
            for y in range(21, 26):
                px[x, y] = C_GRAY
        px[cx + 5, 22] = C_WHITE
        px[cx + 6, 23] = C_WHITE
        px[cx + 7, 24] = C_WHITE

        # Temples
        for x in range(cx - 15, cx - 12):
            px[x, 21] = C_BLACK
        for x in range(cx + 13, cx + 16):
            px[x, 21] = C_BLACK
        return outline_and_scale(img)

    # 5. FLOWER (Bunga melati putih & kuning)
    def gen_flower():
        img = make_canvas()
        px = img.load()
        C_PETAL = (255, 252, 245, 255)
        C_PETAL_SHADOW = (225, 225, 238, 255)
        C_CENTER = (255, 215, 60, 255)
        C_LEAF = (90, 185, 95, 255)
        fx, fy = cx + 11, 13
        # Green leaf
        for x in range(fx + 2, fx + 7):
            for y in range(fy - 5, fy - 1):
                px[x, y] = C_LEAF
        # Petals
        for x in range(fx - 2, fx + 3):
            for y in range(fy - 6, fy - 1):
                px[x, y] = C_PETAL
            for y in range(fy + 2, fy + 7):
                px[x, y] = C_PETAL_SHADOW
        for x in range(fx - 6, fx - 1):
            for y in range(fy - 2, fy + 3):
                px[x, y] = C_PETAL
        for x in range(fx + 2, fx + 7):
            for y in range(fy - 2, fy + 3):
                px[x, y] = C_PETAL_SHADOW
        for x in range(fx - 1, fx + 2):
            for y in range(fy - 1, fy + 2):
                px[x, y] = C_CENTER
        return outline_and_scale(img)

    # 6. ANGEL HALO (Cincin malaikat ringan, terbuka, dan melayang)
    def gen_angel_halo():
        img = make_canvas()
        px = img.load()
        C_GOLD = (255, 220, 55, 255)
        C_LIGHT = (255, 248, 190, 255)
        C_AMBER = (225, 165, 25, 255)

        def row(y, left, right, color):
            for x in range(left, right + 1):
                px[x, y] = color

        # Thin stepped outer contour: wide enough to read above Ponyo,
        # but deliberately not a solid robot-like body.
        row(9, 27, 36, C_OUTLINE)
        row(10, 23, 40, C_OUTLINE)
        row(11, 18, 45, C_OUTLINE)
        for y in range(12, 14):
            row(y, 14, 49, C_OUTLINE)
        for y in range(14, 23):
            row(y, 9, 54, C_OUTLINE)
        for y in range(23, 25):
            row(y, 14, 49, C_OUTLINE)
        row(25, 18, 45, C_OUTLINE)
        row(26, 22, 41, C_OUTLINE)
        row(27, 26, 37, C_OUTLINE)
        row(28, 29, 34, C_OUTLINE)
        row(29, 27, 36, C_OUTLINE)

        # Cream-to-gold upper rim gives the halo a soft luminous edge.
        row(11, 23, 40, C_LIGHT)
        row(12, 18, 45, C_LIGHT)
        row(13, 15, 48, C_GOLD)
        for y in range(14, 16):
            row(y, 10, 53, C_GOLD)

        # Side shoulders remain visible while the middle is an open void.
        for y in range(16, 23):
            row(y, 10, 17, C_GOLD)
            row(y, 46, 53, C_GOLD)
            px[17, y] = C_OUTLINE
            px[46, y] = C_OUTLINE

        # Warm underside is a narrow ring band, not a filled lower body.
        row(23, 15, 48, C_GOLD)
        row(24, 15, 48, C_GOLD)
        row(25, 19, 44, C_AMBER)
        row(26, 23, 40, C_AMBER)
        row(27, 27, 36, C_AMBER)

        # Clear the large opening after outlining: final PNG alpha must be 0.
        ring = outline_and_scale(img)
        ring_px = ring.load()
        for base_x in range(18, 46):
            for base_y in range(16, 23):
                for dx in range(SCALE):
                    for dy in range(SCALE):
                        ring_px[base_x * SCALE + dx, base_y * SCALE + dy] = C_TRANS
        return ring

    # 7. DEVIL HORNS (Tanduk setan merah, melengkung ke dalam)
    def gen_devil_horns():
        img = make_canvas()
        px = img.load()
        C_RED = (225, 45, 55, 255)
        C_BRIGHT = (255, 95, 80, 255)
        C_MID = (190, 35, 48, 255)
        C_DARK = (115, 18, 32, 255)
        # Ujung berdiri vertikal di luar, lalu tiap tingkat turun dan
        # bergeser menuju tengah kepala: kiri ke kanan, kanan ke kiri.
        left_centers = [12, 12, 12, 12, 13, 14, 15, 16, 17, 18, 19, 20, 20, 20]
        right_centers = [50, 50, 50, 50, 49, 48, 47, 46, 45, 44, 43, 42, 42, 42]
        widths = [1, 1, 1, 1, 2, 2, 2, 3, 3, 3, 4, 4, 5, 5]
        for side, centers in ((-1, left_centers), (1, right_centers)):
            for y, (x_center, width) in enumerate(zip(centers, widths), start=3):
                for x in range(x_center - width, x_center + width + 1):
                    if 0 <= x < GW:
                        inner = (x - x_center) * side < 0
                        px[x, y] = C_RED if inner else (C_MID if y > 6 else C_DARK)
                highlight_x = x_center + side * max(0, width - 1)
                if 0 <= highlight_x < GW:
                    px[highlight_x, y] = C_BRIGHT
        return outline_and_scale(img)

    # 7. KNIGHT HELMET (Helm Ksatria Guardian Tales: 3 Celah Dahi, Sayap Pipi & Bulu Merah Melengkung)
    def gen_knight():
        img = make_canvas()
        px = img.load()

        C_WHITE = (255, 255, 255, 255)
        C_OFF_WHITE = (245, 242, 237, 255)
        C_SILVER = (208, 202, 195, 255)
        C_SLATE_SHADOW = (140, 129, 147, 255)
        C_DARK_INSET = (68, 58, 76, 255)
        C_GOLD = (217, 158, 65, 255)
        C_GOLD_DARK = (163, 109, 38, 255)

        C_PLUME_HIGH = (235, 67, 106, 255)
        C_PLUME_MID = (181, 30, 68, 255)
        C_PLUME_DARK = (84, 14, 34, 255)

        def set_px(x, y, col):
            if 0 <= x < GW and 0 <= y < GH:
                px[x, y] = col

        def fill_rect(x1, y1, x2, y2, col):
            for x in range(x1, x2 + 1):
                for y in range(y1, y2 + 1):
                    set_px(x, y, col)

        # 1. Bulu Plume Ksatria Merah (Crest melengkung ke kanan dengan rivet emas)
        fill_rect(cx - 1, 6, cx + 1, 7, C_DARK_INSET)
        set_px(cx, 6, C_GOLD)

        fill_rect(cx - 1, 4, cx + 1, 5, C_PLUME_MID)
        set_px(cx - 1, 4, C_PLUME_MID)
        set_px(cx + 1, 4, C_PLUME_HIGH)
        set_px(cx + 1, 5, C_PLUME_MID)

        plume_pixels = [
            # y = 0 (Puncak lengkungan bulu)
            (cx + 1, 0, C_PLUME_HIGH), (cx + 2, 0, C_PLUME_HIGH), (cx + 3, 0, C_PLUME_HIGH), (cx + 4, 0, C_PLUME_HIGH),
            # y = 1
            (cx, 1, C_PLUME_MID), (cx + 1, 1, C_PLUME_HIGH), (cx + 2, 1, C_PLUME_HIGH), (cx + 3, 1, C_PLUME_HIGH), (cx + 4, 1, C_PLUME_MID), (cx + 5, 1, C_PLUME_MID), (cx + 6, 1, C_PLUME_DARK),
            # y = 2
            (cx - 1, 2, C_PLUME_MID), (cx, 2, C_PLUME_MID), (cx + 1, 2, C_PLUME_HIGH), (cx + 2, 2, C_PLUME_HIGH), (cx + 3, 2, C_PLUME_MID), (cx + 4, 2, C_PLUME_MID), (cx + 5, 2, C_PLUME_MID), (cx + 6, 2, C_PLUME_DARK), (cx + 7, 2, C_PLUME_DARK),
            # y = 3
            (cx - 1, 3, C_PLUME_DARK), (cx, 3, C_PLUME_MID), (cx + 1, 3, C_PLUME_MID), (cx + 5, 3, C_PLUME_MID), (cx + 6, 3, C_PLUME_DARK), (cx + 7, 3, C_PLUME_DARK),
            # y = 4
            (cx + 5, 4, C_PLUME_MID), (cx + 6, 4, C_PLUME_DARK), (cx + 7, 4, C_PLUME_DARK),
            # y = 5
            (cx + 4, 5, C_PLUME_MID), (cx + 5, 5, C_PLUME_DARK), (cx + 6, 5, C_PLUME_DARK),
            # y = 6
            (cx + 4, 6, C_PLUME_DARK), (cx + 5, 6, C_PLUME_DARK)
        ]
        for x, y, col in plume_pixels:
            set_px(x, y, col)

        # Rivet Emas di tengah pusaran bulu
        set_px(cx + 3, 3, C_GOLD)
        set_px(cx + 4, 3, C_GOLD)
        set_px(cx + 3, 4, C_GOLD_DARK)
        set_px(cx + 4, 4, C_GOLD_DARK)

        # 2. Kubah Helm Baja Putih-Perak (Dome y = 8 to 14)
        dome_bands = [
            (8, 7),
            (9, 10),
            (10, 12),
            (11, 14),
            (12, 15),
            (13, 16),
            (14, 16)
        ]
        for y, w in dome_bands:
            for x in range(cx - w, cx + w + 1):
                if x < cx - (w * 0.5):
                    col = C_SLATE_SHADOW
                elif x < cx - 1:
                    col = C_SILVER
                elif x < cx + (w * 0.4):
                    col = C_WHITE if y <= 10 else C_OFF_WHITE
                else:
                    col = C_OFF_WHITE if x < cx + w - 1 else C_SILVER
                set_px(x, y, col)

        # 3. Plat Dahi / Brow Plate & 3 Celah Ventilasi Vertikal (y = 15 to 20)
        for y in range(15, 21):
            w = 16
            for x in range(cx - w, cx + w + 1):
                col = C_SLATE_SHADOW if x < cx - 8 else (C_OFF_WHITE if x < cx + 8 else C_SILVER)
                set_px(x, y, col)

        # Garis lis highlight bawah dahi (y = 20)
        for x in range(cx - 10, cx + 11):
            set_px(x, 20, C_WHITE)

        # Celah tengah (2 px lebar, 5 px tinggi: y = 15 to 19)
        fill_rect(cx - 1, 15, cx, 19, C_DARK_INSET)
        set_px(cx - 1, 15, C_SLATE_SHADOW)
        set_px(cx + 1, 16, C_WHITE)
        set_px(cx + 1, 17, C_WHITE)
        set_px(cx + 1, 18, C_WHITE)

        # Celah kiri (2 px lebar, 4 px tinggi: y = 16 to 19)
        fill_rect(cx - 6, 16, cx - 5, 19, C_DARK_INSET)
        set_px(cx - 6, 16, C_SLATE_SHADOW)
        set_px(cx - 4, 17, C_WHITE)
        set_px(cx - 4, 18, C_WHITE)

        # Celah kanan (2 px lebar, 4 px tinggi: y = 16 to 19)
        fill_rect(cx + 4, 16, cx + 5, 19, C_DARK_INSET)
        set_px(cx + 4, 16, C_SLATE_SHADOW)
        set_px(cx + 6, 17, C_WHITE)
        set_px(cx + 6, 18, C_WHITE)

        # 4. Pelindung Pipi & Kuping Samping (Cheek Guards y = 21 to 30)
        # Sisi kiri (x = cx - 16 to cx - 11)
        for y in range(21, 31):
            lx_start = cx - 17 if 21 <= y <= 24 else cx - 16
            for x in range(lx_start, cx - 10):
                if x <= cx - 15:
                    col = C_SLATE_SHADOW
                elif x <= cx - 13:
                    col = C_SILVER
                else:
                    col = C_OFF_WHITE
                set_px(x, y, col)

        # Inset kuping kiri
        set_px(cx - 16, 22, C_DARK_INSET)
        set_px(cx - 15, 22, C_DARK_INSET)
        set_px(cx - 16, 23, C_DARK_INSET)
        set_px(cx - 15, 23, C_DARK_INSET)

        for x in range(cx - 16, cx - 10):
            set_px(x, 30, C_SLATE_SHADOW)

        # Sisi kanan (x = cx + 11 to cx + 16)
        for y in range(21, 31):
            rx_end = cx + 17 if 21 <= y <= 24 else cx + 16
            for x in range(cx + 11, rx_end + 1):
                if x == cx + 11:
                    col = C_WHITE
                elif x <= cx + 13:
                    col = C_OFF_WHITE
                elif x <= cx + 15:
                    col = C_SILVER
                else:
                    col = C_SLATE_SHADOW
                set_px(x, y, col)

        # Inset kuping kanan
        set_px(cx + 15, 22, C_DARK_INSET)
        set_px(cx + 16, 22, C_DARK_INSET)
        set_px(cx + 15, 23, C_DARK_INSET)
        set_px(cx + 16, 23, C_DARK_INSET)

        for x in range(cx + 11, cx + 14):
            set_px(x, 30, C_SILVER)
        for x in range(cx + 14, cx + 17):
            set_px(x, 30, C_SLATE_SHADOW)

        return outline_and_scale(img)

    items = {
        "ribbon": gen_ribbon(),
        "witch": gen_witch(),
        "crown": gen_crown(),
        "glasses": gen_glasses(),
        "flower": gen_flower(),
        "angel_halo": gen_angel_halo(),
        "devil_horns": gen_devil_horns(),
        "knight": gen_knight()
    }

    for name, s_img in items.items():
        p = os.path.join(output_dir, f"{name}.png")
        s_img.save(p, "PNG")
        print(f"[ACCESSORY] Dibuat: {p}")


if __name__ == "__main__":
    generate_all_accessories()

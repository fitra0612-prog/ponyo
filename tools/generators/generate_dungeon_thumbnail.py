"""
generate_dungeon_thumbnail.py - Generator Thumbnail YouTube Resolusi Tinggi (1280x720)
untuk Game DUNGEON SLASHER dengan Karakter PONYO KNIGHT (Ponyo si Hantu Imut memakai Helm Knight).
Versi 2: Pedang Ksatria Terangkat Heroik, Shading Obor Sinematik, & Integrasi Bebas Ghosting.
"""

import os
import math
import random
from PIL import Image, ImageDraw, ImageFilter, ImageEnhance, ImageFont


PROJECT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
THUMBNAIL_DIR = os.path.join(PROJECT_DIR, "assets", "thumbnails")
DUNGEON_ASSET_DIR = os.path.join(PROJECT_DIR, "assets", "dungeon")
os.makedirs(THUMBNAIL_DIR, exist_ok=True)


def create_dungeon_slasher_ponyo_thumbnail(output_path: str | None = None):
    output_path = output_path or os.path.join(THUMBNAIL_DIR, "thumbnail_dungeon_slasher_ponyo.png")
    TW, TH = 1280, 720
    # Render pada skala 2x (2560x1440) untuk hasil super-sampling yang halus, tajam, dan bebas jagged edge
    SW, SH = TW * 2, TH * 2

    # 1. Muat Background Original Dungeon Slasher
    orig_header_path = os.path.join(DUNGEON_ASSET_DIR, "user_header.jpg")
    if not os.path.exists(orig_header_path):
        raise FileNotFoundError(f"File {orig_header_path} tidak ditemukan!")

    base_orig = Image.open(orig_header_path).convert("RGBA")
    bw, bh = base_orig.size

    # Skala background agar menutupi seluruh kanvas 2560x1440
    scale = SH / bh
    scaled_w = int(bw * scale)
    scaled_h = SH
    bg_scaled = base_orig.resize((scaled_w, scaled_h), Image.Resampling.LANCZOS)

    # Crop center ke 2560x1440
    crop_x = (scaled_w - SW) // 2
    canvas = bg_scaled.crop((crop_x, 0, crop_x + SW, SH))

    # Tingkatkan kontras dan kejernihan dungeon agar pencahayaan lebih sinematik
    enhancer = ImageEnhance.Contrast(canvas)
    canvas = enhancer.enhance(1.18)
    color_enhancer = ImageEnhance.Color(canvas)
    canvas = color_enhancer.enhance(1.10)

    # Transformasi koordinat dari sistem 1280x720 ke 2560x1440 (skala 2.0)
    def s(val):
        return int(val * 2)

    def pt(x, y):
        return (int(x * 2), int(y * 2))

    def pts(coord_list):
        return [(int(x * 2), int(y * 2)) for x, y in coord_list]

    # Palet Warna Karakter Ksatria Ponyo
    C_OUTLINE = (24, 26, 38, 255)
    C_OUTLINE_SOFT = (45, 48, 68, 255)

    C_STEEL_DARK = (75, 85, 110, 255)
    C_STEEL_MID = (155, 172, 198, 255)
    C_STEEL_LIGHT = (215, 230, 248, 255)
    C_STEEL_HIGH = (252, 254, 255, 255)
    C_STEEL_TORCH = (255, 215, 160, 255)

    C_GOLD_DARK = (145, 90, 20, 255)
    C_GOLD_MID = (235, 175, 45, 255)
    C_GOLD_LIGHT = (255, 235, 120, 255)

    C_CAPE_DARK = (105, 16, 28, 255)
    C_CAPE_MID = (185, 28, 45, 255)
    C_CAPE_LIGHT = (235, 55, 75, 255)
    C_CAPE_TORCH = (255, 110, 80, 255)

    C_GHOST_WHITE = (255, 255, 255, 255)
    C_GHOST_SHADOW_COOL = (195, 210, 235, 255)
    C_GHOST_WARM_HIGHLIGHT = (255, 242, 215, 255)
    C_BLUSH = (255, 110, 145, 235)
    C_EYE = (24, 24, 36, 255)

    C_FIRE_CORE = (255, 255, 245, 255)
    C_FIRE_YELLOW = (255, 230, 60, 255)
    C_FIRE_ORANGE = (255, 125, 20, 255)
    C_FIRE_RED = (215, 35, 18, 255)

    # -------------------------------------------------------------
    # 2. LAYER PONYO KNIGHT
    # -------------------------------------------------------------
    ponyo_layer = Image.new("RGBA", (SW, SH), (0, 0, 0, 0))
    pdraw = ImageDraw.Draw(ponyo_layer)

    # A. GAMBAR BILLOWING CRIMSON CAPE (Jubah Merah Berkibar di Belakang)
    cape_poly = pts([
        (550, 520), (595, 525), (650, 520), (700, 510),
        (750, 530), (790, 570), (820, 630), (825, 680),
        (805, 715), (770, 700), (760, 680), (730, 695),
        (710, 675), (680, 685), (660, 665), (640, 670),
        (610, 650), (580, 660), (550, 630), (540, 560)
    ])
    pdraw.polygon(cape_poly, fill=C_CAPE_MID)

    # Lipatan gelap jubah
    cape_shadow_poly = pts([
        (650, 530), (730, 540), (780, 580), (810, 640),
        (815, 690), (770, 700), (745, 660), (715, 640),
        (680, 620), (650, 580)
    ])
    pdraw.polygon(cape_shadow_poly, fill=C_CAPE_DARK)

    # Highlight jubah terkena pantulan hangat obor api
    pdraw.polygon(pts([
        (700, 515), (750, 535), (785, 575), (770, 595),
        (735, 565), (695, 535)
    ]), fill=C_CAPE_TORCH)

    pdraw.line(cape_poly + [cape_poly[0]], fill=C_OUTLINE, width=s(5))

    # B. BADAN HANTU PONYO (Floating Ghost Body dengan Shading Sinematik)
    cx, cy = 600, 550
    ghost_pts = []
    # Kubah kepala & torso
    for deg in range(180, 361, 5):
        rad = math.radians(deg)
        gx = cx + math.cos(rad) * 115
        gy = 450 + math.sin(rad) * 110
        ghost_pts.append((gx, gy))

    # Badan kanan mengembang ke arah kawan
    ghost_pts.extend([
        (715, 500), (720, 560), (715, 620), (710, 665)
    ])
    # Scalloped hem bawah bergelombang lembut
    scallops = [
        (695, 685), (680, 660), (660, 688), (640, 665),
        (620, 692), (600, 668), (580, 695), (560, 665),
        (540, 690), (520, 665), (500, 685), (488, 660)
    ]
    ghost_pts.extend(scallops)
    # Badan kiri
    ghost_pts.extend([
        (485, 620), (480, 560), (485, 500)
    ])

    ghost_poly = pts(ghost_pts)
    pdraw.polygon(ghost_poly, fill=C_GHOST_WHITE)

    # Shading dingin pada sisi kiri tubuh hantu (menjauhi obor)
    shadow_cool_pts = pts([
        (485, 500), (480, 560), (485, 620), (488, 660),
        (500, 685), (520, 665), (540, 690), (550, 640),
        (535, 580), (520, 530), (510, 480)
    ])
    pdraw.polygon(shadow_cool_pts, fill=C_GHOST_SHADOW_COOL)

    # Shading hangat di sisi kanan terkena langsung cahaya obor api yang berkobar
    shadow_warm_pts = pts([
        (665, 475), (690, 525), (715, 560), (715, 620),
        (710, 665), (695, 685), (675, 650), (670, 580),
        (660, 525)
    ])
    pdraw.polygon(shadow_warm_pts, fill=C_GHOST_WARM_HIGHLIGHT)

    # Outline tegas badan hantu
    pdraw.line(ghost_poly + [ghost_poly[0]], fill=C_OUTLINE, width=s(5))

    # C. ARMOR CUIRASS & GORGET DI BADAN PONYO
    cuirass_pts = pts([
        (530, 535), (600, 545), (670, 535),
        (665, 585), (640, 625), (600, 640),
        (560, 625), (535, 585)
    ])
    pdraw.polygon(cuirass_pts, fill=C_STEEL_MID)

    # Shading gelap sisi kiri plat dada
    pdraw.polygon(pts([
        (530, 535), (565, 540), (560, 625), (535, 585)
    ]), fill=C_STEEL_DARK)

    # Highlight emas/api sisi kanan plat dada
    pdraw.polygon(pts([
        (600, 545), (670, 535), (665, 585), (640, 625),
        (630, 580), (615, 550)
    ]), fill=C_STEEL_TORCH)

    pdraw.line(cuirass_pts + [cuirass_pts[0]], fill=C_OUTLINE, width=s(4))

    # Lis Emas Baju Besi
    pdraw.line(pts([(530, 535), (600, 545), (670, 535)]), fill=C_GOLD_MID, width=s(4))
    pdraw.line(pts([(560, 625), (600, 640), (640, 625)]), fill=C_GOLD_MID, width=s(4))

    # Lambang Bintang Emas Ksatria di Dada
    star_cx, star_cy = 600, 585
    star_pts = pts([
        (star_cx, star_cy - 16), (star_cx + 5, star_cy - 5),
        (star_cx + 16, star_cy), (star_cx + 5, star_cy + 5),
        (star_cx, star_cy + 16), (star_cx - 5, star_cy + 5),
        (star_cx - 16, star_cy), (star_cx - 5, star_cy - 5)
    ])
    pdraw.polygon(star_pts, fill=C_GOLD_LIGHT)
    pdraw.line(star_pts + [star_pts[0]], fill=C_GOLD_DARK, width=s(2))

    # D. WAJAH IMUT PONYO (Expressive Cute Face)
    eye_y = 475
    left_eye_x = 560
    right_eye_x = 640
    eye_w, eye_h = 16, 22

    for ex in [left_eye_x, right_eye_x]:
        eye_box = [s(ex - eye_w), s(eye_y - eye_h), s(ex + eye_w), s(eye_y + eye_h)]
        pdraw.ellipse(eye_box, fill=C_EYE)
        # Kilau mata besar (Catchlight)
        pdraw.ellipse([s(ex - 8), s(eye_y - 15), s(ex + 4), s(eye_y - 3)], fill=(255, 255, 255, 255))
        # Kilau mata kecil bawah
        pdraw.ellipse([s(ex + 2), s(eye_y + 6), s(ex + 8), s(eye_y + 12)], fill=(255, 255, 255, 255))

    # Pipi merona merah muda (Rosy Blush)
    pdraw.ellipse([s(left_eye_x - 32), s(eye_y + 12), s(left_eye_x + 2), s(eye_y + 26)], fill=C_BLUSH)
    pdraw.ellipse([s(right_eye_x - 2), s(eye_y + 12), s(right_eye_x + 32), s(eye_y + 26)], fill=C_BLUSH)
    for lx in [left_eye_x - 20, left_eye_x - 12, left_eye_x - 4]:
        pdraw.line([pt(lx, eye_y + 14), pt(lx + 4, eye_y + 24)], fill=(255, 75, 120, 200), width=s(2))
    for rx in [right_eye_x + 4, right_eye_x + 12, right_eye_x + 20]:
        pdraw.line([pt(rx, eye_y + 14), pt(rx + 4, eye_y + 24)], fill=(255, 75, 120, 200), width=s(2))

    # Mulut tersenyum ceria penuh semangat petualang
    mouth_pts = pts([
        (582, 502), (600, 518), (618, 502)
    ])
    pdraw.polygon(mouth_pts, fill=(150, 25, 45, 255))
    pdraw.polygon(pts([(588, 512), (600, 518), (612, 512)]), fill=(255, 130, 160, 255))
    pdraw.line(mouth_pts + [mouth_pts[0]], fill=C_OUTLINE, width=s(3))

    # E. HELM KNIGHT GUARDIAN TALES (3 Celah Ventilasi Dahi, Pelindung Pipi, & Bulu Plume Merah)
    helm_poly = pts([
        (515, 435), (525, 385), (555, 350), (600, 335),
        (645, 350), (675, 385), (685, 435),
        # Pelindung pipi kanan turun membingkai wajah
        (688, 480), (682, 530), (655, 530), (658, 465),
        # Lengkungan dahi tengah
        (600, 452),
        # Pelindung pipi kiri
        (542, 465), (545, 530), (518, 530), (512, 480)
    ])
    pdraw.polygon(helm_poly, fill=C_STEEL_MID)

    # Shading sisi kiri helm & pelindung pipi kiri
    helm_shadow = pts([
        (515, 435), (525, 385), (555, 350), (580, 340),
        (560, 420), (542, 465), (545, 530), (518, 530), (512, 480)
    ])
    pdraw.polygon(helm_shadow, fill=C_STEEL_DARK)

    # Highlight pantulan cahaya obor di sisi kanan kubah & pelindung pipi kanan
    helm_high = pts([
        (600, 335), (645, 350), (675, 385), (685, 435),
        (688, 480), (682, 530), (665, 530), (670, 460),
        (650, 400), (615, 345)
    ])
    pdraw.polygon(helm_high, fill=C_STEEL_TORCH)

    pdraw.line(helm_poly + [helm_poly[0]], fill=C_OUTLINE, width=s(5))

    # 3 Celah Ventilasi Vertikal Khas di Dahi (Signature Inset Slots)
    # Celah Tengah
    center_slot = pts([(594, 380), (606, 380), (606, 432), (594, 432)])
    pdraw.polygon(center_slot, fill=(50, 45, 62, 255))
    pdraw.line(center_slot + [center_slot[0]], fill=C_OUTLINE, width=s(2))

    # Celah Kiri
    left_slot = pts([(562, 390), (573, 390), (573, 430), (562, 430)])
    pdraw.polygon(left_slot, fill=(50, 45, 62, 255))
    pdraw.line(left_slot + [left_slot[0]], fill=C_OUTLINE, width=s(2))

    # Celah Kanan
    right_slot = pts([(627, 390), (638, 390), (638, 430), (627, 430)])
    pdraw.polygon(right_slot, fill=(50, 45, 62, 255))
    pdraw.line(right_slot + [right_slot[0]], fill=C_OUTLINE, width=s(2))

    # Baut Inset Kuping Kiri & Kanan
    pdraw.rectangle([s(516), s(450), s(526), s(462)], fill=(50, 45, 62, 255), outline=C_OUTLINE, width=s(2))
    pdraw.rectangle([s(674), s(450), s(684), s(462)], fill=(50, 45, 62, 255), outline=C_OUTLINE, width=s(2))

    # Socket Emas Pengikat Bulu di Puncak Kubah Helm
    socket_pts = pts([(592, 336), (608, 336), (612, 324), (588, 324)])
    pdraw.polygon(socket_pts, fill=C_GOLD_MID)
    pdraw.line(socket_pts + [socket_pts[0]], fill=C_OUTLINE, width=s(3))

    # Bulu Plume Ksatria Merah Melengkung ke Kanan (Curved Red Plume Feather)
    plume_poly = pts([
        (595, 325), (585, 290), (575, 250), (585, 220),
        (615, 205), (655, 215), (680, 245), (675, 280),
        (650, 305), (635, 295), (655, 275), (655, 245),
        (635, 230), (605, 240), (595, 265), (605, 325)
    ])
    pdraw.polygon(plume_poly, fill=C_CAPE_MID)
    pdraw.polygon(pts([
        (595, 325), (585, 290), (575, 250), (585, 220), (600, 250), (605, 325)
    ]), fill=C_CAPE_DARK)
    pdraw.polygon(pts([
        (615, 205), (655, 215), (680, 245), (665, 245), (635, 230)
    ]), fill=C_CAPE_LIGHT)
    pdraw.line(plume_poly + [plume_poly[0]], fill=C_OUTLINE, width=s(4))

    # Rivet Emas di Tengah Lengkungan Bulu
    pdraw.ellipse([s(630), s(255), s(646), s(271)], fill=C_GOLD_LIGHT, outline=C_OUTLINE, width=s(2))

    # F. PEDANG KSATRIA TERANGKAT HEROIK (Heroic Slashing Arming Sword)
    arm_sword_poly = pts([
        (535, 545), (490, 525), (460, 495),
        (480, 475), (515, 505), (550, 530)
    ])
    pdraw.polygon(arm_sword_poly, fill=C_STEEL_MID)
    pdraw.line(arm_sword_poly + [arm_sword_poly[0]], fill=C_OUTLINE, width=s(4))

    # Sarung tangan besi menggenggam gagang pedang
    pdraw.ellipse([s(455), s(475), s(485), s(505)], fill=C_STEEL_LIGHT, outline=C_OUTLINE, width=s(3))

    # Crossguard Emas Pedang
    sword_guard = pts([
        (435, 480), (475, 520), (488, 508), (448, 468)
    ])
    pdraw.polygon(sword_guard, fill=C_GOLD_MID)
    pdraw.line(sword_guard + [sword_guard[0]], fill=C_OUTLINE, width=s(3))

    # Gagang & Pommel Emas
    pdraw.line([pt(470, 510), pt(495, 535)], fill=(120, 70, 30, 255), width=s(6))
    pdraw.ellipse([s(490), s(530), s(506), s(546)], fill=C_GOLD_LIGHT, outline=C_OUTLINE, width=s(2))

    # Bilah Pedang Baja Tajam Terangkat Heroik ke Kiri Atas (X=440, Y=470 -> X=340, Y=345)
    blade_poly = pts([
        (440, 470), (455, 485),
        (355, 365), (340, 345), (345, 360)
    ])
    pdraw.polygon(blade_poly, fill=C_STEEL_HIGH)
    pdraw.polygon(pts([(440, 470), (448, 478), (350, 360), (340, 345)]), fill=C_STEEL_LIGHT)
    # Garis tengah bilah pedang (Fuller)
    pdraw.line([pt(448, 478), pt(340, 345)], fill=(120, 135, 160, 255), width=s(2))
    pdraw.line(blade_poly + [blade_poly[0]], fill=C_OUTLINE, width=s(4))

    # Kilau cahaya tajam pada ujung pedang (Sword Gleam Flare)
    gleam_cx, gleam_cy = 340, 345
    pdraw.line([pt(gleam_cx - 15, gleam_cy), pt(gleam_cx + 15, gleam_cy)], fill=(255, 255, 255, 240), width=s(3))
    pdraw.line([pt(gleam_cx, gleam_cy - 15), pt(gleam_cx, gleam_cy + 15)], fill=(255, 255, 255, 240), width=s(3))
    pdraw.ellipse([s(gleam_cx - 5), s(gleam_cy - 5), s(gleam_cx + 5), s(gleam_cy + 5)], fill=(255, 255, 255, 255))

    # G. TANGAN KIRI TERANGKAT MENJUNJUNG OBOR API MEMBARA (Torch & Flame)
    arm_left_poly = pts([
        (665, 545), (705, 510), (730, 460),
        (755, 475), (725, 535), (680, 570)
    ])
    pdraw.polygon(arm_left_poly, fill=C_STEEL_LIGHT)
    pdraw.line(arm_left_poly + [arm_left_poly[0]], fill=C_OUTLINE, width=s(4))

    # Gagang Kayu Obor
    torch_wood = pts([
        (720, 480), (735, 488), (750, 360), (732, 355)
    ])
    pdraw.polygon(torch_wood, fill=(115, 65, 35, 255))
    pdraw.line(torch_wood + [torch_wood[0]], fill=C_OUTLINE, width=s(3))

    # Sarung Tangan Besi Kiri Menggenggam Obor
    pdraw.ellipse([s(718), s(450), s(748), s(480)], fill=C_STEEL_HIGH, outline=C_OUTLINE, width=s(3))

    # Kepala Logam Pengikat Obor
    torch_head = pts([
        (725, 360), (758, 365), (762, 342), (722, 338)
    ])
    pdraw.polygon(torch_head, fill=(70, 70, 80, 255))
    pdraw.line(torch_head + [torch_head[0]], fill=C_OUTLINE, width=s(3))

    # KOROBAN API OBOR YANG BERKOBAR DAHSYAT (Blazing Fire)
    flame_outer = pts([
        (720, 345), (690, 310), (675, 260), (710, 275),
        (700, 220), (735, 245), (750, 195), (770, 235),
        (800, 220), (790, 270), (820, 285), (795, 325),
        (765, 350)
    ])
    pdraw.polygon(flame_outer, fill=C_FIRE_RED)

    flame_mid = pts([
        (728, 342), (705, 315), (695, 280), (722, 290),
        (715, 245), (742, 265), (755, 225), (772, 255),
        (788, 250), (780, 285), (802, 298), (785, 328),
        (758, 346)
    ])
    pdraw.polygon(flame_mid, fill=C_FIRE_ORANGE)

    flame_inner = pts([
        (733, 340), (718, 318), (715, 295), (732, 302),
        (730, 265), (748, 282), (758, 250), (770, 275),
        (778, 272), (772, 298), (788, 308), (775, 330),
        (752, 342)
    ])
    pdraw.polygon(flame_inner, fill=C_FIRE_YELLOW)

    flame_core = pts([
        (738, 338), (730, 315), (742, 305), (745, 280),
        (755, 295), (762, 275), (768, 300), (765, 325),
        (748, 338)
    ])
    pdraw.polygon(flame_core, fill=C_FIRE_CORE)

    # -------------------------------------------------------------
    # 3. DROP SHADOW DI BELAKANG PONYO UNTUK MEMADUKAN ART
    # -------------------------------------------------------------
    ponyo_alpha = ponyo_layer.split()[3]
    shadow_img = Image.new("RGBA", (SW, SH), (10, 12, 20, 180))
    shadow_img.putalpha(ponyo_alpha)
    shadow_blurred = shadow_img.filter(ImageFilter.GaussianBlur(radius=s(14)))

    # Tempel bayangan ke kanvas terlebih dahulu
    canvas.alpha_composite(shadow_blurred)
    # Tempel Ponyo Knight di atas bayangan
    canvas.alpha_composite(ponyo_layer)

    # -------------------------------------------------------------
    # 4. LIGHTING DINAMIS OBOR PADA DUNGEON & KARAKTER
    # -------------------------------------------------------------
    glow_layer = Image.new("RGBA", (SW, SH), (0, 0, 0, 0))
    gdraw = ImageDraw.Draw(glow_layer)

    torch_fx, torch_fy = s(750), s(270)
    for radius, alpha, col in [
        (s(580), 30, (255, 110, 20)),
        (s(400), 50, (255, 140, 30)),
        (s(260), 75, (255, 185, 45)),
        (s(150), 110, (255, 220, 80)),
        (s(70), 160, (255, 255, 180))
    ]:
        bbox = [torch_fx - radius, torch_fy - radius, torch_fx + radius, torch_fy + radius]
        gdraw.ellipse(bbox, fill=(*col, alpha))

    glow_blurred = glow_layer.filter(ImageFilter.GaussianBlur(radius=s(18)))
    canvas = Image.alpha_composite(canvas, glow_blurred)

    # PERCIKAN BARA API MELAYANG (Flying Embers)
    ember_layer = Image.new("RGBA", (SW, SH), (0, 0, 0, 0))
    edraw = ImageDraw.Draw(ember_layer)
    random.seed(42)
    for _ in range(45):
        ex = s(random.randint(620, 920))
        ey = s(random.randint(80, 380))
        er = s(random.randint(2, 6))
        ecol = random.choice([
            (255, 240, 150, 240),
            (255, 180, 50, 230),
            (255, 100, 30, 210),
            (255, 220, 80, 255)
        ])
        edraw.ellipse([ex - er, ey - er, ex + er, ey + er], fill=ecol)

    canvas = Image.alpha_composite(canvas, ember_layer)

    # -------------------------------------------------------------
    # 5. PILL BADGE YOUTUBE RESMI & MINIMALIS DI SUDUT KIRI BAWAH
    # -------------------------------------------------------------
    badge_layer = Image.new("RGBA", (SW, SH), (0, 0, 0, 0))
    bdraw = ImageDraw.Draw(badge_layer)

    try:
        font_badge = ImageFont.truetype("impact.ttf", s(36))
        font_sub = ImageFont.truetype("arialbd.ttf", s(20))
    except Exception:
        font_badge = ImageFont.load_default()
        font_sub = font_badge

    badge_txt = "PONYO GHOST KNIGHT!"
    sub_txt = "DUNGEON CRAWLER LIVE STREAM"

    # Posisikan flush di sudut kiri bawah sehingga sama sekali tidak menutup karakter atau pedang
    bx, by = s(30), s(628)
    bw_box = s(380)
    bh_box = s(72)

    # Bayangan kotak badge
    bdraw.rounded_rectangle([bx + s(4), by + s(4), bx + bw_box + s(4), by + bh_box + s(4)], radius=s(12), fill=(10, 12, 20, 210))
    # Badan badge gelap dengan lis emas menyala
    bdraw.rounded_rectangle([bx, by, bx + bw_box, by + bh_box], radius=s(12), fill=(18, 20, 32, 235), outline=(255, 180, 50, 255), width=s(3))

    bdraw.text((bx + s(18), by + s(8)), sub_txt, font=font_sub, fill=(255, 205, 80, 255))
    bdraw.text((bx + s(18), by + s(32)), badge_txt, font=font_badge, fill=(255, 255, 255, 255))

    canvas = Image.alpha_composite(canvas, badge_layer)

    # -------------------------------------------------------------
    # 6. DOWNSAMPLE SUPER-SAMPLING KE RESOLUSI STANDAR 1280x720
    # -------------------------------------------------------------
    final_thumbnail = canvas.resize((TW, TH), Image.Resampling.LANCZOS)
    final_thumbnail.save(output_path, "PNG", quality=95)
    print(f"✅ Thumbnail berhasil dibuat: {output_path} (Ukuran: {TW}x{TH})")
    return output_path


if __name__ == "__main__":
    create_dungeon_slasher_ponyo_thumbnail()

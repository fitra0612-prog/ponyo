"""
YOUTUBE LIVE STREAM THUMBNAIL GENERATOR
=======================================
Menghasilkan thumbnail berkualitas tinggi 1280x720 (16:9 Standard YouTube)
untuk live streaming Slither.io interaktif bersama VTuber Ponyo.
"""

import os
import math
import random
from PIL import Image, ImageDraw, ImageFont, ImageFilter

PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(PROJECT_DIR, "assets", "thumbnails")
os.makedirs(OUTPUT_DIR, exist_ok=True)
OUTPUT_PATH = os.path.join(OUTPUT_DIR, "thumbnail_slither_live.png")
AVATAR_PATH = os.path.join(PROJECT_DIR, "avatars", "open.png")

W, H = 1280, 720

def draw_hex(draw, x, y, r, outline_color):
    points = []
    for i in range(6):
        angle_deg = 60 * i - 30
        angle_rad = math.pi / 180 * angle_deg
        points.append((x + r * math.cos(angle_rad), y + r * math.sin(angle_rad)))
    draw.polygon(points, outline=outline_color)

def create_glowing_pellets(draw_glow, draw_core, x, y, radius, color_rgb):
    # Glow layer
    draw_glow.ellipse([x - radius * 2.2, y - radius * 2.2, x + radius * 2.2, y + radius * 2.2], fill=(*color_rgb, 140))
    # Core layer
    draw_core.ellipse([x - radius, y - radius, x + radius, y + radius], fill=(*color_rgb, 255))
    # Specular white highlight
    draw_core.ellipse([x - radius * 0.5, y - radius * 0.5, x, y], fill=(255, 255, 255, 220))

def draw_lightning_icon(d, x, y, size=20, color=(255, 255, 255, 255)):
    pts = [
        (x + size * 0.52, y),
        (x + size * 0.12, y + size * 0.55),
        (x + size * 0.48, y + size * 0.55),
        (x + size * 0.38, y + size),
        (x + size * 0.92, y + size * 0.38),
        (x + size * 0.56, y + size * 0.38),
    ]
    d.polygon(pts, fill=color)

def draw_arrow_icon(d, x, y, size=16, direction="LEFT", color=(15, 25, 40, 255)):
    if direction == "LEFT":
        pts = [(x, y + size * 0.5), (x + size * 0.65, y), (x + size * 0.65, y + size)]
        d.polygon(pts, fill=color)
        d.rectangle([x + size * 0.6, y + size * 0.3, x + size, y + size * 0.7], fill=color)
    else: # RIGHT
        pts = [(x + size, y + size * 0.5), (x + size * 0.35, y), (x + size * 0.35, y + size)]
        d.polygon(pts, fill=color)
        d.rectangle([x, y + size * 0.3, x + size * 0.4, y + size * 0.7], fill=color)

def draw_spiral_icon(d, x, y, size=18, color=(15, 25, 40, 255)):
    r = size // 2
    cx, cy = x + r, y + r
    d.ellipse([cx - r, cy - r, cx + r, cy + r], outline=color, width=3)
    d.polygon([(cx + r + 3, cy - 2), (cx + r - 5, cy - 2), (cx + r - 1, cy - 8)], fill=color)

def draw_trophy_icon(d, x, y, size=24, color=(255, 220, 0, 255)):
    d.polygon([
        (x + size * 0.18, y), 
        (x + size * 0.82, y), 
        (x + size * 0.66, y + size * 0.58), 
        (x + size * 0.34, y + size * 0.58)
    ], fill=color)
    d.rectangle([x + size * 0.42, y + size * 0.58, x + size * 0.58, y + size * 0.82], fill=color)
    d.rectangle([x + size * 0.22, y + size * 0.82, x + size * 0.78, y + size], fill=color)

def generate_thumbnail():
    # 1. Base Canvas & Radial Gradient
    base = Image.new("RGBA", (W, H), (10, 12, 24, 255))
    draw_base = ImageDraw.Draw(base)

    # Gradient fill from center to edges
    for r in range(int(math.hypot(W, H) / 2), 0, -10):
        t = r / (math.hypot(W, H) / 2)
        # Deep dark blue to rich purple-navy
        cr = int(14 + (1 - t) * 22)
        cg = int(16 + (1 - t) * 32)
        cb = int(32 + (1 - t) * 65)
        draw_base.ellipse([(W//2 - r, H//2 - r), (W//2 + r, H//2 + r)], fill=(cr, cg, cb, 255))

    # 2. Hexagonal Arena Grid (Slither.io Arena Map)
    grid_img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    grid_draw = ImageDraw.Draw(grid_img)
    hex_size = 38
    dx = hex_size * math.sqrt(3)
    dy = hex_size * 1.5

    col_idx = 0
    y = 0
    while y < H + hex_size:
        x = 0 if (col_idx % 2 == 0) else dx / 2
        while x < W + hex_size:
            draw_hex(grid_draw, x, y, hex_size, (60, 90, 160, 38))
            x += dx
        y += dy
        col_idx += 1

    base.alpha_composite(grid_img)

    # 3. Glowing Food Pellets (Scatter in arena)
    glow_pellets = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    core_pellets = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    draw_gp = ImageDraw.Draw(glow_pellets)
    draw_cp = ImageDraw.Draw(core_pellets)

    colors = [
        (0, 255, 230),   # Cyan
        (255, 60, 180),  # Neon Pink
        (255, 220, 0),   # Bright Gold
        (50, 255, 80),   # Lime Green
        (255, 110, 20),  # Orange
        (170, 70, 255)   # Purple
    ]

    random.seed(42)
    for _ in range(85):
        px = random.randint(30, W - 30)
        py = random.randint(30, H - 30)
        pr = random.randint(5, 16)
        c = random.choice(colors)
        create_glowing_pellets(draw_gp, draw_cp, px, py, pr, c)

    # Exploding snake burst on the left
    burst_cx, burst_cy = 320, 480
    for _ in range(40):
        ang = random.uniform(0, math.pi * 2)
        dist = random.uniform(20, 190)
        px = burst_cx + dist * math.cos(ang)
        py = burst_cy + dist * math.sin(ang)
        pr = random.randint(8, 22)
        c = random.choice([(255, 230, 40), (255, 80, 20), (0, 255, 200), (255, 40, 160)])
        create_glowing_pellets(draw_gp, draw_cp, px, py, pr, c)

    # Blur glow layer and merge
    blurred_glow = glow_pellets.filter(ImageFilter.GaussianBlur(14))
    base.alpha_composite(blurred_glow)
    base.alpha_composite(core_pellets)

    # 4. Giant Glowing Slither Snake Body
    snake_layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    snake_draw = ImageDraw.Draw(snake_layer)

    # Curve points for a winding giant snake
    snake_pts = []
    steps = 90
    for i in range(steps):
        t = i / float(steps)
        # S-curve path across the screen
        sx = int(140 + t * 900 + math.sin(t * 6.5) * 110)
        sy = int(680 - t * 440 + math.cos(t * 5.5) * 80)
        snake_pts.append((sx, sy, t))

    # Draw segments from tail to head
    for sx, sy, t in snake_pts:
        radius = int(24 + t * 38)
        # Gradient body scales
        r_col = int(255 * math.sin(t * 3.14))
        g_col = int(40 + 215 * (1 - t))
        b_col = int(220 + 35 * t)
        
        # Outer glow
        snake_draw.ellipse([sx - radius - 6, sy - radius - 6, sx + radius + 6, sy + radius + 6], fill=(0, 220, 255, 60))
        # Main body
        snake_draw.ellipse([sx - radius, sy - radius, sx + radius, sy + radius], fill=(r_col, g_col, b_col, 255))
        # 3D highlight on top-left of each scale
        snake_draw.ellipse([sx - radius * 0.7, sy - radius * 0.7, sx + radius * 0.1, sy + radius * 0.1], fill=(255, 255, 255, 120))

    # Snake Head
    hx, hy, _ = snake_pts[-1]
    head_r = 68
    snake_draw.ellipse([hx - head_r, hy - head_r, hx + head_r, hy + head_r], fill=(0, 240, 255, 255))
    snake_draw.ellipse([hx - head_r - 8, hy - head_r - 8, hx + head_r + 8, hy + head_r + 8], outline=(255, 255, 255, 180), width=4)

    # Cute big eyes on the snake head
    for eye_off in [-22, 22]:
        ex, ey = hx + eye_off, hy - 14
        snake_draw.ellipse([ex - 18, ey - 18, ex + 18, ey + 18], fill=(255, 255, 255, 255))
        snake_draw.ellipse([ex - 9, ey - 9, ex + 9, ey + 9], fill=(20, 25, 40, 255))
        snake_draw.ellipse([ex - 4, ey - 8, ex + 2, ey - 2], fill=(255, 255, 255, 255)) # Glisten

    # Add soft glow to snake layer
    snake_glow = snake_layer.filter(ImageFilter.GaussianBlur(10))
    base.alpha_composite(snake_glow)
    base.alpha_composite(snake_layer)

    # 5. Composite VTuber Ponyo Avatar with Sticker Glow Outline
    if os.path.exists(AVATAR_PATH):
        ponyo_raw = Image.open(AVATAR_PATH).convert("RGBA")
        # Scale to 530x530 for commanding presence on the right
        ponyo_size = 530
        ponyo_scaled = ponyo_raw.resize((ponyo_size, ponyo_size), Image.Resampling.LANCZOS)

        # Position on bottom right
        px = W - ponyo_size + 45
        py = H - ponyo_size + 20

        # Generate outer neon white & cyan glow
        mask = ponyo_scaled.split()[3]
        glow_mask = mask.filter(ImageFilter.GaussianBlur(18))
        glow_surf = Image.new("RGBA", (W, H), (0, 0, 0, 0))

        # Cyan outer glow
        glow_cyan = Image.new("RGBA", (ponyo_size, ponyo_size), (0, 255, 255, 200))
        glow_surf.paste(glow_cyan, (px, py), glow_mask)
        # White inner sticker outline
        outline_mask = mask.filter(ImageFilter.GaussianBlur(5))
        glow_white = Image.new("RGBA", (ponyo_size, ponyo_size), (255, 255, 255, 240))
        glow_surf.paste(glow_white, (px, py), outline_mask)

        base.alpha_composite(glow_surf)
        base.paste(ponyo_scaled, (px, py), ponyo_scaled)

        font_impact = "C:/Windows/Fonts/impact.ttf"
        font_arial = "C:/Windows/Fonts/ariblk.ttf"

        # Ponyo Floating Speech Bubble
        bubble_img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        b_draw = ImageDraw.Draw(bubble_img)
        font_bubble = ImageFont.truetype(font_arial, 22) if os.path.exists(font_arial) else ImageFont.load_default()
        
        bb_x1, bb_y1, bb_x2, bb_y2 = W - 355, 155, W - 65, 222
        b_draw.rounded_rectangle([bb_x1 + 4, bb_y1 + 4, bb_x2 + 4, bb_y2 + 4], radius=14, fill=(10, 15, 30, 200))
        b_draw.rounded_rectangle([bb_x1, bb_y1, bb_x2, bb_y2], radius=14, fill=(255, 255, 255, 255), outline=(30, 35, 55), width=3)
        b_draw.polygon([(W - 200, bb_y2 - 2), (W - 170, bb_y2 - 2), (W - 190, bb_y2 + 18)], fill=(255, 255, 255, 255))
        b_draw.polygon([(W - 200, bb_y2 - 2), (W - 170, bb_y2 - 2), (W - 190, bb_y2 + 18)], outline=(30, 35, 55), width=3)
        b_draw.line([(W - 198, bb_y2 - 2), (W - 172, bb_y2 - 2)], fill=(255, 255, 255, 255), width=4)
        b_draw.text((bb_x1 + 20, bb_y1 + 17), "IKUTAN MAIN YUK!", fill=(20, 25, 45), font=font_bubble)
        base.alpha_composite(bubble_img)

    # 6. Typography & Overlay Badges
    overlay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)

    font_impact = "C:/Windows/Fonts/impact.ttf"
    font_arial = "C:/Windows/Fonts/ariblk.ttf"

    font_title = ImageFont.truetype(font_impact, 114) if os.path.exists(font_impact) else ImageFont.load_default()
    font_sub = ImageFont.truetype(font_impact, 48) if os.path.exists(font_impact) else ImageFont.load_default()
    font_badge = ImageFont.truetype(font_arial, 22) if os.path.exists(font_arial) else ImageFont.load_default()
    font_cmd = ImageFont.truetype(font_arial, 24) if os.path.exists(font_arial) else ImageFont.load_default()
    font_drama = ImageFont.truetype(font_impact, 34) if os.path.exists(font_impact) else ImageFont.load_default()

    # --- TOP BADGE: LIVE STREAM + VTUBER PONYO ---
    # Live Pill
    draw.rounded_rectangle([45, 38, 175, 78], radius=20, fill=(230, 20, 50, 255), outline=(255, 255, 255, 220), width=3)
    draw.ellipse([58, 51, 72, 65], fill=(255, 255, 255, 255))
    draw.text((82, 45), "LIVE", fill=(255, 255, 255), font=font_badge)

    # VTuber Pill
    draw.rounded_rectangle([190, 38, 440, 78], radius=20, fill=(40, 48, 85, 235), outline=(0, 230, 255, 220), width=3)
    draw.text((208, 45), "VTUBER PONYO", fill=(0, 245, 255), font=font_badge)

    # --- MAIN TITLE: SLITHER.IO ---
    title_text = "SLITHER.IO"
    tx, ty = 45, 95

    # 3D Deep Drop Shadow
    for off in range(12, 0, -1):
        draw.text((tx + off, ty + off), title_text, fill=(8, 12, 28, 255), font=font_title)

    # Outer Thick Black Stroke
    stroke_w = 7
    for sx in range(-stroke_w, stroke_w + 1):
        for sy in range(-stroke_w, stroke_w + 1):
            if sx*sx + sy*sy <= stroke_w*stroke_w:
                draw.text((tx + sx, ty + sy), title_text, fill=(15, 18, 30), font=font_title)

    # Vibrant Yellow-Orange Gradient Fill
    draw.text((tx, ty), title_text, fill=(255, 225, 20), font=font_title)
    draw.text((tx, ty - 2), title_text, fill=(255, 255, 220), font=font_title)

    # --- HOOK BANNER: KENDALIKAN ULAR LEWAT CHAT! ---
    box_x1, box_y1, box_x2, box_y2 = 45, 240, 715, 320
    draw.rounded_rectangle([box_x1 + 6, box_y1 + 6, box_x2 + 6, box_y2 + 6], radius=16, fill=(10, 14, 25, 220))
    draw.rounded_rectangle([box_x1, box_y1, box_x2, box_y2], radius=16, fill=(24, 28, 55, 245), outline=(255, 210, 0), width=4)
    draw.text((box_x1 + 22, box_y1 + 14), "KENDALIKAN ULAR LEWAT CHAT!", fill=(255, 255, 255), font=font_sub)

    # --- INTERACTIVE COMMAND PILLS DENGAN VEKTOR IKON ---
    commands = [
        ("!BOOST", (255, 80, 20), (255, 255, 255), "LIGHTNING"),
        ("!PUTAR", (0, 230, 255), (10, 20, 35), "SPIRAL"),
        ("!KIRI", (50, 255, 90), (10, 30, 15), "LEFT"),
        ("!KANAN", (255, 220, 0), (25, 25, 10), "RIGHT")
    ]

    cx_start = 45
    cy_pos = 345
    pill_w = 158
    pill_h = 52

    for i, (cmd_txt, bg_col, txt_col, icon_type) in enumerate(commands):
        c_x = cx_start + i * (pill_w + 14)
        draw.rounded_rectangle([c_x + 3, cy_pos + 3, c_x + pill_w + 3, cy_pos + pill_h + 3], radius=12, fill=(10, 12, 20, 180))
        draw.rounded_rectangle([c_x, cy_pos, c_x + pill_w, cy_pos + pill_h], radius=12, fill=(*bg_col, 255), outline=(255, 255, 255, 220), width=2)
        
        tw = draw.textlength(cmd_txt, font=font_cmd)
        text_x = c_x + 18
        draw.text((text_x, cy_pos + 12), cmd_txt, fill=txt_col, font=font_cmd)
        
        icon_x = text_x + tw + 8
        icon_y = cy_pos + 16
        if icon_type == "LIGHTNING":
            draw_lightning_icon(draw, icon_x, icon_y - 2, size=20, color=txt_col)
        elif icon_type == "SPIRAL":
            draw_spiral_icon(draw, icon_x, icon_y, size=18, color=txt_col)
        elif icon_type == "LEFT":
            draw_arrow_icon(draw, icon_x, icon_y + 1, size=16, direction="LEFT", color=txt_col)
        elif icon_type == "RIGHT":
            draw_arrow_icon(draw, icon_x, icon_y + 1, size=16, direction="RIGHT", color=txt_col)

    # --- DRAMA / CALL-TO-ACTION STAMP (Bottom Left) ---
    drama_x1, drama_y1, drama_x2, drama_y2 = 45, 625, 500, 685
    draw.rounded_rectangle([drama_x1 + 4, drama_y1 + 4, drama_x2 + 4, drama_y2 + 4], radius=14, fill=(10, 10, 20, 200))
    draw.rounded_rectangle([drama_x1, drama_y1, drama_x2, drama_y2], radius=14, fill=(255, 45, 85, 240), outline=(255, 255, 255), width=3)
    
    # Trophy Vector Icon
    draw_trophy_icon(draw, drama_x1 + 18, drama_y1 + 16, size=26, color=(255, 235, 40, 255))
    draw.text((drama_x1 + 54, drama_y1 + 10), "BISA TEMBUS TOP 10 DUNIA?!", fill=(255, 255, 255), font=font_drama)

    # Final Merge & Save
    base.alpha_composite(overlay)
    final_rgb = base.convert("RGB")
    final_rgb.save(OUTPUT_PATH, "PNG", quality=95)
    print(f"[THUMBNAIL PRO] Berhasil disimpan di: {OUTPUT_PATH}")
    return OUTPUT_PATH

if __name__ == "__main__":
    generate_thumbnail()

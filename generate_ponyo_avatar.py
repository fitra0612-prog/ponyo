import os
from PIL import Image

def generate_ponyo_ghost_avatars(output_dir="avatars"):
    os.makedirs(output_dir, exist_ok=True)
    
    # 64 x 64 native pixel grid
    GW, GH = 64, 64
    SCALE = 9  # 64x64 -> 576x576 crisp retro pixel art

    # Color Palette
    C_TRANS = (0, 0, 0, 0)
    C_OUTLINE = (28, 30, 42, 255)       # Clean dark outline
    C_WHITE = (255, 255, 255, 255)      # Pure white sheet
    C_SHADOW_1 = (220, 228, 242, 255)   # Light soft cool shadow
    C_SHADOW_2 = (185, 196, 218, 255)   # Deeper crease shadow
    C_EYE = (18, 18, 26, 255)           # Bead black eyes
    C_BLUSH = (255, 165, 190, 210)      # Pastel pink blush
    C_MOUTH_BG = (150, 35, 55, 255)     # Inside mouth
    C_TONGUE = (255, 120, 145, 255)     # Cute tongue
    C_SWEAT = (100, 195, 255, 255)      # Cute blue sweat drop
    C_GOLD = (255, 215, 70, 255)        # Gold star / sparkle
    C_TEAR = (95, 190, 255, 235)        # Anime tear streams
    C_RED_ANGER = (240, 45, 60, 255)    # Anime anger mark (popping vein)
    C_SHY_BLUSH = (255, 125, 160, 235)  # Heavy bashful blushing cheek

    def draw_ponyo(mouth_open=False, eyes_closed=False, emotion="NORMAL"):
        img = Image.new("RGBA", (GW, GH), C_TRANS)
        pixels = img.load()

        def set_px(x, y, color):
            if 0 <= x < GW and 0 <= y < GH:
                pixels[x, y] = color

        def fill_rect(x1, y1, x2, y2, color):
            for x in range(x1, x2 + 1):
                for y in range(y1, y2 + 1):
                    set_px(x, y, color)

        cx = 31  # Center X

        # 1. MAIN BODY SILHOUETTE (Capsule dome flaring to scalloped skirt)
        for y in range(8, 57):
            if y < 22:
                # Smooth dome
                dy = 22 - y
                r = int((14**2 - dy**2)**0.5) if dy <= 14 else 0
                rx = max(r, 2)
            elif y < 38:
                # Vertical torso
                rx = 14 + int((y - 22) * 0.15)
            else:
                # Flaring sheet/skirt
                prog = (y - 38) / 18.0
                rx = int(16 + prog * 6)

            lx = cx - rx
            rx_bound = cx + rx

            for x in range(lx, rx_bound + 1):
                col = C_WHITE
                # Right side shadow for 3D depth
                if x > rx_bound - 3:
                    col = C_SHADOW_1

                # Wavy vertical folds along skirt (y >= 40)
                if y >= 40:
                    fold = (x - lx) % 6
                    if fold in [0, 1] or x < lx + 2 or x > rx_bound - 2:
                        col = C_SHADOW_1 if y < 51 else C_SHADOW_2

                set_px(x, y, col)

        # Scalloped bottom hem cutouts
        scallop_notches = [cx - 16, cx - 10, cx - 4, cx + 2, cx + 8, cx + 14]
        for sx in scallop_notches:
            set_px(sx, 55, C_TRANS)
            set_px(sx + 1, 55, C_TRANS)
            set_px(sx, 56, C_TRANS)
            set_px(sx + 1, 56, C_TRANS)
            set_px(sx, 54, C_SHADOW_2)
            set_px(sx + 1, 54, C_SHADOW_2)

        # 2. ARMS: TERANGKAT HANYA JIKA BICARA (mouth_open == True)
        if mouth_open:
            # === TANGAN TERANGKAT KE ATAS (EXCITED / TALKING / BOO!) ===
            # Tangan Kiri Terangkat (Naik ke arah samping atas: y: 22..29, x: 8..17)
            fill_rect(cx - 17, 28, cx - 13, 32, C_WHITE)
            fill_rect(cx - 20, 25, cx - 16, 29, C_WHITE)
            fill_rect(cx - 23, 22, cx - 19, 26, C_WHITE) # Ujung tangan terangkat
            # Bayangan bawah tangan kiri
            fill_rect(cx - 19, 30, cx - 14, 33, C_SHADOW_1)

            # Tangan Kanan Terangkat (Naik ke arah samping atas: y: 22..29, x: 45..54)
            fill_rect(cx + 13, 28, cx + 17, 32, C_WHITE)
            fill_rect(cx + 16, 25, cx + 20, 29, C_WHITE)
            fill_rect(cx + 19, 22, cx + 23, 26, C_WHITE) # Ujung tangan terangkat
            # Bayangan bawah tangan kanan
            fill_rect(cx + 14, 30, cx + 19, 33, C_SHADOW_1)
        else:
            # === TANGAN TURUN / ISTIRAHAT KE SAMPING BAWAH (IDLE / DIAM) ===
            # Tangan Kiri Turun di Samping Tubuh (y: 33..42, x: 10..18)
            fill_rect(cx - 18, 33, cx - 13, 37, C_WHITE)
            fill_rect(cx - 20, 36, cx - 16, 40, C_WHITE)
            fill_rect(cx - 21, 39, cx - 18, 43, C_WHITE) # Ujung tangan mengarah ke bawah
            # Bayangan bawah tangan kiri
            for ax in range(cx - 21, cx - 17):
                set_px(ax, 44, C_SHADOW_1)

            # Tangan Kanan Turun di Samping Tubuh (y: 33..42, x: 44..52)
            fill_rect(cx + 13, 33, cx + 18, 37, C_WHITE)
            fill_rect(cx + 16, 36, cx + 20, 40, C_WHITE)
            fill_rect(cx + 18, 39, cx + 21, 43, C_WHITE) # Ujung tangan mengarah ke bawah
            # Bayangan bawah tangan kanan
            for ax in range(cx + 18, cx + 22):
                set_px(ax, 44, C_SHADOW_1)

        # 3. EYES & EXPRESSIONS
        eye_y = 23
        left_eye_x = cx - 6   # 25
        right_eye_x = cx + 4  # 35

        if emotion == "HAPPY":
            # Joyful curved eyes + rosy blush
            for ex in [left_eye_x, right_eye_x]:
                set_px(ex - 2, eye_y + 3, C_EYE)
                set_px(ex - 1, eye_y + 1, C_EYE)
                set_px(ex, eye_y, C_EYE)
                set_px(ex + 1, eye_y, C_EYE)
                set_px(ex + 2, eye_y + 1, C_EYE)
                set_px(ex + 3, eye_y + 3, C_EYE)
            fill_rect(left_eye_x - 3, eye_y + 4, left_eye_x, eye_y + 6, C_BLUSH)
            fill_rect(right_eye_x + 1, eye_y + 4, right_eye_x + 4, eye_y + 6, C_BLUSH)
        elif emotion == "SHOCK":
            # Wide startled hollow eyes + blue sweat drop on forehead
            for ex in [left_eye_x, right_eye_x]:
                fill_rect(ex - 1, eye_y - 1, ex + 2, eye_y + 4, C_EYE)
                fill_rect(ex, eye_y + 1, ex + 1, eye_y + 2, C_WHITE)
            fill_rect(cx + 10, 15, cx + 11, 18, C_SWEAT)
            set_px(cx + 10, 14, C_SWEAT)
        elif emotion == "POUT":
            # Cute pouty eyebrows + puffed cheeks
            for ex in [left_eye_x, right_eye_x]:
                fill_rect(ex, eye_y + 1, ex + 1, eye_y + 4, C_EYE)
            set_px(left_eye_x - 1, eye_y - 2, C_EYE)
            set_px(left_eye_x, eye_y - 1, C_EYE)
            set_px(left_eye_x + 1, eye_y, C_EYE)
            set_px(right_eye_x + 2, eye_y - 2, C_EYE)
            set_px(right_eye_x + 1, eye_y - 1, C_EYE)
            set_px(right_eye_x, eye_y, C_EYE)
            fill_rect(left_eye_x - 4, eye_y + 4, left_eye_x - 1, eye_y + 7, C_BLUSH)
            fill_rect(right_eye_x + 2, eye_y + 4, right_eye_x + 5, eye_y + 7, C_BLUSH)
        elif emotion == "THINK":
            # Eyes looking slightly up
            for ex in [left_eye_x, right_eye_x]:
                fill_rect(ex, eye_y - 1, ex + 1, eye_y + 3, C_EYE)
                set_px(ex, eye_y - 1, C_WHITE)
            fill_rect(left_eye_x - 3, eye_y + 5, left_eye_x - 1, eye_y + 6, C_BLUSH)
            fill_rect(right_eye_x + 2, eye_y + 5, right_eye_x + 4, eye_y + 6, C_BLUSH)
        elif emotion == "CRY":
            # Squeezed sad shut eyes with pouring blue tear streams
            for ex in [left_eye_x, right_eye_x]:
                set_px(ex - 2, eye_y + 1, C_EYE)
                set_px(ex - 1, eye_y + 2, C_EYE)
                fill_rect(ex, eye_y + 3, ex + 1, eye_y + 3, C_EYE)
                set_px(ex + 2, eye_y + 2, C_EYE)
                set_px(ex + 3, eye_y + 1, C_EYE)
                # Tear streams cascading down cheeks
                fill_rect(ex - 1, eye_y + 4, ex + 1, eye_y + 13, C_TEAR)
                set_px(ex - 2, eye_y + 8, C_TEAR)
                set_px(ex + 2, eye_y + 11, C_TEAR)
            fill_rect(left_eye_x - 4, eye_y + 5, left_eye_x - 2, eye_y + 7, C_BLUSH)
            fill_rect(right_eye_x + 2, eye_y + 5, right_eye_x + 4, eye_y + 7, C_BLUSH)
        elif emotion == "SMUG":
            # Sly confident squinting eyes (> <) + rosy cheeks
            for ex, is_left in [(left_eye_x, True), (right_eye_x, False)]:
                if is_left:
                    set_px(ex - 2, eye_y + 1, C_EYE)
                    set_px(ex - 1, eye_y + 2, C_EYE)
                    fill_rect(ex, eye_y + 3, ex + 2, eye_y + 3, C_EYE)
                    set_px(ex + 3, eye_y + 2, C_EYE)
                else:
                    set_px(ex - 2, eye_y + 2, C_EYE)
                    fill_rect(ex - 1, eye_y + 3, ex + 1, eye_y + 3, C_EYE)
                    set_px(ex + 2, eye_y + 2, C_EYE)
                    set_px(ex + 3, eye_y + 1, C_EYE)
            fill_rect(left_eye_x - 3, eye_y + 4, left_eye_x, eye_y + 6, C_BLUSH)
            fill_rect(right_eye_x + 1, eye_y + 4, right_eye_x + 4, eye_y + 6, C_BLUSH)
        elif emotion == "SHY":
            # Bashful downward oval eyes + deep red blush across the whole face
            for ex in [left_eye_x, right_eye_x]:
                fill_rect(ex, eye_y + 1, ex + 1, eye_y + 4, C_EYE)
                set_px(ex, eye_y + 3, C_WHITE)
            fill_rect(left_eye_x - 5, eye_y + 4, right_eye_x + 5, eye_y + 7, C_SHY_BLUSH)
            fill_rect(left_eye_x - 4, eye_y + 8, right_eye_x + 4, eye_y + 8, C_BLUSH)
        elif emotion == "SLEEPY":
            # Peaceful horizontal sleepy slit eyes (- -)
            for ex in [left_eye_x, right_eye_x]:
                fill_rect(ex - 2, eye_y + 2, ex + 2, eye_y + 2, C_EYE)
                set_px(ex - 2, eye_y + 3, C_EYE)
                set_px(ex + 2, eye_y + 3, C_EYE)
            fill_rect(left_eye_x - 3, eye_y + 4, left_eye_x - 1, eye_y + 5, C_BLUSH)
            fill_rect(right_eye_x + 2, eye_y + 4, right_eye_x + 4, eye_y + 5, C_BLUSH)
            # Sleep bubble (hana-chochin) blowing from center nose/mouth
            fill_rect(cx + 2, eye_y + 4, cx + 7, eye_y + 9, C_TEAR)
            fill_rect(cx + 3, eye_y + 3, cx + 6, eye_y + 10, C_TEAR)
            set_px(cx + 4, eye_y + 5, C_WHITE)
            # Floating retro 'Zzz' above head in soft blue
            C_Z = (145, 175, 225, 255)
            # Big 'Z' at (cx + 8, 12)
            fill_rect(cx + 7, 11, cx + 11, 11, C_Z)
            set_px(cx + 10, 12, C_Z)
            set_px(cx + 9, 13, C_Z)
            set_px(cx + 8, 14, C_Z)
            fill_rect(cx + 7, 15, cx + 11, 15, C_Z)
            # Smaller 'z' at (cx + 13, 7)
            fill_rect(cx + 13, 6, cx + 16, 6, C_Z)
            set_px(cx + 15, 7, C_Z)
            set_px(cx + 14, 8, C_Z)
            fill_rect(cx + 13, 9, cx + 16, 9, C_Z)
        elif emotion == "ANGRY":
            # Fierce slanted determined eyebrows + anime popping vein cross mark
            for ex, is_left in [(left_eye_x, True), (right_eye_x, False)]:
                fill_rect(ex, eye_y + 1, ex + 1, eye_y + 4, C_EYE)
                if is_left:
                    set_px(ex - 2, eye_y - 2, C_EYE)
                    set_px(ex - 1, eye_y - 1, C_EYE)
                    set_px(ex, eye_y, C_EYE)
                    set_px(ex + 1, eye_y + 1, C_EYE)
                else:
                    set_px(ex + 3, eye_y - 2, C_EYE)
                    set_px(ex + 2, eye_y - 1, C_EYE)
                    set_px(ex + 1, eye_y, C_EYE)
                    set_px(ex, eye_y + 1, C_EYE)
            # Red popping vein cross (#) on right forehead
            fill_rect(cx + 9, 13, cx + 9, 17, C_RED_ANGER)
            fill_rect(cx + 12, 13, cx + 12, 17, C_RED_ANGER)
            fill_rect(cx + 8, 14, cx + 13, 14, C_RED_ANGER)
            fill_rect(cx + 8, 16, cx + 13, 16, C_RED_ANGER)
        elif emotion == "STAR":
            # Distinct 4-pointed golden sparkle stars (✦ ✦) as eyes!
            for ex in [left_eye_x, right_eye_x]:
                # Horizontal bar
                fill_rect(ex - 3, eye_y + 1, ex + 4, eye_y + 2, C_GOLD)
                # Vertical bar
                fill_rect(ex, eye_y - 2, ex + 1, eye_y + 5, C_GOLD)
                # Diagonal taper
                set_px(ex - 1, eye_y, C_GOLD)
                set_px(ex + 2, eye_y, C_GOLD)
                set_px(ex - 1, eye_y + 3, C_GOLD)
                set_px(ex + 2, eye_y + 3, C_GOLD)
                # Bright white shining center glint
                fill_rect(ex, eye_y + 1, ex + 1, eye_y + 2, C_WHITE)
            fill_rect(left_eye_x - 4, eye_y + 5, left_eye_x - 1, eye_y + 6, C_BLUSH)
            fill_rect(right_eye_x + 2, eye_y + 5, right_eye_x + 5, eye_y + 6, C_BLUSH)
        else:
            for ex in [left_eye_x, right_eye_x]:
                if not eyes_closed:
                    fill_rect(ex, eye_y, ex + 1, eye_y + 4, C_EYE)
                    set_px(ex - 1, eye_y + 1, C_EYE)
                    set_px(ex - 1, eye_y + 2, C_EYE)
                    set_px(ex - 1, eye_y + 3, C_EYE)
                    set_px(ex + 2, eye_y + 1, C_EYE)
                    set_px(ex + 2, eye_y + 2, C_EYE)
                    set_px(ex + 2, eye_y + 3, C_EYE)
                else:
                    set_px(ex - 2, eye_y + 3, C_EYE)
                    set_px(ex - 1, eye_y + 2, C_EYE)
                    set_px(ex, eye_y + 1, C_EYE)
                    set_px(ex + 1, eye_y + 1, C_EYE)
                    set_px(ex + 2, eye_y + 2, C_EYE)
                    set_px(ex + 3, eye_y + 3, C_EYE)

            # 4. CHEEK BLUSH
            fill_rect(left_eye_x - 3, eye_y + 5, left_eye_x - 1, eye_y + 6, C_BLUSH)
            fill_rect(right_eye_x + 2, eye_y + 5, right_eye_x + 4, eye_y + 6, C_BLUSH)

        # 5. MOUTH (Closed vs Open vs Emotion)
        if emotion == "CRY":
            # Sad wobbly open crying mouth
            fill_rect(cx - 2, eye_y + 6, cx + 2, eye_y + 9, C_OUTLINE)
            fill_rect(cx - 1, eye_y + 7, cx + 1, eye_y + 8, C_MOUTH_BG)
        elif emotion == "SMUG":
            # Playful cat mouth / confident tilted smirk (:3)
            set_px(cx - 3, eye_y + 5, C_OUTLINE)
            set_px(cx - 2, eye_y + 6, C_OUTLINE)
            set_px(cx - 1, eye_y + 5, C_OUTLINE)
            set_px(cx, eye_y + 6, C_OUTLINE)
            set_px(cx + 1, eye_y + 5, C_OUTLINE)
            set_px(cx + 2, eye_y + 4, C_OUTLINE)
        elif emotion == "SHY":
            # Shy small wavy embarrassed smile
            set_px(cx - 2, eye_y + 6, C_OUTLINE)
            set_px(cx - 1, eye_y + 5, C_OUTLINE)
            set_px(cx, eye_y + 6, C_OUTLINE)
            set_px(cx + 1, eye_y + 5, C_OUTLINE)
        elif emotion == "SLEEPY":
            # Tiny relaxed round O mouth
            fill_rect(cx - 1, eye_y + 6, cx + 1, eye_y + 7, C_OUTLINE)
        elif emotion == "ANGRY":
            # Fierce determined teeth-clenched grin
            fill_rect(cx - 2, eye_y + 5, cx + 2, eye_y + 7, C_OUTLINE)
            fill_rect(cx - 1, eye_y + 6, cx + 1, eye_y + 6, C_WHITE)
        elif emotion == "STAR":
            # Big joyful open smiling mouth
            fill_rect(cx - 2, eye_y + 4, cx + 2, eye_y + 9, C_OUTLINE)
            fill_rect(cx - 1, eye_y + 5, cx + 1, eye_y + 8, C_MOUTH_BG)
            set_px(cx - 1, eye_y + 8, C_TONGUE)
            set_px(cx, eye_y + 8, C_TONGUE)
            set_px(cx + 1, eye_y + 8, C_TONGUE)
        elif emotion == "POUT" and not mouth_open:
            set_px(cx - 2, eye_y + 6, C_OUTLINE)
            set_px(cx - 1, eye_y + 5, C_OUTLINE)
            set_px(cx, eye_y + 6, C_OUTLINE)
            set_px(cx + 1, eye_y + 5, C_OUTLINE)
            set_px(cx + 2, eye_y + 6, C_OUTLINE)
        elif emotion == "SHOCK":
            fill_rect(cx - 2, eye_y + 4, cx + 2, eye_y + 9, C_OUTLINE)
            fill_rect(cx - 1, eye_y + 5, cx + 1, eye_y + 8, C_MOUTH_BG)
        elif not mouth_open:
            set_px(cx - 1, eye_y + 5, C_OUTLINE)
            set_px(cx, eye_y + 6, C_OUTLINE)
            set_px(cx + 1, eye_y + 5, C_OUTLINE)
        else:
            fill_rect(cx - 2, eye_y + 4, cx + 2, eye_y + 8, C_OUTLINE)
            fill_rect(cx - 1, eye_y + 5, cx + 1, eye_y + 7, C_MOUTH_BG)
            set_px(cx - 1, eye_y + 7, C_TONGUE)
            set_px(cx, eye_y + 7, C_TONGUE)
            set_px(cx + 1, eye_y + 7, C_TONGUE)

        # 6. AUTO-PIXEL ART OUTLINE (1-pixel clean border around all opaque elements)
        outlined = Image.new("RGBA", (GW, GH), C_TRANS)
        out_pix = outlined.load()

        # Copy original pixels
        for x in range(GW):
            for y in range(GH):
                if pixels[x, y][3] > 0:
                    out_pix[x, y] = pixels[x, y]

        # Generate outer outline
        for x in range(GW):
            for y in range(GH):
                if pixels[x, y][3] == 0:
                    has_opaque_neighbor = False
                    for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                        nx, ny = x + dx, y + dy
                        if 0 <= nx < GW and 0 <= ny < GH and pixels[nx, ny][3] > 0:
                            has_opaque_neighbor = True
                            break
                    if has_opaque_neighbor:
                        out_pix[x, y] = C_OUTLINE

        # Garis lipatan dalam tangan agar terlihat terpisah dari dada
        if mouth_open:
            for ay in range(27, 32):
                out_pix[cx - 13, ay] = C_SHADOW_2
                out_pix[cx + 13, ay] = C_SHADOW_2
        else:
            for ay in range(34, 40):
                out_pix[cx - 13, ay] = C_SHADOW_2
                out_pix[cx + 13, ay] = C_SHADOW_2

        # Scale up using Nearest Neighbor for crisp retro pixel art
        final_img = outlined.resize((GW * SCALE, GH * SCALE), Image.Resampling.NEAREST)
        return final_img

    # Generate all 4 states for natural PNGTuber animation
    # 1. Closed mouth, eyes open (Idle)
    img_closed = draw_ponyo(mouth_open=False, eyes_closed=False)
    closed_path = os.path.join(output_dir, "closed.png")
    img_closed.save(closed_path, "PNG")
    print(f"Created {closed_path}")

    # 2. Closed mouth, eyes blinking (Idle Blink)
    img_blink = draw_ponyo(mouth_open=False, eyes_closed=True)
    blink_path = os.path.join(output_dir, "blink.png")
    img_blink.save(blink_path, "PNG")
    print(f"Created {blink_path}")

    # 3. Open mouth, eyes open (Talking)
    img_open = draw_ponyo(mouth_open=True, eyes_closed=False)
    open_path = os.path.join(output_dir, "open.png")
    img_open.save(open_path, "PNG")
    print(f"Created {open_path}")

    # 4. Open mouth, eyes blinking (Talking Blink)
    img_blink_open = draw_ponyo(mouth_open=True, eyes_closed=True)
    blink_open_path = os.path.join(output_dir, "blink_open.png")
    img_blink_open.save(blink_open_path, "PNG")
    print(f"Created {blink_open_path}")

    # 5. Dynamic Emotion Sprites (10 Emosi: HAPPY, SHOCK, POUT, THINK, CRY, SMUG, SHY, SLEEPY, ANGRY, STAR)
    all_emotions = [
        ("happy", True),
        ("shock", True),
        ("pout", False),
        ("think", False),
        ("cry", True),
        ("smug", False),
        ("shy", False),
        ("sleepy", False),
        ("angry", False),
        ("star", True),
    ]
    for emo, m_open in all_emotions:
        img_emo = draw_ponyo(mouth_open=m_open, eyes_closed=False, emotion=emo.upper())
        emo_path = os.path.join(output_dir, f"{emo}.png")
        img_emo.save(emo_path, "PNG")
        print(f"Created {emo_path}")

    # 6. Ekspresi Ojigi (Membungkuk Hormat / Zarei Khas Jepang untuk Minta Maaf)
    img_ojigi = draw_ojigi()
    ojigi_path = os.path.join(output_dir, "ojigi.png")
    img_ojigi.save(ojigi_path, "PNG")
    print(f"Created {ojigi_path}")

    # 7. Animasi Melambaikan Tangan HAPPY untuk Closing Livestream (wave_1 & wave_2)
    img_wave1 = draw_wave_frame(1)
    img_wave1.save(os.path.join(output_dir, "wave_1.png"), "PNG")
    img_wave2 = draw_wave_frame(2)
    img_wave2.save(os.path.join(output_dir, "wave_2.png"), "PNG")
    print(f"Created {output_dir}/wave_1.png and wave_2.png")

    # 8. Large Human Hand Pixel Art for Petting (!pat)
    generate_pat_hand_sprites(output_dir)


def draw_wave_frame(frame=1):
    """Menggambar frame animasi melambaikan tangan ceria (HAPPY) untuk closing stream"""
    GW, GH = 64, 64
    SCALE = 9

    C_TRANS = (0, 0, 0, 0)
    C_OUTLINE = (28, 30, 42, 255)
    C_WHITE = (255, 255, 255, 255)
    C_SHADOW_1 = (220, 228, 242, 255)
    C_SHADOW_2 = (185, 198, 222, 255)
    C_BLUSH = (255, 125, 160, 235)
    C_EYE = (28, 30, 42, 255)
    C_MOUTH_BG = (120, 25, 45, 255)
    C_TONGUE = (255, 135, 160, 255)

    img = Image.new("RGBA", (GW, GH), C_TRANS)
    pixels = img.load()

    def set_px(x, y, color):
        if 0 <= x < GW and 0 <= y < GH:
            pixels[x, y] = color

    def fill_rect(x1, y1, x2, y2, color):
        for x in range(x1, x2 + 1):
            for y in range(y1, y2 + 1):
                set_px(x, y, color)

    cx = 31

    # 1. MAIN BODY SILHOUETTE
    for y in range(8, 57):
        if y < 22:
            dy = 22 - y
            r = int((14**2 - dy**2)**0.5) if dy <= 14 else 0
            rx = max(r, 2)
        elif y < 38:
            rx = 14 + int((y - 22) * 0.15)
        else:
            prog = (y - 38) / 18.0
            rx = int(16 + prog * 6)

        lx = cx - rx
        rx_bound = cx + rx

        for x in range(lx, rx_bound + 1):
            col = C_WHITE
            if x > rx_bound - 3:
                col = C_SHADOW_1
            if y >= 40:
                fold = (x - lx) % 6
                if fold in [0, 1] or x < lx + 2 or x > rx_bound - 2:
                    col = C_SHADOW_1 if y < 51 else C_SHADOW_2
            set_px(x, y, col)

    scallop_notches = [cx - 16, cx - 10, cx - 4, cx + 2, cx + 8, cx + 14]
    for sx in scallop_notches:
        set_px(sx, 55, C_TRANS)
        set_px(sx + 1, 55, C_TRANS)
        set_px(sx, 56, C_TRANS)
        set_px(sx + 1, 56, C_TRANS)
        set_px(sx, 54, C_SHADOW_2)
        set_px(sx + 1, 54, C_SHADOW_2)

    # 2. ARMS:
    # Left Arm: Resting cute flipper on side
    fill_rect(cx - 18, 32, cx - 13, 36, C_WHITE)
    fill_rect(cx - 20, 35, cx - 16, 39, C_WHITE)
    fill_rect(cx - 21, 38, cx - 18, 42, C_WHITE)
    for ax in range(cx - 21, cx - 17):
        set_px(ax, 43, C_SHADOW_1)

    # Right Arm: Melambaikan tangan ke atas bergantian
    if frame == 1:
        fill_rect(cx + 13, 27, cx + 17, 31, C_WHITE)
        fill_rect(cx + 16, 23, cx + 20, 27, C_WHITE)
        fill_rect(cx + 19, 18, cx + 23, 23, C_WHITE)
        fill_rect(cx + 21, 14, cx + 25, 19, C_WHITE)
        fill_rect(cx + 22, 11, cx + 26, 15, C_WHITE)
        fill_rect(cx + 14, 29, cx + 19, 32, C_SHADOW_1)
        fill_rect(cx + 17, 25, cx + 22, 28, C_SHADOW_1)
    else:
        fill_rect(cx + 13, 27, cx + 17, 31, C_WHITE)
        fill_rect(cx + 15, 22, cx + 19, 27, C_WHITE)
        fill_rect(cx + 16, 17, cx + 20, 22, C_WHITE)
        fill_rect(cx + 17, 13, cx + 21, 18, C_WHITE)
        fill_rect(cx + 16, 10, cx + 20, 14, C_WHITE)
        fill_rect(cx + 14, 29, cx + 18, 32, C_SHADOW_1)
        fill_rect(cx + 16, 24, cx + 20, 27, C_SHADOW_1)

    # 3. HAPPY FACE
    eye_y = 23
    left_eye_x = cx - 6
    right_eye_x = cx + 4

    for ex in [left_eye_x, right_eye_x]:
        set_px(ex - 2, eye_y + 3, C_EYE)
        set_px(ex - 1, eye_y + 1, C_EYE)
        set_px(ex, eye_y, C_EYE)
        set_px(ex + 1, eye_y, C_EYE)
        set_px(ex + 2, eye_y + 1, C_EYE)
        set_px(ex + 3, eye_y + 3, C_EYE)

    fill_rect(left_eye_x - 3, eye_y + 4, left_eye_x, eye_y + 6, C_BLUSH)
    fill_rect(right_eye_x + 1, eye_y + 4, right_eye_x + 4, eye_y + 6, C_BLUSH)

    fill_rect(cx - 2, eye_y + 4, cx + 2, eye_y + 8, C_OUTLINE)
    fill_rect(cx - 1, eye_y + 5, cx + 1, eye_y + 7, C_MOUTH_BG)
    set_px(cx - 1, eye_y + 7, C_TONGUE)
    set_px(cx, eye_y + 7, C_TONGUE)
    set_px(cx + 1, eye_y + 7, C_TONGUE)

    # 4. OUTLINE
    outlined = Image.new("RGBA", (GW, GH), C_TRANS)
    out_pix = outlined.load()
    for x in range(GW):
        for y in range(GH):
            if pixels[x, y][3] > 0:
                out_pix[x, y] = pixels[x, y]
    for x in range(GW):
        for y in range(GH):
            if pixels[x, y][3] == 0:
                for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                    nx, ny = x + dx, y + dy
                    if 0 <= nx < GW and 0 <= ny < GH and pixels[nx, ny][3] > 0:
                        out_pix[x, y] = C_OUTLINE
                        break

    return outlined.resize((GW * SCALE, GH * SCALE), Image.Resampling.NEAREST)


def draw_ojigi():
    """Menggambar ekspresi Ojigi (Membungkuk hormat/terima kasih ala Jepang)"""
    GW, GH = 64, 64
    SCALE = 9

    C_TRANS = (0, 0, 0, 0)
    C_OUTLINE = (28, 30, 42, 255)
    C_WHITE = (255, 255, 255, 255)
    C_SHADOW_1 = (220, 228, 242, 255)
    C_SHADOW_2 = (185, 198, 222, 255)
    C_BLUSH = (255, 140, 180, 240)
    C_EYE = (28, 30, 42, 255)

    img = Image.new("RGBA", (GW, GH), C_TRANS)
    pixels = img.load()

    def set_px(x, y, color):
        if 0 <= x < GW and 0 <= y < GH:
            pixels[x, y] = color

    def fill_rect(x1, y1, x2, y2, color):
        for x in range(x1, x2 + 1):
            for y in range(y1, y2 + 1):
                set_px(x, y, color)

    cx = 31

    # 1. FORESHORTENED BOWING BODY
    for y in range(16, 54):
        if y < 34:
            dy = 34 - y
            rx = int((22**2 - (dy * 1.25)**2)**0.5) if (dy * 1.25) <= 22 else 4
        elif y < 45:
            rx = 22 + int((y - 34) * 0.1)
        else:
            prog = (y - 45) / 8.0
            rx = int(22 + prog * 3)

        lx = cx - rx
        rx_bound = cx + rx

        for x in range(lx, rx_bound + 1):
            col = C_WHITE
            if y < 24:
                col = C_SHADOW_1 if y < 20 else C_WHITE
            elif x > rx_bound - 3:
                col = C_SHADOW_1

            if y >= 46:
                fold = (x - lx) % 6
                if fold in [0, 1] or x < lx + 2 or x > rx_bound - 2:
                    col = C_SHADOW_1 if y < 51 else C_SHADOW_2
            set_px(x, y, col)

    # Scalloped bottom hem cutouts
    scallop_notches = [cx - 16, cx - 10, cx - 4, cx + 2, cx + 8, cx + 14]
    for sx in scallop_notches:
        set_px(sx, 52, C_TRANS)
        set_px(sx + 1, 52, C_TRANS)
        set_px(sx, 53, C_TRANS)
        set_px(sx + 1, 53, C_TRANS)
        set_px(sx, 51, C_SHADOW_2)
        set_px(sx + 1, 51, C_SHADOW_2)

    # 2. FACE (Positioned low, closed peaceful curved eyes looking down at ground)
    eye_y = 37
    left_eye_x = cx - 7
    right_eye_x = cx + 6

    for ex in [left_eye_x, right_eye_x]:
        set_px(ex - 2, eye_y + 1, C_EYE)
        set_px(ex - 1, eye_y, C_EYE)
        set_px(ex, eye_y, C_EYE)
        set_px(ex + 1, eye_y, C_EYE)
        set_px(ex + 2, eye_y + 1, C_EYE)
        set_px(ex + 3, eye_y + 2, C_EYE)

    fill_rect(left_eye_x - 3, eye_y + 2, left_eye_x - 1, eye_y + 3, C_BLUSH)
    fill_rect(right_eye_x + 2, eye_y + 2, right_eye_x + 4, eye_y + 3, C_BLUSH)

    # 3. DISTINCT TRAPEZOIDAL SEIZA / OJIGI HANDS WITH WRISTS
    hand_y = 43
    # Left wrist and hand
    fill_rect(cx - 12, hand_y + 1, cx - 10, hand_y + 3, C_WHITE)
    fill_rect(cx - 9, hand_y, cx - 2, hand_y + 4, C_WHITE)
    fill_rect(cx - 13, hand_y + 1, cx - 13, hand_y + 3, C_OUTLINE)
    fill_rect(cx - 12, hand_y, cx - 10, hand_y, C_OUTLINE)
    fill_rect(cx - 9, hand_y - 1, cx - 2, hand_y - 1, C_OUTLINE)
    fill_rect(cx - 1, hand_y, cx - 1, hand_y + 4, C_OUTLINE)
    fill_rect(cx - 9, hand_y + 5, cx - 2, hand_y + 5, C_OUTLINE)
    fill_rect(cx - 12, hand_y + 4, cx - 10, hand_y + 4, C_OUTLINE)

    # Right wrist and hand
    fill_rect(cx + 10, hand_y + 1, cx + 12, hand_y + 3, C_WHITE)
    fill_rect(cx + 2, hand_y, cx + 9, hand_y + 4, C_WHITE)
    fill_rect(cx + 13, hand_y + 1, cx + 13, hand_y + 3, C_OUTLINE)
    fill_rect(cx + 10, hand_y, cx + 12, hand_y, C_OUTLINE)
    fill_rect(cx + 2, hand_y - 1, cx + 9, hand_y - 1, C_OUTLINE)
    fill_rect(cx + 1, hand_y, cx + 1, hand_y + 4, C_OUTLINE)
    fill_rect(cx + 2, hand_y + 5, cx + 9, hand_y + 5, C_OUTLINE)
    fill_rect(cx + 10, hand_y + 4, cx + 12, hand_y + 4, C_OUTLINE)

    fill_rect(cx - 1, hand_y + 5, cx + 1, hand_y + 5, C_OUTLINE)

    # Outline
    outlined = Image.new("RGBA", (GW, GH), C_TRANS)
    out_pix = outlined.load()
    for x in range(GW):
        for y in range(GH):
            if pixels[x, y][3] > 0:
                out_pix[x, y] = pixels[x, y]
    for x in range(GW):
        for y in range(GH):
            if pixels[x, y][3] == 0:
                for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                    nx, ny = x + dx, y + dy
                    if 0 <= nx < GW and 0 <= ny < GH and pixels[nx, ny][3] > 0:
                        out_pix[x, y] = C_OUTLINE
                        break

    return outlined.resize((GW * SCALE, GH * SCALE), Image.Resampling.NEAREST)


def generate_pat_hand_sprites(output_dir="avatars"):
    os.makedirs(output_dir, exist_ok=True)
    GW, GH = 64, 64
    SCALE = 9

    C_TRANS = (0, 0, 0, 0)
    C_OUTLINE = (28, 30, 42, 255)
    C_SKIN = (252, 214, 180, 255)
    C_SKIN_SHADOW = (220, 164, 126, 255)
    C_SKIN_DEEP = (182, 126, 92, 255)
    C_SKIN_HI = (255, 240, 224, 255)
    C_NAIL = (255, 245, 238, 255)
    C_SLEEVE = (58, 76, 118, 255)
    C_SLEEVE_SHADOW = (38, 50, 82, 255)
    C_SLEEVE_HI = (88, 114, 168, 255)

    def make_hand(down=True):
        img = Image.new("RGBA", (GW, GH), C_TRANS)
        px = img.load()

        def set_px(x, y, col):
            if 0 <= x < GW and 0 <= y < GH:
                px[x, y] = col

        def fill_rect(x1, y1, x2, y2, col):
            for x in range(x1, x2 + 1):
                for y in range(y1, y2 + 1):
                    set_px(x, y, col)

        dy = 4 if down else 0

        # 1. SLEEVE (Cozy oversized sweater cuff entering from top right)
        for y in range(0, 16):
            start_x = 45 - int(y * 0.4)
            for x in range(start_x, 64):
                col = C_SLEEVE
                if x > 58:
                    col = C_SLEEVE_SHADOW
                elif x == start_x or x == start_x + 1:
                    col = C_SLEEVE_HI
                set_px(x, y, col)

        # Ribbed Cuff
        for y in range(12, 23):
            start_x = 40 - int((y - 12) * 0.3)
            for x in range(start_x, 56):
                col = C_SLEEVE
                if (x - start_x) % 3 == 0:
                    col = C_SLEEVE_HI
                elif (x - start_x) % 3 == 2 or x > 50:
                    col = C_SLEEVE_SHADOW
                set_px(x, y, col)

        # 2. WRIST & PALM / BACK OF HAND
        fill_rect(36, 18, 43, 25, C_SKIN)
        fill_rect(41, 20, 44, 25, C_SKIN_SHADOW)
        fill_rect(37, 18, 39, 21, C_SKIN_HI)

        for y in range(20 + dy, 32 + dy):
            x_min = 22 - int((y - (20 + dy)) * 0.2)
            x_max = 42 + int((y - (20 + dy)) * 0.1)
            for x in range(x_min, x_max + 1):
                col = C_SKIN
                if x < x_min + 3:
                    col = C_SKIN_HI
                elif x > x_max - 3 or y > 28 + dy:
                    col = C_SKIN_SHADOW
                set_px(x, y, col)

        # 3. THUMB
        thumb_base_y = 25 + dy
        fill_rect(38, thumb_base_y, 45, thumb_base_y + 4, C_SKIN)
        fill_rect(42, thumb_base_y + 2, 47, thumb_base_y + 7, C_SKIN)
        fill_rect(44, thumb_base_y + 6, 48, thumb_base_y + 10, C_SKIN)
        fill_rect(43, thumb_base_y + 9, 47, thumb_base_y + 11, C_SKIN)
        fill_rect(44, thumb_base_y + 10, 46, thumb_base_y + 11, C_NAIL)
        fill_rect(46, thumb_base_y + 4, 48, thumb_base_y + 10, C_SKIN_SHADOW)

        # 4. FOUR FINGERS
        curl = 4 if down else 1

        # Pinky
        p_x, p_y = 33, 28 + dy
        fill_rect(p_x, p_y, p_x + 4, p_y + 7, C_SKIN)
        fill_rect(p_x - 1, p_y + 6, p_x + 3, p_y + 10 + curl, C_SKIN)
        fill_rect(p_x, p_y + 9 + curl, p_x + 2, p_y + 11 + curl, C_NAIL)
        fill_rect(p_x + 3, p_y + 2, p_x + 4, p_y + 8, C_SKIN_SHADOW)

        # Ring finger
        r_x, r_y = 27, 29 + dy
        fill_rect(r_x, r_y, r_x + 4, r_y + 8, C_SKIN)
        fill_rect(r_x - 2, r_y + 7, r_x + 2, r_y + 12 + curl, C_SKIN)
        fill_rect(r_x - 1, r_y + 11 + curl, r_x + 1, r_y + 13 + curl, C_NAIL)
        fill_rect(r_x + 3, r_y + 2, r_x + 4, r_y + 9, C_SKIN_SHADOW)

        # Middle finger
        m_x, m_y = 20, 29 + dy
        fill_rect(m_x, m_y, m_x + 5, m_y + 9, C_SKIN)
        fill_rect(m_x - 3, m_y + 8, m_x + 2, m_y + 13 + curl, C_SKIN)
        fill_rect(m_x - 2, m_y + 12 + curl, m_x + 1, m_y + 14 + curl, C_NAIL)
        fill_rect(m_x + 3, m_y + 2, m_x + 5, m_y + 9, C_SKIN_SHADOW)

        # Index finger
        i_x, i_y = 13, 27 + dy
        fill_rect(i_x, i_y, i_x + 5, i_y + 8, C_SKIN)
        fill_rect(i_x - 4, i_y + 6, i_x + 1, i_y + 11 + curl, C_SKIN)
        fill_rect(i_x - 3, i_y + 10 + curl, i_x - 1, i_y + 12 + curl, C_NAIL)
        fill_rect(i_x + 1, i_y, i_x + 4, i_y + 4, C_SKIN_HI)
        fill_rect(i_x + 3, i_y + 4, i_x + 5, i_y + 9, C_SKIN_SHADOW)

        # Creases
        fill_rect(i_x + 5, i_y + 3, i_x + 5, i_y + 8, C_SKIN_DEEP)
        fill_rect(m_x + 5, m_y + 3, m_x + 5, m_y + 8, C_SKIN_DEEP)
        fill_rect(r_x + 4, r_y + 3, r_x + 4, r_y + 8, C_SKIN_DEEP)

        fill_rect(16, 27 + dy, 36, 28 + dy, C_SKIN_HI)
        set_px(17, 28 + dy, C_SKIN_DEEP)
        set_px(23, 28 + dy, C_SKIN_DEEP)
        set_px(29, 28 + dy, C_SKIN_DEEP)
        set_px(35, 27 + dy, C_SKIN_DEEP)

        # Outline
        outlined = Image.new("RGBA", (GW, GH), C_TRANS)
        out_pix = outlined.load()

        for x in range(GW):
            for y in range(GH):
                if px[x, y][3] > 0:
                    out_pix[x, y] = px[x, y]

        for x in range(GW):
            for y in range(GH):
                if px[x, y][3] == 0:
                    has_opaque = False
                    for ndx, ndy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                        nx, ny = x + ndx, y + ndy
                        if 0 <= nx < GW and 0 <= ny < GH and px[nx, ny][3] > 0:
                            has_opaque = True
                            break
                    if has_opaque:
                        out_pix[x, y] = C_OUTLINE

        return outlined.resize((GW * SCALE, GH * SCALE), Image.Resampling.NEAREST)

    down_img = make_hand(down=True)
    down_path = os.path.join(output_dir, "pat_hand_down.png")
    down_img.save(down_path, "PNG")
    print(f"Created {down_path}")

    up_img = make_hand(down=False)
    up_path = os.path.join(output_dir, "pat_hand_up.png")
    up_img.save(up_path, "PNG")
    print(f"Created {up_path}")

if __name__ == "__main__":
    generate_ponyo_ghost_avatars(os.path.join(os.path.dirname(os.path.abspath(__file__)), "avatars"))

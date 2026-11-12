import os
from PIL import Image

PROJECT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))


def generate_pixel_ghost(output_dir=None):
    output_dir = output_dir or os.path.join(PROJECT_DIR, "avatars")
    os.makedirs(output_dir, exist_ok=True)
    
    # Canvas size for pixel art (72 x 72 pixels)
    GW, GH = 72, 72
    SCALE = 8  # Scales 72x72 -> 576x576 crisp pixel art

    # Color Palette
    C_TRANS = (0, 0, 0, 0)
    C_OUTLINE = (38, 42, 58, 255)       # Dark slate outline
    C_WHITE = (255, 255, 255, 255)      # Primary body
    C_HIGHLIGHT = (255, 255, 255, 255)
    C_SHADOW_1 = (222, 230, 242, 255)   # Light soft cool shadow
    C_SHADOW_2 = (188, 198, 218, 255)   # Deeper crease shadow
    C_EYE = (24, 24, 32, 255)           # Bead eyes
    C_BLUSH = (255, 175, 195, 200)      # Soft pastel pink blush
    C_MOUTH_OPEN = (160, 45, 65, 255)   # Inside mouth
    C_TONGUE = (255, 130, 150, 255)     # Tongue

    def draw_base_ghost(mouth_open=False):
        img = Image.new("RGBA", (GW, GH), C_TRANS)
        pixels = img.load()

        # Helper functions
        def set_px(x, y, color):
            if 0 <= x < GW and 0 <= y < GH:
                pixels[x, y] = color

        def fill_rect(x1, y1, x2, y2, color):
            for x in range(x1, x2 + 1):
                for y in range(y1, y2 + 1):
                    set_px(x, y, color)

        # Center X is 35 (half of 72)
        cx = 35

        # 1. BODY SILHOUETTE (Dome top flaring into wavy skirt)
        # Scanline generation for the ghost sheet
        # Top dome starts around Y = 10, bottom ripples end around Y = 62
        for y in range(10, 63):
            # Width radius at row Y
            if y < 26:
                # Hemispherical dome
                dy = 26 - y
                r = int((16**2 - dy**2)**0.5) if dy <= 16 else 0
                rx = max(r, 1)
            elif y < 44:
                # Vertical cylindrical torso
                rx = 16 + int((y - 26) * 0.25)
            else:
                # Flaring sheet/skirt
                progress = (y - 44) / 18.0
                rx = int(18 + progress * 7)

            # Left and right boundary
            lx = cx - rx
            rx_bound = cx + rx

            # Draw horizontal slice of body
            for x in range(lx, rx_bound + 1):
                # Default body fill
                col = C_WHITE

                # Shading on right side (3D volume)
                if x > rx_bound - 3:
                    col = C_SHADOW_1

                # Bottom ripples and folds (Y >= 46)
                if y >= 46:
                    # Wave pattern with 5 folds across the skirt
                    wave = (x - lx) % 7
                    if wave in [0, 1] or x < lx + 2 or x > rx_bound - 2:
                        col = C_SHADOW_1 if y < 58 else C_SHADOW_2
                    elif wave == 2 and y > 54:
                        col = C_SHADOW_1

                set_px(x, y, col)

        # Scalloped bottom ripples (carving out empty spaces between ripples)
        scallop_dents = [cx - 18, cx - 10, cx - 2, cx + 6, cx + 14]
        for sx in scallop_dents:
            set_px(sx, 61, C_TRANS)
            set_px(sx + 1, 61, C_TRANS)
            set_px(sx, 62, C_TRANS)
            set_px(sx + 1, 62, C_TRANS)
            set_px(sx, 60, C_SHADOW_2)
            set_px(sx + 1, 60, C_SHADOW_2)

        # 2. OUTSTRETCHED ARMS (Stubby nubs reaching forward/upward)
        # Left Arm (reaches forward-left from x=20..27, y=34..39)
        fill_rect(20, 36, 26, 39, C_WHITE)
        fill_rect(19, 35, 23, 38, C_WHITE)
        # Left arm shadow underneath
        for ax in range(20, 27):
            set_px(ax, 40, C_SHADOW_1)

        # Right Arm (reaches forward-right from x=44..51, y=34..39)
        fill_rect(44, 36, 50, 39, C_WHITE)
        fill_rect(47, 35, 51, 38, C_WHITE)
        # Right arm shadow underneath
        for ax in range(44, 51):
            set_px(ax, 40, C_SHADOW_1)

        # 3. EYES (Vertical bead-like ovals just above arm level)
        # Spaced apart symmetrically, vertical oval 3x5 pixels
        eye_y = 28
        left_eye_x = cx - 7   # 28
        right_eye_x = cx + 5  # 40

        for ex in [left_eye_x, right_eye_x]:
            fill_rect(ex, eye_y, ex + 2, eye_y + 4, C_EYE)
            # Soft rounded corners for the eye bead
            set_px(ex, eye_y, C_WHITE)
            set_px(ex + 2, eye_y, C_WHITE)
            set_px(ex, eye_y + 4, C_WHITE)
            set_px(ex + 2, eye_y + 4, C_WHITE)

        # 4. CHEEKS (Cute blush under the eyes)
        fill_rect(left_eye_x - 3, eye_y + 5, left_eye_x - 1, eye_y + 6, C_BLUSH)
        fill_rect(right_eye_x + 3, eye_y + 5, right_eye_x + 5, eye_y + 6, C_BLUSH)

        # 5. MOUTH (Closed vs Open)
        if not mouth_open:
            # Cute subtle closed mouth smile
            set_px(cx - 1, eye_y + 5, C_OUTLINE)
            set_px(cx, eye_y + 6, C_OUTLINE)
            set_px(cx + 1, eye_y + 5, C_OUTLINE)
        else:
            # Happy open mouth for talking
            fill_rect(cx - 2, eye_y + 4, cx + 2, eye_y + 8, C_OUTLINE)
            fill_rect(cx - 1, eye_y + 5, cx + 1, eye_y + 7, C_MOUTH_OPEN)
            # Tongue
            set_px(cx - 1, eye_y + 7, C_TONGUE)
            set_px(cx, eye_y + 7, C_TONGUE)
            set_px(cx + 1, eye_y + 7, C_TONGUE)

        # 6. PIXEL ART OUTLINE (Auto-generate clean 1-pixel border around opaque pixels)
        outlined = Image.new("RGBA", (GW, GH), C_TRANS)
        out_pix = outlined.load()

        # Copy body pixels
        for x in range(GW):
            for y in range(GH):
                if pixels[x, y][3] > 0:
                    out_pix[x, y] = pixels[x, y]

        # Add outline around non-transparent edges
        for x in range(GW):
            for y in range(GH):
                if pixels[x, y][3] == 0:
                    # Check neighbors
                    has_neighbor = False
                    for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                        nx, ny = x + dx, y + dy
                        if 0 <= nx < GW and 0 <= ny < GH and pixels[nx, ny][3] > 0:
                            has_neighbor = True
                            break
                    if has_neighbor:
                        out_pix[x, y] = C_OUTLINE

        # Scale up using Nearest Neighbor to maintain authentic, sharp pixel art
        final_img = outlined.resize((GW * SCALE, GH * SCALE), Image.Resampling.NEAREST)
        return final_img

    # Generate and save both states
    img_closed = draw_base_ghost(mouth_open=False)
    closed_path = os.path.join(output_dir, "closed.png")
    img_closed.save(closed_path, "PNG")
    print(f"Created {closed_path}")

    img_open = draw_base_ghost(mouth_open=True)
    open_path = os.path.join(output_dir, "open.png")
    img_open.save(open_path, "PNG")
    print(f"Created {open_path}")

if __name__ == "__main__":
    project_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    generate_pixel_ghost(os.path.join(project_dir, "avatars"))

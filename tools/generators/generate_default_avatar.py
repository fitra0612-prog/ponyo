import os
from PIL import Image, ImageDraw

PROJECT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))


def create_default_avatars(output_dir=None):
    output_dir = output_dir or os.path.join(PROJECT_DIR, "avatars")
    os.makedirs(output_dir, exist_ok=True)
    width, height = 512, 512
    
    def draw_base_character():
        # Transparent canvas
        img = Image.new("RGBA", (width, height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        
        # Hair back
        draw.ellipse([100, 100, 412, 420], fill=(255, 140, 180, 255))
        
        # Face / Head
        draw.ellipse([126, 130, 386, 390], fill=(255, 235, 220, 255))
        
        # Cheeks blush
        draw.ellipse([145, 275, 195, 305], fill=(255, 170, 180, 140))
        draw.ellipse([317, 275, 367, 305], fill=(255, 170, 180, 140))
        
        # Eyes
        # Left eye
        draw.ellipse([170, 215, 225, 280], fill=(60, 40, 90, 255))
        draw.ellipse([185, 225, 205, 245], fill=(255, 255, 255, 255))
        draw.ellipse([195, 255, 210, 270], fill=(180, 140, 240, 255))
        
        # Right eye
        draw.ellipse([287, 215, 342, 280], fill=(60, 40, 90, 255))
        draw.ellipse([302, 225, 322, 245], fill=(255, 255, 255, 255))
        draw.ellipse([312, 255, 327, 270], fill=(180, 140, 240, 255))
        
        # Eyebrows
        draw.arc([170, 190, 220, 215], start=200, end=340, fill=(180, 70, 100, 255), width=4)
        draw.arc([292, 190, 342, 215], start=200, end=340, fill=(180, 70, 100, 255), width=4)
        
        # Hair front (bangs)
        draw.pieslice([116, 90, 396, 260], start=180, end=360, fill=(255, 140, 180, 255))
        draw.polygon([(116, 175), (170, 220), (200, 175)], fill=(255, 140, 180, 255))
        draw.polygon([(190, 175), (256, 230), (280, 175)], fill=(255, 140, 180, 255))
        draw.polygon([(270, 175), (342, 220), (396, 175)], fill=(255, 140, 180, 255))
        
        # Cat ears / hair accessory
        draw.polygon([(110, 130), (160, 40), (210, 120)], fill=(255, 120, 160, 255))
        draw.polygon([(130, 120), (160, 65), (195, 115)], fill=(255, 210, 225, 255))
        draw.polygon([(302, 120), (352, 40), (402, 130)], fill=(255, 120, 160, 255))
        draw.polygon([(317, 115), (352, 65), (382, 120)], fill=(255, 210, 225, 255))
        
        # Nose
        draw.ellipse([253, 270, 259, 276], fill=(220, 150, 140, 255))
        
        # Body / Shoulders
        draw.ellipse([140, 370, 372, 540], fill=(70, 80, 130, 255))
        draw.polygon([(220, 370), (256, 420), (292, 370)], fill=(255, 255, 255, 255))
        # Ribbon
        draw.ellipse([240, 410, 272, 435], fill=(255, 90, 120, 255))
        draw.polygon([(230, 410), (205, 430), (235, 440)], fill=(255, 100, 130, 255))
        draw.polygon([(282, 410), (307, 430), (277, 440)], fill=(255, 100, 130, 255))
        
        return img, draw

    # 1. Closed mouth avatar
    img_closed, draw_c = draw_base_character()
    # Cute closed smile
    draw_c.arc([236, 290, 276, 318], start=20, end=160, fill=(160, 60, 60, 255), width=5)
    closed_path = os.path.join(output_dir, "closed.png")
    img_closed.save(closed_path, "PNG")
    print(f"Created {closed_path}")

    # 2. Open mouth avatar
    img_open, draw_o = draw_base_character()
    # Cheerful open mouth
    draw_o.pieslice([232, 292, 280, 335], start=0, end=180, fill=(180, 50, 60, 255))
    # Teeth / tongue
    draw_o.chord([234, 293, 278, 305], start=0, end=180, fill=(255, 255, 255, 255))
    draw_o.chord([240, 315, 272, 333], start=0, end=180, fill=(255, 140, 150, 255))
    open_path = os.path.join(output_dir, "open.png")
    img_open.save(open_path, "PNG")
    print(f"Created {open_path}")

if __name__ == "__main__":
    create_default_avatars()

"""Regression tests for Ponyo's accessory wardrobe."""
import os
import tempfile

from tools.generators.generate_accessories import generate_all_accessories


def test_generated_wardrobe_has_new_accessories_without_cat_ears():
    with tempfile.TemporaryDirectory() as temp_dir:
        generate_all_accessories(temp_dir)
        names = {name[:-4] for name in os.listdir(temp_dir) if name.endswith(".png")}
    assert "angel_halo" in names
    assert "devil_horns" in names
    assert "cat_ears" not in names


def test_display_source_uses_new_cycle_entries():
    with open("vtuber_display.py", "r", encoding="utf-8") as handle:
        source = handle.read()
    assert '"angel_halo"' in source
    assert '"devil_horns"' in source
    assert '"cat_ears"' not in source


def _base_pixel(image, x, y, scale=9):
    return image.getpixel((x * scale + scale // 2, y * scale + scale // 2))


def _load_generated(name):
    temp_dir = tempfile.TemporaryDirectory()
    generate_all_accessories(temp_dir.name)
    Image = __import__("PIL.Image", fromlist=["Image"])
    source = Image.open(os.path.join(temp_dir.name, name))
    image = source.copy()
    source.close()
    temp_dir.cleanup()
    return image


def test_halo_is_an_open_floating_ring_not_a_robot_body():
    halo = _load_generated("angel_halo.png")
    outline = (28, 30, 42)
    gold = (255, 220, 55)
    # Wide but light stepped halo silhouette.
    assert _base_pixel(halo, 31, 9)[:3] == outline
    assert _base_pixel(halo, 9, 19)[:3] == outline
    assert _base_pixel(halo, 54, 19)[:3] == outline
    assert _base_pixel(halo, 31, 29)[:3] == outline
    # Gold ring bands surround a large open centre.
    assert _base_pixel(halo, 31, 12)[:3] == (255, 248, 190)
    assert _base_pixel(halo, 13, 19)[:3] == gold
    assert _base_pixel(halo, 31, 26)[:3] == (225, 165, 25)
    assert _base_pixel(halo, 31, 16)[3] == 0
    assert _base_pixel(halo, 31, 20)[3] == 0
    assert _base_pixel(halo, 24, 19)[3] == 0
    # No solid lower body, screen, or feet: the opening spans the centre.
    assert _base_pixel(halo, 31, 22)[3] == 0


def test_halo_is_symmetric_floating_and_not_cropped():
    halo = _load_generated("angel_halo.png")
    for y in range(9, 30):
        for x in range(64):
            mirror = 63 - x
            assert halo.getpixel((x * 9 + 4, y * 9 + 4)) == halo.getpixel((mirror * 9 + 4, y * 9 + 4))
    assert _base_pixel(halo, 9, 26)[3] == 0
    assert _base_pixel(halo, 54, 26)[3] == 0
    assert _base_pixel(halo, 31, 17)[3] == 0
    assert _base_pixel(halo, 31, 35)[3] == 0


def test_horns_curve_inward_with_vertical_tips():
    with tempfile.TemporaryDirectory() as temp_dir:
        generate_all_accessories(temp_dir)
        Image = __import__("PIL.Image", fromlist=["Image"])
        with Image.open(os.path.join(temp_dir, "devil_horns.png")) as source:
            horns = source.copy()
    # Left tip starts outward and its lower body moves inward.
    assert _base_pixel(horns, 12, 3)[3] > 0
    assert _base_pixel(horns, 20, 16)[3] > 0
    # Right side mirrors the left.
    assert _base_pixel(horns, 50, 3)[3] > 0
    assert _base_pixel(horns, 42, 16)[3] > 0
    assert _base_pixel(horns, 31, 16)[3] == 0


if __name__ == "__main__":
    tests = [
        test_generated_wardrobe_has_new_accessories_without_cat_ears,
        test_display_source_uses_new_cycle_entries,
        test_halo_is_an_open_floating_ring_not_a_robot_body,
        test_halo_is_symmetric_floating_and_not_cropped,
        test_horns_curve_inward_with_vertical_tips,
    ]
    for test in tests:
        test()
    print("Accessory tests passed")

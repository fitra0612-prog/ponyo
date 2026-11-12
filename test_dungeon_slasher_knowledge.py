from dungeon_slasher_knowledge import (
    DUNGEON_SLASHER_KNOWLEDGE_PROMPT,
    get_dungeon_slasher_context,
)
from yapping_catalog import classify_screen, get_yapping_angle, get_fallback_yap


def test_dungeon_slasher_is_classified_separately():
    assert classify_screen("DUNGEON SLASHER - Steam") == "GAME_DUNGEON_SLASHER"


def test_knowledge_prompt_contains_core_mechanics():
    lowered = DUNGEON_SLASHER_KNOWLEDGE_PROMPT.lower()
    for term in ("roguelike", "artifact", "skill", "synergy", "boss"):
        assert term in lowered


def test_context_is_short_and_in_character():
    context = get_dungeon_slasher_context()
    assert len(context) <= 2200
    assert "PENGETAHUAN KHUSUS PONYO" in context


def test_dungeon_yapping_catalog_has_varied_fallbacks():
    angle = get_yapping_angle("GAME_DUNGEON_SLASHER", 0)
    fallback = get_fallback_yap("GAME_DUNGEON_SLASHER")
    assert angle
    assert fallback
    assert "catur" not in fallback.lower()


if __name__ == "__main__":
    for test in (
        test_dungeon_slasher_is_classified_separately,
        test_knowledge_prompt_contains_core_mechanics,
        test_context_is_short_and_in_character,
        test_dungeon_yapping_catalog_has_varied_fallbacks,
    ):
        test()
    print("Dungeon Slasher knowledge tests passed")

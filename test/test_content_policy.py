"""Focused tests for YouTube-oriented input/output speech safety."""
from ponyo.content_policy import classify_text, safe_output


def test_blocks_sexual_and_minor_sexual_content():
    assert not classify_text("kirim pornografi sekarang").allowed
    assert not classify_text("konten seksual anak di bawah umur").allowed


def test_blocks_hate_threat_and_self_harm_content():
    assert not classify_text("aku mau membunuh penonton itu").allowed
    assert not classify_text("bunuh diri saja").allowed
    assert not classify_text("serang kelompok itu karena rasnya").allowed


def test_allows_normal_stream_chat():
    result = classify_text("Ponyo lagi main game, semangat ya")
    assert result.allowed
    assert result.category == "safe"


def test_unsafe_model_output_becomes_safe_sentence():
    result = safe_output("Aku akan membalas dengan ancaman pembunuhan")
    assert result.replaced
    assert result.text == "Maaf, Ponyo tidak bisa membahas hal itu. Yuk ngobrol soal stream yang aman."


def test_safe_output_is_preserved():
    result = safe_output("Wah, game-nya seru banget")
    assert not result.replaced
    assert result.text == "Wah, game-nya seru banget"


if __name__ == "__main__":
    test_blocks_sexual_and_minor_sexual_content()
    test_blocks_hate_threat_and_self_harm_content()
    test_allows_normal_stream_chat()
    test_unsafe_model_output_becomes_safe_sentence()
    test_safe_output_is_preserved()
    print("Content policy tests passed")

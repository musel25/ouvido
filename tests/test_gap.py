import pytest
from ouvido.gap import render_gap
from ouvido.schema import Note, ValidationError


def note(sent2: str, span: str) -> Note:
    return Note(item="dar um jeito", gloss="to sort it out", sent1="Dá um jeito aí.",
                sent1_en="Sort it out.", sent2=sent2, sent2_en="He'll sort it out.",
                sent2_span=span, stratum="chunk", rules=["R5"])


def test_blanks_the_inflected_span_not_the_citation_form():
    n = note("Ele deu um jeito nisso ontem.", "deu um jeito")
    assert render_gap(n) == "Ele _____ nisso ontem."


def test_preserves_surrounding_punctuation():
    n = note("Relaxa, ele deu um jeito!", "deu um jeito")
    assert render_gap(n) == "Relaxa, ele _____!"


def test_case_insensitive_match_at_sentence_start():
    n = note("Deu um jeito, como sempre.", "deu um jeito")
    assert render_gap(n) == "_____, como sempre."


def test_custom_blank():
    n = note("Ele deu um jeito nisso.", "deu um jeito")
    assert render_gap(n, blank="[...]") == "Ele [...] nisso."


def test_missing_span_raises():
    with pytest.raises(ValidationError):
        render_gap(note("Ele resolveu isso.", "deu um jeito"))

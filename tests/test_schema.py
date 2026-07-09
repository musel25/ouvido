import pytest
from ouvido.schema import Note, ValidationError, validate_note, validate_deck


def good(**over) -> Note:
    base = dict(
        item="a fim de", item_full="", gloss="up for, in the mood to",
        sent1="Cê tá a fim de sair hoje?", sent1_en="You up for going out today?",
        sent2="Eu tava a fim de pizza ontem.", sent2_en="I was in the mood for pizza yesterday.",
        sent2_span="a fim de", notes="Fixed expression.", cuidado="", ear="",
        stratum="chunk", rules=["R5"],
    )
    base.update(over)
    return Note(**base)


def test_valid_note_passes():
    validate_note(good())


def test_span_must_occur_in_sent2():
    with pytest.raises(ValidationError, match="span not found"):
        validate_note(good(sent2_span="nunca aparece"))


def test_span_must_occur_exactly_once():
    n = good(sent2="A fim de tudo, a fim de nada.", sent2_span="a fim de")
    with pytest.raises(ValidationError, match="exactly once"):
        validate_note(n)


def test_sent1_must_differ_from_sent2():
    with pytest.raises(ValidationError, match="Sent1 == Sent2"):
        validate_note(good(sent2=good().sent1, sent2_span="a fim de"))


def test_gloss_required():
    with pytest.raises(ValidationError, match="gloss"):
        validate_note(good(gloss="  "))


def test_rules_must_be_known_and_nonempty():
    with pytest.raises(ValidationError, match="rule"):
        validate_note(good(rules=[]))
    with pytest.raises(ValidationError, match="rule"):
        validate_note(good(rules=["R9"]))


def test_duplicate_items_rejected_across_deck():
    with pytest.raises(ValidationError, match="duplicate item"):
        validate_deck([good(), good()])


def test_distinct_items_accepted_across_deck():
    validate_deck([good(), good(item="dar um jeito", sent2_span="dar um jeito",
                               sent2="Ele vai dar um jeito nisso.")])

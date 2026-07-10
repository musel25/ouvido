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


def test_span_may_not_blank_far_more_than_the_item():
    """The cloze answer must be recoverable. Blanking six words when the item is
    one turns Card 3 into a guessing game."""
    with pytest.raises(ValidationError, match="span too long"):
        validate_note(good(item="pegar", gloss="to grab",
                           sent2="Vou pegar o ônibus das sete hoje.",
                           sent2_span="pegar o ônibus das sete"))


def test_span_may_absorb_interposed_words():
    """`deixar na mão` really surfaces as `deixa a gente na mão` -- two extra
    tokens for an interposed object is legitimate, not sloppy."""
    validate_note(good(item="deixar na mão", gloss="to let someone down",
                       sent1="Ele deixou na mão.",
                       sent2="Não deixa a gente na mão agora.",
                       sent2_span="deixa a gente na mão"))


def test_parenthetical_disambiguator_does_not_count_toward_item_length():
    validate_note(good(item="ficar (tornar-se)", gloss="to become",
                       sent1="Ela ficou brava.",
                       sent2="A conta ficou cara demais.",
                       sent2_span="ficou cara"))


def test_note_from_dict_ignores_build_metadata():
    """Rows carry build-time keys (`fonte`) that are tags, not note content.

    Without this, push-notes dies with
    TypeError: Note.__init__() got an unexpected keyword argument 'fonte'
    """
    from ouvido.schema import note_from_dict
    row = dict(item="mala", gloss="suitcase", sent1="Cadê a mala?", sent1_en="Where's the suitcase?",
               sent2="Perdi a mala no aeroporto.", sent2_en="I lost the suitcase at the airport.",
               sent2_span="mala", stratum="falso-amigo", rules=["R2"],
               fonte="pois-nao", unexpected_key=123)
    note = note_from_dict(row)
    assert note.item == "mala"
    assert not hasattr(note, "fonte")

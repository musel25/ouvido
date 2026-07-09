from ouvido.notetype import MODEL_NAME, FIELDS, TEMPLATES, CSS, fields_for
from ouvido.schema import Note


def n() -> Note:
    return Note(item="a fim de", gloss="up for", sent1="Cê tá a fim?", sent1_en="You up for it?",
                sent2="Tava a fim de pizza.", sent2_en="I was up for pizza.",
                sent2_span="a fim de", stratum="chunk", rules=["R5"], cuidado="", ear="")


def test_item_is_first_field_so_it_is_the_duplicate_key():
    assert FIELDS[0] == "Item"


def test_three_templates_named_correctly():
    assert [t["Name"] for t in TEMPLATES] == ["Listen", "Read", "Cloze"]


def test_listen_front_has_audio_and_no_sentence_text():
    front = TEMPLATES[0]["Front"]
    assert "{{Sent1Audio}}" in front
    assert "{{Sent1}}" not in front       # the whole point: no text on the front
    assert "{{Gloss}}" not in front


def test_read_front_has_no_audio_so_it_can_be_reviewed_silently():
    front = TEMPLATES[1]["Front"]
    assert "{{Item}}" in front
    assert "Audio" not in front


def test_cloze_front_shows_gap_not_answer():
    front = TEMPLATES[2]["Front"]
    assert "{{Sent2Gap}}" in front
    assert "{{Sent2}}" not in front.replace("{{Sent2Gap}}", "").replace("{{Sent2Audio}}", "")


def test_conditional_cuidado_and_ear():
    for t in TEMPLATES:
        if "{{Cuidado}}" in t["Back"]:
            assert "{{#Cuidado}}" in t["Back"]
        if "{{Ear}}" in t["Back"]:
            assert "{{#Ear}}" in t["Back"]


def test_css_supports_night_mode():
    assert ".nightMode" in CSS


def test_fields_for_maps_every_declared_field():
    f = fields_for(n(), gap="Tava _____ pizza.")
    assert set(f) == set(FIELDS)
    assert f["Sent2Gap"] == "Tava _____ pizza."
    assert f["Sent1Audio"].startswith("[sound:ouv_")
    assert f["Cuidado"] == ""

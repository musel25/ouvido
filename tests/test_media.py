import hashlib
from ouvido.media import media_name, speakable, clips_for, VOICES
from ouvido.schema import Note


def n() -> Note:
    return Note(item="ficar (tornar-se)", gloss="to become",
                sent1="Ela ficou brava.", sent1_en="She got angry.",
                sent2="A conta ficou cara.", sent2_en="The bill turned out expensive.",
                sent2_span="ficou", stratum="estrutura", rules=["R6"])


def test_media_name_is_content_addressed_and_stable():
    a = media_name("a fim de", "s1")
    b = media_name("a fim de", "s1")
    assert a == b
    expect = hashlib.sha1("a fim de".encode()).hexdigest()[:10]
    assert a == f"ouv_{expect}_s1.mp3"


def test_media_name_differs_by_slot_and_item():
    assert media_name("x", "s1") != media_name("x", "s2")
    assert media_name("x", "s1") != media_name("y", "s1")


def test_speakable_strips_disambiguator():
    assert speakable("ficar (tornar-se)") == "ficar"
    assert speakable("a fim de") == "a fim de"


def test_clips_for_yields_three_clips_with_correct_voices():
    clips = clips_for(n())
    assert len(clips) == 3
    texts = {c[0] for c in clips}
    assert "ficar" in texts                      # speakable item, not "ficar (tornar-se)"
    assert "Ela ficou brava." in texts
    assert "A conta ficou cara." in texts
    by_text = {c[0]: c[1] for c in clips}
    assert by_text["Ela ficou brava."] == VOICES["s1"]
    assert by_text["A conta ficou cara."] == VOICES["s2"]
    assert by_text["Ela ficou brava."] != by_text["A conta ficou cara."]


def test_clips_use_full_item_string_for_hashing_not_speakable():
    # the disambiguator must participate in the filename, or ficar(x)/ficar(y) collide
    clips = clips_for(n())
    names = {c[2] for c in clips}
    assert media_name("ficar (tornar-se)", "item") in names

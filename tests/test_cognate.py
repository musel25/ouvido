from ouvido.cognate import similarity, is_transparent, should_exclude, strip_accents


def test_strip_accents():
    assert strip_accents("coração") == "coracao"
    assert strip_accents("ÀÉÎÕÜ") == "AEIOU"


def test_identical_words_are_transparent():
    assert is_transparent("hospital", "hospital")
    assert similarity("hospital", "hospital") == 1.0


def test_near_identical_cognates_are_transparent():
    assert is_transparent("importante", "importante")
    assert is_transparent("problema", "problema")
    assert is_transparent("necessário", "necesario")


def test_opaque_words_are_not_transparent():
    assert not is_transparent("bagunça", "desorden")
    assert not is_transparent("cadê", "dónde está")


def test_transparent_word_excluded_when_no_override():
    assert should_exclude("hospital", "hospital", rules=["R1"])


def test_false_friend_never_excluded_despite_similarity():
    # esquisito/exquisito are near-identical strings with opposite meanings.
    assert is_transparent("esquisito", "exquisito")
    assert not should_exclude("esquisito", "exquisito", rules=["R2"])


def test_phonological_trap_never_excluded_despite_similarity():
    # presidente is a perfect cognate but sounds alien: [pɾeziˈdẽtʃi]
    assert is_transparent("presidente", "presidente")
    assert not should_exclude("presidente", "presidente", rules=["R7"])


def test_opaque_word_kept():
    assert not should_exclude("bagunça", "desorden", rules=["R1"])

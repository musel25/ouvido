from ouvido.candidates import Candidate, filter_candidates

FREQS = {"bagunça": 400, "hospital": 900, "esquisito": 300, "inventado": 1}


def test_transparent_cognate_rejected_with_reason():
    kept, rejected = filter_candidates(
        [Candidate("hospital", "hospital", "lexico", ["R1"], 12)], FREQS)
    assert kept == []
    assert rejected[0]["item"] == "hospital"
    assert "transparent" in rejected[0]["reason"]


def test_false_friend_survives_transparency():
    kept, rejected = filter_candidates(
        [Candidate("esquisito", "exquisito", "falso-amigo", ["R2"], 800)], FREQS)
    assert [c.item for c in kept] == ["esquisito"]
    assert rejected == []


def test_unattested_item_rejected():
    # The Spanish gloss must NOT be a near-cognate of the item, or the
    # transparency check fires first and this test never reaches attestation.
    # sim("inventado", "palabra rara") = 0.095 — safely opaque.
    kept, rejected = filter_candidates(
        [Candidate("inventado", "palabra rara", "lexico", ["R1"], None)], FREQS)
    assert kept == []
    assert "unattested" in rejected[0]["reason"]


def test_opaque_attested_item_kept():
    kept, _ = filter_candidates([Candidate("bagunça", "desorden", "lexico", ["R1"], 700)], FREQS)
    assert [c.item for c in kept] == ["bagunça"]


def test_multiword_chunks_skip_the_single_word_attestation_check():
    # "dar um jeito" is never a SUBTLEX unigram; attestation happens in Task 12
    kept, rejected = filter_candidates(
        [Candidate("dar um jeito", "apañárselas", "chunk", ["R5"], None)], FREQS)
    assert [c.item for c in kept] == ["dar um jeito"]
    assert rejected == []


def test_nothing_is_dropped_silently():
    cands = [Candidate("hospital", "hospital", "lexico", ["R1"], 12),
             Candidate("inventado", "palabra rara", "lexico", ["R1"], None)]
    kept, rejected = filter_candidates(cands, FREQS)
    assert len(kept) + len(rejected) == len(cands)


def test_spoken_only_forms_skip_attestation():
    """A written corpus cannot attest a spoken-only spelling.

    `falano` (falando) and `tavam` (estavam) are how Brazilians SAY these words;
    subtitles spell them the standard way, so SUBTLEX will never contain them.
    Gating them on attestation would delete the reductions stratum outright.
    """
    kept, rejected = filter_candidates(
        [Candidate("falano", "hablando", "reducao", ["R3"], None),
         Candidate("putz", "uf, vaya", "marcador", ["R4"], None)], FREQS)
    assert {c.item for c in kept} == {"falano", "putz"}
    assert rejected == []


def test_hyphenated_item_skips_attestation():
    """`puxa-saco` is a real word; SUBTLEX tokenises the hyphen and never lists it."""
    kept, rejected = filter_candidates(
        [Candidate("puxa-saco", "pelota, lameculos", "lexico", ["R1"], None)], FREQS)
    assert [c.item for c in kept] == ["puxa-saco"]


def test_lexico_single_word_still_gated_on_attestation():
    """The exemptions must not disable attestation where we actually claim it."""
    kept, rejected = filter_candidates(
        [Candidate("inventado", "palabra rara", "lexico", ["R1"], None)], FREQS)
    assert kept == []
    assert "unattested" in rejected[0]["reason"]


def test_duplicate_items_are_merged_not_dropped():
    """The same item can be proposed by two strata (`pelo` is a contraction AND
    a false friend). Anki keys on Item, so only one note may survive -- but the
    rules must be UNIONED, or `pelo` loses its R2 protection."""
    kept, rejected = filter_candidates([
        Candidate("pelo", "por el; ojo: ES pelo = cabelo", "falso-amigo", ["R2"], None),
        Candidate("pelo", "por el (contracción por+o)", "reducao", ["R3"], None),
    ], FREQS)
    assert len(kept) == 1
    assert sorted(kept[0].rules) == ["R2", "R3"]
    assert len(rejected) == 1
    assert "duplicate" in rejected[0]["reason"]


def test_dedupe_keeps_the_most_informative_occurrence():
    kept, _ = filter_candidates([
        Candidate("tá ligado", "¿sabes?", "estrutura", ["R1"], None),
        Candidate("tá ligado", "¿sabes?", "marcador", ["R1", "R3", "R4"], None),
    ], FREQS)
    assert len(kept) == 1
    assert kept[0].stratum == "marcador"      # cited more rules
    assert sorted(kept[0].rules) == ["R1", "R3", "R4"]


def test_dedupe_is_case_insensitive_and_accounted_for():
    cands = [Candidate("Né", "¿no?", "marcador", ["R4"], None),
             Candidate("né", "¿no?", "reducao", ["R3"], None)]
    kept, rejected = filter_candidates(cands, FREQS)
    assert len(kept) + len(rejected) == len(cands)   # nothing vanishes silently

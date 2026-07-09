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

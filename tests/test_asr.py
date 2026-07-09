from ouvido.asr import expand, normalize, agreement, check_clip


def test_expand_reductions():
    assert expand("Cê tá a fim de sair?") == "Você está a fim de sair?"
    assert expand("Num sei, sei lá.") == "Não sei, sei lá."
    assert expand("A gente vai pro cinema.") == "A gente vai para o cinema."
    assert expand("Ele tá falano bobagem.") == "Ele está falando bobagem."


def test_expand_is_word_bounded():
    # "tá" must not fire inside "está"; "num" must not fire inside "numeroso"
    assert expand("Ele está numeroso") == "Ele está numeroso"


def test_normalize():
    assert normalize("Você está, né?") == "voce esta ne"


def test_agreement_identical_after_expansion():
    assert agreement("Você está a fim de sair?", "Você está a fim de sair?") == 1.0


def test_check_clip_passes_when_asr_matches_expanded_form():
    # what edge-tts was given vs what Whisper heard (Whisper normalizes spelling)
    assert check_clip("Cê tá a fim de sair?", "Você está a fim de sair?")


def test_check_clip_fails_on_truncation():
    assert not check_clip("Cê tá a fim de sair hoje com a gente?", "Você está")


def test_check_clip_fails_on_empty():
    assert not check_clip("Cê tá bem?", "")

import textwrap
from ouvido.corpus import load_subtlex, ranks, coverage_curve, is_attested


def write_csv(tmp_path):
    p = tmp_path / "subtlex.csv"
    p.write_text(textwrap.dedent("""\
        Word,FREQcount
        que,500
        não,300
        de,150
        você,40
        bagunça,10
        raríssimo,1
    """))
    return str(p)


def test_load_subtlex(tmp_path):
    freqs = load_subtlex(write_csv(tmp_path))
    assert freqs["que"] == 500
    assert freqs["raríssimo"] == 1
    assert len(freqs) == 6


def test_ranks_are_frequency_ordered(tmp_path):
    r = ranks(load_subtlex(write_csv(tmp_path)))
    assert r["que"] == 1
    assert r["não"] == 2
    assert r["raríssimo"] == 6


def test_coverage_curve(tmp_path):
    freqs = load_subtlex(write_csv(tmp_path))          # total = 1001
    cov = coverage_curve(freqs, [1, 3])
    assert abs(cov[1] - 500 / 1001) < 1e-9             # top-1 word
    assert abs(cov[3] - 950 / 1001) < 1e-9             # top-3 words


def test_is_attested(tmp_path):
    freqs = load_subtlex(write_csv(tmp_path))
    assert is_attested("bagunça", freqs, min_freq=5)
    assert not is_attested("raríssimo", freqs, min_freq=5)
    assert not is_attested("inventadinho", freqs, min_freq=5)

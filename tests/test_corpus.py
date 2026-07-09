import textwrap
from ouvido.corpus import load_subtlex, ranks, coverage_curve, is_attested


def write_tsv(tmp_path):
    """Real SUBTLEX-PT-BR is tab-separated with a CDcount and Spellcheck column."""
    p = tmp_path / "subtlex.tsv"
    p.write_text(textwrap.dedent("""\
        Word\tFREQcount\tCDcount\tSpellcheck
        que\t500\t100\tTRUE
        não\t300\t90\tTRUE
        de\t150\t80\tTRUE
        você\t40\t30\tTRUE
        bagunça\t10\t8\tTRUE
        raríssimo\t1\t1\tTRUE
    """), encoding="utf-8")
    return str(p)


def test_load_subtlex_reads_tab_separated(tmp_path):
    freqs = load_subtlex(write_tsv(tmp_path))
    assert freqs["que"] == 500
    assert freqs["raríssimo"] == 1
    assert len(freqs) == 6


def test_load_subtlex_sums_case_duplicates(tmp_path):
    p = tmp_path / "dup.tsv"
    p.write_text("Word\tFREQcount\tCDcount\tSpellcheck\nA\t10\t1\tTRUE\na\t5\t1\tTRUE\n",
                 encoding="utf-8")
    # the real file contains both "A" and "a"; overwriting would lose 10 counts
    assert load_subtlex(str(p))["a"] == 15


def test_ranks_are_frequency_ordered(tmp_path):
    r = ranks(load_subtlex(write_tsv(tmp_path)))
    assert r["que"] == 1
    assert r["não"] == 2
    assert r["raríssimo"] == 6


def test_coverage_curve(tmp_path):
    freqs = load_subtlex(write_tsv(tmp_path))          # total = 1001
    cov = coverage_curve(freqs, [1, 3])
    assert abs(cov[1] - 500 / 1001) < 1e-9             # top-1 word
    assert abs(cov[3] - 950 / 1001) < 1e-9             # top-3 words


def test_is_attested(tmp_path):
    freqs = load_subtlex(write_tsv(tmp_path))
    assert is_attested("bagunça", freqs, min_freq=5)
    assert not is_attested("raríssimo", freqs, min_freq=5)
    assert not is_attested("inventadinho", freqs, min_freq=5)

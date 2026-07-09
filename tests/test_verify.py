import pytest

from ouvido.verify import LENSES, Verdict, ships


def v(lens, passed):
    return Verdict(lens=lens, passed=passed, reason="")


def test_all_pass_ships():
    assert ships([v("naturalness", True), v("semantics", True), v("mechanics", True)])


def test_two_of_three_ships_when_semantics_passes():
    assert ships([v("naturalness", False), v("semantics", True), v("mechanics", True)])


def test_semantics_failure_is_a_veto_even_with_two_passes():
    # a factual error about Spanish cannot be outvoted by two agents who liked the sentence
    assert not ships([v("naturalness", True), v("semantics", False), v("mechanics", True)])


def test_two_failures_does_not_ship():
    assert not ships([v("naturalness", False), v("semantics", True), v("mechanics", False)])


def test_missing_lens_does_not_ship():
    assert not ships([v("semantics", True), v("mechanics", True)])


def test_duplicate_lens_does_not_ship():
    # a lens voting twice would let one agent outvote the veto
    assert not ships([v("semantics", True), v("semantics", True), v("mechanics", True)])


def test_lenses_are_exactly_the_three_named():
    assert set(LENSES) == {"naturalness", "semantics", "mechanics"}

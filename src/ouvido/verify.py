"""Adversarial verification of authored notes.

Three lenses, each prompted to REFUTE rather than approve. Semantics is a veto
lens: a factual error about meaning, or a false claim about Spanish, cannot be
outvoted by two agents who happened to like the sentence.

This rule exists because during research a verifier caught four errors
(`exquisito`, `experto`, `conta`, a duplicated `polvo`) in a hand-written
false-friend list that looked entirely plausible.
"""

from __future__ import annotations

from dataclasses import dataclass

LENSES = ("naturalness", "semantics", "mechanics")

VETO_LENS = "semantics"


@dataclass
class Verdict:
    lens: str
    passed: bool
    reason: str


def ships(verdicts: list[Verdict]) -> bool:
    """A note ships iff every lens voted once, semantics passed, and >=2 passed."""
    by_lens = {v.lens: v for v in verdicts}
    if len(by_lens) != len(verdicts):
        return False  # a lens voted twice; it could outvote the veto
    if set(by_lens) != set(LENSES):
        return False
    if not by_lens[VETO_LENS].passed:
        return False
    return sum(v.passed for v in by_lens.values()) >= 2

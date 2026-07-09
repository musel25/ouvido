"""Exclude what Spanish already gives the learner for free.

A Spanish speaker owns thousands of Portuguese words on sight. Cards spent on
them are wasted. The exceptions are the words where similarity is precisely the
trap: false friends (R2) and phonological traps (R7).
"""
from __future__ import annotations

import unicodedata
from difflib import SequenceMatcher

OVERRIDE_RULES = frozenset({"R2", "R7"})


def strip_accents(s: str) -> str:
    nfkd = unicodedata.normalize("NFKD", s)
    return "".join(c for c in nfkd if not unicodedata.combining(c))


def _norm(s: str) -> str:
    return strip_accents(s.strip().lower())


def similarity(pt: str, es: str) -> float:
    return SequenceMatcher(None, _norm(pt), _norm(es)).ratio()


def is_transparent(pt: str, es: str, threshold: float = 0.80) -> bool:
    return similarity(pt, es) >= threshold


def should_exclude(pt: str, es: str, rules: list[str], threshold: float = 0.80) -> bool:
    if OVERRIDE_RULES & set(rules):
        return False
    return is_transparent(pt, es, threshold)

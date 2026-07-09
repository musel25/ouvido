"""Candidate intake: everything an agent proposes must survive the selection
rule and corpus attestation, and everything rejected is written down."""
from __future__ import annotations

from dataclasses import dataclass

from ouvido.cognate import should_exclude
from ouvido.corpus import is_attested


@dataclass
class Candidate:
    item: str
    es: str
    stratum: str
    rules: list[str]
    subtlex_rank: int | None


def filter_candidates(
    cands: list[Candidate], freqs: dict[str, int]
) -> tuple[list[Candidate], list[dict]]:
    kept: list[Candidate] = []
    rejected: list[dict] = []

    for c in cands:
        if should_exclude(c.item, c.es, c.rules):
            rejected.append({"item": c.item, "reason": "transparent cognate; Spanish gives it free"})
            continue
        # Multi-word chunks are not unigrams; they are attested in Task 12 instead.
        if " " not in c.item.strip() and not is_attested(c.item, freqs):
            rejected.append({"item": c.item, "reason": "unattested in SUBTLEX-PT-BR"})
            continue
        kept.append(c)

    return kept, rejected

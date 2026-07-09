"""Candidate intake: everything an agent proposes must survive the selection
rule and corpus attestation, and everything rejected is written down."""
from __future__ import annotations

from dataclasses import dataclass

from ouvido.cognate import should_exclude
from ouvido.corpus import is_attested

# Rules whose items a WRITTEN corpus structurally cannot attest.
#   R3 reduced forms  — subtitles spell `falando`, nobody writes `falano`
#   R4 discourse markers / interjections — `putz`, `vixe` live in speech
NO_ATTESTATION_RULES = frozenset({"R3", "R4"})


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
        # Attestation only applies to single tokens whose spelling a written
        # corpus could plausibly contain. Multi-word chunks are attested in
        # Task 12; hyphenated words are split by the corpus tokeniser; and
        # spoken-only forms (R3/R4) are absent from subtitles by construction.
        item = c.item.strip()
        multi_token = " " in item or "-" in item
        spoken_only = bool(NO_ATTESTATION_RULES & set(c.rules))
        if not multi_token and not spoken_only and not is_attested(item, freqs):
            rejected.append({"item": c.item, "reason": "unattested in SUBTLEX-PT-BR"})
            continue
        kept.append(c)

    return kept, rejected

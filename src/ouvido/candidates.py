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


# When two strata propose the same item, the surviving note keeps this
# stratum tag. Order = how well the stratum explains the item.
_STRATUM_PRIORITY = ["falso-amigo", "marcador", "reducao", "chunk", "estrutura", "lexico"]


def _dedupe(cands: list[Candidate]) -> tuple[list[Candidate], list[dict]]:
    """Collapse repeated items, UNIONING their rules.

    `Item` is Anki's duplicate key, so only one note per item may survive. But
    dropping the loser's rules would strip protection: `pelo` is proposed by
    `falso-amigo` as R2 and by `reducao` as R3, and it needs both.
    """
    groups: dict[str, list[Candidate]] = {}
    for c in cands:
        groups.setdefault(c.item.strip().lower(), []).append(c)

    kept: list[Candidate] = []
    rejected: list[dict] = []
    for key, group in groups.items():
        if len(group) == 1:
            kept.append(group[0])
            continue
        union = sorted({r for c in group for r in c.rules})
        winner = min(
            group,
            key=lambda c: (-len(c.rules), _STRATUM_PRIORITY.index(c.stratum)
                           if c.stratum in _STRATUM_PRIORITY else len(_STRATUM_PRIORITY)),
        )
        kept.append(Candidate(winner.item, winner.es, winner.stratum, union, winner.subtlex_rank))
        for loser in group:
            if loser is winner:
                continue
            rejected.append({
                "item": loser.item,
                "reason": f"duplicate of {winner.item!r} kept in stratum "
                          f"{winner.stratum!r}; rules merged to {union}",
            })
    return kept, rejected


def filter_candidates(
    cands: list[Candidate], freqs: dict[str, int]
) -> tuple[list[Candidate], list[dict]]:
    cands, rejected = _dedupe(cands)
    kept: list[Candidate] = []

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

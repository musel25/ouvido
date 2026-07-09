"""Note model and the validation rules that gate every pipeline stage."""
from __future__ import annotations

from dataclasses import dataclass

RULES = frozenset({"R1", "R2", "R3", "R4", "R5", "R6", "R7"})
STRATA = frozenset({"reducao", "marcador", "chunk", "falso-amigo", "estrutura", "lexico"})


class ValidationError(Exception):
    pass


@dataclass
class Note:
    item: str
    gloss: str
    sent1: str
    sent1_en: str
    sent2: str
    sent2_en: str
    sent2_span: str
    stratum: str
    rules: list[str]
    item_full: str = ""
    notes: str = ""
    cuidado: str = ""
    ear: str = ""


def _count_ci(haystack: str, needle: str) -> int:
    h, n = haystack.lower(), needle.lower()
    if not n:
        return 0
    count = start = 0
    while (i := h.find(n, start)) != -1:
        count += 1
        start = i + 1
    return count


def locate_span(haystack: str, needle: str) -> tuple[int, int]:
    """Find the one and only occurrence of `needle`, case-insensitively.

    The single source of truth for the gap rule: the blank must have exactly
    one well-defined answer. Both validate_note and gap.render_gap call this,
    so the rule cannot drift between validation and rendering.
    """
    n = _count_ci(haystack, needle)
    if n == 0:
        raise ValidationError(f"span not found in sent2: {needle!r}")
    if n > 1:
        raise ValidationError(f"span must occur exactly once, found {n}")
    start = haystack.lower().find(needle.lower())
    return start, start + len(needle)


def validate_note(note: Note) -> None:
    if not note.item.strip():
        raise ValidationError("item is empty")
    if not note.gloss.strip():
        raise ValidationError("gloss is empty")
    if not note.rules:
        raise ValidationError("note cites no inclusion rule")
    for r in note.rules:
        if r not in RULES:
            raise ValidationError(f"unknown rule {r!r}")
    if note.stratum not in STRATA:
        raise ValidationError(f"unknown stratum {note.stratum!r}")
    if note.sent1.strip() == note.sent2.strip():
        raise ValidationError("Sent1 == Sent2")

    locate_span(note.sent2, note.sent2_span)


def validate_deck(notes: list[Note]) -> None:
    seen: set[str] = set()
    for n in notes:
        validate_note(n)
        key = n.item.strip().lower()
        if key in seen:
            raise ValidationError(f"duplicate item: {n.item!r}")
        seen.add(key)


def note_from_dict(d: dict) -> Note:
    return Note(**d)

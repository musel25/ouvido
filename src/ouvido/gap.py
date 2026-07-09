"""Pre-render the cloze gap. Anki note types cannot be both standard and cloze,
so Card 3's blank is baked into a field at build time."""
from __future__ import annotations

from ouvido.schema import Note, locate_span


def render_gap(note: Note, blank: str = "_____") -> str:
    start, end = locate_span(note.sent2, note.sent2_span)
    return note.sent2[:start] + blank + note.sent2[end:]

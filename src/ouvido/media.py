"""Content-addressed audio. Filenames must not depend on the Anki note ID:
storeMediaFile and addNote both need the name before the note exists."""
from __future__ import annotations

import hashlib
import re

import edge_tts

from ouvido.schema import Note

VOICES = {
    "item": "pt-BR-FranciscaNeural",
    "s1": "pt-BR-FranciscaNeural",
    "s2": "pt-BR-AntonioNeural",
}

_DISAMBIG = re.compile(r"\s*\([^)]*\)\s*$")


def media_name(item: str, slot: str) -> str:
    digest = hashlib.sha1(item.encode("utf-8")).hexdigest()[:10]
    return f"ouv_{digest}_{slot}.mp3"


def speakable(item: str) -> str:
    return _DISAMBIG.sub("", item).strip()


def clips_for(note: Note) -> list[tuple[str, str, str]]:
    return [
        (speakable(note.item), VOICES["item"], media_name(note.item, "item")),
        (note.sent1, VOICES["s1"], media_name(note.item, "s1")),
        (note.sent2, VOICES["s2"], media_name(note.item, "s2")),
    ]


async def synth(text: str, voice: str, out_path: str) -> None:
    await edge_tts.Communicate(text, voice).save(out_path)

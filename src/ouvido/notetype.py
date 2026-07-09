"""The `PT Ouvido` note type: three cards from one note.

Card 1 (Listen) is ear-first with no text on the front — the only card that
tests the ear. Card 2 (Read) keeps audio on the back so reviews work without
headphones. Card 3 (Cloze) uses a pre-baked gap, because an Anki note type
cannot be both standard and cloze.
"""
from __future__ import annotations

from ouvido.media import media_name
from ouvido.schema import Note

MODEL_NAME = "PT Ouvido"

FIELDS = [
    "Item", "ItemFull", "ItemAudio", "Gloss",
    "Sent1", "Sent1Audio", "Sent1EN",
    "Sent2", "Sent2Audio", "Sent2EN", "Sent2Gap",
    "Notes", "Cuidado", "Ear",
]

CSS = """
.card { font-family: -apple-system, system-ui, sans-serif; font-size: 21px;
        text-align: center; color: #1a1a1a; background: #fdfdfd; }
.listen  { font-size: 56px; margin: 28px 0 12px; }
.item    { font-size: 26px; font-weight: 600; }
.gloss   { font-size: 24px; margin: 6px 0 14px; }
.pt      { color: #0b3d2c; }
.en      { color: #555; font-size: 18px; }
.full    { color: #777; font-size: 17px; font-style: italic; }
.notes   { font-size: 17px; color: #333; margin: 14px auto; max-width: 34em; }
.ear     { font-size: 16px; color: #6a4b00; background: #fff8e1;
           padding: 6px 10px; border-radius: 6px; margin: 12px auto; max-width: 34em; }
.cuidado { font-size: 16px; color: #7a1c1c; background: #fdecec;
           padding: 6px 10px; border-radius: 6px; margin: 12px auto; max-width: 34em; }
.ex      { margin: 12px auto; max-width: 34em; text-align: left; }
.nightMode .card    { color: #e8e8e8; background: #1e1e1e; }
.nightMode .pt      { color: #7fd6ac; }
.nightMode .en,
.nightMode .full    { color: #aaa; }
.nightMode .notes   { color: #ddd; }
.nightMode .ear     { color: #ffe08a; background: #3a3116; }
.nightMode .cuidado { color: #ffb3b3; background: #3a1c1c; }
"""

_LISTEN_FRONT = """<div class="listen">🎧</div>
{{Sent1Audio}}"""

_LISTEN_BACK = """{{FrontSide}}
<hr id=answer>
<div class="pt">{{Sent1}}</div>
<div class="en">{{Sent1EN}}</div>
<div class="item">{{Item}} — {{Gloss}}</div>
{{#Ear}}<div class="ear">👂 {{Ear}}</div>{{/Ear}}
{{#Cuidado}}<div class="cuidado">⚠️ {{Cuidado}}</div>{{/Cuidado}}"""

_READ_FRONT = """<div class="item">{{Item}}</div>"""

_READ_BACK = """{{FrontSide}}
<hr id=answer>
<div class="gloss">{{Gloss}}</div>
{{ItemAudio}}
{{#ItemFull}}<div class="full">= {{ItemFull}}</div>{{/ItemFull}}
{{#Notes}}<div class="notes">{{Notes}}</div>{{/Notes}}
{{#Cuidado}}<div class="cuidado">⚠️ {{Cuidado}}</div>{{/Cuidado}}
<div class="ex"><span class="pt">{{Sent1}}</span> {{Sent1Audio}}<br><span class="en">{{Sent1EN}}</span></div>
<div class="ex"><span class="pt">{{Sent2}}</span> {{Sent2Audio}}<br><span class="en">{{Sent2EN}}</span></div>"""

_CLOZE_FRONT = """{{Sent2Audio}}
<div class="pt">{{Sent2Gap}}</div>"""

_CLOZE_BACK = """{{FrontSide}}
<hr id=answer>
<div class="pt">{{Sent2}}</div>
<div class="en">{{Sent2EN}}</div>
{{#Ear}}<div class="ear">👂 {{Ear}}</div>{{/Ear}}"""

TEMPLATES = [
    {"Name": "Listen", "Front": _LISTEN_FRONT, "Back": _LISTEN_BACK},
    {"Name": "Read", "Front": _READ_FRONT, "Back": _READ_BACK},
    {"Name": "Cloze", "Front": _CLOZE_FRONT, "Back": _CLOZE_BACK},
]


def fields_for(note: Note, gap: str) -> dict[str, str]:
    snd = lambda slot: f"[sound:{media_name(note.item, slot)}]"  # noqa: E731
    return {
        "Item": note.item,
        "ItemFull": note.item_full,
        "ItemAudio": snd("item"),
        "Gloss": note.gloss,
        "Sent1": note.sent1,
        "Sent1Audio": snd("s1"),
        "Sent1EN": note.sent1_en,
        "Sent2": note.sent2,
        "Sent2Audio": snd("s2"),
        "Sent2EN": note.sent2_en,
        "Sent2Gap": gap,
        "Notes": note.notes,
        "Cuidado": note.cuidado,
        "Ear": note.ear,
    }

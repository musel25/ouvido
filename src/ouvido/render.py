"""Render Anki templates to standalone HTML.

Lets a card be reviewed in a browser before anything is written to the
collection. Supports the subset of Anki's template syntax the deck uses:
`{{Field}}`, `{{#Field}}…{{/Field}}`, `{{FrontSide}}`, and `[sound:x.mp3]`.
"""

from __future__ import annotations

import re

_SOUND = re.compile(r"\[sound:([^\]]+)\]")
_COND = re.compile(r"\{\{#(\w+)\}\}(.*?)\{\{/\1\}\}", re.DOTALL)
_FIELD = re.compile(r"\{\{(\w+)\}\}")


def _audio(text: str) -> str:
    return _SOUND.sub(r'<audio controls src="\1"></audio>', text)


def render_card(fields: dict, template: dict) -> str:
    def one_side(tpl: str) -> str:
        # conditionals first: an empty field must not leave its wrapper behind
        tpl = _COND.sub(lambda m: m.group(2) if fields.get(m.group(1), "").strip() else "", tpl)
        tpl = _FIELD.sub(lambda m: fields.get(m.group(1), ""), tpl)
        return _audio(tpl)

    front = one_side(template["Front"])
    back_tpl = template["Back"].replace("{{FrontSide}}", front)
    back = one_side(back_tpl) if back_tpl.strip() else ""

    if not back.strip():
        return f'<div class="card">{front}</div>'
    return f'<div class="card">{front}<hr>{back}</div>'

"""ASR round-trip gate.

Whisper outputs standard orthography regardless of what it heard, so a clip
synthesized from "Cê tá" transcribes as "Você está". Comparing ASR output to
the colloquial source would fail every reduced clip. We expand first.

Catches: truncation, empty clips, gross mispronunciation.
Does not catch: unnatural prosody. Only a human ear can (Task 14).
"""
from __future__ import annotations

import re
import unicodedata
from difflib import SequenceMatcher

EXPANSIONS = {
    "cê": "você", "cês": "vocês",
    "tá": "está", "tão": "estão", "tô": "estou", "tava": "estava",
    "num": "não",
    "pra": "para", "pro": "para o",
    "cadê": "onde está",
    "vamo": "vamos",
    "falano": "falando", "falá": "falar",
}

_PUNCT = re.compile(r"[^\w\s]", re.UNICODE)


def expand(text: str) -> str:
    def sub(m: re.Match) -> str:
        word = m.group(0)
        repl = EXPANSIONS.get(word.lower())
        if repl is None:
            return word
        return repl.capitalize() if word[0].isupper() else repl

    pattern = r"\b(" + "|".join(sorted(map(re.escape, EXPANSIONS), key=len, reverse=True)) + r")\b"
    return re.sub(pattern, sub, text, flags=re.IGNORECASE)


def normalize(text: str) -> str:
    nfkd = unicodedata.normalize("NFKD", text.lower())
    stripped = "".join(c for c in nfkd if not unicodedata.combining(c))
    return " ".join(_PUNCT.sub(" ", stripped).split())


def agreement(expected: str, heard: str) -> float:
    return SequenceMatcher(None, normalize(expand(expected)), normalize(heard)).ratio()


def check_clip(expected_text: str, heard_text: str, threshold: float = 0.75) -> bool:
    if not heard_text.strip():
        return False
    return agreement(expected_text, heard_text) >= threshold


def transcribe(paths: list[str], model_size: str = "small") -> dict[str, str]:
    from faster_whisper import WhisperModel

    model = WhisperModel(model_size, device="cpu", compute_type="int8")
    out: dict[str, str] = {}
    for p in paths:
        segments, _ = model.transcribe(p, language="pt", beam_size=5)
        out[p] = "".join(s.text for s in segments).strip()
    return out

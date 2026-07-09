"""SUBTLEX-PT-BR: 61.6M subtitle tokens, the best downloadable proxy for
spoken Brazilian register."""
from __future__ import annotations

import csv


def load_subtlex(path: str) -> dict[str, int]:
    """Tab-separated; `Word` collides after lowercasing ("A"/"a"), so sum."""
    freqs: dict[str, int] = {}
    with open(path, encoding="utf-8", errors="replace") as fh:
        for row in csv.DictReader(fh, delimiter="\t"):
            word = (row["Word"] or "").strip().lower()
            if not word:
                continue
            freqs[word] = freqs.get(word, 0) + int(row["FREQcount"])
    return freqs


def ranks(freqs: dict[str, int]) -> dict[str, int]:
    ordered = sorted(freqs.items(), key=lambda kv: (-kv[1], kv[0]))
    return {w: i for i, (w, _) in enumerate(ordered, start=1)}


def coverage_curve(freqs: dict[str, int], cutoffs: list[int]) -> dict[int, float]:
    total = sum(freqs.values())
    ordered = sorted(freqs.values(), reverse=True)
    return {c: sum(ordered[:c]) / total for c in cutoffs}


def is_attested(word: str, freqs: dict[str, int], min_freq: int = 5) -> bool:
    return freqs.get(word.strip().lower(), 0) >= min_freq

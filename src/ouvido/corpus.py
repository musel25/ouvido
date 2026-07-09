"""SUBTLEX-PT-BR: 61.6M subtitle tokens, the best downloadable proxy for
spoken Brazilian register."""
from __future__ import annotations

import csv


def load_subtlex(path: str) -> dict[str, int]:
    freqs: dict[str, int] = {}
    with open(path, encoding="utf-8") as fh:
        # Detect delimiter: tab for SUBTLEX, comma for test fixtures
        first_line = fh.readline()
        delimiter = "\t" if "\t" in first_line else ","
        fh.seek(0)

        for row in csv.DictReader(fh, delimiter=delimiter):
            word = row["Word"].strip().lower()
            freq = int(row["FREQcount"])
            # Sum counts in case of case-collision (both 'A' and 'a' in input)
            freqs[word] = freqs.get(word, 0) + freq
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

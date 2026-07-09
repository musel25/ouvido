"""Single entry point for every pipeline stage.

Handlers import their heavy dependencies lazily: `--help` must not pull in
edge_tts or faster_whisper.
"""
from __future__ import annotations

import argparse
import json
import os
from typing import Any

_SUBCOMMANDS = [
    ("filter-candidates", "Apply the selection rule and corpus attestation to candidates"),
    ("validate-notes", "Validate authored note batches against the schema"),
    ("apply-verdicts", "Keep only notes that pass the 3-lens verification"),
    ("attest", "Check multi-word chunks against corpus attestation"),
    ("sample", "Render sample cards and synthesize the human-gate clips"),
    ("synth", "Synthesize all clips"),
    ("asr-gate", "Transcribe every clip and flag divergence"),
    ("push-media", "Upload media to Anki via storeMediaFile"),
    ("push-notes", "Add notes to Anki"),
]


def read_json(path: str) -> Any:
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def write_json(path: str, obj: Any) -> None:
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(obj, fh, ensure_ascii=False, indent=2)


def write_jsonl(path: str, rows: list[dict]) -> None:
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        for row in rows:
            fh.write(json.dumps(row, ensure_ascii=False) + "\n")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="ouvido")
    subs = parser.add_subparsers(dest="command")
    for name, help_text in _SUBCOMMANDS:
        sp = subs.add_parser(name, help=help_text)
        sp.add_argument("--in", dest="in_path")
        sp.add_argument("--out", dest="out_path")
        sp.add_argument("--log", dest="log_path")
        sp.add_argument("--notes", dest="notes_path")
        sp.add_argument("--freqs", dest="freqs_path")
        sp.add_argument("--media", dest="media_path")
        sp.add_argument("--verdicts", dest="verdicts_path")
        sp.add_argument("--deck", dest="deck")
        sp.add_argument("--n", dest="n", type=int, default=20)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if not args.command:
        print("no subcommand given; try --help")
        return 2
    raise SystemExit(f"handler for {args.command!r} is implemented in a later task")


if __name__ == "__main__":  # `python -m ouvido.cli <subcommand>`
    raise SystemExit(main())

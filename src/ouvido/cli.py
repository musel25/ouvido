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


def _handle_filter_candidates(args: argparse.Namespace) -> int:
    from ouvido.candidates import Candidate, filter_candidates
    from ouvido.corpus import load_subtlex

    freqs = load_subtlex(args.freqs_path)

    filenames = sorted(f for f in os.listdir(args.in_path) if f.endswith(".json"))
    all_cands: list[Candidate] = []
    for fname in filenames:
        rows = read_json(os.path.join(args.in_path, fname))
        for row in rows:
            all_cands.append(Candidate(
                item=row["item"],
                es=row["es"],
                stratum=row["stratum"],
                rules=row["rules"],
                subtlex_rank=row.get("subtlex_rank"),
            ))

    kept, rejected = filter_candidates(all_cands, freqs)

    write_json(args.out_path, [
        {
            "item": c.item,
            "es": c.es,
            "stratum": c.stratum,
            "rules": c.rules,
            "subtlex_rank": c.subtlex_rank,
        }
        for c in kept
    ])
    write_jsonl(args.log_path, rejected)

    print(f"kept {len(kept)}, rejected {len(rejected)} (from {len(filenames)} files)")
    return 0


def _handle_validate_notes(args) -> int:
    """Validate every authored note batch. Nothing invalid reaches Anki.

    Per-note failures and cross-deck duplicate items are both logged; the log
    file is written even when empty, so "no failures" is an artifact rather
    than an absence.
    """
    import os

    from ouvido.schema import ValidationError, note_from_dict, validate_deck, validate_note

    failures: list[dict] = []
    notes = []
    filenames = sorted(f for f in os.listdir(args.in_path) if f.endswith(".json"))
    for fn in filenames:
        for row in read_json(os.path.join(args.in_path, fn)):
            try:
                note = note_from_dict(row)
                validate_note(note)
            except (ValidationError, TypeError) as e:
                failures.append({"item": row.get("item", "<no item>"), "file": fn, "error": str(e)})
                continue
            notes.append(note)

    try:
        validate_deck(notes)
    except ValidationError as e:
        failures.append({"item": "<deck>", "file": "*", "error": str(e)})

    write_jsonl(args.log_path, failures)
    if failures:
        print(f"FAIL: {len(failures)} invalid, {len(notes)} valid (from {len(filenames)} files)")
        return 1
    print(f"OK: {len(notes)} notes valid (from {len(filenames)} files)")
    return 0



def _handle_apply_verdicts(args) -> int:
    """Keep only notes that survive the three-lens adversarial review.

    An unjudged note never ships: silence is not approval.
    """
    import os

    from ouvido.verify import Verdict, ships

    verdicts_by_item = read_json(args.verdicts_path)

    notes: list[dict] = []
    for fn in sorted(f for f in os.listdir(args.notes_path) if f.endswith(".json")):
        notes.extend(read_json(os.path.join(args.notes_path, fn)))

    shipped: list[dict] = []
    rejected: list[dict] = []
    for note in notes:
        raw = verdicts_by_item.get(note["item"])
        if not raw:
            rejected.append({"item": note["item"], "reason": "no verdicts recorded"})
            continue
        verdicts = [Verdict(lens=v["lens"], passed=bool(v["passed"]), reason=v.get("reason", ""))
                    for v in raw]
        if ships(verdicts):
            shipped.append(note)
        else:
            failed = "; ".join(f"{v.lens}: {v.reason or 'refuted'}" for v in verdicts if not v.passed)
            rejected.append({"item": note["item"], "reason": failed or "insufficient passing lenses"})

    write_json(args.out_path, shipped)
    write_jsonl(args.log_path, rejected)
    print(f"shipping {len(shipped)}, rejected {len(rejected)} (of {len(notes)} notes)")
    return 0


_HANDLERS = {
    "filter-candidates": _handle_filter_candidates,
    "validate-notes": _handle_validate_notes,
    "apply-verdicts": _handle_apply_verdicts,
}


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
    handler = _HANDLERS.get(args.command)
    if handler is None:
        raise SystemExit(f"handler for {args.command!r} is implemented in a later task")
    return handler(args)


if __name__ == "__main__":  # `python -m ouvido.cli <subcommand>`
    raise SystemExit(main())

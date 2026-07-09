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



def _handle_attest(args) -> int:
    """Check multi-word chunks against the corpus, token by token.

    HONEST LIMIT: SUBTLEX-PT-BR is a UNIGRAM frequency list. It cannot attest
    that "dar um jeito" occurs as a phrase -- only that `dar`, `um` and `jeito`
    each occur. Every token being attested is NECESSARY, not SUFFICIENT, evidence
    that the chunk is real. A chunk whose tokens are all common can still be an
    invented collocation; that is what the naturalness lens is for.

    Spoken-only forms (R3/R4) are skipped: a subtitle corpus writes `falando`,
    never `falano`.
    """
    import os
    import re

    from ouvido.candidates import NO_ATTESTATION_RULES
    from ouvido.corpus import is_attested, load_subtlex

    freqs = load_subtlex(args.freqs_path)
    token = re.compile(r"[^\W\d_]+", re.UNICODE)

    notes: list[dict] = []
    for fn in sorted(f for f in os.listdir(args.notes_path) if f.endswith(".json")):
        notes.extend(read_json(os.path.join(args.notes_path, fn)))

    flagged: list[dict] = []
    checked = 0
    for note in notes:
        if NO_ATTESTATION_RULES & set(note.get("rules", [])):
            continue
        item = re.sub(r"\s*\([^)]*\)", "", note["item"]).strip()
        toks = token.findall(item.lower())
        if len(toks) < 2:
            continue  # single words were attested at candidate time
        checked += 1
        missing = [t for t in toks if not is_attested(t, freqs)]
        if missing:
            flagged.append({"item": note["item"], "unattested_tokens": missing,
                            "reason": "chunk contains token(s) absent from SUBTLEX-PT-BR"})

    write_jsonl(args.log_path, flagged)
    print(f"attested {checked - len(flagged)}/{checked} multi-word chunks "
          f"(token-level; necessary, not sufficient)")
    return 0



def _load_notes(notes_path: str) -> list[dict]:
    """Accept either a directory of batch files or a single JSON array file."""
    import os

    if os.path.isdir(notes_path):
        out: list[dict] = []
        for fn in sorted(f for f in os.listdir(notes_path) if f.endswith(".json")):
            out.extend(read_json(os.path.join(notes_path, fn)))
        return out
    return read_json(notes_path)


def _handle_synth(args) -> int:
    """Synthesize every clip. Resumable: existing non-empty files are skipped."""
    import asyncio
    import os

    from ouvido.media import clips_for, synth
    from ouvido.schema import note_from_dict

    notes = [note_from_dict(r) for r in _load_notes(args.notes_path)]
    os.makedirs(args.media_path, exist_ok=True)

    todo = []
    for note in notes:
        for text, voice, fname in clips_for(note):
            dest = os.path.join(args.media_path, fname)
            if os.path.exists(dest) and os.path.getsize(dest) > 2000:
                continue
            todo.append((text, voice, dest))

    print(f"{len(notes)} notes -> {3 * len(notes)} clips; {len(todo)} to synthesize")

    async def run() -> list[str]:
        sem = asyncio.Semaphore(6)
        failed: list[str] = []

        async def one(text: str, voice: str, dest: str) -> None:
            async with sem:
                for attempt in range(4):
                    try:
                        await synth(text, voice, dest)
                        if os.path.getsize(dest) > 2000:
                            return
                    except Exception:  # noqa: BLE001 - retried, then reported
                        pass
                    await asyncio.sleep(2 * (attempt + 1))
                failed.append(dest)

        await asyncio.gather(*(one(t, v, d) for t, v, d in todo))
        return failed

    failed = asyncio.run(run()) if todo else []
    if failed:
        print(f"FAILED to synthesize {len(failed)} clips")
        for f in failed[:10]:
            print("  ", f)
        return 1
    print("all clips present")
    return 0


def _handle_asr_gate(args) -> int:
    """Transcribe every clip and flag divergence from the expanded source text.

    Catches truncation, empty files, gross mispronunciation. Does NOT catch
    unnatural prosody -- Whisper normalises orthography, so `Cê tá` comes back
    as `Você está` whether or not the reduction was spoken.
    """
    import os

    from ouvido.asr import check_clip, transcribe
    from ouvido.media import clips_for
    from ouvido.schema import note_from_dict

    notes = [note_from_dict(r) for r in _load_notes(args.notes_path)]
    expected: dict[str, str] = {}
    for note in notes:
        for text, _voice, fname in clips_for(note):
            path = os.path.join(args.media_path, fname)
            if os.path.exists(path):
                expected[path] = text

    paths = sorted(expected)
    print(f"transcribing {len(paths)} clips ...")
    heard = transcribe(paths)

    flagged = [
        {"file": os.path.basename(p), "expected": expected[p], "heard": heard.get(p, "")}
        for p in paths
        if not check_clip(expected[p], heard.get(p, ""))
    ]
    write_jsonl(args.log_path, flagged)
    print(f"ASR gate: {len(paths) - len(flagged)}/{len(paths)} clips agree; {len(flagged)} flagged")
    return 0


def _handle_push_media(args) -> int:
    """Upload every clip through AnkiConnect. Never write into collection.media directly."""
    import os

    from ouvido.anki import Anki

    anki = Anki()
    files = sorted(f for f in os.listdir(args.media_path) if f.endswith(".mp3"))
    for i, fn in enumerate(files, 1):
        anki.store_media(fn, os.path.join(args.media_path, fn))
        if i % 100 == 0:
            print(f"  {i}/{len(files)}")
    print(f"stored {len(files)} media files")
    return 0


def _handle_push_notes(args) -> int:
    """Add notes to Anki. Duplicates return None and are logged, not raised."""
    from ouvido.anki import Anki
    from ouvido.gap import render_gap
    from ouvido.notetype import fields_for
    from ouvido.schema import note_from_dict

    anki = Anki()
    rows = _load_notes(args.notes_path)
    log: list[dict] = []
    added = 0
    for row in rows:
        note = note_from_dict(row)
        fields = fields_for(note, render_gap(note))
        tags = [f"estrato::{note.stratum}"] + [f"regra::{r}" for r in sorted(note.rules)]
        if row.get("fonte"):
            tags.append(f"fonte::{row['fonte']}")
        note_id = anki.add_note(args.deck, fields, tags)
        if note_id is None:
            log.append({"item": note.item, "reason": "duplicate; addNote returned null"})
        else:
            added += 1
            log.append({"item": note.item, "note_id": note_id})
    write_jsonl(args.log_path, log)
    print(f"added {added}/{len(rows)} notes to deck {args.deck!r}")
    return 0 if added == len(rows) else 1


def _handle_sample(args) -> int:
    """Render N notes as standalone HTML so the cards can be reviewed in a browser."""
    import os
    import shutil

    from ouvido.gap import render_gap
    from ouvido.media import clips_for
    from ouvido.notetype import CSS, TEMPLATES, fields_for
    from ouvido.render import render_card
    from ouvido.schema import note_from_dict

    rows = _load_notes(args.notes_path)
    step = max(1, len(rows) // args.n)
    picked = [note_from_dict(r) for r in rows[::step][: args.n]]

    os.makedirs(args.out_path, exist_ok=True)
    if args.media_path:
        for note in picked:
            for _t, _v, fname in clips_for(note):
                src = os.path.join(args.media_path, fname)
                if os.path.exists(src):
                    shutil.copy(src, os.path.join(args.out_path, fname))

    parts = [
        "<title>Ouvido — sample cards</title>",
        f"<style>{CSS}\nbody{{font-family:system-ui;margin:2rem;background:#f6f6f6}}"
        ".card{background:#fff;border-radius:10px;padding:18px;margin:18px auto;max-width:640px;"
        "box-shadow:0 1px 4px rgba(0,0,0,.12)}h2{font:600 15px system-ui;color:#666;"
        "max-width:640px;margin:26px auto 0}</style>",
        "<h1>Ouvido — sample cards</h1>",
    ]
    for note in picked:
        gap = render_gap(note)
        fields = fields_for(note, gap)
        for tpl in TEMPLATES:
            parts.append(f"<h2>{note.item} — {tpl['Name']}</h2>")
            parts.append(render_card(fields, tpl))

    index = os.path.join(args.out_path, "index.html")
    with open(index, "w", encoding="utf-8") as fh:
        fh.write("\n".join(parts))
    print(f"wrote {index} ({len(picked)} notes x 3 cards)")
    return 0


_HANDLERS = {
    "filter-candidates": _handle_filter_candidates,
    "validate-notes": _handle_validate_notes,
    "apply-verdicts": _handle_apply_verdicts,
    "attest": _handle_attest,
    "synth": _handle_synth,
    "asr-gate": _handle_asr_gate,
    "push-media": _handle_push_media,
    "push-notes": _handle_push_notes,
    "sample": _handle_sample,
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

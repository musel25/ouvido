import json
import pytest
from ouvido.cli import build_parser, write_jsonl, read_json, write_json, main

SUBCOMMANDS = {"filter-candidates", "validate-notes", "apply-verdicts", "attest",
               "sample", "synth", "asr-gate", "push-media", "push-notes"}


def test_every_subcommand_the_plan_invokes_is_registered():
    parser = build_parser()
    sub = next(a for a in parser._actions if a.dest == "command")
    assert SUBCOMMANDS <= set(sub.choices)


def test_unknown_subcommand_exits_nonzero():
    with pytest.raises(SystemExit):
        build_parser().parse_args(["does-not-exist"])


def test_no_subcommand_returns_error_code():
    assert main([]) == 2


def test_write_jsonl_creates_parent_dirs(tmp_path):
    p = tmp_path / "logs" / "out.jsonl"
    write_jsonl(str(p), [{"a": 1}, {"b": 2}])
    lines = p.read_text().strip().split("\n")
    assert [json.loads(x) for x in lines] == [{"a": 1}, {"b": 2}]


def test_write_jsonl_empty_still_creates_file(tmp_path):
    # an empty rejection log must exist and be readable — "no file" is ambiguous
    p = tmp_path / "logs" / "empty.jsonl"
    write_jsonl(str(p), [])
    assert p.exists() and p.read_text() == ""


def test_json_roundtrip_is_utf8_not_escaped(tmp_path):
    p = tmp_path / "n.json"
    write_json(str(p), [{"item": "cadê"}])
    assert "cadê" in p.read_text(encoding="utf-8")
    assert read_json(str(p)) == [{"item": "cadê"}]


def test_module_entrypoint_prints_help(tmp_path):
    """`python -m ouvido.cli --help` must actually print usage.

    Without an `if __name__ == "__main__"` guard, running cli.py as a module
    defines functions and exits silently — every pipeline command in the plan
    would no-op while appearing to succeed.
    """
    import subprocess, sys
    r = subprocess.run([sys.executable, "-m", "ouvido.cli", "--help"],
                       capture_output=True, text=True)
    assert r.returncode == 0
    assert "filter-candidates" in r.stdout
    assert "push-notes" in r.stdout


def _write_freqs_tsv(path):
    path.write_text(
        "Word\tFREQcount\n"
        "bagunça\t400\n"
        "esquisito\t300\n"
        "hospital\t900\n"
        "inventado\t1\n",
        encoding="utf-8",
    )


def test_filter_candidates_handler_kept_and_log(tmp_path, capsys):
    in_dir = tmp_path / "candidates"
    in_dir.mkdir()
    (in_dir / "01_lexico.json").write_text(json.dumps([
        {"item": "hospital", "es": "hospital", "stratum": "lexico", "rules": ["R1"], "subtlex_rank": 12},
        {"item": "bagunça", "es": "desorden", "stratum": "lexico", "rules": ["R1"], "subtlex_rank": 700},
    ]), encoding="utf-8")
    (in_dir / "02_falso-amigo.json").write_text(json.dumps([
        {"item": "esquisito", "es": "exquisito", "stratum": "falso-amigo", "rules": ["R2"], "subtlex_rank": 300},
        {"item": "inventado", "es": "palabra rara", "stratum": "lexico", "rules": ["R1"], "subtlex_rank": None},
    ]), encoding="utf-8")

    freqs_path = tmp_path / "subtlex.tsv"
    _write_freqs_tsv(freqs_path)

    out_path = tmp_path / "kept.json"
    log_path = tmp_path / "logs" / "rejected.jsonl"

    rc = main([
        "filter-candidates",
        "--in", str(in_dir),
        "--freqs", str(freqs_path),
        "--out", str(out_path),
        "--log", str(log_path),
    ])

    assert rc == 0
    assert out_path.exists()
    assert log_path.exists()

    kept = json.loads(out_path.read_text(encoding="utf-8"))
    rejected_lines = log_path.read_text(encoding="utf-8").strip().split("\n")
    rejected = [json.loads(line) for line in rejected_lines]

    assert {c["item"] for c in kept} == {"bagunça", "esquisito"}
    assert {r["item"] for r in rejected} == {"hospital", "inventado"}
    assert all("reason" in r for r in rejected)
    assert len(kept) + len(rejected) == 4

    captured = capsys.readouterr()
    assert captured.out.strip() == "kept 2, rejected 2 (from 2 files)"


def test_filter_candidates_handler_creates_empty_log_when_nothing_rejected(tmp_path):
    in_dir = tmp_path / "candidates"
    in_dir.mkdir()
    (in_dir / "01_lexico.json").write_text(json.dumps([
        {"item": "bagunça", "es": "desorden", "stratum": "lexico", "rules": ["R1"], "subtlex_rank": 700},
        {"item": "esquisito", "es": "exquisito", "stratum": "falso-amigo", "rules": ["R2"], "subtlex_rank": 300},
    ]), encoding="utf-8")

    freqs_path = tmp_path / "subtlex.tsv"
    _write_freqs_tsv(freqs_path)

    out_path = tmp_path / "kept.json"
    log_path = tmp_path / "logs" / "rejected.jsonl"

    rc = main([
        "filter-candidates",
        "--in", str(in_dir),
        "--freqs", str(freqs_path),
        "--out", str(out_path),
        "--log", str(log_path),
    ])

    assert rc == 0
    kept = json.loads(out_path.read_text(encoding="utf-8"))
    assert len(kept) == 2
    assert log_path.exists()
    assert log_path.read_text(encoding="utf-8") == ""


def test_every_subcommand_now_has_a_handler():
    """Once all handlers land, no subcommand may silently fall through to the stub."""
    from ouvido.cli import _HANDLERS
    parser = build_parser()
    sub = next(a for a in parser._actions if a.dest == "command")
    assert set(sub.choices) == set(_HANDLERS), set(sub.choices) ^ set(_HANDLERS)


def _note(**over):
    base = dict(item="a fim de", item_full="", gloss="up for",
                sent1="Cê tá a fim de sair?", sent1_en="You up for going out?",
                sent2="Eu tava a fim de pizza.", sent2_en="I was up for pizza.",
                sent2_span="a fim de", notes="", cuidado="", ear="",
                stratum="chunk", rules=["R5"])
    base.update(over)
    return base


def test_validate_notes_accepts_good_batch(tmp_path, capsys):
    d = tmp_path / "notes"; d.mkdir()
    write_json(str(d / "batch_00.json"), [_note()])
    log = tmp_path / "logs" / "schema_failures.jsonl"
    assert main(["validate-notes", "--in", str(d), "--log", str(log)]) == 0
    assert log.exists() and log.read_text() == ""
    assert "1 notes valid" in capsys.readouterr().out


def test_validate_notes_logs_failures_and_returns_nonzero(tmp_path):
    d = tmp_path / "notes"; d.mkdir()
    bad = _note(item="x", sent2_span="not present in sent2")
    write_json(str(d / "batch_00.json"), [_note(), bad])
    log = tmp_path / "logs" / "schema_failures.jsonl"
    assert main(["validate-notes", "--in", str(d), "--log", str(log)]) == 1
    rows = [json.loads(l) for l in log.read_text().strip().split("\n")]
    assert len(rows) == 1
    assert rows[0]["item"] == "x"
    assert "span not found" in rows[0]["error"]


def test_validate_notes_catches_duplicate_items_across_batches(tmp_path):
    d = tmp_path / "notes"; d.mkdir()
    write_json(str(d / "batch_00.json"), [_note()])
    write_json(str(d / "batch_01.json"), [_note()])   # same Item -> Anki dup key
    log = tmp_path / "logs" / "f.jsonl"
    assert main(["validate-notes", "--in", str(d), "--log", str(log)]) == 1
    assert "duplicate item" in log.read_text()


def _verdicts(item, nat=True, sem=True, mech=True):
    return [{"lens": "naturalness", "passed": nat, "reason": ""},
            {"lens": "semantics", "passed": sem, "reason": "bad spanish claim" if not sem else ""},
            {"lens": "mechanics", "passed": mech, "reason": ""}]


def test_apply_verdicts_ships_passing_notes_and_logs_the_rest(tmp_path):
    d = tmp_path / "notes"; d.mkdir()
    write_json(str(d / "batch_00.json"), [_note(item="ok"), _note(item="vetoed"), _note(item="weak")])
    vpath = tmp_path / "verdicts.json"
    write_json(str(vpath), {
        "ok": _verdicts("ok"),
        "vetoed": _verdicts("vetoed", sem=False),          # semantics veto
        "weak": _verdicts("weak", nat=False, mech=False),  # only 1 of 3
    })
    out = tmp_path / "final.json"
    log = tmp_path / "logs" / "rejected_notes.jsonl"
    rc = main(["apply-verdicts", "--notes", str(d), "--verdicts", str(vpath),
               "--out", str(out), "--log", str(log)])
    assert rc == 0
    shipped = [n["item"] for n in read_json(str(out))]
    assert shipped == ["ok"]
    rows = [json.loads(l) for l in log.read_text().strip().split("\n")]
    assert {r["item"] for r in rows} == {"vetoed", "weak"}
    assert any("bad spanish claim" in r["reason"] for r in rows)


def test_apply_verdicts_rejects_note_with_no_verdicts(tmp_path):
    """An unjudged note must never ship. Silence is not approval."""
    d = tmp_path / "notes"; d.mkdir()
    write_json(str(d / "b.json"), [_note(item="unjudged")])
    vpath = tmp_path / "v.json"; write_json(str(vpath), {})
    out = tmp_path / "o.json"; log = tmp_path / "l.jsonl"
    assert main(["apply-verdicts", "--notes", str(d), "--verdicts", str(vpath),
                 "--out", str(out), "--log", str(log)]) == 0
    assert read_json(str(out)) == []
    assert "no verdicts" in log.read_text()


def test_apply_verdicts_conserves_every_note(tmp_path):
    d = tmp_path / "notes"; d.mkdir()
    write_json(str(d / "b.json"), [_note(item="a"), _note(item="b")])
    vpath = tmp_path / "v.json"
    write_json(str(vpath), {"a": _verdicts("a"), "b": _verdicts("b", sem=False)})
    out = tmp_path / "o.json"; log = tmp_path / "l.jsonl"
    main(["apply-verdicts", "--notes", str(d), "--verdicts", str(vpath),
          "--out", str(out), "--log", str(log)])
    shipped = len(read_json(str(out)))
    rejected = len([l for l in log.read_text().split("\n") if l.strip()])
    assert shipped + rejected == 2


def _freqs_file(tmp_path):
    p = tmp_path / "f.tsv"
    p.write_text("Word\tFREQcount\tCDcount\tSpellcheck\n"
                 "dar\t900\t9\tTRUE\num\t800\t9\tTRUE\njeito\t700\t9\tTRUE\n"
                 "bagunça\t400\t9\tTRUE\n", encoding="utf-8")
    return str(p)


def test_attest_passes_chunk_whose_every_token_is_attested(tmp_path):
    d = tmp_path / "n"; d.mkdir()
    write_json(str(d / "b.json"), [_note(item="dar um jeito", sent2_span="dar um jeito",
                                         sent2="Ele vai dar um jeito nisso.")])
    log = tmp_path / "unattested.jsonl"
    assert main(["attest", "--notes", str(d), "--freqs", _freqs_file(tmp_path),
                 "--log", str(log)]) == 0
    assert log.read_text() == ""


def test_attest_flags_chunk_with_an_unattested_token(tmp_path):
    d = tmp_path / "n"; d.mkdir()
    write_json(str(d / "b.json"), [_note(item="dar um chabu", sent2_span="dar um chabu",
                                         sent2="Vai dar um chabu isso.")])
    log = tmp_path / "unattested.jsonl"
    main(["attest", "--notes", str(d), "--freqs", _freqs_file(tmp_path), "--log", str(log)])
    rows = [json.loads(l) for l in log.read_text().strip().split("\n")]
    assert rows[0]["item"] == "dar um chabu"
    assert "chabu" in rows[0]["unattested_tokens"]


def test_attest_never_flags_spoken_only_forms(tmp_path):
    """R3/R4 items are spoken-only; a subtitle corpus cannot contain them."""
    d = tmp_path / "n"; d.mkdir()
    write_json(str(d / "b.json"), [_note(item="falano", rules=["R3"], stratum="reducao",
                                         sent1="Cê tá falano o quê?", sent1_en="What are you saying?",
                                         sent2="Ele tá falano bobagem.", sent2_en="He's talking nonsense.",
                                         sent2_span="falano")])
    log = tmp_path / "u.jsonl"
    main(["attest", "--notes", str(d), "--freqs", _freqs_file(tmp_path), "--log", str(log)])
    assert log.read_text() == ""


def test_synth_writes_a_failure_log_even_when_nothing_fails(tmp_path, monkeypatch):
    """Every stage writes a rejection log, always. `synth` is the one stage whose
    failures are per-file rather than per-note, and it was silently exempt."""
    import ouvido.cli as cli

    async def fake_synth(text, voice, dest):
        with open(dest, "wb") as fh:
            fh.write(b"\x00" * 3000)

    monkeypatch.setattr("ouvido.media.synth", fake_synth)
    notes = tmp_path / "n.json"
    write_json(str(notes), [_note()])
    media = tmp_path / "media"
    log = tmp_path / "logs" / "synth_failures.jsonl"
    rc = cli.main(["synth", "--notes", str(notes), "--media", str(media), "--log", str(log)])
    assert rc == 0
    assert log.exists() and log.read_text() == ""
    assert len(list(media.glob("*.mp3"))) == 3


def test_synth_logs_the_underlying_error_when_a_clip_fails(tmp_path, monkeypatch):
    import ouvido.cli as cli

    async def boom(text, voice, dest):
        raise RuntimeError("edge-tts said no")

    monkeypatch.setattr("ouvido.media.synth", boom)
    monkeypatch.setattr("asyncio.sleep", _no_sleep)
    notes = tmp_path / "n.json"
    write_json(str(notes), [_note()])
    log = tmp_path / "logs" / "synth_failures.jsonl"
    rc = cli.main(["synth", "--notes", str(notes), "--media", str(tmp_path / "m"), "--log", str(log)])
    assert rc == 1
    rows = [json.loads(l) for l in log.read_text().strip().split("\n")]
    assert len(rows) == 3
    assert "edge-tts said no" in rows[0]["error"]      # the real cause, not just a path


async def _no_sleep(*_a, **_k):
    return None


def test_apply_verdicts_accepts_a_single_notes_file(tmp_path):
    """`--notes` must accept a file or a directory, like synth/asr-gate/push-notes."""
    notes = tmp_path / "one.json"
    write_json(str(notes), [_note(item="solo")])
    v = tmp_path / "v.json"; write_json(str(v), {"solo": _verdicts("solo")})
    out = tmp_path / "o.json"; log = tmp_path / "l.jsonl"
    assert main(["apply-verdicts", "--notes", str(notes), "--verdicts", str(v),
                 "--out", str(out), "--log", str(log)]) == 0
    assert [n["item"] for n in read_json(str(out))] == ["solo"]

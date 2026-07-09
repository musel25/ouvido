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

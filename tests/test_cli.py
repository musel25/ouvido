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

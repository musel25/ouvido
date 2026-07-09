import json
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

import pytest
from ouvido.anki import Anki, AnkiError

RECEIVED: list[dict] = []
REPLY: dict = {}


class Handler(BaseHTTPRequestHandler):
    def do_POST(self):
        body = self.rfile.read(int(self.headers["Content-Length"]))
        RECEIVED.append(json.loads(body))
        payload = json.dumps(REPLY).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def log_message(self, *a):
        pass


@pytest.fixture
def server():
    RECEIVED.clear()
    srv = HTTPServer(("127.0.0.1", 0), Handler)
    t = threading.Thread(target=srv.serve_forever, daemon=True)
    t.start()
    yield f"http://127.0.0.1:{srv.server_port}"
    srv.shutdown()
    srv.server_close()


def test_invoke_sends_version_6_envelope(server):
    REPLY.clear(); REPLY.update({"result": ["Default"], "error": None})
    assert Anki(server).deck_names() == ["Default"]
    sent = RECEIVED[0]
    assert sent["action"] == "deckNames"
    assert sent["version"] == 6


def test_error_field_raises(server):
    REPLY.clear(); REPLY.update({"result": None, "error": "deck not found"})
    with pytest.raises(AnkiError, match="deck not found"):
        Anki(server).deck_names()


def test_add_note_disallows_duplicates(server):
    REPLY.clear(); REPLY.update({"result": 12345, "error": None})
    Anki(server).add_note("Ouvido", {"Item": "cê"}, ["estrato::reducao"])
    note = RECEIVED[0]["params"]["note"]
    assert note["deckName"] == "Ouvido"
    assert note["modelName"] == "PT Ouvido"
    assert note["options"]["allowDuplicate"] is False
    assert note["tags"] == ["estrato::reducao"]


def test_create_model_is_not_cloze(server):
    REPLY.clear(); REPLY.update({"result": {}, "error": None})
    Anki(server).create_model()
    p = RECEIVED[0]["params"]
    assert p["modelName"] == "PT Ouvido"
    assert p["isCloze"] is False
    assert p["inOrderFields"][0] == "Item"
    assert len(p["cardTemplates"]) == 3


def test_store_media_sends_base64(server, tmp_path):
    f = tmp_path / "a.mp3"
    f.write_bytes(b"\x00\x01\x02")
    REPLY.clear(); REPLY.update({"result": "a.mp3", "error": None})
    Anki(server).store_media("a.mp3", str(f))
    p = RECEIVED[0]["params"]
    assert p["filename"] == "a.mp3"
    assert p["data"] == "AAEC"          # base64 of \x00\x01\x02


def test_suspend(server):
    REPLY.clear(); REPLY.update({"result": True, "error": None})
    assert Anki(server).suspend([1, 2, 3]) is True
    assert RECEIVED[0]["params"]["cards"] == [1, 2, 3]

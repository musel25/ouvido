"""AnkiConnect client. Requires the Anki GUI to be running — there is no
headless mode."""
from __future__ import annotations

import base64
import json
import urllib.error
import urllib.request
from typing import Any

from ouvido.notetype import CSS, FIELDS, MODEL_NAME, TEMPLATES


class AnkiError(Exception):
    pass


class Anki:
    def __init__(self, url: str = "http://localhost:8765", timeout: int = 60):
        self.url = url
        self.timeout = timeout

    def invoke(self, action: str, **params) -> Any:
        payload = json.dumps({"action": action, "version": 6, "params": params}).encode()
        req = urllib.request.Request(self.url, payload, {"Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                body = json.load(resp)
        except urllib.error.URLError as e:
            raise AnkiError(f"cannot reach AnkiConnect at {self.url} — is Anki open? ({e})") from e
        if body.get("error") is not None:
            raise AnkiError(body["error"])
        return body["result"]

    def deck_names(self) -> list[str]:
        return self.invoke("deckNames")

    def model_names(self) -> list[str]:
        return self.invoke("modelNames")

    def create_deck(self, name: str) -> int:
        return self.invoke("createDeck", deck=name)

    def create_model(self) -> Any:
        return self.invoke(
            "createModel",
            modelName=MODEL_NAME,
            inOrderFields=FIELDS,
            css=CSS,
            isCloze=False,
            cardTemplates=TEMPLATES,
        )

    def store_media(self, filename: str, path: str) -> str:
        with open(path, "rb") as fh:
            data = base64.b64encode(fh.read()).decode()
        return self.invoke("storeMediaFile", filename=filename, data=data)

    def add_note(self, deck: str, fields: dict, tags: list[str]) -> int | None:
        """Add one note. Returns None if it is already in the collection.

        AnkiConnect RAISES on a duplicate ("cannot create note because it is a
        duplicate") rather than returning null, so we absorb exactly that error
        and let every other one propagate. Without this, re-running a build
        crashes on the first note that already exists.
        """
        try:
            return self.invoke(
                "addNote",
                note={
                    "deckName": deck,
                    "modelName": MODEL_NAME,
                    "fields": fields,
                    "tags": tags,
                    "options": {"allowDuplicate": False},
                },
            )
        except AnkiError as e:
            if "duplicate" in str(e).lower():
                return None
            raise

    def find_cards(self, query: str) -> list[int]:
        return self.invoke("findCards", query=query)

    def suspend(self, card_ids: list[int]) -> bool:
        return self.invoke("suspend", cards=card_ids)

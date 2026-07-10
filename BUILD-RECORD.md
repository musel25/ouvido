# Build complete — 2026-07-10

The deck is finished. This file used to be the continuation plan; it is now the record of what shipped.

## What is in Anki

- Deck **`Ouvido`**: **364 notes / 1,092 cards / 1,092 audio clips**, note type `PT Ouvido`.
- Zero missing media, zero duplicate `Item` values, exactly 3 cards per note.
- 69 of the 73 `Pois Não` false cognates carried over, tagged `fonte::pois-nao`.

| stratum | shipped | authored |
|---|---|---|
| chunk | 85 | 86 |
| falso-amigo | 88 | 92 |
| lexico | 54 | 55 |
| reducao | 50 | 52 |
| estrutura | 45 | 47 |
| marcador | 42 | 42 |
| **total** | **364** | **374** |

## `Pois Não`

Not deleted. Precisely suspended:

- **138 cards suspended** — the 69 false cognates that were absorbed into `Ouvido`.
- **70 cards left active** — the 31 `Erro Comum` notes (never absorbed; they teach production
  corrections, not comprehension), plus the 4 false cognates that did not carry over.

To unsuspend everything: `Browse → deck:"Pois Não" → Ctrl+A → Ctrl+J`.

## The 10 notes the lenses refuted

Seven died on the **semantics veto** — a factual error about meaning or a false claim about Spanish
cannot be outvoted by two agents who liked the sentence:

- `paquete` — could not confirm it is real BR slang for menstruation (inherited from `Pois Não`).
- `fechar` — the `cuidado` made a false claim about how Spanish uses `fechar`.
- `ficar bom (de saúde)` — the `cuidado` invented a "moral sense" ambiguity in Spanish.
- `largar` — the `cuidado` made a doubtful claim about rioplatense Spanish.
- `pra mim` — `notes` and `cuidado` mis-stated the grammar of `pra mim` as a subject.
- `tá (como resposta sozinha)` — `item_full` contradicted the note's own `ear` field.
- `vô` — `sent2` and `sent2_en` disagreed about the meaning of `lá em casa`.

Three failed on naturalness + mechanics:

- `jogar verde para colher maduro` — proverbial/written, and the gap left a dangling fragment.
- `película` — the span swallowed the disambiguating noun; both sentences used unnatural collocations.
- `todavia` — `sent2` mixed the reduced spoken `tava` with a formal connective. Register clash.

Four of the still-active `Pois Não` cards are `banana`, `fechar`, `paquete`, `película`. `banana` was
dropped by the candidate critic because it is not a false friend at all — same word, same meaning.
`fechar` and `película` are genuine PT-ES divergences whose *notes* were wrong; re-author them if you
want them back.

## Evidence

- **108 tests pass.**
- **ASR gate: 1,055/1,092 clips agree.** All 37 flags are isolated single-word `item` clips, where
  Whisper has no context (`tirar` → "Cheirar", `tijolo` → "Tiz e Olu!"). **Zero sentence clips flagged**
  — every clip that plays on a Listen or Cloze card transcribed correctly.
- Whisper transcribed the `cê tá` clip as `Cê tá!`, preserving the reduction rather than normalising it
  — direct evidence the reduced form is genuinely spoken, not merely spelled.
- `synth` and `push-notes` are idempotent: a third consecutive push adds 0, skips 364, exits 0.

## Rebuilding from scratch

```bash
./scripts/fetch_subtlex.sh
uv run python -m ouvido.cli synth      --notes data/notes_verified.json --media out/media \
    --log data/logs/synth_failures.jsonl
uv run python -m ouvido.cli push-media --media out/media        # Anki must be OPEN
uv run python -m ouvido.cli push-notes --notes data/notes_verified.json --deck Ouvido \
    --log data/logs/build.jsonl
```

## Still true, and not fixable by more agents

1. **No native speaker reviewed these sentences.** Three adversarial lenses plus corpus attestation is
   the best available proxy, not an equivalent.
2. **TTS is not speech.** No carioca *chiado*, no caipira retroflex R, no overlapping talk, no annoyed
   prosody. The deck teaches lexicon, chunks and reduced forms; accent robustness needs real audio.
3. **`attest` is token-level.** SUBTLEX is a unigram list — it cannot confirm a chunk occurs as a phrase.
4. **The ASR gate cannot hear prosody.** It catches truncation, empty clips and gross mispronunciation.
5. The ~4,162 orphaned `pimenrich_*.mp3` files (~110 MB) from the deleted Pimsleur deck are still in
   `collection.media/`. Run **Tools → Check Media** to see them. Ask before deleting.

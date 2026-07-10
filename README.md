# ouvido

Builds **Ouvido**, a Brazilian Portuguese listening-comprehension Anki deck for a native **Spanish**
speaker. The goal is understanding spoken Brazilian Portuguese — not speaking, not writing, not
European Portuguese.

## Why it isn't a frequency deck

A Spanish speaker already owns thousands of Portuguese words on sight: `hospital`, `problema`,
`importante`. A frequency-ordered deck spends most of its cards on them.

Measured on SUBTLEX-PT-BR (78,908 word forms, 58.7M tokens of film subtitles):

| top-N word forms | coverage of spoken text |
|---|---|
| 1,000 | 79.88% |
| 2,000 | 85.86% |
| 3,000 | 88.92% |
| 5,000 | 92.27% |

Portuguese never reaches the ~95% listening-adequacy threshold on a tractable word list, because it
inflects six ways where English inflects two. So an item earns a card only if **Spanish does not give
it for free**:

| rule | meaning | example |
|---|---|---|
| R1 | opaque to Spanish | `bagunça` |
| R2 | false friend | `todavia` = *however*, not `todavía` |
| R3 | reduced form | `cê`, `tá`, `num`, `cadê` |
| R4 | discourse marker | `né`, `aí`, `tipo`, `pois é` |
| R5 | idiomatic chunk | `dar um jeito` |
| R6 | structure Spanish lacks | `a gente` + 3sg, existential `tem` |
| R7 | phonological trap | `presidente` → [pɾeziˈdẽtʃi] |

R2, R3 and R7 are exempt from the cognate filter: for them, similarity to Spanish *is* the danger.
R3 and R4 are exempt from corpus attestation — subtitles write `falando`, never `falano`.

## Three cards per note

- **Listen** — front is audio only, zero text. The only card that tests the ear.
- **Read** — front is the item as text; audio on the back, so you can review without headphones.
- **Cloze** — audio plays, then a pre-rendered gap. (An Anki note type cannot be both standard and
  cloze, so the blank is baked into a field at build time.)

Glosses are **English** — a Spanish gloss on a cognate is a freebie that generates no memory. Spanish
survives as the `Cuidado` warning, shown only where Spanish actively lies to you.

## Verification

Every note faces three independent agents, each prompted to **refute**: naturalness, semantics,
mechanics. A note ships only if ≥2 pass **and semantics passes** — a factual error about Spanish cannot
be outvoted by two agents who liked the sentence.

## Usage

Requires `uv`, and Anki running with the AnkiConnect add-on (there is no headless mode).

```bash
./scripts/fetch_subtlex.sh
uv run pytest                                     # 108 tests

uv run python -m ouvido.cli filter-candidates --in data/candidates --freqs data/subtlex/subtlex.tsv \
    --out data/candidates_kept.json --log data/logs/rejected_candidates.jsonl
uv run python -m ouvido.cli validate-notes  --in data/notes --log data/logs/schema_failures.jsonl
uv run python -m ouvido.cli apply-verdicts  --notes data/notes --verdicts data/verdicts.json \
    --out data/notes_verified.json --log data/logs/rejected_notes.jsonl
uv run python -m ouvido.cli synth      --notes data/notes_verified.json --media out/media \
    --log data/logs/synth_failures.jsonl
uv run python -m ouvido.cli asr-gate   --notes data/notes_verified.json --media out/media \
    --log data/logs/asr_failures.jsonl
uv run python -m ouvido.cli sample     --notes data/notes_verified.json --media out/media --out out/sample
uv run python -m ouvido.cli push-media --media out/media
uv run python -m ouvido.cli push-notes --notes data/notes_verified.json --deck Ouvido \
    --log data/logs/build.jsonl
```

Every stage writes a rejection log, always — an empty log is an artifact, not an absence. The build is
idempotent end to end: `synth` skips clips that already exist, and `push-notes` skips notes already in
the collection (AnkiConnect *raises* on a duplicate rather than returning null; `add_note` absorbs
exactly that error and nothing else).

Shipped: **364 notes / 1,092 cards / 1,092 clips.** 374 were authored; 10 were refuted by the three
lenses, 7 of them by the semantics veto.

## What this cannot do

- **No native speaker reviews the sentences.** Adversarial verification and corpus attestation are the
  best available proxy, not an equivalent.
- **TTS is not speech.** No carioca *chiado*, no retroflex R, no overlapping talk.
- **`attest` is token-level.** SUBTLEX is a unigram list; it cannot confirm a chunk occurs as a phrase.
- **The ASR gate cannot hear prosody.** Whisper normalises orthography, so `Cê tá` transcribes as
  `Você está` either way. It catches truncation and empty clips.

Colloquial spelling does produce colloquial audio, though — measured, silence-trimmed: `tá` runs 149 ms
shorter than `está`, and `cadê` 219 ms shorter than `onde está`.

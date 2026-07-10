# Resume: verify and ship the remaining 199 notes

The 2026-07-09 build stopped mid-verification when an API session limit hit. Everything needed to
finish is committed. This file is the exact continuation.

## State at the stop

- **374 notes authored** and schema-valid, in `data/notes/batch_00..18.json`.
- **175 shipped** to the Anki deck `Ouvido` (525 cards, 525 clips).
- **199 not shipped**: 174 never judged, 20 judged by only one or two lenses, 5 refuted on purpose.
- Partial verdicts are in `data/verdicts/<lens>_<batch>.json` — 23 of the 57 expected files.

The shipped deck is badly skewed. This is the thing to fix:

| stratum | shipped | authored |
|---|---|---|
| chunk | 85 | 86 |
| estrutura | 45 | 47 |
| falso-amigo | 42 | 92 |
| reducao | **2** | 52 |
| marcador | **1** | 42 |
| lexico | **0** | 55 |

`reducao`, `marcador` and `lexico` are the strata the research identified as highest-value for a
Spanish speaker. They are the ones missing.

## Which lens/batch pairs are still needed

Run this to compute it — do not trust a hand-written list:

```bash
uv run python - <<'EOF'
import itertools, os
have = set(os.listdir("data/verdicts"))
missing = [f"{lens}_{b:02d}.json"
           for lens, b in itertools.product(("naturalness","semantics","mechanics"), range(19))
           if f"{lens}_{b:02d}.json" not in have]
print(len(missing), "missing:"); [print(" ", m) for m in missing]
EOF
```

## Step 1 — re-run the missing lens agents

The verify workflow script is at
`~/.claude/projects/-home-musel-Documents-obsidian-m/*/workflows/scripts/ouvido-verify-*.js`
(if the session is gone, re-author it — the three lens prompts are reproduced in the SOP and in the
git history of this file's sibling docs).

Each agent reads `data/notes/batch_<id>.json` and writes
`data/verdicts/<lens>_<id>.json`, shaped:

```json
{ "cê tá": {"passed": true, "reason": ""},
  "esquisito": {"passed": false, "reason": "why it is wrong"} }
```

Three lenses, each prompted to **refute, not approve**, defaulting to `passed: false` when uncertain:

- **naturalness** — would a Brazilian actually say this? Catch European Portuguese, textbook stiffness.
- **semantics** — is the English gloss right, and is the Spanish `cuidado` a TRUE claim about Spanish?
  This is the veto lens.
- **mechanics** — does `sent2_span` occur exactly once, is the blank recoverable, is `sent1 != sent2`?

## Step 2 — merge, apply, build

```bash
cd ~/Documents/projects/ouvido

# merge every verdict file into one map, keyed by item
uv run python - <<'EOF'
import json, glob, os, collections
merged = collections.defaultdict(list)
for f in sorted(glob.glob("data/verdicts/*.json")):
    lens = os.path.basename(f).split("_")[0]
    for item, v in json.load(open(f, encoding="utf-8")).items():
        merged[item].append({"lens": lens, "passed": bool(v.get("passed")), "reason": v.get("reason","")})
json.dump(merged, open("data/verdicts.json","w",encoding="utf-8"), ensure_ascii=False, indent=1)
print(len(merged), "items have verdicts")
EOF

uv run python -m ouvido.cli apply-verdicts --notes data/notes --verdicts data/verdicts.json \
    --out data/notes_verified.json --log data/logs/rejected_notes.jsonl

uv run python -m ouvido.cli synth    --notes data/notes_verified.json --media out/media \
    --log data/logs/synth_failures.jsonl
uv run python -m ouvido.cli asr-gate --notes data/notes_verified.json --media out/media \
    --log data/logs/asr_failures.jsonl

# Anki must be OPEN — AnkiConnect has no headless mode
uv run python -m ouvido.cli push-media --media out/media
uv run python -m ouvido.cli push-notes --notes data/notes_verified.json --deck Ouvido \
    --log data/logs/build.jsonl
```

Both `synth` and `push-notes` are safe to re-run: `synth` skips clips that already exist, and `addNote`
uses `allowDuplicate: false`, so the 175 already-present notes return `null` and land in `build.jsonl`
rather than duplicating.

## Step 3 — only then, suspend `Pois Não`

`Pois Não` (208 cards) is still **active** on purpose: only 42 of its 92 false friends made it into
`Ouvido`. Once the false-friend stratum is fully shipped, suspend it — never delete it, so its
scheduling history survives.

```bash
uv run python -c "
from ouvido.anki import Anki
a = Anki()
ids = a.find_cards('deck:\"Pois Não\"')
print('suspending', len(ids), 'cards'); a.suspend(ids)"
```

## Step 4 — Check Media

In Anki: **Tools → Check Media**. Expect zero missing. The ~4,162 unused `pimenrich_*.mp3` files are
orphans from the deleted Pimsleur deck (~110 MB) — **ask before deleting them.**

## Notes that were refuted on purpose

Do not resurrect these without fixing them first:

- `paquete` — could not confirm it is real BR slang for menstruation. Inherited from `Pois Não`.
- `fechar`, `ficar bom (de saúde)` — the Spanish `cuidado` made a FALSE claim about Spanish.
- `tá (como resposta sozinha)` — `item_full` contradicted the note's own `ear` field.
- `jogar verde para colher maduro` — failed naturalness and mechanics.

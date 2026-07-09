#!/usr/bin/env bash
# SUBTLEX-PT-BR (Tang 2012): 61M-token film-subtitle corpus, the best
# downloadable proxy for spoken Brazilian register.
# OSF node: https://osf.io/vb5yp/   (the node URL is NOT a download link)
set -euo pipefail
mkdir -p data/subtlex

# Per-file download link, resolved from the OSF API. The node-level URL
# https://osf.io/download/vb5yp/ returns HTTP 500 — do not use it.
URL="https://osf.io/download/3r5j8/"   # SUBTLEX_PT-BR_CDAbove2_Alpha_SpellcheckTrue.tsv

curl -fL --retry 3 -m 120 -o data/subtlex/subtlex.tsv "$URL" || {
  echo "FETCH FAILED — download by hand from https://osf.io/vb5yp/ and save as" >&2
  echo "data/subtlex/subtlex.tsv. Do NOT substitute another corpus silently." >&2
  exit 1; }

lines=$(wc -l < data/subtlex/subtlex.tsv)
[ "$lines" -gt 70000 ] || { echo "suspiciously small file: $lines lines" >&2; exit 1; }
echo "ok: $lines lines"
head -3 data/subtlex/subtlex.tsv

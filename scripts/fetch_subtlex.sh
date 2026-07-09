#!/usr/bin/env bash
set -euo pipefail
mkdir -p data/subtlex
cd data/subtlex
echo "SUBTLEX-PT-BR: https://osf.io/vb5yp/  ·  http://crr.ugent.be/subtlex-pt-br/"
echo "If the automated fetch fails, download the unigram file by hand and place it here as subtlex.tsv"
curl -fL --retry 3 -o subtlex_raw "https://osf.io/download/3r5j8/" || {
  echo "FETCH FAILED — download manually, do not substitute another corpus." >&2; exit 1; }
# The OSF returns a TSV file directly, not a ZIP; rename it appropriately
if file subtlex_raw | grep -q "Zip"; then
  unzip -o subtlex_raw
  rm subtlex_raw
else
  mv subtlex_raw subtlex.tsv
fi
ls -la

#!/usr/bin/env bash
# Fetch the SRAG (SIVEP-Gripe) source files this repository's module 00 is built on.
#
# Two paths, deliberately:
#
#   1. DISCOVERY (Guaraci) — finds what the portal currently publishes. Needs
#      Docker. Use it to learn about new years or a new "banco vivo" extraction:
#
#        git clone https://github.com/autoaihub/guaraci.git && cd guaraci
#        docker build -t guaraci .
#        docker run --rm -v "$PWD:/app" guaraci \
#          guaraci fetch discover srag_arquivos --sizes
#
#      Guaraci discovers by scraping dadosabertos.saude.gov.br. That portal was
#      returning HTTP 500 on every page on 2026-08-30 (both dadosabertos and
#      opendatasus hosts — same backend), which is why discovery alone is not a
#      dependable acquisition path.
#
#   2. ACQUISITION (this script) — downloads the pinned S3 objects directly.
#      The bucket is a different service and stayed up through that outage.
#
# Why the frozen banks: the 2019-2024 files are "banco congelado (26/06/2025)"
# with stable basenames, so this script is reproducible. The 2025/2026 files are
# "banco vivo" whose basename embeds the extraction date and changes weekly —
# they are deliberately NOT pinned here. Fetch them via Guaraci discovery when
# you want them, and record the extraction date with the data.
#
# The SIVEP ficha and its confirmation criteria change between versions, so a
# SRAG extract without its year and extraction date is not interpretable later.
# That pair is in every basename below.
#
# Usage:  bash tools/srag_10_fetch.sh [destination]     (default: ~/Documents/srag-data)

set -euo pipefail

BASE="https://s3.sa-east-1.amazonaws.com/ckan.saude.gov.br/SRAG"
DEST="${1:-$HOME/Documents/srag-data}"
EXTRACTION="26-06-2025"      # the frozen-bank extraction date, part of the basename
YEARS="19 20 21 22 23 24"    # 2019-2024, the frozen banks

mkdir -p "$DEST"

# Official documentation — the data dictionary is what module 00 documents against.
for doc in "dicionario-de-dados-2019-a-2025.pdf" "ficha-de-notificacao-2025.pdf"; do
  if [ ! -f "$DEST/$doc" ]; then
    echo "==> $doc"
    curl -fSL --retry 3 --max-time 300 "$BASE/$doc" -o "$DEST/$doc"
  fi
done

# The yearly microdata, in parquet (the portal also publishes csv/json/xml).
for y in $YEARS; do
  f="INFLUD${y}-${EXTRACTION}.parquet"
  if [ -f "$DEST/$f" ]; then
    echo "==> 20$y already present, skipping"
    continue
  fi
  echo "==> 20$y  ($BASE/20$y/$f)"
  curl -fSL --retry 3 --max-time 900 "$BASE/20$y/$f" -o "$DEST/$f"
done

echo
echo "Done. Files in $DEST:"
ls -lh "$DEST"

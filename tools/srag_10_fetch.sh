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
# with stable basenames; the committed SHA-256 manifest identifies the exact
# bytes adopted here, not a Ministry signature. The 2025/2026 files are
# "banco vivo" whose basename embeds the extraction date and changes weekly —
# they are deliberately NOT pinned here. Fetch them via Guaraci discovery when
# you want them, and record the extraction date with the data.
#
# The SIVEP ficha and its confirmation criteria change between versions, so a
# SRAG extract without its year and extraction date is not interpretable later.
# That pair is in every basename below.
#
# Usage: bash tools/srag_10_fetch.sh [destination [filename ...]]
# Default: all eight files, in ~/Documents/srag-data.
# Example: bash tools/srag_10_fetch.sh /tmp/srag INFLUD23-26-06-2025.parquet

set -euo pipefail

BASE="https://s3.sa-east-1.amazonaws.com/ckan.saude.gov.br/SRAG"
DEST="${1:-$HOME/Documents/srag-data}"
EXTRACTION="26-06-2025"      # the frozen-bank extraction date, part of the basename
YEARS="19 20 21 22 23 24"    # 2019-2024, the frozen banks
FILES=("dicionario-de-dados-2019-a-2025.pdf" "ficha-de-notificacao-2025.pdf")
for y in $YEARS; do
  FILES+=("INFLUD${y}-${EXTRACTION}.parquet")
done
if [ "$#" -gt 0 ]; then
  shift
fi
if [ "$#" -gt 0 ]; then
  selected=("$@")
else
  selected=("${FILES[@]}")
fi

# Validate the entire selection before any download or destination creation.
seen="|"
for name in "${selected[@]}"; do
  admitted=false
  for file in "${FILES[@]}"; do
    if [ "$name" = "$file" ]; then
      admitted=true
      break
    fi
  done
  if [ "$admitted" = false ]; then
    echo "Unknown source filename: $name" >&2
    exit 64
  fi
  case "$seen" in
    *"|$name|"*) echo "Repeated source filename: $name" >&2; exit 64 ;;
  esac
  seen="$seen$name|"
done

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
MANIFEST="$SCRIPT_DIR/../modules/00-dataset/provenance/source-sha256.txt"
download_tmp=""

cleanup() {
  if [ -n "$download_tmp" ]; then
    rm -f -- "$download_tmp"
  fi
}
trap cleanup EXIT
trap 'exit 129' HUP
trap 'exit 130' INT
trap 'exit 143' TERM

if command -v shasum >/dev/null 2>&1; then
  hash_file() { shasum -a 256 -- "$1" | awk '{print $1}'; }
elif command -v sha256sum >/dev/null 2>&1; then
  hash_file() { sha256sum -- "$1" | awk '{print $1}'; }
else
  echo "SHA-256 verification requires shasum or sha256sum" >&2
  exit 1
fi

expected_hash() {
  local expected
  expected="$(awk -v name="$1" '$2 == name {print $1}' "$MANIFEST")"
  if [[ ! "$expected" =~ ^[0-9a-f]{64}$ ]]; then
    echo "Missing, repeated or invalid SHA-256 in manifest: $1" >&2
    return 1
  fi
  printf '%s\n' "$expected"
}

verify_file() {
  local path="$1" expected="$2" actual
  if [ ! -f "$path" ]; then
    echo "Expected a regular file: $path" >&2
    return 1
  fi
  actual="$(hash_file "$path")" || return 1
  if [ "$actual" != "$expected" ]; then
    echo "SHA-256 mismatch: $path (refusing unverified input)" >&2
    return 1
  fi
}

fetch_file() {
  local name="$1" url="$2" timeout="$3" expected target
  expected="$(expected_hash "$name")"
  target="$DEST/$name"
  if [ -e "$target" ] || [ -L "$target" ]; then
    verify_file "$target" "$expected"
    echo "==> $name already present, SHA-256 verified"
    return
  fi

  echo "==> $name  ($url)"
  download_tmp="$(mktemp "$DEST/.${name}.part.XXXXXXXX")"
  curl -fSL --retry 3 --max-time "$timeout" "$url" -o "$download_tmp"
  verify_file "$download_tmp" "$expected"

  # Never replace an existing destination, including one created during curl.
  mv -n -- "$download_tmp" "$target"
  verify_file "$target" "$expected"
  cleanup
  download_tmp=""
}

# Check every required manifest entry before starting any acquisition.
for file in "${FILES[@]}"; do
  expected_hash "$file" >/dev/null
done

mkdir -p "$DEST"

# Keep the same verification and atomic acquisition for a full or partial set.
for name in "${selected[@]}"; do
  case "$name" in
    INFLUD*) fetch_file "$name" "$BASE/20${name:6:2}/$name" 900 ;;
    *) fetch_file "$name" "$BASE/$name" 300 ;;
  esac
done

echo
echo "Done. Files in $DEST:"
ls -lh "$DEST"

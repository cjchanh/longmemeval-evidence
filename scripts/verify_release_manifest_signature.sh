#!/usr/bin/env bash
set -eu
repo=$(CDPATH= cd -- "$(dirname "$0")/.." && pwd)
root="$repo/eval/dense_chain_v32_20260830/RELEASE_MANIFEST.root"
sig="${root}.sig"
if [ ! -f "$sig" ]; then
  printf 'UNSIGNED\n'
  exit 2
fi
allowed="$repo/eval/dense_chain_v32_20260830/allowed_signers"
if [ ! -f "$allowed" ]; then
  allowed="$repo/allowed_signers"
fi
ssh-keygen -Y verify \
  -f "$allowed" \
  -I release@centennialdefense.systems \
  -n longmemeval-release \
  -s "$sig" \
  < "$root"

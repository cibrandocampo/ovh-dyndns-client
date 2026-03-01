#!/usr/bin/env bash
# Installs the pre-commit hook by creating a symlink from .git/hooks/pre-commit
# to scripts/pre-commit.
#
# Usage:  bash scripts/install-hooks.sh

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
HOOK_SRC="$REPO_ROOT/scripts/pre-commit"
HOOK_DST="$REPO_ROOT/.git/hooks/pre-commit"

if [ ! -f "$HOOK_SRC" ]; then
  echo "Error: $HOOK_SRC not found."
  exit 1
fi

chmod +x "$HOOK_SRC"
ln -sf "$HOOK_SRC" "$HOOK_DST"
echo "Pre-commit hook installed: $HOOK_DST -> $HOOK_SRC"

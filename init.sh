#!/usr/bin/env bash
# Usage: ./init.sh /path/to/project
# Copies the kit into a project without overwriting existing files.
set -euo pipefail
TARGET="${1:?Usage: ./init.sh /path/to/project}"
KIT="$(cd "$(dirname "$0")" && pwd)"
mkdir -p "$TARGET/.agents"
for f in AGENTS.md PROJECT.md; do
  if [ -e "$TARGET/$f" ]; then echo "skip (exists): $f"; else cp "$KIT/$f" "$TARGET/$f"; echo "added: $f"; fi
done
cp -rn "$KIT/.agents/." "$TARGET/.agents/"
if [ -d "$KIT/docs" ]; then
  mkdir -p "$TARGET/docs"
  cp -rn "$KIT/docs/." "$TARGET/docs/"
  echo "synced: docs/"
fi
echo "Done. Next: fill in $TARGET/PROJECT.md (or ask the agent to draft it from the repo)."

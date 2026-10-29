#!/usr/bin/env bash
# Build the two CS239 submission archives into dist/.
# Usage: ./package.sh <name> <uid>
set -euo pipefail

if [ $# -ne 2 ]; then
  echo "usage: $0 <name> <uid>" >&2
  exit 1
fi

NAME="$1"
UID_="$2"
APP="QuantumJobRunner"
cd "$(dirname "$0")"
mkdir -p dist

# Keep caches and macOS metadata out of the archives.
export COPYFILE_DISABLE=1
EXCLUDES=(--exclude='__pycache__' --exclude='*.pyc' --exclude='.DS_Store' --exclude='.env')

# Archive 1: just the application description folder (lives in src/), at the archive root.
tar -czf "dist/${NAME}-${APP}-${UID_}-requirements.tar.gz" "${EXCLUDES[@]}" -C src "$APP"
# Archive 2: everything (src/ already contains the application description).
tar -czf "dist/${NAME}-${APP}-${UID_}-whole.tar.gz" "${EXCLUDES[@]}" --exclude='src/traces/web' \
  src tests README.md requirements.md policies.md LICENSE

ls -lh dist/

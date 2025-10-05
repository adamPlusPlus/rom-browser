#!/usr/bin/env bash
set -euo pipefail

# Move common config file types from external/GameSuite into config/
project_root_dir="$(cd "$(dirname "$0")"/.. && pwd)"
cd "$project_root_dir"

mkdir -p config

find external/GameSuite -type f \( \
  -name '*.conf' -o \
  -name '*.json' -o \
  -name '*.ini'  -o \
  -name '*.yaml' -o \
  -name '*.yml' \
\) -print0 | while IFS= read -r -d '' f; do
  mv -f "$f" config/
done

ls -la config



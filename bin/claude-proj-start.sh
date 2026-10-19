#!/usr/bin/env bash
set -euo pipefail

# Resolve the hub directory from the script's real location (follows symlinks)
SCRIPT="$(realpath "${BASH_SOURCE[0]}")"
HUB="$(cd "$(dirname "$SCRIPT")/.." && pwd)"

# The repos this project spans
REPOS=(
  "$HOME/source/repos/zeta_ball_api_data"
  "$HOME/source/repos/connors_snowflake_db"
  "$HOME/source/repos/aws_iac_mngr"
)

ADD_DIRS=()
for repo in "${REPOS[@]}"; do
  ADD_DIRS+=(--add-dir "$repo")
done

cd "$HUB"
exec claude "${ADD_DIRS[@]}" "$@"
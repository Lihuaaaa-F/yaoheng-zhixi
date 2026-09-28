#!/usr/bin/env bash
set -euo pipefail
project_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
if [ -f "$project_dir/环境接入.local.sh" ]; then source "$project_dir/环境接入.local.sh"; fi
exec bash "$project_dir/05_原型/scripts/stop.sh" "$@"

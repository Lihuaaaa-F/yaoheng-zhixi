#!/usr/bin/env bash
set -euo pipefail
app_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
exec "$(bash "$app_dir/scripts/pharma_python.sh")" "$app_dir/scripts/manage.py" stop

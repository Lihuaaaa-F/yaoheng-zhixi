#!/usr/bin/env bash
set -euo pipefail
app_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$app_dir"
export PYTHONPATH="$app_dir/backend" ANONYMIZED_TELEMETRY=False OTEL_SDK_DISABLED=true
case "$(uname -s)" in MINGW*|MSYS*|CYGWIN*) export TMPDIR="${TEMP:-/tmp}";; *) export TMPDIR=/tmp;; esac
exec "$(bash "$(dirname -- "${BASH_SOURCE[0]}")/pharma_python.sh")" scripts/verify.py "$@"

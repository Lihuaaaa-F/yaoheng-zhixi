#!/usr/bin/env bash
set -euo pipefail
here="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
app_dir="$(cd -- "$here/.." && pwd)"
export PYTHONPATH="$app_dir/backend" ANONYMIZED_TELEMETRY=False OTEL_SDK_DISABLED=true
case "$(uname -s)" in MINGW*|MSYS*|CYGWIN*) export TMPDIR="${TEMP:-/tmp}";; *) export TMPDIR=/tmp;; esac
exec "$(bash "$here/pharma_python.sh")" "$here/verify.py" "$@"

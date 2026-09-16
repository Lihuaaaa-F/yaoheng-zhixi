#!/usr/bin/env bash
set -euo pipefail
app_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$app_dir"
here="$(dirname -- "${BASH_SOURCE[0]}")"

# 1) Interpreter: one resolution order shared by every entry point.
pharma_python="$(bash "$here/pharma_python.sh")"
pharma_deps_log="$(mktemp)"
if [ -z "${PHARMA_PYTHON:-}" ] && [ ! -x "$app_dir/.venv/bin/python" ] && [ ! -x "$app_dir/.venv/Scripts/python.exe" ]; then
  "$pharma_python" -m venv .venv
  pharma_python="$(bash "$here/pharma_python.sh")"
fi
echo "解释器: $pharma_python"

# 2) Dependencies: compatible pinned versions plus real capability probes.
if ! env -u PYTHONPATH "$pharma_python" scripts/check_dependencies.py >"$pharma_deps_log" 2>&1; then
  if [ -n "${PHARMA_PYTHON:-}" ]; then
    cat "$pharma_deps_log" >&2 || true
    echo "指定的复用解释器缺少依赖或不兼容；请移除PHARMA_PYTHON并创建本项目venv。" >&2
    exit 1
  fi
  dependency_file=requirements.txt
  if [ -f requirements.lock ]; then
    dependency_file=requirements.lock
    case "$(uname -s)" in
      MINGW*|MSYS*|CYGWIN*)
        # The lock was built on Linux and lost PEP 508 markers; drop
        # POSIX-only transitive pins instead of failing their source build.
        dependency_file=.runtime/requirements.windows.txt
        mkdir -p .runtime
        grep -iv '^uvloop==' requirements.lock > "$dependency_file"
        ;;
    esac
  fi
  env -u PYTHONPATH "$pharma_python" -m pip install --retries 1 --timeout 30 -r "$dependency_file"
  env -u PYTHONPATH "$pharma_python" scripts/check_dependencies.py
fi

# 3) Frontend: rebuild whenever any build input changes. The shipped dist
# alone never proves the served UI matches src/config/lock.
build_inputs="$( (find frontend/src frontend/public -type f 2>/dev/null; ls frontend/package.json frontend/package-lock.json frontend/tsconfig.json frontend/vite.config.ts frontend/index.html 2>/dev/null) | sort )"
input_hash="$(echo "$build_inputs" | while read -r f; do [ -f "$f" ] && sha256sum "$f"; done | sha256sum | cut -d' ' -f1)"
stale=1
if [ -f frontend/dist/index.html ] && [ -f frontend/dist/.build-inputs ] && [ "$(cat frontend/dist/.build-inputs)" = "$input_hash" ]; then
  stale=0
fi
if [ "$stale" = 1 ]; then
  [ -d frontend/node_modules ] || (cd frontend && npm ci --ignore-scripts)
  (cd frontend && npm run build)
  printf '%s' "$input_hash" > frontend/dist/.build-inputs
  echo "前端已按当前源码重新构建 (input-hash ${input_hash:0:12})"
else
  echo "前端dist与当前源码一致 (input-hash ${input_hash:0:12})，跳过构建"
fi

# 4) Data, retrieval assets and working template.
export PYTHONPATH="$app_dir/backend" ANONYMIZED_TELEMETRY=False OTEL_SDK_DISABLED=true
case "$(uname -s)" in MINGW*|MSYS*|CYGWIN*) export TMPDIR="$TEMP";; *) export TMPDIR=/tmp;; esac
"$pharma_python" -c 'from pharma.ingestion import ingest; print(ingest()["snapshot_id"])'
"$pharma_python" scripts/fetch_embedding.py
"$pharma_python" -c 'from pharma.knowledge import Knowledge; print(Knowledge().build())'
"$pharma_python" -c 'from pharma.reports import TEMPLATE,normalize_template; print(normalize_template()["template_hash"] if not TEMPLATE.exists() else "工作模板已存在，复用")'

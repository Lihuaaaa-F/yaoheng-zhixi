#!/usr/bin/env bash
set -euo pipefail
# Resolve absolute paths BEFORE any cd: callers may invoke this script by a
# relative path from the project root.
here="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
app_dir="$(cd -- "$here/.." && pwd)"
cd "$app_dir"

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
input_hash="$("$pharma_python" "$here/build_inputs.py")"
lock_hash="$("$pharma_python" "$here/build_inputs.py" --lock)"
if [ ! -f frontend/node_modules/.lock-input ] || [ "$(cat frontend/node_modules/.lock-input)" != "$lock_hash" ]; then
  (cd frontend && npm ci --ignore-scripts)
  printf '%s' "$lock_hash" > frontend/node_modules/.lock-input
fi
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
"$pharma_python" scripts/fetch_embedding.py --check-only || echo "嵌入模型不可用：保留关键词检索，未下载或覆盖外置模型。"
"$pharma_python" - <<'BOOTSTRAP'
# 2026-09-22 三模块改版：系统专注制药赛题定制——赛题数据目录在位即摄取
# （企业主数据默认解析仓库内 competition_configuration），冒烟验证默认上下文；
# 合成演示上下文不再出现在目录（PHARMA_SHOW_TEST_CONTEXTS=1 可列出校验）。
from pharma.config import PACKAGE
from pharma.industry import context_catalog,analyze_reference
from pharma.context_services import retrieve
if PACKAGE.is_dir():
    from pharma.ingestion import ingest
    from pharma.reports import normalize_template,TEMPLATE
    print('赛题数据摄取：',ingest()['status'])
    if not TEMPLATE.exists():normalize_template()
else:
    print('未找到赛题数据目录：跳过摄取，可在数据中心导入业务数据')
catalog=context_catalog()
default=catalog['default_context_id']
if not default:
    print('无可用数据上下文（赛题数据缺失且未导入企业）：工作台将引导到数据中心')
else:
    snapshot=analyze_reference(default)
    evidence=retrieve(snapshot,'成本 工序 核查')
    print(default,evidence['status'],'上下文共',len(catalog['contexts']),'个')
BOOTSTRAP

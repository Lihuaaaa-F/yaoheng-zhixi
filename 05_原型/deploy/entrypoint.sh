#!/bin/sh
# 容器入口：按服务职责映射启动命令；向量模型缺失时先按固定哈希清单补齐
# （可用国内镜像），失败不阻断启动——确定性分析与 BM25 检索仍可用，
# 页面会显示降级状态。
set -e

CMD="$1"
case "$CMD" in
  web)   EXEC="python -m uvicorn pharma.api:app --host 0.0.0.0 --port 8765" ;;
  worker) EXEC="python -m pharma.worker" ;;
  rpa)   EXEC="python -m uvicorn pharma.synthetic_rpa:app --host 0.0.0.0 --port 8090" ;;
  *)     EXEC="$@" ;;
esac

if [ "$CMD" = "worker" ] && [ "${PHARMA_FETCH_EMBEDDING:-0}" = "1" ]; then
  python /app/05_原型/scripts/fetch_embedding.py --check-only >/dev/null 2>&1 || \
  python /app/05_原型/scripts/fetch_embedding.py >/dev/null 2>&1 || \
  echo "[entrypoint] 向量模型未能就绪（可设 PHARMA_EMBEDDING_MIRROR=1 重试）；当前以确定性分析与词法检索降级运行" >&2
fi

exec $EXEC

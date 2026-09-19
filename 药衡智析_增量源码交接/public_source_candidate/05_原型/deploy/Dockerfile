# 药衡智析正式运行镜像（构建上下文 = public_source_candidate/）
# 分两阶段：Node 构建前端静态产物；Python 运行时安装依赖、LibreOffice 与中文字体。
# 赛题原件不烧入镜像——运行期以只读卷挂载（见 docker-compose.yml）。

# ---------- 阶段 1：前端构建 ----------
FROM node:20-alpine AS frontend
WORKDIR /src
ENV PLAYWRIGHT_SKIP_BROWSER_DOWNLOAD=1
COPY 05_原型/frontend/package.json 05_原型/frontend/package-lock.json ./
RUN npm ci
COPY 05_原型/frontend ./
RUN npm run build

# ---------- 阶段 2：应用运行时 ----------
FROM python:3.12-slim
ENV PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app/05_原型/backend \
    PYTHONDONTWRITEBYTECODE=1 \
    MPLCONFIGDIR=/data/runtime/matplotlib \
    ANONYMIZED_TELEMETRY=False \
    OTEL_SDK_DISABLED=true \
    PHARMA_RUNTIME_DIR=/data/runtime \
    PHARMA_ARTIFACTS_DIR=/data/artifacts \
    PHARMA_DATA_PACKAGE=/app/package \
    PHARMA_COMPETITION_CONFIG_DIR=/app/competition_configuration \
    PHARMA_RPA_SIMULATION=1 \
    PHARMA_RPA_INTERNAL_SIMULATOR=rpa \
    RPA_BASE_URL=http://rpa:8090

# LibreOffice 提供 DOCX→PDF 转换；Noto CJK 提供离线中文字体。
# apt 使用国内镜像源（构建环境不依赖外网代理；代理可经预定义 build-args 叠加）。
RUN sed -i 's|deb.debian.org|mirrors.tuna.tsinghua.edu.cn|g' /etc/apt/sources.list.d/debian.sources \
    && apt-get update \
    && apt-get install -y --no-install-recommends \
        libreoffice-writer fonts-noto-cjk fontconfig \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app/05_原型
COPY 05_原型/requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt

COPY 05_原型/backend ./backend
COPY 05_原型/industry_packs ./industry_packs
COPY 05_原型/assets ./assets
COPY 05_原型/scripts ./scripts
COPY --from=frontend /src/dist ./frontend/dist
# 赛题正式配置（主数据/术语/场景）随镜像分发，保持正式口径自包含；
# 环境变量可重定向到挂载副本。
COPY competition_configuration /app/competition_configuration
COPY docs/embedding_manifest.json /app/docs/embedding_manifest.json
COPY 05_原型/deploy/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh && mkdir -p /data/runtime /data/artifacts

EXPOSE 8765
ENTRYPOINT ["/entrypoint.sh"]

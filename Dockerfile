# ============================================
# Stage 1: Base - 通用运行环境
# ============================================
FROM mcr.microsoft.com/playwright/python:v1.49.0-jammy AS base

# ---------- 构建参数 ----------
ARG USER_ID=1000
ARG GROUP_ID=1000
ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

USER root

# ---------- 系统依赖 ----------
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
      dnsutils ca-certificates dirmngr apt-transport-https net-tools \
      iputils-ping netcat-openbsd curl wget jq vim nano less \
      postgresql-client redis-tools && \
    curl -O https://packages.clickhouse.com/deb/pool/main/c/clickhouse-client/clickhouse-client_24.3.1.2077_amd64.deb && \
    dpkg -i clickhouse-client_24.3.1.2077_amd64.deb || apt-get install -f -y && \
    rm -rf clickhouse-client_24.3.1.2077_amd64.deb && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# ---------- 创建应用用户和设置权限 ----------
RUN if ! getent group 1001 > /dev/null; then \ 
    groupadd -g 1001 appuser; \ 
fi
RUN if ! getent passwd appuser > /dev/null; then \ 
    useradd -u 1001 -g 1001 -m -s /bin/bash appuser; \ 
fi
RUN mkdir -p /home/appuser/.local
RUN chown -R 1001:1001 /home/appuser
RUN mkdir -p /app /app/data /app/logs /etc/collector /var/lib/collector /var/log/collector /var/cache/collector
RUN chown -R 1001:1001 /app /etc/collector /var/*

USER appuser
WORKDIR /app

# ---------- 复制依赖文件 ----------
COPY --chown=1001:1001 requirements.txt config.yaml ./
COPY --chown=1001:1001 config/ /etc/collector/

# ---------- 安装 Python 依赖 ----------
RUN --mount=type=cache,target=/tmp/.cache/pip \
    pip install --user --timeout 120 --retries 5 -r requirements.txt
RUN --mount=type=cache,target=/tmp/.cache/pip \
    pip install playwright
RUN echo "Installing requirements.txt..." && cat requirements.txt
RUN --mount=type=cache,target=/tmp/.cache/pip \
    pip install --user --timeout 120 --retries 5 -r requirements.txt
RUN echo "Installed packages after requirements.txt:" && pip list
RUN if ! pip list | grep celery; then echo "ERROR: Celery not installed!"; exit 1; fi
RUN echo "Celery installation verified"

# ---------- 环境变量 ----------
ENV HOME=/home/appuser \
    PATH="/home/appuser/.local/bin:/usr/local/bin:${PATH}" \
    PYTHONPATH="/home/appuser/.local/lib/python3.10/site-packages:${PYTHONPATH}" \
    XDG_CACHE_HOME=/var/cache/collector \
    PLAYWRIGHT_BROWSERS_PATH=/var/cache/collector/ms-playwright \
    CRAWL4AI_WORKDIR=/var/cache/collector/crawl4ai \
    CRAWL4AI_CACHE_DIR=/var/cache/collector/crawl4ai/cache

# ============================================
# Stage 2: Development
# ============================================
FROM base AS development
USER root

RUN apt-get update && apt-get install -y dos2unix htop tree net-tools && apt-get clean && rm -rf /var/lib/apt/lists/*
COPY --chown=appuser:appuser requirements-dev.txt ./

RUN --mount=type=cache,target=/tmp/.cache/pip \
    pip install -r requirements-dev.txt

COPY --chown=appuser:appuser . /app

# ---------- entrypoint ----------
COPY --chown=appuser:appuser entrypoint.sh /usr/local/bin/entrypoint.sh
RUN dos2unix /usr/local/bin/entrypoint.sh && chmod 755 /usr/local/bin/entrypoint.sh

USER appuser
EXPOSE 8000

ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]
CMD ["python", "-m", "src.financial_data_collector.main", "--debug"]

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:8000/health || exit 1

# ============================================
# Stage 3: Production
# ============================================
FROM base AS production
USER root

# ---------- 清理开发工具 ----------
RUN apt-get purge -y vim nano htop tree netcat-openbsd && \
    apt-get autoremove -y && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# ---------- 复制应用代码 ----------
COPY --chown=appuser:appuser . /app

RUN chown -R appuser:appuser /app /var/lib/collector /var/log/collector && \
    chmod -R 755 /etc/collector && \
    chmod -R 775 /var/lib/collector /var/log/collector

# ---------- 环境变量 ----------
ENV PYTHONOPTIMIZE=1 \
    CONFIG_FILE=/etc/collector/production.yaml

USER appuser
EXPOSE 8000

ENTRYPOINT ["python", "-m", "src.financial_data_collector.main"]
CMD ["--config", "/etc/collector/production.yaml"]

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:8000/health || exit 1

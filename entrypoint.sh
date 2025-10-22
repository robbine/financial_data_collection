#!/bin/sh
set -e

# -------------------------------
# 设置 PYTHONPATH
# -------------------------------
# 将项目 src 目录和用户 site-packages 加入 PYTHONPATH
export PYTHONPATH="/app/src:$(python -m site --user-site):${PYTHONPATH}"
echo "[DEBUG] Python版本: $(python --version)"
echo "[DEBUG] 工作目录: $(pwd)"
echo "[DEBUG] PYTHONPATH: ${PYTHONPATH}"

# -------------------------------
# 调试输出
# -------------------------------
echo "[DEBUG] 接收到的命令参数: $@"
echo "[DEBUG] 当前用户: $(whoami)"
echo "[DEBUG] 工作目录内容: $(ls -la)"

# -------------------------------
# 如果第一个参数是 celery，则使用 python -m celery 启动
# -------------------------------
if [ "$1" = "celery" ]; then
    echo "[DEBUG] 检测到 Celery 命令，使用 python -m celery 调用"
    shift  # 移除 "celery"
    set -- python -m celery "$@"
fi

# -------------------------------
# 执行最终命令
# -------------------------------
echo "[DEBUG] 执行命令: $@"
exec "$@"

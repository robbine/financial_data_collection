#!/bin/sh
set -e

# 动态设置PYTHONPATH以包含用户site-packages目录
export PYTHONPATH="$(python -m site --user-site):${PYTHONPATH}"
echo "[DEBUG] Python版本: $(python --version)"
echo "[DEBUG] 用户site路径: $(python -m site --user-site)"
echo "[DEBUG] 已安装包: $(pip list | grep celery)"
echo "[DEBUG] Python可执行路径: $(which python)"
echo "[DEBUG] Python版本详细信息: $(python -VV)"
echo "[DEBUG] 完整已安装包列表:"
pip list
echo "[DEBUG] site-packages目录内容:"
ls -la $(python -m site --user-site)
echo "[DEBUG] 设置PYTHONPATH: ${PYTHONPATH}"

# 添加调试输出
echo "[DEBUG] 启动入口脚本，当前用户: $(whoami)"
echo "[DEBUG] 工作目录内容: $(ls -la)"
echo "[DEBUG] 数据目录权限: $(ls -la /app/data)"

# 调试输出命令参数
echo "[DEBUG] 接收到的命令参数: $@"

# 如果第一个参数是 celery，则改用 python -m celery 方式执行
if [ "$1" = "celery" ]; then
    echo "[DEBUG] 检测到 Celery 命令，改为使用 python -m celery 调用"
    shift  # 移除 "celery"
    set -- python -m celery "$@"
fi

echo "[DEBUG] 完整命令: exec $@"
exec "$@" 2>&1

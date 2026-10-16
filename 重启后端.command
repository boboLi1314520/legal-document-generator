#!/bin/bash
# ============================================================
#  重启后端服务（macOS）
# ============================================================
# 对应 Windows 侧的 重启后端.bat：
#   杀掉占用 8002 的进程 → 重新在后台启动后端 → 等就绪
#
# 双击运行即可。注意：双击时窗口在工作目录上是不可靠的，
# 因此这里一律用脚本自身位置推项目目录。

set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/scripts/mac_common.sh"

echo "================================================"
echo "    后端服务重启"
echo "================================================"
echo

find_python
ensure_venv

echo
kill_port

echo
start_backend_bg

echo
if ! wait_ready 30; then
  echo "[警告] 后端启动较慢或失败，请查看日志：$SERVER_LOG"
fi

echo
echo "================================================"
echo "    后端地址: http://localhost:8002"
echo "    日志文件: backend/server.log"
echo "================================================"
echo "    关闭本窗口不会停止后端服务"
echo

pause_on_error

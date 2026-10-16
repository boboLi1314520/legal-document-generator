#!/bin/bash
# ============================================================
#  开发模式启动（macOS）
# ============================================================
# 对应 Windows 侧的 启动器.bat：
#   后台起后端（8002）+ 前台跑前端热更新（3000，/api 由 vite 代理到后端）
#
# 与"双击 启动.command"的区别：启动.command 跑的是 frontend/dist 里的
# 构建产物，改了 src/ 必须重新 npm run build 才生效；
# 本脚本跑的是 vite 开发服务器，改 src/ 立即热更新，无需构建。
#
# 退出：在本窗口按 Control + C 停止前端；后台后端需用 重启后端.command 或
# 手动 kill 停止（关闭窗口不影响它）。

set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/scripts/mac_common.sh"

echo "================================================"
echo "    法律文书自动生成系统 - 开发模式"
echo "================================================"
echo

if ! command -v npm >/dev/null 2>&1; then
  echo "[错误] 未检测到 Node.js / npm，开发模式需要它。"
  echo "        下载地址: https://nodejs.org/"
  open "https://nodejs.org/" || true
  pause_on_error
  exit 1
fi

find_python
ensure_venv

echo
kill_port

echo
start_backend_bg

echo
if ! wait_ready 30; then
  echo "[警告] 后端启动较慢，前端代理到 8002 的请求可能暂时失败"
fi

cd "$FRONTEND_DIR"

if [[ ! -d node_modules ]]; then
  echo
  echo "首次运行：正在安装前端依赖，可能需要几分钟……"
  npm install
fi

echo
echo "================================================"
echo "    前端 http://localhost:3000"
echo "    后端 http://localhost:8002"
echo "================================================"
echo "    改 src/ 下的文件会立即热更新，无需 npm run build"
echo "    按 Control + C 停止前端（后台后端不受影响）"
echo

# 等 vite 起来再开浏览器，避免打开一个连不上的页面
( sleep 5; open "http://localhost:3000" ) &

# 放前台，这样 Control + C 能停掉 vite。
#
# --strictPort 是必需的：vite 默认在 3000 被占用时会静默改用 3001，而本脚本
# 已经把浏览器指向 3000 —— 那样你会打开别人的服务、或一个连不上后端的旧页面，
# 且没有任何提示。加严格模式后 vite 会大声报 "Port 3000 is already in use" 并退出。
npm run dev -- --strictPort

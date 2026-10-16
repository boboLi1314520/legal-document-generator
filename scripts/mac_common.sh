#!/bin/bash
# ============================================================
#  macOS 启动脚本公用库
# ============================================================
# 被 启动.command / 重启后端.command / 开发模式.command 共用，
# 集中处理"找 Python → 定位虚拟环境 → 按需装依赖 → 管端口 → 等就绪"。
#
# 用法：在 .command 脚本里
#     SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
#     source "$SCRIPT_DIR/scripts/mac_common.sh"
# 然后调用 find_python / ensure_venv / kill_port / start_backend_bg / wait_ready。
#
# 修改这里的逻辑会同时影响三个脚本——这是刻意的，避免三份重复实现各自腐烂。

# 本文件位于 <项目>/scripts/ 下，因此项目根目录是它的上一级。
# 注意：不能用调用方的 BASH_SOURCE 推项目目录，被 source 时那是本文件的路径。
_MAC_COMMON_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd -- "$_MAC_COMMON_DIR/.." && pwd)"

BACKEND_DIR="$PROJECT_DIR/backend"
FRONTEND_DIR="$PROJECT_DIR/frontend"
REQUIREMENTS="$BACKEND_DIR/requirements.txt"
SERVER_LOG="$BACKEND_DIR/server.log"
PORT=8002
STATUS_URL="http://127.0.0.1:${PORT}/api/status"

# 双击 .command 时窗口不会自动停留，出错时必须让用户看到信息再关窗。
pause_on_error() {
  read -r -p "按回车键关闭此窗口..." || true
}

# 依次尝试 3.14 / 3.13 / 3.12 / 3.11，选中第一个满足 3.11 <= 版本 < 3.15 的。
# 设 PYTHON_BIN。
find_python() {
  PYTHON_BIN=""
  local candidate candidate_path
  for candidate in python3.14 python3.13 python3.12 python3.11; do
    candidate_path="$(command -v "$candidate" || true)"
    if [[ -n "$candidate_path" ]] && \
       "$candidate_path" -c 'import sys; raise SystemExit(0 if (3, 11) <= sys.version_info[:2] < (3, 15) else 1)'; then
      PYTHON_BIN="$candidate_path"
      break
    fi
  done

  if [[ -z "$PYTHON_BIN" ]]; then
    echo "未检测到 Python 3.11 至 3.14。请安装 Python 3.14.8 后重新双击本文件："
    echo "https://www.python.org/downloads/release/python-3148/"
    open "https://www.python.org/downloads/release/python-3148/" || true
    pause_on_error
    exit 1
  fi
}

# 按选定的 Python 版本定位/创建 .venv-mac-<major.minor>，并在 requirements.txt
# 内容变化时装依赖。设 VENV_DIR 与 VENV_PY。
ensure_venv() {
  local python_version venv_version requirements_hash install_marker
  python_version="$("$PYTHON_BIN" -c 'import sys; print("%d.%d" % sys.version_info[:2])')"
  VENV_DIR="$PROJECT_DIR/.venv-mac-$python_version"
  VENV_PY="$VENV_DIR/bin/python"
  echo "使用 Python ${python_version}：${PYTHON_BIN}"

  # 注意 -x 对悬空软链为假：本项目里就有一个从打包者机器整个拷来的
  # .venv-mac-3.11，它的 bin/python 指向 /Users/hezhipeng/.local/bin/python3.11，
  # 在本机是死链。这种残留目录要用 --clear 重建，否则 venv 会在其上失败。
  if [[ ! -x "$VENV_PY" ]] || ! "$VENV_PY" -c 'import sys' >/dev/null 2>&1; then
    if [[ -d "$VENV_DIR" ]]; then
      echo "检测到不可用的虚拟环境（可能是从别的机器拷来的），正在重建：${VENV_DIR}"
      "$PYTHON_BIN" -m venv --clear "$VENV_DIR"
    else
      "$PYTHON_BIN" -m venv "$VENV_DIR"
    fi
  fi

  venv_version="$("$VENV_PY" -c 'import sys; print("%d.%d" % sys.version_info[:2])')"
  if [[ "$venv_version" != "$python_version" ]]; then
    echo "[错误] 虚拟环境 ${VENV_DIR} 的 Python 版本不匹配（${venv_version}）。"
    echo "        请删除该目录后重新运行。"
    pause_on_error
    exit 1
  fi

  # 用 requirements.txt 的哈希做安装标记，内容没变就不重复装。
  requirements_hash="$(shasum -a 256 "$REQUIREMENTS" | awk '{print $1}')"
  install_marker="$VENV_DIR/.requirements-$requirements_hash"
  if [[ ! -f "$install_marker" ]]; then
    echo "首次运行：正在安装后端依赖，可能需要几分钟……"
    "$VENV_PY" -m pip install --upgrade pip
    "$VENV_PY" -m pip install -r "$REQUIREMENTS"
    touch "$install_marker"
  fi
}

# 列出占用 $PORT 且处于 LISTEN 状态的 PID。
#
# 必须带 -sTCP:LISTEN。否则浏览器到 8002 的 ESTABLISHED 连接会让 lsof 把
# 浏览器的 PID 也列出来，直接 kill 就会误杀用户的浏览器——只取监听者，
# 才能保证杀到的确实是后端。
port_listener_pids() {
  lsof -nP -iTCP:"$PORT" -sTCP:LISTEN -t 2>/dev/null || true
}

# 终止占用 $PORT 的进程。
#
# 不询问（按既定策略直接杀），但绝不静默：杀之前打印每个进程的启动时间和
# 完整命令行。这条信息很关键——曾有一次占用者来自桌面上的另一份项目副本，
# 正是靠它才看出来。
kill_port() {
  local pids pid info i
  pids="$(port_listener_pids)"

  if [[ -z "$pids" ]]; then
    return 0
  fi

  # 护栏：绝不杀自己，绝不杀 launchd（PID 1）。另外 pids 为空时必须提前
  # return——空串传给 kill 会报错，而 `kill 0` 会杀掉整个进程组。
  local victims=""
  for pid in $pids; do
    if [[ "$pid" == "$$" || "$pid" == "1" ]]; then
      echo "  跳过 PID ${pid}（本脚本自身或系统进程）"
      continue
    fi
    victims="$victims $pid"
  done
  [[ -z "${victims// /}" ]] && return 0
  pids="$victims"

  echo "端口 $PORT 已被占用，将终止以下进程："
  for pid in $pids; do
    info="$(ps -o lstart=,command= -p "$pid" 2>/dev/null || true)"
    echo "  PID $pid  ${info:-（无法读取进程信息）}"
  done

  # 先 TERM 给正常退出的机会
  for pid in $pids; do
    kill -TERM "$pid" 2>/dev/null || true
  done
  sleep 2

  # 有些进程会忽略 TERM（例如曾用 uvicorn --reload 启动的），再升级到 KILL
  for pid in $pids; do
    if kill -0 "$pid" 2>/dev/null; then
      echo "  PID $pid 未响应 TERM，改用 KILL"
      kill -9 "$pid" 2>/dev/null || true
    fi
  done

  # 等端口真正释放
  for i in 1 2 3 4 5 6 7 8 9 10; do
    [[ -z "$(port_listener_pids)" ]] && break
    sleep 0.5
  done
}

# 在后台启动后端。注意 backend/main.py 里有 `from app.api.routes import ...`，
# 必须以 backend/ 为工作目录运行，否则导入失败。
# 用子 shell 包住 cd，避免改变调用方的工作目录。
# 设 BACKEND_PID。
start_backend_bg() {
  (
    cd "$BACKEND_DIR" || exit 1
    exec nohup "$VENV_PY" main.py >> "$SERVER_LOG" 2>&1
  ) &
  BACKEND_PID=$!
  disown 2>/dev/null || true
  # 变量一律用 ${} 包住：紧邻全角字符时，bash 的变量名扫描可能把多字节字符
  # 的字节当成变量名的一部分，导致 "unbound variable" 之类的诡异报错。
  echo "后端已在后台启动（PID ${BACKEND_PID}），日志：${SERVER_LOG}"
}

# 轮询 /api/status 直到就绪，最多等 $1 秒（默认 30）。
wait_ready() {
  local max_wait="${1:-30}" i
  printf '等待后端就绪'
  for ((i = 0; i < max_wait; i++)); do
    if curl -sf -m 2 "$STATUS_URL" >/dev/null 2>&1; then
      printf ' 已就绪\n'
      return 0
    fi
    printf '.'
    sleep 1
  done
  printf ' 超时\n'
  return 1
}

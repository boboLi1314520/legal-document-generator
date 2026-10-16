#!/bin/bash
# ============================================================
#  一键启动（macOS）
# ============================================================
# 找 Python → 定位/创建虚拟环境 → 按需装依赖 → 交给 launcher.py。
#
# 环境解析逻辑已抽到 scripts/mac_common.sh，与 重启后端.command、
# 开发模式.command 共用，避免三份重复实现各自腐烂。
#
# 本脚本跑的是 frontend/dist 里的构建产物。改了 frontend/src/ 必须
# 重新 npm run build 才生效；改代码时请改用 开发模式.command。

set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/scripts/mac_common.sh"

find_python
ensure_venv

exec "$VENV_PY" "$PROJECT_DIR/launcher.py"

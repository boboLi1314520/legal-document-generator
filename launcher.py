"""
法律文书自动生成系统 - 一键启动脚本（方案1：预构建便携包）
需要 Python 3.11+，无需 Node.js
"""
import os
import sys
import time
import socket
import signal
import subprocess
import webbrowser
from pathlib import Path

PROJECT_DIR = Path(__file__).parent.resolve()
BACKEND_DIR = PROJECT_DIR / "backend"
DIST_DIR = PROJECT_DIR / "frontend" / "dist"
REQUIREMENTS = BACKEND_DIR / "requirements.txt"
ENV_FILE = BACKEND_DIR / ".env"
HOST = "127.0.0.1"
PORT = 8002
URL = f"http://{HOST}:{PORT}"

# 最小 Python 版本
MIN_PYTHON = (3, 11)


def print_banner():
    print()
    print("=" * 50)
    print("    法律文书自动生成系统  v1.0")
    print("    预构建便携版 - 需要 Python 3.11+")
    print("=" * 50)
    print()


def check_python():
    """检查 Python 版本"""
    ver = sys.version_info[:2]
    if ver < MIN_PYTHON:
        print(f"[错误] Python 版本过低：{ver[0]}.{ver[1]}")
        print(f"        需要 Python {MIN_PYTHON[0]}.{MIN_PYTHON[1]}+")
        print("        下载地址: https://www.python.org/downloads/")
        return False
    if ver >= (3, 15):
        print(f"[错误] 当前依赖尚未支持 Python {ver[0]}.{ver[1]}")
        print("        请使用 Python 3.11 至 3.14；macOS 推荐 Python 3.14.8")
        return False
    print(f"[1/5] Python {ver[0]}.{ver[1]} 环境已就绪")
    return True


def check_frontend_dist():
    """检查前端构建文件是否存在"""
    dist_index = DIST_DIR / "index.html"
    if not dist_index.exists():
        print()
        print("[错误] 未找到前端构建文件 frontend/dist/")
        print()
        print("请在已安装 Node.js 的电脑上执行以下命令：")
        print("  cd frontend")
        print("  npm install")
        print("  npm run build")
        print()
        print("然后将 frontend/dist/ 文件夹一同复制到目标电脑。")
        return False
    print(f"[2/5] 前端构建文件已就绪")
    return True


def install_dependencies():
    """检查并安装后端依赖"""
    print(f"[3/5] 检查后端依赖...")

    # 快速检查核心依赖是否已安装
    try:
        import fastapi, uvicorn, docx, openpyxl, pandas, httpx, fitz, rapidocr, onnxruntime  # noqa
        from langchain_core.messages import HumanMessage  # noqa
        from langchain_openai import ChatOpenAI  # noqa
        print("       依赖已就绪")
        return True
    except ImportError:
        pass

    print("       首次运行，正在安装依赖（可能需要几分钟）...")
    print()

    # 尝试使用清华镜像源
    print("       [1/2] 尝试清华镜像源...")
    result = subprocess.run(
        [sys.executable, "-m", "pip", "install", "-r", str(REQUIREMENTS),
         "-i", "https://pypi.tuna.tsinghua.edu.cn/simple"],
        cwd=str(BACKEND_DIR),
        capture_output=False
    )

    if result.returncode != 0:
        print()
        print("       [2/2] 镜像源失败，使用默认源...")
        result = subprocess.run(
            [sys.executable, "-m", "pip", "install", "-r", str(REQUIREMENTS)],
            cwd=str(BACKEND_DIR),
            capture_output=False
        )

    if result.returncode != 0:
        print()
        print("[错误] 依赖安装失败，请检查网络连接后重试")
        return False

    print()
    print("       依赖安装完成！")
    return True


def configure_env():
    """检查/创建 .env 配置文件"""
    print(f"[4/5] 配置检查...")

    if ENV_FILE.exists():
        # 检查是否有有效的 API Key
        content = ENV_FILE.read_text(encoding="utf-8", errors="ignore")
        if "DEEPSEEK_API_KEY=" in content:
            key_value = content.split("DEEPSEEK_API_KEY=", 1)[1].split("\n")[0].strip()
            if key_value and key_value != "请在此输入您的APIKey" and key_value != "您的key":
                print("       配置文件已存在")
                return True

    print()
    print("       " + "-" * 55)
    print("       首次运行，需要配置 DeepSeek API Key")
    print("       如果没有 API Key，请前往 https://platform.deepseek.com 注册获取")
    print("       " + "-" * 55)
    print()

    try:
        api_key = input("请输入 DeepSeek API Key: ").strip()
    except (EOFError, KeyboardInterrupt):
        api_key = ""

    if api_key:
        ENV_FILE.write_text(f"DEEPSEEK_API_KEY={api_key}\n", encoding="utf-8")
        print("       API Key 已保存")
    else:
        ENV_FILE.write_text("DEEPSEEK_API_KEY=请在此输入您的APIKey\n", encoding="utf-8")
        print("[警告] 未输入 API Key，请稍后编辑 backend\\.env 文件")

    return True


def create_runtime_dirs():
    """创建运行时目录"""
    (BACKEND_DIR / "outputs" / "cases").mkdir(parents=True, exist_ok=True)
    (BACKEND_DIR / "uploads").mkdir(parents=True, exist_ok=True)


def _listener_pids():
    """返回占用 PORT 且处于 LISTEN 状态的进程 PID（字符串）列表。

    只取 LISTEN，不取已建立的连接：否则浏览器到 8002 的 ESTABLISHED 连接
    会让 lsof 把浏览器的 PID 也列出来，照着杀就会误杀用户的浏览器。
    """
    try:
        if sys.platform == "win32":
            out = subprocess.run(
                ["netstat", "-ano", "-p", "TCP"],
                capture_output=True, text=True, timeout=10
            ).stdout
            pids = set()
            for line in out.splitlines():
                # 形如： TCP  0.0.0.0:8002  0.0.0.0:0  LISTENING  12345
                fields = line.split()
                if len(fields) >= 5 and fields[3] == "LISTENING" \
                        and fields[1].endswith(f":{PORT}"):
                    pids.add(fields[4])
            return sorted(pids)

        out = subprocess.run(
            ["lsof", "-nP", f"-iTCP:{PORT}", "-sTCP:LISTEN", "-t"],
            capture_output=True, text=True, timeout=10
        ).stdout
        return sorted({p.strip() for p in out.split() if p.strip()})
    except (OSError, subprocess.SubprocessError):
        return []


def _describe_pid(pid):
    """尽量给出进程的启动时间与命令行，便于判断杀的是谁。"""
    try:
        if sys.platform == "win32":
            out = subprocess.run(
                ["tasklist", "/FI", f"PID eq {pid}", "/NH", "/FO", "CSV"],
                capture_output=True, text=True, timeout=10
            ).stdout.strip()
        else:
            out = subprocess.run(
                ["ps", "-o", "lstart=,command=", "-p", str(pid)],
                capture_output=True, text=True, timeout=10
            ).stdout.strip()
        return out or "（无法读取进程信息）"
    except (OSError, subprocess.SubprocessError):
        return "（无法读取进程信息）"


def _pid_alive(pid):
    if sys.platform == "win32":
        try:
            out = subprocess.run(
                ["tasklist", "/FI", f"PID eq {pid}", "/NH"],
                capture_output=True, text=True, timeout=10
            ).stdout
            return str(pid) in out
        except (OSError, subprocess.SubprocessError):
            return False
    try:
        os.kill(int(pid), 0)
        return True
    except (OSError, ValueError):
        return False


def _kill_pid(pid, force=False):
    try:
        if sys.platform == "win32":
            cmd = ["taskkill", "/PID", str(pid)]
            if force:
                cmd.insert(1, "/F")
            subprocess.run(cmd, capture_output=True, timeout=10)
        else:
            os.kill(int(pid), signal.SIGKILL if force else signal.SIGTERM)
    except (OSError, ValueError, subprocess.SubprocessError):
        pass


def free_port():
    """端口被占用时终止占用者，返回 True 表示端口已释放。"""
    pids = _listener_pids()
    if not pids:
        return True

    print(f"[警告] 端口 {PORT} 已被占用，将终止以下进程：")
    for pid in pids:
        print(f"        PID {pid}  {_describe_pid(pid)}")

    # 先 TERM 给正常退出的机会
    for pid in pids:
        _kill_pid(pid, force=False)
    time.sleep(2)

    # 有些进程会忽略 TERM（例如用 uvicorn --reload 起的），再升级到 KILL
    for pid in pids:
        if _pid_alive(pid):
            print(f"        PID {pid} 未响应 TERM，改用强制终止")
            _kill_pid(pid, force=True)

    # 等端口真正释放
    for _ in range(20):
        if not _listener_pids():
            print(f"        端口 {PORT} 已释放")
            return True
        time.sleep(0.5)

    print(f"[错误] 端口 {PORT} 仍被占用")
    return False


def check_port():
    """确保端口可用；被占用则终止占用者。

    注意：这个函数原先从未被 main() 调用过（死代码）。端口被占用时启动器
    会静默继续——后端进程照常起来，却绑在通配地址上被已有进程劫持，浏览器
    的请求全部落到旧进程，表现为"前端能打开但一直报错"，且日志里除了一句
    address already in use 之外没有任何提示，极难排查。
    现在改为显式处理并全程打印，不再静默。
    """
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        sock.bind((HOST, PORT))
        sock.close()
        return True  # 端口可用
    except OSError:
        sock.close()

    return free_port()


def wait_for_server(max_wait=30):
    """轮询等待服务就绪"""
    import urllib.request
    print("       等待服务就绪...", end="", flush=True)

    for i in range(max_wait // 2):
        try:
            req = urllib.request.Request(f"{URL}/api/status")
            with urllib.request.urlopen(req, timeout=2) as resp:
                if resp.status == 200:
                    print()
                    print("       服务已就绪！")
                    return True
        except Exception:
            pass
        time.sleep(2)
        print(".", end="", flush=True)

    print()
    print("[警告] 服务启动较慢，请稍后手动刷新浏览器")
    return False


def main():
    print_banner()

    if not check_python():
        input("\n按回车键退出...")
        sys.exit(1)

    print()
    if not check_frontend_dist():
        input("\n按回车键退出...")
        sys.exit(1)

    print()
    if not install_dependencies():
        input("\n按回车键退出...")
        sys.exit(1)

    print()
    if not configure_env():
        input("\n按回车键退出...")
        sys.exit(1)

    create_runtime_dirs()

    # 端口检查：被占用时显式终止占用者，避免静默失败（见 check_port 注释）
    if not check_port():
        print()
        print(f"[错误] 无法释放端口 {PORT}，请手动处理后重试")
        input("\n按回车键退出...")
        sys.exit(1)

    print()
    print(f"[5/5] 启动服务（端口 {PORT}）...")
    print()

    # 后台启动 FastAPI 服务
    server_cmd = [sys.executable, str(BACKEND_DIR / "main.py")]
    if sys.platform == "win32":
        # Windows: 使用 CREATE_NEW_CONSOLE 在新窗口启动
        proc = subprocess.Popen(
            server_cmd,
            cwd=str(BACKEND_DIR),
            creationflags=subprocess.CREATE_NEW_CONSOLE
        )
    else:
        with (BACKEND_DIR / "server.log").open("a", encoding="utf-8") as log_file:
            proc = subprocess.Popen(
                server_cmd,
                cwd=str(BACKEND_DIR),
                stdout=log_file,
                stderr=subprocess.STDOUT,
                start_new_session=True
            )

    print("=" * 50)
    print("    正在启动后端服务...")
    print("=" * 50)
    print()

    # 等待服务就绪
    ready = wait_for_server()

    # 服务没就绪、而后端进程已经退出 —— 把日志尾部打出来。
    # 端口冲突只是后端静默失败的原因之一：导入错误、依赖缺失、.env 写坏
    # 都会走同一条路——报错只写进 server.log 没人看，浏览器却连着一个旧进程，
    # 用户看到的现象一律是"页面打开了但一直报错"。这道闸让任何一种都变得可见。
    if not ready and proc.poll() is not None:
        print()
        print(f"[错误] 后端进程已退出（退出码 {proc.returncode}）。server.log 末尾：")
        print("-" * 50)
        try:
            lines = (BACKEND_DIR / "server.log").read_text(
                encoding="utf-8", errors="ignore"
            ).splitlines()
            for line in lines[-25:]:
                print("   " + line)
        except OSError:
            print("   （无法读取 server.log）")
        print("-" * 50)
        input("\n按回车键退出...")
        sys.exit(1)

    # 打开浏览器
    print(f"\n       正在打开浏览器: {URL}")
    webbrowser.open(URL)

    print()
    print("=" * 50)
    print("    启动完成！")
    print("=" * 50)
    print()
    print(f"   访问地址: {URL}")
    print()
    print("   macOS 后端日志: backend/server.log")
    print("   开发模式请参阅 README.md")
    print("=" * 50)

    # 保持运行（Windows 下等待用户输入，否则窗口会闪退）
    try:
        input("\n按回车键退出启动器（不会停止后端服务）...")
    except (EOFError, KeyboardInterrupt):
        pass


if __name__ == "__main__":
    main()
